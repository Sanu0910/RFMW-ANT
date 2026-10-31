"""Independent cross-check of the system S-parameters with heavi (nodal Y-matrix solver).

Run with the repo venv (heavi lives there):  ..\\..\\..\\.venv\\Scripts\\python.exe crosscheck_heavi.py

Builds the same 3-port system as simulate.py, but from the Touchstone files in ../Touchstone
(so it also checks the files) and with heavi's own lumped elements for the bias network, then
compares S31 / S32 / S11 / S22 / S33 against ../Touchstone/SIM_System_3port.s3p.
"""
from pathlib import Path
import json

import numpy as np
import skrf as rf
import heavi as hv
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "Touchstone"
Z0 = 50.0

f = np.linspace(1.10e9, 1.65e9, 1101)


def sfuncs(net: rf.Network, cubic=False):
    """heavi wants S[i][j] as callables of frequency. Dense files: linear polar interpolation;
    the 200 MHz LNA table: cubic spline on dB / unwrapped phase (same rule as models.tqp_on)."""
    n = net.nports
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            fx = net.f
            mdb = 20 * np.log10(np.abs(net.s[:, i, j]))
            ph = np.unwrap(np.angle(net.s[:, i, j]))
            if cubic:
                cm, cp = CubicSpline(fx, mdb), CubicSpline(fx, ph)
                row.append(lambda ff, cm=cm, cp=cp: 10 ** (cm(ff) / 20) * np.exp(1j * cp(ff)))
            else:
                row.append(lambda ff, mdb=mdb, ph=ph, fx=fx:
                           10 ** (np.interp(ff, fx, mdb) / 20) * np.exp(1j * np.interp(ff, fx, ph)))
        out.append(row)
    return out


def const_s(m):
    return [[(lambda ff, v=v: np.full(np.shape(ff), v, complex)) for v in row] for row in m]


lna = rf.Network(str(TS / "TQP3M9037_5V.s2p"))
hc = rf.Network(str(TS / "HC125A.s4p"))
b7 = rf.Network(str(TS / "B7504.s2p"))
b8 = rf.Network(str(TS / "B8889_matched.s2p"))
dx = rf.Network(str(TS / "DXP02A.s3p"))

a = 1 / np.sqrt(2)
CP = [[0, 0, a, -1j * a], [0, 0, -1j * a, a], [a, -1j * a, 0, 0], [-1j * a, a, 0, 0]]

m = hv.Model()
g = m.gnd


def lna_stage(n_in, n_out):
    """Same parts and parasitics as models.BIAS, built from heavi's own R/L/C elements:
    100 pF (0.25 nH, 0.15 ohm) DC block -> LNA -> 18 nH choke (Q 40 @ 1.4 GHz, 0.12 pF across)
    to a 100 pF (0.4 nH, 0.1 ohm) bypass -> 100 pF DC block."""
    def dc_block(na, nb):
        x1, x2 = m.node(), m.node()
        m.capacitor(na, x1, 100e-12)
        m.inductor(x1, x2, 0.25e-9)
        m.resistor(x2, nb, 0.15)
    a1, a2, a3, a4, a5, a6 = (m.node() for _ in range(6))
    dc_block(n_in, a1)
    m.n_port_S(g, [a1, a2], sfuncs(lna, cubic=True), Z0)
    m.inductor(a2, a3, 18e-9)
    m.resistor(a3, a4, 2 * np.pi * 1.4e9 * 18e-9 / 40)
    m.capacitor(a2, a4, 0.12e-12)
    m.capacitor(a4, a5, 100e-12)
    m.inductor(a5, a6, 0.4e-9)
    m.resistor(a6, g, 0.1)
    dc_block(a2, n_out)


def branch(port_node, saw):
    c1, c2, c3, h1, h2 = (m.node() for _ in range(5))
    m.n_port_S(g, [port_node, c1, c2, c3], const_s(CP), Z0)
    m.resistor(c1, g, Z0)                      # LHCP termination
    m.n_port_S(g, [h1, h2, c2, c3], sfuncs(hc), Z0)
    m.resistor(h2, g, Z0)                      # hybrid isolated port
    s1i, s1o, s2i, s2o = (m.node() for _ in range(4))
    lna_stage(h1, s1i)
    m.n_port_S(g, [s1i, s1o], sfuncs(saw), Z0)
    lna_stage(s1o, s2i)
    m.n_port_S(g, [s2i, s2o], sfuncs(saw), Z0)
    return s2o


n1, n2, n3 = m.node(), m.node(), m.node()
p1 = m.new_port(Z0, n1)
p2 = m.new_port(Z0, n2)
o1 = branch(n1, b7)
o2 = branch(n2, b8)
m.n_port_S(g, [n3, o1, o2], sfuncs(dx), Z0)
p3 = m.new_port(Z0, n3)

S = m.run_sp(f)
ref = rf.Network(str(TS / "SIM_System_3port.s3p")).interpolate(rf.Frequency.from_f(f, unit="Hz"))


def db(x):
    return 20 * np.log10(np.abs(x))


report = {}
for name, hv_s, (i, j) in [("S31", S.S31, (2, 0)), ("S32", S.S32, (2, 1)), ("S11", S.S11, (0, 0)),
                            ("S22", S.S22, (1, 1)), ("S33", S.S33, (2, 2))]:
    d = db(hv_s) - db(ref.s[:, i, j])
    inband = ((f > 1.164e9) & (f < 1.230e9)) | ((f > 1.559e9) & (f < 1.606e9))
    report[name] = dict(max_abs_diff_db_inband=float(np.abs(d[inband]).max()),
                        mean_diff_db_inband=float(d[inband].mean()))
    print(name, report[name])
k = np.argmin(abs(f - 1575.42e6))
print("L1 gain heavi %.2f dB / skrf %.2f dB" % (db(S.S31[k]), db(ref.s[k, 2, 0])))
k5 = np.argmin(abs(f - 1176.45e6))
print("L5 gain heavi %.2f dB / skrf %.2f dB" % (db(S.S32[k5]), db(ref.s[k5, 2, 1])))
report["L1_gain_heavi_db"] = float(db(S.S31[k]))
report["L5_gain_heavi_db"] = float(db(S.S32[k5]))
(ROOT / "Extracted_Data" / "crosscheck_heavi.json").write_text(json.dumps(report, indent=1))
