#!/usr/bin/env bash
# Regenerate every project-17 output from the scripts.
#   1. footprints (needs Input/Gerber_4CH_GNSS.zip; skipped if absent - CRPA17.pretty is committed)
#   2. board (KiCad 10 python) + zone fill + DRC (kicad-cli)
#   3. Gerbers, drill, CPL, IPC-D-356, layer PDF, renders
#   4. BOM, netlist, budgets, schematics, design report
# Override the KiCad install with KICAD10=/path/to/KiCad/10.0
set -e
cd "$(dirname "$0")"
if [ -f ../Input/Gerber_4CH_GNSS.zip ]; then python build_footprints.py >/dev/null; fi
bash run_drc.sh
bash export_fab.sh >/dev/null
python make_docs.py
