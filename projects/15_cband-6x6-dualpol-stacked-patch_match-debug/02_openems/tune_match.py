"""Two-section series matching on the 100-ohm element branch for sim_tune.py candidates.

Zin at the port (after LF mm of 100-ohm line) is moved back to the patch edge, then two series microstrip sections
(Z1, L1 from the patch, then Z2, L2) are searched to minimise the worst VSWR (100 ohm) over the band.
Microstrip on RT5880 0.8 mm (Hammerstad); Z limited to 60-150 ohm (2.0-0.25 mm), lengths 0-14 mm each.

usage:  python tune_match.py tag [tag ...] [--band 4.9 6.4]      (prints result and widths; writes <tag>_tm.txt)
        python tune_match.py --apply tag                            (also writes <tag>_tm_S.csv, the matched response)
"""
import os, sys, json, re
import numpy as np
from scipy.optimize import differential_evolution, brentq

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
ER, H = 2.2, 0.8


def z_eeff(w):
    u = w / H
    eeff = (ER + 1) / 2 + (ER - 1) / 2 / np.sqrt(1 + 12 / u)
    if u <= 1:
        z = 60 / np.sqrt(eeff) * np.log(8 / u + u / 4)
    else:
        z = 120 * np.pi / np.sqrt(eeff) / (u + 1.393 + 0.667 * np.log(u + 1.444))
    return z, eeff


def width(z):
    return brentq(lambda w: z_eeff(w)[0] - z, 0.05, 10)


def line(zl, z0, L, f):
    ee = z_eeff(width(z0))[1]
    t = np.tan(2 * np.pi * f * np.sqrt(ee) / 3e8 * L * 1e-3)
    return z0 * (zl + 1j * z0 * t) / (z0 + 1j * zl * t)


def load(tag):
    d = np.loadtxt(os.path.join(R, f'{tag}_S.csv'), delimiter=',')
    P = json.loads(re.search(r'(\{.*\})', open(os.path.join(R, f'{tag}_summary.txt')).readline()).group(1))
    return d, P


STUB = False      # --stub: add an open shunt stub (Zs, Ls) between the two series sections


def best(tag, band):
    d, P = load(tag)
    f = d[:, 0] * 1e9; z = d[:, 3] + 1j * d[:, 4]
    zedge = line(z, 100.0, -P['LF'], f)                     # de-embed the 100-ohm feed line
    m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)
    def resp(p, ff, zz):
        z1 = line(zz, p[0], p[1], ff)
        if STUB:
            ee = z_eeff(width(p[4]))[1]
            y = 1j * np.tan(2 * np.pi * ff * np.sqrt(ee) / 3e8 * p[5] * 1e-3) / p[4]
            z1 = 1 / (1 / z1 + y)
        return line(z1, p[2], p[3], ff)
    def cost(p):
        zz = resp(p, f[m], zedge[m]); g = abs((zz - 100) / (zz + 100)); return g.max()
    bnd = [(60, 150), (0, 14), (60, 150), (0, 14)] + ([(60, 150), (0, 14)] if STUB else [])
    r = differential_evolution(cost, bnd, seed=3, tol=1e-7, maxiter=200, polish=True)
    zz = resp(r.x, f, zedge); g = abs((zz - 100) / (zz + 100))
    return r.x, g, f, d, P


if __name__ == '__main__':
    args = sys.argv[1:]; band = (4.9, 6.4); apply = False
    if '--band' in args:
        i = args.index('--band'); band = (float(args[i + 1]), float(args[i + 2])); del args[i:i + 3]
    if '--stub' in args:
        STUB = True; args.remove('--stub')
    if '--apply' in args:
        apply = True; args.remove('--apply')
    for tag in args:
        p, g, f, d, P = best(tag, band)
        v = (1 + g) / (1 - g)
        def stats(b):
            m = (f >= b[0] * 1e9) & (f <= b[1] * 1e9); return v[m].max(), (v[m] <= 2).mean() * 100, (v[m] <= 3).mean() * 100
        s1, s2 = stats(band), stats((4.0, 7.0))
        g0 = 10 ** (d[:, 1] / 20); v0 = (1 + g0) / (1 - g0); m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)
        txt = (f'{tag}: L1 {P["L1"]:.2f} L2 {P["L2"]:.2f} h {P["h"]:.2f} ins {P["ins"]:.2f} | unmatched worst VSWR {band[0]}-{band[1]} GHz {v0[m].max():.2f}'
               f' -> matched {s1[0]:.2f} (VSWR<=2 {s1[1]:.0f} %) | 4-7 GHz worst {s2[0]:.2f}, <=3 {s2[2]:.0f} %\n'
               f'   match: {p[0]:.1f} ohm ({width(p[0]):.2f} mm) x {p[1]:.2f} mm at the patch, '
               + (f'open stub {p[4]:.1f} ohm ({width(p[4]):.2f} mm) x {p[5]:.2f} mm, ' if STUB else '')
               + f'then {p[2]:.1f} ohm ({width(p[2]):.2f} mm) x {p[3]:.2f} mm, then 100 ohm (0.73 mm)')
        print(txt)
        open(os.path.join(R, f'{tag}_tm.txt'), 'w').write(txt + '\n')
        if apply:
            np.savetxt(os.path.join(R, f'{tag}_tm_S.csv'), np.c_[d[:, 0], 20 * np.log10(g)], delimiter=',',
                       header='f_GHz,S11_dB_matched(circuit)', fmt='%.5f')
