"""openEMS: row-1 / col-1 element cut out of the layer files, as built or with fix B (06_fixB), both feeds as ports.

Like sim_element.py, but the clip is larger so that the fix-B matching sections (21.9 mm of route) are fully inside;
both feeds are cut where they run vertically as 0.73 mm (100 ohm) lines at y = YCUT and end in 100-ohm ports.
Ground and laminates run into the PML (element on an infinite ground, as inside the array).

usage:  python sim_element_fix.py --variant asbuilt|fixB --port 1|2 [--threads N] [--nf2ff]
"""
import os, argparse
import numpy as np
from shapely.geometry import box, LineString
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import EPS0
import cbgeom as g

ap = argparse.ArgumentParser()
ap.add_argument('--variant', default='fixB')
ap.add_argument('--port', type=int, default=1)
ap.add_argument('--threads', type=int, default=4)
ap.add_argument('--res', type=float, default=0.3)
ap.add_argument('--nf2ff', action='store_true')
ap.add_argument('--par', type=float, default=0.0, help='parasitic patch size, mm (square about its centre); 0 = as drawn')
ap.add_argument('--gap', type=float, default=0.0, help='air gap In2.Cu -> FR4 sheet, mm; 0 = 4.0 as built')
ap.add_argument('--tag', default=None)
a = ap.parse_args()
tag = a.tag or f'elemfix_{a.variant}_p{a.port}'
if a.gap > 0:                                                    # spacer height only: FR4 + F.Cu move up/down
    g.Z_FR4_BOT = g.H_SUB + a.gap; g.Z_PAR = g.Z_FR4_BOT + g.H_FR4

f0, fc = 5.5e9, 3.0e9
freq = np.linspace(3.5e9, 7.5e9, 401)
CX, CY = -105.45, 107.25
CLIP = (-124.5, 87.5, -91.0, 118.0)
YCUT = CLIP[1]
here = os.path.dirname(os.path.abspath(__file__))
sim = os.path.join(here, 'sim', tag); os.makedirs(sim, exist_ok=True)
res = os.path.join(here, '..', '03_results')

L = g.layers(None if a.variant == 'asbuilt' else a.variant)
drv = L['drv'].intersection(box(*CLIP))
par = L['par'].intersection(box(CX - 15, CY - 15, CX + 15, CY + 15))
if a.par > 0:
    c0 = par.centroid; par = box(c0.x - a.par / 2, c0.y - a.par / 2, c0.x + a.par / 2, c0.y + a.par / 2)
cuts = [s for s in g.parts(LineString([(CLIP[0], YCUT + 1e-3), (CLIP[2], YCUT + 1e-3)]).intersection(drv)) if s.length > 0.3]
assert len(cuts) == 2 and all(abs(s.length - 0.73) < 0.05 for s in cuts), [round(s.length, 3) for s in cuts]
cuts.sort(key=lambda s: s.bounds[0])                         # left cut = H feed (port 1), right cut = V feed (port 2)

FDTD = openEMS(NrTS=60000, EndCriteria=1e-4)
FDTD.SetGaussExcite(f0, fc); FDTD.SetBoundaryCond(['PML_8'] * 6)
CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
w = 2 * np.pi * f0 * EPS0
X0, X1, Y0, Y1 = CLIP[0] - 12, CLIP[2] + 12, CLIP[1] - 12, CLIP[3] + 12
GB = 300
CSX.AddMaterial('RT5880', epsilon=g.ER_SUB, kappa=w * g.ER_SUB * g.TD_SUB).AddBox([CX - GB, CY - GB, 0], [CX + GB, CY + GB, g.H_SUB])
CSX.AddMaterial('FR4', epsilon=g.ER_FR4, kappa=w * g.ER_FR4 * g.TD_FR4).AddBox([CX - GB, CY - GB, g.Z_FR4_BOT], [CX + GB, CY + GB, g.Z_PAR])
pec = CSX.AddMetal('PEC')
pec.AddBox([CX - GB, CY - GB, 0], [CX + GB, CY + GB, 0], priority=10)
g.add_poly(pec, drv, g.Z_DRV)
g.add_poly(pec, par, g.Z_PAR)
ports = []
for k, s in enumerate(cuts, start=1):
    xa, xb = round(s.bounds[0], 3), round(s.bounds[2], 3)
    ports.append(FDTD.AddLumpedPort(k, 100, [xa, YCUT, 0], [xb, YCUT, g.H_SUB], 'z', excite=1.0 if a.port == k else 0, priority=5))

# mesh: essential lines (all copper vertices, ports) kept; regular grid fills in
ex, ey = [X0, X1, CX - 60, CX + 60], [Y0, Y1, CY - 60, CY + 60, YCUT]
for geom in (drv, par):
    for p in g.parts(geom):
        if p.geom_type == 'Polygon':
            xs, ys = p.exterior.coords.xy; ex += list(xs); ey += list(ys)
for s in cuts:
    ex += [s.bounds[0], s.bounds[2]]
def lines(ess, lo, hi, r, d=0.06):
    e = np.unique(np.round(ess, 3)); e = e[(e >= lo - 61) & (e <= hi + 61)]
    keep = [e[0]]
    for t in e[1:]:
        if t - keep[-1] >= d: keep.append(t)
    e = np.array(keep)
    grid = [x for x in np.round(np.arange(lo, hi, r), 3) if np.min(np.abs(e - x)) >= d]
    return np.unique(np.r_[e, grid])
mesh.AddLine('x', lines(ex, X0, X1, a.res)); mesh.AddLine('y', lines(ey, Y0, Y1, a.res))
mesh.AddLine('z', np.unique(np.round([-20, 0, g.H_SUB / 3, 2 * g.H_SUB / 3, g.H_SUB] + list(np.linspace(g.H_SUB, g.Z_FR4_BOT, 9))
                                     + [g.Z_PAR, g.Z_PAR + 25], 3)))
mesh.AddLine('x', [CX - 60, CX + 60]); mesh.AddLine('y', [CY - 60, CY + 60])
mesh.SmoothMeshLines('x', 2.0, 1.3); mesh.SmoothMeshLines('y', 2.0, 1.3); mesh.SmoothMeshLines('z', 2.0, 1.3)
fz = np.array([4.9e9, 5.2e9, 5.5e9, 5.8e9, 6.1e9, 6.4e9])
nf2ff = FDTD.CreateNF2FFBox(frequency=fz) if a.nf2ff else None

FDTD.Run(sim, cleanup=True, verbose=0, numThreads=a.threads)
for p in ports:
    p.CalcPort(sim, freq, ref_impedance=100)
pe, po = ports[a.port - 1], ports[2 - a.port]
sii = pe.uf_ref / pe.uf_inc; sji = po.uf_ref / pe.uf_inc; zin = pe.uf_tot / pe.if_tot
i, j = a.port, 3 - a.port
np.savetxt(os.path.join(res, f'{tag}_S.csv'), np.c_[freq / 1e9, 20 * np.log10(abs(sii)), 20 * np.log10(abs(sji)), zin.real, zin.imag],
           delimiter=',', header=f'f_GHz,S{i}{i}_dB(100ohm),S{j}{i}_dB,Re_Zin,Im_Zin', fmt='%.5f')
with open(os.path.join(res, f'{tag}_summary.txt'), 'w') as fh:
    fh.write(f'element from layer files, variant {a.variant}, port {a.port} ({"H feed" if a.port == 1 else "V feed"}), Zref 100\n')
    for band in ((4.9, 6.4), (5.1, 6.2), (5.2, 6.1)):
        m = (freq >= band[0] * 1e9) & (freq <= band[1] * 1e9); gm = abs(sii[m]); v = (1 + gm) / (1 - gm)
        fh.write(f'{band[0]}-{band[1]} GHz: worst VSWR {v.max():.2f}, VSWR<=2 {(v <= 2).mean()*100:.0f} %, <=3 {(v <= 3).mean()*100:.0f} %, '
                 f'worst coupling {20*np.log10(abs(sji[m]).max()):.1f} dB\n')
    if nf2ff is not None:
        nf = nf2ff.CalcNF2FF(sim, fz, [0.0], [0.0], center=[CX, CY, g.Z_DRV], outfile='nf2ff_bs.h5')
        Pinc = np.array([np.interp(f, freq, pe.P_inc) for f in fz])
        for k, f in enumerate(fz):
            U = float(np.squeeze(nf.E_norm[k])) ** 2 * float(np.squeeze(nf.r)) ** 2 / (2 * 376.73)
            fh.write(f'{f/1e9:4.1f} GHz  broadside realised gain {10*np.log10(4*np.pi*U/Pinc[k]):5.2f} dBi\n')
print(open(os.path.join(res, f'{tag}_summary.txt')).read())
