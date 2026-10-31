"""Simulation report as DOCX (python-docx) and PDF (reportlab) from one content list.

Inputs: results.json, ../Extracted_Data/*.json, ../Images/*.png, build_extracted tables.
Outputs: ../Report/GNSS_FrontEnd_Simulation_Report.docx and .pdf
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import ds_data as D
import build_extracted as X

ROOT = Path(__file__).resolve().parent.parent
IMG, REP, XD, AP = ROOT / "Images", ROOT / "Report", ROOT / "Extracted_Data", ROOT / "ANSYS_Project"
REP.mkdir(exist_ok=True)
R = json.loads((ROOT / "Scripts" / "results.json").read_text())


def jload(p):
    return json.loads(p.read_text()) if p.exists() else None


HEAVI = jload(XD / "crosscheck_heavi.json")
CRF = jload(XD / "crosscheck_circuitrf.json")
AEDT = jload(XD / "crosscheck_aedt.json")
AEDT_RUN = jload(AP / "aedt_run.json")
TODAY = dt.date.today().isoformat()


def f2(x, n=2):
    return "-" if x is None else (f"{x:.{n}f}" if isinstance(x, (int, float)) else str(x))


# ======================================================================================
# content
# ======================================================================================
C: list[tuple] = []


def h1(t): C.append(("h1", t))
def h2(t): C.append(("h2", t))
def p(t): C.append(("p", t))
def eq(t): C.append(("eq", t))
def bl(items): C.append(("bullets", items))
def img(name, cap, width=16.0): C.append(("img", IMG / name, cap, width))
def tab(head, rows, cap, widths=None): C.append(("table", head, rows, cap, widths))
def pb(): C.append(("pagebreak",))


S = {r["band"]: r for r in R["summary"]}
st = R["stability"]
b_l1 = R["budgets"]["L1 C/A (1575.42 MHz, 2.046 MHz)"]
b_l5 = R["budgets"]["L5 (1176.45 MHz, 20.46 MHz)"]
b_l2 = R["budgets"]["L2C (1227.60 MHz, 2.046 MHz)"]
intf = R["interferers"]


def it(name, br):
    return next(x for x in intf if x["interferer"] == name and x["branch"] == br)


dme, iri = it("DME/TACAN (aviation)", "L2/L5"), it("Iridium", "L1")

h1("1  Executive summary")
p("This report models a dual-branch GNSS active-antenna front end built only from the eight documents supplied "
  "(Qorvo TQP3M9037, Taoglas HC125A and DXP.02.A, Qualcomm RF360 B7504 and B8889, the RF360 GNSS SAW product brief, "
  "the RF360 automotive SAW selection table and RF360 application note #18). The topology was confirmed by the user: "
  "two patch feeds per band are combined in an HC125A hybrid, followed by LNA - SAW - LNA - SAW, and the two bands "
  "are combined in the DXP.02.A SAW diplexer onto one RF output. All four LNAs run at +5 V / 70 mA.")
tab(["Band", "f (MHz)", "Gain (dB)", "Ripple (dB)", "NF (dB)", "In VSWR", "Out VSWR", "GD (ns)", "GD ripple (ns)"],
    [[r["band"], f2(r["f_mhz"], 2), f2(r["gain_db"]), f2(r["gain_ripple_db"]), f2(r["nf_db"]), f2(r["vswr_in"]),
      f2(r["vswr_out"]), f2(r["gd_ns"], 1), f2(r["gd_ripple_ns"], 1)] for r in R["summary"]],
    "Table 1 - Simulated system performance at the band centres (virtual RHCP input to RF output, 50 ohm, 25 C). "
    "Ripple and group-delay ripple over the signal bandwidth. Group delay is an estimate (min-phase SAW models).")
p("Key findings:")
bl([
    f"Noise figure {S['L1/E1/B1C']['nf_db']:.2f} dB at L1 and {S['L5/E5a/B2a']['nf_db']:.2f} dB at L5, set almost "
    f"entirely by the hybrid loss ({-b_l1[0]['gain_db']:.2f} / {-b_l5[0]['gain_db']:.2f} dB) plus LNA 1. The second LNA, "
    "both SAWs and the 3.1-3.6 dB diplexer loss add < 0.02 dB.",
    f"Gain {S['L1/E1/B1C']['gain_db']:.1f} dB (L1) and {S['L5/E5a/B2a']['gain_db']:.1f} dB (L5) - higher than most "
    "GNSS receivers want (typ. 15-30 dB at the receiver input after the cable). See recommendations.",
    f"All blocks and both branches are unconditionally stable: LNA K >= {st['lna_table_k_min']:.3f}, "
    f"mu >= {st['lna_table_mu_min']:.3f} over 0.05-5 GHz; branch mu >= {min(st['branch_l1_mu_min'], st['branch_l2_mu_min']):.3f}.",
    f"Input match at the RHCP port is only VSWR {S['L1/E1/B1C']['vswr_in']:.2f} at L1 and "
    f"{S['E5b/B2b']['vswr_in']:.2f} at E5b: the LNA S11 (-10 dB) reflects through the hybrid back to the antenna.",
    "GLONASS G2 (1246-1256 MHz) is not usable: the B8889 pass-band ends at ~1245 MHz "
    f"(gain ripple {S['G2']['gain_ripple_db']:.1f} dB across G2).",
    f"Interference: an aviation DME/TACAN pulse of -30 dBm at 1150 MHz is attenuated only ~4 dB by each B8889 and "
    f"reaches {dme['lna2_out']:+.1f} dBm at LNA 2 output - above the B8889 input rating (+5 dBm) and only "
    f"{dme['lna2_backoff_db']:.1f} dB below LNA 2 P1dB; Iridium (1621 MHz, -20 dBm) reaches {iri['lna2_out']:+.1f} dBm "
    "in the L1 branch. There is no filter in front of LNA 1, so cellular uplinks at -10 dBm leave only ~7-10 dB "
    "back-off at LNA 1.",
    "Three independent circuit solvers agree: scikit-rf (reference), heavi and circuitRF differ by < 0.01 dB in "
    "band. " + ("ANSYS AEDT Circuit result: see section 10." if AEDT else "The ANSYS AEDT run is described in section 10."),
])
p("Data quality: only the LNA S-parameters and noise parameters, the HC125A typical table and the datasheet spec "
  "tables are measured/extracted values. The SAW and diplexer Touchstone files are ESTIMATES built from digitized "
  "curves with a minimum-phase reconstruction; they reproduce every datasheet insertion-loss and attenuation table "
  "entry (section 11) but are not measured data. Replace them with vendor .s2p/.s3p files when available.")

pb()
h1("2  System architecture and connection diagram")
img("connection_diagram.png", "Figure 1 - Connection diagram (user-confirmed topology).")
p("Signal path per branch: two orthogonal patch feeds -> HC125A 3 dB quadrature hybrid (pins 3/4 in, pin 1 out, "
  "pin 2 terminated in 50 ohm) -> TQP3M9037 LNA 1 -> SAW -> TQP3M9037 LNA 2 -> SAW -> DXP.02.A port (L1: pin 7, "
  "L2/L5: pin 5). The DXP.02.A is used in reverse as a combiner (reciprocal SAW device) and drives the common RF "
  "output (pin 2).")
tab(["Ref", "Part", "Manufacturer", "Function", "Qty", "Data used"],
    [["U1-U4", "TQP3M9037", "Qorvo", "LNA 0.7-6 GHz, NF 0.4 dB, 20 dB", "4", "S-param + noise tables (5 V)"],
     ["HY1, HY2", "HC125A", "Taoglas", "3 dB 90 deg hybrid 1150-1630 MHz", "2", "Typical table p.6"],
     ["F1, F2", "B7504 (B39162B7504L210)", "Qualcomm RF360", "SAW L1/B1/G1 1559-1606 MHz", "2", "Spec table + digitized plots"],
     ["F3, F4", "B8889 (B39122B8889P810)", "Qualcomm RF360", "SAW L5/E5/B2/L2 1166-1229 MHz (+2x6.8 nH)", "2", "Spec table + digitized plots"],
     ["DX1", "DXP.02.A", "Taoglas", "SAW diplexer L1 / L2+L5", "1", "Spec table + digitized plots"],
     ["-", "SAW product brief, SDST, AN #18", "Qualcomm RF360", "Alternatives / matching method", "-", "Reference only"]],
    "Table 2 - Component summary.", [1.6, 3.4, 2.4, 4.6, 0.9, 3.6])

h1("3  Extracted datasheet parameters")
p("All extracted numbers are in Scripts/ds_data.py (single source) and exported to Extracted_Data/ as "
  f"{len(X.TABLES)} CSV tables plus Extracted_Parameters.xlsx (one sheet per table, with an INDEX sheet naming source page "
  "and kind: TABLE = typed from a datasheet table, DIGITIZED = read off a plot, [ASSUMED] = estimate).")
tab(["Parameter", "Value", "Source"],
    [["TQP3M9037 gain / NF / OP1dB / OIP3 @1.95 GHz, 5 V", "20.0 dB / 0.40 dB / +20 dBm / +35 dBm", "Qorvo p.2"],
     ["TQP3M9037 IDD / VDD range / abs. max RF in", "70 mA / 3.0-5.25 V / +22 dBm", "Qorvo p.2"],
     ["TQP3M9037 eval @1.7 GHz (5 V)", "21.4 dB, NF 0.36 dB, OP1dB 20.7, OIP3 34.9 dBm", "Qorvo p.6"],
     ["TQP3M9037 noise parameters", "1.5-2.7 GHz: NFmin 0.29-0.51 dB, |Gopt| 0.02-0.16, Rn 0.04-0.08 ohm", "Qorvo p.3"],
     ["HC125A IL / isolation / VSWR / balance", "<= 0.3 dB / >= 22 dB / 1.2 / +/-0.35 dB, 90 deg", "Taoglas p.5"],
     ["HC125A typical @1582 MHz", "C -3.25, T -3.27 dB, iso 28.6 dB, phase 92.97 deg", "Taoglas p.6"],
     ["B7504 IL typ/max", "1.1/2.0 (B1), 0.9/1.4 (L1), 1.2/2.0 (G1) dB", "RF360 p.7"],
     ["B7504 min attenuation", "45-60 dB cellular, 35-42 dB at 4.4-5.85 GHz", "RF360 p.7"],
     ["B7504 max input power", "+23 dBm @915 (GSM 1:8), +15 dBm CW @1463/1710 MHz", "RF360 p.8"],
     ["B8889 IL typ/max", "0.9/1.5 (L5), 1.0/1.3 (B2b), 1.4/2.6 (L2) dB", "RF360 p.7"],
     ["B8889 matching / max input", "6.8 nH shunt both ports / +5 dBm CW in-band", "RF360 p.6, p.8"],
     ["DXP.02.A IL", "3.8 typ / 4.6 max (L1), 4.2 / 5.2 (L2/L5) dB", "Taoglas p.4"],
     ["DXP.02.A isolation / input power", ">= 22 dB (typ 31-35) / 10 dBm", "Taoglas p.4"]],
    "Table 3 - Main extracted parameters (full tables in Extracted_Data/).", [5.6, 7.2, 2.6])

h1("4  Design assumptions")
p("Every value not printed in a datasheet. The same list is in Extracted_Data/assumptions_log.md and in the XLSX.")
tab(["ID", "Item", "Assumption", "Basis / how to close"], [list(a) for a in X.ASSUMPTIONS],
    "Table 4 - Assumptions log.", [1.0, 2.6, 8.6, 4.0])

pb()
h1("5  Models and equations")
h2("5.1  Component models")
bl(["TQP3M9037: datasheet S-parameter table (0.05-5 GHz, device leads) -> TQP3M9037_5V.s2p with the measured noise block; "
    "the circuit adds the eval-board bias network (Figure 3).",
    "HC125A: 4-port from the typical table (magnitudes, coupled-through phase difference) -> HC125A.s4p.",
    "B7504 / B8889: |S21| digitized from Fig. 4 and anchored to the attenuation table, |S11|/|S22| from VSWR Fig. 5/6, "
    "phase by minimum-phase reconstruction -> B7504.s2p, B8889_matched.s2p (the B8889 file includes the 6.8 nH inductors).",
    "DXP.02.A: 3-port from the digitized p.6-8 curves (eval matching included) -> DXP02A.s3p.",
    "Patch antenna: ideal dual-feed RHCP source -> PatchCP_ideal_RHCP_feed.s4p (placeholder for the real patch).",
    "Equivalent circuits: LNA stage = series C(ESL, ESR) - 2-port table - shunt [L(Q) || Cpar] + bypass C(ESL) - series C; "
    "SAW static model = capacitive (DC block function, AN #18 Fig. 9)."])
h2("5.2  Equations")
eq("VSWR = (1 + |G|) / (1 - |G|),   RL = -20 log10|G|,   |G| = (VSWR - 1)/(VSWR + 1)")
eq("Min-phase: ln H(w) = ln|H(w)| + j arg H(w),  arg H = -Hilbert{ln|H|} (real-cepstrum folding)")
eq("SAW reflection phase: arg S11 = arg S22 = arg S21 + 90 deg  (S11 S21* + S21 S22* = 0, lossless symmetric 2-port)")
eq("Transducer gain G_T = |S21|^2 (50 ohm source and load);  group delay tau = -d(arg S21)/d(omega)")
eq("RHCP excitation of the hybrid: a3 = 1/sqrt2,  a4 = -j/sqrt2  ->  b1 = (S13 - j S14)/sqrt2")
eq("Rollett K = (1 - |S11|^2 - |S22|^2 + |D|^2) / (2|S12 S21|),  D = S11 S22 - S12 S21")
eq("Edwards-Sinsky mu = (1 - |S11|^2) / (|S22 - D S11*| + |S12 S21|)  (mu > 1: unconditionally stable)")
eq("Passive noise (Twiss): C_Y = 2kT0 Re{Y};  C_A = T C_Y T^H,  T = [[0, B], [1, D]]")
eq("Active noise: C_A = 2kT0 [[Rn, (Fmin-1)/2 - Rn Yopt*], [(Fmin-1)/2 - Rn Yopt, Rn |Yopt|^2]]")
eq("Cascade: C_A = C_A1 + A1 C_A2 A1^H;   F = 1 + z^H C_A z / (2kT0 Re Zs),  z = [1, Zs*]^T")
eq("Friis: F = F1 + (F2 - 1)/G1 + ...;  1/IIP3 = sum (G_before,i / IIP3_i)  (linear units)")
eq("Noise floor N = kT0 B F G = -174 dBm/Hz + 10 log10 B + NF + G;  output noise of both branches adds in the DXP: "
   "F_L1,sys = (F1 G1 + F2 G2)/G1")

pb()
h1("6  Schematics")
img("schematic_system.png", "Figure 2 - Top-level schematic, design FrontEnd_3port (as built by Scripts/aedt_circuit.py).", 17)
img("schematic_lna_stage.png", "Figure 3 - LNA stage with bias network (one of four).", 15)
img("schematic_matching_networks.png", "Figure 4 - Datasheet matching networks contained in the SAW and diplexer models.", 15)

pb()
h1("7  S-parameter results")
img("sparams_L1.png", "Figure 5 - L1 branch S11 / S21 / S12 / S22 (shaded: B1I, L1/E1, G1).")
img("sparams_L2.png", "Figure 6 - L2/L5 branch S11 / S21 / S12 / S22 (shaded: L5/E5a, E5b, L2).")
img("gain_inband.png", "Figure 7 - In-band gain of both branches.")
img("gain_wideband.png", "Figure 8 - Wide-band transfer 0.6-2.2 GHz.")
img("vswr.png", "Figure 9 - VSWR at the RHCP inputs and the RF output.")
img("noise_figure.png", "Figure 10 - System noise figure (both branches' output noise included) and LNA NFmin.")
img("stability.png", f"Figure 11 - Stability: K and mu. LNA alone: K_min = {st['lna_table_k_min']:.3f} at "
    f"{st['lna_table_k_min_f_ghz']:.2f} GHz, mu_min = {st['lna_table_mu_min']:.3f}, |D|max = {st['lna_table_delta_max']:.2f}; "
    f"LNA stage with bias: K_min = {st['stage_k_min']:.2f}, mu_min = {st['stage_mu_min']:.2f}.")
img("group_delay.png", "Figure 12 - Group delay (estimated: SAW/DXP phase is minimum-phase).")
img("phase.png", "Figure 13 - Transmission phase.")
img("lna_sparams.png", "Figure 14 - TQP3M9037 datasheet S-parameters (5 V, 70 mA).")
img("component_models.png", "Figure 15 - Component models against the datasheet data.")

EX = R.get("extras")
if EX:
    pb()
    h1("7A  Rejection, insertion loss and other RF parameters")
    p("Rejection is quoted in dBc: how far below the band-centre gain a frequency is passed (rejection = G(fc) - G(f)). "
      "Filter rejection is shown per component against the datasheet minimum-attenuation table, and for the complete "
      "chain. Model rejection beyond ~60-80 dBc is not achievable on a real board: radiation and ground currents leak "
      "around the filters, so treat deeper values as 'limited by layout'.")
    if EX.get("filter_files"):
        img("filter_touchstone_files.png", "Figure 15-0 - The filter Touchstone files (pass-band view).")
        tab(["File", "Points", "Range (MHz)", "Passive", "Use"],
            [[r["file"], str(r["points"]), f"{r['f_min_mhz']:.0f}-{r['f_max_mhz']:.0f}", "yes" if r["passive"] else "NO",
              {"B7504.s2p": "L1 SAW, no matching needed (50 ohm)",
               "B8889_matched.s2p": "L2/L5 SAW with its 2 x 6.8 nH (use as one block)",
               "B8889_bare_deembedded.s2p": "L2/L5 SAW chip only - add your own matching",
               "DXP02A_common_to_L1.s2p": "diplexer L1 path, L2/L5 port in 50 ohm",
               "DXP02A_common_to_L2L5.s2p": "diplexer L2/L5 path, L1 port in 50 ohm"}[r["file"]]]
             for r in EX["filter_files"]] + [["DXP02A.s3p", "3201", "600-2200", "yes", "full 3-port diplexer"]],
            "Table 7A-0 - Filter S-parameter files (all ESTIMATED from datasheet curves).", [4.6, 1.2, 2.0, 1.2, 7.2])
    img("filter_rejection.png", "Figure 15A - Rejection of each filter (one device) against the datasheet limits: "
        "B7504, B8889 (with its 6.8 nH matching), DXP.02.A common-L1 and common-L2/L5 paths.")
    tab(["Filter", "Band (MHz)", "Spec min att. (dB)", "Spec typ (dB)", "Model min att. (dB)", "Margin to spec (dB)"],
        [[r["filter"], f"{r['f_lo_mhz']:g}-{r['f_hi_mhz']:g}", f2(r["spec_min_att_db"], 0), f2(r["spec_typ_att_db"], 0),
          f2(r["model_min_att_db"], 1), f2(r["margin_to_spec_db"], 1)] for r in EX["filter_rejection"]],
        "Table 7A-1 - Filter rejection vs the datasheet attenuation specification (worst point in each band). "
        "All bands pass; smallest margins ~3 dB (B8889 cellular bands, DXP).", [2.4, 2.6, 2.4, 2.0, 2.6, 2.6])
    img("filter_rejection_skirts.png", "Figure 15B - Skirt rejection next to the GNSS bands, one filter and the two "
        "filters in series as used in each branch. The weak points are the B8889 lower skirt (DME, < 4 dB at 1150 MHz "
        "per filter) and the B7504 upper skirt (Iridium, ~5-11 dB per filter).")
    img("rejection_per_stage.png", "Figure 15C - Cumulative filter rejection: after SAW 1, after SAW 2, after SAW 2 + DXP.")
    img("rejection_system.png", "Figure 15D - Rejection of the complete system (LNAs included) with the interferer bands.")
    tab(["Interferer band", "MHz", "L1 branch min (dBc)", "L1 mean (dBc)", "L2/L5 branch min (dBc)", "L2/L5 mean (dBc)"],
        [[r["band"], f"{r['f_lo_mhz']:g}-{r['f_hi_mhz']:g}", f2(r["rej_min_L1_dBc"], 1), f2(r["rej_mean_L1_dBc"], 1),
          f2(r["rej_min_L2/L5_dBc"], 1), f2(r["rej_mean_L2/L5_dBc"], 1)] for r in EX["rejection"]],
        "Table 7A-2 - System rejection in the interferer bands (min = worst point in the band). Values above ~80 dBc "
        "are model values; expect layout-limited results in practice. Inmarsat DL (1525-1559 MHz) touches the L1 "
        "pass-band edge, hence the low minimum.", [4.2, 2.2, 2.2, 2.2, 2.4, 2.4])
    img("insertion_loss.png", "Figure 15E - Insertion loss of each passive part and of the passive chain per branch.")
    tab(["Band", "f (MHz)", "Hybrid (dB)", "SAW, one (dB)", "SAW max in BW (dB)", "DXP (dB)", "Total passive (dB)",
         "Total max in BW (dB)"],
        [[r["band"], f2(r["f_mhz"], 2), f2(r["hybrid_db"]), f2(r["saw_db"]), f2(r["saw_max_in_bw_db"]), f2(r["dxp_db"]),
          f2(r["total_passive_db"]), f2(r["total_passive_max_in_bw_db"])] for r in EX["insertion_loss"]],
        "Table 7A-3 - Insertion loss (total passive = hybrid + 2 SAW + DXP; the LNAs make up for it).",
        [2.4, 1.6, 1.6, 1.8, 2.0, 1.6, 2.0, 2.0])
    img("return_loss_isolation.png", "Figure 15F - Return loss at all ports (10 dB line) and isolation: between the "
        "two antenna inputs, reverse isolation output-to-input, and the DXP port-to-port isolation.")
    img("output_noise_psd.png", f"Figure 15G - Output noise density delivered to the receiver. Total noise power "
        f"0.6-2.2 GHz = {EX['output_noise_total_dbm']:.1f} dBm (the receiver front end must handle it without compressing).")
    img("polarisation.png", "Figure 15H - Cross-polar (LHCP) rejection and axial-ratio contribution caused by the "
        "HC125A amplitude/phase imbalance (ideal patch assumed; the real antenna axial ratio adds to this).")
    tab(["Band", "Gain", "NF", "Te (K)", "RL in", "RL out", "Mismatch loss in", "Rev. iso", "XPD", "AR (dB)", "GD (ns)",
         "IIP3 / OIP3 (dBm)", "IP1dB in / OP1dB out (dBm)", "SFDR (dB)", "C/N0 (dB-Hz)"],
        [[r["band"], f2(r["gain_db"], 1), f2(r["nf_db"]), f2(r["te_k"], 0), f2(r["rl_in_db"], 1), f2(r["rl_out_db"], 1),
          f2(r["mismatch_loss_in_db"]), f2(r["reverse_iso_db"], 0), f2(r["xpd_db"], 1), f2(r["ar_db"]), f2(r["gd_ns"], 1),
          (f"{r['iip3_dbm']:.1f} / {r['oip3_dbm']:.1f}" if "iip3_dbm" in r else "-"),
          (f"{r['ip1db_in_dbm']:.1f} / {r['op1db_out_dbm']:.1f}" if "ip1db_in_dbm" in r else "-"),
          (f2(r["sfdr_db"], 1) if "sfdr_db" in r else "-"), (f2(r["cn0_dbhz"], 1) if "cn0_dbhz" in r else "-")]
         for r in EX["rf_parameters"]],
        "Table 7A-4 - RF parameter summary per GNSS band (dB unless stated). SFDR in the signal bandwidth (2.046 MHz "
        "L1/L2, 20.46 MHz L5); C/N0 for the minimum signal with the antenna at 290 K.",
        [1.8, 1.0, 0.9, 0.9, 0.9, 0.9, 1.1, 0.9, 0.9, 0.8, 0.9, 1.6, 1.8, 1.0, 1.1])
    p(f"Inter-frequency group delay: L1 - L5 = {EX['gd_l1_minus_l5_ns']:.1f} ns through the front end (estimated, "
      "min-phase SAW models). Dual-frequency receivers calibrate this as an inter-frequency bias; it must be stable "
      "over temperature, which SAW filters are not perfectly (not modelled).")
    tab(["Band", "Gain typ (dB)", "Gain min (dB)", "Gain max (dB)", "NF typ (dB)", "NF max (dB)"],
        [[r["band"], f2(r["gain_typ_db"], 1), f2(r["gain_min_db"], 1), f2(r["gain_max_db"], 1), f2(r["nf_typ_db"]),
          f2(r["nf_max_db"])] for r in EX["worst_case"]],
        "Table 7A-5 - Worst case from the datasheet limits (Friis, 50 ohm): LNA gain typ +/-1.5 dB and NF max 0.65 dB, "
        "SAW and DXP IL max, hybrid IL max 0.3 dB. The receiver must accept the full gain range.", [2.0, 2.4, 2.4, 2.4, 2.4, 2.4])

pb()
h1("8  Cascade analysis and power budget")
p("Stage values at band centre in 50 ohm (passives: NF = loss at T0). Signal = minimum received power for a 0 dBic "
  "antenna. Noise = kT0 B F G in the signal bandwidth; 'C/N' is the ratio in that bandwidth (negative for GNSS - the "
  "signal is recovered by despreading; C/N0 = C/N + 10 log10 B).")
for case, rows in R["budgets"].items():
    tab(["Stage", "G (dB)", "NF (dB)", "Cum G", "Cum NF", "Cum IIP3 (dBm)", "Cum IP1dB (dBm)", "Signal (dBm)",
         "Noise (dBm)", "C/N (dB)"],
        [[r["stage"], f2(r["gain_db"]), f2(r["nf_db"]), f2(r["cum_gain_db"]), f2(r["cum_nf_db"]),
          f2(r["cum_iip3_dbm"], 1), f2(r["cum_iip1db_dbm"], 1), f2(r["signal_dbm"], 1), f2(r["noise_dbm"], 1),
          f2(r["snr_db"], 1)] for r in rows],
        f"Cascade - {case}.", [3.6, 1.1, 1.1, 1.1, 1.1, 1.5, 1.5, 1.5, 1.5, 1.1])
c_n0 = b_l1[-1]["snr_db"] + 10 * __import__("math").log10(2.046e6)
p(f"L1 C/A: C/N0 at the RF output = {c_n0:.1f} dB-Hz for the minimum signal (sky noise at 290 K assumed; with a "
  "real sky temperature of ~100 K the front-end NF matters more and C/N0 rises by ~2-3 dB). The Friis cascade "
  "(50 ohm stages) and the full noise-correlation simulation agree within 0.02 dB.")
img("level_diagram.png", "Figure 16 - Level diagram: minimum signal and thermal noise through the chain.")
p("Power consumption: 4 x 70 mA x 5 V = 1.40 W (VDD 4.2 V typ allowed: 4 x ~60 mA). DC is fed through the 18 nH "
  "chokes; if the antenna is powered over the coax, add a bias tee at the RF output (the DXP and SAWs block DC; "
  "the SAWs are rated 5 V DC max).")

h1("9  Interference and linearity")
p("Out-of-band signals at the antenna feed (levels assumed for a co-located terminal, A18) propagated through "
  "each branch with the small-signal gains. 'Back-off' = LNA OP1dB minus the interferer level at that LNA output.")
tab(["Interferer", "f (MHz)", "P ant (dBm)", "Branch", "LNA1 out", "SAW1 out", "LNA2 out", "RF out", "Back-off LNA1", "Back-off LNA2"],
    [[x["interferer"], f2(x["f_mhz"], 1), f2(x["p_ant_dbm"], 0), x["branch"], f2(x["lna1_out"], 1), f2(x["saw1_out"], 1),
      f2(x["lna2_out"], 1), f2(x["rf_out"], 1), f2(x["lna1_backoff_db"], 1), f2(x["lna2_backoff_db"], 1)] for x in intf],
    "Table - Interferer levels in dBm at each node.", [3.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.4, 1.4])
bl([f"DME/TACAN 960-1215 MHz (pulsed, aviation): the B8889 lower skirt gives only ~4 dB at 1150 MHz, so LNA 2 "
    f"output reaches {dme['lna2_out']:+.1f} dBm and the RF output {dme['rf_out']:+.1f} dBm for -30 dBm at the antenna. "
    "This exceeds the B8889 +5 dBm input rating at SAW 2 and can block the receiver. Critical for aviation/automotive near airports.",
    f"Iridium 1616-1626.5 MHz: B7504 attenuation at 1621 MHz ~11 dB per filter; LNA 2 output {iri['lna2_out']:+.1f} dBm "
    "for -20 dBm at the antenna.",
    "Cellular uplinks (-10 dBm): LNA 1 sees the full level (no pre-filter); back-off 7-10 dB from OP1dB, ~13 dB below "
    "the +22 dBm absolute-maximum input. After SAW 1 the levels drop by 40-60 dB.",
    "In-band: cascaded input P1dB -21 to -24 dBm and IIP3 -8 to -12 dBm, limited by LNA 2 (the GNSS signal itself is "
    "~100 dB below this)."])

h1("10  Simulation tool cross-checks")
rows = [["scikit-rf 1.x (reference)", "Network cascade + Circuit, noise-correlation matrices", "-", "Scripts/simulate.py"]]
if HEAVI:
    rows.append(["heavi 0.7.9 (nodal Y solver)", "Same circuit from the Touchstone files, own R/L/C",
                 f"{max(v['max_abs_diff_db_inband'] for k, v in HEAVI.items() if k.startswith('S')):.4f} dB",
                 "Scripts/crosscheck_heavi.py"])
if CRF:
    rows.append(["circuitRF 1.6.1 (CLI sparam)", "Netlist circuitRF/gnss_frontend.cnl, SnP blocks",
                 f"{max(v['max_abs_diff_db_inband'] for v in CRF.values()):.4f} dB", "Scripts/build_circuitrf.py"])
if AEDT:
    rows.append(["ANSYS AEDT 2026 R1 Circuit (Nexxim LNA)", "PyAEDT-built schematic, Touchstone components",
                 f"{max(v['max_abs_diff_db_inband'] for v in AEDT.values()):.4f} dB", "Scripts/aedt_circuit.py"])
tab(["Solver", "How", "Max |dS| in band vs reference", "Script"], rows,
    "Table - Solver agreement on S31, S32, S11, S22, S33 inside 1164-1230 and 1559-1606 MHz.", [4.2, 6.0, 2.8, 3.6])
if not AEDT:
    p("ANSYS AEDT: the PyAEDT script builds, solves and saves the project. In this session AEDT 2026 R1 is installed "
      "but the headless gRPC session could not be started from the automation shell (see the error log, appendix A); "
      "run 'python Scripts/aedt_circuit.py' on the workstation (add --gui to watch it). The script exports "
      "ANSYS_Project/AEDT_System_3port.s3p, which Scripts/build_all.py then compares with the reference.")
p("Sensitivity found during the cross-check: interpolating the 200 MHz-step LNA table linearly instead of with a "
  "cubic spline changes in-band gain by up to 1.4 dB. The LNA table resolution is therefore a model uncertainty "
  "of the order of +/-0.7 dB in gain (assumption A6).")

h1("11  Model validation against the datasheets")
tab(["Item", "Datasheet typ", "Datasheet max", "Model"],
    [[v["item"], f2(v["ds_typ"]), f2(v["ds_max"]), f2(v["model"])] for v in R["validation"]],
    "Table - Model vs datasheet (insertion loss: mean over the band; attenuation: worst case in the band).",
    [8.0, 2.4, 2.4, 2.4])
p("Every B7504/B8889 attenuation value meets the datasheet minimum and is within ~4 dB of the typical value. "
  "The DXP model gives 3.3 dB at the band centres (the measured plots) against 3.8/4.2 dB typical in the table - the "
  "table values appear to be band-edge figures (inconsistency I17).")

h1("12  Bill of materials")
tab(["Qty", "Ref", "Part / value", "Package", "Manufacturer / note"],
    [["2", "ANT1, ANT2", "Dual-feed patch, L1 and L2/L5 (or stacked patch)", "-", "Not supplied - e.g. Taoglas GPDF series"],
     ["2", "HY1, HY2", "HC125A 3 dB hybrid", "6.35 x 5.08 x 1.5 mm", "Taoglas"],
     ["2", "R1, R2", "50 ohm (49.9 ohm 1 %) hybrid isolated-port load", "0402", "thin film, RF rated"],
     ["4", "U1-U4", "TQP3M9037", "DFN 2 x 2 mm, 8 pin", "Qorvo"],
     ["8", "C1/C2 per LNA", "100 pF NPO/C0G 50 V (DC block)", "0402", "Murata GJM/GRM series"],
     ["4", "C3", "100 pF NPO (VDD bypass)", "0402", "-"],
     ["4", "C4", "1.0 uF X5R 10 V (VDD bypass)", "0402", "-"],
     ["4", "L1", "18 nH ceramic, 5 % (RF choke)", "0603", "e.g. Coilcraft 0603CS / Murata LQW18"],
     ["8 (opt.)", "R1/R2 per LNA", "10 k / 33 k shutdown divider", "0402", "only if PD control is used"],
     ["2", "F1, F2", "B7504 SAW (B39162B7504L210)", "0.9 x 0.7 mm", "Qualcomm RF360"],
     ["2", "F3, F4", "B8889 SAW (B39122B8889P810)", "1.1 x 0.9 mm", "Qualcomm RF360"],
     ["4", "Lp1/Lp4", "6.8 nH wire-wound, high Q (B8889 matching)", "0402", "e.g. Murata LQW15AN6N8"],
     ["1", "DX1", "DXP.02.A SAW diplexer", "5 x 5 x 1.7 mm", "Taoglas"],
     ["1", "L2", "4.3 nH (DXP common)", "0402", "TDK (eval board)"],
     ["1", "C1", "1.5 pF (DXP common)", "0402", "Murata (eval board)"],
     ["1", "L1", "4.7 nH (DXP L1 port)", "0402", "TDK (eval board)"],
     ["1", "L3", "3.3 nH (DXP L2/L5 port)", "0402", "TDK (eval board)"],
     ["1", "C2", "1 pF (DXP L2/L5 port)", "0402", "Murata (eval board)"],
     ["1", "J1", "RF output connector (SMA/U.FL/MMCX)", "-", "per enclosure"]],
    "Table - Bill of materials (eval-board reference values).", [1.4, 2.6, 6.2, 2.6, 4.0])

h1("13  Datasheet inconsistencies and missing parameters")
tab(["ID", "Where", "Finding"], [list(i) for i in X.INCONSISTENCIES], "Table - Inconsistencies.", [1.0, 3.6, 11.6])
tab(["Part", "Missing parameter", "Treatment"], [list(m) for m in X.MISSING], "Table - Missing parameters.", [2.4, 8.6, 5.2])

h1("14  Limitations")
bl(["SAW and diplexer Touchstone files are estimates from digitized plots: magnitude accuracy +/-0.3 dB in band and "
    "+/-2 dB in the stop band; phase and group delay are minimum-phase estimates (real SAW delay can be larger).",
    "HC125A phase is assumed; only magnitudes and the coupled/through phase difference are datasheet values. The "
    "HC125A is held flat outside 1150-1630 MHz.",
    "The antenna is an ideal RHCP source; patch impedance, feed coupling, axial ratio and pattern are not modelled.",
    "LNA data are 25 C typical at 5 V with 200 MHz steps; no temperature, supply, part-to-part or aging spread.",
    "No PCB interconnect, via, ground or coupling effects; no layout-induced feedback around the 40 dB of gain.",
    "Noise below 1.5 GHz and large-signal values at L-band are interpolated/estimated.",
    "Interference analysis is small-signal (no compression, no intermodulation products, no pulsed DME statistics).",
    "AN #18 is an RKE (315/434/868 MHz) application note; its method is used, its component values are not."])

h1("15  Recommendations")
bl(["Add a pre-LNA filter or at least a DME/L-band notch: the L2/L5 branch needs > 30 dB at 960-1150 MHz; e.g. "
    "move one B8889 in front of LNA 1 (costs ~0.9 dB NF) or use a ceramic/cavity L5 pre-filter. For L1, a pre-filter "
    "with steeper upper skirt (Iridium) such as B39162B2611P810 (0.9 dB, pre-LNA) from the SDST.",
    "Reduce gain to what the receiver needs (typ. 25-30 dB at the connector): drop to one LNA per branch, or keep two "
    "and run LNA 2 at 3.3 V (-1.5 dB gain, -4 dBm OP1dB, 44 mA) or add a pad - this also eases the SAW 2 power rating.",
    "Improve the RHCP-port match: use the Qorvo optimized-return-loss input network (3.3 pF series + 3.9 nH shunt, "
    "p.9) or a two-step AN #18 style match; the hybrid then also sees a better load, improving combining/axial ratio.",
    "Choose the second B8889 position or replace B8889 by B2642/B2632 if GLONASS G2 is required (B8889 stops at ~1245 MHz).",
    "Get measured data: RF360 provides measured .s2p for B7504/B8889; Taoglas for HC125A (.s4p) and DXP.02.A (.s3p); "
    "Qorvo for the TQP3M9037 fine-step .s2p and low-band noise parameters. Drop them into Touchstone/ and rerun "
    "Scripts/build_all.py - every result regenerates.",
    "Layout: keep 40 dB of gain stable - separate input and output grounds of each LNA with via fences, keep the SAWs "
    "between the LNAs, follow the Qorvo via pattern (p.15) and HC125A footprint (p.11-13).",
    "Next simulation step: import the real patch S-parameters (HFSS) in place of PatchCP_ideal, and add MSL models for "
    "the interconnects in AEDT Circuit."])

h1("16  Deliverables")
tab(["Folder", "Content"],
    [["Touchstone/", "TQP3M9037_5V.s2p (extracted, with noise), TQP3M9037_stage_5V_with_bias.s2p, HC125A.s4p, B7504.s2p, "
      "B8889_matched.s2p, DXP02A.s3p, PatchCP_ideal_RHCP_feed.s4p (estimated); SIM_*.s2p/.s3p (simulated results)"],
     ["Scripts/", "ds_data.py, models.py, simulate.py, build_extracted.py, make_schematics.py, aedt_circuit.py (PyAEDT), "
      "build_circuitrf.py, crosscheck_heavi.py, make_report.py, build_all.py"],
     ["ANSYS_Project/", "GNSS_L1_L2L5_FrontEnd.aedt (when AEDT runs), AEDT_System_3port.s3p, aedt_run.log"],
     ["circuitRF/", "gnss_frontend.cnl netlist and its circuitRF S-parameter result"],
     ["Report/", "this report (PDF and DOCX), error_log.md"],
     ["Images/", "schematics (PNG + SVG), connection diagram, all result plots"],
     ["Extracted_Data/", "36 CSV tables, Extracted_Parameters.xlsx, assumptions_log.md, results_*.csv, cross-check JSON"]],
    "Table - Deliverables.", [3.0, 13.2])

pb()
h1("Appendix A - Error log")
err = (REP / "error_log.md").read_text(encoding="utf-8").splitlines() if (REP / "error_log.md").exists() else []
for line in err:
    if line.startswith("|") and not line.startswith("|---"):
        pass
rows = [l.strip("|").split("|") for l in err if l.startswith("|") and not l.startswith("|---")]
if rows:
    tab([c.strip() for c in rows[0]], [[c.strip() for c in r] for r in rows[1:]], "Table - Errors met while building "
        "this project and how they were resolved.", [1.0, 3.2, 6.4, 5.6])


# ======================================================================================
# renderers
# ======================================================================================
TITLE = "GNSS L1 + L2/L5 Active Antenna Front End"
SUBLINE = f"RFMW-ANT project 16 &nbsp;|&nbsp; {TODAY} &nbsp;|&nbsp; VDD +5 V &nbsp;|&nbsp; data: 8 supplied datasheets"
MARKING = ""          # classification line printed in the header and footer of every page (empty = none)
FOOTER = "RFMW-ANT project 16"
SUB = "RF circuit models, Touchstone files, ANSYS Circuit automation and simulation report"


def render_docx(path):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    stl = doc.styles["Normal"]
    stl.font.name = "Calibri"
    stl.font.size = Pt(10)
    if MARKING:
        for part in (sec.header, sec.footer):
            hp = part.paragraphs[0]
            hp.text = MARKING
            hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            hp.runs[0].font.size = Pt(8); hp.runs[0].bold = True
            hp.runs[0].font.color.rgb = RGBColor(0xB0, 0x10, 0x1A)
    doc.add_heading(TITLE, 0)
    doc.add_paragraph(SUB)
    doc.add_paragraph(SUBLINE.replace("&nbsp;", " "))
    for blk in C:
        k = blk[0]
        if k == "h1":
            doc.add_heading(blk[1], 1)
        elif k == "h2":
            doc.add_heading(blk[1], 2)
        elif k == "p":
            doc.add_paragraph(blk[1])
        elif k == "eq":
            para = doc.add_paragraph()
            r = para.add_run(blk[1]); r.font.name = "Consolas"; r.font.size = Pt(9)
            para.paragraph_format.left_indent = Cm(0.8)
        elif k == "bullets":
            for b in blk[1]:
                doc.add_paragraph(b, style="List Bullet")
        elif k == "img":
            if blk[1].exists():
                doc.add_picture(str(blk[1]), width=Cm(min(blk[3], 17.0)))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap = doc.add_paragraph(blk[2]); cap.runs[0].font.size = Pt(8.5); cap.runs[0].italic = True
        elif k == "table":
            _, head, rows, cap, widths = blk
            t = doc.add_table(rows=1, cols=len(head))
            t.style = "Light Grid Accent 1"
            for i, h in enumerate(head):
                t.rows[0].cells[i].text = str(h)
            for row in rows:
                cells = t.add_row().cells
                for i, v in enumerate(row):
                    cells[i].text = str(v)
            for r_ in t.rows:
                for i, c in enumerate(r_.cells):
                    for pp in c.paragraphs:
                        for rn in pp.runs:
                            rn.font.size = Pt(7.5)
                    if widths:
                        c.width = Cm(widths[i] * 17.0 / sum(widths))
            cp = doc.add_paragraph(cap); cp.runs[0].font.size = Pt(8.5); cp.runs[0].italic = True
        elif k == "pagebreak":
            doc.add_page_break()
    doc.save(path)


def render_pdf(path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
                                    ListFlowable, ListItem, KeepTogether)
    from xml.sax.saxutils import escape
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12.2)
    cell = ParagraphStyle("c", parent=body, fontSize=7, leading=8.4)
    cellh = ParagraphStyle("ch", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
    capst = ParagraphStyle("cap", parent=body, fontSize=8, leading=10, textColor=colors.HexColor("#52514e"),
                           fontName="Helvetica-Oblique", spaceAfter=8)
    eqst = ParagraphStyle("eq", parent=body, fontName="Courier", fontSize=8, leading=10.5, leftIndent=12)
    h1s = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=14, textColor=colors.HexColor("#1b2f8f"), spaceBefore=8)
    h2s = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.5, textColor=colors.HexColor("#1b2f8f"))
    W = A4[0] - 3.6 * cm
    story = [Paragraph(TITLE, ParagraphStyle("t", parent=ss["Title"], fontSize=20, textColor=colors.HexColor("#1b2f8f"))),
             Paragraph(SUB, ParagraphStyle("s", parent=body, fontSize=11, alignment=1)),
             Paragraph(SUBLINE,
                       ParagraphStyle("s2", parent=body, alignment=1, textColor=colors.HexColor("#52514e"))),
             Spacer(1, 10)]
    for blk in C:
        k = blk[0]
        if k == "h1":
            story.append(Paragraph(escape(blk[1]), h1s))
        elif k == "h2":
            story.append(Paragraph(escape(blk[1]), h2s))
        elif k == "p":
            story.append(Paragraph(escape(blk[1]), body))
        elif k == "eq":
            story.append(Paragraph(escape(blk[1]), eqst))
        elif k == "bullets":
            story.append(ListFlowable([ListItem(Paragraph(escape(b), body), leftIndent=10) for b in blk[1]],
                                      bulletType="bullet", start="-", leftIndent=10))
        elif k == "img":
            if blk[1].exists():
                from PIL import Image as PI
                w_, h_ = PI.open(blk[1]).size
                wd = min(W, blk[3] * cm)
                story.append(KeepTogether([Image(str(blk[1]), width=wd, height=wd * h_ / w_),
                                           Paragraph(escape(blk[2]), capst)]))
        elif k == "table":
            _, head, rows, cap, widths = blk
            data = [[Paragraph(escape(str(h)), cellh) for h in head]] + \
                   [[Paragraph(escape(str(v)), cell) for v in r] for r in rows]
            cw = [W * x / sum(widths) for x in widths] if widths else None
            t = Table(data, colWidths=cw, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b2f8f")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f1ed")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9c8c2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            story += [t, Paragraph(escape(cap), capst)]
        elif k == "pagebreak":
            story.append(PageBreak())

    def foot(cv, doc_):
        cv.saveState()
        cv.setFont("Helvetica", 7)
        cv.setFillColor(colors.HexColor("#808080"))
        cv.drawString(1.8 * cm, 1.0 * cm, f"{TITLE} - {FOOTER}")
        cv.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"page {doc_.page}")
        if MARKING:
            cv.setFont("Helvetica-Bold", 7.5)
            cv.setFillColor(colors.HexColor("#b0101a"))
            cv.drawCentredString(A4[0] / 2, A4[1] - 0.9 * cm, MARKING)
            cv.drawCentredString(A4[0] / 2, 0.55 * cm, MARKING)
        cv.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm,
                      bottomMargin=1.6 * cm, title=TITLE, author="RFMW-ANT").build(story, onFirstPage=foot, onLaterPages=foot)


if __name__ == "__main__":
    render_docx(REP / "GNSS_FrontEnd_Simulation_Report.docx")
    render_pdf(REP / "GNSS_FrontEnd_Simulation_Report.pdf")
    print("report written")
