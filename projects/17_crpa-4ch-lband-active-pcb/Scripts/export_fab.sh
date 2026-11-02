#!/usr/bin/env bash
# Fabrication outputs from KiCad/CRPA17_4CH_LBAND.kicad_pcb (run after build_pcb.py + run_drc.sh).
#   Fab/Gerbers/         Gerber X2 (4 Cu, mask, paste, silk, edge) + Excellon PTH/NPTH + drill map
#   Fab/CRPA17_4CH_LBAND_Gerbers.zip
#   Fab/CRPA17_4CH_LBAND_CPL_bottom.csv   pick-and-place (all SMD parts are on the bottom)
#   Fab/CRPA17_4CH_LBAND.d356             IPC-D-356 netlist for bare-board electrical test
#   Docs/CRPA17_layers.pdf                one page per layer
#   Images/render_top.png, render_bottom.png
set -e
cd "$(dirname "$0")/.."
KI="${KICAD10:-/c/Program Files/KiCad/10.0}/bin/kicad-cli.exe"
PCB=KiCad/CRPA17_4CH_LBAND.kicad_pcb
rm -rf Fab/Gerbers && mkdir -p Fab/Gerbers Docs Images
"$KI" pcb export gerbers --output Fab/Gerbers/ \
  --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
  --subtract-soldermask --use-drill-file-origin "$PCB" >/dev/null
"$KI" pcb export drill --output Fab/Gerbers/ --format excellon --excellon-separate-th \
  --generate-map --map-format gerberx2 --excellon-units mm "$PCB" >/dev/null
"$KI" pcb export pos --output Fab/CRPA17_4CH_LBAND_CPL_bottom.csv --format csv --units mm \
  --side back --exclude-dnp "$PCB" >/dev/null
"$KI" pcb export ipcd356 --output Fab/CRPA17_4CH_LBAND.d356 "$PCB" >/dev/null
"$KI" pcb export pdf --output Docs/CRPA17_layers.pdf --mode-multipage --scale 0 --include-border-title \
  --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,B.Silkscreen,F.Silkscreen" --common-layers "Edge.Cuts" "$PCB" >/dev/null
# In1.Cu as an image: GND plane + the per-channel +5V star traces from the single bias point
"$KI" pcb export pdf --output Docs/_in1.pdf --scale 0 --layers "In1.Cu,Edge.Cuts" "$PCB" >/dev/null
pdftoppm -r 90 -png -singlefile Docs/_in1.pdf Images/bias_star_In1Cu >/dev/null 2>&1 || true
rm -f Docs/_in1.pdf
for side in top bottom; do
  "$KI" pcb render --side $side -w 2000 -h 2000 --quality high --background opaque \
    -o Images/render_$side.png "$PCB" >/dev/null
done
(cd Fab && rm -f CRPA17_4CH_LBAND_Gerbers.zip && python -c "
import zipfile, pathlib
with zipfile.ZipFile('CRPA17_4CH_LBAND_Gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(pathlib.Path('Gerbers').iterdir()):
        z.write(f, f.name)
")
ls -la Fab Fab/Gerbers
