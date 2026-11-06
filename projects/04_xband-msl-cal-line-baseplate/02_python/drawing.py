"""CNC manufacturing drawing, A3 landscape, true scale -> ../04_drawings/<PN>_DRAWING.pdf (+ PNG per sheet)
  sheet 1  PLATE: section A-A, end view J1, top view, view from below, section B-B, hole table, notes
  sheet 2  ASSEMBLY: render, exploded render, parts list, assembly notes
Datum for every coordinate: plate outside south-west corner, bottom face (X along the line toward J2, Y, Z up).
Datum A = board pocket floor, datum B = J1 bore axis."""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, Polygon, Circle, Arc, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import box, LineString, Polygon as SPoly
from shapely.ops import unary_union
import config as C
import plate as Pm

OUTD = os.path.join(C.ROOT, "04_drawings")
INK = "#111"; AL = "#e3e7ea"; HAT = "#9aa3ab"; RED = "#b02020"
A3 = (420.0, 297.0)


# ---------------- primitives ----------------
def view(fig, x, y, lim, s):
    """Axes whose data mm map to paper mm at scale s; (x, y) = paper position of the data point (lim[0], lim[2])."""
    w, h = (lim[1] - lim[0]) * s, (lim[3] - lim[2]) * s
    ax = fig.add_axes([x / A3[0], y / A3[1], w / A3[0], h / A3[1]])
    ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3]); ax.set_aspect("equal"); ax.axis("off")
    return ax


def dim(ax, p0, p1, off, text, horiz=True, fs=6.0, col=INK):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = (max(y0, y1) + off) if off > 0 else (min(y0, y1) + off)
        ax.plot([x0, x0], [y0, y + (0.6 if off > 0 else -0.6)], lw=0.3, color=col); ax.plot([x1, x1], [y1, y + (0.6 if off > 0 else -0.6)], lw=0.3, color=col)
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color=col, shrinkA=0, shrinkB=0, mutation_scale=4))
        ax.text((x0 + x1) / 2, y, text, ha="center", va="bottom" if off > 0 else "top", fontsize=fs, color=col)
    else:
        x = (max(x0, x1) + off) if off > 0 else (min(x0, x1) + off)
        ax.plot([x0, x + (0.6 if off > 0 else -0.6)], [y0, y0], lw=0.3, color=col); ax.plot([x1, x + (0.6 if off > 0 else -0.6)], [y1, y1], lw=0.3, color=col)
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<|-|>", lw=0.45, color=col, shrinkA=0, shrinkB=0, mutation_scale=4))
        ax.text(x, (y0 + y1) / 2, text, ha="right" if off < 0 else "left", va="center", fontsize=fs, rotation=90, color=col)


def leader(ax, p, q, text, fs=5.6, ha="left"):
    ax.annotate(text, p, q, fontsize=fs, ha=ha, va="center", arrowprops=dict(arrowstyle="-|>", lw=0.35, color=INK, mutation_scale=4))


def shape(ax, g, fc=AL, ec=INK, lw=0.6, hatch=None, z=1):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        if q.is_empty: continue
        ax.add_patch(Polygon(list(q.exterior.coords), fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z))
        for i in q.interiors: ax.add_patch(Polygon(list(i.coords), fc="white", ec=ec, lw=lw, zorder=z))


def outline(ax, g, ls="-", lw=0.6, col=INK, z=3):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        for ring in [q.exterior] + list(q.interiors):
            xs, ys = zip(*ring.coords); ax.plot(xs, ys, ls=ls, lw=lw, color=col, zorder=z)


def tapped(ax, x, y, d, tap, lw=0.5):
    """Thread symbol (plan view): full circle = tap drill, 3/4 thin circle = major diameter."""
    ax.add_patch(Circle((x, y), tap / 2, fill=False, lw=lw, ec=INK, zorder=4))
    ax.add_patch(Arc((x, y), d, d, theta1=0, theta2=270, lw=0.3, ec=INK, zorder=4))


def cl(ax, p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], lw=0.3, color=INK, ls=(0, (6, 1.5, 1, 1.5)), zorder=5)


def frame(fig, B, sheet, n, title, scale):
    fig.add_artist(Rectangle((0.01, 0.012), 0.98, 0.976, fill=False, lw=1.4, transform=fig.transFigure))
    tb = (0.70, 0.02, 0.28, 0.12)
    fig.add_artist(Rectangle(tb[:2], tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    fig.text(tb[0] + 0.008, tb[1] + 0.092, "BEL - CRL", fontsize=13, weight="bold")
    fig.text(tb[0] + 0.008, tb[1] + 0.075, "ANTENNA / RFM LAB", fontsize=7, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.097, C.TEXT["title"], fontsize=7.4, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.082, "%s mm THRU (%s)" % (B["key"], B["name"]), fontsize=5.2)
    fig.text(tb[0] + 0.105, tb[1] + 0.068, title, fontsize=6.6)
    items = (("PART", B["pn"]), ("DWG", B["pn"] + "-DWG"), ("REV", C.TEXT["rev"]), ("SHEET", "%d / %d" % (sheet, n)),
             ("DATE", C.TEXT["date"]), ("UNITS", "mm"), ("SCALE", scale), ("PROJ.", "1st angle"))
    for i, (k, v) in enumerate(items):
        fig.text(tb[0] + 0.008 + (i % 4) * 0.069, tb[1] + 0.043 - (i // 4) * 0.03, "%s\n%s" % (k, v), fontsize=5.6)


# ---------------- sections ----------------
def section_xz(H, y):
    """Plate cut by the plane y = const, as XZ regions (datum X)."""
    P, K = C.PLATE, C.CONN; ox = -H.x0
    sl = LineString([(H.x0 - 1, y), (H.x1 + 1, y)])
    g = box(H.x0, 0, H.x1, H.z_top)
    for w in H.walls:
        if w.bounds[1] <= y <= w.bounds[3]: g = g.union(box(w.bounds[0], H.z_top, w.bounds[2], H.z_wall))
    pk = sl.intersection(unary_union([H.pocket] + H.notches))
    for seg in (pk.geoms if hasattr(pk, "geoms") else [pk]):
        if not seg.is_empty: x = [c[0] for c in seg.coords]; g = g.difference(box(min(x), H.z_floor, max(x), H.z_top + 50))
    un = sl.intersection(unary_union(H.under))
    for seg in (un.geoms if hasattr(un, "geoms") else [un]):
        if not seg.is_empty: x = [c[0] for c in seg.coords]; g = g.difference(box(min(x), -1, max(x), H.z_under))
    if abs(y) < K["bore_d"] / 2:
        h = (K["bore_d"] ** 2 / 4 - y * y) ** 0.5
        for p in H.ports:
            xa, xb = sorted((p["xf"], p["xf"] - p["ux"] * P["wall"])); g = g.difference(box(xa - 1 if p["ux"] < 0 else xa, H.pin_z - h, xb if p["ux"] < 0 else xb + 1, H.pin_z + h))
    for x, yy, d in H.B["holes"]:
        if abs(y - yy) < 2.5 / 2:
            g = g.difference(box(x - 1.25, -1, x + 1.25, H.z_floor))
    c = P["chamfer"]
    g = g.difference(SPoly([(H.x0 - 0.01, -0.01), (H.x0 + c, -0.01), (H.x0 - 0.01, c)])).difference(SPoly([(H.x1 + 0.01, -0.01), (H.x1 - c, -0.01), (H.x1 + 0.01, c)]))
    from shapely.affinity import translate
    return translate(g, ox, 0)


# ---------------- sheet 1: plate ----------------
def sheet_plate(B, H):
    from shapely.affinity import translate, scale as sscale
    P, K, t = C.PLATE, C.CONN, C.PCB["t"]
    s = 2.5 if H.L <= 60 else 1.5
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    frame(fig, B, 1, 2, "PLATE - CNC MACHINING", "%g : 1" % s)
    ox, oy = -H.x0, H.yo                                   # model -> datum
    L, W = H.L, H.W
    X = lambda x: x + ox; Y = lambda y: y + oy
    q = lambda mm: mm / s                                  # paper mm -> data mm
    mx, myb, myt = q(16), q(15), q(9)                      # view margins (data mm): sides, bottom (title), top
    left, gap = 14.0, 5.0
    x2 = left + (L + 2 * mx) * s + gap                     # second column
    wide = x2 + (L + 2 * mx) * s <= 284.0
    ytop = 286.0

    # ---- row 1: section A-A + end view J1 ----
    hA = H.z_wall + myb + myt
    y1 = ytop - hA * s
    ax2 = view(fig, left, y1, (-mx, L + mx, -myb, H.z_wall + myt), s)
    shape(ax2, section_xz(H, 0.0), fc="white", hatch="////////", ec=INK, lw=0.6)
    ax2.add_patch(Rectangle((X(H.board[0]), H.z_floor), H.board[2] - H.board[0], t, fc="#7fb08a", ec="#2f6b3a", lw=0.4, ls=(0, (2, 1)), alpha=0.45, zorder=4))
    ax2.text(X(H.xw) + q(2), H.z_pcb_top + q(1.0), "cal PCB (ref.) t %.2f [ASSUMED]" % t, ha="left", va="bottom", fontsize=4.8, color="#1f4d29", zorder=6)
    cl(ax2, (-q(4), H.pin_z), (L + q(4), H.pin_z))
    dim(ax2, (0, 0), (0, H.z_wall), -q(9), "%.2f" % H.z_wall, horiz=False, fs=5.6)
    dim(ax2, (0, 0), (0, H.pin_z), -q(4), "%.2f" % H.pin_z, horiz=False, fs=5.6)
    dim(ax2, (L, 0), (L, H.z_top), q(4), "%.2f" % H.z_top, horiz=False, fs=5.6)
    xr = X(H.xe) - q(5)
    dim(ax2, (xr, H.z_floor), (xr, H.pin_z), 0.001, "%.2f ±0.02 " % (H.pin_z - H.z_floor), horiz=False, fs=5.6, col=RED)
    xf = (X(H.xw) + X(H.xe)) / 2
    dim(ax2, (xf, 0), (xf, H.z_floor), 0.001, "%.2f " % H.z_floor, horiz=False, fs=5.6)
    dim(ax2, (0, H.z_wall), (X(H.xw), H.z_wall), q(3), "%.2f" % P["wall"], fs=5.6)
    leader(ax2, (X(H.x0) + P["wall"] * 0.6, H.pin_z + K["bore_d"] / 2), (X(H.xw) + q(10), H.z_wall + q(4)), "Ø%.2f +0.05/0 THRU  (B1, B2)" % K["bore_d"])
    xa = X(H.xw) + q(14)
    ax2.add_patch(Rectangle((xa - q(1.6), H.z_floor - q(4.6)), q(3.2), q(3.2), fc="white", ec=RED, lw=0.5, zorder=6))
    ax2.text(xa, H.z_floor - q(3.0), "A", fontsize=6, color=RED, weight="bold", ha="center", va="center", zorder=7)
    ax2.plot([xa, xa], [H.z_floor - q(1.4), H.z_floor], color=RED, lw=0.5, zorder=7)
    ax2.text(L / 2, -myb + q(1), "SECTION A-A  (on the line axis)", ha="center", va="bottom", fontsize=7, weight="bold")

    ax3 = view(fig, x2, y1, (-mx, W + mx, -myb, H.z_wall + myt), s)
    YE = lambda y: W - Y(y)                                # first angle: view from -X drawn on the right, Y runs right-to-left
    shape(ax3, box(0, 0, W, H.z_top).union(box(YE(P["wall_w"] / 2), H.z_top, YE(-P["wall_w"] / 2), H.z_wall)))
    ax3.add_patch(Circle((YE(0), H.pin_z), K["bore_d"] / 2, fc="white", ec=INK, lw=0.6, zorder=4))
    for _x, hy, hz in H.ports[0]["holes"]: tapped(ax3, YE(hy), hz, 2.5, 2.05)
    cl(ax3, (YE(0), -q(2)), (YE(0), H.z_wall + q(2))); cl(ax3, (YE(7.5), H.pin_z), (YE(-7.5), H.pin_z))
    hs = K["hole_sq"] / 2
    dim(ax3, (YE(hs), H.z_wall), (YE(-hs), H.z_wall), q(3), "%.2f" % K["hole_sq"], fs=5.4)
    dim(ax3, (YE(-hs), H.pin_z - hs), (YE(-hs), H.pin_z + hs), (W - YE(-hs)) + q(4), "%.2f" % K["hole_sq"], horiz=False, fs=5.4)
    dim(ax3, (0, 0), (W, 0), -q(4), "%.2f" % W, fs=5.4)
    dim(ax3, (YE(P["wall_w"] / 2), H.z_top + q(2.5)), (YE(-P["wall_w"] / 2), H.z_top + q(2.5)), 0.001, "%.1f" % P["wall_w"], fs=5.0)
    leader(ax3, (YE(hs) - 0.9, H.pin_z + hs + 0.9), (-mx + q(1), H.z_wall + q(5)), "4x M2.5-6H ↧%.1f  (C1-C4; J2 face: C5-C8)" % K["tap_depth"], fs=5.2)
    ax3.text(W / 2, -myb + q(1), "VIEW J1  (from -X)", ha="center", va="bottom", fontsize=7, weight="bold")

    # ---- row 2: top view (+ view from below when it fits) ----
    hT = W + myb + myt
    y2 = y1 - hT * s - 2
    ax = view(fig, left, y2, (-mx, L + mx, -myb, W + myt), s)
    plate = H._rrect(X(H.x0), 0, X(H.x1), W, P["corner_r"])
    shape(ax, plate)
    pk = translate(unary_union([H.pocket] + H.notches).intersection(box(H.x0, -H.yo, H.x1, H.yo)), ox, oy)
    shape(ax, pk, fc="#f6f7f8", lw=0.6, z=2)
    for w in H.walls: shape(ax, translate(w, ox, oy), fc="#cfd5da", lw=0.6, z=2)
    for u in H.under: outline(ax, translate(u, ox, oy), ls=(0, (3, 2)), lw=0.3, col="#777")
    for x, y, _d in B["holes"]: tapped(ax, X(x), Y(y), 3.0, 2.5)
    cl(ax, (-q(6), Y(0)), (L + q(6), Y(0)))
    for p in H.ports:
        ax.text(X(p["xf"] - p["ux"] * P["wall"] / 2), Y(0) + q(5), p["label"], ha="center", va="center", fontsize=6.5, weight="bold", zorder=6)
    yb = max(P["rib"] / 2 + 1.0, min(abs(y) for _x, y, _d in B["holes"]) - 3.0)
    cl(ax, (-q(6), Y(yb)), (-0.3, Y(yb))); cl(ax, (L + 0.3, Y(yb)), (L + q(6), Y(yb)))
    for xx, ha in ((-q(7), "right"), (L + q(7), "left")):
        ax.text(xx, Y(0), "A", color=RED, fontsize=7, weight="bold", ha=ha, va="center")
        ax.text(xx, Y(yb), "B", color=RED, fontsize=7, weight="bold", ha=ha, va="center")
    for x_ in (-q(5), L + q(5)):
        for yy in (Y(0), Y(yb)):
            ax.annotate("", (x_, yy + q(3)), (x_, yy), arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.5, mutation_scale=5))
    dim(ax, (0, 0), (L, 0), -q(9), "%.2f" % L)
    dim(ax, (0, 0), (0, W), -q(10), "%.2f" % W, horiz=False)
    dim(ax, (X(H.xw), Y(-H.yp)), (X(H.xe), Y(-H.yp)), -q(4.5), "%.2f +0.10/+0.05" % (H.xe - H.xw), fs=5.6)
    xb_ = X(H.board[2]) - q(9)
    dim(ax, (xb_, Y(-H.yp)), (xb_, Y(H.yp)), 0.001, "%.2f +0.10/+0.05 " % (2 * H.yp), horiz=False, fs=5.6)
    dim(ax, (0, Y(H.yp)), (0, W), -q(4), "%.2f" % (W / 2 - H.yp), horiz=False, fs=5.0)
    xc = (X(H.board[0]) + X(H.board[2])) / 2
    dim(ax, (xc - P["notch_w"] / 2, W), (xc + P["notch_w"] / 2, W), q(3), "%.1f (2x)" % P["notch_w"], fs=5.6)
    dim(ax, (0, W), (xc, W), q(7), "%.2f" % xc, fs=5.6)
    leader(ax, (X(H.xw) + 0.65, Y(H.yp) - 0.65), (X(H.xw) + q(16), W + q(5)), "R%.1f (4x)" % H.pocket_r)
    leader(ax, (X(H.x1) - 0.9, W - 0.9), (L + q(2), W + q(6)), "R%.0f (4x)" % P["corner_r"])
    x3, y3 = X(B["holes"][0][0]), Y(B["holes"][0][1])
    leader(ax, (x3 + 1.1, y3 - 1.1), (x3 + q(14), -q(5)), "4x M3-6H THRU  (A1-A4, hole table)")
    ax.text(L / 2, -myb + q(1), "TOP VIEW", ha="center", va="bottom", fontsize=7, weight="bold")

    def below(ax5):
        YB = lambda y: W - Y(y)                            # seen from below: Y mirrored
        shape(ax5, plate)
        for u in H.under: shape(ax5, translate(sscale(u, 1, -1, origin=(0, 0)), ox, oy), fc="#f6f7f8", lw=0.5, z=2)
        for x, y, _d in B["holes"]: tapped(ax5, X(x), YB(y), 3.0, 2.5)
        cl(ax5, (-q(3), Y(0)), (L + q(3), Y(0)))
        ub = max(H.under, key=lambda g: g.bounds[0]).bounds
        dim(ax5, (X(ub[0]), W), (X(ub[2]), W), q(3), "%.2f" % (ub[2] - ub[0]), fs=5.2)
        dim(ax5, (L, YB(ub[1])), (L, YB(ub[3])), q(4), "%.2f" % (ub[3] - ub[1]), horiz=False, fs=5.2)
        dim(ax5, (L, Y(-P["rib"] / 2)), (L, Y(P["rib"] / 2)), q(10), "%.1f" % P["rib"], horiz=False, fs=5.0)
        ax5.text(L / 2, -myb + q(1), "VIEW FROM BELOW  (pockets ↧%.2f, R%.0f min)" % (H.z_under, P["tool_r"]), ha="center", va="bottom", fontsize=7, weight="bold")

    # ---- row 3: section B-B (+ view from below in row 4 when it did not fit in row 2) ----
    y3_ = y2 - hA * s - 2
    if wide:
        below(view(fig, x2, y2, (-mx, L + mx, -myb, W + myt), s))
    ax4 = view(fig, left, y3_, (-mx, L + mx, -myb, H.z_wall + myt), s)
    shape(ax4, section_xz(H, yb), fc="white", hatch="////////", ec=INK, lw=0.6)
    xu = (min(g.bounds[2] for g in H.under) + max(g.bounds[0] for g in H.under)) / 2 + ox
    dim(ax4, (xu - q(3), 0), (xu - q(3), H.z_under), 0.001, "%.2f " % H.z_under, horiz=False, fs=5.6)
    dim(ax4, (xu + q(3), H.z_under), (xu + q(3), H.z_floor), 0.001, " %.2f" % (H.z_floor - H.z_under), horiz=False, fs=5.6)
    ax4.text(L / 2, -myb + q(1), "SECTION B-B  (Y %.2f)" % Y(yb), ha="center", va="bottom", fontsize=7, weight="bold")
    if not wide:
        below(view(fig, left, y3_ - hT * s - 2, (-mx, L + mx, -myb, W + myt), s))

    # ---- hole table + notes (right column) ----
    rows = [("ID", "Feature", "X", "Y", "Z", "Face")]
    for i, (x, y, _d) in enumerate(B["holes"]):
        rows.append(("A%d" % (i + 1), "M3-6H THRU (drill Ø2.5)", "%.2f" % X(x), "%.2f" % Y(y), "%.2f" % H.z_floor, "floor (-Z)"))
    for j, p in enumerate(H.ports):
        f = "%s (%sX)" % (p["label"], "-" if p["ux"] < 0 else "+")
        rows.append(("B%d" % (j + 1), "Ø%.2f +0.05/0 THRU wall" % K["bore_d"], "%.2f" % X(p["xf"]), "%.2f" % Y(0), "%.2f" % H.pin_z, f))
        for k, (_hx, hy, hz) in enumerate(p["holes"]):
            rows.append(("C%d" % (4 * j + k + 1), "M2.5-6H ↧%.1f (drill Ø2.05 ↧%.1f)" % (K["tap_depth"], K["tap_depth"] + 0.6), "%.2f" % X(p["xf"]), "%.2f" % Y(hy), "%.2f" % hz, f))
    tx, ty = 0.695, 0.945
    fig.text(tx, ty + 0.016, "HOLE TABLE  (datum: plate SW corner, bottom face)", fontsize=6.6, weight="bold")
    cw = [0.022, 0.125, 0.035, 0.035, 0.03, 0.05]
    for r_i, row in enumerate(rows):
        xx = tx
        for c_i, cell in enumerate(row):
            fig.text(xx, ty - r_i * 0.0148, cell, fontsize=5.3, weight="bold" if r_i == 0 else "normal"); xx += cw[c_i]
    notes = [
        "NOTES",
        "1. Material: %s, from plate." % P["material"],
        "2. Finish: chromate conversion MIL-DTL-5541 Type II Class 3,",
        "    clear (conductive), all over, after machining.",
        "3. Tolerances %s; hole positions ±0.05." % P["tolerance"],
        "4. Datum A = pocket floor, flatness 0.02. Bore axis B1/B2 to A",
        "    %.2f ±0.02; B1-B2 coaxial Ø0.05; wall inner faces ⊥ A 0.03." % (H.pin_z - H.z_floor),
        "5. Bore height is for a %.2f mm cal PCB [ASSUMED]. Confirm the" % t,
        "    board thickness before machining: axis = A + t + %.2f." % (K["pin_d"] / 2),
        "6. Flange faces J1 / J2: flat 0.02, Ra 1.6, bores deburred.",
        "7. Break sharp edges 0.2 max; bottom outside edges %.1f x 45°." % P["chamfer"],
        "8. Engrave %.1f deep, Arial Bold: '%s REV %s' on the -Y" % (P["engrave_depth"], B["pn"], C.TEXT["rev"]),
        "    face (h 2.0), 'J1' / 'J2' on the wall tops (h 2.2).",
        "9. Underside pockets: D4 end mill min. Mass %.1f g." % getattr(H, "mass_g", 0.0),
        "10. %s_PLATE.step governs where not dimensioned." % B["pn"],
    ]
    y0n = ty - len(rows) * 0.0148 - 0.03
    for i, n_ in enumerate(notes):
        fig.text(tx, y0n - i * 0.0135, n_, fontsize=6.6 if i == 0 else 5.4, weight="bold" if i == 0 else "normal")
    return fig


# ---------------- sheet 2: assembly ----------------
def sheet_assy(B, H):
    P, K = C.PLATE, C.CONN
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    frame(fig, B, 2, 2, "ASSEMBLY + PARTS LIST", "NTS")
    st = os.path.join(C.ROOT, "03_step")
    for (fn, pos, ttl) in ((B["pn"] + "_ASSY_iso.png", [0.03, 0.42, 0.46, 0.54], "ASSEMBLY"),
                           (B["pn"] + "_ASSY_EXPLODED_iso.png", [0.50, 0.42, 0.48, 0.54], "EXPLODED"),
                           (B["pn"] + "_PLATE_bottom.png", [0.03, 0.03, 0.30, 0.37], "PLATE FROM BELOW")):
        p = os.path.join(st, fn)
        if not os.path.exists(p): continue
        ax = fig.add_axes(pos); im = mpimg.imread(p)
        h, w = im.shape[:2]; ax.imshow(im[int(h * 0.12):int(h * 0.9), int(w * 0.1):int(w * 0.9)]); ax.axis("off")
        ax.set_title(ttl, fontsize=8, weight="bold")
    rows = [("Item", "Qty", "Part", "Description"),
            ("1", "1", B["pn"] + "_PLATE", "Base plate, %s (sheet 1)" % P["material"].split(",")[0]),
            ("2", "1", B["name"], "Cal PCB (customer), MSL-SL-MSL THRU %s mm" % B["key"]),
            ("3", "2", "23_SMA-50-0-272/133_N", "H+S SMA jack, 4-hole flange, pin on the launch pad"),
            ("4", "8", "ISO 4762 M2.5 x 5", "A2-70, flange screws, 0.4 Nm"),
            ("5", "4", "ISO 4762 M3 x %g" % P["m3_screw_len"], "A2-70, PCB to plate, 0.6 Nm"),
            ("6", "-", "Sn62Pb36Ag2 / SAC305", "Solder: SMA pin to the launch pad")]
    tx, ty = 0.36, 0.36
    fig.text(tx, ty + 0.02, "PARTS LIST", fontsize=7.5, weight="bold")
    cw = [0.03, 0.025, 0.12, 0.17]
    for r_i, row in enumerate(rows):
        xx = tx
        for c_i, cell in enumerate(row):
            fig.text(xx, ty - r_i * 0.019, cell, fontsize=6, weight="bold" if r_i == 0 else "normal"); xx += cw[c_i]
    notes = ["ASSEMBLY",
             "1. Clean the pocket floor and the PCB bottom ground (IPA). No paste/foil under the board.",
             "2. Drop the PCB into the pocket (L1 up, J1 end = DXF x min); fit 4 x M3 x %g, finger tight." % P["m3_screw_len"],
             "3. Fit both SMA jacks through the walls (pin on the launch pad), 4 x M2.5 x 5 each, 0.4 Nm.",
             "4. Push the PCB toward neither wall: the pocket centres it (%.2f gap each end); torque M3 to 0.6 Nm." % (P["clr_x"] - (K["spigot_len"] - P["wall"])),
             "5. Solder each pin to its pad with a small fillet; check the pin is not lifted (gap < 0.05).",
             "6. Check: DC continuity J1-J2 centre, no short to ground; then S-parameters 8-12 GHz."]
    for i, n_ in enumerate(notes):
        fig.text(0.36, 0.20 - i * 0.017, n_, fontsize=6.6 if i == 0 else 5.8, weight="bold" if i == 0 else "normal")
    return fig


def write(B, H):
    os.makedirs(OUTD, exist_ok=True)
    pdf = os.path.join(OUTD, B["pn"] + "_DRAWING.pdf")
    with PdfPages(pdf) as pp:
        for i, f in enumerate((sheet_plate(B, H), sheet_assy(B, H))):
            pp.savefig(f); f.savefig(os.path.join(OUTD, "%s_sheet%d.png" % (B["pn"], i + 1)), dpi=110); plt.close(f)
    print("drawing ->", os.path.relpath(pdf, C.ROOT))
    return pdf
