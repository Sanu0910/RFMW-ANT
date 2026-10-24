"""Build the NOVA-RF1 DATASHEET-style PDF: features, block diagram, pinouts, functional
description, electrical characteristics, RF bands, power tree, mechanical, ordering."""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, HRFlowable)

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
OUT = os.path.normpath(os.path.join(HERE, "..", "04_docs", "NOVA-RF1_datasheet.pdf"))

ss = getSampleStyleSheet()
NAVY = colors.HexColor("#14314f")
BLUE = colors.HexColor("#2e5a84")
H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=20, spaceAfter=2, textColor=NAVY)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontSize=10, textColor=BLUE, spaceAfter=2)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=9, spaceAfter=3, textColor=NAVY)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=10, spaceBefore=5, spaceAfter=1, textColor=BLUE)
BODY = ParagraphStyle("BODY", parent=ss["Normal"], fontSize=8.8, leading=12)
SMALL = ParagraphStyle("SMALL", parent=ss["Normal"], fontSize=7.3, leading=9, textColor=colors.HexColor("#555"))
CAP = ParagraphStyle("CAP", parent=ss["Italic"], fontSize=7.5, textColor=colors.HexColor("#555"), alignment=1)


def P(t, s=BODY):
    return Paragraph(t, s)


def tbl(data, widths, hdr=True, size=7.6, align_r_from=1):
    t = Table(data, colWidths=[w * mm for w in widths])
    st = [("FONTSIZE", (0, 0), (-1, -1), size),
          ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    if hdr:
        st += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(st))
    return t


def img(path, w_mm):
    from PIL import Image as PImage
    iw, ih = PImage.open(path).size
    w = w_mm * mm
    return Image(path, width=w, height=w * ih / iw)


def build():
    doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=14 * mm, bottomMargin=12 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm, title="NOVA-RF1 Datasheet")
    e = []
    # ===== page 1: header + features + description =====
    e += [P("NOVA-RF1", H1),
          P("Hand-held multi-band RF / NFC / sub-GHz / IR multi-tool &mdash; Preliminary Datasheet, Rev v0.1", SUB),
          HRFlowable(width="100%", color=NAVY, thickness=1.2, spaceAfter=5)]

    feat = [["Features", "Applications"]]
    feat += [[Paragraph(f, SMALL), Paragraph(a, SMALL)] for f, a in [
        ("STM32WB55RGV6: Cortex-M4 64 MHz + Cortex-M0+ BLE 5.0, 1 MB flash, 256 KB RAM", "RFID / NFC development & research"),
        ("Sub-GHz CC1101: 300-348 / 387-464 / 779-928 MHz, OOK/2-FSK/GFSK/MSK, up to +12 dBm", "Sub-GHz remote capture & replay"),
        ("13.56 MHz NFC ST25R3916: reader / card-emulation / peer, ISO14443A/B, 15693, FeliCa", "Access-control / CTF / education"),
        ("125 kHz RFID discrete AFE (read EM4100 / HID-class)", "IR universal remote"),
        ("IR TX (38 kHz) + learning RX; 1-Wire / iButton", "1-Wire / iButton tooling"),
        ("128x64 mono LCD, microSD, RGB LED, speaker, vibro, 6-key UI", "BLE peripheral / beacon work"),
        ("USB-C charge (BQ25896) + fuel gauge (BQ27220), 1S Li-Po", "Embedded / hardware hacking"),
        ("18-pin expansion header (GPIO, SPI, UART, I2C, SWD, 3V3/5V)", "Open firmware (Flipper FW compatible)"),
    ]]
    e += [tbl(feat, [92, 78], size=7.3), Spacer(1, 5)]

    e += [P("General description", H2),
          P("NOVA-RF1 is an original open-hardware hand-held multi-tool that integrates five radio/signalling "
            "front-ends around an STM32WB55 wireless MCU. A single Cortex-M4 application core runs the UI and "
            "protocol logic while an on-chip Cortex-M0+ handles the BLE&nbsp;5.0 stack. Peripherals attach over two "
            "SPI buses, an I&sup2;C power bus, and timer/GPIO lines following the pin map of the open-source Flipper "
            "Zero firmware (GPLv3), which the board is designed to run. The board is 100&nbsp;&times;&nbsp;60&nbsp;mm, "
            "4-layer, two-sided SMT, in a two-part hand-held enclosure.", BODY),
          P("This is an original design: its schematic, PCB, outline, silkscreen and name are its own; it uses none "
            "of Flipper Devices' trademarks, logo, dolphin mascot or hardware design files. The CC1101 sub-GHz "
            "transmitter and the BLE radio require RF type approval (FCC / CE / WPC-ETA + BIS) before a product is "
            "sold or operated; transmit only on licensed bands and powers.", SMALL)]

    # block diagram
    e += [P("Block diagram", H2),
          P("<font face='Courier' size=7>"
            "USB-C 5V &mdash;&gt; BQ25896 charger/boost &mdash;&gt; 1S Li-Po &mdash;&gt; LM3281 bucks &mdash;&gt; 3V3 core / periph<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BQ27220 gauge (I2C)&nbsp;&nbsp;&nbsp;RS3221 LDO &mdash;&gt; A3V3 (analog)<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ STM32WB55 MCU + BLE ]<br/>"
            "&nbsp;SPI-R &mdash;+&mdash; CC1101 &mdash;&gt; balun &mdash;&gt; RF switch &mdash;&gt; U.FL (sub-GHz antenna)<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+&mdash; ST25R3916 &mdash;&gt; EMC/match &mdash;&gt; 13.56 MHz loop antenna<br/>"
            "&nbsp;GPIO &mdash;+&mdash; 125 kHz coil driver + op-amp/comparator RX &mdash;&gt; coil<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+&mdash; IR TX/RX, iButton, buttons, RGB LED, speaker, vibro<br/>"
            "&nbsp;SPI-D &mdash;+&mdash; ST7565 128x64 LCD&nbsp;&nbsp;&nbsp;+&mdash; microSD<br/>"
            "&nbsp;2.4 GHz (on-chip) &mdash;&gt; BLE filter &mdash;&gt; chip antenna</font>", BODY),
          PageBreak()]

    # ===== page 2: interfaces / pinouts =====
    e += [P("Bus &amp; interface map", H2),
          tbl([["Bus", "MCU pins", "Devices"],
               ["SPI-R (radio)", "SCK PA5 / MISO PB4 / MOSI PB5", "CC1101 (CS PD0, GDO0 PA1); ST25R3916 (CS PE4)"],
               ["SPI-D (display)", "SCK PD1 / MISO PC2 / MOSI PB15", "ST7565 LCD (CS PC11, DC PB1, RST PB0); microSD (CS PC12, CD PC10)"],
               ["I2C power", "SDA PA10 / SCL PA9", "BQ25896 charger, BQ27220 gauge, LP5562 LED driver"],
               ["USB-FS", "DM PA11 / DP PA12", "USB-C (via USBLC6 ESD)"],
               ["SWD", "SWDIO PA13 / SWCLK PA14 / NRST", "Tag-Connect TC2030"],
               ["UART1", "TX PB6 / RX PB7", "expansion header"]],
              [24, 52, 94]), Spacer(1, 4)]

    e += [P("Expansion header J_GPIO (2&times;9, 2.54 mm)", H3),
          tbl([["Pin", "Net", "Pin", "Net"],
               ["1", "+3V3", "2", "GPIO PA7"],
               ["3", "GPIO PA6", "4", "GPIO PA4"],
               ["5", "GPIO PB3", "6", "GPIO PB2"],
               ["7", "GPIO PC3", "8", "GPIO PC1"],
               ["9", "GPIO PC0", "10", "SWCLK"],
               ["11", "SWDIO", "12", "UART TX (PB6)"],
               ["13", "UART RX (PB7)", "14", "I2C SDA (PA10)"],
               ["15", "I2C SCL (PA9)", "16", "VBUS (+5V)"],
               ["17", "VIBRO (PA8)", "18", "GND"]],
              [12, 40, 12, 40]), Spacer(1, 4)]

    e += [P("Other connectors", H3),
          tbl([["Ref", "Type", "Function"],
               ["J_USB", "USB-C receptacle", "5 V charge input + USB-FS data"],
               ["X10", "1.25 mm 3-pin", "external 1S Li-Po: BAT / NTC / GND"],
               ["X6", "18-pin 0.5 mm FFC", "link to NFC/RFID/IR sub-section (if partitioned)"],
               ["J_SUBG", "U.FL", "sub-GHz antenna"],
               ["J_SWD", "Tag-Connect TC2030", "SWD programming / debug"]],
              [20, 44, 106]), PageBreak()]

    # ===== page 3: functional description =====
    e += [P("Functional description", H2)]
    blocks = [
        ("MCU &amp; BLE (U1, STM32WB55RGV6)",
         "Dual-core wireless MCU: a Cortex-M4 at up to 64 MHz runs the application, a Cortex-M0+ runs the certified "
         "BLE&nbsp;5.0 stack. 1 MB flash / 256 KB RAM, USB-FS, AES/PKA crypto. A 32 MHz HSE crystal (Y1, under the "
         "chip) clocks the radio and an internal SMPS (L_SMPS 10 uH) powers it; a 32.768 kHz LSE (Y2) clocks the RTC. "
         "The 2.4 GHz BLE output passes through a band-pass filter (FLT1) and pi-match to a chip antenna (ANT1)."),
        ("Sub-GHz transceiver (U2, CC1101)",
         "Configured over SPI-R. Supports 300-348, 387-464 and 779-928 MHz with OOK, 2-FSK, GFSK and MSK, data rates "
         "to 600 kbps, sensitivity to ~-112 dBm and output to ~+12 dBm. The differential RF port is converted by a "
         "balun (FLT2) and LC match, then two SPDT RF switches (SW1/SW2) select band/antenna to the U.FL output. "
         "A 26 MHz crystal (ZQ3) sets the reference; RBIAS = 56 k."),
        ("13.56 MHz NFC (U3, ST25R3916)",
         "Reader / card-emulation / active-peer front-end on SPI-R, clocked by a 27.12 MHz crystal (ZQ1). The "
         "differential driver feeds an EMC + matching network (L1/L2 270 nH plus the tuning caps) into a PCB loop "
         "antenna; the receiver reads card modulation on RFI_P/RFI_N. Supports ISO14443A/B, ISO15693 and FeliCa."),
        ("125 kHz RFID analog front-end",
         "A FET H-bridge (VT4/VT6) drives the read coil with a 125 kHz carrier gated by an MCU timer. The returning "
         "amplitude-modulated signal is band-pass amplified by two op-amps (DA3/DA4, LMV358) on the clean A3V3 rail, "
         "sliced by a comparator (DA5, LMV331) against a 1.65 V mid-rail (R_MID divider), and read back as digital "
         "data. Reads EM4100 / HID-class tags."),
        ("Infrared, 1-Wire, UI",
         "IR: a VSMY14940 LED bank driven from a timer pin transmits 38 kHz-modulated codes; a TSOP75338 demodulator "
         "receives for learning. iButton: an ESD-protected open-drain GPIO (PB14). UI: 128x64 ST7565 LCD and microSD "
         "on SPI-D, a 6-key cluster, an RGB LED (LP5562), a magnetic speaker and a vibromotor."),
        ("Power",
         "USB-C 5 V feeds a BQ25896 1-cell Li-ion charger with 5 V OTG boost and I2C control; a BQ27220 fuel gauge "
         "reports state-of-charge. Two LM3281 bucks generate the 3.3 V core and peripheral rails; an RS3221 LDO "
         "supplies the clean analog rail (A3V3); a TPS22917 load switch cuts the peripheral rail in deep sleep. The "
         "battery is external (X10)."),
    ]
    for t, d in blocks:
        e += [P(t, H3), P(d, BODY)]
    e += [PageBreak()]

    # ===== page 4: electrical / RF / mechanical =====
    e += [P("Absolute maximum ratings", H2),
          tbl([["Parameter", "Min", "Max", "Unit"],
               ["USB-C VBUS input", "-0.3", "6.0", "V"],
               ["Battery (VBAT)", "-0.3", "4.5", "V"],
               ["Logic I/O (3V3 domain)", "-0.3", "3.6", "V"],
               ["Operating temperature", "-20", "+60", "degC"],
               ["Storage temperature", "-40", "+85", "degC"]],
              [70, 20, 20, 20])]
    e += [P("Recommended operating conditions", H2),
          tbl([["Rail", "Typ", "Range", "Source / load"],
               ["VBUS", "5.0 V", "4.4-5.25 V", "USB-C charge in / OTG out"],
               ["VBAT", "3.7 V", "3.0-4.2 V", "1S Li-Po"],
               ["+3V3 (core)", "3.3 V", "+/-3%", "LM3281 buck - MCU, radios, display"],
               ["+3V3_PERIPH", "3.3 V", "+/-3%", "switched (load switch) - SD/radios"],
               ["A3V3 (analog)", "3.3 V", "+/-2%", "RS3221 LDO - RFID op-amps"]],
              [28, 18, 28, 76])]
    e += [P("Estimated current (indicative)", H2),
          tbl([["Mode", "Typ current (at VBAT)"],
               ["Idle (display on, radios off)", "~25-40 mA"],
               ["Sub-GHz RX / NFC poll", "~40-70 mA"],
               ["Sub-GHz TX (+12 dBm) burst", "~120-160 mA peak"],
               ["Deep sleep (peripheral rail off)", "~100-300 uA"]],
              [80, 60]),
          P("Current figures are design estimates for budgeting; confirm on hardware.", SMALL)]

    e += [P("RF summary", H2),
          tbl([["Radio", "Band", "Notes"],
               ["Sub-GHz (CC1101)", "300-928 MHz (ISM sub-bands)", "OOK/FSK/GFSK/MSK; antenna via U.FL + RF switch"],
               ["NFC (ST25R3916)", "13.56 MHz", "ISO14443A/B, 15693, FeliCa; PCB loop antenna"],
               ["125 kHz RFID", "125 kHz", "EM4100 / HID-class read; wound/PCB coil"],
               ["BLE (STM32WB55)", "2.400-2.4835 GHz", "BLE 5.0; chip antenna via band filter"]],
              [34, 44, 92])]

    e += [P("Mechanical", H2),
          tbl([["Parameter", "Value"],
               ["Board size", "100 x 60 mm, rounded handheld outline"],
               ["Layers / thickness", "4-layer (Sig/GND/PWR/Sig), 1.6 mm, ENIG"],
               ["Enclosure", "two-part printed case, outer ~106 x 66 mm"],
               ["Assembly", "double-sided SMT (ICs/connectors top, passives bottom)"]],
              [45, 125]), Spacer(1, 4)]
    shot = os.path.join(K, "nova-rf1-routed.png")
    if os.path.exists(shot):
        e += [img(shot, 150), P("Figure: routed 4-layer board (red=top, blue=bottom, inner GND/PWR planes, dots=vias).", CAP)]

    e += [Spacer(1, 4), HRFlowable(width="100%", color=colors.HexColor("#bbb")),
          P("Ordering: NOVA-RF1 v0.1, 4-layer PCBA, original open-hardware. Compliance: radios require type approval "
            "(FCC/CE/WPC-ETA+BIS) before sale or transmit. Preliminary - all values subject to change and hardware "
            "verification. Original design; not a Flipper Zero; no Flipper Devices IP used.", SMALL)]

    doc.build(e)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
