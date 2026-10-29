"""openEMS: one stacked-patch element cut out of the array, both feeds as ports.

The element (row 1, col 1, patch centre (-105.45, 107.25)) is clipped out of IN2_CU together with
its two edge-feed stubs, up to where each stub becomes a 0.73 mm (~100 ohm) branch line.
Each branch is cut and terminated in a 100-ohm lumped port, so S11/S22 here are the reflections
each element sends back into its own branch of the corporate network (|S11| is invariant along
the lossless 100-ohm line, so the cut position does not matter for the magnitude).

usage:  python sim_element.py [--gap-er 1.0] [--tag name] [--no-par] [--plot-only]
"""
import os, sys, argparse
import numpy as np
from shapely.geometry import box
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import EPS0, C0
import cbgeom as g

ap = argparse.ArgumentParser()
ap.add_argument('--gap-er', type=float, default=1.0, help='permittivity of the 4 mm gap (1.0 = air)')
ap.add_argument('--gap-tand', type=float, default=0.0)
ap.add_argument('--no-par', action='store_true', help='remove the parasitic patch + FR4')
ap.add_argument('--tag', default='element_air')
ap.add_argument('--plot-only', action='store_true')
ap.add_argument('--par-scale', type=float, default=1.0, help='scale the parasitic patch about its centre')
ap.add_argument('--threads', type=int, default=0)
a = ap.parse_args()

f0, fc = 5.5e9, 3.0e9
freq = np.linspace(3.5e9, 7.5e9, 401)
CX, CY = -105.45, 107.25
CLIP = (-121.0, 93.0, -96.0, 118.0)
GND_HALF = 30.0
ZREF = 100.0
sim = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sim', a.tag)
os.makedirs(sim, exist_ok=True)
res = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
os.makedirs(res, exist_ok=True)

L = g.layers()
drv = L['drv'].intersection(box(*CLIP))
par = L['par'].intersection(box(CX - 15, CY - 15, CX + 15, CY + 15))
if a.par_scale != 1.0:
    from shapely import affinity
    par = affinity.scale(par, a.par_scale, a.par_scale, origin='centroid')

# port faces at the two clip cuts
def cut(x):
    s = drv.intersection(box(x - 0.01, CLIP[1], x + 0.01, CLIP[3]))
    return s.bounds[1], s.bounds[3]
pL, pB = cut(CLIP[0]), cut(CLIP[2])

FDTD = openEMS(NrTS=60000, EndCriteria=1e-5)
FDTD.SetGaussExcite(f0, fc)
FDTD.SetBoundaryCond(['PML_8'] * 6)
CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(1e-3)

w = 2 * np.pi * f0 * EPS0
sub = CSX.AddMaterial('RT5880', epsilon=g.ER_SUB, kappa=w * g.ER_SUB * g.TD_SUB)
sub.AddBox([CX - GND_HALF, CY - GND_HALF, 0], [CX + GND_HALF, CY + GND_HALF, g.H_SUB])
if a.gap_er != 1.0:
    gap = CSX.AddMaterial('gap', epsilon=a.gap_er, kappa=w * a.gap_er * a.gap_tand)
    gap.AddBox([CX - GND_HALF, CY - GND_HALF, g.H_SUB], [CX + GND_HALF, CY + GND_HALF, g.Z_FR4_BOT])
if not a.no_par:
    fr4 = CSX.AddMaterial('FR4', epsilon=g.ER_FR4, kappa=w * g.ER_FR4 * g.TD_FR4)
    fr4.AddBox([CX - GND_HALF, CY - GND_HALF, g.Z_FR4_BOT], [CX + GND_HALF, CY + GND_HALF, g.Z_PAR])
pec = CSX.AddMetal('PEC')
pec.AddBox([CX - GND_HALF, CY - GND_HALF, 0], [CX + GND_HALF, CY + GND_HALF, 0], priority=10)
g.add_poly(pec, drv, g.Z_DRV)
if not a.no_par:
    g.add_poly(pec, par, g.Z_PAR)

p1 = FDTD.AddLumpedPort(1, ZREF, [CLIP[0], pL[0], 0], [CLIP[0], pL[1], g.H_SUB], 'z', excite=1.0, priority=5)
p2 = FDTD.AddLumpedPort(2, ZREF, [CLIP[2], pB[0], 0], [CLIP[2], pB[1], g.H_SUB], 'z', excite=0, priority=5)

# mesh: 0.25 mm in-plane over the element, edges of all copper snapped
res_xy = 0.25
xs = list(np.arange(CX - GND_HALF, CX + GND_HALF + 1e-6, 1.0))
ys = list(np.arange(CY - GND_HALF, CY + GND_HALF + 1e-6, 1.0))
for geom in (drv, par):
    for p in g.parts(geom):
        bx = p.exterior.coords.xy
        xs += list(bx[0]); ys += list(bx[1])
xs += [CLIP[0], CLIP[2], CX - GND_HALF - 25, CX + GND_HALF + 25]
ys += list(pL) + list(pB) + [CY - GND_HALF - 25, CY + GND_HALF + 25]
zs = [-20, 0, g.H_SUB, g.Z_FR4_BOT, g.Z_PAR, g.Z_PAR + 25]
zs += list(np.linspace(0, g.H_SUB, 5)) + list(np.linspace(g.H_SUB, g.Z_FR4_BOT, 9)) + list(np.linspace(g.Z_FR4_BOT, g.Z_PAR, 3))
xs = np.unique(np.round(xs, 3)); ys = np.unique(np.round(ys, 3))
# drop lines closer than 0.08 mm (DXF vertices that almost coincide)
def thin(v, d=0.08):
    out = [v[0]]
    for t in v[1:]:
        if t - out[-1] >= d:
            out.append(t)
    return np.array(out)
mesh.AddLine('x', thin(xs)); mesh.AddLine('y', thin(ys)); mesh.AddLine('z', np.unique(np.round(zs, 4)))
mesh.SmoothMeshLines('x', res_xy * 2, 1.4)
mesh.SmoothMeshLines('y', res_xy * 2, 1.4)
mesh.SmoothMeshLines('z', 2.0, 1.4)

nf2ff = FDTD.CreateNF2FFBox()

if not a.plot_only:
    print('mesh cells', len(mesh.GetLines('x')), len(mesh.GetLines('y')), len(mesh.GetLines('z')))
    FDTD.Run(sim, cleanup=True, verbose=1, numThreads=a.threads)

p1.CalcPort(sim, freq, ref_impedance=ZREF)
p2.CalcPort(sim, freq, ref_impedance=ZREF)
s11 = p1.uf_ref / p1.uf_inc
s21 = p2.uf_ref / p1.uf_inc
zin = p1.uf_tot / p1.if_tot
# second run is needed for S22; by symmetry of the edge feeds we only report port-1 quantities here
fz = np.array([5.0e9, 5.5e9, 6.0e9, 6.5e9])
nf = nf2ff.CalcNF2FF(sim, fz, [0.0], [0.0], center=[CX, CY, g.Z_DRV], outfile='nf2ff_broadside.h5')
Pin = np.array([np.interp(f, freq, np.real(0.5 * p1.uf_tot * np.conj(p1.if_tot))) for f in fz])
Pinc = np.array([np.interp(f, freq, p1.P_inc) for f in fz])
Z0 = 376.73
U = np.array([float(np.squeeze(nf.E_norm[i])) ** 2 * float(np.squeeze(nf.r)) ** 2 / (2 * Z0) for i in range(len(fz))])
G_real = 10 * np.log10(4 * np.pi * U / Pinc)       # realised gain (includes mismatch)
D = 10 * np.log10(4 * np.pi * U / Pin)             # gain w.r.t. accepted power (~directivity, lossless)

np.savetxt(os.path.join(res, f'{a.tag}_S.csv'),
           np.c_[freq / 1e9, 20 * np.log10(abs(s11)), 20 * np.log10(abs(s21)), zin.real, zin.imag],
           delimiter=',', header='f_GHz,S11_dB(100ohm),S21_dB,Re_Zin,Im_Zin', fmt='%.5f')
with open(os.path.join(res, f'{a.tag}_summary.txt'), 'w') as fh:
    fh.write(f'element sim {a.tag}: gap er={a.gap_er}, parasitic={not a.no_par}, par scale={a.par_scale}, Zref={ZREF}\n')
    for f in (4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0):
        i = np.argmin(abs(freq - f * 1e9))
        G = abs(s11[i]); vswr = (1 + G) / (1 - G)
        fh.write(f'{f:4.1f} GHz  S11 {20*np.log10(G):6.2f} dB  VSWR {vswr:5.2f}  S21 {20*np.log10(abs(s21[i])):6.1f} dB  Zin {zin[i].real:7.1f}{zin[i].imag:+7.1f}j\n')
    for f, d, gr in zip(fz, D, G_real):
        fh.write(f'{f/1e9:4.1f} GHz  broadside G(accepted) {d:5.2f} dBi  realised G {gr:5.2f} dBi\n')
print(open(os.path.join(res, f'{a.tag}_summary.txt')).read())
