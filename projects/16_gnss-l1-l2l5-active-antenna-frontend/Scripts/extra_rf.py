"""Additional RF parameters for project 16 (run after simulate.py; reads its Touchstone results).

Adds:
  rejection (dBc) of the full system and per stage, with a table at the interferer bands
  insertion loss of every passive part and of the passive chain
  return loss (dB) and port-to-port / reverse isolation
  output noise power density and integrated noise power into the receiver
  cross-polar (LHCP) rejection of the hybrid and the implied axial-ratio contribution
  noise temperature, mismatch loss, output P1dB / OIP3, SFDR, C/N0, L1-L5 group-delay difference
  worst-case gain / NF from the datasheet min/max limits

Equations:
  rejection(f)  = G(f_c) - G(f)                                  [dBc, relative to the band-centre gain]
  passive IL    = -10 log10 |S21|^2; hybrid excess loss = -10 log10(|S31|^2 + |S41|^2)
  RL            = -20 log10 |Sii|;  mismatch loss = -10 log10(1 - |S11|^2)
  N_out(f)      = kT0 (F1 G1 + F2 G2)   (both branches feed the DXP)   [W/Hz]
  XPD           = |b_out(RHCP)| / |b_out(LHCP)|;  AR = 20 log10((1 + r)/(1 - r)), r = 1/XPD (linear)
  Te            = T0 (F - 1)
  SFDR          = 2/3 (IIP3 - N_in),  N_in = -174 dBm/Hz + 10 log10 B + NF
  C/N0          = P_sig - (-174 + NF)   [dB-Hz, antenna at T0]
Writes ../Images/*.png, ../Extracted_Data/results_rejection.csv, results_rf_parameters.csv,
results_worst_case.csv, and merges 'extras' into results.json.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import skrf as rf
import matplotlib.pyplot as plt

import ds_data as D
import models as M
import simulate as S

ROOT, IMG, XD, TS = S.ROOT, S.IMG, S.XD, S.TS
F, FM = S.F, S.FM
db = S.db
C1, C2, C3, C4, INK, INK2 = S.C1, S.C2, S.C3, S.C4, S.INK, S.INK2

REJ_BANDS = [  # name, f_lo, f_hi (MHz)
    ("LTE B13/B14 UL", 777, 798), ("GSM-900 / LTE B8 UL", 880, 915), ("GSM-900 DL", 925, 960),
    ("DME/TACAN (below L5)", 960, 1150), ("ARNS / radar", 1260, 1300), ("LTE B11/B21 / B32 (L-band)", 1427, 1511),
    ("Inmarsat DL", 1525, 1559), ("Iridium", 1616, 1626.5), ("Inmarsat UL", 1626.5, 1660.5),
    ("LTE B3 UL", 1710, 1785), ("DCS-1800 / LTE B3 DL", 1805, 1880), ("PCS / LTE B2 UL", 1850, 1910),
    ("LTE B1 UL", 1920, 1980), ("LTE B1 DL / B4 DL", 2110, 2170),
]
CENTRE = {"L1": 1575.42, "L2/L5": 1176.45}


def band_marks(ax, ymin):
    for i, (nm, lo, hi) in enumerate(REJ_BANDS):
        ax.axvspan(lo / 1e3, hi / 1e3, color="#f2f1ed", zorder=0)
        ax.text((lo + hi) / 2e3, ymin, nm.split(" (")[0], rotation=90, fontsize=5.8,
                color=INK2, ha="center", va="bottom")


def main():
    sysn = rf.Network(str(TS / "SIM_System_3port.s3p"))
    assert sysn.frequency.npoints == F.npoints
    s = sysn.s
    g = {"L1": db(s[:, 2, 0]), "L2/L5": db(s[:, 2, 1])}
    gc = {k: g[k][S.idx(CENTRE[k])] for k in g}
    out = {}

    # ---------------------------------------------------------------- rejection (system)
    rej = {k: gc[k] - g[k] for k in g}
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    band_marks(ax, 158)
    ax.plot(FM / 1e3, rej["L1"], color=C1, label="L1 branch (ref. 1575.42 MHz)")
    ax.plot(FM / 1e3, rej["L2/L5"], color=C2, label="L2/L5 branch (ref. 1176.45 MHz)")
    ax.axhline(80, color=INK2, lw=0.9, ls="--")
    ax.text(2.19, 78, "practical limit ~60-80 dBc (PCB leakage around the filters)", fontsize=7, color=INK2,
            ha="right", va="bottom")
    ax.set_ylim(-5, 160); ax.invert_yaxis()
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Rejection (dBc)")
    ax.set_title("System rejection relative to the band-centre gain (shaded: interferer bands)")
    ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.62))
    S._save(fig, "rejection_system.png")

    rows = []
    for nm, lo, hi in REJ_BANDS:
        sel = (FM >= lo) & (FM <= hi)
        r = dict(band=nm, f_lo_mhz=lo, f_hi_mhz=hi)
        for k in g:
            r[f"rej_min_{k}_dBc"] = float(rej[k][sel].min())
            r[f"rej_mean_{k}_dBc"] = float(rej[k][sel].mean())
        rows.append(r)
    out["rejection"] = rows
    with open(XD / "results_rejection.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # ---------------------------------------------------------------- the filter Touchstone files themselves
    files = [("B7504.s2p", 1500, 1660, C1), ("B8889_matched.s2p", 1100, 1300, C2),
             ("B8889_bare_deembedded.s2p", 1100, 1300, C4), ("DXP02A_common_to_L1.s2p", 1500, 1660, C1),
             ("DXP02A_common_to_L2L5.s2p", 1100, 1300, C2)]
    fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.2))
    ftab = []
    for ax, (fn, lo, hi, c) in zip(axs.flat, files):
        n = rf.Network(str(TS / fn))
        fm = n.f / 1e6
        sel = (fm >= lo) & (fm <= hi)
        ax.plot(fm[sel] / 1e3, db(n.s[sel, 1, 0]), color=c, label="S21")
        ax.plot(fm[sel] / 1e3, db(n.s[sel, 0, 0]), color=C3, label="S11")
        ax.plot(fm[sel] / 1e3, db(n.s[sel, 1, 1]), color=INK2, ls="--", label="S22")
        ax.set_ylim(-40, 2); ax.set_title(fn, fontsize=8.5); ax.set_xlabel("Frequency (GHz)")
        ftab.append(dict(file=fn, points=len(fm), f_min_mhz=float(fm[0]), f_max_mhz=float(fm[-1]),
                         passive=bool(n.is_passive())))
    axs[0, 0].set_ylabel("dB"); axs[1, 0].set_ylabel("dB"); axs[0, 0].legend(loc="lower center", fontsize=7)
    axs.flat[-1].axis("off")
    axs.flat[-1].text(0.0, 0.5, "Filter Touchstone files (Touchstone/):\nall ESTIMATED from datasheet curves,\n"
                      "min-phase phase, GHz / RI format.\nB8889_matched includes 2 x 6.8 nH;\nB8889_bare has them "
                      "de-embedded.", fontsize=8, color=INK, va="center")
    S._save(fig, "filter_touchstone_files.png")
    out["filter_files"] = ftab

    # ---------------------------------------------------------------- rejection of each filter vs datasheet mask
    filt_rows = []
    fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.2))
    for ax, n, ref_f, pts_tbl, title, c in (
            (axs[0, 0], S.B7_full, 1575.42, D.B7504_ATT, "B7504 (one filter)", C1),
            (axs[0, 1], S.B8_full, 1176.45, D.B8889_ATT, "B8889 incl. 6.8 nH (one filter)", C2)):
        fg = n.f / 1e6
        a = -db(n.s[:, 1, 0])
        r_ = a - a[np.argmin(abs(fg - ref_f))]
        ax.plot(fg / 1e3, r_, color=c, label="model rejection")
        for lo, hi, mn, typ in pts_tbl:
            ref_il = a[np.argmin(abs(fg - ref_f))]
            ax.plot([lo / 1e3, hi / 1e3], [mn - ref_il] * 2, color=C4, lw=2.2)
            ax.plot([lo / 1e3, hi / 1e3], [typ - ref_il] * 2, color=C3, lw=1.2, ls="--")
            sel = (fg >= lo) & (fg <= hi)
            filt_rows.append(dict(filter=title.split(" ")[0], f_lo_mhz=lo, f_hi_mhz=hi, spec_min_att_db=mn,
                                  spec_typ_att_db=typ, model_min_att_db=float(a[sel].min()),
                                  model_min_rej_dbc=float(r_[sel].min()),
                                  margin_to_spec_db=float(a[sel].min() - mn)))
        ax.plot([], [], color=C4, lw=2.2, label="datasheet min attenuation")
        ax.plot([], [], color=C3, lw=1.2, ls="--", label="datasheet typ attenuation")
        ax.set_xlim(0, 6); ax.set_ylim(-5, 90); ax.invert_yaxis()
        ax.set_title(f"{title}: rejection vs datasheet"); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Rejection (dBc)")
        ax.legend(loc="lower right", fontsize=7)
    fd = S.DX_full.f / 1e6
    for ax, j, ref_f, title, c, masks in (
            (axs[1, 0], 1, 1582.19, "DXP.02.A common <-> L1 port", C1, [(10, 1330, 32, 38), (1660, 2000, 27, 33)]),
            (axs[1, 1], 2, 1206.92, "DXP.02.A common <-> L2/L5 port", C2, [(10, 1100, 17, 23), (1320, 2000, 20, 28)])):
        a = -db(S.DX_full.s[:, j, 0])
        k0 = np.argmin(abs(fd - ref_f))
        ax.plot(fd / 1e3, a - a[k0], color=c, label="model rejection")
        for lo, hi, mn, typ in masks:
            ax.plot([max(lo, 600) / 1e3, hi / 1e3], [mn] * 2, color=C4, lw=2.2)
            ax.plot([max(lo, 600) / 1e3, hi / 1e3], [typ] * 2, color=C3, lw=1.2, ls="--")
            sel = (fd >= max(lo, 600)) & (fd <= hi)
            filt_rows.append(dict(filter=f"DXP {'L1' if j == 1 else 'L2/L5'}", f_lo_mhz=max(lo, 600), f_hi_mhz=hi,
                                  spec_min_att_db=mn, spec_typ_att_db=typ,
                                  model_min_att_db=float(a[sel].min()), model_min_rej_dbc=float((a - a[k0])[sel].min()),
                                  margin_to_spec_db=float((a - a[k0])[sel].min() - mn)))
        ax.plot([], [], color=C4, lw=2.2, label="datasheet min (rel. 0 dB)")
        ax.plot([], [], color=C3, lw=1.2, ls="--", label="datasheet typ")
        ax.set_ylim(-5, 70); ax.invert_yaxis()
        ax.set_title(title); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Rejection (dBc)")
        ax.legend(loc="lower right", fontsize=7)
    S._save(fig, "filter_rejection.png")
    # close-up of the skirts near the GNSS bands
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.9))
    for ax, n, ref_f, lo, hi, c, nm in ((axs[0], S.B8_full, 1176.45, 1050, 1350, C2, "B8889"),
                                        (axs[1], S.B7_full, 1575.42, 1450, 1720, C1, "B7504")):
        fg = n.f / 1e6
        sel = (fg >= lo) & (fg <= hi)
        a = -db(n.s[:, 1, 0]); r_ = a - a[np.argmin(abs(fg - ref_f))]
        ax.plot(fg[sel] / 1e3, r_[sel], color=c, label=f"{nm} x1")
        ax.plot(fg[sel] / 1e3, 2 * r_[sel], color=c, ls="--", label=f"{nm} x2 (as in the chain)")
        for nm2, l2, h2 in REJ_BANDS:
            if l2 < hi and h2 > lo:
                ax.axvspan(max(l2, lo) / 1e3, min(h2, hi) / 1e3, color="#f2f1ed", zorder=0)
                ax.text((max(l2, lo) + min(h2, hi)) / 2e3, 75, nm2.split(" (")[0], rotation=90, fontsize=6,
                        color=INK2, ha="center", va="bottom")
        ax.set_ylim(-3, 100); ax.invert_yaxis()
        ax.set_title(f"{nm}: skirt rejection near the GNSS band"); ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Rejection (dBc)"); ax.legend(loc="center right", fontsize=7)
    S._save(fig, "filter_rejection_skirts.png")
    out["filter_rejection"] = filt_rows
    with open(XD / "results_filter_rejection.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filt_rows[0])); w.writeheader(); w.writerows(filt_rows)

    # ---------------------------------------------------------------- rejection per stage (filters only)
    hyb = S.cp_hybrid_2port()
    saw = {"L1": S.b7("s"), "L2/L5": S.b8("s")}
    dxr = {"L1": S.dxp_2port(1), "L2/L5": S.dxp_2port(2)}
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.9), sharey=True)
    for ax, k, c in ((axs[0], "L2/L5", C2), (axs[1], "L1", C1)):
        k0 = S.idx(CENTRE[k])
        s1 = db(saw[k].s[:, 1, 0])
        s2 = 2 * s1
        s3 = s2 + db(dxr[k].s[:, 1, 0])
        for y, lab, ls in ((s1, "after SAW 1", ":"), (s2, "after SAW 2", "--"), (s3, "after SAW 2 + DXP", "-")):
            ax.plot(FM / 1e3, y[k0] - y, color=c, ls=ls, label=lab)
        ax.set_ylim(-5, 160); ax.invert_yaxis()
        ax.set_title(f"{k} branch: filter rejection by stage")
        ax.set_xlabel("Frequency (GHz)")
    axs[0].set_ylabel("Rejection (dBc)")
    axs[1].legend(loc="lower right", fontsize=7)
    S._save(fig, "rejection_per_stage.png")

    # ---------------------------------------------------------------- insertion loss
    hc = S.on_sys(S.HC_full, "hc")
    hc_excess = -10 * np.log10(abs(hc.s[:, 2, 0]) ** 2 + abs(hc.s[:, 3, 0]) ** 2)
    il = {"HC125A excess (combine)": -db(hyb.s[:, 1, 0]), "B7504": -db(saw["L1"].s[:, 1, 0]),
          "B8889 (matched)": -db(saw["L2/L5"].s[:, 1, 0]), "DXP common-L1": -db(dxr["L1"].s[:, 1, 0]),
          "DXP common-L2/L5": -db(dxr["L2/L5"].s[:, 1, 0])}
    tot = {"L1": il["HC125A excess (combine)"] + 2 * il["B7504"] + il["DXP common-L1"],
           "L2/L5": il["HC125A excess (combine)"] + 2 * il["B8889 (matched)"] + il["DXP common-L2/L5"]}
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 4.0), sharey=True)
    for ax, k, lo, hi, parts in ((axs[0], "L2/L5", 1150, 1260, ["B8889 (matched)", "DXP common-L2/L5"]),
                                 (axs[1], "L1", 1545, 1620, ["B7504", "DXP common-L1"])):
        sel = (FM >= lo) & (FM <= hi)
        S.shade(ax, "L1" if k == "L1" else "L2")
        ax.plot(FM[sel] / 1e3, il["HC125A excess (combine)"][sel], color=C3, label="HC125A (RHCP combine)")
        ax.plot(FM[sel] / 1e3, il[parts[0]][sel], color=C1 if k == "L1" else C2, label=f"{parts[0]} (one filter)")
        ax.plot(FM[sel] / 1e3, il[parts[1]][sel], color=C4, label=parts[1])
        ax.plot(FM[sel] / 1e3, tot[k][sel], color=INK, lw=2, label="total passive (hyb + 2 SAW + DXP)")
        ax.set_ylim(0, 12); ax.invert_yaxis()
        ax.set_title(f"{k} branch: insertion loss"); ax.set_xlabel("Frequency (GHz)")
    axs[0].set_ylabel("Insertion loss (dB)")
    axs[1].legend(loc="lower center", fontsize=7)
    S._save(fig, "insertion_loss.png")
    ilrows = []
    for band, (fc, hb, br) in D.GNSS_BANDS.items():
        k = S.idx(fc)
        sel = (FM >= fc - hb) & (FM <= fc + hb)
        b = "L1" if br == "L1" else "L2/L5"
        filt = "B7504" if b == "L1" else "B8889 (matched)"
        dx = "DXP common-L1" if b == "L1" else "DXP common-L2/L5"
        ilrows.append(dict(band=band, f_mhz=fc, hybrid_db=float(il["HC125A excess (combine)"][k]),
                           saw_db=float(il[filt][k]), saw_max_in_bw_db=float(il[filt][sel].max()),
                           dxp_db=float(il[dx][k]), total_passive_db=float(tot[b][k]),
                           total_passive_max_in_bw_db=float(tot[b][sel].max()),
                           hc_excess_4port_db=float(hc_excess[k])))
    out["insertion_loss"] = ilrows

    # ---------------------------------------------------------------- return loss + isolation
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.9))
    for i, (lab, c) in enumerate((("P1 L1 input", C1), ("P2 L2/L5 input", C2), ("P3 RF output", C3))):
        axs[0].plot(FM / 1e3, -db(s[:, i, i]), color=c, label=lab)
    axs[0].axhline(10, color=INK2, lw=0.8, ls="--"); axs[0].text(0.62, 10.5, "10 dB", fontsize=7, color=INK2)
    axs[0].set_ylim(0, 40); axs[0].invert_yaxis()
    axs[0].set_xlabel("Frequency (GHz)"); axs[0].set_ylabel("Return loss (dB)")
    axs[0].set_title("Return loss at all ports"); axs[0].legend(loc="lower left", fontsize=7)
    axs[1].plot(FM / 1e3, -db(s[:, 1, 0]), color=C4, label="P1 <-> P2 (L1 in <-> L2/L5 in)")
    axs[1].plot(FM / 1e3, -db(s[:, 0, 2]), color=C1, label="reverse P3 -> P1")
    axs[1].plot(FM / 1e3, -db(s[:, 1, 2]), color=C2, label="reverse P3 -> P2")
    axs[1].plot(FM / 1e3, -db(S.DX_full.s[:, 2, 1]), color=C3, label="DXP L1 <-> L2/L5 port")
    axs[1].set_ylim(0, 220); axs[1].invert_yaxis()
    axs[1].set_xlabel("Frequency (GHz)"); axs[1].set_ylabel("Isolation (dB)")
    axs[1].set_title("Isolation"); axs[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncols=2, fontsize=7)
    S._save(fig, "return_loss_isolation.png")

    # ---------------------------------------------------------------- output noise
    nf1, net1, _ = S.branch_noise(S.b7("s"), 1)
    nf2, net2, _ = S.branch_noise(S.b8("s"), 2)
    g1, g2 = abs(net1.s[:, 1, 0]) ** 2, abs(net2.s[:, 1, 0]) ** 2
    psd = 10 * np.log10(S.k_B * M.T0 * (nf1 * g1 + nf2 * g2) * 1e3)          # dBm/Hz
    df = (FM[1] - FM[0]) * 1e6
    p_tot = 10 * np.log10(np.sum(10 ** (psd / 10)) * df)
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    ax.plot(FM / 1e3, psd, color=C1)
    ax.axhline(-174, color=INK2, lw=0.8, ls="--"); ax.text(0.62, -172, "kT0 = -174 dBm/Hz", fontsize=7, color=INK2)
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Noise PSD at RF out (dBm/Hz)")
    ax.set_title(f"Output noise power density (both branches); total 0.6-2.2 GHz = {p_tot:.1f} dBm into 50 ohm")
    S._save(fig, "output_noise_psd.png")
    out["output_noise_total_dbm"] = float(p_tot)
    out["output_noise_psd_peak_dbm_hz"] = float(psd.max())

    # ---------------------------------------------------------------- polarisation (hybrid imbalance)
    pr = rf.circuit.Circuit.Port(F, "rhcp")
    pl = rf.circuit.Circuit.Port(F, "lhcp")
    po = rf.circuit.Circuit.Port(F, "out")
    cp = M.patch_cp_feed(F); cp.name = "CPx"
    hcx = S.on_sys(S.HC_full, "HCx")
    iso = M.load_z(F, name="isox")
    xn = rf.circuit.Circuit([[(pr, 0), (cp, 0)], [(pl, 0), (cp, 1)], [(cp, 2), (hcx, 2)], [(cp, 3), (hcx, 3)],
                             [(hcx, 1), (iso, 0)], [(hcx, 0), (po, 0)]]).network
    xpd = db(xn.s[:, 2, 0]) - db(xn.s[:, 2, 1])
    rr = 10 ** (-xpd / 20)
    ar = 20 * np.log10((1 + rr) / (1 - rr))
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6))
    sel = (FM >= 1150) & (FM <= 1630)
    axs[0].plot(FM[sel] / 1e3, xpd[sel], color=C1)
    axs[0].set_title("Cross-pol (LHCP) rejection of the HC125A combiner"); axs[0].set_ylabel("XPD (dB)")
    axs[1].plot(FM[sel] / 1e3, ar[sel], color=C2)
    axs[1].set_title("Axial-ratio contribution of the hybrid"); axs[1].set_ylabel("Axial ratio (dB)")
    for a in axs:
        a.set_xlabel("Frequency (GHz)")
    S._save(fig, "polarisation.png")

    # ---------------------------------------------------------------- per-band parameter table
    gd = {"L1": -np.gradient(np.unwrap(np.angle(s[:, 2, 0])), 2 * np.pi * F.f) * 1e9,
          "L2/L5": -np.gradient(np.unwrap(np.angle(s[:, 2, 1])), 2 * np.pi * F.f) * 1e9}
    budgets = R["budgets"]
    bmap = {"L1/E1/B1C": "L1 C/A (1575.42 MHz, 2.046 MHz)", "L5/E5a/B2a": "L5 (1176.45 MHz, 20.46 MHz)",
            "L2": "L2C (1227.60 MHz, 2.046 MHz)"}
    bw = {"L1/E1/B1C": 2.046e6, "L5/E5a/B2a": 20.46e6, "L2": 2.046e6}
    psig = {"L1/E1/B1C": D.GNSS_MIN_POWER_DBM["L1/E1/B1C"], "L5/E5a/B2a": D.GNSS_MIN_POWER_DBM["L5/E5a/B2a"],
            "L2": D.GNSS_MIN_POWER_DBM["L2"]}
    params = []
    for band, (fc, hb, br) in D.GNSS_BANDS.items():
        k = S.idx(fc)
        b = "L1" if br == "L1" else "L2/L5"
        col = 0 if b == "L1" else 1
        nf = 10 * np.log10((nf1[k] * g1[k] + nf2[k] * g2[k]) / (g1[k] if b == "L1" else g2[k]))
        row = dict(band=band, f_mhz=fc, gain_db=float(db(s[k, 2, col])), nf_db=float(nf),
                   te_k=float(M.T0 * (10 ** (nf / 10) - 1)),
                   rl_in_db=float(-db(s[k, col, col])), rl_out_db=float(-db(s[k, 2, 2])),
                   mismatch_loss_in_db=float(-10 * np.log10(1 - abs(s[k, col, col]) ** 2)),
                   reverse_iso_db=float(-db(s[k, col, 2])), xpd_db=float(xpd[k]), ar_db=float(ar[k]),
                   gd_ns=float(gd[b][k]))
        if band in bmap:
            last = budgets[bmap[band]][-1]
            iip3, ip1 = last["cum_iip3_dbm"], last["cum_iip1db_dbm"]
            nin = -174 + 10 * np.log10(bw[band]) + row["nf_db"]
            row.update(iip3_dbm=iip3, oip3_dbm=iip3 + row["gain_db"], ip1db_in_dbm=ip1,
                       op1db_out_dbm=ip1 + row["gain_db"] - 1, sfdr_db=2 / 3 * (iip3 - nin),
                       cn0_dbhz=psig[band] + 174 - row["nf_db"], bw_mhz=bw[band] / 1e6)
        params.append(row)
    gd_diff = float(gd["L1"][S.idx(1575.42)] - gd["L2/L5"][S.idx(1176.45)])
    out["rf_parameters"] = params
    out["gd_l1_minus_l5_ns"] = gd_diff
    keys = sorted({k for r in params for k in r}, key=lambda x: list(params[0]).index(x) if x in params[0] else 99)
    with open(XD / "results_rf_parameters.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(params)
    with open(XD / "results_insertion_loss.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ilrows[0])); w.writeheader(); w.writerows(ilrows)

    # ---------------------------------------------------------------- worst case from datasheet limits
    def friis(stages):
        gl, fc_, gcum = 1.0, 1.0, 0.0
        for gdb, nfdb in stages:
            fc_ += (10 ** (nfdb / 10) - 1) / gl
            gl *= 10 ** (gdb / 10)
        return 10 * np.log10(gl), 10 * np.log10(fc_)

    wc = []
    for case, br, fcen, saw_typ, saw_max, dx_typ, dx_max in (
            ("L1", "L1", 1575.42, 0.9, 1.4, 3.8, 4.6), ("L5", "L2", 1176.45, 0.9, 1.5, 4.2, 5.2),
            ("L2", "L2", 1227.60, 1.4, 2.6, 4.2, 5.2)):
        k = S.idx(fcen)
        g_lna = float(db(S.STAGE.s[k, 1, 0]))
        hyb_typ = float(-db(hyb.s[k, 1, 0]))
        nf_lna = 0.40
        typ = friis([(-hyb_typ, hyb_typ), (g_lna, nf_lna), (-saw_typ, saw_typ), (g_lna, nf_lna),
                     (-saw_typ, saw_typ), (-dx_typ, dx_typ)])
        worst = friis([(-0.3, 0.3), (g_lna - 1.5, 0.65), (-saw_max, saw_max), (g_lna - 1.5, 0.65),
                       (-saw_max, saw_max), (-dx_max, dx_max)])
        best = friis([(-hyb_typ, hyb_typ), (g_lna + 1.5, nf_lna), (-saw_typ * 0.8, saw_typ * 0.8),
                      (g_lna + 1.5, nf_lna), (-saw_typ * 0.8, saw_typ * 0.8), (-3.3, 3.3)])
        wc.append(dict(band=case, gain_typ_db=typ[0], gain_min_db=worst[0], gain_max_db=best[0],
                       nf_typ_db=typ[1], nf_max_db=worst[1]))
    out["worst_case"] = wc
    with open(XD / "results_worst_case.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(wc[0])); w.writeheader(); w.writerows(wc)

    R["extras"] = out
    (ROOT / "Scripts" / "results.json").write_text(json.dumps(R, indent=1, default=float))
    return out


R = json.loads((ROOT / "Scripts" / "results.json").read_text())

if __name__ == "__main__":
    o = main()
    for r in o["rejection"]:
        print(f"{r['band']:30s} L1 {r['rej_min_L1_dBc']:6.1f}  L2/L5 {r['rej_min_L2/L5_dBc']:6.1f}")
    for r in o["insertion_loss"]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    for r in o["rf_parameters"]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    print("GD L1-L5", round(o["gd_l1_minus_l5_ns"], 1), "ns; output noise", round(o["output_noise_total_dbm"], 1), "dBm")
    for r in o["worst_case"]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
