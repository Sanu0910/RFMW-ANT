# NFMS Beam-Steering CP RLSA with Hybrid Metasurfaces (20 GHz): DXF + STEP + Python + MATLAB + HFSS Pack
Rebuild of Afzal, Esselle & Koli, IEEE TAP 70(1), Jan 2022. A fixed CP radial-line slot array, Ø345 mm with 960 slot pairs, sits under two rotating hybrid metasurfaces (48 × 48 cells of 7.5 mm). Rotating them steers the beam to about 41° elevation at any azimuth.

**Read first: `05_docs/DESIGN_GUIDE.pdf`.** It covers terminology, a table checking the paper's claims (with an equation error and the radial-line λg issue), assumptions, stack-up, HFSS steps and what the paper leaves out.

| Folder | What |
|---|---|
| `01_dxf/A_rlsa` | RLSA laminate (TLY-5 1.6 mm, 1920 slots, probe pocket), Al ground plate, `slot_table.csv` |
| `01_dxf/B_hm1`, `C_hm2` | HM I (correction + gradient) and HM II (gradient): M1–M4 patches, DRILL, rim holes, cell-assignment and drill tables |
| `01_dxf/D_fab_laminates` | One DXF per laminate (LAM1/LAM2/LAM3) plus the post-bond drill file, for each HM |
| `01_dxf/E_unit_cells` | Paper example cells for HFSS checks |
| `02_python` | `cells.py` (Type I/II models), `nfmsgeom.py` (geometry), `build_nfms.py` (DXF/BOM/DRC), `nfms_study.py` (every check and the steering model), `build_step.py` (STEP via SolidCraft), `crosscheck_matlab.py` |
| `03_matlab` | `nfms_demo` and its functions; identical to Python (checked in Octave 8.4) |
| `04_hfss` | `hfss_nfms_build.py`: Type I/II Floquet unit-cell sweeps, RLSA with probe, full system at any (ψ1, ψ2) |
| `05_docs` | design guide (md / html / pdf) |
| `06_step` | STEP AP242: `RLSA_feed_assembly.step`, `HM1.step.zip`, `HM2.step.zip`, `NFMS_system_psi1_0_psi2_120.step.zip`, plus renders |

**Rebuild:**
```bash
cd 02_python
python build_nfms.py      # DXFs, previews, tables, BOM, DRC          (~30 s)
python nfms_study.py      # results/study_report.txt + plots/CSVs     (~2 min)
python build_step.py 0 120  # STEP models with solidcraft-cli on PATH  (~4 min)
```

**DXF layers** (mm, top view; HM x = phase-delay axis):

| Layer | Contents |
|---|---|
| OUTLINE | board / plate edge (HM: V notch at +x) |
| TOP_CU / TOP_SLOT | RLSA copper / slots to subtract |
| BOT_POCKET | Ø2.8 × 0.6 mm pocket under the RLSA laminate (probe head) |
| M1 … M4 | HM patch layers (M1 faces the RLSA) |
| DRILL | HM Type II non-plated holes |
| NPTH | spacer / SMA holes |
| SILK_TOP / ASSY / FAB | marking (axis arrow, 15° scale) / component bodies / notes |
