# RFMW-ANT: RF / Microwave Antenna Design Reproductions

Engineering reproductions of recent antenna and microwave papers, built so each one can be **re-simulated, checked and fabricated**:
- layered DXF geometry with silkscreen and assembly layers
- Python and MATLAB models of the paper's equations, cross-checked against each other
- PyAEDT scripts for Ansys HFSS
- a designer's guide per paper: terminology, a check of the paper's claims, assumptions, HFSS workflow, missing design steps, verification checklist

The papers themselves are **not** included (IEEE copyright); see [`docs/REFERENCES.md`](docs/REFERENCES.md) for citations and DOIs.

## Projects

| # | Folder | Paper | Band | Content |
|---|---|---|---|---|
| 01 | [`projects/01_reactive-beamforming-metasurface_TAP2025`](projects/01_reactive-beamforming-metasurface_TAP2025) | Almunif, Alsolamy, Grbic, *Network-Based Design of Reactive Beamforming Metasurfaces*, IEEE TAP 2025 | 10 GHz | 11×11 aperture-coupled cells, 121-port network synthesis, Fig. 11/12 meander rebuilds, eq. 1–25 MATLAB pipeline |
| 02 | [`projects/02_null-steering-cp-modular-antenna_TAP2025`](projects/02_null-steering-cp-modular-antenna_TAP2025) | Younus, Sultan, Fumeaux, Abbosh, *Reconfigurable Modular Antenna System With Null Steering and CP*, IEEE TAP 2025 | 5–7 GHz | Varactor reflection-type phase shifter + printed dipole; 1-D / 2-D null steering, CP; with/without-antenna boards, dividers, fab panel |
| 03 | [`projects/03_1bit-rba-mmwave-1x5_AWPL2026`](projects/03_1bit-rba-mmwave-1x5_AWPL2026) | Jiao, Wang, Xu, *Compact Low-Cost 1-Bit Reconfigurable Wide Beam-Steering mm-Wave Array*, IEEE AWPL 2026 | 25–29 GHz | PIN-diode 1-bit shorted-patch element, 1×5 array, fixed-phase preloading, 1:5 divider |
| 04 | [`projects/04_nfms-hybrid-metasurface-cp-rlsa_TAP2022`](projects/04_nfms-hybrid-metasurface-cp-rlsa_TAP2022) | Afzal, Esselle, Koli, *A Beam-Steering Solution With Highly Transmitting Hybrid Metasurfaces and CP High-Gain RLSA Antennas*, IEEE TAP 2022 | 20 GHz | CP RLSA (960 slot pairs) + two rotating hybrid metasurfaces (48×48 Type I/II cells), near-field meta-steering to ~41°; **STEP models** |

**Each project folder contains:**
- `00_README.md`: what is where
- `PAPER_SUMMARY.md`: what the paper does, how, and what our checks found
- `*_docs/DESIGN_GUIDE.pdf / .md / .html`: the full designer and verification guide
- DXF folders with preview PNGs, a BOM / placement CSV and a DRC report
- Python, MATLAB and HFSS (PyAEDT) folders
- STEP models (project 04 on), built with [SolidCraft](https://github.com/bherbruck/solidcraft) `solidcraft-cli`

## Quick start
```bash
pip install -r docs/requirements.txt
cd projects/03_1bit-rba-mmwave-1x5_AWPL2026/02_python && python rba_array.py && python build_rba.py
```
- MATLAB / Octave: `cd` into a project's MATLAB folder and run its `*_demo*` or `*selftest*` script.
- HFSS: run the project's `hfss_*.py` with Ansys AEDT 2024.x and PyAEDT.

## Conventions
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) covers units, DXF layer naming, HFSS import, and how assumptions are flagged.

## Status
| Item | Status |
|---|---|
| Python and MATLAB models | Run and verified against each other (MATLAB checked in GNU Octave 8.4) |
| HFSS PyAEDT scripts | Written against `ansys.aedt.core` but not executed (no licence in the build environment). The GUI steps in each guide are the fallback. |
| STEP models | Built with `solidcraft-cli` 0.11.1; part volumes checked against hand calculations (`06_step/STEP_report.txt`) |
| Geometry | Follows each paper's published dimensions; every undocumented value is listed in that guide's assumptions table |
