"""Gerber RS-274X (X2) + Excellon drill set made from the PCB V3 DXF (the board that fits housing CRL-XB-PD8-03).
Same coordinates as the DXF (customer frame, mm).
    -> ../01_pcb_v3/gerber_v3/*.gbr, *.drl, README.txt, preview.png, and ../01_pcb_v3/<NAME>_gerber.zip
Layers:
    F_Cu      TOP_COPPER + TOP_GROUND_POUR regions, VIA_PADS d0.50 flashes, M2 hole pads (MOUNT_HEAD_KEEPOUT d) flashes
    B_Cu      solid ground over the whole board outline [ASSUMED: the DXF has no bottom layer]
    F_Mask, B_Mask  whole board open = no solder mask [ASSUMED: bare RO4350B + ENIG, usual for X-band microstrip]
    F_Paste   RES_PADS_0402 lands
    Edge_Cuts BOARD_OUTLINE, 0.10 mm line
    PTH.drl   VIA_HOLES d0.20 + MOUNT_HOLES_PTH d2.40, all plated, finished sizes
Run: python gerber_v3.py   (also run by build_all.py)"""
import os, zipfile
import ezdxf
import config as C

NAME = "Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady_V3"
SRC = os.path.join(C.ROOT, "01_pcb_v3", NAME + ".dxf")
OUT = os.path.join(C.ROOT, "01_pcb_v3", "gerber_v3")
VIA_PAD = 0.50                                   # generator script: via_pad_mm


def num(v):                                       # format 4.6, mm
    return "%d" % round(v * 1e6)


def poly_pts(e):
    pts = [(p[0], p[1]) for p in e.get_points()]
    assert all(abs(p[4]) < 1e-12 for p in e.get_points()), "arc segment in %s" % e.dxf.layer
    if pts[0] != pts[-1]: pts.append(pts[0])
    return pts


class Gbr:
    def __init__(self, func, polarity="Positive"):
        self.l = ["%TF.GenerationSoftware,RFMW-ANT,gerber_v3.py,1*%",
                  "%TF.Part,Single*%", "%%TF.SameCoordinates,%s*%%" % NAME,
                  "%%TF.FileFunction,%s*%%" % func, "%%TF.FilePolarity,%s*%%" % polarity,
                  "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%", "G01*"]
        self.ap = {}

    def aperture(self, d):
        if d not in self.ap:
            code = 10 + len(self.ap); self.ap[d] = code
            self.l.append("%%ADD%dC,%.4f*%%" % (code, d))
        return self.ap[d]

    def region(self, pts):
        self.l += ["G36*", "X%sY%sD02*" % (num(pts[0][0]), num(pts[0][1]))]
        self.l += ["X%sY%sD01*" % (num(x), num(y)) for x, y in pts[1:]]
        self.l.append("G37*")

    def flashes(self, d, xys):
        self.l.append("D%d*" % self.aperture(d))
        self.l += ["X%sY%sD03*" % (num(x), num(y)) for x, y in xys]

    def line(self, d, pts):
        self.l.append("D%d*" % self.aperture(d))
        self.l.append("X%sY%sD02*" % (num(pts[0][0]), num(pts[0][1])))
        self.l += ["X%sY%sD01*" % (num(x), num(y)) for x, y in pts[1:]]

    def save(self, path):
        # apertures must be defined before use: move every %ADD line up to the header
        head = [s for s in self.l if not s.startswith("%ADD")]
        adds = [s for s in self.l if s.startswith("%ADD")]
        i = head.index("G01*")
        with open(path, "w", newline="\n") as fh:
            fh.write("\n".join(head[:i] + adds + head[i:] + ["M02*", ""]))


def build():
    os.makedirs(OUT, exist_ok=True)
    m = ezdxf.readfile(SRC).modelspace()
    q = lambda t, lay: list(m.query('%s[layer=="%s"]' % (t, lay)))
    circ = lambda lay: [(e.dxf.center.x, e.dxf.center.y, e.dxf.radius) for e in q("CIRCLE", lay)]
    outline = poly_pts(q("LWPOLYLINE", "BOARD_OUTLINE")[0])
    sig = [poly_pts(e) for e in q("LWPOLYLINE", "TOP_COPPER")]
    pour = [poly_pts(e) for e in q("LWPOLYLINE", "TOP_GROUND_POUR")]
    pads = [poly_pts(e) for e in q("LWPOLYLINE", "RES_PADS_0402")]
    vpad, vhole = circ("VIA_PADS"), circ("VIA_HOLES")
    mhole, mkeep = circ("MOUNT_HOLES_PTH"), circ("MOUNT_HEAD_KEEPOUT")
    files = {}

    g = Gbr("Copper,L1,Top"); [g.region(p) for p in sig + pour]
    g.flashes(VIA_PAD, [(x, y) for x, y, r in vpad])
    g.flashes(round(2 * mkeep[0][2], 4), [(x, y) for x, y, r in mkeep]); files["F_Cu.gbr"] = g
    g = Gbr("Copper,L2,Bot"); g.region(outline); files["B_Cu.gbr"] = g
    for side, f in (("Top", "F_Mask.gbr"), ("Bot", "B_Mask.gbr")):
        g = Gbr("Soldermask,%s" % side, "Negative"); g.region(outline); files[f] = g
    g = Gbr("Paste,Top"); [g.region(p) for p in pads]; files["F_Paste.gbr"] = g
    g = Gbr("Profile,NP"); g.line(0.10, outline); files["Edge_Cuts.gbr"] = g
    for f, gb in files.items(): gb.save(os.path.join(OUT, "%s-%s" % (NAME, f)))

    tools = {}
    for x, y, r in vhole + mhole: tools.setdefault(round(2 * r, 3), []).append((x, y))
    drl = ["M48", "; DRILL file RFMW-ANT gerber_v3.py, finished hole sizes, all plated",
           "; #@! TF.FileFunction,Plated,1,2,PTH", "FMAT,2", "METRIC,TZ"]
    for i, d in enumerate(sorted(tools)): drl.append("T%dC%.3f" % (i + 1, d))
    drl += ["G90", "%", "G05"]
    for i, d in enumerate(sorted(tools)):
        drl.append("T%d" % (i + 1)); drl += ["X%.4fY%.4f" % xy for xy in tools[d]]
    drl += ["T0", "M30", ""]
    with open(os.path.join(OUT, NAME + "-PTH.drl"), "w", newline="\n") as fh: fh.write("\n".join(drl))

    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    readme = """{name} - Gerber set (generated by 02_python/gerber_v3.py from {name}.dxf; do not edit by hand)
Board  : {w:.3f} x {h:.3f} mm, 2 layers, Rogers RO4350B 0.762 mm (30 mil), 1 oz Cu both sides, finish ENIG (or immersion silver)
Units  : mm, Gerber X2 format 4.6, absolute; drill Excellon METRIC, finished sizes; same origin as the DXF
Files  : F_Cu       top copper (signal + ground pour + via pads + M2 hole pads)
         B_Cu       bottom copper, solid ground [ASSUMED - confirm with the PCB designer]
         F_Mask/B_Mask  whole board open = NO solder mask [ASSUMED]
         F_Paste    0402 resistor lands (21 x 0402, 42 pads)
         Edge_Cuts  board outline
         PTH.drl    {nv} x d0.20 vias + {nm} x d2.40 M2 mounting holes, all plated through
Notes  : M2 holes are plated and tied to top pour and bottom ground. No silkscreen.
         Board fits housing {pn} (lid channel cage). Impedance-critical: 50 ohm microstrip, do not etch-compensate without asking.
""".format(name=NAME, w=max(xs) - min(xs), h=max(ys) - min(ys), nv=len(vhole), nm=len(mhole), pn=C.TEXT["pn"])
    with open(os.path.join(OUT, "README.txt"), "w", newline="\n") as fh: fh.write(readme)

    preview(os.path.join(OUT, "preview.png"))
    zpath = os.path.join(C.ROOT, "01_pcb_v3", NAME + "_gerber.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(OUT)):
            if f != "preview.png": z.write(os.path.join(OUT, f), f)
    return dict(dir=OUT, zip=zpath, vias=len(vhole), mount=len(mhole), pads=len(pads), tools=sorted(tools))


def preview(path):
    """Read the files back with gerbonara (independent parser) and plot copper + drills."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    import gerbonara as gb
    fig, axs = plt.subplots(1, 2, figsize=(14, 9))
    for ax, f, col in ((axs[0], "F_Cu", "#d08a2a"), (axs[1], "B_Cu", "#5a8a50")):
        lay = gb.GerberFile.open(os.path.join(OUT, "%s-%s.gbr" % (NAME, f)))
        for o in lay.objects:
            for p in o.to_primitives(gb.utils.MM):
                if isinstance(p, gb.graphic_primitives.ArcPoly):
                    ax.fill(*zip(*p.outline), color=col, lw=0)
                elif isinstance(p, gb.graphic_primitives.Circle):
                    ax.add_patch(Circle((p.x, p.y), p.r, color=col if f == "B_Cu" else "#b06a10", lw=0))
        ax.set_title("%s (read back with gerbonara)" % f); ax.set_aspect("equal")
    drl = gb.ExcellonFile.open(os.path.join(OUT, NAME + "-PTH.drl"))
    for o in drl.objects:
        axs[0].add_patch(Circle((o.x, o.y), o.tool.diameter / 2, color="k", lw=0))
    edge = gb.GerberFile.open(os.path.join(OUT, NAME + "-Edge_Cuts.gbr"))
    for ax in axs:
        for o in edge.objects:
            ax.plot([o.x1, o.x2], [o.y1, o.y2], "b", lw=0.8)
        ax.autoscale_view(); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


if __name__ == "__main__":
    r = build()
    print("Gerbers -> %s\n  zip %s\n  %d vias, %d M2 holes, %d paste pads, drill tools %s"
          % (r["dir"], r["zip"], r["vias"], r["mount"], r["pads"], r["tools"]))
