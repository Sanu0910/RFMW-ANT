#!/usr/bin/env python3
"""
render.py  --  "MVDR Beamforming, explained" : a ~2 minute 1080p explainer.

Every beam pattern, null, covariance matrix and SINR figure shown in the video
is computed live by mvdr_core.py, so the animation *is* the algorithm running.

    python3 render.py --selftest     # numbers only, no video
    python3 render.py --preview      # contact sheet of key frames -> preview.png
    python3 render.py                # full MP4  -> mvdr_explainer.mp4
    python3 render.py --fps 24 --range 60,80   # quick partial render for tuning
"""
import os, sys, math, time, subprocess, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, FancyArrowPatch
from matplotlib.collections import LineCollection

import mvdr_core as mv

# ------------------------------------------------------------------ config ----
W, H, DPI = 1920, 1080, 100
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))

BG    = "#0b1020"   # deep navy background
PANEL = "#141d38"   # panel / card fill
FG    = "#eef2fb"   # primary text
MUT   = "#93a1c4"   # muted text
GRID  = "#26324f"
CYAN  = "#39d8f0"   # array / beam / weights
GREEN = "#37d67a"   # desired satellite
RED   = "#ff5c5c"   # jammer
AMBER = "#ffb23a"   # spoofer
VIO   = "#b09bff"   # accents / math

plt.rcParams.update({
    "figure.facecolor": BG, "savefig.facecolor": BG,
    "font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans",
    "text.color": FG, "axes.edgecolor": GRID, "axes.labelcolor": MUT,
    "xtick.color": MUT, "ytick.color": MUT,
})

FIG = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)

# ---------------------------------------------------------------- easings -----
def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eo(t):  t = clamp(t); return 1 - (1 - t) ** 3
def ei(t):  t = clamp(t); return t ** 3
def eio(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def eob(t, s=1.70):
    t = clamp(t); return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def fade(t, D, fin=0.6, fout=0.5):
    return eo(seg(t, 0, fin)) * (1 - eo(seg(t, D - fout, D)))

# -------------------------------------------------------------- primitives ----
def base():
    """Reset the figure and return a full-frame background axis (16 x 9 units)."""
    FIG.clf()
    ax = FIG.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(0, 9)
    ax.axis("off"); ax.set_facecolor(BG)
    ax.add_patch(Rectangle((0, 0), 16, 9, color=BG, zorder=-10))
    return ax

def T(ax, x, y, s, size=20, color=FG, weight="normal", alpha=1.0,
      ha="center", va="center", family=None, style="normal", zorder=5):
    return ax.text(x, y, s, fontsize=size, color=color, weight=weight, alpha=clamp(alpha),
                   ha=ha, va=va, family=family, style=style, zorder=zorder)

def chip(ax, x, y, w, h, color, alpha=1.0, lw=0, ec="none", z=2, rounding=0.12):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle=f"round,pad=0.02,rounding_size={rounding}",
                       fc=color, ec=ec, lw=lw, alpha=clamp(alpha), zorder=z,
                       mutation_aspect=1)
    ax.add_patch(p); return p

def kicker(ax, x, y, text, color, a=1.0, size=17):
    """Small colored section label."""
    T(ax, x, y, text, size=size, color=color, weight="bold", alpha=a, ha="left")
    ax.plot([x, x + 0.02], [y - 0.28, y - 0.28], color=color, lw=0, alpha=a)

# ------------------------------------------------------- array + wavefronts ---
def draw_array(ax, x0=4.5, x1=11.5, y=1.9, a=1.0, hl=None, size=0.32, labels=False):
    xs = np.linspace(x0, x1, mv.M)
    for i, xe in enumerate(xs):
        col = AMBER if (hl is not None and i == hl) else CYAN
        ax.add_patch(FancyBboxPatch((xe - size, y - size), 2 * size, 2 * size,
                     boxstyle="round,pad=0.01,rounding_size=0.08",
                     fc=col, ec="none", alpha=0.92 * a, zorder=4))
        ax.add_patch(Circle((xe, y), size * 0.32, fc=BG, ec="none", alpha=a, zorder=5))
        if labels:
            T(ax, xe, y - 0.75, f"{i}", size=13, color=MUT, alpha=a)
    return xs

def wavefronts(ax, xs, y_arr, theta_deg, t, a=1.0, n=7, L=3.4, col=CYAN, speed=1.6,
               cy_ref=None, cap=None, arrow=2.2):
    """Animated plane-wave crests arriving from `theta_deg` (0 = broadside/up)."""
    th = math.radians(theta_deg)
    u = np.array([math.sin(th), math.cos(th)])     # propagation (toward array = -u)
    v = np.array([math.cos(th), -math.sin(th)])    # along the crest
    cx = np.array([xs.mean(), (y_arr + 2.6) if cy_ref is None else cy_ref])
    segs, alphas = [], []
    for k in range(n):
        c = (k * 1.05 + (t * speed) % 1.05) - 1.0
        P = cx + (c * 1.05 + 1.2) * u
        if cap is not None and P[1] > cap:          # keep crests out of the text band
            continue
        p1, p2 = P - L * v, P + L * v
        segs.append([p1, p2]); alphas.append(clamp(1 - k / n) * 0.55 * a)
    lc = LineCollection(segs, colors=[(*_hex(col), al) for al in alphas], linewidths=2.2, zorder=3)
    ax.add_collection(lc)
    # arrival arrow
    tip = cx - 0.3 * u; tail = cx + arrow * u
    ax.add_patch(FancyArrowPatch(tail, tip, arrowstyle="-|>", mutation_scale=16,
                 color=col, alpha=0.8 * a, lw=2, zorder=3))

def _hex(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def polar_pattern(rect, g_db, floor=-60, a=1.0, title=None):
    """Draw a real dB beam pattern in a polar inset (rect in figure fraction)."""
    axp = FIG.add_axes(rect, projection="polar"); axp.set_facecolor(PANEL)
    axp.patch.set_alpha(0.0)
    th = np.radians(mv.THETA_GRID)
    r = np.clip(g_db, floor, 5) - floor
    axp.plot(th, r, color=CYAN, lw=2.4, alpha=a)
    axp.fill(th, r, color=CYAN, alpha=0.10 * a)
    axp.set_theta_zero_location("N"); axp.set_theta_direction(-1)
    axp.set_thetamin(-90); axp.set_thetamax(90)
    axp.set_rlim(0, 5 - floor); axp.set_rticks([])
    axp.set_thetagrids([-90, -45, 0, 45, 90],
                       labels=["-90", "-45", "0", "45", "90"], fontsize=10, color=MUT)
    axp.grid(color=GRID, alpha=0.6 * a)
    for ang, col in [(mv.DESIRED_DEG, GREEN)] + [(j, RED) for j in mv.JAMMERS_DEG] + [(mv.SPOOFER_DEG, AMBER)]:
        axp.plot([math.radians(ang)] * 2, [0, 5 - floor], color=col, lw=1.4, alpha=0.5 * a, ls=":")
    for s in axp.spines.values(): s.set_alpha(a * 0.5)
    if title:
        axp.set_title(title, color=MUT, fontsize=12, alpha=a, pad=8)
    return axp

# ================================================================ SCENES ======
def sc_title(ax, t, D):
    a = fade(t, D)
    # subtle array + beam motif
    xs = np.linspace(6.4, 9.6, mv.M); ya = 2.0
    ap = eo(seg(t, 0.2, 1.3))
    for xe in xs:
        ax.add_patch(Circle((xe, ya), 0.11, fc=CYAN, ec="none", alpha=0.9 * ap * a, zorder=4))
    sweep = lerp(-38, 38, (math.sin(t * 0.9) * 0.5 + 0.5))
    R = mv.scene_covariance(); w = mv.mvdr_weights(R); g = mv.beam_pattern_db(w)
    th = np.radians(mv.THETA_GRID); rr = (np.clip(g, -55, 5) + 55) / 60 * 2.7
    bx = 8 + rr * np.sin(th); by = ya + rr * np.cos(th)
    ax.plot(bx, by, color=CYAN, lw=2, alpha=0.35 * ap * a, zorder=3)
    ax.add_patch(FancyArrowPatch((8, ya), (8 + 2.9 * math.sin(math.radians(sweep)), ya + 2.9 * math.cos(math.radians(sweep))),
                 arrowstyle="-|>", mutation_scale=16, color=CYAN, alpha=0.5 * ap * a, lw=2, zorder=3))
    # titles
    s1 = eob(seg(t, 0.15, 1.1))
    T(ax, 8, 6.5, "MVDR Beamforming", size=64 * (0.8 + 0.2 * s1), color=FG, weight="bold", alpha=a)
    T(ax, 8, 5.5, "Minimum Variance Distortionless Response  ·  Capon's adaptive beamformer",
      size=23, color=CYAN, alpha=eo(seg(t, 0.5, 1.4)) * a)
    T(ax, 8, 4.55, "How it works — steering, nulling, the maths, and the inputs",
      size=20, color=MUT, alpha=eo(seg(t, 0.9, 1.8)) * a)
    ab = eo(seg(t, 1.5, 2.6))
    for i, (txt, c) in enumerate([("ANTI-JAMMING", RED), ("ANTI-SPOOFING", AMBER), ("GNSS / RF ARRAYS", CYAN)]):
        x = 4.9 + i * 3.1
        chip(ax, x, 3.55, 2.7, 0.55, PANEL, alpha=ab * a, ec=c, lw=1.5)
        T(ax, x, 3.55, txt, size=16, color=c, weight="bold", alpha=ab * a)

def _sky_pos(ang, cx=8.0, cy=1.45, R=5.05):
    th = math.radians(ang); return cx + R * math.sin(th), cy + R * math.cos(th)

def _satellite(ax, x, y, col, a, scale=1.0, fake=False):
    ls = (0, (3, 2)) if fake else "solid"
    s = 0.34 * scale
    ax.add_patch(Rectangle((x - s * 0.6, y - s * 0.6), s * 1.2, s * 1.2, fc="none" if fake else col,
                 ec=col, lw=2, ls=ls, alpha=a, zorder=6))
    for sgn in (-1, 1):
        ax.add_patch(Rectangle((x + sgn * s * 1.55 - s * 0.55, y - s * 0.75), s * 1.1, s * 1.5,
                     fc="none" if fake else col, ec=col, lw=1.6, ls=ls, alpha=a * 0.9, zorder=6))
        ax.plot([x + sgn * s * 0.6, x + sgn * s], [y, y], color=col, lw=1.4, alpha=a, zorder=6)

def _burst(ax, x, y, col, a, scale=1.0):
    pts = []
    for k in range(16):
        ang = math.pi * k / 8
        r = (0.55 if k % 2 == 0 else 0.24) * scale
        pts.append((x + r * math.cos(ang), y + r * math.sin(ang)))
    ax.add_patch(Polygon(pts, closed=True, fc=col, ec="none", alpha=0.85 * a, zorder=6))

def sc_scenario(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE PROBLEM", CYAN, a)
    T(ax, 1.0, 7.75, "Signals pour into the array from many directions at once.",
      size=25, color=FG, weight="bold", alpha=a, ha="left")
    T(ax, 1.0, 7.2, "The satellite we actually want is by far the weakest of them.",
      size=19, color=MUT, alpha=eo(seg(t, 0.4, 1.2)) * a, ha="left")
    # ground + array
    cx, cy = 8.0, 1.35
    ax.plot([1.5, 14.5], [cy - 0.25, cy - 0.25], color=GRID, lw=2, alpha=a)
    xs = draw_array(ax, 6.7, 9.3, cy + 0.1, a=a, size=0.24)
    sources = [
        (mv.DESIRED_DEG, GREEN, "SATELLITE", "desired · weak", _satellite, 0.35),
        (mv.JAMMERS_DEG[0], RED, "JAMMER", "+40 dB", _burst, 0.55),
        (mv.JAMMERS_DEG[1], RED, "JAMMER", "+40 dB", _burst, 0.75),
        (mv.SPOOFER_DEG, AMBER, "SPOOFER", "counterfeit sat", _satellite, 0.95),
    ]
    for ang, col, name, sub, icon, delay in sources:
        av = eo(seg(t, 0.6 + delay, 1.5 + delay)) * a
        if av <= 0: continue
        sx, sy = _sky_pos(ang)
        # ray
        ax.plot([sx, cx], [sy, cy + 0.1], color=col, lw=1.6, alpha=0.32 * av, zorder=2)
        # travelling pulse
        pp = (t * 0.8 + delay) % 1.0
        px, py = lerp(sx, cx, pp), lerp(sy, cy + 0.1, pp)
        ax.add_patch(Circle((px, py), 0.07, fc=col, ec="none", alpha=0.8 * av, zorder=3))
        if icon is _satellite:
            _satellite(ax, sx, sy, col, av, fake=(name == "SPOOFER"))
        else:
            _burst(ax, sx, sy, col, av)
        T(ax, sx, sy - 0.72, name, size=15, color=col, weight="bold", alpha=av)
        T(ax, sx, sy - 1.05, sub, size=12.5, color=MUT, alpha=av)
    T(ax, cx, cy - 0.7, "M-element array", size=14, color=CYAN, alpha=a)

def sc_input(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE INPUT", CYAN, a)
    T(ax, 1.0, 7.75, "A snapshot: one complex sample from every element at time t.",
      size=25, color=FG, weight="bold", alpha=a, ha="left")
    ya = 2.6
    xs = draw_array(ax, 4.2, 11.8, ya, a=a, labels=True)
    theta = lerp(-8, 34, eio(seg(t, 0.2, 0.9)))
    wavefronts(ax, xs, ya, theta, t, a=a)
    # path-difference wedge on last elements
    av = eo(seg(t, 1.0, 1.8)) * a
    if av > 0:
        th = math.radians(theta)
        for i in (mv.M - 2, mv.M - 1):
            xe = xs[i]
            ax.plot([xe, xe - 0.9 * math.sin(th)], [ya, ya + 0.9 * math.cos(th)],
                    color=AMBER, lw=1.4, ls=":", alpha=0.7 * av)
        T(ax, xs[-1] + 0.2, ya + 1.1, r"extra path $=\, n\,d\,\sin\theta$",
          size=15, color=AMBER, alpha=av, ha="left")
    # the input vector
    av2 = eo(seg(t, 1.3, 2.2)) * a
    chip(ax, 8, 0.95, 12.2, 1.1, PANEL, alpha=0.9 * av2, ec=GRID, lw=1)
    T(ax, 8, 1.12, r"$\mathbf{x}(t)=[\,x_1(t),\ x_2(t),\ \dots,\ x_M(t)\,]^{\mathsf{T}}"
      r"=\mathbf{a}(\theta)\,s(t)+\ \mathrm{interference}\ +\ \mathbf{n}(t)$",
      size=22, color=FG, alpha=av2)
    T(ax, 8, 0.55, "the array's raw data — M numbers per time sample — is all MVDR ever sees",
      size=14.5, color=MUT, alpha=av2)

def sc_steer(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE STEERING VECTOR", CYAN, a)
    T(ax, 1.0, 7.75, "a(θ) is the phase ramp a plane wave from θ stamps across the array.",
      size=24, color=FG, weight="bold", alpha=a, ha="left")
    T(ax, 1.0, 7.25, "It is the array's fingerprint for direction θ — the only thing we must know about the target.",
      size=17, color=MUT, alpha=eo(seg(t, 0.4, 1.2)) * a, ha="left")
    ya = 4.7
    xs = draw_array(ax, 3.4, 12.6, ya, a=a, size=0.28)
    theta = lerp(0, 32, math.sin(seg(t, 0.2, 1.0) * math.pi / 2)) if t < D * 0.55 else \
            lerp(32, -22, eio(seg(t, D * 0.55, D * 0.95)))
    psi = math.pi * mv.D_SPACING / 0.5 * math.sin(math.radians(theta))  # = pi*sin(theta)
    wavefronts(ax, xs, ya, theta, t, a=a * 0.72, n=8, L=1.9, cy_ref=ya + 0.3, cap=5.8, arrow=1.1)
    # phasor dials under each element
    for n, xe in enumerate(xs):
        ph = n * psi
        cyl = ya - 1.35
        ax.add_patch(Circle((xe, cyl), 0.36, fc=PANEL, ec=GRID, lw=1.2, alpha=a, zorder=4))
        ax.add_patch(FancyArrowPatch((xe, cyl), (xe + 0.30 * math.cos(ph), cyl + 0.30 * math.sin(ph)),
                     arrowstyle="-|>", mutation_scale=10, color=VIO, lw=2, alpha=a, zorder=5))
        T(ax, xe, cyl - 0.62, (r"$1$" if n == 0 else rf"$e^{{j{n}\psi}}$"),
          size=13, color=VIO, alpha=a)
    T(ax, 8, ya + 1.85, rf"$\theta = {theta:+.0f}^\circ$", size=20, color=CYAN, alpha=a)
    av = eo(seg(t, 0.6, 1.4)) * a
    chip(ax, 8, 1.5, 13.0, 1.5, PANEL, alpha=0.9 * av, ec=GRID, lw=1)
    T(ax, 8, 1.85, r"$\mathbf{a}(\theta)=\left[\,1,\ e^{j\psi},\ e^{j2\psi},\ \dots,\ e^{j(M-1)\psi}\,\right]^{\mathsf{T}}$",
      size=25, color=FG, alpha=av)
    T(ax, 8, 1.05, r"$\psi=2\pi\,\dfrac{d}{\lambda}\,\sin\theta$"
      r"$\qquad$ each element lags its neighbour by the same phase step $\psi$",
      size=18, color=MUT, alpha=av)

def sc_cov(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE COVARIANCE MATRIX", CYAN, a)
    T(ax, 1.0, 7.75, "R = E[ x xᴴ ] — how the elements' signals correlate.",
      size=25, color=FG, weight="bold", alpha=a, ha="left")
    T(ax, 1.0, 7.2, "In practice we average snapshots:  R̂ = (1/N) Σ x xᴴ.  Strong jammers dominate it.",
      size=18, color=MUT, alpha=eo(seg(t, 0.4, 1.2)) * a, ha="left")
    # growing sample covariance heatmap (left)
    N = int(lerp(4, 4000, ei(seg(t, 0.3, 1.0))) if t < D * 0.8 else 4000)
    R = mv.sample_covariance(N, rng=np.random.default_rng(3))
    axm = FIG.add_axes([0.08, 0.14, 0.40, 0.46]); axm.set_facecolor(PANEL)
    Rlog = 10 * np.log10(np.abs(R) + 1e-3)
    im = axm.imshow(Rlog, cmap="magma", vmin=-10, vmax=45, alpha=a)
    axm.set_xticks(range(mv.M)); axm.set_yticks(range(mv.M))
    axm.set_xticklabels(range(mv.M), fontsize=9); axm.set_yticklabels(range(mv.M), fontsize=9)
    axm.set_title(f"|R|  (dB)   —   N = {N} snapshots", color=MUT, fontsize=13, alpha=a)
    for s in axm.spines.values(): s.set_color(GRID)
    cb = FIG.colorbar(im, ax=axm, fraction=0.046, pad=0.04)
    cb.ax.tick_params(labelsize=8, color=GRID); cb.outline.set_edgecolor(GRID)
    cb.set_alpha(a); cb.ax.set_alpha(a)
    # eigen-story (right)
    av = eo(seg(t, 0.9, 1.8)) * a
    ev = np.sort(np.linalg.eigvalsh(mv.scene_covariance()).real)[::-1]
    axb = FIG.add_axes([0.58, 0.16, 0.36, 0.40]); axb.set_facecolor("none")
    cols = [RED, RED, AMBER] + [MUT] * (mv.M - 3)
    axb.bar(range(mv.M), 10 * np.log10(ev), color=cols, alpha=av, width=0.62)
    axb.set_ylim(-3, 48); axb.set_xticks(range(mv.M))
    axb.set_ylabel("eigenvalue power (dB)", fontsize=12, color=MUT)
    axb.set_title("eigenvalues of R", color=MUT, fontsize=13, alpha=av)
    axb.tick_params(labelsize=9)
    for s in axb.spines.values(): s.set_color(GRID)
    axb.spines["top"].set_visible(False); axb.spines["right"].set_visible(False)
    axb.grid(axis="y", color=GRID, alpha=0.4 * av)
    T(ax, 12.1, 6.55, "few huge eigenvalues\n= the jammers/spoofer", size=15, color=RED, alpha=av)
    T(ax, 13.7, 2.5, "small ones\n= noise floor", size=13.5, color=MUT, alpha=av)

def sc_opt(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE OPTIMISATION", CYAN, a)
    T(ax, 1.0, 7.75, "Choose the weights w that combine the elements:  y(t) = wᴴ x(t).",
      size=24, color=FG, weight="bold", alpha=a, ha="left")
    # the two-line program
    av = eo(seg(t, 0.3, 1.1)) * a
    chip(ax, 8, 5.6, 12.5, 1.35, PANEL, alpha=0.9 * av, ec=GREEN, lw=1.4)
    T(ax, 8, 5.95, r"$\min_{\mathbf{w}}\ \ \mathbf{w}^{H}\mathbf{R}\,\mathbf{w}$"
      r"$\qquad\mathrm{subject\ to}\qquad \mathbf{w}^{H}\mathbf{a}(\theta_d)=1$",
      size=30, color=FG, alpha=av)
    T(ax, 4.6, 5.25, "minimum variance", size=16, color=RED, weight="bold", alpha=av)
    T(ax, 11.0, 5.25, "distortionless", size=16, color=GREEN, weight="bold", alpha=av)
    # explanations
    a1 = eo(seg(t, 0.9, 1.7)) * a
    chip(ax, 4.3, 3.1, 6.0, 2.2, "#1a1330", alpha=0.85 * a1, ec=RED, lw=1.2)
    T(ax, 4.3, 3.95, "MINIMUM VARIANCE", size=17, color=RED, weight="bold", alpha=a1)
    T(ax, 4.3, 3.25, "wᴴRw is the total output power.\nDriving it down starves every\nstrong signal — i.e. the jammers.",
      size=15.5, color=FG, alpha=a1)
    a2 = eo(seg(t, 1.2, 2.0)) * a
    chip(ax, 11.7, 3.1, 6.0, 2.2, "#0f2318", alpha=0.85 * a2, ec=GREEN, lw=1.2)
    T(ax, 11.7, 3.95, "DISTORTIONLESS", size=17, color=GREEN, weight="bold", alpha=a2)
    T(ax, 11.7, 3.25, "wᴴa(θd) = 1 pins unit gain on\nthe satellite, so it passes through\nuntouched while power is minimised.",
      size=15.5, color=FG, alpha=a2)
    a3 = eo(seg(t, 1.6, 2.4)) * a
    T(ax, 8, 1.15, r"Lagrangian:  $\mathcal{L}=\mathbf{w}^{H}\mathbf{R}\mathbf{w}-\lambda\,(\mathbf{w}^{H}\mathbf{a}(\theta_d)-1)$"
      r"$\;\Rightarrow\;$ solve $\partial\mathcal{L}/\partial\mathbf{w}=0$",
      size=19, color=VIO, alpha=a3)

def sc_weights(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.3, "THE MVDR WEIGHTS", CYAN, a)
    T(ax, 1.0, 7.75, "Solving the constrained problem gives one clean closed form:",
      size=24, color=FG, weight="bold", alpha=a, ha="left")
    s1 = eob(seg(t, 0.25, 1.2))
    chip(ax, 8, 5.2, 11.5, 2.2, PANEL, alpha=a, ec=CYAN, lw=1.6)
    T(ax, 8, 5.2, r"$\mathbf{w}_{\mathrm{MVDR}}=\dfrac{\mathbf{R}^{-1}\,\mathbf{a}(\theta_d)}"
      r"{\mathbf{a}^{H}(\theta_d)\,\mathbf{R}^{-1}\,\mathbf{a}(\theta_d)}$",
      size=44 * (0.85 + 0.15 * s1), color=FG, alpha=a)
    av = eo(seg(t, 1.0, 1.9)) * a
    T(ax, 4.6, 2.85, "R⁻¹  whitens the interference —\nit rotates the strong jammer\ndirections down to nothing.",
      size=16, color=RED, alpha=av)
    T(ax, 11.4, 2.85, "the denominator is just a scale\nfactor that re-imposes unit gain\non the look direction θd.",
      size=16, color=GREEN, alpha=av)
    T(ax, 8, 1.1, "Only two ingredients:  the covariance R (from the data)  and  the steering vector a(θd) (the target bearing).",
      size=16.5, color=MUT, alpha=eo(seg(t, 1.4, 2.2)) * a)

def sc_beam(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.4, "STEERING  +  NULLING", CYAN, a)
    # diagonal-loading sweep: huge load (=> uniform phased array) -> 0 (=> full MVDR)
    tau = eio(seg(t, 0.18, 0.62))
    load = 10 ** lerp(6.0, -3.0, tau)
    R = mv.scene_covariance(diag_load=load)
    w = mv.mvdr_weights(R); g = mv.beam_pattern_db(w)
    axp = FIG.add_axes([0.07, 0.12, 0.60, 0.66]); axp.set_facecolor("none")
    axp.plot(mv.THETA_GRID, g, color=CYAN, lw=2.6, alpha=a)
    axp.fill_between(mv.THETA_GRID, -70, g, color=CYAN, alpha=0.08 * a)
    axp.set_xlim(-90, 90); axp.set_ylim(-70, 6)
    axp.set_xticks(range(-90, 91, 30))
    axp.set_xlabel("arrival angle  θ  (degrees)", fontsize=15, color=MUT)
    axp.set_ylabel("array gain (dB)", fontsize=15, color=MUT)
    axp.tick_params(labelsize=11)
    axp.grid(color=GRID, alpha=0.5 * a)
    for s in axp.spines.values(): s.set_color(GRID)
    axp.spines["top"].set_visible(False); axp.spines["right"].set_visible(False)
    for ang, col, nm in [(mv.DESIRED_DEG, GREEN, "satellite")] + \
                        [(j, RED, "jammer") for j in mv.JAMMERS_DEG] + [(mv.SPOOFER_DEG, AMBER, "spoofer")]:
        axp.axvline(ang, color=col, lw=1.3, ls=":", alpha=0.55 * a)
        gd = g[np.argmin(np.abs(mv.THETA_GRID - ang))]
        axp.plot([ang], [gd], "o", color=col, ms=8, alpha=a)
        axp.annotate(nm, (ang, gd), (ang, gd - 5 if col != GREEN else gd + 3),
                     color=col, fontsize=12, ha="center", alpha=a)
    # polar mirror appears in the hold phase
    ah = eo(seg(t, 0.66, 0.9)) * a
    if ah > 0.02:
        polar_pattern([0.70, 0.16, 0.27, 0.52], g, a=ah, title="same pattern, polar")
    # captions
    if tau < 0.5:
        cap = "Conventional phased array:  one fat beam, high sidelobes, no idea where the jammers are."
        ccol = MUT
    else:
        cap = "MVDR adaptive:  unit gain stays on the satellite while deep nulls dig in on every interferer."
        ccol = GREEN
    T(ax, 8.0, 7.75, cap, size=18.5, color=ccol, weight="bold", alpha=a)
    null_depth = g[np.argmin(np.abs(mv.THETA_GRID - mv.JAMMERS_DEG[0]))]
    T(ax, 4.7, 0.55, f"jammer null depth:  {null_depth:6.0f} dB     "
                     f"satellite gain:  {g[np.argmin(np.abs(mv.THETA_GRID-mv.DESIRED_DEG))]:+.1f} dB",
      size=16, color=FG, alpha=eo(seg(t, 0.55, 0.8)) * a, ha="center", family="DejaVu Sans Mono")

def sc_defend(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.4, "WHY IT BEATS JAMMING & SPOOFING", CYAN, a)
    # anti-jam card
    a1 = eo(seg(t, 0.2, 1.0)) * a
    chip(ax, 4.3, 5.6, 6.6, 3.0, "#1a1330", alpha=0.9 * a1, ec=RED, lw=1.4)
    T(ax, 4.3, 6.75, "ANTI-JAMMING", size=22, color=RED, weight="bold", alpha=a1)
    T(ax, 4.3, 5.55,
      "A jammer is 10³–10⁵× stronger than\nthe satellite, so it dominates R.\n\n"
      "MVDR spends the array's degrees of\nfreedom sinking a −60 dB null right\n"
      "on its bearing — the CRPA principle\nin every protected GNSS receiver.",
      size=15.5, color=FG, alpha=a1)
    # anti-spoof card
    a2 = eo(seg(t, 0.6, 1.4)) * a
    chip(ax, 11.7, 5.6, 6.6, 3.0, "#2a2008", alpha=0.9 * a2, ec=AMBER, lw=1.4)
    T(ax, 11.7, 6.75, "ANTI-SPOOFING", size=22, color=AMBER, weight="bold", alpha=a2)
    T(ax, 11.7, 5.55,
      "A spoofer fakes the whole constellation\nfrom ONE antenna — so every counterfeit\n"
      "PRN shares a single direction of arrival.\n\n"
      "Real satellites are spread across the sky.\n"
      "MVDR sees the lie in the spatial data and\nnulls that rogue bearing out.",
      size=15.5, color=FG, alpha=a2)
    # SINR payoff
    a3 = eo(seg(t, 1.2, 2.0)) * a
    wc = mv.conventional_weights(); wm = mv.mvdr_weights(mv.scene_covariance())
    s_conv, s_mvdr = mv.output_sinr_db(wc), mv.output_sinr_db(wm)
    grow = eio(seg(t, 1.3, 2.4))
    cur = lerp(s_conv, s_mvdr, grow)
    T(ax, 8.0, 3.35, f"SINR:  {s_conv:+.1f} dB   →   {cur:+.1f} dB      "
                     f"( +{s_mvdr - s_conv:.0f} dB recovered )",
      size=20, color=GREEN, weight="bold", alpha=a3)
    axb = FIG.add_axes([0.32, 0.11, 0.36, 0.15]); axb.set_facecolor("none")
    axb.barh([0], [s_conv], color=MUT, alpha=a3, height=0.55)
    axb.barh([1], [cur], color=GREEN, alpha=a3, height=0.55)
    axb.set_yticks([0, 1]); axb.set_yticklabels(["conventional", "MVDR"], fontsize=13)
    axb.set_xlim(-18, 14); axb.axvline(0, color=GRID, lw=1)
    axb.set_xlabel("output SINR (dB)", fontsize=12, color=MUT)
    for s in axb.spines.values(): s.set_visible(False)
    axb.tick_params(labelsize=10)

def sc_recap(ax, t, D):
    a = fade(t, D)
    kicker(ax, 1.0, 8.4, "THE WHOLE PIPELINE", CYAN, a)
    steps = [
        (r"$\mathbf{x}(t)$", "snapshots\nfrom M elements", CYAN),
        (r"$\hat{\mathbf{R}}=\frac{1}{N}\sum \mathbf{x}\mathbf{x}^{H}$", "estimate the\ncovariance", VIO),
        (r"$\mathbf{w}=\dfrac{\mathbf{R}^{-1}\mathbf{a}(\theta_d)}{\mathbf{a}^{H}\mathbf{R}^{-1}\mathbf{a}(\theta_d)}$",
         "MVDR weights", GREEN),
        (r"$y=\mathbf{w}^{H}\mathbf{x}$", "steer θd  ·  null\nthe rest", AMBER),
    ]
    xs = [2.6, 6.4, 10.2, 13.7]
    for i, (eq, lab, col) in enumerate(steps):
        av = eo(seg(t, 0.2 + i * 0.28, 1.0 + i * 0.28)) * a
        chip(ax, xs[i], 5.2, 3.2, 2.2, PANEL, alpha=0.95 * av, ec=col, lw=1.6)
        T(ax, xs[i], 5.55, eq, size=21, color=FG, alpha=av)
        T(ax, xs[i], 4.4, lab, size=14.5, color=col, alpha=av)
        if i < 3:
            aw = eo(seg(t, 0.45 + i * 0.28, 1.0 + i * 0.28)) * a
            ax.add_patch(FancyArrowPatch((xs[i] + 1.7, 5.2), (xs[i + 1] - 1.7, 5.2),
                         arrowstyle="-|>", mutation_scale=18, color=MUT, lw=2, alpha=aw))
    af = eo(seg(t, 1.5, 2.4)) * a
    T(ax, 8, 2.6, "MVDR keeps the wanted direction distortionless,",
      size=23, color=FG, weight="bold", alpha=af)
    T(ax, 8, 2.0, "and spends every remaining degree of freedom killing interference.",
      size=23, color=CYAN, weight="bold", alpha=af)
    T(ax, 8, 0.85, "RFMW-ANT  ·  MVDR adaptive beamforming for anti-jam / anti-spoof arrays",
      size=15, color=MUT, alpha=eo(seg(t, 1.9, 2.7)) * a)

# ============================================================== timeline ======
SCENES = [
    ("title",    6.0, sc_title),
    ("scenario", 13.0, sc_scenario),
    ("input",    14.0, sc_input),
    ("steer",    15.0, sc_steer),
    ("cov",      13.0, sc_cov),
    ("opt",      15.0, sc_opt),
    ("weights",  10.0, sc_weights),
    ("beam",     21.0, sc_beam),
    ("defend",   15.0, sc_defend),
    ("recap",    11.0, sc_recap),
]
STARTS, _acc = [], 0.0
for _n, _d, _f in SCENES:
    STARTS.append(_acc); _acc += _d
TOTAL = _acc

def frame_at(t):
    for (name, d, fn), t0 in zip(SCENES, STARTS):
        if t < t0 + d - 1e-9:
            ax = base(); fn(ax, t - t0, d); break
    else:
        name, d, fn = SCENES[-1]; ax = base(); fn(ax, d - 1e-4, d)
    FIG.canvas.draw()
    buf = np.asarray(FIG.canvas.buffer_rgba())[:, :, :3]
    if buf.shape[:2] != (H, W):
        import cv2  # pragma: no cover
        buf = cv2.resize(buf, (W, H))
    return np.ascontiguousarray(buf)

# ================================================================= main =======
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--range", type=str, default=None, help="start,end seconds")
    ap.add_argument("--out", type=str, default=os.path.join(HERE, "mvdr_explainer.mp4"))
    args = ap.parse_args()

    print(f"timeline {TOTAL:.0f}s :", ", ".join(f"{n}={d:.0f}s" for n, d, _ in SCENES), flush=True)

    if args.preview:
        keys = [1.5, 9, 19, 27, 34, 42, 50, 57, 66, 78, 88, 100, 112, 121, 128, 132]
        tiles = []
        for k in keys:
            fr = frame_at(min(k, TOTAL - 0.05))
            import matplotlib.image as mpimg
            small = fr[::4, ::4]
            tiles.append(small)
        rows = [np.hstack(tiles[i:i + 4]) for i in range(0, 16, 4)]
        grid = np.vstack(rows)
        plt.imsave(os.path.join(HERE, "preview.png"), grid)
        print("wrote preview.png", flush=True); return

    fps = args.fps
    t0, t1 = (0.0, TOTAL)
    if args.range:
        t0, t1 = [float(x) for x in args.range.split(",")]
    n0, n1 = int(t0 * fps), int(t1 * fps)

    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.2", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", args.out]
    # NOTE: ffmpeg's stderr goes to a file, never a PIPE. A PIPE that we don't
    # drain during the frame loop fills its ~64 KB OS buffer, blocks ffmpeg, and
    # deadlocks against our stdin.write() — which is exactly what bit an earlier run.
    ff_log_path = os.path.join(HERE, "ffmpeg.log")
    ff_log = open(ff_log_path, "wb")
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=ff_log)
    st = time.time(); NF = n1 - n0
    for i in range(n0, n1):
        pr.stdin.write(frame_at(i / fps).tobytes())
        if (i - n0) % 60 == 0:
            el = time.time() - st; done = i - n0 + 1
            eta = el / done * (NF - done)
            print(f"  {done}/{NF}  {el:.0f}s  eta {eta:.0f}s", flush=True)
    pr.stdin.close(); rc = pr.wait(); ff_log.close()
    if rc != 0:
        with open(ff_log_path) as fh:
            print(fh.read()[-2500:])
    print(f"done rc={rc}  {time.time()-st:.0f}s  -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
