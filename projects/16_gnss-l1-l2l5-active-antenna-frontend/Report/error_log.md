# Error log

Problems met while building project 16 (2026-10-31) and what was done about each.

| # | Step | Error | Resolution / status |
|---|---|---|---|
| E1 | Topology | Chain as first written (HC125A - LNA - filter - LNA - filter - DXP) cannot pass both bands: B7504 (L1) and B8889 (L2/L5) have disjoint pass-bands | Asked the user; two-branch topology with the DXP as combiner confirmed |
| E2 | Tool install | `pip install ansys-aedt-core` not found on the package index | Installed `pyaedt` 1.9.0 (provides `ansys.aedt.core`) |
| E3 | Tool install | `uvx` install of the PyAEDT MCP server from GitHub blocked by the permission classifier | Not installed; user asked to run it themselves if wanted |
| E4 | Tool install | heavi 0.7.9 fails to import on Python 3.12 (`mutable default UnassignedType` dataclass error) and downgraded the global numpy | heavi moved to the repo `.venv`; one-line local fix (`__hash__ = object.__hash__` in `heavi/node.py`); global numpy restored to 2.5.4 |
| E5 | Tool install | circuitRF portable zip: `unzip` warns about backslash paths | Extracted with PowerShell `Expand-Archive`; MCP server registered locally (`claude mcp add circuitrf`) |
| E6 | HC125A model | Table magnitudes with arbitrary reflection/isolation phases gave a non-passive 4-port (largest singular value 1.05) | Phases chosen to minimise the largest singular value (1.013); residual scaling <= 0.11 dB (assumption A10) |
| E7 | circuitRF | `Token overflow: got 17 tokens, expected 9 for 2-port` when reading MHz / DB Touchstone files | All Touchstone files rewritten as GHz / RI; circuitRF then reads them |
| E8 | heavi cross-check | First comparison differed by up to 1.4 dB | Cause: linear vs cubic interpolation of the 200 MHz LNA table and missing parasitics. With identical models the difference is < 0.01 dB; the interpolation sensitivity is reported as model uncertainty (A6) |
| E9 | ANSYS AEDT | PyAEDT 1.9 + AEDT 2026 R1: `Failed to start new AEDT gRPC session` (transport mode WNUA) from both Bash and PowerShell; `ansysedt -grpcsrv` process starts but does not open the port within 10 min | Not solved in this session. Run `python Scripts/aedt_circuit.py --gui` on the workstation (an interactive AEDT can answer licence/first-run prompts), or `--version 2024.1` for the 2024 R1 install. Two idle `ansysedt.exe` processes from these attempts (PIDs 9720, 10988) could not be closed from the session (permission denied) - close them in Task Manager |
