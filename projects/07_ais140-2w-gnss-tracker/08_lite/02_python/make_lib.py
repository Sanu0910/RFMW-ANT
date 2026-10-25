"""Lite project library: symbols for EC200U, L76K, XL1509 and the EC200U land pattern.

EC200U pin numbers: Quectel EC200U Series Hardware Design (EC2x-compatible LCC table), confirmed for the
pins used here from search excerpts of V1.0 / V1.2: VBAT_RF 57/58, VBAT_BB 59/60, PWRKEY 21, RESET_N 20,
ANT_MAIN 49, USIM 14-17, STATUS 61, NET_STATUS 6, MAIN_RI 62, MAIN_DTR 66, MAIN_TXD 67, I2C 41/42, ADC 44/45,
GPIO1-4 = 27/26/24/25 (QuecPython machine.Pin). The rest (VDD_EXT 7, MAIN_RXD 68, USB 69-71, DBG 11/12,
GND list) follow the EC2x family table - VERIFY.

EC200U land pattern: PARAMETRIC RECONSTRUCTION (28.0 x 31.0 mm body, 80 LCC + 64 LGA pads). The real pad
pitch / size / LGA positions are in the Hardware Design "Recommended Footprint" figure, which could not be
downloaded. Replace lite.pretty/Quectel_EC200U_LCC-144.kicad_mod with the vendor land pattern before fab.

L76K: Quectel L76 family LCC-18 (stock KiCad RF_GPS:Quectel_L76 footprint), pins 1/10/12 GND, 2 TXD,
3 RXD, 4 1PPS, 6 V_BCKP, 8 VCC, 9 RESET_N, 11 RF_IN, 14 VCC_RF (L76K: VDD_RF) - VERIFY vs L76K HD V1.0.
"""
import os
from sexp import Sym, dump

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(HERE, "..", "01_kicad")
OUT = os.path.join(KDIR, "tracker_lite.kicad_sym")

EC200U = {
    6: ("NET_STATUS", "output"), 7: ("VDD_EXT", "power_out"), 11: ("DBG_RXD", "input"), 12: ("DBG_TXD", "output"),
    13: ("USIM_PRESENCE", "input"), 14: ("USIM_VDD", "power_out"), 15: ("USIM_DATA", "bidirectional"),
    16: ("USIM_CLK", "output"), 17: ("USIM_RST", "output"), 10: ("USIM_GND", "passive"),
    20: ("RESET_N", "input"), 21: ("PWRKEY", "input"), 24: ("GPIO3", "bidirectional"), 25: ("GPIO4", "bidirectional"),
    26: ("GPIO2", "bidirectional"), 27: ("GPIO1", "bidirectional"), 41: ("I2C_SCL", "bidirectional"),
    42: ("I2C_SDA", "bidirectional"), 44: ("ADC1", "input"), 45: ("ADC0", "input"), 49: ("ANT_MAIN", "bidirectional"),
    57: ("VBAT_RF", "power_in"), 58: ("VBAT_RF", "passive"), 59: ("VBAT_BB", "power_in"), 60: ("VBAT_BB", "passive"),
    61: ("STATUS", "output"), 62: ("MAIN_RI", "output"), 63: ("MAIN_DCD", "output"), 64: ("MAIN_CTS", "output"),
    65: ("MAIN_RTS", "input"), 66: ("MAIN_DTR", "input"), 67: ("MAIN_TXD", "output"), 68: ("MAIN_RXD", "input"),
    69: ("USB_DP", "bidirectional"), 70: ("USB_DM", "bidirectional"), 71: ("USB_VBUS", "input"),
}
EC_GND = [8, 9, 19, 22, 36, 46, 48, 50, 51, 52, 53, 54, 56, 72] + list(range(85, 113))
EC_NC = [n for n in range(1, 145) if n not in EC200U and n not in EC_GND]


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


def box_symbol(name, ref, fp, ds, desc, left, right, bottom_gnd=(), top=(), w=20.32, nc=()):
    """left/right: list of (num,name,type) or None for gap. GND pins stacked on one bottom pin, NC pins stacked
    (hidden) on one bottom-left pin."""
    rows = max(len(left), len(right))
    h = (rows + 1) * 2.54
    y0 = h / 2
    items = []

    def place(lst, side):
        for i, e in enumerate(lst):
            if e is None:
                continue
            n, nm, t = e
            y = round((y0 - 2.54 * (i + 1)) / 2.54) * 2.54
            items.append(pin(n, nm, t, (-w / 2 - 2.54) if side == "L" else (w / 2 + 2.54), y, 0 if side == "L" else 180))
    place(left, "L"); place(right, "R")
    ybot = round((-y0 - 2.54) / 2.54) * 2.54
    for k, n in enumerate(bottom_gnd):
        items.append(pin(n, "GND", "power_in" if k == 0 else "passive", 0, ybot, 90, hidden=k > 0))
    for k, n in enumerate(nc):
        items.append(pin(n, "NC", "no_connect", -w / 2 + 2.54, ybot, 90, hidden=k > 0))
    xt = -((len(top) - 1) * 2.54) / 2
    ytop = round((y0 + 2.54) / 2.54) * 2.54
    for k, e in enumerate(top):
        n, nm, t = e
        items.append(pin(n, nm, t, round((xt + k * 2.54) / 1.27) * 1.27, ytop, 270))
    body = [Sym("symbol"), f"{name}_0_1",
            [Sym("rectangle"), [Sym("start"), -w / 2, ybot + 2.54], [Sym("end"), w / 2, ytop - 2.54],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("background")]]]]
    return [Sym("symbol"), name, [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            prop("Reference", ref, 0, ytop + 1.27), prop("Value", name, 0, ybot - 1.27),
            prop("Footprint", fp, 0, 0, True), prop("Datasheet", ds, 0, 0, True), prop("Description", desc, 0, 0, True),
            body, [Sym("symbol"), f"{name}_1_1"] + items]


def ec200u():
    f = lambda lst: [None if n is None else (n, EC200U[n][0], EC200U[n][1]) for n in lst]
    L = [67, 68, 62, 66, 63, 64, 65, None, 12, 11, None, 41, 42, None, 45, 44, None, 27, 26, 24, 25]
    R = [49, None, 14, 15, 16, 17, 13, 10, None, 69, 70, 71, None, 21, 20, 61, 6]
    top = [(57, "VBAT_RF", "power_in"), (58, "VBAT_RF", "passive"), (59, "VBAT_BB", "power_in"),
           (60, "VBAT_BB", "passive"), (7, "VDD_EXT", "power_out")]
    return box_symbol("EC200U", "U", "lite:Quectel_EC200U_LCC-144", "https://www.quectel.com/product/lte-ec200u-series/",
                      "Quectel EC200U LTE Cat-1 bis + GSM module, LCC+LGA 144 pads, 28.0 x 31.0 x 2.4 mm",
                      f(L), f(R), EC_GND, top, w=25.4, nc=EC_NC)


def l76k():
    L = [(8, "VCC", "power_in"), (6, "V_BCKP", "power_in"), (14, "VCC_RF", "power_out"), None, (9, "RESET_N", "input")]
    R = [(11, "RF_IN", "input"), None, (2, "TXD", "output"), (3, "RXD", "input"), (4, "1PPS", "output")]
    return box_symbol("L76K", "U", "lite:Quectel_L76K", "https://www.quectel.com/product/gnss-l76k/",
                      "Quectel L76K GPS/BDS/GLONASS/QZSS module, LCC-18 10.1 x 9.7 mm", L, R, [1, 10, 12],
                      nc=[5, 7, 13, 15, 16, 17, 18])


def mff2():
    L = [(8, "VCC", "power_in"), (7, "RST", "input"), (6, "CLK", "input"), (3, "I/O", "bidirectional")]
    R = [(2, "VPP", "no_connect"), (4, "NC", "no_connect"), (5, "NC", "no_connect")]
    return box_symbol("MFF2_eSIM", "U", "lite:MFF2_eSIM_DFN-8_6x5mm", "https://www.etsi.org/deliver/etsi_ts/102600_102699/102671/",
                      "Embedded UICC / M2M SIM, ETSI TS 102 671 MFF2 (DFN-8 6 x 5 mm)", L, R, [1], w=12.7)


def xl1509():
    L = [(1, "VIN", "power_in"), None, (5, "EN", "input")]
    R = [(2, "SW", "power_out"), None, (4, "FB", "input")]
    return box_symbol("XL1509-ADJ", "U", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "https://www.xlsemi.com/",
                      "XLSEMI 40 V 2 A 150 kHz buck converter, adjustable, SOP-8", L, R, [3, 6, 7, 8], w=15.24)


# ---------------------------------------------------------------- footprint
BODY_W, BODY_H = 28.0, 31.0
PITCH = 1.0                      # VERIFY: LCC pad pitch
PAD_L, PAD_W = 1.8, 0.7          # VERIFY: LCC pad length (radial) x width


def ec200u_pads():
    """(num, x, y, w, h). LCC 1-24 left (top->bottom), 25-40 bottom (left->right), 41-64 right (bottom->top),
    65-80 top (right->left); LGA 81-144 an 8 x 8 grid, row-major from top-left."""
    pads = []
    xs = BODY_W / 2 - PAD_L / 2 + 0.2          # pads overhang the body edge by 0.2 mm
    ys = BODY_H / 2 - PAD_L / 2 + 0.2
    for i in range(24):
        pads.append((1 + i, -xs, -11.5 + PITCH * i, PAD_L, PAD_W))
    for i in range(16):
        pads.append((25 + i, -7.5 + PITCH * i, ys, PAD_W, PAD_L))
    for i in range(24):
        pads.append((41 + i, xs, 11.5 - PITCH * i, PAD_L, PAD_W))
    for i in range(16):
        pads.append((65 + i, 7.5 - PITCH * i, -ys, PAD_W, PAD_L))
    for k in range(64):
        r, c = divmod(k, 8)
        pads.append((81 + k, -7.7 + 2.2 * c, -7.7 + 2.2 * r, 1.0, 1.0))
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


def ec200u_fp():
    W, H = BODY_W / 2, BODY_H / 2
    fp = [Sym("footprint"), "Quectel_EC200U_LCC-144", [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"],
          [Sym("descr"), "Quectel EC200U LCC 80 + LGA 64, 28.0x31.0 mm. PARAMETRIC RECONSTRUCTION - replace with the "
                         "Quectel EC200U Hardware Design recommended footprint before fabrication"],
          [Sym("tags"), "EC200U Cat-1 LTE GSM LCC LGA Quectel"],
          fp_text("Reference", "REF**", 0, -H - 1.6, "F.SilkS"), fp_text("Value", "EC200U", 0, H + 1.6, "F.Fab"),
          [Sym("attr"), Sym("smd")]]
    c = 1.0
    pts = [(-W + c, -H), (W, -H), (W, H), (-W, H), (-W, -H + c), (-W + c, -H)]
    for a, b in zip(pts, pts[1:]):
        fp.append(fp_line(a[0], a[1], b[0], b[1], "F.Fab", 0.1))
    sx, sy = W + 0.45, H + 0.45
    for xs in (-1, 1):
        for ys in (-1, 1):
            fp.append(fp_line(xs * sx, ys * sy, xs * (sx - 1.5), ys * sy, "F.SilkS", 0.12))
            fp.append(fp_line(xs * sx, ys * sy, xs * sx, ys * (sy - 1.5), "F.SilkS", 0.12))
    fp.append([Sym("fp_circle"), [Sym("center"), -W - 1.0, -11.5], [Sym("end"), -W - 0.75, -11.5],
               [Sym("stroke"), [Sym("width"), 0.5], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym("yes")], [Sym("layer"), "F.SilkS"]])
    fp.append(fp_rect(-W - 0.6, -H - 0.6, W + 0.6, H + 0.6, "F.CrtYd", 0.05))
    for n, x, y, w, h in ec200u_pads():
        pad = [Sym("pad"), str(n), Sym("smd"), Sym("rect"), [Sym("at"), round(x, 3), round(y, 3)], [Sym("size"), w, h],
               [Sym("layers"), "F.Cu", "F.Paste", "F.Mask"]]
        if n > 80:
            pad.append([Sym("solder_paste_margin_ratio"), -0.2])
        fp.append(pad)
    return fp


STOCK = "/opt/kicad9/usr/share/kicad/footprints"


def derived_fps(d):
    """Stock footprints adapted for this board:
    Quectel_L76K   = RF_GPS:Quectel_L76 with a body-sized courtyard (stock one is 17.5 x 16.1 mm)
    MFF2_eSIM      = Package_SON:WSON-8-1EP_6x5mm_P1.27mm without the exposed pad (MFF2 has none) - VERIFY
                     the land pattern against the eSIM vendor's drawing (ETSI TS 102 671 MFF2)."""
    from sexp import parse, find
    l76 = parse(open(os.path.join(STOCK, "RF_GPS.pretty", "Quectel_L76.kicad_mod")).read())[0]
    l76[1] = "Quectel_L76K"
    for r in find(l76, "fp_rect"):
        lay = [e for e in r if isinstance(e, list) and e[0] == "layer"][0][1]
        if lay == "F.CrtYd":
            for e in r:
                if isinstance(e, list) and e[0] == "start":
                    e[1], e[2] = -6.05, -5.4
                if isinstance(e, list) and e[0] == "end":
                    e[1], e[2] = 6.05, 5.4
    open(os.path.join(d, "Quectel_L76K.kicad_mod"), "w").write(dump(l76) + "\n")
    w = parse(open(os.path.join(STOCK, "Package_SON.pretty", "WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm.kicad_mod")).read())[0]
    w[1] = "MFF2_eSIM_DFN-8_6x5mm"
    w[:] = [e for e in w if not (isinstance(e, list) and e and e[0] == "pad" and e[1] in ("", "9"))]
    for e in w:
        if isinstance(e, list) and e and e[0] == "descr":
            e[1] = "MFF2 embedded SIM (ETSI TS 102 671), DFN-8 6x5 mm P1.27, no exposed pad"
    open(os.path.join(d, "MFF2_eSIM_DFN-8_6x5mm.kicad_mod"), "w").write(dump(w) + "\n")


def main():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "rfmw_make_lib"],
           [Sym("generator_version"), "9.0"], ec200u(), l76k(), mff2(), xl1509()]
    open(OUT, "w").write(dump(lib) + "\n")
    d = os.path.join(KDIR, "lite.pretty")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "Quectel_EC200U_LCC-144.kicad_mod"), "w").write(dump(ec200u_fp()) + "\n")
    derived_fps(d)
    open(os.path.join(KDIR, "sym-lib-table"), "w").write(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "lite")(type "KiCad")(uri "${KIPRJMOD}/tracker_lite.kicad_sym")'
        '(options "")(descr "CRL-TRK-2W-L1 project symbols"))\n)\n')
    open(os.path.join(KDIR, "fp-lib-table"), "w").write(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "lite")(type "KiCad")(uri "${KIPRJMOD}/lite.pretty")'
        '(options "")(descr "CRL-TRK-2W-L1 project footprints"))\n)\n')
    print("wrote", OUT, "and lite.pretty")


if __name__ == "__main__":
    main()
