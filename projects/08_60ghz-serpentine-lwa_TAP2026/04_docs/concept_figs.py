#!/usr/bin/env python3
"""Explanatory figures for the brief (matplotlib): LWA principle, serpentine trick, FMCW range+angle."""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle, Wedge  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 9, "figure.dpi": 160})


def lwa_principle():
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.add_patch(Rectangle((0, 0), 10, 0.6, fc="#cfd6de", ec="#1f3a5f", lw=1.2))
    for i in range(10):
        x = 0.6 + i * 0.95
        ang = 25 if i % 2 == 0 else -25
        ax.plot([x - 0.18 * np.cos(np.radians(ang)), x + 0.18 * np.cos(np.radians(ang))],
                [0.6 - 0.18 * np.sin(np.radians(ang)) * 0 + 0.0, 0.6 + 0.0], color="k", lw=0)
        ax.add_patch(Rectangle((x - 0.17, 0.55), 0.34, 0.1, angle=ang, rotation_point="center", fc="k"))
    ax.annotate("", xy=(10.8, 0.3), xytext=(-0.9, 0.3), arrowprops=dict(arrowstyle="->", lw=1.5, color="#e76f51"))
    ax.text(-0.9, -0.25, "wave in (port 1)", color="#e76f51", fontsize=8)
    cols = {"58 GHz": ("#5b2a86", 86), "61 GHz": ("#d1495b", 68), "63.5 GHz": ("#edae49", 54)}
    for lab, (c, th) in cols.items():
        r = 4.2
        x0 = 5
        ax.add_patch(Wedge((x0, 0.6), r, th - 5, th + 5, fc=c, alpha=0.35, ec=c))
        ax.text(x0 + (r + 0.3) * np.cos(np.radians(th)), 0.6 + (r + 0.3) * np.sin(np.radians(th)), lab,
                color=c, ha="center", fontsize=8, fontweight="bold")
    ax.text(5, -0.95, "slots leak a little power each; their phases line up in one direction,\n"
                      "and that direction changes with frequency (beam squint)", ha="center", fontsize=8)
    ax.set_xlim(-1.2, 11.2)
    ax.set_ylim(-1.4, 5.5)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "concept_lwa.png"))
    plt.close(fig)


def serpentine_trick():
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.6))
    # straight guide
    ax[0].add_patch(Rectangle((0, 0), 8, 0.5, fc="#cfd6de", ec="#1f3a5f"))
    for i in range(4):
        ax[0].add_patch(Rectangle((0.8 + i * 2 - 0.1, 0.45), 0.2, 0.1, fc="k"))
    ax[0].annotate("", xy=(2.8, 0.9), xytext=(0.8, 0.9), arrowprops=dict(arrowstyle="<->"))
    ax[0].text(1.8, 1.05, "path = d", ha="center")
    ax[0].set_title("straight slotted guide: wave travels d between slots\nsmall phase change with f → 8.7° squint",
                    fontsize=8)
    # serpentine
    xs = np.arange(4) * 1.6
    for i, x in enumerate(xs):
        ax[1].add_patch(Rectangle((x, 0), 0.8, 3, fc="#cfd6de", ec="#1f3a5f"))
        ax[1].add_patch(Rectangle((x + 0.25, 1.45), 0.3, 0.1, angle=25 if i % 2 == 0 else -25,
                                  rotation_point="center", fc="k"))
        if i < 3:
            top = i % 2 == 0
            yc = 3 if top else 0
            th = np.linspace(0, np.pi, 30) if top else np.linspace(np.pi, 2 * np.pi, 30)
            ax[1].plot(x + 1.2 + 0.8 * np.cos(th), yc + 0.8 * np.sin(th), color="#1f3a5f", lw=5, alpha=.5)
    ax[1].annotate("", xy=(1.6 + 0.4, -0.5), xytext=(0.4, -0.5), arrowprops=dict(arrowstyle="<->"))
    ax[1].text(1.2, -0.95, "d = 2.38 mm", ha="center", fontsize=8)
    ax[1].text(3.4, 4.3, "path between slots l = 10.9 mm (4.6 × d)", ha="center", fontsize=8, color="#e76f51")
    ax[1].set_title("serpentine: the wave detours l > d\nphase changes 4.6× faster with f → 32° squint per port",
                    fontsize=8)
    for a in ax:
        a.set_aspect("equal")
        a.axis("off")
    ax[0].set_xlim(-0.3, 8.3)
    ax[0].set_ylim(-0.5, 1.5)
    ax[1].set_xlim(-0.5, 6)
    ax[1].set_ylim(-1.3, 4.6)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "concept_serpentine.png"))
    plt.close(fig)


def fmcw():
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.8))
    t = np.linspace(0, 1, 200)
    ax[0].plot(t, 58 + 5.5 * t, "C3", label="transmitted chirp")
    ax[0].plot(t + 0.08, 58 + 5.5 * t, "C0--", label="echo (delayed)")
    ax[0].annotate("", xy=(0.6, 58 + 5.5 * 0.6), xytext=(0.6, 58 + 5.5 * 0.52),
                   arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax[0].annotate("beat frequency\n∝ round-trip delay\n∝ distance", xy=(0.6, 61.1), xytext=(0.72, 59.2),
                   fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax[0].set_xlabel("time (ramp)")
    ax[0].set_ylabel("frequency (GHz)")
    ax[0].legend(fontsize=7)
    ax[0].set_title("range: FMCW beat frequency", fontsize=9)
    th1, th2 = 75, 60
    f = np.linspace(58, 63.5, 300)
    beam = 86 - (86 - 54) * (f - 58) / 5.5
    p = np.exp(-((beam - th1) / 4) ** 2) + 0.6 * np.exp(-((beam - th2) / 4) ** 2)
    ax[1].plot(f, p, "C3")
    ax[1].set_xlabel("instantaneous frequency (GHz)")
    ax[1].set_ylabel("echo power")
    for th, lab in ((th1, "target A at 75°"), (th2, "target B at 60°")):
        fi = 58 + (86 - th) / (86 - 54) * 5.5
        ax[1].axvline(fi, color="0.6", ls=":")
        ax[1].text(fi, 1.05 if th == th1 else 0.65, lab, ha="center", fontsize=7)
    ax[1].set_ylim(0, 1.2)
    ax[1].set_title("angle: which part of the chirp lights the target", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "concept_fmcw.png"))
    plt.close(fig)


if __name__ == "__main__":
    lwa_principle()
    serpentine_trick()
    fmcw()
    print("ok")
