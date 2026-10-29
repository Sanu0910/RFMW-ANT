# Status: 05_rf-module-enclosures_SMA

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Three enclosures modelled with drawings. **Blocked on board data**: board sizes and port positions are placeholders.

## Done
- Base + lid STEP, assembly and exploded STEP for A_PD_MSL, B_MSL_SL and C_UWB
- A3 drawings, engraving DXFs and PCB-interface DXFs
- Design report per box (checks, cavity resonances, masses)
- Vendor STEP of the HUBER+SUHNER 23_SMA-50-0-272/133_N in every assembly

## Open items
- **Needs your input:** real board L × W × t and port positions for each module (`02_python/encl_config.py`)
- Lid engraves "BEL" as text until `logo/BEL_logo.svg` is supplied

## Next step
Get the latest board layouts, update `encl_config.py`, rerun `build_enclosures.py` and `make_drawings.py` (about 5 min).

## Resume here
`00_README.md`, then `05_docs/DESIGN_NOTES.md`.

## Tools needed
SolidCraft CLI on PATH, Python (ezdxf, shapely, matplotlib, pillow).

History: see `CHANGELOG.md`.
