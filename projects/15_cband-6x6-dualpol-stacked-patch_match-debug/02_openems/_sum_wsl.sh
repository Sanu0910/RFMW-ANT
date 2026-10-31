#!/bin/bash
# usage: _sum_wsl.sh tag...   compact print of wideband-element summaries
cd /root/p15/03_results
for t in "$@"; do
  echo "== $t $(head -1 ${t}_summary.txt | grep -o '{.*}')"
  sed -n 2p ${t}_summary.txt
  awk 'NR>2 && /VSWR/ {printf "%s:%s ", $1, $6} END {print ""}' ${t}_summary.txt
  awk 'NR>2 && /Zin/ {printf "%s:%s%s ", $1, $(NF-1), $NF} END {print ""}' ${t}_summary.txt
done
