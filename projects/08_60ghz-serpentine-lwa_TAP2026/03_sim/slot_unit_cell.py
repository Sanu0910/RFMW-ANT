#!/usr/bin/env python3
"""Full-wave check of one inclined narrow-wall slot (Hertzon / EMerge FEM).

The paper derives slot tilt and depth for a wanted conductance g_n from CST unit-cell runs (its Fig. 4/5). This
script rebuilds that unit cell: a straight WR15 (a = 3.76, b = 1.88 mm, wall t = 0.2 mm) with one slot of
width 0.261 mm across the narrow wall, cut into both broad walls down to depth d_n, radiating into an air box
with an absorbing boundary. With the two waveguide ports it gives |S11|, |S21| and the radiated fraction
P_rad = 1 - |S11|^2 - |S21|^2. For a matched shunt slot y = g, P_rad = 4 g / (2 + g)^2, which is solved for g.

usage: slot_unit_cell.py [tilt_deg depth_mm] ...      default: the three points listed in CASES
Results: results/slot_<tilt>.json and results/slot_summary.csv
Metal is the background (PEC), as in HFSS: only air volumes are modelled.
"""
import csv
import json
import math
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("HERTZON_MCP_MODE", "file")      # work on the .hzn file, no GUI window
from hertzon.mcp import tools as T  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
A, B, TW, W = 3.76, 1.88, 0.20, 0.261
L = 12.0                       # guide length (mm)
F0 = "60.75GHz"
# (tilt, depth): depths from the paper's d_n(g_n) curve at the conductance its Fig. 4 gives for that tilt
CASES = [(10.0, 0.38), (20.0, 0.29), (30.0, 0.20)]
PAPER_G = {10.0: 0.018, 20.0: 0.075, 30.0: 0.16}    # read from paper Fig. 4 (approx.)


def build(tilt, depth):
    path = os.path.join(OUT, f"slot_{tilt:g}.hzn")
    base = {"project": path, "design": "slot"}
    if os.path.exists(path):
        os.remove(path)
    T.t_create_project({"path": path, "name": f"slot_{tilt:g}", "design": "slot", "units": "mm",
                        "solution_type": "Modal", "overwrite": True})

    def obj(kind, name, props, material="vacuum"):
        T.t_add_object(base | {"kind": kind, "name": name, "material": material, "props": props, "check": False})

    obj("CreateBox", "Guide", {"Position": f"{-B / 2},{-A / 2},{-L / 2}", "XSize": f"{B}", "YSize": f"{A}",
                               "ZSize": f"{L}"})
    lc = 2 * (B / 2 + TW + 0.3) / math.cos(math.radians(tilt))
    obj("CreateBox", "Slot", {"Position": f"{-lc / 2},{A / 2 - depth},{-W / 2}", "XSize": f"{lc}",
                              "YSize": f"{TW + depth + 0.4}", "ZSize": f"{W}"})
    T.t_add_operation(base | {"object": "Slot", "kind": "Rotate",
                              "props": {"Axis": "Y", "Angle": f"{tilt}deg", "Center": "0,0,0"}, "check": False})
    obj("CreateBox", "Outer", {"Position": f"-6,-6,{-L / 2}", "XSize": "12", "YSize": "13.5", "ZSize": f"{L}"})
    obj("CreateBox", "Metal", {"Position": f"{-B / 2 - TW},{-A / 2 - TW},{-L / 2}", "XSize": f"{B + 2 * TW}",
                               "YSize": f"{A + 2 * TW}", "ZSize": f"{L}"})
    T.t_add_operation(base | {"object": "Outer", "kind": "Subtract", "props": {"Tools": "Metal"}, "check": False})
    T.t_add_operation(base | {"object": "Guide", "kind": "Unite", "props": {"Tools": "Slot,Outer"}, "check": False})
    geo = T.t_get_geometry(base | {"objects": ["Guide"], "max_faces": 200})
    faces = geo["objects"]["Guide"]["faces"]
    ports, rad = [], []
    for fc in faces:
        c, nrm, area = fc["center"], fc["normal"], fc.get("area", 0)
        on_end = abs(abs(c[2]) - L / 2) < 1e-6 and abs(abs(nrm[2]) - 1) < 1e-6
        if on_end and abs(area - A * B) < 1e-3:
            ports.append((1 if c[2] < 0 else 2, fc["face"]))
        elif on_end or abs(abs(c[0]) - 6) < 1e-6 or abs(c[1] + 6) < 1e-6 or abs(c[1] - 7.5) < 1e-6:
            rad.append(fc["face"])
    for num, idx in sorted(ports):
        T.t_assign(base | {"category": "excitation", "kind": "Wave Port", "name": f"P{num}",
                           "faces": [{"object": "Guide", "face": idx}], "props": {"PortNumber": str(num)}})
    T.t_assign(base | {"category": "boundary", "kind": "Radiation", "name": "Rad",
                       "faces": [{"object": "Guide", "face": i} for i in rad]})
    # radiated power is a small difference (1 - |S21|^2), so start from a finer mesh. Checked for the 10-deg slot:
    # 5.5k tets -> P_rad 0.0062, 75k tets -> 0.0067; 0.8 mm keeps memory below ~6 GB on a 15-GB machine
    T.t_assign(base | {"category": "mesh_operation", "kind": "Length Based Inside Selection", "name": "Fine",
                       "objects": ["Guide"], "props": {"MaxLength": "0.8"}})
    T.t_set_setup(base | {"name": "Setup1", "props": {"Frequency": F0, "MaximumPasses": "6",
                                                       "MaximumDeltaS": "0.002", "MinimumPasses": "2",
                                                       "MinimumConvergedPasses": "2"},
                          "sweeps": [{"name": "Sweep", "props": {"SweepType": "Discrete",
                                                                  "Distribution": "Linear Count", "Start": "58GHz",
                                                                  "Stop": "63.5GHz", "Count": "3"}}]})
    return path, base, len(ports), len(rad)


def run(tilt, depth):
    path, base, npt, nrad = build(tilt, depth)
    if npt != 2:
        raise SystemExit(f"expected 2 port faces, found {npt}")
    val = T.t_validate(base)
    T.t_run_simulation(base | {"setup": "Setup1", "cores": 4})
    t0 = time.time()
    while True:
        st = T.t_get_status(base | {"setup": "Setup1", "wait_seconds": 60})
        state = st.get("state", st.get("status", ""))
        if state in ("done", "failed", "aborted") or time.time() - t0 > 3 * 3600:
            break
    res = T.t_get_results(base | {"setup": "Setup1", "kind": "sparameters", "params": ["S11", "S21"]})
    json.dump({"tilt": tilt, "depth": depth, "validate": val, "status": st, "sparams": res},
              open(os.path.join(OUT, f"slot_{tilt:g}.json"), "w"), indent=1, default=str)
    return st, res


def g_from_prad(p):
    # p = 4g/(2+g)^2  ->  p g^2 + (4p - 4) g + 4p = 0, small root
    a_, b_, c_ = p, 4 * p - 4, 4 * p
    return (-b_ - math.sqrt(max(b_ * b_ - 4 * a_ * c_, 0))) / (2 * a_) if p > 0 else 0.0


def summarise(cases):
    rows = []
    for tilt, depth in cases:
        d = json.load(open(os.path.join(OUT, f"slot_{tilt:g}.json")))
        for r in d["sparams"]["rows"]:
            s11 = 10 ** (r["S11_dB"] / 20)
            s21 = 10 ** (r["S21_dB"] / 20)
            prad = 1 - s11 ** 2 - s21 ** 2
            rows.append({"tilt_deg": tilt, "depth_mm": depth, "f_GHz": r["freq_GHz"], "S11_dB": r["S11_dB"],
                         "S21_dB": r["S21_dB"], "P_rad": round(prad, 5), "g_sim": round(g_from_prad(prad), 5),
                         "g_paper_fig4": PAPER_G.get(tilt, ""), "tets": d["status"].get("final_tets"),
                         "passes": len(d["status"].get("passes", []))})
    with open(os.path.join(OUT, "slot_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    cases = [(float(args[i]), float(args[i + 1])) for i in range(0, len(args), 2)] if args else CASES
    for tilt, depth in cases:
        st, res = run(tilt, depth)
        print(json.dumps({"tilt": tilt, "state": st.get("state"), "res": res}, default=str)[:1500])
    for r in summarise(cases):
        print(r)
