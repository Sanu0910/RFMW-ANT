"""Simulator-style plots of the L-band (L1 + L2/L5) results for the internal technical note.
Reads Touchstone/SIM_System_3port.s3p, SIM_Branch_*.s2p, Extracted_Data/results_sweep.csv and the
component Touchstone files; writes Images/lband_*.png.
"""
from pathlib import Path

import numpy as np
import skrf as rf

import models as M
import aedt_style as A

ROOT = Path(__file__).resolve().parent.parent
TS, IMG, XD = ROOT / "Touchstone", ROOT / "Images", ROOT / "Extracted_Data"
DESIGN = "FrontEnd_3port"
SETUP = "SP_0p6_2p2GHz : Sweep"


def db(x):
    return 20 * np.log10(np.abs(x) + 1e-30)


def main():
    s3 = rf.Network(str(TS / "SIM_System_3port.s3p"))
    f = s3.f / 1e9
    s = s3.s
    sw = np.genfromtxt(XD / "results_sweep.csv", delimiter=",", names=True)
    nf1, nf2 = sw["NF_L1_dB"], sw["NF_L2L5_dB"]
    gd1, gd2 = sw["GD_L1_ns"], sw["GD_L2L5_ns"]
    E = {"S31": "dB(S(P3_RF_OUT,P1_L1_RHCP))", "S32": "dB(S(P3_RF_OUT,P2_L2L5_RHCP))",
         "S11": "dB(S(P1_L1_RHCP,P1_L1_RHCP))", "S22": "dB(S(P2_L2L5_RHCP,P2_L2L5_RHCP))",
         "S33": "dB(S(P3_RF_OUT,P3_RF_OUT))", "S13": "dB(S(P1_L1_RHCP,P3_RF_OUT))",
         "S23": "dB(S(P2_L2L5_RHCP,P3_RF_OUT))", "S21": "dB(S(P2_L2L5_RHCP,P1_L1_RHCP))"}

    def tr(sel, i, j, key):
        return dict(x=f[sel], y=db(s[sel, i, j]), expr=E[key], setup=SETUP, short=key)

    b1 = (f >= 1.53) & (f <= 1.64)
    A.xy_plot(IMG / "lband_sparams_L1.png", "XY Plot 1 - L1 branch S-parameters", DESIGN,
              [tr(b1, 2, 0, "S31"), tr(b1, 0, 0, "S11"), tr(b1, 2, 2, "S33"), tr(b1, 0, 2, "S13")],
              ylabel="Y1 [dB]", markers=[("m1", 1.57542, 0), ("m2", 1.5611, 0), ("m3", 1.602, 0),
                                         ("m4", 1.57542, 1), ("m5", 1.57542, 2)], ylim=(-90, 50),
              spans=[(1.55905, 1.56315, ""), (1.5744, 1.5764, ""), (1.5975, 1.6059, "")])
    b2 = (f >= 1.13) & (f <= 1.28)
    A.xy_plot(IMG / "lband_sparams_L2L5.png", "XY Plot 2 - L2/L5 branch S-parameters", DESIGN,
              [tr(b2, 2, 1, "S32"), tr(b2, 1, 1, "S22"), tr(b2, 2, 2, "S33"), tr(b2, 1, 2, "S23")],
              ylabel="Y1 [dB]", markers=[("m1", 1.17645, 0), ("m2", 1.20714, 0), ("m3", 1.2276, 0),
                                         ("m4", 1.17645, 1), ("m5", 1.17645, 2)], ylim=(-90, 50),
              spans=[(1.16622, 1.18668, ""), (1.1971, 1.2171, ""), (1.22658, 1.22862, "")])
    A.xy_plot(IMG / "lband_wideband.png", "XY Plot 3 - Wide-band transmission", DESIGN,
              [dict(x=f, y=db(s[:, 2, 0]), expr=E["S31"], setup=SETUP, short="S31"),
               dict(x=f, y=db(s[:, 2, 1]), expr=E["S32"], setup=SETUP, short="S32"),
               dict(x=f, y=db(s[:, 1, 0]), expr=E["S21"], setup=SETUP, short="P1-P2")],
              ylabel="Y1 [dB]", markers=[("m1", 1.15, 1), ("m2", 1.621, 0), ("m3", 1.7475, 0), ("m4", 0.8975, 1)],
              ylim=(-160, 50))
    g1 = (f >= 1.55) & (f <= 1.615)
    g2 = (f >= 1.15) & (f <= 1.26)
    A.xy_plot(IMG / "lband_gain.png", "XY Plot 4 - Gain in the GNSS bands", DESIGN,
              [dict(x=f[g2], y=db(s[g2, 2, 1]), expr=E["S32"], setup=SETUP, short="S32"),
               dict(x=f[g1], y=db(s[g1, 2, 0]), expr=E["S31"], setup=SETUP, short="S31")],
              ylabel="Gain [dB]", markers=[("m1", 1.17645, 0), ("m2", 1.20714, 0), ("m3", 1.2276, 0),
                                           ("m4", 1.248, 0), ("m5", 1.5611, 1), ("m6", 1.57542, 1),
                                           ("m7", 1.602, 1)], ylim=(20, 50))
    A.xy_plot(IMG / "lband_nf.png", "XY Plot 5 - Noise figure", DESIGN,
              [dict(x=f[g2], y=nf2[g2], expr="NF(P3_RF_OUT,P2_L2L5_RHCP)", setup=SETUP, short="NF L2/L5"),
               dict(x=f[g1], y=nf1[g1], expr="NF(P3_RF_OUT,P1_L1_RHCP)", setup=SETUP, short="NF L1")],
              ylabel="NF [dB]", markers=[("m1", 1.17645, 0), ("m2", 1.2276, 0), ("m3", 1.57542, 1)], ylim=(0, 2))
    vs = lambda x: (1 + abs(x)) / (1 - abs(x))
    bb = (f >= 1.1) & (f <= 1.65)
    A.xy_plot(IMG / "lband_vswr.png", "XY Plot 6 - VSWR", DESIGN,
              [dict(x=f[bb], y=vs(s[bb, 0, 0]), expr="VSWR(P1_L1_RHCP)", setup=SETUP, short="P1"),
               dict(x=f[bb], y=vs(s[bb, 1, 1]), expr="VSWR(P2_L2L5_RHCP)", setup=SETUP, short="P2"),
               dict(x=f[bb], y=vs(s[bb, 2, 2]), expr="VSWR(P3_RF_OUT)", setup=SETUP, short="P3")],
              ylabel="VSWR", markers=[("m1", 1.57542, 0), ("m2", 1.17645, 1), ("m3", 1.20714, 1),
                                      ("m4", 1.57542, 2), ("m5", 1.17645, 2)], ylim=(1, 4))
    n1 = rf.Network(str(TS / "SIM_Branch_L1.s2p")); n2 = rf.Network(str(TS / "SIM_Branch_L2L5.s2p"))
    k1, mu1, _, _ = M.k_mu(n1); k2, mu2, _, _ = M.k_mu(n2)
    A.xy_plot(IMG / "lband_stability.png", "XY Plot 7 - Stability", DESIGN,
              [dict(x=n1.f / 1e9, y=mu1, expr="Mu1 (L1 branch)", setup=SETUP, short="Mu L1"),
               dict(x=n2.f / 1e9, y=mu2, expr="Mu1 (L2/L5 branch)", setup=SETUP, short="Mu L2/L5"),
               dict(x=n1.f / 1e9, y=np.clip(k1, 0, 50), expr="StabilityFactor K (L1 branch)", setup=SETUP, short="K L1")],
              ylabel="K, Mu", markers=[("m1", 1.57542, 0), ("m2", 1.17645, 1)], ylim=(0, 10), hlines=[(1, "= 1")])
    A.xy_plot(IMG / "lband_group_delay.png", "XY Plot 8 - Group delay", DESIGN,
              [dict(x=f[g2], y=gd2[g2], expr="GroupDelay(P3_RF_OUT,P2_L2L5_RHCP) [ns]", setup=SETUP, short="GD L2/L5"),
               dict(x=f[g1], y=gd1[g1], expr="GroupDelay(P3_RF_OUT,P1_L1_RHCP) [ns]", setup=SETUP, short="GD L1")],
              ylabel="Group delay [ns]", markers=[("m1", 1.17645, 0), ("m2", 1.2276, 0), ("m3", 1.57542, 1)],
              ylim=(0, 120))
    k0 = lambda fx: int(np.argmin(abs(f - fx)))
    rej1 = db(s[k0(1.57542), 2, 0]) - db(s[:, 2, 0])
    rej2 = db(s[k0(1.17645), 2, 1]) - db(s[:, 2, 1])
    A.xy_plot(IMG / "lband_rejection.png", "XY Plot 9 - Rejection (dBc)", DESIGN,
              [dict(x=f, y=-rej1, expr="S31 rel. 1575.42 MHz", setup=SETUP, short="L1"),
               dict(x=f, y=-rej2, expr="S32 rel. 1176.45 MHz", setup=SETUP, short="L2/L5")],
              ylabel="Rejection [dBc]", markers=[("m1", 1.15, 1), ("m2", 1.621, 0), ("m3", 0.8975, 1),
                                                ("m4", 1.7475, 0)], ylim=(-160, 5),
              hlines=[(-80, "practical limit ~60-80 dBc")],
              spans=[(0.96, 1.15, "DME"), (1.616, 1.6265, "Iridium"), (1.71, 1.785, "LTE B3 UL")])
    sm = (f >= 1.1) & (f <= 1.65)
    A.smith_plot(IMG / "lband_smith.png", "Smith Plot 1 - Port reflections", DESIGN,
                 [dict(g=s[sm, 0, 0], f=f[sm], expr="S(P1_L1_RHCP,P1_L1_RHCP)", setup=SETUP, short="S11"),
                  dict(g=s[sm, 1, 1], f=f[sm], expr="S(P2_L2L5_RHCP,P2_L2L5_RHCP)", setup=SETUP, short="S22"),
                  dict(g=s[sm, 2, 2], f=f[sm], expr="S(P3_RF_OUT,P3_RF_OUT)", setup=SETUP, short="S33")],
                 markers=[("m1", 1.57542, 0), ("m2", 1.17645, 1), ("m3", 1.57542, 2)])
    # component models
    for fn, title, rng, mks in (("B7504.s2p", "XY Plot 10 - B7504 model (S2P)", (1.4, 1.8), [1.5591, 1.57542, 1.6059]),
                                ("B8889_matched.s2p", "XY Plot 11 - B8889 model incl. 6.8 nH (S2P)", (1.0, 1.4),
                                 [1.16622, 1.20714, 1.22862])):
        n = rf.Network(str(TS / fn)); ff = n.f / 1e9; sel = (ff >= rng[0]) & (ff <= rng[1])
        A.xy_plot(IMG / f"lband_{fn.split('.')[0].lower()}.png", title, fn,
                  [dict(x=ff[sel], y=db(n.s[sel, 1, 0]), expr="dB(S(2,1))", setup="Touchstone model", short="S21"),
                   dict(x=ff[sel], y=db(n.s[sel, 0, 0]), expr="dB(S(1,1))", setup="Touchstone model", short="S11"),
                   dict(x=ff[sel], y=db(n.s[sel, 1, 1]), expr="dB(S(2,2))", setup="Touchstone model", short="S22")],
                  ylabel="dB", markers=[(f"m{i + 1}", x, 0) for i, x in enumerate(mks)], ylim=(-70, 2))
    n = rf.Network(str(TS / "DXP02A.s3p")); ff = n.f / 1e9
    A.xy_plot(IMG / "lband_dxp02a.png", "XY Plot 12 - DXP.02.A model (S3P)", "DXP02A.s3p",
              [dict(x=ff, y=db(n.s[:, 1, 0]), expr="dB(S(2,1)) common-L1", setup="Touchstone model", short="S21"),
               dict(x=ff, y=db(n.s[:, 2, 0]), expr="dB(S(3,1)) common-L2/L5", setup="Touchstone model", short="S31"),
               dict(x=ff, y=db(n.s[:, 2, 1]), expr="dB(S(3,2)) isolation", setup="Touchstone model", short="S32"),
               dict(x=ff, y=db(n.s[:, 0, 0]), expr="dB(S(1,1))", setup="Touchstone model", short="S11")],
              ylabel="dB", markers=[("m1", 1.58219, 0), ("m2", 1.20692, 1), ("m3", 1.57542, 2)], ylim=(-70, 2))
    n = rf.Network(str(TS / "HC125A.s4p")); ff = n.f / 1e9; sel = (ff >= 1.15) & (ff <= 1.63)
    A.xy_plot(IMG / "lband_hc125a.png", "XY Plot 13 - HC125A model (S4P)", "HC125A.s4p",
              [dict(x=ff[sel], y=db(n.s[sel, 3, 0]), expr="dB(S(4,1)) through", setup="Touchstone model", short="S41"),
               dict(x=ff[sel], y=db(n.s[sel, 2, 0]), expr="dB(S(3,1)) coupled", setup="Touchstone model", short="S31"),
               dict(x=ff[sel], y=db(n.s[sel, 1, 0]), expr="dB(S(2,1)) isolated", setup="Touchstone model", short="S21"),
               dict(x=ff[sel], y=db(n.s[sel, 0, 0]), expr="dB(S(1,1))", setup="Touchstone model", short="S11")],
              ylabel="dB", markers=[("m1", 1.17645, 0), ("m2", 1.57542, 0), ("m3", 1.57542, 2)], ylim=(-50, 0))


if __name__ == "__main__":
    main()
    print("L-band simulator-style plots written")
