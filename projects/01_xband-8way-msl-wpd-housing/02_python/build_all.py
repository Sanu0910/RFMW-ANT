"""Regenerate every output of the project from config.py.
    python build_all.py            # everything
    python build_all.py base lid   # only some CAD parts (base, lid, box, assy, exploded), plus PCB v3 / gasket / report
"""
import os, sys, time
import config as C
import geom as G
import housing as Hm
import pcb_v3


def main(parts):
    t0 = time.time()
    B = G.read_board()
    holes, _ = G.place_holes(B)
    pcb = pcb_v3.build(B, holes)
    print("PCB v3: %d holes, %d vias removed -> %s" % (len(holes), pcb["removed"], os.path.relpath(pcb["path"], C.ROOT)))
    H = Hm.Housing(B, holes)
    pn = C.TEXT["pn"]; res = {}
    if "base" in parts:
        s = Hm.S(); Hm.build_base(s, H)
        res["base"] = Hm.run(s, pn + "_BASE", [pn + "_BASE.step"], [("iso", pn + "_BASE_iso.png", [])])
    if "lid" in parts:
        s = Hm.S(); Hm.build_lid(s, H)
        res["lid"] = Hm.run(s, pn + "_LID", [pn + "_LID.step"], [("top", pn + "_LID_top.png", []), ("bottom", pn + "_LID_cage_bottom.png", [])])
    if "gasket" in parts:
        s = Hm.S(); Hm.build_gasket(s, H)
        res["gasket"] = Hm.run(s, pn + "_GASKET", [pn + "_GASKET.step"])
    if "box" in parts:
        res["box"] = Hm.run(Hm.box_only(H), pn + "_BOX_ONLY", [pn + "_BOX_ONLY.step"], [("iso", pn + "_BOX_ONLY_iso.png", [])])
    if "assy" in parts:
        res["assy"] = Hm.run(Hm.assembly(H), pn + "_ASSY", [pn + "_ASSY.step"],
                             [("iso", pn + "_ASSY_iso.png", []), ("iso", pn + "_ASSY_inside.png", ["--body", "LID:opacity=0.15", "--body", "GASKET:opacity=0.4"])])
    if "exploded" in parts:
        res["exploded"] = Hm.run(Hm.assembly(H, True), pn + "_ASSY_EXPLODED", [pn + "_ASSY_EXPLODED.step"], [("iso", pn + "_ASSY_EXPLODED_iso.png", [])])
    for k in ("base", "lid", "gasket"):                       # masses for the report even when not rebuilt now
        if k not in res: res[k] = Hm.measure("%s_%s.step" % (pn, k.upper()))
    for k, r in res.items():
        print("%-8s %d bodies, %.0f g" % (k, r.get("body_count", 0), r.get("total", {}).get("mass_g", 0)))
    if "report" in parts:
        import report
        report.write(B, holes, H, pcb, res)
    if "drawing" in parts:
        import drawing
        drawing.write(B, holes, H)
    print("done in %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or {"base", "lid", "gasket", "box", "assy", "exploded", "report", "drawing"})
