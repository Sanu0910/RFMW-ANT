# Status: 04_nfms-hybrid-metasurface-cp-rlsa_TAP2022

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design pack complete with STEP models. Not simulated in HFSS, not fabricated.

## Done
- RLSA (1920 slots), HM I and HM II DXFs, per-laminate fab DXFs and drill files
- Python cell models, geometry, study and steering model; MATLAB `nfms_demo` matches Python
- STEP AP242 models built with SolidCraft (`06_step/`)
- Design guide, including the paper's equation error and the radial-line λg issue

## Open items
- PyAEDT Floquet and full-system builds not run here (no HFSS licence)
- Assumed values are marked `[ASSUMED]` in the geometry code and listed in the guide

## Next step
Run the Type I/II Floquet unit-cell sweeps in HFSS and compare the phase/transmission with the cell models.

## Resume here
Read `05_docs/DESIGN_GUIDE.pdf`; rebuild with `build_nfms.py`, `nfms_study.py`, `build_step.py` (see README).

## Tools needed
Python, SolidCraft CLI (STEP), Octave/MATLAB, HFSS + PyAEDT.

History: see `CHANGELOG.md`.
