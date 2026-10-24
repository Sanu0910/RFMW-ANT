"""Generate a KiCad 9 schematic for CRL-MT1 directly from design.py.

Self-contained: each part becomes a procedurally-drawn rectangular symbol with one pin per
entry in its pin map; every pin gets a short wire stub and a global label carrying its net name,
so connectivity is explicit, ERC-checkable and identical to the design.py netlist. Parts are
clustered by functional group and shelf-packed on one large sheet. No external symbol library is
needed (the chip symbols are drawn as generic boxes, which is enough for netlist/ERC purposes;
replace with datasheet symbols before a production schematic review if desired).

  python3 make_schematic.py      -> writes ../01_kicad/crl-mt1.kicad_sch (+ .kicad_pro)
"""
import os
import uuid

from sexp import Sym, dump
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
os.makedirs(KDIR, exist_ok=True)
PROJECT = "crl-mt1"
REV = "A"
COMPANY = "Carl RF Microwave"

NS = uuid.UUID("b2f4a6c8-1d3e-4f50-9a7b-6c5d4e3f2a10")
G = 1.27


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


ROOT_UUID = U("root")


def snap(v, g=G):
    return round(v / g) * g


def eff(size=1.27, justify=None, hide=False):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


# -------------------------------------------------------------- reconstruct per-part pin maps
def part_pins():
    """ref -> list of (pin, net), in a stable order (net declaration order)."""
    pm = {}
    for net, nodes in D.NETS.items():
        for node in nodes:
            ref, pin = node.rsplit(".", 1)
            pm.setdefault(ref, []).append((pin, net))
    return pm


DIRV = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}   # sheet coords (Y down)


class Placed:
    """A part laid out as a box: pins split left (first half) / right (second half)."""

    def __init__(self, ref, value, fp, group, desc, mpn, mfr, pins):
        self.ref, self.value, self.fp, self.group = ref, value, fp, group
        self.desc, self.mpn, self.mfr = desc, mpn, mfr
        self.pins = pins                       # [(pin, net)]
        self.libname = f"{PROJECT}:{self._sym_key()}"
        n = len(pins)
        self.nleft = (n + 1) // 2
        self.nright = n - self.nleft
        rows = max(self.nleft, self.nright, 1)
        self.body_h = (rows + 1) * 2.54
        namelen = max([len(p) for p, _ in pins] + [len(ref), len(value), 4])
        # width must be an even multiple of the 1.27 mm grid so +/- body_w/2 stays on the grid
        self.body_w = round(max(12.7, namelen * 1.4 + 7.62) / 2.54) * 2.54
        # stub list: (pin_num, px, py, dir_outward)
        self.stubs = []
        self._pin_geo = []                     # for the lib symbol: (num, name, x, y, ang)
        half = self.body_h / 2.0
        for i, (pin, net) in enumerate(pins):
            # _pin_geo is in library (Y-up) coords; stubs are in sheet (Y-down) coords: Y negated
            if i < self.nleft:
                py = snap(-half + (i + 1) * 2.54)
                px = -self.body_w / 2.0
                self._pin_geo.append((pin, pin, px - 2.54, -py, 0))   # ang 0: points right into body
                self.stubs.append((pin, px - 2.54, py, 180))          # stub goes left (outward)
            else:
                j = i - self.nleft
                py = snap(-half + (j + 1) * 2.54)
                px = self.body_w / 2.0
                self._pin_geo.append((pin, pin, px + 2.54, -py, 180))  # ang 180: points left into body
                self.stubs.append((pin, px + 2.54, py, 0))             # stub goes right (outward)

    def _sym_key(self):
        # unique per part: box geometry depends on this part's own pin-name lengths,
        # so sharing a symbol across parts would misalign pins
        return "".join(c if c.isalnum() else "_" for c in f"{self.ref}_{self.group}")

    def lib_symbol(self):
        """Generic box symbol: rectangle + passive pins, numbers == names."""
        half_w = self.body_w / 2.0
        half_h = self.body_h / 2.0
        name = self.libname.split(":")[-1]
        gfx = [Sym("symbol"), f"{name}_0_1",
               [Sym("rectangle"), [Sym("start"), -half_w, half_h], [Sym("end"), half_w, -half_h],
                [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
                [Sym("fill"), [Sym("type"), Sym("background")]]]]
        pinblk = [Sym("symbol"), f"{name}_1_1"]
        for num, pname, x, y, ang in self._pin_geo:
            pinblk.append(
                [Sym("pin"), Sym("passive"), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), 2.54],
                 [Sym("name"), pname, eff(1.0)], [Sym("number"), num, eff(1.0)]])
        return [Sym("symbol"), self.libname,
                [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")],
                [Sym("on_board"), Sym("yes")],
                [Sym("property"), "Reference", "U", [Sym("at"), 0, half_h + 2.54, 0], eff()],
                [Sym("property"), "Value", name, [Sym("at"), 0, -half_h - 2.54, 0], eff()],
                [Sym("property"), "Footprint", "", [Sym("at"), 0, 0, 0], eff(1.27, None, True)],
                [Sym("property"), "Datasheet", "", [Sym("at"), 0, 0, 0], eff(1.27, None, True)],
                [Sym("property"), "Description", "", [Sym("at"), 0, 0, 0], eff(1.27, None, True)],
                gfx, pinblk]


def glabel(net, x, y, d, uid):
    ang, just = {0: (0, "left"), 180: (180, "right"), 90: (90, "left"), 270: (270, "right")}[d]
    return [Sym("global_label"), net, [Sym("shape"), Sym("bidirectional")], [Sym("at"), x, y, ang],
            [Sym("fields_autoplaced"), Sym("yes")], eff(1.27, just), [Sym("uuid"), uid],
            [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), x, y, 0],
             eff(1.27, just, True)]]


def place_symbol(pl, x, y, items):
    ref = pl.ref
    s = [Sym("symbol"), [Sym("lib_id"), pl.libname], [Sym("at"), x, y, 0], [Sym("unit"), 1],
         [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
         [Sym("dnp"), Sym("no")], [Sym("uuid"), U("sym", ref)],
         [Sym("property"), "Reference", ref, [Sym("at"), x, y - pl.body_h / 2.0 - 2.54, 0], eff()],
         [Sym("property"), "Value", pl.value, [Sym("at"), x, y + pl.body_h / 2.0 + 2.54, 0], eff()],
         [Sym("property"), "Footprint", pl.fp, [Sym("at"), x, y, 0], eff(1.27, None, True)],
         [Sym("property"), "Datasheet", "", [Sym("at"), x, y, 0], eff(1.27, None, True)],
         [Sym("property"), "Description", pl.desc, [Sym("at"), x, y, 0], eff(1.27, None, True)],
         [Sym("property"), "MPN", pl.mpn, [Sym("at"), x, y, 0], eff(1.27, None, True)],
         [Sym("property"), "Manufacturer", pl.mfr, [Sym("at"), x, y, 0], eff(1.27, None, True)]]
    for num, *_ in pl._pin_geo:
        s.append([Sym("pin"), num, [Sym("uuid"), U("sym", ref, "pin", num)]])
    s.append([Sym("instances"), [Sym("project"), PROJECT,
                                 [Sym("path"), f"/{ROOT_UUID}", [Sym("reference"), ref], [Sym("unit"), 1]]]])
    items.append(s)
    # stubs + global labels
    for (num, px, py, d), (pin, net) in zip(pl.stubs, pl.pins):
        ex, ey = x + px, y + py
        dx, dy = DIRV[d]
        wx, wy = ex + dx * 2.54, ey + dy * 2.54
        items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), ex, ey], [Sym("xy"), wx, wy]],
                      [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                      [Sym("uuid"), U("sym", ref, "w", num)]])
        items.append(glabel(net, wx, wy, d, U("sym", ref, "l", num)))


def build():
    pm = part_pins()
    placed = []
    for (ref, value, mpn, mfr, fp, group, desc) in D.PARTS:
        pins = pm.get(ref, [])
        if not pins:
            continue
        placed.append(Placed(ref, value, fp, group, desc, mpn, mfr, pins))

    # group by functional group, shelf-pack
    groups = {}
    for pl in placed:
        groups.setdefault(pl.group, []).append(pl)

    PAGE_W = 1050.0
    items = []
    libs = {}
    x, y, shelf = 20.0, 30.0, 0.0
    colgap, rowgap = 10.0, 16.0
    for gname, members in groups.items():
        # a group occupies a cluster; wrap within page width
        for pl in members:
            w = pl.body_w + 60.0          # room for labels either side
            h = pl.body_h + 16.0
            if x + w > PAGE_W and x > 20.0:
                x = 20.0
                y += shelf + rowgap
                shelf = 0.0
            cx = snap(x + w / 2.0)
            cy = snap(y + h / 2.0)
            place_symbol(pl, cx, cy, items)
            libs.setdefault(pl.libname, pl.lib_symbol())
            x += w + colgap
            shelf = max(shelf, h)
        # break line between groups
        x = 20.0
        y += shelf + rowgap
        shelf = 0.0

    root = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
            [Sym("generator_version"), "9.0"], [Sym("uuid"), ROOT_UUID], [Sym("paper"), "A0"],
            [Sym("title_block"), [Sym("title"), "CRL-MT1 multi-tool RF board"], [Sym("date"), "2026-10-24"],
             [Sym("rev"), REV], [Sym("company"), COMPANY],
             [Sym("comment"), 1, "Generated from 02_python/design.py - edit the source, then regenerate"],
             [Sym("comment"), 2, "Original firmware-compatible design; not a Flipper Zero"]],
            [Sym("lib_symbols")] + list(libs.values())]
    root += items
    root += [[Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]],
             [Sym("embedded_fonts"), Sym("no")]]
    with open(os.path.join(KDIR, f"{PROJECT}.kicad_sch"), "w") as f:
        f.write(dump(root) + "\n")

    # minimal project file so kicad-cli erc / netlist work
    pro = os.path.join(KDIR, f"{PROJECT}.kicad_pro")
    if not os.path.exists(pro):
        with open(pro, "w") as f:
            f.write('{\n  "board": {},\n  "meta": {"filename": "%s.kicad_pro", "version": 1},\n'
                    '  "sheets": [], "text_variables": {}\n}\n' % PROJECT)
    print(f"schematic: {len(placed)} symbols, {len(D.NETS)} nets, {len(libs)} generated box-symbols")


if __name__ == "__main__":
    build()
