#!/usr/bin/env bash
# Build the board, refill zones and run DRC (kicad-cli). Usage: bash run_drc.sh
set -e
cd "$(dirname "$0")"
KI="${KICAD10:-/c/Program Files/KiCad/10.0}"
"$KI/bin/python.exe" build_pcb.py
cd ../KiCad
"$KI/bin/kicad-cli.exe" pcb drc --refill-zones --save-board --severity-all --format json \
    -o ../Fab/_drc.json CRPA17_4CH_LBAND.kicad_pcb | tail -3
