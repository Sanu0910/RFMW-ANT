"""Regenerate every output of the PocketSDR v2.3 CNC case from config.py.
    python build_case.py                    # parts, assembly, exploded STEP + renders, then the drawing set
    python build_case.py tube ant usb       # only some of: tube ant usb assy exploded drawing
"""
import sys, time
import config as C
import case as Cm

STEPS = ("tube", "ant", "usb", "assy", "exploded", "drawing")


def main(args):
    t0 = time.time()
    todo = [a for a in args if a in STEPS] or list(STEPS)
    H = Cm.Case()
    for n, v, rule, ok in H.checks():
        print("%-4s %-48s %-14s %s" % ("ok" if ok else "FAIL", n, v, rule))
    bad = [c for c in H.checks() if not c[3]]
    if bad: raise SystemExit("failed checks: %s" % bad)
    res = {}
    for key in ("tube", "ant", "usb"):
        if key not in todo: continue
        s = Cm.S(); pn = C.PARTS[key]
        Cm.build_tube(s, H) if key == "tube" else Cm.build_panel(s, H, key)
        res[key] = Cm.run(s, pn, [pn + ".step"], [("iso", pn + "_iso.png", [])])
    if "assy" in todo:
        res["assy"] = Cm.run(Cm.assembly(H), C.PN + "_ASSY", [C.PN + "_ASSY.step"],
                             [("iso", C.PN + "_ASSY_iso.png", []), ("iso", C.PN + "_ASSY_xray.png", ["--body", "TUBE:opacity=0.25"])])
    if "exploded" in todo:
        res["exploded"] = Cm.run(Cm.assembly(H, 10.0), C.PN + "_ASSY_EXPLODED", [C.PN + "_ASSY_EXPLODED.step"],
                                 [("iso", C.PN + "_ASSY_EXPLODED_iso.png", [])])
    for k, r in res.items():
        print("%-9s %3d bodies  %8.0f mm3" % (k, r.get("body_count", 0), r.get("total", {}).get("volume_mm3", 0)))
    if "drawing" in todo:
        import drawing
        drawing.write(H)
    print("done in %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main(sys.argv[1:])
