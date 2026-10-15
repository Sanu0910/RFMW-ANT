"""Build every DXF, preview, cell table, BOM and DRC report for the NFMS RLSA + hybrid-metasurface pack.
    python build_nfms.py            -> ../01_dxf   (also writes results/cell_library.csv, phase-map CSVs)
DXF layers (mm):
  OUTLINE      board / plate edge (HM: with the V index notch at +x = phase-delay axis)
  TOP_CU       RLSA top copper disc;  TOP_SLOT  radiating slots to SUBTRACT from TOP_CU
  BOT_POCKET   RLSA: 0.6 mm deep blind pocket on the bottom face for the probe head
  M1..M4       HM patch layers, M1 = input face (towards the RLSA), M4 = output
  DRILL        HM Type II cells: non-plated holes through all three laminates (circle = finished hole)
  NPTH         mounting / spacer holes (and SMA holes on the ground plate)
  SILK_TOP     marking on the top face (axis arrow, angle scale, names);  ASSY  component bodies;  FAB  notes
All views are from the top (+z looking down).  Layers on the bottom of a laminate are NOT mirrored."""
import os, csv, math
import numpy as np
import ezdxf
from shapely.geometry import MultiPolygon, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
import cells as CL
import nfmsgeom as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "01_dxf"))
RES = os.path.join(HERE, "results")
LAY = {"OUTLINE": 7, "TOP_CU": 1, "TOP_SLOT": 3, "BOT_POCKET": 6, "M1": 1, "M2": 30, "M3": 5, "M4": 3,
       "DRILL": 6, "NPTH": 9, "SILK_TOP": 7, "ASSY": 4, "FAB": 8}
FAB_RLSA = ["RLSA: Taconic TLY-5 1.6 mm (er 2.2), double-side 1/2 oz Cu. Etch TOP_CU minus TOP_SLOT; remove ALL bottom Cu.",
            "Mill BOT_POCKET d2.8 x 0.6 deep from the bottom (probe head). Drill NPTH d3.0 (24x on R187.5).",
            "Slot width 1.0 mm +/-0.02; slot length 4.3 -> 4.9 mm (linear in radius). 960 pairs, CCW outward spiral, RHCP.",
            "Suspended 3.0 mm above the Al ground plate on nylon spacers (air part of the radial waveguide)."]
FAB_HM = ["HM: 3 x Taconic TLY-5 1.6 mm, bonded with thin prepreg (e.g. FR-27/fastRise 0.1 mm) [ASSUMED, paper ignores prepreg].",
          "LAM1 = M1 (bottom) + M2 (top); LAM2 = no Cu; LAM3 = M3 (bottom) + M4 (top). Order from RLSA side: LAM1, LAM2, LAM3.",
          "After bonding drill DRILL holes (non-plated) through all; drill NPTH d3.0 (24x on R187.5). Cu 17 um, no finish needed (or ENIG).",
          "Register the three laminates on the 24 rim holes + the +x notch. Phase-delay axis = +x (arrow)."]

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]

def merged(b, lay):
    g = unary_union(b.L.get(lay, []))
    if lay == "TOP_CU": g = g.difference(unary_union(b.L.get("TOP_SLOT", [])))
    return g

def write(b, path, layers=None, fab=(), cut_slots=True):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4
    for n, c in LAY.items(): d.layers.add(n, color=c)
    m = d.modelspace(); keep = layers or list(LAY)
    for lay in ("OUTLINE", "TOP_CU", "TOP_SLOT", "BOT_POCKET", "M1", "M2", "M3", "M4", "SILK_TOP"):
        if lay not in keep or lay not in b.L: continue
        if lay == "TOP_CU" and not cut_slots: g = unary_union(b.L["TOP_CU"])
        else: g = merged(b, lay) if lay != "TOP_SLOT" else None
        geoms = b.L["TOP_SLOT"] if lay == "TOP_SLOT" else polys(g)
        for p in geoms:
            m.add_lwpolyline(list(p.exterior.coords)[:-1], close=True, dxfattribs={"layer": lay})
            for h in p.interiors: m.add_lwpolyline(list(h.coords)[:-1], close=True, dxfattribs={"layer": lay})
    for lay, x, y, dd, note in b.holes:
        if lay in keep: m.add_circle((x, y), dd / 2, dxfattribs={"layer": lay})
    for (lay, s, x, y, h, rot, al) in b.txt:
        if lay in keep:
            t = m.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay}); t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment[al])
    if "ASSY" in keep:
        for c in b.comp:
            x, y, w, h = c["x"], c["y"], c["w"], c["h"]
            m.add_lwpolyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], close=True, dxfattribs={"layer": "ASSY"})
            t = m.add_text(c["ref"], height=2.0, dxfattribs={"layer": "ASSY"}); t.set_placement((x, y + h / 2 + 2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    if "FAB" in keep:
        bx = b.L["OUTLINE"][0].bounds
        for k, s in enumerate(fab):
            t = m.add_text(s, height=3.0, dxfattribs={"layer": "FAB"}); t.set_placement((bx[0], bx[1] - 8 - 5 * k))
    d.saveas(path)

# ---------------- previews ----------------
def _draw(ax, g, **kw):
    import matplotlib.pyplot as plt
    for p in polys(g):
        ax.add_patch(plt.Polygon(list(p.exterior.coords), **kw))
        for h in p.interiors: ax.add_patch(plt.Polygon(list(h.coords), fc="white", ec="none"))

def preview_rlsa(b, path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(19, 6.8))
    for a_, lim in zip(ax, (200, 40, None)):
        a_.add_patch(plt.Polygon(list(b.L["OUTLINE"][0].exterior.coords), fc="#e9e2cf", ec="k", lw=0.6))
        if lim is not None:
            _draw(a_, unary_union(b.L["TOP_CU"]), fc="#c98a3c", ec="none")
            for s in b.L["TOP_SLOT"]: a_.add_patch(plt.Polygon(list(s.exterior.coords), fc="#e9e2cf", ec="none"))
            for lay, x, y, dd, n in b.holes: a_.add_patch(plt.Circle((x, y), dd / 2, fc="white", ec="k", lw=0.3))
            a_.set_xlim(-lim, lim); a_.set_ylim(-lim, lim)
            if lim < 100:
                a_.add_patch(plt.Circle((0, 0), G.R["head_d"] / 2, fc="none", ec="b", ls="--", lw=0.8))
                for p in b.pairs[:40]: a_.text(*p["ca"], str(p["n"]), fontsize=5, color="navy", ha="center", va="center")
                a_.set_title("centre: slot pairs 0-39 (A at +45 deg, B on A's normal, lambda_g/4 out); probe head dashed", fontsize=8)
            else:
                a_.set_title("RLSA top copper (%d slot pairs, %.2f turns), dielectric rim and 24 spacer holes" % (len(b.pairs), G.turns_of(b.pairs)), fontsize=9)
        else:
            r = [p["rho"] for p in b.pairs]; L = [p["L"] for p in b.pairs]
            a_.remove(); a_ = fig.add_subplot(1, 3, 3); a_.plot(r, L, "k.", ms=2); a_.set_xlabel("pair radius (mm)"); a_.set_ylabel("slot length (mm)")
            a_.set_title("slot length taper (linear [ASSUMED], 4.3 -> 4.9 mm)", fontsize=9); a_.grid(alpha=0.3); continue
        a_.set_aspect("equal"); a_.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)

def preview_hm(b, path, tgt):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(22, 6.0))
    pm = G.phase_maps(); ext = [pm["x"][0] - 3.75, pm["x"][-1] + 3.75, pm["y"][0] - 3.75, pm["y"][-1] + 3.75]
    im = ax[0].imshow(tgt, origin="lower", extent=ext, cmap="jet", vmin=-360, vmax=0); fig.colorbar(im, ax=ax[0], fraction=0.046)
    ax[0].set_title("%s required transmission phase (deg)" % b.name, fontsize=9)
    ach = np.full(tgt.shape, np.nan); err = np.full(tgt.shape, np.nan)
    for r in b.rows: ach[r["j"], r["i"]] = r["phase"]; err[r["j"], r["i"]] = r["err"]
    im = ax[1].imshow(err, origin="lower", extent=ext, cmap="coolwarm", vmin=-30, vmax=30); fig.colorbar(im, ax=ax[1], fraction=0.046)
    ax[1].set_title("phase error of the chosen cells (deg), rms %.1f" % np.sqrt(np.nanmean(err ** 2)), fontsize=9)
    for a_, lays, ttl in ((ax[2], ("M1",), "M1 (= M3) patches a + DRILL (Type II holes)"), (ax[3], ("M2",), "M2 (= M4) patches b, silkscreen")):
        a_.add_patch(plt.Polygon(list(b.L["OUTLINE"][0].exterior.coords), fc="#d8d2bf", ec="k", lw=0.6))
        for lay in lays: _draw(a_, unary_union(b.L.get(lay, [])), fc="#b87333", ec="none")
        for lay, x, y, dd, n in b.holes: a_.add_patch(plt.Circle((x, y), dd / 2, fc="white", ec="k", lw=0.2))
        if "M2" in lays:
            _draw(a_, unary_union(b.L.get("SILK_TOP", [])), fc="k", ec="none")
            for (l, s, x, y, h, rot, al) in b.txt:
                if l == "SILK_TOP": a_.text(x, y, s, fontsize=max(3, h * 1.6), rotation=rot, ha="center", va="center")
        a_.set_xlim(-200, 200); a_.set_ylim(-200, 200); a_.set_aspect("equal"); a_.set_title(ttl, fontsize=9); a_.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)

def preview_simple(b, path, title, layers):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, a_ = plt.subplots(figsize=(7, 7))
    a_.add_patch(plt.Polygon(list(b.L["OUTLINE"][0].exterior.coords), fc="#d8d2bf", ec="k", lw=0.6))
    for lay in layers: _draw(a_, unary_union(b.L.get(lay, [])), fc="#b87333", ec="none")
    for lay, x, y, dd, n in b.holes: a_.add_patch(plt.Circle((x, y), dd / 2, fc="white", ec="k", lw=0.3))
    bx = b.L["OUTLINE"][0].bounds; a_.set_xlim(bx[0] - 2, bx[2] + 2); a_.set_ylim(bx[1] - 2, bx[3] + 2)
    a_.set_aspect("equal"); a_.set_title(title, fontsize=9); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)

# ---------------- DRC ----------------
def min_gap(geoms, search=2.0):
    if len(geoms) < 2: return 99.0
    t = STRtree(geoms); mg = 99.0
    for k, s in enumerate(geoms):
        for m in t.query(s.buffer(search)):
            if m > k: mg = min(mg, s.distance(geoms[m]))
    return mg

def drc_hm(b):
    rep = []
    for lay in ("M1", "M2", "M3", "M4"):
        g = b.L.get(lay, []); mg = min_gap(g, G.H["d"])
        rep.append("%s: %d patches, min copper gap %.3f mm%s, smallest patch %.2f mm" % (lay, len(g), mg, "  <-- below 0.15" if mg < 0.15 else "",
                   min((p.bounds[2] - p.bounds[0] for p in g), default=0)))
    dr = [Point(x, y).buffer(d / 2) for lay, x, y, d, n in b.holes if lay == "DRILL"]
    web = min_gap(dr, 8.0) if dr else 99
    cu = unary_union([unary_union(b.L.get(l, [])) for l in ("M1", "M2", "M3", "M4")])
    hit = unary_union(dr).intersection(cu).area if dr else 0
    rep.append("DRILL: %d Type II holes, d %.2f-%.2f mm, min dielectric web %.3f mm; holes through copper: %.4f mm2" %
               (len(dr), min((h[3] for h in b.holes if h[0] == "DRILL"), default=0), max((h[3] for h in b.holes if h[0] == "DRILL"), default=0), web, hit))
    n1 = sum(1 for r in b.rows if r["type"] == 1); n2 = len(b.rows) - n1; n2h = sum(1 for r in b.rows if r["type"] == 2 and r["r"] > 0)
    e = np.array([r["err"] for r in b.rows]); m = np.array([r["mag_db"] for r in b.rows])
    rep.append("cells: %d (Type I %d, Type II %d of which %d drilled, %d bare dielectric); metal-free fraction %.1f %%" % (len(b.rows), n1, n2, n2h, n2 - n2h, 100 * n2 / len(b.rows)))
    rep.append("phase error: rms %.2f deg, max %.2f deg;  |S21| model: mean %.2f dB, worst %.2f dB, cells below -1 dB: %d" %
               (np.sqrt(np.mean(e ** 2)), np.max(np.abs(e)), np.mean(m), np.min(m), int(np.sum(m < -1))))
    return rep

def drc_rlsa(b):
    sl = b.L["TOP_SLOT"]; mg = min_gap(sl, 3.0)
    ext = max(math.hypot(*p.centroid.coords[0]) for p in sl)
    head = Point(0, 0).buffer(G.R["head_d"] / 2)
    return ["TOP_SLOT: %d slots, min copper web between slots %.3f mm, outermost slot centre r = %.2f mm, copper disc r = %d mm" % (len(sl), mg, ext, b.r_cu),
            "paper aperture r = %.1f mm -> outermost slots extend %.1f mm beyond it (see guide)" % (G.R["D_ap"] / 2, ext + G.R["Lmax"] / 2 - G.R["D_ap"] / 2),
            "slots over the probe head: %.4f mm2;  innermost slot centre r = %.2f mm" % (unary_union(sl).intersection(head).area, min(math.hypot(*p.centroid.coords[0]) for p in sl))]

def write_csv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)

def unit_cell(kind, **kw):
    d = G.H["d"]; b = G.Board("CELL", box(-d / 2, -d / 2, d / 2, d / 2))
    if kind == 1:
        for lay, s in (("M1", kw["a"]), ("M2", kw["b"]), ("M3", kw["a"]), ("M4", kw["b"])): b.add(lay, box(-s / 2, -s / 2, s / 2, s / 2))
    else:
        b.hole("DRILL", 0, 0, 2 * kw["r"])
    return b

def main():
    for s in ("A_rlsa", "B_hm1", "C_hm2", "D_fab_laminates", "E_unit_cells"): os.makedirs(os.path.join(OUT, s), exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    log, bom = [], []
    # cell library
    hf = os.path.join(RES, "hfss_cell_table.csv")
    lib = CL.load_table(hf) if os.path.exists(hf) else CL.library()       # full-wave table wins when present
    log.append("cell library: " + ("HFSS table " + hf if os.path.exists(hf) else "closed-form models (cells.py, C_SCALE %.2f)" % CL.C_SCALE))
    write_csv(os.path.join(RES, "cell_library.csv"), ["type", "a_mm", "b_mm", "r_mm", "phase_unwrapped_deg", "phase_norm_deg", "S21_dB"],
              [[c["type"], c["a"], c["b"], c["r"], round(c["phase_unwrapped"], 3), round(c["phase_norm"], 3), round(c["mag_db"], 4)] for c in lib])
    # RLSA + ground
    rl = G.board_rlsa(); gp = G.board_ground()
    p = os.path.join(OUT, "A_rlsa", "RLSA_TLY5_1p6_960pairs")
    write(rl, p + ".dxf", fab=FAB_RLSA); preview_rlsa(rl, p + "_preview.png")
    write(rl, os.path.join(OUT, "A_rlsa", "RLSA_TOP_CU_uncut_plus_SLOT_layer.dxf"), ["OUTLINE", "TOP_CU", "TOP_SLOT", "NPTH"], cut_slots=False)
    q = os.path.join(OUT, "A_rlsa", "GROUND_PLATE_Al_3mm")
    write(gp, q + ".dxf", ["OUTLINE", "NPTH", "SILK_TOP"], fab=["Aluminium 6061, 3.0 mm, flat to 0.1 mm. Holes per NPTH layer. SMA from below."]); preview_simple(gp, q + "_preview.png", "Ground plate (Al 3 mm): SMA + 24 spacer holes", [])
    write_csv(os.path.join(OUT, "A_rlsa", "slot_table.csv"), ["pair", "rho_A_mm", "phi_A_deg", "L_mm", "xA", "yA", "angA_deg", "xB", "yB", "angB_deg"],
              [[s["n"], round(s["rho"], 4), round(math.degrees(s["phi"]), 4), round(s["L"], 4), round(s["ca"][0], 4), round(s["ca"][1], 4), round(s["ang_a"], 3),
                round(s["cb"][0], 4), round(s["cb"][1], 4), round(s["ang_b"], 3)] for s in rl.pairs])
    log.append("== RLSA"); log += ["   " + r for r in drc_rlsa(rl)]
    bom.append(["RLSA", "PCB", "Taconic TLY-5 1.6 mm D%.0f, slotted top" % G.R["D_diel"], 1, "A_rlsa/RLSA_TLY5_1p6_960pairs.dxf"])
    bom.append(["RLSA", "plate", "Al 6061 3 mm D%.0f ground plate" % G.R["D_diel"], 1, "A_rlsa/GROUND_PLATE_Al_3mm.dxf"])
    bom.append(["RLSA", "J1", "SMA 4-hole flange jack, PTFE flush with plate top, pin cut to 1.6 mm [ASSUMED part]", 1, "centre"])
    bom.append(["RLSA", "probe head", "brass disc d2.8 x 2.0 mm, soldered/glued on the SMA pin (Fig. 9(a), Fig. 16 inset)", 1, "z 1.6-3.6"])
    # phase maps
    pm = G.phase_maps()
    for k in ("corr", "grad", "hm1", "hm2"):
        np.savetxt(os.path.join(RES, "phase_map_%s.csv" % k), pm[k], delimiter=",", fmt="%.2f")
    # HMs
    for which, sub in ((1, "B_hm1"), (2, "C_hm2")):
        b = G.board_hm(which, lib)
        name = "HM%s_48x48_all_layers" % ("1" if which == 1 else "2")
        path = os.path.join(OUT, sub, name)
        write(b, path + ".dxf", fab=FAB_HM); preview_hm(b, path + "_preview.png", pm["hm1" if which == 1 else "hm2"])
        write_csv(os.path.join(OUT, sub, "HM%d_cell_assignment.csv" % which), ["i", "j", "x_mm", "y_mm", "target_deg", "type", "a_mm", "b_mm", "r_mm", "phase_deg", "error_deg", "S21_dB_model"],
                  [[r["i"], r["j"], r["x"], r["y"], round(r["target"], 2), r["type"], r["a"], r["b"], r["r"], round(r["phase"], 2), round(r["err"], 2), round(r["mag_db"], 3)] for r in b.rows])
        tag = "HM%d" % which
        write(b, os.path.join(OUT, "D_fab_laminates", tag + "_LAM1_M1bottom_M2top.dxf"), ["OUTLINE", "M1", "M2", "NPTH", "FAB"], fab=["%s LAM1: M1 on BOTTOM (input), M2 on TOP; top view, not mirrored" % tag])
        write(b, os.path.join(OUT, "D_fab_laminates", tag + "_LAM2_no_copper.dxf"), ["OUTLINE", "NPTH", "FAB"], fab=["%s LAM2: TLY-5 1.6 mm, all copper removed" % tag])
        write(b, os.path.join(OUT, "D_fab_laminates", tag + "_LAM3_M3bottom_M4top.dxf"), ["OUTLINE", "M3", "M4", "NPTH", "SILK_TOP", "FAB"], fab=["%s LAM3: M3 on BOTTOM, M4 on TOP (output); top view" % tag])
        write(b, os.path.join(OUT, "D_fab_laminates", tag + "_DRILL_after_bonding.dxf"), ["OUTLINE", "DRILL", "NPTH", "FAB"], fab=["%s: drill DRILL (NPTH) through the bonded stack, sizes = circle diameters" % tag])
        log.append("== " + b.name); log += ["   " + r for r in drc_hm(b)]
        n1 = sum(1 for r in b.rows if r["type"] == 1)
        bom.append([b.name, "PCB stack", "3 x TLY-5 1.6 mm D%.0f + 2 prepreg, %d Type I + %d Type II cells" % (G.H["D_diel"], n1, len(b.rows) - n1), 1, sub + "/" + name + ".dxf"])
        drills = {}
        for lay, x, y, d, n in b.holes:
            if lay == "DRILL": drills[round(d, 2)] = drills.get(round(d, 2), 0) + 1
        write_csv(os.path.join(OUT, sub, "HM%d_drill_table.csv" % which), ["finished_diameter_mm", "count"], sorted(drills.items()))
    bom.append(["ASSY", "spacers", "nylon M2.5 screw + spacers: 3.0 mm (ground-RLSA), 15.0 mm (RLSA-HM I), 15.0 mm (HM I-HM II) on R187.5 [ASSUMED]", 72, "24 per level"])
    # unit cells for HFSS
    ex = [("TypeI_a4p0_b3p7_paper_example", unit_cell(1, a=4.0, b=3.7)), ("TypeII_r2p8_paper_edge_example", unit_cell(2, r=2.8)), ("TypeII_r1p4_if_2p8_were_diameter", unit_cell(2, r=1.4))]
    for n, b in ex: write(b, os.path.join(OUT, "E_unit_cells", n + ".dxf"), ["OUTLINE", "M1", "M2", "M3", "M4", "DRILL"])
    write_csv(os.path.join(OUT, "BOM_and_placement.csv"), ["item", "ref", "description", "qty", "file / position"], bom)
    with open(os.path.join(OUT, "DRC_report.txt"), "w") as fh: fh.write("\n".join(log) + "\n")
    print("\n".join(log))

if __name__ == "__main__":
    main()
