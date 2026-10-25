"""SPS-24G-01 project library: the MOC3063 opto-triac symbol and four custom footprints
(TR5 radial fuse, 14 mm MOV disc, 9 mm NTC disc, LD2410B radar module header).

Everything else uses stock KiCad 9 symbols / footprints (HLK-PM01, BTA16-600B, ATtiny13A-SS, DIP-6,
screw terminal, trimmer, tactile switch, film / electrolytic caps).
"""
import os
from sexp import Sym, dump

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(HERE, "..", "01_kicad")
OUT = os.path.join(KDIR, "bps_switch.kicad_sym")


# ------------------------------------------------------------------- symbol helpers
def prop(k, v, x, y, hide=False, size=1.27):
    p = [Sym("property"), k, v, [Sym("at"), x, y, 0], [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]]
    if hide:
        p[-1].append([Sym("hide"), Sym("yes")])
    return p


def pin(num, name, etype, x, y, ang, length=2.54):
    return [Sym("pin"), Sym(etype), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), length],
            [Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.016, 1.016]]]],
            [Sym("number"), str(num), [Sym("effects"), [Sym("font"), [Sym("size"), 1.016, 1.016]]]]]


def moc3063():
    """6-pin zero-cross opto-triac driver. 1=anode 2=cathode (SELV input); 6,4=main terminals (mains output);
    3,5 = NC. Body is a rectangle with the isolation gap shown as a dashed line down the middle."""
    name = "MOC3063"
    w, h = 10.16, 7.62
    items = [
        pin(1, "ANODE", "passive", -w / 2 - 2.54, 2.54, 0),
        pin(2, "CATHODE", "passive", -w / 2 - 2.54, -2.54, 0),
        pin(6, "MT", "passive", w / 2 + 2.54, 2.54, 180),
        pin(4, "MT", "passive", w / 2 + 2.54, -2.54, 180),
        pin(3, "NC", "no_connect", -w / 2 - 2.54, 0, 0),
        pin(5, "NC", "no_connect", w / 2 + 2.54, 0, 180),
    ]
    body = [Sym("symbol"), f"{name}_0_1",
            [Sym("rectangle"), [Sym("start"), -w / 2, h / 2], [Sym("end"), w / 2, -h / 2],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
             [Sym("fill"), [Sym("type"), Sym("background")]]],
            # isolation barrier (dashed centre line)
            [Sym("polyline"), [Sym("pts"), [Sym("xy"), 0, h / 2 - 0.6], [Sym("xy"), 0, -h / 2 + 0.6]],
             [Sym("stroke"), [Sym("width"), 0.2], [Sym("type"), Sym("dash")]], [Sym("fill"), [Sym("type"), Sym("none")]]]]
    return [Sym("symbol"), name, [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")],
            [Sym("on_board"), Sym("yes")],
            prop("Reference", "U", 0, h / 2 + 1.27), prop("Value", name, 0, -h / 2 - 1.27),
            prop("Footprint", "Package_DIP:DIP-6_W7.62mm", 0, 0, True),
            prop("Datasheet", "https://www.onsemi.com/pdf/datasheet/moc3061m-d.pdf", 0, 0, True),
            prop("Description", "Zero-cross opto-triac driver, 600 V, 7.5 kVrms isolation, DIP-6", 0, 0, True),
            body, [Sym("symbol"), f"{name}_1_1"] + items]


# ------------------------------------------------------------------- footprint helpers
def fp_line(x1, y1, x2, y2, layer, w):
    return [Sym("fp_line"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("layer"), layer]]


def fp_circle(cx, cy, r, layer, w, fill="no"):
    return [Sym("fp_circle"), [Sym("center"), cx, cy], [Sym("end"), cx + r, cy],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym(fill)], [Sym("layer"), layer]]


def fp_rect(x1, y1, x2, y2, layer, w, fill="no"):
    return [Sym("fp_rect"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym(fill)], [Sym("layer"), layer]]


def fp_text(kind, txt, x, y, layer, hide=False, size=1.0):
    t = [Sym("property"), kind, txt, [Sym("at"), x, y, 0], [Sym("layer"), layer]]
    if hide:
        t.append([Sym("hide"), Sym("yes")])
    t.append([Sym("effects"), [Sym("font"), [Sym("size"), size, size], [Sym("thickness"), 0.15]]])
    return t


def fp_usertext(txt, x, y, layer, size=0.8):
    return [Sym("fp_text"), Sym("user"), txt, [Sym("at"), x, y, 0], [Sym("layer"), layer],
            [Sym("effects"), [Sym("font"), [Sym("size"), size, size], [Sym("thickness"), size * 0.15]]]]


def tht_pad(n, x, y, drill, dia, shape="circle"):
    p = [Sym("pad"), str(n), Sym("thru_hole"), Sym(shape), [Sym("at"), x, y], [Sym("size"), dia, dia],
         [Sym("drill"), drill], [Sym("layers"), "*.Cu", "*.Mask"]]
    if shape == "rect":
        p.append([Sym("roundrect_rratio"), 0])
    return p


def header(name, descr, tags, pitch, drill, dia, x, y, w, h):
    """generic header footprint body; pads filled by caller"""
    fp = [Sym("footprint"), name, [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"], [Sym("descr"), descr], [Sym("tags"), tags],
          fp_text("Reference", "REF**", 0, y - 1.4, "F.SilkS"), fp_text("Value", name, 0, y + h + 1.0, "F.Fab"),
          [Sym("attr"), Sym("through_hole")]]
    return fp


def disc_fp(name, descr, tags, pitch, drill, dia, disc_d, body_w):
    """two-lead radial disc (MOV / NTC / film) along x, leads at +-pitch/2, body circle of disc_d."""
    fp = [Sym("footprint"), name, [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"], [Sym("descr"), descr], [Sym("tags"), tags],
          fp_text("Reference", "REF**", 0, -disc_d / 2 - 1.2, "F.SilkS"),
          fp_text("Value", name, 0, disc_d / 2 + 1.2, "F.Fab"), [Sym("attr"), Sym("through_hole")]]
    fp.append(fp_circle(0, 0, disc_d / 2, "F.Fab", 0.1))
    fp.append(fp_circle(0, 0, disc_d / 2 + 0.2, "F.SilkS", 0.12))
    cr = disc_d / 2 + 0.5
    fp.append(fp_rect(-cr, -cr, cr, cr, "F.CrtYd", 0.05))
    fp.append(tht_pad(1, -pitch / 2, 0, drill, dia, "rect"))
    fp.append(tht_pad(2, pitch / 2, 0, drill, dia))
    return fp


def fuse_tr5():
    """TR5 (sub-miniature radial cartridge) time-lag fuse, 5.08 mm pitch, ~7.5 x 7.3 mm body."""
    name = "Fuse_TR5_P5.08mm"
    bw, bh = 7.6, 7.3
    fp = [Sym("footprint"), name, [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"], [Sym("descr"), "TR5 radial time-lag fuse, 5.08 mm lead pitch (382/372 series)"],
          [Sym("tags"), "fuse TR5 radial time-lag mains"],
          fp_text("Reference", "REF**", 0, -bh / 2 - 1.2, "F.SilkS"),
          fp_text("Value", name, 0, bh / 2 + 1.2, "F.Fab"), [Sym("attr"), Sym("through_hole")]]
    fp.append(fp_rect(-bw / 2, -bh / 2, bw / 2, bh / 2, "F.Fab", 0.1))
    fp.append(fp_rect(-bw / 2 - 0.2, -bh / 2 - 0.2, bw / 2 + 0.2, bh / 2 + 0.2, "F.SilkS", 0.12))
    fp.append(fp_rect(-bw / 2 - 0.4, -bh / 2 - 0.4, bw / 2 + 0.4, bh / 2 + 0.4, "F.CrtYd", 0.05))
    fp.append(tht_pad(1, -5.08 / 2, 0, 0.9, 1.7, "rect"))
    fp.append(tht_pad(2, 5.08 / 2, 0, 0.9, 1.7))
    return fp


def ld2410b():
    """LD2410B 24 GHz radar carried on a 5-pin 1.27 mm header at the board edge.
    Pads 1..5 in a row (OUT, TX, RX, GND, VCC), 1.27 mm pitch. The 7 x 35 mm module mounts VERTICALLY on
    this header (stands perpendicular to the main PCB), antenna facing the front cover - so only its ~7 x 2 mm
    edge sits on the board. Two 1.1 mm brace holes support it. The no-copper antenna keep-out is added in
    make_pcb over the area in front of the standing module."""
    name = "LD2410B_Module"
    pitch = 1.27
    x0 = -2 * pitch
    fp = [Sym("footprint"), name, [Sym("version"), 20241229], [Sym("generator"), "rfmw_make_lib"],
          [Sym("layer"), "F.Cu"],
          [Sym("descr"), "Hi-Link HLK-LD2410B 24 GHz presence radar on a vertical 5-pin 1.27 mm header"],
          [Sym("tags"), "LD2410B radar 24GHz mmwave presence Hi-Link"],
          fp_text("Reference", "REF**", 0, -2.2, "F.SilkS"),
          fp_text("Value", name, 0, 3.6, "F.Fab"), [Sym("attr"), Sym("through_hole")]]
    names = ["OUT", "TX", "RX", "GND", "VCC"]
    for i in range(5):
        x = x0 + i * pitch
        fp.append(tht_pad(i + 1, x, 0, 0.55, 0.95, "rect" if i == 0 else "circle"))
        fp.append(fp_usertext(names[i], x, 1.6, "F.SilkS", 0.5))
    # the module stands on the header; its 7 mm-wide edge sits at y=0, antenna points +y (toward the cover)
    bw = 7.6
    fp.append(fp_rect(-bw / 2, -1.0, bw / 2, 0.8, "F.Fab", 0.1))
    fp.append(fp_line(-bw / 2, -1.0, bw / 2, -1.0, "F.SilkS", 0.12))
    fp.append(fp_usertext("LD2410B vertical - ANT faces cover", 0, -2.0, "F.Fab", 0.7))
    fp.append(fp_rect(-bw / 2 - 0.3, -1.4, bw / 2 + 0.3, 2.1, "F.CrtYd", 0.05))
    return fp


LIBTAB_SYM = ('(sym_lib_table\n\t(version 7)\n\t(lib (name "bps")(type "KiCad")(uri "${KIPRJMOD}/bps_switch.kicad_sym")'
              '(options "")(descr "SPS-24G-01 project symbols"))\n)\n')
LIBTAB_FP = ('(fp_lib_table\n\t(version 7)\n\t(lib (name "bps")(type "KiCad")(uri "${KIPRJMOD}/bps.pretty")'
             '(options "")(descr "SPS-24G-01 project footprints"))\n)\n')


def main():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "rfmw_make_lib"],
           [Sym("generator_version"), "9.0"], moc3063()]
    open(OUT, "w").write(dump(lib) + "\n")
    d = os.path.join(KDIR, "bps.pretty")
    os.makedirs(d, exist_ok=True)
    fps = {
        "Fuse_TR5_P5.08mm": fuse_tr5(),
        "Varistor_Disc_D16mm_P7.5mm": disc_fp("Varistor_Disc_D16mm_P7.5mm", "MOV disc 14 mm class (D16 body), 7.5 mm leads",
                                              "varistor MOV disc mains", 7.5, 1.0, 1.9, 16.0, 16.0),
        "NTC_Disc_D11mm_P5mm": disc_fp("NTC_Disc_D11mm_P5mm", "NTC inrush disc 5D-9 (9 mm class, D11 body), 5 mm leads",
                                       "NTC thermistor inrush disc", 5.0, 0.9, 1.7, 11.0, 11.0),
        "LD2410B_Module": ld2410b(),
    }
    for n, fp in fps.items():
        open(os.path.join(d, n + ".kicad_mod"), "w").write(dump(fp) + "\n")
    open(os.path.join(KDIR, "sym-lib-table"), "w").write(LIBTAB_SYM)
    open(os.path.join(KDIR, "fp-lib-table"), "w").write(LIBTAB_FP)
    print("wrote", OUT, "and bps.pretty:", ", ".join(fps))


if __name__ == "__main__":
    main()
