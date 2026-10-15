"""A3 manufacturing drawing per enclosure (PDF + PNG) from the same geometry as the STEP files.
    python make_drawings.py            -> ../03_drawings/<PN>_DRAWING.pdf / .png"""
import os, sys, math, datetime
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
from encl_config import CONN, BOX, BOARDS
from encl_geom import Encl, THREAD
import build_enclosures as BE

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "03_drawings")
LW, THIN = 0.9, 0.45

def rr(ax, cx, cy, w, h, r, **kw):
    ax.add_patch(FancyBboxPatch((cx - w / 2 + r, cy - h / 2 + r), w - 2 * r, h - 2 * r, boxstyle="round,pad=%g" % r, **kw))

def dim(ax, p0, p1, off, text, horiz=True, fs=6):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = max(y0, y1) + off if off > 0 else min(y0, y1) + off
        for x, yy in ((x0, y0), (x1, y1)): ax.plot([x, x], [yy, y + (0.8 if off > 0 else -0.8)], "k-", lw=0.3)
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + (0.6 if off > 0 else -0.6), text, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:
        x = max(x0, x1) + off if off > 0 else min(x0, x1) + off
        for xx, y in ((x0, y0), (x1, y1)): ax.plot([xx, x + (0.8 if off > 0 else -0.8)], [y, y], "k-", lw=0.3)
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
        ax.text(x + (0.6 if off > 0 else -0.6), (y0 + y1) / 2, text, ha="left" if off > 0 else "right", va="center", fontsize=fs, rotation=90)

def view_top(ax, e):
    B = BOX
    rr(ax, 0, 0, e.Lo, e.Wo, B["outer_r"], fc="#e9ecef", ec="k", lw=LW)
    rr(ax, 0, 0, e.Lc, e.Wc, B["cav_r"], fc="white", ec="k", lw=LW)
    b = e.b
    rr(ax, 0, 0, b["L"], b["W"], 1.2, fc="#dcefe0", ec="#2f6b3a", lw=THIN, ls="--")
    for x, y in e.lid_screws: ax.add_patch(Circle((x, y), THREAD["M2.5"]["tap"] / 2, fc="white", ec="k", lw=THIN))
    for x, y in e.pcb_screws: ax.add_patch(Circle((x, y), THREAD["M2"]["tap"] / 2, fc="white", ec="b", lw=THIN))
    for x, y in e.mount: ax.add_patch(Circle((x, y), THREAD["M3"]["tap"] / 2, fc="none", ec="gray", lw=THIN, ls=":"))
    for p in e.ports:
        ux, uy = p["u"]; fx, fy = p["face"]; tx, ty = p["t"]; f = CONN["flange"]; t = CONN["flange_t"]
        c = [(fx + tx * s1 * f / 2 + ux * s2 * t, fy + ty * s1 * f / 2 + uy * s2 * t) for s1, s2 in ((-1, 0), (1, 0), (1, 1), (-1, 1))]
        ax.add_patch(Polygon(c, fc="#f3e7b3", ec="k", lw=THIN))
        ax.plot([fx + ux * t, fx + ux * (t + 6)], [fy + uy * t, fy + uy * (t + 6)], "k-", lw=1.4)
        ax.plot([fx - ux * B["wall"], fx], [fy - uy * B["wall"], fy], "k--", lw=0.4)
        ax.text(fx + ux * (t + 9), fy + uy * (t + 9), p["label"], ha="center", va="center", fontsize=6, weight="bold")
    dim(ax, (-e.Lo / 2, -e.Wo / 2), (e.Lo / 2, -e.Wo / 2), -9, "%.2f" % e.Lo)
    dim(ax, (-e.Lc / 2, e.Wc / 2), (e.Lc / 2, e.Wc / 2), 12, "%.2f +0.05/0 (cavity)" % e.Lc)
    dim(ax, (e.Lo / 2, -e.Wo / 2), (e.Lo / 2, e.Wo / 2), 16, "%.2f" % e.Wo, horiz=False)
    dim(ax, (-e.Lc / 2, -e.Wc / 2), (-e.Lc / 2, e.Wc / 2), -14, "%.2f +0.05/0" % e.Wc, horiz=False)
    for p in e.ports:
        if p["wall"] in "WE" and abs(p["off"]) > 1e-6:
            x = p["face"][0]; dim(ax, (x, 0), (x, p["off"]), (6 if p["wall"] == "E" else -6) * (1 if p["off"] > 0 else 1), "%.2f" % abs(p["off"]), horiz=False, fs=5)
    ax.plot([-e.Lo / 2 - 5, e.Lo / 2 + 5], [0, 0], "k-.", lw=0.3); ax.text(-e.Lo / 2 - 6, 0, "A", fontsize=7, weight="bold", ha="right", va="center")
    ax.text(e.Lo / 2 + 6, 0, "A", fontsize=7, weight="bold", va="center")
    ax.set_title("BASE - TOP VIEW (lid removed)", fontsize=8, weight="bold")
    ax.text(0, -e.Wo / 2 - 16, "%d x %s tap %.1f deep (lid)   %d x %s tap %.1f deep (PCB, blue)   4 x %s tap %.0f deep from bottom (dotted)"
            % (len(e.lid_screws), B["lid_screw"], B["lid_tap_depth"], len(e.pcb_screws), B["pcb_screw"], B["pcb_tap_depth"], B["mount_screw"], B["mount_tap_depth"]), fontsize=5, ha="center")

def view_wall(ax, e, wall="W"):
    B = BOX; ports = [p for p in e.ports if p["wall"] == wall]
    W = e.Wo if wall in "WE" else e.Lo
    ax.add_patch(Rectangle((-W / 2, 0), W, e.z_wall, fc="#e9ecef", ec="k", lw=LW))
    ax.add_patch(Rectangle((-W / 2, e.z_wall), W, B["t_lid"], fc="#d6dbe0", ec="k", lw=LW))
    for p in ports:
        a = p["off"] * (1 if wall in "W" else -1) if wall in "WE" else p["off"]
        ax.add_patch(Circle((a, e.pin_z), CONN["bore_d"] / 2, fc="white", ec="k", lw=THIN))
        for s1 in (-1, 1):
            for s2 in (-1, 1): ax.add_patch(Circle((a + s1 * CONN["hole_sq"] / 2, e.pin_z + s2 * CONN["hole_sq"] / 2), THREAD["M2.5"]["tap"] / 2, fc="white", ec="k", lw=THIN))
        ax.add_patch(Rectangle((a - CONN["flange"] / 2, e.pin_z - CONN["flange"] / 2), CONN["flange"], CONN["flange"], fc="none", ec="#a08a2a", lw=THIN, ls="--"))
        ax.text(a, e.pin_z - CONN["flange"] / 2 - 1.2, p["label"], fontsize=5, ha="center", va="top")
    p = ports[0]; a = p["off"] * (1 if wall == "W" else -1)
    dim(ax, (W / 2, 0), (W / 2, e.pin_z), 5, "%.3f (pin axis)" % e.pin_z, horiz=False, fs=5)
    dim(ax, (-W / 2, 0), (-W / 2, e.z_wall), -4, "%.2f" % e.z_wall, horiz=False, fs=5)
    dim(ax, (-W / 2, 0), (-W / 2, e.z_top), -10, "%.2f" % e.z_top, horiz=False, fs=5)
    dim(ax, (a - CONN["hole_sq"] / 2, e.z_top), (a + CONN["hole_sq"] / 2, e.z_top), 4, "%.2f sq (4x %s, 4 deep)" % (CONN["hole_sq"], CONN["screw"]), fs=5)
    ax.text(a, e.pin_z + 0.0, "d%.2f H8\nthru wall" % CONN["bore_d"], fontsize=4, ha="center", va="center")
    ax.set_title("VIEW ON %s WALL (connector face)" % {"W": "WEST", "E": "EAST", "N": "NORTH", "S": "SOUTH"}[wall], fontsize=8, weight="bold")

def view_section(ax, e):
    B = BOX; b = e.b; Lo, Lc = e.Lo, e.Lc
    ax.add_patch(Polygon([(-Lo / 2, 0), (Lo / 2, 0), (Lo / 2, e.z_wall), (Lc / 2, e.z_wall), (Lc / 2, e.floor), (-Lc / 2, e.floor), (-Lc / 2, e.z_wall), (-Lo / 2, e.z_wall)],
                         fc="#e9ecef", ec="k", lw=LW, hatch="///"))
    o, w = B["lip_clr"], B["lip_w"]; z0 = e.z_wall
    lid = [(-Lo / 2, z0), (-Lc / 2 + o, z0), (-Lc / 2 + o, z0 - B["lip_h"]), (-Lc / 2 + o + w, z0 - B["lip_h"]), (-Lc / 2 + o + w, z0),
           (-Lc / 2 + o + w + B["absorber_inset"], z0), (-Lc / 2 + o + w + B["absorber_inset"], z0 + B["absorber_depth"]),
           (Lc / 2 - o - w - B["absorber_inset"], z0 + B["absorber_depth"]), (Lc / 2 - o - w - B["absorber_inset"], z0), (Lc / 2 - o - w, z0),
           (Lc / 2 - o - w, z0 - B["lip_h"]), (Lc / 2 - o, z0 - B["lip_h"]), (Lc / 2 - o, z0), (Lo / 2, z0), (Lo / 2, e.z_top), (-Lo / 2, e.z_top)]
    ax.add_patch(Polygon(lid, fc="#d6dbe0", ec="k", lw=LW, hatch="\\\\\\"))
    ax.add_patch(Rectangle((-b["L"] / 2, e.floor), b["L"], b["t"], fc="#2f6b3a", ec="k", lw=THIN))
    for p in e.ports:
        if p["wall"] in "WE" and abs(p["off"]) < 1e-6:
            s = -1 if p["wall"] == "W" else 1; xw = s * Lo / 2
            ax.add_patch(Rectangle((min(xw, xw - s * B["wall"]), e.pin_z - CONN["spigot_d"] / 2), B["wall"], CONN["spigot_d"], fc="#f3e7b3", ec="k", lw=THIN))
            ax.plot([xw - s * B["wall"], xw - s * (B["wall"] + CONN["pin_proj"])], [e.pin_z, e.pin_z], "k-", lw=1.6)
            ax.add_patch(Rectangle((min(xw, xw + s * CONN["flange_t"]), e.pin_z - CONN["flange"] / 2), CONN["flange_t"], CONN["flange"], fc="#f3e7b3", ec="k", lw=THIN))
    dim(ax, (Lo / 2, 0), (Lo / 2, e.floor), 4, "%.2f floor" % e.floor, horiz=False, fs=5)
    dim(ax, (Lo / 2, e.floor + b["t"]), (Lo / 2, e.z_wall), 12, "%.1f air" % B["h_air"], horiz=False, fs=5)
    dim(ax, (Lo / 2, e.z_wall), (Lo / 2, e.z_top), 4, "%.1f lid" % B["t_lid"], horiz=False, fs=5)
    dim(ax, (-Lo / 2, -0.5), (-Lc / 2, -0.5), -4, "%.1f wall" % B["wall"], fs=5)
    ax.text(0, e.z_wall + B["absorber_depth"] / 2, "absorber recess %.1f deep" % B["absorber_depth"], fontsize=4.5, ha="center", va="center")
    ax.text(-Lc / 2 + 2, z0 - B["lip_h"] - 1.2, "RF lip %.1f x %.1f" % (w, B["lip_h"]), fontsize=4.5)
    ax.set_title("SECTION A-A", fontsize=8, weight="bold")

def view_lid(ax, e):
    B = BOX; b = e.b
    rr(ax, 0, 0, e.Lo, e.Wo, B["outer_r"], fc="#d6dbe0", ec="k", lw=LW)
    for x, y in e.lid_screws:
        ax.add_patch(Circle((x, y), B["lid_clear_d"] / 2, fc="white", ec="k", lw=THIN))
    import engraving_dxf as ED
    for txt, h, font, y in ED.lid_layout(e):
        for poly in ED.glyph_polys(txt, h, font, 0.0, y): ax.add_patch(Polygon(poly, fc="none", ec="k", lw=0.25))
    ax.set_title("LID - TOP VIEW (engrave 0.3 deep, fill black optional)", fontsize=8, weight="bold")
    ax.text(0, -e.Wo / 2 - 5, "%d x d%.1f thru (%s x %g ISO 7380 button head)" % (len(e.lid_screws), B["lid_clear_d"], B["lid_screw"], B["lid_screw_len"]), fontsize=5, ha="center")

def sheet(key):
    b = BOARDS[key]; e = Encl(key, b); B = BOX
    fig = plt.figure(figsize=(16.54, 11.69))                 # A3 landscape
    fig.add_artist(Rectangle((0.01, 0.01), 0.98, 0.98, fill=False, lw=1.5, transform=fig.transFigure))
    axs = [fig.add_axes(r) for r in ([0.03, 0.47, 0.44, 0.48], [0.52, 0.62, 0.45, 0.33], [0.52, 0.36, 0.45, 0.25], [0.03, 0.08, 0.30, 0.36])]
    view_top(axs[0], e); view_wall(axs[1], e, "W" if any(p["wall"] == "W" for p in e.ports) else e.ports[0]["wall"]); view_section(axs[2], e); view_lid(axs[3], e)
    for ax in axs: ax.set_aspect("equal"); ax.autoscale_view(); ax.axis("off"); ax.margins(0.12)
    notes = ["NOTES", "1. Material: " + B["material"], "2. Finish: " + B["finish"], "3. Tolerances: " + B["tolerance"],
             "4. Threads ISO 262 metric coarse, 6H. Break all sharp edges 0.2-0.3 x 45 deg, except the lid seat and lip.",
             "5. Lid seat (wall top) and lid underside: Ra 0.8, flat 0.05 - RF contact surfaces, no paint/anodise there.",
             "6. Connector bores d%.2f H8 coaxial with the tapped pattern within 0.05." % CONN["bore_d"],
             "7. Connector: %s; pin %.2f lies on the 50 ohm trace, solder." % (CONN["part"], CONN["pin_d"]),
             "8. Engrave 0.3 deep: logo / title / P/N / S/N on the lid, port labels on the walls.",
             "9. PCB: %.2f x %.2f x %.3f (%s) - ASSUMED, confirm with the layout." % (b["L"], b["W"], b["t"], b["substrate"]),
             "10. Optional: 1 mm RF absorber bonded in the lid recess (cavity modes in band, see report)."]
    if b["band"][1] > 8: notes.append("11. f_max %.1f GHz: conductive elastomer gasket on the lid seat recommended (seam > lambda/4)." % b["band"][1])
    fig.text(0.355, 0.40, "\n".join(notes), fontsize=5.8, va="top", family="DejaVu Sans")
    rows = BE.bom_rows(e)
    fig.text(0.355, 0.235, "BILL OF MATERIALS", fontsize=7, weight="bold")
    for i, r in enumerate(rows):
        fig.text(0.355, 0.22 - i * 0.0125, "%d  %-24s %-60s qty %s" % (i + 1, r[0][:24], r[1][:60], r[3]), fontsize=5.5, family="DejaVu Sans Mono")
    # title block
    tb = [0.66, 0.02, 0.32, 0.12]
    fig.add_artist(Rectangle((tb[0], tb[1]), tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    fig.text(tb[0] + 0.01, tb[1] + 0.095, B["company"], fontsize=16, weight="bold")
    fig.text(tb[0] + 0.08, tb[1] + 0.098, b["title"], fontsize=8.5, weight="bold")
    fig.text(tb[0] + 0.08, tb[1] + 0.078, "RF ENCLOSURE - BASE %s-01 / LID %s-02" % (b["pn"], b["pn"]), fontsize=7)
    for i, (k, v) in enumerate((("DWG NO", b["pn"] + "-DWG"), ("REV", "A"), ("SCALE", "NTS (dims in mm)"), ("SHEET", "1/1"),
                                ("DATE", datetime.date.today().isoformat()), ("PROJECTION", "1st angle"),
                                ("MASS", "base+lid see report"), ("CAD", "SolidCraft STEP AP242"))):
        fig.text(tb[0] + 0.01 + (i % 4) * 0.078, tb[1] + 0.045 - (i // 4) * 0.025, "%s\n%s" % (k, v), fontsize=5.5)
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, b["pn"] + "_DRAWING.pdf")); fig.savefig(os.path.join(OUT, b["pn"] + "_DRAWING.png"), dpi=110)
    plt.close(fig)

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(BOARDS)): sheet(k)
    print("drawings ->", OUT)
