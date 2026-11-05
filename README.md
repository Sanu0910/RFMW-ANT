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

_No projects yet._

**Each project folder contains** `00_README.md` (what is where), `STATUS.md` (where it stands, open items, next step) and `CHANGELOG.md` (dated history).

## Quick start
Running locally (all tools + MCP servers) and pushing finished projects: see [`LOCAL_SETUP.md`](LOCAL_SETUP.md).

```bash
pip install -r docs/requirements.txt
```

## Conventions
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) covers units, DXF layer naming, HFSS import, and how assumptions are flagged. The tool setup is in [`STATUS.md`](STATUS.md).
