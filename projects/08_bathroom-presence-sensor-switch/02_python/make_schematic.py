"""Generate the hierarchical KiCad 9 schematic from design.py.

Each pin gets a short wire stub and a global label carrying its net name (GND uses the power symbol),
so connectivity is explicit, ERC-checkable and identical to the PCB netlist. Parts that belong to the
same functional group are clustered; clusters are shelf-packed on each sheet.
"""
import math, os, uuid
from sexp import Sym, dump, find, first
import design as D
from libsym import get_symbol, pins, prop

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(HERE, "..", "01_kicad")
EXTRA = {D.LIB: os.path.join(KDIR, f"{D.PROJECT}.kicad_sym")}
NS = uuid.UUID("c18f2320-60d1-4010-958c-690db1c75e12")
G = 1.27


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


ROOT_UUID = U("root")
SHEET_UUID = {s: U("sheet", s) for s in D.SHEETS}


def snap(v, g=G):
    return round(v / g) * g


def eff(size=1.27, justify=None, hide=False):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


def text_len(t):
    return 1.05 * len(t) + 2.5


DIRV = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}   # sheet coords (Y down)


class Placed:
    def __init__(self, p):
        self.p = p
        self.sym = get_symbol(p["lib"], EXTRA)
        self.pins = pins(self.sym)
        self.power = p["lib"].startswith("power:") and "PWR_FLAG" not in p["lib"]
        self.flag = "PWR_FLAG" in p["lib"]
        # body bbox from graphics
        xs, ys = [], []
        def walk(n):
            if isinstance(n, list):
                if n and n[0] in ("xy", "start", "end", "center") and len(n) >= 3:
                    try:
                        xs.append(float(n[1])); ys.append(-float(n[2]))
                    except (TypeError, ValueError):
                        pass
                for e in n:
                    walk(e)
        for sub in find(self.sym, "symbol"):
            for g in sub:
                if isinstance(g, list) and g[0] in ("rectangle", "polyline", "circle", "arc"):
                    walk(g)
        for pn in self.pins:
            xs.append(pn[2]); ys.append(-pn[3])
        if not xs:
            xs, ys = [0], [0]
        self.bb = [min(xs) - 1, min(ys) - 3, max(xs) + 1, max(ys) + 3]
        # pins grouped by location (stacked pins share one stub)
        self.stubs = []
        seen = {}
        for num, name, x, y, ang, ln, et, unit in self.pins:
            key = (round(x, 3), round(y, 3))
            net = p["nets"].get(num, None)
            if key in seen:
                prev = seen[key]
                if net and prev["net"] and net != prev["net"]:
                    raise ValueError(f"{p['ref']}: stacked pins {prev['num']}/{num} on different nets")
                prev["net"] = prev["net"] or net
                continue
            outward = int((ang + 180) % 360)
            st = dict(num=num, x=x, y=-y, dir=outward, net=net, etype=et)
            seen[key] = st
            self.stubs.append(st)
        for st in self.stubs:
            if self.power:
                continue
            dx, dy = DIRV[st["dir"]]
            n = st["net"] or ""
            L = 2.54 + (text_len(n) if n and n != "GND" else 4)
            ex, ey = st["x"] + dx * L, st["y"] + dy * L
            self.bb[0] = min(self.bb[0], ex - (1.5 if dx == 0 else 0)); self.bb[2] = max(self.bb[2], ex + (1.5 if dx == 0 else 0))
            self.bb[1] = min(self.bb[1], ey - (1.5 if dy == 0 else 0)); self.bb[3] = max(self.bb[3], ey + (1.5 if dy == 0 else 0))
        if len(self.stubs) == 2 and all(st["dir"] in (90, 270) for st in self.stubs) and not self.power:
            self.bb[2] = max(self.bb[2], 2.54 + 1.1 * max(len(p["ref"]), len(p["value"])) + 1.5)
        self.w = self.bb[2] - self.bb[0]
        self.h = self.bb[3] - self.bb[1]


def layout(items, page_w, x0, y0, gap=10.0):
    """Shelf-pack clusters (lists of Placed). Returns placements {id: (ox, oy)} and used height."""
    clusters = []
    for cl in items:
        cx = 0.0; ch = 0.0; pos = []
        for pl in cl:
            pos.append((pl, cx - pl.bb[0], -pl.bb[1]))
            cx += pl.w + 4.0
            ch = max(ch, pl.h)
        clusters.append((cx - 4.0, ch, pos))
    out = {}
    x, y, shelf = x0, y0, 0.0
    for w, h, pos in clusters:
        if x + w > x0 + page_w and x > x0:
            x = x0; y += shelf + gap; shelf = 0.0
        for pl, ox, oy in pos:
            out[id(pl)] = (snap(x + ox), snap(y + oy))
        x += w + gap
        shelf = max(shelf, h)
    return out, y + shelf - y0


PAPERS = [("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594)]


class Sheet:
    def __init__(self, key, title, page_no, pwr_counter):
        self.key, self.title, self.page = key, title, page_no
        self.items = []
        self.libs = {}
        self.pwr = pwr_counter
        self.path = f"/{ROOT_UUID}/{SHEET_UUID[key]}" if key in SHEET_UUID else f"/{ROOT_UUID}"

    def add_lib(self, sym):
        self.libs.setdefault(sym[1], sym)

    def symbol(self, pl, x, y):
        p = pl.p
        self.add_lib(pl.sym)
        ref = p["ref"]
        s = [Sym("symbol"), [Sym("lib_id"), p["lib"]], [Sym("at"), x, y, 0], [Sym("unit"), 1],
             [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("no" if (pl.power or pl.flag or p["lib"] in ("Connector:TestPoint",) or p["lib"].startswith("Mechanical:") or "footprint only" in p["mpn"]) else "yes")],
             [Sym("on_board"), Sym("no" if (pl.power or pl.flag) else "yes")], [Sym("dnp"), Sym("yes" if p["dnp"] else "no")],
             [Sym("uuid"), U(self.key, ref)]]
        top = y + pl.bb[1] + (0 if pl.power else 1.2)
        bot = y + pl.bb[3] - (0 if pl.power else 1.2)
        props = [("Reference", ref, (x, y + (pl.bb[1] if not pl.power else 2.5)), pl.power),
                 ("Value", p["value"], (x, y + (pl.bb[3] if not pl.power else 3.8)), False),
                 ("Footprint", p["fp"], (x, y), True),
                 ("Datasheet", prop(pl.sym, "Datasheet") or "", (x, y), True),
                 ("Description", p["desc"] or prop(pl.sym, "Description") or "", (x, y), True)]
        if not pl.power:
            body_top = min(st["y"] for st in pl.stubs) if pl.stubs else -2
            body_bot = max(st["y"] for st in pl.stubs) if pl.stubs else 2
            props[0] = ("Reference", ref, (x + 0.0, snap(y + min(body_top, -2.54) - 1.27)), False)
            props[1] = ("Value", p["value"], (x + 0.0, snap(y + max(body_bot, 2.54) + 1.27)), False)
            if len(pl.stubs) == 2 and all(st["dir"] in (90, 270) for st in pl.stubs):   # vertical 2-pin passive
                props[0] = ("Reference", ref, (x + 2.54, y - 1.27), False)
                props[1] = ("Value", p["value"], (x + 2.54, y + 1.27), False)
            props += [("MPN", p["mpn"], (x, y), True), ("Manufacturer", p["mfr"], (x, y), True)]
            if p["note"]:
                props.append(("Note", p["note"], (x, y), True))
        for k, v, (px, py), hide in props:
            just = "left" if (k in ("Reference", "Value") and not pl.power and len(pl.stubs) == 2
                              and all(st["dir"] in (90, 270) for st in pl.stubs)) else None
            s.append([Sym("property"), k, v, [Sym("at"), snap(px, 0.01), snap(py, 0.01), 0], eff(1.27, just, hide)])
        for num, *_ in pl.pins:
            s.append([Sym("pin"), num, [Sym("uuid"), U(self.key, ref, "pin", num)]])
        s.append([Sym("instances"), [Sym("project"), D.PROJECT,
                                     [Sym("path"), self.path, [Sym("reference"), ref], [Sym("unit"), 1]]]])
        self.items.append(s)
        if pl.power:
            return
        for st in pl.stubs:
            ex, ey = x + st["x"], y + st["y"]
            net = st["net"]
            if not net:
                self.items.append([Sym("no_connect"), [Sym("at"), ex, ey], [Sym("uuid"), U(self.key, ref, "nc", st["num"])]])
                continue
            dx, dy = DIRV[st["dir"]]
            wx, wy = ex + dx * 2.54, ey + dy * 2.54
            self.items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), ex, ey], [Sym("xy"), wx, wy]],
                               [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                               [Sym("uuid"), U(self.key, ref, "w", st["num"])]])
            if net == "GND":
                self.gnd(wx, wy, st["dir"])
            else:
                self.glabel(net, wx, wy, st["dir"], U(self.key, ref, "l", st["num"]))

    def gnd(self, x, y, d):
        self.pwr[0] += 1
        ref = f"#PWR{self.pwr[0]:03d}"
        sym = get_symbol("power:GND")
        self.add_lib(sym)
        ang = {270: 0, 90: 180, 0: 90, 180: 270}[d]
        self.items.append([Sym("symbol"), [Sym("lib_id"), "power:GND"], [Sym("at"), x, y, ang], [Sym("unit"), 1],
                           [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                           [Sym("dnp"), Sym("no")], [Sym("uuid"), U(self.key, ref)],
                           [Sym("property"), "Reference", ref, [Sym("at"), x, y + 6.35, 0], eff(1.27, None, True)],
                           [Sym("property"), "Value", "GND", [Sym("at"), x, y + 3.81, 0], eff(1.0, None, True)],
                           [Sym("property"), "Footprint", "", [Sym("at"), x, y, 0], eff(1.27, None, True)],
                           [Sym("property"), "Datasheet", "", [Sym("at"), x, y, 0], eff(1.27, None, True)],
                           [Sym("property"), "Description", "", [Sym("at"), x, y, 0], eff(1.27, None, True)],
                           [Sym("pin"), "1", [Sym("uuid"), U(self.key, ref, "p")]],
                           [Sym("instances"), [Sym("project"), D.PROJECT,
                                               [Sym("path"), self.path, [Sym("reference"), ref], [Sym("unit"), 1]]]]])

    def glabel(self, net, x, y, d, uid):
        ang, just = {0: (0, "left"), 180: (180, "right"), 90: (90, "left"), 270: (270, "right")}[d]
        self.items.append([Sym("global_label"), net, [Sym("shape"), Sym("bidirectional")], [Sym("at"), x, y, ang],
                           [Sym("fields_autoplaced"), Sym("yes")], eff(1.27, just), [Sym("uuid"), uid],
                           [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), x, y, 0],
                            eff(1.27, just, True)]])

    def text(self, s, x, y, size=1.27):
        self.items.append([Sym("text"), s, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
                           eff(size, "left top"), [Sym("uuid"), U(self.key, "text", s[:40], x, y)]])

    def write(self, paper, extra_title=""):
        root = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
                [Sym("generator_version"), "9.0"], [Sym("uuid"), SHEET_UUID.get(self.key, ROOT_UUID)],
                [Sym("paper"), paper],
                [Sym("title_block"), [Sym("title"), f"{D.PN} - {self.title}"], [Sym("date"), "2026-10-24"],
                 [Sym("rev"), D.REV], [Sym("company"), D.COMPANY],
                 [Sym("comment"), 1, "Generated from 02_python/design.py - edit the source, then regenerate"],
                 [Sym("comment"), 2, extra_title]],
                [Sym("lib_symbols")] + list(self.libs.values())]
        root += self.items
        return root


def notes_for(parts):
    lines = []
    for p in parts:
        if p["note"] and not p["ref"].startswith("#"):
            lines.append(f"{p['ref']}: {p['note']}")
    return lines


SHEET_NOTES = {
    "power": ["!! MAINS 85-265 VAC on this sheet. All copper left of the HLK-PM01 AC pins is LIVE. !!",
              "Live path: J1.L -> F1 (T500 mA) -> ACL_F. MOV1 (14D471K) + CX1 (100 nF X2) + RB1 (1M bleeder) across L-N.",
              "PSU feed: ACL_F -> NTC1 (5D-9 inrush) -> HLK-PM01 AC/L; AC/N -> Neutral. The lamp inrush does NOT pass NTC1.",
              "HLK-PM01: reinforced-isolation AC-DC, 5 V / 3 W. Its isolation is the primary SELV barrier (>=6 mm creepage).",
              "5 V rail: CB1 220 uF bulk + C5 100 nF. Feeds the radar (~79 mA, bursty), MCU and opto LED.",
              "Layout: AC pins and DC pins of PS1 are 29 mm apart - route the isolation slot between them."],
    "load": ["!! MAINS on the triac (Q1) and the MOC3063 output pins 4/6. The opto is the isolation barrier. !!",
             "MCU PB0/MOSI -> R1 (330R) -> MOC3063 LED (pins 1/2, SELV). Opto output (4/6) drives the BTA16 gate.",
             "MOC3063 is ZERO-CROSSING: it only fires near the mains zero-crossing -> low EMI, low gate inrush.",
             "RG1 180R = gate resistor (ACL_F -> opto -> gate). RS1 100R + CS1 10 nF = dv/dt snubber across MT1-MT2.",
             "Q1 BTA16-600B: MT1(A1)=Line (ACL_F), MT2(A2)=Lamp. Derate / heatsink for lamp currents > ~2 A.",
             "VERIFY per ON AN-3004: peak opto current < 1 A ITSM; 180R OK for a zero-cross opto, raise to 360R if not."],
    "mcu": ["ATtiny13A-SU at 5 V, internal 9.6 MHz RC. 1 kB flash. Everything on this sheet is SELV (isolated 5 V).",
            "PB5=RESET (ISP), PB3/ADC3=delay trimmer, PB4=radar OUT, PB0=opto drive, PB1=LED, PB2=button.",
            "ISP header J2 is the standard 6-pin AVR pinout. C3 (RESET cap) is DNP so ISP timing is clean.",
            "Program the board on the bench with mains DISCONNECTED (the opto/LED share the ISP lines)."],
    "io": ["LD2410B 24 GHz radar on J3 at the board edge, antenna facing the front cover; no copper under the antenna.",
           "OUT (pin1, 3.3 V) -> PB4: HIGH = person present. UART TX/RX on J4 for the Hi-Link PC config tool (3.3 V).",
           "SW1 override on PB2 (debounced, 1k series so it does not fight the ISP SCK). RP1 10k pull-up, active low.",
           "RV1 10k trimmer -> ADC3 sets the no-one OFF delay (10 s ... 10 min, mapped in firmware).",
           "D1 status LED on PB1: on = presence, slow blink = manual mode, fast blink = fault (e.g. radar not responding)."],
}


def build():
    pwr = [0]
    all_sheets = []
    for i, (key, title) in enumerate(D.SHEETS.items()):
        sh = Sheet(key, title, i + 2, pwr)
        parts = [p for p in D.PARTS if p["sheet"] == key]
        groups = {}
        for p in parts:
            groups.setdefault(p["group"] or p["ref"], []).append(Placed(p))
        clusters = list(groups.values())
        for name, pw, ph in PAPERS:
            pos, used = layout(clusters, pw - 40, 20, 25)
            if used < ph - 75:
                paper = name
                break
        else:
            paper = PAPERS[-1][0]
        for cl in clusters:
            for pl in cl:
                x, y = pos[id(pl)]
                sh.symbol(pl, x, y)
        ny = snap(25 + used + 8)
        sh.text("DESIGN NOTES\n" + "\n".join(SHEET_NOTES.get(key, [])), 20, ny, 1.5)
        nl = notes_for(parts)
        if nl:
            sh.text("PART NOTES (VERIFY = check against vendor datasheet before release)\n" + "\n".join(nl),
                    snap(min(220, {"A3": 220, "A2": 300, "A1": 420}[paper])), ny, 1.27)
        all_sheets.append((sh, paper))
        with open(os.path.join(KDIR, f"{key}.kicad_sch"), "w") as f:
            f.write(dump(sh.write(paper, f"Sheet {i + 2}: {title}")) + "\n")
    # root sheet
    root = Sheet("root", "Top level", 1, pwr)
    x, y = 25.4, 40.64
    for i, (key, title) in enumerate(D.SHEETS.items()):
        sx, sy = x + (i % 2) * 120.65, y + (i // 2) * 50.8
        root.items.append([Sym("sheet"), [Sym("at"), sx, sy], [Sym("size"), 101.6, 30.48],
                           [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                           [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                           [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                           [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), SHEET_UUID[key]],
                           [Sym("property"), "Sheetname", title, [Sym("at"), sx, sy - 0.7, 0], eff(1.8, "left bottom")],
                           [Sym("property"), "Sheetfile", f"{key}.kicad_sch", [Sym("at"), sx, sy + 31.1, 0], eff(1.27, "left top")],
                           [Sym("instances"), [Sym("project"), D.PROJECT, [Sym("path"), f"/{ROOT_UUID}", [Sym("page"), str(i + 2)]]]]])
    root.text(
        "SPS-24G-01  Smart Presence Sensor Switch  -  70 x 56 mm, 2-layer 1.6 mm FR-4, 1 oz, ENIG  (SAMAY ELECTRONICS)\n"
        "Standalone (no WiFi / no BLE). Fits a standard Indian 86 x 86 mm modular wall box.\n\n"
        "===== HIGH-VOLTAGE (AC) SECTION =====================|===== LOW-VOLTAGE (SELV) SECTION ==========\n"
        "L in -> F1 T500mA -> ACL_F -+- MOV1 14D471K           |  HLK-PM01 +5V -> ATtiny13A-SU\n"
        "                            +- CX1 100nF X2 + RB1 1M  |      PB4 <- LD2410B OUT (24 GHz radar)\n"
        "                            +- NTC1 5D-9 -> HLK-PM01 AC/L  |  PB3 <- 10k delay trimmer (10 s..10 min)\n"
        "                            +- BTA16-600B MT1          |      PB2 <- override button, PB1 -> status LED\n"
        "LAMP out <- BTA16 MT2 ; gate <- RG1 180R <- MOC3063   |      PB0 -> MOC3063 LED (opto, SELV side)\n"
        "snubber RS1 100R + CS1 10nF across MT1-MT2            |  ISP: 6-pin AVR header (program with mains OFF)\n\n"
        "Isolation: HLK-PM01 (reinforced AC-DC) + MOC3063 (7.5 kVrms opto) are the ONLY parts crossing the barrier.\n"
        ">= 6 mm creepage / >= 3 mm clearance + a routed isolation slot separate the two sections. SEE SAFETY_REVIEW.md.",
        25.4, 150.0, 1.6)
    with open(os.path.join(KDIR, f"{D.PROJECT}.kicad_sch"), "w") as f:
        r = root.write("A3", "Top level: block diagram")
        r += [[Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]], [Sym("embedded_fonts"), Sym("no")]]
        f.write(dump(r) + "\n")
    print("sheets:", [(s.key, p) for s, p in all_sheets])


if __name__ == "__main__":
    build()
