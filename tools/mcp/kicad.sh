#!/bin/sh
# Launch the KiCad MCP server (KiCAD-MCP-Server) with a KiCad 9 Python that can import pcbnew.
# Used by .mcp.json, so the same entry works on a local machine and in a cloud container.
#   KICAD_MCP_DIR  server checkout (default /opt/KiCAD-MCP-Server)
#   KICAD_PYTHON   force a python; otherwise picked in this order:
#     1. $KICAD_MCP_DIR/venv/bin/python   (local install: venv with --system-site-packages over KiCad 9)
#     2. $KICAD_MCP_DIR/kicad-python-chroot.sh   (cloud install: KiCad image in /opt/kicad9, needs root)
#     3. python3
SRV="${KICAD_MCP_DIR:-/opt/KiCAD-MCP-Server}"
if [ ! -f "$SRV/dist/index.js" ]; then
  echo "kicad MCP: $SRV/dist/index.js not found - run tools/setup_local.sh (or set KICAD_MCP_DIR)" >&2
  exit 1
fi
if [ -z "$KICAD_PYTHON" ]; then
  if [ -x "$SRV/venv/bin/python" ] && "$SRV/venv/bin/python" -c "import pcbnew" 2>/dev/null; then
    KICAD_PYTHON="$SRV/venv/bin/python"
  elif [ -x "$SRV/kicad-python-chroot.sh" ] && [ "$(id -u)" -eq 0 ]; then
    KICAD_PYTHON="$SRV/kicad-python-chroot.sh"
  else
    KICAD_PYTHON=python3
  fi
fi
export KICAD_PYTHON
exec node "$SRV/dist/index.js"
