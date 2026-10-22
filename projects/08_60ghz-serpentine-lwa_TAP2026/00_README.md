# 08: 60-GHz serpentine slotted-waveguide leaky-wave antenna (replica)

Replica of **Gabsteiger, Robisch, Koelpin, Lurz, "Advancing 60-GHz SISO Radar: Additively Manufactured Leaky Wave
Antenna With Enhanced Beam Steering", IEEE TAP 74(7), July 2026, DOI 10.1109/TAP.2026.3681348**.

Main specs:
- WR15 serpentine with 16 inclined narrow-wall slots;
- 76° frequency beam steering over 58–63.5 GHz with two ports;
- SLA-printed and silver-plated.

Start with **`04_docs/LWA_60GHz_Brief.pdf`**, which explains the antenna from the basics to the advanced design and
documents the replica. `PAPER_SUMMARY.md` is the one-page version.

| Folder | Content |
|---|---|
| `01_cad/` | `build_lwa_cad.py` → `lwa_shell.step` / `lwa_shell.stl` (printable shell with slots and flanges), `lwa_air.step` (air volume for FEM), `geometry.json`; `render_cad.py` (PNG views) |
| `02_python/` | `lwa_design.py` re-derives every design number from the paper equations (β, beam angle, l, Dolph–Chebyshev taper, g_n, tilt and depth fits, array-factor patterns, FMCW numbers) → `results/` |
| `03_sim/` | `slot_unit_cell.py`: full-wave Hertzon/EMerge model of one slot (S-parameters → radiated power → conductance) |
| `04_docs/` | `make_brief.py` → `LWA_60GHz_Brief.pdf`; `concept_figs.py`; `img/` |

## Regenerate

```bash
cd 02_python && python3 lwa_design.py                      # tables, CSV, figures (numpy/scipy/matplotlib)
cd ../01_cad && python3 build_lwa_cad.py                   # STEP/STL (gmsh)
xvfb-run -a python3 render_cad.py                          # renders (pyvista)
cd ../03_sim && HERTZON_MCP_MODE=file python3 slot_unit_cell.py   # FEM check (Hertzon, docs/HERTZON.md)
cd ../04_docs && python3 concept_figs.py && python3 make_brief.py
```

The scripts were run with the Hertzon virtual environment (`/opt/hertzon-venv/bin/python`), which provides
gmsh, pyvista and EMerge. The brief builder only needs reportlab.

## Replication status

**Design equations: reproduced.**
- Beam angle 86.05° at 58 GHz and 53.89° at 63.5 GHz (paper: 86° and 53.8°).
- Path length l = 10.903 mm (paper: 10.9 mm).
- Dolph–Chebyshev a_n identical to Table I; tilts from eq. 17 within 0.15°.

**CAD: built from Table II.** The paper does not give:
- the bend shape;
- the wall and air-gap split;
- the feed and flange details.

These are assumed and documented in `build_lwa_cad.py`.

**Full-wave:** only a single-slot unit cell was simulated on this machine (4 cores, 15 GB). The full antenna needs
a larger workstation. See `03_sim/README.md`.

**Not done: printing, plating and measurement.**
