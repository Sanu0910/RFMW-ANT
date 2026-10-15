"""Array / system models for the modular null-steering and CP antenna (paper Sec. II and IV).

Element model: endfire printed dipole radiating toward +z (board +y), E-field parallel to the board's x axis
(dipole arms).  Default pattern g(theta) = ((1+cos theta)/2)^n gives a broad beam (~5 dBi class).
Replace with HFSS embedded element patterns via load_element_csv() for verification-grade results.

Excitation of unit i:  a_i = s_i * A_i * exp(j*phi_i)
   s_i  = +1 for type A, -1 for the mirrored type B (the paper's built-in 180 deg),
   phi_i = phase-shifter setting (relative, 0..range(f) deg, from rtps_model).
Run:  python array_models.py   -> figures + LUT CSVs in ./results"""
import os, math, csv
import numpy as np
import rtps_model as rm

C0 = 299792458.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ------------------------------------------------------------------ geometry of the three systems
D = 25e-3   # element spacing = board width = lambda0/2 at 6 GHz
def system(name, cp_types=("A", "B", "B", "A")):
    """Returns list of dicts: position r (m), polarisation unit vector p (world), type sign s."""
    if name == "1D":
        return [dict(u=1, r=(-D / 2, 0, 0), p=(1, 0, 0), s=+1), dict(u=2, r=(D / 2, 0, 0), p=(-1, 0, 0), s=+1)]
        # NOTE: type B is the mirror image of A: its arm/E-vector points along -x for the same feed; the
        # mirror is captured by p=(-1,0,0) with s=+1 (equivalently p=(+1,0,0), s=-1).
    if name == "2D":
        out = []
        for u, (x, y), t in ((1, (D / 2, D / 2), "A"), (2, (-D / 2, D / 2), "B"), (3, (D / 2, -D / 2), "B"), (4, (-D / 2, -D / 2), "A")):
            out.append(dict(u=u, r=(x, y, 0), p=(1, 0, 0), s=+1 if t == "A" else -1))
        return out
    if name == "CP":
        out = []
        for (u, az), t in zip(((1, 45), (2, 135), (3, 315), (4, 225)), cp_types):
            c, s_ = math.cos(math.radians(az)), math.sin(math.radians(az))
            # wing board: x axis points radially outward; phase centre ~12.5 mm from the axis
            out.append(dict(u=u, r=(12.5e-3 * c, 12.5e-3 * s_, 0), p=(c, s_, 0), s=+1 if t == "A" else -1))
        return out
    raise ValueError(name)

# ------------------------------------------------------------------ far field
def grid(dth=1.0, dph=2.0):
    th = np.radians(np.arange(0, 180 + 1e-9, dth)); ph = np.radians(np.arange(0, 360, dph))
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    return TH, PH

def unit_vectors(TH, PH):
    st, ct, sp, cp = np.sin(TH), np.cos(TH), np.sin(PH), np.cos(PH)
    rhat = np.stack([st * cp, st * sp, ct]); that = np.stack([ct * cp, ct * sp, -st]); phat = np.stack([-sp, cp, np.zeros_like(TH)])
    return rhat, that, phat

def element_field(TH, PH, p, n=1.5):
    """Far field (theta, phi components) of one element with polarisation p, endfire toward +z."""
    rhat, that, phat = unit_vectors(TH, PH)
    g = ((1 + np.cos(TH)) / 2) ** n
    pv = np.array(p, float).reshape(3, 1, 1)
    return g * np.sum(pv * that, 0), g * np.sum(pv * phat, 0)

def array_field(elems, phases_deg, f, TH, PH, amp=None, elem_fn=None):
    k = 2 * np.pi * f / C0; rhat, _, _ = unit_vectors(TH, PH)
    Et = np.zeros(TH.shape, complex); Ep = np.zeros_like(Et)
    for i, e in enumerate(elems):
        a = e["s"] * (1 if amp is None else amp[i]) * np.exp(1j * np.radians(phases_deg[i]))
        r = np.array(e["r"]).reshape(3, 1, 1)
        af = np.exp(1j * k * np.sum(rhat * r, 0))
        if elem_fn is None: et, ep = element_field(TH, PH, e["p"])
        elif callable(elem_fn): et, ep = elem_fn(TH, PH, e["p"])
        else: et, ep = elem_fn[i]            # per-element (Et, Ep) arrays, e.g. HFSS embedded patterns
        Et += a * af * et; Ep += a * af * ep
    return Et, Ep

def directivity_dBi(Et, Ep, TH, dth, dph):
    U = np.abs(Et) ** 2 + np.abs(Ep) ** 2
    P = np.sum(U * np.sin(TH)) * np.radians(dth) * np.radians(dph)
    return 10 * np.log10(4 * np.pi * U / P)

def load_element_csv(path, TH, PH):
    """HFSS embedded element pattern of ONE unit (all other ports terminated, varactors at the bias of interest),
    exported as CSV with columns Theta_deg, Phi_deg, Re_rETheta, Im_rETheta, Re_rEPhi, Im_rEPhi on a regular grid.
    Returns (Et, Ep) on (TH, PH) by nearest-neighbour lookup.  Use as elem_fn=[(Et1,Ep1),(Et2,Ep2),...] in array_field.
    With embedded patterns the element position phase is already inside the data -> set e["r"]=(0,0,0)."""
    import numpy as np
    D_ = np.loadtxt(path, delimiter=",", skiprows=1)
    th = np.round(D_[:, 0], 3); ph = np.round(D_[:, 1] % 360, 3)
    key = {(a, b): i for i, (a, b) in enumerate(zip(th, ph))}
    Et = np.zeros(TH.shape, complex); Ep = np.zeros(TH.shape, complex)
    for idx in np.ndindex(TH.shape):
        i = key[(round(float(np.degrees(TH[idx])), 3), round(float(np.degrees(PH[idx])) % 360, 3))]
        Et[idx] = D_[i, 2] + 1j * D_[i, 3]; Ep[idx] = D_[i, 4] + 1j * D_[i, 5]
    return Et, Ep

# ------------------------------------------------------------------ 1-D null steering
def phases_1d(theta_null_deg, f, ref_mid=None):
    """Phase-shifter settings (deg) for U1 (x=-d/2) and U2 (x=+d/2) putting the null at theta_null in the xz plane.
    The antiphase pair nulls where k d sin(th) = phi1 - phi2 (U1 at x=-d/2, U2 at x=+d/2, e^{jwt}).
    Both shifters are used symmetrically about mid-range: phi1 = mid + dphi/2, phi2 = mid - dphi/2."""
    k = 2 * np.pi * f / C0
    dphi = np.degrees(k * D * np.sin(np.radians(theta_null_deg)))
    mid = ref_mid if ref_mid is not None else 0.0
    return np.array([mid + dphi / 2, mid - dphi / 2]), dphi

def max_null_angle_1d(f, ps_range_deg):
    k = 2 * np.pi * f / C0; x = np.radians(ps_range_deg) / (k * D)
    return np.degrees(np.arcsin(min(1.0, x)))

def cut(Et, Ep, TH, PH, phi_deg):
    """theta from -180..180 cut in plane phi (dB, normalised to the cut max)."""
    ph = np.degrees(PH[0]); i1 = np.argmin(np.abs(ph - phi_deg % 360)); i2 = np.argmin(np.abs(ph - (phi_deg + 180) % 360))
    th = np.degrees(TH[:, 0]); U = np.abs(Et) ** 2 + np.abs(Ep) ** 2
    t = np.r_[-th[::-1], th[1:]]; u = np.r_[U[::-1, i2], U[1:, i1]]
    return t, 10 * np.log10(u / u.max() + 1e-12)

def null_depth_db(Et, Ep, TH, PH, theta_null_deg, phi_deg=0, window=3):
    """Depth of the null near theta_null (dB below the peak of the same cut)."""
    t, u = cut(Et, Ep, TH, PH, phi_deg)
    m = np.abs(t - theta_null_deg) <= window
    return -u[m].min(), t[m][np.argmin(u[m])]

# ------------------------------------------------------------------ 2-D null steering
def phases_2d(u0, v0, f):
    """Null planes at u = u0 (x pairs) and v = v0 (y pairs); phi_i = +-ax +- ay with ax = k d u0 / 2."""
    k = 2 * np.pi * f / C0
    ax = np.degrees(k * D * u0 / 2); ay = np.degrees(k * D * v0 / 2)
    sx = {1: +1, 2: -1, 3: +1, 4: -1}; sy = {1: +1, 2: +1, 3: -1, 4: -1}
    return np.array([-(sx[u] * ax + sy[u] * ay) for u in (1, 2, 3, 4)])

# ------------------------------------------------------------------ CP
def axial_ratio_db(Et, Ep):
    """AR at every direction from the (theta, phi) complex components."""
    El = (Et + 1j * Ep) / np.sqrt(2); Er = (Et - 1j * Ep) / np.sqrt(2)       # LHCP/RHCP (IEEE, e^{jwt}, outgoing)
    a, b = np.abs(El), np.abs(Er)
    with np.errstate(divide='ignore', invalid='ignore'):
        ar = 20 * np.log10(np.maximum(a + b, 1e-300) / np.maximum(np.abs(a - b), 1e-12))
    return ar, El, Er

# ------------------------------------------------------------------ Monte-Carlo: null depth vs imbalance
def mc_null_depth(sig_amp_db, sig_ph_deg, f=6e9, theta_null=25.0, n=400, seed=1):
    """Returns (rejection at the intended angle [dB below peak], deepest-null depth [dB], null pointing error [deg])."""
    rng = np.random.default_rng(seed); TH, PH = grid(0.25, 180.0)
    el = system("1D"); ph0, _ = phases_1d(theta_null, f)
    rej, deep, perr = [], [], []
    for _ in range(n):
        amp = 10 ** (rng.normal(0, sig_amp_db, 2) / 20); ph = ph0 + rng.normal(0, sig_ph_deg, 2)
        Et, Ep = array_field(el, ph, f, TH, PH, amp)
        t, u = cut(Et, Ep, TH, PH, 0)
        rej.append(-u[np.argmin(np.abs(t - theta_null))])
        d_, tmin = null_depth_db(Et, Ep, TH, PH, theta_null, 0, 15)
        deep.append(d_); perr.append(tmin - theta_null)
    return np.array(rej), np.array(deep), np.array(perr)

# ------------------------------------------------------------------ main study
def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(OUT, exist_ok=True)
    p = rm.finalize(rm.default_params()); p["Lp"] = 0.35e-9          # case B of rtps_model (paper-like range)
    TH, PH = grid(1.0, 2.0)
    rep = []
    # ---- steering limits vs frequency
    rng_f = {f: rm.phase_curve(f, p)[1].max() for f in (5e9, 6e9, 7e9)}
    for f, r in rng_f.items():
        rep.append("1-D: PS range %.0f deg at %.0f GHz -> max null angle +-%.1f deg (both shifters used)"
                   % (r, f / 1e9, max_null_angle_1d(f, r)))
    # ---- null squint for a FIXED bias set for 40 deg at 6 GHz
    ph40, dphi40 = phases_1d(40, 6e9)
    for f in (5e9, 6e9, 7e9):
        k = 2 * np.pi * f / C0; th = np.degrees(np.arcsin(np.radians(dphi40) / (k * D)))
        rep.append("Fixed bias for 40 deg @6 GHz -> null at %.1f deg @ %.0f GHz (phase shifter is not true-time-delay)" % (th, f / 1e9))
    # ---- 1-D patterns (bias re-tuned per frequency) + 6 GHz bias LUT
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    lut = []
    el = system("1D")
    for j, f in enumerate((5e9, 6e9, 7e9)):
        Cs, ph = rm.phase_curve(f, p); mid = ph.max() / 2
        for tn in (-40, -25, 0, 25, 40):
            phs, dphi = phases_1d(tn, f, ref_mid=mid)
            ok = (phs.min() >= 0) and (phs.max() <= ph.max())
            Et, Ep = array_field(el, phs, f, TH, PH)
            t, u = cut(Et, Ep, TH, PH, 0)
            depth, tpk = null_depth_db(Et, Ep, TH, PH, tn, 0, 3)
            ax[j].plot(t, u, label="null %+d" % tn)
            if ok:
                c1, v1 = rm.phase_to_bias(f, phs[0], p); c2, v2 = rm.phase_to_bias(f, phs[1], p)
                lut.append([f / 1e9, tn, round(phs[0], 2), round(phs[1], 2), round(float(c1) * 1e12, 4), round(float(c2) * 1e12, 4), round(float(v1), 3), round(float(v2), 3)])
            else:
                lut.append([f / 1e9, tn, round(phs[0], 2), round(phs[1], 2), "OUT OF RANGE", "", "", ""])
        ax[j].set_xlim(-90, 90); ax[j].set_ylim(-40, 1); ax[j].grid(alpha=.3); ax[j].legend(fontsize=7)
        ax[j].set_title("1-D xz-plane cut, %.0f GHz (bias re-tuned)" % (f / 1e9), fontsize=9); ax[j].set_xlabel("theta (deg)")
    ax[0].set_ylabel("normalised (dB)"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "1D_null_steering_cuts.png"), dpi=110); plt.close(fig)
    with open(os.path.join(OUT, "LUT_1D_null_angle_to_bias.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["f_GHz", "null_deg", "phi_U1_deg", "phi_U2_deg", "C_U1_pF", "C_U2_pF", "V_U1", "V_U2"]); w.writerows(lut)
    # ---- 2-D uv maps
    fig, ax = plt.subplots(1, 4, figsize=(17, 4.3))
    TH2, PH2 = grid(1.0, 2.0); el2 = system("2D")
    rng6 = rng_f[6e9]
    for a_, (u0, v0, ttl) in zip(ax, ((0, 0, "nulls at u=0, v=0"), (math.sin(math.radians(40)), 0, "x-null steered to 40 deg"),
                                      (0, -math.sin(math.radians(40)), "y-null steered to -40 deg"), (0.40, 0.40, "both steered ~23.6 deg"))):
        phs = phases_2d(u0, v0, 6e9); span = phs.max() - phs.min()
        Et, Ep = array_field(el2, phs, 6e9, TH2, PH2)
        U = np.abs(Et) ** 2 + np.abs(Ep) ** 2; U = 10 * np.log10(U / U.max() + 1e-9)
        up = np.sin(TH2) * np.cos(PH2); vp = np.sin(TH2) * np.sin(PH2); m = TH2 <= np.pi / 2
        sc = a_.scatter(up[m], vp[m], c=np.clip(U[m], -30, 0), s=3, cmap="viridis")
        a_.set_aspect("equal"); a_.set_title("%s\nphase span %.0f deg (PS range %.0f) %s" % (ttl, span, rng6, "OK" if span <= rng6 else "EXCEEDS"), fontsize=8)
        a_.set_xlabel("u"); a_.set_ylabel("v")
    fig.colorbar(sc, ax=ax, shrink=0.8, label="dB"); fig.savefig(os.path.join(OUT, "2D_null_steering_uv.png"), dpi=110); plt.close(fig)
    rep.append("2-D: each element phase = +-ax +-ay -> span 2(|ax|+|ay|) must fit the PS range: |u0|+|v0| <= %.3f at 6 GHz"
               % (np.radians(rng6) / (2 * np.pi * 6e9 / C0 * D)))
    # ---- CP: which wing-type assignment gives co-phased opposite wings, AR vs frequency
    TH3, PH3 = grid(1.0, 2.0)
    for types in (("A", "B", "B", "A"), ("A", "A", "B", "B")):
        elc = system("CP", types)
        for sense, phs in (("RHCP-try (U1,U4 +90)", [90, 0, 0, 90]), ("LHCP-try (U2,U3 +90)", [0, 90, 90, 0])):
            res = []
            for f in (5e9, 6e9, 7e9):
                Et, Ep = array_field(elc, np.array(phs, float), f, TH3, PH3)
                AR, El, Er = axial_ratio_db(Et, Ep)
                g_bs = 10 * np.log10((np.abs(Et[0, 0]) ** 2 + np.abs(Ep[0, 0]) ** 2) / np.max(np.abs(Et) ** 2 + np.abs(Ep) ** 2))
                res.append("%.0fGHz AR(bs)=%.2f dB, rel. broadside level %.1f dB, %s" % (f / 1e9, AR[0, 0], g_bs, "LHCP" if abs(El[0, 0]) > abs(Er[0, 0]) else "RHCP"))
            rep.append("CP types U1..U4=%s, %s: %s" % ("".join(types), sense, " | ".join(res)))
    # ---- CP axial ratio vs quadrature error / amplitude imbalance (co-phased assignment)
    rows_ar = []
    elc = system("CP", ("A", "A", "B", "B"))
    for da in (0.0, 0.5, 1.0, 2.0):
        for dp in (0, 5, 10, 15, 20):
            amp = [10 ** (da / 20), 1, 1, 10 ** (da / 20)]
            Et, Ep = array_field(elc, np.array([90 + dp, 0, 0, 90 + dp], float), 6e9, TH3[:1, :1], PH3[:1, :1], amp)
            rows_ar.append([da, dp, round(float(axial_ratio_db(Et, Ep)[0][0, 0]), 2)])
    with open(os.path.join(OUT, "CP_axial_ratio_vs_imbalance.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["amp_imbalance_dB", "quadrature_error_deg", "AR_broadside_dB"]); w.writerows(rows_ar)
    rep.append("CP AR (broadside) for 10 deg quadrature error: %.2f dB; for 1 dB amplitude imbalance + 10 deg: %.2f dB (paper: AR < 2.3 dB)"
               % ([r[2] for r in rows_ar if r[0] == 0 and r[1] == 10][0], [r[2] for r in rows_ar if r[0] == 1.0 and r[1] == 10][0]))
    # ---- Monte Carlo: rejection at the interferer angle, null fill and null pointing error
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    rows = []; sps = (0.5, 1, 2, 4, 8)
    for sa in (0.0, 0.25, 0.5, 1.0):
        r10, pe = [], []
        for sp in sps:
            rj, dp, pr = mc_null_depth(sa, sp, n=200)
            r10.append(np.percentile(rj, 10)); pe.append(np.percentile(np.abs(pr), 90))
            rows.append([sa, sp, round(np.median(rj), 1), round(np.percentile(rj, 10), 1), round(np.median(dp), 1), round(np.percentile(np.abs(pr), 90), 2)])
        ax[0].plot(sps, r10, "o-", label="amp sigma %.2f dB" % sa); ax[1].plot(sps, pe, "o-", label="amp sigma %.2f dB" % sa)
    ax[0].axhline(15, color="r", ls="--", lw=1); ax[0].text(0.55, 16, "paper: >15 dB (1-D)", color="r", fontsize=8)
    for a_ in ax: a_.set_xscale("log"); a_.set_xlabel("phase error sigma per channel (deg)"); a_.grid(alpha=.3, which="both"); a_.legend(fontsize=8)
    ax[0].set_ylabel("rejection at intended angle, 10th pct (dB)"); ax[1].set_ylabel("null pointing error, 90th pct (deg)")
    ax[0].set_title("1-D, interferer at 25 deg, 6 GHz", fontsize=9); ax[1].set_title("phase error steers the null; amplitude error fills it", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "MC_null_depth_vs_errors.png"), dpi=110); plt.close(fig)
    with open(os.path.join(OUT, "MC_null_depth.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["amp_sigma_dB", "phase_sigma_deg", "median_rejection_at_angle_dB", "p10_rejection_dB", "median_deepest_null_dB", "p90_pointing_error_deg"]); w.writerows(rows)
    sel = [r for r in rows if r[0] == 0.5 and r[1] == 4][0]
    rep.append("Monte Carlo (0.5 dB / 4 deg rms per channel): rejection at 25 deg median %.1f dB, 10th pct %.1f dB; null pointing error 90th pct %.1f deg"
               % (sel[2], sel[3], sel[5]))
    with open(os.path.join(OUT, "system_study_report.txt"), "w") as fh: fh.write("\n".join(rep))
    print("\n".join(rep))

if __name__ == "__main__":
    main()
