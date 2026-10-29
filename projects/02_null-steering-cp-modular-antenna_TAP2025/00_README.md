# Modular Null-Steering / CP Antenna: HFSS + MATLAB + Python Verification Pack
Rebuild of Younus, Sultan, Fumeaux & Abbosh, "Reconfigurable Modular Antenna System With Null Steering and Circular Polarization", IEEE TAP 73(5), May 2025.
5–7 GHz, varactor-tuned broadside-coupled phase shifter plus printed dipole, built as 1-D, 2-D and CP systems.

**Read first: `05_docs/DESIGN_GUIDE.pdf`.** It covers terminology, the paper-claim verification table, the stack-up and the assumptions made where the paper is silent. It also has the HFSS steps, a list of design steps the paper leaves out, and a verification checklist.

## Contents
| Folder | What |
|---|---|
| `01_dxf/A_without_antenna` | Phase shifter alone (2-port test board), slot variants, choke or resistor bias |
| `01_dxf/B_antenna_only` | Printed dipole + balun alone |
| `01_dxf/C_units_with_antenna` | Unit type A and mirrored type B (180°), MID ground as drawn / extended |
| `01_dxf/D_system_1D_2units` | 1-D system panel + assembly drawing |
| `01_dxf/E_system_2D_4units` | 2×2 system rows + assembly drawing |
| `01_dxf/F_system_CP_4units` | CP wing boards + assembly drawings (paper colours and the co-phased fix) |
| `01_dxf/G_feed_dividers` | Wilkinson 1:2 / 1:4 at 6 GHz, 25 mm pitch (replaces external splitters) |
| `01_dxf/H_fab_panel` | U1–U4 + phase-shifter and dipole coupons on one panel, fiducials |
| `01_dxf/*.csv, DRC_report.txt` | BOM/placement, 3-D board placement per system, design-rule report |
| `02_python` | `rtps_model.py` (paper eqs. 1–7 plus parasitics, bias LUT), `array_models.py` (1-D/2-D/CP, squint, Monte Carlo, AR), `nsgeom.py` + `build_boards.py` (regenerate all DXFs) |
| `02_python/results` | Plots and CSVs: null-steering cuts, uv maps, Monte Carlo, CP AR table, null-angle → bias LUT |
| `03_matlab` | Same models in MATLAB (`ns_demo_phase_shifter`, `ns_demo_system`); outputs identical to Python (checked in Octave 8.4) |
| `04_hfss` | `hfss_ns_build.py`: PyAEDT build of PS / dipole / unit / 1-D / 2-D / CP with one C variable per varactor |
| `05_docs` | Designer and verification guide (PDF / HTML / MD); **`MODEL_VERIFICATION.md`**: every dimension measured on the model vs. the paper |
| `06_step` | STEP AP242 built with SolidCraft (`02_python/build_step.py`): standalone phase shifter and dipole, units A/B (MID as in the paper / extended), 1-D, 2-D, CP and co-phased CP systems; `STEP_report.txt` checks every body's volume and the board sizes; `renders/` |

## DXF layers
- **Copper:** TOP (front, z = 1.116), MID (inner GND, z = 0.608), BOT (back, z = 0). Holes are on `*_CUTOUT`; subtract them in HFSS.
- **Drills and ports:** VIA (drill circles), PORT (RF port reference).
- **Silkscreen:** SILK_TOP and SILK_BOT carry refdes, labels, polarity and unit numbers. The `<ORG> <PROJECT> REV` field is a placeholder for your own marking.
- **Assembly and fab:** ASSY_TOP / ASSY_BOT (component bodies), FAB (stack-up notes).
- **Coordinates:** mm, board frame (x across, y along, y = 0 at the RF input, beam toward +y). The 3-D placement is in `assembly_3D_placement.csv`.

## Key findings to verify in HFSS
1. **The paper's 145° phase range is beyond the ideal-part model.** A single 12:1 varactor in a reflection-type phase shifter caps out near 116°. About 0.3–0.4 nH of package and pad inductance plus real-part SRF effects bring it to 136–150°.
2. **The 1-D null squints with frequency.** A fixed bias set for 40° at 6 GHz lands at 50.5° at 5 GHz and 33.4° at 7 GHz, so the bias look-up table must be per frequency.
3. **2-D steering envelope.** The 2-D system can only reach |u0| + |v0| ≤ 0.79 with a 143° phase shifter, so ±40° in both planes at once isn't possible.
4. **CP wing assignment.** With the Fig. 1(c) colours and identically mounted wings, opposite wings cancel at broadside. Opposite wings need opposite board types (`SYS_CP_cophased`).
5. **Bias parts.** The 100 nH / 39 pF parts are past self-resonance at 5–7 GHz. Co-simulate them with vendor S-parameter files.
