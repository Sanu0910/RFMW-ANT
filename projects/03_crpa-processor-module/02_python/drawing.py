"""CNC manufacturing drawings, A3 landscape, 1st-angle projection, true scale -> ../07_drawings/CRL-PSDR23-CASE_DRAWINGS.pdf
  sheet 1  -01 TUBE           top view (marking), bottom view (holes), end view, hole table, notes
  sheet 2  -02 PANEL ANT      outside face, inside face, top view (lug profile), section A-A through a lug hole, notes
  sheet 3  -03 PANEL USB      same views
  sheet 4  ASSEMBLY           renders, parts list (screws / nuts supplied by the vendor with spares), assembly notes
Datums: tube = ANT end face (X), centre lines (Y, Z); panel = flange inside face (A), centre lines (B, C)."""
import os, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, Polygon, Circle, Arc
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import box, Point, Polygon as SPoly
from shapely.ops import unary_union
from shapely.affinity import translate, scale as sscale
import config as C
import case as Cm
import text_art as A

OUTD = os.path.join(C.ROOT, "07_drawings")
STEPD = os.path.join(C.ROOT, "06_step")
INK = "#111"; AL = "#e3e7ea"; HAT = "#9aa3ab"; RED = "#b02020"; GRN = "#2f6b3a"
A3 = (420.0, 297.0)


# ---------------- primitives ----------------
def view(fig, x, y, lim, s):
    w, h = (lim[1] - lim[0]) * s, (lim[3] - lim[2]) * s
    ax = fig.add_axes([x / A3[0], y / A3[1], w / A3[0], h / A3[1]])
    ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3]); ax.set_aspect("equal"); ax.axis("off")
    return ax


def dim(ax, p0, p1, off, text, horiz=True, fs=6.0, col=INK):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = (max(y0, y1) + off) if off > 0 else (min(y0, y1) + off)
        e = 0.6 if off > 0 else -0.6
        ax.plot([x0, x0], [y0, y + e * 0.4], lw=0.3, color=col); ax.plot([x1, x1], [y1, y + e * 0.4], lw=0.3, color=col)
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color=col, shrinkA=0, shrinkB=0, mutation_scale=4))
        ax.text((x0 + x1) / 2, y, text, ha="center", va="bottom" if off > 0 else "top", fontsize=fs, color=col)
    else:
        x = (max(x0, x1) + off) if off > 0 else (min(x0, x1) + off)
        e = 0.6 if off > 0 else -0.6
        ax.plot([x0, x + e * 0.4], [y0, y0], lw=0.3, color=col); ax.plot([x1, x + e * 0.4], [y1, y1], lw=0.3, color=col)
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color=col, shrinkA=0, shrinkB=0, mutation_scale=4))
        ax.text(x, (y0 + y1) / 2, text, ha="right" if off < 0 else "left", va="center", fontsize=fs, rotation=90, color=col)


def leader(ax, p, q, text, fs=5.6, ha="left"):
    ax.annotate(text, p, q, fontsize=fs, ha=ha, va="center", arrowprops=dict(arrowstyle="-|>", lw=0.35, color=INK, mutation_scale=4))


def shape(ax, g, fc=AL, ec=INK, lw=0.6, hatch=None, z=1, ls="-"):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        if q.is_empty: continue
        ax.add_patch(Polygon(list(q.exterior.coords), fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, ls=ls))
        for i in q.interiors: ax.add_patch(Polygon(list(i.coords), fc="white", ec=ec, lw=lw, zorder=z))


def outline(ax, g, ls="-", lw=0.6, col=INK, z=3):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        if q.is_empty: continue
        for ring in [q.exterior] + list(q.interiors):
            xs, ys = zip(*ring.coords); ax.plot(xs, ys, ls=ls, lw=lw, color=col, zorder=z)


def cl(ax, p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], lw=0.3, color=INK, ls=(0, (6, 1.5, 1, 1.5)), zorder=5)


def title(ax, x, y, t, fs=7):
    ax.text(x, y, t, ha="center", va="bottom", fontsize=fs, weight="bold")


def frame(fig, sheet, n, pn, name, mat, scale):
    fig.add_artist(Rectangle((0.01, 0.012), 0.98, 0.976, fill=False, lw=1.4, transform=fig.transFigure))
    tb = (0.66, 0.02, 0.32, 0.13)
    fig.add_artist(Rectangle(tb[:2], tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    lg = mpimg.imread(C.LOGO_PNG)
    axl = fig.add_axes([tb[0] + 0.004, tb[1] + 0.078, 0.11, 0.048]); axl.imshow(lg); axl.axis("off")
    fig.text(tb[0] + 0.122, tb[1] + 0.112, C.TEXT["title"], fontsize=7.2, weight="bold")
    fig.text(tb[0] + 0.122, tb[1] + 0.095, name, fontsize=7.0)
    fig.text(tb[0] + 0.122, tb[1] + 0.081, mat, fontsize=4.9)
    items = (("PART", pn), ("DWG", pn + "-DWG"), ("REV", C.TEXT["rev"]), ("SHEET", "%d / %d" % (sheet, n)),
             ("DATE", C.TEXT["date"]), ("UNITS", "mm"), ("SCALE", scale), ("PROJ.", "1st angle"))
    for i, (k, v) in enumerate(items):
        fig.text(tb[0] + 0.006 + (i % 4) * 0.079, tb[1] + 0.047 - (i // 4) * 0.032, "%s\n%s" % (k, v), fontsize=5.8)
    fig.text(tb[0] + 0.006, tb[1] + 0.003, "Design: PocketSDR FE 2CH v2.3 case (T. Takasu), unchanged. Model: %s" % (pn + ".step"), fontsize=4.6)


def notes_block(fig, x, y, lines, fs=5.6):
    for i, n_ in enumerate(lines):
        fig.text(x, y - i * 0.0142, n_, fontsize=fs + 1.2 if i == 0 else fs, weight="bold" if i == 0 else "normal")


def table(fig, x, y, rows, cw, fs=5.6, dy=0.0148):
    for r_i, row in enumerate(rows):
        xx = x
        for c_i, cell in enumerate(row):
            fig.text(xx, y - r_i * dy, cell, fontsize=fs, weight="bold" if r_i == 0 else "normal"); xx += cw[c_i]


def new_fig():
    return plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))


# ---------------- sheet 1: tube ----------------
def sheet_tube(H):
    T = C.TUBE; s = 2.5; L, W, Hh = H.L, T["W"], T["H"]
    fig = new_fig(); frame(fig, 1, 4, C.PARTS["tube"], C.NAMES["tube"], C.MATERIAL["tube"], "%g : 1" % s)
    q = lambda mm: mm / s
    # top view (marking): X right, Y up
    ax = view(fig, 16, 160, (-q(16), L + q(14), -W / 2 - q(19), W / 2 + q(9)), s)
    shape(ax, box(0, -W / 2, L, W / 2))
    for yy in (-W / 2 + T["r_out"], W / 2 - T["r_out"]): ax.plot([0, L], [yy, yy], lw=0.3, color=INK)
    regs = A.logo_regions(C.LOGO_PNG, T["logo_w"], L / 2, T["logo_y"]) + \
        A.text_regions(C.TEXT["product"], T["name_h"], C.FONT_BOLD, L / 2, T["name_y"]) + \
        A.text_regions(C.TEXT["date"], T["date_h"], C.FONT_BOLD, L / 2, T["date_y"])
    for r in regs: shape(ax, r, fc="#555", ec="#333", lw=0.1, z=3)
    cl(ax, (-q(5), 0), (L + q(5), 0)); cl(ax, (L / 2, -W / 2 - q(4)), (L / 2, W / 2 + q(4)))
    dim(ax, (0, -W / 2), (L, -W / 2), -q(9), "%.1f ±0.05" % L)
    dim(ax, (0, -W / 2), (0, W / 2), -q(9), "%.1f" % W, horiz=False)
    lb = unary_union(A.logo_regions(C.LOGO_PNG, T["logo_w"], L / 2, T["logo_y"])).bounds
    dim(ax, (lb[0], lb[3]), (lb[2], lb[3]), q(4), "%.1f (logo)" % (lb[2] - lb[0]), fs=5.4)
    dim(ax, (L, 0), (L, T["logo_y"]), q(4), "%.1f" % T["logo_y"], horiz=False, fs=5.2)
    dim(ax, (L, T["name_y"]), (L, 0), q(9), "%.1f" % -T["name_y"], horiz=False, fs=5.2)
    dim(ax, (L, T["date_y"]), (L, 0), q(4) - 0.0, "", horiz=False, fs=5.2)
    ax.text(L + q(5.5), T["date_y"] / 2 - 1.2, "%.1f" % -T["date_y"], fontsize=5.2, rotation=90, va="center")
    ax.text(-q(4), W / 2 + q(2), "ANT end", fontsize=5.4, ha="left", color=RED)
    ax.text(L + q(4), W / 2 + q(2), "USB end", fontsize=5.4, ha="right", color=RED)
    title(ax, L / 2, -W / 2 - q(19), "TOP VIEW (Z+, component side)  - marking")

    # bottom view: seen from below, Y mirrored
    ax2 = view(fig, 16, 52, (-q(16), L + q(14), -W / 2 - q(19), W / 2 + q(9)), s)
    shape(ax2, box(0, -W / 2, L, W / 2))
    for yy in (-W / 2 + T["r_out"], W / 2 - T["r_out"]): ax2.plot([0, L], [yy, yy], lw=0.3, color=INK)
    for i, (x, y) in enumerate(H.holes):
        ax2.add_patch(Circle((x, -y), T["hole_d"] / 2, fc="white", ec=INK, lw=0.6, zorder=4))
        ax2.text(x + 1.6, -y + 1.2, "H%d" % (i + 1), fontsize=5.4, color=RED)
        cl(ax2, (x - 2.2, -y), (x + 2.2, -y)); cl(ax2, (x, -y - 2.2), (x, -y + 2.2))
    for r in A.text_regions("%s REV %s" % (C.PARTS["tube"], C.TEXT["rev"]), 1.6, C.FONT_BOLD, L / 2, -0.8):
        shape(ax2, r, fc="#555", ec="#333", lw=0.1, z=3)
    cl(ax2, (-q(5), 0), (L + q(5), 0))
    x0, x1 = H.holes[0][0], H.holes[2][0]
    dim(ax2, (0, -W / 2), (x0, -W / 2), -q(5), "%.1f" % x0, fs=5.6)
    dim(ax2, (0, -W / 2), (x1, -W / 2), -q(10), "%.1f" % x1, fs=5.6)
    dim(ax2, (0, -T["hole_y"]), (0, T["hole_y"]), -q(8), "%.1f" % (2 * T["hole_y"]), horiz=False, fs=5.6)
    leader(ax2, (x1 + 0.9, T["hole_y"] - 0.9), (x1 - q(30), W / 2 + q(6)), "4x Ø%.1f THRU (one wall)" % T["hole_d"])
    title(ax2, L / 2, -W / 2 - q(19), "BOTTOM VIEW (Z-)  - screw holes + part number")

    # end view (from -X): section of the tube
    s3 = 4.0
    ax3 = view(fig, 190, 175, (-W / 2 - 4, W / 2 + 4, -Hh / 2 - 5, Hh / 2 + 4), s3)
    sec = sscale(H.tube_section(), -1, 1, origin=(0, 0))
    shape(ax3, sec, fc="white", hatch="////////")
    cl(ax3, (-W / 2 - 2, 0), (W / 2 + 2, 0)); cl(ax3, (0, -Hh / 2 - 2), (0, Hh / 2 + 2))
    dim(ax3, (-W / 2, Hh / 2), (W / 2, Hh / 2), 1.5, "%.1f ±0.2" % W, fs=5.4)
    dim(ax3, (W / 2, -Hh / 2), (W / 2, Hh / 2), 1.5, "%.1f ±0.2" % Hh, horiz=False, fs=5.4)
    dim(ax3, (-W / 2 + T["wall"], -Hh / 2), (W / 2 - T["wall"], -Hh / 2), -1.5, "%.1f ref." % (W - 2 * T["wall"]), fs=5.0)
    leader(ax3, (-W / 2 + T["wall"] / 2, -3), (-W / 2 - 1.0, -Hh / 2 - 3.2), "wall %.1f" % T["wall"], fs=5.0, ha="right")
    leader(ax3, (W / 2 - 0.3, Hh / 2 - 0.3), (W / 2 - 1, Hh / 2 + 3.2), "R%.1f / R%.1f [ASSUMED]" % (T["r_out"], T["r_in"]), fs=5.0, ha="right")
    title(ax3, 0, -Hh / 2 - 5, "END VIEW (from ANT end)  %g : 1" % s3)

    rows = [("ID", "Feature", "X", "Y", "Face")]
    for i, (x, y) in enumerate(H.holes):
        rows.append(("H%d" % (i + 1), "Ø%.1f THRU wall" % T["hole_d"], "%.2f" % x, "%+.2f" % y, "bottom (Z-)"))
    fig.text(0.452, 0.535, "HOLE TABLE  (X from the ANT end face, Y from the centre line)", fontsize=6.6, weight="bold")
    table(fig, 0.452, 0.515, rows, [0.025, 0.09, 0.04, 0.04, 0.05])
    notes_block(fig, 0.452, 0.40, [
        "NOTES",
        "1. Material: %s." % C.MATERIAL["tube"],
        "2. Cut to length %.1f ±0.05; both ends faced square to the axis 0.05, deburred." % L,
        "3. Holes H1-H4 in the bottom wall only; position ±0.05 to the ANT end face and the centre line.",
        "4. Marking on the top face: laser marking preferred (hairlines 0.07). If engraved: %.1f deep, Ø0.2 engraver." % T["engrave"],
        "    Artwork: 00_input/BEL_CRL_logo.png and the text as drawn; %s.step governs." % C.PARTS["tube"],
        "5. Finish: %s." % C.FINISH,
        "6. Tolerances %s. Break sharp edges 0.1 max." % C.TOL,
        "7. Inside 22.0 x 12.0 nominal: check the panel spigot (21.7 x 11.8) slides in by hand.",
    ])
    return fig


# ---------------- sheets 2/3: panels ----------------
def panel_geo(H, end):
    """Panel geometry in its own frame: d = depth from the flange OUTSIDE face (0) inward, Y, Z."""
    K = C.PANEL; t = K["t"]
    lugs = []
    for sy in (1, -1):
        g = H.lug_profile()
        lugs.append(SPoly([(t + x, sy * K["lug_y"] + y) for x, y in g.exterior.coords]).buffer(0))
    return dict(t=t, lugs=lugs, tip=t + K["lug_x"] + K["lug_r"], hole_d=t + K["lug_x"])


def sheet_panel(H, end, sheet):
    K = C.PANEL; T = C.TUBE; pn = C.PARTS[end]; s = 3.0
    fig = new_fig(); frame(fig, sheet, 4, pn, C.NAMES[end], C.MATERIAL["panel"], "%g : 1" % s)
    G = panel_geo(H, end); W, Hh = T["W"], T["H"]
    lim = (-W / 2 - 6, W / 2 + 6, -Hh / 2 - 6, Hh / 2 + 5)
    # ---- view 1: outside face ----
    ax = view(fig, 14, 182, lim, s)
    shape(ax, H.flange())
    outline(ax, box(-W / 2 + K["edge_ch"], -Hh / 2 + K["edge_ch"], W / 2 - K["edge_ch"], Hh / 2 - K["edge_ch"]), lw=0.3)
    shape(ax, H.through(end), fc="white", z=3)
    if end == "ant":
        a = K["ant_cb"] / 2; outline(ax, box(-a, -a, a, a), lw=0.6, z=4)
    cl(ax, (-W / 2 - 2, 0), (W / 2 + 2, 0)); cl(ax, (0, -Hh / 2 - 2), (0, Hh / 2 + 2))
    dim(ax, (-W / 2, Hh / 2), (W / 2, Hh / 2), 2.6, "%.2f ±0.05" % W, fs=5.6)
    dim(ax, (-W / 2, -Hh / 2), (-W / 2, Hh / 2), -2.6, "%.2f ±0.05" % Hh, horiz=False, fs=5.6)
    if end == "ant":
        a, b = K["ant_sq"] / 2, K["ant_cb"] / 2
        dim(ax, (-a, -b), (a, -b), -1.6, "%.2f +0.1/0 (□)" % K["ant_sq"], fs=5.2)
        dim(ax, (-b, -Hh / 2), (b, -Hh / 2), -1.4, "%.2f (□) ↧%.2f" % (K["ant_cb"], K["ant_cb_d"]), fs=5.2)
        dim(ax, (a, -a), (a, a), 4.6, "%.2f" % K["ant_sq"], horiz=False, fs=5.2)
    else:
        cz, w, h = K["usb_cz"], K["usb_w"], K["usb_h"]
        dim(ax, (-w / 2, cz - h / 2), (w / 2, cz - h / 2), -2.2, "%.2f +0.1/0" % w, fs=5.2)
        dim(ax, (w / 2, cz - h / 2), (w / 2, cz + h / 2), 2.0, "%.2f +0.1/0" % h, horiz=False, fs=5.2)
        dim(ax, (W / 2, 0), (W / 2, cz), 2.0, "%.2f" % cz, horiz=False, fs=5.2)
        leader(ax, (-w / 2 + 0.4, cz + h / 2 - 0.2), (-W / 2 + 0.5, Hh / 2 + 1.6), "R%.2f full, edges R%.1f" % (h / 2, K["usb_fillet"]), fs=5.0)
    title(ax, 0, lim[2], "VIEW 1 - OUTSIDE FACE")

    # ---- view 2: inside face (from the tube side): flange, spigot, lugs, holes ----
    ax2 = view(fig, 14 + (lim[1] - lim[0]) * s + 10, 182, lim, s)
    YI = lambda y: -y                                            # first angle: inside face mirrored left-right
    shape(ax2, H.flange())
    sp = sscale(H.spigot(end), -1, 1, origin=(0, 0)); shape(ax2, sp, fc="#cfd5da", z=2)
    thr = sscale(H.through(end), -1, 1, origin=(0, 0)); shape(ax2, thr, fc="white", z=3)
    for sy in (1, -1):
        y0, y1 = sorted((YI(sy * K["lug_y"] - K["lug_w"] / 2), YI(sy * K["lug_y"] + K["lug_w"] / 2)))
        for zr in (K["thick_z"], K["thin_z"]):
            shape(ax2, box(y0, zr[0], y1, zr[1]), fc="#b5bdc4", z=4)
        if end == "ant":
            b = K["ant_block"]; shape(ax2, box(YI(sy * K["lug_y"]) - b["y_half"], b["z"][0], YI(sy * K["lug_y"]) + b["y_half"], b["z"][1]), fc="#9aa3ab", z=4)
        cl(ax2, (YI(sy * K["lug_y"]), -Hh / 2 - 1.5), (YI(sy * K["lug_y"]), Hh / 2 + 1.5))
    cl(ax2, (-W / 2 - 2, 0), (W / 2 + 2, 0))
    yl = YI(K["lug_y"])
    dim(ax2, (YI(-K["lug_y"]), Hh / 2), (yl, Hh / 2), 2.6, "%.2f ±0.05" % (2 * K["lug_y"]), fs=5.4)
    dim(ax2, (-K["sp_w"] / 2, -Hh / 2), (K["sp_w"] / 2, -Hh / 2), -1.4, "%.2f 0/-0.1 (spigot)" % K["sp_w"], fs=5.2)
    dim(ax2, (yl - K["lug_w"] / 2, K["sp_z"][1]), (yl + K["lug_w"] / 2, K["sp_z"][1]), 1.0, "%.1f" % K["lug_w"], fs=5.0)
    xr = W / 2 + 0.6
    for (za, zb), off in (((K["sp_z"][0], K["sp_z"][1]), 4.2), ((K["slot"][0], K["slot"][1]), 1.6)):
        dim(ax2, (xr, za), (xr, zb), off, "%.2f" % (zb - za) + (" 0/-0.1" if off > 3 else " +0.1/0 slot"), horiz=False, fs=5.0)
    xl = -W / 2 - 0.6
    for zz, lab in ((K["thick_z"][0], "%.2f" % K["thick_z"][0]), (K["slot"][0], "%.2f" % K["slot"][0]),
                    (K["slot"][1], "%.2f" % K["slot"][1]), (K["thin_z"][1], "%+.2f" % K["thin_z"][1]), (K["sp_z"][1], "%+.2f" % K["sp_z"][1])):
        ax2.plot([xl - 0.2, -K["sp_w"] / 2], [zz, zz], lw=0.25, color=RED, ls=(0, (2, 1)), zorder=6)
        ax2.text(xl - 0.4, zz, lab, fontsize=4.6, color=RED, ha="right", va="center")
    ax2.text(xl - 0.4, Hh / 2 + 1.0, "Z from C", fontsize=4.6, color=RED, ha="right")
    if end == "usb":
        r = K["usb_relief"]
        dim(ax2, (-r["w"] / 2, r["z"][1]), (r["w"] / 2, r["z"][1]), 0.8, "%.1f relief, Z %.2f..%.2f" % (r["w"], r["z"][0], r["z"][1]), fs=4.8)
    title(ax2, 0, lim[2], "VIEW 2 - INSIDE (from the tube)")

    # ---- view 3: top view (from +Z): depth d vertical down, Y horizontal  -> lug profile with R3 ends + nut trap ----
    s3 = 3.0; lim3 = (-W / 2 - 6, W / 2 + 6, -G["tip"] - 7, 4)
    ax3 = view(fig, 14, 90, lim3, s3)
    shape(ax3, box(-W / 2, -G["t"], W / 2, 0))
    shape(ax3, box(-K["sp_w"] / 2, -G["t"] - K["sp_t"], K["sp_w"] / 2, -G["t"]), fc="#cfd5da")
    for lg in G["lugs"]:
        shape(ax3, SPoly([(y, -d) for d, y in lg.exterior.coords]), fc="#b5bdc4", z=3)
    for sy in (1, -1):
        hx = H.hexagon(-G["hole_d"], sy * K["lug_y"], K["nut_af"])
        outline(ax3, SPoly([(y, d) for d, y in hx.exterior.coords]), lw=0.6, z=5)
        ax3.add_patch(Circle((sy * K["lug_y"], -G["hole_d"]), K["hole_d"] / 2, fill=False, ec=INK, lw=0.4, ls=(0, (2, 1)), zorder=5))
        cl(ax3, (sy * K["lug_y"], 1.5), (sy * K["lug_y"], -G["tip"] - 1.5))
        if end == "ant":
            b = K["ant_block"]
            outline(ax3, box(sy * K["lug_y"] - b["y_half"], -G["t"] - b["x"][1], sy * K["lug_y"] + b["y_half"], -G["t"] - b["x"][0]), lw=0.4, ls=(0, (2, 1)), z=5)
    cl(ax3, (-W / 2 - 2, -G["hole_d"]), (W / 2 + 2, -G["hole_d"]))
    yl = K["lug_y"]
    dim(ax3, (-W / 2, 0), (-W / 2, -G["t"]), -1.6, "%.1f" % G["t"], horiz=False, fs=5.0)
    dim(ax3, (-W / 2, -G["t"]), (-W / 2, -G["hole_d"]), -4.6, "%.2f ±0.05" % K["lug_x"], horiz=False, fs=5.0)
    dim(ax3, (W / 2, 0), (W / 2, -G["tip"]), 1.6, "%.1f" % G["tip"], horiz=False, fs=5.0)
    dim(ax3, (K["sp_w"] / 2, -G["t"]), (K["sp_w"] / 2, -G["t"] - K["sp_t"]), 3.6, "%.1f" % K["sp_t"], horiz=False, fs=5.0)
    leader(ax3, (yl + 2.1, -G["hole_d"] - 2.1), (yl + 3.0, -G["tip"] - 3.6), "R%.1f (4x)" % K["lug_r"], fs=5.0)
    leader(ax3, (-yl + 1.0, -G["hole_d"] + 1.5), (-yl + 6.5, -G["tip"] - 3.6),
           "hex %.1f A/F THRU upper lug, corners on the axis,\nR0.3 max in the corners (M2 nut trap)" % K["nut_af"], fs=4.8)
    title(ax3, 0, lim3[2], "VIEW 3 - TOP (from Z+)")

    # ---- section A-A through a lug hole (plane Y = +lug_y): depth d horizontal, Z vertical ----
    lim4 = (-2.5, G["tip"] + 9, -Hh / 2 - 6, Hh / 2 + 5); s4 = 4.0
    ax4 = view(fig, 14 + (lim3[1] - lim3[0]) * s3 + 10, 30, lim4, s4)
    sec = box(0, -Hh / 2, G["t"], Hh / 2).union(box(G["t"], K["sp_z"][0], G["t"] + K["sp_t"], K["sp_z"][1]))
    sec = sec.difference(box(G["t"] - 0.01, K["slot"][0], G["t"] + 5, K["slot"][1]))
    lug_x = (G["t"] + K["sp_t"] - 0.5, G["tip"])
    for zr in (K["thick_z"], K["thin_z"]): sec = sec.union(box(lug_x[0], zr[0], lug_x[1], zr[1]))
    if end == "ant":
        b = K["ant_block"]; sec = sec.union(box(G["t"] + b["x"][0], b["z"][0], G["t"] + b["x"][1], b["z"][1]))
    hd = G["hole_d"]; R = K["nut_af"] / math.sqrt(3)
    sec = sec.difference(box(hd - K["hole_d"] / 2, K["thick_z"][0] - 0.1, hd + K["hole_d"] / 2, K["thick_z"][1] + 0.01))
    sec = sec.difference(box(hd - R, K["thin_z"][0] - 0.01, hd + R, K["thin_z"][1] + 0.1))
    shape(ax4, sec, fc="white", hatch="////////")
    cl(ax4, (hd, -Hh / 2 - 1.5), (hd, Hh / 2 + 1.5))
    dim(ax4, (0, -Hh / 2), (G["t"], -Hh / 2), -1.2, "%.1f" % G["t"], fs=4.8)
    dim(ax4, (0, Hh / 2), (hd, Hh / 2), 1.2, "%.2f" % hd, fs=4.8)
    dim(ax4, (0, Hh / 2), (G["tip"], Hh / 2), 3.0, "%.2f" % G["tip"], fs=4.8)
    zr = K["thick_z"]; dim(ax4, (G["tip"], zr[0]), (G["tip"], zr[1]), 0.8, "%.2f" % (zr[1] - zr[0]), horiz=False, fs=4.8)
    zr = K["thin_z"]; dim(ax4, (G["tip"], zr[0]), (G["tip"], zr[1]), 0.8, "%.2f" % (zr[1] - zr[0]), horiz=False, fs=4.8)
    leader(ax4, (hd + K["hole_d"] / 2, -4.0), (G["tip"] + 1.2, -Hh / 2 - 2.6), "Ø%.1f +0.1/0 THRU lower lug" % K["hole_d"], fs=4.8)
    leader(ax4, (hd + R, 1.0), (G["tip"] + 1.2, Hh / 2 + 1.2), "hex %.1f A/F THRU" % K["nut_af"], fs=4.8)
    ax4.text(G["t"] + K["sp_t"] + 0.4, (K["slot"][0] + K["slot"][1]) / 2, "PCB slot %.1f" % (K["slot"][1] - K["slot"][0]), fontsize=4.6, va="center", color=GRN)
    if end == "ant":
        b = K["ant_block"]; ax4.text(G["t"] + b["x"][1] + 0.3, b["z"][1] + 0.2, "nut stop", fontsize=4.4)
    title(ax4, G["tip"] / 2 + 2, lim4[2], "SECTION A-A (on a lug axis)  %g : 1" % s4)

    tx = 0.60
    rows = [("Feature", "Size", "Position")]
    rows.append(("Flange", "%.1f x %.1f x %.1f" % (W, Hh, G["t"]), "outside 0.2 x 45°"))
    rows.append(("Spigot", "%.2f x %.2f x %.1f" % (K["sp_w"], K["sp_z"][1] - K["sp_z"][0], K["sp_t"]), "Z %.2f..%+.2f" % K["sp_z"]))
    rows.append(("PCB slot", "%.2f +0.1/0" % (K["slot"][1] - K["slot"][0]), "Z %.2f..%.2f" % K["slot"]))
    rows.append(("Lugs (2 pairs)", "%.1f wide, R%.1f" % (K["lug_w"], K["lug_r"]), "Y ±%.2f" % K["lug_y"]))
    rows.append(("Lower lug", "Ø%.1f THRU" % K["hole_d"], "Z %.2f..%.2f" % K["thick_z"]))
    rows.append(("Upper lug", "hex %.1f A/F THRU" % K["nut_af"], "Z %.2f..%+.2f" % K["thin_z"]))
    if end == "ant":
        rows.append(("SMA opening", "□%.2f THRU, □%.2f ↧%.2f" % (K["ant_sq"], K["ant_cb"], K["ant_cb_d"]), "on B / C"))
        b = K["ant_block"]; rows.append(("Nut stops (2)", "%.1f x %.1f x %.1f" % (2 * b["y_half"], b["z"][1] - b["z"][0], b["x"][1] - b["x"][0]), "Z %.1f..%.1f" % b["z"]))
    else:
        rows.append(("USB-C slot", "%.2f x %.2f stadium THRU" % (K["usb_w"], K["usb_h"]), "Z %+.2f" % K["usb_cz"]))
        r = K["usb_relief"]; rows.append(("Spigot relief", "%.1f wide" % r["w"], "Z %.2f..%.2f" % r["z"]))
    fig.text(tx, 0.94, "FEATURES  (Z from the centre line C, Y from B, depth from A)", fontsize=6.4, weight="bold")
    table(fig, tx, 0.92, rows, [0.085, 0.14, 0.10], fs=5.4)
    notes_block(fig, tx, 0.92 - len(rows) * 0.0148 - 0.03, [
        "NOTES",
        "1. Material: %s." % C.MATERIAL["panel"],
        "2. Design = PocketSDR v2.3 printed panel, unchanged; dims from its .3mf.",
        "3. Datum A = flange inside face (seats on the tube end);",
        "    B / C = centre lines of the 25 x 15 outline.",
        "4. Spigot 0/-0.1: slide fit in the tube (inside 22 x 12).",
        "5. Hex nut trap: wire-EDM, or end mill with R0.3 max corners;",
        "    an ISO 4032 M2 nut must press in by hand.",
        "6. Finish: %s." % C.FINISH.replace(", after machining and engraving", ""),
        "7. Tolerances %s; break edges 0.1." % C.TOL,
        "8. %s.step governs where not dimensioned." % pn,
    ], fs=5.3)
    return fig


# ---------------- sheet 4: assembly ----------------
def sheet_assy(H):
    fig = new_fig(); frame(fig, 4, 4, C.PN + "-ASSY", "ASSEMBLY + PARTS LIST", "see parts list", "NTS")
    for (fn, pos, ttl) in ((C.PN + "_ASSY_iso.png", [0.02, 0.50, 0.40, 0.46], "ASSEMBLY"),
                           (C.PN + "_ASSY_xray.png", [0.33, 0.50, 0.36, 0.46], "INSIDE (tube see-through)"),
                           (C.PN + "_ASSY_EXPLODED_iso.png", [0.64, 0.50, 0.35, 0.46], "EXPLODED")):
        p = os.path.join(STEPD, fn)
        if not os.path.exists(p): continue
        ax = fig.add_axes(pos); im = mpimg.imread(p)
        h, w = im.shape[:2]; ax.imshow(im[int(h * 0.1):int(h * 0.9), int(w * 0.08):int(w * 0.92)]); ax.axis("off")
        ax.set_title(ttl, fontsize=8, weight="bold")
    sp = Cm.SUPPLY
    rows = [("Item", "Qty", "Part", "Description", "Supply"),
            ("1", "1", C.PARTS["tube"], "Tube 25 x 15 x 1.5 x 55, marked (sheet 1)", "CNC vendor"),
            ("2", "1", C.PARTS["ant"], "End panel, ANT / SMA (sheet 2)", "CNC vendor"),
            ("3", "1", C.PARTS["usb"], "End panel, USB-C (sheet 3)", "CNC vendor"),
            ("4", "4 + %d" % sp["screw_spare"], C.SCREW["spec"], "Lugs to the tube, through the PCB", "CNC vendor, with spares"),
            ("5", "4 + %d" % sp["nut_spare"], C.NUT["spec"], "In the hex traps of the upper lugs", "CNC vendor, with spares"),
            ("6", "1", "PocketSDR FE 2CH v2.3", "PCB assembly 55 x 21.6 x 1.6 (not in this order)", "BEL CRL")]
    tx, ty = 0.03, 0.44
    fig.text(tx, ty + 0.02, "PARTS LIST  (per case)", fontsize=7.5, weight="bold")
    table(fig, tx, ty, rows, [0.035, 0.035, 0.15, 0.20, 0.13], fs=6.0, dy=0.019)
    notes_block(fig, tx, 0.27, [
        "ASSEMBLY",
        "1. Press one M2 nut into each hex trap of the upper lugs (both panels), flat face toward the PCB slot.",
        "2. Slide the PCB into the USB panel slot (components up = the side of the thin lugs), then into the tube.",
        "3. Fit the ANT panel over the SMA end; both flanges seat on the tube ends (PCB 55.0 = tube 55.0).",
        "4. Fit 4 x M2 x 10 from the bottom face (H1-H4): tube wall -> lower lug -> PCB hole -> nut. 0.2 Nm max.",
        "5. Check: USB-C plug mates fully; SMA nut runs free on the jack; PCB does not rattle.",
        "",
        "Vendor supplies items 1-5 per the parts list, items 4 and 5 with the spares shown.",
        "Marking on the tube (logo, %s, %s) per sheet 1." % (C.TEXT["product"], C.TEXT["date"]),
    ], fs=6.0)
    return fig


def write(H):
    os.makedirs(OUTD, exist_ok=True)
    pdf = os.path.join(OUTD, C.PN + "_DRAWINGS.pdf")
    figs = [sheet_tube(H), sheet_panel(H, "ant", 2), sheet_panel(H, "usb", 3), sheet_assy(H)]
    with PdfPages(pdf) as pp:
        for i, f in enumerate(figs):
            pp.savefig(f); f.savefig(os.path.join(OUTD, "%s_sheet%d.png" % (C.PN, i + 1)), dpi=110); plt.close(f)
    print("drawing ->", os.path.relpath(pdf, C.ROOT))
    return pdf
