"""NFMS study: checks every equation and number of the paper and simulates the steered system with the cells chosen
by build_nfms.py.  python nfms_study.py -> results/ (PNG, CSV, study_report.txt)
Models (all closed form, no full-wave solver):
  * eq. (1), (2), (6) forward and the corrected inverse of eqs. (3)-(4)
  * radial-line TM0 dispersion of the 3 mm air + 1.6 mm TLY-5 waveguide (transverse resonance, exact)
  * RLSA: 1920 slot magnetic dipoles, outward travelling wave, 6 dB taper -> broadside directivity, AR, pattern
  * system: aperture field (Fig. 12(a) near-field phase, 6 dB taper) x HM I cell S21 x rotated HM II cell S21,
    radiated by FFT (Huygens obliquity) -> beam direction, gain, sidelobes for the six Table I cases."""
import os, math, csv
import numpy as np
from scipy.optimize import brentq
import cells as CL
import nfmsgeom as G

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
K0 = 2 * math.pi / G.LAM0
TABLE1 = [  # psi1, psi2, phi_p, theta_p, phi_m, theta_m  (paper Table I)
    (0, 30, 15, 40.2, 15, 40.6), (0, 60, 30, 35.3, 30, 35.7), (0, 90, 45, 28.2, 45, 28.2),
    (0, 120, 60, 19.5, 60, 20.0), (0, 150, 75, 9.9, 75, 10.0), (0, 180, None, 0.0, None, 0.0)]
TABLE2 = {30: (27.1, 1.1), 60: (28.2, 1.05), 90: (29.6, 0.94), 120: (30.0, 0.94), 150: (30.0, 0.94), 180: (31.5, 0.89)}

# ---------------- equations ----------------
def beam(p1, p2, psi1, psi2, k=K0):
    s = math.sqrt(max(p1 * p1 + p2 * p2 + 2 * p1 * p2 * math.cos(math.radians(psi1 - psi2)), 0.0)) / k
    th = math.degrees(math.asin(min(s, 1.0)))
    ph = math.degrees(math.atan2(p1 * math.sin(math.radians(psi1)) + p2 * math.sin(math.radians(psi2)),
                                 p1 * math.cos(math.radians(psi1)) + p2 * math.cos(math.radians(psi2))))
    return th, ph

def inverse_paper(theta, phi, p, k=K0):
    x = (k * math.sin(math.radians(theta))) ** 2 / p ** 2 - 1
    if abs(x) > 1: return None
    dl = math.degrees(math.acos(x)) / 2; return phi + dl, phi - dl

def inverse_correct(theta, phi, p, k=K0):
    x = (k * math.sin(math.radians(theta))) ** 2 / (2 * p ** 2) - 1
    if abs(x) > 1: return None
    dl = math.degrees(math.acos(x)) / 2; return phi + dl, phi - dl

# ---------------- radial waveguide dispersion ----------------
def tm0_eps_eff(f=G.F0, h_air=G.R["h_air"], h_d=G.R["h_diel"], er=G.R["er"]):
    """Exact TM0 (E normal to plates) of PEC | air h_air | dielectric h_d | PEC.  Returns (beta/k0)^2."""
    k0 = 2 * math.pi * f / CL.C0
    def fn(n2):
        b2 = n2 * k0 * k0
        g1 = math.sqrt(max(b2 - k0 * k0, 1e-30))          # air: evanescent (beta > k0)
        kd = math.sqrt(max(er * k0 * k0 - b2, 1e-30))      # dielectric: propagating
        # TM transverse resonance: (g1/1) tanh(g1 h1) = (kd/er) tan(kd h2)
        return g1 * math.tanh(g1 * h_air) - (kd / er) * math.tan(kd * h_d)
    return brentq(fn, 1.0 + 1e-9, er - 1e-9)

# ---------------- RLSA slot array ----------------
def taper(rho, R=G.R["D_ap"] / 2, edge_db=6.0):
    return 10 ** (-edge_db / 20 * (rho / R) ** 2)

def rlsa_far_field(pairs, lam_g_true, f=G.F0, th=np.radians(np.linspace(-50, 50, 1001)), cut_phi=0.0):
    """Magnetic dipoles along each slot, excited by a radial wave exp(-j 2pi rho / lam_g_true) with amplitude taper and
    the projection of the radial surface current on the slot normal.  Returns E_RHCP, E_LHCP along the cut."""
    k = 2 * math.pi * f / CL.C0
    pos, mom = [], []
    for p in pairs:
        for c, ang in ((p["ca"], p["ang_a"]), (p["cb"], p["ang_b"])):
            rho = math.hypot(*c); ur = np.array(c) / rho
            t = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); n = np.array([-t[1], t[0]])
            a = taper(rho) * np.dot(ur, n) * np.exp(-1j * 2 * math.pi * rho / lam_g_true)
            pos.append(c); mom.append(a * t)
    pos = np.array(pos); mom = np.array(mom)
    cp = math.cos(cut_phi); sp = math.sin(cut_phi)
    ER, EL = [], []
    for t_ in th:
        u = math.sin(t_) * cp; v = math.sin(t_) * sp
        ph = np.exp(1j * k * (pos[:, 0] * u + pos[:, 1] * v))
        Mx = np.sum(mom[:, 0] * ph); My = np.sum(mom[:, 1] * ph)
        # far E of a z-normal magnetic current sheet ~ z_hat x M projected (small-angle form adequate inside +-50 deg)
        Ex, Ey = -My, Mx
        ER.append((Ex + 1j * Ey) / math.sqrt(2)); EL.append((Ex - 1j * Ey) / math.sqrt(2))
    return np.degrees(th), np.array(ER), np.array(EL)

# ---------------- steered system ----------------
def cell_lookup(rows, N=G.H["N"]):
    T = np.zeros((N, N), complex)
    for r in rows: T[r["j"], r["i"]] = 10 ** (r["mag_db"] / 20) * np.exp(1j * math.radians(r["phase"]))
    return T

def hm_screen(T, X, Y, psi_deg):
    """Transmission of an HM rotated CCW by psi, sampled at world points X, Y (nearest cell)."""
    c, s = math.cos(math.radians(psi_deg)), math.sin(math.radians(psi_deg))
    xl = c * X + s * Y; yl = -s * X + c * Y
    i = np.rint((xl - G.H["x0"]) / G.H["d"]).astype(int); j = np.rint((yl - G.H["x0"]) / G.H["d"]).astype(int)
    ok = (i >= 0) & (i < G.H["N"]) & (j >= 0) & (j < G.H["N"])
    out = np.zeros(X.shape, complex); out[ok] = T[j[ok], i[ok]]
    return out

def rlsa_aperture(X, Y):
    rho = np.hypot(X, Y)
    rr = np.array(G.ring_radii()[::-1]); ph = np.array(G.FIG12A_PHASE[::-1], float)
    phase = np.interp(rho, rr, np.degrees(np.unwrap(np.radians(ph))))
    E = taper(rho) * np.exp(1j * np.radians(phase)); E[rho > G.R["D_ap"] / 2] = 0
    return E

def steer(T1, T2, psi1, psi2, dx=2.5, nfft=4096, f=G.F0):
    lam = CL.C0 / f
    n = int(round(2 * 180 / dx)) + 1; ax = (np.arange(n) - (n - 1) / 2) * dx
    X, Y = np.meshgrid(ax, ax)
    E0 = rlsa_aperture(X, Y)
    E = E0 * hm_screen(T1, X, Y, psi1) * hm_screen(T2, X, Y, psi2)
    F = np.fft.fftshift(np.fft.fft2(E, (nfft, nfft)))
    fr = np.fft.fftshift(np.fft.fftfreq(nfft, dx)) * lam           # direction cosines u (= -fx * lam for exp(-j) kernel)
    U, V = np.meshgrid(-fr, -fr)
    vis = U ** 2 + V ** 2 < 1
    cth = np.sqrt(np.clip(1 - U ** 2 - V ** 2, 0, 1))
    P = np.abs(F) ** 2 * ((1 + cth) / 2) ** 2 * vis
    k = np.unravel_index(np.argmax(P), P.shape)
    u, v = U[k], V[k]
    th = math.degrees(math.asin(min(math.hypot(u, v), 1))); ph = math.degrees(math.atan2(v, u))
    dA = dx * dx
    G_ = 4 * math.pi / lam ** 2 * P[k] * dA * dA / (np.sum(np.abs(E0) ** 2) * dA)   # gain wrt power leaving the RLSA aperture
    Dd = 4 * math.pi / lam ** 2 * P[k] * dA * dA / (np.sum(np.abs(E) ** 2) * dA)
    # peak sidelobe: mask a 3-beamwidth disc around the peak
    bw = lam / (G.R["D_ap"]) * 1.2
    mask = (U - u) ** 2 + (V - v) ** 2 > (2.5 * bw) ** 2
    sll = 10 * math.log10(np.max(P * mask) / P[k])
    return dict(theta=th, phi=ph, gain_dbi=10 * math.log10(G_), dir_dbi=10 * math.log10(Dd), sll_db=sll, U=U, V=V, P=P)

def main():
    rep = []; W = rep.append
    W("NFMS RLSA + hybrid metasurfaces - model study (Afzal, Esselle, Koli, IEEE TAP 70(1) 2022)")
    W("lambda0 = %.3f mm at %.1f GHz" % (G.LAM0, G.F0))
    # --- eq (5) and the elevation limit
    W("\n[1] Gradient: eq. (5) dphi = 360 d sin(theta0)/lambda0 = %.2f deg (paper uses 60); theta0 for 60 deg exactly = %.2f deg" %
      (G.H["dphi_exact"], math.degrees(math.asin(60 / 360 * G.LAM0 / G.H["d"]))))
    p = K0 * math.sin(math.radians(G.H["theta0"]))
    W("    max elevation (psi1 = psi2): asin(2 sin 19.5) = %.2f deg; paper's 40.6 deg is the psi2 = 30 case, the psi2 = 0 state was not measured" % beam(p, p, 0, 0)[0])
    # --- Table I
    W("\n[2] Table I with eqs. (1), (6):  psi2 | phi_p paper/ours | theta_p paper/ours | theta_m measured")
    rows = []
    for a, b, php, thp, phm, thm in TABLE1:
        th, ph = beam(p, p, a, b)
        W("    %3d | %5s / %6.2f | %5.1f / %6.2f | %5.1f" % (b, php, ph if th > 1e-6 else float("nan"), thp, th, thm))
        rows.append([a, b, php, round(ph, 2), thp, round(th, 2), thm])
    # --- inverse
    W("\n[3] Inverse problem, eqs. (3)-(4).  The printed form acos[(k sin th)^2 / p1^2 - 1] is wrong by a factor 2:")
    for th in (0.0, 20.0, 35.3, 40.2):
        ip = inverse_paper(th, 30.0, p); ic = inverse_correct(th, 30.0, p)
        chk = beam(p, p, *ic) if ic else None
        W("    theta %5.1f phi 30: paper -> %s ; corrected acos[(k sin th)^2/(2 p^2) - 1] -> (%.2f, %.2f), forward check theta %.2f phi %.2f" %
          (th, "(%.2f, %.2f)" % ip if ip else "undefined (|arg|>1)", ic[0], ic[1], chk[0], chk[1] if chk[0] > 1e-6 else float("nan")))
    # --- radial line
    ne = tm0_eps_eff()
    W("\n[4] Radial waveguide (3 mm air + 1.6 mm TLY-5): eps_eff paper 1.41 (volume average) -> lambda_g %.2f mm (paper 12.56)" % G.R["lam_g"])
    W("    quasi-static series value %.3f -> lambda_g %.2f mm;  exact TM0 at 20 GHz: eps_eff %.3f -> lambda_g %.2f mm" % (G.R["eps_eff_series"], G.R["lam_g_series"], ne, G.LAM0 / math.sqrt(ne)))
    for f in (19.0, 19.5, 20.0, 20.5, 21.0):
        e = tm0_eps_eff(f); W("      f %.1f GHz: TM0 eps_eff %.3f lambda_g %.2f mm" % (f, e, CL.C0 / f / math.sqrt(e)))
    # --- RLSA pattern
    pairs = G.rlsa_pairs()
    W("\n[5] RLSA slot model (%d pairs on %.2f turns; outermost slot reaches r = %.1f mm vs the 172.5 mm aperture)" %
      (len(pairs), G.turns_of(pairs), max(max(np.hypot(*q["ca"]), np.hypot(*q["cb"])) + q["L"] / 2 for q in pairs)))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    out = []; ref = None
    for lg, lab in ((G.R["S_rho"], "radial wave lambda_g = S_rho = 12.6 mm (design)"), (G.LAM0 / math.sqrt(ne), "lambda_g = %.2f mm (exact TM0)" % (G.LAM0 / math.sqrt(ne))),
                    (G.R["lam_g_series"], "lambda_g = %.2f mm (series eps)" % G.R["lam_g_series"])):
        th, ER, EL = rlsa_far_field(pairs, lg)
        i0 = np.argmin(np.abs(th))
        if ref is None: ref = np.abs(ER[i0])
        pk = ref
        ar = (abs(ER[i0]) + abs(EL[i0])) / max(abs(abs(ER[i0]) - abs(EL[i0])), 1e-12)
        out.append((lab, 20 * np.log10(np.abs(ER[i0]) / pk + 1e-12), 20 * math.log10(ar), th[np.argmax(np.abs(ER))]))
        ax[0].plot(th, 20 * np.log10(np.abs(ER) / pk + 1e-9), label=lab)
        if lg == G.R["S_rho"]:
            ax[1].plot(th, 20 * np.log10(np.abs(ER) / pk + 1e-9), "k", label="RHCP (co-pol)"); ax[1].plot(th, 20 * np.log10(np.abs(EL) / pk + 1e-9), "r--", label="LHCP (cross-pol)")
    for lab, b0, arb, tpk in out: W("    %-44s broadside %6.2f dB rel. design case, peak at %5.1f deg, AR(broadside) %.2f dB" % (lab, b0, tpk, arb))
    for a_ in ax: a_.set_ylim(-40, 2); a_.set_xlabel("theta (deg), phi = 0 cut"); a_.grid(alpha=0.3); a_.legend(fontsize=7)
    ax[0].set_title("RLSA pattern vs true guided wavelength (spiral pitch fixed at 12.6 mm)", fontsize=9); ax[1].set_title("design case, co/cross-pol", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "rlsa_pattern_lambda_g_sensitivity.png"), dpi=150); plt.close(fig)
    ap = math.pi * (G.R["D_ap"] / 2) ** 2
    du = 10 * math.log10(4 * math.pi * ap / G.LAM0 ** 2)
    # taper efficiency of the 6 dB taper
    rr = np.linspace(0, G.R["D_ap"] / 2, 4000); A = taper(rr)
    eta_t = (np.trapezoid(A * rr, rr) ** 2) / (np.trapezoid(A * A * rr, rr) * (G.R["D_ap"] / 2) ** 2 / 2)
    W("    uniform-aperture directivity D = 4 pi A / lambda^2 = %.2f dBi; 6 dB taper efficiency %.3f -> %.2f dBi (paper simulated 34 dBi)" % (du, eta_t, du + 10 * math.log10(eta_t)))
    for g, f, Dap in ((30.9, 20.0, G.R["D_ap"]), (30.9, 20.0, 2 * G.H["R_cells"]), (31.5, 19.4, G.R["D_ap"])):
        lam = CL.C0 / f; W("    aperture efficiency of %.1f dBic at %.1f GHz over D = %.0f mm: %.1f %%" % (g, f, Dap, 100 * 10 ** (g / 10) / (4 * math.pi * math.pi * (Dap / 2) ** 2 / lam ** 2)))
    # --- cells
    W("\n[6] Cells (closed-form models, see cells.py):")
    W("    Type II r = 0: %.1f deg (paper -169); r = 3.4: %.1f deg (paper -134)" % (CL.phase_type2_unwrapped(0), CL.phase_type2_unwrapped(3.4)))
    for r in (1.4, 2.8): W("    Type II r = %.1f mm -> normalised %.1f deg" % (r, CL.phase_type2_unwrapped(r) - CL.phase_type2_unwrapped(3.4)))
    W("    -> the paper's 'hole diameter 2.8 mm' for the -13.8 deg edge cell fits a RADIUS of 2.8 mm (diameter 2.8 gives about -30 deg)")
    W("    Type I grid-capacitance factor fitted to the paper example (a 4, b 3.7 -> -171 deg): C_SCALE = %.3f" % CL.fit_c_scale())
    lib = CL.library(); u = CL.usable(lib); t1 = [c for c in u if c["type"] == 1]
    W("    usable (> -1 dB) Type I: %d cells, unwrapped %.1f .. %.1f deg (paper -169 .. -458);  largest uncovered arc %d deg (paper 35)" %
      (len(t1), max(c["phase_unwrapped"] for c in t1), min(c["phase_unwrapped"] for c in t1), CL.coverage(u)[1]))
    W("    largest patch among usable Type I cells %.1f mm = %.0f %% of the cell area (paper: limited to 36 %%, i.e. 4.5 mm)" %
      (max(max(c["a"], c["b"]) for c in t1), 100 * max(max(c["a"], c["b"]) for c in t1) ** 2 / CL.D_CELL ** 2))
    ul = CL.usable(CL.library(area_limit=True)); W("    with the 36 %% area limit the usable set leaves a %d deg gap" % CL.coverage(ul)[1])
    # --- assignment comparison and steering
    W("\n[7] HM cell assignment (complex-error rule used for the DXFs vs the paper's closest-phase-above-1 dB rule):")
    boards = {}
    for rule in ("complex", "paper"):
        for w in (1, 2):
            b = G.board_hm(w, lib, rule); boards[(rule, w)] = b
            e = np.array([r["err"] for r in b.rows]); m = np.array([r["mag_db"] for r in b.rows])
            t2 = sum(1 for r in b.rows if r["type"] == 2)
            W("    %-7s HM%s: rms phase error %5.2f deg, max %5.2f, mean |S21| %5.2f dB, worst %5.2f dB, metal-free cells %.1f %%" %
              (rule, "I " if w == 1 else "II", math.sqrt(np.mean(e ** 2)), np.max(np.abs(e)), np.mean(m), np.min(m), 100 * t2 / len(b.rows)))
    W("    paper: '1/3 of HM II is metal-free'. With Type II covering 0..-35 deg only the 0-deg column of the 6-column period is Type II -> 1/6.")
    W("\n[8] Steered system (aperture model; psi1 = 0, psi2 = 30..180):")
    W("    psi2 | theta eq / model / meas | phi eq / model / meas | model gain dBi (complex rule, paper rule) | meas. max gain | model SLL dB")
    res = []
    T = {k: cell_lookup(b.rows) for k, b in boards.items()}
    fig, axs = plt.subplots(2, 3, figsize=(15, 9.5))
    for n, (a, b, php, thp, phm, thm) in enumerate(TABLE1):
        r1 = steer(T[("complex", 1)], T[("complex", 2)], a, b); r2 = steer(T[("paper", 1)], T[("paper", 2)], a, b)
        th_e, ph_e = beam(p, p, a, b)
        W("    %4d | %5.1f / %5.1f / %5.1f | %5.1f / %5.1f / %5s | %6.2f, %6.2f | %5.1f | %6.1f" %
          (b, th_e, r1["theta"], thm, ph_e if th_e > 1e-6 else float("nan"), r1["phi"] if r1["theta"] > 0.5 else float("nan"), phm, r1["gain_dbi"], r2["gain_dbi"], TABLE2[b][0], r1["sll_db"]))
        res.append([a, b, round(th_e, 2), round(r1["theta"], 2), thm, round(ph_e, 2), round(r1["phi"], 2), phm, round(r1["gain_dbi"], 2), round(r2["gain_dbi"], 2), TABLE2[b][0], round(r1["sll_db"], 2)])
        a_ = axs.flat[n]; Pn = 10 * np.log10(r1["P"] / r1["P"].max() + 1e-12)
        a_.imshow(np.where(r1["U"] ** 2 + r1["V"] ** 2 < 1, Pn, np.nan), origin="lower", extent=[r1["U"][0, 0], r1["U"][0, -1], r1["V"][0, 0], r1["V"][-1, 0]], vmin=-30, vmax=0, cmap="viridis")
        a_.set_xlim(-1, 1); a_.set_ylim(-1, 1); a_.set_aspect("equal"); a_.set_title("psi1 0, psi2 %d: theta %.1f phi %.1f, %.1f dBi" % (b, r1["theta"], r1["phi"], r1["gain_dbi"]), fontsize=9)
        a_.set_xlabel("u"); a_.set_ylabel("v")
    fig.suptitle("Model u-v patterns (dB, normalised) - compare with paper Fig. 20", fontsize=10); fig.tight_layout(); fig.savefig(os.path.join(RES, "uv_patterns_six_cases.png"), dpi=130); plt.close(fig)
    rr0 = steer(T[("complex", 1)], T[("complex", 2)], 0, 0)
    W("    psi1 = psi2 = 0 (not in the paper): theta %.1f deg, gain %.2f dBi -> the true elevation limit of this hardware" % (rr0["theta"], rr0["gain_dbi"]))
    W("    model gains exclude dielectric/copper loss (paper: ~0.7 dB), feed mismatch and RLSA radiation efficiency; compare trends, not absolutes.")
    with open(os.path.join(RES, "steering_table.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["psi1", "psi2", "theta_eq", "theta_model", "theta_meas", "phi_eq", "phi_model", "phi_meas", "gain_model_complex_dBi", "gain_model_paper_rule_dBi", "gain_meas_max_dBic", "SLL_model_dB"]); w.writerows(res)
    with open(os.path.join(RES, "table1_check.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["psi1", "psi2", "phi_paper", "phi_ours", "theta_paper", "theta_ours", "theta_measured"]); w.writerows(rows)
    # --- steering map (inverse) for the operator
    with open(os.path.join(RES, "LUT_beam_to_rotation.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["theta_deg", "phi_deg", "psi1_deg", "psi2_deg"])
        for th in range(0, 42, 2):
            for ph in range(0, 360, 15):
                ic = inverse_correct(th, ph, p)
                if ic: w.writerow([th, ph, round(ic[0] % 360, 2), round(ic[1] % 360, 2)])
    # --- frequency: squint of the gradient (beam angle of a fixed phase screen ~ 1/f)
    W("\n[9] Frequency: a fixed phase gradient steers to sin(theta) = (f0/f) * 2 sin(theta0) cos(dpsi/2); at the max-elevation case:")
    for f in (19.0, 19.5, 20.0, 20.5):
        s = (G.F0 / f) * 2 * math.sin(math.radians(G.H["theta0"])) * math.cos(math.radians(15)); W("    f %.1f GHz: theta %.2f deg" % (f, math.degrees(math.asin(s))))
    # --- heights
    z = G.R["Wh"] + G.H["gap_rlsa"] + G.H["t"] + G.H["gap_hm"] + G.H["t"]
    W("\n[10] Stack height from the ground-plate top with the assumed 15 mm gaps: %.1f mm (+3 mm plate = %.1f); paper 45 mm = 3 lambda0" % (z, z + G.R["t_ground"]))
    W("     HM-HM gap that gives exactly 45.0 mm from the plate top: %.1f mm" % (45.0 - (G.R["Wh"] + G.H["gap_rlsa"] + 2 * G.H["t"])))
    with open(os.path.join(RES, "study_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))

if __name__ == "__main__":
    main()
