#!/bin/sh
# Fab + documentation outputs with kicad-cli (KiCad 9). Usage: KCLI="<kicad-cli wrapper>" ./make_fab.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"; F="$HERE/../03_fab"; D="$HERE/../04_docs"; R="$HERE/../05_renders"
KCLI="${KCLI:-kicad-cli}"; PCB="$K/tracker_lite.kicad_pcb"; PN=CRL-TRK-2W-L1
mkdir -p "$F/gerbers" "$R"; rm -f "$F/gerbers/"*
$KCLI pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
      --subtract-soldermask --use-drill-file-origin -o "$F/gerbers/" "$PCB"
$KCLI pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o "$F/gerbers/" "$PCB"
(cd "$F/gerbers" && rm -f "../${PN}_gerbers.zip" && zip -q "../${PN}_gerbers.zip" *)
$KCLI pcb export pos --side front --format csv --units mm -o "$F/${PN}_CPL_raw.csv" "$PCB"
(cd "$HERE" && python3 make_cpl.py)
$KCLI pcb export step --subst-models --include-tracks --include-zones --no-dnp -f -o "$R/${PN}.step" "$PCB"
for s in top bottom; do $KCLI pcb render --side $s --width 1600 --height 1200 --quality high -o "$R/${PN}_3d_$s.png" "$PCB"; done
$KCLI pcb render --side top --rotate "-45,0,45" --zoom 0.9 --width 1600 --height 1200 --quality high -o "$R/${PN}_3d_iso.png" "$PCB"
$KCLI pcb export pdf --layers F.Fab,F.Courtyard,Edge.Cuts --mode-single -o "$D/${PN}_assembly_top.pdf" "$PCB"
$KCLI pcb export svg --layers F.Cu,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet -o "$R/copper_F.svg" "$PCB"
$KCLI pcb export svg --layers B.Cu,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet -o "$R/copper_B.svg" "$PCB"
$KCLI sch export pdf -o "$D/${PN}_schematic.pdf" "$K/tracker_lite.kicad_sch"
echo fab outputs done
