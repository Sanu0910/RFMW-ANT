# Changelog: 15_cband-6x6-dualpol-stacked-patch_match-debug

Newest first.

## 2026-10-30
- Bench measurements of the built panel added (`05_measured/`: gain vs reference horn, S21, S11 of both ports, setup photos) and compared with the simulation (`02_openems/compare_measured.py` -> `03_results/measured_vs_sim.png`). Measured S11 follows the simulated array; measured gain 20.4 dBi peak (25-35 % aperture efficiency mid-band) falling to 11-14 dBi at 6.2-6.4 GHz.
- Results-only client report `04_docs/Telmart_CBand_Array_Results_Status.pdf` (5 pages, TM-RF-15-002 Rev. A) built by `02_openems/client_results_report.py`: results, neutral re-plotted figures (`04_docs/res_*.png`) and project status; no methods, tools or design concepts disclosed. Preliminary array curves refreshed (5.5 h into the runs).
- Client report `04_docs/Telmart_CBand_Array_VSWR_Report.pdf` (8 pages, Telmart branding, doc. TM-RF-15-001 Rev. A) built by `02_openems/client_report.py`; `html2pdf.js` takes an optional footer text. Preliminary array curves refreshed (4.5 h into the runs).
- Preliminary full-array S11/S22/S21 (`02_openems/array_interim.py`, `03_results/array_interim*`) from the runs in progress, ~2.5 h in; added to report section 6, marked preliminary.
- Report rev. 2 (12 pages): new section 7 "Wideband redesign study", section 9 rewritten as "What can be done next" (work plan + design advice), array status updated.
- Wideband element study: `sim_wb_element.py` (aperture-coupled stacked patch, single/dual-pol), `opt_wb_element.py` ((1+4) evolution strategy), `match_wb.py` (feed-layer matching on every candidate), `wb_figures.py`. 40 runs; best candidate `wbN4` VSWR<=3 4.95-5.75 GHz, no better than the present element. Results in `03_results/wb*`, `opt*`, `match_wb.txt`, `opt_wb_log.txt`.
- `sim_array.py`: port coordinates rounded to the 1 um mesh grid (port 2 at x = -1.5081 mm injected no energy), `--threads` and `--nrts` options. Full-array runs restarted locally in WSL.
- WSL helper scripts `02_openems/_run_wsl.sh`, `_batch_wsl.sh`, `_py_wsl.sh`, `_sum_wsl.sh`, `_pull_wsl.sh` for running the models on the local PC.

## 2026-10-29
- PDF report `04_docs/CBand_6x6_Array_S11_Analysis_Report.pdf`: element results, parasitic-size sweep, matching study, root causes, fixes. Uses only the as-built stack-up (air gap er 1.0). NF2FF now stores frequency-domain data only.
- New project: inputs, openEMS element/array models, first element result and matching study (S11 debug of the C-band array).
