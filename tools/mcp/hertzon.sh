#!/bin/sh
# Launch the Hertzon (EMerge FEM) MCP server from its venv. Used by .mcp.json.
#   HERTZON_VENV  default /opt/hertzon-venv  (created by tools/install_hertzon.sh)
VENV="${HERTZON_VENV:-/opt/hertzon-venv}"
if [ ! -x "$VENV/bin/python" ]; then
  echo "hertzon MCP: $VENV not found - run tools/install_hertzon.sh (or set HERTZON_VENV)" >&2
  exit 1
fi
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
exec "$VENV/bin/python" -m hertzon.mcp
