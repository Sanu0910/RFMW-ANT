# In the name of God, the Most Gracious, the Most Merciful
"""Layer-by-layer 3-D STEP export of the null-steering / CP modular antenna boards.

Reuses the exact parametric geometry in nsgeom.py (dimensions straight from the
paper, Younus et al., IEEE TAP 73(5), 2025) and extrudes each copper layer onto
the real stack-up, so the solids carry the same coordinates as the DXFs - nothing
is drawn by hand or to an approximate size.

Stack-up (mm, from nsgeom):   z = 0      BOT copper (feed / balun loop)
                              z = 0..0.608  RO4450F 0.1 + RO4003C 0.508  (lower dielectric)
                              z = 0.608  MID copper (phase-shifter ground)
                              z = 0.608..1.116  RO4003C 0.508            (upper dielectric)
                              z = 1.116  TOP copper (feeder, patches, dipole arms + ground)
Copper is modelled 17 um thick. Each board writes:
  <board>/<board>__L<n>_<LAYER>.step   one solid per copper layer (layer by layer)
  <board>/<board>__dielectric.step     the two laminate blocks
  <board>/<board>__vias.step           plated through/blind via barrels (if any)
  <board>__assembly.step               everything, for a quick import / sanity view
Run:  python build_step.py            -> writes into ../06_step
"""
import os, math
import cadquery as cq
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
import nsgeom as G

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "06_step"))
CU_T = 0.017                                   # copper thickness (mm)
ZCU = {"BOT": (-CU_T, CU_T), "MID": (G.Z_MID, CU_T), "TOP": (G.Z_TOP, CU_T)}
# via layer span -> (z_lo, z_hi)
VSPAN = {"TOP-MID": (G.Z_MID, G.Z_TOP), "MID-BOT": (0.0, G.Z_MID),
         "TOP-MID-BOT": (0.0, G.Z_TOP), "TOP-BOT": (0.0, G.Z_TOP)}


def _polys(g):
    if g.is_empty:
        return []
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def _face(poly):
    """shapely Polygon (with holes) -> cadquery planar Face at z=0."""
    outer = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in poly.exterior.coords])
    inners = [cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in r.coords]) for r in poly.interiors]
    return cq.Face.makeFromWires(outer, inners)


def _extrude_layer(merged, z0, t):
    """Extrude a merged (multi)polygon to a list of solids placed at z0..z0+t."""
    out = []
    for p in _polys(merged):
        if p.area < 1e-9:
            continue
        solid = cq.Solid.extrudeLinear(_face(p), cq.Vector(0, 0, t)).located(
            cq.Location(cq.Vector(0, 0, z0)))
        out.append(solid)
    return out


def _dielectric(board):
    """Two laminate blocks spanning the board outline."""
    out = []
    for p in _polys(unary_union(board.L["OUTLINE"])):
        lo = cq.Solid.extrudeLinear(_face(p), cq.Vector(0, 0, G.Z_MID))          # 0 .. MID
        up = cq.Solid.extrudeLinear(_face(p), cq.Vector(0, 0, G.Z_TOP - G.Z_MID)).located(
            cq.Location(cq.Vector(0, 0, G.Z_MID)))                                # MID .. TOP
        out += [lo, up]
    return out


def _vias(board):
    out = []
    for (x, y, d, layers) in board.vias:
        lo, hi = VSPAN.get(layers, (0.0, G.Z_TOP))
        out.append(cq.Solid.makeCylinder(d / 2.0, hi - lo, cq.Vector(x, y, lo), cq.Vector(0, 0, 1)))
    return out


def _write(solids, path):
    if not solids:
        return False
    comp = cq.Compound.makeCompound(solids)
    cq.exporters.export(comp, path)
    return True


def export_board(board, name=None):
    name = name or board.name
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    allsolids = []
    n = 0
    for lay in ("BOT", "MID", "TOP"):
        if lay not in board.L:
            continue
        merged = unary_union(board.L[lay])
        solids = _extrude_layer(merged, ZCU[lay][0], ZCU[lay][1])
        if _write(solids, os.path.join(d, "%s__L%d_%s.step" % (name, n, lay))):
            allsolids += solids
            n += 1
    diel = _dielectric(board)
    _write(diel, os.path.join(d, "%s__dielectric.step" % name))
    vias = _vias(board)
    _write(vias, os.path.join(d, "%s__vias.step" % name))
    # assembly: copper + vias (+ dielectric as the last, so EM meshers can drop it if they want)
    _write(allsolids + vias + diel, os.path.join(OUT, "%s__assembly.step" % name))
    print("  %-26s copper layers=%d  vias=%d" % (name, n, len(vias)))
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    print("== STEP export -> %s" % OUT)
    boards = [
        G.board_dipole(),
        G.board_phase_shifter(slot="paper", bias="L"),
        G.board_unit("A", slot="paper", mid="paper", unit_no=1),
        G.board_unit("B", slot="paper", mid="paper", unit_no=2),
        G.board_unit("A", slot="paper", mid="extended", unit_no=1),
        G.board_unit("B", slot="paper", mid="extended", unit_no=2),
    ]
    # give the extended variants distinct names
    names = ["DIPOLE_standalone", "PS_standalone",
             "UNIT_A_mid-paper", "UNIT_B_mid-paper",
             "UNIT_A_mid-extended", "UNIT_B_mid-extended"]
    for b, nm in zip(boards, names):
        export_board(b, nm)


if __name__ == "__main__":
    main()
