#!/bin/bash
# usage: _batch_wsl.sh tag "k=v,..." [extra args]   (one detached wideband-element run, 4 threads, single-pol)
cd /root/p15/02_openems
source /opt/openEMS/venv/bin/activate
tag=$1; set=$2; shift 2
setsid nohup python sim_wb_element.py --single --no-nf2ff --res 0.5 --threads 4 --tag "$tag" --set "G=50,$set" "$@" > "log_$tag.txt" 2>&1 < /dev/null &
