"""Figures for the wideband-element study (sim_wb_element.py / opt_wb_element.py / match_wb.py results in 03_results).

    python wb_figures.py [best_tag]          (default wbN4: best candidate, port 10 mm inside the ground)
Writes 04_docs/fig_wb_geometry.png, 03_results/wb_S11.png, 03_results/wb_study.png.
"""
import os, sys, json, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, '..', '03_results'); D = os.path.join(HERE, '..', '04_docs')
tag = sys.argv[1] if len(sys.argv) > 1 else 'wbN4'


def params(t):
    ln = open(os.path.join(R, f'{t}_summary.txt')).readline()
    return json.loads(re.search(r'(\{.*\})', ln).group(1)), 'dual=True' in ln


def vswr_lines(ax):
    for v, ls in ((3, '--'), (2, ':')):
        g = (v - 1) / (v + 1); ax.axhline(20 * np.log10(g), color='k', ls=ls, lw=0.8)
        ax.text(7.45, 20 * np.log10(g) + 0.3, f'VSWR {v}:1', ha='right', fontsize=8)
    ax.axvspan(4, 7, color='tab:green', alpha=0.06)


P, dual = params(tag)

# 1. geometry: top view + cross-section of the best candidate
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw=dict(width_ratios=[1, 1.15]))
G = P['G'] / 2; yp = -G + P.get('dp', 1.0)
a1.add_patch(Rectangle((-G, -G), 2 * G, 2 * G, fc='#e9d3b0', ec='k', lw=0.8, label='ground (z = 0)'))
Ls, Ws = P['Ls'], P['Ws']
a1.add_patch(Rectangle((-Ls / 2, -Ws / 2), Ls, Ws, fc='white', ec='k', lw=0.8, label=f'coupling slot {Ls:.1f} x {Ws:.2f} mm'))
if dual:
    a1.add_patch(Rectangle((-Ws / 2, P['yH'] - P['Ls2'] / 2), Ws, P['Ls2'], fc='white', ec='k', lw=0.8))
y0 = -G if P.get('dp', 1.0) <= 1 else yp
a1.add_patch(Rectangle((-1.24, y0), 2.48, P['Lst'] - y0, fc='tab:red', alpha=0.75, label=f'50 ohm feed under ground, stub {P["Lst"]:.1f} mm'))
a1.plot([0], [yp], 'o', ms=8, mfc='yellow', mec='k', label='port')
h = P['Lp1'] / 2; a1.add_patch(Rectangle((-h, -h), 2 * h, 2 * h, fc='none', ec='0.25', lw=1.6, label=f'driven patch {P["Lp1"]:.1f} mm'))
h = P['Lp2'] / 2; a1.add_patch(Rectangle((-h, -h), 2 * h, 2 * h, fc='none', ec='tab:orange', lw=1.6, ls='--', label=f'parasitic patch {P["Lp2"]:.1f} mm'))
a1.set_xlim(-G - 1, G + 1); a1.set_ylim(-G - 1, G + 1); a1.set_aspect('equal'); a1.grid(alpha=0.25)
a1.set_xlabel('x (mm)'); a1.set_ylabel('y (mm)'); a1.set_title(f'Top view ({tag})')
a1.legend(fontsize=7.5, loc='upper right', framealpha=0.9)

def lay(z0, hgt, c, t, cu=False):
    a2.add_patch(Rectangle((0, z0), 10, hgt, fc=c, ec='k', lw=0.6))
    a2.text(10.3 if cu else 5, z0 + hgt / 2, t, ha='left' if cu else 'center', va='center', fontsize=8.5)
z1 = P['h1']; zf = z1 + P['h2']
lay(-0.95, 0.12, '#b87333', 'feed line 2.48 mm (50 ohm)', True)
lay(-0.83, 0.8, '#fff3c4', 'RT5880 0.8 mm (er 2.2)')
lay(-0.03, 0.12, '#b87333', 'ground with slot', True)
lay(0.09, z1 - 0.09, '#e8f4ff', f'air / foam h1 = {z1:.2f} mm')
lay(z1, 0.12, '#b87333', f'driven patch {P["Lp1"]:.1f} mm', True)
lay(z1 + 0.12, P['h2'] - 0.12, '#e8f4ff', f'air / foam h2 = {P["h2"]:.2f} mm')
lay(zf, 0.4, '#c8e6a0', 'FR4 0.4 mm')
lay(zf + 0.4, 0.12, '#b87333', f'parasitic patch {P["Lp2"]:.1f} mm', True)
a2.set_xlim(0, 19); a2.set_ylim(-1.3, zf + 1.0); a2.axis('off')
a2.set_title(f'Cross-section (total height {zf + 0.4 + 0.8:.1f} mm)')
fig.tight_layout(); fig.savefig(os.path.join(D, 'fig_wb_geometry.png'), dpi=140); plt.close(fig)

# 2. best candidate vs present element
fig, ax = plt.subplots(figsize=(9, 5))
for t, c, lw, name in (('element_air', '0.45', 2.0, 'present element, as built (100 ohm branch)'),
                       (tag, 'tab:red', 2.0, f'best aperture-coupled candidate ({tag}, 50 ohm)'),
                       (f'{tag}_matched', 'tab:purple', 1.5, f'{tag} + best feed-layer matching network')):
    p = os.path.join(R, f'{t}_S.csv')
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=','); ax.plot(d[:, 0], d[:, 1], color=c, lw=lw, label=name)
vswr_lines(ax)
ax.set(xlabel='Frequency (GHz)', ylabel='|S11| (dB)', xlim=(3.5, 7.5), ylim=(-30, 0),
       title='Redesign study: best candidate so far vs the present element (openEMS)')
ax.grid(alpha=0.3); ax.legend(fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(R, 'wb_S11.png'), dpi=130); plt.close(fig)

# 3. what the study showed: representative candidates
fig, (b1, b2) = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
for t, name in (('wbnopatch', 'feed + slot only (no patches)'), ('wbN3', 'single patch 20 mm, slot 12 mm'),
                ('wbt1', 'start: patches 15 / 19 mm'), ('wbE', 'patches 20 / 23 mm')):
    p = os.path.join(R, f'{t}_S.csv')
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=','); b1.plot(d[:, 0], d[:, 1], lw=1.4, label=name)
for t, name in (('opt03_0', 'optimiser best (gen 3)'), ('wbS12', 'same, stub 12 mm'),
                ('wbP2', 'small driven 18 / large parasitic 26 mm'), ('wbN4', 'best, port 10 mm inside')):
    p = os.path.join(R, f'{t}_S.csv')
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=','); b2.plot(d[:, 0], d[:, 1], lw=1.4, label=name)
for b, t in ((b1, 'Diagnostics and first candidates'), (b2, 'Optimised and physics-guided candidates')):
    vswr_lines(b); b.set(xlabel='Frequency (GHz)', xlim=(3.5, 7.5), ylim=(-30, 0), title=t)
    b.grid(alpha=0.3); b.legend(fontsize=7.5, loc='lower left')
b1.set_ylabel('|S11| (dB, 50 ohm)')
fig.tight_layout(); fig.savefig(os.path.join(R, 'wb_study.png'), dpi=130); plt.close(fig)
print('wb figures written')
