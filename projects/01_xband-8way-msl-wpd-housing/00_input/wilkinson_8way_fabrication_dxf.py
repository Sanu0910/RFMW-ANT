#!/usr/bin/env python3
"""
X-band 8-way equal-split Wilkinson power divider on RO4350B (30 mil):
signal copper, top ground pour, via fences, stitching vias and board outline,
written to one DXF file.

Flow
----
1. Chebyshev multisection transformer synthesis (2*Z0 -> Z0 in each branch).
2. Hammerstad-Jensen microstrip synthesis: width, eps_eff, lambda_g, lambda_g/4.
3. Isolation resistor values from an odd-mode minimax optimisation (reported).
4. Binary tree (1->2, 2->4, 4->8) derived from the output Y coordinates. Every
   divider is mirror-symmetric, so all input-to-output paths are identical.
5. Signal copper: ONE closed outline (0402 pads are merged into it).
6. Ground pour: constant clearance from the signal copper, rounded corners,
   one simple polygon per region (no holes, no overlaps).
7. Vias: fence along every pour edge, a second row near junctions, resistors
   and board edges, and a stitching grid inside the pour.
8. Design-rule checks, then DXF export.

DXF layers
----------
TOP_COPPER       signal outline (closed LWPOLYLINE)
TOP_GROUND_POUR  ground polygons (closed LWPOLYLINEs)
VIA_PADS         via pads (CIRCLE)
VIA_HOLES        via drills (CIRCLE)
BOARD_OUTLINE    board edge (closed LWPOLYLINE)
RES_PADS_0402    optional reference rectangles of the resistor lands

Coordinates: millimetres, input port edge centred on (0,0), signal along +X.

Requirements:  Python 3.11+  and  ezdxf   (pip install ezdxf)
Run:           python wilkinson_8way_fabrication_dxf.py

Design decisions worth knowing
------------------------------
* The landing lines run to the connector edges of the board (edge-mount SMA),
  pulled back only by `edge_pullback_mm`. `board_margin_mm` therefore applies
  to the two edges without connectors.
* The via fence sits inside the pour, so its distance from a trace is at least
  the ground clearance plus the pad inset. `via_to_trace_edge_mm` only takes
  effect when the clearance is smaller than that distance.
* No connector footprint is drawn (the part is not specified). A keep-out
  zone around every port is kept free of vias.
* The line model is quasi-static; the top ground, junctions, bends and
  resistor parasitics are not compensated. Tune with a full-wave solver.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

import ezdxf
from ezdxf import units

Point = tuple[float, float]
ChainPoint = tuple[float, float, bool]      # (x, y, no-ground-allowed flag)


# =============================================================================
# 1. USER-EDITABLE PARAMETERS
# =============================================================================
@dataclass
class DesignConfig:
    # ---- Electrical specification -------------------------------------------
    f_low_hz: float = 8.0e9             # lower band edge
    f_high_hz: float = 12.0e9           # upper band edge
    f_center_hz: float = 10.0e9         # centre frequency
    z0_ohm: float = 50.0                # system impedance
    n_sections: int = 3                 # quarter-wave sections per branch
    fractional_bandwidth: float = 0.40  # Chebyshev design bandwidth (df/f0)

    # ---- Substrate: Rogers RO4350B, 30 mil ----------------------------------
    eps_r: float = 3.48                 # relative dielectric constant
    loss_tangent: float = 0.0037        # used for the loss estimate only
    substrate_h_mm: float = 0.762       # substrate thickness
    copper_t_mm: float = 0.035          # copper thickness

    # ---- Optional manual overrides (None = synthesise automatically) --------
    port_width_override_mm: float | None = None                  # 50-ohm line
    section_width_override_mm: tuple[float, ...] | None = None   # per section
    section_length_override_mm: tuple[float, ...] | None = None  # per section

    # ---- Output ports: Y coordinates (all end at the same X) ----------------
    # The number of ports must be a power of two. The tree is derived from
    # these values, so they fully define the branching geometry.
    output_y_mm: tuple[float, ...] = (
        -54.39, -38.07, -23.57, -7.25, 7.25, 23.57, 38.07, 54.39)

    # ---- 0402 (1005 metric) land pattern, IPC-7351 nominal ------------------
    pad_length_mm: float = 0.54         # pad size along the resistor axis
    pad_width_mm: float = 0.64          # pad size across the resistor axis
    pad_pitch_mm: float = 1.02          # pad centre-to-centre spacing
    export_pad_reference: bool = True   # draw land rectangles on own layer

    # ---- Signal layout ------------------------------------------------------
    connector_landing_mm: float = 12.0  # straight 50-ohm line at every port
    interstage_length_mm: float = 4.0   # straight 50-ohm line between stages
    bend_radius_ratio: float = 3.0      # 50-ohm bend radius / 50-ohm width
    section_arc_angle_deg: float = 50.0     # nominal arc angle of section bends
    min_branch_gap_mm: float = 0.30     # minimum slot width at a Y-junction
    taper_length_mm: float = 0.80       # smooth width transition at each step
    curve_step_mm: float = 0.05         # centre-line sampling step

    # ---- Top ground pour ----------------------------------------------------
    ground_clearance_factor: float = 2.5        # clearance / 50-ohm line width
    ground_clearance_mm: float | None = None    # fixed value overrides factor
    ground_corner_radius_mm: float = 0.50       # rounding of pour corners
    ground_step_mm: float = 0.10                # pour boundary sampling step

    # ---- Vias ---------------------------------------------------------------
    via_drill_mm: float = 0.20          # finished hole diameter
    via_pad_mm: float = 0.50            # pad diameter
    via_to_trace_edge_mm: float = 1.0   # wanted fence distance from a trace
    via_pour_edge_margin_mm: float = 0.20   # pad edge to pour edge
    via_pitch_divisor: float = 20.0     # fence pitch <= lambda_g(f_high) / this
    via_pitch_max_mm: float = 1.5       # absolute upper limit of fence pitch
    via_min_spacing_mm: float = 0.65    # minimum via centre-to-centre distance
    extra_via_reach_mm: float = 3.0     # extent of second row near hot spots
    stitch_pitch_mm: float = 2.5        # ground stitching grid (0 = off)

    # ---- Edge-mount SMA landing ---------------------------------------------
    connector_keepout_length_mm: float = 6.0    # via-free zone, from the edge
    connector_keepout_width_mm: float = 10.0    # via-free zone, across the line

    # ---- Board --------------------------------------------------------------
    edge_pullback_mm: float = 0.25      # copper to board edge (all copper)
    board_margin_mm: float = 5.0        # signal copper to non-connector edges
    ground_rim_mm: float = 4.0          # pour width outside the outer traces
    screw_margin_mm: float = 0.0        # extra room at non-connector edges
    board_height_override_mm: float | None = None

    # ---- Manufacturing rules ------------------------------------------------
    min_copper_spacing_mm: float = 0.20
    min_trace_width_mm: float = 0.15
    min_annular_ring_mm: float = 0.10

    # ---- Output -------------------------------------------------------------
    layer_copper: str = "TOP_COPPER"
    layer_ground: str = "TOP_GROUND_POUR"
    layer_via_pads: str = "VIA_PADS"
    layer_via_holes: str = "VIA_HOLES"
    layer_outline: str = "BOARD_OUTLINE"
    layer_res_pads: str = "RES_PADS_0402"
    dxf_version: str = "R2018"
    output_file: str = "Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady.dxf"


# =============================================================================
# 2. MICROSTRIP MODEL (Hammerstad-Jensen, 1980)
# =============================================================================
class Microstrip:
    """Quasi-static microstrip analysis and synthesis."""

    ETA0 = 376.730313668      # free-space wave impedance, ohm
    C0_MM = 299_792_458e3     # speed of light, mm/s

    def __init__(self, eps_r: float, h_mm: float, t_mm: float) -> None:
        self.eps_r = eps_r
        self.h = h_mm
        self.t = t_mm

    @classmethod
    def _z01(cls, u: float) -> float:
        """Impedance of the air-filled line, u = w/h."""
        f = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
        return cls.ETA0 / (2.0 * math.pi) * math.log(
            f / u + math.sqrt(1.0 + (2.0 / u) ** 2))

    @staticmethod
    def _eps_eff_static(u: float, er: float) -> float:
        """Effective permittivity for a zero-thickness strip."""
        a = (1.0
             + math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) / 49.0
             + math.log(1.0 + (u / 18.1) ** 3) / 18.7)
        b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
        return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (-a * b)

    def analyze(self, w_mm: float) -> tuple[float, float]:
        """Return (Z0 in ohm, eps_eff) for a strip of width w_mm."""
        u = w_mm / self.h
        tn = self.t / self.h
        # Strip-thickness correction -> equivalent widths u1 (air) and ur.
        du1 = tn / math.pi * math.log(
            1.0 + 4.0 * math.e * math.tanh(math.sqrt(6.517 * u)) ** 2 / tn)
        dur = 0.5 * (1.0 + 1.0 / math.cosh(math.sqrt(self.eps_r - 1.0))) * du1
        u1, ur = u + du1, u + dur
        eps_r_eq = self._eps_eff_static(ur, self.eps_r)
        z0 = self._z01(ur) / math.sqrt(eps_r_eq)
        eps_eff = eps_r_eq * (self._z01(u1) / self._z01(ur)) ** 2
        return z0, eps_eff

    def synthesize_width(self, z0_target: float) -> float:
        """Strip width (mm) for a target impedance. Z0 falls as w grows."""
        lo, hi = 1e-3 * self.h, 50.0 * self.h
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if self.analyze(mid)[0] > z0_target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def guided_wavelength(self, w_mm: float, f_hz: float) -> float:
        """Guided wavelength (mm) at f_hz."""
        return self.C0_MM / (f_hz * math.sqrt(self.analyze(w_mm)[1]))

    def dielectric_loss_db_per_mm(self, w_mm: float, f_hz: float, tan_d: float) -> float:
        """Dielectric attenuation of the line (dB/mm)."""
        e_eff = self.analyze(w_mm)[1]
        lambda0 = self.C0_MM / f_hz
        return (27.3 * self.eps_r / (self.eps_r - 1.0)
                * (e_eff - 1.0) / math.sqrt(e_eff) * tan_d / lambda0)


# =============================================================================
# 3. CHEBYSHEV MULTISECTION TRANSFORMER (small-reflection theory)
# =============================================================================
class ChebyshevTransformer:
    """N-section quarter-wave Chebyshev transformer from z_source to z_load."""

    def __init__(self, z_source: float, z_load: float, n: int, fbw: float) -> None:
        # Band edge electrical length: df/f0 = 2 - 4*theta_m/pi
        self.theta_m = math.pi / 4.0 * (2.0 - fbw)
        sec = 1.0 / math.cos(self.theta_m)
        t_n = math.cosh(n * math.acosh(sec))                 # T_N(sec theta_m)
        amp = math.log(z_load / z_source) / (2.0 * t_n)
        self.gamma_max = abs(amp)                            # passband ripple
        # Gamma_k = A * (coefficient of z^(N-2k)) in T_N(sec * (z + 1/z) / 2)
        coeff = self._chebyshev_laurent(n, sec)
        gammas = [amp * coeff[n - 2 * k] for k in range(n + 1)]
        # ln Z(k+1) = ln Z(k) + 2 * Gamma_k
        self.impedances: list[float] = []
        ln_z = math.log(z_source)
        for g in gammas[:-1]:
            ln_z += 2.0 * g
            self.impedances.append(math.exp(ln_z))

    @staticmethod
    def _chebyshev_laurent(n: int, s: float) -> dict[int, float]:
        """Coefficients {power: value} of T_n(s*(z + 1/z)/2) in powers of z."""
        t_prev: dict[int, float] = {0: 1.0}
        t_cur: dict[int, float] = {1: s / 2.0, -1: s / 2.0}
        for _ in range(n - 1):               # T(k+1) = 2x*T(k) - T(k-1)
            t_next: dict[int, float] = {}
            for p, c in t_cur.items():
                for dp in (1, -1):
                    t_next[p + dp] = t_next.get(p + dp, 0.0) + s * c
            for p, c in t_prev.items():
                t_next[p] = t_next.get(p, 0.0) - c
            t_prev, t_cur = t_cur, t_next
        return t_cur


# =============================================================================
# 4. ELECTRICAL DESIGN OF ONE 2-WAY DIVIDER (all seven are identical)
# =============================================================================
@dataclass
class Section:
    z0: float           # characteristic impedance, ohm
    width: float        # strip width, mm
    eps_eff: float      # effective dielectric constant
    lambda_g: float     # guided wavelength at f0, mm
    length: float       # lambda_g / 4, mm


class WilkinsonDesign:
    """Impedances, line dimensions and isolation resistors of a 2-way divider.

    Sections and resistors are ordered from the Y-junction towards the outputs.
    Resistor k bridges the two branches at the output end of section k.
    """

    def __init__(self, cfg: DesignConfig) -> None:
        self.cfg = cfg
        n = cfg.n_sections
        self.line = Microstrip(cfg.eps_r, cfg.substrate_h_mm, cfg.copper_t_mm)
        self.port = self._make_section(cfg.z0_ohm, cfg.port_width_override_mm, None)
        self.transformer = ChebyshevTransformer(
            2.0 * cfg.z0_ohm, cfg.z0_ohm, n, cfg.fractional_bandwidth)
        widths = cfg.section_width_override_mm or (None,) * n
        lengths = cfg.section_length_override_mm or (None,) * n
        if len(widths) != n or len(lengths) != n:
            raise ValueError("Section overrides need one value per section.")
        self.sections = [self._make_section(z, w, length) for z, w, length
                         in zip(self.transformer.impedances, widths, lengths)]
        self.resistors = self._optimise_resistors()

    def _make_section(self, z0: float, width: float | None,
                      length: float | None) -> Section:
        """Synthesise a line; a width / length override replaces the result."""
        w = width if width is not None else self.line.synthesize_width(z0)
        z_actual, eps_eff = self.line.analyze(w)
        lam = self.line.guided_wavelength(w, self.cfg.f_center_hz)
        return Section(z_actual, w, eps_eff, lam,
                       length if length is not None else lam / 4.0)

    # ---- Ideal transmission-line network analysis ---------------------------
    @staticmethod
    def _through_line(y_load: complex, zc: float, theta: float) -> complex:
        """Input admittance of a line (zc, theta) terminated in y_load."""
        yc, c, s = 1.0 / zc, math.cos(theta), math.sin(theta)
        return yc * (y_load * c + 1j * yc * s) / (yc * c + 1j * y_load * s)

    def _band(self, n_points: int = 41) -> list[float]:
        """Frequencies across the band, normalised to f0."""
        c = self.cfg
        return [(c.f_low_hz + (c.f_high_hz - c.f_low_hz) * i / (n_points - 1))
                / c.f_center_hz for i in range(n_points)]

    def _gamma_odd(self, fn: float, resistors: list[float]) -> complex:
        """Odd-mode reflection at an output (junction is a virtual short)."""
        theta = 0.5 * math.pi * fn
        z = [s.z0 for s in self.sections]
        y = -1j / (z[0] * math.tan(theta)) + 2.0 / resistors[0]
        for zk, rk in zip(z[1:], resistors[1:]):
            y = self._through_line(y, zk, theta) + 2.0 / rk
        y0 = 1.0 / self.cfg.z0_ohm
        return (y0 - y) / (y0 + y)

    def _gamma_even(self, fn: float, from_input: bool) -> complex:
        """Even-mode reflection seen from the input or from an output."""
        theta = 0.5 * math.pi * fn
        z = [s.z0 for s in self.sections]
        y_in, y_out = 0.5 / self.cfg.z0_ohm, 1.0 / self.cfg.z0_ohm
        y, y_ref, order = (y_out, y_in, reversed(z)) if from_input else (y_in, y_out, z)
        for zk in order:
            y = self._through_line(y, zk, theta)
        return (y_ref - y) / (y_ref + y)

    def _optimise_resistors(self) -> list[float]:
        """Minimise the worst in-band odd-mode reflection (pattern search)."""
        band = self._band()

        def cost(log_r: list[float]) -> float:
            r = [math.exp(v) for v in log_r]
            return max(abs(self._gamma_odd(fn, r)) for fn in band)

        x = [math.log(2.0 * self.cfg.z0_ohm * 2.0 ** k)
             for k in range(self.cfg.n_sections)]
        best, step = cost(x), 0.5
        while step > 1e-5:
            improved = False
            for i in range(len(x)):
                for delta in (step, -step):
                    trial = list(x)
                    trial[i] += delta
                    c = cost(trial)
                    if c < best:
                        x, best, improved = trial, c, True
            if not improved:
                step *= 0.5
        return [math.exp(v) for v in x]

    def worst_case_db(self) -> dict[str, float]:
        """Worst in-band |S11|, |S22|, |S23| (dB) of one ideal 2-way divider."""
        s11 = s22 = s23 = 0.0
        for fn in self._band():
            ge = self._gamma_even(fn, from_input=False)
            go = self._gamma_odd(fn, self.resistors)
            s11 = max(s11, abs(self._gamma_even(fn, from_input=True)))
            s22 = max(s22, abs(ge + go) / 2.0)
            s23 = max(s23, abs(ge - go) / 2.0)
        return {k: 20.0 * math.log10(max(v, 1e-12))
                for k, v in (("S11", s11), ("S22", s22), ("S23", s23))}


# =============================================================================
# 5. GEOMETRY HELPERS
# =============================================================================
class CenterLine:
    """Centre-line made of straights and tangent arcs, sampled densely."""

    def __init__(self, x: float, y: float, heading: float, step: float) -> None:
        self.x, self.y, self.heading, self.s = x, y, heading, 0.0
        self.step = step
        self.samples: list[tuple[float, float, float, float]] = [(x, y, heading, 0.0)]

    def straight(self, length: float) -> None:
        if length <= 0.0:
            return
        n = max(1, math.ceil(length / self.step))
        x0, y0, s0 = self.x, self.y, self.s
        dx, dy = math.cos(self.heading), math.sin(self.heading)
        for i in range(1, n + 1):
            d = length * i / n
            self.samples.append((x0 + d * dx, y0 + d * dy, self.heading, s0 + d))
        self.x, self.y, self.s = self.samples[-1][0], self.samples[-1][1], s0 + length

    def arc(self, radius: float, angle: float) -> None:
        """Tangent arc. angle > 0 turns left (CCW), angle < 0 turns right."""
        if abs(angle) < 1e-12:
            return
        sgn = 1.0 if angle > 0.0 else -1.0
        h0, s0 = self.heading, self.s
        cx = self.x - sgn * radius * math.sin(h0)      # arc centre
        cy = self.y + sgn * radius * math.cos(h0)
        n = max(2, math.ceil(radius * abs(angle) / self.step))
        for i in range(1, n + 1):
            h = h0 + angle * i / n
            self.samples.append((cx + sgn * radius * math.sin(h),
                                 cy - sgn * radius * math.cos(h),
                                 h, s0 + radius * abs(h - h0)))
        self.x, self.y, self.heading, self.s = self.samples[-1]

    def edges(self, width_at: Callable[[float], float]) -> tuple[list[Point], list[Point]]:
        """Left and right strip edges for a width profile w(s)."""
        left, right = [], []
        for x, y, h, s in self.samples:
            half = 0.5 * width_at(s)
            nx, ny = -math.sin(h), math.cos(h)
            left.append((x + half * nx, y + half * ny))
            right.append((x - half * nx, y - half * ny))
        return left, right


class PointGrid:
    """Uniform grid of points for fast 'is anything within r' queries."""

    def __init__(self, cell: float) -> None:
        self.cell = cell
        self._cells: dict[tuple[int, int], list[Point]] = defaultdict(list)

    def add(self, p: Point) -> None:
        self._cells[(math.floor(p[0] / self.cell), math.floor(p[1] / self.cell))].append(p)

    def extend(self, points: list[Point]) -> None:
        for p in points:
            self.add(p)

    def nearest(self, p: Point, radius: float) -> float:
        """Distance to the nearest stored point within `radius`, else inf."""
        x, y = p
        best = radius * radius
        found = False
        for ix in range(math.floor((x - radius) / self.cell),
                        math.floor((x + radius) / self.cell) + 1):
            for iy in range(math.floor((y - radius) / self.cell),
                            math.floor((y + radius) / self.cell) + 1):
                for qx, qy in self._cells.get((ix, iy), ()):
                    d2 = (qx - x) ** 2 + (qy - y) ** 2
                    if d2 < best:
                        best, found = d2, True
        return math.sqrt(best) if found else math.inf

    def any_within(self, p: Point, radius: float) -> bool:
        """True if a stored point lies closer than `radius` to p."""
        x, y = p
        r2 = radius * radius
        for ix in range(math.floor((x - radius) / self.cell),
                        math.floor((x + radius) / self.cell) + 1):
            for iy in range(math.floor((y - radius) / self.cell),
                            math.floor((y + radius) / self.cell) + 1):
                for qx, qy in self._cells.get((ix, iy), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < r2:
                        return True
        return False


def mirror_x(points: list[Point]) -> list[Point]:
    """Mirror points about the x axis."""
    return [(x, -y) for x, y in points]


def translate(points: list[Point], dx: float, dy: float) -> list[Point]:
    return [(x + dx, y + dy) for x, y in points]


def rectangle(cx: float, cy: float, size_x: float, size_y: float) -> list[Point]:
    hx, hy = 0.5 * size_x, 0.5 * size_y
    return [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)]


def drop_duplicates(points: list[Point], tol: float = 1e-9) -> list[Point]:
    """Remove consecutive coincident vertices (including last == first)."""
    out: list[Point] = []
    for p in points:
        if not out or math.dist(p, out[-1]) > tol:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= tol:
        out.pop()
    return out


def densify(points: list[Point], step: float) -> list[Point]:
    """Insert vertices so that no edge of the closed polygon exceeds `step`."""
    out: list[Point] = []
    n = len(points)
    for i in range(n):
        (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
        k = max(1, math.ceil(math.hypot(x1 - x0, y1 - y0) / step))
        out.extend((x0 + (x1 - x0) * j / k, y0 + (y1 - y0) * j / k) for j in range(k))
    return out


def remove_collinear(points: list[Point], tol: float = 1e-6) -> list[Point]:
    """Drop vertices of a closed polygon that lie on a straight edge."""
    out: list[Point] = []
    n = len(points)
    for i in range(n):
        ax, ay = out[-1] if out else points[-1]
        px, py = points[i]
        bx, by = points[(i + 1) % n]
        chord = math.hypot(bx - ax, by - ay)
        if chord < 1e-12:
            continue
        # Distance of p from the line a-b.
        if abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / chord > tol:
            out.append((px, py))
    return out


def polygon_area(points: list[Point]) -> float:
    """Signed area (positive for counter-clockwise polygons)."""
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                     in zip(points, points[1:] + points[:1]))


def left_normals(points: list[Point], closed: bool) -> list[Point]:
    """Unit normals pointing to the left of the direction of travel."""
    n = len(points)
    normals: list[Point] = []
    for k in range(n):
        if closed:
            (ax, ay), (bx, by) = points[k - 1], points[(k + 1) % n]
        else:
            (ax, ay), (bx, by) = points[max(k - 1, 0)], points[min(k + 1, n - 1)]
        tx, ty = bx - ax, by - ay
        length = math.hypot(tx, ty) or 1.0
        normals.append((-ty / length, tx / length))
    return normals


def find_spacing_violation(points: list[Point], min_dist: float
                           ) -> tuple[Point, Point, float] | None:
    """Minimum width / spacing check on a closed outline.

    Two boundary points that are closer than `min_dist` in the plane but far
    apart along the perimeter indicate a copper neck or gap that is too small,
    or a self-intersection. The outline must be sampled finer than `min_dist`.
    Uses a uniform grid so the run time is roughly linear in the vertex count.
    """
    n = len(points)
    perimeter = [0.0]
    for i in range(1, n):
        perimeter.append(perimeter[-1] + math.dist(points[i - 1], points[i]))
    total = perimeter[-1] + math.dist(points[-1], points[0])
    along_min = 4.0 * min_dist          # ignore neighbours on the same edge

    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, (x, y) in enumerate(points):
        ix, iy = math.floor(x / min_dist), math.floor(y / min_dist)
        for cx in (ix - 1, ix, ix + 1):
            for cy in (iy - 1, iy, iy + 1):
                for j in grid.get((cx, cy), ()):
                    d = math.dist(points[i], points[j])
                    if d < min_dist:
                        along = perimeter[i] - perimeter[j]
                        if min(along, total - along) > along_min:
                            return points[j], points[i], d
        grid[(ix, iy)].append(i)
    return None


# =============================================================================
# 6. ONE 2-WAY DIVIDER CELL (local coordinates, input at (0,0), axis along +x)
# =============================================================================
class DividerCell:
    """Geometry of one symmetric 3-section 2-way Wilkinson divider.

    Layout along +x:
        feed line -> Y-junction -> N quarter-wave sections -> arc bend that
        spreads the outputs to +/- pitch/2 -> straight 50-ohm tail.

    Each quarter-wave section is an outward bump built from four tangent arcs
    whose centre-line length equals lambda_g/4 exactly. The two branches meet
    again at every section end, where a 0402 resistor bridges them.

    Only the upper branch is computed; the lower one is its mirror image, so
    both branches have identical length.
    """

    def __init__(self, cfg: DesignConfig, design: WilkinsonDesign, pitch: float,
                 feed_length: float, tail_length: float) -> None:
        self.cfg, self.design = cfg, design
        self.pitch = pitch                      # output centre-to-centre spacing
        self.x_junction = feed_length
        self.tail_length = tail_length
        self.outer: list[Point] = []            # upper branch, outer edge
        self.inner: list[Point] = []            # upper branch, inner edge
        self.n_blocked = 0                      # inner[:n_blocked] faces the
        #                                         other branch (no ground there)
        self.slot: list[Point] = []             # rounded slot root at junction
        self.pads: list[list[Point]] = []       # 0402 land rectangles
        self.node_x: list[float] = []           # resistor positions on the axis
        self.section_lengths: list[float] = []  # drawn centre-line lengths
        self.branch_length = 0.0                # junction -> output, centre-line
        self.x_end = 0.0                        # x of the output port edges
        self.node_gap = 0.0                     # smallest gap between branches
        self._build()

    # ---- Section bump -------------------------------------------------------
    def _add_section(self, path: CenterLine, length: float, dy: float,
                     width: float) -> None:
        """Bump of given centre-line length ending dy above its start.

        Arc sequence (upper branch): left a1, right a1, right a2, left a2.
        All four arcs share one radius R, with a1 + a2 = 2 * nominal angle:
            length = 2 R (a1 + a2),    dy = 2 R (cos a2 - cos a1)
        """
        a_nom = math.radians(self.cfg.section_arc_angle_deg)
        radius = length / (4.0 * a_nom)
        if radius <= 0.5 * width:
            raise ValueError("Bend radius below half the strip width: "
                             "reduce section_arc_angle_deg.")
        d = dy / (2.0 * radius)
        lo, hi = 0.0, 2.0 * a_nom

        def f(a1: float) -> float:
            return math.cos(2.0 * a_nom - a1) - math.cos(a1) - d

        if f(lo) > 0.0 or f(hi) < 0.0:
            raise ValueError("Section offset too large for the chosen arc angle.")
        for _ in range(80):                       # f is monotonic on [lo, hi]
            mid = 0.5 * (lo + hi)
            if f(mid) < 0.0:
                lo = mid
            else:
                hi = mid
        a1 = 0.5 * (lo + hi)
        a2 = 2.0 * a_nom - a1
        path.arc(radius, +a1)
        path.arc(radius, -a1)
        path.arc(radius, -a2)
        path.arc(radius, +a2)

    # ---- Output spreading bend ----------------------------------------------
    @staticmethod
    def _add_s_bend(path: CenterLine, offset: float, radius: float) -> None:
        """Move the line sideways by `offset` (to the left) using arcs only."""
        if offset < 0.0:
            raise ValueError("Output pitch is too small for the divider.")
        if offset <= 2.0 * radius:
            a = math.acos(1.0 - offset / (2.0 * radius))
            path.arc(radius, +a)
            path.arc(radius, -a)
        else:                                     # large offset: 90-deg arcs
            path.arc(radius, +math.pi / 2.0)
            path.straight(offset - 2.0 * radius)
            path.arc(radius, -math.pi / 2.0)

    # ---- Width profile with smooth steps ------------------------------------
    def _width_profile(self, nodes: list[float], widths: list[float]
                       ) -> Callable[[float], float]:
        """w(s): widths[k] before nodes[k], cosine-blended across each node."""
        half = 0.5 * self.cfg.taper_length_mm

        def width_at(s: float) -> float:
            for k, s_node in enumerate(nodes):
                if s < s_node - half:
                    return widths[k]
                if s <= s_node + half:
                    t = (s - (s_node - half)) / (2.0 * half)
                    blend = 0.5 * (1.0 - math.cos(math.pi * t))
                    return widths[k] + (widths[k + 1] - widths[k]) * blend
            return widths[-1]

        return width_at

    # ---- Resistor land merged into the strip edge ---------------------------
    @staticmethod
    def _merge_pad(edge: list[Point], x_left: float, x_right: float,
                   y_pad: float) -> list[Point]:
        """Extend the inner strip edge down to the inner edge of a pad.

        Between x_left and x_right the edge is lowered to y_pad, with a
        vertical step at each side. The pad becomes part of the outline, so no
        separate (overlapping) pad polygon is needed on the copper layer.
        """
        def y_at(x: float, a: Point, b: Point) -> float:
            return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])

        i0 = next(i for i, p in enumerate(edge) if p[0] >= x_left)
        i1 = i0
        while edge[i1 + 1][0] <= x_right:
            i1 += 1
        y_l = y_at(x_left, edge[i0 - 1], edge[i0])
        y_r = y_at(x_right, edge[i1], edge[i1 + 1])
        lowered = [(x, min(y, y_pad)) for x, y in edge[i0:i1 + 1]]
        return (edge[:i0] + [(x_left, y_l), (x_left, min(y_l, y_pad))] + lowered
                + [(x_right, min(y_r, y_pad)), (x_right, y_r)] + edge[i1 + 1:])

    # ---- Assembly -----------------------------------------------------------
    def _build(self) -> None:
        cfg, des = self.cfg, self.design
        w50 = des.port.width
        sec = des.sections
        widths = [s.width for s in sec] + [w50]   # along one branch
        pad_inner = 0.5 * (cfg.pad_pitch_mm - cfg.pad_length_mm)
        pad_outer = 0.5 * (cfg.pad_pitch_mm + cfg.pad_length_mm)

        # Centre-line height of the upper branch at the junction and at each
        # resistor node. At a node the inner strip edge sits on the inner pad
        # edge, so the resistor lands directly on the two branches.
        x_j = self.x_junction
        y_nodes = [max(0.5 * (w50 - sec[0].width),
                       0.5 * (sec[0].width + cfg.min_branch_gap_mm))]
        for k in range(len(sec)):
            w_min, w_max = sorted((widths[k], widths[k + 1]))
            y = pad_inner + 0.5 * w_max
            if y - 0.5 * w_min >= pad_outer or y + 0.5 * w_min <= pad_outer:
                raise ValueError("0402 pad does not fit on the strip at a node.")
            y_nodes.append(y)

        # Upper-branch centre-line: sections, spreading bend, straight tail.
        path = CenterLine(x_j, y_nodes[0], 0.0, cfg.curve_step_mm)
        node_s: list[float] = []
        for k, s in enumerate(sec):
            s_start = path.s
            self._add_section(path, s.length, y_nodes[k + 1] - y_nodes[k], s.width)
            self.section_lengths.append(path.s - s_start)
            node_s.append(path.s)
            self.node_x.append(path.x)
        self._add_s_bend(path, 0.5 * self.pitch - path.y, cfg.bend_radius_ratio * w50)
        path.straight(self.tail_length)
        self.branch_length = path.s
        self.x_end = path.x

        self.outer, inner = path.edges(self._width_profile(node_s, widths))
        # Snap the port corners so the outputs land exactly on +/- pitch/2.
        self.outer[-1] = (self.x_end, 0.5 * self.pitch + 0.5 * w50)
        inner[-1] = (self.x_end, 0.5 * self.pitch - 0.5 * w50)

        # Merge the resistor lands into the inner edge and keep reference
        # rectangles (resistor axis along y, one land on each branch).
        half_w = 0.5 * cfg.pad_width_mm
        for x in self.node_x:
            inner = self._merge_pad(inner, x - half_w, x + half_w, pad_inner)
            for sign in (1.0, -1.0):
                self.pads.append(rectangle(x, sign * 0.5 * cfg.pad_pitch_mm,
                                           cfg.pad_width_mm, cfg.pad_length_mm))
        self.inner = inner
        # The inner edge faces the other branch up to the last resistor land.
        self.n_blocked = next(i for i, p in enumerate(inner)
                              if p[0] > self.node_x[-1] + half_w + 1e-9)

        # Rounded root of the slot between the branches (smooth Y-junction):
        # a half circle tangent to both inner strip edges, cut into the feed.
        r_slot = y_nodes[0] - 0.5 * sec[0].width
        self.slot_radius = r_slot
        n_arc = 48
        self.slot = [(x_j + r_slot * math.cos(a), r_slot * math.sin(a))
                     for a in (math.pi / 2.0 + math.pi * i / n_arc
                               for i in range(1, n_arc))]

        # Smallest copper gap between the two branches (slot or pad gap).
        self.node_gap = min(2.0 * r_slot, 2.0 * pad_inner)


# =============================================================================
# 7. BINARY TREE LAYOUT (signal copper)
# =============================================================================
def derive_stage_pitches(output_y: tuple[float, ...], tol: float = 1e-6
                         ) -> tuple[float, list[float]]:
    """Derive the tree from the output Y coordinates.

    Adjacent outputs are paired; each divider sits at the midpoint of its two
    outputs. Returns (root_y, [pitch of stage 1, stage 2, ...]).

    All dividers of one stage must share the same output pitch; otherwise the
    stage would not be built from identical cells and the electrical lengths
    to the outputs would differ.
    """
    ys = sorted(output_y)
    n = len(ys)
    if n < 2 or n & (n - 1):
        raise ValueError("The number of output ports must be a power of two.")
    pitches: list[float] = []
    while len(ys) > 1:
        pairs = [(ys[i], ys[i + 1]) for i in range(0, len(ys), 2)]
        stage = [b - a for a, b in pairs]
        if max(stage) - min(stage) > tol:
            raise ValueError("Output spacing is not uniform within a stage: "
                             "equal path lengths are not possible with "
                             "identical dividers.")
        pitches.append(stage[0])
        ys = [0.5 * (a + b) for a, b in pairs]
    return ys[0], pitches[::-1]


class WilkinsonTreeLayout:
    """Complete N-way divider as one closed signal-copper outline.

    Besides the outline, the boundary walk records one open chain per ground
    region: the stretch of copper edge between two neighbouring ports. The
    ground pour is later built from these chains.
    """

    def __init__(self, cfg: DesignConfig, design: WilkinsonDesign) -> None:
        self.cfg, self.design = cfg, design
        root_y, self.pitches = derive_stage_pitches(cfg.output_y_mm)
        if abs(root_y) > 1e-6:
            raise ValueError("Output ports are not centred on the input (y = 0).")

        # One cell per stage; every divider of a stage is a translated copy.
        # The first feed and the last tails are the SMA landing lines.
        n_stages = len(self.pitches)
        self.cells = [
            DividerCell(
                cfg, design, pitch,
                feed_length=cfg.connector_landing_mm if k == 0 else 0.0,
                tail_length=(cfg.connector_landing_mm if k == n_stages - 1
                             else cfg.interstage_length_mm))
            for k, pitch in enumerate(self.pitches)]

        self.pads: list[list[Point]] = []           # 0402 land rectangles
        self.output_ports: list[Point] = []
        self.junctions: list[Point] = []            # Y-junction centres
        self.resistor_nodes: list[Point] = []       # resistor centres
        self.chains: list[list[ChainPoint]] = [[]]  # copper edge per region
        raw: list[Point] = []
        self._walk(0, 0.0, 0.0, raw)
        raw = drop_duplicates(raw)
        self.dense = densify(raw, cfg.curve_step_mm)    # used by the checks
        self.outline = remove_collinear(raw)            # written to the DXF
        self.output_ports.sort(key=lambda p: p[1])
        self.x_end = self.output_ports[0][0]
        self.path_length = cfg.connector_landing_mm + sum(
            c.branch_length for c in self.cells)

    def _walk(self, stage: int, x0: float, y0: float, raw: list[Point]) -> None:
        """Walk the copper boundary of the sub-tree with input at (x0, y0).

        Order: feed top edge -> upper branch outer edge -> (upper child
        sub-tree or output port) -> upper inner edge back to the junction ->
        slot root -> lower inner edge -> (lower child or port) -> lower outer
        edge back. The walk is continuous, so the tree is one closed polygon,
        and the copper is always on the right-hand side of the walk.
        """
        cell = self.cells[stage]
        w50 = self.design.port.width
        last = stage == len(self.cells) - 1
        x_out, dy = x0 + cell.x_end, 0.5 * cell.pitch
        nb = cell.n_blocked

        def emit(local: list[Point], blocked: bool) -> None:
            for x, y in local:
                p = (x + x0, y + y0)
                raw.append(p)
                self.chains[-1].append((p[0], p[1], blocked))

        def child(y_child: float) -> None:
            if last:                              # port edge: next ground region
                self.output_ports.append((x_out, y_child))
                self.chains.append([])
            else:
                self._walk(stage + 1, x_out, y_child, raw)

        self.junctions.append((x0 + cell.x_junction, y0))
        self.resistor_nodes += [(x0 + x, y0) for x in cell.node_x]
        self.pads += [translate(p, x0, y0) for p in cell.pads]

        emit([(0.0, 0.5 * w50), (cell.x_junction, 0.5 * w50)] + cell.outer, False)
        child(y0 + dy)
        emit(cell.inner[nb - 1:][::-1], False)
        emit(cell.inner[:nb][::-1] + cell.slot + mirror_x(cell.inner[:nb]), True)
        emit(mirror_x(cell.inner[nb - 1:]), False)
        child(y0 - dy)
        emit(mirror_x(cell.outer)[::-1]
             + [(cell.x_junction, -0.5 * w50), (0.0, -0.5 * w50)], False)


# =============================================================================
# 8. CONNECTOR LANDINGS (edge-mount SMA)
# =============================================================================
@dataclass(frozen=True)
class ConnectorLanding:
    """Straight 50-ohm landing at a board edge with a via keep-out zone."""
    x_edge: float       # x of the port (start of the landing line)
    y: float            # centre of the landing line
    inward: float       # +1: board interior towards +x, -1: towards -x
    length: float       # keep-out length measured from the port
    width: float        # keep-out width across the line

    def keepout_contains(self, p: Point) -> bool:
        along = (p[0] - self.x_edge) * self.inward
        return along <= self.length and abs(p[1] - self.y) <= 0.5 * self.width


class ConnectorPlanner:
    """Creates the landing / keep-out description for every port."""

    def __init__(self, cfg: DesignConfig, layout: WilkinsonTreeLayout) -> None:
        if cfg.connector_landing_mm < cfg.connector_keepout_length_mm:
            raise ValueError("Landing line shorter than the connector keep-out.")
        size = (cfg.connector_keepout_length_mm, cfg.connector_keepout_width_mm)
        self.landings = [ConnectorLanding(0.0, 0.0, +1.0, *size)] + [
            ConnectorLanding(x, y, -1.0, *size) for x, y in layout.output_ports]

    def in_keepout(self, p: Point) -> bool:
        return any(c.keepout_contains(p) for c in self.landings)


# =============================================================================
# 9. BOARD OUTLINE
# =============================================================================
class BoardOutline:
    """Rectangular board sized from the layout.

    Connector edges (left / right): `edge_pullback_mm` beyond the ports.
    Other edges: signal copper + max(board margin, clearance + ground rim).
    """

    def __init__(self, cfg: DesignConfig, layout: WilkinsonTreeLayout,
                 clearance: float) -> None:
        y_copper = max(abs(y) for _, y in layout.outline)
        half = (y_copper + max(cfg.board_margin_mm, clearance + cfg.ground_rim_mm)
                + cfg.screw_margin_mm)
        if cfg.board_height_override_mm is not None:
            half = 0.5 * cfg.board_height_override_mm
            if half < y_copper + clearance + cfg.edge_pullback_mm + 1.0:
                raise ValueError("board_height_override_mm is too small.")
        self.x_min = -cfg.edge_pullback_mm
        self.x_max = layout.x_end + cfg.edge_pullback_mm
        self.y_max = half
        self.y_min = -half
        # Limits of all copper (pour and traces) inside the board.
        self.copper_x0, self.copper_x1 = 0.0, layout.x_end
        self.copper_y = half - cfg.edge_pullback_mm

    def polygon(self) -> list[Point]:
        return [(self.x_min, self.y_min), (self.x_max, self.y_min),
                (self.x_max, self.y_max), (self.x_min, self.y_max)]

    @property
    def size(self) -> tuple[float, float]:
        return self.x_max - self.x_min, self.y_max - self.y_min


# =============================================================================
# 10. TOP GROUND POUR
# =============================================================================
class GroundPour:
    """Ground polygons with constant clearance g from the signal copper.

    Method (per region chain of the copper boundary):
      1. Offset every boundary point along its normal by D = g + r.
      2. Keep only offset points that are at least D away from ALL signal
         copper. What survives is the true outline of the keep-out area grown
         by r; the removed stretches are the places where offsets of different
         edges cross (inner bends, the fork between two branches).
      3. Pull the surviving points back by r (giving exactly clearance g) and
         bridge every removed stretch with an arc of radius r around the
         crossing point. This rounds every pour corner, removes pour slivers
         narrower than 2r and never reduces the clearance below g.
    Regions between the two coupled branches of a divider are never filled.

    Only the upper half and the central region are computed; the lower half is
    mirrored, which keeps the pour exactly symmetric.
    """

    VALID_TOL = 0.01        # mm, tolerance of the distance test
    GAP_LIMIT = 2.5         # mm, largest chord accepted across a corner

    def __init__(self, cfg: DesignConfig, layout: WilkinsonTreeLayout,
                 board: BoardOutline, clearance: float) -> None:
        self.cfg, self.layout, self.board = cfg, layout, board
        self.clearance = clearance
        self.radius = cfg.ground_corner_radius_mm
        self._copper = PointGrid(1.0)
        self._copper.extend(layout.dense)

        n_half = len(cfg.output_y_mm) // 2
        upper: list[list[Point]] = []
        for index in range(n_half + 1):             # n_half = central region
            boundary = self._offset_chain(self._resample(layout.chains[index]))
            if index == 0:                          # outer region: board corners
                boundary += [(board.copper_x1, board.copper_y),
                             (board.copper_x0, board.copper_y)]
            if polygon_area(boundary) <= 0.0:
                raise ValueError("Ground region is degenerate: reduce the "
                                 "ground clearance.")
            upper.append(boundary)
        self.half_polygons = upper                  # upper regions + central
        lower = [mirror_x(p)[::-1] for p in upper[:n_half]]
        self.polygons = [remove_collinear(p) for p in upper + lower[::-1]]

    def _resample(self, chain: list[ChainPoint]) -> list[ChainPoint]:
        """Resample a chain to roughly `ground_step_mm` point spacing."""
        step = self.cfg.ground_step_mm
        out: list[ChainPoint] = [chain[0]]
        for x1, y1, b1 in chain[1:]:
            x0, y0, b0 = out[-1]
            d = math.hypot(x1 - x0, y1 - y0)
            if d < 1e-9:
                continue
            k = math.ceil(d / step)
            if k > 1:                               # long straight edge
                out.extend((x0 + (x1 - x0) * j / k, y0 + (y1 - y0) * j / k,
                            b0 or b1) for j in range(1, k))
                out.append((x1, y1, b1))
            elif d >= 0.6 * step or b1 != b0:
                out.append((x1, y1, b1))
        end = chain[-1]
        if math.hypot(out[-1][0] - end[0], out[-1][1] - end[1]) > 1e-9:
            out.append(end)
        return out

    def _offset_chain(self, chain: list[ChainPoint]) -> list[Point]:
        g, r = self.clearance, self.radius
        dist = g + r
        pts = [(x, y) for x, y, _ in chain]
        normals = left_normals(pts, closed=False)   # ground is on the left
        raw = [(x + dist * nx, y + dist * ny) for (x, y), (nx, ny) in zip(pts, normals)]
        valid = [not blocked
                 and not self._copper.any_within(q, dist - self.VALID_TOL)
                 for q, (_, _, blocked) in zip(raw, chain)]
        if not (valid[0] and valid[-1]):
            raise ValueError("No room for ground next to a port: reduce the "
                             "ground clearance or widen the port spacing.")
        out: list[Point] = []
        last = -1
        for k, ok in enumerate(valid):
            if not ok:
                continue
            if last >= 0 and k > last + 1:
                out += self._fillet(raw, normals, last, k)
            x, y = pts[k]
            out.append((x + g * normals[k][0], y + g * normals[k][1]))
            last = k
        return out

    def _fillet(self, raw: list[Point], normals: list[Point], i: int, j: int
                ) -> list[Point]:
        """Arc of radius r bridging the removed stretch between raw[i], raw[j]."""
        qa, qb = raw[i], raw[j]
        if math.dist(qa, qb) > self.GAP_LIMIT:
            raise ValueError(
                f"Ground pour topology not supported near ({qa[0]:.2f}, "
                f"{qa[1]:.2f}): reduce the ground clearance.")
        # Corner = crossing of the two offset curves (tangent-line estimate).
        mid = (0.5 * (qa[0] + qb[0]), 0.5 * (qa[1] + qb[1]))
        (nax, nay), (nbx, nby) = normals[i], normals[j]
        ta, tb = (nay, -nax), (nby, -nbx)
        cross = ta[0] * tb[1] - ta[1] * tb[0]
        corner = mid
        if abs(cross) > 1e-6:
            s = ((qb[0] - qa[0]) * tb[1] - (qb[1] - qa[1]) * tb[0]) / cross
            cand = (qa[0] + s * ta[0], qa[1] + s * ta[1])
            if math.dist(cand, mid) <= self.GAP_LIMIT:
                corner = cand

        def normal_at(k: int, k_next: int) -> Point:
            """Normal of the offset curve at the corner (interpolated)."""
            (x0, y0), (x1, y1) = raw[k], raw[k_next]
            dx, dy = x1 - x0, y1 - y0
            f = ((corner[0] - x0) * dx + (corner[1] - y0) * dy) / (dx * dx + dy * dy or 1.0)
            f = min(1.0, max(0.0, f))
            nx = normals[k][0] + f * (normals[k_next][0] - normals[k][0])
            ny = normals[k][1] + f * (normals[k_next][1] - normals[k][1])
            length = math.hypot(nx, ny) or 1.0
            return nx / length, ny / length

        na, nb = normal_at(i, i + 1), normal_at(j, j - 1)
        a0 = math.atan2(-na[1], -na[0])
        sweep = (math.atan2(-nb[1], -nb[0]) - a0 + math.pi) % (2.0 * math.pi) - math.pi
        r = self.radius
        m = max(1, math.ceil(abs(sweep) * r / self.cfg.curve_step_mm))
        return [(corner[0] + r * math.cos(a0 + sweep * t / m),
                 corner[1] + r * math.sin(a0 + sweep * t / m)) for t in range(m + 1)]


def ground_clearance(cfg: DesignConfig, design: WilkinsonDesign) -> float:
    """Constant pour clearance: fixed value, or factor x 50-ohm line width."""
    if cfg.ground_clearance_mm is not None:
        return cfg.ground_clearance_mm
    return cfg.ground_clearance_factor * design.port.width


# =============================================================================
# 11. VIAS (fence, extra rows, stitching)
# =============================================================================
class ViaGenerator:
    """Ground vias, generated for the upper half and mirrored about y = 0.

    Row 1  : along every pour edge (both sides of every line, and the board
             edges), at the fence pitch.
    Row 2  : a second row behind row 1 near Y-junctions and resistors and
             along the board edges.
    Stitch : regular grid inside the pour to suppress parallel-plate modes.
    Vias are never placed inside a connector keep-out zone.
    """

    def __init__(self, cfg: DesignConfig, design: WilkinsonDesign,
                 layout: WilkinsonTreeLayout, board: BoardOutline,
                 pour: GroundPour, connectors: ConnectorPlanner) -> None:
        self.cfg, self.board, self.connectors = cfg, board, connectors
        lam = design.line.guided_wavelength(design.port.width, cfg.f_high_hz)
        self.pitch = min(cfg.via_pitch_max_mm, lam / cfg.via_pitch_divisor)
        if self.pitch < cfg.via_min_spacing_mm:
            raise ValueError("Fence pitch is below the minimum via spacing.")
        # Distance of the first row from the pour edge.
        self.inset = max(0.5 * cfg.via_pad_mm + cfg.via_pour_edge_margin_mm,
                         cfg.via_to_trace_edge_mm - pour.clearance)
        self.row_spacing = max(cfg.via_min_spacing_mm, 0.866 * self.pitch)
        self.trace_distance = pour.clearance + self.inset
        self.counts: dict[str, int] = {}

        self._placed: list[Point] = []              # upper half (y >= 0)
        self._via_grid = PointGrid(1.0)
        self._edge_grid = PointGrid(0.5)            # pour boundary points
        dense = [densify(p, cfg.ground_step_mm) for p in pour.half_polygons]
        for poly in dense:
            self._edge_grid.extend(poly)

        hot = self._hot_flags(dense, layout)
        before = 0
        for name, inset, use_flags in (("fence", self.inset, False),
                                       ("extra", self.inset + self.row_spacing, True)):
            for poly, flags in zip(dense, hot):
                self._place_row(poly, inset, flags if use_flags else None)
            self.counts[name] = len(self._placed) - before
            before = len(self._placed)
        if cfg.stitch_pitch_mm > 0.0:
            self._place_stitching(pour.half_polygons)
        self.counts["stitch"] = len(self._placed) - before

        # Mirror about the x axis. Vias on the axis are kept once.
        self.vias: list[Point] = []
        for x, y in self._placed:
            if y < 0.5 * cfg.via_min_spacing_mm:
                self.vias.append((x, 0.0))
            else:
                self.vias += [(x, y), (x, -y)]

    # ---- Where a second row is wanted ---------------------------------------
    def _hot_flags(self, dense: list[list[Point]], layout: WilkinsonTreeLayout
                   ) -> list[list[bool]]:
        """Per boundary point: near a junction / resistor, or on a board edge."""
        b, eps = self.board, 1e-6
        spots = [p for p in layout.junctions + layout.resistor_nodes if p[1] > -eps]
        # Reach of every hot spot: its distance to the pour plus a margin.
        reach = []
        for hx, hy in spots:
            nearest = min(math.hypot(x - hx, y - hy) for poly in dense for x, y in poly)
            reach.append((nearest + self.cfg.extra_via_reach_mm) ** 2)
        flags: list[list[bool]] = []
        for poly in dense:
            row = []
            for x, y in poly:
                on_edge = (x < b.copper_x0 + eps or x > b.copper_x1 - eps
                           or y > b.copper_y - eps)
                row.append(on_edge or any(
                    (x - hx) ** 2 + (y - hy) ** 2 <= r2
                    for (hx, hy), r2 in zip(spots, reach)))
            flags.append(row)
        return flags

    # ---- Rows along the pour boundary ---------------------------------------
    def _place_row(self, poly: list[Point], inset: float,
                   flags: list[bool] | None) -> None:
        """Vias on the curve `inset` inside a (counter-clockwise) polygon."""
        normals = left_normals(poly, closed=True)   # pointing into the pour
        n = len(poly)
        cands: list[Point | None] = []
        for k, ((x, y), (nx, ny)) in enumerate(zip(poly, normals)):
            c = (x + inset * nx, y + inset * ny)
            ok = ((flags is None or flags[k])
                  and not self._edge_grid.any_within(c, inset - 0.01))
            cands.append(c if ok else None)
        if all(c is None for c in cands):
            return
        # Start right after a break so that no run wraps around the list end.
        start = next((k for k in range(n) if cands[k] is None), 0)
        run: list[Point] = []
        prev: Point | None = None
        for step in range(1, n + 1):
            c = cands[(start + step) % n]
            if c is None:
                self._place_run(run)
                run, prev = [], None
                continue
            if c[1] >= 0.0:
                if prev is not None and prev[1] < 0.0:      # entering upper half
                    run = [self._axis_point(prev, c)]
                run.append(c)
            elif prev is not None and prev[1] >= 0.0:       # leaving upper half
                run.append(self._axis_point(prev, c))
                self._place_run(run)
                run = []
            prev = c
        self._place_run(run)

    @staticmethod
    def _axis_point(a: Point, b: Point) -> Point:
        """Point where the segment a-b crosses y = 0."""
        t = a[1] / (a[1] - b[1])
        return a[0] + t * (b[0] - a[0]), 0.0

    def _place_run(self, run: list[Point]) -> None:
        """Evenly spaced vias (spacing <= pitch) along an open run."""
        if not run:
            return
        cum = [0.0]
        for a, b in zip(run, run[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        total = cum[-1]
        count = max(1, math.ceil(total / self.pitch))
        k = 0
        for i in range(count):
            target = (i + 0.5) * total / count
            while k < len(run) - 2 and cum[k + 1] < target:
                k += 1
            seg = cum[k + 1] - cum[k] if len(run) > 1 else 0.0
            t = (target - cum[k]) / seg if seg > 0.0 else 0.0
            a, b = run[k], run[min(k + 1, len(run) - 1)]
            self._try_add((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])),
                          self.cfg.via_min_spacing_mm)

    def _try_add(self, p: Point, min_dist: float) -> bool:
        if self.connectors.in_keepout(p):
            return False
        if self._via_grid.any_within(p, min_dist - 1e-9):
            return False
        self._via_grid.add(p)
        self._placed.append(p)
        return True

    # ---- Stitching grid -----------------------------------------------------
    def _place_stitching(self, polygons: list[list[Point]]) -> None:
        """Grid vias inside the pour (scan-line fill of each polygon)."""
        pitch = self.cfg.stitch_pitch_mm
        x_start = self.board.copper_x0 + 0.5 * pitch
        rows = math.ceil(self.board.copper_y / pitch)
        for poly in polygons:
            edges = list(zip(poly, poly[1:] + poly[:1]))
            for j in range(rows):
                y = (j + 0.5) * pitch
                xs = sorted(x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                            for (x0, y0), (x1, y1) in edges
                            if (y0 <= y) != (y1 <= y))
                for x_in, x_out in zip(xs[::2], xs[1::2]):
                    i = math.ceil((x_in - x_start) / pitch)
                    while x_start + i * pitch < x_out:
                        p = (x_start + i * pitch, y)
                        if not self._edge_grid.any_within(p, self.inset):
                            self._try_add(p, 0.6 * pitch)
                        i += 1


# =============================================================================
# 12. DESIGN-RULE CHECKS
# =============================================================================
class DesignRuleCheck:
    """Geometry checks. `run` raises ValueError on the first failure."""

    def __init__(self, cfg: DesignConfig, design: WilkinsonDesign,
                 layout: WilkinsonTreeLayout, board: BoardOutline,
                 pour: GroundPour, vias: ViaGenerator) -> None:
        self.cfg, self.design, self.layout = cfg, design, layout
        self.board, self.pour, self.vias = board, pour, vias

    def run(self) -> list[str]:
        cfg, lay = self.cfg, self.layout
        w50 = self.design.port.width
        rule = cfg.min_copper_spacing_mm
        done: list[str] = []

        # 1. Sampling must be finer than the rule for the outline checks.
        if cfg.curve_step_mm > 0.5 * rule:
            raise ValueError("curve_step_mm must be <= min_copper_spacing_mm / 2.")

        # 2. Minimum trace width.
        w_min = min(s.width for s in self.design.sections)
        if w_min < cfg.min_trace_width_mm:
            raise ValueError(f"Trace width {w_min:.3f} mm is below the rule.")
        done.append(f"minimum trace width {w_min:.3f} mm")

        # 3. Gap between the branches of a divider; room for the slot root.
        gap = min(c.node_gap for c in lay.cells)
        if gap < rule:
            raise ValueError(f"Branch gap {gap:.3f} mm is below the rule.")
        feed_min = min(cfg.connector_landing_mm, cfg.interstage_length_mm)
        if feed_min <= max(c.slot_radius for c in lay.cells):
            raise ValueError("Feed / inter-stage line is too short for the slot.")
        done.append(f"minimum branch gap {gap:.3f} mm")

        # 4. Signal outline: spacing and self-intersection.
        self._outline_check(lay.dense, rule, "Signal copper")
        done.append(f"signal outline spacing >= {rule:.2f} mm, no self-intersection")

        # 5. Output ports: required Y values on one common X.
        target = sorted(cfg.output_y_mm)
        xs = [p[0] for p in lay.output_ports]
        ys = [p[1] for p in lay.output_ports]
        if max(xs) - min(xs) > 1e-9:
            raise ValueError("Output ports do not share the same X coordinate.")
        if any(abs(a - b) > 1e-9 for a, b in zip(ys, target)):
            raise ValueError("Output ports miss the required Y coordinates.")
        if min(b - a for a, b in zip(target, target[1:])) - w50 < rule:
            raise ValueError("Output lines are too close together.")
        done.append(f"{len(ys)} output ports on target at x = {xs[0]:.3f} mm")

        # 6. Ground pour: width / self-intersection, and clearance to signal.
        copper = PointGrid(1.0)
        copper.extend(lay.dense)
        g = self.pour.clearance
        worst = math.inf
        for poly in self.pour.half_polygons:
            dense = densify(poly, cfg.curve_step_mm)
            self._outline_check(dense, rule, "Ground pour")
            worst = min(worst, min(copper.nearest(p, g + 0.5) for p in dense))
        if worst < g - 0.02:
            raise ValueError(f"Ground clearance {worst:.3f} mm is below {g:.3f} mm.")
        done.append(f"{len(self.pour.polygons)} ground polygons, clearance to "
                    f"signal >= {min(worst, g):.2f} mm")

        # 7. Vias: annular ring, mutual spacing, distance to signal, board.
        ring = 0.5 * (cfg.via_pad_mm - cfg.via_drill_mm)
        if ring < cfg.min_annular_ring_mm:
            raise ValueError(f"Annular ring {ring:.3f} mm is below the rule.")
        grid = PointGrid(1.0)
        limit = g + 0.5 * cfg.via_pad_mm
        b = self.board
        for p in self.vias.vias:
            if grid.any_within(p, cfg.via_min_spacing_mm - 1e-6):
                raise ValueError(f"Vias too close near ({p[0]:.2f}, {p[1]:.2f}).")
            grid.add(p)
            if copper.any_within(p, limit - 0.02):
                raise ValueError(f"Via too close to signal copper at "
                                 f"({p[0]:.2f}, {p[1]:.2f}).")
            if not (b.copper_x0 < p[0] < b.copper_x1 and abs(p[1]) < b.copper_y):
                raise ValueError("Via outside the pour area.")
        done.append(f"{len(self.vias.vias)} vias, annular ring {ring:.3f} mm, "
                    f"spacing >= {cfg.via_min_spacing_mm:.2f} mm")
        return done

    @staticmethod
    def _outline_check(dense: list[Point], rule: float, name: str) -> None:
        hit = find_spacing_violation(dense, rule)
        if hit:
            (xa, ya), (xb, yb), d = hit
            raise ValueError(f"{name}: {d:.3f} mm width/spacing below the rule "
                             f"between ({xa:.3f}, {ya:.3f}) and ({xb:.3f}, {yb:.3f}).")


# =============================================================================
# 13. REPORT AND DXF EXPORT
# =============================================================================
def design_report(cfg: DesignConfig, design: WilkinsonDesign,
                  layout: WilkinsonTreeLayout, board: BoardOutline,
                  pour: GroundPour, vias: ViaGenerator) -> str:
    n_out = len(cfg.output_y_mm)
    rows = [
        f"{n_out}-way Wilkinson divider: design summary",
        f"  Substrate : er = {cfg.eps_r}, tan d = {cfg.loss_tangent}, "
        f"h = {cfg.substrate_h_mm} mm, t = {cfg.copper_t_mm * 1e3:.0f} um",
        f"  Band      : {cfg.f_low_hz / 1e9:g}-{cfg.f_high_hz / 1e9:g} GHz, "
        f"f0 = {cfg.f_center_hz / 1e9:g} GHz, "
        f"Chebyshev FBW = {cfg.fractional_bandwidth * 100:g} %",
        "",
        "  Line        Z0 [ohm]   w [mm]   eps_eff   lambda_g [mm]   lg/4 [mm]",
    ]
    named = [("Port", design.port)] + [
        (f"Section {i}", s) for i, s in enumerate(design.sections, 1)]
    for name, s in named:
        rows.append(f"  {name:<10}  {s.z0:8.2f}   {s.width:6.3f}   "
                    f"{s.eps_eff:7.3f}   {s.lambda_g:13.3f}   {s.length:9.3f}")
    rows.append("")
    rows.append("  Isolation resistors per divider, junction side first [ohm]: "
                + ", ".join(f"{r:.1f}" for r in design.resistors))
    rows.append("  Ideal 2-way divider, worst in-band: "
                + ", ".join(f"{k} = {v:.1f} dB"
                            for k, v in design.worst_case_db().items()))
    rows.append("  Stage output pitches [mm]: "
                + ", ".join(f"{p:.2f}" for p in layout.pitches))
    loss = layout.path_length * design.line.dielectric_loss_db_per_mm(
        design.port.width, cfg.f_center_hz, cfg.loss_tangent)
    rows.append(f"  Path length input -> any output: {layout.path_length:.3f} mm "
                f"(dielectric loss about {loss:.2f} dB at f0, conductor loss "
                f"not included)")
    rows.append(f"  Ideal split: {10.0 * math.log10(n_out):.2f} dB per output")
    rows.append(f"  Ground clearance: {pour.clearance:.3f} mm, "
                f"corner radius {pour.radius:.2f} mm")
    rows.append(f"  Via fence: pitch <= {vias.pitch:.3f} mm, "
                f"{vias.trace_distance:.3f} mm from the trace edge "
                f"(requested {cfg.via_to_trace_edge_mm:.2f} mm)")
    rows.append("  Vias per half board: "
                + ", ".join(f"{k} {v}" for k, v in vias.counts.items())
                + f"; total {len(vias.vias)}")
    rows.append(f"  Board: {board.size[0]:.2f} x {board.size[1]:.2f} mm")
    return "\n".join(rows)


class DxfExporter:
    """Writes all layers to one DXF file (units mm)."""

    def __init__(self, cfg: DesignConfig) -> None:
        self.cfg = cfg

    def save(self, layout: WilkinsonTreeLayout, pour: GroundPour,
             vias: ViaGenerator, board: BoardOutline) -> str:
        cfg = self.cfg
        doc = ezdxf.new(cfg.dxf_version)
        doc.units = units.MM
        msp = doc.modelspace()
        for name, color in ((cfg.layer_copper, 1), (cfg.layer_ground, 3),
                            (cfg.layer_via_pads, 2), (cfg.layer_via_holes, 7),
                            (cfg.layer_outline, 5)):
            doc.layers.add(name, color=color)

        def polygons(layer: str, items: list[list[Point]]) -> None:
            for polygon in items:
                msp.add_lwpolyline(polygon, close=True, dxfattribs={"layer": layer})

        polygons(cfg.layer_copper, [layout.outline])
        polygons(cfg.layer_ground, pour.polygons)
        polygons(cfg.layer_outline, [board.polygon()])
        if cfg.export_pad_reference:
            doc.layers.add(cfg.layer_res_pads, color=6)
            polygons(cfg.layer_res_pads, layout.pads)
        for center in vias.vias:
            msp.add_circle(center, 0.5 * cfg.via_pad_mm,
                           dxfattribs={"layer": cfg.layer_via_pads})
            msp.add_circle(center, 0.5 * cfg.via_drill_mm,
                           dxfattribs={"layer": cfg.layer_via_holes})
        doc.saveas(cfg.output_file)
        return cfg.output_file


# =============================================================================
# 14. MAIN
# =============================================================================
def main() -> None:
    cfg = DesignConfig()
    design = WilkinsonDesign(cfg)
    layout = WilkinsonTreeLayout(cfg, design)
    clearance = ground_clearance(cfg, design)
    board = BoardOutline(cfg, layout, clearance)
    connectors = ConnectorPlanner(cfg, layout)
    pour = GroundPour(cfg, layout, board, clearance)
    vias = ViaGenerator(cfg, design, layout, board, pour, connectors)

    print(design_report(cfg, design, layout, board, pour, vias))
    print("\nDesign-rule checks passed:")
    for line in DesignRuleCheck(cfg, design, layout, board, pour, vias).run():
        print(f"  - {line}")
    print("\nOutput ports (x, y) [mm]:")
    for x, y in layout.output_ports:
        print(f"  ({x:.3f}, {y:+.2f})")
    print(f"\nSaved: {DxfExporter(cfg).save(layout, pour, vias, board)}")


if __name__ == "__main__":
    main()
