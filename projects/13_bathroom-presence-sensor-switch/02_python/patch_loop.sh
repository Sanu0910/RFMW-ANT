#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"; K="$HERE/../01_kicad"
KC=/home/user/RFMW-ANT/tools/kicad-python-chroot.sh
KCLI=/home/user/RFMW-ANT/tools/kicad-cli-chroot.sh
PCB="$K/bps_switch.kicad_pcb"
for i in $(seq 1 15); do
  $KCLI pcb drc --format json -o /tmp/drc.json "$PCB" >/dev/null 2>&1
  UC=$(python3 -c "import json;print(len(json.load(open('/tmp/drc.json')).get('unconnected_items',[])))")
  echo "=== iter $i: unconnected=$UC ==="
  [ "$UC" = "0" ] && break
  $KC "$HERE/make_pcb.py" patch 2>&1 | grep -v "memory leak" | grep -E "patched|failed|island"
done
echo "patch_loop done"
