# 11: customcst, a CST-style 3D FDTD solver in Python (saved copy)

Copy of the `customcst/` folder of **[inhardwetrust/Electrodinamics_exp](https://github.com/inhardwetrust/Electrodinamics_exp/tree/main/customcst)**,
commit `1d269c6` (2026-10-22), with the repository's `LICENSE`.

## What it is
An attempt to rebuild part of CST Studio's time-domain workflow from scratch, in about 13k lines of Python:
1. import a STEP model;
2. assign materials and ports per body;
3. build a non-uniform rectilinear (hexahedral) grid;
4. run a 3D FDTD;
5. read S11 like on a VNA.

The upstream README states that all of the code was written with Claude, with the author directing.

The code is built in levels, bottom-up (upstream `ARCHITECTURE.md`):

| Level | Folder | Role |
|---|---|---|
| 0 | `geometry/` | STEP import via OpenCASCADE (`cadquery-ocp`) into triangulated bodies; KiCad STEP handling (copper merged per layer, vias as one body), holes, ray casting |
| 1 | `project/` | project model: materials per body, ports, frequency range, boundaries (`model.toml`) |
| 2 | `mesh/rectilinear.py` | compute grid: fixpoints at planar CAD faces, max step λ_min/N per material, grading limit |
| 3 | `discretize/` | ε, σ, μ and PEC masks on the Yee grid (staircase; conformal is planned) |
| 4 | `solver/` | non-uniform Yee FDTD with numba kernels, CPML, lumped ports and loads, 2D waveguide-port mode solver (`port_mode.py`), S-parameters (`sparams.py`), VNA-style display (`vna.py`) |
| 5 | monitors | S-matrix and Z_in done; DFT field monitors and far field still planned |
| 6 | `view/` | PySide6 + vispy GUI: geometry, sections with the mesh, results |

The models worked through upstream:
- a microstrip with discrete ports;
- a 50 Ω coax with waveguide ports (Z0 = 49.5 Ω from the port solver);
- an SMA connector on a 4-layer PCB with a grounded coplanar line and a 50 Ω lumped load, at about −30 dB S11
  over 4–6 GHz;
- the same board imported from a KiCad STEP export.

`checks/` holds 21 numerical self-checks (cavity, line, ports, waveguide port, vias, VNA, STEP import …).

Open items listed upstream:
- wideband dispersive dielectrics (Djordjevic–Sarkar / Debye ADE);
- separate merge distance and minimum cell, for narrow CPW gaps;
- field monitors and far field.

## Why it is useful here
- It is a readable, small FDTD reference next to openEMS (`docs/GDS2OPENEMS.md`) and Hertzon (`docs/HERTZON.md`).
- Its KiCad STEP → FDTD path suits our boards, for example the feed lines of
  `projects/07_ais140-2w-gnss-tracker`.

## Run it
```bash
cd upstream_snapshot/customcst
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # numpy scipy numba vispy PySide6 cadquery-ocp
python3 main.py                   # GUI (needs a display)
python3 checks/check_fdtd_line.py # one of the numerical self-checks
```
I have not run it here.

## Licence and changes
- The upstream is **public domain (The Unlicense)**, see `upstream_snapshot/LICENSE`.
- Changes from upstream: only this README, and `customcst/CLAUDE.md` renamed to `customcst/UPSTREAM_CLAUDE.md`,
  so that AI coding assistants working in this repository do not load the upstream's agent instructions.
- The sibling folders `atomicfdtd/`, `myinventor/` and `pseudo_cst_3d/` of the upstream repository were not copied.
