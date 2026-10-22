#!/usr/bin/env python3
"""Design replica of the 60-GHz serpentine slotted-waveguide leaky-wave antenna.

Paper: J. Gabsteiger, C. Robisch, A. Koelpin, F. Lurz, "Advancing 60-GHz SISO Radar: Additively Manufactured
Leaky Wave Antenna With Enhanced Beam Steering", IEEE TAP vol. 74 no. 7, July 2026, DOI 10.1109/TAP.2026.3681348.

Re-derives every design number of the paper from its equations and writes results/ (CSV + PNG):
  eq. 6   WR15 dispersion beta(f)
  eq. 11  serpentine beam angle theta0(f), port 1 and port 2 (mirrored)
  eq. 12  grating-lobe limit d < lambda0/2 at 63.5 GHz
  eq. 14  serpentine path length l from theta0(58 GHz) = 86 deg
  eq. 15  array factor of the 16 slots, patterns over 58-63.5 GHz, HPBW and beam trajectory
  eq. 16  slot conductances from a 20-dB Dolph-Chebyshev taper (Table I)
  eq. 17/18/20  slot tilt and depth from the paper's polynomial fits (Tables I and II)
  eq. 1/2/4  FMCW range resolution and the range-angle uncertainty relation
"""
import csv
import json
import os

import numpy as np
from scipy.signal.windows import chebwin

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299_792_458.0
# ---------------------------------------------------------------- paper parameters
A_WG = 3.76e-3        # WR15 broad dimension a (m)
B_WG = 1.88e-3        # WR15 narrow dimension b (m)
GAP_WALLS = 0.5e-3    # air gap + two wall thicknesses (m), eq. 13
D = B_WG + GAP_WALLS  # slot spacing d = 2.38 mm
N = 16                # number of slots
SLL_DB = 20.0         # Dolph-Chebyshev sidelobe level
M = 1                 # Floquet index in eq. 11
F_LO, F_HI = 58e9, 63.5e9
W_SLOT = A_WG / 16 / 0.9   # eq. 19 -> 0.261 mm (adjusted to 0.34 mm for printing)
W_SLOT_ADJ = 0.34e-3

# paper tables for comparison
TABLE_I = [(0.866, 0.069, 18.731, 0.296), (0.504, 0.023, 11.332, 0.361), (0.621, 0.035, 13.656, 0.338),
           (0.733, 0.049, 15.947, 0.319), (0.832, 0.064, 18.017, 0.302), (0.913, 0.077, 19.710, 0.287),
           (0.970, 0.087, 20.907, 0.276), (1.000, 0.092, 21.526, 0.270)]
TABLE_II = [(28.097, 0.195), (16.998, 0.308), (20.484, 0.281), (23.921, 0.248), (27.026, 0.210), (29.566, 0.173),
            (31.361, 0.145), (32.289, 0.130)]


def mirror(half):
    return list(half) + list(half[::-1])


def k0(f):
    return 2 * np.pi * f / C0


def beta_wr15(f, a=A_WG):
    """eq. 6: TE10 phase constant (rad/m)."""
    return np.sqrt(k0(f) ** 2 - (np.pi / a) ** 2)


def theta0_serpentine(f, l, d=D, m=M):
    """eq. 11: main-beam angle (deg) measured from the array axis, port 1."""
    arg = (beta_wr15(f) * l - 2 * np.pi * (m + 0.5)) / (k0(f) * d)
    return np.degrees(np.arccos(np.clip(arg, -1, 1)))


def theta0_straight(f, d=D):
    """eq. 10: conventional (non-serpentine) alternating slotted radiator."""
    arg = beta_wr15(f) / k0(f) - (C0 / f) / (2 * d)
    return np.degrees(np.arccos(np.clip(arg, -1, 1)))


def path_length_for(theta_deg, f, d=D, m=M):
    """eq. 11 solved for l (the paper's eq. 14 step)."""
    return (k0(f) * d * np.cos(np.radians(theta_deg)) + 2 * np.pi * (m + 0.5)) / beta_wr15(f)


def tilt_from_g(g):
    """eq. 17 (natural log, checked against Table I)."""
    x = np.log(g)
    return 0.020 * x ** 4 + 0.479 * x ** 3 + 5.353 * x ** 2 + 28.877 * x + 65.765


def depth_from_g(g):
    """eq. 18 (mm)."""
    x = np.log(g)
    return -0.003 * x ** 4 - 0.047 * x ** 3 - 0.302 * x ** 2 - 0.877 * x - 0.660


def depth_from_tilt(t):
    """eq. 20 (mm), for the adjusted tilts theta_adj = 1.5 theta."""
    return 1.5e-6 * t ** 4 - 0.0001508 * t ** 3 + 0.0051532 * t ** 2 - 0.0819125 * t + 0.8250823


def array_factor(f, l, a_n, theta_deg, port=1, d=D):
    """eq. 15 generalised: slots at z_n = n d, travelling-wave phase -beta l per element, +pi per element from
    the alternating slot tilt. Port 2 feeds from the other end (reversed phase progression)."""
    th = np.radians(theta_deg)
    n = np.arange(len(a_n))
    psi = k0(f) * d * np.cos(th)[:, None] * n[None, :]
    phase = -(beta_wr15(f) * l - np.pi) * n
    if port == 2:
        phase = -(beta_wr15(f) * l - np.pi) * (len(a_n) - 1 - n)
    af = np.abs(np.sum(np.asarray(a_n)[None, :] * np.exp(1j * (psi + phase[None, :])), axis=1))
    return af / af.max()


def hpbw(theta, pat_db):
    i = int(np.argmax(pat_db))
    lo = i
    while lo > 0 and pat_db[lo] > -3:
        lo -= 1
    hi = i
    while hi < len(pat_db) - 1 and pat_db[hi] > -3:
        hi += 1
    return theta[i], theta[hi] - theta[lo]


def main():
    res = {}
    lam_hi = C0 / F_HI
    res["d_mm"] = D * 1e3
    res["grating_limit_mm"] = lam_hi / 2 * 1e3
    l = path_length_for(86.0, F_LO)
    res["l_mm_exact"] = l * 1e3
    L = 10.9e-3                                     # paper value, eq. 14
    res["l_mm_paper"] = L * 1e3
    res["theta_58_deg"] = float(theta0_serpentine(F_LO, L))
    res["theta_63p5_deg"] = float(theta0_serpentine(F_HI, L))
    res["scan_per_port_deg"] = res["theta_58_deg"] - res["theta_63p5_deg"]
    res["straight_theta_58_deg"] = float(theta0_straight(F_LO))
    res["straight_theta_63p5_deg"] = float(theta0_straight(F_HI))
    res["slot_width_eq19_mm"] = W_SLOT * 1e3
    res["fc_TE10_GHz"] = C0 / (2 * A_WG) / 1e9

    # ---- Table I / II
    a_n = chebwin(N, SLL_DB)
    g_n = a_n ** 2 / np.sum(a_n ** 2)
    tilt = tilt_from_g(g_n)
    depth = depth_from_g(g_n)
    tilt_adj = 1.5 * tilt
    depth_adj = depth_from_tilt(tilt_adj)
    t1 = mirror(TABLE_I)
    t2 = mirror(TABLE_II)
    rows = []
    for i in range(N):
        rows.append({"slot": i + 1, "a_n": round(a_n[i], 3), "a_n_paper": t1[i][0],
                     "g_n": round(g_n[i], 4), "g_n_paper": t1[i][1],
                     "tilt_deg": round(tilt[i], 3), "tilt_deg_paper": t1[i][2],
                     "depth_mm": round(depth[i], 3), "depth_mm_paper": t1[i][3],
                     "tilt_adj_deg": round(tilt_adj[i], 3), "tilt_adj_deg_paper": t2[i][0],
                     "depth_adj_mm": round(depth_adj[i], 3), "depth_adj_mm_paper": t2[i][1]})
    with open(os.path.join(OUT, "slot_table.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # the CAD uses the paper's own Table II values (the exact final design)
    with open(os.path.join(OUT, "slot_table_for_cad.json"), "w") as fh:
        json.dump({"tilt_deg": [r[0] for r in t2], "depth_mm": [r[1] for r in t2],
                   "width_mm": W_SLOT_ADJ * 1e3, "pitch_mm": D * 1e3, "l_mm": L * 1e3,
                   "a_mm": A_WG * 1e3, "b_mm": B_WG * 1e3}, fh, indent=1)

    # ---- beam trajectory and patterns
    f = np.linspace(F_LO, F_HI, 23)
    th = np.linspace(0, 180, 3601)
    traj = []
    for fi in f:
        for port in (1, 2):
            p = 20 * np.log10(array_factor(fi, L, a_n, th, port) + 1e-12)
            peak, bw = hpbw(th, p)
            traj.append((fi / 1e9, port, peak, bw))
    with open(os.path.join(OUT, "beam_trajectory.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["f_GHz", "port", "theta_peak_deg", "hpbw_deg"])
        for r in traj:
            w.writerow([f"{r[0]:.3f}", r[1], f"{r[2]:.2f}", f"{r[3]:.2f}"])
    p1 = [r for r in traj if r[1] == 1]
    p2 = [r for r in traj if r[1] == 2]
    res["af_port1_range_deg"] = [p1[0][2], p1[-1][2]]
    res["af_port2_range_deg"] = [p2[0][2], p2[-1][2]]
    res["total_coverage_deg"] = max(r[2] for r in p2) - min(r[2] for r in p1)
    res["hpbw_mean_deg"] = float(np.mean([r[3] for r in traj]))
    res["scan_rate_deg_per_GHz"] = res["scan_per_port_deg"] / ((F_HI - F_LO) / 1e9)

    # ---- FMCW numbers (eq. 1, 2, 4, and the switch doubling of section V-B)
    B = F_HI - F_LO
    res["range_res_full_bw_cm"] = C0 / (2 * B) * 100
    res["range_res_500MHz_cm"] = C0 / (2 * 500e6) * 100
    res["eff_bw_per_beam_MHz"] = B / 1e6 * res["hpbw_mean_deg"] / res["scan_per_port_deg"]
    res["range_res_effective_cm"] = C0 / (2 * res["eff_bw_per_beam_MHz"] * 1e6) * 100
    res["uncertainty_product_m_deg"] = C0 / (2 * B) * res["scan_per_port_deg"]
    res["virtual_bw_with_switch_GHz"] = 2 * B / 1e9
    with open(os.path.join(OUT, "design_summary.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    # ---- figures
    plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
    ff = np.linspace(57e9, 64e9, 300)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].plot(ff / 1e9, theta0_serpentine(ff, L), "C3", label="serpentine, port 1 (eq. 11)")
    ax[0].plot(ff / 1e9, 180 - theta0_serpentine(ff, L), "C3--", label="serpentine, port 2")
    ax[0].plot(ff / 1e9, theta0_straight(ff), "C0", label="straight slotted guide (eq. 10)")
    ax[0].axvspan(58, 63.5, color="0.92")
    ax[0].set_xlabel("frequency (GHz)")
    ax[0].set_ylabel("beam angle from array axis (deg)")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=.3)
    ax[0].set_title("Beam squint: 8.7° straight vs 32° per port serpentine")
    ax[1].plot(ff / 1e9, beta_wr15(ff) / k0(ff), "C0", label="β/k0 of WR15 (eq. 6)")
    ax[1].plot(ff / 1e9, (beta_wr15(ff) * L - np.pi) / (k0(ff) * D), "C3",
               label="effective (βl − π)/(k0 d), serpentine")
    ax[1].set_xlabel("frequency (GHz)")
    ax[1].set_ylabel("normalised phase constant")
    ax[1].legend(fontsize=7)
    ax[1].grid(alpha=.3)
    ax[1].set_title("Dispersion: the meander multiplies the slope")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_beam_angle_dispersion.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    cols = plt.cm.plasma(np.linspace(0.1, 0.85, 4))
    for c, fi in zip(cols, [58e9, 59e9, 61e9, 63.5e9]):
        for port, ls in ((1, "-"), (2, "--")):
            p = 20 * np.log10(array_factor(fi, L, a_n, th, port) + 1e-12)
            ax.plot(th, p, ls, color=c, lw=1.1, label=f"{fi / 1e9:g} GHz, port {port}")
    ax.set_ylim(-40, 2)
    ax.set_xlim(0, 180)
    ax.set_xlabel("angle from array axis (deg)")
    ax.set_ylabel("normalised AF (dB)")
    ax.grid(alpha=.3)
    ax.legend(fontsize=6.5, ncol=4, loc="lower center")
    ax.set_title("Array factor, 16 slots, 20-dB Dolph-Chebyshev (compare paper Fig. 9)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_patterns.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    for port, mk in ((1, "o"), (2, "s")):
        rr = [r for r in traj if r[1] == port]
        ax.errorbar([r[2] for r in rr], [r[0] for r in rr], xerr=[r[3] / 2 for r in rr], fmt=mk, ms=3,
                    color="C3" if port == 1 else "C4", ecolor="pink", elinewidth=4, label=f"port {port}")
    ax.set_xlabel("beam angle (deg)")
    ax.set_ylabel("frequency (GHz)")
    ax.grid(alpha=.3)
    ax.legend(fontsize=7)
    ax.set_title("Frequency–angle map ±HPBW/2 (paper Fig. 12)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_freq_angle.png"))
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    idx = np.arange(1, N + 1)
    ax[0].bar(idx - 0.2, a_n, 0.4, label="computed chebwin(16, 20 dB)")
    ax[0].bar(idx + 0.2, [r[0] for r in t1], 0.4, label="paper Table I")
    ax[0].set_xlabel("slot n")
    ax[0].set_ylabel("excitation a_n")
    ax[0].legend(fontsize=7)
    ax[0].set_title("Amplitude taper")
    ax[1].plot(idx, [r[0] for r in t2], "o-", label="tilt θ_adj (deg), Table II")
    ax[1].plot(idx, tilt_adj, "x--", label="tilt from eq. 17 × 1.5")
    ax2 = ax[1].twinx()
    ax2.plot(idx, [r[1] for r in t2], "s-", color="C2", label="depth d_adj (mm)")
    ax[1].set_xlabel("slot n")
    ax[1].set_ylabel("tilt (deg)")
    ax2.set_ylabel("slot depth (mm)")
    ax[1].legend(fontsize=7, loc="upper left")
    ax2.legend(fontsize=7, loc="upper right")
    ax[1].set_title("Slot geometry along the antenna")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_slot_params.png"))
    plt.close(fig)

    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
