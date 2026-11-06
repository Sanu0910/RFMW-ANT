"""Gerber helpers: read a copper layer into shapely geometry (polarity applied in file order)."""
from gerbonara import GerberFile
import shapely.geometry as sg
import shapely.affinity as sa
from shapely.ops import unary_union


def prim_geo(pr):
    c = type(pr).__name__
    if c == "Circle":
        return sg.Point(pr.x, pr.y).buffer(pr.r, 24)
    if c in ("Line", "Arc"):
        return sg.LineString([(pr.x1, pr.y1), (pr.x2, pr.y2)]).buffer(pr.width / 2, 8)
    if c == "ArcPoly":
        return sg.Polygon(list(pr.outline)).buffer(0) if len(pr.outline) > 2 else None
    if c == "Rectangle":
        b = sg.box(pr.x - pr.w / 2, pr.y - pr.h / 2, pr.x + pr.w / 2, pr.y + pr.h / 2)
        return sa.rotate(b, pr.rotation, origin=(pr.x, pr.y), use_radians=True)
    return None


def layer_geo(path):
    """Union of dark primitives minus clear ones, applied batch-wise in file order."""
    res, batch, pol = sg.Polygon(), [], True
    for obj in GerberFile.open(path).objects:
        for pr in obj.to_primitives():
            g = prim_geo(pr)
            if g is None:
                continue
            if pr.polarity_dark != pol and batch:
                u = unary_union(batch)
                res = res.union(u) if pol else res.difference(u)
                batch = []
            pol = pr.polarity_dark
            batch.append(g)
    if batch:
        u = unary_union(batch)
        res = res.union(u) if pol else res.difference(u)
    return res
