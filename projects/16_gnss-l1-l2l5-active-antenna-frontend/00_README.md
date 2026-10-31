# 16 - GNSS L1 + L2/L5 (+ NavIC S) active antenna front end

RF circuit models, Touchstone files, an ANSYS Circuit (PyAEDT) automation script and a simulation report for a
dual-branch GNSS active-antenna front end, built from eight supplied datasheets and application notes.

```
L1 patch    -> HC125A -> TQP3M9037 -> B7504 -> TQP3M9037 -> B7504 ---+
                                                                     +-> DXP.02.A (combiner) -> RF out
L2/L5 patch -> HC125A -> TQP3M9037 -> B8889 -> TQP3M9037 -> B8889 ---+
```
Topology confirmed by the user on 2026-10-31. A single chain is not possible because B7504 (L1) and B8889 (L2/L5)
have disjoint pass-bands. LNAs run at +5 V / 70 mA.

S-band branch (separate output): S patch -> C2327J5003AHF -> TQP3M9037 -> TA1442A -> TQP3M9037 -> TA1442A;
35.0 dB gain, 1.17 dB NF at 2492.028 MHz (`Scripts/sband.py`). Internal note: `Report/Internal_ActiveAntenna_RF_Technical_Note.pdf`.

## Results (25 C, virtual RHCP input -> RF out, 50 ohm)
| Band | Gain | NF | In VSWR |
|---|---|---|---|
| L1 / E1 / B1C 1575.42 MHz | 38.6 dB | 0.74 dB | 2.29 |
| L5 / E5a 1176.45 MHz | 42.0 dB | 0.59 dB | 1.63 |
| L2 1227.60 MHz | 40.1 dB | 0.62 dB | 1.96 |

All stages are unconditionally stable. Main risks: no pre-LNA filter (DME at 1150 MHz and Iridium at 1621 MHz pass the
SAW skirts), gain higher than most receivers need, and GLONASS G2 is outside the B8889 pass-band. Details and
recommendations are in the report.

## Folders
| Folder | Content |
|---|---|
| `Touchstone/` | `TQP3M9037_5V.s2p` (extracted from the datasheet, with noise block), `HC125A.s4p`, `B7504.s2p`, `B8889_matched.s2p`, `B8889_bare_deembedded.s2p`, `DXP02A.s3p`, `DXP02A_common_to_L1.s2p`, `DXP02A_common_to_L2L5.s2p`, `PatchCP_ideal_RHCP_feed.s4p` (estimated, see headers), `TQP3M9037_stage_5V_with_bias.s2p`, `SIM_*` (simulated results). GHz / RI format |
| `Scripts/` | `ds_data.py` (all extracted numbers, single source), `models.py`, `simulate.py`, `build_extracted.py`, `make_schematics.py`, `aedt_circuit.py` (PyAEDT), `build_circuitrf.py`, `crosscheck_heavi.py`, `make_report.py`, `build_all.py` |
| `ANSYS_Project/` | AEDT project and exported `.s3p` once `aedt_circuit.py` has run; run logs |
| `circuitRF/` | `gnss_frontend.cnl` netlist and its circuitRF S-parameter result (cross-check) |
| `Report/` | `GNSS_FrontEnd_Simulation_Report.pdf` / `.docx`, `error_log.md` |
| `Images/` | schematics (PNG + SVG), connection diagram, all plots |
| `Extracted_Data/` | 36 CSV tables + `Extracted_Parameters.xlsx`, `assumptions_log.md`, `results_*.csv`, cross-check JSON |

## Rebuild
```
cd Scripts
python build_all.py            # everything except AEDT
python build_all.py --aedt     # also builds/solves the AEDT project (AEDT 2026 R1 + licence)
python aedt_circuit.py --gui   # AEDT only, with the GUI visible
```
Needs Python with numpy, scipy, matplotlib, scikit-rf, pandas, openpyxl, python-docx, reportlab, pyaedt (1.x).
heavi runs from the repo `.venv` (see `STATUS.md`); circuitRF from `%LOCALAPPDATA%\circuitRF-1.6.1\x\circuitRF.exe`
(or set `CIRCUITRF_EXE`).

## Data quality
Measured/extracted: LNA S- and noise parameters, HC125A typical table, all spec tables. Estimated: SAW and diplexer
Touchstone files (digitized curves + minimum-phase reconstruction), hybrid absolute phase, antenna. Replace the estimated
files with vendor measurements when available and rerun `build_all.py`.
