# 02 - CRL-LS-CRPA4: L/S-band 4-channel CRPA RF module, shield cover, test board, back cover

Front end for the BEL CRL 4-element circular CRPA board `combine_model_2.0` (`00_input/PCB_FAB_LS_4E`, Ø200 mm,
6-layer FR4 + RO4350B, 4 × GPDF6010 L1/L2 patches + 4 NavIC S patches, lumped hybrids on board).
Planned deliverables (part numbers [ASSUMED], confirm):

| P/N | Item |
|---|---|
| CRL-LS-RFM-01 | plug-in RF module, 4 per CRPA, on the existing 2 × 13-pad footprint: L1 + L2/L5 chains combined to OUT_L, NavIC S chain to OUT_S (limiter, 2 LNA, 3 SAW per band; parts from projects 16 / 17) |
| CRL-LS-RFM-01-SC | machined shield cover of the module (per-band compartments) |
| CRL-LS-RFM-TB01 | module test board (RO4350B 0.508, SMA, THRU/LINE cal) |
| CRL-LS-CRPA4-BC01 | back cover of the CRPA: 8 × SMA bulkhead + DC connector |

**State:** Rev A board DRC clean, fab package + BOM in `04_fab/`, board + combined back cover STEP in `06_step/`, drawings in `07_drawings/`, design report in `05_docs/`. See `STATUS.md`.

Rebuild: `bash 02_python/run_drc.sh` (board + DRC), `python 02_python/make_fab.py` (fab files, BOM, STEP), `python 02_python/covers.py main` (back cover, ~6 min).

## Files
| Folder | Content |
|---|---|
| `00_input/` | customer Gerbers + fab note (`PCB_FAB_LS_4E/`), original zip |
| `00_vendor/` | CLM-83-2W+ and RLM-63-2W+ data sheets |
| `00_reference/p16`, `p17` | copied from projects 16 / 17 on `main`: part data `ds_data.py`, Touchstone files, spec tables; KiCad footprints `CRPA17.pretty`, `crpa_design.py`, `build_pcb.py`, RF budgets, BOM, report |
| `02_python/` | `read_interface.py` (decodes the Gerbers), `gerber_geo.py` |
| `05_docs/` | `CRL-LS_design_basis.md`, `CRL-LS_module_footprint.csv`, `CRL-LS_module_placement.csv`, `CRL-LS_main_board_holes.csv`, `CRL-LS-CRPA4_design_report.md/.pdf`, RF budget / rejection / power CSV, review gaps, `img/` |
| `07_drawings/` | `CRL-LS-CRPA4_DRAWINGS.pdf` (6 sheets) + PNG per sheet |

## Rebuild
```bash
cd 02_python && ../../../.venv/Scripts/python.exe read_interface.py     # needs gerbonara, shapely
```
