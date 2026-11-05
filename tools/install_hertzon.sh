#!/usr/bin/env bash
# Install Hertzon (3D full-wave FEM EM simulator on EMerge, https://github.com/c8501024/Hertzon)
# into its own Python 3.13 virtual environment. Linux, ~1 GB download.
set -euo pipefail
SRC=${HERTZON_SRC:-/opt/src/Hertzon}
VENV=${HERTZON_VENV:-/opt/hertzon-venv}
PY=${PYTHON:-python3.13}          # Hertzon / EMerge 3 support Python 3.10-3.13

if [ ! -d "$SRC/.git" ]; then
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 https://github.com/c8501024/Hertzon.git "$SRC"
fi
[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -e "$SRC[test]"

# compile the solver kernels once with a small test solve (about a minute)
QT_QPA_PLATFORM=offscreen "$VENV/bin/python" -m hertzon.solver.warmup || \
  echo "warmup failed; kernels compile on the first solve instead"
echo "Hertzon installed: $("$VENV/bin/pip" show hertzon | grep ^Version)"
echo "GUI (needs a display; headless: xvfb-run): $VENV/bin/hertzon"
echo "Headless solve: $VENV/bin/python -m hertzon.solver.run Project.hzn Design Setup1 out_dir"
