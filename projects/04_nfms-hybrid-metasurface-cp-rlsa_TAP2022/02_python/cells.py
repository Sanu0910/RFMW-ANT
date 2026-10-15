"""Phase-shifting cells of the hybrid metasurfaces (HMs), Afzal, Esselle, Koli, IEEE TAP 70(1), Jan 2022, Sec. III.

Type I  (Fig. 4): 4 square copper patches (a, b, a, b from input to output) on 3 x 1.6 mm TLY-5 (er 2.2).
Type II (Fig. 6): 4.8 mm of TLY-5 with a non-plated through-hole of radius r at the cell centre, no metal.
Both cells: d = 7.5 mm (lambda0/2 at 20 GHz), h = 4.8 mm, normal incidence, plane wave along +z.

The paper uses full-wave unit-cell simulations that it does not tabulate. Here both cells have closed-form
models, so the whole design chain can be rebuilt and checked without a solver:
  Type I : transmission-line (ABCD) cascade, each patch layer a shunt capacitive grid
           (quasi-static patch-array formula, Luukkonen et al., IEEE TAP 56(6) 2008, eq. for the grid of patches).
  Type II: Maxwell Garnett effective permittivity of a slab with air cylinders (E transverse to the hole axis),
           then the exact slab S21.
Phase reference (both): S21 between the two outer faces of the 4.8 mm cell, the reference that reproduces the
paper's unnormalised numbers (bare slab -169 deg, Type II at r = 3.4 mm -134 deg).
Normalised phase (paper, Sec. III-B): unnormalised phase minus that of Type II at r = r_max, so 0 deg = largest hole.
The final values have to come from the HFSS unit-cell sweep in 04_hfss (hfss_hm_unitcell.py)."""
import math
import numpy as np

C0 = 299.792458          # mm * GHz
ETA0 = 376.730313668
EPS0 = 8.8541878128e-12
F0 = 20.0                # GHz, design frequency (Sec. IV)
ER = 2.2                 # Taconic TLY-5
TAND = 0.0009            # TLY-5 loss tangent (datasheet, 10 GHz) - used only for the loss estimate
T_LAM = 1.6              # mm, one laminate
N_LAM = 3
H_CELL = N_LAM * T_LAM   # 4.8 mm
D_CELL = 7.5             # mm
A_MIN, A_MAX, A_STEP = 0.2, 7.2, 0.1     # Type I sweep range of a and b (paper)
R_MAX = 3.4              # mm, Type II hole radius limit (mechanical, paper)
R_MIN_DRILL = 0.4        # mm, smallest hole drilled (d 0.8 mm in 4.8 mm = 6:1); a smaller hole shifts < 0.6 deg -> left out [ours]
PATCH_AREA_LIMIT = 0.36  # "maximum area of the metal patch limited to 36 % of the cell area" (Sec. I) -> a, b <= 4.5 mm
T_MIN_DB = -1.0          # transmission filter (paper)
C_SCALE = 1.42            # calibration factor on the grid capacitance, fitted by fit_c_scale() to the paper's example cell (Fig. 14)

def _slab(beta_t, z):
    c, s = np.cos(beta_t), np.sin(beta_t)
    return np.array([[c, 1j * z * s], [1j * s / z, c]], dtype=complex)

def _shunt(y):
    return np.array([[1, 0], [y, 1]], dtype=complex)

def grid_capacitance(a, d=D_CELL, eps_eff=ER, scale=None):
    """Quasi-static capacitance (F per square) of a grid of square patches of side a, period d (mm)."""
    g = d - a
    if a <= 0 or g <= 0: return 0.0 if a <= 0 else np.inf
    return (C_SCALE if scale is None else scale) * EPS0 * eps_eff * (2 * d * 1e-3 / math.pi) * math.log(1 / math.sin(math.pi * g / (2 * d)))

def s21_type1(a, b, f=F0, tand=0.0, scale=None):
    """Complex S21 of a Type I cell (patch sides a, b in mm)."""
    w = 2 * math.pi * f * 1e9
    er = ER * (1 - 1j * tand)
    k = 2 * math.pi * f / C0 * np.sqrt(er)           # rad/mm
    z = ETA0 / np.sqrt(er)
    out_eff, in_eff = (1 + ER) / 2, ER
    seq = [(a, out_eff), (b, in_eff), (a, in_eff), (b, out_eff)]
    m = np.eye(2, dtype=complex)
    for n, (s, ee) in enumerate(seq):
        m = m @ _shunt(1j * w * grid_capacitance(s, eps_eff=ee, scale=scale))
        if n < 3: m = m @ _slab(k * T_LAM, z)
    A, B, C, D = m[0, 0], m[0, 1], m[1, 0], m[1, 1]
    return 2 / (A + B / ETA0 + C * ETA0 + D)

def eps_mg(r, d=D_CELL, eh=ER, ei=1.0):
    """2-D Maxwell Garnett permittivity of a host eh with cylinders ei (fill f = pi r^2 / d^2), E transverse."""
    f = math.pi * r * r / (d * d)
    return eh * ((1 + f) * ei + (1 - f) * eh) / ((1 - f) * ei + (1 + f) * eh)

def s21_type2(r, f=F0, tand=0.0):
    er = eps_mg(r) * (1 - 1j * tand * (1 - math.pi * r * r / D_CELL ** 2))
    k = 2 * math.pi * f / C0 * np.sqrt(er); z = ETA0 / np.sqrt(er)
    A, B, C, D = _slab(k * H_CELL, z).ravel()
    return 2 / (A + B / ETA0 + C * ETA0 + D)

def phase_type2_unwrapped(r, f=F0):
    # one slab: the unwrapped insertion phase is close to -k h; take the branch next to it
    s = s21_type2(r, f); ph = math.degrees(np.angle(s))
    ref = -math.degrees(2 * math.pi * f / C0 * math.sqrt(eps_mg(r)) * H_CELL)
    return ph + 360 * round((ref - ph) / 360)

def library(f=F0, scale=None, area_limit=False, step=A_STEP, r_step=0.05, tand=0.0):
    """All cells.  Returns list of dicts: type, a, b, r, phase_unwrapped, phase_norm, mag_db."""
    av = np.round(np.arange(A_MIN, A_MAX + 1e-9, step), 3)
    ph = np.zeros((len(av), len(av))); mag = np.zeros_like(ph)
    for i, a in enumerate(av):
        for j, b in enumerate(av):
            s = s21_type1(a, b, f, tand, scale); ph[i, j] = math.degrees(np.angle(s)); mag[i, j] = 20 * math.log10(abs(s))
    # unwrap: first along b at the smallest a, then along a for every b; start on the bare-slab branch
    ph[0, :] = np.degrees(np.unwrap(np.radians(ph[0, :])))
    ph[0, :] += 360 * round((phase_type2_unwrapped(0.0, f) - ph[0, 0]) / 360)
    for j in range(len(av)):
        col = np.degrees(np.unwrap(np.radians(ph[:, j]))); ph[:, j] = col - col[0] + ph[0, j]
    ref = phase_type2_unwrapped(R_MAX, f)
    cells = []
    amax = math.sqrt(PATCH_AREA_LIMIT) * D_CELL
    for i, a in enumerate(av):
        for j, b in enumerate(av):
            if area_limit and max(a, b) > amax + 1e-9: continue
            cells.append(dict(type=1, a=float(a), b=float(b), r=0.0, phase_unwrapped=ph[i, j], phase_norm=ph[i, j] - ref, mag_db=mag[i, j]))
    for r in [0.0] + list(np.round(np.arange(R_MIN_DRILL, R_MAX + 1e-9, r_step), 3)):
        s = s21_type2(r, f)
        p = phase_type2_unwrapped(r, f)
        cells.append(dict(type=2, a=0.0, b=0.0, r=float(r), phase_unwrapped=p, phase_norm=p - ref, mag_db=20 * math.log10(abs(s))))
    return cells

def usable(cells, tmin=T_MIN_DB):
    return [c for c in cells if c["mag_db"] > tmin]

def wrapdiff(p, q):
    """Smallest signed difference p - q in degrees."""
    return (p - q + 180.0) % 360.0 - 180.0

def choose(cells, target):
    """Cell whose (normalised, wrapped) phase is closest to target; ties -> higher |S21| (paper: closest phase)."""
    best, key = None, None
    for c in cells:
        e = abs(wrapdiff(c["phase_norm"], target))
        k = (round(e, 3), -c["mag_db"])
        if key is None or k < key: best, key = c, k
    return best

def coverage(cells):
    """Covered normalised-phase intervals (wrapped to (-360, 0]) on a 1-degree grid, and the largest gap."""
    grid = np.zeros(360, bool)
    for c in cells: grid[int(math.floor(-(c["phase_norm"] % -360.0))) % 360] = True
    # largest run of False on the circle
    best = run = 0
    for v in np.concatenate([grid, grid]):
        run = 0 if v else run + 1; best = max(best, run)
    return grid, min(best, 360)

def fit_c_scale(a=4.0, b=3.7, target_norm=-171.0, f=F0):
    """Factor on the grid capacitance that puts the paper's example cell (Fig. 14: a 4, b 3.7 -> -171 deg) on target."""
    ref = phase_type2_unwrapped(R_MAX, f)
    def err(s):
        # continuous phase of (a, b) found by unwrapping along a straight path from the bare slab
        n = 60; prev = None; acc = None
        for t in np.linspace(0, 1, n + 1):
            p = math.degrees(np.angle(s21_type1(max(t * a, 1e-6), max(t * b, 1e-6), f, 0.0, s)))
            if prev is None: acc = p + 360 * round((phase_type2_unwrapped(0.0, f) - p) / 360)
            else: acc += wrapdiff(p, prev)
            prev = p
        return acc - ref - target_norm
    lo, hi = 0.2, 5.0
    for _ in range(60):
        m = (lo + hi) / 2
        if err(m) > 0: lo = m
        else: hi = m
    return (lo + hi) / 2

def load_table(path):
    """Read a cell table (e.g. results/hfss_cell_table.csv from the HFSS sweep) in the cell_library.csv format."""
    import csv
    out = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            out.append(dict(type=int(r["type"]), a=float(r["a_mm"]), b=float(r["b_mm"]), r=float(r["r_mm"]),
                            phase_unwrapped=float(r["phase_unwrapped_deg"]), phase_norm=float(r["phase_norm_deg"]), mag_db=float(r["S21_dB"])))
    return out
