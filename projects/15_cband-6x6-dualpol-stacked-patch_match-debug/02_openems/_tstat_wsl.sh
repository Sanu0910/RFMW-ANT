#!/bin/bash
# status of the sim_tune runs: running processes, last log line and summary presence per tag
ps -eo pid,etime,args | grep '[s]im_tune' | cut -c1-90
cd /root/p15/02_openems
for f in log_T*.txt; do echo "$f: $(grep Timestep $f | tail -1 | cut -c1-110)"; done
ls /root/p15/03_results/T*_summary.txt 2>/dev/null
