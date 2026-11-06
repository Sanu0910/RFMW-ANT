# Repository status: tools and projects

_Last updated: 2026-11-06._

Local machine: `bash tools/setup_local.sh`, then `python3 tools/doctor.py` (see `LOCAL_SETUP.md`). Cloud sessions start from a fresh container, so the tools below are **not installed** when a new session begins. Reinstall the ones a task needs with the commands in the last column (all need root; the container runs as root).

## Tools

Verified in the session of 2026-10-29:

| Tool | Result | How it was checked | Reinstall |
|---|---|---|---|
| SolidCraft MCP (`solidcraft-cli`) | Working | Built a 40×20×5 mm block with a Ø8 hole; volume 3748.7 mm³ matches the hand calculation | Preinstalled; registered in `.mcp.json` |
| Python deps (`docs/requirements.txt` + scikit-rf) | Working | All modules import | `pip install -r docs/requirements.txt scikit-rf` |
| openEMS v0.37.0 + CSXCAD | Working | `MSL_NotchFilter.py` tutorial ran headless: 15 402 steps, 270 k cells, 37 s (111 MCells/s) | `bash tools/install_openems.sh` (~20 min build) |
| gds2openEMS | Installed | Install script import check passed | `bash tools/install_gds2openems.sh` (after openEMS) |
| KiCad 9.0.9 (chroot in `/opt/kicad9`) | Working | `kicad-cli pcb drc` on project 13 ran and gave the documented result | `DOCKER_MIRROR=mirror.gcr.io bash tools/install_kicad_mcp.sh` |
| KiCad MCP server 2.8.3 | Working | Server starts and lists 244 tools. Registered as `kicad` in `.mcp.json` | Same script (the server only connects once `/opt/KiCAD-MCP-Server` exists) |
| KiCadRoutingTools (grid_router 0.23.7) | Working | Test route on `cap_chain.kicad_pcb`: 0 → 8 tracks | `sh tools/install_krt.sh` |
| Hertzon 0.2.6 (EMerge FEM) + MCP | Working (MCP registered as `hertzon` in `.mcp.json`, 33 tools) | `HairpinFilter.hzn` example solved headless: 91-point S2P over 2.0–2.9 GHz, passband S21 −2.3 dB / S11 −13 dB at 2.56 GHz | `bash tools/install_hertzon.sh` |
| Backplane 0.10.0 | Working | Headless web UI answered HTTP 200 on port 3787 | `bash tools/install_backplane.sh` |
| REA | Not installed | Not needed for RF/PCB work | `bash tools/install_rea.sh` |
| Qucs-S 26.1.1 (Qucsator-RF 1.0.7, ngspice) | Working (local Windows, 2026-11-01) | Project 16 `build_qucs.py`: 3-port front end within 0.0007 dB of scikit-rf in band | `winget install -e --id TheQucsTeam.Qucs-S` |
| ngspice 45.2, KLayout 0.30.0, Meep 1.29 + MPB, GNU Radio 3.10.12, LibrePCB, OpenOCD | Installed (local WSL Ubuntu 26.04, 2026-11-01) | Version / import checks (`tools/doctor.py`) | `apt-get install ngspice klayout meep mpb python3-meep gnuradio librepcb openocd` |
| SDRangel 8.0.0, CLI-Hub 0.4.1 (CLI-Anything) | Installed (local Windows, 2026-11-01) | Version checks; CLI-Hub registry has no EDA/RF harness yet | `winget install -e --id f4exb.sdrangel`; `uv tool install cli-anything-hub` |

Notes:
- Use `DOCKER_MIRROR=mirror.gcr.io` for the KiCad install. Anonymous Docker Hub pulls hit HTTP 429 rate limits.
- `kicad-cli` and `pcbnew` only run inside the chroot: call them through `/opt/KiCAD-MCP-Server/kicad-python-chroot.sh`.
- SolidCraft runs headless unless the SolidCraft desktop app is open.
- Not available in this environment: Ansys HFSS (no licence), MATLAB (use GNU Octave), FreeCAD, ngspice.

## Projects

Each project folder has its own `STATUS.md` and `CHANGELOG.md`.

| # | Project | State |
|---|---|---|
| 01 | X-band 8-way MSL divider housing V3 | Base, lid, gasket STEP + PCB V3 DXF + Gerbers + drawings done; assembly STEPs pending |
| 02 | L/S-band 4-ch CRPA board + back cover | PCB Rev A DRC clean, fab package + BOM, back cover STEP, RF budget, drawings, design report; test boards + Rev B gain plan pending |
