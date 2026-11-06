# Changelog: 04_xband-msl-cal-line-baseplate

Newest first.

## 2026-11-06 - Rev A base plates
- New project. Input: customer `MSL_SL_Cal_Lines.zip` (X-band DXFs extracted to `00_input/`); connector STEP and data
  sheet copied from project 01.
- `02_python/`: `config.py`, `plate.py` (geometry, 11 checks, SolidCraft scripts), `drawing.py`, `report.py`, `build_all.py`.
- Outputs: CRL-XB-CALP-15 / -65 plate, assembly and exploded STEP + renders; A3 CNC drawings; design report, BOM,
  hole table. Board thickness 1.73 mm is [ASSUMED] until the fab confirms it.
