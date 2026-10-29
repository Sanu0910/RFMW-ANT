# Status: 03_1bit-rba-mmwave-1x5_AWPL2026

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design pack complete. Not simulated in HFSS, not fabricated.

## Done
- DXFs: single element, 5-port 1×5 array, array with 1:5 preload divider, split antenna/feed boards
- Python beam table, element-width study, squint, Monte Carlo and PSO (`rba_array.py`)
- MATLAB `rba_demo`, identical to Python (checked in Octave 8.4)
- PyAEDT build with R/L/C variables per diode for beam codes
- Design guide (`05_docs/DESIGN_GUIDE.pdf`)

## Open items
- PyAEDT script not run here (no HFSS licence)
- Geometry assumptions are listed in the design guide

## Next step
Simulate the single element in HFSS (both diode states), then the 5-port array.

## Resume here
Read `05_docs/DESIGN_GUIDE.pdf`; regenerate DXFs with `02_python/build_rba.py`.

## Tools needed
Python, Octave/MATLAB, HFSS + PyAEDT.

History: see `CHANGELOG.md`.
