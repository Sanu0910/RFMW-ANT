#!/bin/sh
# Install KiCadRoutingTools (drandyhaas/KiCadRoutingTools) — a fast Rust-accelerated
# A* autorouter + functional-group placer for KiCad PCBs, with a CLI.
# MIT-licensed. See tools/KICAD_ROUTING.md for usage.
set -e

DEST=/opt/KiCadRoutingTools
VENV=/opt/krt-venv

# 1. Python deps in an isolated venv (PyPI, not repo code)
python3 -m venv "$VENV"
"$VENV/bin/pip" -q install --upgrade pip
"$VENV/bin/pip" -q install "numpy>=1.22" "scipy>=1.7" "shapely>=2.0" "Pillow>=10.1"

# 2. Get the code
if [ ! -d "$DEST" ]; then
  git clone --depth 1 https://github.com/drandyhaas/KiCadRoutingTools "$DEST"
fi

# 3. Build the Rust router (downloads a prebuilt binary; falls back to cargo build).
#    Needs a Rust toolchain only for the source fallback (cargo).
cd "$DEST"
"$VENV/bin/python" build_router.py

echo "KiCadRoutingTools ready at $DEST (venv: $VENV)."
echo "Test: $VENV/bin/python py_router/route.py kicad_files/cap_chain.kicad_pcb /tmp/r.kicad_pcb --nets '*'"
