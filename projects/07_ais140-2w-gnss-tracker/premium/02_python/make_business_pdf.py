#!/usr/bin/env python3
"""Product, cost & business plan PDF for Samay Track 2W (CRL-TRK-2W-01).

Output: ../07_marketing/SamayTrack2W_Business_Plan.pdf
Reuses the drawing helpers and styles of make_workflow_pdf.py. All money figures are estimates (Oct 2026, ex-GST).
"""
import csv
import os

from reportlab.graphics.shapes import Circle, Drawing, Line, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import make_workflow_pdf as wf
from make_workflow_pdf import (BODY, BOLD, C_ALERT, C_CLOUD, C_IO, C_MCU, C_NOTE, C_PWR, C_RF, CAP, FONT, GREY, H1,
                               H2, LEAD, LIGHT, NAVY, ORANGE, TEAL, W, arrow, box, callout, chain, fit, seg, table, txt)

ROOT = wf.ROOT
OUT = os.path.join(ROOT, "07_marketing", "SamayTrack2W_Business_Plan.pdf")
BOM = os.path.join(ROOT, "03_fab", "CRL-TRK-2W-01_BOM_costed.csv")
POSTER = os.path.join(ROOT, "07_marketing", "SamayTrack2W_poster.png")
HERO = os.path.join(ROOT, "07_marketing", "board.png")
GREEN = colors.HexColor("#2E9E6B")
RED = colors.HexColor("#C0392B")
WARN = colors.HexColor("#FFF4E8")


def inr(v):
    """Indian digit grouping: 1234567 -> 12,34,567."""
    s = f"{int(round(v)):d}"
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def bom_groups():
    """Category totals (INR) from the costed BOM; fall back to the pricing-note figures if missing."""
    cats = {}
    mods = {}
    if os.path.exists(BOM):
        for r in csv.DictReader(open(BOM)):
            if r["Designators"] == "TOTAL" or not r["Category"]:
                continue
            v = float(r["Ext INR"])
            cats[r["Category"]] = cats.get(r["Category"], 0) + v
            if r["Category"] == "Modules":
                mods[r["MPN"]] = v
    if not cats:
        cats = {"Modules": 2957, "ICs & sensors": 986, "Connectors": 208, "Passives": 143, "Discretes & misc": 99}
        mods = {"NEO-F10N-00B": 1848, "SIM7080G": 836, "ESP32-S3-WROOM-1-N8R2": 273}
    return cats, mods


# ------------------------------------------------------------------ charts / diagrams
def hbars(items, maxv=None, unit="₹", bar_color=TEAL, label_w=170, h_row=19, note=None):
    maxv = maxv or max(v for _, v in items)
    d = Drawing(W, len(items) * h_row + 8)
    bw = W - label_w - 70
    for i, (lab, v) in enumerate(items):
        y = d.height - (i + 1) * h_row
        txt(d, label_w - 6, y + 5, lab, 7.6, False, colors.black, "end")
        d.add(Rect(label_w, y + 2, bw, h_row - 6, fillColor=LIGHT, strokeColor=None))
        d.add(Rect(label_w, y + 2, max(1.5, bw * v / maxv), h_row - 6, fillColor=bar_color, strokeColor=None))
        txt(d, label_w + bw * v / maxv + 5, y + 5, f"{unit}{inr(v)}", 7.6, True, NAVY, "start")
    return d


def stacked_unit_cost():
    """One stacked bar: where the ₹6,180 goes."""
    cats, mods = bom_groups()
    parts = [("GNSS NEO-F10N", mods.get("NEO-F10N-00B", 1848), colors.HexColor("#1F3A5F")),
             ("LTE SIM7080G", mods.get("SIM7080G", 836), colors.HexColor("#2A9D8F")),
             ("ESP32-S3", mods.get("ESP32-S3-WROOM-1-N8R2", 273), colors.HexColor("#4C9BE8")),
             ("Other ICs", cats.get("ICs & sensors", 986), colors.HexColor("#8E7CC3")),
             ("Small parts", cats.get("Connectors", 208) + cats.get("Passives", 143) + cats.get("Discretes & misc", 99),
              colors.HexColor("#B8C4D6")),
             ("PCB + SMT", 300, colors.HexColor("#E9C46A")),
             ("Box build", 1490, colors.HexColor("#E76F51"))]
    tot = sum(p[1] for p in parts)
    d = Drawing(W, 84)
    x = 0
    for name, v, c in parts:
        w = W * v / tot
        d.add(Rect(x, 44, w, 26, fillColor=c, strokeColor=colors.white, strokeWidth=1))
        if w > 34:
            txt(d, x + w / 2, 53, f"{100 * v / tot:.0f}%", 7.4, True, colors.white)
        x += w
    # legend
    for i, (name, v, c) in enumerate(parts):
        x, y = (i % 4) * W / 4, 24 - (i // 4) * 16
        d.add(Rect(x, y, 8, 8, fillColor=c, strokeColor=None))
        txt(d, x + 11, y + 1, f"{name} ₹{inr(v)}", 7, False, colors.black, "start")
    txt(d, 0, 75, f"Total ≈ ₹{inr(tot)} per unit at 1,000 pcs", 8, True, NAVY, "start")
    return d


def lite_block():
    d = Drawing(493, 150)
    box(d, 0, 88, 88, 52, "Vehicle 12/24 V\nIGN, SOS,\nrelay", C_PWR)
    box(d, 0, 10, 88, 52, "300 mAh cell\n2–4 h backup", C_PWR)
    box(d, 108, 50, 92, 60, "Protection +\n40 V buck,\ncharger", C_PWR)
    box(d, 222, 40, 128, 80, "4G Cat-1 + 2G\nmodule\n(A7672S / EC200U)\nruns the firmware", C_MCU, size=8.4)
    box(d, 372, 98, 121, 44, "GPS + BeiDou\nL76K (NavIC opt.)", C_RF)
    box(d, 372, 50, 121, 40, "Accelerometer\nmotion / tow", C_RF)
    box(d, 372, 4, 121, 40, "Flash + SIM\n(eSIM option)", C_MCU)
    arrow(d, 88, 114, 108, 95)
    arrow(d, 88, 36, 108, 65)
    arrow(d, 200, 80, 222, 80)
    arrow(d, 350, 105, 372, 118)
    arrow(d, 350, 80, 372, 70)
    arrow(d, 350, 55, 372, 26)
    return fit(d)


def app_architecture():
    d = Drawing(493, 205)
    box(d, 0, 110, 92, 60, "Tracker\nGPS + 4G\nMQTT / TLS", C_RF)
    box(d, 120, 70, 150, 130, "", colors.HexColor("#F3F6FA"))
    txt(d, 195, 188, "Cloud (AWS / Azure Mumbai)", 7.6, True, NAVY)
    box(d, 130, 140, 130, 36, "MQTT broker\nEMQX / Mosquitto", C_CLOUD, size=7.4)
    box(d, 130, 98, 130, 36, "API + rules engine\ngeofence, theft, crash", C_CLOUD, size=7.4)
    box(d, 130, 76, 62, 18, "Database", C_NOTE, size=6.6)
    box(d, 198, 76, 62, 18, "Push (FCM)", C_NOTE, size=6.6)
    arrow(d, 92, 150, 130, 158, label="data", ly=158)
    arrow(d, 130, 120, 92, 128, label="commands", ly=111)
    arrow(d, 195, 140, 195, 134)
    box(d, 300, 140, 92, 48, "Rider app\nFlutter: Android\n+ iPhone", C_MCU)
    box(d, 300, 82, 92, 48, "Fleet web\ndashboard", C_MCU)
    box(d, 410, 140, 83, 48, "Payments\nRazorpay", C_IO)
    box(d, 410, 82, 83, 48, "Maps\nMappls / Google", C_IO)
    box(d, 300, 20, 193, 44, "Optional: state AIS-140 backend\n(VAHAN-linked, fixed packet format)", C_ALERT)
    arrow(d, 260, 116, 300, 160)
    arrow(d, 260, 110, 300, 106)
    arrow(d, 392, 164, 410, 164)
    arrow(d, 392, 106, 410, 106)
    arrow(d, 230, 70, 300, 42)
    box(d, 0, 20, 92, 48, "Login\nphone + OTP\n(MSG91)", C_IO)
    arrow(d, 92, 44, 130, 80)
    return fit(d)


def phone(d, x, y, title, rows, accent):
    w, h = 140, 250
    d.add(Rect(x, y, w, h, rx=16, ry=16, fillColor=colors.HexColor("#0B1A33"), strokeColor=colors.HexColor("#0B1A33")))
    d.add(Rect(x + 7, y + 10, w - 14, h - 30, rx=10, ry=10, fillColor=colors.white, strokeColor=None))
    d.add(Rect(x + 52, y + h - 14, 36, 5, rx=2, ry=2, fillColor=colors.HexColor("#33415C"), strokeColor=None))
    d.add(Rect(x + 7, y + h - 46, w - 14, 26, fillColor=accent, strokeColor=None))
    txt(d, x + w / 2, y + h - 37, title, 8.2, True, colors.white)
    yy = y + h - 54
    for kind, a, b in rows:
        if kind == "map":
            d.add(Rect(x + 14, yy - 92, w - 28, 88, fillColor=colors.HexColor("#E6EEF5"), strokeColor=None))
            for k in range(5):
                d.add(Line(x + 14, yy - 16 - k * 18, x + w - 14, yy - 10 - k * 16,
                           strokeColor=colors.HexColor("#C9D6E3"), strokeWidth=2))
            d.add(Line(x + 30, yy - 80, x + 70, yy - 40, strokeColor=TEAL, strokeWidth=2.5))
            d.add(Line(x + 70, yy - 40, x + 105, yy - 55, strokeColor=TEAL, strokeWidth=2.5))
            d.add(Circle(x + 105, yy - 55, 6, fillColor=ORANGE, strokeColor=colors.white, strokeWidth=1.5))
            yy -= 100
        elif kind == "row":
            d.add(Rect(x + 14, yy - 26, w - 28, 22, rx=5, ry=5, fillColor=LIGHT, strokeColor=None))
            d.add(Circle(x + 25, yy - 15, 4, fillColor=b, strokeColor=None))
            txt(d, x + 34, yy - 18, a, 6.8, False, colors.black, "start")
            yy -= 27
        elif kind == "btn":
            d.add(Rect(x + 14, yy - 34, w - 28, 28, rx=8, ry=8, fillColor=b, strokeColor=None))
            txt(d, x + w / 2, yy - 24, a, 8, True, colors.white)
            yy -= 38
        elif kind == "kv":
            txt(d, x + 16, yy - 13, a, 6.8, False, GREY, "start")
            txt(d, x + w - 16, yy - 13, b, 6.8, True, colors.black, "end")
            d.add(Line(x + 16, yy - 18, x + w - 16, yy - 18, strokeColor=LIGHT, strokeWidth=0.8))
            yy -= 19


def app_screens():
    d = Drawing(493, 262)
    phone(d, 0, 6, "Live map", [("map", "", ""), ("kv", "Speed", "38 km/h"), ("kv", "Ignition", "ON"),
                                 ("kv", "Battery", "92 %"), ("btn", "Share live location", TEAL)], NAVY)
    phone(d, 176, 6, "Alerts", [("row", "Theft: bike moved 02:14", RED), ("row", "Geofence exit: Office", ORANGE),
                                ("row", "Power cut: on battery", ORANGE), ("row", "SOS pressed: Rider", RED),
                                ("row", "Crash detected: 11:42", RED), ("row", "Trip ended: 12.4 km", GREEN),
                                ("row", "OTA update installed", TEAL)], ORANGE)
    phone(d, 352, 6, "Bike control", [("kv", "Device", "Samay Track 2W"), ("kv", "Plan", "valid to 03/2027"),
                                      ("kv", "GPS", "NavIC + L5 fix"), ("kv", "Network", "LTE-M  ▂▄▆"),
                                      ("btn", "Lock engine (PIN)", RED), ("btn", "Geofences", NAVY),
                                      ("btn", "Renew ₹1,999", GREEN)], TEAL)
    return fit(d)


def gantt():
    tasks = [("Firmware v1 (tracker)", 0, 3, C_MCU), ("Prototype 2 × 10 boards", 0, 3, C_PWR),
             ("App + server v1", 1, 4, C_CLOUD), ("Enclosure design + mould", 2, 5, C_IO),
             ("Validation: EMC, heat, vibration", 3, 5, C_ALERT), ("WPC / BIS / EPR / TEC", 4, 7, C_ALERT),
             ("Pilot 100 units with B2B customers", 6, 8, C_RF), ("Production batch 500–1,000", 8, 10, C_PWR),
             ("Dealers + Amazon launch", 9, 12, C_RF), ("AIS-140 approval (optional)", 9, 15, colors.HexColor("#EADCF5")),
             ("Lite version design", 6, 10, C_MCU)]
    months = 15
    lw = 150
    rh = 17
    d = Drawing(W, len(tasks) * rh + 26)
    cw = (W - lw) / months
    top = d.height - 16
    for m in range(months):
        x = lw + m * cw
        d.add(Rect(x, 0, cw, top, fillColor=LIGHT if m % 2 else colors.white, strokeColor=None))
        txt(d, x + cw / 2, top + 4, f"M{m + 1}", 6.6, True, NAVY)
    for i, (name, a, b, c) in enumerate(tasks):
        y = top - (i + 1) * rh
        txt(d, lw - 6, y + 5, name, 7.2, False, colors.black, "end")
        d.add(Rect(lw + a * cw + 1, y + 2, (b - a) * cw - 2, rh - 5, rx=3, ry=3, fillColor=c, strokeColor=NAVY,
                   strokeWidth=0.5))
    return d


# ------------------------------------------------------------------ document
def on_page(c, doc):
    c.saveState()
    if doc.page == 1:
        c.setFillColor(colors.HexColor("#0B1A33"))
        c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#22D3EE"))
        c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, fill=1, stroke=0)
        c.restoreState()
        return
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.8)
    c.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
    c.setFont(FONT, 7.5)
    c.setFillColor(GREY)
    c.drawString(18 * mm, A4[1] - 11 * mm, "Samay Electronics · Samay Track 2W (CRL-TRK-2W-01)")
    c.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "Product, cost & business plan · Oct 2026 · estimates")
    c.drawString(18 * mm, 10 * mm, "Confidential, internal planning document")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"page {doc.page}")
    c.restoreState()


def img(path, width):
    if not os.path.exists(path):
        return Spacer(1, 1)
    from PIL import Image as PImage
    w, h = PImage.open(path).size
    return Image(path, width=width, height=width * h / w)


def warn(html):
    return callout(html, bg=WARN, edge=ORANGE)


def build():
    s = []
    P = lambda t, st=BODY: s.append(Paragraph(t, st))  # noqa: E731
    cats, mods = bom_groups()
    board = sum(cats.values())
    hw = board + 300 + 1490

    # ---------------- cover (dark page)
    white = ParagraphStyle("cw", parent=H1, textColor=colors.white, fontSize=34, leading=40)
    s.append(Spacer(1, 22 * mm))
    s.append(Paragraph("SAMAY ELECTRONICS", ParagraphStyle("k", parent=BODY, textColor=colors.HexColor("#22D3EE"),
                                                           fontName=BOLD, fontSize=11, leading=14)))
    s.append(Paragraph("Samay Track 2W", white))
    s.append(Paragraph("Product, design, cost and business plan", ParagraphStyle(
        "cs", parent=LEAD, textColor=colors.HexColor("#93A4C3"), fontSize=15, leading=20)))
    s.append(Spacer(1, 8 * mm))
    s.append(img(HERO, W))
    s.append(Spacer(1, 8 * mm))
    facts = Table([[Paragraph(f"<b>₹{inr(hw)}</b><br/>hardware cost / unit", ParagraphStyle("f", parent=BODY,
                                                                                           textColor=colors.white,
                                                                                           fontSize=10, leading=14)),
                    Paragraph("<b>₹26–50 lakh</b><br/>to reach the first 100 sales", ParagraphStyle(
                        "f2", parent=BODY, textColor=colors.white, fontSize=10, leading=14)),
                    Paragraph("<b>≈ 10–12 months</b><br/>to a production launch", ParagraphStyle(
                        "f3", parent=BODY, textColor=colors.white, fontSize=10, leading=14)),
                    Paragraph("<b>Rev A0</b><br/>PCB designed, not built yet", ParagraphStyle(
                        "f4", parent=BODY, textColor=colors.white, fontSize=10, leading=14))]],
                  colWidths=[W / 4] * 4)
    facts.setStyle(TableStyle([("LINEBEFORE", (1, 0), (-1, 0), 0.5, colors.HexColor("#33415C")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    s.append(facts)
    s.append(Spacer(1, 10 * mm))
    s.append(Paragraph("All prices are planning estimates (October 2026, INR, excluding GST). Confirm them with "
                       "supplier quotes, test labs and a compliance consultant before you commit money.",
                       ParagraphStyle("cf", parent=BODY, textColor=colors.HexColor("#6C7C99"), fontSize=8.5)))
    s.append(PageBreak())

    # ---------------- contents + summary
    P("Contents", H1)
    toc = [["#", "Section"],
           ["1", "Executive summary"], ["2", "The product and how it works"], ["3", "Hardware design"],
           ["4", "BOM cost: line by line"], ["5", "Unit economics and profit margins"],
           ["6", "Lite version: design and cost"], ["7", "Competitors and our difference"],
           ["8", "App and cloud: design and cost"], ["9", "Certifications and legal"],
           ["10", "AIS-140: what, who, cost"], ["11", "How to sell (and Amazon)"],
           ["12", "Total money needed (investment plan)"], ["13", "Timeline: idea to market"],
           ["14", "What you were missing, and risks"], ["15", "Next 10 steps"]]
    s.append(table(toc, [12 * mm, W - 12 * mm]))
    s.append(Spacer(1, 6 * mm))
    P("1. Executive summary", H1)
    summ = [["Topic", "Answer in one line"],
            ["Product", "Premium 4G LTE-M GPS + NavIC tracker for motorcycles and scooters, with a 40 h backup "
                        "battery, crash/theft/SOS alerts and an engine lock"],
            ["Status", "PCB fully designed (DRC/ERC clean, Gerbers, BOM). <b>No prototype yet, no firmware, "
                       "no app.</b>"],
            ["Unit cost", f"≈ ₹{inr(hw)} hardware at 1,000 pcs (≈ ₹6,600 landed). Lite version ≈ ₹1,200–1,500"],
            ["Price", "Rider ₹10,999 · Fleet ₹7,999 · Renewal ₹1,999/yr (suggested; the draft poster still shows ₹9,499 / ₹7,499). "
                       "Lite ₹2,999–3,499"],
            ["Margin", "≈ 31 % direct, 13 % via dealers, 18 % fleet. Renewals ≈ 70 %: <b>the profit is in "
                       "subscriptions</b>"],
            ["Best market", "B2B first: two-wheeler loan companies, rentals, delivery fleets, small EV makers. "
                            "Then dealers and Amazon (Lite)"],
            ["Money needed", "≈ ₹26–50 lakh to the first 100 paid units. Add inventory for volume, and "
                             "₹15–25 lakh + guarantees if you do AIS-140"],
            ["Time", "≈ 6–8 months to the pilot, 10–12 months to a production launch"],
            ["Biggest gaps", "Firmware, a working prototype, enclosure, app/server, certificates, SIM contract, funding"]]
    s.append(table(summ, [28 * mm, W - 28 * mm]))
    s.append(PageBreak())

    # ---------------- 2 product
    P("2. The product and how it works", H1)
    P("The tracker sits under the seat. It reads satellites (GPS, Galileo, BeiDou and India's NavIC) and senses "
      "motion. It sends position and alerts over the mobile network to your cloud server, which shows them in the app. "
      "<b>There is no distance limit</b>: it works anywhere with LTE-M / NB-IoT coverage, and stores data offline "
      "where there is no coverage.", LEAD)
    s.append(fit(wf.big_picture()))
    P("Figure 1: the system, from the bike to the people who need the information.", CAP)
    P("Key specifications", H2)
    spec = [["Item", "Value"],
            ["Positioning", "u-blox NEO-F10N, dual-band L1 + L5, GPS / Galileo / BeiDou / QZSS / <b>NavIC</b>; "
                            "≈ 2 m in open sky"],
            ["Network", "SIMCom SIM7080G LTE Cat-M1 / NB-IoT, nano-SIM (eSIM in rev B), no 2G"],
            ["Brain", "ESP32-S3: BLE setup, TLS, OTA updates, rules"],
            ["Sensors", "IIM-42652 6-axis IMU (wake-on-motion, crash), RTC with tamper input, battery gauge"],
            ["Memory", "16 MB flash ≈ 4 lakh positions offline"],
            ["Power", "9–36 V vehicle input, reverse and load-dump protected; 18650 backup ≈ 40 h tracking; "
                      "sleep ≈ 0.11 mA"],
            ["I/O", "Ignition, SOS, DIN1, AIN1 (0–30 V), DOUT1 relay (engine lock), USB-C service"],
            ["Size", "PCB 60 × 45 mm, 4-layer; IP67 enclosure target"],
            ["Report rate", "every 10 s while driving (configurable); heartbeat while parked"]]
    s.append(table(spec, [30 * mm, W - 30 * mm]))
    s.append(PageBreak())

    # ---------------- 3 design
    P("3. Hardware design", H1)
    P("Designed in KiCad 9 from Python source files, so every output can be rebuilt. The schematic has 6 sheets and the "
      "PCB has 180 parts on 4 layers, with parts on both sides. Checks: <b>DRC 0 errors, ERC clean, "
      "schematic and PCB in sync</b>. The outputs are ready for JLCPCB / PCBWay: Gerbers, BOM, pick-and-place, "
      "3D STEP, assembly drawings.", LEAD)
    s.append(fit(wf.block_diagram()))
    P("Figure 2: functional block diagram.", CAP)
    s.append(Table([[img(wf.RENDER.format("top"), W / 2 - 6), img(wf.RENDER.format("bottom"), W / 2 - 6)],
                    [Paragraph("Top side: modules, power, connectors", CAP),
                     Paragraph("Bottom side: small parts, SIM, USB-C, test pads", CAP)]], colWidths=[W / 2, W / 2]))
    P("Design files in the repository", H2)
    files = [["Need", "File"],
             ["Schematic (PDF)", "04_docs/CRL-TRK-2W-01_schematic.pdf"],
             ["KiCad project (Altium imports it)", "01_kicad/tracker.kicad_pro"],
             ["Manufacturing", "03_fab/ Gerbers zip, BOM_JLCPCB.csv, CPL_JLCPCB.csv"],
             ["Engineering report", "04_docs/DESIGN_REPORT.md (power, EMC, SI, DFM, test)"],
             ["Values to check before ordering", "04_docs/VERIFY_LIST.md"]]
    s.append(table(files, [55 * mm, W - 55 * mm]))
    s.append(PageBreak())

    # ---------------- 4 BOM cost
    P("4. BOM cost, line by line", H1)
    P("Estimated at 1,000 pieces with typical distributor prices (₹88 per USD). Every line is in "
      "<b>03_fab/CRL-TRK-2W-01_BOM_costed.csv</b>. Three modules make up two-thirds of the board cost.", LEAD)
    s.append(stacked_unit_cost())
    s.append(Spacer(1, 4))
    items = [("NEO-F10N GNSS", mods.get("NEO-F10N-00B", 1848)), ("SIM7080G LTE-M", mods.get("SIM7080G", 836)),
             ("GNSS antenna (active L1/L5)", 550), ("ICs & sensors", cats.get("ICs & sensors", 986)),
             ("ESP32-S3 module", mods.get("ESP32-S3-WROOM-1-N8R2", 273)), ("Harness, fuse, SOS, relay", 300),
             ("PCB + SMT assembly", 300), ("IP67 enclosure", 250), ("18650 pack + PCM + NTC", 220),
             ("Connectors", cats.get("Connectors", 208)), ("Passives", cats.get("Passives", 143)),
             ("LTE antenna", 120), ("Discretes & misc", cats.get("Discretes & misc", 99)), ("Packaging", 50)]
    s.append(hbars(items))
    P("Figure 3: cost per unit by item (₹, 1,000 pcs).", CAP)
    qty = [["Quantity", "Hardware / unit", "Why"],
           ["10 (prototype)", "≈ ₹9,000–12,000", "small-quantity prices, setup fees, courier"],
           ["100 (pilot)", "≈ ₹7,500", "partial price breaks"],
           ["1,000", f"≈ ₹{inr(hw)} (≈ ₹6,600 landed)", "the basis of this plan"],
           ["10,000", "≈ ₹5,300–5,600", "module prices fall 15–20 % at this volume"]]
    s.append(table(qty, [35 * mm, 45 * mm, W - 80 * mm]))
    s.append(Spacer(1, 3))
    s.append(warn("<b>Cost-down options:</b> ICM-42670 IMU instead of IIM-42652 (≈ ₹200 saved) · generic U.FL "
                  "connectors · combine buck + LDO · negotiate modules at volume · MAX-F10S or a cheaper NavIC "
                  "GNSS once it is qualified."))
    s.append(PageBreak())

    # ---------------- 5 unit economics
    P("5. Unit economics and profit margins", H1)
    P("Costs per unit, beyond the hardware: year-1 data and cloud ₹600 and installation ₹300 (Rider only; fleets pay "
      "data through the platform fee), "
      "warranty reserve 3 % of price, packaging and shipping ₹150. Dealer margin is 18 % of price. "
      "Fixed costs such as staff and certification are covered in section 12.", LEAD)

    def econ(price, inst=300, dealer=False, fleet=False):
        # fleets pay data/cloud through the separate platform fee, and install themselves
        cost = hw + (0 if fleet else 600 + inst) + 0.03 * price + 150 + (0.18 * price if dealer else 0)
        return cost, price - cost, 100 * (price - cost) / price

    rows = [["Plan", "Price", "Total cost", "Profit / unit", "Margin"]]
    for name, price, kw in [("Rider: direct (poster)", 9499, {}), ("Rider: dealer (poster)", 9499, {"dealer": True}),
                            ("Fleet (poster)", 7499, {"fleet": True}), ("Rider: direct (suggested)", 10999, {}),
                            ("Rider: dealer (suggested)", 10999, {"dealer": True}),
                            ("Fleet (suggested)", 7999, {"fleet": True})]:
        c_, p_, m_ = econ(price, **kw)
        rows.append([name, f"₹{inr(price)}", f"₹{inr(c_)}", f"₹{inr(p_)}", f"{m_:.0f} %"])
    rows += [["Renewal / year", "₹1,999", "₹600", "₹1,399", "70 %"],
             ["Fleet platform fee / year", "₹1,499", "₹600", "₹899", "60 %"]]
    s.append(table(rows, [52 * mm, 25 * mm, 30 * mm, 30 * mm, W - 137 * mm]))
    s.append(Spacer(1, 4))
    _, p_direct, _ = econ(10999)
    life = [("Year 1: device sale (direct)", p_direct), ("Year 2: renewal", 1399), ("Year 3: renewal", 1399)]
    s.append(hbars(life, bar_color=GREEN, label_w=150))
    P(f"Figure 4: profit from one direct Rider customer over 3 years ≈ ₹{inr(p_direct + 2 * 1399)}.", CAP)
    s.append(callout("<b>Conclusion:</b> at the poster prices (₹9,499 / ₹7,499) hardware margins are too thin, "
                     "especially through dealers (≈ 3 %). Use the <b>suggested prices</b> (₹10,999 / ₹7,999) and "
                     "push yearly renewals. Every renewing customer adds ≈ ₹1,400 a year at about 70 % margin."))
    s.append(PageBreak())

    # ---------------- 6 lite
    P("6. Lite version: design and cost", H1)
    P("A cheaper model for consumers and Amazon. It is a <b>new 2-layer board</b>: one 4G Cat-1 module with "
      "2G fallback runs the firmware itself, so the ESP32 is dropped, and the GNSS is a cheaper single-band "
      "part.", LEAD)
    s.append(lite_block())
    P("Figure 5: Lite block diagram.", CAP)
    lite = [["Part", "Choice", "₹ / unit"],
            ["4G modem", "Cat-1 + 2G (SIMCom A7672S / Quectel EC200U), also runs the app firmware", "500–650"],
            ["GNSS", "L76K-class GPS + BeiDou (NavIC-capable part +₹300–400)", "200–250"],
            ["Sensors and power", "accelerometer, 40 V buck, charger, 300 mAh cell", "140–190"],
            ["Antennas", "on-board GNSS patch + FPC LTE", "60–80"],
            ["Other", "flash, SIM, ESD, passives", "80–100"],
            ["PCB + SMT", "2-layer, single-sided", "80–100"],
            ["Box build", "IP65 enclosure, 4-wire harness, packaging", "130–170"],
            ["<b>Total</b>", "", "<b>≈ 1,200–1,500</b>"]]
    s.append(table(lite, [32 * mm, W - 62 * mm, 30 * mm]))
    s.append(Spacer(1, 4))
    cmp_ = [["", "Full (Samay Track 2W)", "Lite"],
            ["Hardware cost", f"≈ ₹{inr(hw)}", "≈ ₹1,200–1,500"],
            ["Retail price", "₹10,999 (suggested)", "₹2,999–3,499 incl. year 1"],
            ["Margin (direct)", "≈ 31 %", "≈ 35–40 %"],
            ["NavIC / dual band", "yes / yes", "optional / no"],
            ["Backup battery", "≈ 40 h", "2–4 h"],
            ["Crash detection, big black box", "yes", "basic / no"],
            ["2G fallback", "no", "yes"],
            ["AIS-140 possible", "yes (rev B with eSIM)", "no"],
            ["Where to sell", "fleets, NBFCs, premium riders", "Amazon, Flipkart, dealers"]]
    s.append(table(cmp_, [45 * mm, (W - 45 * mm) / 2, (W - 45 * mm) / 2]))
    s.append(PageBreak())

    # ---------------- 7 competitors
    P("7. Competitors and our difference", H1)
    comp = [["Segment", "Examples", "Price (web listings, Oct 2026)"],
            ["Budget 4G bike trackers", "SeTrack, Ajjas 4G Lite, Onelap Micro / LocoShield, Fleettrack 4G",
             "₹900–2,900 incl. year 1, then ≈ ₹999/yr"],
            ["Mid-range", "Alike GPS VT05R", "from ₹3,999"],
            ["AIS-140 VLTD", "Atlanta WP 30L, Gtropy, Algotrack and others",
             "₹4,500–13,000, mostly ₹5–8k + install + ₹1–2.5k/yr"],
            ["Premium imported", "Monimoto 9", "≈ ₹47,000"],
            ["Built-in on EVs", "Ather, Ola, TVS iQube, Bajaj Chetak", "bundled with the scooter"]]
    s.append(table(comp, [38 * mm, 70 * mm, W - 108 * mm]))
    P("Where Samay Track 2W is different", H2)
    diff = [["Samay Track 2W", "Typical competitor"],
            ["Dual-band L1 + L5 GNSS <b>+ NavIC</b>", "single-band GPS, often no NavIC"],
            ["<b>≈ 40 h</b> backup battery (18650)", "minutes to a few hours, or none"],
            ["Crash and fall detection (industrial IMU)", "vibration alert only"],
            ["16 MB black box ≈ 4 lakh points", "small buffer, gaps in the route"],
            ["Reverse wiring / 36 V spike proof, 9–36 V", "basic fuse"],
            ["Sleep ≈ 0.11 mA, protects the bike battery", "often 2–10 mA"],
            ["AIS-140 features in a 60 × 45 mm box", "large boxes built for buses and trucks"]]
    s.append(table(diff, [W / 2, W / 2], head_bg=TEAL))
    s.append(Spacer(1, 4))
    s.append(warn("<b>Not different:</b> 4G, live map, app, engine lock, SOS, geofence. Everyone has these. "
                  "<b>Weaker:</b> price, no 2G, not certified yet, LTE-M rural coverage. "
                  "Verify competitors' spec sheets before you print comparison claims."))
    P("Sources: amazon.in listings; kingswayaccessories.com; alikegps.com; sahajgps.com; blog.fleetx.ai; "
      "indiamart.com and tradeindia.com AIS-140 listings.", CAP)
    s.append(PageBreak())

    # ---------------- 8 app
    P("8. App and cloud: design and cost", H1)
    P("<b>One Flutter code base</b> builds both the Android and the iPhone app. The tracker never talks to the phone "
      "directly; everything goes through your server. A faster route is to start from the open-source "
      "<b>Traccar</b> server and add your own app on top.", LEAD)
    s.append(app_architecture())
    P("Figure 6: app and cloud architecture.", CAP)
    s.append(app_screens())
    P("Figure 7: app concept: live map, alerts, bike control (wireframe, not a final UI).", CAP)
    appc = [["Item", "Cost", "Notes"],
            ["Version 1: Traccar + custom Flutter app", "₹2–4 lakh, 1–2 months", "fastest route to a working demo"],
            ["Fully custom app + server", "₹5–10 lakh, 3–5 months", "own protocol, own dashboard"],
            ["Cloud server", "₹3,000–10,000 / month", "first few thousand devices"],
            ["Store accounts", "Google $25 once · Apple $99 / yr", "iPhone build needs a Mac + Xcode"],
            ["Maps, OTP SMS, push", "≈ ₹1–5 / user / yr", "Mappls / Google, MSG91, Firebase (free)"],
            ["Payments", "Razorpay 2 %", "for renewals"]]
    s.append(table(appc, [58 * mm, 50 * mm, W - 108 * mm], font_size=7.8))
    s.append(PageBreak())

    # ---------------- 9 certs
    P("9. Certifications and legal (before you sell anything)", H1)
    P("These apply to <b>every</b> version, even without AIS-140. Confirm the exact list with a compliance "
      "consultant; the costs are rough estimates.", LEAD)
    cert = [["What", "Why", "Rough cost", "Time"],
            ["WPC ETA", "radio device (LTE, BLE): mandatory", "₹0.5–1.5 lakh", "1–2 months"],
            ["BIS (IS 16046) for the Li-ion cell / pack", "compulsory registration", "₹1–2 lakh (or buy a certified pack)",
             "2–3 months"],
            ["TEC / MTCTE", "may apply to 4G tracking devices: check", "₹1–4 lakh", "2–4 months"],
            ["CPCB EPR: e-waste + battery", "producer responsibility", "₹0.3–1 lakh + yearly targets", "1–2 months"],
            ["DoT M2M service provider registration", "if you sell the SIM / data with the device", "≈ ₹0.1–0.5 lakh",
             "1–2 months"],
            ["Pre-compliance EMC, temperature, vibration, ISO 7637", "avoid failing the formal tests",
             "₹1–3 lakh", "2–4 weeks"],
            ["Legal Metrology labelling", "MRP, maker, support on the box", "small", "—"],
            ["DPDP Act: privacy policy, consent, data in India", "you store location data", "₹0.3–1 lakh (lawyer)",
             "2–4 weeks"],
            ["Trademark \"Samay\" + company + GST", "brand protection, Amazon Brand Registry",
             "₹0.2–0.5 lakh", "filing: days; grant: months"],
            ["Product liability insurance", "engine lock / crash features carry risk", "₹0.3–1 lakh / yr", "—"]]
    s.append(table(cert, [52 * mm, 50 * mm, 40 * mm, W - 142 * mm], font_size=7.6))
    s.append(Spacer(1, 4))
    s.append(callout("<b>Total for basic certificates and legal ≈ ₹5–12 lakh</b>, taking 3–6 months, with "
                     "several running in parallel. AIS-140 is extra (next section)."))
    s.append(PageBreak())

    # ---------------- 10 AIS-140
    P("10. AIS-140: what, who, cost", H1)
    P("AIS-140 is India's standard for <b>vehicle location tracking devices (VLTD) in public and commercial "
      "vehicles</b>. It is issued under MoRTH by ARAI.", LEAD)
    ais = [["Topic", "Details"],
           ["Must have", "GPS + NavIC · panic button linked to the state control room / 112 · live data to the state "
                         "backend · tamper and power-cut alerts · backup battery · store-and-forward + SMS · embedded "
                         "multi-operator SIM · OTA"],
           ["Who must fit it", "buses, taxis, cabs, school vans, trucks with permits"],
           ["Two-wheelers", "<b>exempt</b> in the 2018 MoRTH notification, as are 3-wheelers and e-rickshaws. Bike-taxi "
                            "rules vary by state, so check"],
           ["Approval", "type approval by ARAI / ICAT, then a listing in each state"]]
    s.append(table(ais, [30 * mm, W - 30 * mm]))
    P("Cost to get AIS-140", H2)
    aisc = [["Item", "Cost", "Basis"],
            ["Type-approval testing (ARAI / ICAT), 3–6 months", "≈ ₹5–15 lakh", "estimate"],
            ["Yearly Conformity of Production audit", "≈ ₹2–5 lakh / yr", "estimate"],
            ["State registration", "₹10,000 + ₹10,000 per model", "Sikkim / West Bengal documents"],
            ["Performance bank guarantee", "up to ₹25 lakh per state (refundable)", "Sikkim SOP"],
            ["Integration with each state backend", "≈ ₹1–3 lakh per state", "estimate"],
            ["Board rev B: eSIM, 2G question", "≈ ₹2–5 lakh", "estimate"],
            ["<b>Total</b>", "<b>≈ ₹15–25 lakh + ₹10–25 lakh+ locked in guarantees</b>", "for 1–2 states"]]
    s.append(table(aisc, [70 * mm, 60 * mm, W - 130 * mm]))
    s.append(Spacer(1, 4))
    s.append(warn("<b>Advice:</b> skip AIS-140 for the launch. Do it only once a fleet or commercial customer is "
                  "ready to buy. Two-wheeler consumer sales do not need it."))
    s.append(PageBreak())

    # ---------------- 11 selling
    P("11. How to sell (and Amazon)", H1)
    s.append(fit(chain(["Get ready\nprototype, app,\ncertificates",
                        "B2B pilots\n10–50 units with\nNBFC / rental / fleet",
                        "Testimonials\nfix issues,\ncase studies",
                        "Retail\ndealers, website,\nAmazon (Lite)",
                        "Grow\nrenewals, new\ncities, AIS-140"],
                       [C_IO, C_RF, C_MCU, C_CLOUD, C_PWR], h=58, size=7.6)))
    sell = [["Buyer", "Why they buy", "Offer"],
            ["Two-wheeler loan companies (NBFCs, banks)", "track and recover bikes on unpaid loans",
             "per-unit price + yearly plan, bulk"],
            ["Bike rental firms", "theft protection, renter tracking", "free 10-unit pilot, then bulk"],
            ["Delivery / bike-taxi fleets", "rider safety, SOS, route proof", "fleet dashboard"],
            ["Small EV makers", "need tracking, no in-house team", "white-label ₹1,500–3,000 (Lite) in bulk"],
            ["Insurers", "fewer theft claims", "premium discount partnership"],
            ["Showrooms / accessory shops", "extra margin, installs", "15–20 % margin, demo unit, poster"],
            ["Website + WhatsApp", "best margin", "cash on delivery + installation in your city"],
            ["Amazon / Flipkart", "reach, trust", "Lite with a self-install video"]]
    s.append(table(sell, [52 * mm, 55 * mm, W - 107 * mm]))
    P("Amazon checklist", H2)
    amz = [["Need", "Detail"],
           ["Seller account", "GSTIN, PAN, bank account; FBA or Easy Ship"],
           ["Brand Registry", "trademark filed for \"Samay\""],
           ["Documents Amazon may ask for", "WPC ETA, BIS for the battery, invoices, EPR"],
           ["Fees", "≈ 12–20 % of price (commission, closing, shipping) + 5–10 % ads at launch"],
           ["Result at ₹2,999 (Lite)", "≈ ₹500–1,000 profit per unit before ads"]]
    s.append(table(amz, [52 * mm, W - 52 * mm]))
    s.append(PageBreak())

    # ---------------- 12 investment
    P("12. Total money needed (investment plan)", H1)
    P("<b>Not covered in the earlier notes:</b> how much cash the whole project needs before it earns. Phase 1 "
      "takes the product to the first 100 paying units. Phase 2 is volume production.", LEAD)
    inv = [("Prototypes: 2 rounds × 10 boards", 1.5, 2.5), ("Firmware + app + server (dev, testing)", 3, 8),
           ("Enclosure design + injection mould", 3, 6), ("Production test fixture (pogo bed)", 0.5, 1.5),
           ("Pre-compliance testing", 1, 3), ("Certificates + legal (section 9)", 3, 8),
           ("Company, trademark, insurance", 0.5, 1), ("Pilot batch: 100 units × ≈ ₹7,500", 7.5, 7.5),
           ("Launch marketing (demos, video, ads)", 2, 5), ("6 months running costs: cloud, SIM, support", 4, 8)]
    lo = sum(a for _, a, _ in inv)
    hi = sum(b for _, _, b in inv)
    rows = [["Phase 1 item", "Low (₹ lakh)", "High (₹ lakh)"]]
    rows += [[n, f"{a:g}", f"{b:g}"] for n, a, b in inv]
    rows.append(["<b>Phase 1 total</b>", f"<b>{lo:g}</b>", f"<b>{hi:g}</b>"])
    s.append(table(rows, [W - 60 * mm, 30 * mm, 30 * mm]))
    s.append(Spacer(1, 4))
    ph2 = [["Phase 2 (choose)", "Cash needed", "Comment"],
           ["500 full units inventory", "≈ ₹31–33 lakh", "modules need 8–12 weeks lead time and are paid upfront"],
           ["1,000 full units inventory", "≈ ₹62–66 lakh", "price-break volume"],
           ["1,000 Lite units", "≈ ₹12–15 lakh", "after the Lite design (≈ ₹3–5 lakh extra development)"],
           ["AIS-140 (optional)", "≈ ₹15–25 lakh + guarantees", "only with a committed fleet customer"]]
    s.append(table(ph2, [48 * mm, 42 * mm, W - 90 * mm]))
    s.append(Spacer(1, 4))
    _, p_dealer, _ = econ(10999, dealer=True)
    blend = 0.4 * p_direct + 0.6 * p_dealer
    be = 40e5 / blend
    s.append(callout(f"<b>Break-even:</b> with a mix of 40 % direct and 60 % dealer sales at ₹10,999, the device "
                     f"profit averages ≈ ₹{inr(blend)} per unit. Recovering ₹40 lakh of fixed costs needs "
                     f"<b>≈ {inr(round(be, -1))} units</b>, or fewer once renewals (≈ ₹1,400 per customer per "
                     "year) start to add up."))
    s.append(PageBreak())

    # ---------------- 13 timeline
    P("13. Timeline: idea to market", H1)
    P("Firmware and the prototype run in parallel. The certificates start once the enclosure and the hardware are "
      "frozen. The <b>critical path</b> is firmware → validation → certificates → pilot.", LEAD)
    s.append(gantt())
    P("Figure 8: 15-month plan (M1 = month 1).", CAP)
    ms = [["Milestone", "Month", "Done when"],
          ["First boards power up", "M2", "all rails OK, modules answer (production checklist §8)"],
          ["End-to-end demo", "M4", "position on the phone, theft alert, engine lock"],
          ["Design freeze", "M5", "validation passed, enclosure and BOM fixed"],
          ["Certificates in hand", "M7", "WPC, BIS, EPR (TEC if required)"],
          ["Pilot customers live", "M8", "100 units in the field, feedback collected"],
          ["Production launch", "M10–M12", "batch built, dealers and Amazon listings live"]]
    s.append(table(ms, [48 * mm, 22 * mm, W - 70 * mm]))
    s.append(PageBreak())

    # ---------------- 14 missing + risks
    P("14. What you were missing, and risks", H1)
    P("These items are needed for a real product. They had not been discussed yet, or are not done yet.", LEAD)
    miss = [["#", "Missing item", "Why it matters", "Action"],
            ["1", "<b>Tracker firmware</b>", "the board does nothing without it", "write firmware v1 (Claude can do this)"],
            ["2", "<b>Built and tested prototype</b>", "the design is not proven; some values are unverified "
                                                       "(VERIFY_LIST)", "order 10 boards, run the test checklist"],
            ["3", "<b>Enclosure design + mould</b>", "IP67, mounting, antenna placement", "3D design, then a mould ₹3–6 lakh"],
            ["4", "<b>App + server</b>", "customers see only the app", "Traccar + Flutter v1"],
            ["5", "<b>IoT SIM contract</b>", "data cost per device, eSIM, roaming between operators",
             "talk to Jio / Airtel IoT teams"],
            ["6", "<b>Warranty, returns, service</b>", "trust, dealer support", "1-year replace policy, RMA process"],
            ["7", "<b>Installer network</b>", "wiring needs skill", "train 2–3 installers per city, install video"],
            ["8", "<b>Customer support</b>", "alerts at night, app issues", "WhatsApp support, FAQ, help line"],
            ["9", "<b>Funding / cash flow</b>", "inventory is paid 2–3 months before sales", "plan ₹26–50 lakh + inventory"],
            ["10", "<b>Team</b>", "firmware, app, sales, installs", "1 developer + 1 sales + installers (freelance OK)"],
            ["11", "<b>Second source for key parts</b>", "NEO-F10N / SIM7080G shortages", "qualify alternatives, buffer stock"],
            ["12", "<b>Engine-lock safety and legal terms</b>", "liability if misused", "safe-stop logic, T&amp;C, insurance"],
            ["13", "<b>Police / data requests policy</b>", "location data is sensitive", "DPDP-compliant data policy"],
            ["14", "<b>Trademark search for \"Samay\"</b>", "name may already be taken in this class", "search before you print"],
            ["15", "<b>Price validation</b>", "₹10,999 is untested", "ask pilot customers, A/B offers"]]
    s.append(table(miss, [8 * mm, 46 * mm, 62 * mm, W - 116 * mm], head_bg=ORANGE, font_size=7.6))
    P("Top risks", H2)
    risk = [["Risk", "Impact", "Mitigation"],
            ["Price competition from ₹1,500 trackers", "high", "sell value to B2B; Lite version for consumers"],
            ["LTE-M / NB-IoT coverage gaps, no 2G", "medium", "offline log; Lite has Cat-1 + 2G; test routes first"],
            ["Certification delays", "medium", "pre-compliance tests, consultant, start early"],
            ["Component lead time / price", "medium", "buffer stock, second sources"],
            ["First-batch field failures", "high", "pilot with 100 units before volume, OTA fixes"],
            ["Cash running out before sales", "high", "B2B pilots with advance payment, phase the spending"]]
    s.append(table(risk, [62 * mm, 20 * mm, W - 82 * mm]))
    s.append(PageBreak())

    # ---------------- 15 next steps
    P("15. Next 10 steps", H1)
    steps = [["#", "Step", "Who", "Cost"],
             ["1", "Check VERIFY_LIST values, order 10 prototype boards (JLCPCB)", "you + Claude", "≈ ₹1–1.2 lakh"],
             ["2", "Write tracker firmware v1 + a GPS simulator", "Claude", "—"],
             ["3", "Build the server (Traccar) + Flutter Android app v1", "Claude + you (accounts)", "accounts ≈ ₹10k"],
             ["4", "Bring up and test the boards with the production checklist", "you / technician", "lab time"],
             ["5", "Enclosure: 3D-print a prototype, then quote a mould", "mechanical designer", "₹0.5 lakh → ₹3–6 lakh"],
             ["6", "Register company / GST, file the trademark, get an IoT SIM deal", "you", "≈ ₹0.5 lakh"],
             ["7", "Pre-compliance tests, then WPC / BIS / EPR applications", "consultant", "≈ ₹5–12 lakh"],
             ["8", "Sign 2–3 B2B pilot customers (NBFC, rental, fleet)", "you (sales)", "demo units"],
             ["9", "Pilot 100 units, collect feedback, fix through OTA", "team", "≈ ₹7.5 lakh"],
             ["10", "Decide: production batch size, Lite version, AIS-140", "you", "see section 12"]]
    s.append(table(steps, [8 * mm, 98 * mm, 34 * mm, W - 140 * mm]))
    s.append(Spacer(1, 6 * mm))
    s.append(KeepTogether([Paragraph("Launch poster (draft)", H2), img(POSTER, W * 0.42)]))
    s.append(Spacer(1, 4))
    P("Related files: 07_marketing/BUSINESS_PLAN_NOTES.md, PRICING_NOTES.md, poster; 04_docs/DESIGN_REPORT.md, "
      "CRL-TRK-2W-01_Workflow_UseCases.pdf; 03_fab/CRL-TRK-2W-01_BOM_costed.csv.", CAP)
    return s


def main():
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                            bottomMargin=16 * mm, title="Samay Track 2W: product, cost & business plan",
                            author="Samay Electronics", subject="CRL-TRK-2W-01 business plan")
    doc.build(build(), onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
