#!/bin/bash
# fix-B circuit design for several minimum line widths; keeps one result file per width
bash /root/sync.sh >/dev/null
cd /root/p15/02_openems; source /opt/openEMS/venv/bin/activate
for w in 0 0.5 0.73; do
  python fixb_design.py --wmin $w | head -6
  cp ../03_results/fixb_design.txt ../03_results/fixb_design_wmin$w.txt
done
