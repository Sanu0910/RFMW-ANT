#!/bin/sh
# place + RF + fan-out -> Freerouting -> SES import -> pours/stitching -> 3D models. Usage: KC=<kicad python wrapper> ./route_all.sh
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"
KC="${KC:-$HERE/../../../../tools/kicad-python-chroot.sh}"
FR="${FREEROUTING:-/opt/freerouting/freerouting-1.9.0.jar}"
run() { "$KC" "$HERE/make_pcb.py" "$@" 2>&1 | grep -v "memory leak"; }
run dsn | tail -3
(cd "$K" && xvfb-run -a java -jar "$FR" -de tracker_lite.dsn -do tracker_lite.ses -mp ${PASSES:-50} > freerouting.log 2>&1)
run ses; run finish; run models
# DRC-driven finishing: patch open nets, drop dangling GND copper, merge vias, tie pour fragments, link islands
drc() { "$KCLI" pcb drc --schematic-parity --format json -o /tmp/drc.json "$K/tracker_lite.kicad_pcb" > /dev/null; }
KCLI="${KCLI:-kicad-cli}"
for i in 1 2 3; do drc; run patch; done
drc; run dangle; run merge; run tie; "$KC" "$HERE/gnd_link.py" 2>&1 | grep -E "patched|failed"
