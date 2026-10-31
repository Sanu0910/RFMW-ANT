#!/bin/bash
# start one detached as-built element run with a parasitic size / air gap: _psweep_wsl.sh par gap port
cd /root/p15/02_openems; source /opt/openEMS/venv/bin/activate
t=ps_${1}_${2}_p${3}
setsid nohup python sim_element_fix.py --variant asbuilt --port $3 --par $1 --gap $2 --tag $t --res 0.4 > log_$t.txt 2>&1 < /dev/null &
sleep 2
