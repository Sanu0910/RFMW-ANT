"""Engraving artwork as shapely regions: text from exact font outlines (from project 04) and the logo from its PNG
(contour trace, from project 02 covers.py)."""
from functools import reduce
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale, translate
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


def logo_regions(png, width, x, y, mirror=False, thr=170, tol=0.02):
    """Ink (blue mark + black text) of the logo PNG as regions, `width` mm wide, centred on (x, y)."""
    import contourpy
    a = np.asarray(Image.open(png).convert("RGB")).astype(float)
    ink = np.pad((a.min(axis=2) < thr).astype(float), 2)
    polys = []
    for pts, offs in zip(*contourpy.contour_generator(z=ink, fill_type="OuterOffset").filled(0.5, 2.0)):
        rings = [pts[offs[k]:offs[k + 1]] for k in range(len(offs) - 1)]
        if len(rings[0]) < 4: continue
        q = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if q.area > 4.0: polys.append(q)
    g = unary_union(polys)
    s_ = width / ink.shape[1]
    g = scale(g, -s_ if mirror else s_, -s_, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    g = translate(g, x - (x0 + x1) / 2, y - (y0 + y1) / 2).simplify(tol)
    return [r for r in (g.geoms if hasattr(g, "geoms") else [g]) if r.area > 1e-3]
