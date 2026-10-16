"""A3 drawing of the X-band 8-way cage housing (PDF + PNG) -> ../03_drawings."""
import os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cage_build as CB
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
import make_drawings as MD
import engraving_dxf as ED
E, B, CC = CB.E, CB.B, CB.CC

def view_section(ax):
    Lo, Lc, C = E.Lo, E.Lc, CC.CAGE
    hb = B["h_air"] - C["gap"]; z0 = E.z_wall
    ax.add_patch(Polygon([(-Lo / 2, 0), (Lo / 2, 0), (Lo / 2, z0), (Lc / 2, z0), (Lc / 2, E.floor), (-Lc / 2, E.floor), (-Lc / 2, z0), (-Lo / 2, z0)], fc="#e9ecef", ec="k", lw=0.9, hatch="///"))
    ax.add_patch(Rectangle((-Lo / 2, z0), Lo, B["t_lid"], fc="#d6dbe0", ec="k", lw=0.9, hatch="\\\\\\"))
    # cage block cut at y = 0 (through the input launch and resistor group): ribs + cells along x
    from shapely.geometry import LineString
    line = LineString([(-Lc / 2, 0.5), (Lc / 2, 0.5)])
    cuts = [c.intersection(line) for c in CB.CELLS if c.intersects(line)]
    xs = sorted([(g.bounds[0], g.bounds[2]) for g in cuts])
    x = CB.FOOT.bounds[0]
    for a, b in xs + [(CB.FOOT.bounds[2], CB.FOOT.bounds[2])]:
        if a > x: ax.add_patch(Rectangle((x, z0 - hb), a - x, hb, fc="#d6dbe0", ec="k", lw=0.5, hatch="\\\\\\"))
        x = max(x, b)
    ax.add_patch(Rectangle((-E.b["L"] / 2, E.floor), E.b["L"], E.b["t"], fc="#2f6b3a", ec="k", lw=0.4))
    MD.dim(ax, (Lo / 2, 0), (Lo / 2, E.floor), 4, "%.2f floor" % E.floor, horiz=False, fs=5)
    MD.dim(ax, (Lo / 2, E.floor + E.b["t"]), (Lo / 2, z0), 12, "%.1f air" % B["h_air"], horiz=False, fs=5)
    MD.dim(ax, (Lo / 2, z0), (Lo / 2, E.z_top), 4, "%.1f lid" % B["t_lid"], horiz=False, fs=5)
    ax.text(0, z0 - hb / 2, "cage ribs, face %.2f above PCB" % C["gap"], fontsize=5, ha="center", va="center")
    ax.set_title("SECTION A-A (y = +0.5)", fontsize=8, weight="bold")

def view_cage(ax):
    ax.add_patch(Polygon(list(CB.FOOT.exterior.coords), fc="#9aa3ab", ec="k", lw=0.6))
    for c in CB.CELLS: ax.add_patch(Polygon(list(c.exterior.coords), fc="white", ec="k", lw=0.4))
    for x, y, rot, ref in CB.BRD["res"]: ax.add_patch(Rectangle((x - 0.4, y - 0.8), 0.8, 1.6, fc="k"))
    ax.set_title("CAGE (lid underside, viewed from below = mirrored in x)", fontsize=8, weight="bold")

def view_lid(ax):
    MD.rr(ax, 0, 0, E.Lo, E.Wo, B["outer_r"], fc="#d6dbe0", ec="k", lw=0.9)
    for x, y in E.lid_screws: ax.add_patch(Circle((x, y), B["lid_clear_d"] / 2, fc="white", ec="k", lw=0.4))
    for x, y in CB.JACKS: ax.add_patch(Circle((x, y), 1.5, fc="#9fd3ff", ec="k", lw=0.4)); ax.text(x, y - 3.6 * (1 if y > 0 else -1), "JACK M3", fontsize=4.5, ha="center", va="center")
    for (x, y), lab in zip(CB.DOWELS, ("d2 H7", "d2 H7 slot")): ax.add_patch(Circle((x, y), 1.0, fc="#ffd24d", ec="k", lw=0.4)); ax.text(x, y - 3.6 * (1 if y > 0 else -1), lab, fontsize=4.5, ha="center", va="center")
    for g in CB.lid_text_regions() + CB.BE.glyph_regions(CB.port_label_rows()):
        ax.add_patch(Polygon(list(g.exterior.coords), fc="#333", ec="none"))
        for h in g.interiors: ax.add_patch(Polygon(list(h.coords), fc="#d6dbe0", ec="none"))
    ax.set_title("LID - TOP (engrave 0.3)", fontsize=8, weight="bold")

def main():
    fig = plt.figure(figsize=(16.54, 11.69))
    fig.add_artist(Rectangle((0.01, 0.01), 0.98, 0.98, fill=False, lw=1.5, transform=fig.transFigure))
    a1 = fig.add_axes([0.02, 0.06, 0.24, 0.9]); MD.view_top(a1, E)
    for x, y in CB.DOWELS: a1.add_patch(Circle((x, y), 1.0, fc="#ffd24d", ec="k", lw=0.4)); a1.text(x, y - 3.2, "DOWEL d2", fontsize=4, ha="center")
    a1.add_patch(Circle((-E.Lo / 2 - 1.5, CB.F["earth_y"]), 1.5, fc="none", ec="g", lw=0.6)); a1.text(-E.Lo / 2 - 4, CB.F["earth_y"], "GND M3", fontsize=4.5, ha="right", va="center", color="g")
    a2 = fig.add_axes([0.25, 0.06, 0.22, 0.9]); view_cage(a2)
    a3 = fig.add_axes([0.46, 0.06, 0.22, 0.9]); view_lid(a3)
    a4 = fig.add_axes([0.69, 0.70, 0.29, 0.26]); MD.view_wall(a4, E, "E")
    a5 = fig.add_axes([0.69, 0.50, 0.29, 0.18]); view_section(a5)
    for ax in (a1, a2, a3, a4, a5): ax.set_aspect("equal"); ax.autoscale_view(); ax.axis("off"); ax.margins(0.06)
    notes = ["NOTES", "1. Material Al 6061-T6; conductive chromate MIL-DTL-5541 Cl.3 (or Ni); outside may be",
             "   black anodised, but NOT the lid seat, cage face, connector faces or the GND point.",
             "2. ISO 2768-mK; cavity +0.05/0; lid seat and cage face flat 0.03, Ra 0.8.",
             "3. Cage face %.2f above the PCB top: fit 0.25 mm conductive elastomer" % CC.CAGE["gap"],
             "   sheet (e.g. CHO-SEAL 1298 / 1310) cut to the rib pattern.",
             "4. PCB: customer DXF %s, t = %.3f [ASSUMED] -" % ("XBand_8Way_MSL_to_SL", CC.BOARD["t"]),
             "   confirm the stack-up; floor and cage height follow it.",
             "5. 9 x H+S 23_SMA-50-0-272/133_N; pin on the 1.686 MSL launch, solder.",
             "6. Output flanges 1.8 mm apart (board pitch 14.5): fit 2-3, 4-5, 6-7 in order.",
             "7. Seam: conductive gasket on the lid seat recommended (X band).",
             "8. Engrave 0.3: CRL BEL on the lid; IN / 1-8 ports; RF IN and GND on the west wall.",
             "9. Lid located by 2 x d2 h6 x 8 dowels (ISO 8734), pressed 5 deep in the base; lid hole + slot H7.",
             "10. Lid removal: 2 x M3 jack screws through the lid push on the wall top - never pry.",
             "11. Assembly: board (M3 x 6, 0.5 N m) > connectors (M2.5 x 5, 0.35 N m, solder pins) > elastomer",
             "    sheet on the cage > lid on dowels > 50 x M2.5 x 8 ISO 7380, 0.35 N m, cross pattern.",
             "12. Break edges: lid top 0.6 x 45, base bottom 0.5 x 45, vertical R2."]
    fig.text(0.69, 0.46, "\n".join(notes), fontsize=6.2, va="top")
    tb = [0.69, 0.02, 0.29, 0.13]
    fig.add_artist(Rectangle((tb[0], tb[1]), tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    fig.text(tb[0] + 0.01, tb[1] + 0.095, "CRL BEL", fontsize=15, weight="bold")
    fig.text(tb[0] + 0.01, tb[1] + 0.075, "ANTENNA / RFM LAB", fontsize=8, weight="bold")
    fig.text(tb[0] + 0.11, tb[1] + 0.098, CC.TEXT["title"], fontsize=8.5, weight="bold")
    fig.text(tb[0] + 0.11, tb[1] + 0.080, "CAGE HOUSING - BASE %s-01 / LID %s-02" % (CC.TEXT["pn"], CC.TEXT["pn"]), fontsize=6.5)
    for i, (k, v) in enumerate((("DWG NO", CC.TEXT["pn"] + "-DWG"), ("REV", "A"), ("SCALE", "NTS (mm)"), ("SHEET", "1/1"),
                                ("DATE", datetime.date.today().isoformat()), ("PROJECTION", "1st angle"), ("OUTSIDE", "%.1f x %.1f x %.1f" % (E.Lo, E.Wo, E.z_top)), ("CAD", "SolidCraft STEP AP242"))):
        fig.text(tb[0] + 0.01 + (i % 4) * 0.07, tb[1] + 0.045 - (i // 4) * 0.025, "%s\n%s" % (k, v), fontsize=5.5)
    out = os.path.join(CB.ROOT, "03_drawings"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, CC.TEXT["pn"] + "_DRAWING.pdf")); fig.savefig(os.path.join(out, CC.TEXT["pn"] + "_DRAWING.png"), dpi=110); plt.close(fig)
    print("drawing ok")

if __name__ == "__main__":
    main()
