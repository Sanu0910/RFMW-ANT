"""Cal-line base plate: geometry (from the cal-board DXF + config.py) and the SolidCraft scripts for the plate and assembly.
Frame: x along the line (origin = J1 signal via of the board DXF), y = 0 on the line, z = 0 on the plate bottom."""
import os, json, math, shutil, subprocess
import ezdxf
from ezdxf import path as ezpath
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import config as C
import artwork as A

THREAD = {"M2.5": dict(d=2.5, tap=2.05, head_d=4.5, head_k=2.5, socket=2.0),
          "M3": dict(d=3.0, tap=2.5, head_d=5.5, head_k=3.0, socket=2.5)}
COL = {"al": "#b9c0c7", "pcb": "#2f6b3a", "cu": "#c8823a", "screw": "#3a3d42", "conn": "#d8c37a"}
OUT = os.path.join(C.ROOT, "03_step")


def _poly(e):
    pts = [(round(p.x, 5), round(p.y, 5)) for p in ezpath.make_path(e).flattening(0.005)]
    return Polygon(pts).buffer(0)


def read_board(key):
    """Board outline, mounting holes and top copper from the customer DXFs."""
    b = C.BOARDS[key]
    m = ezdxf.readfile(b["mech"]).modelspace()
    out = _poly(next(iter(m.query('LWPOLYLINE[layer=="BOARD_OUTLINE"]'))))
    holes = [(round(e.dxf.center.x, 4), round(e.dxf.center.y, 4), round(2 * e.dxf.radius, 4)) for e in m.query('CIRCLE[layer=="MOUNTING_HOLES"]')]
    conn = [_poly(e).bounds for e in m.query('LWPOLYLINE[layer=="CONNECTOR"]')]
    a = ezdxf.readfile(b["all"]).modelspace()
    sig = [_poly(e) for e in a.query('LWPOLYLINE[layer=="TOP_SIGNAL"]')]
    gnd = [_poly(e) for e in a.query('LWPOLYLINE[layer=="TOP_GROUND"]')]
    return dict(b, key=key, outline=out, holes=sorted(holes), conn=conn, top_sig=sig, top_gnd=gnd)


class Plate:
    def __init__(self, B):
        P, K, t = C.PLATE, C.CONN, C.PCB["t"]
        self.B = B
        bx0, by0, bx1, by1 = B["outline"].bounds
        self.board = (bx0, by0, bx1, by1)
        self.xw, self.xe = bx0 - P["clr_x"], bx1 + P["clr_x"]                  # pocket ends = wall inner faces
        self.yp = by1 + P["clr_y"]                                             # pocket half width
        self.x0, self.x1 = self.xw - P["wall"], self.xe + P["wall"]            # plate ends = wall outer faces (flange seats)
        self.yo = self.yp + P["rim"]
        self.L, self.W = self.x1 - self.x0, 2 * self.yo
        pin_r = K["pin_d"] / 2
        self.pin_z = K["flange"] / 2 + P["flange_margin"]                      # connector axis height
        self.z_pcb_top = self.pin_z - pin_r                                    # pin bottom rests on the trace
        self.z_floor = self.z_pcb_top - t
        self.z_top = self.z_floor + P["pocket"]
        self.z_wall = self.pin_z + K["flange"] / 2 + P["wall_above_flange"]
        self.z_under = self.z_floor - P["skin"]                                # underside pocket depth
        self.pocket_r = 2.0 + max(P["clr_x"], P["clr_y"])
        self.pocket = self._rrect(self.xw, -self.yp, self.xe, self.yp, self.pocket_r)
        xc = (bx0 + bx1) / 2; nw = P["notch_w"] / 2
        self.notches = [box(xc - nw, self.yp - 0.5, xc + nw, self.yo + 0.5), box(xc - nw, -self.yo - 0.5, xc + nw, -self.yp + 0.5)]
        self.ports = []
        for lab, ux, xf in (("J1", -1, self.x0), ("J2", 1, self.x1)):
            holes = [(xf, s1 * K["hole_sq"] / 2, self.pin_z + s2 * K["hole_sq"] / 2) for s1 in (-1, 1) for s2 in (-1, 1)]
            self.ports.append(dict(label=lab, ux=ux, xf=xf, holes=holes, rot=0.0 if ux < 0 else 180.0))
        self.walls = [box(self.x0, -P["wall_w"] / 2, self.xw, P["wall_w"] / 2), box(self.xe, -P["wall_w"] / 2, self.x1, P["wall_w"] / 2)]
        self.under = self._under()

    @staticmethod
    def _rrect(x0, y0, x1, y1, r):
        return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=32)

    def _under(self):
        """Underside lightening pockets: inside the rims, off the wall zones, round the M3 bosses, split by ribs."""
        P = C.PLATE
        xa, xb = self.xw + P["under_end"], self.xe - P["under_end"]
        g = box(xa, -self.yo + P["under_rim"], xb, self.yo - P["under_rim"])
        cut = [Point(x, y).buffer(P["boss_r"], resolution=32) for x, y, _d in self.B["holes"]]
        cut.append(box(xa - 1, -P["rib"] / 2, xb + 1, P["rib"] / 2))                     # rib along the line
        n = max(1, math.ceil((xb - xa) / P["rib_x"]))
        for i in range(1, n):
            xr = xa + i * (xb - xa) / n
            cut.append(box(xr - P["rib"] / 2, -self.yo, xr + P["rib"] / 2, self.yo))
        g = g.difference(unary_union(cut))
        g = g.buffer(-P["tool_r"], join_style=1).buffer(P["tool_r"], resolution=32)  # tool radius + drop slivers
        return [q for q in (g.geoms if hasattr(g, "geoms") else [g]) if q.area > 4.0]

    def summary(self):
        return dict(L=self.L, W=self.W, H=self.z_wall, z_floor=self.z_floor, z_top=self.z_top, z_pcb_top=self.z_pcb_top,
                    pin_z=self.pin_z, z_wall=self.z_wall, x0=self.x0, x1=self.x1, xw=self.xw, xe=self.xe, yp=self.yp, yo=self.yo)

    def checks(self):
        P, K, t = C.PLATE, C.CONN, C.PCB["t"]
        r = []
        def chk(name, val, rule, ok): r.append((name, val, rule, bool(ok)))
        fb = self.pin_z - K["flange"] / 2
        chk("Connector flange bottom above the bench", "%.2f" % fb, ">= 0.5", fb >= 0.5 - 1e-9)
        chk("Wall top above the flange top", "%.2f" % (self.z_wall - self.pin_z - K["flange"] / 2), ">= 0.5", self.z_wall - self.pin_z - K["flange"] / 2 >= 0.5)
        sp = K["spigot_len"] - P["wall"]
        gap = P["clr_x"] - sp
        chk("Spigot face to board edge (nominal)", "%.2f" % gap, ">= 0.05 (board +/-0.1 is centred by the pocket)", gap >= 0.05)
        cu0 = min(q.bounds[0] for q in self.B["top_sig"]) - self.board[0]                # copper pull-back from the board edge
        ov = K["pin_proj"] + sp - P["clr_x"] - cu0
        chk("Pin length on the launch copper", "%.2f" % ov, ">= 2.0 (solder fillet)", ov >= 2.0)
        cx0, cy0, cx1, cy1 = self.B["conn"][0]
        chk("Pin inside the DXF CONNECTOR zone", "x %.2f..%.2f" % (self.board[0] + P["clr_x"] - sp, self.board[0] + P["clr_x"] - sp + K["pin_proj"]),
            "<= %.2f" % cx1, self.xw + sp + K["pin_proj"] <= cx1 + 1e-6)
        chk("Pocket floor skin over the underside pockets", "%.2f" % (self.z_floor - self.z_under), ">= 2.0", self.z_floor - self.z_under >= 2.0 - 1e-9)
        lo = self.pin_z - K["hole_sq"] / 2 - THREAD["M2.5"]["d"] / 2
        chk("Lower M2.5 flange taps inside solid plate", "z %.2f..%.2f" % (lo, lo + 2.5), "> 0, wall zone solid", lo > 0 and min(q.bounds[0] for q in self.under) > self.xw)
        top = self.z_wall - (self.pin_z + K["hole_sq"] / 2 + THREAD["M2.5"]["d"] / 2)
        chk("Metal above the upper M2.5 taps", "%.2f" % top, ">= 1.0", top >= 1.0)
        eng = P["m3_screw_len"] - t
        chk("M3 x %g thread engagement in the plate" % P["m3_screw_len"], "%.2f" % eng, ">= 1.2 d = 3.6, <= floor %.2f" % self.z_floor, 3.6 <= eng <= self.z_floor)
        hd = THREAD["M3"]["head_d"] / 2
        chk("M3 head inside the DXF keep-out (r 3.0)", "head r %.2f" % hd, "<= 3.0", hd <= 3.0)
        m_ok = all(Point(x, y).buffer(P["boss_r"] - 0.01).intersection(unary_union(self.under)).area < 1e-6 for x, y, _d in self.B["holes"])
        chk("M3 taps fully in solid bosses", "boss r %.1f" % P["boss_r"], "no underside pocket inside", m_ok)
        return r


# ======================= SolidCraft script writer =======================
class S:
    def __init__(self): self.c = []
    def a(self, cmd, **p): self.c.append({"command": cmd, "params": p})
    def color(self, body, col): self.a("appearance.assign", bodies=[body], color=COL[col])


def plane_for(origin, axis):
    ax = [float(v) for v in axis]
    ref = [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]
    xd = [ref[1] * ax[2] - ref[2] * ax[1], ref[2] * ax[0] - ref[0] * ax[2], ref[0] * ax[1] - ref[1] * ax[0]]
    n = math.sqrt(sum(v * v for v in xd)); xd = [v / n for v in xd]
    yd = [ax[1] * xd[2] - ax[2] * xd[1], ax[2] * xd[0] - ax[0] * xd[2], ax[0] * xd[1] - ax[1] * xd[0]]
    return {"origin": [round(v, 6) for v in origin], "x_dir": [round(v, 9) for v in xd], "y_dir": [round(v, 9) for v in yd]}


def xy_plane(z): return {"origin": [0, 0, round(z, 6)], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}


def screw(s, name, size, length, seat, axis_out):
    """ISO 4762 socket head cap screw; seat = point under the head, axis_out = from the hole toward the head."""
    t = THREAD[size]; pl = plane_for(seat, axis_out)
    s.a("sketch.create", plane=pl); s.a("sketch.circle.center", center=[0, 0], diameter=t["head_d"]); s.a("sketch.finish")
    s.a("solid.extrude", distance=t["head_k"], operation="new", body_name=name)
    s.a("sketch.create", plane=pl); s.a("sketch.circle.center", center=[0, 0], diameter=t["d"]); s.a("sketch.finish")
    s.a("solid.extrude", distance=length, direction="negative", operation="new", body_name=name + "_shank")
    top = [seat[k] + axis_out[k] * t["head_k"] for k in range(3)]
    s.a("sketch.create", plane=plane_for(top, axis_out)); s.a("sketch.polygon.inscribed", center=[0, 0], radius=t["socket"] / math.sqrt(3), sides=6); s.a("sketch.finish")
    s.a("solid.extrude", distance=t["head_k"] * 0.55, direction="negative", operation="cut", targets=[name])
    s.a("solid.combine", target=name, tools=[name + "_shank"], operation="join")
    s.color(name, "screw")


def dxf_regions(regs, tag):
    """Regions -> DXF of closed polylines (robust planar booleans); returns (path relative to 03_step, pick points)."""
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace(); pts = []
    for r in regs:
        for ring in [r.exterior] + list(r.interiors):
            m.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(ring.coords)[:-1]], close=True)
        q = r.representative_point(); pts.append({"point": [round(q.x, 4), round(q.y, 4)]})
    os.makedirs(os.path.join(OUT, "dxf_src"), exist_ok=True)
    p = os.path.join(OUT, "dxf_src", tag + ".dxf"); d.saveas(p)
    return os.path.relpath(p, OUT).replace("\\", "/"), pts


def extrude_regions(s, regs, plane, depth, tag, op, body, direction=None):
    rel, pts = dxf_regions(regs, tag)
    s.a("sketch.create", plane=plane); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    p = dict(distance=depth, profiles=pts, operation=op)
    if direction: p["direction"] = direction
    if op == "new": p["body_name"] = body
    else: p["targets"] = [body]
    s.a("solid.extrude", **p)


def build_plate(s, H):
    P, K = C.PLATE, C.CONN; nm = "PLATE"; pn = H.B["pn"]; tag = pn
    s.a("sketch.create", plane="XY", offset=0.0)
    s.a("sketch.rectangle.rounded", p0=[H.x0, -H.yo], p1=[H.x1, H.yo], radius=P["corner_r"]); s.a("sketch.finish")
    s.a("solid.extrude", distance=H.z_top, operation="new", body_name=nm)
    xm = (H.x0 + H.x1) / 2
    s.a("solid.chamfer", edges=[[xm, -H.yo, 0.0], [xm, H.yo, 0.0], [H.x0, 0.0, 0.0], [H.x1, 0.0, 0.0]], distance=P["chamfer"])   # bottom outside edges
    extrude_regions(s, H.walls, xy_plane(H.z_top), H.z_wall - H.z_top, tag + "_walls", "join", nm)
    pk = unary_union([H.pocket] + H.notches)
    extrude_regions(s, [pk], xy_plane(H.z_top), P["pocket"], tag + "_pocket", "cut", nm, "negative")
    extrude_regions(s, H.under, xy_plane(0), H.z_under, tag + "_underside", "cut", nm)
    for p in H.ports:
        ux = p["ux"]
        s.a("solid.hole", position=[p["xf"], 0.0, H.pin_z], direction=[-ux, 0, 0], diameter=K["bore_d"], depth=P["wall"] + 0.5)
        for hx, hy, hz in p["holes"]:
            s.a("solid.hole", position=[hx, hy, hz], direction=[-ux, 0, 0], thread=K["screw"], depth=K["tap_depth"])
    for x, y, _d in H.B["holes"]:
        s.a("solid.hole", position=[x, y, H.z_floor], direction=[0, 0, -1], thread="M3", depth=H.z_floor + 0.5)
    # engraving: part number on the -y side face (reads left to right from the front), J1 / J2 on the wall tops
    pl = {"origin": [0.0, -H.yo - 0.1, 0.0], "x_dir": [1.0, 0.0, 0.0], "y_dir": [0.0, 0.0, 1.0]}
    h = 2.0
    regs = A.text_regions("%s REV %s" % (pn, C.TEXT["rev"]), h, C.FONT_BOLD, xm, (P["chamfer"] + H.z_top) / 2 - h / 2)
    extrude_regions(s, regs, pl, P["engrave_depth"] + 0.1, tag + "_side_text", "cut", nm, "negative")
    regs = []
    for p in H.ports:
        regs += A.text_regions(p["label"], 2.2, C.FONT_BOLD, p["xf"] - p["ux"] * P["wall"] / 2, -1.1)
    extrude_regions(s, regs, xy_plane(H.z_wall + 0.1), P["engrave_depth"] + 0.1, tag + "_wall_text", "cut", nm, "negative")
    s.color(nm, "al"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm


def build_pcb(s, H, dz=0.0):
    B = H.B; t, cu = C.PCB["t"], C.PCB["cu"]; z = H.z_floor + dz; nm = "CAL_PCB"; pn = B["pn"]
    g = B["outline"].difference(unary_union([Point(x, y).buffer(d / 2, resolution=24) for x, y, d in B["holes"]]))
    extrude_regions(s, [g], xy_plane(z), t - cu, pn + "_pcb", "new", nm); s.color(nm, "pcb")
    gnd = unary_union(B["top_gnd"]).difference(unary_union([Point(x, y).buffer(d / 2 + 0.3, resolution=24) for x, y, d in B["holes"]]))
    cu_regs = list(gnd.geoms if hasattr(gnd, "geoms") else [gnd]) + [q.simplify(0.003) for q in B["top_sig"]]
    extrude_regions(s, cu_regs, xy_plane(z + t - cu), cu, pn + "_pcb_cu", "new", "CAL_PCB_TOP_CU"); s.color("CAL_PCB_TOP_CU", "cu")


def add_connectors(s, H, out=0.0, sout=0.0):
    K = C.CONN
    for p in H.ports:
        nm = "%s_SMA" % p["label"]; ux = p["ux"]
        s.a("file.insert_step", path=os.path.relpath(K["step"], OUT).replace("\\", "/"), name=nm)
        s.a("body.rename", body="PartBody", name=nm)
        if p["rot"]: s.a("solid.move", bodies=[nm], axis=[0, 0, 1], angle=p["rot"])
        s.a("solid.move", bodies=[nm], translate=[round(p["xf"] + K["x_contact"] * ux + ux * out, 6), 0.0, round(H.pin_z, 6)])
        s.color(nm, "conn")
        for j, (hx, hy, hz) in enumerate(p["holes"]):
            screw(s, "SC_%s_%d_M2.5x5" % (p["label"], j + 1), "M2.5", K["screw_len"], [hx + ux * (K["flange_t"] + out + sout), hy, hz], [ux, 0, 0])


def assembly(H, explode=False):
    P = C.PLATE; s = S()
    d = dict(pcb=10.0, pcb_s=8.0, conn=14.0, conn_s=8.0) if explode else dict.fromkeys(("pcb", "pcb_s", "conn", "conn_s"), 0.0)
    build_plate(s, H); build_pcb(s, H, d["pcb"])
    for i, (x, y, _d) in enumerate(H.B["holes"]):
        screw(s, "SP%d_M3x%g" % (i + 1, P["m3_screw_len"]), "M3", P["m3_screw_len"], [x, y, H.z_pcb_top + d["pcb"] + d["pcb_s"]], [0, 0, 1])
    add_connectors(s, H, d["conn"], d["conn_s"])
    return s


def _exe():
    return shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"


def measure(step_name):
    """Volume etc. of an exported STEP (solidcraft-cli eval), {} if the file is missing."""
    if not os.path.exists(os.path.join(OUT, step_name)): return {}
    jo = os.path.join(OUT, "_measure.json")
    r = subprocess.run([_exe(), "eval", step_name, "--json-out", os.path.basename(jo)], capture_output=True, text=True, cwd=OUT)
    if r.returncode or not os.path.exists(jo): return {}
    with open(jo, encoding="utf-8") as fh: res = json.load(fh)
    os.remove(jo)
    return res


def run(script, name, outs, snaps=()):
    os.makedirs(OUT, exist_ok=True)
    js = os.path.join(OUT, name + ".solidcraft.json")
    with open(js, "w") as fh: json.dump({"commands": script.c}, fh, indent=0)
    jo = os.path.join(OUT, "_" + name + ".result.json")
    r = subprocess.run([_exe(), "run", os.path.basename(js), "--json-out", os.path.basename(jo)] + sum((["--out", o] for o in outs), []),
                       capture_output=True, text=True, cwd=OUT)
    if r.returncode:
        print(r.stdout[-4000:], r.stderr[-4000:]); raise SystemExit("solidcraft failed: " + name)
    with open(jo, encoding="utf-8") as fh: res = json.load(fh)
    os.remove(jo)
    for view, png, extra in snaps:
        rr = subprocess.run([_exe(), "snapshot", os.path.basename(js), "--out", png, "--width", "1800", "--height", "1300", "--view", view, "--no-grid"] + list(extra),
                            capture_output=True, text=True, cwd=OUT)
        if rr.returncode: print("snapshot failed", png, rr.stderr[-500:])
    return res
