"""Cage housing for the X-band 8-way stripline divider: STEP via SolidCraft + checks + DXFs.
    python cage_build.py        -> ../01_step (BASE, LID, ASSY, ASSY_EXPLODED, renders), ../03_drawings, ../05_docs
Re-uses the connector / screw / engraving machinery of project 05 (02_python)."""
import os, sys, math, json, csv, re
HERE = os.path.dirname(os.path.abspath(__file__))
P05 = os.path.abspath(os.path.join(HERE, "..", "..", "05_rf-module-enclosures_SMA", "02_python"))
sys.path.insert(0, P05); sys.path.insert(0, HERE)
import ezdxf
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
from shapely.affinity import translate
import encl_config as EC
from encl_geom import Encl, THREAD
import build_enclosures as BE
import cage_config as CC

ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "01_step")

# ---------------- read the board ----------------
def read_board():
    m = ezdxf.readfile(CC.DXF_ALL).modelspace()
    poly = lambda e: Polygon([(p[0], p[1]) for p in e.get_points("xy")])
    outline = poly(next(iter(m.query("LWPOLYLINE[layer=='BOARD_OUTLINE']"))))
    x0, y0, x1, y1 = outline.bounds; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sh = lambda g: translate(g, -cx, -cy)
    conns = [sh(poly(e)) for e in m.query("LWPOLYLINE[layer=='CONNECTOR']")]
    ports = []
    for c in conns:
        bx = c.bounds; yc = (bx[1] + bx[3]) / 2
        ports.append(("W" if bx[0] < 0 else "E", round(yc, 4)))
    holes = [(e.dxf.center.x - cx, e.dxf.center.y - cy, e.dxf.radius) for e in m.query("CIRCLE[layer=='MOUNTING_HOLES']")]
    sig = [sh(poly(e)) for e in m.query("LWPOLYLINE[layer=='TOP_SIGNAL']")]
    w_trace = max(s.bounds[3] - s.bounds[1] for s in sig)
    res = []
    with open(CC.RES_CSV) as fh:
        for r in csv.DictReader(fh): res.append((float(r["x_mm"]) - cx, float(r["y_mm"]) - cy, float(r["rotation_deg"]), r["ref"]))
    return dict(outline=sh(outline), L=x1 - x0, W=y1 - y0, shift=(cx, cy), ports=ports, holes=holes, w=w_trace, res=res,
                keep=[sh(poly(e)) for e in m.query("LWPOLYLINE[layer=='KEEP_OUT']")])

BRD = read_board()
west = [p for p in BRD["ports"] if p[0] == "W"]; east = sorted([p for p in BRD["ports"] if p[0] == "E"], key=lambda p: -p[1])
PORTS = [("IN", "W", west[0][1], BRD["w"])] + [(str(i + 1), "E", p[1], BRD["w"]) for i, p in enumerate(east)]
B = EC.BOX
EC.BOX["lid_screw_pitch_min"] = 6.0
board = dict(title=CC.TEXT["title"], pn=CC.TEXT["pn"], L=round(BRD["L"], 4), W=round(BRD["W"], 4), t=CC.BOARD["t"], cu=CC.BOARD["cu"],
             er=CC.BOARD["er"], band=CC.BOARD["band"], substrate="2 x RO4350B 0.762 (ASSUMED)", ports=PORTS)
E = Encl("XB8", board)
E.pcb_screws = [(round(x, 4), round(y, 4)) for x, y, r in BRD["holes"]]       # the board's own 4 x d3.2 holes -> M3

F = CC.FEATURES
_a, _c = E._wall_track()
DOWELS = [(round(-_a + 10.0, 3), round(_c, 3)), (round(_a - 10.0, 3), round(-_c, 3))]       # diagonal, on the N and S walls
JACKS = [(0.0, round(_c, 3)), (0.0, round(-_c, 3))]
def _refill_short_walls():
    """N and S walls: rebuild the screw row around the dowel and the jacking hole (>= 4 mm from both), screws
    >= the head clearance apart; a small dynamic programme on a 0.1 mm grid minimises the largest gap (then the count)."""
    keep = [q for q in E.lid_screws if abs(abs(q[1]) - _c) > 0.01]
    A = round(_a, 3); dmin = B["lid_cb_d"]
    for yy in (_c, -_c):
        obst = [(x, 4.0) for x, y in DOWELS + JACKS if abs(y - yy) < 0.01]
        g = sorted(set([round(-A + 0.1 * k, 3) for k in range(int(2 * A / 0.1) + 1)] + [A] + [round(o + sg * r, 3) for o, r in obst for sg in (-1, 1)]))
        g = [t for t in g if -A <= t <= A and all(abs(t - o) >= r - 1e-6 for o, r in obst)]
        best = {0: (0.0, 1, None)}                               # index -> (max gap so far, screws, previous index)
        for i in range(1, len(g)):
            cand = None
            for j in range(i):
                if j in best and g[i] - g[j] >= dmin - 1e-6:
                    v = (max(best[j][0], g[i] - g[j]), best[j][1] + 1, j)
                    if cand is None or v[:2] < cand[:2]: cand = v
            if cand: best[i] = cand
        i = len(g) - 1; row = []
        while i is not None: row.append(g[i]); i = best[i][2]
        keep += [(x, round(yy, 3)) for x in row]
    return keep
E.lid_screws = _refill_short_walls()

# ---------------- cage geometry ----------------
def cage_cells():
    """Cells (open pockets) in the cage block; everything else is rib touching the top ground pour."""
    C = CC.CAGE
    foot = Polygon([(-E.Lc / 2 + 0.1, -E.Wc / 2 + 0.1), (E.Lc / 2 - 0.1, -E.Wc / 2 + 0.1), (E.Lc / 2 - 0.1, E.Wc / 2 - 0.1), (-E.Lc / 2 + 0.1, E.Wc / 2 - 0.1)])
    inner = foot.buffer(-C["frame"], join_style=2)
    x0, y0, x1, y1 = inner.bounds
    nx = max(1, round((x1 - x0) / C["pitch"])); ny = max(1, round((y1 - y0) / C["pitch"]))
    ribs = []
    for k in range(1, nx):
        x = x0 + (x1 - x0) * k / nx; ribs.append(box(x - C["rib"] / 2, y0, x + C["rib"] / 2, y1))
    for k in range(1, ny):
        y = y0 + (y1 - y0) * k / ny; ribs.append(box(x0, y - C["rib"] / 2, x1, y + C["rib"] / 2))
    zones = []
    for p in E.ports:                                   # launch pockets, open to the wall
        ex, ey = p["edge"]; ux, uy = p["u"]
        a = (ex + ux * 0.5, ey); b_ = (ex - ux * C["launch_len"], ey)
        zones.append(box(min(a[0], b_[0]), ey - C["launch_halfw"], max(a[0], b_[0]), ey + C["launch_halfw"]))
    groups = {}
    for x, y, rot, ref in BRD["res"]: groups.setdefault((round(y, 2)), []).append((x, y))
    for y, pts in groups.items():
        # stages share y; split groups by x proximity
        pts.sort(); cl = [[pts[0]]]
        for q in pts[1:]:
            (cl[-1].append(q) if q[0] - cl[-1][-1][0] < 5 else cl.append([q]))
        for g in cl:
            xs = [q[0] for q in g]; m = CC.CAGE["res_margin"] + 1.0
            zones.append(box(min(xs) - m, y - 1.1 - m, max(xs) + m, y + 1.1 + m))
    for x, y in E.pcb_screws: zones.append(Point(x, y).buffer(C["screw_head_r"], 32))
    Z = unary_union(zones).intersection(foot)
    grid = inner.difference(unary_union(ribs)).difference(Z.buffer(C["rib"], join_style=2))   # grid cells keep a rib ring round every pocket
    parts = list(grid.geoms) if hasattr(grid, "geoms") else [grid]
    zs = list(Z.geoms) if hasattr(Z, "geoms") else [Z]
    cells = [c for c in parts + zs if c.area > 2.0 and min(c.bounds[2] - c.bounds[0], c.bounds[3] - c.bounds[1]) >= 3.0]   # thinner slivers stay solid rib (millable)
    return foot, cells, zones

FOOT, CELLS, ZONES = cage_cells()

def cell_resonances():
    out = []
    for c in CELLS:
        x0, y0, x1, y1 = c.bounds; a, b = x1 - x0, y1 - y0
        out.append((EC_C0 / 2 * math.sqrt(1 / a ** 2 + 1 / b ** 2), a, b))
    return sorted(out)
EC_C0 = 299.792458

# ---------------- CAD ----------------
def build_base(s):
    nm = "BASE"
    s.rrect(0, -E.Lo / 2, -E.Wo / 2, E.Lo / 2, E.Wo / 2, B["outer_r"])
    s.a("solid.extrude", distance=E.z_wall, operation="new", body_name=nm)
    s.rrect(E.z_wall, -E.Lc / 2, -E.Wc / 2, E.Lc / 2, E.Wc / 2, B["cav_r"])
    s.a("solid.extrude", distance=E.z_wall - E.floor, direction="negative", operation="cut", targets=[nm])
    for p in E.ports:
        ux, uy = p["u"]
        s.a("solid.hole", position=[p["face"][0], p["face"][1], E.pin_z], direction=[-ux, -uy, 0], diameter=EC.CONN["bore_d"], depth=B["wall"] + 0.3)
        for hx, hy, hz in p["holes"]:
            s.a("solid.hole", position=[hx, hy, hz], direction=[-ux, -uy, 0], thread=EC.CONN["screw"], depth=4.0)
    for x, y in E.lid_screws:
        s.a("solid.hole", position=[x, y, E.z_wall], direction=[0, 0, -1], thread=B["lid_screw"], depth=B["lid_tap_depth"])
    for x, y in E.pcb_screws:
        s.a("solid.hole", position=[x, y, E.floor], direction=[0, 0, -1], thread="M3", depth=min(4.0, E.floor - 0.8))
    for x, y in E.mount:
        s.a("solid.hole", position=[x, y, 0], direction=[0, 0, 1], thread=B["mount_screw"], depth=B["mount_tap_depth"])
    s.a("sketch.create", plane="XY", offset=E.z_wall + 0.1)                 # dowel holes (press fit)
    for x, y in DOWELS: s.a("sketch.circle.center", center=[x, y], diameter=F["dowel_d"] - 0.01, connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=F["dowel_depth"] + 0.1, direction="negative", profiles="all", operation="cut", targets=[nm])
    s.a("solid.hole", position=[-E.Lo / 2, F["earth_y"], E.pin_z], direction=[1, 0, 0], thread=F["earth"], depth=F["earth_depth"])
    # "RF IN" on the west wall beside the input flange
    p = E.ports[0]; ux, uy = p["u"]; fx, fy = p["face"]; h = 3.0
    pl = {"origin": [fx + ux * 0.1, fy + uy * 0.1, 0.0], "x_dir": [-uy, ux, 0.0], "y_dir": [0.0, 0.0, 1.0]}
    sign = -uy * p["t"][0] + ux * p["t"][1]
    w = BE.text_w("RF IN", h, B["font_bold"])
    regs = BE.glyph_regions([("RF IN", h, B["font_bold"], (p["off"] + EC.CONN["flange"] / 2 + 2 + w / 2) * sign, E.pin_z - h / 2, "center")])
    BE.cut_regions(s, regs, pl, nm, B["engrave_depth"], "base_lbl_in")
    wg = BE.text_w("GND", h, B["font_bold"])                                # label beside the earth point
    regs = BE.glyph_regions([("GND", h, B["font_bold"], (F["earth_y"] + 3.5 + wg / 2) * sign, E.pin_z - h / 2, "center")])
    BE.cut_regions(s, regs, pl, nm, B["engrave_depth"], "base_lbl_gnd")
    s.a("solid.chamfer", edges=[[0.0, -E.Wo / 2, 0.0], [0.0, E.Wo / 2, 0.0], [-E.Lo / 2, 60.0, 0.0], [E.Lo / 2, 60.0, 0.0]], distance=F["chamfer_base"])
    s.color(nm, "al"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm

def lid_rows():
    """Text rows laid out in a (u = reading direction, v = across) frame; the block is turned 90 deg onto the lid's
    long axis (reads bottom-to-top), centred, clear of the port numbers and screws."""
    T = CC.TEXT
    across = E.Lo - 2 * (B["wall"] + 3.0 + BE.text_w("8", 3.0, B["font_bold"]) + 3.0)    # room between the port-number columns
    along = E.Wo - 2 * (B["wall"] + 6.0)
    spec = ((T["logo"], 9.0, B["font_bold"], 3.0), (T["lab"], 3.6, B["font_bold"], 4.0), (T["title"], 3.0, B["font_bold"], 2.0),
            (T["sub"], 2.5, B["font"], 2.6), ("P/N %s  REV A" % T["pn"], 2.4, B["font"], 1.6), ("S/N ________", 2.4, B["font"], 0.0))
    if CC.TEXT.get("only_logo"):
        spec = ((T["logo"], 18.0, B["font_bold"], 0.0),)
    hs = [min(h, along / BE.text_w(t, 1.0, f) * 0.97) for t, h, f, g in spec]
    total = sum(hs) + sum(g for *_, g in spec)
    k = min(1.0, across / total); y = total * k / 2; rows = []
    for (t, h0, f, g), h in zip(spec, hs):
        h = round(h * k, 2); y -= h; rows.append((t, h, f, round(y, 3), "center")); y -= g * k
    return rows

def lid_text_regions():
    from shapely.affinity import rotate
    regs = BE.glyph_regions([(r[0], r[1], r[2], 0.0, r[3], r[4]) for r in lid_rows()])
    return [rotate(g, 90, origin=(0, 0)) for g in regs]

def port_label_rows():
    """Output numbers on the lid top beside the east wall, input label beside the west wall."""
    rows = []
    for p in E.ports:
        h = 3.0
        if p["wall"] == "E": rows.append((p["label"], h, B["font_bold"], E.Lo / 2 - B["wall"] - 3.0, p["off"] - h / 2, "right"))
        else: rows.append(("IN", h, B["font_bold"], -E.Lo / 2 + B["wall"] + 3.0, p["off"] - h / 2, "left"))
    return rows

def build_lid(s, dz=0.0):
    nm = "LID"; z0 = E.z_wall + dz; zt = E.z_top + dz; C = CC.CAGE
    s.rrect(z0, -E.Lo / 2, -E.Wo / 2, E.Lo / 2, E.Wo / 2, B["outer_r"])
    s.a("solid.extrude", distance=B["t_lid"], operation="new", body_name=nm)
    hb = B["h_air"] - C["gap"]                                  # cage block height (face 0.2 above the PCB)
    fx0, fy0, fx1, fy1 = FOOT.bounds
    s.rrect(z0, fx0, fy0, fx1, fy1, B["cav_r"] - 0.1)
    s.a("solid.extrude", distance=hb, direction="negative", operation="join", targets=[nm])
    BE.cut_regions(s, CELLS, {"origin": [0, 0, z0 - hb - 0.1], "x_dir": [1, 0, 0], "y_dir": [0, -1, 0]} if False else
                   {"origin": [0, 0, z0 + 0.0], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, nm, hb - 0.1, "lid_cells")   # cut down from the plate underside
    s.a("sketch.create", plane="XY", offset=zt + 0.1)
    for x, y in E.lid_screws: s.a("sketch.circle.center", center=[x, y], diameter=B["lid_clear_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=B["t_lid"] + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    BE.cut_regions(s, lid_text_regions(), {"origin": [0, 0, zt + 0.1], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, nm, B["engrave_depth"], "lid_txt")
    if F["port_labels"]:
        BE.cut_regions(s, BE.glyph_regions(port_label_rows()), {"origin": [0, 0, zt + 0.1], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, nm, B["engrave_depth"], "lid_ports")
    from shapely.geometry import LineString as _LS
    (x0_, y0_), (x1_, y1_) = DOWELS
    hole = Point(x0_, y0_).buffer(F["dowel_d"] / 2 + 0.006, 48)                              # H7 round hole
    ux_, uy_ = (x0_ - x1_) / math.dist(DOWELS[0], DOWELS[1]), (y0_ - y1_) / math.dist(DOWELS[0], DOWELS[1])
    slot = _LS([(x1_ - ux_ * 0.5, y1_ - uy_ * 0.5), (x1_ + ux_ * 0.5, y1_ + uy_ * 0.5)]).buffer(F["dowel_d"] / 2 + 0.006, 24)   # slot along the dowel line
    BE.cut_regions(s, [hole, slot], {"origin": [0, 0, zt + 0.1], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, nm, B["t_lid"] + 0.1, "lid_dowels")
    s.a("sketch.create", plane="XY", offset=zt + 0.1)                       # jacking holes: M3 tap drill d2.5 through (thread per drawing)
    for x, y in JACKS: s.a("sketch.circle.center", center=[x, y], diameter=THREAD[F["jack"]]["tap"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=B["t_lid"] + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    s.a("solid.chamfer", edges=[[0.0, -E.Wo / 2, zt], [0.0, E.Wo / 2, zt], [-E.Lo / 2, 60.0, zt], [E.Lo / 2, 60.0, zt]], distance=F["chamfer_lid"])
    s.color(nm, "lid"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm

def build_pcb(s, dz=0.0):
    nm = "PCB_XB8_MSL_SL"; z = E.floor + dz
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; mm = d.modelspace()
    mm.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(BRD["outline"].exterior.coords)[:-1]], close=True)
    os.makedirs(os.path.join(BE.OUTDIR, "dxf_src"), exist_ok=True); pth = os.path.join(BE.OUTDIR, "dxf_src", "pcb_outline.dxf"); d.saveas(pth)
    s.a("sketch.create", plane="XY", offset=z); s.a("sketch.insert_dxf", path=os.path.relpath(pth, BE.OUTDIR)); s.a("sketch.finish")
    s.a("solid.extrude", distance=CC.BOARD["t"], profiles=[{"point": [0.0, 0.0]}], operation="new", body_name=nm)
    s.a("sketch.create", plane="XY", offset=z + CC.BOARD["t"] + 0.1)
    for x, y, r in BRD["holes"]: s.a("sketch.circle.center", center=[round(x, 4), round(y, 4)], diameter=2 * r, connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=CC.BOARD["t"] + 0.1, direction="negative", profiles="all", operation="cut", targets=[nm])
    s.color(nm, "pcb")
    # launch traces (top copper) and the 21 resistors
    for p in E.ports:
        ex, ey = p["edge"]; ux = p["u"][0]; x0, x1 = sorted((ex + ux * B["clr"] - ux * 0.3, ex - ux * 6.0))
        s.a("sketch.create", plane="XY", offset=z + CC.BOARD["t"]); s.a("sketch.rectangle.two_point", p0=[round(x0, 4), round(ey - p["w"] / 2, 4)], p1=[round(x1, 4), round(ey + p["w"] / 2, 4)]); s.a("sketch.finish")
        s.a("solid.extrude", distance=CC.BOARD["cu"], operation="new", body_name="TRACE_" + p["label"]); s.color("TRACE_" + p["label"], "cu")
    R = CC.BOARD["resistor"]
    s.a("sketch.create", plane="XY", offset=z + CC.BOARD["t"])
    for x, y, rot, ref in BRD["res"]:
        a, b = (R["W"] / 2, R["L"] / 2) if abs(rot - 90) < 1 else (R["L"] / 2, R["W"] / 2)
        s.a("sketch.rectangle.two_point", p0=[round(x - a, 4), round(y - b, 4)], p1=[round(x + a, 4), round(y + b, 4)])
    s.a("sketch.finish")
    s.a("solid.extrude", distance=R["H"], profiles="all", operation="new", body_name="RESISTORS_0603")
    s.a("appearance.assign", bodies=["RESISTORS_0603"], color="#1d1d1d")
    return nm

def dowels(s, dz=0.0):
    for i, (x, y) in enumerate(DOWELS):
        nm = "DOWEL%d_D2x8" % (i + 1)
        s.a("sketch.create", plane="XY", offset=E.z_wall - F["dowel_depth"] + dz); s.a("sketch.circle.center", center=[x, y], diameter=F["dowel_d"]); s.a("sketch.finish")
        s.a("solid.extrude", distance=F["dowel_len"], operation="new", body_name=nm); s.a("appearance.assign", bodies=[nm], color="#d0d4d8")

def box_only():
    s = BE.S(); build_base(s); dowels(s); build_lid(s)
    for i, (x, y) in enumerate(E.lid_screws):
        BE.screw(s, "SL%d_M2.5" % (i + 1), "M2.5_BH", B["lid_screw_len"], [x, y, E.z_top], [0, 0, 1])
    return s

def assembly(explode=False):
    s = BE.S(); d = dict(lid=34.0, lid_s=52.0, pcb=14.0, pcb_s=24.0, conn=16.0, conn_s=12.0) if explode else dict(lid=0, lid_s=0, pcb=0, pcb_s=0, conn=0, conn_s=0)
    build_base(s); build_pcb(s, d["pcb"])
    for i, (x, y) in enumerate(E.pcb_screws):
        BE.screw(s, "SP%d_M3" % (i + 1), "M3", 6.0, [x, y, E.floor + CC.BOARD["t"] + d["pcb"] + d["pcb_s"]], [0, 0, 1])
    dowels(s, d["pcb"] * 0)
    build_lid(s, d["lid"])
    for i, (x, y) in enumerate(E.lid_screws):
        BE.screw(s, "SL%d_M2.5" % (i + 1), "M2.5_BH", B["lid_screw_len"], [x, y, E.z_top + d["lid"] + d["lid_s"]], [0, 0, 1])
    BE.add_connectors(s, E, d["conn"], d["conn_s"])
    return s

# ---------------- checks + report ----------------
def report(res_assy):
    C = CC.CAGE; lines = ["# X-band 8-way MSL-SL stripline divider - cage housing (%s)" % CC.TEXT["pn"], ""]
    lines += ["| Item | Value |", "|---|---|",
              "| Board (from the customer DXF) | %.3f x %.3f mm, 2 mm corner chamfers, 4 x d3.2 holes; thickness %.3f mm **[ASSUMED]** |" % (BRD["L"], BRD["W"], CC.BOARD["t"]),
              "| Ports | IN on the west wall; outputs 1-8 on the east wall at y = %s mm (board centre) |" % ", ".join("%+.2f" % p["off"] for p in E.ports[1:]),
              "| Launch | top-layer microstrip %.3f mm wide, 0.3 mm set back from the board edge |" % BRD["w"],
              "| Outside | %.2f x %.2f x %.2f mm (base %.2f + lid plate %.1f) |" % (E.Lo, E.Wo, E.z_top, E.z_wall, B["t_lid"]),
              "| Cavity | %.3f x %.3f mm, floor %.2f, connector axis %.3f above the bottom |" % (E.Lc, E.Wc, E.floor, E.pin_z),
              "| Cage | block %.1f mm tall under the lid, face %.2f above the PCB (0.25 mm conductive elastomer sheet recommended); ribs %.1f mm on a %.1f mm grid; %d cells |" % (B["h_air"] - C["gap"], C["gap"], C["rib"], C["pitch"], len(CELLS)),
              "| Lid screws | %d x M2.5 x %.0f ISO 7380; largest gap %.2f mm |" % (len(E.lid_screws), B["lid_screw_len"], E.max_screw_gap()),
              "| Board screws | 4 x M3 x 6 ISO 4762 through the board's own holes into the floor (pockets in the cage clear the heads) |",
              "| Connectors | 9 x HUBER+SUHNER 23_SMA-50-0-272/133_N, 36 x M2.5 x 5 ISO 4762 |",
              "| Lid location | 2 x d2 h6 dowels ISO 8734 2x8 pressed in the N/S walls at %s; lid: d2 H7 hole + d2 H7 x 1 slot |" % DOWELS,
              "| Lid removal | 2 x M3 jacking holes through the lid at %s (push on the wall top) |" % JACKS,
              "| Earth point | %s tapped %.0f deep, west wall, y = %+.0f mm, at the connector-axis height |" % (F["earth"], F["earth_depth"], F["earth_y"]),
              "| Edges | lid top %.1f x 45 deg, base bottom %.1f x 45 deg, vertical edges R%.0f |" % (F["chamfer_lid"], F["chamfer_base"], B["outer_r"]), ""]
    lines += ["## Checks", "", "| Check | Value (mm) | Rule | Result |", "|---|---|---|---|"]
    for n, v, lim, ok, u in E.checks(): lines.append("| %s | %.2f | %s | %s |" % (n, v, lim, "OK" if ok else "**WARN**"))
    rs = cell_resonances(); fmax = CC.BOARD["band"][1]
    lines.append("| lowest cage-cell resonance (largest cell %.1f x %.1f) | %.2f GHz | > 1.3 x f_max = %.1f GHz | %s |" % (rs[0][1], rs[0][2], rs[0][0], 1.3 * fmax, "OK" if rs[0][0] > 1.3 * fmax else "**WARN**"))
    open_cav = EC_C0 / 2 * math.sqrt(1 / E.Lc ** 2 + 1 / E.Wc ** 2)
    lines.append("| (for comparison) open cavity without the cage, TE110 | %.2f GHz | - | in band: the cage is what removes it |" % open_cav)
    lines += ["", "## Cage cells (largest first)", "", "| Cell (a x b mm) | TE110 (GHz) |", "|---|---|"]
    for f, a, b in rs[:10]: lines.append("| %.1f x %.1f | %.1f |" % (a, b, f))
    if res_assy:
        vol = {bd["name"]: bd["volume_mm3"] for bd in res_assy["bodies"]}
        lines += ["", "Machined mass (Al): base %.0f g, lid %.0f g." % (vol.get("BASE", 0) * 2.70e-3, vol.get("LID", 0) * 2.70e-3)]
    open(os.path.join(ROOT, "05_docs", "design_report.md"), "w").write("\n".join(lines) + "\n")
    return lines

def cage_preview(path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 13))
    ax.add_patch(plt.Polygon(list(FOOT.exterior.coords), fc="#9aa3ab", ec="k"))
    for c in CELLS: ax.add_patch(plt.Polygon(list(c.exterior.coords), fc="white", ec="k", lw=0.5))
    ax.add_patch(plt.Polygon(list(BRD["outline"].exterior.coords), fc="none", ec="g", ls="--", lw=0.6))
    for x, y, rot, ref in BRD["res"]: ax.add_patch(plt.Rectangle((x - 0.4, y - 0.8), 0.8, 1.6, fc="k"))
    for p in E.ports: ax.text(p["edge"][0] - p["u"][0] * 4.5, p["off"], p["label"], ha="center", va="center", fontsize=7, color="r")
    ax.set_aspect("equal"); ax.autoscale_view(); ax.set_title("Cage block seen from below: grey = ribs on the top ground, white = cells", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)

def main(parts=("base", "lid", "assy", "exploded")):
    BE.OUTDIR = OUT; os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(ROOT, "05_docs"), exist_ok=True)
    pn = CC.TEXT["pn"]; ra = None
    cage_preview(os.path.join(ROOT, "03_drawings", pn + "_cage_from_below.png"))
    if "base" in parts:
        s = BE.S(); build_base(s); BE.run(s, os.path.join(OUT, pn + "_BASE.solidcraft.json"), [pn + "_BASE.step"])
    if "lid" in parts:
        s = BE.S(); build_lid(s); BE.run(s, os.path.join(OUT, pn + "_LID.solidcraft.json"), [pn + "_LID.step"], [("top", pn + "_lid_top.png"), ("bottom", pn + "_lid_cage_bottom.png")])
    if "box" in parts:
        BE.run(box_only(), os.path.join(OUT, pn + "_BOX_ONLY.solidcraft.json"), [pn + "_BOX_ONLY.step"], [("iso", pn + "_box_only.png")])
    if "assy" in parts:
        ra = BE.run(assembly(), os.path.join(OUT, pn + "_ASSY.solidcraft.json"), [pn + "_ASSY.step"], [("iso", pn + "_iso.png")])
    if "exploded" in parts:
        BE.run(assembly(True), os.path.join(OUT, pn + "_ASSY_EXPLODED.solidcraft.json"), [pn + "_ASSY_EXPLODED.step"], [("iso", pn + "_exploded.png")])
    for l in report(ra)[:40]: print(l)

if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("base", "lid", "box", "assy", "exploded"))
