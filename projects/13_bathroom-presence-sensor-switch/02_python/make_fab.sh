#!/bin/sh
# Fab + documentation outputs with kicad-cli (KiCad 9) through the chroot wrapper. Absolute paths (chroot cwd=/).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
K="$HERE/../01_kicad"; F="$HERE/../03_fab"; D="$HERE/../04_docs"; R="$HERE/../05_renders"
KCLI="${KCLI:-/home/user/RFMW-ANT/tools/kicad-cli-chroot.sh}"
PCB="$K/bps_switch.kicad_pcb"; SCH="$K/bps_switch.kicad_sch"; PN=SPS-24G-01
mkdir -p "$F/gerbers" "$R"; rm -f "$F/gerbers/"*
$KCLI pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
      --subtract-soldermask --use-drill-file-origin -o "$F/gerbers/" "$PCB"
$KCLI pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o "$F/gerbers/" "$PCB"
(cd "$F/gerbers" && rm -f "../${PN}_gerbers.zip" && zip -q "../${PN}_gerbers.zip" *)
$KCLI pcb export pos --side front --format csv --units mm -o "$F/${PN}_CPL_raw.csv" "$PCB"
python3 "$HERE/make_cpl.py"
$KCLI pcb export step --subst-models --no-dnp -f -o "$R/${PN}.step" "$PCB"
for s in top bottom; do $KCLI pcb render --side $s --width 1600 --height 1200 --quality high -o "$R/${PN}_3d_$s.png" "$PCB"; done
$KCLI pcb render --side top --perspective --rotate "-30,0,30" --width 1600 --height 1200 --quality high -o "$R/${PN}_3d_iso.png" "$PCB"
$KCLI pcb export pdf --layers F.Fab,F.Silkscreen,Edge.Cuts --mode-single -o "$D/${PN}_assembly_top.pdf" "$PCB"
$KCLI pcb export pdf --layers B.Fab,B.Silkscreen,Edge.Cuts --mirror --mode-single -o "$D/${PN}_assembly_bottom.pdf" "$PCB"
$KCLI sch export pdf -o "$D/${PN}_schematic.pdf" "$SCH"
echo "fab outputs done"
