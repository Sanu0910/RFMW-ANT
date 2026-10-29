# Status: 02_null-steering-cp-modular-antenna_TAP2025

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design pack complete, balun corrected to paper Fig. 6, STEP export added. Not simulated in HFSS, not fabricated.

## Done
- DXFs for phase shifter, dipole, unit A/B, 1-D, 2-D and CP systems, Wilkinson dividers and fab panel
- Python and MATLAB models of the phase shifter and arrays (outputs match, checked in Octave 8.4)
- Printed-dipole balun redrawn as the paper's closed loop + centre feeder + tuning stub (2026-10-27)
- Layer-by-layer 3-D STEP export from the same geometry (`06_step/`, cadquery)
- Design and verification guide; `05_docs/FIRST_SIMULATIONS.md`

## Open items
- Front decoupling strip `l_s` and its width are not dimensioned in the paper: assumed ls = 4.1, ls_w = 1.2 mm
- The paper's 145° phase range needs package parasitics to reach; confirm in HFSS (README finding 1)
- Bias parts (100 nH / 39 pF) are past self-resonance at 5–7 GHz: co-simulate with vendor S-parameters
- PyAEDT build `04_hfss/hfss_ns_build.py` not run here (no HFSS licence)

## Next step
Simulate the standalone phase shifter and dipole in HFSS (see `05_docs/FIRST_SIMULATIONS.md`) and compare with the paper.

## Resume here
Read `05_docs/DESIGN_GUIDE.pdf`; regenerate DXFs with `02_python/build_boards.py`.

## Tools needed
Python, Octave/MATLAB, cadquery (STEP), HFSS + PyAEDT. openEMS could replace HFSS for first checks.

History: see `CHANGELOG.md`.
