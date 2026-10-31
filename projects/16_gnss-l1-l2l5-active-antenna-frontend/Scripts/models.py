"""Component models for the GNSS L1 + L2/L5 active front end.

Builds scikit-rf Networks from the datasheet data in ds_data.py:
  TQP3M9037   measured S-parameter table (extracted) + noise parameters (extracted, extended [ASSUMED])
  HC125A      4-port from the typical-performance table; absolute phase [ASSUMED]
  B7504/B8889 2-port from digitized curves; phase from a minimum-phase reconstruction [ESTIMATED]
  DXP.02.A    3-port from digitized curves; phase from minimum-phase reconstruction [ESTIMATED]
  lumped bias/DC-block parts with parasitics [ASSUMED]
plus a noise-correlation-matrix cascade (Hillbrand & Russer 1976) for noise figure.

Equations (also in the report):
  min-phase:   ln H(w) = ln|H(w)| + j*arg H(w), arg H = -Hilbert{ln|H|}  (real-cepstrum folding)
  VSWR -> |G|: |G| = (VSWR-1)/(VSWR+1)
  SAW S11/S22 phase: arg S11 = arg S22 = arg S21 + 90 deg  (lossless, reciprocal, symmetric 2-port:
               S11 S21* + S21 S22* = 0)
  passive noise (Y form):   C_Y = 2kT0 Re{Y}            -> C_A = T C_Y T^H, T = [[0, B], [1, D]]
  active noise (ABCD form): C_A = 2kT0 [[Rn, (Fmin-1)/2 - Rn Yopt*], [(Fmin-1)/2 - Rn Yopt, Rn |Yopt|^2]]
  cascade:                  C_A = C_A1 + A1 C_A2 A1^H
  noise factor:             F = 1 + z^H C_A z / (2kT0 Re{Zs}),  z = [1, Zs*]^T
  stability:  K = (1 - |S11|^2 - |S22|^2 + |D|^2) / (2 |S12 S21|),  D = S11 S22 - S12 S21
              mu = (1 - |S11|^2) / (|S22 - D S11*| + |S12 S21|)
"""
from __future__ import annotations

import numpy as np
import skrf as rf
from scipy.interpolate import PchipInterpolator, CubicSpline

import ds_data as D

Z0 = 50.0
T0 = 290.0

# --------------------------------------------------------------------------------------
# frequency grids
# --------------------------------------------------------------------------------------
F_SYS = rf.Frequency(600, 2200, 3201, unit="MHz")            # system grid, 0.5 MHz step
F_SAW = rf.Frequency(10, 6000, 11981, unit="MHz")            # SAW Touchstone grid, 0.5 MHz step
F_DXP = rf.Frequency(600, 2200, 3201, unit="MHz")            # diplexer Touchstone grid
F_HC = rf.Frequency(600, 2200, 401, unit="MHz")              # hybrid Touchstone grid, 4 MHz step

# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def db2mag(db):
    return 10 ** (np.asarray(db) / 20)


def vswr2gamma(v):
    v = np.asarray(v, float)
    return (v - 1) / (v + 1)


def pchip_db(points, f_mhz, lo_hold=True):
    """Monotone (PCHIP) interpolation of digitized (f, value) points, held flat outside."""
    p = np.array(sorted(points), float)
    f = np.clip(f_mhz, p[0, 0], p[-1, 0]) if lo_hold else f_mhz
    return PchipInterpolator(p[:, 0], p[:, 1])(f)


def min_phase(f_mhz, att_db_func, fmax_mhz=8192.0, n=32768):
    """Minimum-phase transfer function from an attenuation curve (positive dB).

    Builds |H| on a uniform 0..fmax grid, takes the real cepstrum, folds it and returns the
    complex H interpolated (magnitude in dB, phase unwrapped) at f_mhz.
    """
    fg = np.linspace(0, fmax_mhz, n // 2 + 1)
    logmag = -att_db_func(fg) / 20 * np.log(10)                  # ln|H|
    full = np.concatenate([logmag, logmag[-2:0:-1]])             # even spectrum, length n
    cep = np.fft.ifft(full).real
    fold = np.zeros(n)
    fold[0] = cep[0]
    fold[1:n // 2] = 2 * cep[1:n // 2]
    fold[n // 2] = cep[n // 2]
    h = np.exp(np.fft.fft(fold))[: n // 2 + 1]
    ph = np.unwrap(np.angle(h))
    mag_db = 20 * np.log10(np.abs(h))
    ph_i = np.interp(f_mhz, fg, ph)
    mag_i = np.interp(f_mhz, fg, mag_db)
    return db2mag(mag_i) * np.exp(1j * ph_i)


def enforce_passive(s, margin=0.999):
    """Scale each frequency's S matrix so its largest singular value is <= margin."""
    s = s.copy()
    for k in range(s.shape[0]):
        sv = np.linalg.svd(s[k], compute_uv=False)[0]
        if sv > margin:
            s[k] *= margin / sv
    return s


def series_z(freq: rf.Frequency, z: np.ndarray, name="series") -> rf.Network:
    s = np.zeros((freq.npoints, 2, 2), complex)
    s[:, 0, 0] = s[:, 1, 1] = z / (z + 2 * Z0)
    s[:, 0, 1] = s[:, 1, 0] = 2 * Z0 / (z + 2 * Z0)
    return rf.Network(frequency=freq, s=s, z0=Z0, name=name)


def shunt_z(freq: rf.Frequency, z: np.ndarray, name="shunt") -> rf.Network:
    y = 1 / z
    s = np.zeros((freq.npoints, 2, 2), complex)
    s[:, 0, 0] = s[:, 1, 1] = -y * Z0 / (2 + y * Z0)
    s[:, 0, 1] = s[:, 1, 0] = 2 / (2 + y * Z0)
    return rf.Network(frequency=freq, s=s, z0=Z0, name=name)


def z_cap(freq, c, esl=0.0, esr=0.0):
    w = 2 * np.pi * freq.f
    return esr + 1j * w * esl + 1 / (1j * w * c)


def z_ind(freq, l, q_ref=40.0, f_qref=1.4e9, cpar=0.0):
    """Inductor with series loss set by Q at f_qref and a parallel (SRF) capacitance."""
    w = 2 * np.pi * freq.f
    r = 2 * np.pi * f_qref * l / q_ref
    zl = r + 1j * w * l
    if cpar:
        zl = 1 / (1 / zl + 1j * w * cpar)
    return zl


def load_z(freq, z=Z0, name="load"):
    g = (z - Z0) / (z + Z0)
    return rf.Network(frequency=freq, s=np.full((freq.npoints, 1, 1), g, complex), z0=Z0, name=name)


# --------------------------------------------------------------------------------------
# TQP3M9037 LNA
# --------------------------------------------------------------------------------------
def tqp_table_network() -> rf.Network:
    t = np.array(D.TQP_SPARAMS_5V)
    f = t[:, 0] * 1e9
    s = np.zeros((len(f), 2, 2), complex)
    for (i, j), c in {(0, 0): 1, (1, 0): 3, (0, 1): 5, (1, 1): 7}.items():
        s[:, i, j] = db2mag(t[:, c]) * np.exp(1j * np.deg2rad(t[:, c + 1]))
    return rf.Network(frequency=rf.Frequency.from_f(f, unit="Hz"), s=s, z0=Z0, name="TQP3M9037_5V")


def tqp_noise_table(extended=True):
    rows = (D.TQP_NOISE_EXT if extended else []) + D.TQP_NOISE_5V
    a = np.array(rows)
    return a[:, 0] * 1e9, a[:, 1], a[:, 2] * np.exp(1j * np.deg2rad(a[:, 3])), a[:, 4]


def tqp_on(freq: rf.Frequency) -> rf.Network:
    """LNA S-parameters interpolated (dB magnitude / unwrapped phase, cubic) onto freq."""
    t = tqp_table_network()
    fs = t.f
    s = np.zeros((freq.npoints, 2, 2), complex)
    for i in range(2):
        for j in range(2):
            mag = CubicSpline(fs, 20 * np.log10(np.abs(t.s[:, i, j])))(freq.f)
            ph = CubicSpline(fs, np.unwrap(np.angle(t.s[:, i, j])))(freq.f)
            s[:, i, j] = db2mag(mag) * np.exp(1j * ph)
    return rf.Network(frequency=freq, s=s, z0=Z0, name="TQP3M9037")


def tqp_noise_on(freq: rf.Frequency):
    """NFmin [dB], Gopt, Rn on freq (linear interp of the table incl. [ASSUMED] extension)."""
    f, nf, g, rn = tqp_noise_table()
    nf_i = np.interp(freq.f, f, nf)
    g_i = np.interp(freq.f, f, np.abs(g)) * np.exp(1j * np.interp(freq.f, f, np.unwrap(np.angle(g))))
    rn_i = np.interp(freq.f, f, rn)
    return nf_i, g_i, rn_i


# Bias network / DC blocks, eval-board values (Qorvo p.5) with [ASSUMED] parasitics
BIAS = dict(
    c_block=100e-12, c_block_esl=0.25e-9, c_block_esr=0.15,      # 0402 NPO, ESL/ESR [ASSUMED]
    l_choke=18e-9, l_choke_q=40.0, l_choke_cpar=0.12e-12,        # 0603 ceramic, Q/SRF [ASSUMED]
    c_bypass=100e-12, c_bypass_esl=0.4e-9,                        # choke cold end to ground
)


def lna_stage(freq: rf.Frequency):
    """Input DC block -> TQP3M9037 -> output bias tee (choke to bypassed VDD) -> output DC block.

    Returns (pre, lna, post, stage): pre/post are passive 2-ports for the noise cascade.
    """
    b = BIAS
    cin = series_z(freq, z_cap(freq, b["c_block"], b["c_block_esl"], b["c_block_esr"]), "C1_dcblock")
    zchoke = z_ind(freq, b["l_choke"], b["l_choke_q"], cpar=b["l_choke_cpar"]) + \
        z_cap(freq, b["c_bypass"], b["c_bypass_esl"], 0.1)
    choke = shunt_z(freq, zchoke, "L1_choke")
    cout = series_z(freq, z_cap(freq, b["c_block"], b["c_block_esl"], b["c_block_esr"]), "C2_dcblock")
    lna = tqp_on(freq)
    post = choke ** cout
    stage = cin ** lna ** post
    stage.name = "LNA_stage"
    return cin, lna, post, stage


# --------------------------------------------------------------------------------------
# HC125A hybrid
# --------------------------------------------------------------------------------------
HC_F0_MHZ = 1390.0  # [ASSUMED] quarter-wave centre for the through-path phase model


def hc125a(freq: rf.Frequency = F_HC) -> rf.Network:
    """4-port HC125A. Pin1 in -> Pin4 through (angle th), Pin3 coupled (angle th - phase col),
    Pin2 isolated. Symmetric: pairs (1,2) and (3,4) isolated.

    Magnitudes: table p.6 ('Transmission' -> through, 'Coupling' -> coupled, 'Isolation', RL per
    port). Absolute through phase th = -90 deg * f/f0 [ASSUMED], isolation phase th - 180
    [ASSUMED], reflection phase 0 [ASSUMED]. Held flat outside 1150-1630 MHz [EXTRAPOLATED].
    """
    t = np.array(D.HC_TABLE)
    fm = freq.f / 1e6

    def col(c):
        return np.interp(fm, t[:, 0], t[:, c])

    th = np.deg2rad(-90.0 * fm / HC_F0_MHZ)
    T = db2mag(col(2)) * np.exp(1j * th)
    C = db2mag(col(1)) * np.exp(1j * (th - np.deg2rad(col(6))))
    r = [db2mag(col(7 + k)) for k in range(4)]

    def build(ph_r, ph_i):
        I = db2mag(col(4)) * np.exp(1j * (th + ph_i))
        s = np.zeros((freq.npoints, 4, 4), complex)
        for k in range(4):
            s[:, k, k] = r[k] * np.exp(1j * (th + ph_r))
        for (a, b_), v in {(0, 1): I, (2, 3): I, (0, 3): T, (1, 2): T, (0, 2): C, (1, 3): C}.items():
            s[:, a, b_] = s[:, b_, a] = v
        return s

    # [ASSUMED] reflection and isolation phases (not in the datasheet) are chosen, as constant
    # offsets from the through phase, to minimise the largest singular value, i.e. so that the
    # table magnitudes form a passive 4-port without rescaling.
    best = None
    for ph_r in np.deg2rad(np.arange(0, 360, 15)):
        for ph_i in np.deg2rad(np.arange(0, 360, 15)):
            s = build(ph_r, ph_i)
            smax = np.linalg.svd(s, compute_uv=False)[:, 0].max()
            if best is None or smax < best[0]:
                best = (smax, ph_r, ph_i)
    hc125a.phase_offsets_deg = (np.rad2deg(best[1]), np.rad2deg(best[2]), best[0])
    return rf.Network(frequency=freq, s=enforce_passive(build(best[1], best[2])), z0=Z0, name="HC125A")


def patch_cp_feed(freq: rf.Frequency) -> rf.Network:
    """[ASSUMED] ideal dual-feed patch excited by RHCP: lossless 4-port quadrature splitter.
    Port 1 = RHCP virtual input, port 2 = LHCP (terminated, its noise = sky/ambient at T0),
    ports 3/4 = feed A (-> HC125A pin 3) / feed B (-> HC125A pin 4), feed A leads by 90 deg."""
    a = 1 / np.sqrt(2)
    m = np.array([[0, 0, a, -1j * a], [0, 0, -1j * a, a], [a, -1j * a, 0, 0], [-1j * a, a, 0, 0]])
    return rf.Network(frequency=freq, s=np.repeat(m[None], freq.npoints, 0), z0=Z0, name="PatchCP")


# --------------------------------------------------------------------------------------
# SAW filters (2-port) and diplexer (3-port)
# --------------------------------------------------------------------------------------
def _reflection(f_mhz, s21_mag, vswr_pts, refl_k=0.95, blend_mhz=4.0):
    """|S11| from digitized VSWR inside its range, reflective sqrt(1-|S21|^2)*k outside,
    crossfaded over blend_mhz at the range edges."""
    p = np.array(sorted(vswr_pts), float)
    g_v = vswr2gamma(PchipInterpolator(p[:, 0], p[:, 1])(np.clip(f_mhz, p[0, 0], p[-1, 0])))
    g_r = np.sqrt(np.clip(1 - s21_mag ** 2, 0, 1)) * refl_k
    w_lo = np.clip((f_mhz - p[0, 0]) / blend_mhz, 0, 1)
    w_hi = np.clip((p[-1, 0] - f_mhz) / blend_mhz, 0, 1)
    w = w_lo * w_hi
    return w * g_v + (1 - w) * g_r


def saw_filter(name, att_pts, vswr_in_pts, vswr_out_pts, freq: rf.Frequency = F_SAW) -> rf.Network:
    fm = freq.f / 1e6
    p = np.array(sorted(att_pts), float)
    att = PchipInterpolator(p[:, 0], p[:, 1])

    def att_f(f):
        return att(np.clip(f, p[0, 0], p[-1, 0]))

    s21 = min_phase(fm, att_f)
    g11 = _reflection(fm, np.abs(s21), vswr_in_pts)
    g22 = _reflection(fm, np.abs(s21), vswr_out_pts)
    ph = np.angle(s21) + np.pi / 2
    s = np.zeros((freq.npoints, 2, 2), complex)
    s[:, 1, 0] = s[:, 0, 1] = s21
    s[:, 0, 0] = g11 * np.exp(1j * ph)
    s[:, 1, 1] = g22 * np.exp(1j * ph)
    return rf.Network(frequency=freq, s=enforce_passive(s), z0=Z0, name=name)


def b7504(freq=F_SAW):
    return saw_filter("B7504", D.B7504_ATT_DIG, D.B7504_VSWR_IN_DIG, D.B7504_VSWR_OUT_DIG, freq)


def b8889(freq=F_SAW):
    """B8889 including the datasheet's required 6.8 nH shunt matching at both ports (the
    datasheet curves are measured with it), i.e. the 'matched block'."""
    return saw_filter("B8889_matched", D.B8889_ATT_DIG, D.B8889_VSWR_IN_DIG, D.B8889_VSWR_OUT_DIG, freq)


def dxp02a(freq: rf.Frequency = F_DXP) -> rf.Network:
    """3-port: 1 = common (pin 2), 2 = L1 (pin 7), 3 = L2/L5 (pin 5); eval-board matching included.
    Transmission phases minimum-phase; reflection phase = phase of the dominant transmission
    from that port + 90 deg [ASSUMED]."""
    fm = freq.f / 1e6

    def mp(pts):
        p = np.array(sorted(pts), float)
        a = PchipInterpolator(p[:, 0], p[:, 1])
        return min_phase(fm, lambda f: a(np.clip(f, p[0, 0], p[-1, 0])))

    s21, s31, s23 = mp(D.DXP_S21_DIG), mp(D.DXP_S31_DIG), mp(D.DXP_S23_DIG)
    rl = [db2mag(-pchip_db(pts, fm)) for pts in (D.DXP_RL1_DIG, D.DXP_RL2_DIG, D.DXP_RL3_DIG)]
    dom1 = np.where(np.abs(s21) >= np.abs(s31), np.angle(s21), np.angle(s31))
    dom2 = np.where(np.abs(s21) >= np.abs(s23), np.angle(s21), np.angle(s23))
    dom3 = np.where(np.abs(s31) >= np.abs(s23), np.angle(s31), np.angle(s23))
    s = np.zeros((freq.npoints, 3, 3), complex)
    s[:, 0, 0] = rl[0] * np.exp(1j * (dom1 + np.pi / 2))
    s[:, 1, 1] = rl[1] * np.exp(1j * (dom2 + np.pi / 2))
    s[:, 2, 2] = rl[2] * np.exp(1j * (dom3 + np.pi / 2))
    s[:, 0, 1] = s[:, 1, 0] = s21
    s[:, 0, 2] = s[:, 2, 0] = s31
    s[:, 1, 2] = s[:, 2, 1] = s23
    return rf.Network(frequency=freq, s=enforce_passive(s), z0=Z0, name="DXP02A")


# --------------------------------------------------------------------------------------
# noise (ABCD correlation matrices, normalised to 2kT0)
# --------------------------------------------------------------------------------------
def abcd(n: rf.Network):
    return n.a


def ca_passive(n: rf.Network):
    """C_A of a passive 2-port at T0 from Re{Y} (Twiss)."""
    y = n.y
    cy = 0.5 * (y + np.conj(np.swapaxes(y, 1, 2)))
    a = n.a
    T = np.zeros_like(a)
    T[:, 0, 1] = a[:, 0, 1]
    T[:, 1, 0] = 1
    T[:, 1, 1] = a[:, 1, 1]
    return T @ cy @ np.conj(np.swapaxes(T, 1, 2))


def ca_active(nfmin_db, gopt, rn):
    fmin = 10 ** (np.asarray(nfmin_db) / 10)
    yopt = (1 - gopt) / (Z0 * (1 + gopt))
    c = np.zeros((len(fmin), 2, 2), complex)
    c[:, 0, 0] = rn
    c[:, 0, 1] = (fmin - 1) / 2 - rn * np.conj(yopt)
    c[:, 1, 0] = (fmin - 1) / 2 - rn * yopt
    c[:, 1, 1] = rn * np.abs(yopt) ** 2
    return c


def cascade_noise(blocks):
    """blocks: list of (Network, C_A). Returns (A_total, C_A_total)."""
    a_tot, c_tot = None, None
    for n, c in blocks:
        a = n.a
        if a_tot is None:
            a_tot, c_tot = a, c
        else:
            c_tot = c_tot + a_tot @ c @ np.conj(np.swapaxes(a_tot, 1, 2))
            a_tot = a_tot @ a
    return a_tot, c_tot


def noise_factor(c_a, zs=Z0):
    zs = np.broadcast_to(np.asarray(zs, complex), c_a.shape[:1])
    z = np.stack([np.ones_like(zs), np.conj(zs)], axis=1)[:, :, None]
    num = (np.conj(np.swapaxes(z, 1, 2)) @ c_a @ z)[:, 0, 0].real
    return 1 + num / np.real(zs)


def _self_test():
    f = rf.Frequency(1, 2, 3, unit="GHz")
    # matched 3 dB attenuator must give NF = 3 dB
    k = 10 ** (-3 / 20)
    s = np.zeros((3, 2, 2), complex)
    s[:, 0, 1] = s[:, 1, 0] = k
    att = rf.Network(frequency=f, s=s, z0=Z0)
    # (a pure attenuator needs matched resistive realisation: use a pi-pad via Y from S)
    nf = 10 * np.log10(noise_factor(ca_passive(att)))
    assert np.allclose(nf, 3.0, atol=1e-6), nf
    # active block at Zs = Zopt must give F = Fmin
    g = np.full(3, 0.3 * np.exp(1j * 0.5))
    c = ca_active(np.full(3, 0.5), g, np.full(3, 10.0))
    zopt = Z0 * (1 + g) / (1 - g)
    assert np.allclose(10 * np.log10(noise_factor(c, zopt)), 0.5, atol=1e-9)


_self_test()


# --------------------------------------------------------------------------------------
# stability
# --------------------------------------------------------------------------------------
def k_mu(n: rf.Network):
    s11, s12, s21, s22 = n.s[:, 0, 0], n.s[:, 0, 1], n.s[:, 1, 0], n.s[:, 1, 1]
    dlt = s11 * s22 - s12 * s21
    k = (1 - abs(s11) ** 2 - abs(s22) ** 2 + abs(dlt) ** 2) / (2 * abs(s12 * s21))
    mu = (1 - abs(s11) ** 2) / (abs(s22 - dlt * np.conj(s11)) + abs(s12 * s21))
    mu2 = (1 - abs(s22) ** 2) / (abs(s11 - dlt * np.conj(s22)) + abs(s12 * s21))
    return k, mu, mu2, abs(dlt)
