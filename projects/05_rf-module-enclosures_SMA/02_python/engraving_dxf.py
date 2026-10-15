"""Engraving artwork as DXF (exact glyph outlines from the same fonts) for the CNC engraving program.
    <PN>_LID_ENGRAVING.dxf   top view of the lid, origin = lid centre, plus the screw holes for registration
    <PN>_WALL_LABELS.dxf     one block per port label, origin = connector axis on the wall face (viewed from outside)"""
import os, math
import ezdxf
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from encl_config import BOX, CONN
import build_enclosures as BE

def glyph_polys(txt, h, font, x, y, align="center"):
    fp = FontProperties(fname=font)
    cap = TextPath((0, 0), "H", size=100, prop=fp).get_extents().height / 100.0
    tp = TextPath((0, 0), txt, size=h / cap, prop=fp)
    ext = tp.get_extents()
    dx = {"center": -ext.width / 2 - ext.x0, "left": -ext.x0, "right": -ext.x1}[align]
    out = []
    for poly in tp.to_polygons(closed_only=True):
        out.append([(px + dx + x, py + y) for px, py in poly])
    return out

def lid_layout(e):
    """Same layout rules as build_enclosures.engrave()."""
    B = BOX; b = e.b; keep = B["wall"] + 3.5; avail = e.Lo - 2 * (keep + 1.0)
    tl, h1 = BE.fit_lines(b["title"], 3.0, 1.8, avail, B["font_bold"])
    h2 = min(2.2, avail / BE.text_w("S/N ______  10.6-10.6 GHz", 1.0, B["font"]) * 0.98); g = 2.0
    lh = min(B["logo_h"], avail / BE.text_w(B["logo_text"], 1.0, B["font_bold"]) * 0.98)
    total = lh + g + len(tl) * h1 + (len(tl) - 1) * 1.2 + g + h2 + 1.6 + h2
    y = total / 2; rows = [(B["logo_text"], lh, B["font_bold"], y - lh)]
    y -= lh + g
    for line in tl:
        y -= h1; rows.append((line, h1, B["font_bold"], y)); y -= 1.2
    y += 1.2; y -= g + h2; rows.append(("P/N %s  REV A" % b["pn"], h2, B["font"], y))
    y -= 1.6 + h2; rows.append(("S/N ______  %.1f-%.1f GHz" % b["band"], h2, B["font"], y))
    return rows

def write(e, outdir):
    B = BOX; pn = e.b["pn"]
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace()
    for n, c in (("LID_OUTLINE", 7), ("ENGRAVE_0p3", 1), ("SCREW_HOLES", 3), ("LOGO_ZONE", 5), ("NOTES", 2)): d.layers.add(n, color=c)
    r = B["outer_r"]; L, W = e.Lo / 2, e.Wo / 2
    m.add_lwpolyline([(-L + r, -W), (L - r, -W), (L, -W + r), (L, W - r), (L - r, W), (-L + r, W), (-L, W - r), (-L, -W + r)], close=True, dxfattribs={"layer": "LID_OUTLINE"})
    for x, y in e.lid_screws: m.add_circle((x, y), B["lid_clear_d"] / 2, dxfattribs={"layer": "SCREW_HOLES"})
    rows = lid_layout(e)
    for txt, h, font, y in rows:
        for p in glyph_polys(txt, h, font, 0.0, y): m.add_lwpolyline(p, close=True, dxfattribs={"layer": "ENGRAVE_0p3"})
    lt, lh, lf, ly = rows[0]
    m.add_lwpolyline([(-B["logo_w"] / 2, ly), (B["logo_w"] / 2, ly), (B["logo_w"] / 2, ly + B["logo_h"]), (-B["logo_w"] / 2, ly + B["logo_h"])], close=True, dxfattribs={"layer": "LOGO_ZONE"})
    t = m.add_text("Engrave %.1f deep, D0.3-0.5 engraving cutter; LOGO_ZONE = %g x %g mm box for the supplied logo" % (B["engrave_depth"], B["logo_w"], B["logo_h"]), height=1.2, dxfattribs={"layer": "NOTES"})
    t.set_placement((-L, -W - 4))
    d.saveas(os.path.join(outdir, pn + "_LID_ENGRAVING.dxf"))
    # wall labels
    d = ezdxf.new("R2010"); d.units = ezdxf.units.MM; d.header["$INSUNITS"] = 4; m = d.modelspace(); d.layers.add("ENGRAVE_0p3", color=1); d.layers.add("FLANGE", color=8)
    for k, p in enumerate(e.ports):
        ox = k * 40.0
        m.add_lwpolyline([(ox - CONN["flange"] / 2, -CONN["flange"] / 2), (ox + CONN["flange"] / 2, -CONN["flange"] / 2), (ox + CONN["flange"] / 2, CONN["flange"] / 2), (ox - CONN["flange"] / 2, CONN["flange"] / 2)], close=True, dxfattribs={"layer": "FLANGE"})
        h = 2.5; w = BE.text_w(p["label"], h, B["font_bold"])
        for q in glyph_polys(p["label"], h, B["font_bold"], ox + CONN["flange"] / 2 + 1.2 + w / 2, -h / 2): m.add_lwpolyline(q, close=True, dxfattribs={"layer": "ENGRAVE_0p3"})
        t = m.add_text("%s - %s wall, origin = connector axis" % (p["label"], p["wall"]), height=1.0); t.set_placement((ox - 6, -9))
    d.saveas(os.path.join(outdir, pn + "_WALL_LABELS.dxf"))
