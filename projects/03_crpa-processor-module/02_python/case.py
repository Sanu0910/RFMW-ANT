"""GNSS_JAM_PRO v1.0 case (PocketSDR v2.3 case design): geometry from config.py and the SolidCraft scripts for the
tube, the two end panels and the assembly. Frame: see config.py (X along the tube from the ANT end, Z up = component side)."""
import os, json, math, shutil, subprocess
import ezdxf
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.affinity import scale
import config as C
import text_art as A

OUT = os.path.join(C.ROOT, "06_step")
COL = {"al": "#2b2d31", "panel": "#3a3d42", "pcb": "#2f6b3a", "shield": "#c9ccd0", "ic": "#2a2a2a",
       "screw": "#b8bcc2", "nut": "#a9adb3", "sma": "#d8c37a"}
SUPPLY = dict(screw_spare=2, nut_spare=2)       # vendor supplies 4 + spares per case (user, 2026-11-06)


# ======================= geometry =======================
class Case:
    def __init__(self):
        P, T, K = C.PCB, C.TUBE, C.PANEL
        self.L = T["L"]
        self.X = lambda kx: kx - P["kx0"] + (T["L"] - P["L"]) / 2       # KiCad x -> X
        self.Y = lambda ky: -(ky - P["ky_c"])                           # KiCad y -> Y
        self.z_top = P["z_mid"] + P["t"] / 2
        self.z_bot = P["z_mid"] - P["t"] / 2
        self.hw, self.hh = T["W"] / 2, T["H"] / 2
        self.iw, self.ih = self.hw - T["wall"], self.hh - T["wall"]
        self.holes = [(x, s * T["hole_y"]) for x in (T["hole_x"], T["L"] - T["hole_x"]) for s in (1, -1)]
        self.leds = [(n, f, self.X(kx), self.Y(ky)) for n, f, kx, ky in P["leds_k"]]   # LED windows, top wall
        self.usb_front = self.X(P["usb_k"][0]) + 3.675                  # USB4105 shell front (KiCad model)
        self.ends = {"ant": dict(sx=-1.0, xf=0.0), "usb": dict(sx=1.0, xf=self.L)}

    @staticmethod
    def stadium(cy, cz, w, h):
        r = h / 2
        return box(cy - w / 2 + r, cz - r, cy + w / 2 - r, cz + r).buffer(r, resolution=24)

    @staticmethod
    def rrect(y0, z0, y1, z1, r):
        return box(y0 + r, z0 + r, y1 - r, z1 - r).buffer(r, resolution=24)

    def tube_section(self):
        T = C.TUBE
        return self.rrect(-self.hw, -self.hh, self.hw, self.hh, T["r_out"]).difference(
            self.rrect(-self.iw, -self.ih, self.iw, self.ih, T["r_in"]))

    # ---- panel features in the panel's YZ plane ----
    def flange(self):
        return box(-self.hw, -self.hh, self.hw, self.hh)

    def spigot(self, end):
        K = C.PANEL
        g = box(-K["sp_w"] / 2, K["sp_z"][0], K["sp_w"] / 2, K["sp_z"][1]).difference(box(-20, K["slot"][0], 20, K["slot"][1]))
        if end == "usb":
            r = K["usb_relief"]; g = g.difference(box(-r["w"] / 2, r["z"][0], r["w"] / 2, r["z"][1]))
        return g

    def through(self, end):
        K = C.PANEL
        if end == "ant":
            a = K["ant_sq"] / 2; return box(-a, C.PCB["sma_axis_z"] - a, a, C.PCB["sma_axis_z"] + a)
        return self.stadium(0.0, K["usb_cz"], K["usb_w"], K["usb_h"])

    def lug_profile(self):
        """Lug side profile in the (x from the flange face, y) plane: from the spigot face to an R3 end round the hole."""
        K = C.PANEL; r = K["lug_r"]; w = K["lug_w"]
        return box(K["sp_t"] - 0.5, -w / 2, K["lug_x"], w / 2).union(Point(K["lug_x"], 0).buffer(r, resolution=48))

    def hexagon(self, cx, cy, af):
        R = af / math.sqrt(3)            # corner radius; corners along X (the tube axis)
        return Polygon([(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(0, 360, 60)])

    def checks(self):
        T, K, P, S = C.TUBE, C.PANEL, C.PCB, C.SCREW
        r = []
        def chk(n, v, rule, ok): r.append((n, v, rule, bool(ok)))
        cy, cz = self.iw - K["sp_w"] / 2, min(self.ih - K["sp_z"][1], self.ih + K["sp_z"][0])
        chk("Spigot in the tube, Y / Z (nominal tube inside 22 x 12)", "%.2f / %.2f" % (cy, cz), ">= 0.05 (drawing: spigot 0/-0.1)", min(cy, cz) >= 0.05 - 1e-9)
        tol = 0.15
        play = (K["slot"][1] - K["slot"][0] - P["t"]) / 2
        chk("PCB in the 1.7 slot, play each side", "%.2f" % play, ">= 0.03", play >= 0.03)
        chk("Lug hole = PCB hole (X from the board end)", "%.2f / %.2f" % (K["lug_x"], P["holes_k"][0][0] - P["kx0"]), "|d| <= 0.1",
            abs(K["lug_x"] - (P["holes_k"][0][0] - P["kx0"])) <= 0.1)
        tip = -self.hh + S["L"]; nut_top = K["thin_z"][0] + C.NUT["m"]
        chk("M2 x %g tip past the nut (nut on the PCB side of its trap)" % S["L"], "%.2f" % (tip - nut_top), ">= 0.5", tip - nut_top >= 0.5)
        chk("Screw tip above the upper lug (into the board space)", "%.2f" % (tip - K["thin_z"][1]), "<= 1.5", tip - K["thin_z"][1] <= 1.5)
        a = K["ant_sq"] / 2
        chk("SMA body (6.35) in the 6.6 cut-out", "%.3f / side" % (a - 3.175), "> 0", a - 3.175 > 0)
        usb_lo, usb_hi = self.z_top + 0.05, self.z_top + 3.31
        cut_lo, cut_hi = K["usb_cz"] - K["usb_h"] / 2, K["usb_cz"] + K["usb_h"] / 2
        chk("USB-C shell (KiCad model) in the slot, Z", "%.2f / %.2f" % (usb_lo - cut_lo, cut_hi - usb_hi), "source design",
            True)
        ceil = self.ih - tol - (self.z_top + P["shield_h"])
        chk("Shield can to the tube ceiling (worst case)", "%.2f" % ceil, ">= 1.0", ceil >= 1.0)
        lg = unary_union(A.logo_regions(C.LOGO_PNG, T["logo_w"], self.L / 2, T["logo_y"]))
        gap = min(Point(x, y).distance(lg) for _n, _f, x, y in self.leds) - T["led_d"] / 2
        chk("LED window holes clear of the logo engraving", "%.2f" % gap, ">= 0.8", gap >= 0.8)
        return r


# ======================= SolidCraft script writer =======================
class S:
    def __init__(self): self.c = []
    def a(self, cmd, **p): self.c.append({"command": cmd, "params": p})
    def color(self, body, col): self.a("appearance.assign", bodies=[body], color=COL[col])


def plane(origin, xd, yd):
    return {"origin": [round(v, 6) for v in origin], "x_dir": xd, "y_dir": yd}


def xy_plane(z, down=False):
    return plane([0, 0, z], [1, 0, 0], [0, -1 if down else 1, 0])


def dxf_regions(regs, tag):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace(); pts = []
    for r in regs:
        for q in (r.geoms if hasattr(r, "geoms") else [r]):
            for ring in [q.exterior] + list(q.interiors):
                m.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(ring.coords)[:-1]], close=True)
            p = q.representative_point(); pts.append({"point": [round(p.x, 4), round(p.y, 4)]})
    os.makedirs(os.path.join(OUT, "dxf_src"), exist_ok=True)
    p = os.path.join(OUT, "dxf_src", tag + ".dxf"); d.saveas(p)
    return os.path.relpath(p, OUT).replace("\\", "/"), pts


def extrude_regions(s, regs, pl, depth, tag, op, body, direction=None):
    rel, pts = dxf_regions(regs, tag)
    s.a("sketch.create", plane=pl); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    p = dict(distance=depth, profiles=pts, operation=op)
    if direction: p["direction"] = direction
    if op == "new": p["body_name"] = body
    else: p["targets"] = [body]
    s.a("solid.extrude", **p)


def build_tube(s, H):
    T = C.TUBE; nm = "TUBE"; pn = C.PARTS["tube"]
    extrude_regions(s, [H.tube_section()], plane([0, 0, 0], [0, 1, 0], [0, 0, 1]), H.L, pn + "_section", "new", nm)
    for x, y in H.holes:
        s.a("solid.hole", position=[x, y, -H.hh], direction=[0, 0, 1], diameter=T["hole_d"], depth=T["wall"] + 0.3)
    for _n, _f, x, y in H.leds:   # LED windows through the top wall, on the LED centres
        s.a("solid.hole", position=[x, y, H.hh], direction=[0, 0, -1], diameter=T["led_d"], depth=T["wall"] + 0.3)
    # top face (Z+), read with the ANT end on the left: logo, product name, date
    regs = A.logo_regions(C.LOGO_PNG, T["logo_w"], H.L / 2, T["logo_y"])
    regs += A.text_regions(C.TEXT["product"], T["name_h"], C.FONT_BOLD, H.L / 2, T["name_y"])
    regs += A.text_regions(C.TEXT["date"], T["date_h"], C.FONT_BOLD, H.L / 2, T["date_y"])
    extrude_regions(s, regs, xy_plane(H.hh + 0.1), T["engrave"] + 0.1, pn + "_top_mark", "cut", nm, "negative")
    txt = A.text_regions("%s REV %s" % (pn, C.TEXT["rev"]), 1.6, C.FONT_BOLD, H.L / 2, -0.8)
    extrude_regions(s, txt, xy_plane(-H.hh - 0.1, down=True), T["engrave"] + 0.1, pn + "_pn", "cut", nm, "negative")
    s.color(nm, "al"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm


def build_panel(s, H, end):
    """Flange outside the tube end, spigot + lugs inside. Sketch planes face outward (u = sx * ... see yz())."""
    K = C.PANEL; e = H.ends[end]; sx, xf = e["sx"], e["xf"]; pn = C.PARTS[end]; nm = "PANEL_" + end.upper()
    xo = xf + sx * K["t"]
    yz = lambda x: plane([x, 0, 0], [0, 1, 0], [0, 0, 1])                 # normal +X, u = Y, v = Z
    ddir = "positive" if sx < 0 else "negative"                            # toward +X for the ANT end, -X for the USB end
    # flange (from the outside face inward), spigot (from the tube end face inward)
    extrude_regions(s, [H.flange()], yz(xo), K["t"], pn + "_flange", "new", nm, ddir)
    extrude_regions(s, [H.spigot(end)], yz(xf), K["sp_t"], pn + "_spigot", "join", nm, ddir)
    # lugs: profile in the XY plane (x from the flange face), extruded over the lug thickness in Z
    for zr, tag in ((K["thick_z"], "thick"), (K["thin_z"], "thin")):
        regs = []
        for sy in (1, -1):
            g = H.lug_profile()
            regs.append(Polygon([(xf - sx * x, sy * K["lug_y"] + y) for x, y in g.exterior.coords]).buffer(0))
        extrude_regions(s, regs, xy_plane(zr[0]), zr[1] - zr[0], pn + "_lug_" + tag, "join", nm)
    if end == "ant":                                                       # nut back-stop blocks
        b = K["ant_block"]; regs = []
        for sy in (1, -1):
            regs.append(box(min(xf - sx * b["x"][0], xf - sx * b["x"][1]), sy * K["lug_y"] - b["y_half"],
                            max(xf - sx * b["x"][0], xf - sx * b["x"][1]), sy * K["lug_y"] + b["y_half"]))
        extrude_regions(s, regs, xy_plane(b["z"][0]), b["z"][1] - b["z"][0], pn + "_blocks", "join", nm)
    # cut-outs from the outside face through flange + spigot
    extrude_regions(s, [H.through(end)], yz(xo + sx * 0.1), K["t"] + K["sp_t"] + 0.3, pn + "_thru", "cut", nm,
                    "positive" if sx < 0 else "negative")
    if end == "ant":
        a = K["ant_cb"] / 2
        extrude_regions(s, [box(-a, -a, a, a)], yz(xo + sx * 0.1), K["ant_cb_d"] + 0.1, pn + "_recess", "cut", nm, "positive" if sx < 0 else "negative")
    # lug holes: D2.2 through the lower lug (from below), hex nut trap through the upper lug
    xh = xf - sx * K["lug_x"]
    for sy in (1, -1):
        s.a("solid.hole", position=[xh, sy * K["lug_y"], K["thick_z"][0]], direction=[0, 0, 1], diameter=K["hole_d"],
            depth=K["thick_z"][1] - K["thick_z"][0] + 0.05, targets=[nm])
    hexes = [H.hexagon(xh, sy * K["lug_y"], K["nut_af"]) for sy in (1, -1)]
    extrude_regions(s, hexes, xy_plane(K["thin_z"][1] + 0.1), K["thin_z"][1] - K["thin_z"][0] + 0.2, pn + "_nut", "cut", nm, "negative")
    s.color(nm, "panel"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm


def build_pcb(s, H, dz=0.0):
    P = C.PCB; x0 = H.X(P["kx0"]); zb = H.z_bot + dz; zt = H.z_top + dz
    g = box(x0, -P["W"] / 2, x0 + P["L"], P["W"] / 2).difference(
        unary_union([Point(H.X(x), H.Y(y)).buffer(P["hole_d"] / 2, resolution=24) for x, y in P["holes_k"]]))
    extrude_regions(s, [g], xy_plane(zb), P["t"], "PSDR23_pcb", "new", "PCB"); s.color("PCB", "pcb")
    for nm, kxy, a, h, col in (("SHIELD", P["shield_k"], P["shield"], P["shield_h"], "shield"), ("U3", P["u3_k"], P["u3"], P["u3_h"], "ic")):
        x, y = H.X(kxy[0]), H.Y(kxy[1])
        s.a("sketch.create", plane=xy_plane(zt)); s.a("sketch.rectangle.two_point", p0=[x - a / 2, y - a / 2], p1=[x + a / 2, y + a / 2]); s.a("sketch.finish")
        s.a("solid.extrude", distance=h, operation="new", body_name=nm); s.color(nm, col)
    # J4 edge SMA (reference shape from the SMA-ANG footprint): neck 5.2 sq, body D6.35 to 7.9 beyond the board edge
    zc = P["sma_axis_z"] + dz; yzm = lambda x: plane([x, 0, 0], [0, -1, 0], [0, 0, 1])     # normal -X
    s.a("sketch.create", plane=yzm(x0 + 0.6)); s.a("sketch.rectangle.two_point", p0=[-2.6, zc - 2.6], p1=[2.6, zc + 2.6]); s.a("sketch.finish")
    s.a("solid.extrude", distance=2.0, operation="new", body_name="J4_SMA")
    s.a("sketch.create", plane=yzm(x0 - 1.4)); s.a("sketch.circle.center", center=[0, zc], diameter=6.35); s.a("sketch.finish")
    s.a("solid.extrude", distance=7.9 - 1.4, operation="new", body_name="J4_SMA_body")
    s.a("solid.combine", target="J4_SMA", tools=["J4_SMA_body"], operation="join")
    s.a("solid.hole", position=[x0 - 7.9, 0, zc], direction=[1, 0, 0], diameter=4.6, depth=5.0)
    s.color("J4_SMA", "sma")
    # J2 = KiCad USB4105 model: footprint rotation 90 deg about Z, origin on the board top at the footprint position
    a = math.radians(P["usb_rot"]); c, sn = round(math.cos(a), 9), round(math.sin(a), 9)
    s.a("file.insert_step", path=C.USB_STEP.replace("\\", "/"), name="J2_USB",
        matrix=[[c, -sn, 0, round(H.X(P["usb_k"][0]), 4)], [sn, c, 0, round(H.Y(P["usb_k"][1]), 4)], [0, 0, 1, round(zt, 4)]])


def screw(s, name, x, y, z0):
    """ISO 7045 pan head M2: head under z0 (outside the tube bottom), shank up."""
    S_ = C.SCREW
    s.a("sketch.create", plane=xy_plane(z0, down=True)); s.a("sketch.circle.center", center=[x, -y], diameter=S_["head_d"]); s.a("sketch.finish")
    s.a("solid.extrude", distance=S_["head_k"], operation="new", body_name=name)
    s.a("sketch.create", plane=xy_plane(z0)); s.a("sketch.circle.center", center=[x, y], diameter=S_["d"]); s.a("sketch.finish")
    s.a("solid.extrude", distance=S_["L"], operation="new", body_name=name + "_shank")
    s.a("solid.combine", target=name, tools=[name + "_shank"], operation="join")
    for a, b in ((1.1, 0.25), (0.25, 1.1)):                  # cross recess
        s.a("sketch.create", plane=xy_plane(z0 - S_["head_k"], down=True))
        s.a("sketch.rectangle.two_point", p0=[x - a, -y - b], p1=[x + a, -y + b]); s.a("sketch.finish")
        s.a("solid.extrude", distance=0.8, direction="negative", operation="cut", targets=[name])
    s.color(name, "screw")


def nut(s, name, H, x, y, z0):
    N = C.NUT; R = N["af"] / math.sqrt(3)
    s.a("sketch.create", plane=xy_plane(z0))
    s.a("sketch.polygon.inscribed", center=[x, y], radius=round(R, 4), sides=6); s.a("sketch.finish")
    s.a("solid.extrude", distance=N["m"], operation="new", body_name=name)
    s.a("solid.hole", position=[x, y, z0 + N["m"]], direction=[0, 0, -1], diameter=1.6, targets=[name])
    s.color(name, "nut")


def assembly(H, explode=0.0):
    s = S(); e = explode; K = C.PANEL
    build_tube(s, H)
    for end in ("ant", "usb"):
        nm = build_panel(s, H, end)
        if e: s.a("solid.move", bodies=[nm], translate=[H.ends[end]["sx"] * e * 1.8, 0, 0])
    build_pcb(s, H, e * 1.8)
    for i, (x, y) in enumerate(H.holes):
        sx = -1.0 if x < H.L / 2 else 1.0; dx = sx * e * 1.8
        screw(s, "SCR%d_M2x10" % (i + 1), x, y, -H.hh - e)
        nut(s, "NUT%d_M2" % (i + 1), H, x + dx, y, K["thin_z"][0] + 0.2 + e * 1.8 * 0)
        if e: s.a("solid.move", bodies=["NUT%d_M2" % (i + 1)], translate=[0, 0, e * 3.2])
    return s


# ======================= runner =======================
def _exe():
    return shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"


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
        rr = subprocess.run([_exe(), "snapshot", os.path.basename(js), "--out", png, "--width", "1800", "--height", "1300",
                             "--view", view, "--no-grid", "--no-axes"] + list(extra), capture_output=True, text=True, cwd=OUT)
        if rr.returncode: print("snapshot failed", png, rr.stderr[-500:])
    return res
