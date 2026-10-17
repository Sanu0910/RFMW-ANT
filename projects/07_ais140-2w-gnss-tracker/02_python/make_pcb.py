"""Build the 4-layer PCB from design.py with pcbnew (run inside the KiCad 9 Python).

  python3 make_pcb.py place     -> place footprints, nets, outline, zones; report courtyard overlaps
  python3 make_pcb.py dsn       -> + export Specctra DSN for Freerouting
  python3 make_pcb.py ses       -> import routed SES, add stitching, fill zones, save

Coordinates in PLACE are board-local mm (origin = top-left board corner, +y down).
Side 'B' parts are flipped to the bottom; their rotation is the final rotation seen from the top.
"""
import json, math, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
from make_schematic import U, SHEET_UUID, EXTRA
from libsym import get_symbol, pins as _pins

_symcache = {}


def sympins(lib):
    if lib not in _symcache:
        _symcache[lib] = _pins(get_symbol(lib, EXTRA))
    return _symcache[lib]

KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
PCB = os.path.join(KDIR, "tracker.kicad_pcb")
FPROOT = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board origin on the KiCad page
BW, BH, BR = 60.0, 45.0, 2.0   # board size and corner radius

# ------------------------------------------------------------------------------------ placement
# Anchors: hand-placed parts  ref: (x, y, rot, side).  'B' parts are flipped to the bottom.
PLACE = {
    # GNSS corner (top-left): U.FL pad 1 straight above RF_IN (pin 11); series R36, shunts C39/C38,
    # bias-T L2 + C37 + R35 tapped off the line (u-blox IM fig.6)
    "U14": (9.0, 16.45, -90, "F"), "J7": (4.15, 2.6, 0, "F"),
    "R36": (3.1, 7.25, 90, "F"), "C39": (1.8, 5.75, 180, "F"), "C38": (1.75, 8.75, 180, "F"),
    "L2": (4.4, 5.75, 180, "F"), "C37": (6.35, 5.75, 0, "F"), "R35": (5.3, 7.6, 90, "F"),
    # MCU (top-middle), antenna flush with the top edge
    "U8": (27.5, 13.0, 0, "F"),
    # LTE modem (bottom-right), RF pin 32 -> pi pad -> U.FL on the right edge
    "U11": (46.3, 34.7, 0, "F"), "R32": (56.6, 31.8, 270, "F"), "C32": (57.9, 30.3, 0, "F"),
    "C33": (57.9, 33.5, 0, "F"), "J6": (57.65, 37.0, 0, "F"),
    # vehicle connector + buck (top-right, >30 mm from the GNSS module)
    "J1": (46.6, 3.3, 0, "F"), "U2": (45.6, 15.0, 0, "F"), "L1": (53.0, 14.9, 0, "F"),
    # charger / LDO (top, bottom-middle)
    "U3": (25.5, 32.5, 0, "F"), "U5": (33.9, 30.4, 0, "F"),
    # mechanics
    "H1": (2.6, 42.4, 0, "F"), "H2": (2.6, 26.6, 0, "F"), "H3": (39.95, 2.6, 0, "F"), "H4": (33.2, 42.4, 0, "F"),
    # bottom side anchors
    "J3": (4.6, 34.5, 90, "B"), "J2": (19.5, 39.6, 0, "B"), "J5": (48.4, 37.0, 0, "B"),
    "J4": (14.0, 9.0, 90, "B"), "SW1": (4.4, 5.4, 90, "B"), "SW2": (4.4, 14.2, 90, "B"),
    "U10": (23.0, 29.4, 0, "B"), "C3": (41.0, 15.2, 90, "B"),
    "TP1": (57.6, 26.8, 0, "B"), "TP2": (57.6, 29.2, 0, "B"), "TP3": (57.6, 31.6, 0, "B"),
}

# Greedy-placed small parts, in priority order: (ref, side, target) with target = (ref, pad) or (x, y)
SMALL = [
    # GNSS support (top)
    ("C35", "F", ("U14", "23")), ("C34", "F", ("U14", "23")), ("C36", "F", ("U14", "22")),
    ("R33", "F", ("U14", "20")), ("R34", "F", ("U14", "21")),
    ("U7", "F", (14.5, 27.5)), ("C19", "F", ("U7", "4")), ("R18", "F", ("U7", "3")), ("R52", "F", ("U7", "5")),
    # buck (top)
    ("C6", "F", ("U2", "2")), ("C7", "F", ("U2", "7")), ("C4", "F", ("U2", "2")), ("C5", "F", ("U2", "2")),
    ("R1", "F", ("U2", "3")), ("R2", "F", ("U2", "3")), ("R3", "F", ("U2", "4")), ("R4", "F", ("U2", "5")),
    ("R5", "F", ("U2", "5")), ("R6", "F", ("U2", "6")), ("C8", "F", ("L1", "2")), ("C9", "F", ("L1", "2")),
    ("FB1", "F", (39.4, 21.5)), ("D2", "F", ("L1", "2")),
    # modem supply (top) + load switch
    ("C24", "F", ("U11", "34")), ("C25", "F", ("U11", "35")),
    ("U6", "F", (45.0, 22.5)), ("C18", "F", ("U6", "4")), ("R17", "F", ("U6", "3")), ("R51", "F", ("U6", "5")),
    # charger + LDO (top)
    ("C11", "F", ("U3", "13")), ("C12", "F", ("U3", "10")), ("C13", "F", ("U3", "2")), ("R9", "F", ("U3", "12")),
    ("R10", "F", ("U3", "16")), ("R11", "F", ("U3", "15")), ("R12", "F", ("U3", "14")), ("R13", "F", ("U3", "1")),
    ("R14", "F", ("U3", "7")), ("D4", "F", ("U3", "13")),
    ("C16", "F", ("U5", "1")), ("C17", "F", ("U5", "5")),
    # LEDs (top, bottom edge)
    ("D5", "F", (21.0, 43.0)), ("R24", "F", (21.0, 41.0)), ("D6", "F", (24.6, 43.0)), ("R25", "F", (24.6, 41.0)),
    ("D8", "F", (28.2, 43.0)), ("R28", "F", (28.2, 41.0)),
    # ---- bottom
    ("C21", "B", ("U8", "2")), ("C20", "B", ("U8", "2")), ("R19", "B", ("U8", "3")), ("C22", "B", ("U8", "3")),
    ("R20", "B", ("U8", "27")),
    ("C26", "B", ("U11", "34")), ("C27", "B", ("U11", "34")), ("C28", "B", ("U11", "35")), ("D7", "B", ("U11", "35")),
    ("Q2", "B", ("U11", "39")), ("R26", "B", ("U11", "39")),
    ("U13", "B", ("J5", "7")), ("R29", "B", ("J5", "7")), ("R30", "B", ("J5", "3")), ("R31", "B", ("J5", "2")),
    ("C31", "B", ("J5", "1")),
    ("U12", "B", ("U11", "2")), ("C29", "B", ("U12", "2")), ("C30", "B", ("U12", "19")),
    ("U9", "B", ("J3", "A6")), ("R21", "B", ("J3", "A5")), ("R22", "B", ("J3", "B5")),
    ("C23", "B", ("U10", "8")), ("R23", "B", ("U10", "1")), ("R53", "B", ("U10", "3")), ("R54", "B", ("U10", "7")),
    ("U15", "B", (31.0, 31.0)), ("C40", "B", ("U15", "8")), ("C41", "B", ("U15", "5")),
    ("U16", "B", (13.6, 19.8)), ("C42", "B", ("U16", "7")), ("R37", "B", ("U16", "8")),
    ("R38", "B", ("U16", "4")), ("R39", "B", ("U16", "3")), ("R40", "B", ("U16", "2")),
    ("U4", "B", ("J2", "1")), ("C15", "B", ("U4", "3")), ("R15", "B", ("U4", "3")), ("R16", "B", ("U4", "3")),
    ("C14", "B", ("U4", "3")),
    ("Q3", "B", (28.2, 40.0)), ("R27", "B", (28.2, 40.0)),
    # input protection (bottom, under the buck)
    ("F1", "B", ("J1", "1")), ("D1", "B", ("J1", "1")), ("Q1", "B", (47.0, 15.5)), ("U1", "B", (51.0, 16.5)),
    ("C1", "B", (53.0, 16.5)), ("C2", "B", (49.0, 18.5)), ("R7", "B", (51.0, 20.5)), ("R8", "B", (53.5, 20.5)),
    ("C10", "B", (53.5, 21.5)), ("D3", "B", (55.5, 21.0)),
    # vehicle I/O conditioning (bottom, near J1)
    ("R41", "B", (31.0, 8.0)), ("R43", "B", (31.0, 11.5)), ("R45", "B", (31.0, 15.0)), ("R47", "B", (31.0, 18.5)),
    ("D9", "B", (35.3, 8.0)), ("D10", "B", (35.3, 11.5)), ("D11", "B", (35.3, 15.0)), ("D12", "B", (35.3, 18.5)),
    ("C43", "B", (20.0, 8.2)), ("C45", "B", (21.8, 8.2)), ("C47", "B", (23.6, 8.2)), ("C49", "B", (25.4, 8.2)),
    ("R42", "B", (27.0, 7.5)), ("R44", "B", (27.0, 9.5)), ("R46", "B", (28.0, 7.5)), ("R48", "B", (28.0, 9.5)),
    ("C44", "B", (20.0, 11.0)), ("C46", "B", (22.0, 11.0)), ("C48", "B", (24.0, 11.0)), ("C50", "B", (26.0, 11.0)),
    ("Q4", "B", (40.0, 22.3)), ("R49", "B", (43.5, 23.4)), ("R50", "B", (45.5, 23.4)), ("D13", "B", (45.0, 21.0)),
    # test pads (bottom)
    ("TP4", "B", (57.6, 41.5)), ("TP5", "B", (55.2, 42.6)),
    ("TP10", "B", ("C2", "1")), ("TP11", "B", ("D2", "1")), ("TP12", "B", ("U3", "10")), ("TP13", "B", ("J2", "1")),
    ("TP14", "B", ("U5", "5")), ("TP15", "B", ("C24", "1")), ("TP16", "B", ("U7", "6")), ("TP17", "B", (30.0, 43.0)),
    ("TP18", "B", (9.6, 2.4)), ("TP19", "B", ("D9", "3")), ("TP20", "B", ("D10", "3")), ("TP6", "B", ("U14", "8")),
    ("TP7", "B", ("U14", "1")), ("TP8", "B", ("U14", "3")), ("TP9", "B", ("U16", "8")),
]

NETCLASS = {
    # name: (clearance, track, via_dia, via_drill)
    "Default": (0.127, 0.127, 0.45, 0.2),
    "Power": (0.15, 0.3, 0.6, 0.3),
    "HV": (0.25, 0.3, 0.6, 0.3),
    "RF50": (0.20, 0.36, 0.45, 0.2),
}
NET_PATTERNS = {
    "Power": ["VSYS", "VBAT", "VBAT_MDM", "+3V3", "+3V3_GNSS", "V5_*", "VBUS", "BUCK_SW", "GND"],
    "HV": ["VIN_*", "IGN_RAW", "PANIC_RAW", "DIN1_RAW", "AIN1_RAW", "DOUT1"],
    "RF50": ["LTE_RF*", "GNSS_RF*"],
}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(KDIR, "tracker.pretty") if lib == "tracker" else os.path.join(FPROOT, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def outline(board):
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)

    def arc(c, start, ang):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetCenter(pt(*c)); s.SetStart(pt(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
    r = BR
    seg((r, 0), (BW - r, 0)); seg((BW, r), (BW, BH - r)); seg((BW - r, BH), (r, BH)); seg((0, BH - r), (0, r))
    arc((BW - r, r), (BW - r, 0), 90); arc((BW - r, BH - r), (BW, BH - r), 90)
    arc((r, BH - r), (r, BH), 90); arc((r, r), (0, r), 90)


def zone(board, net, layer, poly, prio=0, name="", clearance=0.2, minw=0.2, thermal=0.3, spoke=0.35, solid=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if net:
        z.SetNet(board.FindNet(net))
    ol = z.Outline(); ol.NewOutline()
    for x, y in poly:
        ol.Append(mm(OX + x), mm(OY + y))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(minw))
    z.SetThermalReliefGap(mm(thermal))
    z.SetThermalReliefSpokeWidth(mm(spoke))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


def build(do_zones=True, outer=True):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.1); ds.m_MinClearance = mm(0.1); ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2); ds.m_HoleToHoleMin = mm(0.25); ds.m_CopperEdgeClearance = mm(0.3)
    ds.SetBoardThickness(mm(1.6))
    ds.m_MinResolvedSpokes = 1
    for lyr, nm in ((pcbnew.In1_Cu, "In1.Cu GND"), (pcbnew.In2_Cu, "In2.Cu PWR")):
        board.SetLayerName(lyr, nm.split()[0])
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    outline(board)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            nets[n] = ni
        return nets[n]
    fps = {}
    for p in D.PARTS:
        if p["ref"].startswith("#") or not p["fp"]:
            continue
        fp = load_fp(p["fp"])
        fp.SetReference(p["ref"]); fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH(f"/{SHEET_UUID[p['sheet']]}/{U(p['sheet'], p['ref'])}"))
        if p["dnp"]:
            fp.SetDNP(True)
        for k in ("MPN", "Manufacturer"):
            v = p["mpn"] if k == "MPN" else p["mfr"]
            if v:
                f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldId(), k)
                f.SetText(v); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
                fp.Add(f)
        board.Add(fp)
        pinname = {q[0]: q[1] for q in sympins(p["lib"])}
        for pad in fp.Pads():
            num = pad.GetNumber()
            n = p["nets"].get(num)
            if n:
                pad.SetNet(net(n))
            elif num in p["nets"] or (num in pinname and num not in p["nets"]):
                pn = pinname.get(num, '').replace('/', '{slash}')
                pad.SetNet(net(f"unconnected-({p['ref']}-{pn}-Pad{num})"))
        fps[p["ref"]] = fp
    placer = Placer(board, fps)
    for ref, (x, y, rot, side) in PLACE.items():
        placer.put(ref, x, y, rot, side)
    for ref, side, tgt in SMALL:
        placer.auto(ref, side, tgt)
    missing = [r for r in fps if r not in placer.done]
    if missing:
        print("NOT PLACED:", " ".join(missing))
    if do_zones:
        full = [(0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)]
        zone(board, "GND", pcbnew.In1_Cu, full, 0, "L2_GND", clearance=0.2)
        add_l3_pours(board)
        edge_keepout(board)
        if outer:
            add_outer_pours(board)
    return board



# Explicit RF geometry: (net, [points (x, y) board mm], width). Pads are on the lines by construction.
RF_ROUTES = [
    ("GNSS_RF", [(3.1, 2.6), (3.1, 6.77)], 0.36),
    ("GNSS_RF", [(2.28, 5.75), (3.1, 5.75), (3.92, 5.75)], 0.36),
    ("GNSS_RF_M", [(3.1, 7.73), (3.1, 10.45)], 0.36),
    ("GNSS_RF_M", [(2.23, 8.75), (3.1, 8.75)], 0.36),
    ("GNSS_BIAS", [(4.88, 5.75), (5.87, 5.75)], 0.25),
    ("GNSS_BIAS", [(5.3, 5.75), (5.3, 7.12)], 0.25),
    ("GNSS_VCC_RF", [(5.3, 8.08), (5.3, 10.45)], 0.25),
    ("LTE_RF_M", [(54.15, 29.65), (56.6, 29.65), (56.6, 31.32)], 0.36),
    ("LTE_RF_M", [(57.42, 30.3), (56.6, 30.3)], 0.36),
    ("LTE_RF", [(56.6, 32.28), (56.6, 37.0)], 0.36),
    ("LTE_RF", [(57.42, 33.5), (56.6, 33.5)], 0.36),
]


def pad_of(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(ref + "." + num)


def add_track(board, a, b, w, layer, net, locked=True):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net); t.SetLocked(locked)
    board.Add(t)
    return t


def route_rf(board):
    for net, pts, w in RF_ROUTES:
        ni = board.FindNet(net)
        for p0, p1 in zip(pts, pts[1:]):
            add_track(board, pt(*p0), pt(*p1), w, pcbnew.F_Cu, ni)


FANOUT = {"GND": 0.3, "+3V3": 0.3}   # net: stub width (mm)
VIA_D, VIA_DRILL, CLR = 0.45, 0.2, 0.15


def _keepouts(board):
    kos = []
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            kos.append(z)
    for fp in board.GetFootprints():
        for z in fp.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowVias():
                kos.append(z)
    return kos


def _clr(it):
    try:
        return max(CLR, pcbnew.ToMM(it.GetOwnClearance(pcbnew.F_Cu)))
    except Exception:
        return CLR


def in_outline(x, y, m):
    """inside the rounded-rectangle board with margin m"""
    if x < m or y < m or x > BW - m or y > BH - m:
        return False
    for cx, cy in ((BR, BR), (BW - BR, BR), (BR, BH - BR), (BW - BR, BH - BR)):
        if abs(x - cx) <= BR and abs(y - cy) <= BR and ((x < BR) == (cx == BR)) and ((y < BR) == (cy == BR)):
            if math.hypot(x - cx, y - cy) > BR - m:
                return False
    return True


def via_ok(board, pos, kos, items, netcode, src_pad=None):
    x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
    if not in_outline(x, y, 0.75):
        return False
    for z in kos:
        if z.Outline().Contains(pos, -1, mm(VIA_D / 2 + 0.1)):
            return False
    r = mm(VIA_D / 2)
    for it in items:
        if isinstance(it, pcbnew.PAD):
            gap = mm(0.15) if it.GetNetCode() == netcode else mm(_clr(it) + 0.03)
            if it.HitTest(pos, r + gap):
                return False
        elif isinstance(it, pcbnew.PCB_VIA):
            if it.HitTest(pos, r + mm(0.2)):
                return False
        else:   # track
            if it.GetNetCode() != netcode and it.HitTest(pos, r + mm(_clr(it) + 0.03)):
                return False
    return True


def seg_ok(board, a, b, w, layer, items, netcode, src):
    n = max(2, int(pcbnew.ToMM((b - a).EuclideanNorm()) / 0.08))
    for i in range(n + 1):
        p = pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * i / n), int(a.y + (b.y - a.y) * i / n))
        for it in items:
            if it is src or it.GetNetCode() == netcode:
                continue
            if isinstance(it, pcbnew.PAD):
                if it.IsOnLayer(layer) and it.HitTest(p, mm(w / 2 + _clr(it) + 0.03)):
                    return False
            elif isinstance(it, pcbnew.PCB_VIA):
                if it.HitTest(p, mm(w / 2 + CLR)):
                    return False
            elif it.GetLayer() == layer and it.HitTest(p, mm(w / 2 + _clr(it) + 0.03)):
                return False
    return True


def fanout(board):
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    added = 0; failed = []
    for fp in board.GetFootprints():
        c0 = fp.GetPosition()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in FANOUT or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            c = pad.GetPosition()
            bb = pad.GetBoundingBox()
            hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
            ox, oy = pcbnew.ToMM(c.x - c0.x), pcbnew.ToMM(c.y - c0.y)
            base = math.atan2(oy, ox) if (abs(ox) + abs(oy)) > 0.05 else 0.0
            w = min(FANOUT[net], 2 * min(hw, hh))
            done = False
            for dang in (0, 30, -30, 60, -60, 90, -90, 120, -120, 150, -150, 180):
                a = base + math.radians(dang)
                ca, sa = math.cos(a), math.sin(a)
                edge = 1.0 / max(1e-6, max(abs(ca) / max(hw, 1e-3), abs(sa) / max(hh, 1e-3)))
                for extra in (0.0, 0.15, 0.3, 0.5, 0.75, 1.0, 1.3):
                    d = edge + VIA_D / 2 + 0.12 + extra
                    pos = pcbnew.VECTOR2I(int(c.x + mm(d * ca)), int(c.y + mm(d * sa)))
                    if not via_ok(board, pos, kos, items, pad.GetNetCode(), pad):
                        continue
                    if not seg_ok(board, c, pos, w, layer, items, pad.GetNetCode(), pad):
                        continue
                    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(pad.GetNet()); v.SetLocked(True); board.Add(v)
                    t = add_track(board, c, pos, w, layer, pad.GetNet())
                    items += [v, t]
                    added += 1; done = True
                    break
                if done:
                    break
            if not done:
                failed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    print(f"fanout: {added} vias, {len(failed)} pads left to pours/router: {' '.join(failed[:40])}")


def all_items(board):
    return [p for p in board.GetPads()] + [t for t in board.GetTracks()]


def add_via(board, pos, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(net); board.Add(v)
    return v


def ep_vias(board):
    """Thermal / ground vias inside exposed pads of small QFN/DFN parts (tented, 0.2 mm drill)."""
    n = 0
    gnd = board.FindNet("GND")
    items = [t for t in board.GetTracks()]
    for ref, num, grid in (("U3", "17", 2), ("U4", "9", 2)):
        fp = board.FindFootprintByReference(ref)
        for p in fp.Pads():
            if p.GetNumber() != num:
                continue
            bb = p.GetBoundingBox(); c = p.GetPosition()
            sx, sy = bb.GetWidth() / (grid + 1), bb.GetHeight() / (grid + 1)
            for i in range(grid):
                for j in range(grid):
                    pos = pcbnew.VECTOR2I(int(bb.GetLeft() + sx * (i + 1)), int(bb.GetTop() + sy * (j + 1)))
                    if any(t.GetNetCode() != gnd.GetNetCode() and t.HitTest(pos, mm(0.225 + _clr(t) + 0.03)) for t in items):
                        continue
                    if any(isinstance(t, pcbnew.PCB_VIA) and t.HitTest(pos, mm(0.3)) for t in items):
                        continue
                    if any(p.GetNetCode() != gnd.GetNetCode() and p.HitTest(pos, mm(0.225 + _clr(p) + 0.03))
                           for p in board.GetPads()):
                        continue
                    items.append(add_via(board, pos, gnd, 0.45, 0.2)); n += 1
    return n


def stitch(board):
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = all_items(board)
    n = 0

    def try_add(x, y):
        nonlocal n, items
        pos = pt(x, y)
        if via_ok(board, pos, kos, items, gnd.GetNetCode()):
            v = add_via(board, pos, gnd)
            items.append(v); n += 1
            return True
        return False
    # RF via fences: both sides of every RF track, ~1.2 mm pitch
    for t in list(board.GetTracks()):
        if t.GetNetClassName() != "RF50" or isinstance(t, pcbnew.PCB_VIA):
            continue
        a, b = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = (pcbnew.ToMM(a.x) - OX, pcbnew.ToMM(a.y) - OY, pcbnew.ToMM(b.x) - OX, pcbnew.ToMM(b.y) - OY)
        L = math.hypot(bx - ax, by - ay)
        if L < 0.3:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        off = pcbnew.ToMM(t.GetWidth()) / 2 + 0.2 + VIA_D / 2 + 0.05
        k = 0.0
        while k <= L:
            for sgn in (1, -1):
                try_add(ax + ux * k - uy * off * sgn, ay + uy * k + ux * off * sgn)
            k += 1.2
    # board edge ring, 3 mm pitch
    e = 0.9
    for x in [e + i * 3.0 for i in range(int((BW - 2 * e) / 3.0) + 1)]:
        try_add(x, e); try_add(x, BH - e)
    for y in [e + i * 3.0 for i in range(int((BH - 2 * e) / 3.0) + 1)]:
        try_add(e, y); try_add(BW - e, y)
    # area grid, 4 mm pitch (keeps L1/L4 pours tied to the L2 plane)
    for i in range(1, int(BW / 4)):
        for j in range(1, int(BH / 4) + 1):
            for dx, dy in ((0, 0), (0.6, 0), (0, 0.6), (-0.6, 0), (0, -0.6)):
                if try_add(i * 4.0 + dx, j * 4.0 - 1.0 + dy):
                    break
    return n


def finish():
    board = pcbnew.LoadBoard(PCB)
    ses = os.path.join(KDIR, "tracker.ses")
    ok = pcbnew.ImportSpecctraSES(board, ses)
    print("SES import", ok, "tracks", len(board.GetTracks()))
    vals = {p["ref"]: p["value"] for p in D.PARTS}
    for fp in board.GetFootprints():            # keep values in sync with design.py
        v = vals.get(fp.GetReference())
        if v and fp.GetValue() != v:
            fp.SetValue(v)
    print("EP vias", ep_vias(board))
    add_outer_pours(board)
    for z in board.Zones():
        if z.GetNetname() == "GND" and not z.GetIsRuleArea():
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    print("stitching vias", stitch(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("saved")


class Placer:
    """Anchor placement + greedy nearest-free placement of small parts (courtyard rectangles)."""

    def __init__(self, board, fps):
        self.board, self.fps, self.done = board, fps, set()
        self.obs = {"F": [], "B": []}
        self.cache = {}

    def _set(self, fp, x, y, rot, side):
        if (fp.GetLayer() == pcbnew.B_Cu) != (side == "B"):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pt(x, y))

    def _bbox(self, fp, side):
        lay = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
        cy = fp.GetCourtyard(lay)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
        return (pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY)

    def _register(self, ref, side):
        fp = self.fps[ref]
        self.obs[side].append((ref,) + self._bbox(fp, side))
        other = "B" if side == "F" else "F"
        for pad in fp.Pads():                       # through-holes block the other side too
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                bb = pad.GetBoundingBox()
                m = 0.25
                self.obs[other].append((ref + ":th", pcbnew.ToMM(bb.GetLeft()) - OX - m, pcbnew.ToMM(bb.GetTop()) - OY - m,
                                        pcbnew.ToMM(bb.GetRight()) - OX + m, pcbnew.ToMM(bb.GetBottom()) - OY + m))
        for z in fp.Zones():                        # rule areas forbidding footprints (antenna keep-out)
            if z.GetIsRuleArea() and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads()):
                bb = z.GetBoundingBox()
                r = (ref + ":ko", max(0, pcbnew.ToMM(bb.GetLeft()) - OX), max(0, pcbnew.ToMM(bb.GetTop()) - OY),
                     pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY)
                self.obs[other].append(r)

    def put(self, ref, x, y, rot, side):
        self._set(self.fps[ref], x, y, rot, side)
        self._register(ref, side)
        self.done.add(ref)

    def pad_xy(self, ref, num):
        for pad in self.fps[ref].Pads():
            if pad.GetNumber() == num:
                p = pad.GetPosition()
                return pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY
        raise KeyError(f"{ref}.{num}")

    def free(self, side, r):
        x0, y0, x1, y1 = r
        if x0 < 0.25 or y0 < 0.25 or x1 > BW - 0.25 or y1 > BH - 0.25:
            return False
        for o in self.obs[side]:
            if x0 < o[3] and o[1] < x1 and y0 < o[4] and o[2] < y1:
                return False
        return True

    def auto(self, ref, side, tgt):
        fp = self.fps[ref]
        tx, ty = self.pad_xy(*tgt) if isinstance(tgt[0], str) else tgt
        shapes = []
        for rot in (0, 90):
            self._set(fp, 0.0, 0.0, rot, side)
            bx = self._bbox(fp, side)
            shapes.append((rot, bx))
        best = None
        step = 0.2
        for ring in range(0, 120):
            rad = ring * step
            n = max(1, int(2 * math.pi * rad / step))
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = tx + rad * math.cos(a), ty + rad * math.sin(a)
                x, y = round(x / 0.05) * 0.05, round(y / 0.05) * 0.05
                for rot, (a0, b0, a1, b1) in shapes:
                    r = (x + a0, y + b0, x + a1, y + b1)
                    if self.free(side, r):
                        best = (x, y, rot)
                        break
                if best:
                    break
            if best:
                break
        if not best:
            print("NO ROOM for", ref)
            return
        self.put(ref, best[0], best[1], best[2], side)


def edge_keepout(board, w=0.5):
    """rule area along the outline: no tracks / vias within w of the edge (router honours it; pours allowed)"""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayerSet(pcbnew.LSET.AllCuMask(4))
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowFootprints(False)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in [(0, 0), (BW, 0), (BW, BH), (0, BH)]:
        ol.Append(mm(OX + x), mm(OY + y))
    ol.NewHole()
    for x, y in [(w, w), (w, BH - w), (BW - w, BH - w), (BW - w, w)]:
        ol.Append(mm(OX + x), mm(OY + y), -1, 0)
    z.SetZoneName("EDGE_KEEPOUT")
    board.Add(z)


def add_l3_pours(board):
    full = [(0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)]
    zone(board, "+3V3", pcbnew.In2_Cu, full, 0, "L3_3V3", clearance=0.2)


def add_outer_pours(board):
    full = [(0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)]
    zone(board, "GND", pcbnew.F_Cu, full, 0, "L1_GND", clearance=0.2)
    zone(board, "GND", pcbnew.B_Cu, full, 0, "L4_GND", clearance=0.2)


def courtyard_check(board):
    items = []
    for fp in board.GetFootprints():
        lay = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
        cy = fp.GetCourtyard(lay)
        if cy.OutlineCount() == 0:
            continue
        bb = cy.BBox()
        items.append((fp.GetReference(), fp.GetLayer(), pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                      pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY, cy))
    bad = []
    for i in range(len(items)):
        a = items[i]
        if a[2] < 0 or a[3] < 0 or a[4] > BW or a[5] > BH:
            bad.append(f"EDGE {a[0]} ({a[2]:.2f},{a[3]:.2f})-({a[4]:.2f},{a[5]:.2f})")
        for j in range(i + 1, len(items)):
            b = items[j]
            if a[1] != b[1] and not (a[0].startswith("H") or b[0].startswith("H")):
                continue
            if a[2] < b[4] and b[2] < a[4] and a[3] < b[5] and b[3] < a[5]:
                if a[6].Collide(b[6]):
                    ox = min(a[4], b[4]) - max(a[2], b[2]); oy = min(a[5], b[5]) - max(a[3], b[3])
                    bad.append(f"OVERLAP {a[0]} / {b[0]}  {ox:.2f} x {oy:.2f}")
    return bad


def apply_netclasses(board):
    ns = board.GetDesignSettings().m_NetSettings
    for name, (cl, tw, vd, vdr) in NETCLASS.items():
        nc = ns.GetDefaultNetclass() if name == "Default" else pcbnew.NETCLASS(name)
        nc.SetClearance(mm(cl)); nc.SetTrackWidth(mm(tw)); nc.SetViaDiameter(mm(vd)); nc.SetViaDrill(mm(vdr))
        nc.SetDiffPairWidth(mm(0.2)); nc.SetDiffPairGap(mm(0.2))
        if name != "Default":
            nc.SetPriority(10)
            ns.SetNetclass(name, nc)
    ns.ClearNetclassPatternAssignments()
    for cls, pats in NET_PATTERNS.items():
        for p in pats:
            ns.SetNetclassPatternAssignment(p, cls)
    ns.RecomputeEffectiveNetclasses()
    board.SynchronizeNetsAndNetClasses(True)


def write_project():
    pro = os.path.join(KDIR, "tracker.kicad_pro")
    try:
        data = json.load(open(pro))
    except Exception:
        data = {}
    data.setdefault("meta", {"filename": "tracker.kicad_pro", "version": 3})
    classes = []
    for name, (cl, tw, vd, vdr) in NETCLASS.items():
        classes.append({"name": name, "clearance": cl, "track_width": tw, "via_diameter": vd, "via_drill": vdr,
                        "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.2,
                        "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                        "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647
                        if name == "Default" else 10})
    pats = [{"netclass": k, "pattern": p} for k, v in NET_PATTERNS.items() for p in v]
    data["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                            "netclass_assignments": None, "netclass_patterns": pats}
    bd = data.setdefault("board", {}).setdefault("design_settings", {})
    bd["rules"] = {"min_clearance": 0.1, "min_track_width": 0.1, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2,
                   "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2,
                   "min_via_annular_width": 0.1, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
                   "solder_mask_to_copper_clearance": 0.0, "min_silk_clearance": 0.0, "min_text_height": 0.8,
                   "min_text_thickness": 0.08, "max_error": 0.005, "min_resolved_spokes": 1, "allow_blind_buried_vias": False,
                   "allow_microvias": False, "use_height_for_length_calcs": True}
    json.dump(data, open(pro, "w"), indent=2)


def render(board_path, out_png, layers, mirror=False):
    pass


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "place"
    if mode == "ses":
        finish()
    if mode == "dsn2":          # continue routing from the current board
        b = pcbnew.LoadBoard(PCB)
        for z in list(b.Zones()):
            if not z.GetIsRuleArea() and z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
                b.Remove(z)
        b.Save(PCB)
        print("dsn", pcbnew.ExportSpecctraDSN(b, os.path.join(KDIR, "tracker.dsn")))
    if mode in ("place", "dsn"):
        b = build(outer=(mode == "place"))
        bad = courtyard_check(b)
        print("\n".join(bad) if bad else "courtyards OK")
        route_rf(b)
        apply_netclasses(b)
        if mode == "dsn":
            fanout(b)
        b.Save(PCB)
        print("saved", PCB, len(b.GetFootprints()), "footprints", b.GetNetCount(), "nets")
        if mode == "dsn":
            b2 = pcbnew.LoadBoard(PCB)
            print("netclasses:", sorted(set(n.GetNetClassName() for n in b2.GetNetsByName().values())))
            ok = pcbnew.ExportSpecctraDSN(b2, os.path.join(KDIR, "tracker.dsn"))
            print("dsn", ok)
