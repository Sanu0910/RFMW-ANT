"""Graphics-first internal design brief (Bharat Electronics, RFM / Antenna Group, CRL-BG):
multi-band GNSS / NavIC active antenna RF front end. Few words; tables and plots.

Outputs: ../Report/BEL_CRL_ActiveAntenna_RF_Brief.pdf and .docx
Uses the renderers of make_report.py with the group logo (Images/bel_logo.png) and internal marking.
"""
import csv
import json

import make_report as MR

ROOT = MR.ROOT
R = json.loads((ROOT / "Scripts" / "results.json").read_text())
RS = json.loads((ROOT / "Scripts" / "results_sband.json").read_text())
EX, SS = R["extras"], RS["summary"]
f2 = MR.f2
KEY = {(r["chain"], float(r["f_mhz"])): r for r in csv.DictReader(open(ROOT / "Extracted_Data" / "rejection_doc_keyfreq.csv"))}

MR.C = []
MR.TITLE = "Multi-band GNSS / NavIC Active Antenna - RF Front End"
MR.SUB = "Design brief: architecture, simulated performance, filter rejection, interference (L1, L2/L5, NavIC S)"
MR.SUBLINE = f"Doc. No.: ________ &nbsp;|&nbsp; Rev.: Draft A &nbsp;|&nbsp; {MR.TODAY}"
MR.GROUP = "RFM / Antenna Group, CRL-BG"
MR.LOGO = ROOT / "Images" / "bel_logo.png"
MR.MARKING = "BEL INTERNAL - FOR INTERNAL CIRCULATION ONLY"
MR.FOOTER = "RFM / Antenna Group, CRL-BG"
h1, h2, p, bl, img, tab, pb = MR.h1, MR.h2, MR.p, MR.bl, MR.img, MR.tab, MR.pb

prm = {r["band"]: r for r in EX["rf_parameters"]}
summ = {r["band"]: r for r in R["summary"]}

tab(["Item", "Entry"],
    [["Prepared by", "RFM / Antenna Group, CRL-BG"], ["Prepared / Checked / Approved", "________ / ________ / ________"],
     ["Basis", "Manufacturer data sheets + circuit simulation (no hardware measurement yet)"],
     ["Distribution", "BEL internal only"]], "Document control.", [5.0, 11.2])

h1("1  Key numbers")
rows = []
for name, b in (("L1 / E1 / B1C", "L1/E1/B1C"), ("B1I", "B1I"), ("G1", "G1"), ("L5 / E5a / B2a", "L5/E5a/B2a"),
                ("E5b / B2b", "E5b/B2b"), ("L2", "L2")):
    r, s = prm[b], summ[b]
    rows.append([name, f2(r["f_mhz"], 2), f2(r["gain_db"], 1), f2(r["nf_db"]), f2(s["vswr_in"]), f2(s["vswr_out"]),
                 f2(s["gain_ripple_db"]), (f2(r["iip3_dbm"], 1) if "iip3_dbm" in r else "-"),
                 (f2(r["op1db_out_dbm"], 1) if "op1db_out_dbm" in r else "-"),
                 (f2(r["cn0_dbhz"], 1) if "cn0_dbhz" in r else "-")])
rows.append(["NavIC S", "2492.03", f2(SS["gain_db"], 1), f2(SS["nf_db"]), f2(SS["vswr_in"]), f2(SS["vswr_out"]),
             f2(SS["ripple_sps_db"]), f2(SS["iip3_dbm"], 1), f2(SS["op1db_out_dbm"], 1), f2(SS["cn0_dbhz"], 1)])
tab(["Band", "MHz", "Gain dB", "NF dB", "VSWR in", "VSWR out", "Ripple dB", "IIP3 dBm", "OP1dB dBm", "C/N0 dB-Hz"],
    rows, "Table 1 - Simulated performance at 25 C (antenna feed RHCP -> RF output, 50 ohm).",
    [2.6, 1.4, 1.3, 1.1, 1.2, 1.3, 1.3, 1.4, 1.5, 1.5])
tab(["Parameter", "L-band", "NavIC S"],
    [["Stability", "unconditional (mu >= 1.035)", f"unconditional (mu >= {SS['mu_min']:.3f})"],
     ["Reverse isolation", f"{prm['L1/E1/B1C']['reverse_iso_db']:.0f} / {prm['L5/E5a/B2a']['reverse_iso_db']:.0f} dB", f"{SS['reverse_iso_db']:.0f} dB"],
     ["LHCP rejection / AR (hybrid)", f"{prm['L1/E1/B1C']['xpd_db']:.1f} dB / {prm['L1/E1/B1C']['ar_db']:.2f} dB",
      f"{SS['xpd_db']:.1f} dB / {SS['ar_db']:.2f} dB"],
     ["Output noise power", f"{EX['output_noise_total_dbm']:.1f} dBm", f"{SS['output_noise_dbm']:.1f} dBm"],
     ["Worst-case gain (data-sheet limits)", "33 - 45 dB", "-"],
     ["DC", "4 x TQP3M9037, 70 mA @ 5 V", "2 x TQP3M9037, 70 mA @ 5 V"],
     ["Total DC", "420 mA @ +5 V = 2.1 W", ""]], "Table 2 - System parameters.", [5.0, 6.0, 5.2])

pb()
h1("2  Architecture")
img("connection_diagram.png", "Figure 1 - L1 and L2/L5 chains, combined in the DXP.02.A.", 17)
img("connection_diagram_sband.png", "Figure 2 - NavIC S-band chain (separate output).", 17)
img("schematic_system.png", "Figure 3 - L-band simulation schematic.", 17)
img("schematic_sband.png", "Figure 4 - S-band simulation schematic.", 17)
img("schematic_lna_stage.png", "Figure 5 - LNA stage and bias network.", 13)

pb()
h1("3  L-band results")
for fn, cap in (("lband_gain.png", "Gain"), ("lband_nf.png", "Noise figure"),
                ("lband_sparams_L1.png", "L1 branch S-parameters"), ("lband_sparams_L2L5.png", "L2/L5 branch S-parameters"),
                ("lband_vswr.png", "VSWR"), ("lband_smith.png", "Port reflections"),
                ("lband_stability.png", "Stability"), ("lband_group_delay.png", "Group delay (estimate)"),
                ("lband_wideband.png", "Wide-band transmission")):
    img(fn, f"Figure - {cap}.", 16.5)

pb()
h1("4  NavIC S-band results")
for fn, cap in (("sband_gain_inband.png", "Gain"), ("sband_nf.png", "Noise figure"), ("sband_sparams.png", "S-parameters"),
                ("sband_vswr.png", "VSWR"), ("sband_smith.png", "Reflections"), ("sband_stability.png", "Stability"),
                ("sband_group_delay.png", "Group delay (estimate)"), ("sband_wideband.png", "Wide-band transmission")):
    img(fn, f"Figure - {cap}.", 16.5)

pb()
h1("5  Filter rejection")
KEYROWS = list(csv.DictReader(open(ROOT / "Extracted_Data" / "rejection_doc_keyfreq.csv")))
inb = list(csv.DictReader(open(ROOT / "Extracted_Data" / "rejection_doc_inband.csv")))


def v(x):
    return "-" if x in ("", None) else f"{max(float(x), 0.0):.1f}"


def keytable(chain, cap, dxp=True):
    rows_ = [r for r in KEYROWS if r["chain"] == chain]
    tab(["MHz", "Service / point", "1 SAW dBc", "2 SAW dBc"] + (["2 SAW + DXP dBc"] if dxp else []) +
        ["Complete chain dBc"],
        [[f"{float(r['f_mhz']):g}", r["service"], v(r["saw1_dbc"]), v(r["saw2_dbc"])] +
         ([v(r["saw2_dxp_dbc"])] if dxp else []) + [v(r["system_dbc"])] for r in rows_],
        cap, [1.4, 4.4, 1.8, 1.8] + ([2.4] if dxp else []) + [2.4])


h2("5.1  L-band filters vs data-sheet limits")
img("filter_rejection.png", "Figure - B7504, B8889 (+2 x 6.8 nH) and DXP.02.A paths vs data-sheet limits (all met).", 16.5)
tab(["Filter", "Stop band (MHz)", "Spec min dB", "Spec typ dB", "Model min dB", "Margin dB"],
    [[r["filter"], f"{r['f_lo_mhz']:g}-{r['f_hi_mhz']:g}", f2(r["spec_min_att_db"], 0), f2(r["spec_typ_att_db"], 0),
      f2(r["model_min_att_db"], 1), f2(r["margin_to_spec_db"], 1)] for r in EX["filter_rejection"]],
    "Table 3 - L-band filter compliance (worst point in each specified stop band).", [2.4, 2.8, 2.0, 2.0, 2.2, 2.0])
img("filter_rejection_skirts.png", "Figure - L-band SAW skirts next to the GNSS bands (one and two filters).", 16.5)

pb()
h2("5.2  L1 chain")
img("rejdoc_L1_near.png", "Figure - L1 chain: in band and near band (B1I, L1/E1, G1 shaded).", 16.5)
img("rejdoc_L1_wide.png", "Figure - L1 chain: out of band, per filter stage.", 16.5)
keytable("L1", "Table 4 - L1 chain rejection (dBc rel. 1575.42 MHz; '-' = outside model range; practical limit ~60-80 dBc).")

pb()
h2("5.3  L2/L5 chain")
img("rejdoc_L2L5_near.png", "Figure - L2/L5 chain: in band and near band (L5/E5a, E5b, L2, G2 shaded).", 16.5)
img("rejdoc_L2L5_wide.png", "Figure - L2/L5 chain: out of band, per filter stage.", 16.5)
keytable("L2/L5", "Table 5 - L2/L5 chain rejection (dBc rel. 1176.45 MHz).")
k = {(r["chain"], float(r["f_mhz"])): r for r in KEYROWS}
tab(["Path", "At", "Rejection (filters + DXP)"],
    [["L1 branch", "L5 1176.45 MHz", f"{float(k[('L1', 1176.45)]['saw2_dxp_dbc']):.0f} dBc"],
     ["L1 branch", "L2 1227.60 MHz", f"{float(k[('L1', 1227.6)]['saw2_dxp_dbc']):.0f} dBc"],
     ["L2/L5 branch", "L1 1575.42 MHz", f"{float(k[('L2/L5', 1575.42)]['saw2_dxp_dbc']):.0f} dBc"]],
    "Table 6 - Cross-band rejection between the L-band branches at the combined output (model).", [4.0, 5.0, 5.0])
img("rejection_per_stage.png", "Figure - L-band cumulative filter rejection: SAW 1, SAW 2, SAW 2 + DXP.", 16.5)
img("insertion_loss.png", "Figure - L-band in-band insertion loss: hybrid, one SAW, DXP path, total passive.", 16.5)
tab(["Chain", "Band", "1 SAW IL dB", "2 SAW IL max dB", "+DXP IL max dB", "+DXP ripple dB", "System ripple dB"],
    [[r["chain"], r["band"], f"{float(r['saw_il_db_mean']):.2f}", f"{float(r['filters_il_db_max']):.2f}",
      f"{float(r['filters_dxp_il_db_max']):.2f}", f"{float(r['filters_dxp_ripple_db']):.2f}",
      f"{float(r['system_gain_ripple_db']):.2f}"] for r in inb if r["chain"] != "S"],
    "Table 7 - L-band in-band filter loss and ripple (G2 lies outside the B8889 pass-band).",
    [1.4, 4.4, 1.8, 2.0, 2.0, 2.0, 2.0])

pb()
h2("5.4  NavIC S chain")
img("rejdoc_ta1442a_spec.png", "Figure - TA1442A vs data-sheet limits and VNA markers (met).", 16)
img("rejdoc_S_near.png", "Figure - NavIC S chain: in band and near band.", 16.5)
img("rejdoc_S_wide.png", "Figure - NavIC S chain: out of band, per filter stage.", 16.5)
keytable("S", "Table 8 - NavIC S chain rejection (dBc rel. 2492.028 MHz).", dxp=False)
tab(["Band", "1 SAW IL dB", "2 SAW IL max dB", "System ripple dB"],
    [[r["band"], f"{float(r['saw_il_db_mean']):.2f}", f"{float(r['filters_il_db_max']):.2f}",
      f"{float(r['system_gain_ripple_db']):.2f}"] for r in inb if r["chain"] == "S"],
    "Table 9 - NavIC S in-band filter loss and ripple.", [6.0, 2.4, 2.6, 2.6])

pb()
h1("6  Interference")
rs_i = {x["interferer"]: x for x in RS["interferers"]}
l_i = {(x["interferer"], x["branch"]): x for x in R["interferers"]}
tab(["Chain", "Interferer", "MHz", "At antenna dBm", "LNA 2 out dBm", "Status"],
    [["L1", "Iridium", "1621", "-20", f2(l_i[("Iridium", "L1")]["lna2_out"], 1), "near band - watch"],
     ["L1", "LTE B3 UL", "1747.5", "-10", f2(l_i[("LTE B3 UL", "L1")]["lna2_out"], 1), "OK"],
     ["L2/L5", "DME / TACAN", "1150", "-30", f2(l_i[("DME/TACAN (aviation)", "L2/L5")]["lna2_out"], 1), "RISK - above B8889 rating"],
     ["L2/L5", "GSM-900", "897.5", "-10", f2(l_i[("GSM-900 / LTE B8 UL", "L2/L5")]["lna2_out"], 1), "OK"],
     ["S", "Wi-Fi ch 13", "2472", "-10", f2(rs_i["Wi-Fi ch 13"]["lna2_out"], 1), "RISK - LNA 2 compressed"],
     ["S", "LTE B41", "2506", "-10", f2(rs_i["LTE B41 / n41 low"]["lna2_out"], 1), "RISK - LNA 2 compressed"],
     ["S", "LTE B7 UL", "2535", "-10", f2(rs_i["LTE B7 UL"]["lna2_out"], 1), "RISK - LNA 2 compressed"],
     ["S", "5G n78", "3500", "-20", f2(rs_i["5G n78"]["lna2_out"], 1), "OK"]],
    "Table 10 - Interferer level at LNA 2 output (LNA OP1dB ~+20 dBm; B8889 +5 dBm, TA1442A +10 dBm max input).",
    [1.4, 2.8, 1.4, 2.0, 2.0, 6.6])
img("sband_rejection.png", "Figure - NavIC S chain rejection with the ISM / LTE bands.", 16.5)
img("lband_rejection.png", "Figure - L-band chain rejection with DME / Iridium / LTE.", 16.5)

pb()
h1("7  Cascade budgets")
for case, rows_ in list(R["budgets"].items()) + [("NavIC S (2492.028 MHz, 2.046 MHz)", RS["budget"])]:
    tab(["Stage", "G dB", "NF dB", "Cum G", "Cum NF", "Cum IIP3", "Cum IP1dB", "Signal dBm", "Noise dBm"],
        [[r["stage"], f2(r["gain_db"]), f2(r["nf_db"]), f2(r["cum_gain_db"]), f2(r["cum_nf_db"]),
          f2(r["cum_iip3_dbm"], 1), f2(r["cum_iip1db_dbm"], 1), f2(r["signal_dbm"], 1), f2(r["noise_dbm"], 1)]
         for r in rows_], f"Cascade - {case}.", [4.4, 1.2, 1.2, 1.2, 1.2, 1.4, 1.5, 1.6, 1.6])
img("level_diagram.png", "Figure - Level diagram (minimum signal and noise), L-band.", 16)

h1("8  Actions")
bl(["NavIC S: narrow pre-filter (<= 20 MHz, > 30 dB at 2472 / 2506 MHz) before LNA 1.",
    "L2/L5: > 30 dB at 960-1150 MHz (DME) before LNA 1.  L1: steeper upper skirt for Iridium.",
    "Reduce gain to 25-30 dB at the connector (one LNA per branch or a pad).",
    "Improve L1 / E5b input match (VSWR 2.3-2.75).",
    "Get measured S-parameters from the vendors; confirm TA1442A availability (2011 data sheet).",
    "Run the AEDT project on the licensed workstation; replace the ideal patch by HFSS data."])

h1("9  Parts")
tab(["Part", "Maker", "Use", "Qty"],
    [["TQP3M9037", "Qorvo", "LNA, 0.4 dB NF, 5 V / 70 mA", "6"], ["HC125A", "Taoglas", "L-band 3 dB hybrid", "2"],
     ["B7504", "Qualcomm RF360", "L1 SAW", "2"], ["B8889", "Qualcomm RF360", "L2/L5 SAW (+2 x 6.8 nH)", "2"],
     ["DXP.02.A", "Taoglas", "L-band diplexer (combiner)", "1"], ["C2327J5003AHF", "TTM / Xinger", "S-band 3 dB hybrid", "1"],
     ["TA1442A", "Tai-Saw", "2492 MHz SAW", "2"], ["Patch elements", "-", "antenna (ideal in simulation)", "3"]],
    "Table 11 - Parts.", [3.4, 3.2, 7.2, 1.2])

if __name__ == "__main__":
    MR.render_docx(MR.REP / "BEL_CRL_ActiveAntenna_RF_Brief.docx")
    MR.render_pdf(MR.REP / "BEL_CRL_ActiveAntenna_RF_Brief.pdf")
    print("brief written")
