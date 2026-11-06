#!/usr/bin/env bash
# Build the main board, refill zones and run DRC (kicad-cli). Usage: bash 02_python/run_drc.sh
set -e
cd "$(dirname "$0")"
KI="${KICAD10:-/c/Program Files/KiCad/10.0}"
mkdir -p ../04_fab
"$KI/bin/python.exe" build_pcb.py
cd ../03_kicad
"$KI/bin/kicad-cli.exe" pcb drc --refill-zones --save-board --severity-all --format json \
    -o ../04_fab/_drc.json CRL-LS-CRPA4.kicad_pcb | tail -3
