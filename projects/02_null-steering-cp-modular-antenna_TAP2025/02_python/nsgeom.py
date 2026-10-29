"""Geometry library: reconfigurable modular null-steering / CP antenna system
(Younus, Sultan, Fumeaux, Abbosh, IEEE TAP 73(5), May 2025).  Units: mm.

Board frame (every unit board, FRONT view as in Fig. 8a):
    x across the board (-W/2 .. +W/2), y along the board: y=0 RF input edge, y=36 phase-shifter/antenna
    boundary, y=60 antenna tip.  Beam (endfire of the printed dipole) points to +y; in the 3-D systems
    the boards stand vertically so +y(board) = +z(world).
Copper layers (3 metal / 2 cores + prepreg):
    TOP  (front)  z = 1.116 : PS input feeder, top coupling patch, top stub/varactor/bias; dipole arms + ground
    MID  (inner)  z = 0.608 : PS ground with elliptical coupling slot (variant: extended under antenna ground)
    BOT  (back)   z = 0     : PS output feeder, bottom patch, bottom stub/varactor/bias; dipole feed/balun loop
    RO4003C 0.508 (TOP-MID) / RO4450F prepreg 0.1 + RO4003C 0.508 (MID-BOT)
Parameters flagged [ASSUMED] are not given (or are inconsistent) in the paper - see 05_docs."""
import math
from shapely.geometry import box, Point, LineString, Polygon
from shapely.affinity import scale, translate
from shapely.ops import unary_union
import rtps_model as rm

# ---------------- stack-up ----------------
H_CORE, H_PREPREG, ER, ER_PP = 0.508, 0.1, 3.55, 3.52
Z_TOP, Z_MID, Z_BOT = H_CORE + H_PREPREG + H_CORE, H_CORE + H_PREPREG, 0.0
W_TOP50 = rm.ms_width_for_z(50, H_CORE, ER)                       # TOP line over MID: 0.508 mm
W_BOT50 = rm.ms_width_for_z(50, H_CORE + H_PREPREG, ER)           # BOT line over MID: 0.608 mm

# ---------------- phase shifter (Fig. 2) ----------------
PS = dict(L=36.0, W=25.0, Fl=13.7, Pl=8.8, Pw=4.9, Sl=8.8, Sw=8.8, lstub=9.4, Stl=6.1,
          w_stub_top=W_TOP50, w_stub_bot=W_BOT50,
          pad=0.5, cgap=0.4, junc_w=1.2, junc_l=1.9, dgap=0.4, dcpad_l=3.6, dcpad_w=4.0,
          via_d=0.3, bias_w=0.3, vbpad=2.0)
SW_DRAWING = 5.3   # [ASSUMED variant] Fig.2(e) ellipse aspect (Sw/Sl ~ 0.6); paper text lists Sw = Sl = 8.8

# ---------------- printed dipole (Fig. 6) ----------------
DP = dict(Lant=24.0, W=25.0, w1=1.6, w2=1.07, l1=1.65, l2=3.1, l3=14.2, l4=4.5, l4f=4.5,
          l5=4.0, l6=4.1, l7=0.43, gs=0.11, ls=4.1, ls_w=1.2)
# l6 printed as "li"; ls (decoupling strip height) and its width not given -> [ASSUMED] ls=4.1, ls_w=1.2

def ellipse(cx, cy, ax, ay, n=256):
    return scale(Point(cx, cy).buffer(1.0, resolution=n // 4), ax, ay)

def thick(pts, w):
    return LineString(pts).buffer(w / 2, cap_style="flat", join_style="mitre", mitre_limit=4)

class Board:
    """Collects polygons per layer, circles (vias), texts (silkscreen) and component markers."""
    def __init__(self, name, outline):
        self.name = name; self.L = {}; self.vias = []; self.txt = []; self.comp = []
        self.add("OUTLINE", outline)
    def add(self, layer, g):
        self.L.setdefault(layer, []).append(g)
    def text(self, layer, s, x, y, h=0.8, rot=0, align="MIDDLE_CENTER"):
        self.txt.append((layer, s, x, y, h, rot, align))
    def via(self, x, y, d=0.3, layers="TOP-MID-BOT"):
        self.vias.append((x, y, d, layers))
    def component(self, ref, value, side, x, y, w, h, rot=0, pin1=None):
        self.comp.append(dict(ref=ref, value=value, side=side, x=x, y=y, w=w, h=h, rot=rot, pin1=pin1))
    def merged(self, layer):
        return unary_union(self.L.get(layer, []))
    def transformed(self, fn_geom, fn_pt, name=None, mirror=False):
        b = Board(name or self.name, fn_geom(self.L["OUTLINE"][0]))
        for k, gs in self.L.items():
            if k == "OUTLINE": continue
            for g in gs: b.add(k, fn_geom(g))
        b.vias = [(*fn_pt(x, y), d, l) for x, y, d, l in self.vias]
        b.txt = [(l, s, *fn_pt(x, y), h, r, a) for (l, s, x, y, h, r, a) in self.txt]
        b.comp = [dict(c, **dict(zip(("x", "y"), fn_pt(c["x"], c["y"])))) for c in self.comp]
        return b

# ======================================================================================
# Phase shifter (standalone y 0..36, or embedded at the bottom of a unit board)
# ======================================================================================
def phase_shifter(b, y0=0.0, slot="paper", standalone=True, bias="L"):
    p = PS; hw = p["W"] / 2
    yc = y0 + p["L"] / 2
    sw = p["Sw"] if slot == "paper" else SW_DRAWING
    # ---- MID ground with elliptical coupling slot ----
    b.add("MID", box(-hw, y0, hw, y0 + p["L"]).difference(ellipse(0, yc, sw / 2, p["Sl"] / 2)))
    # ---- TOP: feeder from RF IN (y0) to patch, patch, stub -> C1 -> junction -> D1 -> DC pad(GND) ----
    wt = W_TOP50
    b.add("TOP", box(-wt / 2, y0, wt / 2, yc - p["Pl"] / 2 + 0.3))
    b.add("TOP", ellipse(0, yc, p["Pw"] / 2, p["Pl"] / 2))
    ys = yc + p["Pl"] / 2                               # patch end (22.4)
    _stub_chain(b, "TOP", ys, +1, p["w_stub_top"], hw, y0, bias, "1", standalone)
    # connector ground pads + vias for J1 (edge SMA at y0, centre pin on TOP feeder)
    if standalone or True:
        for sx in (-1, 1):
            b.add("TOP", box(sx * 1.4 - (sx < 0) * 2.2, y0, sx * 1.4 + (sx > 0) * 2.2, y0 + 2.4))
            for k in range(3): b.via(sx * (2.0 + 0.6 * k), y0 + 1.4, p["via_d"], "TOP-MID")
    # ---- BOT: (mirror along y) feeder from patch to y0+L (OUT / antenna), patch, stub chain downward ----
    wb = W_BOT50
    b.add("BOT", ellipse(0, yc, p["Pw"] / 2, p["Pl"] / 2))
    b.add("BOT", box(-wb / 2, yc + p["Pl"] / 2 - 0.3, wb / 2, y0 + p["L"]))
    _stub_chain(b, "BOT", yc - p["Pl"] / 2, -1, p["w_stub_bot"], hw, y0, bias, "2", standalone)
    if standalone:      # J2 ground pads on BOT at y0+L
        for sx in (-1, 1):
            b.add("BOT", box(sx * 1.4 - (sx < 0) * 2.2, y0 + p["L"] - 2.4, sx * 1.4 + (sx > 0) * 2.2, y0 + p["L"]))
            for k in range(3): b.via(sx * (2.0 + 0.6 * k), y0 + p["L"] - 1.4, p["via_d"], "MID-BOT")
    # ---- silkscreen ----
    b.text("SILK_TOP", "RF IN", -6.5, y0 + 4.2, 0.9)
    b.text("SILK_TOP", "J1", -5.5, y0 + 1.2, 0.8)
    b.text("SILK_BOT", "PS-BOT", 4.5, yc, 0.8, 90)
    b.text("SILK_TOP", "PS-TOP", 4.5, yc, 0.8, 90)
    if standalone:
        b.text("SILK_BOT", "RF OUT", -6.5, y0 + p["L"] - 4.2, 0.9)
        b.text("SILK_BOT", "J2", -5.5, y0 + p["L"] - 1.2, 0.8)
    return b

def _stub_chain(b, lay, ys, d, w, hw, y0, bias, idx, standalone):
    """stub (Stl) -> DC-block C (0402) -> junction pad (bias tap) -> varactor D (0402-class) -> grounded DC pad."""
    p = PS; side = "TOP" if lay == "TOP" else "BOT"; silk = "SILK_" + side
    y = ys
    def seg(a, bb, width):     # box between y=a and y=bb (any order)
        lo, hi = min(a, bb), max(a, bb); return box(-width / 2, lo, width / 2, hi)
    b.add(lay, seg(y - d * 0.3, y + d * p["Stl"], w)); y += d * p["Stl"]                  # stub line
    yC1 = y; b.add(lay, seg(y, y + d * p["pad"], 0.6)); y += d * (p["pad"] + p["cgap"])    # C pad 1
    b.add(lay, seg(y, y + d * p["pad"], 0.6)); y += d * p["pad"]                            # C pad 2
    yJ0 = y; b.add(lay, seg(y, y + d * p["junc_l"], p["junc_w"])); y += d * p["junc_l"]     # junction
    yJ = 0.5 * (yJ0 + y)
    yD = y; y += d * p["dgap"]                                                              # varactor gap
    b.add(lay, seg(y, y + d * p["dcpad_l"], p["dcpad_w"]))                                  # DC pad (GND)
    ydc = y + d * p["dcpad_l"] / 2
    for sx in (-1.4, 1.4):
        for k in range(3): b.via(sx, y + d * (0.6 + 1.2 * k), p["via_d"], "TOP-MID" if lay == "TOP" else "MID-BOT")
    # bias tap: junction -> 0402 choke/resistor (along -x) -> trace -> edge pad
    xa = -p["junc_w"] / 2
    b.add(lay, box(xa - 0.4, yJ - 0.3, xa, yJ + 0.3))
    b.add(lay, box(xa - 0.9, yJ - 0.3, xa - 0.4, yJ + 0.3))                                # L/R pad 1
    b.add(lay, box(xa - 1.8, yJ - 0.3, xa - 1.3, yJ + 0.3))                                # L/R pad 2
    b.add(lay, box(-hw + p["vbpad"], yJ - p["bias_w"] / 2, xa - 1.8, yJ + p["bias_w"] / 2))
    b.add(lay, box(-hw, yJ - p["vbpad"] / 2, -hw + p["vbpad"], yJ + p["vbpad"] / 2))       # VB pad
    # components (assembly/BOM) and silkscreen
    cval = "39pF (see guide)"; lval = "100nH" if bias == "L" else "10k"
    b.component("C" + idx, cval, side, 0, yC1 + d * (p["pad"] + p["cgap"] / 2), 0.5, 1.0)
    b.component("D" + idx, "MAVR-000120-14110P", side, 0, yD + d * p["dgap"] / 2, 0.6, 1.0, pin1="cathode->junction")
    b.component(("L" if bias == "L" else "R") + idx, lval, side, xa - 1.1, yJ, 1.0, 0.5)
    b.text(silk, "C" + idx, 1.6, yC1 + d * 0.7, 0.7)
    b.text(silk, "D" + idx, 2.6, yD, 0.7)
    b.text(silk, ("L" if bias == "L" else "R") + idx, xa - 1.1, yJ + d * 1.1, 0.6)
    b.text(silk, "VB" + idx, -hw + 1.0, yJ + d * 1.9, 0.7)
    b.text(silk, "GND", 0, ydc, 0.7)
    # cathode bar (varactor polarity): cathode toward the junction (positive bias = reverse bias)
    yb = yD - d * 0.15
    b.add(silk, box(1.0, min(yb, yb - d * 0.12), 1.8, max(yb, yb - d * 0.12)))

# ======================================================================================
# Printed dipole with integrated microstrip-to-slotline balun (Fig. 6)
# ======================================================================================
def dipole(b, y0=0.0, front="TOP", back="BOT", feed_w_in=None, decoupling=True):
    d = DP; hw = d["W"] / 2
    yg = y0 + d["Lant"] - d["l3"]                        # ground top edge (9.8 above y0)
    ysq_top = yg - d["l2"]; ysq_bot = ysq_top - d["l1"]
    gnd = box(-hw, y0, hw, yg)
    gnd = gnd.difference(box(-d["l1"] / 2, ysq_bot, d["l1"] / 2, ysq_top))          # square slot (open)
    gnd = gnd.difference(box(-d["gs"] / 2, ysq_top - 0.01, d["gs"] / 2, yg + 0.01))  # slot line (gs)
    b.add(front, gnd)
    ytop = y0 + d["Lant"]
    for s in (-1, 1):
        x_in, x_out = s * d["gs"] / 2, s * (d["gs"] / 2 + d["w1"])
        b.add(front, box(min(x_in, x_out), yg - 0.01, max(x_in, x_out), ytop))         # stem (slotline continues between)
        # 45-deg arm from the stem top, outward and down, length l4, width w1
        c = math.cos(math.radians(45))
        xa, ya = s * (d["gs"] / 2 + d["w1"] / 2), ytop - d["w1"] / 2
        arm = thick([(xa, ya), (xa + s * d["l4"] * c, ya - d["l4"] * c)], d["w1"])
        b.add(front, arm.intersection(box(-hw, y0, hw, ytop)))
    if decoupling:
        b.add(front, box(hw - d["ls_w"], yg - 0.01, hw, yg + d["ls"]))                   # mutual-coupling stub
    # back side: microstrip-to-slotline balun as drawn in Fig. 6(b): the feeder (x=0, length l4) ends at the
    # loop floor and turns left; left wall (l5) up; top bar (l6) across the slot line, which it crosses at x=0;
    # right tuning stub hangs down, open-ended. Nothing runs up the middle: the slot square (dotted in Fig. 6(b))
    # lies in the copper-free loop interior. Dimensions are taken centre line to centre line, which keeps the
    # top bar over the slot line (05_docs/MODEL_VERIFICATION.md lists the conflict between l4, l5, l7 and the
    # front-view l1-l3). Bars are extended by w2/2 so the corners are filled.
    w2 = d["w2"]; yf = y0 + d["l4f"]; xh = d["l6"] / 2; ytopl = yf + d["l5"]
    b.add(back, thick([(0, y0), (0, yf + w2 / 2)], w2))                    # feeder (l4) up to the floor's top edge
    b.add(back, thick([(-xh - w2 / 2, yf), (w2 / 2, yf)], w2))            # loop floor: feeder -> left wall
    b.add(back, thick([(-xh, yf), (-xh, ytopl)], w2))                      # loop left wall (l5)
    b.add(back, thick([(-xh - w2 / 2, ytopl), (xh + w2 / 2, ytopl)], w2))  # top bar (l6), crosses the slot line
    b.add(back, thick([(xh, ytopl), (xh, yf + d["l7"])], w2))              # right tuning stub, open end l7 above the floor centre line
    if feed_w_in and abs(feed_w_in - w2) > 1e-3:
        b.add(back, box(-feed_w_in / 2, y0 - 0.01, feed_w_in / 2, y0 + 0.6))         # width step at the junction
    # silkscreen
    b.text("SILK_TOP", "BEAM +Y", -7.0, ytop - 2.0, 0.8)
    b.text("SILK_TOP", "E-POL <->", 7.0, ytop - 6.5, 0.7)
    return b

# ======================================================================================
# Boards
# ======================================================================================
def board_phase_shifter(slot="paper", bias="L"):
    b = Board("PS_standalone", box(-PS["W"] / 2, 0, PS["W"] / 2, PS["L"]))
    phase_shifter(b, 0, slot, True, bias)
    _title(b, "PS-1 PHASE SHIFTER (NO ANTENNA)", 0, 33.2)
    b.add("PORT", box(-W_TOP50 / 2, 0, W_TOP50 / 2, 0.02))
    b.add("PORT", box(-W_BOT50 / 2, PS["L"] - 0.02, W_BOT50 / 2, PS["L"]))
    return b

def board_dipole():
    b = Board("DIPOLE_standalone", box(-DP["W"] / 2, 0, DP["W"] / 2, DP["Lant"]))
    dipole(b, 0, front="TOP", back="BOT")
    b.text("SILK_BOT", "J1 RF IN", 0, 2.0, 0.8)
    _title(b, "ANT-1 PRINTED DIPOLE (NO PS)", 0, 1.0, layer="SILK_TOP")
    b.add("PORT", box(-DP["w2"] / 2, 0, DP["w2"] / 2, 0.02))
    return b

def board_unit(variant="A", slot="paper", mid="paper", bias="L", unit_no=None):
    """Integrated unit: phase shifter (y 0..36) + dipole (y 36..60).
    variant 'A' = as drawn in Fig. 8 (unit 1); 'B' = mirror image (x -> -x) = the 180-deg ('blue') unit.
    mid 'paper'    : MID ground ends at y=36 (dash-dot line in Fig. 8b);
        'extended' : [RECOMMENDED VARIANT] MID ground continues under the dipole ground with the same
                     square slot + slot line cut, stitched to the TOP ground by a via fence."""
    L = PS["L"]; Lt = L + DP["Lant"]
    b = Board("UNIT", box(-PS["W"] / 2, 0, PS["W"] / 2, Lt))
    phase_shifter(b, 0, slot, False, bias)
    dipole(b, L, front="TOP", back="BOT", feed_w_in=W_BOT50)
    if mid == "extended":
        d = DP; yg = L + d["Lant"] - d["l3"]; ysq_top = yg - d["l2"]; ysq_bot = ysq_top - d["l1"]
        g = box(-PS["W"] / 2, L, PS["W"] / 2, yg)
        g = g.difference(box(-d["l1"] / 2, ysq_bot, d["l1"] / 2, ysq_top)).difference(box(-d["gs"] / 2, ysq_top, d["gs"] / 2, yg + 0.01))
        b.add("MID", g)
        for x in [-11.8, -9.0, -6.0, 6.0, 9.0, 11.8]:
            for y in (L + 0.8, yg - 0.6):
                b.via(x, y, 0.3, "TOP-MID")
        for y in [L + 3.0, L + 5.5, L + 8.0]:
            for x in (-11.8, 11.8): b.via(x, y, 0.3, "TOP-MID")
    b.text("SILK_BOT", "UNIT-%s  PS + DIPOLE%s" % (variant, ("  U%d" % unit_no) if unit_no else ""), -7.5, 20.0, 0.8, 90)
    b.text("SILK_BOT", "<ORG>  <PROJECT>  REV 1.0  YYYY-WW", -9.0, 20.0, 0.6, 90)
    b.add("PORT", box(-W_TOP50 / 2, 0, W_TOP50 / 2, 0.02))
    b.text("SILK_TOP", "TYPE %s" % variant, 7.5, 33.0, 1.0)
    if unit_no: b.text("SILK_TOP", "U%d" % unit_no, -7.5, 33.0, 1.6)
    if variant == "B":
        b = b.transformed(lambda g: scale(g, -1, 1, origin=(0, 0)), lambda x, y: (-x, y), name="UNIT_B")
        # re-anchor texts so silkscreen still reads correctly (only positions mirrored, strings unchanged)
    b.name = "UNIT_%s" % variant
    return b

def _title(b, s, x, y, layer="SILK_TOP"):
    b.text(layer, s, x, y, 0.8)
    b.text(layer, "<ORG>  <PROJECT>  REV 1.0  YYYY-WW", x, y - 1.2, 0.6)

def place(b, dx=0.0, dy=0.0, name=None):
    return b.transformed(lambda g: translate(g, dx, dy), lambda x, y: (x + dx, y + dy), name=name or b.name)

# ======================================================================================
# Wilkinson dividers (optional integrated feed, replaces the external 2-/4-way splitters)
# ======================================================================================
def wilkinson_stage(b, x0, y0, dx_out, y_out, lay="TOP"):
    """One equal-split Wilkinson at 6 GHz on 0.508 mm RO4003C (ground on BOT). Returns the two output points."""
    w50 = rm.ms_width_for_z(50, H_CORE, ER); w70 = rm.ms_width_for_z(70.71, H_CORE, ER)
    ee70, _ = rm.ms_eeff_z0(w70, H_CORE, ER); q = 299.792458 / 6 / math.sqrt(ee70) / 4      # lambda_g/4 (mm)
    a = 2.0; seg1 = math.hypot(a, 1.8); seg3 = math.hypot(a - 0.75, 1.3); vert = q - seg1 - seg3
    outs = []
    for s in (-1, 1):
        pts = [(x0, y0), (x0 + s * a, y0 + 1.8), (x0 + s * a, y0 + 1.8 + vert), (x0 + s * 0.75, y0 + 3.1 + vert)]
        b.add(lay, thick(pts, w70))
        ye = y0 + 3.1 + vert
        out = [(x0 + s * 0.75, ye), (x0 + s * 0.75, ye + 1.6), (x0 + s * dx_out, ye + 1.6), (x0 + s * dx_out, y_out)]
        b.add(lay, thick(out, w50)); outs.append((x0 + s * dx_out, y_out))
    ye = y0 + 3.1 + vert
    b.add(lay, box(x0 - 1.0, ye - 0.25, x0 - 0.5, ye + 0.25)); b.add(lay, box(x0 + 0.5, ye - 0.25, x0 + 1.0, ye + 0.25))
    b.component("R%d" % (len(b.comp) + 1), "100R 0402", lay, x0, ye, 1.0, 0.5)
    b.text("SILK_" + lay, "100R", x0, ye + 1.0, 0.5)
    return outs, q

def board_wilkinson(n_out=2, pitch=25.0):
    w50 = rm.ms_width_for_z(50, H_CORE, ER)
    if n_out == 2:
        W, Lb = pitch + 10, 30.0
        b = Board("WILKINSON_1x2", box(-W / 2, 0, W / 2, Lb)); b.add("BOT", box(-W / 2, 0, W / 2, Lb))
        b.add("TOP", box(-w50 / 2, 0, w50 / 2, 5.05))
        outs, q = wilkinson_stage(b, 0, 5.0, pitch / 2, Lb)
    else:
        W, Lb = 3 * pitch + 10, 50.0
        b = Board("WILKINSON_1x4", box(-W / 2, 0, W / 2, Lb)); b.add("BOT", box(-W / 2, 0, W / 2, Lb))
        b.add("TOP", box(-w50 / 2, 0, w50 / 2, 5.05))
        (o1, o2), q = wilkinson_stage(b, 0, 5.0, pitch, 22.0)
        outs = []
        for (x, y) in (o1, o2):
            oo, _ = wilkinson_stage(b, x, y - 0.05, pitch / 2, Lb); outs += oo
    b.text("SILK_TOP", "IN", 2.0, 1.5, 0.9)
    for k, (x, y) in enumerate(sorted(outs), 1): b.text("SILK_TOP", "OUT%d" % k, x + 3.0, y - 1.5, 0.8)
    _title(b, "WILKINSON 1:%d  6 GHz  PITCH %.0f" % (n_out, pitch), 0, 3.5)
    b.text("SILK_TOP", "lambda_g/4 = %.2f mm" % q, W / 2 - 9.0, 2.0, 0.6)
    return b
