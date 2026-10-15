"""Build every DXF of the null-steering / CP modular antenna pack + previews + DRC + 3-D assembly tables.
    python build_boards.py            -> writes into ../01_dxf
DXF layers (mm):
  OUTLINE            board edge
  TOP / MID / BOT    copper (each layer already merged; holes written on <layer>_CUTOUT for HFSS subtraction)
  VIA                drill circles (layer span in VIA_SPAN text file / table)
  PORT               HFSS lumped/wave-port reference lines (RF in/out)
  SILK_TOP/SILK_BOT  silkscreen (text, polarity bars, outlines)
  ASSY_TOP/ASSY_BOT  component bodies + reference designators (assembly drawing / pick-and-place)
  FAB                fabrication notes (stack-up, drill, finish)"""
import os, csv, math, json
import ezdxf
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import rotate as srot
import nsgeom as G

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "01_dxf"))
LAYERS = {"OUTLINE": 7, "TOP": 1, "TOP_CUTOUT": 1, "MID": 3, "MID_CUTOUT": 3, "BOT": 5, "BOT_CUTOUT": 5,
          "VIA": 6, "PORT": 2, "SILK_TOP": 7, "SILK_BOT": 8, "ASSY_TOP": 4, "ASSY_BOT": 4, "FAB": 9}

FAB_NOTES = ["STACK-UP (TOP->BOT): Cu 17um | RO4003C 0.508 mm er3.55 | Cu (MID GND) | RO4450F 0.1 mm er3.52 | RO4003C 0.508 mm | Cu",
             "TOTAL ~1.15 mm  FINISH ENIG  MASK GREEN/ (NONE ON ANTENNA AREA OPTIONAL)  SILK WHITE",
             "VIAS: 0.3 mm DRILL PTH, TOP-MID / MID-BOT (blind) OR THROUGH IF STACK ALLOWS - SEE GUIDE",
             "LINE/SPACE MIN 0.10 mm   SLOT LINE gs = 0.11 mm (ETCH TOLERANCE CRITICAL)"]

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]

def write_dxf(b, path, fab=True):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4
    for n, c in LAYERS.items(): d.layers.add(n, color=c)
    m = d.modelspace()
    for lay in ("OUTLINE", "TOP", "MID", "BOT", "PORT", "SILK_TOP", "SILK_BOT"):
        g = unary_union(b.L.get(lay, []))
        for p in polys(g):
            m.add_lwpolyline(list(p.exterior.coords)[:-1], close=True, dxfattribs={"layer": lay})
            for h in p.interiors:
                m.add_lwpolyline(list(h.coords)[:-1], close=True, dxfattribs={"layer": lay + "_CUTOUT" if lay in ("TOP", "MID", "BOT") else lay})
    for x, y, dd, span in b.vias:
        m.add_circle((x, y), dd / 2, dxfattribs={"layer": "VIA"})
    for (lay, s, x, y, h, rot, al) in b.txt:
        t = m.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay, "style": "Standard"})
        t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment[al])
    for c in b.comp:
        lay = "ASSY_" + c["side"]
        x, y, w, h = c["x"], c["y"], c["w"], c["h"]
        m.add_lwpolyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], close=True, dxfattribs={"layer": lay})
        t = m.add_text(c["ref"], height=0.35, dxfattribs={"layer": lay}); t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    if fab:
        bx = b.L["OUTLINE"][0].bounds
        for k, s in enumerate(FAB_NOTES):
            t = m.add_text(s, height=0.7, dxfattribs={"layer": "FAB"}); t.set_placement((bx[2] + 3, bx[3] - 1.5 * k))
    d.saveas(path)

def bom_rows(b, board_name):
    return [[board_name, c["ref"], c["value"], c["side"], round(c["x"], 3), round(c["y"], 3), c.get("pin1") or ""] for c in b.comp]

def drc(b, min_gap=0.10, silk_clear=0.10):
    rep = []
    for lay in ("TOP", "MID", "BOT"):
        ps = polys(unary_union(b.L.get(lay, [])))
        mg = min((ps[i].distance(ps[j]) for i in range(len(ps)) for j in range(i + 1, len(ps))), default=99)
        rep.append("%s: %d islands, min gap %.3f mm%s" % (lay, len(ps), mg, "  <-- VIOLATION" if mg < min_gap else ""))
        # thinnest feature (erode test)
        g = unary_union(b.L.get(lay, []))
        if not g.is_empty:
            thin = g.difference(g.buffer(-0.049).buffer(0.049)).area
            if lay != "MID": rep.append("   features < 0.10 mm wide: area %.4f mm2%s" % (thin, " (check)" if thin > 0.01 else ""))
    # silkscreen text over exposed copper (approximate text box)
    for side in ("TOP", "BOT"):
        cu = unary_union(b.L.get(side, []))
        hits = 0
        for (lay, s, x, y, h, rot, al) in b.txt:
            if lay != "SILK_" + side: continue
            wv, hv = 0.62 * h * len(s), h
            r = box(x - wv / 2, y - hv / 2, x + wv / 2, y + hv / 2)
            if rot: r = srot(r, rot, origin=(x, y))
            if r.intersects(cu.buffer(silk_clear)): hits += 1
        rep.append("SILK_%s: %d labels touch copper (OK on large ground pours if mask is present; move if on pads)" % (side, hits))
    return rep

def preview(b, path, title, layers=("TOP", "MID", "BOT", "SILK_TOP")):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    col = {"TOP": "#d9822b", "MID": "#7f8c8d", "BOT": "#2e86c1", "SILK_TOP": "#111111", "SILK_BOT": "#5b2c6f"}
    names = {"TOP": "TOP (front)", "MID": "MID (GND)", "BOT": "BOT (back)", "SILK_TOP": "SILK TOP", "SILK_BOT": "SILK BOT"}
    ob = b.L["OUTLINE"][0].bounds; asp = (ob[3] - ob[1]) / (ob[2] - ob[0])
    fig, ax = plt.subplots(1, len(layers), figsize=(3.3 * len(layers), 3.3 * min(asp, 3.2) + 0.6))
    for a, lay in zip(ax, layers):
        a.add_patch(plt.Polygon(list(b.L["OUTLINE"][0].exterior.coords), fill=True, fc="#f4f1e8", ec="k", lw=0.8))
        g = unary_union(b.L.get(lay if not lay.startswith("SILK") else "TOP", []))
        if lay.startswith("SILK"):
            for p in polys(unary_union(b.L.get("TOP" if lay == "SILK_TOP" else "BOT", []))):
                a.add_patch(plt.Polygon(list(p.exterior.coords), fc="#e8c39e" if lay == "SILK_TOP" else "#b9d4ea", ec="none"))
            for (l, s, x, y, h, rot, al) in b.txt:
                if l == lay: a.text(x, y, s, fontsize=max(3.0, h * 4.2), rotation=rot, ha="center", va="center", color=col[lay])
        else:
            for p in polys(g):
                a.add_patch(plt.Polygon(list(p.exterior.coords), fc=col[lay], ec="none"))
                for hh in p.interiors: a.add_patch(plt.Polygon(list(hh.coords), fc="#f4f1e8", ec="none"))
            for x, y, dd, span in b.vias:
                if lay in span: a.add_patch(plt.Circle((x, y), dd / 2, fc="yellow", ec="k", lw=0.3))
        a.set_xlim(ob[0] - 1, ob[2] + 1); a.set_ylim(ob[1] - 1, ob[3] + 1); a.set_aspect("equal"); a.set_title(names[lay], fontsize=9)
        a.tick_params(labelsize=6)
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)

def build_all():
    os.makedirs(OUT, exist_ok=True)
    for sub in ("A_without_antenna", "B_antenna_only", "C_units_with_antenna", "D_system_1D_2units",
                "E_system_2D_4units", "F_system_CP_4units", "G_feed_dividers", "H_fab_panel"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    bom, drc_log, asm = [], [], []
    def emit(b, sub, fname, title, prev_layers=("TOP", "MID", "BOT", "SILK_TOP")):
        p = os.path.join(OUT, sub, fname)
        write_dxf(b, p + ".dxf"); preview(b, p + "_preview.png", title, prev_layers)
        bom.extend(bom_rows(b, fname)); drc_log.append("== " + fname); drc_log.extend("   " + r for r in drc(b))
    # A: phase shifter alone (2 slot variants, choke or resistor bias)
    emit(G.board_phase_shifter("paper", "L"), "A_without_antenna", "PS_slot-paper-8p8x8p8_choke-bias", "Phase shifter (no antenna) - slot per paper text (8.8 x 8.8)")
    emit(G.board_phase_shifter("drawing", "L"), "A_without_antenna", "PS_slot-drawing-ratio-8p8x5p3_choke-bias", "Phase shifter - slot per Fig.2(e) aspect (8.8 x 5.3) [variant]")
    emit(G.board_phase_shifter("paper", "R"), "A_without_antenna", "PS_slot-paper_resistor-bias_RECOMMENDED", "Phase shifter - 10 k bias resistors instead of 100 nH chokes")
    # B: dipole alone
    emit(G.board_dipole(), "B_antenna_only", "DIPOLE_standalone_0p508mm", "Printed dipole + balun alone (0.508 mm RO4003C, 2 layers)", ("TOP", "BOT", "SILK_TOP", "SILK_BOT"))
    # C: units with antenna (type A / mirrored type B, MID ground per paper / extended)
    for v in ("A", "B"):
        for mid in ("paper", "extended"):
            emit(G.board_unit(v, "paper", mid), "C_units_with_antenna", "UNIT_%s_mid-%s" % (v, mid),
                 "Unit type %s (PS + dipole), MID ground: %s" % (v, mid), ("TOP", "MID", "BOT", "SILK_TOP", "SILK_BOT"))
    # D: 1-D system: two mirrored units side by side (coplanar), centre spacing 25 mm = lambda0/2 @ 6 GHz
    import copy
    uA = G.board_unit("A", unit_no=1); uB = G.board_unit("B", unit_no=2)
    pan = G.Board("SYS_1D", box(-25, 0, 25, 60))
    for b_, dx in ((uA, -12.5), (uB, 12.5)):
        pb = G.place(b_, dx, 0)
        for k, gs in pb.L.items():
            if k == "OUTLINE": continue
            for g in gs: pan.add(k, g)
        pan.vias += pb.vias; pan.txt += pb.txt; pan.comp += [dict(c, ref="U%d-%s" % (1 if dx < 0 else 2, c["ref"])) for c in pb.comp]
    pan.add("SILK_TOP", box(-0.05, 0, 0.05, 30))       # board-split line (two boards butt-joined)
    pan.text("SILK_TOP", "1-D NULL STEER: U1 (A) | U2 (B)  d = 25 mm", 0, -2.0, 0.9)
    emit(pan, "D_system_1D_2units", "SYS1D_U1A_U2B_coplanar_panel", "1-D system: U1 (type A) + U2 (mirrored type B), d = 25 mm", ("TOP", "MID", "BOT", "SILK_TOP"))
    # 3-D assembly tables (board placement for HFSS / mechanical): board frame -> world
    #   board x -> world axis 'u', board y -> world +z, board normal -> world 'n'
    d = 25.0
    asm.append(["SYS_1D", 1, "A", -d / 2, 0, 0, 0, "board plane = world xz, front faces -y"])
    asm.append(["SYS_1D", 2, "B", +d / 2, 0, 0, 0, "board plane = world xz, front faces -y"])
    # E: 2-D 2x2 (U1 +x+y A, U2 -x+y B, U3 +x-y B, U4 -x-y A): x-pairs (1,2),(3,4) and y-pairs (1,3),(2,4) antiphase
    for (u, t, x, y) in ((1, "A", d / 2, d / 2), (2, "B", -d / 2, d / 2), (3, "B", d / 2, -d / 2), (4, "A", -d / 2, -d / 2)):
        asm.append(["SYS_2D", u, t, x, y, 0, 0, "board plane parallel to world xz (two rows, 25 mm apart in y)"])
    for row, (ul, ur) in (("front_y-12p5", (4, 3)), ("back_y+12p5", (2, 1))):
        tl = {1: "A", 2: "B", 3: "B", 4: "A"}
        pan = G.Board("SYS_2D_" + row, box(-25, 0, 25, 60))
        for u_, dx in ((ul, -12.5), (ur, 12.5)):
            pb = G.place(G.board_unit(tl[u_], unit_no=u_), dx, 0)
            for k, gs in pb.L.items():
                if k == "OUTLINE": continue
                for g in gs: pan.add(k, g)
            pan.vias += pb.vias; pan.txt += pb.txt; pan.comp += [dict(c, ref="U%d-%s" % (u_, c["ref"])) for c in pb.comp]
        pan.text("SILK_TOP", "2-D ROW %s: U%d (%s) | U%d (%s)" % (row, ul, tl[ul], ur, tl[ur]), 0, -2.0, 0.9)
        emit(pan, "E_system_2D_4units", "SYS2D_row_%s" % row, "2-D system row %s" % row, ("TOP", "BOT", "SILK_TOP"))
    # F: CP cross (four wings at azimuth 45/135/225/315; board inner edge on the z axis, radiating +z)
    for (u, t, az) in ((1, "A", 45), (2, "B", 135), (4, "A", 225), (3, "B", 315)):
        asm.append(["SYS_CP", u, t, 12.5 * math.cos(math.radians(az)), 12.5 * math.sin(math.radians(az)), 0, az,
                    "wing: board plane contains the radial line at azimuth %d deg; opposite wings (1,4),(2,3)" % az])
    for (u, t, az) in ((1, "A", 45), (2, "A", 135), (4, "B", 225), (3, "B", 315)):
        asm.append(["SYS_CP_cophased", u, t, 12.5 * math.cos(math.radians(az)), 12.5 * math.sin(math.radians(az)), 0, az,
                    "RECOMMENDED: opposite wings opposite type so their E-vectors add at broadside (see array_models CP check)"])
    for u, t in ((1, "A"), (2, "B"), (3, "B"), (4, "A")):
        emit(G.board_unit(t, unit_no=u), "F_system_CP_4units", "CP_wing_U%d_type%s" % (u, t), "CP wing U%d (type %s)" % (u, t), ("TOP", "BOT", "SILK_TOP"))
    # G: Wilkinson dividers
    emit(G.board_wilkinson(2), "G_feed_dividers", "WILKINSON_1x2_6GHz_pitch25", "Wilkinson 1:2 (replaces external 2-way splitter)", ("TOP", "SILK_TOP"))
    emit(G.board_wilkinson(4), "G_feed_dividers", "WILKINSON_1x4_6GHz_pitch25", "Wilkinson 1:4 (replaces external 4-way splitter)", ("TOP", "SILK_TOP"))
    # H: fabrication panel: 4 units (A,B,B,A) + PS coupon + dipole coupon, 3 mm routing gaps
    pan = G.Board("FAB_PANEL", box(-2, -2, 4 * 28 + 25 + 28 + 1, 63))
    items = [(G.board_unit("A", unit_no=1), 12.5, 0), (G.board_unit("B", unit_no=2), 12.5 + 28, 0),
             (G.board_unit("B", unit_no=3), 12.5 + 56, 0), (G.board_unit("A", unit_no=4), 12.5 + 84, 0),
             (G.board_phase_shifter("paper", "L"), 12.5 + 112, 24), (G.board_dipole(), 12.5 + 140, 36)]
    for b_, dx, dy in items:
        pb = G.place(b_, dx, dy)
        pan.add("SILK_TOP", pb.L["OUTLINE"][0].exterior.buffer(0.08))  # route outline marker
        for k, gs in pb.L.items():
            if k == "OUTLINE": continue
            for g in gs: pan.add(k, g)
        pan.vias += pb.vias; pan.txt += pb.txt; pan.comp += pb.comp
    for fx, fy in ((-0.5, -0.5), (pan.L["OUTLINE"][0].bounds[2] - 1.5, -0.5), (-0.5, 61.5)):
        pan.add("TOP", G.Point(fx + 0.5, fy + 0.5).buffer(0.5)); pan.text("SILK_TOP", "FID", fx + 0.5, fy + 1.7, 0.5)
    emit(pan, "H_fab_panel", "FAB_PANEL_4units_PS_ANT_coupons", "Fabrication panel: U1-U4 + PS coupon + dipole coupon", ("TOP", "MID", "BOT", "SILK_TOP"))
    with open(os.path.join(OUT, "BOM_and_placement.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["board_file", "ref", "value", "side", "x_mm", "y_mm", "polarity"]); w.writerows(bom)
    with open(os.path.join(OUT, "assembly_3D_placement.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["system", "unit", "type", "x_world_mm", "y_world_mm", "z_bottom_mm", "azimuth_deg", "note"]); w.writerows(asm)
    with open(os.path.join(OUT, "DRC_report.txt"), "w") as fh: fh.write("\n".join(drc_log))
    print("\n".join(drc_log))

if __name__ == "__main__":
    build_all()

def assembly_views():
    """Top-view assembly drawings (DXF) + 3-D check render for the 1-D, 2-D and CP systems."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    rows = list(csv.DictReader(open(os.path.join(OUT, "assembly_3D_placement.csv"))))
    fig = plt.figure(figsize=(20, 5))
    for k, sysn in enumerate(("SYS_1D", "SYS_2D", "SYS_CP", "SYS_CP_cophased")):
        R = [r for r in rows if r["system"] == sysn]
        d = ezdxf.new("R2010"); d.units = ezdxf.units.MM
        for n, c in (("BOARD_EDGE", 7), ("ANT_PHASE_CENTRE", 1), ("TEXT", 8), ("AXES", 3)): d.layers.add(n, color=c)
        m = d.modelspace()
        m.add_line((-40, 0), (40, 0), dxfattribs={"layer": "AXES"}); m.add_line((0, -40), (0, 40), dxfattribs={"layer": "AXES"})
        m.add_text("x", height=1.5, dxfattribs={"layer": "AXES"}).set_placement((41, 0)); m.add_text("y", height=1.5, dxfattribs={"layer": "AXES"}).set_placement((0, 41))
        ax = fig.add_subplot(1, 4, k + 1, projection="3d")
        for r in R:
            x, y, az = float(r["x_world_mm"]), float(r["y_world_mm"]), float(r["azimuth_deg"])
            if sysn.startswith("SYS_CP"):     # wing: inner edge on the axis, extends radially 25 mm
                ux, uy = math.cos(math.radians(az)), math.sin(math.radians(az))
                p0, p1 = (0, 0), (25 * ux, 25 * uy)
            else:                    # board plane parallel to xz, centred at (x, y)
                p0, p1 = (x - 12.5, y), (x + 12.5, y)
            m.add_line(p0, p1, dxfattribs={"layer": "BOARD_EDGE", "lineweight": 50})
            m.add_circle((x, y), 0.8, dxfattribs={"layer": "ANT_PHASE_CENTRE"})
            m.add_text("U%s (%s)" % (r["unit"], r["type"]), height=1.6, dxfattribs={"layer": "TEXT"}).set_placement((x + 1.5, y + 1.5))
            col = "#d9822b" if r["type"] == "A" else "#2e86c1"
            verts = [[(p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], 60), (p0[0], p0[1], 60)]]
            ax.add_collection3d(Poly3DCollection(verts, fc=col, alpha=0.55, ec="k"))
            ax.text(x, y, 63, "U%s%s" % (r["unit"], r["type"]), fontsize=8)
        m.add_text(sysn + "  top view (boards stand vertically, beam +z). Orange/Type A, blue/Type B = mirrored (180 deg)", height=1.4,
                   dxfattribs={"layer": "TEXT"}).set_placement((-40, -45))
        d.saveas(os.path.join(OUT, {"SYS_1D": "D_system_1D_2units", "SYS_2D": "E_system_2D_4units", "SYS_CP": "F_system_CP_4units", "SYS_CP_cophased": "F_system_CP_4units"}[sysn], "ASSEMBLY_topview_%s.dxf" % sysn))
        ax.set_xlim(-30, 30); ax.set_ylim(-30, 30); ax.set_zlim(0, 65); ax.set_title(sysn + " (A orange, B blue)", fontsize=9)
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z (beam)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "assembly_3D_check.png"), dpi=110)

if __name__ == "__main__":
    assembly_views()
