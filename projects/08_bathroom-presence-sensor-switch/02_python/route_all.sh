#!/bin/sh
# place+DSN -> Freerouting (mains + SELV) -> SES import -> pours/stitch/silk. Usage: ./route_all.sh [passes]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"
KC=/home/user/RFMW-ANT/tools/kicad-python-chroot.sh
FR=/opt/freerouting/freerouting-1.9.0.jar
P="${1:-40}"
"$KC" "$HERE/make_lib.py" >/dev/null 2>&1 || python3 "$HERE/make_lib.py"
"$KC" "$HERE/make_pcb.py" dsn 2>&1 | grep -v "memory leak" | tail -3
(cd "$K" && timeout 500 xvfb-run -a java -jar "$FR" -de bps_switch.dsn -do bps_switch.ses -mp "$P" > /tmp/fr.log 2>&1)
grep -iE "completed" /tmp/fr.log | tail -2
"$KC" "$HERE/make_pcb.py" ses 2>&1 | grep -v "memory leak"
"$KC" "$HERE/make_pcb.py" finish 2>&1 | grep -v "memory leak"
echo "route_all done"
