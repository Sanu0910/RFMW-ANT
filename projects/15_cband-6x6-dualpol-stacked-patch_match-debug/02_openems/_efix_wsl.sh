#!/bin/bash
# start one detached sim_element_fix.py run: _efix_wsl.sh variant port [extra args]
cd /root/p15/02_openems; source /opt/openEMS/venv/bin/activate
v=$1; p=$2; shift 2
setsid nohup python sim_element_fix.py --variant $v --port $p "$@" > log_elemfix_${v}_p${p}.txt 2>&1 < /dev/null &
sleep 2
