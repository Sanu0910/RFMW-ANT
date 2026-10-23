#!/usr/bin/env bash
# Install Backplane (agentic hardware-development workspace + KiCad fork, https://github.com/i2cjak/Backplane).
# Uses the upstream installer, which pins the release version and checks the archive's sha256. It installs
# into ~/.local/share/backplane, links ~/.local/bin/backplane(-serve), and needs no sudo.
set -euo pipefail
D=${BACKPLANE_DL:-/opt/dl/backplane}
mkdir -p "$D"
curl -fsSL -o "$D/install.sh" https://github.com/i2cjak/backplane-bend/releases/latest/download/install.sh
echo "--- installer (review before it runs) ---"; sed -n '1,20p' "$D/install.sh"
BACKPLANE_NO_DESKTOP=${BACKPLANE_NO_DESKTOP:-1} sh "$D/install.sh"
echo "Run headless (web UI on http://127.0.0.1:3787):"
echo "  BACKPLANE_NO_UPDATE=1 BACKPLANE_TELEMETRY=0 ~/.local/bin/backplane --headless"
