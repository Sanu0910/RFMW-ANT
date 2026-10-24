"""Parametric two-part handheld enclosure for the CRL-MT1 board (gmsh / OpenCASCADE).

Bottom tray holds the PCB on four standoffs; top lid snaps over it with a display window,
six button holes and side cut-outs for USB-C and the GPIO header. Exports STEP + STL and a
render. Original design - our own shell, no trademark or mascot.

  <hertzon-python> build_enclosure.py
"""
import math
import os

import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "05_enclosure"))
os.makedirs(OUT, exist_ok=True)

# ---- board + fit parameters (mm) ----
BL, BW, BT = 100.0, 60.0, 1.6     # board length, width, thickness
GAP = 0.8                          # board edge -> inner wall
WALL = 2.0                         # shell wall thickness
BOT_CLR = 3.0                      # space under the board (bottom-side parts)
TOP_CLR = 9.0                      # space over the board (tallest top part + display)
STANDOFF = 3.0                     # board rests this high in the bottom tray
LIP = 4.0                          # overlap between the two shells

IL, IW = BL + 2 * GAP, BW + 2 * GAP           # inner cavity
OL, OW = IL + 2 * WALL, IW + 2 * WALL         # outer footprint
R = 4.0                                        # outer vertical-edge fillet (grip)


def box(x, y, z, dx, dy, dz):
    return gmsh.model.occ.addBox(x, y, z, dx, dy, dz)


def build():
    gmsh.initialize()
    gmsh.model.add("crl-mt1-case")
    occ = gmsh.model.occ

    # ============ BOTTOM TRAY ============
    bt_h = WALL + BOT_CLR + BT + LIP            # tray height
    tray = box(0, 0, 0, OL, OW, bt_h)
    # inner cavity (leave the lip ring at the top)
    cav = box(WALL, WALL, WALL, IL, IW, bt_h)
    tray = occ.cut([(3, tray)], [(3, cav)])[0][0][1]
    parts_bottom = [(3, tray)]
    # four board standoffs (posts up to STANDOFF height, with a screw hole)
    posts = []
    sx = [WALL + GAP + 3, WALL + GAP + IL - 2 * GAP - 3]
    sy = [WALL + GAP + 3, WALL + GAP + IW - 2 * GAP - 3]
    for px in sx:
        for py in sy:
            post = occ.addCylinder(px, py, WALL, 0, 0, BOT_CLR, 2.6)
            hole = occ.addCylinder(px, py, WALL, 0, 0, BOT_CLR + BT, 1.0)
            post = occ.cut([(3, post)], [(3, hole)])[0][0][1]
            posts.append((3, post))
    bottom = occ.fuse(parts_bottom, posts)[0] if posts else parts_bottom

    # USB-C cut-out on the -Y (bottom) wall, at board-edge height
    z_board = WALL + BOT_CLR
    usb = box(OL / 2 - 5, -1, z_board - 1.2, 10, WALL + 2, 4.0)
    bottom = occ.cut(bottom, [(3, usb)])[0]

    occ.synchronize()
    # fillet the four outer vertical edges of the tray for grip
    _fillet_vertical(bottom)
    occ.synchronize()
    gmsh.model.occ.synchronize()
    # save bottom alone
    _export("crl-mt1-case-bottom")

    # ============ TOP LID ============
    gmsh.model.add("lid")
    lid_h = TOP_CLR + WALL
    base_z = 200.0                              # model the lid off to the side in Z for a combined view
    lid = box(0, 0, base_z, OL, OW, lid_h)
    cav2 = box(WALL, WALL, base_z - 0.001, IL, IW, lid_h - WALL + 0.001)
    lid = occ.cut([(3, lid)], [(3, cav2)])[0][0][1]
    lid_parts = [(3, lid)]
    # display window on the top face (centered-upper area)
    win = box(OL / 2 - 20, OW / 2 + 2, base_z + lid_h - WALL - 0.5, 40, 22, WALL + 1)
    lid_parts = occ.cut(lid_parts, [(3, win)])[0]
    # six button holes along the top edge
    bz = base_z + lid_h - WALL - 0.5
    for i in range(6):
        bxp = OL / 2 - 15 + i * 6
        bhole = occ.addCylinder(bxp, OW - WALL - 6, bz, 0, 0, WALL + 1, 1.6)
        lid_parts = occ.cut(lid_parts, [(3, bhole)])[0]
    # GPIO header slot on the +X (right) wall
    gpio = box(OL - 1, OW / 2 - 12, base_z - 0.001, WALL + 2, 24, 6)
    lid_parts = occ.cut(lid_parts, [(3, gpio)])[0]
    occ.synchronize()
    _fillet_vertical(lid_parts)
    occ.synchronize()
    _export("crl-mt1-case-top")

    gmsh.finalize()
    print(f"enclosure: outer {OL:.0f} x {OW:.0f} mm, tray {bt_h:.1f} mm + lid {lid_h:.1f} mm")


def _fillet_vertical(dimtags):
    """Fillet the (near-)vertical outer edges with radius R."""
    try:
        vol = dimtags[0][1] if isinstance(dimtags, list) else dimtags[1]
        edges = gmsh.model.getBoundary([(3, vol)], False, False, True)
        vedges = []
        for (d, e) in edges:
            xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(d, e)
            if abs((zmax - zmin)) > abs((xmax - xmin)) + abs((ymax - ymin)):
                vedges.append(e)
        if vedges:
            gmsh.model.occ.fillet([vol], vedges, [R], removeVolume=True)
    except Exception as ex:
        print("fillet skipped:", ex)


def _export(name):
    gmsh.model.occ.synchronize()
    gmsh.write(os.path.join(OUT, name + ".step"))
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(OUT, name + ".stl"))


if __name__ == "__main__":
    build()
