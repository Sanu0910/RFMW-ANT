"""Feed-layer matching for the wideband element candidates (03_results/<tag>_S.csv from sim_wb_element.py).

The aperture-coupled feed lines sit under the ground, where there is room for a matching network.
For each candidate, search lossless microstrip sections on the RT5880 0.8 mm feed layer (eps_eff ~1.87):
    load (simulated Zin at the 50-ohm port) -> series line Z1,L1 -> open shunt stub Z3,L3 -> series line Z2,L2 -> 50 ohm
Line impedances limited to 40-120 ohm (2.9-0.45 mm wide), lengths 0-22 mm.
Cost: worst |Gamma| over 4-7 GHz.

usage:  python match_wb.py [tag ...]        (no tag: every opt*/wb* candidate; writes 03_results/match_wb.txt)
        python match_wb.py --apply tag      (writes <tag>_matched_S.csv with the best network)
"""
import os, sys, glob, json
import numpy as np
from scipy.optimize import differential_evolution

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
EEFF = 1.87
BND = [(40, 120), (0, 22), (40, 120), (0, 22), (40, 120), (0, 22)]


def load(tag):
    d = np.loadtxt(os.path.join(R, f'{tag}_S.csv'), delimiter=',')
    return d[:, 0] * 1e9, d[:, -2] + 1j * d[:, -1], d


def net(z, f, p):
    Z1, L1, Z2, L2, Z3, L3 = p
    b = 2 * np.pi * f * np.sqrt(EEFF) / 3e8 * 1e-3       # rad/mm
    def line(zl, Z, L):
        t = np.tan(b * L); return Z * (zl + 1j * Z * t) / (Z + 1j * zl * t)
    zz = line(z, Z1, L1)
    zz = 1 / (1 / zz + 1j * np.tan(b * L3) / Z3)
    return line(zz, Z2, L2)


def gam(z): return np.abs((z - 50) / (z + 50))


def best(tag):
    f, z, _ = load(tag)
    m = (f >= 4e9) & (f <= 7e9)
    r = differential_evolution(lambda p: gam(net(z[m], f[m], p)).max(), BND, seed=2, tol=1e-7, maxiter=300, polish=True)
    g0 = gam(z[m]).max(); g1 = r.fun
    return g0, g1, r.x


def vs(g): return (1 + g) / (1 - g)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--apply']:
        tag = sys.argv[2]
        g0, g1, p = best(tag)
        f, z, d = load(tag)
        zm = net(z, f, p); s = 20 * np.log10(gam(zm))
        cols = [d[:, 0], s] + ([d[:, 2]] if d.shape[1] == 5 else []) + [zm.real, zm.imag]
        hdr = open(os.path.join(R, f'{tag}_S.csv')).readline().strip('# \n')
        np.savetxt(os.path.join(R, f'{tag}_matched_S.csv'), np.c_[tuple(cols)], delimiter=',', header=hdr, fmt='%.5f')
        with open(os.path.join(R, f'{tag}_matching.txt'), 'w') as fh:
            fh.write(f'{tag}: worst VSWR 4-7 GHz {vs(g0):.2f} unmatched -> {vs(g1):.2f} with the feed-layer network\n')
            fh.write('network (from the slot side): series line Z1 {:.1f} ohm L1 {:.2f} mm, open stub Z3 {:.1f} ohm L3 {:.2f} mm, '
                     'series line Z2 {:.1f} ohm L2 {:.2f} mm, then 50 ohm\n'.format(p[0], p[1], p[4], p[5], p[2], p[3]))
            m = (f >= 4e9) & (f <= 7e9); v = vs(10 ** (s[m] / 20))
            fh.write(f'share of 4-7 GHz with VSWR<=3: {(v <= 3).mean()*100:.0f} %, VSWR<=2: {(v <= 2).mean()*100:.0f} %\n')
            fh.write(' '.join(f'{a:.2f}:{b:.1f}' for a, b in zip(f[m][::12] / 1e9, v[::12])) + '\n')
        print(open(os.path.join(R, f'{tag}_matching.txt')).read())
        sys.exit()
    tags = sys.argv[1:] or sorted({os.path.basename(p)[:-6] for p in glob.glob(os.path.join(R, 'opt*_S.csv')) + glob.glob(os.path.join(R, 'wb*_S.csv'))
                                   if 'matched' not in p and 'final' not in p})
    out = []
    for t in tags:
        g0, g1, p = best(t)
        par = open(os.path.join(R, f'{t}_summary.txt')).readline()
        out.append((g1, t, vs(g0), vs(g1), par[par.find('{'):].strip()))
        print(f'{t:10s} worst VSWR {vs(g0):7.2f} -> matched {vs(g1):5.2f}', flush=True)
    out.sort()
    with open(os.path.join(R, 'match_wb.txt'), 'w') as fh:
        fh.write('Wideband element candidates: worst VSWR over 4-7 GHz, unmatched and with the best feed-layer network\n')
        for g1, t, v0, v1, par in out:
            fh.write(f'{t:10s} {v0:7.2f} -> {v1:5.2f}   {par}\n')
    print(open(os.path.join(R, 'match_wb.txt')).read())
