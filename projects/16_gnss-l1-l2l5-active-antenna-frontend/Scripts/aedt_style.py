"""Plots that look like a circuit simulator's report window (rectangular XY plot and Smith chart):
dotted grid, boxed 'Curve Info' legend with the trace expression and setup name, marker table
(m1, m2, ...) with triangle markers on the traces, framed plot title bar.

    xy_plot(path, title, design, traces, xlabel, ylabel, markers=..., ylim=..., xlim=...)
    smith_plot(path, title, design, traces, markers=...)

traces:  list of dict(x=..., y=..., expr="dB(S(P3,P1))", setup="SP1 : Sweep")
markers: list of (name, x, trace_index)   -> value read off the trace by interpolation
"""
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

TRACE = ["#e3101a", "#1036e8", "#0f9a12", "#c0168a", "#e07b00", "#008b8b"]
FRAME, GRID, BG = "#5a5a5a", "#b9b9b9", "#ffffff"
FONT = {"family": "DejaVu Sans", "size": 7.5}


def _window(fig, title, design):
    """grey title bar across the top of the figure, like a report window."""
    ax = fig.add_axes([0, 0.935, 1, 0.065])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color="#dcdfe6"))
    ax.text(0.012, 0.5, title, va="center", ha="left", fontsize=8.5, fontweight="bold", color="#1a1a1a")
    ax.text(0.988, 0.5, design, va="center", ha="right", fontsize=7.5, color="#333333", style="italic")


def _side_panel(fig, traces, mk, xname, rect=(0.705, 0.12, 0.285, 0.775)):
    """'Curve Info' box and marker table in a panel right of the plot (never covers a trace)."""
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    n = len(traces)
    h = 0.07 + 0.105 * n
    top = 1.0
    ax.add_patch(Rectangle((0, top - h), 1, h, fc="white", ec=FRAME, lw=0.7))
    ax.text(0.03, top - 0.015, "Curve Info", va="top", fontsize=6.8, fontweight="bold")
    for i, t in enumerate(traces):
        yy = top - 0.07 - 0.105 * i
        c = TRACE[i % len(TRACE)]
        ax.plot([0.03, 0.13], [yy - 0.02] * 2, color=c, lw=1.8)
        ax.text(0.16, yy, t["expr"], va="top", fontsize=6.0)
        ax.text(0.16, yy - 0.045, t.get("setup", "SP1 : Sweep"), va="top", fontsize=5.4, color="#555555")
    if mk:
        y0 = top - h - 0.04
        rows = [[m[0], f"{m[1]:.4f}", (f"{m[2]:.3f}" if isinstance(m[2], (int, float)) else m[2]), m[3]] for m in mk]
        rh = 0.055
        tbl = ax.table(cellText=rows, colLabels=["", xname, "Value", "Trace"], cellLoc="center",
                       colWidths=[0.13, 0.29, 0.25, 0.33],
                       bbox=[0, y0 - rh * (len(rows) + 1), 1, rh * (len(rows) + 1)])
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(6.0)
        for (r, cc), cell in tbl.get_celld().items():
            cell.set_edgecolor(FRAME); cell.set_linewidth(0.5)
            if r == 0:
                cell.set_facecolor("#e9ecf2"); cell.get_text().set_fontweight("bold")


def _style_axes(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(FRAME); s.set_linewidth(0.9); s.set_visible(True)
    ax.grid(True, which="major", color=GRID, ls=(0, (1, 2)), lw=0.7)
    ax.tick_params(labelsize=7, colors="#222222", direction="in", length=3, top=True, right=True)


def xy_plot(path, title, design, traces, xlabel="Freq [GHz]", ylabel="Y1", markers=(), ylim=None, xlim=None,
            figsize=(8.6, 4.3), marker_loc=None, hlines=(), spans=()):
    plt.rcParams.update({"font.family": FONT["family"]})
    fig = plt.figure(figsize=figsize, facecolor="white")
    _window(fig, title, design)
    ax = fig.add_axes([0.075, 0.12, 0.6, 0.775])
    _style_axes(ax)
    for lo, hi, lab in spans:
        ax.axvspan(lo, hi, color="#eef2fb", zorder=0)
        if lab:
            ax.text((lo + hi) / 2, 0.015, lab, transform=ax.get_xaxis_transform(), rotation=90, fontsize=5.5,
                    ha="center", va="bottom", color="#666666")
    for y, lab in hlines:
        ax.axhline(y, color="#7a7a7a", lw=0.8, ls="--")
        if lab:
            ax.text(0.01, y, " " + lab, transform=ax.get_yaxis_transform(), fontsize=6, va="bottom", color="#555555")
    for i, t in enumerate(traces):
        ax.plot(t["x"], t["y"], color=TRACE[i % len(TRACE)], lw=1.25, zorder=5)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    mk = []
    for name, x, ti in markers:
        t = traces[ti]
        y = float(np.interp(x, t["x"], t["y"]))
        ax.plot([x], [y], marker="v", ms=6, color="#2b2b2b", mfc="#ffd400", mew=0.7, zorder=11)
        ax.annotate(name, (x, y), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=6.5,
                    fontweight="bold", zorder=11)
        mk.append((name, x, y, t.get("short", f"Y{ti + 1}")))
    _side_panel(fig, traces, mk, xlabel)
    ax.set_xlabel(xlabel, fontsize=7.5)
    ax.set_ylabel(ylabel, fontsize=7.5)
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def smith_plot(path, title, design, traces, markers=(), figsize=(8.6, 5.6)):
    """traces: dict(g=complex reflection coefficients, f=GHz array, expr=..., setup=...)."""
    fig = plt.figure(figsize=figsize, facecolor="white")
    _window(fig, title, design)
    ax = fig.add_axes([0.01, 0.03, 0.66, 0.88])
    ax.set_aspect("equal"); ax.axis("off")
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=FRAME, lw=1.0)
    for r in (0.2, 0.5, 1, 2, 5):
        c, rad = r / (1 + r), 1 / (1 + r)
        ax.plot(c + rad * np.cos(th), rad * np.sin(th), color=GRID, lw=0.6, ls=(0, (1, 2)))
        ax.text(c - rad + 0.01, 0.015, f"{r:g}", fontsize=5.5, color="#555555")
    for x in (0.2, 0.5, 1, 2, 5):
        for sgn in (1, -1):
            z = 1j * sgn * x + np.linspace(0, 60, 600)
            g = (z - 1) / (z + 1)
            ax.plot(g.real, g.imag, color=GRID, lw=0.6, ls=(0, (1, 2)))
            gi = (1j * sgn * x - 1) / (1j * sgn * x + 1)
            ax.text(gi.real * 1.06, gi.imag * 1.06, f"{sgn * x:g}", fontsize=5.5, color="#555555", ha="center",
                    va="center")
    ax.plot([-1, 1], [0, 0], color=GRID, lw=0.6, ls=(0, (1, 2)))
    for i, t in enumerate(traces):
        ax.plot(t["g"].real, t["g"].imag, color=TRACE[i % len(TRACE)], lw=1.2, zorder=5)
    mk = []
    for name, fx, ti in markers:
        t = traces[ti]
        k = int(np.argmin(abs(t["f"] - fx)))
        g = t["g"][k]
        z = 50 * (1 + g) / (1 - g)
        ax.plot(g.real, g.imag, marker="v", ms=6, color="#2b2b2b", mfc="#ffd400", mew=0.7, zorder=11)
        ax.annotate(name, (g.real, g.imag), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=6.5,
                    fontweight="bold", zorder=11)
        mk.append((name, fx, f"{z.real:.1f}{'+' if z.imag >= 0 else '-'}j{abs(z.imag):.1f}", t.get("short", f"Y{ti + 1}")))
    ax.set_xlim(-1.08, 1.08); ax.set_ylim(-1.08, 1.08)
    _side_panel(fig, traces, mk, "Freq [GHz]", rect=(0.69, 0.05, 0.3, 0.83))
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)
