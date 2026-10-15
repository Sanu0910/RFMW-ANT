"""Compare 03_matlab/matlab_check.csv (written by nfms_demo.m) with the Python models."""
import os, math, numpy as np
import cells as CL, nfmsgeom as G, nfms_study as S
m = np.loadtxt(os.path.join(os.path.dirname(__file__), "..", "03_matlab", "matlab_check.csv"), delimiter=",")
p = S.K0 * math.sin(math.radians(G.H["theta0"]))
th, ph = zip(*[S.beam(p, p, 0, b) for b in (30, 60, 90, 120, 150, 180)])
inv = [S.inverse_correct(t, f, p) for t, f in zip(th[:5], ph[:5])]
s1 = CL.s21_type1(4.0, 3.7)
pm = G.phase_maps()
py = list(th) + list(ph) + [i[0] for i in inv] + [i[1] for i in inv] + [20 * math.log10(abs(s1)), math.degrees(np.angle(s1)),
      CL.phase_type2_unwrapped(0), CL.phase_type2_unwrapped(3.4), S.tm0_eps_eff(), np.sum(~np.isnan(pm["hm1"])), np.nanmean(pm["hm1"]), np.nanmean(pm["hm2"])]
names = ["theta%d" % k for k in range(6)] + ["phi%d" % k for k in range(6)] + ["psi1_%d" % k for k in range(5)] + ["psi2_%d" % k for k in range(5)] + \
        ["T1_dB", "T1_deg", "T2_r0", "T2_rmax", "TM0_eps", "n_cells", "hm1_mean", "hm2_mean"]
bad = 0
for n, a, b in zip(names, m, py):
    if n == "phi5": continue          # broadside: azimuth undefined
    ok = abs(a - b) <= 1e-6 * max(1, abs(b)) + 1e-4
    bad += not ok; print("%-9s matlab %14.6f python %14.6f %s" % (n, a, b, "" if ok else "  <-- MISMATCH"))
print("ALL MATCH" if not bad else "%d mismatches" % bad)
