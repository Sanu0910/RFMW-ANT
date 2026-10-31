"""Option 2 (fix B, wide): new widths on the first ~8 mm of every element feed, routing unchanged.

Writes 06_fixB/IN2_CU_fixB.dxf, F_CU_fixB.dxf (= F_CU.dxf, parasitics as drawn), GND.dxf (= GND.dxf),
fixB_check.txt and two before/after pictures.

From every patch edge where a feed enters, the feed centreline is traced along the drawn route (axis-aligned runs,
chamfered bends). The first a + b mm become section A (width wA, length a) and section B (wB, b) from
03_results/fixb_design.txt (fixb_design.py --wmin 0.73: no line narrower than the existing 0.73 mm). The old
2.48 mm section is always removed completely; where it was longer than a + b the gap is refilled with 0.73 mm line.

Checks: 72 feeds; connected copper pieces before = after (nothing opened or shorted); per feed, the smallest gap from
the new copper to any copper that is not its own route or patch (must be >= 0.2 mm).

    python fix_feeds.py        (after fixb_design.py --wmin 0.73)
"""
import os, re, json, shutil
import numpy as np
import ezdxf
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union, substring
import cbgeom as g

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '06_fixB'); os.makedirs(OUT, exist_ok=True)
R = os.path.join(HERE, '..', '03_results')
prm = json.loads(re.search(r'params (\{.*\})', open(os.path.join(R, 'fixb_design.txt')).read()).group(1))
wA, a, wB, b = prm['wA'], prm['a'], prm['wB'], prm['b']
W_LINE, MIN_GAP = 0.73, 0.2

L = g.layers(); drv = L['drv']
patches = [p for p in g.parts(drv.buffer(-3).buffer(3)) if p.area > 150]
pboxes = [box(*p.bounds) for p in patches]


def extent(pt, d, half=8.0):
    """Copper interval through pt perpendicular to unit vector d: (centre point, width), or (None, 0)."""
    n = np.array([-d[1], d[0]])
    seg = LineString([tuple(pt - n * half), tuple(pt + n * half)]).intersection(drv)
    for s in g.parts(seg):
        if s.geom_type == 'LineString' and s.distance(Point(pt)) < 1e-6:
            return np.array(s.interpolate(0.5, normalized=True).coords[0]), s.length
    return None, 0.0


def trace(start, d, length):
    """Follow the copper from start in direction d for `length` mm of route.
    Returns the straightened centreline and the route length where the 2.48 mm section ends."""
    pts = [np.array(start, float)]; pos = np.array(start, float); d = np.array(d, float); run = 0.0; step = 0.05
    wcur = extent(pos + d * 0.3, d)[1]; narrow_pt = None        # where the 2.48 mm section ends
    while run < length:
        nxt = pos + d * step; n = np.array([-d[1], d[0]])
        if drv.contains(Point(pos + d * 0.25)):
            c, w = extent(nxt, d)
            # stay on the strip centre; a much wider cross-section (or none, at a chamfer) is a bend: go straight
            if c is not None and w < 1.35 * wcur and abs(np.dot(c - nxt, n)) < 0.5 * wcur:
                nxt = nxt + n * np.dot(c - nxt, n); wcur = w
            run += np.linalg.norm(nxt - pos); pos = nxt
            if narrow_pt is None and run > 1.0 and wcur < 1.2:
                narrow_pt = pos.copy()
            continue
        # blocked: a narrower line straight ahead (possibly off-centre)?
        q = pos + d * 0.3
        seg = LineString([tuple(q - n * wcur / 2), tuple(q + n * wcur / 2)]).intersection(drv)
        cont = [s for s in g.parts(seg) if s.geom_type == 'LineString' and s.length > 0.3]
        if cont:
            cc = np.array(max(cont, key=lambda s: s.length).interpolate(0.5, normalized=True).coords[0])
            c2, w2 = extent(cc, d)
            if c2 is not None and w2 < 0.9 * wcur:
                pos = pos + n * np.dot(c2 - pos, n); wcur = w2
                if narrow_pt is None and wcur < 1.2:
                    narrow_pt = pos.copy()
                pts.append(pos.copy()); continue
        # else turn toward the side where the copper runs farther
        def reach(s):
            sg = LineString([tuple(pos), tuple(pos + s * 6.0)]).intersection(drv)
            return max((x.length for x in g.parts(sg) if x.distance(Point(pos)) < 1e-6), default=0.0)
        r1, r2 = reach(n), reach(-n)
        if max(r1, r2) < 1.5:
            raise RuntimeError('dead end at %s after %.2f mm of route (start %s)' % (pos, run, start))
        d = n if r1 > r2 else -n
        c, w = extent(pos + d * 1.8, d)                         # recentre on the new run, clear of the corner
        nn = np.array([-d[1], d[0]]); pos = pos + nn * np.dot(c - pos, nn); wcur = w
        pts.append(pos.copy())
        for _ in range(60):                                     # a chamfered outer corner can leave pos just outside
            if drv.contains(Point(pos + d * 0.25)):
                break
            pos = pos + d * 0.05; run += 0.05
    pts.append(pos.copy())
    # straighten: every run horizontal or vertical on the centre found at its start; corners where runs meet
    P = [p for i, p in enumerate(pts) if i == 0 or np.linalg.norm(p - pts[i - 1]) > 0.2]
    axes = ['h' if abs(q[0] - p[0]) >= abs(q[1] - p[1]) else 'v' for p, q in zip(P[:-1], P[1:])]
    offs = [p[1] if ax == 'h' else p[0] for p, ax in zip(P[:-1], axes)]
    out = [P[0].copy()]
    for k in range(len(axes) - 1):
        if axes[k] != axes[k + 1]:
            out.append(np.array([offs[k + 1], offs[k]]) if axes[k] == 'h' else np.array([offs[k], offs[k + 1]]))
    end = P[-1].copy()
    if axes[-1] == 'h':
        end[1] = offs[-1]
    else:
        end[0] = offs[-1]
    out.append(end)
    line = LineString([tuple(p) for p in out])
    # measure along the straightened route (the raw trace cuts corners and would end the removal too early)
    return line, (line.project(Point(narrow_pt)) if narrow_pt is not None else None)


# feed entries: copper just outside a patch edge
feeds = []
for pb in pboxes:
    x0, y0, x1, y1 = pb.bounds
    for p0, p1, nrm in (((x0, y0), (x0, y1), (-1, 0)), ((x1, y0), (x1, y1), (1, 0)), ((x0, y0), (x1, y0), (0, -1)), ((x0, y1), (x1, y1), (0, 1))):
        nrm = np.array(nrm, float)
        probe = LineString([tuple(np.array(p0) + nrm * 0.05), tuple(np.array(p1) + nrm * 0.05)]).intersection(drv)
        for s in g.parts(probe):
            if s.geom_type == 'LineString' and s.length > 1.0:
                feeds.append((np.array(s.interpolate(0.5, normalized=True).coords[0]) - nrm * 0.05, nrm, s.length))
print('feeds found:', len(feeds), '| entry widths', sorted({round(w, 2) for _, _, w in feeds}))

new_cu, feed_cu, corridor, paths = [], [], [], []
for c, nrm, w in feeds:
    path, run_narrow = trace(c, nrm, max(a + b, 14.0))
    L_rm = max(a + b, (run_narrow or 0) + 0.3)               # remove at least the whole old 2.48 mm section
    if os.environ.get('FIX_DEBUG') and Point(c).distance(Point(-25.93, 19.87)) < 1:
        print('DEBUG run_narrow', run_narrow, 'L_rm', L_rm, 'path', np.round(np.array(path.coords), 2).tolist(), 'len %.2f' % path.length)
    secs = [substring(path, 0, a).buffer(wA / 2, cap_style=2, join_style=2),
            substring(path, a, a + b).buffer(wB / 2, cap_style=2, join_style=2)]
    if L_rm > a + b + 0.01:
        secs.append(substring(path, a + b, L_rm).buffer(W_LINE / 2, cap_style=2, join_style=2))
    new_cu += secs; feed_cu.append(secs)
    corridor.append(substring(path, 0, L_rm).buffer(1.80, cap_style=2, join_style=2))
    paths.append(substring(path, 0, L_rm))
removed = drv.intersection(unary_union(corridor)).difference(unary_union(pboxes))
drv_new = unary_union([drv.difference(removed), unary_union(new_cu)]).buffer(-0.03, join_style=2).buffer(0.03, join_style=2)
drv_new = unary_union([q for q in g.parts(drv_new) if q.area > 0.01])     # opening + filter: no slivers

before, after = len(g.parts(drv)), len(g.parts(drv_new))
clear, where = 99.0, None
for (c, nrm, w), path, sec in zip(feeds, paths, feed_cu):
    own = min(pboxes, key=lambda pb: pb.distance(Point(c)))
    rest = drv_new.difference(unary_union([unary_union(sec).buffer(0.05), path.buffer(0.9), own.buffer(0.3)]))
    dmin = unary_union(sec).distance(rest)
    if dmin < clear:
        clear, where = dmin, np.round(c, 2)
ok = before == after and clear >= MIN_GAP
report = [f'Option 2 / fix B (wide): {len(feeds)} feeds; section A {wA:.3f} mm x {a:.2f} mm, section B {wB:.3f} mm x {b:.2f} mm, then the existing 0.73 mm line',
          f'connected copper pieces on In2.Cu: before {before}, after {after} ({"OK" if before == after else "CHANGED"})',
          f'smallest gap from new copper to other copper: {clear:.3f} mm at the feed starting {where} ({"OK" if clear >= MIN_GAP else "TOO SMALL"}, limit {MIN_GAP} mm)',
          'F.Cu (parasitics) and B.Cu (ground) unchanged', 'ALL CHECKS PASS' if ok else 'CHECK FAILED']


def write(geom, name):
    doc = ezdxf.new('R2004'); doc.header['$INSUNITS'] = 4; ms = doc.modelspace()
    for p in g.no_holes(geom):
        ms.add_lwpolyline(list(p.exterior.coords)[:-1], close=True, dxfattribs={'layer': 'cond'})
    doc.saveas(os.path.join(OUT, name))


write(drv_new, 'IN2_CU_fixB.dxf')
shutil.copy(os.path.join(g.INP, 'F_CU.dxf'), os.path.join(OUT, 'F_CU_fixB.dxf'))
shutil.copy(os.path.join(g.INP, 'GND.dxf'), os.path.join(OUT, 'GND.dxf'))
open(os.path.join(OUT, 'fixB_check.txt'), 'w').write('\n'.join(report) + '\n')
print('\n'.join(report))

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
for nm, (cx, cy) in (('fixB_element_layout.png', (-107.5, 104.5)), ('fixB_tightest_feed.png', tuple(where))):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.6))
    cl = box(cx - 17.5, cy - 15.5, cx + 17.5, cy + 15.5)
    for ax, geom, t in ((axs[0], drv, 'As built'), (axs[1], drv_new, 'Option 2 (fix B)')):
        for p in g.parts(geom.intersection(cl)):
            if p.geom_type == 'Polygon':
                ax.add_patch(MP(np.array(p.exterior.coords), fc='#c77d3a', ec='k', lw=0.4))
                for h in p.interiors:
                    ax.add_patch(MP(np.array(h.coords), fc='white', ec='k', lw=0.3))
        ax.set_xlim(cx - 17.5, cx + 17.5); ax.set_ylim(cy - 15.5, cy + 15.5); ax.set_aspect('equal'); ax.grid(alpha=0.3)
        ax.set_title(f'{t}: In2.Cu around ({cx:.1f}, {cy:.1f}) mm')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, nm), dpi=140); plt.close(fig)
if not ok:
    raise SystemExit('fix B layout check failed - see 06_fixB/fixB_check.txt')
