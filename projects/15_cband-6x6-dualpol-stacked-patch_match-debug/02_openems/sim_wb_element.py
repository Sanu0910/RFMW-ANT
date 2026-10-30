"""openEMS: proposed wideband replacement element - dual-pol aperture-coupled stacked patch.

Stack-up (bottom -> top), z = 0 on the slotted ground:
    feed lines (50 ohm, 2.48 mm)           z = -0.8   on the underside of RT5880 0.8 mm (same laminate as now)
    RT5880 0.8 mm, er 2.2                  z = -0.8 .. 0
    ground with two orthogonal slots       z = 0
    air gap h1                             z = 0 .. h1
    driven patch Lp1 (PEC sheet)           z = h1        [ASSUMED] printed on a thin carrier, carrier ignored
    air gap h2
    parasitic patch Lp2 on FR4 0.4 mm      z = h1 + h2 + 0.4 (copper on top of the FR4, as the present F.Cu)

Slots ("T" arrangement, so the two slots never cross):
    port 1 / V-pol: slot long in x, centred at (0, 0); feed line along y from -y, open stub Lst past the slot
    port 2 / H-pol: slot long in y, centred at (0, yH); feed line along x from -x, open stub Lst past the slot
The H-slot is offset along its own length, where the x-directed patch current is nearly uniform.
--single drops the H slot and port 2 (single-polarised check).

usage:  python sim_wb_element.py [--port 1|2] [--tag name] [--set Lp1=14,h1=3 ...] [--threads N]
"""
import os, argparse, json
import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import EPS0

P = dict(Lp1=15.0, Lp2=19.0, h1=3.0, h2=5.0, Ls=14.0, Ws=1.2, Lst=4.0, yH=9.0, Ls2=12.0, G=60.0, dp=1.0)

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=1)
ap.add_argument('--single', action='store_true')
ap.add_argument('--set', default='', help='comma list k=v overriding the defaults in P')
ap.add_argument('--tag', default=None)
ap.add_argument('--threads', type=int, default=0)
ap.add_argument('--no-nf2ff', action='store_true')
ap.add_argument('--res', type=float, default=0.4)
ap.add_argument('--nrts', type=int, default=25000)
a = ap.parse_args()
for kv in filter(None, a.set.split(',')):
    k, v = kv.split('='); P[k] = float(v)
tag = a.tag or f'wb_p{a.port}'

f0, fc = 5.5e9, 3.0e9
freq = np.linspace(3.5e9, 7.5e9, 401)
here = os.path.dirname(os.path.abspath(__file__))
sim = os.path.join(here, 'sim', tag); os.makedirs(sim, exist_ok=True)
res = os.path.join(here, '..', '03_results'); os.makedirs(res, exist_ok=True)

HF, WF, ER, TD = 0.8, 2.48, 2.2, 0.0004
H_FR4, ER_FR4, TD_FR4 = 0.4, 4.5, 0.02
G = P['G'] / 2
z1 = P['h1']; zf = z1 + P['h2']; z2 = zf + H_FR4

FDTD = openEMS(NrTS=a.nrts, EndCriteria=1e-4)
FDTD.SetGaussExcite(f0, fc)
FDTD.SetBoundaryCond(['PML_8'] * 6)
CSX = ContinuousStructure(); FDTD.SetCSX(CSX)
mesh = CSX.GetGrid(); mesh.SetDeltaUnit(1e-3)
w = 2 * np.pi * f0 * EPS0

CSX.AddMaterial('RT5880', epsilon=ER, kappa=w * ER * TD).AddBox([-G, -G, -HF], [G, G, 0])
CSX.AddMaterial('FR4', epsilon=ER_FR4, kappa=w * ER_FR4 * TD_FR4).AddBox([-G, -G, zf], [G, G, z2])
pec = CSX.AddMetal('PEC')
pec.AddBox([-G, -G, 0], [G, G, 0], priority=10)
air = CSX.AddMaterial('slot', epsilon=1.0)          # slots cut out of the ground (higher priority)
Ls, Ws = P['Ls'], P['Ws']
air.AddBox([-Ls / 2, -Ws / 2, 0], [Ls / 2, Ws / 2, 0], priority=20)
dual = not a.single
if dual:
    L2, yH = P['Ls2'], P['yH']
    air.AddBox([-Ws / 2, yH - L2 / 2, 0], [Ws / 2, yH + L2 / 2, 0], priority=20)
h = P['Lp1'] / 2; pec.AddBox([-h, -h, z1], [h, h, z1], priority=10)
h = P['Lp2'] / 2; pec.AddBox([-h, -h, z2], [h, h, z2], priority=10)

# feed lines on the underside, open stubs Lst past the slot centre lines
# dp: distance of the lumped port from the ground edge; for dp > 1 the line starts at the port
yp = -G + P['dp']
pec.AddBox([-WF / 2, -G if P['dp'] <= 1 else yp, -HF], [WF / 2, P['Lst'], -HF], priority=10)
ports = [FDTD.AddLumpedPort(1, 50, [-WF / 2, yp, -HF], [WF / 2, yp, 0], 'z',
                            excite=1.0 if a.port == 1 else 0, priority=5)]
if dual:
    pec.AddBox([-G if P['dp'] <= 1 else yp, yH - WF / 2, -HF], [P['Lst'], yH + WF / 2, -HF], priority=10)
    ports.append(FDTD.AddLumpedPort(2, 50, [yp, yH - WF / 2, -HF], [yp, yH + WF / 2, 0], 'z',
                                    excite=1.0 if a.port == 2 else 0, priority=5))

r = a.res
xs = [-G, G, -WF / 2, WF / 2, -Ls / 2, Ls / 2, -Ws / 2, Ws / 2, P['Lst'], yp,
      -P['Lp1'] / 2, P['Lp1'] / 2, -P['Lp2'] / 2, P['Lp2'] / 2, -G - 25, G + 25]
ys = list(xs)
if dual:
    ys += [yH - WF / 2, yH + WF / 2, yH - L2 / 2, yH + L2 / 2]
zs = [-HF - 20, -HF, -HF / 2, 0, z1, zf, z2, z2 + 25] + list(np.linspace(0, z1, 6)) + list(np.linspace(z1, zf, 8))
def thin(v, d):
    v = np.unique(np.round(v, 3)); out = [v[0]]
    for t in v[1:]:
        if t - out[-1] >= d: out.append(t)
    return np.array(out)
# fine (r) over the board, growing to 2 mm (lambda/20 at 7.5 GHz) in the surrounding air
xs += list(np.arange(-G, G + 1e-6, r)); ys += list(np.arange(-G, G + 1e-6, r))
mesh.AddLine('x', thin(xs, 0.1)); mesh.AddLine('y', thin(ys, 0.1)); mesh.AddLine('z', thin(zs, 0.1))
mesh.SmoothMeshLines('x', 2.0, 1.3); mesh.SmoothMeshLines('y', 2.0, 1.3); mesh.SmoothMeshLines('z', 2.0, 1.3)
fz = np.array([4.0e9, 4.5e9, 5.0e9, 5.5e9, 6.0e9, 6.5e9, 7.0e9])
nf2ff = None if a.no_nf2ff else FDTD.CreateNF2FFBox(frequency=fz)

n = [len(mesh.GetLines(d)) for d in 'xyz']
print('mesh', n, 'cells %.2f M' % (np.prod(n) / 1e6), json.dumps(P))
FDTD.Run(sim, cleanup=True, verbose=0, numThreads=a.threads)

for p in ports:
    p.CalcPort(sim, freq, ref_impedance=50)
pe = ports[a.port - 1]
sii = pe.uf_ref / pe.uf_inc
zin = pe.uf_tot / pe.if_tot
cols = [freq / 1e9, 20 * np.log10(abs(sii))]
hdr = f'f_GHz,S{a.port}{a.port}_dB'
if dual:
    po = ports[2 - a.port]; j = 3 - a.port
    cols.append(20 * np.log10(abs(po.uf_ref / pe.uf_inc))); hdr += f',S{j}{a.port}_dB'
cols += [zin.real, zin.imag]; hdr += ',Re_Zin,Im_Zin'
np.savetxt(os.path.join(res, f'{tag}_S.csv'), np.c_[tuple(cols)], delimiter=',', header=hdr, fmt='%.5f')

m = (freq >= 4e9) & (freq <= 7e9)
gm = abs(sii[m]); v = (1 + gm) / (1 - gm)
with open(os.path.join(res, f'{tag}_summary.txt'), 'w') as fh:
    fh.write(f'wideband element {tag}: port {a.port}, dual={dual}, params {json.dumps(P)}\n')
    fh.write(f'worst VSWR 4-7 GHz {v.max():.2f}, share of 4-7 GHz with VSWR<=2: {(v <= 2).mean()*100:.0f} %, <=3: {(v <= 3).mean()*100:.0f} %\n')
    for f in np.arange(4.0, 7.01, 0.25):
        k = np.argmin(abs(freq - f * 1e9)); g = abs(sii[k])
        line = f'{f:5.2f} GHz  S{a.port}{a.port} {20*np.log10(g):6.2f} dB  VSWR {(1+g)/(1-g):5.2f}'
        if dual:
            line += f'  S{j}{a.port} {cols[2][k]:6.1f} dB'
        fh.write(line + f'  Zin {zin[k].real:6.1f}{zin[k].imag:+6.1f}j\n')
    if nf2ff is not None:
        th = np.arange(-180, 181, 2.0)
        cut_phi = 90.0 if a.port == 1 else 0.0          # E-plane cut of the excited polarisation
        nf = nf2ff.CalcNF2FF(sim, fz, th, [cut_phi], center=[0, 0, z1], outfile='nf2ff_cut.h5')
        Pinc = np.array([np.interp(f, freq, pe.P_inc) for f in fz])
        pats = []
        for i, f in enumerate(fz):
            E = np.squeeze(nf.E_norm[i]); U = E ** 2 * float(np.squeeze(nf.r)) ** 2 / (2 * 376.73)
            Gr = 10 * np.log10(4 * np.pi * U / Pinc[i]); pats.append(Gr)
            k0 = np.argmin(abs(th)); kb = np.argmin(abs(abs(th) - 180))
            fh.write(f'{f/1e9:4.1f} GHz  broadside realised gain {Gr[k0]:5.2f} dBi  front/back {Gr[k0]-Gr[kb]:5.1f} dB\n')
        np.savetxt(os.path.join(res, f'{tag}_pattern.csv'), np.c_[th, np.array(pats).T], delimiter=',',
                   header='theta_deg,' + ','.join(f'Greal_{f/1e9:.1f}GHz_dBi' for f in fz), fmt='%.3f')
print(open(os.path.join(res, f'{tag}_summary.txt')).read())
