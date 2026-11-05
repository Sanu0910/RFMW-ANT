"""Housing geometry (derived numbers + screw layout) and the SolidCraft command scripts for every part.
Frame: x east, y north (board-outline centre), z = 0 on the base bottom."""
import os, json, math, shutil, subprocess
import ezdxf
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
import config as C
import geom as G
import artwork as A

THREAD = {"M2": dict(d=2.0, tap=1.6, head_d=3.8, head_k=2.0, socket=1.5),
          "M2.5": dict(d=2.5, tap=2.05, head_d=4.5, head_k=2.5, socket=2.0),
          "M3": dict(d=3.0, tap=2.5, head_d=5.5, head_k=3.0, socket=2.5),
          "M2.5_BH": dict(d=2.5, tap=2.05, head_d=4.7, head_k=1.3, socket=1.5)}
COL = {"al": "#b9c0c7", "lid": "#a7b0b9", "pcb": "#2f6b3a", "cu": "#c8823a", "screw": "#3a3d42", "conn": "#d8c37a",
       "gasket": "#4a4f55", "res": "#1d1d1d", "dowel": "#d0d4d8"}
OUT = os.path.join(C.ROOT, "03_step")


class Housing:
    def __init__(self, B, holes):
        X, K = C.BOX, C.CONN
        self.B, self.holes = B, holes
        self.Lc, self.Wc = B["L"] + 2 * X["clr"], B["W"] + 2 * X["clr"]
        self.Lo, self.Wo = self.Lc + 2 * X["wall"], self.Wc + 2 * X["wall"]
        t = C.BOARD["t"]; pin_r = K["pin_d"] / 2
        self.floor = max(X["floor_min"], K["flange"] / 2 + X["flange_margin"] - (t + pin_r))
        self.z_pcb_top = self.floor + t
        self.pin_z = self.z_pcb_top + pin_r
        self.z_wall = self.z_pcb_top + X["h_air"]
        self.z_top = self.z_wall + X["t_lid"]
        self.z_face = self.z_pcb_top + C.CAGE["gap"]                     # cage face (gasket compressed between)
        self.cav = box(-self.Lc / 2, -self.Wc / 2, self.Lc / 2, self.Wc / 2)
        self.foot = self.cav.buffer(-0.1, join_style=2)                  # cage block outline
        self.ports = []
        for p in B["ports"]:
            u = (-1, 0) if p["wall"] == "W" else (1, 0)
            face = (u[0] * self.Lo / 2, p["y"])
            holes = [(face[0], p["y"] + s1 * K["hole_sq"] / 2, self.pin_z + s2 * K["hole_sq"] / 2) for s1 in (-1, 1) for s2 in (-1, 1)]
            self.ports.append(dict(p, u=u, face=face, holes=holes, rot=0.0 if p["wall"] == "W" else 180.0,
                                   edge=(u[0] * B["L"] / 2, p["y"])))
        self.channels = G.cage_channels(B, self.cav).intersection(self.foot.buffer(1.0, join_style=2))
        self.a, self.c = self.Lo / 2 - X["wall"] / 2, self.Wo / 2 - X["wall"] / 2     # wall centre-line track
        self.dowels = [(round(-self.a + 12.0, 3), round(self.c, 3)), (round(self.a - 12.0, 3), round(-self.c, 3))]
        self.jacks = [(0.0, round(self.c, 3)), (0.0, round(-self.c, 3))]
        self.earth = (-self.Lo / 2, -30.0, round(self.floor / 2 + 0.05, 3))      # blind M3 in the solid floor zone (the wall alone is only 5 mm)
        self.lid_screws = self._lid_screws()
        self.mount = self._mount()

    # ---------- lid screws: per side, a minimax-gap row that avoids the connector bores and flange threads ----------
    def _forbidden(self, x, y):
        K = C.CONN; X = C.BOX
        for p in self.ports:
            if abs(abs(x) - self.a) < 0.01 and math.copysign(1, x) == p["u"][0]:
                along = abs(y - p["y"])
                if along < K["bore_d"] / 2 + THREAD["M2.5"]["tap"] / 2 + 1.0: return True            # spigot bore below
                if abs(along - K["hole_sq"] / 2) < THREAD["M2.5"]["d"] / 2 + THREAD["M2.5"]["tap"] / 2 + 1.0: return True   # flange thread
        for q in self.dowels + self.jacks:
            if math.dist((x, y), q) < 4.5: return True
        if math.dist((x, y), self.earth[:2]) < 4.0: return True
        return False

    def _row(self, p0, p1):
        L = math.dist(p0, p1); ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        g = [k * 0.1 for k in range(int(L / 0.1) + 1)]
        g = [t for t in g if not self._forbidden(p0[0] + ux * t, p0[1] + uy * t)]
        dmin = C.BOX["lid_head_d"] + 1.0; P = C.BOX["lid_screw_pitch"]     # gaps up to the pitch cost the same -> fewest screws
        best = {0: (0.0, 1, None)} if g and g[0] == 0 else {}
        if not best: raise RuntimeError("corner lid screw forbidden")
        for i in range(1, len(g)):
            cand = None
            for j in range(i - 1, -1, -1):
                if g[i] - g[j] < dmin - 1e-9: continue
                if j in best:
                    v = (max(best[j][0], g[i] - g[j], P), best[j][1] + 1, j)
                    if cand is None or v[:2] < cand[:2]: cand = v
                if g[i] - g[j] > 40: break
            if cand: best[i] = cand
        i = max(best) if abs(g[-1] - L) > 0.05 else len(g) - 1
        row = []
        while i is not None: row.append(g[i]); i = best[i][2]
        return [(round(p0[0] + ux * t, 3), round(p0[1] + uy * t, 3)) for t in row]

    def _lid_screws(self):
        a, c = self.a, self.c
        pts = []
        for p0, p1 in (((-a, -c), (a, -c)), ((a, -c), (a, c)), ((a, c), (-a, c)), ((-a, c), (-a, -c))):
            for q in self._row(p0, p1):
                if all(math.dist(q, r) > 0.5 for r in pts): pts.append(q)
        return pts

    def max_screw_gap(self, side=None):
        a, c = self.a, self.c; per = 4 * (a + c)
        def s_of(x, y):
            if abs(y + c) < 0.01: return x + a
            if abs(x - a) < 0.01: return 2 * a + (y + c)
            if abs(y - c) < 0.01: return 2 * a + 2 * c + (a - x)
            return 4 * a + 2 * c + (c - y)
        s = sorted(s_of(x, y) for x, y in self.lid_screws)
        gaps = [s[k + 1] - s[k] for k in range(len(s) - 1)] + [per - s[-1] + s[0]]
        return max(gaps)

    def _mount(self):
        """4 x M3 from the bottom, in the N and S walls, midway between lid screws near x = +-Lo/4."""
        out = []
        for sy in (-1, 1):
            xs = sorted(x for x, y in self.lid_screws if abs(y - sy * self.c) < 0.01)
            mids = [(xs[k] + xs[k + 1]) / 2 for k in range(len(xs) - 1)]
            for sx in (-1, 1):
                t = sx * self.Lo / 4
                m = min((v for v in mids if all(math.dist((v, sy * self.c), d) > 5 for d in self.dowels + self.jacks)), key=lambda v: abs(v - t))
                out.append((round(m, 3), round(sy * self.c, 3)))
        return out

    # ---------- checks ----------
    def checks(self):
        X, K, Q = C.BOX, C.CONN, C.CAGE; r = []
        def chk(name, val, rule, ok): r.append((name, val, rule, bool(ok)))
        chk("flange bottom above base bottom", self.pin_z - K["flange"] / 2, ">= %.2f" % X["flange_margin"], self.pin_z - K["flange"] / 2 >= X["flange_margin"] - 1e-9)
        chk("flange top below lid top", self.z_top - (self.pin_z + K["flange"] / 2), ">= 0", self.z_top >= self.pin_z + K["flange"] / 2)
        top_thr = self.pin_z + K["hole_sq"] / 2 + THREAD["M2.5"]["d"] / 2
        chk("upper flange thread below the lid seat", self.z_wall - top_thr, ">= 0.5", self.z_wall - top_thr >= 0.5)
        chk("lower flange thread above base bottom", self.pin_z - K["hole_sq"] / 2 - THREAD["M2.5"]["d"] / 2, ">= 0.5", self.pin_z - K["hole_sq"] / 2 - 1.25 >= 0.5)
        chk("spigot length - wall", K["spigot_len"] - X["wall"], "0 .. 0.2", 0 <= K["spigot_len"] - X["wall"] <= 0.2)
        ov = K["spigot_len"] + K["pin_proj"] - X["wall"] - X["clr"] - C.PCB_HOLES.get("cu_pullback", 0.25)
        chk("pin length on the trace (after 0.25 copper pull-back)", ov, ">= 2.0", ov >= 2.0)
        chk("pin axis - PCB top (pin rests on the copper)", self.pin_z - self.z_pcb_top, "= pin radius %.2f" % (K["pin_d"] / 2), True)
        chk("floor thickness", self.floor, ">= %.1f" % X["floor_min"], self.floor >= X["floor_min"])
        ez = self.earth[2]
        chk("earth M3 in the solid floor zone (thread top below the cavity floor)", self.floor - (ez + 1.5), ">= 0.5", self.floor - (ez + 1.5) >= 0.5)
        chk("earth M3 thread above the bottom chamfer", ez - 1.5 - X["chamfer_base"], ">= 0.4", ez - 1.5 - X["chamfer_base"] >= 0.4)
        chk("floor left under the M2 tap", self.floor - X["pcb_tap_depth"], ">= 0.8", self.floor - X["pcb_tap_depth"] >= 0.8)
        eng = X["pcb_screw_len"] - C.BOARD["t"]
        chk("M2 PCB screw thread engagement", eng, ">= 1.5 d = 3.0", eng >= 3.0)
        chk("M2 tap deeper than the screw", X["pcb_tap_depth"] - eng, ">= 0.3", X["pcb_tap_depth"] - eng >= 0.3)
        eng = X["lid_screw_len"] - X["t_lid"]
        chk("M2.5 lid screw thread engagement", eng, ">= 1.4 d = 3.5", eng >= 3.5)
        chk("M2.5 lid tap deeper than the screw", X["lid_tap_depth"] - eng, ">= 0.5", X["lid_tap_depth"] - eng >= 0.5)
        # lid taps reach down past the upper flange threads, so they must sit beside them along the wall
        cl = []
        for x, y in self.lid_screws:
            for p in self.ports:
                if abs(abs(x) - self.a) < 0.01 and math.copysign(1, x) == p["u"][0]:
                    for hx, hy, hz in p["holes"]:
                        cl.append(abs(y - hy) - THREAD["M2.5"]["tap"] / 2 - THREAD["M2.5"]["d"] / 2)
                    cl.append(abs(y - p["y"]) - THREAD["M2.5"]["tap"] / 2 - K["bore_d"] / 2)
        chk("lid tap to flange thread / spigot bore (wall left)", min(cl), ">= 1.0", min(cl) >= 1.0)
        chk("lid screw hole clear of the lid edge", X["wall"] / 2 - X["lid_clear_d"] / 2, ">= 0.8", X["wall"] / 2 - X["lid_clear_d"] / 2 >= 0.8)
        g = self.max_screw_gap()
        chk("largest lid-screw gap (seam backed by the cage + gasket)", g, "<= 35 (no screws over the outputs)", g <= 35)
        east = sorted((p for p in self.ports if p["wall"] == "E"), key=lambda p: -p["y"])
        gg = min(abs(p["y"] - q["y"]) - K["flange"] for p, q in zip(east, east[1:]))
        chk("smallest flange-to-flange gap (outputs 2-3, 4-5, 6-7)", gg, ">= 1.5 (fit flanges in order)", gg >= 1.5)
        lim = self.Wo / 2 - X["outer_r"]
        worst = max(abs(p["y"]) + K["flange"] / 2 for p in self.ports)
        chk("outer flanges inside the box outline", lim - worst, ">= 0", lim >= worst)
        comp_nom = Q["gasket_t"] - Q["gap"]
        comp_min = comp_nom - 0.051 - 0.03; comp_max = comp_nom + 0.051 + 0.03
        chk("gasket compression min (thin board, tolerances)", 100 * comp_min / Q["gasket_t"], "%% >= 10", comp_min / Q["gasket_t"] >= 0.10)
        chk("gasket compression max (thick board)", 100 * comp_max / Q["gasket_t"], "%% <= 50", comp_max / Q["gasket_t"] <= 0.50)
        chk("channel ceiling above the 0402 resistors", Q["ch_air"] - C.BOARD["resistor"]["H"], ">= 3", Q["ch_air"] - 0.35 >= 3)
        ph = Q["screw_pocket_h"] - THREAD["M2"]["head_k"]
        chk("cage pocket over the M2 heads", ph, ">= 0.4", ph >= 0.4)
        chk("cage metal above the channels", X["h_air"] - Q["ch_air"], ">= 1.5", X["h_air"] - Q["ch_air"] >= 1.5)
        dch = min(Point(h[0], h[1]).distance(self.channels) for h in self.holes) - Q["screw_pocket_d"] / 2
        chk("M2 head pocket to nearest channel", dch, ">= 1.0 (rib left)", dch >= 1.0)
        return r

    def summary(self):
        return dict(Lo=self.Lo, Wo=self.Wo, H=self.z_top, Lc=self.Lc, Wc=self.Wc, floor=self.floor, z_pcb_top=self.z_pcb_top,
                    pin_z=self.pin_z, z_wall=self.z_wall, z_top=self.z_top, z_face=self.z_face)


# ======================= SolidCraft script writer =======================
class S:
    def __init__(self): self.c = []
    def a(self, cmd, **p): self.c.append({"command": cmd, "params": p})
    def rrect(self, z, x0, y0, x1, y1, r):
        self.a("sketch.create", plane="XY", offset=z); self.a("sketch.rectangle.rounded", p0=[x0, y0], p1=[x1, y1], radius=r); self.a("sketch.finish")
    def color(self, body, col): self.a("appearance.assign", bodies=[body], color=COL[col])


def plane_for(origin, axis):
    ax = [float(v) for v in axis]
    ref = [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]
    xd = [ref[1] * ax[2] - ref[2] * ax[1], ref[2] * ax[0] - ref[0] * ax[2], ref[0] * ax[1] - ref[1] * ax[0]]
    n = math.sqrt(sum(v * v for v in xd)); xd = [v / n for v in xd]
    yd = [ax[1] * xd[2] - ax[2] * xd[1], ax[2] * xd[0] - ax[0] * xd[2], ax[0] * xd[1] - ax[1] * xd[0]]
    return {"origin": [round(v, 6) for v in origin], "x_dir": [round(v, 9) for v in xd], "y_dir": [round(v, 9) for v in yd]}


def screw(s, name, size, length, seat, axis_out):
    """ISO 4762 (or ISO 7380 'M2.5_BH') screw; seat = point under the head, axis_out = from the hole toward the head."""
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
    """Regions -> DXF of closed polylines (planar faces, robust booleans); returns (relative path, pick points)."""
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace(); pts = []
    for r in regs:
        for ring in [r.exterior] + list(r.interiors):
            m.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(ring.coords)[:-1]], close=True)
        q = r.representative_point(); pts.append({"point": [round(q.x, 4), round(q.y, 4)]})
    os.makedirs(os.path.join(OUT, "dxf_src"), exist_ok=True)
    p = os.path.join(OUT, "dxf_src", tag + ".dxf"); d.saveas(p)
    return os.path.relpath(p, OUT).replace("\\", "/"), pts


def cut_regions(s, regs, plane, body, depth, tag, direction="negative"):
    if not regs: return
    rel, pts = dxf_regions(regs, tag)
    s.a("sketch.create", plane=plane); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    s.a("solid.extrude", distance=depth, direction=direction, profiles=pts, operation="cut", targets=[body])


def xy_plane(z): return {"origin": [0, 0, round(z, 6)], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}


# ---------------- base ----------------
def build_base(s, H):
    X, K = C.BOX, C.CONN; nm = "BASE"
    s.rrect(0, -H.Lo / 2, -H.Wo / 2, H.Lo / 2, H.Wo / 2, X["outer_r"])
    s.a("solid.extrude", distance=H.z_wall, operation="new", body_name=nm)
    s.rrect(H.z_wall, -H.Lc / 2, -H.Wc / 2, H.Lc / 2, H.Wc / 2, X["cav_r"])
    s.a("solid.extrude", distance=H.z_wall - H.floor, direction="negative", operation="cut", targets=[nm])
    s.a("sketch.create", plane="XY", offset=H.z_wall)                       # corner reliefs for the square board corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.a("sketch.circle.center", center=[sx * H.Lc / 2, sy * H.Wc / 2], diameter=X["corner_relief_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=H.z_wall - H.floor, direction="negative", profiles="all", operation="cut", targets=[nm])
    for p in H.ports:
        ux = p["u"][0]
        s.a("solid.hole", position=[p["face"][0], p["face"][1], H.pin_z], direction=[-ux, 0, 0], diameter=K["bore_d"], depth=X["wall"] + 0.3)
        for hx, hy, hz in p["holes"]:
            s.a("solid.hole", position=[hx, hy, hz], direction=[-ux, 0, 0], thread=K["screw"], depth=K["screw_tap_depth"])
    for x, y in H.lid_screws:
        s.a("solid.hole", position=[x, y, H.z_wall], direction=[0, 0, -1], thread=X["lid_screw"], depth=X["lid_tap_depth"])
    for x, y, _w in H.holes:
        s.a("solid.hole", position=[x, y, H.floor], direction=[0, 0, -1], thread=X["pcb_screw"], depth=X["pcb_tap_depth"])
    for x, y in H.mount:
        s.a("solid.hole", position=[x, y, 0], direction=[0, 0, 1], thread=X["mount_screw"], depth=X["mount_tap_depth"])
    s.a("sketch.create", plane="XY", offset=H.z_wall + 0.1)                 # dowel holes (press fit, d2 - 0.01)
    for x, y in H.dowels: s.a("sketch.circle.center", center=[x, y], diameter=X["dowel_d"] - 0.01, connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=X["dowel_depth"] + 0.1, direction="negative", profiles="all", operation="cut", targets=[nm])
    ex, ey, ez = H.earth
    s.a("solid.hole", position=[ex, ey, ez], direction=[1, 0, 0], thread=X["earth"], depth=X["earth_depth"])
    # west-wall labels, read from outside (looking east): reading direction = -y
    pl = {"origin": [-H.Lo / 2 - 0.1, 0.0, 0.0], "x_dir": [0.0, -1.0, 0.0], "y_dir": [0.0, 0.0, 1.0]}
    h = 3.0; regs = []
    w = A.text_width("RF IN", h, C.FONT_BOLD)
    regs += A.text_regions("RF IN", h, C.FONT_BOLD, -(K["flange"] / 2 + 2.0 + w / 2), H.pin_z - h / 2)   # north of the IN flange (u = -y)
    wg = A.text_width("GND", h, C.FONT_BOLD)
    regs += A.text_regions("GND", h, C.FONT_BOLD, -ey - (3.5 + wg / 2), ez - h / 2)
    cut_regions(s, regs, pl, nm, X["engrave_depth"] + 0.1, "base_west_labels", direction="negative")
    s.a("solid.chamfer", edges=[[0.0, -H.Wo / 2, 0.0], [0.0, H.Wo / 2, 0.0], [-H.Lo / 2, 40.0, 0.0], [H.Lo / 2, 62.0, 0.0]], distance=X["chamfer_base"])
    s.color(nm, "al"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm


# ---------------- lid + cage ----------------
def lid_artwork(H):
    """Lid-top engraving: logo, title, P/N, date, band; port labels at the edges. Returns (regions, layout rows)."""
    T = C.TEXT; X = C.BOX
    regs_logo, lh = A.logo_regions(T["logo_w"])
    rows = [(T["title"], 4.2, C.FONT_BOLD), ("P/N " + T["pn"] + "    " + T["band"], 3.2, C.FONT),
            ("DATE " + T["date"] + "    S/N ________", 3.2, C.FONT)]
    gaps = [6.0, 3.2, 2.6]
    total = lh + sum(h for _, h, _ in rows) + sum(gaps)
    y = total / 2
    from shapely.affinity import translate
    logo = [translate(r, 0, y - lh / 2) for r in regs_logo]; y -= lh
    regs = list(logo); layout = [("BEL logo", T["logo_w"], round(lh, 2), round(y + lh / 2, 2))]
    for (t, h, f), g in zip(rows, gaps):
        y -= g + h
        width_max = H.Lo - 2 * (X["wall"] + 14.0)
        hh = min(h, h * width_max / A.text_width(t, h, f))
        regs += A.text_regions(t, hh, f, 0.0, y); layout.append((t, round(A.text_width(t, hh, f), 1), hh, round(y, 2)))
    for p in H.ports:                                           # port labels near the walls
        hp = 3.0
        if p["wall"] == "E": regs += A.text_regions(p["label"], hp, C.FONT_BOLD, H.Lo / 2 - X["wall"] - 2.5, p["y"] - hp / 2, "right")
        else: regs += A.text_regions("IN", hp, C.FONT_BOLD, -H.Lo / 2 + X["wall"] + 2.5, p["y"] - hp / 2, "left")
    return regs, layout


def build_lid(s, H, dz=0.0):
    X, Q = C.BOX, C.CAGE; nm = "LID"
    z0, zt = H.z_wall + dz, H.z_top + dz
    s.rrect(z0, -H.Lo / 2, -H.Wo / 2, H.Lo / 2, H.Wo / 2, X["outer_r"])
    s.a("solid.extrude", distance=X["t_lid"], operation="new", body_name=nm)
    hb = H.z_wall - H.z_face                                     # cage block height
    fx0, fy0, fx1, fy1 = H.foot.bounds
    s.rrect(z0, fx0, fy0, fx1, fy1, X["cav_r"] - 0.1)
    s.a("solid.extrude", distance=hb, direction="negative", operation="join", targets=[nm])
    zf = H.z_face + dz
    chans = list(H.channels.geoms) if hasattr(H.channels, "geoms") else [H.channels]
    cut_regions(s, chans, xy_plane(zf - 0.1), nm, Q["ch_air"] - Q["gap"] + 0.1, "lid_channels", direction="positive")
    pockets = [Point(x, y).buffer(Q["screw_pocket_d"] / 2, 48) for x, y, _w in H.holes]
    cut_regions(s, pockets, xy_plane(zf - 0.1), nm, Q["screw_pocket_h"] - Q["gap"] + 0.1, "lid_screw_pockets", direction="positive")
    s.a("sketch.create", plane="XY", offset=zt + 0.1)
    for x, y in H.lid_screws: s.a("sketch.circle.center", center=[x, y], diameter=X["lid_clear_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=X["t_lid"] + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    (x0_, y0_), (x1_, y1_) = H.dowels
    dd = math.dist(H.dowels[0], H.dowels[1]); ux_, uy_ = (x0_ - x1_) / dd, (y0_ - y1_) / dd
    hole = Point(x0_, y0_).buffer(X["dowel_d"] / 2 + 0.006, 48)                    # H7 hole
    slot = LineString([(x1_ - ux_ * 0.5, y1_ - uy_ * 0.5), (x1_ + ux_ * 0.5, y1_ + uy_ * 0.5)]).buffer(X["dowel_d"] / 2 + 0.006, 24)
    cut_regions(s, [hole, slot], xy_plane(zt + 0.1), nm, X["t_lid"] + 0.3, "lid_dowels")
    s.a("sketch.create", plane="XY", offset=zt + 0.1)                               # jacking holes (M3 tap drill, thread per drawing)
    for x, y in H.jacks: s.a("sketch.circle.center", center=[x, y], diameter=THREAD[X["jack"]]["tap"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=X["t_lid"] + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    regs, _ = lid_artwork(H)
    cut_regions(s, regs, xy_plane(zt + 0.1), nm, X["engrave_depth"] + 0.1, "lid_engraving")
    s.a("solid.chamfer", edges=[[0.0, -H.Wo / 2, zt], [0.0, H.Wo / 2, zt], [-H.Lo / 2, 40.0, zt], [H.Lo / 2, 62.0, zt]], distance=X["chamfer_lid"])
    s.color(nm, "lid"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm


def gasket_regions(H):
    face = H.foot.difference(H.channels)
    for x, y, _w in H.holes: face = face.difference(Point(x, y).buffer(C.CAGE["screw_pocket_d"] / 2, 48))
    return list(face.geoms) if hasattr(face, "geoms") else [face]


def build_gasket(s, H, dz=0.0):
    nm = "GASKET"; Q = C.CAGE
    rel, pts = dxf_regions(gasket_regions(H), "gasket")
    s.a("sketch.create", plane=xy_plane(H.z_pcb_top + dz)); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    s.a("solid.extrude", distance=Q["gap"], profiles=pts, operation="new", body_name=nm)       # shown compressed
    s.color(nm, "gasket")


# ---------------- PCB (v3) ----------------
def build_pcb(s, H, dz=0.0):
    B = H.B; nm = "PCB_V3"; z = H.floor + dz; t = C.BOARD["t"]; cu = C.BOARD["cu"]
    s.rrect(z, -B["L"] / 2, -B["W"] / 2, B["L"] / 2, B["W"] / 2, 0.05)
    s.a("solid.extrude", distance=t - cu, operation="new", body_name=nm)
    s.a("sketch.create", plane="XY", offset=z + t + 0.1)
    for x, y, _w in H.holes: s.a("sketch.circle.center", center=[x, y], diameter=C.PCB_HOLES["drill"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=t + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    s.color(nm, "pcb")
    sig = list(B["sig"].geoms) if hasattr(B["sig"], "geoms") else [B["sig"]]
    rel, pts = dxf_regions([g.simplify(0.005) for g in sig], "pcb_signal")
    s.a("sketch.create", plane=xy_plane(z + t - cu)); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    s.a("solid.extrude", distance=cu, profiles=pts, operation="new", body_name="PCB_SIGNAL_CU"); s.color("PCB_SIGNAL_CU", "cu")
    R = C.BOARD["resistor"]
    s.a("sketch.create", plane="XY", offset=z + t)
    for x, y, rot in B["res"]:
        a, b = (R["L"] / 2, R["W"] / 2) if rot == 0.0 else (R["W"] / 2, R["L"] / 2)
        s.a("sketch.rectangle.two_point", p0=[round(x - a, 4), round(y - b, 4)], p1=[round(x + a, 4), round(y + b, 4)])
    s.a("sketch.finish")
    s.a("solid.extrude", distance=R["H"], profiles="all", operation="new", body_name="RESISTORS_0402"); s.color("RESISTORS_0402", "res")
    return nm


def add_connectors(s, H, out=0.0, sout=0.0):
    K = C.CONN
    for k, p in enumerate(H.ports):
        nm = "J%d_%s" % (k + 1, p["label"])
        s.a("file.insert_step", path=os.path.relpath(C.CONN_STEP, OUT).replace("\\", "/"), name=nm)
        s.a("body.rename", body="PartBody", name=nm)
        if p["rot"]: s.a("solid.move", bodies=[nm], axis=[0, 0, 1], angle=p["rot"])
        ux = p["u"][0]
        s.a("solid.move", bodies=[nm], translate=[round(p["face"][0] + K["x_contact"] * ux + ux * out, 6), round(p["face"][1], 6), round(H.pin_z, 6)])
        s.color(nm, "conn")
        for j, (hx, hy, hz) in enumerate(p["holes"]):
            screw(s, "SC%d%d_M2.5" % (k + 1, j + 1), "M2.5", K["screw_len"], [hx + ux * (K["flange_t"] + out + sout), hy, hz], [ux, 0, 0])


def dowels(s, H):
    X = C.BOX
    for i, (x, y) in enumerate(H.dowels):
        nm = "DOWEL%d_D2x8" % (i + 1)
        s.a("sketch.create", plane="XY", offset=H.z_wall - X["dowel_depth"]); s.a("sketch.circle.center", center=[x, y], diameter=X["dowel_d"]); s.a("sketch.finish")
        s.a("solid.extrude", distance=X["dowel_len"], operation="new", body_name=nm); s.color(nm, "dowel")


def assembly(H, explode=False):
    X = C.BOX; s = S()
    d = dict(lid=40.0, lid_s=30.0, gas=24.0, pcb=12.0, pcb_s=8.0, conn=18.0, conn_s=10.0) if explode else dict.fromkeys(("lid", "lid_s", "gas", "pcb", "pcb_s", "conn", "conn_s"), 0.0)
    build_base(s, H); build_pcb(s, H, d["pcb"])
    for i, (x, y, _w) in enumerate(H.holes):
        screw(s, "SP%d_M2" % (i + 1), "M2", X["pcb_screw_len"], [x, y, H.z_pcb_top + d["pcb"] + d["pcb_s"]], [0, 0, 1])
    dowels(s, H)
    build_gasket(s, H, d["gas"])
    build_lid(s, H, d["lid"])
    for i, (x, y) in enumerate(H.lid_screws):
        screw(s, "SL%d_M2.5" % (i + 1), "M2.5_BH", X["lid_screw_len"], [x, y, H.z_top + d["lid"] + d["lid_s"]], [0, 0, 1])
    add_connectors(s, H, d["conn"], d["conn_s"])
    return s


def box_only(H):
    X = C.BOX; s = S(); build_base(s, H); dowels(s, H); build_lid(s, H)
    for i, (x, y) in enumerate(H.lid_screws):
        screw(s, "SL%d_M2.5" % (i + 1), "M2.5_BH", X["lid_screw_len"], [x, y, H.z_top], [0, 0, 1])
    return s


def measure(step_name):
    """Mass / volume of an exported STEP (SolidCraft eval), {} if the file is missing."""
    p = os.path.join(OUT, step_name)
    if not os.path.exists(p): return {}
    exe = shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"
    jo = os.path.join(OUT, "_measure.json")
    r = subprocess.run([exe, "eval", step_name, "--json-out", os.path.basename(jo)], capture_output=True, text=True, cwd=OUT)
    if r.returncode or not os.path.exists(jo): return {}
    with open(jo, encoding="utf-8") as fh: res = json.load(fh)
    os.remove(jo)
    return res


def run(script, name, outs, snaps=()):
    os.makedirs(OUT, exist_ok=True)
    js = os.path.join(OUT, name + ".solidcraft.json")
    with open(js, "w") as fh: json.dump({"commands": script.c}, fh, indent=0)
    exe = shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"
    jo = os.path.join(OUT, "_" + name + ".result.json")
    r = subprocess.run([exe, "run", os.path.basename(js), "--json-out", os.path.basename(jo)] + sum((["--out", o] for o in outs), []), capture_output=True, text=True, cwd=OUT)
    if r.returncode:
        print(r.stdout[-4000:], r.stderr[-4000:]); raise SystemExit("solidcraft failed: " + name)
    with open(jo, encoding="utf-8") as fh: res = json.load(fh)
    os.remove(jo)
    for view, png, extra in snaps:
        rr = subprocess.run([exe, "snapshot", os.path.basename(js), "--out", png, "--width", "1800", "--height", "1300", "--view", view, "--no-grid"] + list(extra),
                            capture_output=True, text=True, cwd=OUT)
        if rr.returncode: print("snapshot failed", png, rr.stderr[-500:])
    return res
