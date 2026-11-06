"""Engraving text as shapely regions from exact font outlines (from project 01's artwork.py, logo part removed)."""
from functools import reduce
from shapely.geometry import Polygon
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties


def _cap(fp):
    return TextPath((0, 0), "H", size=100, prop=fp).get_extents().height / 100.0


def text_regions(txt, h, font, x, y, align="center"):
    """Text at cap height h; (x, y) = baseline anchor. Even-odd glyph filling."""
    fp = FontProperties(fname=font)
    tp = TextPath((0, 0), txt, size=h / _cap(fp), prop=fp)
    ext = tp.get_extents()
    dx = {"center": -ext.width / 2 - ext.x0, "left": -ext.x0, "right": -ext.x1}[align]
    loops = [Polygon([(px + dx + x, py + y) for px, py in poly]).buffer(0) for poly in tp.to_polygons(closed_only=True) if len(poly) >= 3]
    loops = [l for l in loops if not l.is_empty]
    if not loops: return []
    g = reduce(lambda u, v: u.symmetric_difference(v), loops)
    return [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-4]
