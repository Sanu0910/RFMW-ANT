# MATLAB / Octave models
Run `nfms_demo` in this folder. It prints Table I, the corrected inverse, cell values, the radial-line TM0 permittivity and the
phase-map statistics, and writes `matlab_check.csv`. `python ../02_python/crosscheck_matlab.py` compares every number with the Python
models (tolerance 1e-6 relative, NaN where the beam is broadside).

| File | What |
|---|---|
| `nfms_params.m` | all constants (same as `nfmsgeom.py` / `cells.py`) |
| `nfms_beam.m` | eqs. (1)-(2) |
| `nfms_inverse.m` | eqs. (3)-(4), **corrected** (factor 2) |
| `nfms_cell_type1.m`, `nfms_cell_type2.m` | closed-form cell S21 models |
| `nfms_tm0.m` | exact TM0 dispersion of the air + TLY-5 radial line |
| `nfms_phase_maps.m` | correction, gradient, HM I and HM II maps (48 x 48) |
