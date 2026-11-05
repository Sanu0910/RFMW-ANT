"""Board geometry, PCB v3 mounting holes, lid-cage channels and RF checks (pure data, no CAD).
Frame: x east, y north, origin at the board-outline centre; z = 0 on the base bottom (set in housing.py)."""
import math
import numpy as np
import ezdxf
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.affinity import translate
from shapely.prepared import prep
import config as C

C0 = 299.792458  # mm * GHz


def _poly(e):
    return Polygon([(p[0], p[1]) for p in e.get_points("xy")])


def read_board(path=C.PCB_DXF_IN):
    m = ezdxf.readfile(path).modelspace()
    outline = _poly(next(iter(m.query("LWPOLYLINE[layer=='BOARD_OUTLINE']"))))
    x0, y0, x1, y1 = outline.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sh = lambda g: translate(g, -cx, -cy)
    sig = unary_union([sh(_poly(e)) for e in m.query("LWPOLYLINE[layer=='TOP_COPPER']")])
    pour = unary_union([sh(_poly(e)) for e in m.query("LWPOLYLINE[layer=='TOP_GROUND_POUR']")])
    pads = [sh(_poly(e)) for e in m.query("LWPOLYLINE[layer=='RES_PADS_0402']")]
    vias = [(e.dxf.center.x - cx, e.dxf.center.y - cy, e.dxf.radius) for e in m.query("CIRCLE[layer=='VIA_PADS']")]
    drills = [(e.dxf.center.x - cx, e.dxf.center.y - cy, e.dxf.radius) for e in m.query("CIRCLE[layer=='VIA_HOLES']")]
    # ports: where the signal copper meets the west / east board edge
    sx0, _, sx1, _ = sig.bounds
    ports = []
    for xe, wall in ((sx0, "W"), (sx1, "E")):
        cut = sig.intersection(box(xe - 0.01, -1e3, xe + 0.01, 1e3))
        parts = list(cut.geoms) if hasattr(cut, "geoms") else [cut]
        for p in parts:
            b = p.bounds
            ports.append(dict(wall=wall, y=round((b[1] + b[3]) / 2, 4), w=round(b[3] - b[1], 4), x_cu=xe))
    west = [p for p in ports if p["wall"] == "W"]
    east = sorted([p for p in ports if p["wall"] == "E"], key=lambda p: -p["y"])     # 1 = north-most
    for p in west: p["label"] = "IN"
    for i, p in enumerate(east): p["label"] = str(i + 1)
    # resistor centres: 2 pads per resistor -> pair the nearest pads
    cen = [pd.centroid for pd in pads]; used = set(); res = []
    for i, a in enumerate(cen):
        if i in used: continue
        j = min((k for k in range(len(cen)) if k != i and k not in used), key=lambda k: a.distance(cen[k]))
        used |= {i, j}; b = cen[j]
        res.append(((a.x + b.x) / 2, (a.y + b.y) / 2, 0.0 if abs(a.x - b.x) > abs(a.y - b.y) else 90.0))
    return dict(outline=sh(outline), L=x1 - x0, W=y1 - y0, shift=(cx, cy), sig=sig, pour=pour, pads=pads,
                vias=vias, drills=drills, ports=west + east, res=res)


# ---------------- PCB v3 mounting holes ----------------
def place_holes(B):
    H = C.PCB_HOLES
    allowed = B["pour"].buffer(-(H["head_r"] + H["head_margin"])).intersection(B["outline"].buffer(-H["edge_min"]))
    A = prep(allowed)
    xs = np.arange(-B["L"] / 2, B["L"] / 2, 0.1); ys = np.arange(-B["W"] / 2, B["W"] / 2, 0.1)
    grid = np.array([(x, y) for x in xs[::2] for y in ys[::2]])
    ok = np.array([A.contains(Point(p)) for p in grid])
    G = grid[ok]
    holes = []

    def add(p, why):
        if all(math.dist(p, q[:2]) >= H["min_spacing"] for q in holes):
            holes.append((round(float(p[0]), 2), round(float(p[1]), 2), why))

    L2 = B["L"] / 2
    # 1. both sides of every launch, in a band 2.5..8 mm inside the connector edge, nearest to the line
    for p in B["ports"]:
        xe = -L2 if p["wall"] == "W" else L2; inward = 1 if p["wall"] == "W" else -1
        band = G[(np.abs(G[:, 0] - (xe + inward * H["launch_dx"])) < 2.0)]
        for s in (1, -1):
            side = band[(band[:, 1] - p["y"]) * s > 0]
            if len(side):
                d = np.abs(side[:, 1] - p["y"]) + 0.3 * np.abs(side[:, 0] - (xe + inward * H["launch_dx"]))
                add(side[np.argmin(d)], "launch %s" % p["label"])
    # 2. corners
    for cx_, cy_ in ((-L2, -B["W"] / 2), (L2, -B["W"] / 2), (L2, B["W"] / 2), (-L2, B["W"] / 2)):
        add(G[np.argmin(np.hypot(G[:, 0] - cx_, G[:, 1] - cy_))], "corner")
    # 3. fill: farthest point from the existing holes while that distance exceeds 28 mm
    while True:
        d = np.min(np.hypot(G[:, None, 0] - np.array([h[0] for h in holes])[None, :], G[:, None, 1] - np.array([h[1] for h in holes])[None, :]), axis=1)
        k = int(np.argmax(d))
        if d[k] < 28.0: break
        add(G[k], "field")
    return holes, allowed


def vias_after_holes(B, holes):
    """Vias (pad, drill) kept / removed for the v3 board."""
    H = C.PCB_HOLES; keep, removed = [], []
    for (x, y, r), (_, _, rd) in zip(B["vias"], B["drills"]):
        if any(math.hypot(x - hx, y - hy) < H["drill"] / 2 + H["via_clear"] + r for hx, hy, _w in holes):
            removed.append((x, y, r, rd))
        else:
            keep.append((x, y, r, rd))
    return keep, removed


# ---------------- lid cage ----------------
def cage_channels(B, cav_poly):
    """Channels milled into the cage block over the signal copper (walls wall_offset from the copper). Outside them
    the cage face (with the gasket) rests on the board: on the top-ground pour, or on bare laminate within the
    pour clearance (2.5 .. 4.2 mm from the copper)."""
    G = C.CAGE
    cu = unary_union([B["sig"]] + B["pads"])
    P = cu.buffer(G["wall_offset"], 64)
    P = P.intersection(cav_poly.buffer(1.0, join_style=2))          # runs out through the cage edge at the ports
    P = P.buffer(-G["tool_r"], 64).buffer(G["tool_r"], 64)          # reachable with the D2 end mill
    return P.simplify(0.005)                                        # 5 um chord tolerance keeps the CAD sketch small


def rib_on_pour_fraction(B, P, foot):
    """Share of the cage face (foot - channels) that lands on top ground copper."""
    face = foot.difference(P)
    return face.intersection(B["pour"]).area / face.area, face


def eps_eff_layered(h_air):
    h = C.BOARD["h"]
    return (h_air + h) / (h_air + h / C.BOARD["er"])


def channel_modes(P, n=8, step=0.25):
    """Lowest E-vertical (TM_z) modes of the channel network: -lap(Ez) = k^2 Ez, Ez = 0 on the metal walls.
    Returns [(f GHz air-filled, f with the layered PCB, x, y of the field peak)]."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    x0, y0, x1, y1 = P.bounds
    xs = np.arange(x0 + step / 2, x1, step); ys = np.arange(y0 + step / 2, y1, step)
    PP = prep(P)
    mask = np.array([[PP.contains(Point(x, y)) for x in xs] for y in ys])
    idx = -np.ones(mask.shape, int); idx[mask] = np.arange(mask.sum())
    rows, cols, vals = [], [], []
    ny, nx = mask.shape
    for j in range(ny):
        for i in range(nx):
            k = idx[j, i]
            if k < 0: continue
            rows.append(k); cols.append(k); vals.append(4.0)
            for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jj, ii = j + dj, i + di
                if 0 <= jj < ny and 0 <= ii < nx and idx[jj, ii] >= 0:
                    rows.append(k); cols.append(idx[jj, ii]); vals.append(-1.0)
    Lp = sp.csr_matrix((vals, (rows, cols))) / step ** 2
    w, v = sla.eigsh(Lp, k=n, sigma=0, which="LM")
    order = np.argsort(w); ee = eps_eff_layered(C.CAGE["ch_air"])
    out = []
    pts = np.argwhere(mask)
    for o in order:
        f = C0 * math.sqrt(w[o]) / (2 * math.pi)
        jj, ii = pts[np.argmax(np.abs(v[:, o]))]
        out.append((f, f / math.sqrt(ee), float(xs[ii]), float(ys[jj])))
    return out, ee
