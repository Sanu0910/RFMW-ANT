# Status: 11_customcst-fdtd

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Reference copy only (The Unlicense). Not run here.

## Done
- Upstream `customcst/` at commit `1d269c6` copied, with an overview in `00_README.md`

## Open items
- Never run in this repo; its 21 self-checks are untested here
- Upstream open items: dispersive dielectrics, narrow-gap meshing, field monitors and far field

## Next step
Optional: run `checks/check_fdtd_line.py` and compare with openEMS on one of our boards.

## Resume here
`00_README.md` → Run it.

## Tools needed
Python venv with numpy, scipy, numba, vispy, PySide6, cadquery-ocp.

History: see `CHANGELOG.md`.
