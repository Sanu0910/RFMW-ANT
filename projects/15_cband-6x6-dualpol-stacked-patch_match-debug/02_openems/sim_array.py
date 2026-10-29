"""openEMS: the complete 6x6 array (276.86 mm board) with both coax launches as 50-ohm ports.

Coarse model (0.5 mm in-plane cells) meant to give S11 / S22 / S21 and broadside realised gain
of the board as drawn.  Trace edges snap to the 0.5 mm grid, so the 0.73 mm (~100 ohm) lines are
modelled 0.5 or 1.0 mm wide: expect a few-percent frequency shift and +-1..2 dB on deep nulls,
not on the overall picture.

usage:  python sim_array.py --port 1|2 [--gap-er 1.0] [--tag name]
"""
import os, argparse
import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import EPS0
import cbgeom as g

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=1)
ap.add_argument('--gap-er', type=float, default=1.0)
ap.add_argument('--gap-tand', type=float, default=0.0)
ap.add_argument('--res', type=float, default=0.5)
ap.add_argument('--tag', default=None)
ap.add_argument('--post-only', action='store_true')
a = ap.parse_args()
tag = a.tag or f'array_p{a.port}'

f0, fc = 5.5e9, 3.0e9
freq = np.linspace(3.5e9, 7.5e9, 401)
here = os.path.dirname(os.path.abspath(__file__))
sim = os.path.join(here, 'sim', tag); os.makedirs(sim, exist_ok=True)
res = os.path.join(here, '..', '03_results'); os.makedirs(res, exist_ok=True)

L = g.layers()
P = g.find_ports(L['drv'])
B = 138.43

FDTD = openEMS(NrTS=80000, EndCriteria=10 ** (-35 / 10))
FDTD.SetGaussExcite(f0, fc)
FDTD.SetBoundaryCond(['PML_8'] * 6)
CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)

w = 2 * np.pi * f0 * EPS0
CSX.AddMaterial('RT5880', epsilon=g.ER_SUB, kappa=w * g.ER_SUB * g.TD_SUB).AddBox([-B, -B, 0], [B, B, g.H_SUB])
if a.gap_er != 1.0:
    CSX.AddMaterial('gap', epsilon=a.gap_er, kappa=w * a.gap_er * a.gap_tand).AddBox([-B, -B, g.H_SUB], [B, B, g.Z_FR4_BOT])
CSX.AddMaterial('FR4', epsilon=g.ER_FR4, kappa=w * g.ER_FR4 * g.TD_FR4).AddBox([-B, -B, g.Z_FR4_BOT], [B, B, g.Z_PAR])
pec = CSX.AddMetal('PEC')
pec.AddBox([-B, -B, 0], [B, B, 0], priority=10)
g.add_poly(pec, L['drv'], g.Z_DRV)
g.add_poly(pec, L['par'], g.Z_PAR)

ports = []
for k in (1, 2):
    x, (y0, y1) = P[k]['x'], P[k]['y']
    ports.append(FDTD.AddLumpedPort(k, 50, [x, y0, 0], [x, y1, g.H_SUB], 'z',
                                    excite=1.0 if k == a.port else 0, priority=5))

r = a.res
xs = list(np.arange(-B, B + 1e-6, r)) + [P[1]['x'], P[2]['x'], -B - 30, B + 30]
ys = list(np.arange(-B, B + 1e-6, r)) + list(P[1]['y']) + list(P[2]['y']) + [-B - 30, B + 30]
zs = [-30, 0, g.H_SUB / 2, g.H_SUB] + list(np.linspace(g.H_SUB, g.Z_FR4_BOT, 7)) + [g.Z_PAR, g.Z_PAR + 30]
def thin(v, d):
    v = np.unique(np.round(v, 3)); out = [v[0]]
    for t in v[1:]:
        if t - out[-1] >= d: out.append(t)
    return np.array(out)
mesh.AddLine('x', thin(xs, 0.2)); mesh.AddLine('y', thin(ys, 0.2)); mesh.AddLine('z', thin(zs, 0.05))
mesh.SmoothMeshLines('x', 4.0, 1.3); mesh.SmoothMeshLines('y', 4.0, 1.3); mesh.SmoothMeshLines('z', 4.0, 1.3)
nf2ff = FDTD.CreateNF2FFBox()

if not a.post_only:
    n = [len(mesh.GetLines(d)) for d in 'xyz']
    print('mesh', n, 'cells %.1f M' % (np.prod(n) / 1e6))
    FDTD.Run(sim, cleanup=True, verbose=1)

for p in ports:
    p.CalcPort(sim, freq, ref_impedance=50)
pe = ports[a.port - 1]; po = ports[2 - a.port]
sii = pe.uf_ref / pe.uf_inc
sji = po.uf_ref / pe.uf_inc
zin = pe.uf_tot / pe.if_tot

fz = np.array([4.5e9, 5.0e9, 5.5e9, 6.0e9, 6.5e9])
nf = nf2ff.CalcNF2FF(sim, fz, [0.0], [0.0], center=[0, 0, g.Z_DRV], outfile='nf2ff_broadside.h5')
Pinc = np.array([np.interp(f, freq, pe.P_inc) for f in fz])
Pacc = np.array([np.interp(f, freq, pe.P_acc) for f in fz])
U = np.array([float(np.squeeze(nf.E_norm[i])) ** 2 * float(np.squeeze(nf.r)) ** 2 / (2 * 376.73) for i in range(len(fz))])
Greal = 10 * np.log10(4 * np.pi * U / Pinc)
Gacc = 10 * np.log10(4 * np.pi * U / Pacc)

i, j = a.port, 3 - a.port
np.savetxt(os.path.join(res, f'{tag}_S.csv'),
           np.c_[freq / 1e9, 20 * np.log10(abs(sii)), 20 * np.log10(abs(sji)), zin.real, zin.imag],
           delimiter=',', header=f'f_GHz,S{i}{i}_dB,S{j}{i}_dB,Re_Zin,Im_Zin', fmt='%.5f')
with open(os.path.join(res, f'{tag}_summary.txt'), 'w') as fh:
    fh.write(f'array sim {tag}: port {a.port} excited, gap er={a.gap_er}, in-plane cell {r} mm\n')
    for f in np.arange(4.0, 7.01, 0.25):
        k = np.argmin(abs(freq - f * 1e9)); G = abs(sii[k])
        fh.write(f'{f:5.2f} GHz  S{i}{i} {20*np.log10(G):6.2f} dB  VSWR {(1+G)/(1-G):5.2f}  '
                 f'S{j}{i} {20*np.log10(abs(sji[k])):6.1f} dB  Zin {zin[k].real:6.1f}{zin[k].imag:+6.1f}j\n')
    for f, gr, ga in zip(fz, Greal, Gacc):
        fh.write(f'{f/1e9:4.1f} GHz  broadside realised gain {gr:5.2f} dBi   gain (accepted power) {ga:5.2f} dBi\n')
print(open(os.path.join(res, f'{tag}_summary.txt')).read())
