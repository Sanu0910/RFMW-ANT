"""S-band (NavIC 2492.028 MHz) branch of the active antenna.

    S-band patch (dual feed, ideal) -> C2327J5003AHF 3 dB hybrid -> TQP3M9037 -> TA1442A
                                    -> TQP3M9037 -> TA1442A -> S-band RF out

LNA stages use the Qorvo 2300-2600 MHz reference design (TQP3M9037 data sheet p.10):
2.7 nH shunt + 2.4 pF series at the input, 5.6 nH choke + 100 pF DC block at the output, VDD +5 V.
Writes Touchstone (TA1442A.s2p, C2327J5003AHF.s4p, SIM_SBand_2port.s2p, ...), simulator-style plots
(Images/sband_*.png), Extracted_Data/sband_*.csv and Scripts/results_sband.json.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import skrf as rf
from scipy.interpolate import PchipInterpolator

import ds_data as D
import models as M
import aedt_style as A

ROOT = Path(__file__).resolve().parent.parent
TS, IMG, XD = ROOT / "Touchstone", ROOT / "Images", ROOT / "Extracted_Data"
FS = rf.Frequency(500, 4000, 7001, unit="MHz")          # 0.5 MHz step
FM = FS.f / 1e6
F0 = D.SBAND["f_mhz"]
DESIGN = "SBand_2port"
SETUP = "SP_SBand : Sweep"
k_B = 1.380649e-23


def db(x):
    return 20 * np.log10(np.abs(x) + 1e-30)


def idx(f):
    return int(np.argmin(abs(FM - f)))


# --------------------------------------------------------------------------------------
# component models
# --------------------------------------------------------------------------------------
def ta1442a(freq=M.F_SAW):
    return M.saw_filter("TA1442A", D.TA_ATT_DIG, D.TA_VSWR_DIG, D.TA_VSWR_OUT_DIG, freq)


def xinger(freq: rf.Frequency):
    """C2327J5003AHF as a 4-port: 1 = pin 1 input, 2 = pin 3 isolated, 3 = pin 6 coupled, 4 = pin 4 direct.
    Magnitudes from the excess IL and amplitude balance (|Sd|^2 + |Sc|^2 = 10^(-IL/10), |Sd/Sc| = AB),
    coupled phase = direct phase + 90 deg - phase balance; absolute phase -90 deg x f/2500 MHz [ASSUMED];
    reflection / isolation phases chosen for passivity (as for HC125A)."""
    p = np.array(D.XH_DIG, float)
    fm = freq.f / 1e6

    def col(c):
        return PchipInterpolator(p[:, 0], p[:, c])(np.clip(fm, p[0, 0], p[-1, 0]))

    rl, il, ab, pb, iso = (col(k) for k in range(1, 6))
    ptot = 10 ** (-il / 10)
    r_ab = 10 ** (ab / 20)
    sc = np.sqrt(ptot / (1 + r_ab ** 2))
    sd = sc * r_ab
    th = np.deg2rad(-90.0 * fm / 2500.0)
    T = sd * np.exp(1j * th)
    C = sc * np.exp(1j * (th + np.deg2rad(90 - pb)))
    R = 10 ** (-rl / 20)
    I_mag = 10 ** (-iso / 20)

    def build(pr, pi):
        s = np.zeros((freq.npoints, 4, 4), complex)
        for k in range(4):
            s[:, k, k] = R * np.exp(1j * (th + pr))
        I = I_mag * np.exp(1j * (th + pi))
        for (a, b), v in {(0, 1): I, (2, 3): I, (0, 3): T, (1, 2): T, (0, 2): C, (1, 3): C}.items():
            s[:, a, b] = s[:, b, a] = v
        return s

    best = None
    band_ = (fm >= 2000) & (fm <= 3000)       # optimise where the part is used (2.3-2.7 GHz rated)
    for pr in np.deg2rad(np.arange(0, 360, 5)):
        for pi in np.deg2rad(np.arange(0, 360, 5)):
            s = build(pr, pi)
            sm = np.linalg.svd(s[band_], compute_uv=False)[:, 0].max()
            if best is None or sm < best[0]:
                best = (sm, pr, pi)
    xinger.phase_offsets = (np.rad2deg(best[1]), np.rad2deg(best[2]), best[0])
    return rf.Network(frequency=freq, s=M.enforce_passive(build(best[1], best[2])), z0=M.Z0, name="C2327J5003AHF")


def lna_stage_s(freq):
    """Qorvo 2.3-2.6 GHz reference design (p.10) with [ASSUMED] part parasitics."""
    lshunt = M.shunt_z(freq, M.z_ind(freq, 2.7e-9, q_ref=30.0, f_qref=2.5e9, cpar=0.05e-12), "L2_2n7")
    cin = M.series_z(freq, M.z_cap(freq, 2.4e-12, 0.3e-9, 0.25), "C5_2p4")
    pre = lshunt ** cin
    lna = M.tqp_on(freq)
    choke = M.shunt_z(freq, M.z_ind(freq, 5.6e-9, q_ref=50.0, f_qref=2.5e9, cpar=0.08e-12) +
                      M.z_cap(freq, 100e-12, 0.4e-9, 0.1), "L1_5n6")
    cout = M.series_z(freq, M.z_cap(freq, 100e-12, 0.25e-9, 0.15), "C2_100p")
    post = choke ** cout
    return pre, lna, post, pre ** lna ** post


def on(n, freq, name):
    out = n.interpolate(freq, coords="polar", kind="cubic") if n.frequency != freq else n.copy()
    out.name = name
    return out


TA = ta1442a()
XH_FULL = xinger(rf.Frequency(500, 6000, 1376, unit="MHz"))
XH = on(XH_FULL, FS, "XH")
SAW = on(TA, FS, "SAW")
PRE, LNA, POST, STAGE = lna_stage_s(FS)
NF_MIN, G_OPT, RN = M.tqp_noise_on(FS)


def cp_feed_hyb():
    """virtual RHCP port -> hybrid output (pin 1). Patch feed A -> direct (pin 4), feed B -> coupled (pin 6),
    the orientation that combines coherently for this coupler's phase sign."""
    pi_, po = rf.circuit.Circuit.Port(FS, "in"), rf.circuit.Circuit.Port(FS, "out")
    cp = M.patch_cp_feed(FS); cp.name = "CPs"
    h = XH.copy(); h.name = "XHs"
    l1, l2 = M.load_z(FS, name="lhs"), M.load_z(FS, name="isos")
    return rf.circuit.Circuit([[(pi_, 0), (cp, 0)], [(cp, 1), (l1, 0)], [(cp, 2), (h, 3)], [(cp, 3), (h, 2)],
                               [(h, 1), (l2, 0)], [(h, 0), (po, 0)]]).network


def xpd_network():
    pr, pl, po = (rf.circuit.Circuit.Port(FS, n) for n in ("r", "l", "o"))
    cp = M.patch_cp_feed(FS); cp.name = "CPx"
    h = XH.copy(); h.name = "XHx"
    iso = M.load_z(FS, name="isx")
    return rf.circuit.Circuit([[(pr, 0), (cp, 0)], [(pl, 0), (cp, 1)], [(cp, 2), (h, 3)], [(cp, 3), (h, 2)],
                               [(h, 1), (iso, 0)], [(h, 0), (po, 0)]]).network


def write_ts(n, fname, header):
    n = n.copy(); n.name = n.name or fname[:-4]; n.frequency.unit = "ghz"
    txt = n.write_touchstone(return_string=True, form="ri", skrf_comment=False, format_spec_A="{:.7e}",
                             format_spec_B="{:.7e}", format_spec_freq="{:.9g}", write_noise=False)
    head = ["Project 16: active antenna, S-band (NavIC) branch (RFMW-ANT)",
            "Generated by Scripts/sband.py from Scripts/ds_data.py; format GHz / RI, Z0 = 50 ohm"] + header
    (TS / fname).write_text("\n".join(["! " + h for h in head] + txt.splitlines()) + "\n", encoding="ascii")


INTERF = [("LTE B40 (2300-2400)", 2350, -10), ("Wi-Fi ch 1", 2412, -10), ("Bluetooth / ISM", 2441, -20),
          ("Microwave oven", 2450, -30), ("Wi-Fi ch 13", 2472, -10), ("Globalstar DL (sat.)", 2490, -120),
          ("LTE B41 / n41 low", 2506, -10), ("LTE B7 UL", 2535, -10), ("LTE B41 / n41 mid", 2593, -10),
          ("LTE B7 DL", 2655, -30), ("GNSS L1 (other band)", 1575.42, -125), ("5G n78", 3500, -20)]
REJ_BANDS = [("LTE B40", 2300, 2400), ("Wi-Fi / BT ISM", 2400, 2483.5), ("Globalstar DL", 2483.5, 2500),
             ("LTE B41 / n41", 2496, 2690), ("LTE B7 UL", 2500, 2570), ("LTE B7 DL", 2620, 2690),
             ("LTE B1 DL", 2110, 2170), ("GNSS L-band", 1164, 1610), ("5G n78", 3300, 3800)]


def main():
    write_ts(TA, "TA1442A.s2p", [
        "ESTIMATED from " + D.TA_SOURCE + ": |S21| digitized from the VNA plots p.3 (marker values exact),",
        "VSWR from p.4; phase = minimum-phase reconstruction; arg S11 = arg S22 = arg S21 + 90 deg. NOT measured data."])
    write_ts(XH_FULL, "C2327J5003AHF.s4p", [
        "ESTIMATED from " + D.XH_SOURCE + " plots p.2-3. Ports: 1 = pin1 input, 2 = pin3 isolated,",
        "3 = pin6 coupled, 4 = pin4 direct. Absolute / reflection / isolation phase [ASSUMED]. 0.5-6 GHz."])
    write_ts(STAGE, "TQP3M9037_stage_SBand_refdesign.s2p", [
        "SIMULATED: Qorvo 2.3-2.6 GHz reference design (2.7 nH shunt, 2.4 pF series, 5.6 nH choke, 100 pF)",
        "around the TQP3M9037 5 V table; [ASSUMED] parasitics."])

    p1, p2 = rf.circuit.Circuit.Port(FS, "P1_S_RHCP"), rf.circuit.Circuit.Port(FS, "P2_S_OUT")
    cp = M.patch_cp_feed(FS); cp.name = "PATCH_S"
    h = XH.copy(); h.name = "HYB_S"
    lh, li = M.load_z(FS, name="R_LHCP"), M.load_z(FS, name="R_ISO")
    st1, st2 = STAGE.copy(), STAGE.copy(); st1.name, st2.name = "LNA_SA", "LNA_SB"
    f1, f2 = SAW.copy(), SAW.copy(); f1.name, f2.name = "SAW1_S", "SAW2_S"
    sysn = rf.circuit.Circuit([[(p1, 0), (cp, 0)], [(cp, 1), (lh, 0)], [(cp, 2), (h, 3)], [(cp, 3), (h, 2)],
                               [(h, 1), (li, 0)], [(h, 0), (st1, 0)], [(st1, 1), (f1, 0)], [(f1, 1), (st2, 0)],
                               [(st2, 1), (f2, 0)], [(f2, 1), (p2, 0)]]).network
    sysn.name = "SIM_SBand_2port"
    write_ts(sysn, "SIM_SBand_2port.s2p", ["SIMULATED S-band branch: port 1 = virtual RHCP input, port 2 = S-band RF out."])

    # noise
    hyb = cp_feed_hyb()
    ca_l = M.ca_active(NF_MIN, G_OPT, RN)
    blocks = [(hyb, M.ca_passive(hyb)), (PRE, M.ca_passive(PRE)), (LNA, ca_l), (POST, M.ca_passive(POST)),
              (SAW, M.ca_passive(SAW)), (PRE, M.ca_passive(PRE)), (LNA, ca_l), (POST, M.ca_passive(POST)),
              (SAW, M.ca_passive(SAW))]
    a, ca = M.cascade_noise(blocks)
    nf = 10 * np.log10(M.noise_factor(ca))
    s = sysn.s
    g = db(s[:, 1, 0])
    k0 = idx(F0)
    gd = -np.gradient(np.unwrap(np.angle(s[:, 1, 0])), 2 * np.pi * FS.f) * 1e9
    kk, mu, mu2, _ = M.k_mu(sysn)
    k_st, mu_st, _, _ = M.k_mu(STAGE)
    xn = xpd_network()
    xpd = db(xn.s[:, 2, 0]) - db(xn.s[:, 2, 1])
    rr = 10 ** (-xpd / 20)
    ar = 20 * np.log10((1 + rr) / (1 - rr))
    vs = lambda x: (1 + abs(x)) / (1 - abs(x))

    def band(lo, hi):
        return (FM >= lo) & (FM <= hi)

    sps, spec, rs = band(F0 - 1.023, F0 + 1.023), band(2489.5, 2494.5), band(F0 - 8.25, F0 + 8.25)
    # Friis cascade at F0 (50 ohm stages)
    eval_f = sorted(D.TQP_EVAL_5V)
    oip3 = float(np.interp(F0, eval_f, [D.TQP_EVAL_5V[f][4] for f in eval_f]))
    op1 = float(np.interp(F0, eval_f, [D.TQP_EVAL_5V[f][3] for f in eval_f]))
    lna_nf = float(10 * np.log10(M.noise_factor(M.cascade_noise(
        [(PRE, M.ca_passive(PRE)), (LNA, ca_l), (POST, M.ca_passive(POST))])[1]))[k0])
    stages = [("C2327J5003AHF (RHCP combine)", float(db(hyb.s[k0, 1, 0])), None),
              ("LNA1 TQP3M9037 (ref. design)", float(db(STAGE.s[k0, 1, 0])), lna_nf),
              ("TA1442A #1", float(db(SAW.s[k0, 1, 0])), None),
              ("LNA2 TQP3M9037 (ref. design)", float(db(STAGE.s[k0, 1, 0])), lna_nf),
              ("TA1442A #2", float(db(SAW.s[k0, 1, 0])), None)]
    bw = D.SBAND["bw_sps_mhz"] * 1e6
    nfloor = -174 + 10 * np.log10(bw)
    gl, fcum, iinv, pinv, budget = 1.0, 1.0, 0.0, 0.0, []
    for nm, gdb, nfx in stages:
        nfx = -gdb if nfx is None else nfx
        fcum += (10 ** (nfx / 10) - 1) / gl
        if "LNA" in nm:
            iinv += gl / 10 ** ((oip3 - gdb) / 10)
            pinv += gl / 10 ** ((op1 - gdb + 1) / 10)
        gl *= 10 ** (gdb / 10)
        gc, nfc = 10 * np.log10(gl), 10 * np.log10(fcum)
        budget.append(dict(stage=nm, gain_db=gdb, nf_db=nfx, cum_gain_db=gc, cum_nf_db=nfc,
                           cum_iip3_dbm=(10 * np.log10(1 / iinv) if iinv else None),
                           cum_iip1db_dbm=(10 * np.log10(1 / pinv) if pinv else None),
                           signal_dbm=D.SBAND["p_min_dbm"] + gc, noise_dbm=nfloor + nfc + gc))
    iip3, ip1 = budget[-1]["cum_iip3_dbm"], budget[-1]["cum_iip1db_dbm"]
    # interferers
    intf = []
    for nm, f, p in INTERF:
        k = idx(f)
        lv = [p + db(hyb.s[k, 1, 0])]
        for blk in (STAGE, SAW, STAGE, SAW):
            lv.append(lv[-1] + db(blk.s[k, 1, 0]))
        intf.append(dict(interferer=nm, f_mhz=f, p_ant_dbm=p, lna1_in=float(lv[0]), lna1_out=float(lv[1]),
                         saw1_out=float(lv[2]), lna2_out=float(lv[3]), rf_out=float(lv[4]),
                         lna1_backoff_db=float(op1 - lv[1]), lna2_backoff_db=float(op1 - lv[3]),
                         saw2_in_vs_10dbm_rating_db=float(10 - lv[3])))
    rej = g[k0] - g
    rejrows = [dict(band=n_, f_lo_mhz=lo, f_hi_mhz=hi, rej_min_dbc=float(rej[band(lo, hi)].min()),
                    rej_mean_dbc=float(rej[band(lo, hi)].mean())) for n_, lo, hi in REJ_BANDS]
    # filter vs spec
    fa = -db(TA.s[:, 1, 0]); ff = TA.f / 1e6
    tav = []
    for lo, hi, mn, typ in ((10, 2390, 33, 40), (2575, 3000, 43, 50)):
        sel = (ff >= lo) & (ff <= hi)
        tav.append(dict(item=f"TA1442A attenuation {lo}-{hi} MHz", spec_min=mn, spec_typ=typ, model=float(fa[sel].min())))
    sel = (ff >= 2489.5) & (ff <= 2494.5)
    tav.append(dict(item="TA1442A IL 2489.5-2494.5 MHz (mean)", spec_min=None, spec_typ=1.55, model=float(fa[sel].mean())))
    tav.append(dict(item="TA1442A ripple 2489.5-2494.5 MHz", spec_min=None, spec_typ=0.2, model=float(fa[sel].max() - fa[sel].min())))
    for fx, vv in ((2390, 46.73), (2575, 53.98), (2489.5, 1.558), (2494.5, 1.464)):
        tav.append(dict(item=f"TA1442A VNA marker {fx} MHz", spec_min=None, spec_typ=vv, model=float(fa[np.argmin(abs(ff - fx))])))
    xk = np.argmin(abs(XH_FULL.f / 1e6 - F0))
    xs = XH_FULL.s[xk]
    tav.append(dict(item="C2327J5003AHF excess IL @2492 MHz", spec_min=None, spec_typ=0.3,
                    model=float(-10 * np.log10(abs(xs[3, 0]) ** 2 + abs(xs[2, 0]) ** 2))))
    tav.append(dict(item="C2327J5003AHF isolation @2492 MHz", spec_min=18, spec_typ=22, model=float(-db(xs[1, 0]))))
    tav.append(dict(item="C2327J5003AHF return loss @2492 MHz", spec_min=15, spec_typ=18, model=float(-db(xs[0, 0]))))

    out_noise = 10 * np.log10(k_B * M.T0 * 10 ** (nf / 10) * abs(s[:, 1, 0]) ** 2 * 1e3)
    p_noise = 10 * np.log10(np.sum(10 ** (out_noise / 10)) * 0.5e6)
    summ = dict(
        f_mhz=F0, gain_db=float(g[k0]), ripple_sps_db=float(np.ptp(g[sps])), ripple_spec_band_db=float(np.ptp(g[spec])),
        ripple_rs_16p5MHz_db=float(np.ptp(g[rs])), nf_db=float(nf[k0]), te_k=float(M.T0 * (10 ** (nf[k0] / 10) - 1)),
        vswr_in=float(vs(s[k0, 0, 0])), vswr_out=float(vs(s[k0, 1, 1])), rl_in_db=float(-db(s[k0, 0, 0])),
        rl_out_db=float(-db(s[k0, 1, 1])), reverse_iso_db=float(-db(s[k0, 0, 1])),
        k_min=float(kk[band(600, 3900)].min()), mu_min=float(mu[band(600, 3900)].min()),
        stage_k_min=float(k_st.min()), stage_mu_min=float(mu_st.min()),
        gd_ns=float(gd[k0]), gd_ripple_sps_ns=float(np.ptp(gd[sps])), gd_ripple_rs_ns=float(np.ptp(gd[rs])),
        xpd_db=float(xpd[k0]), ar_db=float(ar[k0]), iip3_dbm=iip3, oip3_dbm=iip3 + float(g[k0]),
        ip1db_in_dbm=ip1, op1db_out_dbm=ip1 + float(g[k0]) - 1,
        sfdr_db=2 / 3 * (iip3 - (nfloor + float(nf[k0]))), cn0_dbhz=D.SBAND["p_min_dbm"] + 174 - float(nf[k0]),
        output_noise_dbm=float(p_noise), bw_3db_mhz=float(np.ptp(FM[g >= g[k0] - 3][[0, -1]])),
        hyb_phase_offsets=list(map(float, xinger.phase_offsets)))
    res = dict(summary=summ, budget=budget, interferers=intf, rejection=rejrows, validation=tav)
    (ROOT / "Scripts" / "results_sband.json").write_text(json.dumps(res, indent=1, default=float))
    for name, rows in (("sband_budget", budget), ("sband_interferers", intf), ("sband_rejection", rejrows),
                       ("sband_validation", tav)):
        with open(XD / f"results_{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(XD / "results_sband_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["parameter", "value"])
        for k, v in summ.items():
            w.writerow([k, v])

    # ---------------------------------------------------------------- simulator-style plots
    fg = FS.f / 1e9
    nb = band(2300, 2700)
    A.xy_plot(IMG / "sband_sparams.png", "XY Plot 1 - S-parameters", DESIGN,
              [dict(x=fg[nb], y=db(s[nb, 1, 0]), expr="dB(S(P2_S_OUT,P1_S_RHCP))", setup=SETUP, short="S21"),
               dict(x=fg[nb], y=db(s[nb, 0, 0]), expr="dB(S(P1_S_RHCP,P1_S_RHCP))", setup=SETUP, short="S11"),
               dict(x=fg[nb], y=db(s[nb, 1, 1]), expr="dB(S(P2_S_OUT,P2_S_OUT))", setup=SETUP, short="S22"),
               dict(x=fg[nb], y=db(s[nb, 0, 1]), expr="dB(S(P1_S_RHCP,P2_S_OUT))", setup=SETUP, short="S12")],
              ylabel="Y1 [dB]", markers=[("m1", F0 / 1e3, 0), ("m2", F0 / 1e3, 1), ("m3", F0 / 1e3, 2), ("m4", F0 / 1e3, 3),
                       ("m5", 2.39, 0), ("m6", 2.575, 0)],
              ylim=(-90, 50), spans=[(2.4895, 2.4945, "")])
    nb2 = band(2400, 2600)
    A.xy_plot(IMG / "sband_gain_inband.png", "XY Plot 2 - Gain, NavIC S band", DESIGN,
              [dict(x=fg[nb2], y=g[nb2], expr="dB(S(P2_S_OUT,P1_S_RHCP))", setup=SETUP, short="S21")],
              ylabel="dB(S(P2,P1))", markers=[("m1", 2.472, 0), ("m2", F0 / 1e3, 0), ("m3", 2.506, 0), ("m4", 2.45, 0),
                                              ("m5", 2.535, 0)],
              ylim=(0, 45), spans=[(2.4895, 2.4945, ""), (2.4, 2.4835, "Wi-Fi / ISM 2400-2483.5"),
                                   (2.496, 2.6, "LTE B41 / n41 from 2496")])
    A.xy_plot(IMG / "sband_wideband.png", "XY Plot 3 - Wide-band transmission", DESIGN,
              [dict(x=fg, y=g, expr="dB(S(P2_S_OUT,P1_S_RHCP))", setup=SETUP, short="S21")],
              ylabel="dB(S(P2,P1))", markers=[("m1", 2.39, 0), ("m2", F0 / 1e3, 0), ("m3", 2.575, 0)],
              ylim=(-100, 50))
    A.xy_plot(IMG / "sband_rejection.png", "XY Plot 4 - Rejection relative to 2492.028 MHz", DESIGN,
              [dict(x=fg, y=-rej, expr="dB(S(P2,P1)) - dB(S(P2,P1))@2.492GHz", setup=SETUP, short="rej.")],
              ylabel="Rejection [dBc]", markers=[("m1", 2.35, 0), ("m2", 2.472, 0), ("m3", 2.506, 0),
                                                ("m4", 2.593, 0)],
              ylim=(-140, 5), spans=[(lo / 1e3, hi / 1e3, nm) for nm, lo, hi in REJ_BANDS[:6]],
              hlines=[(-80, "practical limit ~60-80 dBc")])
    A.xy_plot(IMG / "sband_nf.png", "XY Plot 5 - Noise figure", DESIGN,
              [dict(x=fg[nb2], y=nf[nb2], expr="NF(P2_S_OUT,P1_S_RHCP)", setup=SETUP, short="NF"),
               dict(x=fg[nb2], y=NF_MIN[nb2], expr="NFmin TQP3M9037 (data sheet)", setup="table, 5 V", short="NFmin")],
              ylabel="NF [dB]", markers=[("m1", F0 / 1e3, 0)], ylim=(0, 3))
    A.xy_plot(IMG / "sband_vswr.png", "XY Plot 6 - VSWR", DESIGN,
              [dict(x=fg[nb2], y=vs(s[nb2, 0, 0]), expr="VSWR(P1_S_RHCP)", setup=SETUP, short="P1"),
               dict(x=fg[nb2], y=vs(s[nb2, 1, 1]), expr="VSWR(P2_S_OUT)", setup=SETUP, short="P2")],
              ylabel="VSWR", markers=[("m1", F0 / 1e3, 0), ("m2", F0 / 1e3, 1)], ylim=(1, 4))
    A.xy_plot(IMG / "sband_stability.png", "XY Plot 7 - Stability", DESIGN,
              [dict(x=fg, y=np.clip(kk, 0, 20), expr="StabilityFactor K (system)", setup=SETUP, short="K"),
               dict(x=fg, y=mu, expr="Mu1 (system)", setup=SETUP, short="Mu1"),
               dict(x=fg, y=M.k_mu(STAGE)[0], expr="K (LNA stage, ref. design)", setup=SETUP, short="K stage"),
               dict(x=fg, y=M.k_mu(STAGE)[1], expr="Mu1 (LNA stage)", setup=SETUP, short="Mu1 stage")],
              ylabel="K, Mu", markers=[("m1", F0 / 1e3, 0), ("m2", F0 / 1e3, 1)], ylim=(0, 10), hlines=[(1, "K = 1")])
    A.xy_plot(IMG / "sband_group_delay.png", "XY Plot 8 - Group delay", DESIGN,
              [dict(x=fg[nb2], y=gd[nb2], expr="GroupDelay(P2_S_OUT,P1_S_RHCP) [ns]", setup=SETUP, short="GD")],
              ylabel="Group delay [ns]", markers=[("m1", 2.4895, 0), ("m2", F0 / 1e3, 0), ("m3", 2.4945, 0)],
              ylim=(0, 60))
    A.smith_plot(IMG / "sband_smith.png", "Smith Plot 1 - Input / output reflection", DESIGN,
                 [dict(g=s[nb2, 0, 0], f=fg[nb2], expr="S(P1_S_RHCP,P1_S_RHCP)", setup=SETUP, short="S11"),
                  dict(g=s[nb2, 1, 1], f=fg[nb2], expr="S(P2_S_OUT,P2_S_OUT)", setup=SETUP, short="S22")],
                 markers=[("m1", F0 / 1e3, 0), ("m2", F0 / 1e3, 1)])
    # component validation, simulator style
    tf = TA.f / 1e9
    A.xy_plot(IMG / "sband_ta1442a.png", "XY Plot 9 - TA1442A model (S2P)", "TA1442A.s2p",
              [dict(x=tf, y=db(TA.s[:, 1, 0]), expr="dB(S(2,1))", setup="Touchstone model", short="S21"),
               dict(x=tf, y=db(TA.s[:, 0, 0]), expr="dB(S(1,1))", setup="Touchstone model", short="S11")],
              ylabel="dB", markers=[("m1", 2.39, 0), ("m2", 2.4895, 0), ("m3", 2.4945, 0), ("m4", 2.575, 0)],
              xlim=(2.2, 2.8), ylim=(-70, 2), marker_loc="lower left")
    xf = XH_FULL.f / 1e9
    A.xy_plot(IMG / "sband_c2327.png", "XY Plot 10 - C2327J5003AHF model (S4P)", "C2327J5003AHF.s4p",
              [dict(x=xf, y=db(XH_FULL.s[:, 3, 0]), expr="dB(S(4,1)) direct", setup="Touchstone model", short="S41"),
               dict(x=xf, y=db(XH_FULL.s[:, 2, 0]), expr="dB(S(3,1)) coupled", setup="Touchstone model", short="S31"),
               dict(x=xf, y=db(XH_FULL.s[:, 1, 0]), expr="dB(S(2,1)) isolated", setup="Touchstone model", short="S21"),
               dict(x=xf, y=db(XH_FULL.s[:, 0, 0]), expr="dB(S(1,1))", setup="Touchstone model", short="S11")],
              ylabel="dB", markers=[("m1", F0 / 1e3, 0), ("m2", F0 / 1e3, 1)], xlim=(2.0, 3.0), ylim=(-40, 0),
              marker_loc="lower left")
    return res


if __name__ == "__main__":
    r = main()
    for k, v in r["summary"].items():
        print(k, round(v, 3) if isinstance(v, float) else v)
    for x in r["budget"]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items()})
    for x in r["interferers"]:
        print("%-24s %7.1f lna1out %6.1f lna2out %6.1f out %6.1f bo2 %5.1f saw2margin %5.1f" % (
            x["interferer"], x["f_mhz"], x["lna1_out"], x["lna2_out"], x["rf_out"], x["lna2_backoff_db"],
            x["saw2_in_vs_10dbm_rating_db"]))
    for x in r["validation"]:
        print(x)
