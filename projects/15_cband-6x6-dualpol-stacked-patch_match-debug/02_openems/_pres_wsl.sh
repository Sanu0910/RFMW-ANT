#!/bin/bash
# wait (max ~9.5 min) until N sweep summaries exist, then print them: _pres_wsl.sh N [pattern]
n=$1; pat=${2:-ps_*_summary.txt}
cd /root/p15/03_results
for i in $(seq 1 57); do
  [ "$(ls $pat 2>/dev/null | wc -l)" -ge "$n" ] && break
  sleep 10
done
for f in $(ls $pat 2>/dev/null); do echo "$f"; sed -n 2,4p "$f"; done
