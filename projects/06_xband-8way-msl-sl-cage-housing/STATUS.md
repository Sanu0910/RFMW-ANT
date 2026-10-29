# Status: 06_xband-8way-msl-sl-cage-housing

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Cage housing modelled with drawing (CRL-XB-PD8-01). Some inputs still assumed; not machined.

## Done
- Base, cage lid, box-only, assembly and exploded STEP
- A3 drawing and cage-from-below view
- Design report: 52 cells, lowest cell resonance 18.5 GHz

## Open items
- Board thickness 1.524 mm is **[ASSUMED]**: send the stack-up
- Output flanges 2-3, 4-5, 6-7 leave only 1.8 mm between them: assemble in order or change connector
- Seam between output connectors relies on a conductive gasket
- Customer DXF package (`00_input/`) is not in git; copy it in to rebuild

## Next step
Confirm the stack-up, then rebuild with `cage_build.py` and `make_cage_drawing.py` (~15 min).

## Resume here
`00_README.md` → Open points; `05_docs/design_report.md`.

## Tools needed
SolidCraft CLI, Python; reuses `projects/05_rf-module-enclosures_SMA/02_python`.

History: see `CHANGELOG.md`.
