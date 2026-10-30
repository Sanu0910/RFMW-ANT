"""VSWR fix within the existing build: present element vs the element with a two-section match on its 100-ohm branch.

Full-wave results (sim_tune.py): I0 = present patches without match, VA1/VA2 = match for 4.9-6.4 GHz (V/H ports),
VB1/VB2 = match for 5.1-6.2 GHz. Writes 03_results/fix_vswr.png and prints a summary table.
    python fix_figures.py
"""
import os, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')


def vswr(tag):
    p = os.path.join(R, f'{tag}_S.csv')
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p, delimiter=','); g = 10 ** (d[:, 1] / 20)
    return d[:, 0], (1 + g) / (1 - g), d[:, 2]


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
for tag, c, ls, name in (('I0', '0.55', '-', 'present element, no match'),
                         ('VA1', 'tab:blue', '-', 'fix A (4.9-6.4 GHz match), V port'), ('VA2', 'tab:blue', '--', 'fix A, H port'),
                         ('VB1', 'tab:red', '-', 'fix B (5.1-6.2 GHz match), V port'), ('VB2', 'tab:red', '--', 'fix B, H port')):
    r = vswr(tag)
    if r is not None:
        a1.plot(r[0], r[1], color=c, ls=ls, lw=2.0 if tag != 'I0' else 1.6, label=name)
        if tag in ('VA1', 'VB1', 'I0'):
            a2.plot(r[0], r[2], color=c, lw=1.4, label=f'{name.split(",")[0]}: V-H coupling')
for v, ls in ((3, '--'), (2, ':')):
    a1.axhline(v, color='k', ls=ls, lw=0.8)
for ax in (a1, a2):
    ax.axvspan(4.9, 6.4, color='tab:green', alpha=0.07); ax.grid(alpha=0.3)
a1.set(xlabel='Frequency (GHz)', ylabel='VSWR (100-ohm element branch)', xlim=(4.4, 7.0), ylim=(1, 8), title='Element VSWR: present vs fixed')
a1.legend(fontsize=7.5, loc='upper center')
a2.set(xlabel='Frequency (GHz)', ylabel='dB', xlim=(4.4, 7.0), ylim=(-45, -10), title='Isolation between the V and H feeds')
a2.legend(fontsize=7.5, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'fix_vswr.png'), dpi=130)

print('tag   band        worst VSWR  VSWR<=2   VSWR<=3   worst coupling')
for tag in ('I0', 'VA1', 'VA2', 'VB1', 'VB2'):
    r = vswr(tag)
    if r is None:
        continue
    for b in ((4.9, 6.4), (5.1, 6.2)):
        m = (r[0] >= b[0]) & (r[0] <= b[1])
        print(f'{tag:4s}  {b[0]}-{b[1]}   {r[1][m].max():6.2f}    {(r[1][m] <= 2).mean()*100:5.0f} %   {(r[1][m] <= 3).mean()*100:5.0f} %   {r[2][m].max():6.1f} dB')
    p = os.path.join(R, f'{tag}_summary.txt')
    g = re.findall(r'([\d.]+) GHz\s+broadside realised gain\s+([-\d.]+)', open(p).read())
    if g:
        print('      element realised gain: ' + ', '.join(f'{f} GHz {v} dBi' for f, v in g))
