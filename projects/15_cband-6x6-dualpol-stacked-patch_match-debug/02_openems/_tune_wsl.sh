#!/bin/bash
# usage: _tune_wsl.sh tag "k=v,..." [extra args]   (sync sim_tune.py and start one detached run, 4 threads)
cd /root/p15/02_openems
sed 's/\r$//' /mnt/e/git/RFMW-ANT/projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems/sim_tune.py > sim_tune.py
sed 's/\r$//' /mnt/e/git/RFMW-ANT/projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems/tune_match.py > tune_match.py
source /opt/openEMS/venv/bin/activate
tag=$1; set=$2; shift 2
setsid nohup python sim_tune.py --tag "$tag" --set "$set" "$@" > "log_$tag.txt" 2>&1 < /dev/null &
sleep 2
