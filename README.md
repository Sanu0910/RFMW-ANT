# RFMW-ANT: RF / Microwave Antenna Design Reproductions

Engineering reproductions of recent antenna and microwave papers, built so each one can be **re-simulated, checked and fabricated**:
- layered DXF geometry with silkscreen and assembly layers
- Python and MATLAB models of the paper's equations, cross-checked against each other
- PyAEDT scripts for Ansys HFSS
- a designer's guide per paper: terminology, a check of the paper's claims, assumptions, HFSS workflow, missing design steps, verification checklist

The papers themselves are **not** included (IEEE copyright); see [`docs/REFERENCES.md`](docs/REFERENCES.md) for citations and DOIs.

EM simulation tooling: [`docs/GDS2OPENEMS.md`](docs/GDS2OPENEMS.md) — openEMS FDTD + gds2openEMS (GDSII → openEMS), installed with `tools/install_gds2openems.sh`.
EM simulation tooling: [`docs/HERTZON.md`](docs/HERTZON.md) — Hertzon 3D full-wave FEM simulator (EMerge solver, HFSS-style GUI, MCP server), installed with `tools/install_hertzon.sh`.
PCB tooling: [`docs/KICAD_MCP.md`](docs/KICAD_MCP.md) — KiCad 9 + KiCAD-MCP-Server headless, installed with `tools/install_kicad_mcp.sh`.
Agentic CAD workspace: [`docs/BACKPLANE.md`](docs/BACKPLANE.md) — Backplane (KiCad + FreeCAD viewers, KiCad fork with IPC schematic API, multi-agent orchestration), installed with `tools/install_backplane.sh`.
Reverse engineering: [`docs/REA.md`](docs/REA.md) — REA (Reverse Engineer Anything) CLI/MCP for binaries, Electron/JS apps, firmware and more, installed with `tools/install_rea.sh`.

## Projects

| # | Folder | Paper | Band | Content |
|---|---|---|---|---|
| 01 | [`projects/01_reactive-beamforming-metasurface_TAP2025`](projects/01_reactive-beamforming-metasurface_TAP2025) | Almunif, Alsolamy, Grbic, *Network-Based Design of Reactive Beamforming Metasurfaces*, IEEE TAP 2025 | 10 GHz | 11×11 aperture-coupled cells, 121-port network synthesis, Fig. 11/12 meander rebuilds, eq. 1–25 MATLAB pipeline |
| 02 | [`projects/02_null-steering-cp-modular-antenna_TAP2025`](projects/02_null-steering-cp-modular-antenna_TAP2025) | Younus, Sultan, Fumeaux, Abbosh, *Reconfigurable Modular Antenna System With Null Steering and CP*, IEEE TAP 2025 | 5–7 GHz | Varactor reflection-type phase shifter + printed dipole; 1-D / 2-D null steering, CP; with/without-antenna boards, dividers, fab panel |
| 03 | [`projects/03_1bit-rba-mmwave-1x5_AWPL2026`](projects/03_1bit-rba-mmwave-1x5_AWPL2026) | Jiao, Wang, Xu, *Compact Low-Cost 1-Bit Reconfigurable Wide Beam-Steering mm-Wave Array*, IEEE AWPL 2026 | 25–29 GHz | PIN-diode 1-bit shorted-patch element, 1×5 array, fixed-phase preloading, 1:5 divider |
| 04 | [`projects/04_nfms-hybrid-metasurface-cp-rlsa_TAP2022`](projects/04_nfms-hybrid-metasurface-cp-rlsa_TAP2022) | Afzal, Esselle, Koli, *A Beam-Steering Solution With Highly Transmitting Hybrid Metasurfaces and CP High-Gain RLSA Antennas*, IEEE TAP 2022 | 20 GHz | CP RLSA (960 slot pairs) + two rotating hybrid metasurfaces (48×48 Type I/II cells), near-field meta-steering to ~41°; **STEP models** |
| 05 | [`projects/05_rf-module-enclosures_SMA`](projects/05_rf-module-enclosures_SMA) | Machined RF housings (own design) for a microstrip power divider, an MSL→stripline transition and a UWB power divider, with HUBER+SUHNER 23_SMA-50-0-272/133_N connectors | 0.5–12 GHz | Base + screwed RF-lip lid, engraved logo/labels, STEP parts + assembly + exploded, A3 drawings, PCB interface DXF, design checks |
| 06 | [`projects/06_xband-8way-msl-sl-cage-housing`](projects/06_xband-8way-msl-sl-cage-housing) | CRL BEL Antenna / RFM Lab X-band 8-way stripline divider (MSL→SL launches): cage housing built from the board DXF | 8–12 GHz | Base + lid with a ribbed cage (52 cells, lowest resonance 18.5 GHz), 9 H+S SMA, engraved lid, STEP parts/assembly/exploded, A3 drawing |
| 07 | [`projects/07_ais140-2w-gnss-tracker`](projects/07_ais140-2w-gnss-tracker) | AIS-140 two-wheeler GNSS/LTE tracker, two variants in subfolders: **`premium/`** (CRL-TRK-2W-01: ESP32-S3, SIM7080G, NEO-F10N NavIC, 4-layer) and **`lite/`** (CRL-TRK-2W-L1: Quectel EC200U + L76K, 2-layer, cost-reduced) | L1/L5 GNSS, LTE-M/NB-IoT | per variant: KiCad 9 project (ERC/DRC clean), Gerbers, CPL, BOM, STEP, assembly drawings, design report |
| 08 | [`projects/08_60ghz-serpentine-lwa_TAP2026`](projects/08_60ghz-serpentine-lwa_TAP2026) | 60-GHz serpentine slotted-waveguide leaky-wave antenna (Gabsteiger et al., IEEE TAP 2026): 16 inclined edge slots, 76° frequency scan with two ports, SLA + silver | 58–63.5 GHz | design equations reproduced (Python), parametric STEP/STL replica, Hertzon/EMerge unit-slot FEM check, basic-to-advanced brief PDF |
| 09 | [`projects/09_aeris10-plfm-radar_study`](projects/09_aeris10-plfm-radar_study) | Study + saved copy of AERIS-10 (PLFM_RADAR): open-source 10.5 GHz pulse-LFM phased-array radar, Artix-7 DSP chain, STM32, ADAR1000 ×4 | 10.5 GHz | learning notes, derived performance numbers, 2 findings (alumina-guide λg, beam phases), upstream snapshot (CERN-OHL-P / MIT) |
| 10 | [`projects/10_minev-quantum-notebook`](projects/10_minev-quantum-notebook) | Saved copy of Zlatko Minev's Quantum Notebook: 76 talks, lectures and notes on superconducting qubits, cQED, quantum hardware design and error mitigation (CC BY-NC-ND 4.0) | — | verbatim PDF archive + website source, index by shelf/year |
| 11 | [`projects/11_customcst-fdtd`](projects/11_customcst-fdtd) | Saved copy of customcst: CST-style STEP → non-uniform grid → 3D FDTD → S11 solver in Python (public domain) | RF/microwave | source, numerical checks, notes |
| 12 | [`projects/12_multitool-rf-board`](projects/12_multitool-rf-board) | CRL-MT1: original firmware-compatible multi-tool RF board (STM32WB55, CC1101 sub-GHz, ST25R3916 NFC, 125 kHz RFID, IR, iButton); runs the open Flipper Zero firmware; not a Flipper clone, no trademark/trade dress | sub-GHz · 13.56 MHz · 125 kHz | architecture from firmware pin map, schematic netlist, BOM, firmware GPIO header (schematic stage) |
| 13 | [`projects/13_bathroom-presence-sensor-switch`](projects/13_bathroom-presence-sensor-switch) | SAMAY ELECTRONICS **SPS-24G-01** smart presence light switch: HLK-LD2410B 24 GHz radar, ATtiny13A, MOC3063 + BTA16 zero-cross triac, HLK-PM01, 85–265 VAC, mains-isolated | 24 GHz presence / 230 V | 70×56 mm 2-layer KiCad 9 mains PCB (ERC/DRC clean, ≥9.5 mm isolation + slot), Gerbers, CPL, BOM, STEP, datasheet, safety review, firmware |
| 14 | [`projects/14_mvdr-beamforming-explainer`](projects/14_mvdr-beamforming-explainer) | MVDR (Capon) adaptive beamformer animated explainer: steering vectors, covariance, nulls, eigenvalues and SINR computed live from the algorithm for anti-jam / anti-spoof GNSS arrays | antenna arrays / DSP | unit-tested `mvdr_core.py`, matplotlib+ffmpeg render engine, 1080p explainer video |
| 15 | [`projects/15_cband-6x6-dualpol-stacked-patch_match-debug`](projects/15_cband-6x6-dualpol-stacked-patch_match-debug) | User design: C-band 6×6 dual-pol edge-fed stacked-patch array (RT5880 + 4 mm air + FR4) whose VSWR never gets below 3:1 | 4–7 GHz | openEMS element and full-array models from the DXFs, parasitic sweep, matching study, PDF root-cause report |

**Each project folder contains:**
- `00_README.md`: what is where
- `PAPER_SUMMARY.md`: what the paper does, how, and what our checks found
- `*_docs/DESIGN_GUIDE.pdf / .md / .html`: the full designer and verification guide
- DXF folders with preview PNGs, a BOM / placement CSV and a DRC report
- Python, MATLAB and HFSS (PyAEDT) folders
- STEP models (project 04 on), built with [SolidCraft](https://github.com/bherbruck/solidcraft) `solidcraft-cli`

## Quick start
**Running locally (all tools + MCP servers) and pushing finished projects:** see [`LOCAL_SETUP.md`](LOCAL_SETUP.md).

```bash
pip install -r docs/requirements.txt
cd projects/03_1bit-rba-mmwave-1x5_AWPL2026/02_python && python rba_array.py && python build_rba.py
```
- MATLAB / Octave: `cd` into a project's MATLAB folder and run its `*_demo*` or `*selftest*` script.
- HFSS: run the project's `hfss_*.py` with Ansys AEDT 2024.x and PyAEDT.

## Conventions
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) covers units, DXF layer naming, HFSS import, and how assumptions are flagged.

Each project has a `STATUS.md` (where it stands, open items, next step) and a `CHANGELOG.md` (dated history). Start there when coming back to a project. The tool setup is in [`STATUS.md`](STATUS.md).

## Status
| Item | Status |
|---|---|
| Python and MATLAB models | Run and verified against each other (MATLAB checked in GNU Octave 8.4) |
| HFSS PyAEDT scripts | Written against `ansys.aedt.core` but not executed (no licence in the build environment). The GUI steps in each guide are the fallback. |
| STEP models | Built with `solidcraft-cli` 0.11.1; part volumes checked against hand calculations (`06_step/STEP_report.txt`) |
| Geometry | Follows each paper's published dimensions; every undocumented value is listed in that guide's assumptions table |
