"""Geometry + stack-up for the C-band 6x6 dual-polarised stacked-patch array.

Source: 01_input/{F_CU,IN2_CU,GND}.dxf and C_Band_Stackup.pdf (KiCad export).
Frame: mm, board centre at (0,0), z = 0 on the ground plane (B.Cu), +z towards the sky.

Stack-up (top -> bottom), as built:
    F.Cu      parasitic patches (36 squares)      z = 5.2
    FR4       0.4 mm, er 4.5, tand 0.02            z = 4.8 .. 5.2
    air gap   4.0 mm  (the PDF lists er 4.5/tand 0.02 for this layer -- a stack-up table error, see README)
    In2.Cu    driven patches + both feed networks  z = 0.8
    RT5880    0.8 mm, er 2.2, tand 0.0004          z = 0 .. 0.8
    B.Cu      solid ground (GND.dxf, 276.86 mm sq) z = 0
Copper is modelled as zero-thickness PEC sheets (35 um ignored).
"""
import os
import numpy as np
import ezdxf
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, '..', '01_input')

H_SUB, H_AIR, H_FR4 = 0.8, 4.0, 0.4
Z_GND, Z_DRV = 0.0, H_SUB
Z_FR4_BOT = H_SUB + H_AIR
Z_PAR = Z_FR4_BOT + H_FR4
ER_SUB, TD_SUB = 2.2, 0.0004
ER_FR4, TD_FR4 = 4.5, 0.02

# Two coax launch points found in IN2_CU.dxf: open ends of the two 2.5 mm (50 ohm) lines.
# P1 drives the network that feeds one edge of every patch, P2 the orthogonal edge.
PORTS = {1: dict(x=-76.95, y=(-3.30, -0.80)),   # filled in exactly by find_ports()
         2: dict(x=-1.45, y=(-3.30, -0.80))}


def _polys(name, folder=INP):
    out = []
    for e in ezdxf.readfile(os.path.join(folder, name)).modelspace():
        if e.dxftype() == 'LWPOLYLINE':
            p = Polygon([v[:2] for v in e.get_points()])
            out.append(p if p.is_valid else p.buffer(0))
    return out


def layers(variant=None):
    """Return dict of shapely geometries: 'par' (F.Cu), 'drv' (In2.Cu), 'gnd' (B.Cu).
    variant='fixB' reads the fix-B layer files from 06_fixB/ instead of the supplied ones in 01_input/."""
    if variant == 'fixB':
        d = os.path.join(HERE, '..', '06_fixB')
        return dict(par=unary_union(_polys('F_CU_fixB.dxf', d)), drv=unary_union(_polys('IN2_CU_fixB.dxf', d)),
                    gnd=unary_union(_polys('GND.dxf', d)))
    return dict(par=unary_union(_polys('F_CU.dxf')),
                drv=unary_union(_polys('IN2_CU.dxf')),
                gnd=unary_union(_polys('GND.dxf')))


def parts(geom):
    return list(geom.geoms) if hasattr(geom, 'geoms') else [geom]


def find_ports(drv):
    """Locate the open end of each 50-ohm launch line (x of the end face, y span)."""
    res = {}
    for k, guess in PORTS.items():
        b = drv.intersection(box(guess['x'] - 0.6, -6, guess['x'] + 3, 2))
        x0 = b.bounds[0]
        sl = drv.intersection(box(x0 + 0.05, -6, x0 + 0.15, 2))
        res[k] = dict(x=x0, y=(sl.bounds[1], sl.bounds[3]))
    return res


def line_widths(drv, step=0.5):
    """Histogram of copper widths along x- and y-cuts (rough trace-width census)."""
    xs0, ys0, xs1, ys1 = drv.bounds
    w = []
    for y in np.arange(ys0, ys1, step):
        seg = drv.intersection(box(xs0 - 1, y, xs1 + 1, y + 1e-3))
        for s in parts(seg):
            w.append(round(s.bounds[2] - s.bounds[0], 2))
    return np.array(w)


def no_holes(geom):
    """Split polygons with holes (feed loops) into hole-free pieces by cutting through each hole."""
    out, todo = [], [p for p in parts(geom)]
    while todo:
        p = todo.pop()
        if p.is_empty or p.area < 1e-4:
            continue
        if not p.interiors:
            out.append(p); continue
        hx = p.interiors[0].centroid.x
        x0, y0, x1, y1 = p.bounds
        todo += parts(p.intersection(box(x0 - 1, y0 - 1, hx, y1 + 1)))
        todo += parts(p.intersection(box(hx, y0 - 1, x1 + 1, y1 + 1)))
    return [q for q in out if q.geom_type == 'Polygon']


def add_poly(prop, geom, z, prio=10):
    for g in no_holes(geom):
        x, y = g.exterior.coords.xy
        prop.AddPolygon([np.array(x[:-1]), np.array(y[:-1])], 'z', z, priority=prio)
