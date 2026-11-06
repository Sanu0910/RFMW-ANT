"""RF budget, rejection, linearity / damage, power and thermal for CRL-LS-CRPA4 (one channel = L1, L2/L5, S branches).
Inputs: project 16 Touchstone models (00_reference/p16/Touchstone), project 17 stage values for the L chain,
this board's RF track lengths (04_fab/_netlen.json), data-sheet values (00_vendor, 00_reference/p16/Extracted_Data).
Outputs (05_docs/): CRL-LS-CRPA4_rf_budget.csv, _rejection.csv, _power.csv, _rf_summary.json, img/rf_*.png.
Run with the repo .venv:  python rf_budget.py
[ASSUMED] / [ESTIMATE] values are marked in the tables.
"""
import csv, json, math, os
import numpy as np
import skrf as rf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
TS = os.path.join(PRJ, "00_reference", "p16", "Touchstone")
DOCS = os.path.join(PRJ, "05_docs")
IMG = os.path.join(DOCS, "img")
PN = "CRL-LS-CRPA4"
NET = json.load(open(os.path.join(PRJ, "04_fab", "_netlen.json")))

LINE_DB_CM_25 = 0.066          # 0.34 mm line on RO4350B 0.168 mm at 2.5 GHz (scikit-rf, ls_design.py)


def line_db(mm, f_ghz):
    """[ESTIMATE] microstrip loss scaled from 2.5 GHz with f^0.75 (conductor ~sqrt f + dielectric ~f)."""
    return LINE_DB_CM_25 * (f_ghz / 2.5) ** 0.75 * mm / 10


def net_mm(*names):
    return sum(NET.get("CH1_" + n, 0.0) for n in names)


def load(name):
    return rf.Network(os.path.join(TS, name))


# ----------------------------------------------------------------------------- stage tables
# (name, gain dB, NF dB, OP1dB dBm or None, OIP3 dBm or None, note).  Passive: NF = loss.
def chain(band):
    if band == "S":
        f = 2.492028
        lna = load("TQP3M9037_stage_SBand_refdesign.s2p")
        saw = load("TA1442A.s2p")
        g_lna = float(lna.s_db[np.argmin(abs(lna.f - f * 1e9)), 1, 0])
        il_saw = -float(saw.s_db[np.argmin(abs(saw.f - f * 1e9)), 1, 0])
        st = [("Feed line, patch pin -> hybrid", -line_db(net_mm("S_F0"), f), None, None, f"{net_mm('S_F0'):.1f} mm"),
              ("C2327J5003AHF hybrid (RHCP combine)", -0.30, None, None, "TTM Rev K typ excess IL"),
              ("Line, hybrid -> limiter", -line_db(net_mm("S_HYB"), f), None, None, f"{net_mm('S_HYB'):.1f} mm"),
              ("CLM-83-2W+ limiter", -0.30, None, None, "[ESTIMATE] 0.5 dB typ broadband, 0.17 dB at L1 (p17)"),
              ("Line, limiter -> LNA1", -line_db(net_mm("S_LIM", "S_A1IN"), f), None, None, ""),
              ("LNA1 TQP3M9037 (2.3-2.6 GHz match)", g_lna, 0.60, 20.0, 34.0, "NFmin 0.51 dB @2.5 GHz + 0.1 match [ESTIMATE]"),
              ("TA1442A #1", -il_saw, None, None, "Tai-Saw model (p16 A24)"),
              ("LNA2 TQP3M9037", g_lna, 0.60, 20.0, 34.0, ""),
              ("TA1442A #2", -il_saw, None, None, ""),
              ("TA1442A #3", -il_saw, None, None, ""),
              ("Output line + DC block -> SMA", -line_db(net_mm("S_S3OUT", "S_RFOUT") + 8, f), None, None, "incl. SMA launch [ESTIMATE]")]
        return f, "NavIC S (2492.028 MHz)", st
    p17 = {r["stage"]: r for r in csv.DictReader(open(os.path.join(PRJ, "00_reference", "p17", "rf_budget_stages.csv")))
           if r["case"].startswith({"L1": "L1", "L5": "L5", "L2": "L2C"}[band])}
    f = {"L1": 1.57542, "L5": 1.17645, "L2": 1.2276}[band]
    b = "L1" if band == "L1" else "L2"
    saw = "B7504" if band == "L1" else "B8889"
    gv = lambda k: float(p17[k]["gain_db"])
    st = [("Feed line, patch pin -> hybrid", -line_db(net_mm(f"{b}_F0"), f), None, None, f"{net_mm(b + '_F0'):.1f} mm"),
          ("HC125A hybrid (RHCP combine)", gv("HC125A (RHCP combine)"), None, None, "p16 model"),
          ("Line, hybrid -> limiter", -line_db(net_mm(f"{b}_HYB"), f), None, None, f"{net_mm(b + '_HYB'):.1f} mm"),
          ("CLM-83-2W+ limiter", gv("CLM-83-2W+ limiter"), None, None, "p17"),
          ("Line, limiter -> LNA1", -line_db(net_mm(f"{b}_LIM", f"{b}_A1IN"), f), None, None, ""),
          ("LNA1 TQP3M9037 + bias", gv("LNA1 TQP3M9037 + bias"), float(p17["LNA1 TQP3M9037 + bias"]["nf_db"]), 21.0, 34.5, "p16 model"),
          (f"{saw} #1", gv(f"{saw} #1"), None, None, ""),
          ("LNA2 TQP3M9037 + bias", gv("LNA2 TQP3M9037 + bias"), float(p17["LNA2 TQP3M9037 + bias"]["nf_db"]), 21.0, 34.5, ""),
          (f"{saw} #2", gv(f"{saw} #2"), None, None, ""),
          (f"{saw} #3", gv(f"{saw} #3 (Rev B)"), None, None, ""),
          ("DXP.02.A combiner", gv("DXP.02.A (combiner)"), None, None, "p16 model"),
          ("Output line + DC block -> SMA", -line_db(net_mm(f"{b}_DXP", "RFOUT") + 8, f), None, None, "")]
    name = {"L1": "GPS L1 C/A (1575.42 MHz)", "L5": "GPS L5 (1176.45 MHz)", "L2": "GPS L2C (1227.60 MHz)"}[band]
    return f, name, st


def cascade(st):
    """Friis NF, cascaded gain, input-referred P1dB / IIP3 (amplifier stages only), gain ahead of each stage."""
    g_lin, f_tot, rows, ip3_inv, p1_inv = 1.0, 1.0, [], 0.0, 0.0
    for s in st:
        name, g, nf, op1, oip3, note = s if len(s) == 6 else (s[0], s[1], None, None, None, s[4])
        nf = nf if nf is not None else max(-g, 0.0)
        g_before = 10 * math.log10(g_lin)
        f_tot += (10 ** (nf / 10) - 1) / g_lin
        g_lin *= 10 ** (g / 10)
        if oip3 is not None:
            ip3_inv += 1 / 10 ** ((oip3 - g - g_before) / 10)       # input-referred IIP3 of this stage, mW
            p1_inv += 1 / 10 ** ((op1 - g + 1 - g_before) / 10)
        rows.append(dict(stage=name, gain_db=round(g, 3), nf_db=round(nf, 3), gain_before_db=round(g_before, 2),
                         cum_gain_db=round(10 * math.log10(g_lin), 2), cum_nf_db=round(10 * math.log10(f_tot), 3), note=note))
    return rows, 10 * math.log10(1 / ip3_inv), 10 * math.log10(1 / p1_inv)


# ----------------------------------------------------------------------------- wideband chain response
def chain_s21(band):
    """Cascade of the active chain from the LNA1 input to the output (Touchstone, mismatch included), dB vs MHz,
    plus the passive front end as a flat loss (hybrid, limiter, lines)."""
    if band == "S":
        lna, saw = load("TQP3M9037_stage_SBand_refdesign.s2p"), load("TA1442A.s2p")
        fr = rf.Frequency(2000, 3000, 2001, "MHz")
        lna, saw = lna.interpolate(fr), saw.interpolate(fr)
        net = lna ** saw ** lna ** saw ** saw
    else:
        lna = load("TQP3M9037_stage_5V_with_bias.s2p")
        saw = load("B7504.s2p" if band == "L1" else "B8889_matched.s2p")
        dxp = load("DXP02A_common_to_L1.s2p" if band == "L1" else "DXP02A_common_to_L2L5.s2p")
        fr = rf.Frequency(800, 2100, 2601, "MHz")
        lna, saw, dxp = (n.interpolate(fr) for n in (lna, saw, dxp))
        net = lna ** saw ** lna ** saw ** saw ** dxp.flipped()      # DXP: band port -> common output
    return net.f / 1e6, net.s_db[:, 1, 0], net


INTERFERERS = {
    "S": [("LTE B40 (2300-2400) 2350", 2350), ("WiFi ch1 / BT low 2412", 2412), ("WiFi ch6 2437", 2437),
          ("WiFi ch11 2462", 2462), ("WiFi ch13 / BT high 2472-2480", 2476), ("LTE B41 low 2506", 2506),
          ("LTE B7 UL 2535", 2535), ("LTE B41 / B7 2570", 2570), ("LTE B41 2650", 2650)],
    "L1": [("GSM900 / LTE B8 UL 900", 900), ("DME / TACAN 1150", 1150), ("Inmarsat UL 1643", 1643),
           ("Iridium 1621", 1621), ("LTE B3 UL 1747", 1747), ("LTE B1 UL 1950", 1950)],
    "L2": [("GSM900 / LTE B8 UL 900", 900), ("DME / TACAN 1025", 1025), ("DME / TACAN 1150", 1150),
           ("Radar / ATC 1300", 1300), ("GPS L1 1575", 1575), ("LTE B3 UL 1747", 1747)],
}


def rejection(band, f0_mhz):
    f, s21, _ = chain_s21(band)
    g0 = float(np.interp(f0_mhz, f, s21))
    rows = []
    for name, fi in INTERFERERS[band]:
        m = g0 - float(np.interp(fi, f, s21))
        # a real board leaks around the filters (cavity, ground, bias lines): quote at most 80 dB [ESTIMATE]
        rows.append(dict(band=band, interferer=name, f_mhz=fi, model_db=round(m, 1),
                         rejection_db=(">80" if m > 80 else round(m, 1))))
    return rows, (f, s21 - g0)


def saw_limit(band, rows_budget, f0):
    """Antenna-port CW power that drives the first SAW / second SAW to its max rating, in band (worst case: the
    SAW is the only frequency-selective element ahead of it). Limiter caps LNA1 input at +11.5 dBm typ."""
    rating = {"S": 10.0, "L1": 15.0, "L2": 5.0}[band]
    g = {r["stage"]: r for r in rows_budget}
    s1 = next(r for r in rows_budget if "#1" in r["stage"])
    s2 = next(r for r in rows_budget if "#2" in r["stage"])
    return rating, round(rating - s1["gain_before_db"], 1), round(rating - s2["gain_before_db"], 1)


# ----------------------------------------------------------------------------- power / thermal
POWER = [  # item, qty, I typ mA, I max mA, V
    ("TQP3M9037 LNA (2 per branch x 3 branches x 4 ch)", 24, 70, 90, 5.0),
    ("Q1 reverse-polarity PFET + F1 + D1 TVS (loss at 1.7 A)", 1, 0, 0, 0.0),
]


def power():
    rows, it, im = [], 0.0, 0.0
    for item, q, ityp, imax, v in POWER:
        rows.append(dict(item=item, qty=q, i_typ_ma=q * ityp, i_max_ma=q * imax, p_typ_w=round(q * ityp * v / 1000, 2),
                         p_max_w=round(q * imax * v / 1000, 2)))
        it += q * ityp; im += q * imax
    p_lna = 0.070 * 5.0
    tj = dict(theta_jc=53.4, p_lna_w=p_lna, dT_jc=round(53.4 * p_lna, 1),
              tcase_85=85.0, tj_85=round(85 + 53.4 * p_lna, 1), tj_limit=190.0)
    return rows, dict(i_typ_a=it / 1000, i_max_a=im / 1000, p_typ_w=it * 5 / 1000, p_max_w=im * 5.25 / 1000), tj


def main():
    os.makedirs(IMG, exist_ok=True)
    allrows, summ, rej_all, curves = [], {}, [], {}
    for band in ("L1", "L5", "L2", "S"):
        f, name, st = chain(band)
        rows, iip3, ip1 = cascade(st)
        for r in rows: r["case"] = name
        allrows += rows
        rb = "L2" if band == "L5" else band
        rat, lim1, lim2 = saw_limit(rb, rows, f)
        summ[band] = dict(case=name, f_mhz=f * 1000, gain_db=rows[-1]["cum_gain_db"], nf_db=rows[-1]["cum_nf_db"],
                          iip3_dbm=round(iip3, 1), ip1db_dbm=round(ip1, 1), saw_rating_dbm=rat,
                          p_ant_saw1_dbm=lim1, p_ant_saw2_dbm=lim2)
        if band in ("L1", "L2", "S"):
            rr, cv = rejection(band, f * 1000)
            rej_all += rr; curves[band] = cv
    with open(os.path.join(DOCS, PN + "_rf_budget.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["case", "stage", "gain_db", "nf_db", "gain_before_db", "cum_gain_db", "cum_nf_db", "note"])
        w.writeheader(); w.writerows(allrows)
    with open(os.path.join(DOCS, PN + "_rejection.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rej_all[0])); w.writeheader(); w.writerows(rej_all)
    prow, ptot, tj = power()
    with open(os.path.join(DOCS, PN + "_power.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prow[0])); w.writeheader(); w.writerows(prow)
    json.dump(dict(chains=summ, power=ptot, thermal=tj), open(os.path.join(DOCS, PN + "_rf_summary.json"), "w"), indent=1)

    # figures
    fig, axs = plt.subplots(3, 1, figsize=(9, 10))
    for ax, band, f0, title in zip(axs, ("L1", "L2", "S"), (1575.42, 1197.0, 2492.028),
                                   ("L1 branch (LNA-B7504-LNA-B7504-B7504-DXP)", "L2/L5 branch (LNA-B8889-LNA-B8889-B8889-DXP)",
                                    "NavIC S branch (LNA-TA1442A-LNA-TA1442A-TA1442A)")):
        fx, rel = curves[band]
        ax.plot(fx, rel, lw=1.1, color="#1f4e79")
        for nm, fi in INTERFERERS[band]:
            ax.axvline(fi, color="#c0392b", lw=0.6, ls="--")
            ax.text(fi, 3, nm.split(" ")[0] + " " + nm.split(" ")[-1], rotation=90, fontsize=6, va="bottom", ha="right", color="#c0392b")
        ax.set_ylim(-140, 25); ax.grid(alpha=0.3); ax.set_ylabel("dB rel. pass band"); ax.set_title(title, fontsize=9)
        if band == "S": ax.set_xlim(2250, 2750)
    axs[-1].set_xlabel("MHz")
    fig.tight_layout(); fig.savefig(os.path.join(IMG, "rf_rejection.png"), dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    for band, c in (("L1", "#1f4e79"), ("L5", "#2e86c1"), ("S", "#c0392b")):
        rr = [r for r in allrows if r["case"] == summ[band]["case"]]
        ax.plot(range(len(rr)), [r["cum_gain_db"] for r in rr], "-o", ms=3, color=c, label=f"{band} gain")
        ax.plot(range(len(rr)), [10 * r["cum_nf_db"] for r in rr], ":s", ms=3, color=c, label=f"{band} NF x10")
    ax.set_xticks(range(12)); ax.set_xticklabels([f"S{i}" for i in range(12)], fontsize=7)
    ax.set_xlabel("stage (see budget table)"); ax.set_ylabel("dB"); ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=3)
    fig.tight_layout(); fig.savefig(os.path.join(IMG, "rf_cascade.png"), dpi=150); plt.close(fig)
    print(json.dumps(summ, indent=1)); print(ptot, tj)
    for r in rej_all: print(r)


if __name__ == "__main__":
    main()
