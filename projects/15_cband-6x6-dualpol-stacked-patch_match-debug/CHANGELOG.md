# Changelog: 15_cband-6x6-dualpol-stacked-patch_match-debug

Newest first.

## 2026-10-30
- Preliminary full-array S11/S22/S21 (`02_openems/array_interim.py`, `03_results/array_interim*`) from the runs in progress, ~2.5 h in; added to report section 6, marked preliminary.
- Report rev. 2 (12 pages): new section 7 "Wideband redesign study", section 9 rewritten as "What can be done next" (work plan + design advice), array status updated.
- Wideband element study: `sim_wb_element.py` (aperture-coupled stacked patch, single/dual-pol), `opt_wb_element.py` ((1+4) evolution strategy), `match_wb.py` (feed-layer matching on every candidate), `wb_figures.py`. 40 runs; best candidate `wbN4` VSWR<=3 4.95-5.75 GHz, no better than the present element. Results in `03_results/wb*`, `opt*`, `match_wb.txt`, `opt_wb_log.txt`.
- `sim_array.py`: port coordinates rounded to the 1 um mesh grid (port 2 at x = -1.5081 mm injected no energy), `--threads` and `--nrts` options. Full-array runs restarted locally in WSL.
- WSL helper scripts `02_openems/_run_wsl.sh`, `_batch_wsl.sh`, `_py_wsl.sh`, `_sum_wsl.sh`, `_pull_wsl.sh` for running the models on the local PC.

## 2026-10-29
- PDF report `04_docs/CBand_6x6_Array_S11_Analysis_Report.pdf`: element results, parasitic-size sweep, matching study, root causes, fixes. Uses only the as-built stack-up (air gap er 1.0). NF2FF now stores frequency-domain data only.
- New project: inputs, openEMS element/array models, first element result and matching study (S11 debug of the C-band array).
