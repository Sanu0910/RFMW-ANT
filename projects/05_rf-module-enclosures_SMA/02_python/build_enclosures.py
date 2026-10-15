"""Build every enclosure with SolidCraft (solidcraft-cli) from encl_config.py.
    python build_enclosures.py            # all three
    python build_enclosures.py A_PD_MSL   # one
Per enclosure, in ../01_step/<key>/:
  <PN>_BASE.step, <PN>_LID.step         machined parts (what goes to the workshop)
  <PN>_ASSY.step                        closed assembly: base, lid, PCB dummy, H+S SMA connectors, all screws
  <PN>_ASSY_EXPLODED.step               the same, exploded along the assembly directions
  *_iso.png / *_exploded.png / *_lid_top.png   renders;  *.solidcraft.json  the command scripts
Then ../04_pcb_interface/<key>_PCB_interface.dxf and ../05_docs/<key>_design_report.md (checks, resonances, BOM)."""
import os, sys, json, math, subprocess, shutil, re, csv
import ezdxf
from encl_config import CONN, BOX, BOARDS
from encl_geom import Encl, THREAD

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
COL = {"al": "#b9c0c7", "lid": "#a7b0b9", "pcb": "#2f6b3a", "cu": "#c8823a", "screw": "#3a3d42", "conn": "#d8c37a"}

class S:
    def __init__(self): self.c = []
    def a(self, cmd, **p): self.c.append({"command": cmd, "params": p})
    def rrect(self, z, x0, y0, x1, y1, r, name=None):
        self.a("sketch.create", plane="XY", offset=z, **({"name": name} if name else {}))
        self.a("sketch.rectangle.rounded", p0=[x0, y0], p1=[x1, y1], radius=r)
        self.a("sketch.finish")
    def color(self, body, col): self.a("appearance.assign", bodies=[body], color=COL[col])

def plane_for(origin, axis):
    """Sketch plane with normal = axis (unit, x/y/z aligned or general)."""
    ax = [float(v) for v in axis]
    ref = [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]
    xd = [ref[1] * ax[2] - ref[2] * ax[1], ref[2] * ax[0] - ref[0] * ax[2], ref[0] * ax[1] - ref[1] * ax[0]]
    n = math.sqrt(sum(v * v for v in xd)); xd = [v / n for v in xd]
    yd = [ax[1] * xd[2] - ax[2] * xd[1], ax[2] * xd[0] - ax[0] * xd[2], ax[0] * xd[1] - ax[1] * xd[0]]
    return {"origin": [round(v, 6) for v in origin], "x_dir": [round(v, 9) for v in xd], "y_dir": [round(v, 9) for v in yd]}

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

def text_w(txt, h, font):
    """Width in mm of txt at cap height h (glyph metrics from the font file)."""
    from PIL import ImageFont
    f = ImageFont.truetype(font, 200)
    cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    return (f.getbbox(txt)[2] - f.getbbox(txt)[0]) / cap * h

def fit_lines(txt, h_max, h_min, width, font):
    """One line at the largest height <= h_max that fits, else two lines split at the best space."""
    h = min(h_max, width / text_w(txt, 1.0, font) * 0.98)
    if h >= h_min: return [txt], round(h, 2)
    words = txt.split(); best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        w = max(text_w(a, 1.0, font), text_w(b, 1.0, font))
        if best is None or w < best[0]: best = (w, [a, b])
    return best[1], round(min(h_max, width / best[0] * 0.98), 2)

def build_base(s, e, tag="BASE"):
    B = BOX; nm = tag
    s.rrect(0, -e.Lo / 2, -e.Wo / 2, e.Lo / 2, e.Wo / 2, B["outer_r"])
    s.a("solid.extrude", distance=e.z_wall, operation="new", body_name=nm)
    s.rrect(e.z_wall, -e.Lc / 2, -e.Wc / 2, e.Lc / 2, e.Wc / 2, B["cav_r"])
    s.a("solid.extrude", distance=e.z_wall - e.floor, direction="negative", operation="cut", targets=[nm])
    for p in e.ports:
        ux, uy = p["u"]
        s.a("solid.hole", position=[p["face"][0], p["face"][1], e.pin_z], direction=[-ux, -uy, 0], diameter=CONN["bore_d"], depth=B["wall"] + 0.3)
        for hx, hy, hz in p["holes"]:
            s.a("solid.hole", position=[hx, hy, hz], direction=[-ux, -uy, 0], thread=CONN["screw"], depth=4.0)
    for x, y in e.lid_screws:
        s.a("solid.hole", position=[x, y, e.z_wall], direction=[0, 0, -1], thread=B["lid_screw"], depth=B["lid_tap_depth"])
    for x, y in e.pcb_screws:
        s.a("solid.hole", position=[x, y, e.floor], direction=[0, 0, -1], thread=B["pcb_screw"], depth=B["pcb_tap_depth"])
    for x, y in e.mount:
        s.a("solid.hole", position=[x, y, 0], direction=[0, 0, 1], thread=B["mount_screw"], depth=B["mount_tap_depth"])
    engrave_ports(s, e, nm)
    s.color(nm, "al"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm

def build_lid(s, e, dz=0.0, tag="LID"):
    B = BOX; nm = tag; z0 = e.z_wall + dz; zt = e.z_top + dz
    s.rrect(z0, -e.Lo / 2, -e.Wo / 2, e.Lo / 2, e.Wo / 2, B["outer_r"])
    s.a("solid.extrude", distance=B["t_lid"], operation="new", body_name=nm)
    o = B["lip_clr"]; w = B["lip_w"]
    s.a("sketch.create", plane="XY", offset=z0)
    s.a("sketch.rectangle.rounded", p0=[-e.Lc / 2 + o, -e.Wc / 2 + o], p1=[e.Lc / 2 - o, e.Wc / 2 - o], radius=B["cav_r"] - o)
    s.a("sketch.rectangle.rounded", p0=[-e.Lc / 2 + o + w, -e.Wc / 2 + o + w], p1=[e.Lc / 2 - o - w, e.Wc / 2 - o - w], radius=0.3)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=B["lip_h"], direction="negative", profiles=[{"point": [0.0, e.Wc / 2 - o - w / 2]}], operation="join", targets=[nm])
    ia = B["absorber_inset"]
    s.rrect(z0, -e.Lc / 2 + o + w + ia, -e.Wc / 2 + o + w + ia, e.Lc / 2 - o - w - ia, e.Wc / 2 - o - w - ia, 0.5)
    s.a("solid.extrude", distance=B["absorber_depth"], operation="cut", targets=[nm])
    s.a("sketch.create", plane="XY", offset=zt + 0.1)                                   # clearance holes
    for x, y in e.lid_screws: s.a("sketch.circle.center", center=[x, y], diameter=B["lid_clear_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=B["t_lid"] + 0.2, direction="negative", profiles="all", operation="cut", targets=[nm])
    engrave(s, e, nm, zt)
    s.color(nm, "lid"); s.a("material.assign", bodies=[nm], material="Aluminum")
    return nm

def glyph_regions(rows):
    """rows: (text, cap height, font, x, y, align) -> list of shapely polygons (even-odd filled glyphs)."""
    from shapely.geometry import Polygon
    from functools import reduce
    import engraving_dxf as ED
    regs = []
    for txt, h, font, x, y, al in rows:
        loops = [Polygon(p).buffer(0) for p in ED.glyph_polys(txt, h, font, x, y, al) if len(p) >= 3]
        loops = [l for l in loops if not l.is_empty]
        if not loops: continue
        g = reduce(lambda u, v: u.symmetric_difference(v), loops)
        regs += list(g.geoms) if hasattr(g, "geoms") else [g]
    return [r for r in regs if r.area > 1e-4]

def cut_regions(s, regs, plane, body, depth, tag, to_local=None):
    """Write the regions as a DXF (polylines: planar faces only -> robust booleans), insert, cut by picked points."""
    if not regs: return
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace()
    pts = []
    for r in regs:
        for ring in [r.exterior] + list(r.interiors):
            m.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(ring.coords)[:-1]], close=True)
        q = r.representative_point(); pts.append({"point": [round(q.x, 4), round(q.y, 4)]})
    os.makedirs(os.path.join(OUTDIR, "dxf_src"), exist_ok=True)
    p = os.path.join(OUTDIR, "dxf_src", tag + ".dxf"); d.saveas(p)
    s.a("sketch.create", plane=plane)
    s.a("sketch.insert_dxf", path=os.path.relpath(p, OUTDIR))
    s.a("sketch.finish")
    s.a("solid.extrude", distance=depth + 0.1, direction="negative", profiles=pts, operation="cut", targets=[body])

def engrave(s, e, body, zt):
    """Lid top: logo (outlined SVG if supplied, else bold text), title, P/N + rev, S/N + band - one centred block."""
    import engraving_dxf as ED
    B = BOX
    logo = os.path.join(ROOT, B["logo_svg"])
    rows = ED.lid_layout(e)
    if os.path.exists(logo):
        lt, lh, lf, ly = rows[0]
        vb = re.search(r'viewBox="([-\d.\s]+)"', open(logo).read())
        w = float(vb.group(1).split()[2]) if vb else 100.0; sc = B["logo_w"] / w
        s.a("sketch.create", plane="XY", offset=zt + 0.1)
        s.a("sketch.insert_svg", path=os.path.relpath(logo, OUTDIR), scale=sc, at=[-B["logo_w"] / 2, ly])
        s.a("sketch.finish")
        s.a("solid.extrude", distance=B["engrave_depth"] + 0.1, direction="negative", profiles="all", operation="cut", targets=[body])
        rows = rows[1:]
    regs = glyph_regions([(t, h, f, 0.0, y, "center") for t, h, f, y in rows])
    cut_regions(s, regs, {"origin": [0, 0, zt + 0.1], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, body, B["engrave_depth"], body + "_lid_engraving")

def engrave_ports(s, e, body):
    """Port label on the outside wall beside each connector flange (reads from outside)."""
    B = BOX; h = 2.5
    for p in e.ports:
        ux, uy = p["u"]; fx, fy = p["face"]
        xd = [-uy, ux, 0.0]                                  # (-u) x z : reading direction seen from outside
        pl = {"origin": [fx + ux * 0.1, fy + uy * 0.1, 0.0], "x_dir": xd, "y_dir": [0.0, 0.0, 1.0]}
        sign = xd[0] * p["t"][0] + xd[1] * p["t"][1]
        half_wall = (e.Wo if p["wall"] in "WE" else e.Lo) / 2
        w = text_w(p["label"], h, B["font_bold"]); sh = CONN["flange"] / 2 + 1.2 + w / 2
        others = [q["off"] for q in e.ports if q["wall"] == p["wall"] and q is not p]
        pick = None
        for a_ in (p["off"] + sh, p["off"] - sh) if p["off"] >= 0 else (p["off"] - sh, p["off"] + sh):
            if abs(a_) + w / 2 > half_wall - B["outer_r"] - 1.0: continue
            if any(abs(a_ - o) < CONN["flange"] / 2 + w / 2 + 0.8 for o in others): continue
            pick = a_; break
        if pick is None: continue
        regs = glyph_regions([(p["label"], h, B["font_bold"], pick * sign, e.pin_z - h / 2, "center")])
        cut_regions(s, regs, pl, body, B["engrave_depth"], body + "_lbl_" + p["label"].split()[0])

def build_pcb(s, e, dz=0.0):
    b = e.b; z = e.floor + dz; nm = "PCB_" + b["pn"]
    s.rrect(z, -b["L"] / 2, -b["W"] / 2, b["L"] / 2, b["W"] / 2, 1.2)
    s.a("solid.extrude", distance=b["t"], operation="new", body_name=nm)
    s.a("sketch.create", plane="XY", offset=z + b["t"] + 0.1)        # PCB holes: sketch cut on the PCB only
    for x, y in e.pcb_screws: s.a("sketch.circle.center", center=[x, y], diameter=BOX["pcb_clear_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=b["t"] + 0.1, direction="negative", profiles="all", operation="cut", targets=[nm])
    s.color(nm, "pcb")
    # 50-ohm launch stubs (illustrative: real copper comes from the layout)
    for k, p in enumerate(e.ports):
        ex, ey = p["edge"]; ux, uy = p["u"]; L = 7.0; w = p["w"]
        x0, y0 = ex + ux * BOX["clr"], ey + uy * BOX["clr"]; x1, y1 = x0 - ux * L, y0 - uy * L
        tx, ty = p["t"]
        xs = [x0 + tx * w / 2, x0 - tx * w / 2, x1 - tx * w / 2, x1 + tx * w / 2]; ys = [y0 + ty * w / 2, y0 - ty * w / 2, y1 - ty * w / 2, y1 + ty * w / 2]
        s.a("sketch.create", plane="XY", offset=z + b["t"])
        s.a("sketch.rectangle.two_point", p0=[round(min(xs), 4), round(min(ys), 4)], p1=[round(max(xs), 4), round(max(ys), 4)])
        s.a("sketch.finish")
        s.a("solid.extrude", distance=b["cu"], operation="new", body_name="TRACE_%s" % p["label"].split()[0])
        s.color("TRACE_%s" % p["label"].split()[0], "cu")
    return nm

def connector_translation(e, p, out=0.0):
    """Translation that puts the rotated STEP (contact face at x_contact * u_out after rotation... ) on the wall."""
    ux, uy = p["u"]; fx, fy = p["face"]; xc = CONN["x_contact"]
    # STEP frame: mating side -x. After rotating so that -x points along u, the contact face lies at (-xc)*(-u)... = xc*(-1)*u?
    # A point at (xc, 0, 0) maps to xc * (-u) * (-1) = -xc * u? : rotation maps -x_hat -> u, so x_hat -> -u, point xc*x_hat -> -xc*u.
    cx, cy = -xc * ux, -xc * uy                    # contact face centre after rotation (xc < 0 -> outward side)
    return [round(fx - cx + ux * out, 6), round(fy - cy + uy * out, 6), round(e.pin_z, 6)]

def add_connectors(s, e, out=0.0, sout=0.0):
    names = []
    for k, p in enumerate(e.ports):
        nm = "J%d_%s" % (k + 1, p["label"].split()[0])
        s.a("file.insert_step", path=os.path.relpath(os.path.join(ROOT, CONN["step"]), OUTDIR), name=nm)
        s.a("body.rename", body="PartBody", name=nm)
        if p["rot"]: s.a("solid.move", bodies=[nm], axis=[0, 0, 1], angle=p["rot"])
        s.a("solid.move", bodies=[nm], translate=connector_translation(e, p, out))
        s.color(nm, "conn"); names.append(nm)
        ux, uy = p["u"]
        for j, (hx, hy, hz) in enumerate(p["holes"]):
            seat = [hx + ux * (CONN["flange_t"] + out + sout), hy + uy * (CONN["flange_t"] + out + sout), hz]
            screw(s, "S%d%d_%s" % (k + 1, j + 1, CONN["screw"]), CONN["screw"], CONN["screw_len"], seat, [ux, uy, 0])
    return names

def assembly(e, explode=False):
    s = S(); B = BOX
    d = dict(lid=28.0, lid_s=46.0, pcb=12.0, pcb_s=20.0, conn=14.0, conn_s=12.0) if explode else dict(lid=0, lid_s=0, pcb=0, pcb_s=0, conn=0, conn_s=0)
    build_base(s, e)
    build_pcb(s, e, d["pcb"])
    for i, (x, y) in enumerate(e.pcb_screws):
        screw(s, "SP%d_%s" % (i + 1, B["pcb_screw"]), B["pcb_screw"], B["pcb_screw_len"], [x, y, e.floor + e.b["t"] + d["pcb"] + d["pcb_s"]], [0, 0, 1])
    build_lid(s, e, d["lid"])
    for i, (x, y) in enumerate(e.lid_screws):
        screw(s, "SL%d_%s" % (i + 1, B["lid_screw"]), "M2.5_BH", B["lid_screw_len"], [x, y, e.z_top + d["lid"] + d["lid_s"]], [0, 0, 1])
    add_connectors(s, e, d["conn"], d["conn_s"])
    return s

def run(script, js, outs, snap=None):
    with open(js, "w") as fh: json.dump({"commands": script.c}, fh, indent=0)
    exe = shutil.which("solidcraft-cli")
    if not exe: print("solidcraft-cli not found; wrote", js); return None
    cmd = [exe, "run", js] + sum((["--out", o] for o in outs), [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=OUTDIR)
    if r.returncode: print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit("solidcraft failed: " + js)
    res = json.loads(r.stdout[r.stdout.index("{"):])
    for view, png in (snap or []):
        subprocess.run([exe, "snapshot", js, "--out", png, "--width", "1600", "--height", "1100", "--view", view], capture_output=True, text=True, cwd=OUTDIR)
    return res

def pcb_interface_dxf(e, path):
    """Board outline, screw holes, port centre lines and keep-outs for the PCB designer."""
    b = e.b; d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace()
    for n, c in (("PCB_OUTLINE", 7), ("NPTH_M2_CLEAR", 1), ("GND_PAD_KEEP_CU", 3), ("PORT_CL", 5), ("CAVITY", 8), ("NOTES", 2)): d.layers.add(n, color=c)
    L, W, r = b["L"] / 2, b["W"] / 2, 1.2
    m.add_lwpolyline([(-L + r, -W), (L - r, -W), (L, -W + r), (L, W - r), (L - r, W), (-L + r, W), (-L, W - r), (-L, -W + r)], close=True, dxfattribs={"layer": "PCB_OUTLINE"})
    m.add_lwpolyline([(-e.Lc / 2, -e.Wc / 2), (e.Lc / 2, -e.Wc / 2), (e.Lc / 2, e.Wc / 2), (-e.Lc / 2, e.Wc / 2)], close=True, dxfattribs={"layer": "CAVITY"})
    for x, y in e.pcb_screws:
        m.add_circle((x, y), BOX["pcb_clear_d"] / 2, dxfattribs={"layer": "NPTH_M2_CLEAR"})
        m.add_circle((x, y), 2.3, dxfattribs={"layer": "GND_PAD_KEEP_CU"})
    for p in e.ports:
        ex, ey = p["edge"]; ux, uy = p["u"]
        m.add_line((ex + ux * BOX["clr"], ey + uy * BOX["clr"]), (ex - ux * 8, ey - uy * 8), dxfattribs={"layer": "PORT_CL"})
        t = m.add_text("%s  pin %.2f x %.2f mm lies on the trace" % (p["label"], CONN["pin_d"], CONN["pin_proj"] - BOX["clr"]), height=1.0, dxfattribs={"layer": "NOTES"})
        t.set_placement((ex - ux * 9, ey - uy * 9 + 1.5))
    for k, s_ in enumerate(["Board %.2f x %.2f mm, corners R1.2 (pocket R1.0)" % (b["L"], b["W"]), "M2 clearance d%.1f, solid GND pad d4.6 top+bottom, stitched vias" % BOX["pcb_clear_d"],
                             "Board edge to cavity wall 0.10 mm; launch: GCPW taper recommended (pin d1.26)", "Bottom copper = solid ground in contact with the housing floor"]):
        t = m.add_text(s_, height=1.2, dxfattribs={"layer": "NOTES"}); t.set_placement((-L, -W - 4 - 2 * k))
    d.saveas(path)

def report(e, res_assy, path, files):
    B = BOX; b = e.b
    lines = ["# %s - %s (%s)" % (e.key, b["title"], b["pn"]), ""]
    lines += ["| Item | Value |", "|---|---|",
              "| Board (ASSUMED until the layout is supplied) | %.2f x %.2f x %.3f mm, %s |" % (b["L"], b["W"], b["t"], b["substrate"]),
              "| Band | %.1f-%.1f GHz |" % b["band"],
              "| Outside | %.2f x %.2f x %.2f mm (base %.2f + lid %.1f) |" % (e.Lo, e.Wo, e.z_top, e.z_wall, B["t_lid"]),
              "| Cavity | %.2f x %.2f mm, depth %.2f mm from the wall top, floor %.2f mm |" % (e.Lc, e.Wc, e.z_wall - e.floor, e.floor),
              "| Air above PCB | %.1f mm (lid lip %.1f mm, absorber recess %.1f mm) |" % (B["h_air"], B["lip_h"], B["absorber_depth"]),
              "| Connector axis | %.3f mm above the base bottom (= PCB top + pin radius) |" % e.pin_z,
              "| Ports | %s |" % "; ".join("%s on %s wall at %+.1f mm" % (p["label"], p["wall"], p["off"]) for p in e.ports),
              "| Lid screws | %d x %s x %.0f ISO 7380 button head on d2.9 holes; max gap %.2f mm (pitch target %.2f) |" % (len(e.lid_screws), B["lid_screw"], B["lid_screw_len"], e.max_screw_gap(), e.pitch()),
              "| PCB screws | %d x %s x %.0f ISO 4762 (4 corners + 2 per launch) |" % (len(e.pcb_screws), B["pcb_screw"], B["pcb_screw_len"]),
              "| Connector screws | %d x %s x %.0f ISO 4762 |" % (4 * len(e.ports), CONN["screw"], CONN["screw_len"]),
              "| Mounting | 4 x %s tapped %.0f deep in the bottom |" % (B["mount_screw"], B["mount_tap_depth"]), ""]
    lines += ["## Design checks", "", "| Check | Value (mm) | Rule | Result |", "|---|---|---|---|"]
    for n, v, lim, ok, u in e.checks():
        lines.append("| %s | %.2f | %s | %s |" % (n, v, lim, "OK" if ok else "**WARN**"))
    rs, ee = e.resonances(6)
    lines += ["", "## Cavity resonances (air cavity %.1f x %.1f mm; PCB-loaded estimate eps_eff %.3f)" % (e.Lc, e.Wc, ee), "",
              "| Mode | Empty (GHz) | With PCB (GHz) | In band? |", "|---|---|---|---|"]
    for f, m, n, fl in rs:
        inb = b["band"][0] <= fl <= b["band"][1] * 1.1
        lines.append("| TE%d%d0-type | %.2f | %.2f | %s |" % (m, n, f, fl, "**YES** - fit absorber" if inb else "no"))
    if res_assy:
        lines += ["", "## Bodies in the assembly (SolidCraft)", "", "| Part | Bodies | Volume (mm3) |", "|---|---|---|"]
        agg = {}
        for bd in res_assy["bodies"]:
            k = re.sub(r"\d+_M[\d.]+$|\s\(\d+\)$", "", bd["name"]); a = agg.setdefault(k, [0, 0.0]); a[0] += 1; a[1] += bd["volume_mm3"]
        for k, (n, v) in agg.items(): lines.append("| %s | %d | %.1f |" % (k, n, v))
        al = [bd for bd in res_assy["bodies"] if bd["name"] in ("BASE", "LID")]
        lines.append("")
        lines.append("Machined mass (Al 2.70 g/cm3): base %.1f g, lid %.1f g." % tuple(bd["volume_mm3"] * 2.70e-3 for bd in al))
    lines += ["", "## Files", ""] + ["- `%s`" % f for f in files]
    open(path, "w").write("\n".join(lines) + "\n")

def bom_rows(e):
    B = BOX; b = e.b
    return [[b["pn"] + "-01", "Base, machined", B["material"], 1, B["finish"]],
            [b["pn"] + "-02", "Lid with RF lip, engraved", B["material"], 1, B["finish"]],
            ["23030310", CONN["part"], "brass / BeCu, PTFE", len(e.ports), "solder pin to the trace"],
            ["ISO 4762 %s x %g" % (CONN["screw"], CONN["screw_len"]), "connector flange screw", "A2 stainless", 4 * len(e.ports), "thread-lock low strength"],
            ["ISO 7380 %s x %g" % (B["lid_screw"], B["lid_screw_len"]), "lid screw (button head)", "A2 stainless", len(e.lid_screws), "torque 0.35 N m"],
            ["ISO 4762 %s x %g" % (B["pcb_screw"], B["pcb_screw_len"]), "PCB hold-down / launch ground", "A2 stainless", len(e.pcb_screws), "torque 0.2 N m"],
            ["absorber sheet", "RF absorber 1 mm, e.g. Laird Eccosorb MCS / ARC WAVE-X (cut %.1f x %.1f)" % (e.Lc - 2 * (B["lip_clr"] + B["lip_w"] + B["absorber_inset"]), e.Wc - 2 * (B["lip_clr"] + B["lip_w"] + B["absorber_inset"])), "silicone/ferrite", 1, "optional, bond in the lid recess"],
            [b["pn"] + "-PCB", "RF board (customer)", b["substrate"], 1, "%.2f x %.2f, holes per PCB interface DXF" % (b["L"], b["W"])]]

def build(key):
    global OUTDIR
    b = BOARDS[key]; e = Encl(key, b); pn = b["pn"]
    OUTDIR = os.path.join(ROOT, "01_step", key); os.makedirs(OUTDIR, exist_ok=True)
    s = S(); build_base(s, e); run(s, os.path.join(OUTDIR, pn + "_BASE.solidcraft.json"), [pn + "_BASE.step"])
    s = S(); build_lid(s, e); run(s, os.path.join(OUTDIR, pn + "_LID.solidcraft.json"), [pn + "_LID.step"], [("top", pn + "_lid_top.png")])
    ra = run(assembly(e), os.path.join(OUTDIR, pn + "_ASSY.solidcraft.json"), [pn + "_ASSY.step"], [("iso", pn + "_iso.png")])
    run(assembly(e, True), os.path.join(OUTDIR, pn + "_ASSY_EXPLODED.solidcraft.json"), [pn + "_ASSY_EXPLODED.step"], [("iso", pn + "_exploded.png")])
    os.makedirs(os.path.join(ROOT, "04_pcb_interface"), exist_ok=True)
    pcb_interface_dxf(e, os.path.join(ROOT, "04_pcb_interface", key + "_PCB_interface.dxf"))
    with open(os.path.join(OUTDIR, pn + "_BOM.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["part number", "description", "material", "qty", "note"]); w.writerows(bom_rows(e))
    files = sorted(os.listdir(OUTDIR))
    report(e, ra, os.path.join(ROOT, "05_docs", key + "_design_report.md"), ["01_step/%s/%s" % (key, f) for f in files])
    print(key, "done:", ", ".join(f for f in files if f.endswith(".step")))
    return e, ra

if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "05_docs"), exist_ok=True)
    for k in (sys.argv[1:] or list(BOARDS)): build(k)
