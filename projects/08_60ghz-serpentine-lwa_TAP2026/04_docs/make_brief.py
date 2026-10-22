#!/usr/bin/env python3
"""Build LWA_60GHz_Brief.pdf: the paper explained from basics to advanced, plus the replica in this repository.

Needs the figures from ../02_python/lwa_design.py, concept_figs.py, ../01_cad/render_cad.py and (optional)
../03_sim/results/slot_summary.csv.
"""
import csv
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(HERE, "img")
RES = os.path.join(ROOT, "02_python", "results")
SIM = os.path.join(ROOT, "03_sim", "results", "slot_summary.csv")
OUT = os.path.join(HERE, "LWA_60GHz_Brief.pdf")

FONT, BOLD = "Helvetica", "Helvetica-Bold"
for name, f in (("DV", "DejaVuSans.ttf"), ("DVB", "DejaVuSans-Bold.ttf")):
    p = "/usr/share/fonts/truetype/dejavu/" + f
    if os.path.exists(p):
        pdfmetrics.registerFont(TTFont(name, p))
if "DVB" in pdfmetrics.getRegisteredFontNames():
    FONT, BOLD = "DV", "DVB"
    pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

NAVY = colors.HexColor("#1F3A5F")
TEAL = colors.HexColor("#2A9D8F")
ORANGE = colors.HexColor("#E76F51")
GREY = colors.HexColor("#5C6670")
LIGHT = colors.HexColor("#EEF3F8")
W = A4[0] - 36 * mm - 12

H1 = ParagraphStyle("H1", fontName=BOLD, fontSize=17, leading=21, textColor=NAVY, spaceAfter=4)
H2 = ParagraphStyle("H2", fontName=BOLD, fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=7, spaceAfter=3)
BODY = ParagraphStyle("B", fontName=FONT, fontSize=9.3, leading=13, spaceAfter=4)
LEAD = ParagraphStyle("L", parent=BODY, fontSize=10, leading=14, textColor=GREY)
SMALL = ParagraphStyle("S", fontName=FONT, fontSize=8, leading=10.3)
CELLH = ParagraphStyle("CH", fontName=BOLD, fontSize=8.2, leading=10.4, textColor=colors.white)
CAP = ParagraphStyle("C", parent=SMALL, alignment=TA_CENTER, textColor=GREY, spaceBefore=2, spaceAfter=4)
EQ = ParagraphStyle("E", parent=BODY, fontName=FONT, alignment=TA_CENTER, fontSize=9.6, textColor=NAVY,
                    spaceBefore=2, spaceAfter=5)
LEVEL = {"basic": colors.HexColor("#2E9E6B"), "intermediate": colors.HexColor("#E9A23B"),
         "advanced": colors.HexColor("#C0392B")}


def table(rows, widths, head=NAVY, fs=None):
    st = SMALL if fs is None else ParagraphStyle("t", parent=SMALL, fontSize=fs, leading=fs * 1.28)
    data = [[Paragraph(str(c), CELLH) for c in rows[0]]] + [[Paragraph(str(c), st) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    sty = [("BACKGROUND", (0, 0), (-1, 0), head), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#C8D2DC")),
           ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    sty += [("BACKGROUND", (0, i), (-1, i), LIGHT) for i in range(2, len(data), 2)]
    t.setStyle(TableStyle(sty))
    return t


def callout(html, edge=TEAL, bg=LIGHT):
    t = Table([[Paragraph(html, BODY)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def img(path, width):
    if not os.path.exists(path):
        return Paragraph(f"[missing figure {os.path.basename(path)}]", SMALL)
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(path, width=width, height=width * h / w)


def level_tag(level):
    c = LEVEL[level]
    t = Table([[Paragraph(f"<font color='white'><b>{level.upper()}</b></font>", SMALL)]], colWidths=[30 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c), ("TOPPADDING", (0, 0), (-1, -1), 1),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    t.hAlign = "LEFT"
    return t


def on_page(c, doc):
    c.saveState()
    if doc.page > 1:
        c.setStrokeColor(TEAL)
        c.setLineWidth(0.8)
        c.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
        c.setFont(FONT, 7.4)
        c.setFillColor(GREY)
        c.drawString(18 * mm, A4[1] - 11 * mm, "60-GHz serpentine leaky-wave antenna: brief and replica")
        c.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "after Gabsteiger et al., IEEE TAP 74(7), 2026")
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"page {doc.page}")
        c.drawString(18 * mm, 10 * mm, "projects/08_60ghz-serpentine-lwa_TAP2026 · github.com/sanu0910/rfmw-ant")
    c.restoreState()


def build():
    s = []
    P = lambda t, st=BODY: s.append(Paragraph(t, st))  # noqa: E731
    E = lambda t: s.append(Paragraph(t, EQ))  # noqa: E731
    summ = json.load(open(os.path.join(RES, "design_summary.json")))
    slots = list(csv.DictReader(open(os.path.join(RES, "slot_table.csv"))))
    geo = json.load(open(os.path.join(ROOT, "01_cad", "geometry.json")))

    # ---------------- cover
    s.append(Spacer(1, 12 * mm))
    P("60-GHz Serpentine Leaky-Wave Antenna", ParagraphStyle("t", parent=H1, fontSize=26, leading=31))
    P("A brief from basics to advanced, and a replica you can print", ParagraphStyle(
        "t2", parent=LEAD, fontSize=13, leading=17))
    s.append(Spacer(1, 4 * mm))
    s.append(img(os.path.join(IMG, "cad_iso.png"), W))
    P("The replica built in this repository from the paper's equations and Table II (STEP / STL).", CAP)
    s.append(Spacer(1, 3 * mm))
    s.append(table([["Paper", "Result"],
                    ["J. Gabsteiger, C. Robisch, A. Koelpin, F. Lurz, \"Advancing 60-GHz SISO Radar: Additively "
                     "Manufactured Leaky Wave Antenna With Enhanced Beam Steering\", IEEE Trans. Antennas Propag., "
                     "vol. 74, no. 7, pp. 6130–6145, July 2026, DOI 10.1109/TAP.2026.3681348 (CC BY 4.0)",
                     "<b>76°</b> beam steering over <b>58–63.5 GHz</b> (5.5 GHz) with two ports · 16 slots · "
                     "<b>13–15 dBi</b> · 3D-printed resin, silver-coated · ≈ 1° angle accuracy in a SISO radar"]],
                   [W * 0.6, W * 0.4]))
    s.append(Spacer(1, 4 * mm))
    P("How to read this: every section is tagged <font color='#2E9E6B'><b>BASIC</b></font>, "
      "<font color='#E9A23B'><b>INTERMEDIATE</b></font> or <font color='#C0392B'><b>ADVANCED</b></font>. "
      "Read only the green parts for the idea, add the orange parts for how it works, and the red parts "
      "to design or build one.", LEAD)
    s.append(PageBreak())

    # ---------------- 1 big idea
    s.append(level_tag("basic"))
    P("1. The big idea in one page", H1)
    P("A radar finds <b>how far</b> a target is easily, but finding <b>in which direction</b> it is usually needs "
      "many receive antennas and channels (MIMO) or a motor that turns the antenna. This paper does it with "
      "<b>one transmit and one receive channel</b>: the antenna itself points its beam in a different direction "
      "for every frequency. When the radar sweeps its frequency (a <i>chirp</i>), the beam sweeps across the "
      "room like a searchlight, and the moment a target answers tells the angle.", LEAD)
    s.append(img(os.path.join(IMG, "concept_lwa.png"), W * 0.9))
    P("Figure 1: a leaky-wave antenna. A wave runs inside a metal tube (waveguide); small slots let a bit of it "
      "leak out. The direction where all leaks add up depends on frequency.", CAP)
    s.append(table([["Everyday picture", "In the antenna"],
                    ["A garden hose with small holes: water leaks out of every hole", "a waveguide with 16 slots: "
                     "microwaves leak out of every slot"],
                    ["Waves from all holes add up in one direction, like a stadium 'wave'", "the main beam, about 8° "
                     "wide"],
                    ["Change the water pressure and the spray angle changes", "change the frequency and the beam "
                     "angle changes (≈ 6° per GHz)"],
                    ["Fold the hose into a zig-zag to make the effect stronger", "the serpentine: a 4.6× longer "
                     "path between slots, so 4× more steering"]], [W / 2, W / 2]))
    s.append(Spacer(1, 3))
    s.append(callout("<b>Why 60 GHz?</b> The 57–64 GHz band is licence-free and has several GHz of bandwidth. "
                     "Ready-made radar chips exist (Infineon BGT60TR13, used here), and the antennas are only a few "
                     "cm long. More bandwidth means both finer range and more beam steering."))
    s.append(PageBreak())

    # ---------------- 2 radar
    s.append(level_tag("basic"))
    P("2. How the radar measures range and angle", H1)
    s.append(img(os.path.join(IMG, "concept_fmcw.png"), W))
    P("Figure 2: left, FMCW range. The echo is a delayed copy of the chirp, and their difference (the beat "
      "frequency) grows with distance. Right, the angle. A target only answers while the beam points at it, i.e. "
      "during a certain part of the chirp.", CAP)
    s.append(level_tag("intermediate"))
    P("The formulas", H2)
    E("ΔR = c / (2B)   (eq. 1)       R = c · f<sub>beat</sub> · t<sub>mod</sub> / (2B)   (eq. 3)")
    P(f"With B = 5.5 GHz, ΔR = {summ['range_res_full_bw_cm']:.1f} cm. But a squinting beam only illuminates a "
      "target for part of the chirp, so only a slice B' of the bandwidth carries that target's range information:")
    E("ΔR = c / (2B') = (c / 2B) · θ<sub>s</sub> / θ<sub>3dB</sub>   (eq. 2)      "
      "ΔR · θ<sub>3dB</sub> = c · θ<sub>s</sub> / (2B)   (eq. 4)")
    P(f"Equation 4 is an <b>uncertainty relation</b>: a narrower beam (better angle) means fewer GHz per target "
      f"(worse range). For our design θ<sub>s</sub> ≈ {summ['scan_per_port_deg']:.0f}° per port and θ<sub>3dB</sub> "
      f"≈ {summ['hpbw_mean_deg']:.1f}°, so each beam position gets B' ≈ {summ['eff_bw_per_beam_MHz']:.0f} MHz, "
      f"and ΔR ≈ {summ['range_res_effective_cm']:.0f} cm. The paper quotes 30 cm for a 500 MHz slice.")
    P("Signal processing", H2)
    P("The received beat signal is cut into overlapping windows (a short-time Fourier transform, STFT). Each window "
      "belongs to a known frequency slice, hence a known beam direction, and its FFT gives the range of the "
      "targets in that direction. This is the same maths as FFT beamforming, only the 'spatial' axis is replaced "
      "by the frequency–angle law of the antenna.")
    s.append(callout("<b>Dual port + switch:</b> feeding the antenna from the other end mirrors the beam about "
                     "broadside. A waveguide switch alternates the two ports, so 5.5 GHz of physical bandwidth "
                     "gives an 11 GHz 'virtual' sweep and 76° of coverage.", edge=ORANGE))
    s.append(PageBreak())

    # ---------------- 3 waveguide & slots
    s.append(level_tag("intermediate"))
    P("3. Waveguides and slots", H1)
    P("A rectangular waveguide is a hollow metal pipe. Above its cutoff frequency it carries the TE10 mode, whose "
      "electric field spans the short side b and varies along the long side a. For 60 GHz the standard size is "
      "<b>WR15: a = 3.76 mm, b = 1.88 mm</b>, cutoff f<sub>c</sub> = c/2a = "
      f"{summ['fc_TE10_GHz']:.1f} GHz. The wave inside travels with phase constant", LEAD)
    E("β = 2π / λ<sub>g</sub> = √( (2πf)²μ<sub>0</sub>ε<sub>0</sub> − (π/a)² )   (eq. 6)")
    P("β is always smaller than the free-space k = 2π/λ<sub>0</sub>, and it grows with frequency faster than "
      "k does. That difference is what makes a leaky-wave antenna steer.")
    P("Why tilted slots in the narrow wall?", H2)
    P("Currents on the narrow wall flow across it, around the guide. A slot cut straight across the narrow wall "
      "runs parallel to those currents and does not interrupt them, so it does not radiate. Tilting it by θ<sub>n</sub> "
      "cuts the currents, and the radiated power grows roughly with sin²θ<sub>n</sub>. The slot is longer than b, so "
      "it wraps around the corners into both broad walls to a depth d<sub>n</sub>; together, tilt and depth set "
      "the slot's <b>conductance</b> g<sub>n</sub>, the fraction of power it takes out. Neighbouring slots are "
      "tilted in opposite directions, which adds 180° of phase between them.")
    P("Standing-wave vs travelling-wave arrays", H2)
    s.append(table([["", "Standing-wave (d = λ<sub>g</sub>/2)", "Travelling-wave (d ≠ λ<sub>g</sub>/2): this paper"],
                    ["phase between slots", "exactly 180° (+180° from the tilt) → in phase",
                     "frequency-dependent"],
                    ["beam", "fixed at broadside, narrow band", "scans with frequency (leaky-wave)"],
                    ["end of guide", "short circuit", "matched / second port"]], [W * 0.22, W * 0.36, W * 0.42]))
    s.append(Spacer(1, 4))
    P("The beam direction (Floquet theory)", H2)
    P("A periodic array radiates where the phases of all elements line up (eq. 7), k d cos φ − β d = 2π m. "
      "Solving for the angle gives eq. 8. Only the m = −1 space harmonic radiates (eq. 9), and the alternating "
      "slot tilt doubles the period to 2d:")
    E("φ = arccos( β/k − λ / (2d) )   (eq. 10)")
    P(f"Straight slotted guide with d = 2.38 mm: {summ['straight_theta_58_deg']:.1f}° at 58 GHz and "
      f"{summ['straight_theta_63p5_deg']:.1f}° at 63.5 GHz, <b>only "
      f"{summ['straight_theta_58_deg'] - summ['straight_theta_63p5_deg']:.1f}° of steering</b>. Not enough for a "
      "radar that needs at least 40°.")
    s.append(PageBreak())

    # ---------------- 4 serpentine
    s.append(level_tag("intermediate"))
    P("4. The serpentine trick", H1)
    s.append(img(os.path.join(IMG, "concept_serpentine.png"), W))
    P("Figure 3: the slots stay 2.38 mm apart, but the wave detours through a U-bend between them.", CAP)
    P("If the wave travels a path <b>l</b> between slots that are <b>d</b> apart, the phase between slots is βl "
      "(not βd). A small change of β with frequency then turns into a large change of phase, so the beam moves "
      "much further:", LEAD)
    E("θ<sub>0</sub> = arccos( (β l − 2π(m + ½)) / (k d) )   (eq. 11)")
    P("Design steps from the paper, reproduced exactly by <font face='Courier'>02_python/lwa_design.py</font>:")
    s.append(table([["Step", "Rule", "Paper", "This replica"],
                    ["slot spacing d", "d &lt; λ<sub>0</sub>/2 at 63.5 GHz (no grating lobe); d = b + 0.5 mm",
                     "2.38 mm (limit 2.36)", f"{summ['d_mm']:.2f} mm (limit {summ['grating_limit_mm']:.2f})"],
                    ["path length l", "θ<sub>0</sub>(58 GHz) = 86°, m = 1", "10.9 mm",
                     f"{summ['l_mm_exact']:.3f} mm"],
                    ["beam at 58 GHz", "eq. 11", "86°", f"{summ['theta_58_deg']:.2f}°"],
                    ["beam at 63.5 GHz", "eq. 11", "53.8°", f"{summ['theta_63p5_deg']:.2f}°"],
                    ["scan per port", "", "32.2° (sim.), 34° (meas.)", f"{summ['scan_per_port_deg']:.1f}°"],
                    ["with port 2", "mirror about 90°", "76° total", f"{summ['total_coverage_deg']:.0f}° between "
                     "beam peaks (+ beamwidth ≈ 76°)"]], [W * 0.17, W * 0.39, W * 0.2, W * 0.24], fs=7.8))
    s.append(Spacer(1, 4))
    s.append(img(os.path.join(RES, "fig_beam_angle_dispersion.png"), W))
    P("Figure 4: beam angle and effective dispersion, computed with this repository's design script.", CAP)
    s.append(PageBreak())

    # ---------------- 5 slots design
    s.append(level_tag("advanced"))
    P("5. Designing the 16 slots", H1)
    P("Each slot takes a share of the power that is still travelling in the guide. To get low sidelobes, the "
      "radiated amplitudes follow a <b>Dolph–Chebyshev</b> taper (N = 16, 20 dB sidelobes). For a given sidelobe "
      "level it gives the narrowest possible main beam:", LEAD)
    E("(AF)<sub>2M</sub> = Σ a<sub>n</sub> cos[(2n − 1) ψ/2],  ψ = k d cos φ − β l   (eq. 15)       "
      "g<sub>n</sub> = a<sub>n</sub>² / Σ a<sub>i</sub>²   (eq. 16)")
    P("The paper turns each g<sub>n</sub> into a tilt and a depth with polynomial fits of CST unit-cell runs "
      "(eq. 17, 18; the logarithm is the natural log, checked against Table I). The first model radiated too "
      "little (S21 ≈ −3 dB), so all tilts were scaled by 1.5, depths recomputed with eq. 20, and the slot widened "
      "from 0.261 mm (eq. 19, w = a/(16·0.9)) to 0.34 mm for printing. That gave S21 ≈ −6.5 dB and "
      "S11 &lt; −15 dB.")
    rows = [["n", "a<sub>n</sub> ours / paper", "g<sub>n</sub> ours / paper", "tilt ours / paper (°)",
             "tilt<sub>adj</sub> paper (°)", "depth<sub>adj</sub> paper (mm)"]]
    for r in slots[:8]:
        rows.append([r["slot"], f"{r['a_n']} / {r['a_n_paper']}", f"{r['g_n']} / {r['g_n_paper']}",
                     f"{float(r['tilt_deg']):.2f} / {r['tilt_deg_paper']}", r["tilt_adj_deg_paper"],
                     r["depth_adj_mm_paper"]])
    s.append(table(rows, [W * 0.06, W * 0.2, W * 0.2, W * 0.2, W * 0.16, W * 0.18], fs=7.8))
    P("Slots 9–16 mirror slots 8–1. The tilt formula eq. 17 is reproduced to within 0.15°. The printed depth fit "
      "(eq. 18) is rounded in the paper and gives depths up to 0.09 mm off, so the CAD uses the paper's own "
      "Table II values.", CAP)
    s.append(img(os.path.join(RES, "fig_slot_params.png"), W))
    P("Figure 5: taper and slot geometry along the antenna.", CAP)
    s.append(PageBreak())

    # ---------------- 6 patterns
    s.append(level_tag("advanced"))
    P("6. Radiation patterns, beam map and the open stopband", H1)
    s.append(img(os.path.join(RES, "fig_patterns.png"), W))
    P("Figure 6: array factor of the 16 tapered slots for both ports (compare with paper Fig. 9). The real "
      "antenna adds the slot element pattern and the gain dip near broadside.", CAP)
    s.append(Table([[img(os.path.join(RES, "fig_freq_angle.png"), W * 0.48),
                     Paragraph("<b>Frequency–angle map</b> (paper Figs. 12/26): each port covers one side of "
                               "broadside, almost linearly, at about 5.8° per GHz in this model (7°/GHz measured). "
                               "The bars show the half-power beamwidth.<br/><br/>"
                               "<b>Open stopband (OSB).</b> Near broadside (β<sub>eff</sub> → 0, around 57.5–59 GHz) "
                               "the forward and backward space harmonics couple, all reflections add in phase, and "
                               "S11 rises to ≈ −2 dB while the gain dips. It is usually removed by breaking the "
                               "symmetry of the unit cell. The paper tried this (Fig. 10/11) but kept the "
                               "symmetric design because both ports must behave the same; the horn receiver "
                               "partly hides the dip.<br/><br/>"
                               "<b>Polarisation:</b> 12.5 dBi co-pol and 2.5 dBi cross-pol, so XPD ≈ 10 dB "
                               "(eq. 21), which is enough for radar.", BODY)]],
                   colWidths=[W * 0.5, W * 0.5], style=[("VALIGN", (0, 0), (-1, -1), "TOP")]))
    s.append(PageBreak())

    # ---------------- 7 manufacturing
    s.append(level_tag("advanced"))
    P("7. How it is made: SLA printing and silver plating", H1)
    s.append(table([["Step", "Paper's process", "Why it matters"],
                    ["Printer", "Formlabs Form 3+, clear resin, 25 µm layers",
                     "smooth walls; a 0.34 mm slot needs fine resolution"],
                    ["Orientation", "tilted 5–12° to the build plate (Fig. 17)",
                     "flat causes suction-cup peeling and micro-cracks; steep (> 20°) causes staircase edges"],
                    ["Cleaning", "Form Wash, then isopropanol + compressed air through the guide",
                     "resin stays trapped in the narrow slots and bends"],
                    ["Cure", "UV in Form Cure", "dimensional stability"],
                    ["Activation", "SnCl<sub>2</sub> + HCl + water dip",
                     "creates seeds so silver can grow on plastic"],
                    ["Silvering (Tollens')", "1.5 g AgNO<sub>3</sub> in 75 mL water, 0.3 g NaOH, NH<sub>4</sub>OH "
                     "until clear, then 1.5 g dextrose in 30 mL water; 1–5 min, 3 cycles",
                     "a conformal metal layer with no electrical contact needed (fume hood, PPE)"],
                    ["Pump-assisted", "reagent circulated through the guide by a peristaltic pump",
                     "removes deposits in the bends that shortened the path l"],
                    ["Result", "Ag 14–22 µm thick; the skin depth at 60 GHz is ≈ 0.25 µm",
                     "more than 50 skin depths, so the loss is not limited by plating thickness"],
                    ["Shrink fix", "printed opening was 3.38 × 1.72 mm: widen by 100 µm, lengthen each half loop "
                     "by 200 µm", "the beam angle depends on l and a, so 0.2 mm errors shift it by degrees"]],
                   [W * 0.15, W * 0.45, W * 0.4], fs=7.7))
    s.append(Spacer(1, 4))
    s.append(callout("<b>Sensitivity in numbers:</b> the first prototype, without the pump, steered only 47° and was "
                     "shifted by about 16°. The corrected, pump-plated one reached 76° and matched the simulation "
                     "within 1–2° (rms gain error ≈ 1 dB).", edge=ORANGE))
    P("8. Measured performance and comparison", H2)
    s.append(table([["Work", "Squint", "Rel. bandwidth", "Band"],
                    ["[18] (sim. only)", "48°", "34.3 %", "28–40 GHz"], ["[19]", "7°", "7.4 %", "91–98 GHz"],
                    ["[20]", "17°", "18.8 %", "24–29 GHz"], ["[21] metal FDM print", "19°", "24.4 %", "9–11.5 GHz"],
                    ["[22] serpentine", "30.6°", "37.5 %", "12–18 GHz"], ["[23]", "39°", "6 %", "9.7–10.3 GHz"],
                    ["[10] same group, parallel-plate", "42°", "16.6 %", "55–65 GHz"],
                    ["<b>this paper</b>", "<b>76°</b>", "<b>9.1 %</b>", "<b>58–63.5 GHz</b>"]],
                   [W * 0.4, W * 0.15, W * 0.2, W * 0.25]))
    P("Measured: gain 13–15 dBi, 76° with both ports, angle test 9° measured for a 10° target, i.e. 1° error.", CAP)
    s.append(PageBreak())

    # ---------------- 9 replica
    s.append(level_tag("advanced"))
    P("9. The replica in this repository", H1)
    s.append(Table([[img(os.path.join(IMG, "cad_top_slots.png"), W * 0.49),
                     img(os.path.join(IMG, "cad_slots_closeup.png"), W * 0.49)]], colWidths=[W * 0.5, W * 0.5]))
    P("Figure 7: replica CAD. Left: the radiating face with the serpentine legs and two flanges. Right: close-up of "
      "the alternately tilted slots, each cut through the narrow wall and into the broad walls.", CAP)
    s.append(table([["Item", "Value", "Source"],
                    ["waveguide a × b", f"{geo['a']} × {geo['b']} mm (WR15)", "paper"],
                    ["slot pitch d", f"{geo['d']:.2f} mm", "paper eq. 13"],
                    ["wall t / air gap", f"{geo['t']} / {geo['gap']} mm", "assumed (t + t + gap = 0.5 mm)"],
                    ["path between slots l", f"{geo['l']} mm; straight leg {geo['leg_straight']:.3f} mm + "
                     f"semicircular bend Rc = {geo['bend_rc']:.2f} mm", "paper l; bend shape assumed"],
                    ["slots", f"16, width {geo['w_slot']} mm, tilt/depth from Table II, alternating ±tilt",
                     "paper"],
                    ["feeds", "both at the bottom of legs 1 and 16, 90° E-plane elbow (R = 2 mm), horizontal WR15",
                     "assumed"],
                    ["flanges", f"Ø{geo['flange_d']} mm, 4 × Ø{geo['flange_hole_d']} mm holes on "
                                f"Ø{geo['flange_bolt_circle']} mm, {geo['flange_span']} mm apart",
                     "span from paper; flange pattern simplified, check against your UG-385/U"],
                    ["files", "01_cad/lwa_shell.step, lwa_shell.stl (print), lwa_air.step (FEM air volume)", ""]],
                   [W * 0.2, W * 0.52, W * 0.28], fs=7.8))
    s.append(Spacer(1, 4))
    P("To build one", H2)
    P("1) Print <font face='Courier'>lwa_shell.stl</font> on an SLA printer (25 µm), tilted 5–12°, with supports "
      "away from the slot face. 2) Measure the printed opening and adjust "
      "<font face='Courier'>P['a'], P['b'], P['l']</font> in <font face='Courier'>build_lwa_cad.py</font> to "
      "compensate shrinkage (the paper needed +0.1 mm and +0.2 mm). 3) Clean, cure, activate and silver-plate with "
      "the pump (section 7). 4) Measure S11/S21 on a VNA with WR15 transitions and the pattern on a turntable. "
      "<b>The 0.1 mm air gap between legs is at the limit of desktop SLA</b>; if it fuses, the slot ends see metal "
      "instead of air and the conductances change, so re-tune the depths.")
    s.append(PageBreak())

    # ---------------- 10 full-wave check
    s.append(level_tag("advanced"))
    P("10. Full-wave check of one slot (Hertzon / EMerge)", H1)
    P("<font face='Courier'>03_sim/slot_unit_cell.py</font> rebuilds the paper's unit cell in the open-source FEM "
      "simulator Hertzon (EMerge solver). It is a straight WR15 with one inclined slot (w = 0.261 mm) and two wave "
      "ports, radiating into an air box with an absorbing boundary. The radiated fraction "
      "P<sub>rad</sub> = 1 − |S11|² − |S21|² gives the slot conductance through P<sub>rad</sub> = 4g / (2 + g)².",
      LEAD)
    if os.path.exists(SIM):
        rows = list(csv.DictReader(open(SIM)))
        tab = [["tilt (°)", "depth (mm)", "f (GHz)", "S21 (dB)", "S11 (dB)", "P<sub>rad</sub>", "g sim",
                "g paper Fig. 4", "tets"]]
        for r in rows:
            tab.append([r["tilt_deg"], r["depth_mm"], r["f_GHz"], r["S21_dB"], r["S11_dB"], r["P_rad"], r["g_sim"],
                        r["g_paper_fig4"] if abs(float(r["f_GHz"]) - 60.75) < 0.01 else "", r["tets"]])
        s.append(table(tab, [W / 9] * 9, fs=7.6))
        s.append(Spacer(1, 4))
        s.append(callout(SIM_NOTE, edge=ORANGE))
    else:
        P("(Run 03_sim/slot_unit_cell.py to fill this table.)")
    P("What a full model would need", H2)
    P("The complete antenna is about 45 × 12 × 4 mm with 0.34 mm slots and thin walls. A converged FEM run is "
      "roughly 1–3 million unknowns per frequency. That is feasible on a 32–64 GB workstation with Hertzon, CST "
      "or HFSS using <font face='Courier'>01_cad/lwa_air.step</font>, but not on the 4-core / 15 GB machine used "
      "here.")
    s.append(PageBreak())

    # ---------------- glossary
    s.append(level_tag("basic"))
    P("11. Glossary", H1)
    s.append(table([["Term", "Meaning"],
                    ["LWA", "leaky-wave antenna: a guided wave that radiates continuously along its length"],
                    ["beam squint", "the beam direction changes with frequency"],
                    ["SISO / MIMO", "single / multiple input, multiple output: number of radar channels"],
                    ["FMCW", "frequency-modulated continuous wave radar: a chirp; range comes from the beat frequency"],
                    ["STFT", "short-time Fourier transform: FFTs of short overlapping windows"],
                    ["WR15", "standard waveguide for 50–75 GHz, 3.76 × 1.88 mm"],
                    ["TE10, cutoff", "the basic waveguide mode; below cutoff (39.9 GHz for WR15) nothing propagates"],
                    ["β, λg", "phase constant and wavelength of the wave inside the guide"],
                    ["Floquet harmonic", "the space harmonics of a periodic structure; m = −1 is the one that radiates"],
                    ["grating lobe", "an unwanted second main beam when elements are spaced more than ≈ λ/2 apart"],
                    ["Dolph–Chebyshev", "amplitude taper with equal sidelobes and the narrowest beam for a given "
                                        "sidelobe level"],
                    ["conductance g", "normalised power a slot takes out of the guide"],
                    ["HPBW", "half-power (−3 dB) beamwidth"], ["OSB", "open stopband: mismatch and gain dip near "
                                                                       "broadside in periodic LWAs"],
                    ["XPD", "cross-polarisation discrimination, co-pol / cross-pol power"],
                    ["SLA", "stereolithography 3D printing: a laser cures liquid resin layer by layer"],
                    ["Tollens' reaction", "chemical silver deposition from a silver-ammonia complex and a sugar"],
                    ["skin depth", "depth to which RF current flows in a metal; 0.25 µm for silver at 60 GHz"]],
                   [W * 0.22, W * 0.78]))
    s.append(Spacer(1, 6))
    P("Files: 02_python/lwa_design.py (all design equations, CSV and figures) · 01_cad/build_lwa_cad.py "
      "(STEP / STL) · 03_sim/slot_unit_cell.py (FEM check) · 04_docs/make_brief.py (this PDF).", SMALL)
    return s


SIM_NOTE = ""


def main():
    global SIM_NOTE
    SIM_NOTE = os.environ.get("SIM_NOTE", "Unit-cell results above; see 03_sim/README.md for the interpretation.")
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                            bottomMargin=16 * mm, title="60-GHz serpentine leaky-wave antenna: brief and replica",
                            author="RFMW-ANT repository", subject="after Gabsteiger et al., IEEE TAP 2026")
    doc.build(build(), onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
