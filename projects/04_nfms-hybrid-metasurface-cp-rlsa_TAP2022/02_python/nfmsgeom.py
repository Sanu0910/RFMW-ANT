"""Geometry library: CP radial-line slot array (RLSA) + two rotating hybrid metasurfaces (HMs), near-field meta-steering.
Afzal, Esselle, Koli, "A Beam-Steering Solution With Highly Transmitting Hybrid Metasurfaces and Circularly Polarized
High-Gain Radial-Line Slot Array Antennas", IEEE TAP 70(1), pp. 365-377, Jan 2022, DOI 10.1109/TAP.2021.3111522.
Units mm, GHz.  Frame: z up (broadside), origin = RLSA centre on the TOP face of the aluminium ground plate.
HM local frame: x = phase-delay axis (phase decreases toward +x, beam tilts toward +x).

Stack (z, mm)                                          source
  -3.0 .. 0.0   aluminium ground plate, 3 mm            Sec. V
   0.0 .. 3.0   air (radial waveguide, part 1)          Fig. 9(a)
   3.0 .. 4.6   TLY-5 1.6 mm, slots etched on top Cu    Fig. 9(a), Sec. V
   4.6          RLSA top copper (slotted)               Wh = 4.6 mm
  19.6          HM I input face (lambda0 above RLSA)    Sec. IV-B (probing plane = HM I plane)
  19.6 .. 24.4  HM I: 3 x 1.6 mm TLY-5, Cu M1..M4       Sec. III, V
  39.4 .. 44.2  HM II (gap HM I-HM II = 15 mm)          [ASSUMED] total height "4.5 cm" (Sec. V)
Values marked [ASSUMED] are not given in the paper - see 05_docs/DESIGN_GUIDE (assumptions table)."""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.affinity import rotate as srot, translate
import cells as CL

F0 = 20.0
LAM0 = CL.C0 / F0                     # 14.99 mm (paper rounds to 15)
# ---------------- RLSA (Sec. IV-A, Fig. 9) ----------------
R = dict(
    D_ap=345.0,                       # radial waveguide / aperture diameter (23 lambda0)
    Wh=4.6, h_air=3.0, h_diel=1.6,    # waveguide height, air part, TLY-5 part
    er=CL.ER,
    eps_eff_paper=1.41,               # paper: "effective relative dielectric ... 1.41" (volume average)
    lam_g_paper=12.56,                # paper (mm)
    Sw=1.0, Lmin=4.3, Lmax=4.9,       # slot width, length range (centre -> edge)
    rho0=6.0,                         # first slot radius
    S_rho=12.6, S_phi=7.5,            # spiral pitch (= lambda_g) and circumferential pair spacing
    n_pairs=960, n_turns=13,
    L_taper="linear in radius",       # [ASSUMED] the paper gives only Lmin/Lmax (ref [43] holds the taper)
    pair="T",                         # [ASSUMED from Fig. 9(b) inset]: slot B on slot A's normal, lambda_g/4 outward
    cu_margin=3.0,                    # top copper disc radius = outermost slot + margin [ASSUMED]
    D_diel=390.0,                     # dielectric / ground-plate diameter incl. assembly rim [ASSUMED, Fig. 16]
    t_ground=3.0,                     # aluminium plate (Sec. V)
    # feed (Fig. 9(a)): SMA pin to z = 1.6, flat disc head d 2.8 x 2.0 mm high, top at z = 3.6 (0.6 mm into TLY-5)
    probe_pin_d=1.27, head_d=2.8, head_z0=1.6, head_h=2.0, pocket_depth=0.6,
    sma_ptfe_d=4.1, sma_flange_holes=8.64, sma_hole_d=2.6,   # 4-hole flange SMA [ASSUMED part, check datasheet]
)
R["lam_g"] = LAM0 / math.sqrt(R["eps_eff_paper"])
# physically, the quasi-TEM field of a partially filled parallel plate with E normal to the layers sees the SERIES mix:
R["eps_eff_series"] = R["Wh"] / (R["h_diel"] / R["er"] + R["h_air"])
R["lam_g_series"] = LAM0 / math.sqrt(R["eps_eff_series"])

# ---------------- HMs (Sec. III, IV-B, V) ----------------
H = dict(
    d=CL.D_CELL, N=48, x0=-176.25,    # 48 x 48 grid of 7.5 mm cells, first centre at -176.25 (Fig. 11(b))
    theta0=19.5, dphi=60.0,           # metasurface tilt and gradient step (eq. (5)); paper rounds 60.09 to 60
    phi_first=-180.0,                 # phase of the leftmost column (Sec. IV-B)
    R_cells=180.0,                    # cells used out to RLSA radius + lambda0/2 (Sec. IV-B, "extended by lambda0/2")
    D_diel=390.0, n_holes=24, R_holes=187.5, hole_d=3.0,  # rim with a ring of 3 mm holes (Sec. IV-B, V); count/radius [ASSUMED]
    t=CL.H_CELL, gap_rlsa=15.0, gap_hm=15.0,              # HM I input face at lambda0; HM-HM gap [ASSUMED]
    notch=4.0,                        # V index notch on the rim at +x (phase-delay axis) [ASSUMED]
)
H["dphi_exact"] = 360.0 * H["d"] / LAM0 * math.sin(math.radians(H["theta0"]))

# RLSA near-field Ey phase, 15 mm above the aperture, 24 cells along -x (digitised from Fig. 12(a)); centre last
FIG12A_X = [H["x0"] + H["d"] * k for k in range(24)]
FIG12A_PHASE = [74, 35, 161, 106, 119, 118, 129, 117, 110, 102, 98, 111, 91, 109, 97, 104, 84, 90, 54, 65, 49, 20, -28, -8]

def wrap0(p):
    """Wrap to (-360, 0]."""
    q = p % 360.0
    return -((360.0 - q) % 360.0)

# ---------------- RLSA slots ----------------
def slot_length(rho, rmin, rmax):
    t = 0.0 if rmax <= rmin else min(max((rho - rmin) / (rmax - rmin), 0.0), 1.0)
    return R["Lmin"] + t * (R["Lmax"] - R["Lmin"])

def rlsa_pairs():
    """List of slot pairs along the outward CCW spiral rho = rho0 + S_rho * phi / 2pi.
    Slot A at (rho, phi), inclined +45 deg to the radial direction; slot B lambda_g/4 further out, on A's normal,
    inclined -45 deg (orthogonal).  The pair radiates rho_hat - j phi_hat = e^{j phi}(x - j y): RHCP (e^{jwt}),
    and the outward spiral cancels the e^{j phi} term, so all pairs add in phase at broadside."""
    q = R["S_rho"] / 4.0                      # radial offset of B, lambda_g / 4 (using the paper's S_rho = lambda_g)
    pts, phi = [], 0.0
    while len(pts) < R["n_pairs"]:
        rho = R["rho0"] + R["S_rho"] * phi / (2 * math.pi)
        pts.append((rho, phi))
        phi += R["S_phi"] / rho
    rmax = pts[-1][0]
    out = []
    for n, (rho, phi) in enumerate(pts):
        L = slot_length(rho, R["rho0"], rmax)
        ur = np.array([math.cos(phi), math.sin(phi)]); up = np.array([-math.sin(phi), math.cos(phi)])
        ca = rho * ur
        ta = (ur + up) / math.sqrt(2)          # slot A axis, +45 deg
        na = (ur - up) / math.sqrt(2)          # A's normal pointing outward
        cb = ca + na * (q * math.sqrt(2))      # radial component q, tangential -q
        out.append(dict(n=n, rho=rho, phi=phi, L=L, ca=ca, cb=cb, ang_a=math.degrees(math.atan2(ta[1], ta[0])),
                        ang_b=math.degrees(math.atan2(na[1], na[0]))))
    return out

def slot_poly(c, ang, L, w=None):
    w = R["Sw"] if w is None else w
    p = box(-L / 2, -w / 2, L / 2, w / 2)
    return translate(srot(p, ang, origin=(0, 0)), c[0], c[1])

def turns_of(pairs):
    return pairs[-1]["phi"] / (2 * math.pi)

# ---------------- HM phase maps ----------------
def grid_xy():
    c = np.array([H["x0"] + H["d"] * i for i in range(H["N"])])
    return c, c

def gradient_phase(i):
    """Wrapped gradient phase of column i (paper: -180, -240, -300, -360 (0), -60, -120, ...)."""
    return wrap0(H["phi_first"] - H["dphi"] * i)

def ring_radii():
    return [abs(x) for x in FIG12A_X]          # R1 (outer, 176.25) ... R24 (3.75)

def correction_phase(x, y):
    """2-D correction phase: inverse of the Fig. 12(a) field phase, assigned by nearest ring (circular symmetry)."""
    rho = math.hypot(x, y)
    rr = ring_radii(); k = int(np.argmin([abs(rho - r) for r in rr]))
    return -FIG12A_PHASE[k]

def in_aperture(x, y):
    return math.hypot(x, y) <= H["R_cells"] + 1e-9

def phase_maps():
    """Returns dict of 48x48 arrays (NaN outside the circular aperture): corr, grad, hm1, hm2 (wrapped to (-360,0])."""
    xs, ys = grid_xy(); N = H["N"]
    corr = np.full((N, N), np.nan); grad = np.full((N, N), np.nan); hm1 = np.full((N, N), np.nan); hm2 = np.full((N, N), np.nan)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if not in_aperture(x, y): continue
            c = correction_phase(x, y); g = gradient_phase(i)
            corr[j, i] = c; grad[j, i] = g; hm1[j, i] = wrap0(c + g); hm2[j, i] = g
    return dict(x=xs, y=ys, corr=corr, grad=grad, hm1=hm1, hm2=hm2)

def assign_cells(target, lib, rule="complex"):
    """Map each target phase to a cell.  rule 'complex': minimise |exp(j phi_t) - S21| over the whole library
    (trades phase error against loss); rule 'paper': closest phase among cells with |S21| > -1 dB."""
    pool = CL.usable(lib) if rule == "paper" else lib
    P = np.array([c["phase_norm"] for c in pool]); M = 10 ** (np.array([c["mag_db"] for c in pool]) / 20)
    T = M * np.exp(1j * np.radians(P))
    cache, out = {}, np.empty(target.shape, dtype=object)
    for idx, t in np.ndenumerate(target):
        if np.isnan(t): out[idx] = None; continue
        key = round(float(t), 3)
        if key not in cache:
            if rule == "paper":
                e = np.abs(CL.wrapdiff(P, t)); k = int(np.lexsort((-M, np.round(e, 3)))[0])
            else:
                k = int(np.argmin(np.abs(np.exp(1j * math.radians(t)) - T)))
            cache[key] = pool[k]
        out[idx] = cache[key]
    return out

# ---------------- boards (2-D, shapely) ----------------
class Board:
    def __init__(self, name, outline):
        self.name = name; self.L = {}; self.holes = []; self.txt = []; self.comp = []; self.add("OUTLINE", outline)
    def add(self, lay, g): self.L.setdefault(lay, []).append(g)
    def text(self, lay, s, x, y, h=3.0, rot=0): self.txt.append((lay, s, x, y, h, rot, "MIDDLE_CENTER"))
    def hole(self, lay, x, y, d, note=""): self.holes.append((lay, x, y, d, note))
    def component(self, ref, val, side, x, y, w, h, note=""): self.comp.append(dict(ref=ref, value=val, side=side, x=x, y=y, w=w, h=h, note=note))

def _disc(d): return Point(0, 0).buffer(d / 2, resolution=256)

def _rim_holes(b, n, rr, d, lay="NPTH", note="nylon M2.5 [ASSUMED]"):
    for k in range(n):
        a = 2 * math.pi * k / n; b.hole(lay, rr * math.cos(a), rr * math.sin(a), d, note)

def _arrow(b, lay, x0, y0, L, ang=0.0, w=1.2, head=5.0):
    shaft = box(0, -w / 2, L - head, w / 2); tip = Polygon([(L - head, -2.2), (L, 0), (L - head, 2.2)])
    for g in (shaft, tip): b.add(lay, translate(srot(g, ang, origin=(0, 0)), x0, y0))

def board_rlsa():
    """TLY-5 1.6 mm, slotted top copper, bottom copper removed (Sec. V), feed pocket on the bottom."""
    pairs = rlsa_pairs()
    b = Board("RLSA", _disc(R["D_diel"]))
    ext = max(max(np.hypot(*p["ca"]), np.hypot(*p["cb"])) + p["L"] / 2 for p in pairs)
    r_cu = math.ceil(ext + R["cu_margin"])
    b.r_cu = r_cu
    b.add("TOP_CU", _disc(2 * r_cu))
    for p in pairs:
        b.add("TOP_SLOT", slot_poly(p["ca"], p["ang_a"], p["L"])); b.add("TOP_SLOT", slot_poly(p["cb"], p["ang_b"], p["L"]))
    b.add("BOT_POCKET", _disc(R["head_d"]))                      # 0.6 mm deep blind pocket from the bottom (probe head)
    _rim_holes(b, H["n_holes"], H["R_holes"], H["hole_d"])
    b.text("SILK_TOP", "RLSA 20 GHz RHCP  TLY-5 1.6  960 slot pairs", 0, -(r_cu + 7), 3.0)
    b.text("SILK_TOP", "+x", H["R_holes"] - 10, 0, 3.0)
    b.text("FAB", "0.6 mm deep pocket d2.8 on BOTTOM (probe head)", 0, 6, 1.2)
    b.component("J1", "SMA 4-hole flange jack, extended pin [ASSUMED]", "bottom (through ground plate)", 0, 0, 12.7, 12.7)
    b.pairs = pairs
    return b

def board_ground():
    b = Board("GROUND", _disc(R["D_diel"]))
    b.hole("NPTH", 0, 0, R["sma_ptfe_d"], "SMA PTFE / pin clearance")
    s = R["sma_flange_holes"] / 2
    for sx in (-1, 1):
        for sy in (-1, 1): b.hole("NPTH", sx * s, sy * s, R["sma_hole_d"], "SMA flange screw (tap M2 or through)")
    _rim_holes(b, H["n_holes"], H["R_holes"], H["hole_d"])
    b.text("SILK_TOP", "GROUND PLATE  Al 3.0 mm", 0, -150, 4.0)
    return b

def board_hm(which, lib, rule="complex"):
    """HM I (correction + gradient) or HM II (gradient only).  Returns board + per-cell table."""
    pm = phase_maps(); tgt = pm["hm1"] if which == 1 else pm["hm2"]
    cellmap = assign_cells(tgt, lib, rule)
    outline = _disc(H["D_diel"]).difference(Polygon([(H["D_diel"] / 2 + 1, -H["notch"]), (H["D_diel"] / 2 - H["notch"], 0), (H["D_diel"] / 2 + 1, H["notch"])]))
    b = Board("HM%s" % ("I" if which == 1 else "II"), outline)
    rows = []; d = H["d"]
    for (j, i), c in np.ndenumerate(cellmap):
        if c is None: continue
        x, y = pm["x"][i], pm["y"][j]
        if c["type"] == 1:
            for lay, s in (("M1", c["a"]), ("M2", c["b"]), ("M3", c["a"]), ("M4", c["b"])):
                b.add(lay, box(x - s / 2, y - s / 2, x + s / 2, y + s / 2))
        elif c["r"] > 0:
            b.hole("DRILL", x, y, 2 * c["r"], "Type II non-plated through-hole")
        err = CL.wrapdiff(c["phase_norm"], tgt[j, i])
        rows.append(dict(i=i, j=j, x=x, y=y, target=tgt[j, i], type=c["type"], a=c["a"], b=c["b"], r=c["r"],
                         phase=c["phase_norm"], err=err, mag_db=c["mag_db"]))
    _rim_holes(b, H["n_holes"], H["R_holes"], H["hole_d"])
    _arrow(b, "SILK_TOP", -60, H["R_cells"] + 6.5, 120, 0)
    b.text("SILK_TOP", "PHASE-DELAY AXIS (+x)", 0, H["R_cells"] + 12.5, 3.0)
    b.text("SILK_TOP", b.name + ("  correction+gradient" if which == 1 else "  gradient only") + "  M1 = input (RLSA side)", 0, -(H["R_cells"] + 9), 3.0)
    for k in range(0, 24, 2):                                     # 30 deg rotation scale next to the holes
        a = 2 * math.pi * k / 24
        b.text("SILK_TOP", "%d" % (15 * k), (H["R_holes"] - 6) * math.cos(a), (H["R_holes"] - 6) * math.sin(a), 2.2, math.degrees(a) - 90)
    b.rows = rows
    return b
