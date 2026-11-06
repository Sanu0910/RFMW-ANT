"""Regenerate every output of the project from config.py.
    python build_all.py                 # both plates: plate, assembly, exploded STEP + renders, then drawings + report
    python build_all.py plate 15        # only some parts (plate, assy, exploded, drawing, report) / only some boards (15, 65)
"""
import os, sys, time
import config as C
import plate as Pm

PARTS = ("plate", "assy", "exploded", "drawing", "report")


def main(args):
    t0 = time.time()
    parts = [a for a in args if a in PARTS] or list(PARTS)
    keys = [a for a in args if a in C.BOARDS] or list(C.BOARDS)
    done = {}
    for k in keys:
        B = Pm.read_board(k); H = Pm.Plate(B); pn = B["pn"]; res = {}
        bad = [c for c in H.checks() if not c[3]]
        if bad: raise SystemExit("%s: failed checks %s" % (pn, bad))
        if "plate" in parts:
            s = Pm.S(); Pm.build_plate(s, H)
            res["plate"] = Pm.run(s, pn + "_PLATE", [pn + "_PLATE.step"],
                                  [("iso", pn + "_PLATE_iso.png", []), ("bottom", pn + "_PLATE_bottom.png", [])])
        if "assy" in parts:
            res["assy"] = Pm.run(Pm.assembly(H), pn + "_ASSY", [pn + "_ASSY.step"], [("iso", pn + "_ASSY_iso.png", [])])
        if "exploded" in parts:
            res["exploded"] = Pm.run(Pm.assembly(H, True), pn + "_ASSY_EXPLODED", [pn + "_ASSY_EXPLODED.step"], [("iso", pn + "_ASSY_EXPLODED_iso.png", [])])
        if "plate" not in res: res["plate"] = Pm.measure(pn + "_PLATE.step")
        H.mass_g = res["plate"].get("total", {}).get("volume_mm3", 0) * 2.70e-3
        for n, r in res.items():
            print("%s %-9s %d bodies, %.0f mm3" % (pn, n, r.get("body_count", 0), r.get("total", {}).get("volume_mm3", 0)))
        done[k] = (B, H, res)
    if "drawing" in parts:
        import drawing
        for k, (B, H, _r) in done.items(): drawing.write(B, H)
    if "report" in parts:
        import report
        report.write({k: v for k, v in done.items()})
    print("done in %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main(sys.argv[1:])
