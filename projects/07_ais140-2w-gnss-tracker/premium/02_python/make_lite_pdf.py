#!/usr/bin/env python3
"""Short Lite-version plan PDF (design, cost, price, money, timeline). All figures are estimates.

Output: ../07_marketing/SamayTrack_Lite_Plan.pdf
"""
import os

from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

import make_business_pdf as bp
from make_workflow_pdf import BODY, FONT, GREY, TEAL, C_ALERT, C_CLOUD, C_IO, C_MCU, C_PWR, C_RF, CAP, H1, H2, LEAD, NAVY, LIGHT, W, \
    callout, table, txt

OUT = os.path.join(bp.ROOT, "07_marketing", "SamayTrack_Lite_Plan.pdf")
HW = 1350          # mid estimate, hardware per unit at 1,000 pcs
DATA = 400         # year-1 data + cloud
SHIP = 100         # packaging + shipping


def econ(price, fee=0.0):
    cost = HW + DATA + SHIP + 0.03 * price + fee * price
    return cost, price - cost, 100 * (price - cost) / price


def gantt():
    tasks = [("Lite schematic + PCB", 0, 2, C_MCU), ("Prototype 2 × 10 boards", 1, 3, C_PWR),
             ("Firmware on 4G module", 0, 4, C_MCU), ("App + server v1", 1, 4, C_CLOUD),
             ("WPC / BIS / EPR / TEC", 3, 6, C_ALERT), ("Pilot 300 units", 5, 7, C_RF),
             ("Amazon + dealers launch", 6, 8, C_IO)]
    months, lw, rh = 8, 140, 17
    d = Drawing(W, len(tasks) * rh + 24)
    cw = (W - lw) / months
    top = d.height - 15
    for m in range(months):
        x = lw + m * cw
        d.add(Rect(x, 0, cw, top, fillColor=LIGHT if m % 2 else None, strokeColor=None))
        txt(d, x + cw / 2, top + 4, f"M{m + 1}", 6.8, True, NAVY)
    for i, (name, a, b, c) in enumerate(tasks):
        y = top - (i + 1) * rh
        txt(d, lw - 6, y + 5, name, 7.4, False, colors.black, "end")
        d.add(Rect(lw + a * cw + 1, y + 2, (b - a) * cw - 2, rh - 5, rx=3, ry=3, fillColor=c, strokeColor=NAVY,
                   strokeWidth=0.5))
    return d


def on_page(c, doc):
    c.saveState()
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.8)
    c.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
    c.setFont(FONT, 7.5)
    c.setFillColor(GREY)
    c.drawString(18 * mm, A4[1] - 11 * mm, "Samay Electronics · Samay Track Lite")
    c.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "Plan · Oct 2026 · estimates, ex-GST")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"page {doc.page}")
    c.restoreState()


def build():
    s = []
    P = lambda t, st=BODY: s.append(Paragraph(t, st))  # noqa: E731

    # ---- page 1: what + design + cost
    P("Samay Track Lite: product and cost", H1)
    P("A low-cost 4G GPS tracker for bikes and scooters, made to sell on Amazon, through dealers and to small fleets. "
      "It is a <b>new design</b>: a 2-layer board where one 4G module also runs the firmware. "
      "All figures are estimates (Oct 2026, ex-GST).", LEAD)
    s.append(table([["Spec", "Lite"],
                    ["Network", "4G LTE Cat-1 <b>+ 2G fallback</b> (SIMCom A7672S / Quectel EC200U)"],
                    ["GPS", "GPS + BeiDou (L76K class); NavIC chip optional (+₹300–400)"],
                    ["Features", "live tracking · theft / tow alert · engine lock · geofence · ignition · "
                                 "SOS input · power-cut alert"],
                    ["Battery", "300 mAh internal, ≈ 2–4 h after a power cut"],
                    ["Supply", "9–32 V (12 / 24 V vehicles), reverse protected"],
                    ["Size / box", "≈ 50 × 35 mm board, IP65 plastic box, 4-wire harness"],
                    ["Not included", "NavIC dual-band, 40 h battery, crash detection, AIS-140"]],
                   [28 * mm, W - 28 * mm]))
    P("Design", H2)
    s.append(bp.lite_block())
    P("Block diagram: the 4G module is also the processor, so no ESP32 is needed.", CAP)
    P("Cost per unit (1,000 pcs)", H2)
    s.append(table([["Part", "₹"],
                    ["4G Cat-1 + 2G module", "500–650"], ["GPS module", "200–250"],
                    ["Accelerometer, power, charger, 300 mAh cell", "140–190"], ["Antennas (GPS patch + LTE FPC)", "60–80"],
                    ["Flash, SIM holder, ESD, passives", "80–100"], ["2-layer PCB + assembly", "80–100"],
                    ["Box, harness, packaging", "130–170"], ["<b>Total</b>", "<b>≈ 1,200–1,500</b>"]],
                   [W - 40 * mm, 40 * mm]))
    s.append(PageBreak())

    # ---- page 2: price + margin
    P("Price and profit", H1)
    P(f"Assumed hardware cost ₹{HW:,}. Each unit also carries ₹{DATA} year-1 data and cloud, ₹{SHIP} shipping and a "
      "3 % warranty reserve. Self-install, so there is no installation cost.", LEAD)
    rows = [["Channel", "Price", "Fees", "Profit / unit", "Margin"]]
    for name, price, fee, ftxt in [("Own website / WhatsApp", 2999, 0, "—"),
                                   ("Own website / WhatsApp", 3499, 0, "—"),
                                   ("Dealer (18 % cut)", 3499, 0.18, "18 %"),
                                   ("Amazon (18 % fees + 7 % ads)", 2999, 0.25, "25 %"),
                                   ("Amazon (18 % fees + 7 % ads)", 3499, 0.25, "25 %"),
                                   ("Small fleet / EV maker, bulk", 2499, 0, "—")]:
        _, p, m = econ(price, fee)
        rows.append([name, f"₹{price:,}", ftxt, f"₹{p:,.0f}", f"{m:.0f} %"])
    rows.append(["Renewal / year", "₹999", "—", f"₹{999 - DATA}", f"{100 * (999 - DATA) / 999:.0f} %"])
    s.append(table(rows, [62 * mm, 24 * mm, 22 * mm, 30 * mm, W - 138 * mm]))
    s.append(Spacer(1, 6))
    s.append(callout("<b>Recommendation:</b> list at <b>₹3,499 including the first year</b> (₹999/yr after). "
                     "At ₹2,999 on Amazon, only about ₹300 per unit is left after fees and ads. Sell direct and to "
                     "fleets for profit, and use Amazon for reach."))
    P("Competition at this price", H2)
    s.append(table([["Product", "Price"],
                    ["SeTrack, Ajjas 4G Lite, Onelap Micro / LocoShield, Fleettrack 4G", "₹900–2,900 incl. year 1"],
                    ["Alike GPS VT05R", "from ₹3,999"]], [W - 50 * mm, 50 * mm]))
    P("Our edge at ₹3,499: 2G fallback and normal 4G coverage, an engine lock with safe-stop logic, a power-cut "
      "alert with backup, a clean app, and local support. Optional NavIC is a selling point that the cheap ones "
      "lack.", BODY)
    s.append(PageBreak())

    # ---- page 3: money + time + missing
    P("Money needed and timeline", H1)
    inv = [("Lite board design + external review", 0.5, 1), ("Prototypes (2 rounds × 10)", 0.5, 1),
           ("Firmware + app + server", 2, 5), ("Enclosure: stock IP65 box → custom mould later", 0.3, 4),
           ("Test fixture", 0.3, 0.8), ("Certificates: WPC, BIS (certified cell), EPR, TEC, legal", 3, 8),
           ("Pilot batch 300 units × ≈ ₹1,800", 5.4, 5.4), ("Launch: Amazon listing, video, ads", 1, 3),
           ("6 months running costs (cloud, SIM, support)", 3, 6)]
    lo, hi = sum(a for _, a, _ in inv), sum(b for _, _, b in inv)
    rows = [["Item", "Low (₹ lakh)", "High (₹ lakh)"]] + [[n, f"{a:g}", f"{b:g}"] for n, a, b in inv]
    rows.append(["<b>Total to launch</b>", f"<b>{lo:g}</b>", f"<b>{hi:g}</b>"])
    s.append(table(rows, [W - 56 * mm, 28 * mm, 28 * mm]))
    _, pd_, _ = econ(3499)
    _, pa_, _ = econ(3499, 0.25)
    _, pdl_, _ = econ(3499, 0.18)
    blend = 0.3 * pd_ + 0.4 * pa_ + 0.3 * pdl_
    P(f"Then about <b>₹12–15 lakh per 1,000 units</b> of stock. <b>Break-even:</b> with 30 % direct, 40 % Amazon and "
      f"30 % dealer sales at ₹3,499, the average profit is ≈ ₹{blend:,.0f} per unit, so ≈ "
      f"<b>{round(25e5 / blend, -2):,.0f} units</b> recover ₹25 lakh. Renewals at ≈ ₹600 per customer per year "
      "shorten that.", BODY)
    s.append(gantt())
    P("About 8 months from start to launch.", CAP)
    P("Still missing: decide or do these", H2)
    s.append(table([["#", "Item"],
                    ["1", "Choose the module: A7672S or EC200U (price, SDK, supplier in India)"],
                    ["2", "Lite schematic + PCB (Claude can design it, same flow as the full board)"],
                    ["3", "Firmware on the 4G module + the app/server (Claude can write them; you create the accounts)"],
                    ["4", "IoT SIM deal (Jio / Airtel) and DoT M2M registration if you bundle the data"],
                    ["5", "Trademark check for \"Samay\", GST, Amazon seller account"],
                    ["6", "Warranty, returns, and a self-install video"]], [8 * mm, W - 8 * mm]))
    return s


def main():
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                            bottomMargin=16 * mm, title="Samay Track Lite: plan", author="Samay Electronics")
    doc.build(build(), onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
