"""openEMS: parametric version of the present element, for retuning the VSWR within the existing build.

Same stack-up as the board (cbgeom): ground / RT5880 0.8 mm / driven patch + feeds / air gap h / FR4 0.4 mm / parasitic.
Square driven patch L1, square parasitic L2, both centred. Dual-pol edge feeds: port 1 (V) from the -y edge,
port 2 (H) from the -x edge, each a 100-ohm line (0.73 mm) of length LF ending in a 100-ohm lumped port.
Optional inset depth `ins` (notch gap 0.5 mm each side) and optional matching section on the branch:
`wt`, `lt` = width / length of a series section right at the patch edge (0 = none), then the 100-ohm line.

usage:  python sim_tune.py --set "L1=17.07,L2=16.2,h=4" --tag t0 [--port 1|2] [--threads N] [--nf2ff]
"""
import os, argparse, json
import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import EPS0

P = dict(L1=17.07, L2=16.2, h=4.0, ins=0.0, wt=0.0, lt=0.0, wt2=0.0, lt2=0.0, LF=10.0, G=60.0, inf=1.0)
ap = argparse.ArgumentParser()
ap.add_argument('--set', default='')
ap.add_argument('--tag', default='t0')
ap.add_argument('--port', type=int, default=1)
ap.add_argument('--threads', type=int, default=4)
ap.add_argument('--res', type=float, default=0.3)
ap.add_argument('--nf2ff', action='store_true')
ap.add_argument('--nrts', type=int, default=40000)
a = ap.parse_args()
for kv in filter(None, a.set.split(',')):
    k, v = kv.split('='); P[k] = float(v)

H_SUB, ER, TD = 0.8, 2.2, 0.0004
H_FR4, ER4, TD4 = 0.4, 4.5, 0.02
W100 = 0.73
f0, fc = 5.5e9, 3.0e9
freq = np.linspace(3.5e9, 7.5e9, 401)
here = os.path.dirname(os.path.abspath(__file__))
sim = os.path.join(here, 'sim', a.tag); os.makedirs(sim, exist_ok=True)
res = os.path.join(here, '..', '03_results'); os.makedirs(res, exist_ok=True)

G = P['G'] / 2; h1 = P['L1'] / 2; h2 = P['L2'] / 2
# inf=1: ground, RT5880 and FR4 run into the PML, so the element sees an infinite ground like inside the array
# (a finite 60 mm ground has its own resonance near 4.5 GHz that is not there in the real board)
GB = G + 200 if P['inf'] else G
zf = H_SUB + P['h']; zp = zf + H_FR4

FDTD = openEMS(NrTS=a.nrts, EndCriteria=1e-4)
FDTD.SetGaussExcite(f0, fc); FDTD.SetBoundaryCond(['PML_8'] * 6)
CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
w = 2 * np.pi * f0 * EPS0
CSX.AddMaterial('RT5880', epsilon=ER, kappa=w * ER * TD).AddBox([-GB, -GB, 0], [GB, GB, H_SUB])
CSX.AddMaterial('FR4', epsilon=ER4, kappa=w * ER4 * TD4).AddBox([-GB, -GB, zf], [GB, GB, zp])
pec = CSX.AddMetal('PEC')
pec.AddBox([-GB, -GB, 0], [GB, GB, 0], priority=10)
pec.AddBox([-h1, -h1, H_SUB], [h1, h1, H_SUB], priority=10)
pec.AddBox([-h2, -h2, zp], [h2, h2, zp], priority=10)
cut = CSX.AddMaterial('cut', epsilon=ER)          # inset notches (priority above the patch)

lines_x, lines_y = [], []
def feed(axis, port_nr):
    """Feed from the negative edge along `axis` ('y' = V feed, 'x' = H feed)."""
    ins, wt, lt, wt2, lt2 = P['ins'], P['wt'], P['lt'], P['wt2'], P['lt2']
    e = -h1 + ins                                  # where the feed enters the copper
    segs = []                                      # (width, start, stop) along the axis, toward -
    pos = e
    if ins > 0:
        segs.append((W100 if wt <= 0 else wt, pos, -h1)); pos = -h1
    if wt > 0 and lt > 0:
        segs.append((wt, pos, pos - lt)); pos -= lt
    if wt2 > 0 and lt2 > 0:
        segs.append((wt2, pos, pos - lt2)); pos -= lt2
    segs.append((W100, pos, float(np.round(pos - P['LF'], 3)))); pos -= P['LF']
    pos = float(np.round(pos, 3))                  # the port must sit exactly on a mesh line (thin() rounds to 3 decimals)
    for wd, s0, s1 in segs:
        if axis == 'y':
            pec.AddBox([-wd / 2, s1, H_SUB], [wd / 2, s0, H_SUB], priority=12)
            lines_x.extend([-wd / 2, wd / 2]); lines_y.extend([s0, s1])
        else:
            pec.AddBox([s1, -wd / 2, H_SUB], [s0, wd / 2, H_SUB], priority=12)
            lines_y.extend([-wd / 2, wd / 2]); lines_x.extend([s0, s1])
    if ins > 0:
        wi = segs[0][0] / 2 + 0.5
        if axis == 'y':
            cut.AddBox([-wi, -h1, H_SUB], [wi, e, H_SUB], priority=11); lines_x.extend([-wi, wi])
        else:
            cut.AddBox([-h1, -wi, H_SUB], [e, wi, H_SUB], priority=11); lines_y.extend([-wi, wi])
    if axis == 'y':
        port = FDTD.AddLumpedPort(port_nr, 100, [-W100 / 2, pos, 0], [W100 / 2, pos, H_SUB], 'z', excite=1.0 if a.port == port_nr else 0, priority=5)
    else:
        port = FDTD.AddLumpedPort(port_nr, 100, [pos, -W100 / 2, 0], [pos, W100 / 2, H_SUB], 'z', excite=1.0 if a.port == port_nr else 0, priority=5)
    return port, pos
p1, y_end = feed('y', 1)
p2, x_end = feed('x', 2)

r = a.res
def lines(essential, grid, d=0.08):
    """Essential lines (edges, ports) are all kept; plain grid lines closer than d to one of them are dropped."""
    e = np.unique(np.round(essential, 3))
    g = [x for x in np.round(grid, 3) if np.min(np.abs(e - x)) >= d]
    return np.unique(np.r_[e, g])
grid = np.arange(-G, G + 1e-6, r)
ex = [-h1, h1, -h2, h2, -G, G, -G - 25, G + 25] + lines_x
ey = [-h1, h1, -h2, h2, -G, G, -G - 25, G + 25] + lines_y
zs = [-20, 0, H_SUB / 3, 2 * H_SUB / 3, H_SUB, zf, zp, zp + 25] + list(np.linspace(H_SUB, zf, 9))
mesh.AddLine('x', lines(ex, grid)); mesh.AddLine('y', lines(ey, grid)); mesh.AddLine('z', np.unique(np.round(zs, 3)))
mesh.SmoothMeshLines('x', 2.0, 1.3); mesh.SmoothMeshLines('y', 2.0, 1.3); mesh.SmoothMeshLines('z', 2.0, 1.3)
fz = np.array([4.9e9, 5.2e9, 5.5e9, 5.8e9, 6.1e9, 6.4e9])
nf2ff = FDTD.CreateNF2FFBox(frequency=fz) if a.nf2ff else None

FDTD.Run(sim, cleanup=True, verbose=0, numThreads=a.threads)
for p in (p1, p2):
    p.CalcPort(sim, freq, ref_impedance=100)
pe, po = (p1, p2) if a.port == 1 else (p2, p1)
sii = pe.uf_ref / pe.uf_inc; sji = po.uf_ref / pe.uf_inc; zin = pe.uf_tot / pe.if_tot
i, j = a.port, 3 - a.port
np.savetxt(os.path.join(res, f'{a.tag}_S.csv'),
           np.c_[freq / 1e9, 20 * np.log10(abs(sii)), 20 * np.log10(abs(sji)), zin.real, zin.imag],
           delimiter=',', header=f'f_GHz,S{i}{i}_dB(100ohm),S{j}{i}_dB,Re_Zin,Im_Zin', fmt='%.5f')
with open(os.path.join(res, f'{a.tag}_summary.txt'), 'w') as fh:
    fh.write(f'tuned element {a.tag}: port {a.port}, params {json.dumps(P)}\n')
    for band in ((4.9, 6.4), (4.0, 7.0)):
        m = (freq >= band[0] * 1e9) & (freq <= band[1] * 1e9); g = abs(sii[m]); v = (1 + g) / (1 - g)
        fh.write(f'{band[0]}-{band[1]} GHz: worst VSWR {v.max():.2f}, VSWR<=2 {(v <= 2).mean()*100:.0f} %, <=3 {(v <= 3).mean()*100:.0f} %, '
                 f'worst isolation {20*np.log10(abs(sji[m]).max()):.1f} dB\n')
    for f in np.arange(4.0, 7.01, 0.25):
        k = np.argmin(abs(freq - f * 1e9)); g = abs(sii[k])
        fh.write(f'{f:5.2f} GHz  S{i}{i} {20*np.log10(g):6.2f} dB  VSWR {(1+g)/(1-g):5.2f}  S{j}{i} {20*np.log10(abs(sji[k])):6.1f} dB  '
                 f'Zin {zin[k].real:6.1f}{zin[k].imag:+6.1f}j\n')
    if nf2ff is not None:
        nf = nf2ff.CalcNF2FF(sim, fz, [0.0], [0.0], center=[0, 0, H_SUB], outfile='nf2ff_bs.h5')
        Pinc = np.array([np.interp(f, freq, pe.P_inc) for f in fz])
        for k, f in enumerate(fz):
            U = float(np.squeeze(nf.E_norm[k])) ** 2 * float(np.squeeze(nf.r)) ** 2 / (2 * 376.73)
            fh.write(f'{f/1e9:4.1f} GHz  broadside realised gain {10*np.log10(4*np.pi*U/Pinc[k]):5.2f} dBi\n')
print(open(os.path.join(res, f'{a.tag}_summary.txt')).read())
