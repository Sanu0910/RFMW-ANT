#!/bin/bash
# copy every .py of 02_openems from the repository into the WSL run folder (CRLF stripped)
src=/mnt/e/git/RFMW-ANT/projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems
for f in "$src"/*.py; do sed 's/\r$//' "$f" > "/root/p15/02_openems/$(basename "$f")"; done
echo synced $(ls "$src"/*.py | wc -l) files
