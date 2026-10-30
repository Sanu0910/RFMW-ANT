"""Fix B on the real layout: new widths along the existing feed route of every element (no re-routing).

The as-built element (sim_element.py, tag element_air: row-1 element from the DXFs, port on the 0.73 mm branch at the
clip cut) is moved back to the patch edge along the drawn route: 0.73 mm (100 ohm) for D_LINE mm, then the 2.48 mm
(50 ohm) L-section for D_WIDE mm. New feed: section A (width wA, length a from the patch edge) and section B (wB, b)
laid along the same route, then the existing 0.73 mm line. Searched for the lowest worst VSWR over the band.

usage:  python fixb_design.py [--band 5.1 6.2]      (writes 03_results/fixb_design.txt / fixb_circuit_S.csv)
"""
import os, sys, json
import numpy as np
from scipy.optimize import differential_evolution
import tune_match as TM

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
D_WIDE, D_LINE = 8.51, 5.71          # route lengths patch edge -> end of 2.48 mm section -> clip cut (centreline, row 1 col 1, H feed)
AVAIL = 22.0                         # route length available for the two sections before the next junction
band = (5.1, 6.2)
if '--band' in sys.argv:
    i = sys.argv.index('--band'); band = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
WMIN = float(sys.argv[sys.argv.index('--wmin') + 1]) if '--wmin' in sys.argv else 0.0   # narrowest allowed line (mm)
ZMAX = min(150.0, TM.z_eeff(WMIN)[0]) if WMIN > 0 else 150.0

d = np.loadtxt(os.path.join(R, 'element_air_S.csv'), delimiter=',')
f = d[:, 0] * 1e9; z = d[:, 3] + 1j * d[:, 4]
z50 = TM.z_eeff(2.48)[0]
zedge = TM.line(TM.line(z, 100.0, -D_LINE, f), z50, -D_WIDE, f)
m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)


def resp(p, ff, ze):
    zA, a, zB, b = p
    return TM.line(TM.line(ze, zA, a, ff), zB, b, ff)


def cost(p):
    if p[1] + p[3] > AVAIL:
        return 10.0
    zz = resp(p, f[m], zedge[m]); return np.abs((zz - 100) / (zz + 100)).max()


r = differential_evolution(cost, [(40, ZMAX), (1, 16), (40, ZMAX), (1, 16)], seed=4, tol=1e-8, maxiter=400, polish=True)
zA, a, zB, b = r.x
g = np.abs((resp(r.x, f, zedge) - 100) / (resp(r.x, f, zedge) + 100)); v = (1 + g) / (1 - g)
g0 = 10 ** (d[:, 1] / 20); v0 = (1 + g0) / (1 - g0)
np.savetxt(os.path.join(R, 'fixb_circuit_S.csv'), np.c_[d[:, 0], 20 * np.log10(g)], delimiter=',', header='f_GHz,S11_dB(circuit, fix B on real route)', fmt='%.5f')
out = dict(band=band, zA=round(zA, 1), wA=round(TM.width(zA), 3), a=round(a, 2), zB=round(zB, 1), wB=round(TM.width(zB), 3), b=round(b, 2))
txt = (f'fix B on the real route, band {band[0]}-{band[1]} GHz, narrowest line allowed {WMIN:.2f} mm (Z <= {ZMAX:.0f} ohm)\n'
       f'  as built: worst VSWR {v0[m].max():.2f}; circuit with new sections: worst VSWR {v[m].max():.2f}, VSWR<=2 {(v[m] <= 2).mean()*100:.0f} %\n'
       f'  section A: {zA:.1f} ohm, width {TM.width(zA):.3f} mm, {a:.2f} mm from the patch edge along the route\n'
       f'  section B: {zB:.1f} ohm, width {TM.width(zB):.3f} mm, {b:.2f} mm, then the existing 0.73 mm line\n'
       f'  params {json.dumps(out)}\n')
for bb in ((4.9, 6.4), (5.0, 6.3)):
    mm = (f >= bb[0] * 1e9) & (f <= bb[1] * 1e9)
    txt += f'  {bb[0]}-{bb[1]} GHz: worst VSWR {v[mm].max():.2f} (as built {v0[mm].max():.2f})\n'
open(os.path.join(R, 'fixb_design.txt'), 'w').write(txt); print(txt)
