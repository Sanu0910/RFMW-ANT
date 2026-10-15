# MATLAB: network-based reactive metasurface synthesis

Run these in order:

1. `mtsf_selftest` checks power consistency (Re Z vs pattern Gram), analytic vs finite-difference gradients, and the embedded→open pattern conversion.
2. `mtsf_selftest_touchstone` checks the .sNp reader round trip.
3. `mtsf_demo_paper_designs` runs Designs I–IV on an analytic 11×11 array, in about 2–3 minutes in Octave.
4. `mtsf_design_from_hfss` is the real flow. Set `design`, `snp` and `ffdir` at the top.

`reference_plots/demo_cuts_octave_run.png` shows what the demo produced here, so you can compare your MATLAB run. `demo_designI_X.csv` is the demo output in `build_dxf.py` format.

The equation-to-function map is in `06_docs/DESIGN_GUIDE.md` §7.

**Requirements:** base MATLAB. The Optimization Toolbox is optional; it enables `fmincon`, otherwise the built-in projected L-BFGS is used. The code is Octave-compatible.
