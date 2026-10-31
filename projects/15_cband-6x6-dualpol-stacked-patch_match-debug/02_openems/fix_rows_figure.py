"""Fix B effect per array row: element VSWR (H feed, from the layer files) with each row's drawn parasitic size vs 16.2 mm.

Uses the ps_<size>_4.0_p1 runs of sim_element_fix.py (0.4 mm mesh). Writes 03_results/fix_rows.png and fix_rows.txt.
    python fix_rows_figure.py
"""
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
ROWS = [(1, 16.2), (2, 16.5), (3, 16.9), (4, 17.2), (5, 17.5), (6, 17.8)]


def load(size):
    p = os.path.join(R, f'ps_{size}_4.0_p1_S.csv')
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p, delimiter=','); g = 10 ** (d[:, 1] / 20); return d[:, 0], (1 + g) / (1 - g)


fix = load(16.2)
fig, ax = plt.subplots(figsize=(9, 5))
cm = plt.get_cmap('autumn_r')
lines = ['Fix B per row: element VSWR (H feed), as drawn vs all parasitics 16.2 mm',
         'row  parasitic  worst VSWR 5.1-6.2 GHz  VSWR<=2 in 5.1-6.2 GHz   (after fix: all rows as row 1)']
for k, (row, size) in enumerate(ROWS):
    r = load(size)
    if r is None:
        continue
    ax.plot(r[0], r[1], color=cm(0.15 + 0.14 * k), lw=1.3, label=f'row {row} as drawn ({size} mm)')
    m = (r[0] >= 5.1) & (r[0] <= 6.2)
    lines.append(f' {row}    {size:5.1f} mm    {r[1][m].max():6.2f}                 {(r[1][m] <= 2).mean()*100:4.0f} %')
if fix is not None:
    ax.plot(fix[0], fix[1], 'b', lw=2.6, label='fix B: every row 16.2 mm')
for v, ls in ((3, '--'), (2, ':')):
    ax.axhline(v, color='k', ls=ls, lw=0.8)
ax.axvspan(5.1, 6.2, color='tab:green', alpha=0.07)
ax.set(xlabel='Frequency (GHz)', ylabel='VSWR (100-ohm element branch)', xlim=(4.6, 6.8), ylim=(1, 8),
       title='Element VSWR per array row: as drawn vs fix B (feed lines unchanged)')
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc='upper center', ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(R, 'fix_rows.png'), dpi=130)
open(os.path.join(R, 'fix_rows.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
