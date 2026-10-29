# Changelog: 02_null-steering-cp-modular-antenna_TAP2025

Newest first. Add an entry for every change (date, what changed, why). Entries up to 2026-10-29 were built from git history.

## 2026-10-29
- Re-verified every model against the paper; `02_python/verify_geometry.py` writes `05_docs/MODEL_VERIFICATION.md` (41 measured dimensions)
- Fixed the printed-dipole balun: removed the centre bar added on 2026-10-27, which is not in Fig. 6(b) or Fig. 8(b) and lay over the slot square; the feeder now ends at the loop floor
- STEP models rebuilt with SolidCraft instead of cadquery; standalone dipole on its 0.508 mm board (was the 1.116 mm stack); 1-D, 2-D and CP system assemblies added; `06_step/STEP_report.txt` checks each body
- Ellipses drawn with 256 segments (was 96); DXFs, previews and DRC regenerated
- Python and MATLAB (Octave 8.4) models re-run: results unchanged

## 2026-10-27
- proj02: add layer-by-layer 3-D STEP export (cadquery) from the paper geometry (`7e181a3`)
- proj02: correct printed-dipole balun to paper Fig. 6; save source PDF (`5bb8f3e`)

## 2026-10-17
- Project added to the repository (earlier history was squashed into this commit) (`79894bd`)
