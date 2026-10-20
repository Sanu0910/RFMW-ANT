#!/bin/sh
# place + RF + fan-out -> Freerouting -> SES import -> pours/stitching -> 3D models. Usage: KC=<kicad python wrapper> ./route_all.sh
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"
KC="${KC:-$HERE/../../../../tools/kicad-python-chroot.sh}"
FR="${FREEROUTING:-/opt/freerouting/freerouting-1.9.0.jar}"
run() { "$KC" "$HERE/make_pcb.py" "$@" 2>&1 | grep -v "memory leak"; }
run dsn | tail -3
(cd "$K" && xvfb-run -a java -jar "$FR" -de tracker_lite.dsn -do tracker_lite.ses -mp ${PASSES:-50} > freerouting.log 2>&1)
run ses; run finish; run models
