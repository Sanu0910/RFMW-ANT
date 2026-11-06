# RFMW-ANT: RF / Microwave Antenna Design Projects

RF / microwave antenna design projects, one folder per project under `projects/NN_name/`, built so each one can be **re-simulated, checked and fabricated**.

Tooling:
- EM simulation: [`docs/GDS2OPENEMS.md`](docs/GDS2OPENEMS.md) — openEMS FDTD + gds2openEMS, installed with `tools/install_gds2openems.sh`.
- EM simulation: [`docs/HERTZON.md`](docs/HERTZON.md) — Hertzon 3D full-wave FEM simulator (EMerge solver, MCP server), installed with `tools/install_hertzon.sh`.
- PCB: [`docs/KICAD_MCP.md`](docs/KICAD_MCP.md) — KiCad + KiCAD-MCP-Server headless, installed with `tools/install_kicad_mcp.sh`.
- Agentic CAD workspace: [`docs/BACKPLANE.md`](docs/BACKPLANE.md) — Backplane, installed with `tools/install_backplane.sh`.
- Reverse engineering: [`docs/REA.md`](docs/REA.md) — REA CLI/MCP, installed with `tools/install_rea.sh`.

## Projects

| # | Folder | Description | Band | Content |
|---|---|---|---|---|
| 01 | [`projects/01_xband-8way-msl-wpd-housing`](projects/01_xband-8way-msl-wpd-housing) | Machined housing CRL-XB-PD8-03 (V3) for the X-band 8-way microstrip Wilkinson divider on RO4350B 30 mil, 9 x H+S 23_SMA-50-0-272/133_N, BEL logo engraved | 8–12 GHz | base / lid with channel cage / gasket STEP, PCB V3 DXF (M2 holes) + Gerber/drill set, 2D channel-mode and Z0 checks, A3 drawings, report, BOM |
| 02 | [`projects/02_ls-crpa4-rf-module`](projects/02_ls-crpa4-rf-module) | CRL-LS-CRPA4: 4-ch active CRPA board (limiter + 2 LNA + 3 SAW per band, L1 + L2/L5 combined, NavIC S at lambda/2), combined L+S back cover for the BEL CRL 4-element L/S CRPA board | 1.16–1.61 / 2.49 GHz | Ø200 mm 4L PCB (DRC clean), fab package + BOM, combined back cover STEP, RF budget, drawings, design report |

**Each project folder contains** `00_README.md` (what is where), `STATUS.md` (where it stands, open items, next step) and `CHANGELOG.md` (dated history).

## Quick start
Running locally (all tools + MCP servers) and pushing finished projects: see [`LOCAL_SETUP.md`](LOCAL_SETUP.md).

```bash
pip install -r docs/requirements.txt
```

## Conventions
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) covers units, DXF layer naming, HFSS import, and how assumptions are flagged. The tool setup is in [`STATUS.md`](STATUS.md).
