# 15 - C-band 6x6 dual-pol stacked-patch array: S11 / VSWR debug

User design, 4-7 GHz, 276.86 mm board. Symptom: gain is fine but VSWR stays above 3:1.

- `01_input/` the supplied DXFs (F_CU, IN2_CU, GND) and stack-up PDF
- `02_openems/` geometry loader (`cbgeom.py`), element model, full-array model, matching study, plots
- `03_results/` S-parameter CSVs, summaries, plots
- `04_docs/` analysis write-up (to come)

See `STATUS.md` for the current state.
