"""Project library: symbols for parts missing from the KiCad stock library.

SIM7080G pin table: SIMCom SIM7080G Hardware Design V1.04, table 3 (77 pins).
NEO-F10N pin table: u-blox NEO-F10N data sheet UBX-23002117, section 'Pin definition'.
"""
import os
from sexp import Sym, dump

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "01_kicad", "tracker.kicad_sym")

SIM7080G = {
    1: ("UART1_TXD", "output"), 2: ("UART1_RXD", "input"), 3: ("UART1_RTS", "input"), 4: ("UART1_CTS", "output"),
    5: ("UART1_DCD", "output"), 6: ("UART1_DTR", "input"), 7: ("UART1_RI", "output"), 9: ("PCM_DIN", "input"),
    10: ("PCM_DOUT", "output"), 11: ("PCM_CLK", "bidirectional"), 12: ("PCM_SYNC", "bidirectional"), 14: ("GPIO5", "bidirectional"),
    15: ("SIM_DATA", "bidirectional"), 16: ("SIM_CLK", "output"), 17: ("SIM_RST", "output"), 18: ("SIM_VDD", "power_out"),
    20: ("USB_BOOT", "input"), 22: ("UART2_TXD", "output"), 23: ("UART2_RXD", "input"), 24: ("USB_VBUS", "input"),
    25: ("USB_DP", "bidirectional"), 26: ("USB_DM", "bidirectional"), 28: ("NC", "no_connect"), 29: ("NC", "no_connect"),
    32: ("RF_ANT", "bidirectional"), 34: ("VBAT", "power_in"), 35: ("VBAT", "power_in"), 38: ("ADC", "input"),
    39: ("PWRKEY", "input"), 40: ("VDD_EXT", "power_out"), 41: ("NETLIGHT", "output"), 42: ("STATUS", "output"),
    43: ("ANT_CONTROL1", "output"), 44: ("ANT_CONTROL0", "output"), 46: ("NC", "no_connect"), 47: ("NC", "no_connect"),
    48: ("SPI_CS", "output"), 49: ("SPI_MOSI", "output"), 50: ("SPI_CLK", "output"), 51: ("SPI_MISO", "input"),
    52: ("NC", "no_connect"), 53: ("NC", "no_connect"), 54: ("NC", "no_connect"), 55: ("NC", "no_connect"), 56: ("NC", "no_connect"),
    57: ("GPIO1", "bidirectional"), 58: ("GPIO2", "bidirectional"), 59: ("GPIO3", "bidirectional"), 60: ("GPIO4", "bidirectional"),
    61: ("UART3_TXD", "output"), 62: ("UART3_RXD", "input"), 64: ("I2C_SDA", "bidirectional"), 65: ("I2C_SCL", "output"),
    68: ("GNSS_ANT", "bidirectional"),
}
SIM_GND = [8, 13, 19, 21, 27, 30, 31, 33, 36, 37, 45, 63, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77]

NEO_F10N = {
    1: ("SAFEBOOT_N", "input"), 2: ("RSV", "no_connect"), 3: ("TIMEPULSE", "output"), 4: ("EXTINT", "input"),
    5: ("RSV", "no_connect"), 6: ("RSV", "no_connect"), 7: ("RSV", "no_connect"), 8: ("RESET_N", "input"),
    9: ("VCC_RF", "power_out"), 10: ("GND", "power_in"), 11: ("RF_IN", "input"), 12: ("GND", "passive"),
    13: ("GND", "passive"), 14: ("LNA_EN", "output"), 15: ("RSV", "no_connect"), 16: ("RSV", "no_connect"),
    17: ("RSV", "no_connect"), 18: ("RSV", "no_connect"), 19: ("RSV", "no_connect"), 20: ("TXD", "output"),
    21: ("RXD", "input"), 22: ("V_BCKP", "power_in"), 23: ("VCC", "power_in"), 24: ("GND", "passive"),
}


def prop(k, v, x, y, hide=False):
    p = [Sym("property"), k, v, [Sym("at"), x, y, 0], [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]]
    if hide:
        p[-1].append([Sym("hide"), Sym("yes")])
    return p


def pin(num, name, etype, x, y, ang, hidden=False):
    p = [Sym("pin"), Sym(etype), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), 2.54]]
    if hidden:
        p.append(Sym("hide"))
    p += [[Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.016, 1.016]]]],
          [Sym("number"), str(num), [Sym("effects"), [Sym("font"), [Sym("size"), 1.016, 1.016]]]]]
    return p


def box_symbol(name, ref, fp, ds, desc, left, right, bottom_gnd=(), top=()):
    """left/right: list of (num,name,type) or None for gap. GND pins stacked on one bottom pin."""
    rows = max(len(left), len(right))
    h = (rows + 1) * 2.54
    w = 25.4 if name == "SIM7080G" else 20.32
    y0 = h / 2
    items = []
    def place(lst, side):
        for i, e in enumerate(lst):
            if e is None:
                continue
            n, nm, t = e
            y = round((y0 - 2.54 * (i + 1)) / 2.54) * 2.54
            if side == "L":
                items.append(pin(n, nm, t, -w / 2 - 2.54, y, 0))
            else:
                items.append(pin(n, nm, t, w / 2 + 2.54, y, 180))
    place(left, "L"); place(right, "R")
    ybot = round((-y0 - 2.54) / 2.54) * 2.54
    for k, n in enumerate(bottom_gnd):
        items.append(pin(n, "GND", "power_in" if k == 0 else "passive", 0, ybot, 90, hidden=k > 0))
    xt = -((len(top) - 1) * 2.54) / 2
    ytop = round((y0 + 2.54) / 2.54) * 2.54
    for k, e in enumerate(top):
        n, nm, t = e
        items.append(pin(n, nm, t, round((xt + k * 2.54) / 1.27) * 1.27, ytop, 270))
    body = [Sym("symbol"), f"{name}_0_1",
            [Sym("rectangle"), [Sym("start"), -w / 2, ybot + 2.54], [Sym("end"), w / 2, ytop - 2.54],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins_unit = [Sym("symbol"), f"{name}_1_1"] + items
    return [Sym("symbol"), name, [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            prop("Reference", ref, 0, ytop + 1.27), prop("Value", name, 0, ybot - 1.27),
            prop("Footprint", fp, 0, 0, True), prop("Datasheet", ds, 0, 0, True), prop("Description", desc, 0, 0, True),
            body, pins_unit]


def sim7080g():
    L = [1, 2, 3, 4, 5, 6, 7, None, 22, 23, 61, 62, None, 64, 65, None, 48, 49, 50, 51, None, 9, 10, 11, 12]
    R = [32, 68, None, 15, 16, 17, 18, None, 24, 25, 26, 20, None, 39, 42, 41, 38, None, 43, 44, None, 14, 57, 58, 59, 60]
    nc = [28, 29, 46, 47, 52, 53, 54, 55, 56]
    R += [None] + nc[:4]
    L += [None] + nc[4:]
    f = lambda lst: [None if n is None else (n, SIM7080G[n][0], SIM7080G[n][1]) for n in lst]
    top = [(34, "VBAT", "power_in"), (35, "VBAT", "passive"), (40, "VDD_EXT", "power_out")]
    s = box_symbol("SIM7080G", "U", "tracker:SIMCom_SIM7080G_LCC-77", "https://www.simcom.com/product/SIM7080G.html",
                   "SIMCom LTE Cat-M1 / NB-IoT module, LCC 17.6x15.7 mm, 77 pins", f(L), f(R), SIM_GND, top)
    return s


def neo_f10n():
    L = [(23, "VCC", "power_in"), (22, "V_BCKP", "power_in"), (9, "VCC_RF", "power_out"), None,
         (8, "RESET_N", "input"), (1, "SAFEBOOT_N", "input"), (4, "EXTINT", "input"), (14, "LNA_EN", "output")]
    R = [(11, "RF_IN", "input"), None, (20, "TXD", "output"), (21, "RXD", "input"), (3, "TIMEPULSE", "output"), None,
         (2, "RSV", "no_connect"), (5, "RSV", "no_connect"), (6, "RSV", "no_connect"), (7, "RSV", "no_connect"),
         (15, "RSV", "no_connect"), (16, "RSV", "no_connect"), (17, "RSV", "no_connect"), (18, "RSV", "no_connect"),
         (19, "RSV", "no_connect")]
    return box_symbol("NEO-F10N", "U", "RF_GPS:ublox_NEO", "https://www.u-blox.com/en/product/neo-f10n-module",
                      "u-blox L1/L5 dual-band GNSS module with NavIC, NEO form factor 12.2x16 mm", L, R, [10, 12, 13, 24])


def main():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "rfmw_make_lib"],
           [Sym("generator_version"), "9.0"], sim7080g(), neo_f10n()]
    open(OUT, "w").write(dump(lib) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- footprint
# Pad geometry taken from an open, fabricated SIM7080G carrier (github.com/dgtecwise/sim7080_dev_board)
# and cross-checked against SIMCom HD V1.04 fig.4: 1.10 mm outer pitch, 1.40 mm inner pitch,
# 2.60 x 3.10 mm centre pads, 17.60 x 15.70 mm body, 18.30 x 20.20 mm stand-off outline.
def sim7080g_pads():
    pads = []
    for i in range(12):                       # 1..12 left, top->bottom
        pads.append((1 + i, -7.85, -6.05 + 1.1 * i, 1.6, 0.6))
    for i in range(9):                        # 13..21 bottom, left->right
        pads.append((13 + i, -4.4 + 1.1 * i, 8.8, 0.6, 1.6))
    for i in range(12):                       # 22..33 right, bottom->top
        pads.append((22 + i, 7.85, 6.05 - 1.1 * i, 1.6, 0.6))
    for i in range(9):                        # 34..42 top, right->left
        pads.append((34 + i, 4.4 - 1.1 * i, -8.8, 0.6, 1.6))
    for i in range(8):                        # 43..50 inner left column
        pads.append((43 + i, -5.35, -4.9 + 1.4 * i, 1.1, 0.9))
    for i in range(7):                        # 51..57 inner bottom row
        pads.append((51 + i, -4.2 + 1.4 * i, 6.3, 0.9, 1.1))
    for i in range(5):                        # 58..62 inner right column
        pads.append((58 + i, 5.35, 4.9 - 1.4 * i, 1.1, 0.9))
    for i in range(6):                        # 63..68 inner top row
        pads.append((63 + i, 2.8 - 1.4 * i, -6.3, 0.9, 1.1))
    pads.append((69, -2.9, -3.4, 1.0, 1.0))
    centre = {70: (-2.9, 0.0), 71: (-2.9, 3.4), 72: (0.0, 3.4), 73: (2.9, 3.4), 74: (2.9, 0.0),
              75: (2.9, -3.4), 76: (0.0, -3.4), 77: (0.0, 0.0)}
    for n, (x, y) in centre.items():
        pads.append((n, x, y, 2.6, 3.1))
    return pads


def fp_line(x1, y1, x2, y2, layer, w):
    return [Sym("fp_line"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("layer"), layer]]


def fp_rect(x1, y1, x2, y2, layer, w):
    return [Sym("fp_rect"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym("no")], [Sym("layer"), layer]]


def fp_text(kind, txt, x, y, layer, hide=False):
    t = [Sym("property"), kind, txt, [Sym("at"), x, y, 0], [Sym("layer"), layer]]
    if hide:
        t.append([Sym("hide"), Sym("yes")])
    t.append([Sym("effects"), [Sym("font"), [Sym("size"), 1, 1], [Sym("thickness"), 0.15]]])
    return t


def sim7080g_fp():
    W, H = 15.7 / 2, 17.6 / 2
    fp = [Sym("footprint"), "SIMCom_SIM7080G_LCC-77", [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"],
          [Sym("descr"), "SIMCom SIM7080G LCC-77, 17.6x15.7mm. Pads per open SIM7080G carrier, checked vs SIMCom HD V1.04 fig.4"],
          [Sym("tags"), "SIM7080G LTE-M NB-IoT LCC"],
          fp_text("Reference", "REF**", 0, -11.2, "F.SilkS"), fp_text("Value", "SIM7080G", 0, 11.2, "F.Fab"),
          [Sym("attr"), Sym("smd")]]
    # fab body with pin-1 chamfer
    c = 1.0
    pts = [(-W + c, -H), (W, -H), (W, H), (-W, H), (-W, -H + c), (-W + c, -H)]
    for a, b in zip(pts, pts[1:]):
        fp.append(fp_line(a[0], a[1], b[0], b[1], "F.Fab", 0.1))
    # silk corner marks outside the pad ring
    sx, sy = 9.0, 9.95
    for xs in (-1, 1):
        for ys in (-1, 1):
            fp.append(fp_line(xs * sx, ys * sy, xs * (sx - 1.2), ys * sy, "F.SilkS", 0.12))
            fp.append(fp_line(xs * sx, ys * sy, xs * sx, ys * (sy - 1.2), "F.SilkS", 0.12))
    fp.append([Sym("fp_circle"), [Sym("center"), -9.6, -6.05], [Sym("end"), -9.35, -6.05],
               [Sym("stroke"), [Sym("width"), 0.5], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym("yes")], [Sym("layer"), "F.SilkS"]])
    fp.append(fp_rect(-9.15, -10.1, 9.15, 10.1, "F.CrtYd", 0.05))
    for n, x, y, w, h in sim7080g_pads():
        pad = [Sym("pad"), str(n), Sym("smd"), Sym("rect"), [Sym("at"), round(x, 3), round(y, 3)], [Sym("size"), w, h],
               [Sym("layers"), "F.Cu", "F.Paste", "F.Mask"]]
        if n >= 70:
            pad.append([Sym("solder_paste_margin_ratio"), -0.25])   # ~56 % paste on large GND pads
        fp.append(pad)
    # SIMCom "forbidden area" (hatched, upper right inside the pad ring): no copper on F.Cu
    fp.append([Sym("zone"), [Sym("net"), 0], [Sym("net_name"), ""], [Sym("layers"), "F.Cu"], [Sym("name"), "SIMCOM_FORBIDDEN"],
               [Sym("hatch"), Sym("edge"), 0.5], [Sym("connect_pads"), [Sym("clearance"), 0]], [Sym("min_thickness"), 0.25],
               [Sym("filled_areas_thickness"), Sym("no")],
               [Sym("keepout"), [Sym("tracks"), Sym("not_allowed")], [Sym("vias"), Sym("not_allowed")], [Sym("pads"), Sym("allowed")],
                [Sym("copperpour"), Sym("not_allowed")], [Sym("footprints"), Sym("allowed")]],
               [Sym("fill"), [Sym("thermal_gap"), 0.5], [Sym("thermal_bridge_width"), 0.5]],
               [Sym("polygon"), [Sym("pts"), [Sym("xy"), 5.9, -7.9], [Sym("xy"), 6.95, -7.9], [Sym("xy"), 6.95, -4.6], [Sym("xy"), 5.9, -4.6]]]])
    return fp


def write_fp():
    d = os.path.join(HERE, "..", "01_kicad", "tracker.pretty")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "SIMCom_SIM7080G_LCC-77.kicad_mod"), "w").write(dump(sim7080g_fp()) + "\n")


if __name__ == "__main__":
    write_fp()
    print("footprint written")
