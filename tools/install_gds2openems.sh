#!/usr/bin/env bash
# Install gds2openEMS (GDSII -> openEMS FDTD workflow, https://github.com/VolkerMuehlhaus/gds2openEMS)
# on top of a headless openEMS/CSXCAD build. Ubuntu 24.04 has no openEMS apt package, so openEMS
# is built from the official superbuild if it is not importable yet (~20 min on 4 cores).
# Verified 2026-10-16 on Ubuntu 24.04 / Python 3.13: openEMS v0.37.0 + gds2openEMS 0.5.0,
# workflow/run_line_viaport.py runs headless in ~55 s (~270 MCells/s), S11 < -29 dB to 110 GHz.
#
#   sudo bash tools/install_gds2openems.sh        # default prefix /opt/openEMS
#   OPENEMS_PREFIX=$HOME/opt/openEMS bash tools/install_gds2openems.sh
#
# Afterwards: source /opt/openEMS/venv/bin/activate ; python -c "from gds2openEMS import *"
set -euo pipefail

PREFIX="${OPENEMS_PREFIX:-/opt/openEMS}"
SRC="${OPENEMS_SRC:-/opt/src/openEMS-Project}"
REF="${OPENEMS_REF:-v0.37.0}"
G2O_REPO="${G2O_REPO:-$HOME/gds2openEMS}"     # examples + IHP SG13G2 stackups
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

# 1) openEMS + CSXCAD Python bindings (headless, no AppCSXCAD GUI)
if [ -x "$PREFIX/venv/bin/python" ] && "$PREFIX/venv/bin/python" -c "import openEMS, CSXCAD" 2>/dev/null; then
  echo "openEMS already installed in $PREFIX"
else
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq \
    build-essential cmake git libhdf5-dev libvtk9-dev libboost-all-dev \
    libcgal-dev libtinyxml-dev python3-dev
  if [ ! -d "$SRC/.git" ]; then
    $SUDO mkdir -p "$(dirname "$SRC")"
    $SUDO git clone --recursive --branch "$REF" https://github.com/thliebig/openEMS-Project.git "$SRC"
  fi
  (cd "$SRC" && $SUDO ./update_openEMS.sh "$PREFIX" --disable-GUI --python \
      --python-venv-mode=site --njobs="$(nproc)")
fi

# 2) gds2openEMS module (pulls gdspy, shapely, matplotlib, PySide6 for stackupEditor)
$SUDO "$PREFIX/venv/bin/pip" install -q --upgrade gds2openEMS
"$PREFIX/venv/bin/python" -c "from gds2openEMS import *; import gdspy, CSXCAD, openEMS; print('gds2openEMS OK')"

# 3) Examples and technology stackups
[ -d "$G2O_REPO/.git" ] || git clone -q https://github.com/VolkerMuehlhaus/gds2openEMS "$G2O_REPO"
echo "Done. Examples: $G2O_REPO/workflow  (headless: set settings['no_gui'] = True)"
