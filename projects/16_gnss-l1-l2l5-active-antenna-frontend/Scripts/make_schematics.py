"""Schematic and connection-diagram images (PNG + SVG) in an ANSYS Circuit-like style:
white sheet with a dot grid, black component bodies, dark-blue wires, N-port Touchstone
blocks drawn as boxes carrying the file name, red instance names, blue values.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

IMG = Path(__file__).resolve().parent.parent / "Images"
IMG.mkdir(exist_ok=True)
WIRE, BODY, NAME, VAL = "#1b2f8f", "#000000", "#b0101a", "#1240c0"


def box(ax, x, y, w, h, name, sub, pins_l=(), pins_r=(), pins_b=(), body=BODY):
    ax.add_patch(plt.Rectangle((x, y - h / 2), w, h, fill=True, fc="#fbfbf6", ec=body, lw=1.3, zorder=3))
    ax.text(x + w / 2, y + h / 2 + 0.18, name, ha="center", va="bottom", color=NAME, fontsize=8.5, fontweight="bold")
    ax.text(x + w / 2, y, sub, ha="center", va="center", color=VAL, fontsize=6.6, zorder=4, wrap=True)
    pos = {}
    for side, plist in (("l", pins_l), ("r", pins_r)):
        n = len(plist)
        for i, p in enumerate(plist):
            py = y + h / 2 - h * (i + 1) / (n + 1)
            px = x if side == "l" else x + w
            ax.plot([px - 0.25 if side == "l" else px, px if side == "l" else px + 0.25], [py, py], color=BODY, lw=1.3, zorder=3)
            ax.plot(px - 0.25 if side == "l" else px + 0.25, py, "s", ms=2.6, color="#d01010", zorder=5)
            ax.text(px + (0.07 if side == "l" else -0.07), py + 0.07, p, ha="left" if side == "l" else "right",
                    va="bottom", fontsize=5.8, color="#404040", zorder=4)
            pos[p] = (px - 0.25 if side == "l" else px + 0.25, py)
    n = len(pins_b)
    for i, p in enumerate(pins_b):
        px = x + w * (i + 1) / (n + 1)
        ax.plot([px, px], [y - h / 2, y - h / 2 - 0.25], color=BODY, lw=1.3, zorder=3)
        ax.plot(px, y - h / 2 - 0.25, "s", ms=2.6, color="#d01010", zorder=5)
        ax.text(px + 0.06, y - h / 2 + 0.06, p, ha="left", va="bottom", fontsize=5.8, color="#404040", zorder=4)
        pos[p] = (px, y - h / 2 - 0.25)
    return pos


def w(ax, *pts):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=WIRE, lw=1.3, zorder=2, solid_capstyle="round")


def ground(ax, x, y):
    w(ax, (x, y), (x, y - 0.3))
    for k, hw in enumerate((0.22, 0.14, 0.06)):
        ax.plot([x - hw, x + hw], [y - 0.3 - 0.08 * k] * 2, color=BODY, lw=1.3, zorder=3)


def iport(ax, x, y, name, side="l"):
    s = -1 if side == "l" else 1
    ax.add_patch(plt.Polygon([(x, y), (x + s * 0.3, y + 0.18), (x + s * 0.9, y + 0.18), (x + s * 0.9, y - 0.18),
                              (x + s * 0.3, y - 0.18)], closed=True, fc="#fff3c4", ec=BODY, lw=1.2, zorder=3))
    ax.text(x + s * 1.0, y, name, ha="right" if side == "l" else "left", va="center", fontsize=8, color=NAME,
            fontweight="bold")


def resistor(ax, x, y, name, val, vertical=True):
    zz = np.array([[0, 0], [0, -0.15], [0.12, -0.22], [-0.12, -0.36], [0.12, -0.5], [-0.12, -0.64], [0.12, -0.78],
                   [0, -0.85], [0, -1.0]])
    ax.plot(x + zz[:, 0], y + zz[:, 1], color=BODY, lw=1.3, zorder=3)
    ax.text(x + 0.22, y - 0.4, name, fontsize=7, color=NAME, va="center")
    ax.text(x + 0.22, y - 0.65, val, fontsize=7, color=VAL, va="center")
    return (x, y - 1.0)


def cap_h(ax, x, y, name, val):
    """horizontal series capacitor from (x,y) to (x+1,y)"""
    w(ax, (x, y), (x + 0.42, y)); w(ax, (x + 0.58, y), (x + 1, y))
    for xx in (x + 0.42, x + 0.58):
        ax.plot([xx, xx], [y - 0.22, y + 0.22], color=BODY, lw=1.6, zorder=3)
    ax.text(x + 0.5, y + 0.3, name, ha="center", fontsize=7, color=NAME)
    ax.text(x + 0.5, y - 0.45, val, ha="center", fontsize=7, color=VAL)
    return (x + 1, y)


def cap_v(ax, x, y, name, val):
    """vertical shunt capacitor from (x,y) down to (x,y-1)"""
    w(ax, (x, y), (x, y - 0.42)); w(ax, (x, y - 0.58), (x, y - 1))
    for yy in (y - 0.42, y - 0.58):
        ax.plot([x - 0.22, x + 0.22], [yy, yy], color=BODY, lw=1.6, zorder=3)
    ax.text(x + 0.3, y - 0.35, name, fontsize=7, color=NAME)
    ax.text(x + 0.3, y - 0.7, val, fontsize=7, color=VAL)
    return (x, y - 1)


def ind_v(ax, x, y, name, val, length=1.2):
    w(ax, (x, y), (x, y - 0.15))
    t = np.linspace(0, 4 * np.pi, 200)
    yy = y - 0.15 - (length - 0.3) * t / t[-1]
    ax.plot(x + 0.13 * np.abs(np.sin(t / 2)), yy, color=BODY, lw=1.3, zorder=3)
    w(ax, (x, y - length + 0.15), (x, y - length))
    ax.text(x + 0.25, y - length / 2 + 0.1, name, fontsize=7, color=NAME)
    ax.text(x + 0.25, y - length / 2 - 0.2, val, fontsize=7, color=VAL)
    return (x, y - length)


def amp(ax, x, y, name, sub):
    ax.add_patch(plt.Polygon([(x, y + 0.7), (x, y - 0.7), (x + 1.3, y)], closed=True, fc="#fbfbf6", ec=BODY, lw=1.3, zorder=3))
    ax.text(x + 0.45, y + 0.85, name, ha="center", fontsize=8, color=NAME, fontweight="bold")
    ax.text(x - 0.15, y - 1.0, sub, ha="right", fontsize=6.5, color=VAL)
    return (x, y), (x + 1.3, y)


def dot(ax, x, y):
    ax.plot(x, y, "o", ms=3.2, color=WIRE, zorder=4)


def new_sheet(wd, ht, xlim, ylim, title):
    fig, ax = plt.subplots(figsize=(wd, ht))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal"); ax.axis("off")
    gx = np.arange(xlim[0], xlim[1] + 0.01, 0.5)
    gy = np.arange(ylim[0], ylim[1] + 0.01, 0.5)
    X, Y = np.meshgrid(gx, gy)
    ax.scatter(X.ravel(), Y.ravel(), s=0.35, color="#bdbdbd", zorder=0)
    ax.add_patch(plt.Rectangle((xlim[0] + 0.1, ylim[0] + 0.1), xlim[1] - xlim[0] - 0.2, ylim[1] - ylim[0] - 0.2,
                               fill=False, ec="#9a9a9a", lw=0.8))
    ax.text(xlim[0] + 0.3, ylim[1] - 0.45, title, fontsize=10.5, fontweight="bold", color="#202020", va="top")
    ax.text(xlim[1] - 0.3, ylim[0] + 0.3, "Project 16 | Scripts/make_schematics.py | units: ohm, H, F",
            fontsize=6, color="#808080", ha="right")
    return fig, ax


def save(fig, name):
    fig.tight_layout(pad=0.2)
    fig.savefig(IMG / f"{name}.png", dpi=220, facecolor="white")
    fig.savefig(IMG / f"{name}.svg", facecolor="white")
    plt.close(fig)


def stage_block(ax, x, y, tag):
    """compact LNA stage symbol (details on the LNA-stage sheet)"""
    p = box(ax, x, y, 3.2, 1.6, f"LNA_{tag}", "DC block + bias tee\n+5 V, 70 mA\nTQP3M9037_5V.s2p",
            pins_l=["in"], pins_r=["out"])
    return p["in"], p["out"]


def system_sheet():
    fig, ax = new_sheet(18, 9.2, (-1.5, 38.5), (-11.6, 4.8),
                        "FrontEnd_3port - top level (L1 branch top, L2/L5 branch bottom, DXP.02.A combiner)")
    outs = {}
    for br, y, saw, saw_txt in (("L1", 1.0, "B7504", "B7504.s2p\n(L1/B1/G1 SAW)"),
                                ("L2", -6.2, "B8889", "B8889_matched.s2p\n(incl. 2x 6.8 nH)")):
        pc = box(ax, 1.2, y, 3.2, 2.2, f"PATCH_{br}", "PatchCP_ideal\n_RHCP_feed.s4p",
                 pins_l=["1 RHCP", "2 LHCP"], pins_r=["3 feedA", "4 feedB"])
        iport(ax, pc["1 RHCP"][0] - 0.6, pc["1 RHCP"][1], f"P{1 if br == 'L1' else 2}_{br}_RHCP")
        w(ax, (pc["1 RHCP"][0] - 0.6, pc["1 RHCP"][1]), pc["1 RHCP"])
        lx, ly = pc["2 LHCP"]
        w(ax, (lx, ly), (lx - 0.4, ly), (lx - 0.4, ly - 0.6))
        e = resistor(ax, lx - 0.4, ly - 0.6, f"R_LHCP_{br}", "50")
        ground(ax, *e)
        hy = box(ax, 6.0, y, 2.8, 2.2, f"HC125A_{br}", "HC125A.s4p\n3 dB 90 deg hybrid",
                 pins_l=["pin3", "pin4"], pins_r=["pin1", "pin2"])
        w(ax, pc["3 feedA"], (5.1, pc["3 feedA"][1]), (5.1, hy["pin3"][1]), hy["pin3"])
        w(ax, pc["4 feedB"], (5.4, pc["4 feedB"][1]), (5.4, hy["pin4"][1]), hy["pin4"])
        ix, iy = hy["pin2"]
        w(ax, (ix, iy), (ix + 0.4, iy), (ix + 0.4, iy - 0.6))
        e = resistor(ax, ix + 0.4, iy - 0.6, f"R_ISO_{br}", "50")
        ground(ax, *e)
        a_in, a_out = stage_block(ax, 10.4, y + 0.3, f"{br}A")
        w(ax, hy["pin1"], (a_in[0], hy["pin1"][1]) if abs(hy["pin1"][1] - a_in[1]) < 1e-6 else (9.7, hy["pin1"][1]),
          (9.7, a_in[1]), a_in)
        s1 = box(ax, 14.8, y + 0.3, 3.2, 1.6, f"SAW1_{br}", saw_txt, pins_l=["1 in"], pins_r=["3 out" if br == "L1" else "4 out"])
        w(ax, a_out, s1["1 in"])
        b_in, b_out = stage_block(ax, 19.2, y + 0.3, f"{br}B")
        w(ax, list(s1.values())[1], b_in)
        s2 = box(ax, 23.6, y + 0.3, 3.2, 1.6, f"SAW2_{br}", saw_txt, pins_l=["1 in"], pins_r=["3 out" if br == "L1" else "4 out"])
        w(ax, b_out, s2["1 in"])
        outs[br] = list(s2.values())[1]
    dx = box(ax, 30.0, -2.6, 4.4, 3.4, "DXP02A", "DXP02A.s3p\nSAW diplexer\n(eval matching incl.)",
             pins_l=["pin7 L1", "pin5 L2/L5"], pins_r=["pin2 common"], pins_b=["GND"])
    w(ax, outs["L1"], (28.6, outs["L1"][1]), (28.6, dx["pin7 L1"][1]), dx["pin7 L1"])
    w(ax, outs["L2"], (28.6, outs["L2"][1]), (28.6, dx["pin5 L2/L5"][1]), dx["pin5 L2/L5"])
    ground(ax, *dx["GND"])
    ox, oy = dx["pin2 common"]
    w(ax, (ox, oy), (ox + 0.9, oy))
    iport(ax, ox + 0.9, oy, "P3_RF_OUT", side="r")
    # supply note
    ax.text(-1.0, -9.9, "VDD = +5 V to all four LNA stages (70 mA each, 280 mA total)", fontsize=7.5, color=VAL)
    ax.text(-1.0, -10.6, "Analysis: Nexxim linear network analysis (NexximLNA), LINC 0.6 GHz - 2.2 GHz, 3201 points; "
            "ports P1/P2 = virtual RHCP inputs, P3 = receiver port, all 50 ohm.", fontsize=7.5, color="#303030")
    save(fig, "schematic_system")


def lna_sheet():
    fig, ax = new_sheet(11, 6.6, (-1.0, 19.0), (-6.4, 5.4), "LNA stage (one of four): TQP3M9037 with bias network, VDD = +5 V")
    iport(ax, 0.6, 0.0, "RF_IN")
    w(ax, (0.6, 0), (1.5, 0))
    e = cap_h(ax, 1.5, 0, "C1", "100 pF")
    w(ax, e, (4.0, 0))
    i, o = amp(ax, 4.0, 0.0, "U1 TQP3M9037", "TQP3M9037_5V.s2p (pins 2 -> 7)")
    w(ax, o, (8.0, 0))
    dot(ax, 7.0, 0)
    # choke up to VDD
    w(ax, (7.0, 0), (7.0, 0.3))
    t = np.linspace(0, 4 * np.pi, 200)
    yy = 0.3 + 1.6 * t / t[-1]
    ax.plot(7.0 + 0.13 * np.abs(np.sin(t / 2)), yy, color=BODY, lw=1.3, zorder=3)
    ax.text(7.25, 1.2, "L1", fontsize=7, color=NAME); ax.text(7.25, 0.9, "18 nH (0603)", fontsize=7, color=VAL)
    w(ax, (7.0, 1.9), (7.0, 3.2), (13.0, 3.2))
    for xx, nm, vv in ((8.5, "C3", "100 pF"), (10.0, "C4", "1 uF")):
        dot(ax, xx, 3.2)
        e = cap_v(ax, xx, 3.2, nm, vv)
        ground(ax, *e)
    iport(ax, 13.0, 3.2, "VDD +5 V", side="r")
    e = cap_h(ax, 8.0, 0, "C2", "100 pF")
    w(ax, e, (10.5, 0))
    iport(ax, 10.5, 0, "RF_OUT", side="r")
    # shutdown divider (optional)
    w(ax, (4.6, -0.42), (4.6, -1.6))
    ax.text(4.75, -0.8, "pin 6 SD", fontsize=6.5, color="#404040")
    dot(ax, 4.6, -1.6)
    w(ax, (4.6, -1.6), (5.6, -1.6))
    ax.plot([5.6, 6.6], [-1.6, -1.6], color=BODY, lw=1.3)
    zz = np.array([[0, 0], [0.1, 0], [0.18, 0.12], [0.32, -0.12], [0.46, 0.12], [0.6, -0.12], [0.74, 0.12], [0.82, 0], [1.0, 0]])
    ax.plot(5.6 + zz[:, 0], -1.6 + zz[:, 1], color=BODY, lw=1.3, zorder=3)
    ax.text(5.9, -1.35, "R2 33 k", fontsize=7, color=NAME)
    w(ax, (6.6, -1.6), (7.4, -1.6))
    iport(ax, 7.4, -1.6, "PD (0 V = on)", side="r")
    e = resistor(ax, 4.6, -1.6, "R1", "10 k")
    ground(ax, *e)
    ax.text(-0.6, -4.3, "Backside paddle and pins 1,3,4,5,8 to RF/DC ground (via array per Qorvo p.15). "
            "R1/R2 optional (FDD: leave open = always on).", fontsize=7.2, color="#303030")
    ax.text(-0.6, -4.9, "Simulation model: C1/C2 0402 NPO with ESL 0.25 nH, ESR 0.15 ohm; L1 Q = 40 @ 1.4 GHz, 0.12 pF "
            "self-capacitance; C3 ESL 0.4 nH  [ASSUMED parasitics].", fontsize=7.2, color="#303030")
    ax.text(-0.6, -5.5, "Values: Qorvo TQP3M9037-PCB default BOM (data sheet p.5). Input match optional: "
            "3.3 pF series + 3.9 nH shunt (Qorvo p.9 optimized-RL design).", fontsize=7.2, color="#303030")
    save(fig, "schematic_lna_stage")


def matching_sheet():
    fig, ax = new_sheet(12, 6.6, (-1.0, 23.0), (-7.6, 5.4), "Datasheet matching networks (already inside the Touchstone models)")
    # B8889 block
    ax.text(-0.5, 4.0, "B8889 (Qualcomm data sheet p.6): Lp1 = Lp4 = 6.8 nH shunt  ->  B8889_matched.s2p",
            fontsize=8.5, color="#202020", fontweight="bold")
    iport(ax, 0.6, 1.5, "IN")
    w(ax, (0.6, 1.5), (4.5, 1.5)); dot(ax, 2.5, 1.5)
    e = ind_v(ax, 2.5, 1.5, "Lp1", "6.8 nH"); ground(ax, *e)
    s = box(ax, 4.5, 1.5, 3.0, 1.8, "B8889", "pins 1 -> 4\ngnd 2,3,5", pins_l=["1"], pins_r=["4"])
    w(ax, s["4"], (10.0, 1.5)); dot(ax, 9.0, 1.5)
    e = ind_v(ax, 9.0, 1.5, "Lp4", "6.8 nH"); ground(ax, *e)
    iport(ax, 10.0, 1.5, "OUT", side="r")
    # DXP eval board
    ax.text(-0.5, -1.4, "DXP.02.A evaluation board (Taoglas p.13)  ->  included in DXP02A.s3p",
            fontsize=8.5, color="#202020", fontweight="bold")
    iport(ax, 0.6, -3.5, "COMMON")
    w(ax, (0.6, -3.5), (1.8, -3.5)); dot(ax, 1.8, -3.5)
    e = cap_v(ax, 1.8, -3.5, "C1", "1.5 pF"); ground(ax, *e)
    w(ax, (1.8, -3.5), (2.6, -3.5))
    t = np.linspace(0, 4 * np.pi, 200)
    ax.plot(2.6 + 1.0 * t / t[-1], -3.5 + 0.13 * np.abs(np.sin(t / 2)), color=BODY, lw=1.3)
    ax.text(2.8, -3.1, "L2 4.3 nH", fontsize=7, color=NAME)
    w(ax, (3.6, -3.5), (4.5, -3.5))
    d = box(ax, 4.5, -3.5, 3.4, 3.4, "DXP.02.A", "pin 2 in\npin 7 L1, pin 5 L2/L5\ngnd 1,3,4,6,8",
            pins_l=["2"], pins_r=["7 L1", "5 L2/L5"])
    for pin, lval, cval, nm, y_ in ((d["7 L1"], "L1 4.7 nH", "C3 DNF", "L1 OUT", None),
                                    (d["5 L2/L5"], "L3 3.3 nH", "C2 1 pF", "L2/L5 OUT", None)):
        x0, y0 = pin
        w(ax, (x0, y0), (x0 + 0.3, y0))
        ax.plot(x0 + 0.3 + 1.0 * t / t[-1], y0 + 0.13 * np.abs(np.sin(t / 2)), color=BODY, lw=1.3)
        ax.text(x0 + 0.4, y0 + 0.3, lval, fontsize=7, color=NAME)
        w(ax, (x0 + 1.3, y0), (x0 + 3.2, y0)); dot(ax, x0 + 2.2, y0)
        e = cap_v(ax, x0 + 2.2, y0, *cval.split(maxsplit=1)); ground(ax, *e)
        iport(ax, x0 + 3.2, y0, nm, side="r")
    ax.text(-0.5, -7.0, "Do not add these parts again around the .s2p/.s3p models: the datasheet curves were measured with them.",
            fontsize=7.5, color="#b0101a")
    save(fig, "schematic_matching_networks")


def connection_diagram():
    fig, ax = plt.subplots(figsize=(12, 3.6))
    ax.set_xlim(0, 24); ax.set_ylim(-4.2, 3.2); ax.axis("off")
    C = {"L1": "#2a78d6", "L2": "#eb6834"}
    def blk(x, y, t, c="#f2f1ed", wdt=2.4):
        ax.add_patch(plt.Rectangle((x, y - 0.55), wdt, 1.1, fc=c, ec="#52514e", lw=1, zorder=2))
        ax.text(x + wdt / 2, y, t, ha="center", va="center", fontsize=7.5, zorder=3)
        return x, x + wdt
    for br, y, saw, lab in (("L1", 1.6, "B7504", "L1 / E1 / B1 / G1 patch\n(2 orthogonal feeds)"),
                            ("L2", -2.0, "B8889 (+2x6.8 nH)", "L2 / L5 / E5 patch\n(2 orthogonal feeds)")):
        xs = [blk(0.2, y, lab, wdt=3.0)]
        for t in ("HC125A\n3 dB 90 deg", "TQP3M9037\nLNA 1", saw, "TQP3M9037\nLNA 2", saw):
            xs.append(blk(xs[-1][1] + 0.7, y, t, wdt=2.4 if len(t) < 14 else 2.9))
        for (a0, a1), (b0, b1) in zip(xs[:-1], xs[1:]):
            ax.annotate("", (b0, y), (a1, y), arrowprops=dict(arrowstyle="-|>", color=C[br], lw=1.6))
        ax.annotate("", (19.5, 0.0 + (0.3 if br == "L1" else -0.3)), (xs[-1][1], y),
                    arrowprops=dict(arrowstyle="-|>", color=C[br], lw=1.6, connectionstyle="arc3,rad=0"))
        ax.text(0.2, y + 0.75, "L1 branch" if br == "L1" else "L2/L5 branch", color=C[br], fontsize=8, fontweight="bold")
    blk(19.5, 0.0, "DXP.02.A\nSAW diplexer\n(combiner)", wdt=2.3)
    ax.annotate("", (23.9, 0), (21.8, 0), arrowprops=dict(arrowstyle="-|>", color="#0b0b0b", lw=1.6))
    ax.text(22.0, 0.3, "RF out\n(coax)", fontsize=7.5)
    ax.text(0.2, -3.6, "Bias: +5 V, 4 x 70 mA = 280 mA (DC fed via 18 nH chokes at each LNA output; "
            "add a bias tee if powered over the coax). Signal flow left to right.", fontsize=7.5, color="#52514e")
    fig.tight_layout()
    fig.savefig(IMG / "connection_diagram.png", dpi=200, facecolor="white")
    fig.savefig(IMG / "connection_diagram.svg", facecolor="white")
    plt.close(fig)


def sband_sheet():
    fig, ax = new_sheet(18, 7.2, (-1.5, 37.5), (-7.0, 6.0),
                        "SBand_2port - NavIC S-band branch (2492.028 MHz), separate RF output")
    y = 1.0
    pc = box(ax, 1.2, y, 3.2, 2.2, "PATCH_S", "PatchCP_ideal\nRHCP_feed.s4p", pins_l=["1 RHCP", "2 LHCP"],
             pins_r=["3 feedA", "4 feedB"])
    iport(ax, pc["1 RHCP"][0] - 0.6, pc["1 RHCP"][1], "P1_S_RHCP")
    w(ax, (pc["1 RHCP"][0] - 0.6, pc["1 RHCP"][1]), pc["1 RHCP"])
    lx, ly = pc["2 LHCP"]
    w(ax, (lx, ly), (lx - 0.4, ly), (lx - 0.4, ly - 0.6))
    ground(ax, *resistor(ax, lx - 0.4, ly - 0.6, "R_LHCP", "50"))
    hy = box(ax, 6.2, y, 3.4, 2.2, "HYB_S", "C2327J5003AHF.s4p\n3 dB 90 deg 0805", pins_l=["pin4 dir", "pin6 cpl"],
             pins_r=["pin1 in", "pin3 iso"])
    w(ax, pc["3 feedA"], (5.3, pc["3 feedA"][1]), (5.3, hy["pin4 dir"][1]), hy["pin4 dir"])
    w(ax, pc["4 feedB"], (5.6, pc["4 feedB"][1]), (5.6, hy["pin6 cpl"][1]), hy["pin6 cpl"])
    ix, iy = hy["pin3 iso"]
    w(ax, (ix, iy), (ix + 0.4, iy), (ix + 0.4, iy - 0.6))
    ground(ax, *resistor(ax, ix + 0.4, iy - 0.6, "R_ISO_S", "50"))
    prev = hy["pin1 in"]
    x = 11.2
    for i, tag in enumerate(("SA", "SB")):
        p = box(ax, x, y + 0.3, 3.4, 1.8, f"LNA_{tag}", "2.7 nH sh + 2.4 pF\nTQP3M9037 +5 V\n5.6 nH choke, 100 pF",
                pins_l=["in"], pins_r=["out"])
        w(ax, prev, (x - 0.6, prev[1]), (x - 0.6, p["in"][1]), p["in"])
        s_ = box(ax, x + 4.3, y + 0.3, 3.2, 1.8, f"SAW{i + 1}_S", "TA1442A.s2p\n2492 MHz SAW", pins_l=["B in"],
                 pins_r=["E out"])
        w(ax, p["out"], s_["B in"])
        prev = s_["E out"]
        x += 8.6
    w(ax, prev, (prev[0] + 1.0, prev[1]))
    iport(ax, prev[0] + 1.0, prev[1], "P2_S_OUT", side="r")
    ax.text(-1.0, -4.6, "LNA stages: Qorvo TQP3M9037 2300-2600 MHz reference design (data sheet p.10): input 2.7 nH shunt + "
            "2.4 pF series, output 5.6 nH choke to VDD (100 pF + 1 uF bypass), 100 pF DC block. VDD +5 V, 2 x 70 mA.",
            fontsize=7.5, color="#303030")
    ax.text(-1.0, -5.4, "Patch feeds: feed A -> direct (pin 4), feed B -> coupled (pin 6) so RHCP adds at pin 1; "
            "TA1442A pins B in / E out, A/C/D/F ground. Analysis: linear network 0.5-4 GHz.", fontsize=7.5,
            color="#303030")
    save(fig, "schematic_sband")


def sband_connection_diagram():
    fig, ax = plt.subplots(figsize=(12, 1.9))
    ax.set_xlim(0, 24); ax.set_ylim(-1.3, 1.2); ax.axis("off")
    x = 0.2
    for i, t in enumerate(("S-band patch\n(2 orthogonal feeds)", "C2327J5003AHF\n3 dB 90 deg", "TQP3M9037\nLNA 1",
                           "TA1442A\n2492 MHz SAW", "TQP3M9037\nLNA 2", "TA1442A\n2492 MHz SAW", "S-band RF out")):
        wd = 2.9
        ax.add_patch(plt.Rectangle((x, -0.55), wd, 1.1, fc="#f2f1ed" if i < 6 else "white", ec="#52514e", lw=1))
        ax.text(x + wd / 2, 0, t, ha="center", va="center", fontsize=7.5)
        if i < 6:
            ax.annotate("", (x + wd + 0.5, 0), (x + wd, 0), arrowprops=dict(arrowstyle="-|>", color="#1baf7a", lw=1.6))
        x += wd + 0.5
    ax.text(0.2, 0.85, "S-band (NavIC) branch", color="#1baf7a", fontsize=8, fontweight="bold")
    fig.tight_layout()
    fig.savefig(IMG / "connection_diagram_sband.png", dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    sband_sheet()
    sband_connection_diagram()
    system_sheet()
    lna_sheet()
    matching_sheet()
    connection_diagram()
    print("schematics written to", IMG)
