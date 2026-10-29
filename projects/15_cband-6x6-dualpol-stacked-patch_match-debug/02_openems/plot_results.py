"""Plot every *_S.csv in 03_results: element variants and the full array."""
import os, glob
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '03_results')
LBL = {'element_air': 'as built (air gap, parasitic 16.2-17.8 mm)',
       'element_nopar': 'driven patch only (no parasitic/FR4)',
       'element_gap4p5': 'gap filled er 4.5 (stack-up PDF value)',
       'element_par1.15': 'parasitic x1.15', 'element_par1.25': 'parasitic x1.25',
       'element_par1.35': 'parasitic x1.35'}


def vswr_lines(ax):
    for v, ls in ((3, '--'), (2, ':')):
        g = (v - 1) / (v + 1)
        ax.axhline(20 * np.log10(g), color='k', ls=ls, lw=0.8)
        ax.text(7.45, 20 * np.log10(g) + 0.3, f'VSWR {v}:1', ha='right', fontsize=8)
    ax.axvspan(4, 7, color='tab:green', alpha=0.06)


fig, ax = plt.subplots(figsize=(9, 5))
for tag in LBL:
    p = os.path.join(R, f'{tag}_S.csv')
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=',')
        ax.plot(d[:, 0], d[:, 1], lw=2.2 if tag == 'element_air' else 1.2, label=LBL[tag])
vswr_lines(ax)
ax.set(xlabel='Frequency (GHz)', ylabel='|S11| (dB, 100-ohm branch)', ylim=(-30, 0), xlim=(3.5, 7.5),
       title='Single stacked-patch element, V-feed (openEMS)')
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'element_S11.png'), dpi=130)

# Smith-chart style locus of the as-built element
p = os.path.join(R, 'element_air_S.csv')
if os.path.exists(p):
    d = np.loadtxt(p, delimiter=',')
    z = (d[:, 3] + 1j * d[:, 4]) / 100.0
    G = (z - 1) / (z + 1)
    fig, ax = plt.subplots(figsize=(6, 6))
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), 'k', lw=0.8)
    for r in (0.2, 0.5, 1, 2, 5):
        c = r / (1 + r); ax.plot(c + np.cos(t) / (1 + r), np.sin(t) / (1 + r), color='0.8', lw=0.6)
    for vv in (2, 3):
        g = (vv - 1) / (vv + 1); ax.plot(g * np.cos(t), g * np.sin(t), '--', lw=0.8, label=f'VSWR {vv}')
    m = (d[:, 0] >= 4) & (d[:, 0] <= 7)
    ax.plot(G.real[m], G.imag[m], 'C3', lw=2, label='element 4-7 GHz')
    for f in (4, 5, 5.5, 6, 6.5, 7):
        i = np.argmin(abs(d[:, 0] - f)); ax.plot(G.real[i], G.imag[i], 'ko', ms=3)
        ax.annotate(f'{f:g}', (G.real[i], G.imag[i]), fontsize=8, xytext=(3, 3), textcoords='offset points')
    ax.set_aspect('equal'); ax.axis('off'); ax.legend(fontsize=8, loc='lower right')
    ax.set_title('As-built element input reflection (100 ohm)')
    fig.tight_layout(); fig.savefig(os.path.join(R, 'element_smith.png'), dpi=130)

# full array
fig, ax = plt.subplots(figsize=(9, 5))
got = False
for tag, col, name in (('array_p1', 1, 'S11 (port 1, V-pol)'), ('array_p1', 2, 'S21 isolation'),
                       ('array_p2', 1, 'S22 (port 2, H-pol)')):
    p = os.path.join(R, f'{tag}_S.csv')
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=',')
        ax.plot(d[:, 0], d[:, col], lw=1.6, label=name); got = True
if got:
    vswr_lines(ax)
    ax.set(xlabel='Frequency (GHz)', ylabel='dB (50 ohm)', ylim=(-40, 0), xlim=(3.5, 7.5),
           title='Full 6x6 array as drawn (openEMS, 12 M cells)')
    ax.grid(alpha=0.3); ax.legend(fontsize=8, loc='lower left')
    fig.tight_layout(); fig.savefig(os.path.join(R, 'array_S.png'), dpi=130)
print('plots written to', R)
