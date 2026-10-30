"""Measured panel (05_measured/measured_2026-10-30.csv) vs simulation.

Left: measured S11 markers of both ports over the simulated full-array S11/S22 (array_pN_S.csv when the runs are
finished, else the preliminary array_interim_S.csv). Right: measured gain vs the aperture-directivity ceiling of the
276.86 mm board (4 pi A / lambda^2) and the simulated array realised gain when available.

    python compare_measured.py      (writes 03_results/measured_vs_sim.png and prints aperture efficiency)
"""
import os, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, '..', '03_results')
M = os.path.join(HERE, '..', '05_measured', 'measured_2026-10-30.csv')
m = np.genfromtxt(M, delimiter=',', comments='#', skip_header=4, names=True)
fm = m['f_MHz'] / 1e3
# S11 markers (CSV rows + the two extra markers at 5.7 / 5.9 GHz noted in the CSV)
sA = [(f, s) for f, s in zip(fm, m['S11_A_dB']) if np.isfinite(s)] + [(5.7, -14.687), (5.9, -14.039)]
sB = [(f, s) for f, s in zip(fm, m['S11_B_dB']) if np.isfinite(s)] + [(5.7, -13.329), (5.9, -8.103)]
sA.sort(); sB.sort()

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
final = all(os.path.exists(os.path.join(R, f'array_p{k}_S.csv')) for k in (1, 2))
if final:
    for k, c in ((1, 'tab:blue'), (2, 'tab:red')):
        d = np.loadtxt(os.path.join(R, f'array_p{k}_S.csv'), delimiter=',')
        a1.plot(d[:, 0], d[:, 1], color=c, lw=1.0, alpha=0.6, label=f'simulated array S{k}{k}')
else:
    d = np.loadtxt(os.path.join(R, 'array_interim_S.csv'), delimiter=',')
    a1.plot(d[:, 0], d[:, 1], color='tab:blue', lw=1.0, alpha=0.55, label='simulated array S11 (preliminary)')
    a1.plot(d[:, 0], d[:, 3], color='tab:red', lw=1.0, alpha=0.55, label='simulated array S22 (preliminary)')
a1.plot(*zip(*sA), 'o-', color='k', ms=6, lw=1.6, label='measured port A (markers)')
a1.plot(*zip(*sB), 's--', color='tab:green', ms=6, lw=1.6, label='measured port B (markers)')
for v, ls in ((3, '--'), (2, ':')):
    g = (v - 1) / (v + 1); a1.axhline(20 * np.log10(g), color='0.3', ls=ls, lw=0.8)
a1.set(xlabel='Frequency (GHz)', ylabel='|S11| (dB)', xlim=(4.4, 7.0), ylim=(-35, 0), title='Input match: measured vs simulated')
a1.grid(alpha=0.3); a1.legend(fontsize=7.5, loc='lower left')

A = 0.27686 ** 2
f = np.linspace(4.4, 7.0, 200)
Dmax = 10 * np.log10(4 * np.pi * A / (3e8 / (f * 1e9)) ** 2)
a2.plot(f, Dmax, 'k-', lw=1.2, label='aperture limit 4$\\pi$A/$\\lambda^2$ (100 % efficiency)')
a2.plot(f, Dmax - 3, 'k:', lw=1.0, label='50 % aperture efficiency')
a2.axhline(23, color='tab:purple', ls='--', lw=1.0, label='23 dBi panel rating')
a2.plot(fm, m['gain_V_dBi'], 'o-', color='tab:blue', lw=1.8, label='measured gain V')
a2.plot(fm, m['gain_H_dBi'], 's-', color='tab:red', lw=1.8, label='measured gain H')
for k, c in ((1, 'tab:blue'), (2, 'tab:red')):
    p = os.path.join(R, f'array_p{k}_summary.txt')
    if os.path.exists(p):
        g = [(float(x.group(1)), float(x.group(2))) for x in re.finditer(r'([\d.]+) GHz\s+broadside realised gain\s+([-\d.]+)', open(p).read())]
        if g:
            a2.plot(*zip(*g), 'x--', color=c, ms=8, label=f'simulated realised gain port {k}')
a2.set(xlabel='Frequency (GHz)', ylabel='Gain (dBi)', xlim=(4.4, 7.0), ylim=(8, 28), title='Broadside gain: measured vs aperture limit')
a2.grid(alpha=0.3); a2.legend(fontsize=7.5, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'measured_vs_sim.png'), dpi=130)

Dm = 10 * np.log10(4 * np.pi * A / (3e8 / (fm * 1e9)) ** 2)
print(' f GHz  ceiling  gain V  eff V   gain H  eff H')
for f0, dm, gv, gh in zip(fm, Dm, m['gain_V_dBi'], m['gain_H_dBi']):
    print(f' {f0:4.1f}   {dm:5.1f}   {gv:5.1f}  {10**((gv-dm)/10)*100:4.0f} %   {gh:5.1f}  {10**((gh-dm)/10)*100:4.0f} %')
