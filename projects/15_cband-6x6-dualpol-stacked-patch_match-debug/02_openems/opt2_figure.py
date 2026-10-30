"""Option 2 (fix B, wide feed sections) vs as built: element from the layer files, both ports, full-wave.

Uses sim_element_fix.py results elemfix_asbuilt_p1/p2 and elemfix_fixB_p1/p2. Writes 03_results/opt2_vswr.png
and opt2_summary.txt.
    python opt2_figure.py
"""
import os, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')


def load(tag):
    p = os.path.join(R, f'{tag}_S.csv')
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p, delimiter=','); g = 10 ** (d[:, 1] / 20)
    return d[:, 0], (1 + g) / (1 - g), d[:, 2]


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
lines = ['Option 2 (wide feed sections, lines >= 0.73 mm) vs as built - element from the layer files, full-wave, 100-ohm branch',
         'port            band         worst VSWR   VSWR<=2   VSWR<=3   worst V-H coupling']
for k, name in ((1, 'H feed (port 1)'), (2, 'V feed (port 2)')):
    for var, c, lw in (('asbuilt', '0.5', 1.6), ('fixB', 'tab:blue' if k == 1 else 'tab:red', 2.3)):
        r = load(f'elemfix_{var}_p{k}')
        if r is None:
            continue
        ls = '-' if var == 'fixB' else '--'
        a1.plot(r[0], r[1], color=c if var == 'fixB' else ('0.35' if k == 1 else '0.65'), ls=ls, lw=lw,
                label=f'{name}: {"option 2" if var == "fixB" else "as built"}')
        if k == 1:
            a2.plot(r[0], r[2], color='tab:blue' if var == 'fixB' else '0.5', ls=ls, lw=1.5, label=f'V-H coupling, {"option 2" if var == "fixB" else "as built"}')
        for b in ((5.1, 6.2), (4.9, 6.4)):
            m = (r[0] >= b[0]) & (r[0] <= b[1])
            lines.append(f'{name:15s} {var:8s} {b[0]}-{b[1]}   {r[1][m].max():6.2f}    {(r[1][m] <= 2).mean()*100:4.0f} %    {(r[1][m] <= 3).mean()*100:4.0f} %    {r[2][m].max():6.1f} dB')
p = os.path.join(R, 'elemfix_fixB_p1_summary.txt')
if os.path.exists(p):
    gn = re.findall(r'([\d.]+) GHz\s+broadside realised gain\s+([-\d.]+)', open(p).read())
    if gn:
        lines.append('option 2 element realised gain (H feed): ' + ', '.join(f'{f} GHz {v} dBi' for f, v in gn))
for v, ls in ((3, '--'), (2, ':')):
    a1.axhline(v, color='k', ls=ls, lw=0.8)
for ax in (a1, a2):
    ax.axvspan(5.1, 6.2, color='tab:green', alpha=0.07); ax.grid(alpha=0.3)
a1.set(xlabel='Frequency (GHz)', ylabel='VSWR (100-ohm element branch)', xlim=(4.6, 6.8), ylim=(1, 8), title='Element VSWR: as built vs option 2')
a1.legend(fontsize=8, loc='upper center')
a2.set(xlabel='Frequency (GHz)', ylabel='dB', xlim=(4.6, 6.8), ylim=(-40, -10), title='Isolation between the V and H feeds')
a2.legend(fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'opt2_vswr.png'), dpi=130)
open(os.path.join(R, 'opt2_summary.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
