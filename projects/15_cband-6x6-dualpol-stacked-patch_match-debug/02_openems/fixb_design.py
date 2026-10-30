"""Option 2 / fix B: new widths along the existing feed route of every element (no re-routing), both feeds at once.

Starts from the as-built element on an infinite ground (sim_element_fix.py --variant asbuilt, tags
elemfix_asbuilt_p1 = H feed, elemfix_asbuilt_p2 = V feed; 100-ohm ports on the 0.73 mm lines at y = 87.5 mm).
Each feed is moved back to the patch edge along its drawn route (straightened centreline lengths, row 1 col 1):
0.73 mm (100 ohm) for D_LINE mm, then the 2.48 mm (50 ohm) section for D_WIDE mm. New feed: section A (wA, a from
the patch edge) and section B (wB, b) along the same route, then the existing 0.73 mm line. One set of widths for
both feeds: the worse of the two worst VSWRs over the band is minimised.
(The first version used the 60 mm-ground element_air model, whose ground-edge effects misled the design.)

usage:  python fixb_design.py [--band 5.1 6.2] [--wmin 0.73]   (writes 03_results/fixb_design.txt)
"""
import os, sys, json
import numpy as np
from scipy.optimize import differential_evolution
import tune_match as TM

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
FEEDS = {'H': ('elemfix_asbuilt_p1', 8.78, 19.46),     # tag, D_WIDE, D_LINE (mm)
         'V': ('elemfix_asbuilt_p2', 7.64, 15.32)}
AVAIL = 14.0                                          # route length used by the two sections, at most
band = (5.1, 6.2)
if '--band' in sys.argv:
    i = sys.argv.index('--band'); band = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
WMIN = float(sys.argv[sys.argv.index('--wmin') + 1]) if '--wmin' in sys.argv else 0.73
ZMAX = min(150.0, TM.z_eeff(WMIN)[0])
z50 = TM.z_eeff(2.48)[0]

data = {}
for k, (tag, dw, dl) in FEEDS.items():
    d = np.loadtxt(os.path.join(R, f'{tag}_S.csv'), delimiter=',')
    f = d[:, 0] * 1e9; z = d[:, 3] + 1j * d[:, 4]
    data[k] = (f, TM.line(TM.line(z, 100.0, -dl, f), z50, -dw, f), dl, d)


def gam(p, k, sel=None):
    """|Gamma| (100 ohm) after sections A and B, seen at the end of section B."""
    f, ze, dl, d = data[k]
    zz = TM.line(TM.line(ze, p[0], p[1], f), p[2], p[3], f)
    g = np.abs((zz - 100) / (zz + 100))
    return g if sel is None else g[sel]


def cost(p):
    if p[1] + p[3] > AVAIL:
        return 10.0
    worst = 0.0
    for k in data:
        f = data[k][0]; m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)
        worst = max(worst, gam(p, k, m).max())
    return worst


r = differential_evolution(cost, [(35, ZMAX), (0.5, 12), (35, ZMAX), (0.5, 12)], seed=4, tol=1e-9, maxiter=600, polish=True)
zA, a, zB, b = r.x
out = dict(band=band, zA=round(zA, 1), wA=round(TM.width(zA), 3), a=round(a, 2), zB=round(zB, 1), wB=round(TM.width(zB), 3), b=round(b, 2))
txt = f'fix B (option 2) for both feeds, band {band[0]}-{band[1]} GHz, narrowest line {WMIN:.2f} mm (Z <= {ZMAX:.0f} ohm), from the infinite-ground as-built model\n'
for k in data:
    f, ze, dl, d = data[k]
    g = gam(r.x, k); v = (1 + g) / (1 - g); g0 = 10 ** (d[:, 1] / 20); v0 = (1 + g0) / (1 - g0)
    for bb in (band, (4.9, 6.4)):
        m = (f >= bb[0] * 1e9) & (f <= bb[1] * 1e9)
        txt += f'  {k} feed {bb[0]}-{bb[1]} GHz: as built worst VSWR {v0[m].max():.2f} -> circuit {v[m].max():.2f} (VSWR<=2 {(v[m] <= 2).mean()*100:.0f} %)\n'
txt += (f'  section A: {zA:.1f} ohm, width {TM.width(zA):.3f} mm, {a:.2f} mm from the patch edge along the route\n'
        f'  section B: {zB:.1f} ohm, width {TM.width(zB):.3f} mm, {b:.2f} mm, then the existing 0.73 mm line\n'
        f'  params {json.dumps(out)}\n')
open(os.path.join(R, 'fixb_design.txt'), 'w').write(txt); print(txt)
