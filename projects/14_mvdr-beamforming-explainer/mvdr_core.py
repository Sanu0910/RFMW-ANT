#!/usr/bin/env python3
"""
mvdr_core.py  --  Minimum Variance Distortionless Response (Capon) beamformer.

Everything the video draws is computed here from first principles, so the
beam patterns, nulls, covariance matrix and SINR numbers on screen are the
*real* output of the algorithm, not hand-drawn graphics.

Signal model  (narrowband, uniform linear array):

    x(t) = a(theta_d) s(t)  +  sum_j a(theta_j) i_j(t)  +  n(t)

    a(theta) = [1, e^{j psi}, ..., e^{j (M-1) psi}]^T ,   psi = 2 pi (d/lambda) sin(theta)

MVDR problem (Capon, 1969):

    minimise   w^H R w        (output power / "variance")
    subject to w^H a(theta_d) = 1   ("distortionless": unit gain on the look angle)

Closed-form solution via a Lagrange multiplier:

    w = R^{-1} a(theta_d) / ( a(theta_d)^H R^{-1} a(theta_d) )
"""
import numpy as np

# ----------------------------------------------------------------------------
# Array + scenario definition  (used everywhere in the video)
# ----------------------------------------------------------------------------
M = 8                 # number of antenna elements in the uniform linear array
D_SPACING = 0.5       # element spacing in wavelengths (half-wavelength array)

DESIRED_DEG = 20.0    # direction of the wanted GNSS satellite  (broadside = 0 deg)
JAMMERS_DEG = [-42.0, 58.0]   # two high-power jammers
SPOOFER_DEG = -14.0            # a counterfeit ("spoofing") source

# Power relative to the per-element thermal noise floor (which is 1.0):
SNR_DES = 1.0         #   0 dB  -- the satellite signal is weak
JNR_JAM = 1.0e4       # +40 dB  -- jammers are enormously stronger than the signal
JNR_SPO = 1.0e3       # +30 dB  -- the spoofer is strong too
NOISE   = 1.0         #   noise power per element

THETA_GRID = np.linspace(-90.0, 90.0, 1201)   # scan grid for beam patterns


def steering_vector(theta_deg, m=M, d=D_SPACING):
    """a(theta) for one angle (returns shape (m,)) or a grid (returns (m, N))."""
    theta = np.deg2rad(np.atleast_1d(theta_deg))
    n = np.arange(m)[:, None]
    a = np.exp(1j * 2 * np.pi * d * n * np.sin(theta))   # (m, N)
    return a[:, 0] if np.ndim(theta_deg) == 0 else a


def scene_covariance(diag_load=0.0):
    """
    True spatial covariance  R = E[x x^H]  for the scenario above.

        R = noise*I + P_d a_d a_d^H + sum_j P_j a_j a_j^H + P_sp a_sp a_sp^H

    `diag_load` adds sigma^2 * I (diagonal loading / LSMI regularisation).
    """
    R = NOISE * np.eye(M, dtype=complex)
    R += SNR_DES * np.outer(steering_vector(DESIRED_DEG), steering_vector(DESIRED_DEG).conj())
    for jd in JAMMERS_DEG:
        R += JNR_JAM * np.outer(steering_vector(jd), steering_vector(jd).conj())
    R += JNR_SPO * np.outer(steering_vector(SPOOFER_DEG), steering_vector(SPOOFER_DEG).conj())
    if diag_load:
        R += diag_load * np.eye(M)
    return R


def mvdr_weights(R, theta_look=DESIRED_DEG):
    """w = R^{-1} a / (a^H R^{-1} a)  -- the MVDR / Capon weight vector."""
    a = steering_vector(theta_look)
    Rinv_a = np.linalg.solve(R, a)
    return Rinv_a / (a.conj() @ Rinv_a)


def conventional_weights(theta_look=DESIRED_DEG):
    """Plain phased-array ('delay-and-sum') beamformer: w = a / M."""
    return steering_vector(theta_look) / M


def beam_pattern_db(w, theta_grid=THETA_GRID):
    """Array response |w^H a(theta)| in dB (0 dB on the look angle for MVDR)."""
    A = steering_vector(theta_grid)                 # (M, N)
    resp = np.abs(w.conj() @ A)
    return 20.0 * np.log10(np.maximum(resp, 1e-9))


def capon_spectrum_db(R, theta_grid=THETA_GRID):
    """MVDR / Capon spatial (DOA) spectrum  P(theta) = 1 / (a^H R^{-1} a)."""
    A = steering_vector(theta_grid)                 # (M, N)
    Rinv = np.linalg.inv(R)
    denom = np.einsum('mn,mk,kn->n', A.conj(), Rinv, A).real
    P = 1.0 / np.maximum(denom, 1e-12)
    return 10.0 * np.log10(P / P.max())


def output_sinr_db(w):
    """
    Output SINR of weight vector w:
        SINR = P_d |w^H a_d|^2 / ( w^H R_in w ),
    with R_in the interference-plus-noise covariance (desired removed).
    """
    a_d = steering_vector(DESIRED_DEG)
    R_in = NOISE * np.eye(M, dtype=complex)
    for jd in JAMMERS_DEG:
        R_in += JNR_JAM * np.outer(steering_vector(jd), steering_vector(jd).conj())
    R_in += JNR_SPO * np.outer(steering_vector(SPOOFER_DEG), steering_vector(SPOOFER_DEG).conj())
    sig = SNR_DES * np.abs(w.conj() @ a_d) ** 2
    intn = np.real(w.conj() @ R_in @ w)
    return 10.0 * np.log10(sig / intn)


def sample_covariance(n_snapshots, rng=None):
    """
    Estimate R from `n_snapshots` array snapshots -- R_hat = (1/N) sum x x^H.
    Used to animate the covariance matrix 'filling in' as data arrives.
    """
    rng = rng or np.random.default_rng(0)
    srcs = [(DESIRED_DEG, SNR_DES)] + [(j, JNR_JAM) for j in JAMMERS_DEG] + [(SPOOFER_DEG, JNR_SPO)]
    A = np.stack([steering_vector(d) for d, _ in srcs], axis=1)      # (M, K)
    p = np.array([pw for _, pw in srcs])
    N = max(int(n_snapshots), 1)
    s = (rng.standard_normal((len(srcs), N)) + 1j * rng.standard_normal((len(srcs), N)))
    s *= np.sqrt(p / 2)[:, None]
    noise = np.sqrt(NOISE / 2) * (rng.standard_normal((M, N)) + 1j * rng.standard_normal((M, N)))
    X = A @ s + noise
    return (X @ X.conj().T) / N


if __name__ == "__main__":
    # ----- self test: prove the algorithm nulls the jammers/spoofer -----
    R = scene_covariance()
    w = mvdr_weights(R)
    wc = conventional_weights()
    g = beam_pattern_db(w)

    def depth(ang):
        return g[np.argmin(np.abs(THETA_GRID - ang))]

    print(f"Array: M={M} elements, d={D_SPACING} lambda")
    print(f"Look direction (satellite): {DESIRED_DEG:+.0f} deg  -> gain {depth(DESIRED_DEG):+6.2f} dB")
    for jd in JAMMERS_DEG:
        print(f"Jammer  @ {jd:+.0f} deg  -> MVDR gain {depth(jd):+7.2f} dB  (deep null)")
    print(f"Spoofer @ {SPOOFER_DEG:+.0f} deg  -> MVDR gain {depth(SPOOFER_DEG):+7.2f} dB  (deep null)")
    print(f"Output SINR  conventional : {output_sinr_db(wc):+6.2f} dB")
    print(f"Output SINR  MVDR         : {output_sinr_db(w):+6.2f} dB")
    print(f"SINR improvement          : {output_sinr_db(w) - output_sinr_db(wc):+6.2f} dB")
