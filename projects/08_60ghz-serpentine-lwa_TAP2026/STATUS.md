# Status: 08_60ghz-serpentine-lwa_TAP2026

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Design equations reproduced and CAD built. Only a single-slot full-wave check done; not printed or measured.

## Done
- Beam angle 86.05° / 53.89° at 58 / 63.5 GHz (paper 86° / 53.8°), l = 10.903 mm, Dolph–Chebyshev taper matches Table I
- Printable shell STEP/STL and FEM air volume (`01_cad/`)
- Single-slot Hertzon/EMerge unit cell (`03_sim/slot_unit_cell.py`)
- Brief PDF (`04_docs/LWA_60GHz_Brief.pdf`)

## Open items
- Bend shape, wall/air-gap split and feed/flange details are assumed (`build_lwa_cad.py`)
- Full-antenna full-wave run needs a bigger machine than 4 cores / 15 GB
- Printing, silver plating and measurement not done

## Next step
Run the full serpentine in Hertzon or openEMS on a larger workstation, then print a prototype.

## Resume here
`04_docs/LWA_60GHz_Brief.pdf` or `PAPER_SUMMARY.md`; regenerate per README.

## Tools needed
Hertzon venv (`/opt/hertzon-venv`, gmsh, pyvista, EMerge), reportlab, Xvfb.

History: see `CHANGELOG.md`.
