"""Circuit study on the simulated element impedance (03_results/element_air_S.csv).

Question: is the bad S11 a feed-network problem (fixable with lines/transformers) or an element
bandwidth problem?  We take Zin seen at the 100-ohm branch cut and search, for each option,
the best line-based match over 4-7 GHz (lossless TLs on RT5880, eps_eff ~1.87):
  A  as built (100-ohm reference)
  B  series line (Z1, L1) + quarter-wave-type section (Z2, L2) to 100 ohm
  C  B + open shunt stub (Z3, L3)
Reports worst-case VSWR across 4-7 GHz and the 3:1 / 2:1 bandwidths.
"""
import os, numpy as np
from scipy.optimize import differential_evolution
d = np.loadtxt(os.path.join(os.path.dirname(__file__), '..', '03_results', 'element_air_S.csv'), delimiter=',')
f, z = d[:, 0] * 1e9, d[:, 3] + 1j * d[:, 4]
band = (f >= 4e9) & (f <= 7e9)
f, z = f[band], z[band]
beta = 2 * np.pi * f * np.sqrt(1.87) / 3e8          # rad/m, use mm below
def line(zl, Z, L):
    t = np.tan(beta * L * 1e-3)
    return Z * (zl + 1j * Z * t) / (Z + 1j * zl * t)
def gam(zin, Z0=100.0):
    return np.abs((zin - Z0) / (zin + Z0))
def vswr(g): return (1 + g) / (1 - g)
def bw(g, lim):
    ok = vswr(g) <= lim
    return ok.mean() * 3.0                       # GHz inside 4-7 that meet lim
def costB(p):
    Z1, L1, Z2, L2 = p
    return np.max(gam(line(line(z, Z1, L1), Z2, L2)))
def costC(p):
    Z1, L1, Z2, L2, Z3, L3 = p
    zz = line(z, Z1, L1)
    ys = 1j * np.tan(beta * L3 * 1e-3) / Z3       # open stub
    zz = 1 / (1 / zz + ys)
    return np.max(gam(line(zz, Z2, L2)))
out = []
g0 = gam(z)
out.append(('A as built', vswr(g0).max(), bw(g0, 3), bw(g0, 2)))
rB = differential_evolution(costB, [(40, 150), (0, 25), (40, 150), (0, 25)], seed=1, tol=1e-8, maxiter=400)
gB = gam(line(line(z, *rB.x[:2]), *rB.x[2:]))
out.append(('B best line + transformer', vswr(gB).max(), bw(gB, 3), bw(gB, 2)))
rC = differential_evolution(costC, [(40, 150), (0, 25), (40, 150), (0, 25), (40, 150), (0, 25)], seed=1, tol=1e-8, maxiter=400)
Z1, L1, Z2, L2, Z3, L3 = rC.x
zz = line(z, Z1, L1); zz = 1 / (1 / zz + 1j * np.tan(beta * L3 * 1e-3) / Z3); gC = gam(line(zz, Z2, L2))
out.append(('C best line + stub + transformer', vswr(gC).max(), bw(gC, 3), bw(gC, 2)))
with open(os.path.join(os.path.dirname(__file__), '..', '03_results', 'match_study.txt'), 'w') as fh:
    fh.write('Matching study on the simulated element (4-7 GHz, 100-ohm branch reference)\n')
    for n, wv, b3, b2 in out:
        fh.write(f'{n:36s} worst VSWR {wv:7.2f}   GHz with VSWR<=3: {b3:4.2f}/3.00   VSWR<=2: {b2:4.2f}/3.00\n')
    fh.write(f'B params Z1 {rB.x[0]:.1f} L1 {rB.x[1]:.2f} mm, Z2 {rB.x[2]:.1f} L2 {rB.x[3]:.2f} mm\n')
    fh.write(f'C params Z1 {Z1:.1f} L1 {L1:.2f}, Z2 {Z2:.1f} L2 {L2:.2f}, stub Z3 {Z3:.1f} L3 {L3:.2f} mm\n')
    # Bode-Fano style indicator: element 3:1 bandwidth limit with the radiator Q
print(open(os.path.join(os.path.dirname(__file__), '..', '03_results', 'match_study.txt')).read())
