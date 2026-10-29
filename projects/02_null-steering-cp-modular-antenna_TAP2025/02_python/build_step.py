"""STEP (AP242) models of the null-steering / CP modular antenna, built with SolidCraft (solidcraft-cli) from the
same geometry as the DXFs (nsgeom.py, dimensions from Younus et al., IEEE TAP 73(5), May 2025).

    python build_step.py            -> ../06_step/*.step, *.solidcraft.json, STEP_report.txt

Every copper layer is written to a DXF, inserted into a SolidCraft sketch and extruded 17 um; the laminates and the
via barrels are extruded the same way. Each body is then measured by SolidCraft and compared with the volume
computed from the 2-D geometry (area x thickness) and with the paper's board size: STEP_report.txt lists every
body, its error and PASS/FAIL. A mismatch above 0.05 % fails the build.

Stack-ups (board frame: x across, y along the board, z up through the laminate, mm):
  phase shifter / units (Fig. 2(d))  BOT Cu z = -0.017..0   RO4003C 0.508 + RO4450F 0.1  MID Cu centred on z = 0.608
                                      RO4003C 0.508          TOP Cu z = 1.116..1.133
  standalone dipole (Sec. III-B)      BOT Cu z = -0.017..0   RO4003C 0.508               TOP Cu z = 0.508..0.525
The MID copper overlaps the laminate solids by 8.5 um each side and the via barrels run through them: give copper
priority when importing into an EM solver (or subtract it from the dielectric).

Systems (world frame, beam = +z): each unit board stands with board y along +z and its TOP side facing -y, at the
positions of 01_dxf/assembly_3D_placement.csv (1-D: 2 units side by side; 2-D: 2 x 2; CP: four wings at
45/135/225/315 deg, inner edge on the z axis).
The *.solidcraft.json scripts are kept as a record; they read DXFs from 06_step/dxf_src, which this builder writes
and deletes again, so rebuild through this script."""
import os, json, math, shutil, subprocess, zipfile
import ezdxf
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
import nsgeom as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "06_step")); TMP = os.path.join(OUT, "dxf_src")
CU = 0.017
TOL = 5e-4                                   # allowed relative volume error per body
COL = {"cu": "#c8823a", "ro4003": "#e9e1c6", "prepreg": "#d8cfa8", "via": "#b87333"}
STACK3 = dict(BOT=(-CU, CU), MID=(G.Z_MID - CU / 2, CU), TOP=(G.Z_TOP, CU),
              diel=[("lam_lower", 0.0, G.Z_MID, "prepreg"), ("lam_upper", G.Z_MID, G.H_CORE, "ro4003")],
              vspan={"TOP-MID": (G.Z_MID, G.Z_TOP), "MID-BOT": (0.0, G.Z_MID), "TOP-MID-BOT": (0.0, G.Z_TOP)})
STACK1 = dict(BOT=(-CU, CU), TOP=(G.H_CORE, CU), diel=[("lam", 0.0, G.H_CORE, "ro4003")],
              vspan={"TOP-BOT": (0.0, G.H_CORE), "TOP-MID-BOT": (0.0, G.H_CORE)})


def polys(g):
    if g.is_empty: return []
    return [p for p in (g.geoms if isinstance(g, MultiPolygon) else [g]) if p.area > 1e-9]


def write_dxf(name, ps=(), circles=()):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace()
    for p in ps:
        for ring in [p.exterior, *p.interiors]:
            m.add_lwpolyline(list(ring.coords)[:-1], close=True)
    for x, y, r in circles:
        m.add_circle((x, y), r)
    path = os.path.join(TMP, name + ".dxf"); d.saveas(path); return path


class Script:
    """A SolidCraft command script plus the bodies it makes and the volume each should have."""
    def __init__(self):
        self.c, self.expect = [], []          # expect: (body name, volume mm3, z0, z1)

    def body(self, name, dxf_path, z0, t, points, color, vol, n_bodies):
        self.c += [{"command": "sketch.create", "params": {"plane": "XY", "offset": z0, "name": name + "_sk"}},
                   {"command": "sketch.insert_dxf", "params": {"path": os.path.relpath(dxf_path, OUT)}},
                   {"command": "sketch.finish", "params": {}},
                   {"command": "solid.extrude", "params": {"distance": t, "profiles": [{"point": list(p)} for p in points],
                                                            "operation": "new", "body_name": name}}]
        names = [name] + ["%s (%d)" % (name, k) for k in range(2, n_bodies + 1)]
        self.c.append({"command": "appearance.assign", "params": {"bodies": names, "color": COL[color]}})
        self.expect.append((name, vol, z0, z0 + t, n_bodies))
        return names

    def move(self, names, axis=None, angle=None, translate=None):
        p = {"bodies": names}
        if axis: p.update(axis=axis, angle="%.10g deg" % angle)
        if translate: p["translate"] = list(translate)
        self.c.append({"command": "solid.move", "params": p})

    def save(self, path):
        with open(path, "w") as fh: json.dump({"commands": self.c}, fh, indent=0)


def add_board(S, b, tag, stack):
    """All bodies of one board in its own frame. Returns the body names."""
    names = []
    for lay in ("BOT", "MID", "TOP"):
        if lay not in b.L or lay not in stack: continue
        ps = polys(unary_union(b.L[lay]))
        if not ps: continue
        z0, t = stack[lay]
        pts = [p.representative_point().coords[0] for p in ps]
        names += S.body(tag + lay + "_Cu", write_dxf(tag + lay, ps), z0, t, pts, "cu", sum(p.area for p in ps) * t, len(ps))
    outline = polys(unary_union(b.L["OUTLINE"]))
    for nm, z0, t, col in stack["diel"]:
        pts = [p.representative_point().coords[0] for p in outline]
        names += S.body(tag + nm, write_dxf(tag + nm, outline), z0, t, pts, col, sum(p.area for p in outline) * t, len(outline))
    spans = {}
    for x, y, d, lay in b.vias:
        spans.setdefault(stack["vspan"].get(lay, stack["vspan"]["TOP-MID-BOT"]), []).append((x, y, d / 2))
    for k, ((z0, z1), cs) in enumerate(sorted(spans.items())):
        vol = sum(math.pi * r * r for _, _, r in cs) * (z1 - z0)
        names += S.body("%svias_%d" % (tag, k), write_dxf("%svias_%d" % (tag, k), circles=cs), z0, z1 - z0,
                        [(x, y) for x, y, _ in cs], "via", vol, len(cs))
    return names


def run(S, tag):
    js = os.path.join(OUT, tag + ".solidcraft.json"); S.save(js); step = os.path.join(OUT, tag + ".step")
    exe = shutil.which("solidcraft-cli")
    if not exe: raise SystemExit("solidcraft-cli not on PATH (see docs/CONVENTIONS.md)")
    r = subprocess.run([exe, "run", js, "--out", step], capture_output=True, text=True, cwd=OUT)
    if r.returncode: print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit("solidcraft failed on " + tag)
    return json.loads(r.stdout[r.stdout.index("{"):]), step


def check(tag, S, res, lines, size):
    """Compare every body with its expected volume and the model's extents with the paper's sizes."""
    import re
    got = {}
    for bd in res["bodies"]:
        k = re.sub(r" \(\d+\)$", "", bd["name"]); g = got.setdefault(k, [0, 0.0])
        g[0] += 1; g[1] += bd["volume_mm3"]
    ok = True
    lines += ["== %s: %d bodies, total volume %.4f mm3" % (tag, res["body_count"], res["total"]["volume_mm3"]),
              "   %-28s %7s %14s %14s %9s" % ("body", "count", "expected mm3", "SolidCraft mm3", "error")]
    for name, vol, z0, z1, n in S.expect:
        g = got.get(name, [0, 0.0]); err = (g[1] - vol) / vol if vol else 0.0
        good = g[0] == n and abs(err) < TOL; ok &= good
        lines.append("   %-28s %3d/%-3d %14.5f %14.5f %+8.4f%%  %s" % (name, g[0], n, vol, g[1], 100 * err, "PASS" if good else "FAIL"))
    lo = [min(b["bbox"]["min"][i] for b in res["bodies"]) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in res["bodies"]) for i in range(3)]
    for i, ax in enumerate("xyz"):
        if size[i] is None:
            lines.append("   %s extent %9.4f .. %9.4f" % (ax, lo[i], hi[i])); continue
        a, c = size[i]; good = abs(lo[i] - a) < 1e-3 and abs(hi[i] - c) < 1e-3; ok &= good
        lines.append("   %s extent %9.4f .. %9.4f   expected %9.4f .. %9.4f   %s" % (ax, lo[i], hi[i], a, c, "PASS" if good else "FAIL"))
    lines.append("   %s" % ("ALL PASS" if ok else "CHECK FAILED")); lines.append("")
    return ok


BOARDS = [  # name, board, stack, expected extents (x, y, z) from the paper (W x L, stack-up)
    ("DIPOLE_standalone", lambda: G.board_dipole(), STACK1,
     [(-G.DP["W"] / 2, G.DP["W"] / 2), (0, G.DP["Lant"]), (-CU, G.H_CORE + CU)]),
    ("PS_standalone", lambda: G.board_phase_shifter(slot="paper", bias="L"), STACK3,
     [(-G.PS["W"] / 2, G.PS["W"] / 2), (0, G.PS["L"]), (-CU, G.Z_TOP + CU)]),
    ("UNIT_A_mid-paper", lambda: G.board_unit("A", slot="paper", mid="paper", unit_no=1), STACK3,
     [(-G.PS["W"] / 2, G.PS["W"] / 2), (0, G.PS["L"] + G.DP["Lant"]), (-CU, G.Z_TOP + CU)]),
    ("UNIT_B_mid-paper", lambda: G.board_unit("B", slot="paper", mid="paper", unit_no=2), STACK3,
     [(-G.PS["W"] / 2, G.PS["W"] / 2), (0, G.PS["L"] + G.DP["Lant"]), (-CU, G.Z_TOP + CU)]),
    ("UNIT_A_mid-extended", lambda: G.board_unit("A", slot="paper", mid="extended", unit_no=1), STACK3,
     [(-G.PS["W"] / 2, G.PS["W"] / 2), (0, G.PS["L"] + G.DP["Lant"]), (-CU, G.Z_TOP + CU)]),
    ("UNIT_B_mid-extended", lambda: G.board_unit("B", slot="paper", mid="extended", unit_no=2), STACK3,
     [(-G.PS["W"] / 2, G.PS["W"] / 2), (0, G.PS["L"] + G.DP["Lant"]), (-CU, G.Z_TOP + CU)]),
]


def placements():
    import csv
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "01_dxf", "assembly_3D_placement.csv"))))
    out = {}
    for r in rows:
        out.setdefault(r["system"], []).append((int(r["unit"]), r["type"], float(r["x_world_mm"]), float(r["y_world_mm"]),
                                                float(r["z_bottom_mm"]), float(r["azimuth_deg"])))
    return out


def add_system(S, units):
    """Stand each unit board up (board y -> world z, TOP side facing -y), centre its thickness on the board plane,
    turn CP wings to their azimuth and move it to its place."""
    for u, typ, x, y, z, az in units:
        b = G.board_unit(typ, slot="paper", mid="paper", unit_no=u)
        names = add_board(S, b, "U%d_%s_" % (u, typ), STACK3)
        S.move(names, translate=(0, 0, -G.Z_TOP / 2))          # board mid-plane on z = 0 before standing up
        S.move(names, axis=[1, 0, 0], angle=90)
        if az:   # CP wing: board x along the radial line, inner edge (x = -W/2) on the axis
            S.move(names, translate=(G.PS["W"] / 2, 0, 0))
            S.move(names, axis=[0, 0, 1], angle=az)
            S.move(names, translate=(0, 0, z))
        else:
            S.move(names, translate=(x, y, z))


def main():
    os.makedirs(TMP, exist_ok=True); lines = []; ok = True
    for old in os.listdir(OUT):                               # the cadquery per-layer folders are replaced
        p = os.path.join(OUT, old)
        if os.path.isdir(p) and old != "dxf_src": shutil.rmtree(p)
        elif old.endswith("__assembly.step"): os.remove(p)
    for name, make, stack, size in BOARDS:
        S = Script(); add_board(S, make(), "", stack)
        res, _ = run(S, name); ok &= check(name, S, res, lines, size); print(lines[-2], name)
    W, L, h = G.PS["W"], G.PS["L"] + G.DP["Lant"], G.Z_TOP / 2 + CU     # h: half the board thickness, copper included
    r = (W + h) * math.cos(math.radians(45))                           # CP wings at 45 deg: corner of the outer edge
    sys_size = {"SYS_1D": [(-W, W), (-h, h), (0, L)],
                "SYS_2D": [(-W, W), (-W / 2 - h, W / 2 + h), (0, L)],
                "SYS_CP": [(-r, r), (-r, r), (0, L)], "SYS_CP_cophased": [(-r, r), (-r, r), (0, L)]}
    for sysn, units in placements().items():
        S = Script(); add_system(S, units)
        res, _ = run(S, sysn); ok &= check(sysn, S, res, lines, sys_size[sysn]); print(lines[-2], sysn)
    shutil.rmtree(TMP)
    for f in os.listdir(OUT):                                  # keep the repository small: zip files over 20 MB
        p = os.path.join(OUT, f)
        if f.endswith(".step") and os.path.getsize(p) > 20e6:
            with zipfile.ZipFile(p + ".zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z: z.write(p, f)
            os.remove(p)
    hdr = ["STEP build report (SolidCraft %s) - every body measured by SolidCraft vs. area x thickness from nsgeom.py" % _version(),
           "Tolerance %.3f %% per body; extents checked against the paper's board sizes (W = 25, L = 36 + 24 mm) and stack-up." % (100 * TOL), ""]
    with open(os.path.join(OUT, "STEP_report.txt"), "w") as fh: fh.write("\n".join(hdr + lines) + "\n")
    if not ok: raise SystemExit("STEP check failed: see 06_step/STEP_report.txt")


def _version():
    r = subprocess.run(["solidcraft-cli", "--version"], capture_output=True, text=True)
    return r.stdout.strip().split()[-1] if r.returncode == 0 else "?"


if __name__ == "__main__":
    main()
