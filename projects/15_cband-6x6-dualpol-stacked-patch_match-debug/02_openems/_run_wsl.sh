#!/bin/bash
# usage: _run_wsl.sh logname python-args...
cd /root/p15/02_openems
source /opt/openEMS/venv/bin/activate
log=$1; shift
setsid nohup python "$@" > "$log" 2>&1 < /dev/null &
echo started $log
