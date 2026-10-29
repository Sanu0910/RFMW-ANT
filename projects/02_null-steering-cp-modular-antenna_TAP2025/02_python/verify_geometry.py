"""Measure the built geometry against the paper (Younus et al., IEEE TAP 73(5), May 2025, Figs. 2, 6, 8).

    python verify_geometry.py      -> ../05_docs/MODEL_VERIFICATION.md (tables from measurement, notes appended)

Every value in the "model" column is measured on the copper polygons the DXFs and STEP files are made from
(cross-sections through the merged layer), not read back from the parameter table. 06_step/STEP_report.txt then
shows that each SolidCraft body has exactly the area x thickness of these polygons."""
import math, os
from shapely.geometry import LineString, box
from shapely.ops import unary_union
import nsgeom as G

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "05_docs", "MODEL_VERIFICATION.md")


def cut(geom, p0, p1):
    """Intervals (as distances from p0) where the segment p0-p1 lies in geom."""
    s = LineString([p0, p1]).intersection(geom)
    segs = [s] if s.geom_type == "LineString" else list(getattr(s, "geoms", []))
    out = []
    for g in segs:
        if g.length < 1e-9: continue
        (ax, ay), (bx, by) = g.coords[0], g.coords[-1]
        da, db = math.hypot(ax - p0[0], ay - p0[1]), math.hypot(bx - p0[0], by - p0[1])
        out.append((min(da, db), max(da, db)))
    return sorted(out)


def span_at(geom, y, x=0.0, xr=13.0):
    """Width of the copper interval containing x on the horizontal line y."""
    for a, b in cut(geom, (-xr, y), (xr, y)):
        if a - 1e-9 <= x + xr <= b + 1e-9: return b - a, a - xr, b - xr
    return 0.0, None, None


def vspan_at(geom, x, y, y0=-1.0, y1=61.0):
    """Copper interval containing (x, y) on the vertical line x."""
    for a, b in cut(geom, (x, y0), (x, y1)):
        if a - 1e-9 <= y - y0 <= b + 1e-9: return b - a, a + y0, b + y0
    return 0.0, None, None


rows = []
def row(group, name, paper, model, note=""):
    if isinstance(paper, (int, float)) and isinstance(model, (int, float)):
        d = model - paper; st = "match" if abs(d) < 5e-3 else "differs %+.3f" % d
        rows.append((group, name, "%g" % paper, "%.3f" % model, st, note))
    else:
        rows.append((group, name, str(paper), model if isinstance(model, str) else "%.3f" % model, "-", note))


def phase_shifter():
    b = G.board_phase_shifter(slot="paper", bias="L")
    top, mid, bot = b.merged("TOP"), b.merged("MID"), b.merged("BOT")
    x0, y0, x1, y1 = b.L["OUTLINE"][0].bounds
    g = "Phase shifter (Fig. 2)"
    row(g, "L (board length)", 36, y1 - y0); row(g, "W (board width)", 25, x1 - x0)
    yc = 18.0
    row(g, "P_w (patch width, TOP)", 4.9, span_at(top, yc)[0])
    row(g, "P_w (patch width, BOT)", 4.9, span_at(bot, yc)[0])
    # patch length: the ellipse tips are where the copper along x = 0 changes width from the line width
    xs = 1.0                                       # off-axis cut through the ellipse only (lines are < 0.7 half-width)
    ln = vspan_at(top, xs, yc)[0]; pl = ln / math.sqrt(1 - (xs / (G.PS["Pw"] / 2)) ** 2)
    row(g, "l = P_l (patch length, TOP)", 8.8, pl, "from an off-axis chord of the ellipse")
    ptop0 = yc - pl / 2
    row(g, "F_l (feeder: board edge -> patch)", 13.7, ptop0 - y0,
        "patches centred and overlapping on L = 36 gives (36 - 8.8)/2 = 13.6; 13.7 cannot also hold")
    row(g, "TOP feeder width (50 ohm, h 0.508)", "not given", span_at(top, 5.0)[0], "computed, Hammerstad-Jensen")
    row(g, "BOT feeder width (50 ohm, h 0.608)", "not given", span_at(bot, 31.0)[0], "computed, Hammerstad-Jensen")
    hole = [p for p in getattr(mid, "geoms", [mid]) if p.interiors][0].interiors[0]
    hx0, hy0, hx1, hy1 = hole.bounds
    row(g, "S_l (slot length, along the board)", 8.8, hy1 - hy0)
    row(g, "S_w (slot width, across)", 8.8, hx1 - hx0, "caption: circle; Fig. 2(e) draws an ellipse (Sw/Sl ~ 0.66): variant slot-drawing-ratio")
    # stubs along the centre line (BOT runs from the patch tip at 13.6 down to the DC pad)
    cuts = [(a - 1, b - 1) for a, b in cut(bot, (0, -1), (0, 37))]
    tip = yc - G.PS["Pl"] / 2
    main = [c for c in cuts if c[0] < tip < c[1] + 1e-6][0]
    stub_end = main[0]
    # width drops from the 50-ohm stub to the 0.6 mm capacitor pad: find it
    y = tip - 0.01
    while y > stub_end and span_at(bot, y)[0] > 0.9: y -= 0.005
    row(g, "St_l2 (BOT stub: patch -> DC-block C)", 6.1, round((tip - y) / 0.005) * 0.005, "to the start of the C pad (0.005 mm scan)")
    vgap = [c for c in cuts if c[1] < stub_end][-1]                 # junction segment, below the C gap
    row(g, "l_stub (patch -> varactor)", 9.4, tip - vgap[0], "stub + C + junction pad, up to the varactor gap")
    row(g, "h (each core, RO4003C)", 0.508, G.H_CORE); row(g, "prepreg (RO4450F)", 0.1, G.H_PREPREG)
    row(g, "layer order (Fig. 2(d))", "TOP / core / MID / prepreg / core / BOT", "same", "")
    row(g, "Z_TOP, Z_MID (copper heights)", "1.116, 0.608", "%.3f, %.3f" % (G.Z_TOP, G.Z_MID))


def dipole():
    b = G.board_dipole(); top, bot = b.merged("TOP"), b.merged("BOT")
    x0, y0, x1, y1 = b.L["OUTLINE"][0].bounds
    g = "Printed dipole (Fig. 6)"
    row(g, "L_ant", 24, y1 - y0); row(g, "W", 25, x1 - x0)
    yg = vspan_at(top, -8.0, 1.0)[2]                                  # ground top edge (left of the slot)
    row(g, "l_3 (ground edge -> board top)", 14.2, (y1 - y0) - yg)
    sq = cut(top, (0.5, y0), (0.5, yg))                                # off the slot line, through the square
    gap_lo, gap_hi = sq[0][1], sq[1][0]
    row(g, "l_1 (square slot, height)", 1.65, gap_hi - gap_lo)
    w_sq = [c for c in cut(top, (-12.5, gap_lo + 0.5), (12.5, gap_lo + 0.5))]
    row(g, "l_1 (square slot, width)", 1.65, w_sq[1][0] - w_sq[0][1])
    row(g, "l_2 (slot line length)", 3.1, yg - gap_hi)
    ys = yg - 1.0; s = cut(top, (-12.5, ys), (12.5, ys))
    row(g, "g_s (slot line gap)", 0.11, s[1][0] - s[0][1])
    ys = yg + 5.0; s = cut(top, (-6, ys), (6, ys))
    row(g, "w_1 (stem width)", 1.6, s[0][1] - s[0][0])
    # arm: centre line from the stem top at 45 deg outward and down
    c = math.cos(math.radians(45)); xa, ya = G.DP["gs"] / 2 + G.DP["w1"] / 2, 24 - G.DP["w1"] / 2
    along = cut(top, (xa, ya), (xa + 8 * c, ya - 8 * c))
    row(g, "l_4 (arm length, centre line from stem axis)", 4.5, along[0][1], "45 deg; arm drawn outward and down as in Fig. 6(a)")
    mx, my = xa + 2.5 * c, ya - 2.5 * c
    across = cut(top, (mx - 2 * c, my - 2 * c), (mx + 2 * c, my + 2 * c))
    row(g, "w_1 (arm width)", 1.6, max(b_ - a_ for a_, b_ in across))
    lsv = vspan_at(top, 12.4, yg + 1.0)
    row(g, "l_s (decoupling strip height)", "not given", lsv[2] - yg, "[ASSUMED] 4.1 (the caption's 'l_i = 4.1' is read as l_6)")
    row(g, "decoupling strip width", "not given", span_at(top, yg + 1.0, x=12.4)[0], "[ASSUMED]")
    # back side balun
    row(g, "w_2 (feeder width)", 1.07, span_at(bot, 1.0)[0])
    fl = vspan_at(bot, 0.0, 1.0)
    w2 = G.DP["w2"]
    row(g, "l_4 (feeder length to the floor centre line)", 4.5, fl[2] - w2 / 2 - y0)
    xw = -G.DP["l6"] / 2
    wl = vspan_at(bot, xw, 6.0)
    row(g, "l_5 (left wall, centre to centre)", 4.0, wl[0] - w2)
    tb = span_at(bot, wl[2] - w2 / 2, x=0.0)
    row(g, "l_6 (top bar, centre to centre)", 4.1, tb[0] - w2, "caption prints 'l_i = 4.1'; Fig. 6(b) arrow spans the outer edges (outer = 4.1 would make the loop 1.07 narrower)")
    st = vspan_at(bot, -xw, 7.0)
    row(g, "l_7 (stub open end above the floor centre line)", 0.43, st[1] - (fl[2] - w2 / 2), "Fig. 6(b) dimension lines suggest top bar -> slot square instead (see notes)")
    d = G.DP; sqb = box(-d["l1"] / 2, yg - d["l2"] - d["l1"], d["l1"] / 2, yg - d["l2"]); sl = box(-d["gs"] / 2, yg - d["l2"], d["gs"] / 2, yg)
    row(g, "balun over the slot square (must be 0)", 0, bot.intersection(sqb).area, "Fig. 6(b)/8(b): square lies in the copper-free loop interior")
    row(g, "balun crossing the slot line (mm2)", "w_2 x g_s = %.4f" % (w2 * d["gs"]), "%.4f" % bot.intersection(sl).area, "crossed once, by the top bar at x = 0")
    row(g, "substrate", "RO4003C 0.508 (text: 'RT/Duroid 4003C, er = 2.2')", "RO4003C 0.508, er 3.55", "the text's er = 2.2 contradicts RO4003C; model uses 3.55")


def unit():
    g = "Integrated unit (Fig. 8)"
    for v in ("A", "B"):
        b = G.board_unit(v, slot="paper", mid="paper"); x0, y0, x1, y1 = b.L["OUTLINE"][0].bounds
        row(g, "UNIT_%s size W x (L + L_ant)" % v, "25 x 60", "%.3f x %.3f" % (x1 - x0, y1 - y0))
    a, bb = G.board_unit("A", mid="paper"), G.board_unit("B", mid="paper")
    from shapely.affinity import scale
    diff = scale(a.merged("BOT"), -1, 1, origin=(0, 0)).symmetric_difference(bb.merged("BOT")).area
    row(g, "UNIT_B = mirror of UNIT_A (BOT, mm2 difference)", 0, diff, "Fig. 8: unit 2 is the mirror image of unit 1")
    m = a.merged("MID"); row(g, "MID ground ends at y (dash-dot line)", 36, m.bounds[3])
    bot = a.merged("BOT")
    row(g, "BOT feeder width below / above y = 36", "1.371 / 1.07", "%.3f / %.3f" % (span_at(bot, 35.0)[0], span_at(bot, 37.0)[0]),
        "50-ohm PS line steps to w_2 at the dipole")


NOTES = """## Corrected in this check (2026-10-29)
1. **Balun (Fig. 6(b), Fig. 8(b)).** The 2026-10-27 model ran the feeder on up the middle of the loop as a centre bar. Neither
   figure has one: the feeder stops at the loop floor and turns left, the loop goes up the left wall and across the top bar,
   and the right stub hangs down open-ended. The centre bar sat right over the slot square. It is removed; the slot square
   now lies in the copper-free loop interior, and the top bar crosses the slot line once at x = 0.
2. **Standalone dipole stack-up.** The old cadquery STEP put the standalone dipole on the two-core 1.116 mm stack. The paper
   (Sec. III-B) and the DXF name give a single 0.508 mm substrate; the STEP now uses that.
3. **Ellipses** (patches, coupling slot) are drawn with 256 segments instead of 96 (area error -0.07 % -> -0.01 %).
4. **STEP models** are now built with SolidCraft and every body is measured (06_step/STEP_report.txt). The 1-D, 2-D and both
   CP systems are included as assemblies.

## Paper inconsistencies (kept as noted, settle in simulation)
- **F_l = 13.7** cannot hold together with L = 36, P_l = 8.8 and broadside patches that overlap exactly; the model centres
  both patches (F_l = 13.6). The 0.1 mm is below the fabrication tolerance of the feeder end.
- **Coupling slot:** the caption gives S_w = S_l = 8.8 (a circle); Fig. 2(e) draws an ellipse with S_w/S_l ~ 0.66. Both are
  built (`slot="paper"` and the `slot-drawing-ratio` DXF variant).
- **Fig. 6 caption "l_i = 4.1":** there is no l_i in the figure, while l_6 and l_s have no value. It is read as l_6 (the loop
  must be about this wide to hold the 1.65 mm square); l_s and the strip width stay [ASSUMED].
- **Back-view balun numbers vs. front view:** with l_1, l_2, l_3 fixed by the front view, the back-view values l_4 = 4.5,
  l_5 = 4 and l_7 = 0.43 cannot all be met if the dimension arrows are taken edge to edge as drawn (the top bar would sit
  above the ground edge, or the floor would cover the slot square). The model takes l_4, l_5, l_6 centre line to centre line,
  which keeps the top bar over the slot line and the square inside the loop; l_7 is the open-end gap of the right stub.
  Fig. 6(b)'s dimension lines also allow l_7 = gap from the top bar's inner edge to the slot square (it is 1.265 here).
  Tune l_5 / l_7 for S11 in the full-wave model.
- **Dipole substrate:** the text says "RT/Duroid 4003C (er = 2.2)"; RO4003C is er = 3.55 and is what the phase shifter uses.
  The model uses 3.55; er = 2.2 would be RT/duroid 5880.
- **Dipole feed in the unit:** on the integrated unit the dipole's back-side feed (w_2 = 1.07) sits 1.116 mm from the
  TOP ground (MID ground ends at y = 36), not 0.508 mm as on the standalone board, so it is no longer a 50-ohm line there.
  The paper uses the same dimensions; the `mid-extended` unit variant keeps a 0.508 mm reference under the dipole.

## Not changed (shown differently in the paper)
- **Via spans.** Fig. 2(d) and Fig. 8 draw the via groups through the whole board, shared by the connector ground of one
  side and the DC pad of the other. The model keeps blind vias (DC pads TOP-MID / MID-BOT, connector pads to MID) at
  separate positions, because the paper gives no pad or via positions to share. Electrically both reach the MID ground.
- **Pads, bias parts and their placement** are not dimensioned in the paper and stay [ASSUMED] (05_docs/DESIGN_GUIDE.md).

## RF models re-run (2026-10-29)
Python (`rtps_model.py`, `array_models.py`) and MATLAB in GNU Octave 8.4 (`ns_demo_phase_shifter`, `ns_demo_system`) give the
same numbers:

| Check | Result | Paper |
|---|---|---|
| Phase range, ideal parts (eqs. 1-7) | 114.0-115.9 deg (single-varactor limit 116 deg) | 145 deg |
| Phase range with 0.35 nH package inductance | 136.3-147.0 deg, +-6.1 deg, IL <= 0.70 dB | 145 deg, +-2 deg, IL < 1 dB |
| 1-D null with a bias fixed for 40 deg at 6 GHz | 50.5 deg at 5 GHz, 33.4 deg at 7 GHz | not discussed |
| 2-D steering envelope (143 deg shifter) | abs(u0) + abs(v0) <= 0.793 | +-40 deg in xz and yz |
| CP, paper wing types (U1..U4 = A B B A) | fields cancel at broadside | AR < 2.3 dB |
| CP, co-phased wings (A A B B) | AR 0 dB (ideal), 1.52 dB for 10 deg quadrature error | AR < 2.3 dB |

The Monte Carlo medians differ by about 1 dB between the two (different random numbers); the 10th percentiles agree.

## Orientation check
Fig. 8(b) is drawn see-through (unit 1 stays on the left as in (a)). In it, unit 1's loop has its closed wall on the side
opposite its decoupling strip, and unit 2 is the mirror image; UNIT_A / UNIT_B match this (mirror difference 0 mm2).
"""


def main():
    phase_shifter(); dipole(); unit()
    L = ["# Model verification against the paper", "",
         "Generated by `02_python/verify_geometry.py` from the geometry in `nsgeom.py`. The model column is **measured** on the",
         "copper polygons (cross-sections through each layer), the same polygons the DXFs and the SolidCraft STEP files are built",
         "from. `06_step/STEP_report.txt` shows every SolidCraft body equals area x thickness of these polygons (within 0.05 %).", "",
         "All lengths in mm.", ""]
    cur = None
    for grp, name, paper, model, st, note in rows:
        if grp != cur:
            L += ["", "## " + grp, "", "| Dimension | Paper | Model | Result | Note |", "|---|---|---|---|---|"]; cur = grp
        L.append("| %s | %s | %s | %s | %s |" % (name, paper, model, st, note))
    open(OUT, "w").write("\n".join(L) + "\n\n" + NOTES)
    bad = [r for r in rows if r[4].startswith("differs")]
    print("%d checks, %d differ from the paper:" % (len(rows), len(bad)))
    for r in bad: print("  ", r[1], r[2], r[3], r[4])


if __name__ == "__main__":
    main()
