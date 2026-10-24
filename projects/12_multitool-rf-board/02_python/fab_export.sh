#!/bin/sh
# Export the fab package (Gerbers, Excellon drill, CPL) from a routed board via kicad-cli.
# Usage: run inside the KiCad 9 chroot; arg1 = board, arg2 = output 03_fab dir.
set -e
BRD="$1"; OUT="$2"
mkdir -p "$OUT/gerbers"
kicad-cli pcb export gerbers --output "$OUT/gerbers/" \
  --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --no-protel-ext "$BRD"
kicad-cli pcb export drill --output "$OUT/gerbers/" --format excellon \
  --drill-origin absolute --excellon-units mm --generate-map --map-format gerberx2 "$BRD"
kicad-cli pcb export pos --output "$OUT/NOVA-RF1_CPL.csv" --format csv --units mm --side both "$BRD"
( cd "$OUT/gerbers" && zip -q -r ../NOVA-RF1_gerbers.zip . )
echo "fab package written to $OUT"
