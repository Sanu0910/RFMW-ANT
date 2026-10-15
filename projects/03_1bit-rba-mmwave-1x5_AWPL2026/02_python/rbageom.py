"""Geometry library: compact 1-bit reconfigurable 1x5 mm-wave array (RCSPA elements), 25-29 GHz.
Jiao, Wang, Xu, IEEE AWPL 25(6), Jun 2026.  Units: mm.

Stack-up (top -> bottom):
  M1  patch                      z = 0.965
  Sub.1 RT5880  h1 = 0.508  (er 2.2,  tand 0.0009)
  M2  coupled shorted patch      z = 0.457
  Sub.2 RT5880  h2 = 0.254
  M3  ground with coupling slot  z = 0.203     (shorting pins M2 -> M3 through Sub.2)
  Sub.3 RO4003C h3 = 0.203  (er 3.55, tand 0.0027)
  M4  feed line, 1-bit switch loop, PIN diodes, bias   z = 0
Frame: x = array axis (E-plane, xoz, scan plane), y across, z up (broadside).  Origin = array centre.
Values marked [ASSUMED] are not given in the paper (or are inconsistent) - see 05_docs."""
import math
from shapely.geometry import box, Point, LineString, Polygon
from shapely.affinity import translate, scale as sscale
from shapely.ops import unary_union

H1, H2, H3 = 0.508, 0.254, 0.203
Z = {"M1": H1 + H2 + H3, "M2": H2 + H3, "M3": H3, "M4": 0.0}
ER1, ER3 = 2.2, 3.55

def ms(w, h=H3, er=ER3):
    u = w / h; ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
    z0 = 60 / math.sqrt(ee) * math.log(8 / u + u / 4) if u <= 1 else 120 * math.pi / (math.sqrt(ee) * (u + 1.393 + 0.667 * math.log(u + 1.444)))
    return ee, z0
def w_for(zt, h=H3, er=ER3):
    lo, hi = 0.02, 3.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if ms(m, h, er)[1] > zt else (lo, m)
    return (lo + hi) / 2
def lam_g(w, f=26.5e9):
    return 299.792458 / (f / 1e9) / math.sqrt(ms(w)[0])

# ---------------- element (Fig. 1) ----------------
E = dict(Lg=10.0, Wg=10.0, Lp=2.4, Wp=3.1, Sl=2.4, Sw=0.2, Ls=0.6, Ws=2.4, Dp=0.2, Dv=0.2,
         l1=0.9, l2=0.5, l3=2.4, w2=0.45, w3=2.0, w4=2.8,
         w1=None,                    # not given ("w1 =") -> 50 ohm on 0.203 RO4003C [ASSUMED]
         slot_x=-0.35,               # slot centre relative to patch centre [ASSUMED from Fig.1(b)]
         pin_x=-0.75, n_pins=6,      # shorting-pin row inside the M2 strip [ASSUMED]
         loop_w=0.2,                 # switch-loop line width [ASSUMED]
         diode_gap=0.25, diode_x=0.45)
E["w1"] = round(w_for(50.0), 3)
D = 4.5; ALg, AWg = 32.0, 12.0
PATCH_Y = 1.6                       # patch centre y on the array board [ASSUMED from Fig.5(a)]

def thick(pts, w):
    return LineString(pts).buffer(w / 2, cap_style="flat", join_style="mitre", mitre_limit=4)

class Board:
    def __init__(self, name, outline):
        self.name = name; self.L = {}; self.vias = []; self.txt = []; self.comp = []; self.add("OUTLINE", outline)
    def add(self, lay, g): self.L.setdefault(lay, []).append(g)
    def text(self, lay, s, x, y, h=0.35, rot=0): self.txt.append((lay, s, x, y, h, rot, "MIDDLE_CENTER"))
    def via(self, x, y, d, span): self.vias.append((x, y, d, span))
    def component(self, ref, val, side, x, y, w, h, rot=0, pol=""):
        self.comp.append(dict(ref=ref, value=val, side=side, x=x, y=y, w=w, h=h, rot=rot, pin1=pol))

def element(b, xc, yc, n, with_bias=True, port_y=None):
    """One RCSPA element. Patch centre (xc, yc). Returns the M4 feed-port point (x, y) at the bottom of the feed line."""
    e = E
    # M1 patch
    b.add("M1", box(xc - e["Lp"] / 2, yc - e["Wp"] / 2, xc + e["Lp"] / 2, yc + e["Wp"] / 2))
    # M2 coupled shorted strip (edge aligned with the patch's -x edge), pins M2 -> M3
    b.add("M2", box(xc - e["Lp"] / 2, yc - e["Ws"] / 2, xc - e["Lp"] / 2 + e["Ls"], yc + e["Ws"] / 2))
    for k in range(e["n_pins"]):
        yy = yc - e["Ws"] / 2 + 0.2 + k * (e["Ws"] - 0.4) / (e["n_pins"] - 1)
        b.via(xc + e["pin_x"], yy, e["Dp"], "M2-M3")
    # M3 slot (along y)
    xs = xc + e["slot_x"]
    b.add("M3_SLOT", box(xs - e["Sw"] / 2, yc - e["Sl"] / 2, xs + e["Sw"] / 2, yc + e["Sl"] / 2))
    # M4 switch loop: top arm along x crossing the slot at the slot centre, legs down w3, pad row with 2 diode gaps
    lw = e["loop_w"]; xl, xr = xc - e["w4"] / 2, xc + e["w4"] / 2; yt = yc; yb = yc - e["w3"]
    b.add("M4", thick([(xr, yb), (xr, yt), (xl, yt), (xl, yb)], lw))                      # inverted U
    gx, g = e["diode_x"], e["diode_gap"]
    b.add("M4", box(xl - lw / 2, yb - e["w2"] / 2, xc - gx - g / 2, yb + e["w2"] / 2))     # left pad arm (SW1 anode side)
    b.add("M4", box(xc + gx + g / 2, yb - e["w2"] / 2, xr + lw / 2, yb + e["w2"] / 2))     # right pad arm
    b.add("M4", box(xc - gx + g / 2, yb - e["w2"] / 2, xc + gx - g / 2, yb + e["w2"] / 2)) # centre (feed) pad
    # feed line from centre pad down
    yf = (yb - e["l1"] - 1.2) if port_y is None else port_y
    b.add("M4", box(xc - e["w1"] / 2, yf, xc + e["w1"] / 2, yb))
    # DC-block gap (3.6 pF) in the feed line
    yC = yb - e["l1"]
    b.L["M4"][-1] = b.L["M4"][-1].difference(box(xc - 1, yC - 0.15, xc + 1, yC + 0.15))
    b.component("C%d" % n, "3.6pF 0201", "M4", xc, yC, 0.3, 0.6)
    b.component("D%da" % n, "MA4AGFCP910 (SW1)", "M4", xc - gx, yb, 0.4, 0.3, pol="anode=centre pad")
    b.component("D%db" % n, "MA4AGFCP910 (SW2)", "M4", xc + gx, yb, 0.4, 0.3, pol="cathode=centre pad")
    # DC return: loop -> thin line -> shorting via to M3 ground (bottom-right)
    yr = yb - 0.45
    b.add("M4", thick([(xr, yb - e["w2"] / 2), (xr, yr), (xr + 0.35, yr)], 0.1))
    b.add("M4", Point(xr + 0.45, yr).buffer(0.15)); b.via(xr + 0.45, yr, 0.15, "M3-M4")
    if with_bias:
        # V1 bias: feed line (above C) -> thin high-Z line -> radial stub (RF short) -> 100 ohm R -> V pad at board top edge
        yj = yb - e["l1"] / 2
        xs_ = xl - 0.35
        b.add("M4", thick([(xc - e["w1"] / 2, yj), (xs_, yj), (xs_, yc + 2.3)], 0.1))
        # radial stub (70 deg, r = 0.8 mm ~ lambda_g/4) pointing +x from the bias line: RF short at the tap
        cx_, cy_ = xs_, yc + 1.2
        st = Polygon([(cx_, cy_)] + [(cx_ + 0.8 * math.cos(math.radians(a)), cy_ + 0.8 * math.sin(math.radians(a))) for a in range(-35, 36, 5)])
        b.add("M4", st)
        yR = yc + 2.6
        b.add("M4", box(xs_ - 0.15, yc + 2.3, xs_ + 0.15, yR - 0.15))
        b.add("M4", box(xs_ - 0.15, yR + 0.15, xs_ + 0.15, yR + 0.6))
        b.component("R%d" % n, "100R 0201", "M4", xs_, yR, 0.3, 0.6)
        b.add("M4", box(xs_ - 0.35, yR + 0.6, xs_ + 0.35, yR + 1.2))                         # V pad
        b.text("SILK_M4", "V%d" % n, xs_ + 0.75, yR + 0.9, 0.35)
        b.text("SILK_M4", "R%d" % n, xs_ + 0.6, yR, 0.25)
    b.text("SILK_M4", "C%d" % n, xc + 0.6, yC, 0.25)
    b.text("SILK_M4", "SW1", xc - gx, yb - 0.55, 0.22); b.text("SILK_M4", "SW2", xc + gx, yb - 0.55, 0.22)
    # polarity bars (cathode side)
    b.add("SILK_M4", box(xc - gx + 0.05, yb + 0.28, xc - gx + 0.13, yb + 0.42))
    b.add("SILK_M4", box(xc + gx - 0.13, yb + 0.28, xc + gx - 0.05, yb + 0.42))
    b.text("SILK_M1", str(n), xc, yc + e["Wp"] / 2 + 0.6, 0.6)
    return (xc, yf)

# ---------------- boards ----------------
def board_element():
    b = Board("ELEMENT", box(-E["Lg"] / 2, -E["Wg"] / 2, E["Lg"] / 2, E["Wg"] / 2))
    for lay in ("M3",): b.add(lay, box(-E["Lg"] / 2, -E["Wg"] / 2, E["Lg"] / 2, E["Wg"] / 2))
    px, py = element(b, 0, 1.0, 1, port_y=-E["Wg"] / 2)
    b.add("PORT", box(px - E["w1"] / 2, py, px + E["w1"] / 2, py + 0.02))
    b.text("SILK_M4", "RF IN (2.92mm / probe)", 0, -4.4, 0.35)
    b.text("SILK_M4", "STATE0: V1>0 (SW1 ON, 0 deg)   STATE1: V1<0 (SW2 ON, -180 deg)", 0, 4.6, 0.25)
    b.text("SILK_M1", "RCSPA 1-BIT ELEMENT 26.5 GHz", 0, -4.3, 0.4)
    return b

def board_array(with_divider=False, preload=(55.78, -5.79, -73.37, 0.0, -111.72)):
    """Fig.5: 1x5, D = 4.5 mm on ALg x AWg = 32 x 12 (antenna). with_divider: feed board extended below with
    a 1:5 equal-power divider whose branch lengths realise the fixed preload phases (Fig.6c, reconstructed)."""
    yb0 = -AWg / 2 - (19.0 if with_divider else 0.0)
    b = Board("ARRAY", box(-ALg / 2, yb0, ALg / 2, AWg / 2))
    b.add("M3", box(-ALg / 2, yb0, ALg / 2, AWg / 2))
    b.add("ANT_OUTLINE", box(-ALg / 2, -AWg / 2, ALg / 2, AWg / 2).exterior.buffer(0.05))
    ports = []
    for n in range(5):
        xc = (n - 2) * D
        ports.append(element(b, xc, PATCH_Y, n + 1, port_y=-AWg / 2 if not with_divider else -AWg / 2 + 0.5))
    # mounting holes (plastic screws) - antenna and feed boards
    for hx in (-14.5, 14.5):
        for hy in (-4.5, 0.0, 4.5):
            b.add("NPTH", Point(hx, hy).buffer(0.8))
    if not with_divider:
        for k, (px, py) in enumerate(ports, 1):
            b.add("PORT", box(px - E["w1"] / 2, py, px + E["w1"] / 2, py + 0.02))
            b.text("SILK_M4", "P%d" % k, px, py + 0.5, 0.3)
        b.text("SILK_M1", "1x5 1-BIT RBA  D=4.5  26.5 GHz", 0, -5.3, 0.45)
    else:
        info = divider(b, ports, preload, y_in=yb0)
        b.text("SILK_M1", "1x5 1-BIT RBA + 1:5 DIVIDER (PRELOAD)", 0, -5.3, 0.45)
        b.divider_info = info
    b.text("SILK_M4", "+x SCAN (E-plane xoz) ->", 10.0, -5.6 if not with_divider else yb0 + 1.0, 0.3)
    return b

def divider(b, ports, preload, y_in):
    """Corporate 1:5 equal-power divider on M4 (ground M3), 26.5 GHz.
    Split tree: IN -> J1 (2/5 left | 3/5 right) ; left J2 (1:1 -> e1,e2) ; right J3 (1/3 -> e3 | 2/3 -> J4) ; J4 (1:1 -> e4,e5).
    Unequal T-junctions use quarter-wave branch lines Zq = sqrt(Z0 * Z0 / p_i) so each branch presents Z0/p_i at the junction.
    Fixed preload: extra line (hairpin) per branch so that the total insertion phase difference equals the preload.
    Phase is computed with eps_eff of each segment width.  Returns a table of widths/lengths/phases."""
    Z0 = 50.0; f = 26.5e9; w50 = E["w1"]
    def zq(p): return math.sqrt(Z0 * Z0 / p)
    seg = []                                   # (element index list, width, length) to accumulate phase per path
    path_phase = {i: 0.0 for i in range(5)}; path_len = {i: 0.0 for i in range(5)}
    def run(pts, w, idx):
        b.add("M4", thick(pts, w))
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        ph = 360 * L / lam_g(w, f)
        for i in idx: path_phase[i] += ph; path_len[i] += L
        return L
    xs = [p[0] for p in ports]; ytop = ports[0][1]
    yJ1, yJ23, yJ4 = y_in + 2.5, y_in + 6.0, y_in + 9.0
    run([(0, y_in), (0, yJ1)], w50, range(5))
    tbl = []
    def junction(x, y, xl, xr, pl, pr, il, ir, ynext):
        wl, wr = w_for(zq(pl)), w_for(zq(pr)); ql, qr = lam_g(wl, f) / 4, lam_g(wr, f) / 4
        # quarter-wave branches: horizontal out to xl/xr then vertical, total length = lambda_g/4 each, rest at 50 ohm
        for (xx, w, q, idx, p) in ((xl, wl, ql, il, pl), (xr, wr, qr, ir, pr)):
            dx = abs(xx - x); s = 1 if xx > x else -1
            if dx >= q:
                run([(x, y), (x + s * q, y)], w, idx); run([(x + s * q, y), (xx, y), (xx, ynext)], w50, idx)
            else:
                run([(x, y), (xx, y), (xx, y + (q - dx))], w, idx); run([(xx, y + (q - dx)), (xx, ynext)], w50, idx)
            tbl.append(("junction (%.1f,%.1f) branch->x=%.1f" % (x, y, xx), round(p, 3), round(zq(p), 1), round(w, 3), round(q, 3)))
    xL = (xs[0] + xs[1]) / 2; xR = xs[2]
    junction(0, yJ1, xL, xR, 2 / 5, 3 / 5, [0, 1], [2, 3, 4], yJ23)
    junction(xL, yJ23, xs[0], xs[1], 1 / 2, 1 / 2, [0], [1], yJ4)
    xJ4 = (xs[3] + xs[4]) / 2
    junction(xR, yJ23, xs[2], xJ4, 1 / 3, 2 / 3, [2], [3, 4], yJ4)
    junction(xJ4, yJ4, xs[3], xs[4], 1 / 2, 1 / 2, [3], [4], yJ4 + 1.5)
    # risers to the hairpin zone, then hairpins sized for the preload, then up to each element port
    yH = yJ4 + 1.5
    for i in (0, 1, 2):
        run([(xs[i], yJ4 if i < 2 else yJ4), (xs[i], yH)], w50, [i])
    # required insertion phase: phi_i = -beta L_i ; want phi_i - phi_ref = preload_i
    lg = lam_g(w50, f)
    need = [path_phase[i] for i in range(5)]
    target = [-(p) for p in preload]                       # more length -> more negative phase
    # extra electrical degrees needed: extra_i = target_i - need_i + C, choose C so min(extra) >= 0
    raw = [target[i] - need[i] for i in range(5)]
    C = -min(raw); extra = [r + C for r in raw]
    yP = ytop
    for i in range(5):
        Lx = extra[i] / 360 * lg
        x = xs[i]; top = yP - 0.6
        if Lx > 0.05:
            # serpentine to the +x side: each fold = right ww, up p, back left ww, up p  -> adds 2*ww per fold
            p, wmax = 0.8, 1.9
            nf = max(1, math.ceil(Lx / (2 * wmax))); ww = Lx / (2 * nf)
            assert yH + 0.4 + 2 * p * nf < top, "not enough room for preload serpentine on element %d" % (i + 1)
            pts = [(x, yH), (x, yH + 0.4)]; y = yH + 0.4
            for k in range(nf):
                pts += [(x + ww, y), (x + ww, y + p), (x, y + p)]; y += p
                pts += [(x, y + p)]; y += p
            pts += [(x, top)]
            run(pts, w50, [i])
        else:
            run([(x, yH), (x, top)], w50, [i])
        run([(x, top), (x, yP)], w50, [i])
    rel = [path_phase[i] - path_phase[3] for i in range(5)]
    b.add("PORT", box(-w50 / 2, y_in, w50 / 2, y_in + 0.02))
    b.text("SILK_M4", "RF IN", 1.4, y_in + 0.8, 0.4)
    for i in range(5): b.text("SILK_M4", "%+.0f" % (-rel[i]), xs[i] - 0.9, yH + 1.0, 0.25)
    return dict(table=tbl, path_len=path_len, insertion_phase=path_phase, achieved_preload=[-r for r in rel],
                target_preload=list(preload), lam_g_50=lg, w50=w50)
