#!/bin/bash
# usage: _py_wsl.sh script.py args...   (sync the script from the repo, run it in the openEMS venv, foreground)
cd /root/p15/02_openems
src=/mnt/e/git/RFMW-ANT/projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems
sed 's/\r$//' "$src/$1" > "$1"
source /opt/openEMS/venv/bin/activate
python "$@"
