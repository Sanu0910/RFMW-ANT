# Changelog: 16_gnss-l1-l2l5-active-antenna-frontend

Newest first.

## 2026-10-31
- Shareable filter-rejection document `Report/Filter_Rejection_Analysis.pdf/.docx` (`Scripts/make_rejection_doc.py`, 10 pages): in-band IL and ripple per GNSS band, filter compliance with the data-sheet limits (L-band filters + TA1442A), near-band and out-of-band rejection after each filter stage and for the complete L1, L2/L5 and NavIC S chains, cross-band rejection, interference consequences; tables in `Extracted_Data/rejection_doc_*.csv`.
- NavIC S-band branch added (user request, 2 new datasheets): Tai-Saw TA1442A 2492 MHz SAW and TTM/Xinger C2327J5003AHF hybrid; chain patch -> hybrid -> TQP3M9037 (Qorvo 2.3-2.6 GHz ref. design) -> TA1442A -> TQP3M9037 -> TA1442A, separate output (`Scripts/sband.py`, `TA1442A.s2p`, `C2327J5003AHF.s4p`, `SIM_SBand_2port.s2p`). Gain 35.0 dB, NF 1.17 dB; Wi-Fi ch 13 / LTE B41 overload LNA 2 and the TA1442A rating (3 dB BW ~62 MHz).
- Simulator-style plots (`Scripts/aedt_style.py`: report window, Curve Info, marker tables, Smith chart) for L-band (`lband_aedt_plots.py`) and S-band.
- Internal technical note `Report/Internal_ActiveAntenna_RF_Technical_Note.pdf/.docx` (BEL internal marking, 20 pages; `make_internal_report.py`). AEDT script now also builds design `SBand_2port`.
- More filter Touchstone files (user request): `B8889_bare_deembedded.s2p` (6.8 nH inductors removed), `DXP02A_common_to_L1.s2p`, `DXP02A_common_to_L2L5.s2p`; plot `Images/filter_touchstone_files.png` and table in report section 7A.
- Added `Scripts/extra_rf.py` (user request: rejection graphs, insertion loss, other RF parameters): filter rejection of B7504 / B8889 / DXP against the datasheet attenuation limits (all pass, min margin ~3 dB), skirt close-ups, per-stage and system rejection with an interferer-band table, insertion loss per part and per chain, return loss and isolation, output noise PSD and total noise power, LHCP rejection / axial-ratio contribution of the hybrid, per-band summary (Te, mismatch loss, OIP3, OP1dB, SFDR, C/N0, GD), L1-L5 group-delay difference, worst-case gain/NF from datasheet limits. New report section 7A (report now 22 pages).
- Project created from the user's 8 datasheets (TQP3M9037, HC125A, DXP.02.A, B7504, B8889, RF360 GNSS SAW brief,
  RF360 SAW selection table, RF360 AN #18). Topology confirmed with the user: two branches
  (HC125A - LNA - SAW - LNA - SAW) combined by the DXP.02.A; LNAs at 5 V; report as PDF and DOCX.
- Extracted data, component models and Touchstone files; system simulation with noise, stability, group delay,
  cascade and interferer analysis; heavi and circuitRF cross-checks; schematics; PDF/DOCX report.
- PyAEDT script for the AEDT Circuit project written; headless AEDT 2026 R1 gRPC start failed (error log E9).
