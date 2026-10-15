"""Analytical model of the broadside-coupled, varactor-tuned phase shifter (paper Sec. III-A, eqs. 1-7).

Designer's reading of the circuit: it is a REFLECTION-TYPE PHASE SHIFTER (RTPS).
  * The two broadside-coupled elliptical patches + ground slot form a backward-wave (quadrature) coupler.
  * Ports 3 and 4 (coupled & through) are terminated by identical reflective loads Gamma
    (stub of length l_stub + DC-block + varactor to ground).
  * Then (ideal symmetric coupler, T = through, K = coupled):
        S11 = Gamma (T^2 + K^2)      -> paper eq.(6)   [eq.(1) with Gamma = 1, open loads]
        S21 = 2 Gamma T K            -> paper eq.(7)   [eq.(2)]
    with  T = sqrt(1-C^2)/D,  K = j C sin(th)/D,  D = sqrt(1-C^2) cos(th) + j sin(th),  th = beta_ef * l.
  * For a 3-dB coupler at th = 90 deg, |2TK| = 1 and S11 = 0, so |S21| = |Gamma| and the phase of S21
    follows the phase of Gamma -> tuning the varactor capacitance Ci tunes the transmission phase.
  * The quarter-wave stub acts as an impedance transformer that stretches the varactor's reflection-phase
    range (paper Fig.3: stub length chosen ~ lambda_g/4).
Units: SI unless noted.  All component parasitics are explicit so you can see why datasheet SRF matters."""
import numpy as np

C0 = 299792458.0

def ms_eeff_z0(w_mm, h_mm, er):
    u = w_mm / h_mm
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
    if u <= 1: z0 = 60 / np.sqrt(ee) * np.log(8 / u + u / 4)
    else:      z0 = 120 * np.pi / (np.sqrt(ee) * (u + 1.393 + 0.667 * np.log(u + 1.444)))
    return ee, z0

def ms_width_for_z(z_target, h_mm, er):
    lo, hi = 0.05, 10.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if ms_eeff_z0(mid, h_mm, er)[1] > z_target: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

def varactor_C(V, C0j=1.7e-12, Cmin=0.14e-12, Vmax=15.0, Vbi=0.8, gamma=None):
    """Hyperabrupt junction model C(V) = Cp + Cj0/(1+V/Vbi)^gamma, fitted so C(0)=1.7 pF and C(Vmax)=0.14 pF.
    REPLACE with the MAVR-000120-14110P datasheet C-V table (or SPICE model) before building a bias LUT.
    Vmax is an assumption (check the datasheet reverse-voltage rating and the curve's end point)."""
    Cp = 0.05e-12
    if gamma is None:
        gamma = np.log((C0j - Cp) / (Cmin - Cp)) / np.log(1 + Vmax / Vbi)
    return Cp + (C0j - Cp) / (1 + np.asarray(V) / Vbi) ** gamma, gamma

def varactor_V(Ci, **kw):
    """Inverse of varactor_C (bias voltage for a wanted capacitance)."""
    Vg = np.linspace(0, kw.get("Vmax", 15.0), 20001); Cg, _ = varactor_C(Vg, **kw)
    return np.interp(-np.asarray(Ci), -Cg, Vg)

def Z_varactor(f, Ci, Rp=2.0, Lp=0.0):
    w = 2 * np.pi * f
    return Rp + 1 / (1j * w * Ci) + 1j * w * Lp                 # eq.(5)

def Z_cap_real(f, C, esl=0.0, esr=0.0):
    w = 2 * np.pi * f
    return esr + 1 / (1j * w * C) + 1j * w * esl

def Z_ind_real(f, L, srf=None, Q=40):
    """Inductor with parallel self-capacitance giving the self-resonant frequency srf (None = ideal)."""
    w = 2 * np.pi * f
    ZL = 1j * w * L + w * L / Q
    if srf is None: return ZL
    Cpar = 1 / ((2 * np.pi * srf) ** 2 * L)
    return 1 / (1 / ZL + 1j * w * Cpar)

def tline_zin(ZL, Z0, beta_l):
    t = np.tan(beta_l)
    return Z0 * (ZL + 1j * Z0 * t) / (Z0 + 1j * ZL * t)          # eq.(4)

def load_gamma(f, Ci, p):
    """Reflection of the stub-loaded section seen from the coupler, eq.(3).
    Chain (from coupler): stub (Zstub, length lstub) -> DC-block Cb (series) -> node with bias choke Lb to RF ground
    -> varactor (series Rp, Ci, Lp) to ground."""
    w = 2 * np.pi * f
    Zv = Z_varactor(f, Ci, p["Rp"], p["Lp"])
    Zch = Z_ind_real(f, p["Lb"], p.get("Lb_srf"))
    Znode = 1 / (1 / Zv + 1 / Zch)                                 # varactor || choke
    Zl = Znode + Z_cap_real(f, p["Cb"], p.get("Cb_esl", 0.0))       # + DC block
    beta = 2 * np.pi * f * np.sqrt(p["eeff_stub"]) / C0
    Zin = tline_zin(Zl, p["Zstub"], beta * p["lstub"])
    return (Zin - p["Zcl"]) / (Zin + p["Zcl"])

def coupler_TK(f, p):
    th = 2 * np.pi * f * np.sqrt(p["eeff_cpl"]) / C0 * p["lcpl"]
    C = p["Ccpl"]; s = np.sqrt(1 - C ** 2)
    D = s * np.cos(th) + 1j * np.sin(th)
    return s / D, 1j * C * np.sin(th) / D

def rtps_S(f, Ci, p):
    G = load_gamma(f, Ci, p); T, K = coupler_TK(f, p)
    return G * (T ** 2 + K ** 2), 2 * G * T * K                   # eqs.(6),(7)

def default_params():
    h, er = 0.508, 3.55
    w50 = ms_width_for_z(50, h, er)
    ee50, _ = ms_eeff_z0(w50, h, er)
    return dict(Zcl=50.0, Ccpl=10 ** (-3.0 / 20),                  # 3-dB broadside coupler (voltage coupling)
                eeff_cpl=ee50, lcpl=None,                          # set below: 90 deg at 6 GHz
                Zstub=50.0, eeff_stub=ee50, lstub=9.4e-3,          # paper lstub = 9.4 mm
                Rp=2.0, Lp=0.0, Cb=39e-12, Lb=100e-9,              # paper values (ideal parts)
                Cmin=0.14e-12, Cmax=1.7e-12, h=h, er=er, w50=w50)

def finalize(p, f0=6e9):
    if p["lcpl"] is None:
        p["lcpl"] = C0 / f0 / np.sqrt(p["eeff_cpl"]) / 4
    return p

def evaluate(p, f=np.linspace(5e9, 7e9, 41), nC=12):
    Cs = np.geomspace(p["Cmin"], p["Cmax"], nC)
    S11 = np.zeros((nC, f.size), complex); S21 = np.zeros_like(S11)
    for i, c in enumerate(Cs): S11[i], S21[i] = rtps_S(f, c, p)
    ph = np.unwrap(np.angle(S21), axis=0) * 180 / np.pi
    rel = ph - ph[-1]                                              # phase shift relative to Cmax state
    rng = np.abs(rel[0])                                           # range vs frequency
    # phase imbalance: deviation of each state's relative phase from its band average
    imb = np.max(np.abs(rel - rel.mean(axis=1, keepdims=True)))
    return dict(f=f, C=Cs, S11=S11, S21=S21, rel=rel, range_deg=rng, imbalance_deg=imb,
                IL_max_dB=(-20 * np.log10(np.abs(S21))).max(), RL_min_dB=-20 * np.log10(np.abs(S11)).max())

if __name__ == "__main__":
    p = finalize(default_params())
    r = evaluate(p)
    print("50-ohm width on 0.508 mm RO4003C: %.3f mm" % p["w50"])
    print("Ideal parts:  range %.1f..%.1f deg, imbalance +-%.1f deg, max IL %.2f dB, worst RL %.1f dB"
          % (r["range_deg"].min(), r["range_deg"].max(), r["imbalance_deg"], r["IL_max_dB"], r["RL_min_dB"]))

# ---------------------------------------------------------------------------------------------
# Case study: what the bias network really does at 5-7 GHz (the paper uses ideal 100 nH / 39 pF)
# ---------------------------------------------------------------------------------------------
def Z_res(f, R):            # bias resistor (high value) with ~0.05 pF pad parasitic
    w = 2 * np.pi * f
    return 1 / (1 / R + 1j * w * 0.05e-12)

def cases():
    out = []
    base = finalize(default_params())
    defs = {
      "A ideal parts (paper eqs, Lp=0)":            {},
      "B paper + 0.35 nH varactor/pad inductance":   {"Lp": 0.35e-9},
      "C B + real 0402 100nH (SRF 1.5 GHz) + 39pF (ESL 0.4 nH)": {"Lp": 0.35e-9, "Lb_srf": 1.5e9, "Cb_esl": 0.4e-9},
      "D B + 10 kohm bias resistor (no choke SRF) + 39 pF (ESL 0.4 nH)": {"Lp": 0.35e-9, "Lb": None, "Cb_esl": 0.4e-9},
    }
    for name, mod in defs.items():
        p = dict(base); p.update(mod)
        if p.get("Lb") is None:                      # resistor bias instead of choke
            p["Lb"] = 1.0; p["Lb_srf"] = None
            global Z_ind_real
            _orig = Z_ind_real
            Z_ind_real = lambda f, L, srf=None, Q=40: Z_res(f, 10e3)
            r = evaluate(p); Z_ind_real = _orig
        else:
            r = evaluate(p)
        out.append((name, r))
    return out

if __name__ == "__main__":
    print("\nTheoretical single-varactor RTPS range for C ratio %.1f: %.1f deg"
          % (1.7 / 0.14, 4 * np.degrees(np.arctan(np.sqrt(1.7 / 0.14))) - 180))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 4, figsize=(18, 7.5))
    for k, (name, r) in enumerate(cases()):
        print("%-62s range %5.1f-%5.1f deg | imbalance +-%4.1f deg | IL<=%.2f dB | RL>=%.1f dB"
              % (name, r["range_deg"].min(), r["range_deg"].max(), r["imbalance_deg"], r["IL_max_dB"], r["RL_min_dB"]))
        for i in range(len(r["C"])):
            ax[0, k].plot(r["f"] / 1e9, r["rel"][i], lw=1.2)
            ax[1, k].plot(r["f"] / 1e9, 20 * np.log10(np.abs(r["S21"][i])), lw=1.2)
        ax[0, k].set_title(name, fontsize=8.5); ax[0, k].set_ylabel("Phase shift vs Ci=1.7 pF (deg)"); ax[0, k].grid(alpha=.3)
        ax[1, k].set_xlabel("Frequency (GHz)"); ax[1, k].set_ylabel("|S21| (dB)"); ax[1, k].grid(alpha=.3); ax[1, k].set_ylim(-3, 0.2)
    fig.suptitle("RTPS analytic model (eqs. 3-7), Ci = 0.14-1.7 pF, 12 states (lossless substrate)", fontsize=11)
    fig.tight_layout(); fig.savefig("rtps_cases.png", dpi=100)

# ---------------------------------------------------------------------------------------------
# Bias look-up table: wanted relative phase -> Ci -> bias voltage, per frequency
# ---------------------------------------------------------------------------------------------
def phase_curve(f, p, n=400):
    """Relative phase (deg, 0 at Ci=Cmax, increasing as Ci falls) of S21 vs Ci at frequency f."""
    Cs = np.geomspace(p["Cmax"], p["Cmin"], n)
    ph = np.unwrap(np.angle([rtps_S(np.array([f]), c, p)[1][0] for c in Cs])) * 180 / np.pi
    return Cs, ph - ph[0]

def phase_to_bias(f, phi_deg, p, cv=None):
    """Ci and bias voltage giving relative phase phi_deg (0..range) at frequency f.
    cv: optional (V_array, C_array) measured/datasheet table; else the fitted hyperabrupt model."""
    Cs, ph = phase_curve(f, p)
    if np.any(np.asarray(phi_deg) > ph.max() + 1e-9) or np.any(np.asarray(phi_deg) < 0):
        raise ValueError("phase %s outside 0..%.1f deg at %.2f GHz" % (phi_deg, ph.max(), f / 1e9))
    Ci = np.interp(phi_deg, ph, Cs)
    if cv is None: V = varactor_V(Ci)
    else:          V = np.interp(-Ci, -np.asarray(cv[1]), np.asarray(cv[0]))
    return Ci, V
