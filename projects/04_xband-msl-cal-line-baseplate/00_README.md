# 04: X-band MSL cal-line base plates (CRL-XB-CALP-15 / -65)

Lightweight open base plates for the two X-band THRU cal boards (RO4350B 30 mil, MSL launch → via → stripline → via → MSL,
15 mm and 65 mm), each with two HUBER+SUHNER 23_SMA-50-0-272/133_N end-launch jacks, the same connector as the project 01 divider housing.

| Folder | Content |
|---|---|
| `00_input/` | Customer cal-line zip (all four boards) and the extracted X-band DXFs used here |
| `00_vendor/` | H+S connector STEP and data sheet (copied from project 01) |
| `02_python/` | `config.py` (the one file to edit), `plate.py` (geometry + SolidCraft scripts), `drawing.py`, `report.py`, `build_all.py` |
| `03_step/` | `<PN>_PLATE.step` (CNC part), `<PN>_ASSY.step`, `<PN>_ASSY_EXPLODED.step`, renders, SolidCraft scripts |
| `04_drawings/` | `<PN>_DRAWING.pdf`: sheet 1 CNC drawing (sections, views, hole table, notes), sheet 2 assembly + parts list |
| `05_docs/` | Design report, BOM, hole table |

Rebuild everything: `cd 02_python && ../../../.venv/Scripts/python.exe build_all.py` (needs `solidcraft-cli`).
One board or part only: `build_all.py plate 15`, `build_all.py drawing report`.

The UWB RT5880 10 mil boards in the zip are not covered here; adding them is a new entry in `config.BOARDS`
(they need their own board thickness and a check that the pin fits their narrower launch).
