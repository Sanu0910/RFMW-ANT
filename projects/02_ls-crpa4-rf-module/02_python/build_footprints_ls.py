"""Footprints that project 02 adds to / changes in the project 17 library (03_kicad/CRL_LS.pretty).

  GNSS_StackedPatch_L1L2_4feed        GPDF6010.A, drills as on combine_model_2.0 (feeds D1.35, M3 D3.6 PTH GND)
  NavIC_S_Patch_4feed_combine_model   S patch: centre D2.2 GND, 4 pins D0.77 at 4 mm, 4 x D2.2 at 17 mm (customer board)
  TA1442A_SAW_3x3                     Tai-Saw TA1442A 3x3 mm, 6 pads: 2 (B) IN, 5 (E) OUT, 1/3/4/6 GND  (Tai-Saw Rev 1 land pattern)
  Xinger_C2327J5003AHF                TTM Xinger 90 deg hybrid, 6 pads: 1 IN, 3 ISO, 4 DIRECT, 6 COUPLED, 2/5 GND (TTM Rev K land pattern)
  BEL_Logo_Silk / BEL_Logo_Silk_Small BEL logo from 00_input/BEL_logo.png on F.SilkS (flip for the bottom)
Run with the repo .venv:  python build_footprints_ls.py
"""
import os
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union, split
from shapely.affinity import scale, translate
import ls_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
LIBDIR = os.path.join(PRJ, "03_kicad", "CRL_LS.pretty")
LOGO_PNG = os.path.join(PRJ, "00_input", "BEL_logo.png")


def head(name, descr, attr="smd"):
    return [f'(footprint "{name}"', '  (version 20241229)', '  (generator "crl_ls_build_footprints")', '  (layer "F.Cu")',
            f'  (descr "{descr}")', f'  (attr {attr})',
            '  (property "Reference" "REF**" (at 0 -2.6 0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))',
            f'  (property "Value" "{name}" (at 0 2.6 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))']


def rect(layer, x0, y0, x1, y1, w=0.1):
    return f'  (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'


def smd(num, x, y, w, h, shape="rect"):
    return f'  (pad "{num}" smd {shape} (at {x:.4f} {y:.4f}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask"))'


def tht(num, x, y, pad, drill):
    return f'  (pad "{num}" thru_hole circle (at {x:.4f} {y:.4f}) (size {pad} {pad}) (drill {drill}) (layers "*.Cu" "*.Mask"))'


def save(name, lines):
    with open(os.path.join(LIBDIR, name + ".kicad_mod"), "w") as f:
        f.write("\n".join(lines + [")"]) + "\n")


def l_patch():
    n = "GNSS_StackedPatch_L1L2_4feed"
    L = head(n, f"Taoglas GPDF6010.A stacked L1/L2 patch, feeds L1 0/90 at 5.5 mm and L2 0/90 at 12.25 mm (D{D.ANT_FEED_DRILL}), "
                f"centre screw D{D.ANT_STUD_DRILL} GND, 4 x D{D.ANT_MOUNT_DRILL} PTH GND at 29 mm (combine_model_2.0)", "through_hole")
    L += [rect("F.Fab", -32, -32, 32, 32), rect("F.CrtYd", -32.25, -32.25, 32.25, 32.25, 0.05)]
    for x, y in ((-29, 0), (29, 0), (0, -29), (0, 29)):
        L.append(tht("M", x, y, D.ANT_MOUNT_PAD, D.ANT_MOUNT_DRILL))
    L.append(tht("C", 0, 0, 7, D.ANT_STUD_DRILL))
    for num, x, y in (("L1_0", -5.5, 0), ("L1_90", 0, 5.5), ("L2_0", 0, -12.25), ("L2_90", 12.25, 0)):
        L.append(tht(num, x, y, 2.2, D.ANT_FEED_DRILL))
    save(n, L)


def s_patch():
    n = "NavIC_S_Patch_4feed_combine_model"
    r = D.S_FEED_R
    L = head(n, "NavIC S patch, N element pose (top view): 4 pins D0.77 at 4 mm. Project 02 feeds F0 = +x and F90 = -y "
                "(outer pair, same rotation sense as the customer S0 -x / S90 +y pair); NC1 -x, NC2 +y; centre D2.2 GND. "
                "Placed at lambda/2 spacing (r 42.53 mm). Patch <= 25 x 25 mm [OPEN: part number]", "through_hole")
    L += [rect("F.Fab", -12.5, -12.5, 12.5, 12.5), rect("F.CrtYd", -12.75, -12.75, 12.75, 12.75, 0.05)]
    L.append(tht("C", 0, 0, D.S_CENTRE_PAD, D.S_CENTRE_DRILL))
    for num, x, y in (("F0", r, 0), ("F90", 0, -r), ("NC1", -r, 0), ("NC2", 0, r)):
        L.append(tht(num, x, y, D.S_FEED_PAD, D.S_FEED_DRILL))
    for x, y in D.S_MOUNT:
        L.append(tht("M", x, y, 4.0, 2.2))
    save(n, L)


def ta1442a():
    """Tai-Saw TA1442A approval sheet Rev 1 (00_vendor/TA1442A.pdf), F. PCB footprint, top view: 3.20 sq, 3 columns
    0.81 wide at 1.19 mm pitch (0.38 gaps), rows 1.05 high with a 1.09 gap; the A pad is 1.70 high.
    Pad numbers 1..6 = package pins A..F: top row F E D, bottom row A(tall) B C. B (2) IN, E (5) OUT, A/C/D/F GND."""
    n = "TA1442A_SAW_3x3"
    L = head(n, "Tai-Saw TA1442A 2492 MHz SAW, 3.0 x 3.0 x 1.4 mm. Land pattern per Tai-Saw approval sheet Rev 1 (3.20 sq). "
                "Pads 1..6 = pins A..F: 2 (B) IN, 5 (E) OUT, 1/3/4/6 (A/C/D/F) GND")
    L += [rect("F.Fab", -1.5, -1.5, 1.5, 1.5), rect("F.CrtYd", -1.85, -1.85, 1.85, 1.85, 0.05),
          '  (fp_circle (center -2.15 1.6) (end -2.0 1.6) (stroke (width 0.3) (type solid)) (fill yes) (layer "F.SilkS"))']
    px, ry, w, h = 1.19, 1.075, 0.81, 1.05
    for num, x, y in (("6", -px, -ry), ("5", 0, -ry), ("4", px, -ry), ("2", 0, ry), ("3", px, ry)):
        L.append(smd(num, x, y, w, h))
    L.append(smd("1", -px, 1.60 - 0.85, w, 1.70))          # A: 1.70 high, bottom aligned with the row
    save(n, L)


def xinger():
    """TTM C2327J5003AHF Rev K (00_vendor/C2327J5003AHF.pdf): body 2.04 x 1.29 x 0.68; mounting footprint 6 x 0.35 x 0.33
    pads, 0.30 gaps (0.65 pitch), 0.66 between rows (centres +-0.495). Top view: top row 3 2 1, bottom row 4 5 6
    (orientation dot next to pins 1/6). Configuration 1: 1 IN, 3 ISO, 4 DIRECT, 6 COUPLED, 2/5 GND."""
    n = "Xinger_C2327J5003AHF"
    L = head(n, "TTM Xinger C2327J5003AHF 90 deg hybrid 2300-2700 MHz, 2.04 x 1.29 x 0.68 mm. Land pattern per TTM Rev K "
                "(0.35 x 0.33 pads, 0.65 pitch, rows 0.99 apart). Config 1: 1 IN, 2 GND, 3 ISO, 4 DIRECT, 5 GND, 6 COUPLED")
    L += [rect("F.Fab", -1.02, -0.645, 1.02, 0.645), rect("F.CrtYd", -1.3, -0.95, 1.3, 0.95, 0.05),
          '  (fp_circle (center 1.5 0) (end 1.62 0) (stroke (width 0.24) (type solid)) (fill yes) (layer "F.SilkS"))']
    for num, x, y in (("1", 0.65, -0.495), ("2", 0, -0.495), ("3", -0.65, -0.495),
                      ("4", -0.65, 0.495), ("5", 0, 0.495), ("6", 0.65, 0.495)):
        L.append(smd(num, x, y, 0.35, 0.33))
    save(n, L)


def _no_holes(p):
    """Split a polygon with holes by vertical cuts through each hole, until no piece has holes (KiCad fp_poly)."""
    out, todo = [], [p]
    while todo:
        q = todo.pop()
        if q.is_empty or q.area < 1e-4:
            continue
        if not q.interiors:
            out.append(q)
            continue
        hx = Polygon(q.interiors[0]).centroid.x
        x0, y0, x1, y1 = q.bounds
        parts = split(q, LineString([(hx, y0 - 1), (hx, y1 + 1)]))
        todo += [g for g in parts.geoms if g.geom_type == "Polygon"]
    return out


def logo(width, name):
    import contourpy
    a = np.asarray(Image.open(LOGO_PNG).convert("RGB")).astype(float)
    ink = np.pad((a.min(axis=2) < 170).astype(float), 2)
    h_px, w_px = ink.shape
    polys = []
    for pts, offs in zip(*contourpy.contour_generator(z=ink, fill_type="OuterOffset").filled(0.5, 2.0)):
        rings = [pts[offs[k]:offs[k + 1]] for k in range(len(offs) - 1)]
        if len(rings[0]) < 4:
            continue
        q = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if q.area > 4.0:
            polys.append(q)
    g = unary_union(polys)
    s = width / w_px
    g = scale(g, s, s, origin=(0, 0))                     # KiCad y points down, like the image
    x0, y0, x1, y1 = g.bounds
    g = translate(g, -(x0 + x1) / 2, -(y0 + y1) / 2).simplify(0.03)
    L = head(name, f"BEL logo {width:.0f} mm wide, silkscreen (from BEL_logo.png)", "board_only exclude_from_pos_files exclude_from_bom")
    n = 0
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        for q in _no_holes(p):
            pts = " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in list(q.exterior.coords)[:-1])
            L.append(f'  (fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill yes) (layer "F.SilkS"))')
            n += 1
    save(name, L)
    return n, y1 - y0


if __name__ == "__main__":
    l_patch(); s_patch(); ta1442a(); xinger()
    print("logo 24 mm: %d polys, h %.1f mm" % logo(24.0, "BEL_Logo_Silk"))
    print("logo 16 mm: %d polys, h %.1f mm" % logo(16.0, "BEL_Logo_Silk_Small"))
    print(sorted(os.listdir(LIBDIR)))
