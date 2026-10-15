"""Build all DXFs (layered, silkscreen, assembly), previews, BOM, DRC, divider report for the 1-bit RBA pack.
    python build_rba.py  -> ../01_dxf
Layers: OUTLINE, ANT_OUTLINE (antenna-board edge on the larger feed board), M1, M2, M3 (ground), M3_SLOT (subtract),
        M4, VIA (spans in BOM/DRC: M2-M3 shorting pins, M3-M4 DC-return vias), NPTH (plastic-screw holes), PORT,
        SILK_M1 (top silk, antenna board), SILK_M4 (bottom silk, feed board = component side), ASSY_M4, FAB."""
import os, csv, json
import ezdxf
from shapely.geometry import MultiPolygon, box
from shapely.ops import unary_union
from shapely.affinity import rotate as srot
import rbageom as G

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "01_dxf"))
LAY = {"OUTLINE": 7, "ANT_OUTLINE": 8, "M1": 1, "M2": 30, "M3": 3, "M3_SLOT": 3, "M4": 5, "VIA": 6, "NPTH": 9,
       "PORT": 2, "SILK_M1": 7, "SILK_M4": 8, "ASSY_M4": 4, "FAB": 9}
FAB = ["ANTENNA BOARD: M1 | RT5880 0.508 | M2 | RT5880 0.254 | (bottom: pin pads only)  -> pins M2->M3 via pads pressed on M3",
       "FEED BOARD: M3 (GND + slots) | RO4003C 0.203 | M4 (lines, PIN diodes, bias)",
       "ALTERNATIVE (recommended): one laminated board, Sub.2 bonded to Sub.3 with thin bondply; plated pins M2->M3",
       "Cu 17 um (1/2 oz) or 9 um for 0.1 mm lines; ENIG; min line/space 0.10/0.10 mm; pins 0.2 mm drill"]

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]

def write(b, path, layers=None):
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4
    for n, c in LAY.items(): d.layers.add(n, color=c)
    m = d.modelspace(); keep = layers or list(LAY)
    for lay in ("OUTLINE", "ANT_OUTLINE", "M1", "M2", "M3", "M3_SLOT", "M4", "NPTH", "PORT", "SILK_M1", "SILK_M4"):
        if lay not in keep: continue
        g = unary_union(b.L.get(lay, []))
        if lay == "M3": g = g.difference(unary_union(b.L.get("M3_SLOT", []) + b.L.get("NPTH", [])))
        for p in polys(g):
            m.add_lwpolyline(list(p.exterior.coords)[:-1], close=True, dxfattribs={"layer": lay})
            for h in p.interiors: m.add_lwpolyline(list(h.coords)[:-1], close=True, dxfattribs={"layer": lay})
    if "VIA" in keep:
        for x, y, dd, span in b.vias: m.add_circle((x, y), dd / 2, dxfattribs={"layer": "VIA"})
    for (lay, s, x, y, h, rot, al) in b.txt:
        if lay in keep:
            t = m.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay}); t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment[al])
    if "ASSY_M4" in keep:
        for c in b.comp:
            x, y, w, h = c["x"], c["y"], c["w"], c["h"]
            m.add_lwpolyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], close=True, dxfattribs={"layer": "ASSY_M4"})
            t = m.add_text(c["ref"], height=0.15, dxfattribs={"layer": "ASSY_M4"}); t.set_placement((x, y + h / 2 + 0.12), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    if "FAB" in keep:
        bx = b.L["OUTLINE"][0].bounds
        for k, s in enumerate(FAB):
            t = m.add_text(s, height=0.5, dxfattribs={"layer": "FAB"}); t.set_placement((bx[2] + 2, bx[3] - 1.0 * k))
    d.saveas(path)

def preview(b, path, title):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ob = b.L["OUTLINE"][0].bounds; asp = (ob[3] - ob[1]) / (ob[2] - ob[0])
    panels = [("M1 patch + M2 strip + pins", ("M1", "M2")), ("M3 ground + slots", ("M3",)), ("M4 feed / switches / bias", ("M4",)), ("SILK M4 + assembly", ("SILK_M4",))]
    fig, ax = plt.subplots(1, 4, figsize=(18, 18 * asp / 4 + 1.0))
    col = {"M1": "#d9822b", "M2": "#8e44ad", "M3": "#7f8c8d", "M4": "#2e86c1"}
    for a_, (ttl, lays) in zip(ax, panels):
        a_.add_patch(plt.Polygon(list(b.L["OUTLINE"][0].exterior.coords), fc="#f4f1e8", ec="k", lw=0.8))
        for lay in lays:
            if lay == "SILK_M4":
                for p in polys(unary_union(b.L.get("M4", []))): a_.add_patch(plt.Polygon(list(p.exterior.coords), fc="#b9d4ea", ec="none"))
                for p in polys(unary_union(b.L.get("SILK_M4", []))): a_.add_patch(plt.Polygon(list(p.exterior.coords), fc="k", ec="none"))
                for (l, s, x, y, h, r, al) in b.txt:
                    if l == "SILK_M4": a_.text(x, y, s, fontsize=max(2.5, h * 9), ha="center", va="center")
                for c in b.comp: a_.add_patch(plt.Rectangle((c["x"] - c["w"] / 2, c["y"] - c["h"] / 2), c["w"], c["h"], fc="none", ec="r", lw=0.5))
                continue
            g = unary_union(b.L.get(lay, []))
            if lay == "M3": g = g.difference(unary_union(b.L.get("M3_SLOT", []) + b.L.get("NPTH", [])))
            for p in polys(g):
                a_.add_patch(plt.Polygon(list(p.exterior.coords), fc=col[lay], ec="none", alpha=0.85))
                for hh in p.interiors: a_.add_patch(plt.Polygon(list(hh.coords), fc="#f4f1e8", ec="none"))
        for x, y, dd, span in b.vias:
            if any(l in span for l in lays): a_.add_patch(plt.Circle((x, y), dd / 2, fc="yellow", ec="k", lw=0.2))
        if "ANT_OUTLINE" in b.L:
            for g in b.L["ANT_OUTLINE"]: a_.add_patch(plt.Polygon(list(g.exterior.coords), fc="none", ec="k", ls="--", lw=0.5))
        a_.set_xlim(ob[0] - 0.5, ob[2] + 0.5); a_.set_ylim(ob[1] - 0.5, ob[3] + 0.5); a_.set_aspect("equal"); a_.set_title(ttl, fontsize=9); a_.tick_params(labelsize=6)
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)

def drc(b, min_gap=0.10):
    rep = []
    for lay in ("M1", "M2", "M4"):
        ps = polys(unary_union(b.L.get(lay, [])))
        mg = min((ps[i].distance(ps[j]) for i in range(len(ps)) for j in range(i + 1, len(ps))), default=99)
        g = unary_union(b.L.get(lay, []))
        thin = g.difference(g.buffer(-0.049).buffer(0.049)).area if not g.is_empty else 0
        rep.append("%s: %d islands, min copper gap %.3f mm%s, area of features <0.10 mm wide: %.4f mm2" %
                   (lay, len(ps), mg, "  <-- below %.2f" % min_gap if mg < min_gap else "", thin))
    m4 = unary_union(b.L.get("M4", [])); sl = unary_union(b.L.get("M3_SLOT", []))
    rep.append("M4 copper crossing slots (should be only the loop top arms): %.3f mm2" % m4.intersection(sl).area)
    return rep

def main():
    os.makedirs(OUT, exist_ok=True)
    for s in ("A_element_alone", "B_array_without_divider", "C_array_with_divider", "D_split_boards_for_fab"): os.makedirs(os.path.join(OUT, s), exist_ok=True)
    bom, log = [], []
    jobs = [(G.board_element(), "A_element_alone", "RCSPA_element_10x10", "RCSPA 1-bit element (Fig.1) - single port"),
            (G.board_array(False), "B_array_without_divider", "RBA_1x5_5ports_32x12", "1x5 array, 5 ports (Fig.5) - port-level preload in simulation"),
            (G.board_array(True), "C_array_with_divider", "RBA_1x5_with_1to5_divider_preload", "1x5 array + 1:5 divider with fixed preload (Fig.6)")]
    for b, sub, name, title in jobs:
        p = os.path.join(OUT, sub, name)
        write(b, p + ".dxf"); preview(b, p + "_preview.png", title)
        log.append("== " + name); log += ["   " + r for r in drc(b)]
        bom += [[name, c["ref"], c["value"], c["side"], round(c["x"], 3), round(c["y"], 3), c["pin1"]] for c in b.comp]
        if hasattr(b, "divider_info"):
            info = b.divider_info
            with open(os.path.join(OUT, sub, "divider_design_table.csv"), "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["junction / branch", "power fraction", "Z quarter-wave (ohm)", "width (mm)", "length lambda_g/4 (mm)"]); w.writerows(info["table"])
                w.writerow([]); w.writerow(["element", "path length (mm)", "insertion phase (deg)", "target preload (deg)", "achieved preload (deg)"])
                for i in range(5): w.writerow([i + 1, round(info["path_len"][i], 3), round(info["insertion_phase"][i], 2), info["target_preload"][i], round(info["achieved_preload"][i], 2)])
            # split boards for the two-board build of the paper
            write(b, os.path.join(OUT, "D_split_boards_for_fab", "ANTENNA_BOARD_M1_M2_pins.dxf"), ["ANT_OUTLINE", "M1", "M2", "VIA", "NPTH", "SILK_M1", "FAB"])
            write(b, os.path.join(OUT, "D_split_boards_for_fab", "FEED_BOARD_M3_M4_divider.dxf"), ["OUTLINE", "M3", "M3_SLOT", "M4", "VIA", "NPTH", "PORT", "SILK_M4", "ASSY_M4", "FAB"])
    with open(os.path.join(OUT, "BOM_and_placement.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["board", "ref", "value", "side", "x_mm", "y_mm", "polarity"]); w.writerows(bom)
    with open(os.path.join(OUT, "DRC_report.txt"), "w") as fh: fh.write("\n".join(log))
    print("\n".join(log))

if __name__ == "__main__":
    main()
