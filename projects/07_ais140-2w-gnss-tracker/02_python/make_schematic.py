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
EXTRA = {"tracker": os.path.join(KDIR, "tracker.kicad_sym")}
NS = uuid.UUID("6f1d3c2e-8a54-4c1b-9d55-3e1f0a2b7c90")
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
                [Sym("title_block"), [Sym("title"), f"CRL-TRK-2W-01 - {self.title}"], [Sym("date"), "2026-10-17"],
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
    "power_in": ["Input 9-36 V (12 V nominal, survives 24 V jump start, -33 V reverse, ISO 7637-2 pulses via D1).",
                 "F1 + D1 at the connector, then LM74700-Q1 ideal diode (Q1): <15 mV drop, blocks reverse battery.",
                 "FB1 + C4/C5 pi filter keeps buck ripple off the harness (CISPR 25).",
                 "LM5164-Q1 100 V COT buck: 5.0 V / 1 A, 10 uA IQ (key for parked-vehicle battery drain).",
                 "Layout: buck loop (C4-U2-L1-C8) <10 mm, SW node small, far from GNSS (see PCB notes)."],
    "power_rails": ["BQ24074: power path. OUT (VSYS) = 4.4 V on external power, = VBAT on battery.",
                    "Charging is blocked outside 0-45 C by the pack NTC on TS (parked-in-sun safety).",
                    "VSYS feeds the modem directly (SIM7080G VBAT 2.7-4.8 V, 0.5 A peaks) via U6 load switch,",
                    "which lets firmware hard-reset a hung modem. U5 3.3 V LDO is always on (deep sleep rail).",
                    "U7 switches GNSS VCC; V_BCKP stays on +3V3 so ephemeris is kept (hot start < 2 s)."],
    "mcu": ["ESP32-S3: native USB (IO19/20) gives flashing + JTAG + CDC log without extra parts.",
            "TC2050 Tag-Connect for production JTAG/UART; BOOT/RESET buttons for bench use.",
            "Strapping: IO0 boot (pull-up), IO45 LED to GND (VDD_SPI=3.3 V ok), IO46 held low by R50.",
            "RTC-capable wake pins: IO5 IGN, IO6 PANIC, IO14 IMU INT, IO18 modem RI."],
    "cellular": ["SIM7080G: Cat-M1/NB-IoT, PSM 3 uA. 1.8 V UART via TXS0108E (OE = VDD_EXT).",
                 "PWRKEY driven open-drain by Q2. Never cut VBAT while the module runs: AT+CPOWD first,",
                 "U6 only for watchdog recovery. RF_ANT -> 50 R CPWG -> pi pad -> U.FL (flex antenna).",
                 "SIM: 22 R series + ESD array next to the holder; keep SIM traces away from RF and VBAT.",
                 "TP1-TP5: modem USB (firmware upgrade, logs) - bring to bed-of-nails fixture."],
    "gnss": ["NEO-F10N dual-band L1/L5: NavIC SPS-L5 required by AIS-140. RF_IN has an internal DC block.",
             "Active antenna bias from VCC_RF through R35/L2 (u-blox IM fig.6); DNP R35+L2 for passive antennas.",
             "RF trace: 50 R CPWG on L1 over solid L2 ground, via fence every 1.5 mm, no other nets nearby.",
             "UART 1 k series resistors stop back-powering while GNSS VCC is switched off."],
    "io": ["Inputs survive 0-60 V and reverse battery: 1206 series resistors (200 V), BAT54S clamps, RC filter.",
           "PANIC: SOS switch to chassis GND (AIS-140 emergency button). IGN/DIN1: 12/24 V active high.",
           "DOUT1: low-side immobiliser relay driver, flyback D13 to VIN_PROT.",
           "IMU wake-on-motion -> IO14 (theft alert), crash = >6 g peak + tilt > 60 deg (firmware).",
           "RV-3028 EVI pin time-stamps lid opening (TAMPER_N) even with the MCU asleep."],
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
        sx, sy = x + (i % 3) * 120.65, y + (i // 3) * 50.8
        root.items.append([Sym("sheet"), [Sym("at"), sx, sy], [Sym("size"), 101.6, 30.48],
                           [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                           [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                           [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                           [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), SHEET_UUID[key]],
                           [Sym("property"), "Sheetname", title, [Sym("at"), sx, sy - 0.7, 0], eff(1.8, "left bottom")],
                           [Sym("property"), "Sheetfile", f"{key}.kicad_sch", [Sym("at"), sx, sy + 31.1, 0], eff(1.27, "left top")],
                           [Sym("instances"), [Sym("project"), D.PROJECT, [Sym("path"), f"/{ROOT_UUID}", [Sym("page"), str(i + 2)]]]]])
    root.text(
        "CRL-TRK-2W-01  AIS-140 two-wheeler tracker  -  60 x 45 mm, 4-layer 1.6 mm (JLC04161H-7628)\n\n"
        "VEHICLE 9-36 V -> F1/D1 -> LM74700 ideal diode -> pi filter -> LM5164 buck 5.0 V -+-> BQ24074 power path -> VSYS 3.0-4.4 V\n"
        "USB-C VBUS 5 V ---------------------------------------------------------------+     |-> TPS22917 -> SIM7080G VBAT\n"
        "18650 1S pack (PCM + NTC) <-> BQ24074 BAT  (LC709203F fuel gauge, VBAT/2 ADC)        |-> TLV75733 -> +3V3 (always on)\n"
        "                                                                                       -> TPS22917 -> +3V3_GNSS\n\n"
        "ESP32-S3-WROOM-1 <-UART(1.8 V via TXS0108E)-> SIM7080G LTE-M/NB-IoT  -> U.FL -> flex LTE antenna\n"
        "                 <-UART---------------------> NEO-F10N L1/L5 + NavIC  -> U.FL -> active L1/L5 patch\n"
        "                 <-I2C--> IIM-42652 IMU, LC709203F gauge, RV-3028 RTC     <-SPI-> W25Q128 log flash\n"
        "                 <-GPIO-> IGN, PANIC, DIN1, AIN1, DOUT1 (relay), LEDs, Tag-Connect JTAG, USB-C\n\n"
        "Sleep budget (ignition off, modem PSM, GNSS backup): ~110 uA from the pack - see 04_docs/POWER_TREE.md",
        25.4, 160.0, 1.6)
    with open(os.path.join(KDIR, f"{D.PROJECT}.kicad_sch"), "w") as f:
        r = root.write("A3", "Top level: block diagram")
        r += [[Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]], [Sym("embedded_fonts"), Sym("no")]]
        f.write(dump(r) + "\n")
    print("sheets:", [(s.key, p) for s, p in all_sheets])


if __name__ == "__main__":
    build()
