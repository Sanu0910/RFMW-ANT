#!/bin/sh
# full board build: lib -> place+dsn -> freerouting 2.1 -> ses -> finish -> patch loop. Logs to stdout.
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"
KC=/home/user/RFMW-ANT/tools/kicad-python-chroot.sh
KCLI=/home/user/RFMW-ANT/tools/kicad-cli-chroot.sh
PCB="$K/bps_switch.kicad_pcb"
python3 "$HERE/make_lib.py" >/dev/null
$KC "$HERE/make_pcb.py" dsn 2>&1 | grep -v "memory leak" | tail -3
rm -f "$K/bps_switch.ses"
(cd "$K" && timeout 450 xvfb-run -a java -jar /opt/freerouting/freerouting-2.1.0.jar -de bps_switch.dsn -do bps_switch.ses -mp 60 -dct 0 > /tmp/fr2.log 2>&1)
grep -iE "completed in" /tmp/fr2.log | tail -1
$KC "$HERE/make_pcb.py" ses 2>&1 | grep -v "memory leak"
$KC "$HERE/make_pcb.py" finish 2>&1 | grep -v "memory leak"
for i in $(seq 1 12); do
  $KCLI pcb drc --format json -o /tmp/drc.json "$PCB" >/dev/null 2>&1
  UC=$(python3 -c "import json;print(len(json.load(open('/tmp/drc.json')).get('unconnected_items',[])))")
  echo "patch iter $i: unconnected=$UC"
  [ "$UC" = "0" ] && break
  $KC "$HERE/make_pcb.py" patch 2>&1 | grep -v "memory leak" | grep -E "patched|failed"
done
echo "BUILD DONE"
