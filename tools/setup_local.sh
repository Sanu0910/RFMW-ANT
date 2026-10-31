#!/usr/bin/env bash
# One-command local setup for RFMW-ANT on Ubuntu 22.04 / 24.04 (desktop, server or WSL2).
# Installs every tool the projects use and the three MCP servers in .mcp.json, then runs tools/doctor.py.
# Safe to re-run: each step skips what is already installed.
#
#   cd RFMW-ANT && bash tools/setup_local.sh
#
# Skip steps with environment variables, e.g.  SKIP_OPENEMS=1 SKIP_HERTZON=1 bash tools/setup_local.sh
#   SKIP_APT SKIP_NODE SKIP_CLAUDE SKIP_PYTHON SKIP_OPENEMS SKIP_KICAD SKIP_SOLIDCRAFT SKIP_HERTZON
#   SKIP_EXTRAS (gds2openEMS, KiCadRoutingTools, Playwright, Octave)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ME="$(id -un)"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
skip() { [ "${!1:-0}" = "1" ]; }

. /etc/os-release
case "$ID:$VERSION_ID" in
  ubuntu:22.04|ubuntu:24.04) ;;
  *) echo "Tested on Ubuntu 22.04/24.04 only (found $PRETTY_NAME). Continuing anyway in 5 s..."; sleep 5;;
esac
$SUDO true   # ask for the sudo password once, up front

if ! skip SKIP_APT; then
  step "System packages"
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq \
    git curl wget ca-certificates build-essential cmake software-properties-common \
    python3 python3-venv python3-pip python3-dev \
    libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libvulkan1 xvfb \
    gh
fi

if ! skip SKIP_NODE; then
  step "Node.js >= 18 (MCP servers, Claude Code, PDF reports)"
  if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 18 ]; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO -E bash -
    $SUDO apt-get install -y -qq nodejs
  fi
  node --version
fi

if ! skip SKIP_CLAUDE; then
  step "Claude Code CLI"
  command -v claude >/dev/null || $SUDO npm install -g @anthropic-ai/claude-code
  claude --version
fi

if ! skip SKIP_PYTHON; then
  step "Python environment (.venv) for the project scripts"
  [ -x .venv/bin/python ] || python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r docs/requirements.txt scikit-rf
fi

if ! skip SKIP_OPENEMS; then
  step "openEMS + CSXCAD (FDTD, ~20 min build)"
  $SUDO bash tools/install_openems.sh
  $SUDO /opt/openEMS/venv/bin/pip install -q ezdxf shapely matplotlib
fi

if ! skip SKIP_KICAD; then
  step "KiCad 9 (native) + KiCAD-MCP-Server"
  if ! command -v kicad-cli >/dev/null; then
    $SUDO add-apt-repository -y ppa:kicad/kicad-9.0-releases
    $SUDO apt-get update -qq
    DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq kicad
  fi
  kicad-cli version
  SRV=/opt/KiCAD-MCP-Server
  if [ ! -d "$SRV/.git" ]; then
    $SUDO git clone --branch stable https://github.com/mixelpixx/KiCAD-MCP-Server "$SRV"
  fi
  $SUDO chown -R "$ME" "$SRV"
  (cd "$SRV" && npm install --no-fund --no-audit && npm run build)
  # venv that sees KiCad's pcbnew module (system site-packages) plus the server's own deps
  [ -x "$SRV/venv/bin/python" ] || /usr/bin/python3 -m venv --system-site-packages "$SRV/venv"
  "$SRV/venv/bin/pip" install -q -r "$SRV/requirements.txt"
  "$SRV/venv/bin/python" -c "import pcbnew; print('pcbnew', pcbnew.GetBuildVersion())"
fi

if ! skip SKIP_SOLIDCRAFT; then
  step "SolidCraft (solidcraft-cli, CAD + MCP)"
  if ! command -v solidcraft-cli >/dev/null; then
    URL=$(curl -fsSL https://api.github.com/repos/bherbruck/solidcraft/releases/latest \
          | grep -o '"browser_download_url": *"[^"]*\.deb"' | grep -iE 'amd64|x86_64' | head -1 | cut -d'"' -f4 || true)
    if [ -z "$URL" ]; then
      echo "Could not find the SolidCraft .deb automatically. Download it from"
      echo "  https://github.com/bherbruck/solidcraft/releases  and run: sudo apt install ./solidcraft_*.deb"
    else
      TMP=$(mktemp -d); curl -fsSL -o "$TMP/solidcraft.deb" "$URL"
      $SUDO apt-get install -y -qq "$TMP/solidcraft.deb"; rm -rf "$TMP"
    fi
  fi
  command -v solidcraft-cli >/dev/null && solidcraft-cli --version
fi

if ! skip SKIP_HERTZON; then
  step "Hertzon (EMerge FEM simulator + MCP)"
  PY=python3; command -v python3.13 >/dev/null && PY=python3.13
  $SUDO env PYTHON="$PY" bash tools/install_hertzon.sh
  $SUDO chown -R "$ME" /opt/hertzon-venv /opt/src/Hertzon
fi

if ! skip SKIP_EXTRAS; then
  step "Extras: gds2openEMS, KiCadRoutingTools, Playwright (PDF reports), Octave"
  [ -x /opt/openEMS/venv/bin/python ] && { $SUDO bash tools/install_gds2openems.sh || echo "gds2openEMS failed (optional)"; }
  [ -d /opt/KiCadRoutingTools ] || $SUDO sh tools/install_krt.sh || echo "KiCadRoutingTools failed (optional)"
  node -e "require('playwright')" 2>/dev/null || { $SUDO npm install -g playwright && $SUDO npx -y playwright install --with-deps chromium; } || echo "Playwright failed (optional)"
  command -v octave >/dev/null || DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq octave || true
fi

step "Git identity and GitHub login (needed to push)"
git config --global user.name  >/dev/null || echo "  set it:  git config --global user.name  \"Your Name\""
git config --global user.email >/dev/null || echo "  set it:  git config --global user.email \"you@example.com\""
gh auth status >/dev/null 2>&1 || echo "  log in:  gh auth login   (GitHub.com, HTTPS, login with a web browser), then: gh auth setup-git"

step "Checking everything"
NODE_PATH="$(npm root -g)" python3 tools/doctor.py || true
echo
echo "Done. Start Claude Code in the repo with:  cd $ROOT && claude"
