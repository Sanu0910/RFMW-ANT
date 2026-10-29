# Status: 01_reactive-beamforming-metasurface_TAP2025

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design pack complete. Not simulated in HFSS, not fabricated.

## Done
- Fig. 3 unit cell and 11×11 lumped-port arrays for Designs I–V (DXF)
- Reactances digitised from Figs. 4a/6a/7a/8b/9b (`02_reactance_data/`)
- Fig. 11 and Fig. 12 meander rebuilds (`03_dxf_realized/`)
- MATLAB Eq. 1–25 pipeline with self-tests, checked in GNU Octave 8.4
- Python geometry library, DXF builder, DRC and PyAEDT script
- Design guide PDF/HTML/MD (`06_docs/`)

## Open items
- PyAEDT script `hfss_build_and_export.py` was never run (no HFSS licence)
- Meander lengths come from an analytic stub model: replace with HFSS-extracted Zin before fabrication
- Digitised reactances are about ±3 Ω and may be clipped at the colourbar ends
- Assumed geometry values are listed in guide §3 and live in `msgeom.py`

## Next step
Run the HFSS array build, export Z-matrices, run `mtsf_design_from_hfss`, then extract the meander Zin table.

## Resume here
Read `06_docs/DESIGN_GUIDE.pdf`, then follow the Quick start in `00_README.md`.

## Tools needed
Python (numpy/ezdxf/shapely), GNU Octave or MATLAB, Ansys HFSS + PyAEDT (licence needed).

History: see `CHANGELOG.md`.
