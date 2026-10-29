# Status: 02_null-steering-cp-modular-antenna_TAP2025

_Last updated: 2026-10-29 (re-verification). Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design pack complete and re-verified against the paper (2026-10-29): balun fixed to Fig. 6(b)/8(b), SolidCraft STEP models for every board and system. Not simulated in HFSS, not fabricated.

## Done
- DXFs for phase shifter, dipole, unit A/B, 1-D, 2-D and CP systems, Wilkinson dividers and fab panel
- Python and MATLAB models of the phase shifter and arrays (outputs match, checked in Octave 8.4)
- Balun matches Fig. 6(b)/8(b): feeder ends at the loop floor, no centre bar, open right stub (2026-10-29; the 2026-10-27 centre bar was wrong)
- `05_docs/MODEL_VERIFICATION.md`: 41 dimensions measured on the model; all match the paper except F_l (13.6 vs 13.7, a paper inconsistency)
- SolidCraft STEP (`06_step/`): PS, dipole (0.508 mm board), units A/B, 1-D, 2-D, CP systems; 176 volume and size checks pass
- Python and MATLAB (Octave 8.4) models re-run on 2026-10-29 with identical results
- Design and verification guide; `05_docs/FIRST_SIMULATIONS.md`

## Open items
- Front decoupling strip `l_s` and its width are not dimensioned in the paper: assumed ls = 4.1, ls_w = 1.2 mm
- Fig. 6(b) back-view values (l4, l5, l7) conflict with the front view; read centre line to centre line. Tune l5/l7 for S11 (see MODEL_VERIFICATION.md)
- Paper draws through vias shared by connector ground and DC pad (Fig. 2(d), 8); the model keeps blind vias at separate positions
- The paper's 145° phase range needs package parasitics to reach; confirm in HFSS (README finding 1)
- Bias parts (100 nH / 39 pF) are past self-resonance at 5–7 GHz: co-simulate with vendor S-parameters
- PyAEDT build `04_hfss/hfss_ns_build.py` not run here (no HFSS licence)
- `hfss_ns_build.py dipole` puts the standalone dipole on the 1.116 mm layer heights (paper: one 0.508 mm board) and its substrate box has a zero size; fix and test where HFSS is available

## Next step
Simulate the standalone phase shifter and dipole in HFSS (see `05_docs/FIRST_SIMULATIONS.md`) and compare with the paper.

## Resume here
Read `05_docs/DESIGN_GUIDE.pdf` and `05_docs/MODEL_VERIFICATION.md`. Rebuild: `cd 02_python && python3 build_boards.py && python3 build_step.py && python3 verify_geometry.py`.

## Tools needed
Python, Octave/MATLAB, SolidCraft CLI (STEP), HFSS + PyAEDT. openEMS could replace HFSS for first checks.

History: see `CHANGELOG.md`.
