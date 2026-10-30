# Repository status: tools and projects

_Last updated: 2026-10-29._

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

Notes:
- Use `DOCKER_MIRROR=mirror.gcr.io` for the KiCad install. Anonymous Docker Hub pulls hit HTTP 429 rate limits.
- `kicad-cli` and `pcbnew` only run inside the chroot: call them through `/opt/KiCAD-MCP-Server/kicad-python-chroot.sh`.
- SolidCraft runs headless unless the SolidCraft desktop app is open.
- Not available in this environment: Ansys HFSS (no licence), MATLAB (use GNU Octave), FreeCAD, ngspice.

## Projects

Each project folder has its own `STATUS.md` and `CHANGELOG.md`.

| # | Project | State |
|---|---|---|
| 01 | Reactive beamforming metasurface | Design pack done; HFSS not run |
| 02 | Null-steering CP modular antenna | Design pack done, balun fixed, STEP added; HFSS not run |
| 03 | 1-bit RBA mm-wave 1×5 | Design pack done; HFSS not run |
| 04 | NFMS hybrid metasurface CP RLSA | Design pack + STEP done; HFSS not run |
| 05 | RF module enclosures (SMA) | Modelled; **waiting for real board sizes** |
| 06 | X-band 8-way cage housing | Modelled; board thickness assumed |
| 07 | AIS-140 2W GNSS tracker | Premium DRC-clean; Lite needs the EC200U footprint replaced |
| 08 | 60 GHz serpentine LWA | Equations + CAD done; full-wave and prototype not done |
| 09 | AERIS-10 radar study | Study complete |
| 10 | Minev quantum notebook | Reference copy |
| 11 | customcst FDTD | Reference copy, not run |
| 12 | NOVA-RF1 multi-tool board | Routed 101/104 nets; 3 nets and RF matching left |
| 13 | SPS-24G-01 presence switch | Routed + fab package; mains safety items open |
| 14 | MVDR beamforming explainer | Complete |
| 15 | C-band 6×6 stacked-patch S11 debug | Report rev. 2 (root cause + redesign study, iteration 1 below target); full-array runs in progress |
