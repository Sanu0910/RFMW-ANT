# Status: 16_gnss-l1-l2l5-active-antenna-frontend

_Last updated: 2026-10-31. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** L-band (L1 + L2/L5) and NavIC S-band branches modelled and simulated; internal technical note issued as Draft A. Models, Touchstone files, system simulation, three-solver cross-check, schematics, extracted tables and
the PDF/DOCX report are done. The ANSYS AEDT project is scripted (`Scripts/aedt_circuit.py`) but has not been solved
yet: PyAEDT could not start a headless AEDT 2026 R1 gRPC session from the automation shell.

## Done
- All 8 supplied documents read; numbers in `Scripts/ds_data.py` (TABLE / DIGITIZED / [ASSUMED] tags)
- Touchstone: LNA (extracted + noise), HC125A 4-port, B7504, B8889 (with 6.8 nH), DXP.02.A 3-port, ideal RHCP feed
- System simulation (scikit-rf): gain, NF (noise-correlation matrices), VSWR, K/mu, group delay, phase, cascade budgets,
  interferer table
- Cross-checks: heavi (< 0.004 dB) and circuitRF 1.6.1 CLI (< 0.001 dB) against the reference
- Schematics (ANSYS-style PNG/SVG), connection diagram, 16 result figures
- Rejection / insertion loss / return loss / isolation / output noise / XPD / SFDR / worst case (`extra_rf.py`, report section 7A)
- Report `Report/GNSS_FrontEnd_Simulation_Report.pdf` + `.docx` (22 pages), assumptions log, error log

- Filter rejection document `Report/Filter_Rejection_Analysis.pdf/.docx` (for sharing, no internal marking)

## Open items
- Internal note: fill Doc. No., prepared/checked/approved fields
- S-band selectivity (Wi-Fi / LTE B41 overload) needs a narrower pre-filter - design decision
- Run `python Scripts/aedt_circuit.py --gui` on the workstation (or `--version 2024.1`), then `python Scripts/build_all.py`
  to add the AEDT comparison to the report (error log E9)
- Close the two idle `ansysedt.exe` processes left by the failed headless attempts (PIDs 9720, 10988)
- Replace estimated SAW/DXP/HC125A files with vendor measurements; get low-band LNA noise parameters (A3, A6, A8, A12)
- Design decisions for the user: pre-LNA filtering (DME/Iridium), gain reduction, input match, G2 coverage

## Tools
- Python 3.12 with scikit-rf, reportlab, schemdraw, pyaedt 1.9 (installed 2026-10-31)
- heavi 0.7.9 in the repo `.venv` with a local one-line fix in `heavi/node.py` (`__hash__ = object.__hash__`)
- circuitRF 1.6.1 portable at `%LOCALAPPDATA%\circuitRF-1.6.1\x`, MCP server registered locally (`claude mcp add circuitrf`)
- ANSYS AEDT 2026 R1 (licence server 1055@localhost) and 2024 R1 installed

## Resume
`cd Scripts && python build_all.py` regenerates every output from `ds_data.py`.
