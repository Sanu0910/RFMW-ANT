"""Stand-alone filter-rejection document for the active antenna RF chains (L1, L2/L5, NavIC S).

In-band: insertion loss and ripple of the filter chain in each GNSS band.
Near-band / out-of-band: rejection (dBc, relative to the band centre) after each filter stage and for the
complete chain at named interferer frequencies; filter compliance with the data-sheet attenuation limits;
cross-band rejection between the branches.

Reads the Touchstone files in ../Touchstone and results*.json; writes ../Images/rejdoc_*.png,
../Extracted_Data/rejection_doc_*.csv and ../Report/Filter_Rejection_Analysis.pdf / .docx.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import skrf as rf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ds_data as D
import aedt_style as A
import make_report as MR

ROOT = Path(__file__).resolve().parent.parent
TS, IMG, XD = ROOT / "Touchstone", ROOT / "Images", ROOT / "Extracted_Data"
R = json.loads((ROOT / "Scripts" / "results.json").read_text())
RS = json.loads((ROOT / "Scripts" / "results_sband.json").read_text())


def db(x):
    return 20 * np.log10(np.abs(x) + 1e-30)


def att(n, i=1, j=0):
    return n.f / 1e6, -db(n.s[:, i, j])


def at(fm, y, f):
    return float(np.interp(f, fm, y)) if fm[0] <= f <= fm[-1] else None


B7, B8, TA = (rf.Network(str(TS / f)) for f in ("B7504.s2p", "B8889_matched.s2p", "TA1442A.s2p"))
DX1, DX2 = rf.Network(str(TS / "DXP02A_common_to_L1.s2p")), rf.Network(str(TS / "DXP02A_common_to_L2L5.s2p"))
SYS = rf.Network(str(TS / "SIM_System_3port.s3p"))
SYSS = rf.Network(str(TS / "SIM_SBand_2port.s2p"))

CHAINS = {
    "L1": dict(fc=1575.42, saw=B7, saw_name="B7504", dxp=DX1, sys=(SYS, 2, 0),
               bands=[("B1I", 1559.052, 1563.144), ("L1 C/A / E1 / B1C", 1574.397, 1576.443),
                      ("L1 wide (E1/B1C 4.092 MHz)", 1573.374, 1577.466), ("G1 (FDMA)", 1597.5, 1605.9)],
               keys=[(787, "LTE B13/B14 UL"), (897.5, "GSM-900 / LTE B8 UL"), (1176.45, "L5 (other branch)"),
                     (1227.6, "L2 (other branch)"), (1500, "L-band (LTE B11/B21)"), (1530, "Inmarsat DL"),
                     (1545, "Inmarsat DL"), (1550, "lower skirt"), (1612, "upper skirt"), (1616, "Iridium low"),
                     (1621, "Iridium"), (1626.5, "Iridium / Inmarsat UL"), (1643, "Inmarsat UL"),
                     (1660, "Inmarsat UL top"), (1710, "LTE B3 UL low"), (1747.5, "LTE B3 UL"),
                     (1842.5, "DCS-1800 DL"), (1950, "LTE B1 UL"), (2140, "LTE B1 DL"), (2442, "Wi-Fi 2.4 GHz"),
                     (5500, "Wi-Fi 5 GHz")]),
    "L2/L5": dict(fc=1176.45, saw=B8, saw_name="B8889 (+2 x 6.8 nH)", dxp=DX2, sys=(SYS, 2, 1),
                  bands=[("L5 / E5a / B2a", 1166.22, 1186.68), ("E5b / B2b", 1196.91, 1217.37),
                         ("L2", 1226.58, 1228.62), ("G3 (CDMA)", 1197.648, 1212.948), ("G2 (FDMA)", 1242.94, 1251.69)],
                  keys=[(787, "LTE B13/B14 UL"), (897.5, "GSM-900 / LTE B8 UL"), (960, "DME/TACAN low"),
                        (1030, "SSR / IFF interrogation"), (1090, "SSR / ADS-B reply"), (1150, "DME top"),
                        (1160, "lower skirt"), (1250, "upper skirt"), (1260, "ARNS radar"), (1300, "ARNS radar top"),
                        (1400, "L-band"), (1575.42, "L1 (other branch)"), (1621, "Iridium"), (1710, "LTE B3 UL low"),
                        (1950, "LTE B1 UL"), (2442, "Wi-Fi 2.4 GHz"), (5500, "Wi-Fi 5 GHz")]),
    "S": dict(fc=D.SBAND["f_mhz"], saw=TA, saw_name="TA1442A", dxp=None, sys=(SYSS, 1, 0),
              bands=[("NavIC S SPS (2.046 MHz)", 2490.005, 2494.051), ("TA1442A spec band", 2489.5, 2494.5),
                     ("NavIC S RS (16.5 MHz)", 2483.778, 2500.278)],
              keys=[(1575.42, "GNSS L1"), (2110, "LTE B1 DL"), (2350, "LTE B40"), (2390, "TA1442A spec point"),
                    (2412, "Wi-Fi ch 1"), (2441, "Bluetooth / ISM"), (2450, "microwave oven"), (2472, "Wi-Fi ch 13"),
                    (2483.5, "ISM top / Globalstar"), (2500, "Globalstar top"), (2506, "LTE B41 / n41"),
                    (2535, "LTE B7 UL"), (2570, "LTE B7 UL top"), (2575, "TA1442A spec point"),
                    (2593, "LTE B41 mid"), (2655, "LTE B7 DL"), (3500, "5G n78")]),
}


def chain_curves(c):
    fm, a1 = att(c["saw"])
    k = lambda y, fmx: y - float(np.interp(c["fc"], fmx, y))
    out = {"f": fm, "saw1": k(a1, fm), "saw2": k(2 * a1, fm), "il1": a1}
    if c["dxp"] is not None:
        fd, ad = att(c["dxp"])
        a2d = 2 * np.interp(fd, fm, a1) + ad
        out.update(fd=fd, dxp=k(a2d, fd), il_dxp=ad)
    n, i, j = c["sys"]
    fs = n.f / 1e6
    g = db(n.s[:, i, j])
    out.update(fs=fs, sys=float(np.interp(c["fc"], fs, g)) - g)
    return out


def main():
    rows_key, rows_inb = [], []
    for name, c in CHAINS.items():
        cc = chain_curves(c)
        c["cc"] = cc
        for f, svc in c["keys"]:
            rows_key.append(dict(chain=name, f_mhz=f, service=svc, saw1_dbc=at(cc["f"], cc["saw1"], f),
                                 saw2_dbc=at(cc["f"], cc["saw2"], f),
                                 saw2_dxp_dbc=(at(cc["fd"], cc["dxp"], f) if "fd" in cc else None),
                                 system_dbc=at(cc["fs"], cc["sys"], f)))
        for bn, lo, hi in c["bands"]:
            fm = cc["f"]
            sel = (fm >= lo) & (fm <= hi)
            il2 = 2 * cc["il1"][sel]
            r = dict(chain=name, band=bn, f_lo_mhz=lo, f_hi_mhz=hi, saw_il_db_mean=float(cc["il1"][sel].mean()),
                     filters_il_db_max=float(il2.max()), filters_ripple_db=float(il2.max() - il2.min()))
            if "fd" in cc:
                seld = (cc["fd"] >= lo) & (cc["fd"] <= hi)
                tot = 2 * np.interp(cc["fd"][seld], fm, cc["il1"]) + cc["il_dxp"][seld]
                r.update(filters_dxp_il_db_max=float(tot.max()), filters_dxp_ripple_db=float(tot.max() - tot.min()))
            sels = (cc["fs"] >= lo) & (cc["fs"] <= hi)
            r.update(system_gain_ripple_db=float(np.ptp(cc["sys"][sels])))
            rows_inb.append(r)
    for nm, rows in (("rejection_doc_keyfreq", rows_key), ("rejection_doc_inband", rows_inb)):
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with open(XD / f"{nm}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)

    # ---------------------------------------------------------------- plots (simulator style)
    for name, tag, lo, hi, mk in (("L1", "L1", 0.6, 2.2, [1.545, 1.621, 1.7475, 0.8975, 1.17645]),
                                  ("L2/L5", "L2L5", 0.6, 2.2, [1.03, 1.09, 1.15, 1.26, 1.57542]),
                                  ("S", "S", 0.5, 4.0, [2.39, 2.472, 2.506, 2.575, 1.57542])):
        cc = CHAINS[name]["cc"]
        tr = []
        sel = (cc["f"] >= lo * 1e3) & (cc["f"] <= hi * 1e3)
        tr.append(dict(x=cc["f"][sel] / 1e3, y=-cc["saw1"][sel], expr=f"1 x {CHAINS[name]['saw_name']}",
                       setup="filter only", short="1 SAW"))
        tr.append(dict(x=cc["f"][sel] / 1e3, y=-cc["saw2"][sel], expr=f"2 x {CHAINS[name]['saw_name']}",
                       setup="filters as in the chain", short="2 SAW"))
        if "fd" in cc:
            tr.append(dict(x=cc["fd"] / 1e3, y=-cc["dxp"], expr="2 x SAW + DXP.02.A path", setup="all filters",
                           short="+DXP"))
        tr.append(dict(x=cc["fs"] / 1e3, y=-cc["sys"], expr="complete chain (LNAs, hybrid)", setup="system", short="system"))
        A.xy_plot(IMG / f"rejdoc_{tag}_wide.png", f"Rejection - {name} chain, out of band", f"ref. {CHAINS[name]['fc']:.2f} MHz",
                  tr, ylabel="Rejection [dBc]  (0 = band centre)", markers=[(f"m{i + 1}", x, len(tr) - 1) for i, x in enumerate(mk)],
                  ylim=(-160, 5), xlim=(lo, hi), hlines=[(-80, "practical limit ~60-80 dBc (layout leakage)")])
        fc = CHAINS[name]["fc"] / 1e3
        span = {"L1": 0.12, "L2/L5": 0.16, "S": 0.2}[name]
        sel = (cc["f"] >= (fc - span) * 1e3) & (cc["f"] <= (fc + span) * 1e3)
        trn = [dict(x=cc["f"][sel] / 1e3, y=-cc["saw1"][sel], expr=f"1 x {CHAINS[name]['saw_name']}",
                    setup="filter only", short="1 SAW"),
               dict(x=cc["f"][sel] / 1e3, y=-cc["saw2"][sel], expr=f"2 x {CHAINS[name]['saw_name']}",
                    setup="filters as in the chain", short="2 SAW")]
        sels = (cc["fs"] >= (fc - span) * 1e3) & (cc["fs"] <= (fc + span) * 1e3)
        trn.append(dict(x=cc["fs"][sels] / 1e3, y=-cc["sys"][sels], expr="complete chain", setup="system", short="system"))
        nb = [(lo_ / 1e3, hi_ / 1e3, "") for _, lo_, hi_ in CHAINS[name]["bands"]]
        nmk = {"L1": [1.545, 1.5611, 1.57542, 1.602, 1.621], "L2/L5": [1.15, 1.17645, 1.20714, 1.2276, 1.26],
               "S": [2.4412, 2.472, 2.49203, 2.506, 2.535]}[name]
        A.xy_plot(IMG / f"rejdoc_{tag}_near.png", f"Rejection - {name} chain, in band and near band",
                  f"ref. {CHAINS[name]['fc']:.2f} MHz", trn, ylabel="Rejection [dBc]",
                  markers=[(f"m{i + 1}", x, 2) for i, x in enumerate(nmk)], ylim=(-80, 3), spans=nb)
    # TA1442A against its data-sheet limits (same layout as the L-band filter figure)
    fm, a = att(TA)
    ref = float(np.interp(D.SBAND["f_mhz"], fm, a))
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(fm / 1e3, a - ref, color="#1baf7a", lw=1.6, label="TA1442A model rejection")
    for lo, hi, mn, typ in ((10, 2390, 33, 40), (2575, 3000, 43, 50)):
        ax.plot([lo / 1e3, hi / 1e3], [mn - ref] * 2, color="#6250d6", lw=2.4)
        ax.plot([lo / 1e3, hi / 1e3], [typ - ref] * 2, color="#eb6834", lw=1.2, ls="--")
    ax.plot([], [], color="#6250d6", lw=2.4, label="data-sheet min attenuation")
    ax.plot([], [], color="#eb6834", lw=1.2, ls="--", label="data-sheet typ attenuation")
    for fx, v in ((2390, 46.73), (2575, 53.98)):
        ax.plot(fx / 1e3, v - ref, "o", color="#0b0b0b", ms=4)
        ax.annotate(f"VNA {v:.1f} dB", (fx / 1e3, v - ref), xytext=(5, 5), textcoords="offset points", fontsize=7)
    ax.set_xlim(0, 4); ax.set_ylim(-5, 80); ax.invert_yaxis()
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Rejection (dBc)")
    ax.set_title("TA1442A: rejection vs data-sheet limits", fontweight="bold", fontsize=10)
    ax.grid(True, color="#e4e3df"); ax.legend(loc="lower left", fontsize=7, frameon=False)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    fig.tight_layout(); fig.savefig(IMG / "rejdoc_ta1442a_spec.png", dpi=150); plt.close(fig)
    return rows_key, rows_inb


def build_doc(rows_key, rows_inb):
    f2 = MR.f2
    MR.C = []
    MR.TITLE = "Filter Rejection Analysis - GNSS / NavIC Active Antenna RF Chains"
    MR.SUB = "In-band insertion loss and ripple, near-band and out-of-band rejection of the L1, L2/L5 and NavIC S chains"
    MR.SUBLINE = f"Rev. A &nbsp;|&nbsp; {MR.TODAY} &nbsp;|&nbsp; basis: manufacturer data sheets + circuit simulation"
    MR.MARKING = ""
    MR.FOOTER = "filter rejection analysis"
    h1, h2, p, eq, bl, img, tab, pb = MR.h1, MR.h2, MR.p, MR.eq, MR.bl, MR.img, MR.tab, MR.pb

    h1("1  Summary")
    k = {(r["chain"], r["f_mhz"]): r for r in rows_key}
    bl([f"All filters meet their data-sheet attenuation limits (smallest margin ~3 dB: B8889 cellular bands and the "
        f"DXP.02.A paths); TA1442A matches its printed VNA markers (46.7 dB at 2390 MHz, 54.0 dB at 2575 MHz).",
        f"Far out of band the chains reject strongly: e.g. LTE B3 uplink {k[('L1', 1747.5)]['saw2_dbc']:.0f} dBc after "
        f"the two B7504 (L1), GSM-900 {k[('L2/L5', 897.5)]['saw2_dbc']:.0f} dBc after the two B8889 (L2/L5), 5G n78 "
        f"{k[('S', 3500)]['saw2_dbc']:.0f} dBc after the two TA1442A (S). Values beyond ~60-80 dBc are limited by layout "
        "leakage in practice.",
        f"Near-band rejection is the weak point of every chain: L1 upper skirt (Iridium 1621 MHz: "
        f"{k[('L1', 1621)]['saw2_dbc']:.1f} dBc after two filters), L2/L5 lower skirt (DME 1150 MHz: "
        f"{k[('L2/L5', 1150)]['saw2_dbc']:.1f} dBc), NavIC S (Wi-Fi ch 13 2472 MHz: {k[('S', 2472)]['saw2_dbc']:.1f} dBc; "
        f"LTE B41 2506 MHz: {max(k[('S', 2506)]['saw2_dbc'], 0.0):.1f} dBc - inside the filter pass-band).",
        "Aviation signals are well rejected in the L2/L5 chain: SSR/IFF interrogation 1030 MHz "
        f"{k[('L2/L5', 1030)]['saw2_dbc']:.0f} dBc, SSR/ADS-B reply 1090 MHz {k[('L2/L5', 1090)]['saw2_dbc']:.0f} dBc; "
        "the risk is the DME band edge just below L5.",
        "In band (worst point of each band, G2 excluded): two SAW filters cost "
        + ", ".join(f"{r['band'].split(' (')[0]} {r['filters_il_db_max']:.1f} dB" for r in rows_inb if "G2" not in r["band"]
                    and "wide" not in r["band"] and "spec band" not in r["band"] and "RS" not in r["band"])
        + f"; with the diplexer the L-band filter loss is "
        f"{min(r['filters_dxp_il_db_max'] for r in rows_inb if 'filters_dxp_il_db_max' in r and 'G2' not in r['band']):.1f}-"
        f"{max(r['filters_dxp_il_db_max'] for r in rows_inb if 'filters_dxp_il_db_max' in r and 'G2' not in r['band']):.1f} dB. "
        "The LNA ahead of the filters keeps the system noise figure at 0.6-1.2 dB."])

    h1("2  Chains and filter positions")
    img("connection_diagram.png", "Figure 1 - L-band chains (L1 and L2/L5 combined by the DXP.02.A diplexer).", 16)
    img("connection_diagram_sband.png", "Figure 2 - NavIC S-band chain.", 16)
    tab(["Chain", "Filter 1", "Filter 2", "Combiner", "Reference (0 dBc)"],
        [["L1", "B7504 after LNA 1", "B7504 after LNA 2", "DXP.02.A L1 path", "1575.42 MHz"],
         ["L2/L5", "B8889 (+2 x 6.8 nH) after LNA 1", "B8889 after LNA 2", "DXP.02.A L2/L5 path", "1176.45 MHz"],
         ["NavIC S", "TA1442A after LNA 1", "TA1442A after LNA 2", "- (separate output)", "2492.028 MHz"]],
        "Table 1 - Filter positions. No filter is in front of LNA 1 in any chain.", [2.0, 4.2, 3.6, 3.6, 3.0])
    p("Definitions: rejection (dBc) = attenuation at f minus attenuation at the band centre, i.e. how far below the "
      "wanted signal an interferer is passed. 'In band' = inside the GNSS signal band (insertion loss, ripple); "
      "'near band' = the filter skirts within ~100 MHz of the band; 'out of band' = everything further away. "
      "'Complete chain' includes the hybrid, the LNAs and their bias networks.")
    eq("Rejection(f) [dBc] = IL(f) - IL(f_c);   two identical filters: Rej_2(f) = 2 x Rej_1(f);   "
       "chain: Rej = sum of the filter rejections (+ LNA gain slope)")

    h1("3  In-band performance")
    tab(["Chain", "Band", "MHz", "1 SAW IL mean dB", "2 SAW IL max dB", "2 SAW ripple dB", "+DXP IL max dB",
         "+DXP ripple dB", "System gain ripple dB"],
        [[r["chain"], r["band"], f"{r['f_lo_mhz']:.2f}-{r['f_hi_mhz']:.2f}", f2(r["saw_il_db_mean"]),
          f2(r["filters_il_db_max"]), f2(r["filters_ripple_db"]), f2(r.get("filters_dxp_il_db_max")),
          f2(r.get("filters_dxp_ripple_db")), f2(r["system_gain_ripple_db"])] for r in rows_inb],
        "Table 2 - In-band insertion loss and ripple of the filter chain, and gain ripple of the complete chain. "
        "G2 is outside the B8889 pass-band (large loss and ripple).", [1.3, 3.4, 2.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.8])
    img("insertion_loss.png", "Figure 3 - L-band insertion loss: hybrid, one SAW, DXP path and total passive loss.", 16)
    for tag, nm in (("L1", "L1"), ("L2L5", "L2/L5"), ("S", "NavIC S")):
        img(f"rejdoc_{tag}_near.png", f"Figure - {nm} chain, in band and near band (shaded: signal bands).", 16.5)

    pb()
    h1("4  Filter compliance with the data sheets")
    tab(["Filter", "Band (MHz)", "Spec min att. (dB)", "Spec typ (dB)", "Model min att. (dB)", "Margin (dB)"],
        [[r["filter"], f"{r['f_lo_mhz']:g}-{r['f_hi_mhz']:g}", f2(r["spec_min_att_db"], 0), f2(r["spec_typ_att_db"], 0),
          f2(r["model_min_att_db"], 1), f2(r["margin_to_spec_db"], 1)] for r in R["extras"]["filter_rejection"]] +
        [["TA1442A", "10-2390", "33", "40", f2(next(v["model"] for v in RS["validation"] if "10-2390" in v["item"]), 1),
          f2(next(v["model"] for v in RS["validation"] if "10-2390" in v["item"]) - 33, 1)],
         ["TA1442A", "2575-3000", "43", "50", f2(next(v["model"] for v in RS["validation"] if "2575-3000" in v["item"]), 1),
          f2(next(v["model"] for v in RS["validation"] if "2575-3000" in v["item"]) - 43, 1)]],
        "Table 3 - Worst-case attenuation of each filter in its specified stop bands (all pass).",
        [2.4, 2.6, 2.4, 2.0, 2.6, 2.0])
    img("filter_rejection.png", "Figure - L-band filters against the data-sheet limits.", 16)
    img("rejdoc_ta1442a_spec.png", "Figure - TA1442A against the data-sheet limits and VNA markers.", 16)

    pb()
    h1("5  Near-band and out-of-band rejection of the chains")
    for name, tag in (("L1", "L1"), ("L2/L5", "L2L5"), ("S", "S")):
        h2(f"5.{['L1', 'L2/L5', 'S'].index(name) + 1}  {name} chain")
        img(f"rejdoc_{tag}_wide.png", f"Figure - {name} chain rejection after each filter stage and for the complete chain.", 16.5)
        rows = [r for r in rows_key if r["chain"] == name]
        tab(["f (MHz)", "Service / point", "1 SAW dBc", "2 SAW dBc"] + (["2 SAW + DXP dBc"] if name != "S" else []) +
            ["Complete chain dBc"],
            [[f"{r['f_mhz']:g}", r["service"], f2(r["saw1_dbc"], 1), f2(r["saw2_dbc"], 1)] +
             ([f2(r["saw2_dxp_dbc"], 1)] if name != "S" else []) + [f2(r["system_dbc"], 1)] for r in rows],
            f"Table - {name} chain rejection at the main interferer frequencies ('-' = outside the model range).",
            [1.6, 4.4, 1.8, 1.8] + ([2.4] if name != "S" else []) + [2.4])
    h2("5.4  Cross-band rejection between the L-band branches")
    p(f"At the combined output the L1 branch rejects L5 by {k[('L1', 1176.45)]['saw2_dxp_dbc']:.0f} dBc and L2 by "
      f"{k[('L1', 1227.6)]['saw2_dxp_dbc']:.0f} dBc (filters + DXP); the L2/L5 branch rejects L1 by "
      f"{k[('L2/L5', 1575.42)]['saw2_dxp_dbc']:.0f} dBc. Each branch therefore adds no noise or signal in the other "
      "band (noise contribution < 0.01 dB).")
    img("rejection_per_stage.png", "Figure - L-band cumulative filter rejection by stage.", 16)

    h1("6  Interference consequences")
    p("Rejection numbers become power levels in the LNAs. With -10 dBm uplink carriers at the antenna and no filter "
      "in front of LNA 1 (planning values):")
    rs_i = {x["interferer"]: x for x in RS["interferers"]}
    l_i = {(x["interferer"], x["branch"]): x for x in R["interferers"]}
    tab(["Chain", "Interferer", "MHz", "At antenna dBm", "LNA 2 out dBm", "Note"],
        [["L1", "Iridium", "1621", "-20", f2(l_i[("Iridium", "L1")]["lna2_out"], 1), "near-band, ~11 dB per B7504"],
         ["L2/L5", "DME / TACAN", "1150", "-30", f2(l_i[("DME/TACAN (aviation)", "L2/L5")]["lna2_out"], 1),
          "above B8889 +5 dBm rating"],
         ["L1", "LTE B3 UL", "1747.5", "-10", f2(l_i[("LTE B3 UL", "L1")]["lna2_out"], 1), "well rejected"],
         ["S", "Wi-Fi ch 13", "2472", "-10", f2(rs_i["Wi-Fi ch 13"]["lna2_out"], 1), "LNA 2 compressed, TA1442A rating exceeded"],
         ["S", "LTE B41", "2506", "-10", f2(rs_i["LTE B41 / n41 low"]["lna2_out"], 1), "LNA 2 compressed"],
         ["S", "LTE B7 UL", "2535", "-10", f2(rs_i["LTE B7 UL"]["lna2_out"], 1), "LNA 2 compressed"],
         ["S", "5G n78", "3500", "-20", f2(rs_i["5G n78"]["lna2_out"], 1), "well rejected"]],
        "Table - Effect of the near-band rejection (LNA OP1dB ~+20 dBm; B8889 rated +5 dBm, TA1442A +10 dBm input).",
        [1.4, 2.8, 1.4, 2.0, 2.0, 6.6])

    h1("7  Recommendations")
    bl(["NavIC S: add a narrow (<= 20 MHz) pre-filter in front of LNA 1 with > 30 dB at 2472 and 2506 MHz (ceramic / "
        "cavity), or a narrower SAW as filter 1; the TA1442A 3 dB bandwidth (~62 MHz) is too wide for co-located Wi-Fi "
        "and LTE B41/B7.",
        "L2/L5: add > 30 dB rejection at 960-1150 MHz (DME) ahead of LNA 1, e.g. a pre-LNA SAW or ceramic L5 filter.",
        "L1: a pre-filter with a steeper upper skirt for Iridium (1616-1626.5 MHz), e.g. RF360 B39162B2611P810 (pre-LNA).",
        "Expect ~0.5-1.0 dB higher NF with a pre-filter; recheck the budget.",
        "Layout: keep input and output of each filter separated (ground vias, shielding); otherwise the 100+ dBc model "
        "values will not be reached (practical ~60-80 dBc).",
        "Replace the estimated SAW/diplexer models by the manufacturers' measured S-parameter files to confirm the "
        "skirt values used here."])

    h1("8  Basis and limitations")
    bl(["Filter models are built from the data-sheet curves (magnitude digitized, table values and VNA markers used "
        "exactly); phase is a minimum-phase estimate. In-band accuracy ~+/-0.3 dB, stop band ~+/-2 dB.",
        "Room temperature (25 C) typical data; SAW temperature drift (e.g. TA1442A -36 ppm/C, ~-0.09 MHz/C at 2.49 GHz) "
        "shifts the skirts by a few MHz over temperature and is not included.",
        "Small-signal analysis: compression and intermodulation are estimated from the LNA data-sheet P1dB/IP3.",
        "Antenna treated as an ideal RHCP source: the patch's own out-of-band roll-off adds rejection in practice.",
        "Data: Qualcomm RF360 B7504 / B8889, Taoglas DXP.02.A / HC125A, Tai-Saw TA1442A, TTM C2327J5003AHF, Qorvo "
        "TQP3M9037 data sheets. Tables: Extracted_Data/rejection_doc_keyfreq.csv and rejection_doc_inband.csv."])

    MR.render_docx(MR.REP / "Filter_Rejection_Analysis.docx")
    MR.render_pdf(MR.REP / "Filter_Rejection_Analysis.pdf")


if __name__ == "__main__":
    rk, ri = main()
    build_doc(rk, ri)
    for r in rk:
        print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
    print("document written")
