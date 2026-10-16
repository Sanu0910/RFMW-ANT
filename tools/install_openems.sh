#!/usr/bin/env bash
# Install openEMS (FDTD solver) + CSXCAD with Python bindings, headless (no AppCSXCAD GUI).
# Ubuntu 24.04 has no openEMS apt package, so this builds the official superbuild from source.
# Idempotent: exits early if openEMS is already importable. Takes ~10-20 min on 4 cores.
#
#   sudo bash tools/install_openems.sh            # default prefix /opt/openEMS
#   OPENEMS_PREFIX=$HOME/opt/openEMS bash tools/install_openems.sh
#
# Afterwards:  source /opt/openEMS/venv/bin/activate   (python: from openEMS import openEMS)
#              /opt/openEMS/bin/openEMS               (solver CLI)
set -euo pipefail

PREFIX="${OPENEMS_PREFIX:-/opt/openEMS}"
SRC="${OPENEMS_SRC:-/opt/src/openEMS-Project}"
REF="${OPENEMS_REF:-v0.37.0}"

if [ -x "$PREFIX/venv/bin/python" ] && \
   "$PREFIX/venv/bin/python" -c "import openEMS, CSXCAD" 2>/dev/null; then
  echo "openEMS already installed in $PREFIX"; exit 0
fi

SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
$SUDO apt-get update -qq
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq \
  build-essential cmake git libhdf5-dev libvtk9-dev libboost-all-dev \
  libcgal-dev libtinyxml-dev python3-dev python3-venv python3-numpy python3-matplotlib python3-h5py

if [ ! -d "$SRC/.git" ]; then
  $SUDO mkdir -p "$(dirname "$SRC")"
  $SUDO git clone --recursive --branch "$REF" https://github.com/thliebig/openEMS-Project.git "$SRC"
fi

cd "$SRC"
$SUDO ./update_openEMS.sh "$PREFIX" --disable-GUI --python --python-venv-mode=site --njobs="$(nproc)"

"$PREFIX/venv/bin/python" -c "import openEMS, CSXCAD; print('openEMS python OK')"
echo "Done. Activate with: source $PREFIX/venv/bin/activate"
