#!/bin/bash
# copy result files (CSVs, summaries, logs of the studies) from the WSL run folder back into the repository
src=/root/p15/03_results
dst=/mnt/e/git/RFMW-ANT/projects/15_cband-6x6-dualpol-stacked-patch_match-debug/03_results
cd $src
for f in wb* opt* match_wb* array_*; do [ -f "$f" ] && cp "$f" "$dst/"; done
ls $dst | wc -l
