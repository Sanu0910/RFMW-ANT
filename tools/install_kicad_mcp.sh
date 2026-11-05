#!/usr/bin/env bash
# KiCad 9 + KiCAD-MCP-Server (github.com/mixelpixx/KiCAD-MCP-Server, stable) on a headless Ubuntu box
# without the KiCad PPA: unpacks the official kicad/kicad:9.0 Docker image as a rootfs (no Docker
# daemon needed) and runs KiCad's Python inside it through tools/kicad-python-chroot.sh.
# Verified 2026-10-17: KiCad 9.0.9, server 2.8.2, 244 tools, open_project / get_board_info OK.
# Needs root (chroot + bind mounts).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT=/opt/kicad9
SRV=/opt/KiCAD-MCP-Server

[ -x "$ROOT/usr/bin/kicad-cli" ] || python3 -I "$HERE/pull_docker_rootfs.py" kicad/kicad 9.0 "$ROOT"
[ -d "$SRV/.git" ] || git clone --branch stable https://github.com/mixelpixx/KiCAD-MCP-Server "$SRV"
(cd "$SRV" && npm install --no-fund --no-audit && npm run build)
# server python deps as cp311 wheels into the rootfs (the image has no pip)
pip install -q --target "$ROOT/opt/mcp-pylib" --python-version 3.11 --implementation cp --only-binary=:all: \
  --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 --platform manylinux_2_28_x86_64 \
  -r "$SRV/requirements.txt"
install -m 755 "$HERE/kicad-python-chroot.sh" "$SRV/kicad-python-chroot.sh"
mkdir -p "$ROOT/root/.config/kicad/9.0"
cp -n "$ROOT/usr/share/kicad/template/sym-lib-table" "$ROOT/usr/share/kicad/template/fp-lib-table" "$ROOT/root/.config/kicad/9.0/" || true
"$SRV/kicad-python-chroot.sh" -c "import pcbnew, kipy; print('KiCad', pcbnew.GetBuildVersion(), 'ready')"
cat <<EOM
Register with Claude Code (project .mcp.json or 'claude mcp add'):
  claude mcp add kicad -e KICAD_PYTHON=$SRV/kicad-python-chroot.sh -- node $SRV/dist/index.js
EOM
