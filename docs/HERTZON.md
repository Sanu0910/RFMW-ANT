# Hertzon: 3D full-wave EM simulator (FEM)

[Hertzon](https://github.com/c8501024/Hertzon) (GPL-2.0+) is a desktop full-wave electromagnetic simulator with an
HFSS-style workflow:
1. draw the model;
2. assign boundaries and ports;
3. run an adaptive-mesh setup and frequency sweeps;
4. read S-parameters, fields, far field and RCS.

The finite-element solver underneath is [EMerge](https://github.com/FennisRobert/EMerge).

## Install (done in this environment)

```bash
tools/install_hertzon.sh        # clones to /opt/src/Hertzon, venv in /opt/hertzon-venv (Python 3.13)
```

| Item | Value |
|---|---|
| Hertzon | 0.1.21 (commit 10f344a) |
| EMerge | 3.0.0a25 |
| Python | 3.13 |
| Solver warm-up | test solve finished in 126 s; kernels compiled |
| Test suite | 83 passed, 1 skipped |

## Use

```bash
# GUI (needs a display; on a headless machine use xvfb-run)
/opt/hertzon-venv/bin/hertzon /opt/src/Hertzon/examples/PatchAntenna.hzn

# solve without the GUI
/opt/hertzon-venv/bin/python -m hertzon.solver.run Project.hzn DesignName Setup1 out_dir
```

- Results are written to `<project>.hznresults/<design>/<setup>/`: Touchstone `*.sNp`, `sparams_*.npz`, `fields_*.npz`, `farfield_*.npz`.
- Useful examples for this repo:
  - `GPS_L1_RHCP.hzn`, a GNSS patch
  - `PatchAntenna.hzn`
  - `Microstrip.hzn`
  - `HairpinFilter.hzn`
  - `SphereRCS.hzn`

## MCP server (AI assistant)

Hertzon ships an MCP server, `hertzon-mcp`, that lets Claude Code build and run simulations. It is installed but
**not registered**. To register it, run:

```bash
/opt/hertzon-venv/bin/python -m hertzon.mcp --install claude    # adds an entry to ~/.claude.json
/opt/hertzon-venv/bin/python -m hertzon.mcp --config            # print the settings for other clients
```

Start a new Claude Code session afterwards.

## Notes

- Hertzon is under active development, so verify important results with measurements, analytical estimates or a
  second tool such as openEMS (see `docs/GDS2OPENEMS.md`).
- Possible use in this repo: simulate the tracker's LTE / GNSS antenna feeds and matching networks.
