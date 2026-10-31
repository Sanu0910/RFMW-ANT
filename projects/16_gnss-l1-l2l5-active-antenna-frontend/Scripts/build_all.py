"""Regenerate every output of project 16 in order.

    python build_all.py [--aedt]

1. simulate.py          Touchstone models, system simulation, plots, results CSV/JSON
   extra_rf.py          rejection, insertion loss, RL/isolation, output noise, XPD, SFDR, worst case
   sband.py             NavIC S-band branch (TA1442A, C2327J5003AHF) models, simulation, plots
   lband_aedt_plots.py  simulator-style L-band plots
2. build_extracted.py   extracted-parameter CSV/XLSX, assumptions log
3. make_schematics.py   schematic and connection-diagram images
4. crosscheck_heavi.py  heavi cross-check (runs with the repo .venv python, where heavi lives)
5. build_circuitrf.py   circuitRF netlist + CLI run + comparison
6. aedt_circuit.py      ANSYS AEDT Circuit project (only with --aedt; needs AEDT + licence)
7. make_report.py       PDF + DOCX report; make_internal_report.py  internal technical note
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VENV_PY = ROOT.parents[1] / ".venv" / "Scripts" / "python.exe"


def run(script, *args, py=sys.executable, required=True):
    print(f"== {script} {' '.join(args)}")
    r = subprocess.run([str(py), script, *args], cwd=HERE)
    if r.returncode and required:
        sys.exit(f"{script} failed ({r.returncode})")
    return r.returncode == 0


def compare_aedt():
    """Compare ANSYS_Project/AEDT_System_3port.s3p with the scikit-rf reference."""
    import skrf as rf
    f = ROOT / "ANSYS_Project" / "AEDT_System_3port.s3p"
    if not f.exists():
        return
    a = rf.Network(str(f))
    ref = rf.Network(str(ROOT / "Touchstone" / "SIM_System_3port.s3p")).interpolate(a.frequency)
    inb = ((a.f > 1.164e9) & (a.f < 1.230e9)) | ((a.f > 1.559e9) & (a.f < 1.606e9))
    rep = {}
    for nm, (i, j) in {"S31": (2, 0), "S32": (2, 1), "S11": (0, 0), "S22": (1, 1), "S33": (2, 2)}.items():
        d = 20 * np.log10(abs(a.s[:, i, j])) - 20 * np.log10(abs(ref.s[:, i, j]))
        rep[nm] = dict(max_abs_diff_db_inband=float(abs(d[inb]).max()))
    (ROOT / "Extracted_Data" / "crosscheck_aedt.json").write_text(json.dumps(rep, indent=1))
    print("AEDT vs reference:", rep)


if __name__ == "__main__":
    run("simulate.py")
    run("extra_rf.py")
    run("sband.py")
    run("lband_aedt_plots.py")
    run("build_extracted.py")
    run("make_schematics.py")
    if VENV_PY.exists():
        run("crosscheck_heavi.py", py=VENV_PY, required=False)
    run("build_circuitrf.py", required=False)
    if "--aedt" in sys.argv:
        run("aedt_circuit.py", required=False)
    compare_aedt()
    run("make_report.py")
    run("make_internal_report.py")
