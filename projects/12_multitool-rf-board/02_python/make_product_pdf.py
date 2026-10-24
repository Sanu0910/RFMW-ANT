"""Build the NOVA-RF1 product PDF: working principle, BOM cost, and PCB photos."""
import csv
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, HRFlowable)

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
FAB = os.path.normpath(os.path.join(HERE, "..", "03_fab"))
ENC = os.path.normpath(os.path.join(HERE, "..", "05_enclosure"))
OUT = os.path.normpath(os.path.join(HERE, "..", "04_docs", "NOVA-RF1_product.pdf"))

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=22, spaceAfter=4, textColor=colors.HexColor("#1b3a5b"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=14, spaceBefore=10, spaceAfter=4,
                    textColor=colors.HexColor("#1b3a5b"))
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=11, spaceBefore=6, spaceAfter=2,
                    textColor=colors.HexColor("#2e5a84"))
BODY = ParagraphStyle("BODY", parent=ss["Normal"], fontSize=9.3, leading=13)
SMALL = ParagraphStyle("SMALL", parent=ss["Normal"], fontSize=7.6, leading=9.5, textColor=colors.HexColor("#555"))
CAP = ParagraphStyle("CAP", parent=ss["Italic"], fontSize=8, textColor=colors.HexColor("#555"),
                     alignment=1, spaceBefore=2)


def img(path, w_mm):
    from PIL import Image as PImage
    iw, ih = PImage.open(path).size
    w = w_mm * mm
    return Image(path, width=w, height=w * ih / iw)


def P(t, s=BODY):
    return Paragraph(t, s)


def build():
    doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=16 * mm, bottomMargin=14 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title="NOVA-RF1")
    e = []
    # ---------- title ----------
    e += [P("NOVA-RF1", H1),
          P("Original firmware-compatible hand-held RF / NFC / sub-GHz multi-tool", H3),
          HRFlowable(width="100%", color=colors.HexColor("#1b3a5b"), thickness=1.2, spaceAfter=6),
          P("NOVA-RF1 is an <b>original open-hardware</b> hand-held tool for RFID/NFC, 125&nbsp;kHz, "
            "13.56&nbsp;MHz, sub-GHz (300-928&nbsp;MHz), infrared, 1-Wire/iButton and BLE work. It is built "
            "around the same silicon class as popular multi-tools and is designed to run the open-source "
            "Flipper Zero firmware (GPLv3) and its community forks &mdash; but it is <b>not</b> a Flipper Zero: "
            "its schematic, PCB, outline, silkscreen and name are its own, and it uses none of Flipper "
            "Devices' trademarks, logo, dolphin mascot or design files.", BODY),
          P("Board 100&nbsp;&times;&nbsp;60&nbsp;mm, 4-layer, two-sided SMT, in a two-part printed enclosure. "
            "Radios require type approval (FCC / CE / WPC-ETA+BIS) before sale; transmit only on bands and "
            "powers you are licensed for.", SMALL),
          Spacer(1, 6)]

    # ---------- working principle ----------
    e += [P("1. How it works &mdash; working principle", H2),
          P("A single <b>STM32WB55</b> (Cortex-M4 application core + Cortex-M0+ BLE stack) is the brain. It "
            "talks to each radio / peripheral over two SPI buses and a handful of GPIO/timer lines, exactly as "
            "the firmware's pin map declares. Power comes from USB-C or a 1-cell Li-Po through a charger and "
            "switching regulators. Each subsystem:", BODY)]

    subs = [
        ("MCU + Bluetooth LE &mdash; STM32WB55RGV6",
         "The application core runs the UI, protocol stacks and app logic; the on-chip M0+ runs BLE&nbsp;5. A "
         "32&nbsp;MHz crystal (placed directly under the chip) clocks the radio; a 32.768&nbsp;kHz crystal keeps "
         "the RTC. The internal SMPS (with its 10&nbsp;uH inductor) powers the radio efficiently. The 2.4&nbsp;GHz "
         "BLE signal leaves through a band-pass filter and pi-match to a chip antenna."),
        ("Sub-GHz radio &mdash; CC1101 (300-928 MHz)",
         "On the SPI-R bus. The MCU configures frequency, modulation and power; the CC1101's differential RF "
         "port goes through a balun + LC match to two SPDT RF switches that select band/antenna, then to a "
         "helical/whip antenna via a U.FL connector. Used to capture and replay 433/868/915&nbsp;MHz remotes."),
        ("13.56 MHz NFC &mdash; ST25R3916",
         "Also on SPI-R. A 27.12&nbsp;MHz crystal clocks it; its differential driver feeds an EMC + matching "
         "network (L1/L2 270&nbsp;nH + caps) into a PCB loop antenna, and the receiver reads card modulation on "
         "RFI_P/RFI_N. Reads/writes/emulates ISO14443 A/B, ISO15693 and FeliCa cards."),
        ("125 kHz RFID &mdash; discrete analog front-end",
         "Not a single chip: an H-bridge of FETs drives the read coil with a 125&nbsp;kHz carrier gated by the "
         "MCU timer; the returning amplitude-modulated signal is band-pass amplified by two op-amps, sliced by a "
         "comparator against a 1.65&nbsp;V mid-rail, and read back as digital data. Reads EM4100/HID-class tags."),
        ("Infrared",
         "An IR LED bank (driven by a FET from a timer pin) transmits 38&nbsp;kHz-modulated remote codes; a TSOP "
         "demodulator receives and decodes incoming IR for learning remotes."),
        ("1-Wire / iButton",
         "An open-drain GPIO with ESD protection reads and emulates Dallas/iButton (DS1990-class) keys on a "
         "spring-contact pad."),
        ("Display, storage, UI",
         "A 128&times;64 monochrome LCD (ST7565R, SPI-D bus) shows the UI; a microSD card (also SPI-D) holds apps "
         "and captured data; a 5-way + back button cluster drives navigation; an RGB LED (LP5562 driver), a "
         "speaker and a vibromotor give feedback."),
        ("Power path",
         "USB-C 5&nbsp;V feeds a BQ25896 1-cell Li-ion charger with 5&nbsp;V OTG boost; a BQ27220 fuel gauge "
         "tracks charge over the I2C power bus. Two LM3281 buck converters make the 3.3&nbsp;V core and "
         "peripheral rails; an RS3221 LDO gives a clean analog rail; a load switch cuts the peripheral rail in "
         "deep sleep for long standby. The battery pack is external, wired to the X10 connector."),
        ("Expansion",
         "An 18-pin GPIO header exposes 8 user GPIO, both SPI buses, UART, the I2C power bus, SWD and 3V3/5V/GND "
         "&mdash; e.g. for an ESP32-S3 Wi-Fi/BLE add-on. A Tag-Connect pad programs the MCU over SWD."),
    ]
    for t, d in subs:
        e += [P(t, H3), P(d, BODY)]

    e += [Spacer(1, 4),
          P("Signal flow (block diagram)", H3),
          P("USB-C / Li-Po &rarr; BQ25896 charger + LM3281 bucks &rarr; 3.3&nbsp;V rails &rarr; "
            "<b>STM32WB55</b><br/>"
            "&nbsp;&nbsp;&bull; SPI-R &rarr; CC1101 (sub-GHz) &rarr; balun &rarr; RF switch &rarr; U.FL antenna<br/>"
            "&nbsp;&nbsp;&bull; SPI-R &rarr; ST25R3916 (NFC) &rarr; matching net &rarr; 13.56&nbsp;MHz loop<br/>"
            "&nbsp;&nbsp;&bull; timers/GPIO &rarr; 125&nbsp;kHz coil driver + op-amp/comparator RX<br/>"
            "&nbsp;&nbsp;&bull; SPI-D &rarr; ST7565 display + microSD<br/>"
            "&nbsp;&nbsp;&bull; GPIO &rarr; IR TX/RX, iButton, buttons, RGB LED, speaker, vibro<br/>"
            "&nbsp;&nbsp;&bull; on-chip 2.4&nbsp;GHz &rarr; BLE filter &rarr; chip antenna", BODY),
          PageBreak()]

    # ---------- BOM cost ----------
    e += [P("2. Bill of materials &amp; cost", H2),
          P("Estimated small-quantity component cost (USD). Prices are distributor ballpark figures for "
            "budgeting; get a live quote for production. Battery pack is external and listed separately. "
            "Top cost drivers shown; full costed BOM in <font face='Courier'>03_fab/NOVA-RF1_BOM_costed.csv</font>.",
            SMALL)]
    rows = [["Value", "MPN", "Qty", "Unit $", "Ext $"]]
    total = 0.0
    nlines = 0
    with open(os.path.join(FAB, "NOVA-RF1_BOM_costed.csv")) as f:
        for r in csv.reader(f):
            if not r or r[0] in ("Value", ""):
                continue
            value, mpn, desig, qty, up, ext = r
            nlines += 1
            total += float(ext)
            if nlines <= 22:
                rows.append([value[:16], mpn[:22], qty, up, ext])
    rows.append(["...", f"+ {nlines - 22} more lines", "", "", ""])
    t = Table(rows, colWidths=[26 * mm, 48 * mm, 12 * mm, 16 * mm, 16 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a5b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    e += [t, Spacer(1, 6)]

    # cost summary
    pcb = 10.0
    asm = 8.0
    batt = 3.0
    summary = [["Cost line (per unit, low volume)", "USD"],
               ["Components (86 placements)", f"{total:.2f}"],
               ["4-layer PCB (100x60, HDI, ~5-10 pcs)", f"~{pcb:.2f}"],
               ["SMT assembly (est.)", f"~{asm:.2f}"],
               ["Li-Po battery (external)", f"~{batt:.2f}"],
               ["Enclosure (3D print, est.)", "~2.00"],
               ["ESTIMATED TOTAL / unit", f"~{total + pcb + asm + batt + 2:.2f}"]]
    ts = Table(summary, colWidths=[90 * mm, 24 * mm])
    ts.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e5a84")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d7e6f2")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    e += [ts,
          P("At small volume NOVA-RF1 lands around $55-60 built. Components alone are ~$35; the STM32WB55, "
            "ST25R3916 and CC1101 are the biggest drivers. At production volume (1k+) component cost roughly "
            "halves and PCB+assembly drop sharply.", SMALL),
          PageBreak()]

    # ---------- PCB photos ----------
    e += [P("3. PCB &amp; enclosure", H2)]
    shots = [
        (os.path.join(K, "nova-rf1_schematic.png"), "Full schematic (88 parts, 108 nets) - ERC passes with 0 errors."),
        (os.path.join(K, "nova-rf1-placed.png"), "Compact 100 x 60 mm placement, functional bands, connectors on edges (ICs top / passives bottom)."),
        (os.path.join(K, "nova-rf1-routed.png"), "4-layer autorouted board (red=top, blue=bottom, inner=GND/PWR, dots=vias) with poured GND plane."),
        (os.path.join(ENC, "nova-rf1-case.png"), "Two-part handheld enclosure: tray (PCB + USB-C cutout) and lid (display window, button holes, GPIO slot)."),
    ]
    for path, cap in shots:
        if os.path.exists(path):
            e += [img(path, 170), P(cap, CAP), Spacer(1, 6)]

    e += [Spacer(1, 4), HRFlowable(width="100%", color=colors.HexColor("#bbb")),
          P("NOVA-RF1 - original firmware-compatible multi-tool. Not a Flipper Zero; no Flipper Devices "
            "trademark, logo, mascot or design files used. Generated from the open design in "
            "projects/12_multitool-rf-board. Radios need type approval before sale.", SMALL)]

    doc.build(e)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
