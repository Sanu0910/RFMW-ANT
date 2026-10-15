"""1-bit reconfigurable bit array (RBA) study: 5 x RCSPA, D = 4.5 mm, fixed-phase preloading (paper Sec. II-C).
Element n excitation:  a_n = exp(j(P_n + b_n * S_n)),  b_n in {0,1},  P_n = fixed preload (deg),
S_n = state-2 phase (ideal -180 deg; paper Fig.4: -176..-178 deg).  Beam pattern in the xoz (E) plane.
Run:  python rba_array.py  -> results/*.png, *.csv"""
import os, csv, itertools
import numpy as np

C0 = 299792458.0
D = 4.5e-3
N = 5
PRELOAD_PAPER = np.array([55.78, -5.79, -73.37, 0.0, -111.72])
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
TH = np.radians(np.arange(-90, 90.01, 0.25))
STATES = np.array(list(itertools.product((0, 1), repeat=N)))         # 32 x 5

ELEM_TAPER_DB_AT_90 = 4.0   # read from paper Fig.3(a): xoz-plane co-pol ~ -1.7 dB at 60 deg, ~ -4 dB at 90 deg

def elem(th, taper90=None):
    """E-plane (xoz) element field |E| of the shorted quarter-wave patch.  A shorted patch has ONE radiating edge,
    so its E-plane pattern is almost hemispherical (paper Fig.3a).  Model: dB(theta) = -taper90 * (theta/90deg)^2.
    This width is what makes +-55..60 deg scanning possible; a normal half-wave patch (cos^1.2) only reaches ~45 deg.
    Replace by the HFSS embedded pattern for verification (see load_pattern)."""
    t = ELEM_TAPER_DB_AT_90 if taper90 is None else taper90
    return 10 ** (-t * (np.degrees(th) / 90.0) ** 2 / 20)

def load_pattern(csv_path):
    """HFSS/CST E-plane cut export: columns theta_deg, |E| (linear, or dB if header contains 'dB'). Returns callable."""
    import numpy as _np
    d = _np.loadtxt(csv_path, delimiter=",", skiprows=1); th, v = d[:, 0], d[:, 1]
    if "db" in open(csv_path).readline().lower(): v = 10 ** (v / 20)
    return lambda t: _np.interp(_np.degrees(t), th, v)

def af(phases_deg, f, th=TH, amp=None, efn=None, x=None):
    k = 2 * np.pi * f / C0
    x = (np.arange(N) - (N - 1) / 2) * D if x is None else x
    a = (np.ones(N) if amp is None else amp) * np.exp(1j * np.radians(phases_deg))
    E = (np.exp(1j * k * np.outer(np.sin(th), x)) @ a)
    return E * (elem(th) if efn is None else efn(th))

def metrics(E, th=TH, excl=None):
    """peak angle, SLL (dB, highest local max outside the main lobe), main-lobe region by first nulls."""
    U = np.abs(E) ** 2; U = U / U.max(); dB = 10 * np.log10(U + 1e-12)
    ip = np.argmax(U)
    l = ip
    while l > 0 and U[l - 1] < U[l]: l -= 1
    r = ip
    while r < len(U) - 1 and U[r + 1] < U[r]: r += 1
    side = np.r_[dB[:l], dB[r + 1:]]
    sll = side.max() if side.size else -99
    return np.degrees(th[ip]), sll, dB

def directivity_gain_dB(E, th=TH):
    """2-D (E-plane) proxy normalised to the uniform broadside case - used only for relative scan loss."""
    return 10 * np.log10(np.max(np.abs(E) ** 2))

def best_state(theta0, preload, f, S=-180.0, rule="max_gain_in_dir", sll_w=0.0):
    """Choose the 1-bit state for desired direction theta0.
    'quantize'        : classic nearest-phase rounding of the ideal progressive phase
    'max_gain_in_dir' : exhaustive over 32 states, maximise |E(theta0)| (optionally penalise SLL)"""
    k = 2 * np.pi * f / C0; x = (np.arange(N) - (N - 1) / 2) * D
    if rule == "quantize":
        ideal = -np.degrees(k * x * np.sin(np.radians(theta0)))
        b = (np.round(((ideal - preload) % 360) / 180) % 2).astype(int)
        return b
    i0 = np.argmin(np.abs(TH - np.radians(theta0)))
    best, bb = -1e9, None
    for b in STATES:
        E = af(preload + b * S, f)
        pk, sll, dB = metrics(E)
        score = dB[i0] + 20 * np.log10(np.abs(E).max()) - sll_w * max(sll + 5, 0) - 0.2 * abs(pk - theta0)
        if score > best: best, bb = score, b
    return bb

def scan_table(preload, f, angles=(0, 20, -20, 40, -40, 60, -60), S=-180.0, rule="max_gain_in_dir"):
    rows = []; ref = np.abs(af(np.zeros(N), f)).max() ** 2
    for t in angles:
        b = best_state(t, preload, f, S, rule)
        E = af(preload + b * S, f)
        pk, sll, dB = metrics(E)
        loss = 10 * np.log10(np.abs(E).max() ** 2 / ref)
        rows.append(dict(target=t, code="".join(map(str, b)), peak=pk, sll=sll, rel_gain=loss, dB=dB))
    return rows

def pso_preload(f, angles=(0, 20, -20, 40, -40, 60, -60), n_part=24, n_it=50, seed=3):
    """Re-derive the fixed preload with PSO: objective = sum over beams of [pointing error + SLL above -5 dB + gain drop].
    Element 4 phase fixed at 0 (paper normalisation)."""
    rng = np.random.default_rng(seed)
    def cost(p):
        pre = np.r_[p[:3], 0.0, p[3]]
        c = 0
        for r in scan_table(pre, f, angles):
            c += 0.3 * abs(r["peak"] - r["target"]) + 2.0 * max(r["sll"] + 5, 0) - 0.5 * r["rel_gain"]
        return c
    X = rng.uniform(-180, 180, (n_part, 4)); V = np.zeros_like(X)
    P = X.copy(); Pc = np.array([cost(x) for x in X]); g = P[Pc.argmin()].copy(); gc = Pc.min()
    for it in range(n_it):
        w = 0.9 - 0.5 * it / n_it
        V = w * V + 1.5 * rng.random(X.shape) * (P - X) + 1.5 * rng.random(X.shape) * (g - X)
        X = ((X + V + 180) % 360) - 180
        c = np.array([cost(x) for x in X]); m = c < Pc; P[m] = X[m]; Pc[m] = c[m]
        if Pc.min() < gc: gc = Pc.min(); g = P[Pc.argmin()].copy()
    return np.r_[g[:3], 0.0, g[3]], gc

def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(OUT, exist_ok=True)
    f0 = 26.5e9; lam = C0 / f0
    rep = ["D = 4.5 mm = %.3f lambda0 at 26.5 GHz (paper quotes 0.375 lambda0, which is exact at %.1f GHz)" % (D / lam, 0.375 * C0 / D / 1e9)]
    paper = {0: (-1, -8.25), 20: (19, -5.23), -20: (-21, -5.12), 40: (38, -7.43), -40: (-41, -6.72), 60: (56, -4.69), -60: (-54, -4.97)}
    # element-width sensitivity (why the shorted patch matters)
    global ELEM_TAPER_DB_AT_90
    for tp in (2.0, 4.0, 8.0, 12.0):
        ELEM_TAPER_DB_AT_90 = tp
        rr = scan_table(PRELOAD_PAPER, f0, angles=(60, -60))
        rep.append("element taper %4.1f dB at 90 deg -> +60 beam at %+.1f deg (SLL %.1f), -60 beam at %+.1f deg (SLL %.1f)"
                   % (tp, rr[0]["peak"], rr[0]["sll"], rr[1]["peak"], rr[1]["sll"]))
    ELEM_TAPER_DB_AT_90 = 4.0
    cases = [("No preload, nearest-phase quantisation", np.zeros(N), "quantize"),
             ("No preload, best of 32 states", np.zeros(N), "max_gain_in_dir"),
             ("Paper preload (55.78,-5.79,-73.37,0,-111.72), best of 32", PRELOAD_PAPER, "max_gain_in_dir")]
    fig, ax = plt.subplots(1, 3, figsize=(18, 4.6), sharey=True)
    tab = []
    for a_, (name, pre, rule) in zip(ax, cases):
        rows = scan_table(pre, f0, rule=rule)
        for r in rows:
            a_.plot(np.degrees(TH), r["dB"], label="%+d (%s)" % (r["target"], r["code"]))
            tab.append([name, r["target"], r["code"], round(r["peak"], 1), round(r["sll"], 2), round(r["rel_gain"], 2),
                        paper[r["target"]][0] if "Paper" in name else "", paper[r["target"]][1] if "Paper" in name else ""])
        a_.set_title(name, fontsize=9); a_.set_ylim(-30, 1); a_.set_xlim(-90, 90); a_.grid(alpha=.3); a_.legend(fontsize=7, ncol=2)
        a_.axhline(-5, color="r", lw=0.8, ls="--"); a_.set_xlabel("theta in xoz plane (deg)")
    ax[0].set_ylabel("normalised (dB)"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "scan_patterns_26p5GHz.png"), dpi=110); plt.close(fig)
    with open(os.path.join(OUT, "scan_table_26p5GHz.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["case", "target_deg", "state_code_e1..e5 (1=SW2 ON=-180)", "peak_deg", "SLL_dB", "gain_vs_uniform_broadside_dB", "paper_peak_deg", "paper_SLL_dB"]); w.writerows(tab)
    for r in [t for t in tab if "Paper" in t[0]]:
        rep.append("paper preload, target %+3d: code %s peak %+6.1f deg (paper %+d), SLL %6.2f dB (paper %.2f), rel gain %5.2f dB"
                   % (r[1], r[2], r[3], r[6], r[4], r[7], r[5]))
    # frequency behaviour of the paper codes
    codes = {r["target"]: np.array(list(map(int, r["code"]))) for r in scan_table(PRELOAD_PAPER, f0)}
    fr = []
    for f in (25e9, 26.5e9, 28e9, 29e9):
        for t, b in codes.items():
            pk, sll, _ = metrics(af(PRELOAD_PAPER + b * (-180), f))
            fr.append([f / 1e9, t, "".join(map(str, b)), round(pk, 1), round(sll, 2)])
    with open(os.path.join(OUT, "beam_vs_frequency_fixed_codes.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["f_GHz", "target", "code", "peak_deg", "SLL_dB"]); w.writerows(fr)
    sq = [r for r in fr if r[1] == 60]
    rep.append("Beam squint of the +60 code over 25-29 GHz: " + ", ".join("%.1f GHz -> %.1f deg" % (r[0], r[3]) for r in sq))
    # sensitivity: state-2 phase -176/-178 (paper Fig.4) and preload errors from line etching
    rng = np.random.default_rng(7); res = []
    for sig in (0, 5, 10, 15):
        worst = []
        for _ in range(100):
            pre = PRELOAD_PAPER + rng.normal(0, sig, N); S = -177 + rng.normal(0, 2, N)
            for t, b in codes.items():
                pk, sll, _ = metrics(af(pre + b * S, f0)); worst.append(sll)
        res.append([sig, round(np.percentile(worst, 50), 2), round(np.percentile(worst, 90), 2)])
    with open(os.path.join(OUT, "SLL_vs_preload_error.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["preload_phase_error_rms_deg", "median_SLL_dB_all_beams", "p90_SLL_dB"]); w.writerows(res)
    rep.append("SLL (90th pct, all beams) vs preload error rms: " + ", ".join("%d deg -> %.1f dB" % (r[0], r[2]) for r in res))
    # own PSO re-derivation
    pre_pso, c = pso_preload(f0)
    rows = scan_table(pre_pso, f0)
    rep.append("Own PSO preload (deg, e4 = 0): " + ", ".join("%.1f" % p for p in pre_pso) + " | worst SLL %.2f dB, max pointing error %.1f deg"
               % (max(r["sll"] for r in rows), max(abs(r["peak"] - r["target"]) for r in rows)))
    with open(os.path.join(OUT, "preload_PSO_own.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["element", "preload_deg_paper", "preload_deg_own_PSO"]);
        for n in range(N): w.writerow([n + 1, PRELOAD_PAPER[n], round(pre_pso[n], 2)])
    with open(os.path.join(OUT, "study_report.txt"), "w") as fh: fh.write("\n".join(rep))
    print("\n".join(rep))

if __name__ == "__main__":
    main()
