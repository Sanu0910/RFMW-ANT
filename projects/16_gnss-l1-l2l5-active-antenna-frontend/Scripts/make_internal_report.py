"""Internal technical note (BEL internal circulation): multi-band GNSS / NavIC active antenna front end,
L1 + L2/L5 (combined output) and NavIC S-band (separate output), with simulator-style result plots.

Outputs: ../Report/Internal_ActiveAntenna_RF_Technical_Note.pdf and .docx
Uses the renderers of make_report.py (same content model, classification marking on every page).
"""
import json
import math

import make_report as MR
import build_extracted as X
import ds_data as D

ROOT = MR.ROOT
R = json.loads((ROOT / "Scripts" / "results.json").read_text())
RS = json.loads((ROOT / "Scripts" / "results_sband.json").read_text())
EX = R["extras"]
SS = RS["summary"]
f2 = MR.f2

MR.C = []
MR.TITLE = "Multi-band GNSS / NavIC Active Antenna - RF Front End"
MR.SUB = "Technical note: architecture, simulated RF performance, interference risk and actions (L1, L2/L5, NavIC S)"
MR.SUBLINE = f"Doc. No.: ________ &nbsp;|&nbsp; Rev.: Draft A &nbsp;|&nbsp; Date: {MR.TODAY}"
MR.MARKING = "BEL INTERNAL - FOR INTERNAL CIRCULATION ONLY - NOT FOR EXTERNAL DISTRIBUTION"
MR.FOOTER = "internal technical note"
h1, h2, p, eq, bl, img, tab, pb = MR.h1, MR.h2, MR.p, MR.eq, MR.bl, MR.img, MR.tab, MR.pb

prm = {r["band"]: r for r in EX["rf_parameters"]}
L1, L5, E5b, L2 = prm["L1/E1/B1C"], prm["L5/E5a/B2a"], prm["E5b/B2b"], prm["L2"]
summ = {r["band"]: r for r in R["summary"]}

tab(["Field", "Entry"],
    [["Document", "Technical note - RF front end of the multi-band active antenna"],
     ["Document No. / Rev.", "________ / Draft A"],
     ["Prepared / Checked / Approved", "________ / ________ / ________"],
     ["Classification", "BEL internal. Technical details for internal circulation only."],
     ["Basis", "Manufacturer data sheets of the selected parts (listed in section 9); circuit simulation. "
               "No hardware measurement yet."]],
    "Document control.", [4.2, 12.0])

h1("1  Scope")
p("This note gives the RF design data of the active antenna front end: the antenna element is only mentioned "
  "(dual-feed RHCP patch per band, modelled as an ideal source); everything behind the feeds - hybrid combiners, "
  "LNAs, SAW filters and the band combiner - is modelled from the manufacturer data and simulated. Three bands: "
  "GNSS L1 (B1I/L1/E1/G1) and L2/L5 (L5/E5a/E5b/L2) on one combined output, and NavIC S-band (2492.028 MHz) on a "
  "separate output. All LNAs at +5 V.")

h1("2  Architecture")
img("connection_diagram.png", "Figure 1 - L-band chain (two branches combined in the DXP.02.A).")
img("connection_diagram_sband.png", "Figure 2 - NavIC S-band chain (separate output).")
img("schematic_system.png", "Figure 3 - Simulation schematic, L-band (design FrontEnd_3port).", 17)
img("schematic_sband.png", "Figure 4 - Simulation schematic, S-band (design SBand_2port).", 17)
img("schematic_lna_stage.png", "Figure 5 - L-band LNA stage with bias network (S-band stage: Qorvo 2.3-2.6 GHz "
    "reference design, 2.7 nH shunt + 2.4 pF series input match, 5.6 nH choke).", 14)

pb()
h1("3  Performance summary")
rows = []
for name, r, b in (("L1/E1/B1C 1575.42", L1, summ["L1/E1/B1C"]), ("B1I 1561.10", prm["B1I"], summ["B1I"]),
                   ("G1 1602.00", prm["G1"], summ["G1"]), ("L5/E5a 1176.45", L5, summ["L5/E5a/B2a"]),
                   ("E5b/B2b 1207.14", E5b, summ["E5b/B2b"]), ("L2 1227.60", L2, summ["L2"])):
    rows.append([name, f2(r["gain_db"], 1), f2(r["nf_db"]), f2(b["vswr_in"]), f2(b["vswr_out"]),
                 f2(b["gain_ripple_db"]), f2(r["gd_ns"], 1),
                 (f2(r.get("iip3_dbm"), 1) if "iip3_dbm" in r else "-"),
                 (f2(r.get("op1db_out_dbm"), 1) if "op1db_out_dbm" in r else "-"),
                 (f2(r.get("cn0_dbhz"), 1) if "cn0_dbhz" in r else "-")])
rows.append(["NavIC S 2492.028", f2(SS["gain_db"], 1), f2(SS["nf_db"]), f2(SS["vswr_in"]), f2(SS["vswr_out"]),
             f2(SS["ripple_sps_db"]), f2(SS["gd_ns"], 1), f2(SS["iip3_dbm"], 1), f2(SS["op1db_out_dbm"], 1),
             f2(SS["cn0_dbhz"], 1)])
tab(["Band / MHz", "Gain dB", "NF dB", "VSWR in", "VSWR out", "Ripple dB", "GD ns", "IIP3 dBm", "OP1dB dBm",
     "C/N0 dB-Hz"], rows,
    "Table 1 - Simulated performance, 25 C typical, 50 ohm, from the antenna feed (RHCP) to the RF output. "
    "Ripple over the signal bandwidth; C/N0 for the minimum specified signal with the antenna at 290 K.",
    [3.2, 1.3, 1.1, 1.3, 1.3, 1.3, 1.1, 1.4, 1.5, 1.5])
tab(["Item", "L-band", "S-band"],
    [["Stability", f"unconditional; branch mu >= {min(R['stability']['branch_l1_mu_min'], R['stability']['branch_l2_mu_min']):.3f}",
      f"unconditional; mu >= {SS['mu_min']:.3f}, stage mu >= {SS['stage_mu_min']:.2f}"],
     ["Reverse isolation", f"{L1['reverse_iso_db']:.0f} dB (L1), {L5['reverse_iso_db']:.0f} dB (L5)", f"{SS['reverse_iso_db']:.0f} dB"],
     ["Cross-pol (LHCP) rejection of hybrid", f"{L1['xpd_db']:.1f} dB (L1), {L5['xpd_db']:.1f} dB (L5)", f"{SS['xpd_db']:.1f} dB"],
     ["Axial-ratio contribution of hybrid", f"{L1['ar_db']:.2f} dB (L1), {L5['ar_db']:.2f} dB (L5)", f"{SS['ar_db']:.2f} dB"],
     ["Output noise power (whole band)", f"{EX['output_noise_total_dbm']:.1f} dBm", f"{SS['output_noise_dbm']:.1f} dBm"],
     ["3 dB bandwidth", "L1 ~1553-1613 MHz, L2/L5 ~1156-1243 MHz", f"~{SS['bw_3db_mhz']:.0f} MHz (TA1442A is wide)"],
     ["Inter-band group delay", f"L1 - L5 = {EX['gd_l1_minus_l5_ns']:.1f} ns (estimate)", "-"],
     ["Worst-case gain range (data-sheet limits)", "33-45 dB, NF <= 0.98 dB", "-"],
     ["Supply", "4 x TQP3M9037, 70 mA each at 5 V", "2 x TQP3M9037, 70 mA each at 5 V"],
     ["Total DC", "6 LNAs: 420 mA at +5 V = 2.1 W", ""]],
    "Table 2 - Other parameters.", [5.0, 6.6, 4.8])

h1("4  L-band results (simulator plots)")
for fn, cap in (("lband_sparams_L1.png", "L1 branch: S31 (gain), S11, S33, S13."),
                ("lband_sparams_L2L5.png", "L2/L5 branch: S32, S22, S33, S23."),
                ("lband_gain.png", "Gain in the GNSS bands with markers at the signal centres."),
                ("lband_nf.png", "Noise figure."), ("lband_vswr.png", "VSWR at the three ports."),
                ("lband_smith.png", "Port reflections on the Smith chart."),
                ("lband_stability.png", "Stability factors K and mu."),
                ("lband_group_delay.png", "Group delay (estimated phase of SAW/diplexer models)."),
                ("lband_wideband.png", "Wide-band transmission 0.6-2.2 GHz."),
                ("lband_rejection.png", "Rejection in dBc relative to the band-centre gain.")):
    img(fn, "Figure - " + cap, 16.5)

pb()
h1("5  NavIC S-band results (simulator plots)")
for fn, cap in (("sband_sparams.png", "S-band branch: S21, S11, S22, S12 with markers at 2492.028 MHz and at "
                 "the TA1442A specification points 2390 / 2575 MHz."),
                ("sband_gain_inband.png", "In-band gain; markers on Wi-Fi channel 13 (2472 MHz), NavIC centre and "
                 "LTE B41 (2506 MHz)."),
                ("sband_nf.png", "Noise figure and LNA NFmin."), ("sband_vswr.png", "VSWR."),
                ("sband_smith.png", "Input / output reflection."), ("sband_stability.png", "Stability."),
                ("sband_group_delay.png", "Group delay (estimated)."),
                ("sband_wideband.png", "Wide-band transmission 0.5-4 GHz."),
                ("sband_rejection.png", "Rejection relative to 2492.028 MHz.")):
    img(fn, "Figure - " + cap, 16.5)
tab(["Stage", "G dB", "NF dB", "Cum G", "Cum NF", "Cum IIP3 dBm", "Cum IP1dB dBm", "Signal dBm", "Noise dBm"],
    [[r["stage"], f2(r["gain_db"]), f2(r["nf_db"]), f2(r["cum_gain_db"]), f2(r["cum_nf_db"]),
      f2(r["cum_iip3_dbm"], 1), f2(r["cum_iip1db_dbm"], 1), f2(r["signal_dbm"], 1), f2(r["noise_dbm"], 1)]
     for r in RS["budget"]],
    "Table 3 - S-band cascade at 2492.028 MHz (signal = -132.3 dBm reference minimum, noise in 2.046 MHz).",
    [4.4, 1.2, 1.2, 1.2, 1.2, 1.6, 1.8, 1.6, 1.6])

h1("6  Cascade budgets, L-band")
for case, rows_ in R["budgets"].items():
    tab(["Stage", "G dB", "NF dB", "Cum G", "Cum NF", "Cum IIP3 dBm", "Cum IP1dB dBm", "Signal dBm", "Noise dBm"],
        [[r["stage"], f2(r["gain_db"]), f2(r["nf_db"]), f2(r["cum_gain_db"]), f2(r["cum_nf_db"]),
          f2(r["cum_iip3_dbm"], 1), f2(r["cum_iip1db_dbm"], 1), f2(r["signal_dbm"], 1), f2(r["noise_dbm"], 1)]
         for r in rows_], f"Cascade - {case}.", [4.4, 1.2, 1.2, 1.2, 1.2, 1.6, 1.8, 1.6, 1.6])

pb()
h1("7  Interference and filtering")
p("Interferer levels at the antenna feed are planning values for a co-located terminal (cellular / Wi-Fi uplink "
  "-10 dBm). 'Back-off' is LNA OP1dB minus the level at that LNA output; negative = LNA in compression. The TA1442A "
  "is rated +10 dBm input, the B8889 +5 dBm.")
tab(["Interferer", "MHz", "P ant", "LNA1 out", "SAW1 out", "LNA2 out", "RF out", "Back-off LNA2", "SAW2 margin"],
    [[x["interferer"], f2(x["f_mhz"], 1), f2(x["p_ant_dbm"], 0), f2(x["lna1_out"], 1), f2(x["saw1_out"], 1),
      f2(x["lna2_out"], 1), f2(x["rf_out"], 1), f2(x["lna2_backoff_db"], 1), f2(x["saw2_in_vs_10dbm_rating_db"], 1)]
     for x in RS["interferers"]],
    "Table 4 - S-band branch, interferer levels in dBm at each node.", [3.6, 1.3, 1.1, 1.4, 1.4, 1.4, 1.3, 1.6, 1.6])
tab(["Interferer", "MHz", "Branch", "P ant", "LNA1 out", "LNA2 out", "RF out", "Back-off LNA1", "Back-off LNA2"],
    [[x["interferer"], f2(x["f_mhz"], 1), x["branch"], f2(x["p_ant_dbm"], 0), f2(x["lna1_out"], 1),
      f2(x["lna2_out"], 1), f2(x["rf_out"], 1), f2(x["lna1_backoff_db"], 1), f2(x["lna2_backoff_db"], 1)]
     for x in R["interferers"] if x["rf_out"] > -100 or x["lna2_backoff_db"] < 30],
    "Table 5 - L-band branches, cases that reach the output or load LNA 2.", [3.4, 1.2, 1.2, 1.1, 1.4, 1.4, 1.3, 1.6, 1.6])
img("filter_rejection_skirts.png", "Figure - L-band SAW skirts next to the GNSS bands (one and two filters).", 16)
img("filter_rejection.png", "Figure - L-band filter rejection against the data-sheet limits (all met).", 16)
img("sband_ta1442a.png", "Figure - TA1442A model with the data-sheet VNA marker points (2390 / 2489.5 / 2494.5 / 2575 MHz).", 16)

h1("8  Findings")
wifi = next(x for x in RS["interferers"] if x["interferer"] == "Wi-Fi ch 13")
b41 = next(x for x in RS["interferers"] if x["interferer"].startswith("LTE B41 / n41 low"))
dme = next(x for x in R["interferers"] if x["interferer"].startswith("DME") and x["branch"] == "L2/L5")
iri = next(x for x in R["interferers"] if x["interferer"] == "Iridium" and x["branch"] == "L1")
bl([f"Noise figure is set by the hybrid and LNA 1: L1 {L1['nf_db']:.2f} dB, L5 {L5['nf_db']:.2f} dB, "
    f"S {SS['nf_db']:.2f} dB. The S-band hybrid (0.43 dB modelled) and the reference-design input match cost "
    "~0.8 dB more than at L-band.",
    f"Gain is high: {L1['gain_db']:.1f} dB (L1), {L5['gain_db']:.1f} dB (L5), {SS['gain_db']:.1f} dB (S); worst case "
    "spread from data-sheet limits ~12 dB.",
    f"S-band selectivity is the main risk: the TA1442A 3 dB bandwidth is ~{SS['bw_3db_mhz']:.0f} MHz. A Wi-Fi channel 13 "
    f"carrier at -10 dBm drives LNA 2 to {wifi['lna2_out']:+.1f} dBm (compressed, {wifi['lna2_backoff_db']:.1f} dB "
    f"back-off) and exceeds the TA1442A +10 dBm rating at SAW 2 by {-wifi['saw2_in_vs_10dbm_rating_db']:.1f} dB; "
    f"LTE B41 at 2506 MHz behaves the same ({b41['lna2_out']:+.1f} dBm).",
    f"L2/L5: DME/TACAN at 1150 MHz is passed by the B8889 lower skirt; -30 dBm gives {dme['lna2_out']:+.1f} dBm at LNA 2 "
    "(above the B8889 +5 dBm rating).",
    f"L1: Iridium at 1621 MHz is attenuated only ~11 dB per B7504; -20 dBm gives {iri['lna2_out']:+.1f} dBm at LNA 2.",
    "Input match: L1 and E5b input VSWR 2.3-2.75 (LNA S11 reflected through the hybrid); S-band input match is good "
    f"(VSWR {SS['vswr_in']:.2f}) thanks to the reference-design input network.",
    "GLONASS G2 is outside the B8889 pass-band (gain falls 12 dB across G2).",
    "All stages unconditionally stable; three independent solvers agree to < 0.01 dB (L-band)."])

h1("9  Actions / recommendations")
bl(["S-band: add a narrow pre-filter in front of LNA 1 (ceramic or cavity, <= 20 MHz, > 30 dB at 2472 and 2506 MHz), "
    "or replace the first TA1442A by a narrower NavIC S filter and move it ahead of LNA 1. Re-check NF (expect +1 dB).",
    "L2/L5: add a DME/L-band notch or pre-filter (> 30 dB at 960-1150 MHz). L1: steeper upper skirt for Iridium "
    "(e.g. RF360 B39162B2611P810 pre-LNA).",
    "Reduce gain to the receiver requirement (25-30 dB at the connector): one LNA per branch or a pad after LNA 2.",
    "Improve the L-band input match (Qorvo optimised-RL network or AN #18 two-step matching).",
    "Obtain measured S-parameter files: RF360 (B7504, B8889), Taoglas (HC125A, DXP.02.A), Tai-Saw (TA1442A), "
    "TTM (C2327J5003AHF), Qorvo (fine-step TQP3M9037 + low-band noise data). Confirm TA1442A is still in production "
    "(approval sheet dated 2011).",
    "Replace the ideal patch with the HFSS/measured antenna S-parameters; then axial ratio and gain/temperature can be "
    "assessed.",
    "Run the AEDT project (Scripts/aedt_circuit.py) on the licensed workstation to confirm in the company tool."])

h1("10  Parts and data used")
tab(["Part", "Maker", "Function", "Data used"],
    [["TQP3M9037", "Qorvo", "LNA, 6 used", "S-parameter + noise tables (5 V), eval / reference designs"],
     ["HC125A", "Taoglas", "L-band 3 dB hybrid, 2 used", "typical table"],
     ["B7504", "Qualcomm RF360", "L1 SAW, 2 used", "spec table + digitized plots"],
     ["B8889", "Qualcomm RF360", "L2/L5 SAW, 2 used (+2 x 6.8 nH each)", "spec table + digitized plots"],
     ["DXP.02.A", "Taoglas", "L-band diplexer / combiner, 1 used", "spec table + digitized plots"],
     ["C2327J5003AHF", "TTM (Xinger)", "S-band 3 dB hybrid, 1 used", "spec table + digitized plots"],
     ["TA1442A", "Tai-Saw", "2492 MHz SAW, 2 used", "spec table + digitized VNA plots"],
     ["Patch elements", "-", "antenna (mentioned only)", "ideal dual-feed RHCP source"]],
    "Table 6 - Parts.", [3.0, 2.8, 4.8, 5.6])
tab(["ID", "Item", "Assumption", "How to close"], [list(a) for a in X.ASSUMPTIONS],
    "Table 7 - Assumptions.", [1.0, 2.6, 8.6, 4.0])
tab(["ID", "Where", "Finding"], [list(i) for i in X.INCONSISTENCIES], "Table 8 - Data-sheet inconsistencies.",
    [1.0, 3.6, 11.6])
p("Simulation files: Touchstone/ (component models and simulated results), Scripts/ (Python models, PyAEDT script "
  "with designs FrontEnd_3port and SBand_2port), circuitRF/ (netlist), Extracted_Data/ (parameter tables, results).")

if __name__ == "__main__":
    MR.render_docx(MR.REP / "Internal_ActiveAntenna_RF_Technical_Note.docx")
    MR.render_pdf(MR.REP / "Internal_ActiveAntenna_RF_Technical_Note.pdf")
    print("internal note written")
