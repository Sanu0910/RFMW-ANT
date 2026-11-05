"""Engraving artwork as shapely regions: the BEL logo (vectorised from the PNG) and text (exact font outlines)."""
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale, translate
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import config as C


def logo_regions(width_mm, cx=0.0, cy=0.0, simplify=0.02):
    """Every coloured pixel (blue mark, black lettering) becomes engraved area. Returns (regions, height_mm)."""
    import contourpy
    a = np.asarray(Image.open(C.LOGO_PNG).convert("RGB")).astype(float)
    ink = (a.min(axis=2) < 170).astype(float)                      # white background -> 0, blue / black -> 1
    ink = np.pad(ink, 2)
    h_px, w_px = ink.shape
    gen = contourpy.contour_generator(z=ink, fill_type="OuterOffset")
    polys = []
    pts_list, offs_list = gen.filled(0.5, 2.0)
    for pts, offs in zip(pts_list, offs_list):
        rings = [pts[offs[k]:offs[k + 1]] for k in range(len(offs) - 1)]
        if len(rings[0]) < 4: continue
        p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if p.area > 4.0: polys.append(p)                            # drop specks < 2 x 2 px
    g = unary_union(polys)
    s = width_mm / w_px
    g = scale(g, s, -s, origin=(0, 0))                              # image y points down
    x0, y0, x1, y1 = g.bounds
    g = translate(g, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2).simplify(simplify)
    regs = [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-3]
    return regs, y1 - y0


def text_regions(txt, h, font, x, y, align="center"):
    """Text at cap height h; (x, y) = baseline anchor. Even-odd glyph filling."""
    from functools import reduce
    fp = FontProperties(fname=font)
    cap = TextPath((0, 0), "H", size=100, prop=fp).get_extents().height / 100.0
    tp = TextPath((0, 0), txt, size=h / cap, prop=fp)
    ext = tp.get_extents()
    dx = {"center": -ext.width / 2 - ext.x0, "left": -ext.x0, "right": -ext.x1}[align]
    loops = [Polygon([(px + dx + x, py + y) for px, py in poly]).buffer(0) for poly in tp.to_polygons(closed_only=True) if len(poly) >= 3]
    loops = [l for l in loops if not l.is_empty]
    if not loops: return []
    g = reduce(lambda u, v: u.symmetric_difference(v), loops)
    return [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-4]


def text_width(txt, h, font):
    fp = FontProperties(fname=font)
    cap = TextPath((0, 0), "H", size=100, prop=fp).get_extents().height / 100.0
    return TextPath((0, 0), txt, size=h / cap, prop=fp).get_extents().width


def min_feature(regs, tool_d):
    """Area share of the artwork that a cutter of diameter tool_d cannot reach (morphological opening)."""
    g = unary_union(regs)
    lost = g.difference(g.buffer(-tool_d / 2).buffer(tool_d / 2))
    return lost.area / g.area
