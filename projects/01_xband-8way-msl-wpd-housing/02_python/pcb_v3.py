"""PCB v3 = the customer's fab-ready DXF + M2 mounting holes (plated, in the ground pour) + the vias they displace removed.
Coordinates stay in the customer's frame (input port edge centre at 0,0), so the file drops into the same CAM flow.
    -> ../01_pcb_v3/Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady_V3.dxf, _V3_holes.csv, _V3_preview.png"""
import os, csv
import ezdxf
import config as C
import geom as G

OUT = os.path.join(C.ROOT, "01_pcb_v3")
NAME = "Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady_V3"


def build(B, holes):
    os.makedirs(OUT, exist_ok=True)
    cx, cy = B["shift"]
    keep, removed = G.vias_after_holes(B, holes)
    doc = ezdxf.readfile(C.PCB_DXF_IN); m = doc.modelspace()
    gone = {(round(x + cx, 3), round(y + cy, 3)) for x, y, r, rd in removed}
    n_del = 0
    for e in list(m.query("CIRCLE[layer=='VIA_PADS' | layer=='VIA_HOLES']")):
        if (round(e.dxf.center.x, 3), round(e.dxf.center.y, 3)) in gone:
            m.delete_entity(e); n_del += 1
    for name, col in (("MOUNT_HOLES_PTH", 1), ("MOUNT_HEAD_KEEPOUT", 6), ("FAB_NOTES", 2)):
        if name not in doc.layers: doc.layers.add(name, color=col)
    H = C.PCB_HOLES
    for x, y, why in holes:
        m.add_circle((x + cx, y + cy), H["drill"] / 2, dxfattribs={"layer": "MOUNT_HOLES_PTH"})
        m.add_circle((x + cx, y + cy), H["head_r"] + H["head_margin"], dxfattribs={"layer": "MOUNT_HEAD_KEEPOUT"})
    x0, y0, x1, y1 = B["outline"].bounds
    notes = ["V3 (%s): %d x M2 mounting holes added for the housing %s; %d vias removed (pad within %.2f mm of a hole)."
             % (C.TEXT["date"], len(holes), C.TEXT["pn"], len(removed), C.PCB_HOLES["via_clear"]),
             "MOUNT_HOLES_PTH: d%.2f mm FINISHED, plated through, connected to top pour and bottom ground. No solder mask on top/bottom within MOUNT_HEAD_KEEPOUT." % H["drill"],
             "Stack-up: RO4350B 0.762 mm (30 mil), 1 oz Cu both sides; bottom layer = solid ground (not drawn), ENIG or immersion silver.",
             "All other layers unchanged from Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady.dxf."]
    for k, s in enumerate(notes):
        t = m.add_text(s, height=1.2, dxfattribs={"layer": "FAB_NOTES"}); t.set_placement((x0 + cx, y0 + cy - 4 - 2.2 * k))
    path = os.path.join(OUT, NAME + ".dxf"); doc.saveas(path)
    with open(os.path.join(OUT, NAME + "_holes.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["hole", "x_mm (DXF frame)", "y_mm (DXF frame)", "finished_d_mm", "plated", "purpose"])
        for i, (x, y, why) in enumerate(holes):
            w.writerow(["H%d" % (i + 1), "%.3f" % (x + cx), "%.3f" % (y + cy), "%.2f" % H["drill"], "yes", "M2 hold-down / ground, %s" % why])
    preview(B, holes, keep, os.path.join(OUT, NAME + "_preview.png"))
    return dict(path=path, removed=len(removed), deleted_entities=n_del, kept=len(keep))


def preview(B, holes, keep, path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Circle
    cx, cy = B["shift"]
    fig, ax = plt.subplots(figsize=(8.5, 10.5))
    for g in (B["pour"].geoms if hasattr(B["pour"], "geoms") else [B["pour"]]):
        ax.add_patch(MP([(x + cx, y + cy) for x, y in g.exterior.coords], fc="#cfdcc6", ec="#5a8a50", lw=0.3))
    for g in (B["sig"].geoms if hasattr(B["sig"], "geoms") else [B["sig"]]):
        ax.add_patch(MP([(x + cx, y + cy) for x, y in g.exterior.coords], fc="#d08a2a", ec="k", lw=0.3))
    for x, y, r, rd in keep: ax.add_patch(Circle((x + cx, y + cy), r, fc="k", lw=0))
    H = C.PCB_HOLES
    for i, (x, y, why) in enumerate(holes):
        ax.add_patch(Circle((x + cx, y + cy), H["head_r"] + H["head_margin"], fc="none", ec="m", lw=0.8, ls="--"))
        ax.add_patch(Circle((x + cx, y + cy), H["drill"] / 2, fc="r", ec="r"))
        ax.text(x + cx + 2.8, y + cy + 1.2, "H%d" % (i + 1), color="r", fontsize=7, weight="bold")
    ax.add_patch(MP([(x + cx, y + cy) for x, y in B["outline"].exterior.coords], fill=False, ec="b", lw=1))
    ax.set_aspect("equal"); ax.autoscale_view(); ax.grid(alpha=0.25)
    ax.set_title("PCB V3: %d x M2 plated holes d%.1f (red) added in the ground pour, magenta = head keep-out" % (len(holes), H["drill"]), fontsize=9)
    ax.set_xlabel("x (mm, customer DXF frame)"); ax.set_ylabel("y (mm)")
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
