"""CRL-LS-CRPA4-BC01: combined back cover for the L and S channels (one machined part), plus the test-board cover.

Frame = the KiCad STEP of the board exported with --user-origin at the outline centre: X east, Y north (top view),
board bottom (B.Cu, component side) at z = 0, top at z = +1.6. The cover lies below the board (z < 0).

  outer disc D200 (flush with the board), height H; one general pocket (component clearance) everywhere inside the
  rim, leaving
    - RF walls 1.2 mm wide on every shield-frame land of 04_fab/_shield.json (L octagons + S frames, shared walls);
      wall top 0.30 mm below the board for a form-in-place conductive gasket (Chomerics CHOFORM 5575 [ASSUMED]);
      2.6 x 1.0 mm tunnels where the RF output lines leave each cavity (frame notches)
    - rim r 97.0 .. 100 (clamps on the board edge pour), bosses D8 at the 16 L patch M3 holes
  8 SMA openings: D6.8 through + D11.5 x 5.0 counterbore from outside (mating plug nut reaches the jack thread)
  DC: D16.2 through + 4 x M2.5 taps on a 20 mm square for a flange receptacle [ASSUMED type], deep pocket over J5
  outside face: BEL logo + part number, date, channel labels (0.3 mm engraving, mirrored = readable from below)
Run with the repo .venv:  python covers.py [main] [test]
"""
import json, math, os, shutil, subprocess, sys
import ezdxf
import numpy as np
from PIL import Image
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
from shapely.affinity import scale, translate, rotate
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties, findfont
import ls_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
OUT = os.path.join(PRJ, "06_step")
FAB = os.path.join(PRJ, "04_fab")
LOGO_PNG = os.path.join(PRJ, "00_input", "BEL_logo.png")
FONT = findfont(FontProperties(family="DejaVu Sans", weight="bold"))
BCX, BCY = D.BOARD_CENTER

CV = dict(H=11.0, pocket=6.0, wall_w=1.2, gasket_gap=0.30, rim_in=97.0, boss_d=8.0, m3_clear=3.4, m3_cb_d=6.2,
          m3_cb_depth=3.4, sma_hole=6.8, sma_cb_d=11.5, sma_cb_depth=5.0, tunnel_w=2.6, tunnel_h=1.0,
          dc_hole=8.2, dc_at=(-24.0, -72.0), j5_pocket=10.0, engrave=0.3, chamfer=0.8)
CV["engrave_date"] = "05-11-2026"


def bxy(x, y):
    """KiCad board mm -> cover frame (X east, Y north, origin = outline centre)."""
    return (x - BCX, BCY - y)


class S:
    def __init__(self): self.c = []
    def a(self, cmd, **p): self.c.append({"command": cmd, "params": p})


def dxf_regions(regs, tag):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; m = d.modelspace(); pts = []
    for r in regs:
        for ring in [r.exterior] + list(r.interiors):
            m.add_lwpolyline([(round(x, 4), round(y, 4)) for x, y in list(ring.coords)[:-1]], close=True)
        q = r.representative_point(); pts.append({"point": [round(q.x, 4), round(q.y, 4)]})
    os.makedirs(os.path.join(OUT, "dxf_src"), exist_ok=True)
    p = os.path.join(OUT, "dxf_src", tag + ".dxf"); d.saveas(p)
    return os.path.relpath(p, OUT).replace("\\", "/"), pts


def xy_plane(z): return {"origin": [0, 0, round(z, 6)], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}


def cut(s, regs, z, depth, body, tag, direction="negative"):
    regs = [r for r in (regs.geoms if hasattr(regs, "geoms") else [regs]) if not r.is_empty and r.area > 1e-4] \
        if not isinstance(regs, list) else regs
    if not regs: return
    rel, pts = dxf_regions(regs, tag)
    s.a("sketch.create", plane=xy_plane(z)); s.a("sketch.insert_dxf", path=rel); s.a("sketch.finish")
    s.a("solid.extrude", distance=depth, direction=direction, profiles=pts, operation="cut", targets=[body])


def text_regions(txt, h, x, y, mirror=True):
    fp = FontProperties(fname=FONT)
    cap = TextPath((0, 0), "H", size=100, prop=fp).get_extents().height / 100.0
    tp = TextPath((0, 0), txt, size=h / cap, prop=fp)
    e = tp.get_extents()
    from functools import reduce
    loops = [Polygon([(px - e.width / 2 - e.x0, py) for px, py in poly]).buffer(0)
             for poly in tp.to_polygons(closed_only=True) if len(poly) >= 3]
    g = reduce(lambda u, v: u.symmetric_difference(v), [l for l in loops if not l.is_empty])
    if mirror: g = scale(g, -1, 1, origin=(0, 0))
    g = translate(g, x, y)
    return [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-4]


def logo_regions(width, x, y, mirror=True):
    import contourpy
    a = np.asarray(Image.open(LOGO_PNG).convert("RGB")).astype(float)
    ink = np.pad((a.min(axis=2) < 170).astype(float), 2)
    polys = []
    for pts, offs in zip(*contourpy.contour_generator(z=ink, fill_type="OuterOffset").filled(0.5, 2.0)):
        rings = [pts[offs[k]:offs[k + 1]] for k in range(len(offs) - 1)]
        if len(rings[0]) < 4: continue
        q = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if q.area > 4.0: polys.append(q)
    g = unary_union(polys)
    s_ = width / ink.shape[1]
    g = scale(g, -s_ if mirror else s_, -s_, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    g = translate(g, x - (x0 + x1) / 2, y - (y0 + y1) / 2).simplify(0.03)
    return [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-3]


def run(s, name, outs, snaps=()):
    os.makedirs(OUT, exist_ok=True)
    js = os.path.join(OUT, name + ".solidcraft.json")
    with open(js, "w") as fh: json.dump({"commands": s.c}, fh, indent=0)
    exe = shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"
    jo = os.path.join(OUT, "_" + name + ".result.json")
    r = subprocess.run([exe, "run", os.path.basename(js), "--json-out", os.path.basename(jo)] + sum((["--out", o] for o in outs), []),
                       capture_output=True, text=True, cwd=OUT)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit("solidcraft failed: " + name)
    res = json.load(open(jo, encoding="utf-8")); os.remove(jo)
    for view, png in snaps:
        rr = subprocess.run([exe, "snapshot", os.path.basename(js), "--out", png, "--width", "1600", "--height", "1300",
                             "--view", view, "--no-grid"], capture_output=True, text=True, cwd=OUT)
        if rr.returncode: print("snapshot failed", png, rr.stderr[-400:])
    return res


# ----------------------------------------------------------------------------- main board cover
def main_geometry():
    sh = json.load(open(os.path.join(FAB, "_shield.json")))
    parts = json.load(open(os.path.join(FAB, "_parts.json")))
    P = {p["ref"]: p for p in parts}
    walls = []
    for name, verts in sh["outline_board"].items():
        ring = [bxy(x, y) for x, y in verts]
        walls.append(LineString(ring + [ring[0]]).buffer(CV["wall_w"] / 2, cap_style=2, join_style=2))
    # tunnels: notch points of CH1 rotated to every channel (sequential rotation about the array centre)
    acx, acy = bxy(*D.ARRAY_CENTER)
    tunnels = []
    for key, pts in sh["notches_board_ch1"].items():
        for x, y in pts:
            X, Y = bxy(x, y)
            for k in range(4):
                a = -90 * k                                 # KiCad -90 deg (clockwise on screen) = clockwise in Y-up too
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                dx, dy = X - acx, Y - acy
                tunnels.append(Point(acx + dx * ca - dy * sa, acy + dx * sa + dy * ca).buffer(CV["tunnel_w"] / 2, cap_style=3))
    holes_m3 = []
    for k in range(4):
        ref = f"ANT{k + 1}"
        cx_, cy_ = bxy(P[ref]["x"], P[ref]["y"])
        for dx, dy in ((-29, 0), (29, 0), (0, -29), (0, 29)):
            holes_m3.append((cx_ + dx, cy_ + dy))
    smas = [bxy(P[r]["x"], P[r]["y"]) for r in P if r.startswith("J") and r != "J5"]
    j5 = bxy(P["J5"]["x"], P["J5"]["y"])
    return walls, tunnels, holes_m3, smas, j5


def build_main():
    walls, tunnels, m3, smas, j5 = main_geometry()
    H, nm = CV["H"], "BC01"
    s = S()
    s.a("sketch.create", plane=xy_plane(-H)); s.a("sketch.circle.center", center=[0, 0], diameter=2 * D.BOARD_RADIUS); s.a("sketch.finish")
    s.a("solid.extrude", distance=H - CV["gasket_gap"], operation="new", body_name=nm)          # top face at z = -gap
    keep = unary_union(walls + [Point(x, y).buffer(CV["boss_d"] / 2, 32) for x, y in m3])
    pocket = Point(0, 0).buffer(CV["rim_in"], 180).difference(keep)
    cut(s, pocket, -CV["gasket_gap"], CV["pocket"] - CV["gasket_gap"], nm, "bc01_pocket")
    cut(s, unary_union(tunnels).intersection(unary_union(walls)), -CV["gasket_gap"], CV["tunnel_h"], nm, "bc01_tunnels")
    # J5 (Micro-Fit 3.0, ~9.9 mm tall): deeper pocket, 1 mm floor left
    cut(s, box(j5[0] - 8, j5[1] - 7, j5[0] + 8, j5[1] + 7), -CV["pocket"], CV["j5_pocket"] - CV["pocket"], nm, "bc01_j5")
    # SMA openings and M3 holes (from outside)
    s.a("sketch.create", plane=xy_plane(-H))
    for x, y in smas: s.a("sketch.circle.center", center=[x, y], diameter=CV["sma_cb_d"], connect=False)
    for x, y in m3: s.a("sketch.circle.center", center=[x, y], diameter=CV["m3_cb_d"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=CV["sma_cb_depth"], direction="positive", profiles="all", operation="cut", targets=[nm])
    s.a("sketch.create", plane=xy_plane(-H))
    for x, y in smas: s.a("sketch.circle.center", center=[x, y], diameter=CV["sma_hole"], connect=False)
    for x, y in m3: s.a("sketch.circle.center", center=[x, y], diameter=CV["m3_clear"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=H + 1, direction="positive", profiles="all", operation="cut", targets=[nm])
    # DC receptacle: M8 IP67 panel receptacle, front mount, nut on the inside [ASSUMED type], harness to J5.
    # Array-centre position (-24, -72) KiCad: clear of the CH1 L wall (14 mm), the power block (9 mm), the N S chain.
    dcx, dcy = bxy(D.ARRAY_CENTER[0] + CV["dc_at"][0], D.ARRAY_CENTER[1] + CV["dc_at"][1])
    s.a("sketch.create", plane=xy_plane(-H))
    s.a("sketch.circle.center", center=[dcx, dcy], diameter=CV["dc_hole"], connect=False)
    s.a("sketch.finish")
    s.a("solid.extrude", distance=H + 1, direction="positive", profiles="all", operation="cut", targets=[nm])
    # engraving, outside face (mirrored: readable when looking at the bottom)
    regs = logo_regions(46.0, 0.0, 33.0)          # clear of the M3 counterbores at (+-16.5, 45.5)
    for txt, h, y in (("CRL-LS-CRPA4-BC01", 4.0, 21.0), ("L1 + L2/L5 + NavIC S  BACK COVER", 2.4, 15.5),
                      ("DATE " + CV["engrave_date"] + "    S/N ________", 2.6, -30.0)):
        regs += text_regions(txt, h, 0.0, y)
    regs += text_regions("+5V DC", 3.0, dcx, dcy - 9.0)
    P = {p["ref"]: p for p in json.load(open(os.path.join(FAB, "_parts.json")))}
    for ref, p in P.items():                   # channel labels next to each SMA recess, toward the centre
        if ref.startswith("J") and ref != "J5":
            x, y = bxy(p["x"], p["y"])
            r_ = math.hypot(x, y) or 1
            lab = f"CH{ref[1]} {'S' if ref.endswith('S') else 'L'}"
            off = 14.0 if ref.endswith("S") else 0.0
            if off:
                regs += text_regions(lab, 2.5, x - off * x / r_, y - off * y / r_)
    voids = unary_union([Point(x, y).buffer(CV["sma_cb_d"] / 2 + 1.0) for x, y in smas] +
                        [Point(x, y).buffer(CV["m3_cb_d"] / 2 + 1.0) for x, y in m3] + [Point(dcx, dcy).buffer(CV["dc_hole"] / 2 + 1.0)])
    bad = [r for r in regs if r.intersects(voids)]
    if bad:
        print(f"engraving: dropped {len(bad)} regions that touch a hole / recess")
    regs = [r for r in regs if not r.intersects(voids) and Point(0, 0).buffer(D.BOARD_RADIUS - 2.0).contains(r)]
    cut(s, regs, -H, CV["engrave"], nm, "bc01_engraving", direction="positive")
    s.a("appearance.assign", bodies=[nm], color="#b9c0c7")
    s.a("material.assign", bodies=[nm], material="Aluminum")
    return run(s, "CRL-LS-CRPA4-BC01", ["CRL-LS-CRPA4-BC01.step"],
               [("iso", "CRL-LS-CRPA4-BC01_inside.png"), ("bottom", "CRL-LS-CRPA4-BC01_outside.png")])


if __name__ == "__main__":
    which = set(sys.argv[1:]) or {"main"}
    if "main" in which:
        r = build_main()
        print("BC01", r.get("body_count"), r.get("total", {}))
