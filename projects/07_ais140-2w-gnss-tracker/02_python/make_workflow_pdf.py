#!/usr/bin/env python3
"""Workflow & use-case guide (plain-language PDF) for CRL-TRK-2W-01.

Output: ../04_docs/CRL-TRK-2W-01_Workflow_UseCases.pdf
Needs reportlab (DejaVu Sans is used for arrows/symbols when present; falls back to Helvetica).
"""
import math
import os

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
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
OUT = os.path.join(ROOT, "04_docs", "CRL-TRK-2W-01_Workflow_UseCases.pdf")
RENDER = os.path.join(ROOT, "05_renders", "CRL-TRK-2W-01_3d_{}.png")

# ------------------------------------------------------------------ fonts / styles
FONT, BOLD = "Helvetica", "Helvetica-Bold"
DV = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DVB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if os.path.exists(DV) and os.path.exists(DVB):
    pdfmetrics.registerFont(TTFont("DV", DV))
    pdfmetrics.registerFont(TTFont("DVB", DVB))
    pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")
    FONT, BOLD = "DV", "DVB"

NAVY = colors.HexColor("#1F3A5F")
TEAL = colors.HexColor("#2A9D8F")
ORANGE = colors.HexColor("#E76F51")
GREY = colors.HexColor("#5C6670")
LIGHT = colors.HexColor("#EEF3F8")
C_PWR = colors.HexColor("#FDE2CF")
C_MCU = colors.HexColor("#D6E6F5")
C_RF = colors.HexColor("#D8F0EC")
C_IO = colors.HexColor("#F4EBC8")
C_ALERT = colors.HexColor("#F9D3CB")
C_CLOUD = colors.HexColor("#E4DDF4")
C_NOTE = colors.HexColor("#F2F2F2")

H1 = ParagraphStyle("H1", fontName=BOLD, fontSize=18, leading=22, textColor=NAVY, spaceAfter=4)
H2 = ParagraphStyle("H2", fontName=BOLD, fontSize=12, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("B", fontName=FONT, fontSize=9.4, leading=13, spaceAfter=4)
LEAD = ParagraphStyle("L", parent=BODY, fontSize=10.2, leading=14.2, textColor=GREY)
SMALL = ParagraphStyle("S", fontName=FONT, fontSize=8.1, leading=10.4)
CELLH = ParagraphStyle("CH", fontName=BOLD, fontSize=8.4, leading=10.6, textColor=colors.white)
CAP = ParagraphStyle("C", parent=SMALL, alignment=TA_CENTER, textColor=GREY, spaceBefore=2)

W = A4[0] - 36 * mm - 12  # frame width minus the 6 pt frame padding each side


# ------------------------------------------------------------------ diagram helpers
def box(d, x, y, w, h, label, fill, size=8.0, stroke=NAVY):
    """Rounded box, y = bottom edge; label lines split on '\\n', first line bold."""
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor=stroke, strokeWidth=0.9))
    lines = label.split("\n")
    lh = size * 1.2
    top = y + h / 2 + (len(lines) - 1) * lh / 2 - size * 0.35
    for i, ln in enumerate(lines):
        d.add(String(x + w / 2, top - i * lh, ln, fontName=BOLD if i == 0 else FONT,
                     fontSize=size if i == 0 else size - 0.7, textAnchor="middle", fillColor=colors.black))


def arrow(d, x1, y1, x2, y2, color=NAVY, label=None, lx=None, ly=None, lsize=6.6, anchor="middle"):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.1))
    a = math.atan2(y2 - y1, x2 - x1)
    h = 5.5
    d.add(Polygon([x2, y2,
                   x2 - h * math.cos(a - 0.4), y2 - h * math.sin(a - 0.4),
                   x2 - h * math.cos(a + 0.4), y2 - h * math.sin(a + 0.4)],
                  fillColor=color, strokeColor=color, strokeWidth=0.4))
    if label:
        lx = (x1 + x2) / 2 if lx is None else lx
        ly = (y1 + y2) / 2 + 3 if ly is None else ly
        for i, ln in enumerate(label.split("\n")):
            d.add(String(lx, ly - i * lsize * 1.15, ln, fontName=FONT, fontSize=lsize,
                         textAnchor=anchor, fillColor=GREY))


def seg(d, x1, y1, x2, y2, color=NAVY):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.1))


def txt(d, x, y, s, size=7.0, bold=False, color=GREY, anchor="middle"):
    d.add(String(x, y, s, fontName=BOLD if bold else FONT, fontSize=size, textAnchor=anchor, fillColor=color))


def chain(steps, fill, h=56, size=7.6, numbered=True):
    """One horizontal row of boxes joined by arrows."""
    n = len(steps)
    gap = 13
    bw = (W - gap * (n - 1)) / n
    d = Drawing(W, h + 14 if numbered else h + 2)
    for i, s in enumerate(steps):
        x = i * (bw + gap)
        f = fill[i] if isinstance(fill, (list, tuple)) else fill
        box(d, x, 0, bw, h, s, f, size=size)
        if numbered:
            txt(d, x + 8, h + 4, str(i + 1), 8, True, ORANGE, "start")
        if i:
            arrow(d, x - gap + 1, h / 2, x - 1, h / 2)
    return d


def snake(steps, fills, cols=4, bw_h=62, size=7.6, vgap=26):
    """Grid of boxes read left→right, then right→left on the next row (boustrophedon)."""
    rows = (len(steps) + cols - 1) // cols
    gap = 18
    bw = (W - gap * (cols - 1)) / cols
    hgt = rows * bw_h + (rows - 1) * vgap + 12
    d = Drawing(W, hgt)
    pos = []
    for i, s in enumerate(steps):
        r, c = divmod(i, cols)
        if r % 2:
            c = cols - 1 - c
        x = c * (bw + gap)
        y = hgt - 12 - (r + 1) * bw_h - r * vgap
        box(d, x, y, bw, bw_h, s, fills[i], size=size)
        txt(d, x + 7, y + bw_h + 3, str(i + 1), 8, True, ORANGE, "start")
        pos.append((x, y, r))
    for i in range(1, len(steps)):
        (x0, y0, r0), (x1, y1, r1) = pos[i - 1], pos[i]
        if r0 == r1:
            if x1 > x0:
                arrow(d, x0 + bw + 1, y0 + bw_h / 2, x1 - 1, y1 + bw_h / 2)
            else:
                arrow(d, x0 - 1, y0 + bw_h / 2, x1 + bw + 1, y1 + bw_h / 2)
        else:
            arrow(d, x0 + bw / 2, y0 - 1, x1 + bw / 2, y1 + bw_h + 11)
    return d


# ------------------------------------------------------------------ diagrams
def fit(d):
    """Scale a drawing laid out on a fixed native width to the frame width."""
    k = W / d.width
    d.scale(k, k)
    d.width, d.height = W, d.height * k
    return d


def big_picture():
    d = Drawing(493, 150)
    box(d, 0, 45, 92, 66, "Motorcycle\nignition, SOS button,\nstarter relay", C_IO)
    box(d, 112, 40, 104, 76, "CRL-TRK-2W-01\ntracker under the seat\nGNSS + LTE-M + IMU\nbackup battery", C_MCU)
    box(d, 238, 45, 82, 66, "LTE-M / NB-IoT\nmobile network\n(Jio, Airtel, Vi …)", C_RF)
    box(d, 342, 45, 70, 66, "Cloud server\nMQTT / HTTPS\ndatabase, rules", C_CLOUD)
    box(d, 432, 88, 61, 50, "Owner app\nmap, alerts,\nimmobilise", C_CLOUD, size=7.4)
    box(d, 432, 18, 61, 50, "Control room\nAIS-140 state\nbackend (VLTD)", C_CLOUD, size=7.4)
    arrow(d, 92, 78, 112, 78)
    arrow(d, 216, 85, 238, 85)
    arrow(d, 238, 70, 216, 70)
    txt(d, 227, 120, "data ⇄ commands", 6.6)
    arrow(d, 320, 85, 342, 85)
    arrow(d, 342, 70, 320, 70)
    arrow(d, 412, 90, 432, 112)
    arrow(d, 412, 66, 432, 44)
    box(d, 112, 0, 104, 26, "Satellites\nGPS · Galileo · BeiDou · NavIC", C_NOTE, size=6.8)
    arrow(d, 164, 26, 164, 40)
    txt(d, 164, 128, "position every 1–10 s", 6.8)
    return d


def block_diagram():
    d = Drawing(515, 262)
    box(d, 0, 196, 88, 54, "Vehicle harness\n9–36 V, IGN, SOS,\nDIN1, AIN1, DOUT1", C_PWR)
    box(d, 0, 118, 88, 54, "USB-C\n5 V, flashing,\nlogs, JTAG", C_PWR)
    box(d, 0, 30, 88, 60, "18650 backup\n3000 mAh pack\nwith NTC sensor", C_PWR)
    box(d, 106, 196, 96, 54, "Protection\nfuse · 33 V TVS ·\nideal diode", C_PWR)
    box(d, 106, 118, 96, 54, "Power\n100 V buck → 5 V,\ncharger, 3.3 V LDO", C_PWR)
    arrow(d, 88, 223, 106, 223)
    arrow(d, 154, 196, 154, 172)
    arrow(d, 88, 145, 106, 145)
    seg(d, 88, 60, 154, 60)
    arrow(d, 154, 60, 154, 118)
    txt(d, 121, 64, "charge / backup", 6.4)
    box(d, 224, 100, 104, 92, "ESP32-S3\n“the brain”\nrules, alerts, TLS,\nOTA, BLE setup", C_MCU, size=8.6)
    arrow(d, 202, 145, 224, 145, label="3.3 V")
    box(d, 224, 208, 104, 42, "Input conditioning\nclamps + filters", C_IO, size=7.6)
    seg(d, 88, 240, 96, 240)
    seg(d, 96, 240, 96, 258)
    seg(d, 96, 258, 276, 258)
    arrow(d, 276, 258, 276, 250)
    arrow(d, 276, 208, 276, 192)
    box(d, 224, 22, 104, 58, "Memory & time\n16 MB log flash,\nRTC, battery gauge", C_MCU)
    arrow(d, 276, 100, 276, 80)
    box(d, 352, 196, 102, 54, "Cellular\nSIM7080G\nLTE-M / NB-IoT", C_RF)
    box(d, 352, 118, 102, 54, "GNSS\nNEO-F10N L1/L5\nGPS+Galileo+NavIC", C_RF)
    box(d, 352, 30, 102, 58, "Motion sensor\nIIM-42652 IMU\nwake-on-motion,\ncrash detect", C_RF)
    arrow(d, 328, 175, 352, 215, label="UART", lx=326, ly=203, anchor="end")
    arrow(d, 328, 145, 352, 145, label="UART")
    arrow(d, 328, 115, 352, 70, label="SPI + INT", lx=343, ly=100, anchor="start")
    # antennas
    for y, lab in ((223, "LTE ant.\n(U.FL)"), (145, "GNSS ant.\n(U.FL)")):
        seg(d, 454, y, 466, y)
        seg(d, 466, y, 466, y + 12)
        seg(d, 466, y + 12, 459, y + 20)
        seg(d, 466, y + 12, 473, y + 20)
        txt(d, 480, y - 2, lab.split("\n")[0], 6.4, anchor="start")
        txt(d, 480, y - 10, lab.split("\n")[1], 6.4, anchor="start")
    return d


def state_diagram():
    d = Drawing(W, 300)
    bw, bh = 140, 58
    xl, xr = 10, W - 10 - bw
    box(d, xl, 120, bw, bh, "PARKED (sleep)\nignition off, ≈ 110 µA\nIMU watches for motion\nheartbeat every few hours",
        C_MCU, size=8.4)
    box(d, xr, 120, bw, bh, "DRIVING (tracking)\nGNSS on, report every\n10 s (AIS-140 rate)\nlog + live upload",
        C_RF, size=8.4)
    box(d, xl, 232, bw, bh, "THEFT ALERT\nmotion without ignition\n→ alarm + live position", C_ALERT, size=8.4)
    box(d, xr, 232, bw, bh, "EMERGENCY\nSOS pressed / crash\n→ alert to control room", C_ALERT, size=8.4)
    box(d, xr, 8, bw, bh, "POWER CUT\nvehicle wire cut/removed\n→ alert, runs on battery\n≈ 40 h tracking",
        C_PWR, size=8.4)
    box(d, xl, 8, bw, bh, "CONFIG / UPDATE\nBLE setup (5 min window),\nOTA firmware via LTE",
        C_IO, size=8.4)
    # parked <-> driving
    arrow(d, xl + bw, 160, xr, 160, label="ignition ON", ly=164)
    arrow(d, xr, 138, xl + bw, 138, label="ignition OFF (after 2 min)", ly=126)
    # parked <-> theft
    arrow(d, xl + 45, 178, xl + 45, 232, label="motion,\nno ignition", lx=xl + 41, ly=210, anchor="end")
    arrow(d, xl + 100, 232, xl + 100, 178, label="owner acks /\ntimeout", lx=xl + 104, ly=210, anchor="start")
    # driving <-> emergency
    arrow(d, xr + 45, 178, xr + 45, 232, label="SOS / crash", lx=xr + 41, ly=207, anchor="end")
    arrow(d, xr + 100, 232, xr + 100, 178, label="cleared by\ncontrol room", lx=xr + 104, ly=210, anchor="start")
    # driving <-> power cut
    arrow(d, xr + 45, 120, xr + 45, 66, label="main power\nlost", lx=xr + 41, ly=98, anchor="end")
    arrow(d, xr + 100, 66, xr + 100, 120, label="power\nrestored", lx=xr + 104, ly=98, anchor="start")
    # parked <-> config
    arrow(d, xl + 45, 120, xl + 45, 66, label="button /\nserver cmd", lx=xl + 41, ly=98, anchor="end")
    arrow(d, xl + 100, 66, xl + 100, 120, label="done /\nreboot", lx=xl + 104, ly=98, anchor="start")
    # centre note
    box(d, xl + bw + 32, 200, xr - xl - bw - 64, 64,
        "Always, in every state\nno network → store in 16 MB flash\n(≈ 400 000 points), send later;\n"
        "watchdog restarts a stuck modem", C_NOTE, size=7.6, stroke=GREY)
    box(d, xl + bw + 32, 22, xr - xl - bw - 64, 64,
        "Panic button wakes the\ndevice in any state\nand goes straight to\nEMERGENCY", C_NOTE, size=7.6, stroke=GREY)
    return d


def design_flow():
    steps = [
        "Requirements\nmotorcycle, AIS-140,\n60×45 mm, 9–36 V",
        "Part selection\nSIM7080G, NEO-F10N,\nESP32-S3, BQ24074",
        "design.py\none Python file =\nwhole circuit",
        "Schematic\n6 sheets, KiCad 9\nERC: 0 errors",
        "Placement\n4-layer stack-up,\nparts on both sides",
        "RF + power first\n50 Ω antenna lines,\nGND / 3V3 vias",
        "Auto-routing\nFreerouting 1.9\n+ A* finisher",
        "Checks\nDRC 0 errors,\n0 unconnected",
        "Fab outputs\nGerbers, drill,\nBOM, pick & place",
        "3D + drawings\nSTEP, renders,\nassembly PDFs",
        "Reports\npower, EMC, SI,\nDFM, test, verify",
        "GitHub\nevery file versioned\nin sanu0910/rfmw-ant",
    ]
    fills = [C_IO, C_IO, C_MCU, C_MCU, C_RF, C_RF, C_RF, C_ALERT, C_PWR, C_PWR, C_CLOUD, C_CLOUD]
    return snake(steps, fills, cols=4, bw_h=58)


def production_flow():
    steps = [
        "Bare PCB\n4-layer, 1.6 mm,\nimpedance control",
        "SMT assembly\nboth sides,\nJLCPCB / PCBWay",
        "Inspection\nAOI + X-ray on\nmodules & QFNs",
        "Fixture test\npogo pins: rails,\nreverse 13.5 V",
        "Flash firmware\nUSB-C or pogo,\nserial no. + keys",
        "Self-test\nsensors, flash,\nGNSS, modem ATI",
        "RF test\nGNSS C/N0 ≥ 40,\nLTE attach + TX",
        "Sleep current\n< 150 µA on\nbattery only",
        "Final assembly\nantennas, battery,\nIP67 leak test",
        "Label & ship\nIMEI / QR,\nlot traceability",
    ]
    fills = [C_PWR, C_PWR, C_ALERT, C_ALERT, C_MCU, C_MCU, C_RF, C_RF, C_IO, C_CLOUD]
    return snake(steps, fills, cols=5, bw_h=56, size=7.2)


def install_flow():
    return chain(["Mount\nunder seat, label up,\nGPS antenna sky-facing",
                  "Wire harness\n+12 V via 3 A fuse,\nGND, IGN, SOS",
                  "Connect\nantennas + backup\nbattery, close lid",
                  "Power on\nLED blink, GNSS fix\nwithin ~1 min",
                  "Activate\nBLE setup: server,\nvehicle no., geofence"],
                 [C_IO, C_PWR, C_RF, C_MCU, C_CLOUD], h=58, size=7.4)


# ------------------------------------------------------------------ tables
def table(rows, widths, head_bg=NAVY, zebra=True, font_size=None):
    st = SMALL if font_size is None else ParagraphStyle("t", parent=SMALL, fontSize=font_size,
                                                        leading=font_size * 1.28)
    data = [[Paragraph(c, CELLH) for c in rows[0]]]
    data += [[c if not isinstance(c, str) else Paragraph(c, st) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), head_bg),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#C8D2DC")),
             ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
             ("LEFTPADDING", (0, 0), (-1, -1), 4.5), ("RIGHTPADDING", (0, 0), (-1, -1), 4.5)]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    return t


def callout(html, bg=LIGHT, edge=TEAL):
    t = Table([[Paragraph(html, BODY)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


# ------------------------------------------------------------------ page decoration
def on_page(c, doc):
    if doc.page == 1:
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)
        c.setFillColor(ORANGE)
        c.rect(0, A4[1] - 17.5 * mm, A4[0], 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont(BOLD, 10)
        c.drawString(18 * mm, A4[1] - 10 * mm, "CRL-TRK-2W-01  ·  Workflow & Use-Case Guide")
        c.restoreState()
        return
    c.saveState()
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.8)
    c.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
    c.setFont(FONT, 7.5)
    c.setFillColor(GREY)
    c.drawString(18 * mm, A4[1] - 11 * mm, "CRL-TRK-2W-01 — AIS-140 two-wheeler GNSS / LTE-M tracker")
    c.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "Workflow & use-case guide · rev A0")
    c.drawString(18 * mm, 10 * mm, "projects/07_ais140-2w-gnss-tracker · github.com/sanu0910/rfmw-ant")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"page {doc.page}")
    c.restoreState()


def img(name, width):
    p = RENDER.format(name)
    if not os.path.exists(p):
        return Spacer(1, 1)
    from PIL import Image as PImage
    w, h = PImage.open(p).size
    return Image(p, width=width, height=width * h / w)


# ------------------------------------------------------------------ content
def build():
    s = []
    P = lambda t, st=BODY: s.append(Paragraph(t, st))  # noqa: E731

    # ---------------- cover
    s.append(Spacer(1, 14 * mm))
    P("Motorcycle GPS Tracker", ParagraphStyle("T", parent=H1, fontSize=30, leading=35))
    P("How it works, how it was built, and what it is used for", ParagraphStyle("T2", parent=LEAD, fontSize=14,
                                                                                    leading=18))
    s.append(Spacer(1, 6 * mm))
    s.append(img("iso", W * 0.86))
    P("The finished CRL-TRK-2W-01 board (60 × 45 mm), 3D view generated from the KiCad design.", CAP)
    s.append(Spacer(1, 6 * mm))
    facts = [["What", "Where", "Power", "Status"],
             ["GPS + NavIC tracker with LTE-M/NB-IoT, motion sensor, SOS input and starter-cut relay output",
              "India, AIS-140 commercial fleets; motorcycles and scooters (12 V and 24 V vehicles)",
              "9–36 V from the bike + 18650 backup pack (≈ 40 h of tracking after a wire cut)",
              "Rev A0 design complete: ERC/DRC clean, Gerbers, BOM and pick-and-place ready for prototypes"]]
    s.append(table(facts, [W / 4] * 4, zebra=False))
    s.append(Spacer(1, 5 * mm))
    P("<b>Who should read this:</b> fleet owners, installers, firmware developers, hardware and production "
      "engineers. Each page starts with a plain-language summary; the details follow below it.", LEAD)
    s.append(PageBreak())

    # ---------------- contents
    P("Contents", H1)
    toc = [["#", "Section", "For"],
           ["1", "The big picture: what the tracker does", "everyone"],
           ["2", "Inside the box: block diagram", "everyone, engineers"],
           ["3", "Use cases: real situations and what happens", "owners, fleet managers, sales"],
           ["4", "Operating workflow: the device's modes", "owners, firmware, support"],
           ["5", "Step-by-step flows for the key alerts", "firmware, control room, support"],
           ["6", "Installation and wiring", "installers"],
           ["7", "Design workflow: how the PCB was made", "hardware engineers"],
           ["8", "Production and test workflow", "factory, quality"],
           ["9", "Which file do I need?", "everyone"],
           ["10", "Glossary and open items", "everyone"]]
    s.append(table(toc, [12 * mm, 105 * mm, W - 117 * mm]))
    s.append(Spacer(1, 6 * mm))
    s.append(callout("<b>In one sentence:</b> a small box under the seat that always knows where the bike is, "
                     "tells the owner and the control room over the mobile network, raises an alarm if the bike "
                     "is moved, crashed, has its power cut or the rider presses SOS, and can stop the engine "
                     "from starting on command."))

    # ---------------- 1 big picture
    s.append(Spacer(1, 8 * mm))
    P("1. The big picture", H1)
    P("The tracker reads the satellites to know its position, adds what it feels (motion, crash, ignition, "
      "battery) and sends a short message over LTE-M / NB-IoT. That is the low-power 4G variant made for "
      "machines. A cloud server stores the messages, applies the rules (geofence, alarms) and shows the result "
      "in an app and, for AIS-140 vehicles, in the state control room. Commands such as “immobilise” or "
      "“update firmware” travel back the same way.", LEAD)
    s.append(fit(big_picture()))
    P("Figure 1: from the bike to the people who need the information.", CAP)
    s.append(PageBreak())

    # ---------------- 2 block diagram
    P("2. Inside the box", H1)
    P("Power comes from the vehicle and, when that is missing, from the backup pack. Everything is protected "
      "against the electrical abuse of a motorcycle: load dumps, reversed wires and spikes. A single "
      "microcontroller runs the rules and talks to three specialist chips.", LEAD)
    s.append(fit(block_diagram()))
    P("Figure 2: functional block diagram (orange = power, blue = control, green = radios/sensors).", CAP)
    P("What each block does", H2)
    blocks = [["Block", "Main part", "Job, in plain words"],
              ["Protection", "fuse, SMBJ33CA TVS, LM74700-Q1 + 60 V MOSFET",
               "Survives a reversed battery (−33 V), load-dump spikes and jump starts without blowing up."],
              ["Power", "LM5164-Q1, BQ24074, TLV75733, 2× TPS22917",
               "Turns 9–36 V into 5 V and 3.3 V, charges the backup pack and switches the radios fully off "
               "when they are not needed."],
              ["Brain", "ESP32-S3-WROOM-1",
               "Runs the firmware: decides when to wake, what to send, encrypts it (TLS), BLE setup, OTA."],
              ["Cellular", "SIMCom SIM7080G",
               "LTE-M / NB-IoT data and SMS. It sleeps at 3 µA (PSM) between reports."],
              ["GNSS", "u-blox NEO-F10N",
               "Dual-band L1/L5 position from GPS, Galileo, BeiDou and the Indian <b>NavIC</b> required by AIS-140."],
              ["Motion", "TDK IIM-42652",
               "Wakes the system when the parked bike is touched; detects crashes and falls."],
              ["Memory & time", "W25Q128 flash, RV-3028 RTC, LC709203F",
               "Stores ≈ 400 000 positions offline, keeps time, measures battery charge and logs lid tamper."],
              ["I/O", "J1 Micro-Fit 2×4",
               "Ignition sense, SOS button, spare digital/analog input, starter-cut relay output."]]
    s.append(table(blocks, [24 * mm, 52 * mm, W - 76 * mm]))
    s.append(PageBreak())

    # ---------------- 3 use cases
    P("3. Use cases", H1)
    P("Each row is one real-life situation. “Device” is what the tracker does by itself; "
      "“People see” is what reaches the owner, fleet manager or control room.", LEAD)
    uc = [["Use case", "Situation", "Device", "People see"],
          ["<b>Live tracking</b>", "Bike is being ridden",
           "GNSS fix every second, reports every 10 s (configurable), speed and heading",
           "Moving dot on a map, trip history, distance, overspeed"],
          ["<b>Theft alert</b>", "Parked bike is pushed, lifted or towed",
           "IMU wakes the CPU without ignition → GNSS + LTE on → alarm and fast reporting",
           "Push notification “Bike moved!” with live position"],
          ["<b>Immobiliser</b>", "Owner/police wants to stop a stolen bike",
           "Server command → DOUT1 drives the starter-cut relay (only at low speed or standstill)",
           "“Engine disabled” confirmation; re-enable from the app"],
          ["<b>Crash detection</b>", "Rider falls or hits something",
           "IMU sees > 6 g shock + bike lying > 60° for > 2 s → crash event with position",
           "Emergency alert to family / fleet / control room"],
          ["<b>Panic / SOS</b>", "Rider or passenger in danger (AIS-140)",
           "SOS button wakes the device from any state, sends emergency packet + SMS fallback",
           "Emergency on the state control-room screen"],
          ["<b>Geofence</b>", "Vehicle leaves an allowed zone or enters a banned one",
           "Zones stored on the device, checked on every fix (20 m hysteresis)",
           "Enter / exit alert; works even with no network (sent later)"],
          ["<b>Power-cut / tamper</b>", "Thief cuts the tracker wire or opens the box",
           "Detects loss of vehicle voltage or lid switch, keeps tracking on the 18650 for ≈ 40 h",
           "“Main power removed” / “Tamper” alert, tracking continues"],
          ["<b>Battery health</b>", "Bike left parked for weeks",
           "Measures the bike's battery and the backup pack; deep sleep ≈ 110 µA",
           "Low-battery warning before the bike will not start"],
          ["<b>Offline log</b>", "No coverage (tunnel, hills, basement)",
           "Positions written to 16 MB flash, uploaded in order when the network returns",
           "Complete route with no gaps"],
          ["<b>Remote update</b>", "Bug fix or new feature",
           "Downloads new firmware over LTE, verifies it, swaps A/B slot, rolls back if it fails",
           "Fleet updated without visiting the vehicles"],
          ["<b>BLE setup</b>", "Installer configures a new unit",
           "BLE open for 5 min after power-up, phone pairing with passkey",
           "Vehicle number, server and zones set from a phone"],
          ["<b>AIS-140 fleet</b>", "Taxi bikes, rentals, delivery and commercial 2-wheelers",
           "NavIC fix, SOS, tamper, required packet format to the state backend",
           "Compliance for permits and the RTO"]]
    s.append(table(uc, [25 * mm, 36 * mm, 62 * mm, W - 123 * mm], font_size=7.8))
    s.append(PageBreak())

    # ---------------- 4 states
    P("4. Operating workflow: the device's modes", H1)
    P("The tracker is always in one of a few modes. It spends most of its life <b>parked and asleep</b> to protect "
      "the bike's battery and wakes instantly when something happens. Arrows show what makes it change mode.",
      LEAD)
    s.append(state_diagram())
    P("Figure 3: operating modes and transitions.", CAP)
    P("Power in each mode", H2)
    pw = [["Mode", "What is on", "Current (approx.)", "Comment"],
          ["Parked", "LDO, RTC, IMU wake-on-motion, modem PSM, GNSS backup memory",
           "≈ 110 µA (pack) + ≈ 25 µA (bike)", "> 12 months on the 3000 mAh pack"],
          ["Driving", "GNSS, modem, CPU", "≈ 70 mA average", "from the bike; the pack charges at the same time"],
          ["Power cut", "same as driving, from the pack", "≈ 70 mA", "≈ 40 h; AIS-140 asks for ≥ 4 h"],
          ["Transmit burst", "modem RF", "up to 0.5 A for ms", "buffered by 110 µF at the modem"]]
    s.append(table(pw, [24 * mm, 66 * mm, 44 * mm, W - 134 * mm]))
    s.append(PageBreak())

    # ---------------- 5 alert flows
    P("5. Step-by-step flows for the key alerts", H1)
    P("These are the exact sequences the firmware follows. They are useful for the control-room team "
      "(what will arrive, and when) and for firmware testing.", LEAD)
    flows = [
        ("Theft: parked bike is moved", [
            "Motion\nIMU interrupt while\nignition is OFF",
            "Wake\nCPU leaves deep\nsleep (< 1 s)",
            "Confirm\nmotion > 10 s, not\njust wind / a bump",
            "Locate\nGNSS on, hot start\nfix ≈ 2–5 s",
            "Alert\nTHEFT + position,\nthen every 10 s"], C_ALERT),
        ("Crash / fall", [
            "Shock\nIMU > 6 g peak\nat 1 kHz sampling",
            "Check posture\nroll / pitch > 60°\nfor > 2 s",
            "Grace period\n30 s to cancel via\nIGN off/on or button",
            "Send\nCRASH event + last\n30 s of data",
            "Follow-up\nfast tracking until\ncleared"], C_ALERT),
        ("Panic / SOS (AIS-140)", [
            "Press\nSOS button pulls\nPANIC to GND",
            "Wake\nfrom any mode,\ndebounced 50 ms",
            "Fix\nGNSS + NavIC\nposition",
            "Emergency\npacket to state\nbackend + SMS",
            "Repeat\nuntil control room\nacknowledges"], C_ALERT),
        ("Main power cut / tamper", [
            "Detect\nVIN < 6 V or lid\nswitch opens",
            "Switch\ncharger hands over\nto 18650 seamlessly",
            "Alert\nPOWER-CUT or\nTAMPER + time",
            "Keep tracking\non battery ≈ 40 h",
            "Restore\npower back →\nnormal + recharge"], C_PWR),
        ("No network", [
            "Lose\nLTE-M / NB-IoT\nregistration",
            "Store\nevery point to\nflash ring buffer",
            "Retry\nback-off; modem\npower-cycle if stuck",
            "Reconnect\nnetwork found",
            "Replay\nbacklog in order,\nthen live again"], C_MCU),
        ("Firmware update (OTA)", [
            "Command\nserver says new\nversion available",
            "Download\nHTTPS over LTE\ninto spare slot",
            "Verify\nsignature +\nchecksum",
            "Reboot\ninto new slot",
            "Self-check\nOK → keep;\nfail → roll back"], C_CLOUD),
    ]
    for title, steps, fill in flows:
        s.append(KeepTogether([Paragraph(title, H2), chain(steps, fill, h=50, size=7.3, numbered=False)]))
    s.append(PageBreak())

    # ---------------- 6 installation
    P("6. Installation and wiring", H1)
    P("Typical install time is 20–30 minutes. The box goes under the seat or a side panel. The GPS antenna "
      "must see the sky through plastic, not metal.", LEAD)
    s.append(install_flow())
    P("Harness connector J1 (Molex Micro-Fit 3.0, 2 × 4)", H2)
    j1 = [["Pin", "Signal", "Connect to", "Notes"],
          ["1", "+12V (BAT)", "battery + through a 3 A inline blade fuse",
           "permanent supply, 9–36 V; reverse-polarity proof"],
          ["2", "IGN", "ignition-switched wire (key ON = 12 V)", "wakes the device, starts a trip"],
          ["3", "PANIC / SOS", "SOS push-button to GND", "mandatory for AIS-140"],
          ["4", "DIN1", "spare input (e.g. seat/lid switch, door)", "active high, 9–36 V tolerant"],
          ["5", "GND", "battery − / chassis", "short, thick wire"],
          ["6", "AIN1", "analog sensor 0–30 V (e.g. fuel level)", "read by the ADC"],
          ["7", "DOUT1", "starter-cut relay coil (low side)", "immobiliser; 12 V relay, max 500 mA"],
          ["8", "GND", "second ground", "relay return / sensor ground"]]
    s.append(table(j1, [11 * mm, 25 * mm, 68 * mm, W - 104 * mm]))
    P("Other connections", H2)
    oc = [["Item", "Detail"],
          ["GPS/NavIC antenna", "active L1/L5 patch on U.FL J7; mount face-up under the seat plastic or tail cowl"],
          ["LTE antenna", "flex antenna on U.FL J6; stick on the inner lid, ≥ 2 cm away from metal and the GPS patch"],
          ["Backup battery", "1S 18650 pack with protection board and 10 k NTC, on the bottom connector J2"],
          ["SIM", "nano-SIM holder J5 for rev A (an embedded eSIM footprint is planned for rev B, see section 10)"],
          ["USB-C (J3)", "service only: firmware flash, logs and setup on the bench; keep it sealed in the field"]]
    s.append(table(oc, [32 * mm, W - 32 * mm]))
    s.append(Spacer(1, 4 * mm))
    s.append(callout("<b>Installer checklist:</b> fuse fitted · IGN goes high with the key · SOS triggers an "
                     "alert in the app · GNSS fix shown · LTE signal OK · relay cuts the starter when commanded · "
                     "lid closed and the cable gland tight (IP67).", bg=colors.HexColor("#FFF4E8"), edge=ORANGE))
    s.append(PageBreak())

    # ---------------- 7 design workflow
    P("7. Design workflow: how the PCB was made", H1)
    P("The design is <b>code-first</b>. One Python file (<font face='%s'>design.py</font>) describes every part and "
      "connection. Scripts turn it into the KiCad schematic, the board, and the manufacturing files. Changing a "
      "part means editing one line and re-running the scripts, so the schematic, PCB, BOM and firmware pin map "
      "never drift apart." % FONT, LEAD)
    s.append(design_flow())
    P("Figure 4: design pipeline, read in a snake (row 1 → right, row 2 ← left, row 3 → right).", CAP)
    P("Tools and the script for each step", H2)
    tl = [["Step", "Tool / script", "Output"],
          ["Circuit", "02_python/design.py, make_lib.py", "parts, nets, MPNs, library symbols and footprints"],
          ["Schematic", "make_schematic.py → KiCad 9 (kicad-cli ERC)", "tracker.kicad_sch + 6 sub-sheets, schematic PDF"],
          ["Board", "make_pcb.py place / dsn (pcbnew Python)", "outline, 4-layer stack-up, rules, placement"],
          ["RF + power", "make_pcb.py, rf_calc.py", "50 Ω coplanar lines to U.FL, GND & 3.3 V vias"],
          ["Routing", "Freerouting 1.9 + patch_route.py (A* with rip-up)", "all 180 parts connected, 399 vias"],
          ["Verification", "kicad-cli DRC with schematic parity", "0 errors, 0 unconnected, parity clean"],
          ["Manufacturing", "kicad-cli export, make_bom.py, make_cpl.py", "Gerbers zip, JLC BOM + CPL, engineering BOM"],
          ["Docs", "make_models.py, make_pins.py, this script", "STEP, renders, board_pins.h, reports, this PDF"],
          ["Altium", "Altium Import Wizard → KiCad", "same design opened natively in Altium 21+"],
          ["AI assistant", "KiCad MCP server (/opt/KiCAD-MCP-Server)", "244 tools to inspect / edit the board from Claude"]]
    s.append(table(tl, [26 * mm, 72 * mm, W - 98 * mm], font_size=7.8))
    s.append(PageBreak())

    # ---------------- 8 production
    P("8. Production and test workflow", H1)
    P("From the Gerber zip to a sealed, labelled tracker. Every unit goes through the same ten steps. The "
      "fixture uses the bottom-side pogo pads (TP1–TP28), so no extra connector is needed.", LEAD)
    s.append(production_flow())
    P("Figure 5: production flow, read in a snake (row 1 → right, row 2 ← left).", CAP)
    P("Pass / fail limits", H2)
    pf = [["Test", "How", "Pass"],
          ["Power rails", "13.5 V / 1 A limit on J1, probe TP10–TP16",
           "5.0 ± 0.1 V, VSYS 4.4 V, 3.30 ± 0.05 V, input < 30 mA"],
          ["Reverse / over-voltage", "−13.5 V for 1 s, then 30 V", "< 1 mA reverse, rails unchanged, no damage"],
          ["Digital self-test", "test firmware: I²C scan, flash ID, IMU ID, GNSS version, modem ATI / CCID",
           "all devices answer"],
          ["Inputs / output", "fixture drives IGN, SOS, DIN1, AIN1; loads DOUT1", "levels and ADC within ± 3 %"],
          ["GNSS RF", "−130 dBm L1 + L5 from a generator", "C/N0 ≥ 40 dB-Hz"],
          ["LTE RF", "shielded box / call-box", "network attach, RSSI and TX power within spec"],
          ["Sleep", "battery only, 60 s after sleep command", "< 150 µA"],
          ["Charger", "NTC simulated at 25 °C and 50 °C", "charges at 25 °C, stops at 50 °C"],
          ["Enclosure", "pressure-decay leak test", "IP67"]]
    s.append(table(pf, [32 * mm, 80 * mm, W - 112 * mm], font_size=7.8))
    s.append(Spacer(1, 4 * mm))
    s.append(KeepTogether([Paragraph("Board views", H2),
                           Table([[img("top", W / 2 - 6), img("bottom", W / 2 - 6)],
                                  [Paragraph("Top: modules, power, connectors", CAP),
                                   Paragraph("Bottom: small parts, SIM, USB-C, test pads", CAP)]],
                                 colWidths=[W / 2, W / 2])]))
    s.append(PageBreak())

    # ---------------- 9 which file
    P("9. Which file do I need?", H1)
    P("All files are in <b>projects/07_ais140-2w-gnss-tracker/</b> of the GitHub repository.", LEAD)
    wf = [["I am a …", "I want to …", "Open"],
          ["Fleet owner / manager", "understand features and alerts", "this PDF (sections 1, 3–5)"],
          ["Installer", "wire and mount the unit", "this PDF section 6; 04_docs/DESIGN_REPORT.md §6"],
          ["Purchasing", "order parts and boards", "03_fab/BOM_JLCPCB.csv, BOM_engineering.csv, 04_docs/BOM.md"],
          ["PCB fab / assembler", "make the board", "03_fab/CRL-TRK-2W-01_gerbers.zip, CPL_JLCPCB.csv, BOM_JLCPCB.csv"],
          ["Hardware engineer", "review or change the design",
           "01_kicad/tracker.kicad_pro, 02_python/design.py, 04_docs/DESIGN_REPORT.md"],
          ["Altium user", "open the design in Altium", "Import Wizard → KiCad → 01_kicad/tracker.kicad_pro"],
          ["Firmware developer", "write the code", "06_firmware/board_pins.h, DESIGN_REPORT §10 (firmware architecture)"],
          ["Mechanical designer", "design the enclosure", "05_renders/CRL-TRK-2W-01.step, assembly_top/bottom.pdf"],
          ["Test / quality", "build the fixture", "DESIGN_REPORT §8 (test pads, production checklist)"],
          ["Certification", "plan AIS-140 / BIS / WPC / TEC", "DESIGN_REPORT §9, 04_docs/VERIFY_LIST.md"]]
    s.append(table(wf, [34 * mm, 46 * mm, W - 80 * mm]))
    s.append(Spacer(1, 6 * mm))
    P("Regenerate everything", H2)
    s.append(callout("<font face='Courier' size='8'>cd projects/07_ais140-2w-gnss-tracker/02_python<br/>"
                     "python3 make_lib.py &amp;&amp; python3 make_schematic.py &amp;&amp; python3 make_bom.py "
                     "&amp;&amp; python3 make_pins.py<br/>"
                     "python3 make_pcb.py dsn → Freerouting 1.9 → make_pcb.py ses / finish / patch<br/>"
                     "python3 make_cpl.py &amp;&amp; python3 make_workflow_pdf.py</font>"))
    s.append(PageBreak())

    # ---------------- 10 glossary / open items
    P("10. Glossary", H1)
    gl = [["Term", "Meaning"],
          ["AIS-140", "Indian standard for vehicle location tracking devices in public and commercial vehicles"],
          ["VLTD", "Vehicle Location Tracking Device: the AIS-140 name for this product"],
          ["GNSS", "all satellite navigation systems together (GPS, Galileo, BeiDou, NavIC …)"],
          ["NavIC / IRNSS", "India's own satellite navigation system, required by AIS-140"],
          ["L1 / L5", "two GNSS frequency bands; using both gives better accuracy near buildings and trees"],
          ["LTE-M / NB-IoT", "low-power versions of 4G for small devices; good indoor coverage, low data cost"],
          ["PSM", "Power Saving Mode: the modem sleeps for hours but stays registered on the network"],
          ["IMU", "Inertial Measurement Unit: accelerometer + gyroscope that senses motion and crashes"],
          ["Geofence", "a virtual boundary on the map; crossing it raises an alert"],
          ["Immobiliser", "relay that stops the starter motor so the bike cannot be started"],
          ["OTA", "Over-The-Air firmware update through the mobile network"],
          ["MQTT / HTTPS", "the internet protocols used to send data securely to the server"],
          ["BLE", "Bluetooth Low Energy: used to configure the device from a phone"],
          ["U.FL", "tiny snap-on RF connector for the antennas"],
          ["ERC / DRC", "Electrical / Design Rule Check: automatic checks of the schematic and board"],
          ["Gerber, BOM, CPL", "board-making files, Bill of Materials, and pick-and-place component positions"],
          ["IP67", "dust-tight and survives immersion to 1 m for 30 minutes"]]
    s.append(table(gl, [32 * mm, W - 32 * mm], font_size=7.8))
    P("Open items before mass production", H2)
    oi = [["Item", "Why it matters", "Plan"],
          ["Component values", "some values were set without the vendor datasheet at hand",
           "check every line in 04_docs/VERIFY_LIST.md before ordering"],
          ["Embedded SIM", "AIS-140 asks for an eSIM with multi-operator profiles", "add an MFF2 eSIM footprint in rev B"],
          ["2G fallback", "SIM7080G is LTE-M / NB-IoT only", "confirm acceptance with the test agency (ICAT / ARAI)"],
          ["Certification", "CDAC / ICAT type approval, BIS, WPC ETA, TEC", "pre-compliance tests on rev A prototypes"],
          ["Firmware", "the hardware is ready; the features above need implementing",
           "follow DESIGN_REPORT §10 and board_pins.h"]]
    s.append(table(oi, [30 * mm, 70 * mm, W - 100 * mm], head_bg=ORANGE))
    return s


def main():
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                            bottomMargin=16 * mm, title="CRL-TRK-2W-01 Workflow & Use Cases",
                            author="CRL-TRK-2W-01 project", subject="AIS-140 two-wheeler GNSS/LTE-M tracker")
    doc.build(build(), onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
