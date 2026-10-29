"""Geometry figures for the report (04_docs/fig_*.png): layout, feed split, element zoom, stack-up."""
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle
from shapely.geometry import box, Point
import cbgeom as g

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '04_docs')
os.makedirs(D, exist_ok=True)
L = g.layers()
drv, par = L['drv'], L['par']
P = g.find_ports(drv)


def draw(ax, geom, **kw):
    for p in g.parts(geom):
        if p.geom_type != 'Polygon' or p.is_empty:
            continue
        ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, **kw))
        for h in p.interiors:
            ax.add_patch(MPoly(np.array(h.coords), closed=True, fc='white', ec='none'))


# driven patches and the two networks
core = [p for p in g.parts(drv.buffer(-3).buffer(3)) if p.area > 150]
net = drv
for p in core:
    net = net.difference(box(*p.bounds).buffer(0.05, join_style=2))
comps = g.parts(net)
def comp_of(k):
    pt = Point(P[k]['x'] + 0.3, sum(P[k]['y']) / 2)
    return [c for c in comps if c.distance(pt) < 0.01][0]
n1, n2 = comp_of(1), comp_of(2)

# 1. layout with the two networks
fig, ax = plt.subplots(figsize=(9, 9))
ax.add_patch(Rectangle((-138.43, -138.43), 276.86, 276.86, fc='0.93', ec='k', lw=0.8))
draw(ax, drv, fc='0.45', ec='none')
draw(ax, n1, fc='tab:red', ec='none', alpha=0.9)
draw(ax, n2, fc='tab:blue', ec='none', alpha=0.9)
draw(ax, par, fc='none', ec='tab:orange', lw=1.0, ls='--')
for k, c in ((1, 'tab:red'), (2, 'tab:blue')):
    x, y = P[k]['x'], sum(P[k]['y']) / 2
    ax.plot(x, y, 'o', ms=11, mfc='yellow', mec='k')
    ax.annotate(f'P{k}', (x, y), xytext=(x - 4, y + 9), fontsize=12, weight='bold', color=c)
ax.plot([], [], color='tab:red', lw=4, label='Port 1 network: top/bottom edges (V-pol)')
ax.plot([], [], color='tab:blue', lw=4, label='Port 2 network: left/right edges (H-pol)')
ax.plot([], [], color='0.45', lw=6, label='driven patch 17.07 mm (In2.Cu)')
ax.plot([], [], color='tab:orange', ls='--', label='parasitic patch 16.2-17.8 mm (F.Cu)')
ax.set_xlim(-145, 145); ax.set_ylim(-145, 160); ax.set_aspect('equal')
ax.legend(loc='upper center', ncol=2, fontsize=8, frameon=False)
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
fig.tight_layout(); fig.savefig(os.path.join(D, 'fig_layout.png'), dpi=140); plt.close(fig)

# 2. element zoom
fig, ax = plt.subplots(figsize=(7.5, 6.5))
cl = box(-125, 91, -90, 120)
draw(ax, drv.intersection(cl), fc='0.6', ec='k', lw=0.4)
draw(ax, n1.intersection(cl), fc='tab:red', ec='k', lw=0.3, alpha=0.8)
draw(ax, n2.intersection(cl), fc='tab:blue', ec='k', lw=0.3, alpha=0.8)
draw(ax, par.intersection(cl), fc='none', ec='tab:orange', lw=1.5, ls='--')
ax.annotate('driven patch 17.07 x 17.07 mm\n(RT5880 0.8 mm)', (-105.5, 109), ha='center', fontsize=9)
ax.annotate('parasitic 16.2 mm\n(F.Cu, 4.4 mm above)', (-105.5, 102), ha='center', fontsize=9, color='tab:orange')
ax.annotate('edge feed: 2.48 mm (50 ohm)\nstub, then 0.73 mm (100 ohm)', (-124, 111), fontsize=8, color='tab:blue')
ax.annotate('edge feed: 2.48 mm (50 ohm)\nstub, then 0.73 mm (100 ohm)', (-104, 92), fontsize=8, color='tab:red')
ax.set_xlim(-125, -90); ax.set_ylim(91, 120); ax.set_aspect('equal'); ax.grid(alpha=0.3)
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)'); ax.set_title('Element (row 1, col 1) as drawn')
fig.tight_layout(); fig.savefig(os.path.join(D, 'fig_element.png'), dpi=140); plt.close(fig)

# 3. stack-up cross-section as built (the only stack-up used in this analysis)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
def lay(z0, h, c, t):
    ax.add_patch(Rectangle((0, z0), 10, h, fc=c, ec='k', lw=0.6))
    if c == '#b87333':
        ax.text(10.3, z0 + h / 2, t, ha='left', va='center', fontsize=9)
    else:
        ax.text(5, z0 + h / 2, t, ha='center', va='center', fontsize=9.5)
lay(0, 0.12, '#b87333', 'B.Cu ground')
lay(0.12, 0.8, '#fff3c4', 'RT5880 0.8 mm  er 2.2, tand 0.0004')
lay(0.92, 0.12, '#b87333', 'In2.Cu driven patches + feeds')
lay(1.04, 4.0, '#e8f4ff', 'AIR gap 4.0 mm  (er 1.0)')
lay(5.04, 0.4, '#c8e6a0', 'FR4 0.4 mm  er 4.5')
lay(5.44, 0.12, '#b87333', 'F.Cu parasitic patches')
ax.set_xlim(0, 15.5); ax.set_ylim(-0.2, 5.8); ax.axis('off'); ax.set_title('As built (modelled)', fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(D, 'fig_stackup.png'), dpi=150); plt.close(fig)
print('figures in', D)
