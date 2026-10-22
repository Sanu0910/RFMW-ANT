#!/usr/bin/env python3
"""Parametric CAD of the 60-GHz serpentine slotted-waveguide LWA (Gabsteiger et al., IEEE TAP 2026).

Builds the metal shell (the part that is SLA-printed and silver-coated) and the internal air path with gmsh/OCC,
and writes:
  lwa_shell.step   solid shell with the 16 inclined edge slots and two flanges (for printing / CST / HFSS)
  lwa_shell.stl    the same, tessellated for the slicer (PreForm)
  lwa_air.step     the internal air volume (waveguide path), handy for an FEM model
  geometry.json    every dimension used

Coordinate system: array axis = x, legs run along z, radiating face = +y (the narrow walls of all legs).
Each leg has its narrow dimension b along x and its broad dimension a along y, so the +y wall of every
leg is a narrow wall and the 16 inclined narrow-wall ("edge") slots sit on one flat face.

Paper values: WR15 a = 3.76 mm, b = 1.88 mm; slot pitch d = b + 0.5 mm = 2.38 mm; path length between slots
l = 10.9 mm; N = 16; slot width 0.34 mm; tilts and depths from Table II; 44.8 mm between the flanges.
Assumptions (not fully specified in the paper):
  * wall t = 0.20 mm and air gap 0.10 mm (paper: t + t + gap = 0.5 mm);
  * semicircular E-plane U-bends of centre radius d/2 (the paper's bends are chamfered); the straight leg
    length is chosen so that the centre-line path between slot centres is exactly l;
  * slots at mid-leg, alternately tilted +/- theta_n from the transverse direction; the slot cutter crosses
    the narrow wall and cuts into both broad walls down to depth d_n;
  * both feeds leave the bottom of legs 1 and 16 through a 90-degree E-plane elbow into a horizontal WR15
    run that ends at a simplified round flange (check the flange against your UG-385/U hardware).
"""
import json
import math
import os
import sys

import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = os.path.join(HERE, "..", "02_python", "results", "slot_table_for_cad.json")

P = dict(a=3.76, b=1.88, t=0.20, gap=0.10, N=16, l=10.9, w_slot=0.34,
         feed_drop=1.0, feed_radius=2.0, flange_span=44.8, flange_d=19.05, flange_th=2.0,
         flange_hole_d=1.7, flange_bolt_circle=14.29, slot_clear=0.01)


def main(with_flanges=True):
    s = json.load(open(SLOTS))
    tilt, depth = s["tilt_deg"], s["depth_mm"]
    a, b, t, gap, N, l = P["a"], P["b"], P["t"], P["gap"], P["N"], P["l"]
    d = b + 2 * t + gap
    rc = d / 2
    ls = l - math.pi * rc                       # straight leg so that slot-to-slot path = l
    xs = [(n - (N - 1) / 2) * d for n in range(N)]
    P.update(d=d, leg_straight=ls, bend_rc=rc, slot_x=xs)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("lwa")
    occ = gmsh.model.occ

    def path(grow):
        """Waveguide path with the cross-section grown by `grow` on every side (0 = air, t = outer shell)."""
        bb, aa = b + 2 * grow, a + 2 * grow
        vols = []
        for x in xs:                                            # legs
            vols.append(occ.addBox(x - bb / 2, -aa / 2, -ls / 2, bb, aa, ls))
        for n in range(N - 1):                                  # U-bends, top for even n, bottom for odd n
            xc = (xs[n] + xs[n + 1]) / 2
            zc = ls / 2 if n % 2 == 0 else -ls / 2
            rect = occ.addRectangle(xc + rc - bb / 2, -aa / 2, zc, bb, aa)
            ang = -math.pi if n % 2 == 0 else math.pi           # -pi bulges to +z, +pi to -z
            out = occ.revolve([(2, rect)], xc, 0, zc, 0, 1, 0, ang)
            vols += [tag for dim, tag in out if dim == 3]
        rf, drop = P["feed_radius"], P["feed_drop"]
        x_in = P["flange_span"] / 2                             # inner flange faces at +/- 22.4 mm
        for x0, sgn in ((xs[0], -1), (xs[-1], +1)):
            vols.append(occ.addBox(x0 - bb / 2, -aa / 2, -ls / 2 - drop, bb, aa, drop + 1e-3))
            zc = -ls / 2 - drop
            xc = x0 + sgn * rf
            rect = occ.addRectangle(x0 - bb / 2, -aa / 2, zc, bb, aa)
            ang = math.pi / 2 if sgn < 0 else -math.pi / 2
            out = occ.revolve([(2, rect)], xc, 0, zc, 0, 1, 0, ang)
            vols += [tag for dim, tag in out if dim == 3]
            z_h = zc - rf
            x_lo, x_hi = sorted((xc, sgn * x_in))
            vols.append(occ.addBox(x_lo, -aa / 2, z_h - bb / 2, x_hi - x_lo, aa, bb))
        fused, _ = occ.fuse([(3, vols[0])], [(3, v) for v in vols[1:]])
        occ.synchronize()
        return fused

    air = path(0.0)
    outer = path(t)
    shell, _ = occ.cut(outer, air, removeObject=True, removeTool=False)
    occ.synchronize()

    # ---- flanges (simplified round flange with a WR15 bore and 4 holes)
    z_feed = -ls / 2 - P["feed_drop"] - P["feed_radius"]
    if with_flanges:
        fl = []
        for sgn in (-1, 1):
            x_face = sgn * P["flange_span"] / 2
            x0 = x_face if sgn > 0 else x_face - P["flange_th"]
            disc = occ.addCylinder(x0, 0, z_feed, P["flange_th"], 0, 0, P["flange_d"] / 2)
            bore = occ.addBox(x0 - 0.1, -a / 2, z_feed - b / 2, P["flange_th"] + 0.2, a, b)
            holes = []
            for k in range(4):
                ang = math.pi / 4 + k * math.pi / 2
                r = P["flange_bolt_circle"] / 2
                holes.append(occ.addCylinder(x0 - 0.1, r * math.cos(ang), z_feed + r * math.sin(ang),
                                             P["flange_th"] + 0.2, 0, 0, P["flange_hole_d"] / 2))
            f, _ = occ.cut([(3, disc)], [(3, bore)] + [(3, h) for h in holes])
            fl += f
        shell, _ = occ.fuse(shell, fl)
        occ.synchronize()

    # ---- 16 inclined narrow-wall slots on the +y face, alternately tilted
    cutters = []
    half_x = b / 2 + t + gap / 2 - P["slot_clear"]
    for n, x in enumerate(xs):
        th = math.radians(tilt[n]) * (1 if n % 2 == 0 else -1)
        w = P["w_slot"]
        lc = 2 * (half_x - w / 2 * abs(math.sin(th))) / math.cos(th)
        y0 = a / 2 - depth[n]
        hgt = t + depth[n] + 0.2
        box = occ.addBox(x - lc / 2, y0, -w / 2, lc, hgt, w)
        occ.rotate([(3, box)], x, 0, 0, 0, 1, 0, th)
        cutters.append((3, box))
    shell, _ = occ.cut(shell, cutters)
    occ.synchronize()

    vol_shell = sum(occ.getMass(3, tag) for _, tag in shell)
    bbox = gmsh.model.getBoundingBox(-1, -1)
    P["shell_volume_mm3"] = round(vol_shell, 1)
    P["bbox_mm"] = [round(v, 2) for v in bbox]

    # export shell
    air_tags = [tag for _, tag in air]
    occ.remove([(3, v) for v in air_tags], recursive=True)
    occ.synchronize()
    gmsh.write(os.path.join(HERE, "lwa_shell.step"))
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 0.4)
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.03)
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(HERE, "lwa_shell.stl"))
    gmsh.finalize()

    # air volume alone
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("air")
    occ = gmsh.model.occ
    path(0.0)
    gmsh.write(os.path.join(HERE, "lwa_air.step"))
    gmsh.finalize()

    P["slot_tilt_deg"] = tilt
    P["slot_depth_mm"] = depth
    json.dump(P, open(os.path.join(HERE, "geometry.json"), "w"), indent=1)
    print(json.dumps({k: P[k] for k in ("d", "leg_straight", "bend_rc", "shell_volume_mm3", "bbox_mm")}))


if __name__ == "__main__":
    main(with_flanges="--no-flanges" not in sys.argv)
