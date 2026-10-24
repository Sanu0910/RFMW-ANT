"""Generate simplified custom footprints (nova-rf1.pretty) with pads named to match design.py pins.

These cover the mechanical / RF / connector parts KiCad has no stock footprint for. Pad COUNT,
NAMES, pitch and rough size are representative so the board places, nets and routes correctly;
refine the exact courtyard/pad geometry against each part's datasheet drawing before fabrication.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.normpath(os.path.join(HERE, "..", "01_kicad", "nova-rf1.pretty"))
os.makedirs(PRETTY, exist_ok=True)


def fp(name, pads, pitch=1.0, padsize=(0.7, 0.7), rows=1, desc=""):
    """pads: list of pad names. Single row (rows=1) or two rows (rows=2, split L/R)."""
    lines = [f'(footprint "{name}" (version 20240108) (generator "make_footprints")',
             '  (layer "F.Cu")',
             f'  (descr "{desc}")',
             '  (attr smd)']
    n = len(pads)
    if rows == 1:
        w = (n - 1) * pitch
        for i, pn in enumerate(pads):
            x = -w / 2 + i * pitch
            lines.append(_pad(pn, x, 0, padsize))
        bx, by = w / 2 + padsize[0], padsize[1] + 0.6
    else:
        per = (n + 1) // 2
        colgap = 2.0
        h = (per - 1) * pitch
        for i, pn in enumerate(pads):
            if i < per:
                x, y = -colgap / 2, -h / 2 + i * pitch
            else:
                x, y = colgap / 2, -h / 2 + (i - per) * pitch
            lines.append(_pad(pn, x, y, padsize))
        bx, by = colgap / 2 + padsize[0], h / 2 + padsize[1] + 0.3
    # ref / value + courtyard
    lines.append(f'  (fp_text reference "REF**" (at 0 {-by-0.8:.2f}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'  (fp_text value "{name}" (at 0 {by+0.8:.2f}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    for (x1, y1, x2, y2) in [(-bx, -by, bx, by)]:
        lines.append(f'  (fp_rect (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))')
    lines.append(")")
    with open(os.path.join(PRETTY, name + ".kicad_mod"), "w") as f:
        f.write("\n".join(lines) + "\n")


def bga(name, rows, cols, pitch=0.4, ball=0.25, desc=""):
    """Ball grid: rows like ['A','B','C'], cols like [1,2,3,4]; pads named A1.. ."""
    lines = [f'(footprint "{name}" (version 20240108) (generator "make_footprints")',
             '  (layer "F.Cu")', f'  (descr "{desc}")', '  (attr smd)']
    w = (len(cols) - 1) * pitch
    h = (len(rows) - 1) * pitch
    for ri, r in enumerate(rows):
        for ci, c in enumerate(cols):
            x = -w / 2 + ci * pitch
            y = -h / 2 + ri * pitch
            lines.append(_pad(f"{r}{c}", x, y, (ball, ball)))
    bx, by = w / 2 + ball, h / 2 + ball
    lines.append(f'  (fp_text reference "REF**" (at 0 {-by-0.8:.2f}) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))')
    lines.append(f'  (fp_text value "{name}" (at 0 {by+0.8:.2f}) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.1))))')
    lines.append(f'  (fp_rect (start {-bx:.2f} {-by:.2f}) (end {bx:.2f} {by:.2f}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))')
    lines.append(")")
    with open(os.path.join(PRETTY, name + ".kicad_mod"), "w") as f:
        f.write("\n".join(lines) + "\n")


def _pad(pn, x, y, size):
    return (f'  (pad "{pn}" smd roundrect (at {x:.3f} {y:.3f}) (size {size[0]} {size[1]}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')


# 2-pin modules -----------------------------------------------------------------
fp("NFC_Loop_Antenna", ["1", "2"], pitch=4.0, padsize=(1.2, 1.5), desc="13.56 MHz PCB loop antenna feed")
fp("RFID_125k_Coil", ["1", "2"], pitch=4.0, padsize=(1.2, 1.5), desc="125 kHz read coil terminals")
fp("iButton_Contacts", ["DATA", "GND"], pitch=4.0, padsize=(2.0, 2.5), desc="iButton spring contacts")
fp("Speaker_2p", ["+", "-"], pitch=5.0, padsize=(1.5, 2.0), desc="magnetic speaker pads")
fp("Vibro_2p", ["+", "-"], pitch=3.0, padsize=(1.2, 1.5), desc="vibro motor pads")
fp("Battery_3p", ["+", "NTC", "-"], pitch=2.0, padsize=(1.2, 1.6), desc="1S Li-Po + NTC connector")
fp("Antenna_Chip", ["1"], padsize=(1.2, 1.6), desc="2.4 GHz chip antenna feed")
# RF parts ----------------------------------------------------------------------
fp("RF_filter", ["IN", "GND", "OUT"], pitch=0.6, padsize=(0.35, 0.5), desc="2.4 GHz BLE band filter (LFL182G45)")
fp("Johanson_0310_Balun", ["BAL1", "BAL2", "UNBAL", "GND"], pitch=0.5, padsize=(0.3, 0.45), rows=2,
   desc="CC1101 balun B0310J50100AHF")
fp("RF_Switch_TSNP9", ["RFin", "RF1", "RF2", "V1", "V2", "VDD", "GND"], pitch=0.5, padsize=(0.25, 0.35),
   rows=2, desc="BGS13S4N9 SPDT RF switch")
# connectors / IO ---------------------------------------------------------------
fp("Display_ST7565_FFC", ["VSS", "VDD", "SCL", "SI", "A0", "RST", "CS"], pitch=1.0, padsize=(0.6, 1.5),
   desc="128x64 ST7565R display FFC")
fp("TSOP_IR_3p", ["OUT", "GND", "VS"], pitch=2.54, padsize=(1.0, 1.4), desc="TSOP75338 38 kHz IR demod")
fp("TagConnect_TC2030", ["SWDIO", "SWCLK", "NRST", "VCC", "GND"], pitch=1.27, padsize=(0.7, 1.3),
   desc="Tag-Connect TC2030 SWD")
fp("LED_RGB_4p", ["A", "R", "G", "B"], pitch=1.0, padsize=(0.5, 0.7), rows=2, desc="common-anode RGB LED")
fp("microSD_7p", ["VSS", "VDD", "CLK", "CD", "CS", "DI", "DO"], pitch=1.1, padsize=(0.7, 1.6),
   desc="microSD push-pull (SPI mode)")

# LP5562 DSBGA-12: 3 rows (A,B,C) x 4 cols (1-4), 0.4 mm pitch
bga("LP5562_DSBGA12", ["A", "B", "C"], [1, 2, 3, 4], pitch=0.4, ball=0.25, desc="LP5562 12-ball DSBGA YQE")

if __name__ == "__main__":
    print("wrote", len(os.listdir(PRETTY)), "footprints to", PRETTY)
