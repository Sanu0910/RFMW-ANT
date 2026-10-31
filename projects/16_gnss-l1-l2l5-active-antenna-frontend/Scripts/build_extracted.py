"""Extracted-parameter tables (CSV + one XLSX workbook), assumptions log, inconsistency list and
missing-parameter list, all from ds_data.py. Writes into ../Extracted_Data/.
"""
import csv
from pathlib import Path

import pandas as pd

import ds_data as D

XD = Path(__file__).resolve().parent.parent / "Extracted_Data"
XD.mkdir(exist_ok=True)

TABLES = {}


def add(name, rows, cols, source, kind):
    df = pd.DataFrame(rows, columns=cols)
    df.attrs["source"], df.attrs["kind"] = source, kind
    TABLES[name] = df


# ---------------- TQP3M9037
add("TQP3M9037_Sparams_5V", D.TQP_SPARAMS_5V,
    ["f_GHz", "S11_dB", "S11_deg", "S21_dB", "S21_deg", "S12_dB", "S12_deg", "S22_dB", "S22_deg"],
    D.TQP_SOURCE + " p.3", "TABLE (exact)")
add("TQP3M9037_Noise_5V", D.TQP_NOISE_5V, ["f_GHz", "NFmin_dB", "Gopt_mag", "Gopt_deg", "Rn_ohm"],
    D.TQP_SOURCE + " p.3", "TABLE (exact)")
add("TQP3M9037_Noise_ext_ASSUMED", D.TQP_NOISE_EXT, ["f_GHz", "NFmin_dB", "Gopt_mag", "Gopt_deg", "Rn_ohm"],
    "engineering estimate, see assumptions log A3", "[ASSUMED]")
add("TQP3M9037_Specs", D.TQP_SPECS, ["parameter", "min", "typ", "max", "unit", "condition"],
    D.TQP_SOURCE + " p.2, p.16", "TABLE (exact)")
add("TQP3M9037_Eval_5V", [(f, *v) for f, v in D.TQP_EVAL_5V.items()],
    ["f_MHz", "gain_dB", "IRL_dB", "ORL_dB", "OP1dB_dBm", "OIP3_dBm", "NF_dB"], D.TQP_SOURCE + " p.6", "TABLE (exact)")
add("TQP3M9037_Eval_3V3", [(f, *v) for f, v in D.TQP_EVAL_3V3.items()],
    ["f_MHz", "gain_dB", "IRL_dB", "ORL_dB", "OP1dB_dBm", "OIP3_dBm", "NF_dB"], D.TQP_SOURCE + " p.8", "TABLE (exact)")
add("TQP3M9037_EvalBOM", D.TQP_EVAL_BOM, ["ref", "value", "description"], D.TQP_SOURCE + " p.5", "TABLE (exact)")
# ---------------- HC125A
add("HC125A_Typical_25C", D.HC_TABLE,
    ["f_MHz", "coupling_dB", "transmission_dB", "IL_dB", "isolation_dB", "ampl_balance_dB", "phase_deg",
     "RL_S11_dB", "RL_S22_dB", "RL_S33_dB", "RL_S44_dB"], D.HC_SOURCE + " p.6", "TABLE (exact)")
add("HC125A_Specs", D.HC_SPECS, ["parameter", "min", "typ", "max", "unit"], D.HC_SOURCE + " p.5", "TABLE (exact)")
# ---------------- B7504
add("B7504_IL", D.B7504_IL, ["f_lo_MHz", "f_hi_MHz", "typ_dB", "max_dB"], D.B7504_SOURCE + " p.7", "TABLE (exact)")
add("B7504_VSWR", [(a, b, c, d, e, f) for (a, b, c, d), (_, _, e, f) in zip(D.B7504_VSWR_IN, D.B7504_VSWR_OUT)],
    ["f_lo_MHz", "f_hi_MHz", "in_typ", "in_max", "out_typ", "out_max"], D.B7504_SOURCE + " p.7", "TABLE (exact)")
add("B7504_Attenuation", D.B7504_ATT, ["f_lo_MHz", "f_hi_MHz", "min_dB", "typ_dB"], D.B7504_SOURCE + " p.7", "TABLE (exact)")
add("B7504_Ratings_Misc", D.B7504_MAXRAT + D.B7504_MISC + [("Group delay 1597.5-1605.9 MHz", "typ 4.0 / max 15 ns")],
    ["item", "value"], D.B7504_SOURCE + " p.4-8", "TABLE (exact)")
add("B7504_S21_digitized", D.B7504_ATT_DIG, ["f_MHz", "attenuation_dB"], D.B7504_SOURCE + " Fig. 4", "DIGITIZED")
add("B7504_VSWRin_digitized", D.B7504_VSWR_IN_DIG, ["f_MHz", "VSWR"], D.B7504_SOURCE + " Fig. 5", "DIGITIZED")
add("B7504_VSWRout_digitized", D.B7504_VSWR_OUT_DIG, ["f_MHz", "VSWR"], D.B7504_SOURCE + " Fig. 6", "DIGITIZED")
# ---------------- B8889
add("B8889_IL", D.B8889_IL, ["f_lo_MHz", "f_hi_MHz", "typ_dB", "max_dB"], D.B8889_SOURCE + " p.7", "TABLE (exact)")
add("B8889_VSWR", [(a, b, c, d, e, f) for (a, b, c, d), (_, _, e, f) in zip(D.B8889_VSWR_IN, D.B8889_VSWR_OUT)],
    ["f_lo_MHz", "f_hi_MHz", "in_typ", "in_max", "out_typ", "out_max"], D.B8889_SOURCE + " p.7", "TABLE (exact)")
add("B8889_Attenuation", D.B8889_ATT, ["f_lo_MHz", "f_hi_MHz", "min_dB", "typ_dB"], D.B8889_SOURCE + " p.7", "TABLE (exact)")
add("B8889_Ratings_Misc", D.B8889_MAXRAT + D.B8889_MISC, ["item", "value"], D.B8889_SOURCE + " p.4-8", "TABLE (exact)")
add("B8889_S21_digitized", D.B8889_ATT_DIG, ["f_MHz", "attenuation_dB"], D.B8889_SOURCE + " Fig. 4", "DIGITIZED")
add("B8889_VSWRin_digitized", D.B8889_VSWR_IN_DIG, ["f_MHz", "VSWR"], D.B8889_SOURCE + " Fig. 5", "DIGITIZED")
add("B8889_VSWRout_digitized", D.B8889_VSWR_OUT_DIG, ["f_MHz", "VSWR"], D.B8889_SOURCE + " Fig. 6", "DIGITIZED")
# ---------------- DXP
add("DXP02A_Specs", D.DXP_SPECS, ["parameter", "min", "typ", "max", "unit"], D.DXP_SOURCE + " p.4", "TABLE (exact)")
add("DXP02A_Pins", D.DXP_PINS, ["pin", "function"], D.DXP_SOURCE + " p.11", "TABLE (exact)")
add("DXP02A_EvalMatching", D.DXP_EVAL_MATCH, ["ref", "value", "position"], D.DXP_SOURCE + " p.13", "TABLE (exact)")
for nm, pts, col in (("S21_common_to_L1", D.DXP_S21_DIG, "attenuation_dB"), ("S31_common_to_L2L5", D.DXP_S31_DIG, "attenuation_dB"),
                     ("S23_isolation", D.DXP_S23_DIG, "isolation_dB"), ("RL_common", D.DXP_RL1_DIG, "return_loss_dB"),
                     ("RL_L1port", D.DXP_RL2_DIG, "return_loss_dB"), ("RL_L2L5port", D.DXP_RL3_DIG, "return_loss_dB")):
    add(f"DXP02A_{nm}_digitized", pts, ["f_MHz", col], D.DXP_SOURCE + " p.6-8", "DIGITIZED")
# ---------------- S-band parts
add("TA1442A_Specs", D.TA_SPECS, ["parameter", "min", "typ", "max", "unit"], D.TA_SOURCE + " p.2", "TABLE (exact)")
add("TA1442A_Misc", D.TA_MISC, ["item", "value"], D.TA_SOURCE + " p.2-5", "TABLE (exact)")
add("TA1442A_S21_digitized", D.TA_ATT_DIG, ["f_MHz", "attenuation_dB"], D.TA_SOURCE + " p.3 VNA plots", "DIGITIZED")
add("TA1442A_VSWR_digitized", D.TA_VSWR_DIG, ["f_MHz", "VSWR"], D.TA_SOURCE + " p.4 VNA plots", "DIGITIZED")
add("C2327J5003AHF_Specs", D.XH_SPECS, ["parameter", "min", "typ", "max", "unit"], D.XH_SOURCE + " p.1", "TABLE (exact)")
add("C2327J5003AHF_Pins", D.XH_PINS, ["pin", "function"], D.XH_SOURCE + " p.1", "TABLE (exact)")
add("C2327J5003AHF_digitized", D.XH_DIG, ["f_MHz", "return_loss_dB", "excess_IL_dB", "ampl_balance_dB",
    "phase_balance_deg", "isolation_dB"], D.XH_SOURCE + " p.2-3", "DIGITIZED")
# ---------------- reference docs
add("Brief_GNSS_SAW_range", D.BRIEF_FILTERS,
    ["f_lo_MHz", "fc_MHz", "f_hi_MHz", "BW_MHz", "part", "package_mm", "band", "IL_typ_dB", "IL_max_dB",
     "GDR_typ_ns", "GDR_max_ns", "Top_max_C", "comment"], D.BRIEF_SOURCE, "TABLE (exact)")
add("SDST_GNSS_filters", D.SDST_GNSS,
    ["f_start_MHz", "f_stop_MHz", "fc_MHz", "type", "usable_BW_MHz", "IL_dB", "package_mm", "feature"],
    D.SDST_SOURCE + " p.6-7", "TABLE (exact, GNSS rows only)")
add("AN18_matching_rules", D.AN18_RULES, ["topic", "rule"], D.AN18_SOURCE, "SUMMARY of the app note")
add("AN18_RKE_LNA_impedances", D.AN18_RX_IMPEDANCES, ["IC", "f_MHz", "impedance", "R//C"], D.AN18_SOURCE + " p.13",
    "TABLE (exact)")

# ---------------- assumptions, inconsistencies, missing parameters
ASSUMPTIONS = [
    ("A1", "Topology", "Two branches (patch -> HC125A -> LNA -> SAW -> LNA -> SAW) combined by the DXP.02.A, as confirmed by the user 2026-10-31. Single chain is not possible: B7504 (L1) and B8889 (L2/L5) have disjoint pass-bands.", "User decision"),
    ("A2", "Antenna", "Each patch is an ideal dual-feed RHCP source: lossless 90 deg splitter, 50 ohm feeds (PatchCP_ideal_RHCP_feed.s4p). LHCP port terminated at T0 (290 K) for noise.", "Replace with measured/HFSS patch S-parameters"),
    ("A3", "LNA noise below 1.5 GHz", "Noise table starts at 1.5 GHz. NFmin 0.38-0.40 dB, Gopt = 0.15/14.1 deg, Rn = 0.08 ohm used at 0.6-1.2 GHz (bounded by the 50-ohm eval NF of 0.40 dB at 0.9 GHz and 0.36 dB at 1.7 GHz).", "Ask Qorvo for low-band noise parameters"),
    ("A4", "LNA bias", "VDD = +5 V, 70 mA (user choice); S-parameters at device leads; eval-board bias network (100 pF DC blocks, 18 nH choke, 100 pF + 1 uF bypass).", "Datasheet p.2, p.5"),
    ("A5", "Parasitics", "100 pF 0402: ESL 0.25 nH, ESR 0.15 ohm; 18 nH 0603: Q = 40 at 1.4 GHz, 0.12 pF self-capacitance (SRF ~3.4 GHz); bypass ESL 0.4 nH.", "Replace with vendor S-parameter models of the chosen parts"),
    ("A6", "LNA interpolation", "200 MHz table interpolated with a cubic spline on dB magnitude and unwrapped phase. Linear interpolation changes in-band gain by up to 1.4 dB (heavi test) -> a real model uncertainty.", "Download the Qorvo fine-step .s2p"),
    ("A7", "LNA large-signal", "OIP3/OP1dB at L-band interpolated from eval-board values at 0.9 and 1.7 GHz (34.4-34.9 dBm, 22-20.7 dBm).", "Datasheet p.6"),
    ("A8", "HC125A phase", "Datasheet gives magnitudes and the coupled-vs-through phase difference (91.9-93.0 deg) only. Absolute through phase = -90 deg x f/1390 MHz; reflection and isolation phase offsets chosen to keep the 4-port passive (165 / 270 deg).", "Measured .s4p from Taoglas"),
    ("A9", "HC125A port mapping", "'Transmission' column = pin1->pin4 (direct, angle theta), 'Coupling' column = pin1->pin3 (theta-90), from the pin table p.7. Feeds on pins 3/4, LNA on pin 1, pin 2 terminated in 50 ohm.", "Confirm with Taoglas"),
    ("A10", "HC125A passivity", "The 92 deg phase difference with 0.15-0.29 dB loss is slightly non-passive with arbitrary reflection phases; after the phase choice the matrix is scaled by <= 0.11 dB at the worst frequency.", "-"),
    ("A11", "HC125A out of band", "Values held at the 1150/1630 MHz edge outside 1150-1630 MHz. Out-of-band rejection therefore comes from the SAWs/DXP only (conservative).", "-"),
    ("A12", "SAW phase", "No measured phase in the datasheets. S21 phase = minimum-phase (Hilbert / real-cepstrum) reconstruction of the digitized magnitude; S11/S22 phase = S21 phase + 90 deg (lossless symmetric reciprocal condition). Group delay is therefore an estimate; ripple agrees with the brief (B7504 GD ripple 4 ns typ).", "Use RF360 measured .s2p (available on rffe.qualcomm.com)"),
    ("A13", "SAW reflection out of band", "|S11| = 0.95 sqrt(1-|S21|^2) outside the plotted VSWR range (reflective SAW stop-band), blended over 4 MHz.", "-"),
    ("A14", "B8889 matching", "The B8889 model includes the required 6.8 nH shunt inductors (datasheet curves are measured with them).", "Datasheet p.6"),
    ("A15", "DXP model", "Digitized curves include the Taoglas eval-board matching (L2 4.3 nH, C1 1.5 pF, L1 4.7 nH, L3 3.3 nH, C2 1 pF). Reflection phase = dominant transmission phase + 90 deg.", "Measured .s3p from Taoglas"),
    ("A16", "Digitizing accuracy", "Pass-band plots +/-0.3 dB, wide-band attenuation plots +/-2 dB, VSWR +/-0.1.", "-"),
    ("A17", "PCB", "Interconnects ideal (zero length). 50 ohm lines on the real board add ~0.02-0.05 dB/cm loss and phase.", "Add MSL models once the layout exists"),
    ("A18", "Interferer levels", "Interferer powers at the antenna feed (-10 dBm cellular UL, -20 dBm Iridium/Inmarsat UL, -30 dBm DME) are example values for a co-located handset/terminal.", "Set from the product's EMC environment"),
    ("A19", "Signal levels", "Minimum received power (0 dBic antenna): GPS L1 C/A -128.5 dBm, L5 -127.9 dBm, L2C -130 dBm, GLONASS G1 -131 dBm (signal ICDs).", "-"),
    ("A21", "S-band topology", "S-band patch (ideal dual feed) -> C2327J5003AHF -> TQP3M9037 -> TA1442A -> TQP3M9037 -> TA1442A -> separate S-band output (no diplexer). Antenna only mentioned, modelled as ideal RHCP source.", "User request 2026-10-31"),
    ("A22", "S-band LNA match", "Qorvo 2300-2600 MHz reference design (2.7 nH shunt, 2.4 pF series, 5.6 nH choke); inductor Q 30-50 @2.5 GHz, ESL/ESR [ASSUMED].", "Datasheet p.10"),
    ("A23", "C2327J5003AHF model", "Magnitudes from excess IL, amplitude balance, isolation and input return loss (same RL assumed at all ports); coupled phase = direct + 90 deg - phase balance; reflection/isolation phases chosen for passivity over 2-3 GHz -> excess IL 0.43 dB vs 0.3 typ / 0.4 max (conservative).", "Measured .s4p from TTM"),
    ("A24", "TA1442A model", "Digitized VNA plots p.3-4 with the printed marker values used exactly; S11 = S22 shape (markers differ by < 0.01); min-phase phase.", "Measured .s2p from Tai-Saw"),
    ("A25", "NavIC S signal", "2492.028 MHz, SPS BW 2.046 MHz, RS BW 16.5 MHz, minimum received power -132.3 dBm (0 dBic) used as reference values.", "Verify against the IRNSS SPS ICD"),
    ("A20", "Temperature", "All data at 25 C typical. No temperature, part-to-part or aging spread is modelled.", "-"),
]
INCONSISTENCIES = [
    ("I1", "B7504 vs product brief", "Datasheet p.7 lists 'Group delay typ 4.0 / max 15 ns' (GLONASS band); the product brief lists the same numbers as 'group delay ripple'. The model gives ~13 ns absolute delay and ~4-10 ns ripple, so the datasheet label should read 'ripple'."),
    ("I2", "DXP.02.A front page", "Lists 'L2 1227.625 MHz'; GPS L2 is 1227.60 MHz."),
    ("I3", "DXP.02.A isolation row", "'Isolation (1574.22~1576.62 dB)' - unit should be MHz."),
    ("I4", "DXP.02.A pass-band claim", "Text p.11: L2 pin covers '1164-1300 MHz'. Measured plot p.8: insertion loss >6 dB above ~1263 MHz, so GLONASS G2 upper half, B3 (1268.5) and E6 (1278.75) are not usable."),
    ("I5", "DXP.02.A return loss", "Table p.4 band-2 RL typ -8 dB (max -6) vs. the plot p.6 showing 12-24 dB in the L2/L5 band; the plot is used."),
    ("I6", "DXP.02.A pin naming", "Pin 5 is called 'GPS L2 Output' in the pin table but 'GPS L2/L5 OUT' on the symbol."),
    ("I7", "DXP.02.A RL sign", "Return loss given as negative numbers with 'Max -6.0' - ambiguous min/max sense."),
    ("I8", "HC125A phase balance", "Spec says 'Phase balance 90 degrees' with no tolerance; the typical table shows 91.9-93.0 deg (up to 3 deg off), which costs ~0.01 dB of axial-ratio/combining loss."),
    ("I9", "HC125A pin table vs table columns", "Typical table uses 'Coupling/Transmission' and S11..S44 without stating which pins; the pin table uses 'Pin 1..4'. Mapping assumed (A9)."),
    ("I10", "TQP3M9037 noise table", "NFmin 0.40 dB at 1.5 GHz but 0.29 dB at 1.7 GHz (non-monotonic); Gopt angle jumps 85.8 -> 42.1 -> 157.4 deg between 2.4/2.5/2.6 GHz with |Gopt| ~0.02-0.08 (measurement scatter)."),
    ("I11", "TQP3M9037 switching speed", "Table p.2 note: switching speed with C1 = 10 pF; eval board default C1 = 100 pF (switching table p.5 shows both)."),
    ("I12", "TQP3M9037 stability", "'Unconditionally stable' claim holds (K >= 1.01, mu >= 1.06 from the table) but the margin is only ~1 % at 50 MHz."),
    ("I13", "B8889 spec typo", "Data sheet p.7 'Insertion attenuation' first row has no unit; 'linsertion loss' typo on B7504 p.7."),
    ("I14", "B8889 vs brief", "Brief gives B8889 pass-band 1166-1228 MHz (62 MHz); the datasheet spec bands end at 1228.62 MHz. GLONASS G2 (1246-1256) is outside the B8889 pass-band (>4 dB at 1245 MHz) although the HC125A table and the DXP claim to cover it."),
    ("I15", "SDST vs. parts used", "The automotive SAW selection table (Feb 2020) does not list B7504 or B8889; equivalent automotive parts are e.g. B39162B2611P810 (L1, 0.9 dB, pre-LNA) and B39122B2620P810 (E5b/L2)."),
    ("I17", "DXP.02.A insertion loss", "Table p.4: IL typ 3.8 dB (L1) / 4.2 dB (L2/L5); the measured plots p.7-8 show 3.3 dB / 3.1-3.2 dB at the band centres and reach 3.8 / 4.2 dB only at the band edges. The model follows the plots."),
    ("I18", "TA1442A bandwidth", "Cover page 'BW = 5 MHz' is the specified band 2489.5-2494.5 MHz; the measured 3 dB bandwidth is ~62 MHz (about 2453-2537 MHz) and the filter passes Wi-Fi channel 13 and LTE B41/B7 almost unattenuated."),
    ("I19", "TA1442A VSWR", "Spec VSWR typ 1.2 vs VNA markers 1.04-1.12 in the spec band (sample better than typ)."),
    ("I20", "C2327J5003AHF note", "Spec table footnote: 'values are for the case with shunt capacitor across differential lines' - not explained for a 4-port hybrid; no value given."),
    ("I21", "C2327J5003AHF phase balance", "Spec typ 4 deg / max 8 deg vs plot ~2.5-3.2 deg over 2.4-2.6 GHz; broadband plot shows >= 20 deg above 4.4 GHz (part not usable there)."),
    ("I22", "Two datasheet ages", "TA1442A approval sheet is from 2011 (rev. 1): check the part is still in production before design-in."),
    ("I16", "AN #18 scope", "AN #18 covers 315/434/868 MHz RKE receivers (TDA520x, ATA572x). Only its matching method applies here; its component values do not."),
]
MISSING = [
    ("TQP3M9037", "Noise parameters below 1.5 GHz (L2/L5 band)", "Estimated (A3)"),
    ("TQP3M9037", "S-parameters at 3.3 V (only 4 typical points)", "Not needed (5 V chosen)"),
    ("TQP3M9037", "Fine-step S-parameters (table step 200 MHz)", "Interpolated (A6)"),
    ("TQP3M9037", "P1dB / OIP3 at 1.18-1.6 GHz", "Interpolated (A7)"),
    ("HC125A", "Absolute S-parameter phase, reflection phase, data outside 1150-1630 MHz", "Assumed (A8, A11)"),
    ("B7504", "Phase / group delay outside the GLONASS band, in-band power rating at 1559-1606 MHz, IIP3", "Min-phase estimate; not rated"),
    ("B8889", "Group delay, phase, IIP3", "Min-phase estimate"),
    ("DXP.02.A", "Phase, group delay, out-of-band data above 2.2 GHz, power-handling per port", "Min-phase estimate; held flat"),
    ("All", "Temperature drift of the SAW centre frequency (typ. -30...-40 ppm/K for SAW)", "Not modelled"),
    ("TA1442A", "Phase / group delay, power handling per frequency, IIP3", "Min-phase estimate; 10 dBm max input only"),
    ("C2327J5003AHF", "Reflection at ports other than the input, absolute phase", "Assumed (A23)"),
    ("All", "Package/PCB parasitics for the layout", "Not modelled (A17)"),
]


def main():
    with pd.ExcelWriter(XD / "Extracted_Parameters.xlsx") as xw:
        index = pd.DataFrame([(n, t.attrs["kind"], t.attrs["source"], len(t)) for n, t in TABLES.items()],
                             columns=["sheet", "kind", "source", "rows"])
        index.to_excel(xw, sheet_name="INDEX", index=False)
        for n, t in TABLES.items():
            t.to_excel(xw, sheet_name=n[:31], index=False)
            t.to_csv(XD / f"{n}.csv", index=False)
        pd.DataFrame(ASSUMPTIONS, columns=["id", "item", "assumption", "basis / how to close"]).to_excel(
            xw, sheet_name="Assumptions", index=False)
        pd.DataFrame(INCONSISTENCIES, columns=["id", "where", "finding"]).to_excel(xw, sheet_name="Inconsistencies", index=False)
        pd.DataFrame(MISSING, columns=["part", "missing parameter", "treatment"]).to_excel(xw, sheet_name="Missing", index=False)

    md = ["# Assumptions log", "",
          "Every value that is not printed in a datasheet. Extracted values are in the CSV/XLSX tables "
          "(kind = TABLE or DIGITIZED); everything here is an estimate.", "",
          "| ID | Item | Assumption | Basis / how to close |", "|---|---|---|---|"]
    md += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in ASSUMPTIONS]
    md += ["", "## Parameters missing from the datasheets", "", "| Part | Missing | Treatment |", "|---|---|---|"]
    md += [f"| {a} | {b} | {c} |" for a, b, c in MISSING]
    md += ["", "## Inconsistencies between / within datasheets", "", "| ID | Where | Finding |", "|---|---|---|"]
    md += [f"| {a} | {b} | {c} |" for a, b, c in INCONSISTENCIES]
    (XD / "assumptions_log.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(len(TABLES), "tables written")


if __name__ == "__main__":
    main()
