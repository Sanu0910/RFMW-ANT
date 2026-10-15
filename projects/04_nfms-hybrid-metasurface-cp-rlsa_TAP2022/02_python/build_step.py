"""STEP (AP242) models with SolidCraft (solidcraft-cli, https://github.com/bherbruck/solidcraft), from the same
geometry as the DXFs.   python build_step.py [psi1 psi2]     -> ../06_step
  RLSA_feed_assembly.step     Al ground plate + SMA holes, TLY-5 disc with probe pocket, slotted top Cu, probe
  HM1.step, HM2.step          one metasurface each: bonded TLY-5 stack (holes, notch) + copper M1..M4
  NFMS_system_psiA_psiB.step  everything stacked, HMs rotated to psi1 / psi2, nylon spacers
Frame and heights as in nfmsgeom.py (z = 0 on the ground-plate top).  Copper is 17 um.  M2 / M3 are inner layers:
their copper overlaps the dielectric solid (prepreg ignored, as in the paper) - give copper priority on import.
The SolidCraft command scripts (*.solidcraft.json) are kept as a record; they read DXF sources from 06_step/dxf_src,
which this builder writes and deletes again, so rebuild through this script.  STEP files over 20 MB are zipped."""
import os, sys, json, math, subprocess, shutil
import ezdxf
from shapely.geometry import Point
from shapely.affinity import rotate as srot
import cells as CL
import nfmsgeom as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "06_step")); TMP = os.path.join(OUT, "dxf_src")
CU = 0.017
COL = {"cu": "#c8823a", "tly5": "#d9cfb0", "al": "#a9b0b7", "nylon": "#f2f2ee", "brass": "#c9a84c"}

def dxf(name, loops, circles):
    """loops: list of coordinate lists (closed polylines); circles: (x, y, r)."""
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace()
    for pts in loops: m.add_lwpolyline(pts, close=True)
    for x, y, r in circles: m.add_circle((x, y), r)
    p = os.path.join(TMP, name + ".dxf"); d.saveas(p); return p

def rot_poly(p, psi): return srot(p, psi, origin=(0, 0)) if psi else p
def rot_pt(x, y, psi):
    c, s = math.cos(math.radians(psi)), math.sin(math.radians(psi)); return c * x - s * y, s * x + c * y

class Script:
    def __init__(self): self.c = []
    def body(self, name, path, z, dist, profiles, color, direction=None):
        self.c.append({"command": "sketch.create", "params": {"plane": "XY", "offset": z, "name": name + "_sk"}})
        self.c.append({"command": "sketch.insert_dxf", "params": {"path": os.path.relpath(path, OUT)}})
        self.c.append({"command": "sketch.finish", "params": {}})
        e = {"distance": dist, "profiles": profiles, "operation": "new", "body_name": name}
        if direction: e["direction"] = direction
        self.c.append({"command": "solid.extrude", "params": e})
        self.c.append({"command": "appearance.assign", "params": {"bodies": [name], "color": COL[color]}})
    def save(self, path):
        with open(path, "w") as fh: json.dump({"commands": self.c}, fh, indent=0)

def rim_holes(psi=0.0):
    return [(*rot_pt(G.H["R_holes"] * math.cos(2 * math.pi * k / G.H["n_holes"]), G.H["R_holes"] * math.sin(2 * math.pi * k / G.H["n_holes"]), psi), G.H["hole_d"] / 2)
            for k in range(G.H["n_holes"])]

def rim_point(psi=0.0):
    # a point inside the dielectric, clear of holes and notch: R 192, 7.5 deg (between holes)
    return list(rot_pt(192.0 * math.cos(math.radians(7.5)), 192.0 * math.sin(math.radians(7.5)), psi))

def add_rlsa(S, tag=""):
    R = G.R; b = G.board_rlsa(); rd = R["D_diel"] / 2
    gp = G.board_ground()
    S.body("ground_plate" + tag, dxf("ground", [], [(0, 0, rd)] + [(x, y, d / 2) for l, x, y, d, n in gp.holes]), 0.0, R["t_ground"],
           [{"point": [0.0, 120.0]}], "al", "negative")
    S.body("rlsa_tly5" + tag, dxf("rlsa_diel", [], [(0, 0, rd)] + rim_holes() + [(0, 0, R["head_d"] / 2)]), R["h_air"], R["h_diel"],
           [{"point": rim_point()}], "tly5")
    # pocket is 0.6 deep only: fill the top 1.0 mm above it back in
    S.body("rlsa_tly5_over_pocket" + tag, dxf("rlsa_pocket_cap", [], [(0, 0, R["head_d"] / 2)]), R["head_z0"] + R["head_h"], R["h_air"] + R["h_diel"] - (R["head_z0"] + R["head_h"]),
           [{"point": [0.0, 0.0]}], "tly5")
    S.body("rlsa_top_cu" + tag, dxf("rlsa_top_cu", [list(p.exterior.coords)[:-1] for p in b.L["TOP_SLOT"]], [(0, 0, b.r_cu)]), R["Wh"], CU,
           [{"point": [0.0, 0.0]}], "cu")
    S.body("probe_pin" + tag, dxf("pin", [], [(0, 0, R["probe_pin_d"] / 2)]), -R["t_ground"], R["t_ground"] + R["head_z0"], [{"point": [0.0, 0.0]}], "brass")
    S.body("probe_head" + tag, dxf("head", [], [(0, 0, R["head_d"] / 2)]), R["head_z0"], R["head_h"], [{"point": [0.0, 0.0]}], "brass")

def add_hm(S, which, z0, psi=0.0, lib=None):
    b = G.board_hm(which, lib or CL.library()); n = "HM%d" % which; t = CL.T_LAM
    out = [list(p) for p in rot_poly(b.L["OUTLINE"][0], psi).exterior.coords][:-1]
    holes = [(*rot_pt(x, y, psi), d / 2) for l, x, y, d, nn in b.holes]
    S.body(n + "_tly5_stack", dxf(n + "_diel_%g" % psi, [out], holes), z0, 3 * t, [{"point": rim_point(psi)}], "tly5")
    for k, lay in enumerate(("M1", "M2", "M3", "M4")):
        loops = [list(rot_poly(p, psi).exterior.coords)[:-1] for p in b.L[lay]]
        z = z0 + k * t
        if k == 0: z, direc = z0, "negative"            # bottom copper below the stack
        elif k == 3: direc = None                          # top copper above the stack
        else: z, direc = z - CU / 2, None                  # inner layers centred on the interface
        S.body("%s_%s" % (n, lay), dxf("%s_%s_%g" % (n, lay, psi), loops, []), z, CU, "all", "cu", direc)
    return b

def add_spacers(S, levels):
    """levels: list of (name, z_bottom, height). Nylon tubes OD 5 / ID 2.7 on every rim hole [ASSUMED]."""
    for name, z, h in levels:
        circ = []
        for x, y, r in rim_holes(): circ += [(x, y, 2.5), (x, y, 1.35)]
        S.body(name, dxf(name, [], circ), z, h, [{"point": [G.H["R_holes"] * math.cos(2 * math.pi * k / G.H["n_holes"]) + 1.9 * math.cos(2 * math.pi * k / G.H["n_holes"]),
                                                               G.H["R_holes"] * math.sin(2 * math.pi * k / G.H["n_holes"]) + 1.9 * math.sin(2 * math.pi * k / G.H["n_holes"])]} for k in range(G.H["n_holes"])], "nylon")

def run(script, step, tag):
    js = os.path.join(OUT, tag + ".solidcraft.json"); script.save(js)
    exe = shutil.which("solidcraft-cli")
    if not exe:
        print("solidcraft-cli not found: wrote %s only (run: solidcraft-cli run %s --out %s)" % (js, js, step)); return None
    r = subprocess.run([exe, "run", js, "--out", step], capture_output=True, text=True, cwd=OUT)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); raise SystemExit("solidcraft failed on " + tag)
    res = json.loads(r.stdout[r.stdout.index("{"):])
    return res

def report(tag, res, lines):
    """One line per part (patches and spacers are many bodies named 'X', 'X (2)', ...)."""
    if res is None: return
    import re
    lines.append("== %s: %d bodies, total volume %.1f mm3, faces %d" % (tag, res["body_count"], res["total"]["volume_mm3"], res["total"]["faces"]))
    agg = {}
    for bd in res["bodies"]:
        k = re.sub(r" \(\d+\)$", "", bd["name"]); a = agg.setdefault(k, [0, 0.0, 9e9, -9e9])
        a[0] += 1; a[1] += bd["volume_mm3"]; a[2] = min(a[2], bd["bbox"]["min"][2]); a[3] = max(a[3], bd["bbox"]["max"][2])
    for k, (n, v, z0, z1) in agg.items():
        lines.append("   %-24s bodies %5d  volume %12.3f mm3  z %8.3f .. %8.3f" % (k, n, v, z0, z1))

def main(psi1=0.0, psi2=120.0):
    os.makedirs(TMP, exist_ok=True); lines = []
    lib = CL.library()
    S = Script(); add_rlsa(S); report("RLSA_feed_assembly", run(S, os.path.join(OUT, "RLSA_feed_assembly.step"), "RLSA_feed_assembly"), lines)
    z1 = G.R["Wh"] + G.H["gap_rlsa"]; z2 = z1 + G.H["t"] + G.H["gap_hm"]
    for w in (1, 2):
        S = Script(); add_hm(S, w, 0.0, 0.0, lib); report("HM%d" % w, run(S, os.path.join(OUT, "HM%d.step" % w), "HM%d" % w), lines)
    S = Script(); add_rlsa(S); add_hm(S, 1, z1, psi1, lib); add_hm(S, 2, z2, psi2, lib)
    add_spacers(S, [("spacers_gnd_rlsa", 0.0, G.R["h_air"]), ("spacers_rlsa_hm1", G.R["Wh"] + CU, G.H["gap_rlsa"] - 2 * CU), ("spacers_hm1_hm2", z1 + G.H["t"] + CU, G.H["gap_hm"] - 2 * CU)])
    tag = "NFMS_system_psi1_%g_psi2_%g" % (psi1, psi2)
    report(tag, run(S, os.path.join(OUT, tag + ".step"), tag), lines)
    with open(os.path.join(OUT, "STEP_report.txt"), "w") as fh: fh.write("\n".join(lines) + "\n")
    # the big files go into zips (git-friendly); the DXF sources are scratch
    import zipfile
    for f in os.listdir(OUT):
        if f.endswith(".step") and os.path.getsize(os.path.join(OUT, f)) > 20e6:
            with zipfile.ZipFile(os.path.join(OUT, f + ".zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z: z.write(os.path.join(OUT, f), f)
            os.remove(os.path.join(OUT, f))
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n".join(lines))

if __name__ == "__main__":
    a = [float(v) for v in sys.argv[1:3]]
    main(*a) if a else main()
