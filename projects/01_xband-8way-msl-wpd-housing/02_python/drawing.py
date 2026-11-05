"""Manufacturing drawings, A3 landscape, multi-sheet PDF -> ../04_drawings/<PN>_DRAWINGS.pdf (+ PNG per sheet)
  1 BASE   2 LID (top + cage underside)   3 GASKET, PCB V3, ASSEMBLY   4 HOLE TABLE
Datum for every coordinate: outside south-west corner of the base, bottom face (X east, Y north, Z up)."""
import os, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import LineString
import config as C
import housing as Hm
import report

OUTD = os.path.join(C.ROOT, "04_drawings")
INK = "#111"; AL = "#dfe3e7"; AL2 = "#c9d0d6"


def rr(ax, cx, cy, w, h, r, **kw):
    ax.add_patch(FancyBboxPatch((cx - w / 2 + r, cy - h / 2 + r), w - 2 * r, h - 2 * r, boxstyle="round,pad=%g" % r, **kw))


def dim(ax, p0, p1, off, text, horiz=True, fs=6):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = max(y0, y1) + off if off > 0 else min(y0, y1) + off
        ax.plot([x0, x0], [y0, y], lw=0.3, color=INK); ax.plot([x1, x1], [y1, y], lw=0.3, color=INK)
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + (0.8 if off > 0 else -0.8), text, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:
        x = max(x0, x1) + off if off > 0 else min(x0, x1) + off
        ax.plot([x0, x], [y0, y0], lw=0.3, color=INK); ax.plot([x1, x], [y1, y1], lw=0.3, color=INK)
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK, shrinkA=0, shrinkB=0))
        ax.text(x + (0.8 if off > 0 else -0.8), (y0 + y1) / 2, text, ha="left" if off > 0 else "right", va="center", fontsize=fs, rotation=90)


def poly(ax, g, hole_fc="white", **kw):
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        ax.add_patch(Polygon(list(q.exterior.coords), **kw))
        for i in q.interiors: ax.add_patch(Polygon(list(i.coords), fc=hole_fc, ec=kw.get("ec", "none"), lw=kw.get("lw", 0.3)))


def frame(fig, sheet, n, title, part):
    fig.add_artist(Rectangle((0.01, 0.01), 0.98, 0.98, fill=False, lw=1.4, transform=fig.transFigure))
    tb = (0.70, 0.02, 0.28, 0.115)
    fig.add_artist(Rectangle(tb[:2], tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    fig.text(tb[0] + 0.008, tb[1] + 0.085, "BEL - CRL", fontsize=13, weight="bold")
    fig.text(tb[0] + 0.008, tb[1] + 0.068, "ANTENNA / RFM LAB", fontsize=7, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.090, C.TEXT["title"], fontsize=7.6, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.073, title, fontsize=6.6)
    items = (("PART", part), ("DWG", C.TEXT["pn"] + "-DWG"), ("REV", "V3"), ("SHEET", "%d / %d" % (sheet, n)),
             ("DATE", C.TEXT["date"]), ("UNITS", "mm"), ("PROJ.", "1st angle"), ("TOL.", "ISO 2768-mK"))
    for i, (k, v) in enumerate(items):
        fig.text(tb[0] + 0.008 + (i % 4) * 0.069, tb[1] + 0.040 - (i // 4) * 0.028, "%s\n%s" % (k, v), fontsize=5.6)


def finish(ax):
    ax.set_aspect("equal"); ax.autoscale_view(); ax.axis("off"); ax.margins(0.07)


# ---------------- sheet 1: base ----------------
def base_top(ax, H):
    X, K = C.BOX, C.CONN
    rr(ax, 0, 0, H.Lo, H.Wo, X["outer_r"], fc=AL, ec=INK, lw=0.9)
    rr(ax, 0, 0, H.Lc, H.Wc, X["cav_r"], fc="white", ec=INK, lw=0.7)
    for sx in (-1, 1):
        for sy in (-1, 1): ax.add_patch(Circle((sx * H.Lc / 2, sy * H.Wc / 2), X["corner_relief_d"] / 2, fc="white", ec=INK, lw=0.5))
    for x, y in H.lid_screws: ax.add_patch(Circle((x, y), Hm.THREAD["M2.5"]["d"] / 2, fc="white", ec="b", lw=0.5))
    for x, y, w in H.holes: ax.add_patch(Circle((x, y), 1.0, fc="white", ec="m", lw=0.6))
    for x, y in H.dowels: ax.add_patch(Circle((x, y), 1.0, fc="#ffd24d", ec=INK, lw=0.5))
    for x, y in H.mount: ax.add_patch(Circle((x, y), 1.5, fc="none", ec="g", lw=0.5, ls="--"))
    for p in H.ports:
        ux = p["u"][0]; x0 = ux * H.Lo / 2
        ax.add_patch(Rectangle((min(x0, x0 - ux * X["wall"]), p["y"] - K["bore_d"] / 2), X["wall"], K["bore_d"], fc="none", ec=INK, lw=0.4, ls="--"))
        ax.text(x0 + ux * 2.0, p["y"], p["label"], fontsize=5, ha="left" if ux > 0 else "right", va="center", weight="bold")
    ax.add_patch(Circle((H.earth[0] - 1.6, H.earth[1]), 1.5, fc="none", ec="g", lw=0.6)); ax.text(H.earth[0] - 4, H.earth[1], "GND M3", fontsize=4.5, ha="right", va="center", color="g")
    dim(ax, (-H.Lo / 2, H.Wo / 2), (H.Lo / 2, H.Wo / 2), 8, "%.2f" % H.Lo)
    dim(ax, (-H.Lc / 2, H.Wc / 2), (H.Lc / 2, H.Wc / 2), 3.5, "%.3f cavity +0.05/0" % H.Lc, fs=5)
    dim(ax, (-H.Lo / 2, -H.Wo / 2), (-H.Lo / 2, H.Wo / 2), -9, "%.2f" % H.Wo, horiz=False)
    dim(ax, (H.Lc / 2, -H.Wc / 2), (H.Lc / 2, H.Wc / 2), 12, "%.3f cavity +0.05/0" % H.Wc, horiz=False, fs=5)
    ax.text(0, -H.Wo / 2 - 8, "blue M2.5 lid taps (%d)   magenta M2 PCB taps (%d)   yellow dowel d2 (2)   green dashed M3 mounting taps from below (4)\n"
            "dashed: d%.2f connector bores through the wall.   Corner reliefs d%.1f.   All coordinates in the hole table (sheet 4)."
            % (len(H.lid_screws), len(H.holes), K["bore_d"], X["corner_relief_d"]), fontsize=5, ha="center", va="top")
    ax.set_title("BASE %s-01 - TOP VIEW" % C.TEXT["pn"], fontsize=8, weight="bold")


def wall_view(ax, H, wall):
    X, K = C.BOX, C.CONN
    ax.add_patch(Rectangle((-H.Wo / 2, 0), H.Wo, H.z_wall, fc=AL, ec=INK, lw=0.8))
    s = 1 if wall == "E" else -1        # seen from outside: E wall has north on the right (+y), W wall has south on the right
    for p in H.ports:
        if p["wall"] != wall: continue
        yv = s * p["y"]
        ax.add_patch(Rectangle((yv - K["flange"] / 2, H.pin_z - K["flange"] / 2), K["flange"], K["flange"], fc="none", ec="#888", lw=0.4, ls=":"))
        ax.add_patch(Circle((yv, H.pin_z), K["bore_d"] / 2, fc="white", ec=INK, lw=0.6))
        for hx, hy, hz in p["holes"]: ax.add_patch(Circle((s * hy, hz), 1.25, fc="white", ec="b", lw=0.4))
        ax.text(yv, H.pin_z + K["flange"] / 2 + 1.0, p["label"], fontsize=5, ha="center", weight="bold")
    if wall == "W":
        ax.add_patch(Circle((s * H.earth[1], H.earth[2]), 1.5, fc="white", ec="g", lw=0.6))
        ax.text(s * H.earth[1], H.earth[2] + 2.5, "M3x%.0f GND" % X["earth_depth"], fontsize=4.5, ha="center", color="g")
    ax.text(-H.Wo / 2, -2.5, "S" if wall == "E" else "N", fontsize=6, weight="bold"); ax.text(H.Wo / 2, -2.5, "N" if wall == "E" else "S", fontsize=6, weight="bold", ha="right")
    dim(ax, (-H.Wo / 2, 0), (-H.Wo / 2, H.pin_z), -4, "%.3f axis" % H.pin_z, horiz=False, fs=5)
    dim(ax, (H.Wo / 2, 0), (H.Wo / 2, H.z_wall), 4, "%.3f" % H.z_wall, horiz=False, fs=5)
    ax.set_title("%s WALL (seen from outside): d%.2f bores, 4 x M2.5x%.0f per flange on %.2f sq" % (wall, K["bore_d"], K["screw_tap_depth"], K["hole_sq"]), fontsize=7, weight="bold")


def base_section(ax, H):
    X = C.BOX
    z = H
    ax.add_patch(Polygon([(-H.Lo / 2, 0), (H.Lo / 2, 0), (H.Lo / 2, H.z_wall), (H.Lc / 2, H.z_wall), (H.Lc / 2, H.floor), (-H.Lc / 2, H.floor), (-H.Lc / 2, H.z_wall), (-H.Lo / 2, H.z_wall)], fc=AL, ec=INK, lw=0.8, hatch="///"))
    ax.add_patch(Rectangle((-H.B["L"] / 2, H.floor), H.B["L"], C.BOARD["t"], fc="#2f6b3a", ec=INK, lw=0.3))
    ax.add_patch(Rectangle((-H.Lo / 2, H.pin_z - C.CONN["bore_d"] / 2), X["wall"], C.CONN["bore_d"], fc="white", ec=INK, lw=0.4))
    ax.plot([-H.Lo / 2 - 4, -H.Lc / 2 + 4], [H.pin_z, H.pin_z], lw=0.4, ls="-.", color="r")
    dim(ax, (H.Lo / 2, 0), (H.Lo / 2, H.floor), 3, "%.3f floor" % H.floor, horiz=False, fs=5)
    dim(ax, (H.Lo / 2, H.floor), (H.Lo / 2, H.z_pcb_top), 11, "PCB %.3f" % C.BOARD["t"], horiz=False, fs=5)
    dim(ax, (-H.Lo / 2, H.z_wall), (-H.Lc / 2, H.z_wall), 2.5, "%.1f wall" % X["wall"], fs=5)
    ax.text(0, H.z_wall + 2, "SECTION A-A (y = 0, through IN): pin axis %.3f = PCB top + 0.63" % H.pin_z, fontsize=6, ha="center")


def sheet_base(H):
    fig = plt.figure(figsize=(16.54, 11.69))
    a = fig.add_axes([0.02, 0.05, 0.40, 0.90]); base_top(a, H); finish(a)
    b = fig.add_axes([0.44, 0.72, 0.54, 0.24]); wall_view(b, H, "E"); finish(b)
    c = fig.add_axes([0.44, 0.50, 0.54, 0.20]); wall_view(c, H, "W"); finish(c)
    d = fig.add_axes([0.44, 0.33, 0.54, 0.15]); base_section(d, H); finish(d)
    X = C.BOX
    notes = ["NOTES - BASE",
             "1. Material %s. Finish: %s." % (X["material"], X["finish"]),
             "2. Tolerances %s. Cavity, bores and dowel holes +/-0.02." % X["tolerance"].split(";")[0],
             "3. Lid seat (wall top) flat 0.03, Ra 0.8. Cavity floor flat 0.03 (PCB ground contact).",
             "4. Connector bores d%.2f +0.02/0 through, coaxial with the flange tap pattern 8.64 sq." % C.CONN["bore_d"],
             "5. Corners of the cavity: R%.1f with d%.1f reliefs (square PCB corners)." % (X["cav_r"], X["corner_relief_d"]),
             "6. Break edges: base bottom %.1f x 45, vertical outside edges R%.0f, all others 0.2 max." % (X["chamfer_base"], X["outer_r"]),
             "7. Engrave %.1f deep on the W wall: RF IN, GND. Fill white (optional)." % X["engrave_depth"],
             "8. Press 2 x ISO 8734 2 m6 x 8 dowels %.0f deep into the wall top." % X["dowel_depth"],
             "9. 3D model: %s_BASE.step (governs where this sheet is silent)." % C.TEXT["pn"]]
    fig.text(0.44, 0.30, "\n".join(notes), fontsize=6.6, va="top", family="monospace")
    frame(fig, 1, 4, "BASE - machining", C.TEXT["pn"] + "-01")
    return fig


# ---------------- sheet 2: lid ----------------
def lid_top(ax, H):
    X = C.BOX
    rr(ax, 0, 0, H.Lo, H.Wo, X["outer_r"], fc=AL, ec=INK, lw=0.9)
    regs, layout = Hm.lid_artwork(H)
    for g in regs: poly(ax, g, fc="#222", ec="none", hole_fc=AL)
    for x, y in H.lid_screws: ax.add_patch(Circle((x, y), X["lid_clear_d"] / 2, fc="white", ec=INK, lw=0.4))
    ax.add_patch(Circle(H.dowels[0], 1.0, fc="#ffd24d", ec=INK, lw=0.5)); ax.text(H.dowels[0][0], H.dowels[0][1] - 3.5, "d2 H7", fontsize=4.5, ha="center")
    x1, y1 = H.dowels[1]; ax.add_patch(Rectangle((x1 - 1.5, y1 - 1.0), 3.0, 2.0, fc="#ffd24d", ec=INK, lw=0.5)); ax.text(x1, y1 + 3.0, "d2 H7 slot", fontsize=4.5, ha="center")
    for x, y in H.jacks: ax.add_patch(Circle((x, y), 1.5, fc="#9fd3ff", ec=INK, lw=0.4)); ax.text(x, y + (-3.5 if y > 0 else 3.0), "M3 JACK", fontsize=4.5, ha="center")
    ly = layout[0][3]
    dim(ax, (-C.TEXT["logo_w"] / 2, ly + layout[0][2] / 2), (C.TEXT["logo_w"] / 2, ly + layout[0][2] / 2), 4, "logo %.0f" % C.TEXT["logo_w"], fs=5)
    dim(ax, (-H.Lo / 2, H.Wo / 2), (H.Lo / 2, H.Wo / 2), 8, "%.2f" % H.Lo)
    dim(ax, (-H.Lo / 2, -H.Wo / 2), (-H.Lo / 2, H.Wo / 2), -8, "%.2f" % H.Wo, horiz=False)
    ax.set_title("LID %s-02 - TOP: engrave %.1f deep (artwork: dxf_src/lid_engraving.dxf)" % (C.TEXT["pn"], X["engrave_depth"]), fontsize=8, weight="bold")


def lid_under(ax, H):
    """Seen from below, drawn in the top-view frame (x not mirrored) so it overlays the board."""
    Q = C.CAGE; X = C.BOX
    rr(ax, 0, 0, H.Lo, H.Wo, X["outer_r"], fc=AL, ec=INK, lw=0.8)
    poly(ax, H.foot, fc=AL2, ec=INK, lw=0.6)
    poly(ax, H.channels.intersection(H.foot), fc="white", ec=INK, lw=0.4)
    poly(ax, H.B["sig"], fc="#e6b37a", ec="none", lw=0)
    for x, y, w in H.holes: ax.add_patch(Circle((x, y), Q["screw_pocket_d"] / 2, fc="white", ec="m", lw=0.5))
    ax.set_title("LID - CAGE (underside, shown in the top-view frame): grey = face %.2f above PCB, white = channels %.2f deep\n"
                 "channels %.1f mm from the copper (orange = board copper for reference), magenta = d%.1f x %.2f head pockets"
                 % (Q["gap"], Q["ch_air"] - Q["gap"], Q["wall_offset"], Q["screw_pocket_d"], Q["screw_pocket_h"] - Q["gap"]), fontsize=7, weight="bold")


def lid_section(ax, H):
    X, Q = C.BOX, C.CAGE
    hb = H.z_wall - H.z_face
    ax.add_patch(Rectangle((-H.Lo / 2, H.z_wall), H.Lo, X["t_lid"], fc=AL, ec=INK, lw=0.8, hatch="\\\\\\"))
    line = LineString([(-H.Lc / 2, 0.0), (H.Lc / 2, 0.0)])
    ch = H.channels.intersection(H.foot).intersection(line)
    segs = sorted([(g.bounds[0], g.bounds[2]) for g in (ch.geoms if hasattr(ch, "geoms") else [ch]) if not g.is_empty])
    fx0, fx1 = H.foot.bounds[0], H.foot.bounds[2]
    ax.add_patch(Rectangle((fx0, H.z_face), fx1 - fx0, hb, fc=AL, ec=INK, lw=0.6, hatch="\\\\\\"))
    for a, b in segs: ax.add_patch(Rectangle((a, H.z_face - 0.01), b - a, Q["ch_air"] - Q["gap"], fc="white", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-H.B["L"] / 2, H.floor), H.B["L"], C.BOARD["t"], fc="#2f6b3a", ec=INK, lw=0.3))
    ax.add_patch(Rectangle((-H.B["L"] / 2, H.z_pcb_top), H.B["L"], Q["gap"], fc="#555", ec="none"))
    dim(ax, (H.Lo / 2, H.z_pcb_top), (H.Lo / 2, H.z_face), 3, "%.2f gasket" % Q["gap"], horiz=False, fs=4.5)
    dim(ax, (H.Lo / 2, H.z_face), (H.Lo / 2, H.z_wall), 10, "%.2f cage" % hb, horiz=False, fs=5)
    dim(ax, (H.Lo / 2, H.z_wall), (H.Lo / 2, H.z_top), 3, "%.1f" % X["t_lid"], horiz=False, fs=5)
    if segs:
        a, b = segs[0]; dim(ax, (a, H.z_face), (a, H.z_pcb_top + Q["ch_air"]), -3, "%.1f air" % Q["ch_air"], horiz=False, fs=4.5)
    ax.text(0, H.z_top + 2, "SECTION B-B (y = 0) lid on base: channel over the IN line, cage face on the gasket", fontsize=6, ha="center")


def sheet_lid(H):
    fig = plt.figure(figsize=(16.54, 11.69))
    a = fig.add_axes([0.02, 0.05, 0.36, 0.90]); lid_top(a, H); finish(a)
    b = fig.add_axes([0.38, 0.05, 0.36, 0.90]); lid_under(b, H); finish(b)
    c = fig.add_axes([0.75, 0.70, 0.23, 0.18]); lid_section(c, H); finish(c)
    X, Q = C.BOX, C.CAGE
    notes = ["NOTES - LID", "1. Material / finish as the base.",
             "2. Cage face flat 0.03 and parallel", "   to the lid seat 0.03; Ra 1.6.",
             "3. Channels: D2 end mill, R1 min,", "   depth %.2f +0.05/0 from the face." % (Q["ch_air"] - Q["gap"]),
             "   Outline: dxf_src/lid_channels.dxf.",
             "4. Engraving %.1f deep: laser or" % X["engrave_depth"], "   D0.2 V-cutter (logo strokes 0.3).",
             "   Text: logo, title, P/N, DATE %s," % C.TEXT["date"], "   S/N field, IN / 1-8 port labels.",
             "5. Lid holes: %d x d%.1f for M2.5x8" % (len(H.lid_screws), X["lid_clear_d"]), "   ISO 7380; d2 H7 hole + slot;",
             "   2 x M3 jacking taps through.",
             "6. Break edges: top %.1f x 45, R%.0f." % (X["chamfer_lid"], X["outer_r"]),
             "7. Model: %s_LID.step." % C.TEXT["pn"]]
    fig.text(0.755, 0.66, "\n".join(notes), fontsize=6.4, va="top", family="monospace")
    frame(fig, 2, 4, "LID with channel cage - machining + engraving", C.TEXT["pn"] + "-02")
    return fig


# ---------------- sheet 3: gasket, PCB v3, assembly ----------------
def sheet_misc(H, B, holes):
    fig = plt.figure(figsize=(16.54, 11.69))
    a = fig.add_axes([0.02, 0.05, 0.30, 0.90])
    for g in Hm.gasket_regions(H): poly(a, g, fc="#555", ec=INK, lw=0.4)
    a.set_title("GASKET %s-03: %.2f mm conductive elastomer,\ndie-cut from dxf_src/gasket.dxf (top-view frame)" % (C.TEXT["pn"], C.CAGE["gasket_t"]), fontsize=7.5, weight="bold"); finish(a)
    b = fig.add_axes([0.33, 0.05, 0.32, 0.90])
    poly(b, B["pour"], fc="#cfdcc6", ec="#5a8a50", lw=0.3); poly(b, B["sig"], fc="#d08a2a", ec=INK, lw=0.3)
    poly(b, B["outline"], fc="none", ec="b", lw=0.8)
    cx, cy = B["shift"]
    for i, (x, y, w) in enumerate(holes):
        b.add_patch(Circle((x, y), C.PCB_HOLES["drill"] / 2, fc="r", ec="r"))
        b.text(x + 2.6, y + 1.0, "H%d (%.2f, %.2f)" % (i + 1, x + cx, y + cy), fontsize=4.3, color="r")
    b.set_title("PCB V3: %d x M2 PTH d%.2f finished (customer DXF frame)\nfile: 01_pcb_v3/..._V3.dxf, layer MOUNT_HOLES_PTH" % (len(holes), C.PCB_HOLES["drill"]), fontsize=7.5, weight="bold"); finish(b)
    img = os.path.join(C.ROOT, "03_step", C.TEXT["pn"] + "_ASSY_EXPLODED_iso.png")
    if os.path.exists(img):
        c = fig.add_axes([0.66, 0.50, 0.33, 0.45]); c.imshow(plt.imread(img)); c.axis("off"); c.set_title("EXPLODED ASSEMBLY", fontsize=8, weight="bold")
    X, K, Q = C.BOX, C.CONN, C.CAGE
    steps = ["ASSEMBLY", "1. Fit the PCB V3 in the base (copper side up, IN to the W wall).",
             "   %d x M2x5 ISO 4762 A2, 0.20 N m, centre outward." % len(holes),
             "2. Connectors 23_SMA-50-0-272/133_N: spigot into the bore, pin on the",
             "   trace. Fit outputs 2-3, 4-5, 6-7 in order (flanges 1.8 apart).",
             "   4 x M2.5x5 ISO 4762 each, 0.35 N m. Solder each pin to its launch.",
             "3. Clean flux. Lay the %.2f mm gasket on the board (aligned to the" % Q["gasket_t"],
             "   channels) or bond it to the cage face with conductive adhesive.",
             "4. Lid on the 2 dowels; %d x M2.5x8 ISO 7380, 0.35 N m, cross pattern." % len(H.lid_screws),
             "5. Removal: 2 x M3 jack screws through the lid. Never pry.",
             "6. Test: S-parameters 8-12 GHz, all ports; lid fitted."]
    fig.text(0.665, 0.46, "\n".join(steps), fontsize=6.6, va="top", family="monospace")
    frame(fig, 3, 4, "GASKET, PCB V3 holes, ASSEMBLY", C.TEXT["pn"] + "-03 / PCB")
    return fig


# ---------------- sheet 4: hole table ----------------
def sheet_holes(H):
    fig = plt.figure(figsize=(16.54, 11.69))
    rows = report.hole_tables(H)
    cols = 2; per = math.ceil(len(rows) / cols)
    for k in range(cols):
        part = rows[k * per:(k + 1) * per]
        ax = fig.add_axes([0.02 + k * 0.49, 0.15, 0.47, 0.80]); ax.axis("off")
        cell = [[r[0], r[1], r[2], "%.3f" % r[3], "%.3f" % r[4], "%.3f" % r[5]] for r in part]
        t = ax.table(cellText=cell, colLabels=["part", "face", "feature", "X", "Y", "Z"], loc="upper center", cellLoc="left",
                     colWidths=[0.07, 0.10, 0.53, 0.10, 0.10, 0.10])
        t.auto_set_font_size(False); t.set_fontsize(4.6); t.scale(1, 0.62)
    fig.text(0.02, 0.965, "HOLE TABLE - datum: outside SW corner of the base, bottom face. X east, Y north, Z up (Z = face the feature starts from).  "
             "Also as 05_docs/%s_HOLE_TABLE.csv." % C.TEXT["pn"], fontsize=8, weight="bold")
    frame(fig, 4, 4, "HOLE TABLE (base + lid)", C.TEXT["pn"] + "-01/-02")
    return fig


def write(B, holes, H):
    os.makedirs(OUTD, exist_ok=True); pn = C.TEXT["pn"]
    sheets = [sheet_base(H), sheet_lid(H), sheet_misc(H, B, holes), sheet_holes(H)]
    with PdfPages(os.path.join(OUTD, pn + "_DRAWINGS.pdf")) as pdf:
        for i, f in enumerate(sheets):
            pdf.savefig(f); f.savefig(os.path.join(OUTD, "%s_sheet%d.png" % (pn, i + 1)), dpi=100); plt.close(f)
    print("drawings: %d sheets" % len(sheets))
