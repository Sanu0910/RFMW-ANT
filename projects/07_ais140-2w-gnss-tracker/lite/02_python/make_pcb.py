"""Build the 2-layer Lite PCB from design.py with pcbnew (run inside the KiCad 9 Python).

  python3 make_pcb.py place     -> place footprints, nets, outline, zones; report courtyard overlaps
  python3 make_pcb.py dsn       -> place + RF lines + GND fan-out vias, export Specctra DSN for Freerouting
  python3 make_pcb.py ses       -> import the routed SES, purge clashing vias
  python3 make_pcb.py finish    -> GND pours on both layers, stitching / island vias, fill, save
  python3 make_pcb.py models    -> assign envelope STEP models

Coordinates in PLACE are board-local mm (origin = top-left board corner, +y down). All parts on the top side.
Stack-up: L1 signals + GND pour, L2 (bottom) solid GND with short signal jumpers only.
Same 60 x 45 mm outline and M2 holes as CRL-TRK-2W-01, so the Lite fits the same enclosure.
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
PCB = os.path.join(KDIR, "tracker_lite.kicad_pcb")
FPROOT = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board origin on the KiCad page
BW, BH, BR = 60.0, 45.0, 2.0   # board size and corner radius

# ------------------------------------------------------------------------------------ placement
# Anchors: hand-placed parts  ref: (x, y, rot).  Everything is on the top side.
PLACE = {
    # modem on the right; LTE RF leaves pad 49 eastwards and runs down the right edge to J4
    "U3": (42.5, 22.5, 0),
    "J4": (57.6, 41.9, 0), "R14": (58.45, 33.0, 270), "C19": (53.825, 40.6, 180),   # C19 pad 1 sits on the line
    # GNSS corner (top-left): module turned so RF_IN (pad 11) faces the top edge, U.FL straight above it
    "U5": (9.0, 11.3, 90), "J5": (13.5, 2.6, 0),
    # eSIM next to the modem's USIM pads
    "U8": (24.4, 23.1, 0),
    # vehicle connector and battery on the bottom edge, buck above them
    "J1": (8.0, 41.0, 0), "J2": (22.2, 31.3, 0),
    "L1": (8.6, 33.4, 0), "U1": (13.0, 24.6, 0),
    # mechanics (same as CRL-TRK-2W-01)
    "H1": (2.6, 42.4, 0), "H2": (2.6, 26.6, 0), "H3": (39.95, 2.6, 0), "H4": (33.2, 42.4, 0),
}

# Greedy-placed parts, in priority order: (ref, target) with target = (ref, pad) or (x, y)
SMALL = [
    # power input + buck
    ("D1", (6.0, 37.0)), ("F1", ("J1", "1")), ("D2", (5.0, 20.5)), ("C1", ("U1", "1")), ("C2", ("U1", "1")),
    ("C3", ("U1", "1")), ("D3", ("U1", "2")), ("R1", ("U1", "4")), ("R2", ("U1", "4")),
    ("C4", ("L1", "2")), ("C5", ("L1", "2")),
    # charger + power path
    ("D4", (17.5, 31.5)), ("Q1", ("J2", "1")), ("R4", ("Q1", "1")), ("U2", ("J2", "1")), ("C6", ("U2", "4")),
    ("C7", ("U2", "3")), ("R3", ("U2", "5")), ("R7", (25.0, 40.0)), ("R8", (25.0, 40.0)), ("C14", (25.0, 40.0)),
    ("R5", (21.0, 40.0)), ("R6", (21.0, 40.0)), ("C13", (21.0, 40.0)),
    # modem supply + RF
    ("C9", ("U3", "58")), ("C8", ("U3", "60")), ("D5", ("U3", "57")), ("C10", ("U3", "59")), ("C11", ("U3", "59")),
    ("C12", ("U3", "57")), ("C15", ("U3", "7")),
    # eSIM
    ("R11", ("U8", "3")), ("R12", ("U8", "6")), ("R13", ("U8", "7")), ("C17", ("U8", "8")),
    # GNSS support
    ("C22", ("U5", "8")),
    ("U6", (18.0, 9.0)), ("C21", ("U6", "5")), ("C20", ("U6", "1")), ("R15", ("U6", "3")),
    ("Q3", (22.0, 13.0)), ("Q4", (25.5, 13.0)), ("R18", (22.0, 16.0)), ("R19", (22.0, 10.0)),
    ("R20", (25.5, 16.0)), ("R21", (25.5, 10.0)),
    # PWRKEY
    ("Q2", ("U3", "21")), ("C16", ("U3", "21")), ("R9", ("U3", "21")), ("R10", ("U3", "21")),
    # accelerometer next to I2C (pins 41/42, right side bottom) and ACC_INT (pin 26, bottom side)
    ("U7", (48.0, 41.6)), ("C26", ("U7", "14")), ("C27", ("U7", "1")), ("R22", ("U7", "6")), ("R23", ("U7", "4")),
    ("R34", ("U7", "7")),
    # ignition + relay (strip under the modem)
    ("Q5", (37.5, 41.5)), ("R24", (40.5, 41.5)), ("R25", (37.5, 41.5)), ("R26", (37.5, 41.5)), ("C28", (40.5, 41.5)),
    ("C29", (37.5, 41.5)),
    ("Q6", (34.5, 4.5)), ("R27", ("Q6", "1")), ("R28", ("Q6", "1")), ("D6", ("J1", "4")),
    # LEDs on the top edge (light pipes in the lid)
    ("D8", (45.0, 1.4)), ("D7", (48.0, 1.4)), ("D9", (51.0, 1.4)),
    ("R32", (45.0, 3.6)), ("R30", (48.0, 3.6)), ("R33", (51.0, 3.6)),
    ("Q8", (54.5, 2.0)), ("Q7", (34.0, 2.0)), ("R31", (54.5, 4.5)), ("R29", (34.0, 4.5)),
    # test pads
    ("TP1", ("U3", "21")), ("TP2", ("U3", "20")), ("TP3", (28.0, 2.0)), ("TP4", (30.0, 2.0)), ("TP5", (32.0, 4.0)),
    ("TP6", ("U3", "12")), ("TP7", ("U3", "11")), ("TP8", ("U5", "9")), ("TP9", ("U5", "4")),
    ("TP10", ("C1", "1")), ("TP11", ("C4", "1")), ("TP12", ("C9", "1")), ("TP13", ("J2", "1")), ("TP14", ("C15", "1")),
    ("TP15", ("C21", "1")), ("TP16", (57.5, 2.5)), ("TP17", (28.0, 43.5)), ("TP18", ("Q5", "3")),
]

NETCLASS = {
    # name: (clearance, track, via_dia, via_drill)  - JLC standard 2-layer: 0.127 / 0.3 mm drill
    "Default": (0.15, 0.2, 0.6, 0.3),
    "Power": (0.2, 0.4, 0.8, 0.4),
    "HV": (0.25, 0.35, 0.8, 0.4),
    "RF50": (0.2, 1.2, 0.6, 0.3),
}
NET_PATTERNS = {
    "Power": ["VSYS", "VBAT", "V4_BUCK", "BUCK_SW", "+3V3_GNSS"],
    "HV": ["VIN_*", "IGN_RAW", "RELAY_OUT"],
    "RF50": ["LTE_RF*", "GNSS_RF*"],
}
RF_W = 1.2       # CPWG on 1.6 mm FR-4: 1.2 mm / 0.2 mm gap = 51 ohm (rf_calc.py)


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(KDIR, "lite.pretty") if lib == D.LIB else os.path.join(FPROOT, lib + ".pretty")
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


def zone(board, net, layer, poly, prio=0, name="", clearance=0.2, minw=0.2, thermal=0.3, spoke=0.4):
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
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


FULL = [(0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)]


def add_pours(board, top=True):
    zone(board, "GND", pcbnew.B_Cu, FULL, 0, "B_GND", clearance=0.25, minw=0.25)
    if top:
        zone(board, "GND", pcbnew.F_Cu, FULL, 0, "F_GND", clearance=0.2, minw=0.2)


def build(top_pour=False):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.127); ds.m_MinClearance = mm(0.127); ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3); ds.m_HoleToHoleMin = mm(0.25); ds.m_CopperEdgeClearance = mm(0.3)
    ds.SetBoardThickness(mm(1.6))
    ds.m_MinResolvedSpokes = 1
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
            elif num in pinname:
                pn = pinname.get(num, '').replace('/', '{slash}')
                pad.SetNet(net(f"unconnected-({p['ref']}-{pn}-Pad{num})"))
        fps[p["ref"]] = fp
    placer = Placer(board, fps)
    for ref, (x, y, rot) in PLACE.items():
        placer.put(ref, x, y, rot, "F")
    for net, pts, w in RF_ROUTES:                 # keep the RF lines free of parts (except their own)
        xy = [_xy(board, q) for q in pts]
        for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
            m = w / 2 + 0.35
            placer.obs["F"].append(("rf:" + net, min(x0, x1) - m, min(y0, y1) - m, max(x0, x1) + m, max(y0, y1) + m))
    for ref, tgt in SMALL:                        # test pads go on the bottom (pogo fixture, no assembly cost)
        placer.auto(ref, "B" if ref.startswith("TP") else "F", tgt)
    missing = [r for r in fps if r not in placer.done]
    if missing:
        print("NOT PLACED:", " ".join(missing))
    edge_keepout(board)
    add_pours(board, top=top_pour)
    return board


# Explicit RF lines: (net, [points]) where a point is (x, y) or (ref, pad) = that pad's centre.
RF_ROUTES = [
    ("LTE_RF_M", [("U3", "49"), (57.3, "U3.49")], 0.5),            # neck between the module's GND pads 48/50
    ("LTE_RF_M", [(57.3, "U3.49"), (58.45, "U3.49"), ("R14", "1")], RF_W),
    ("LTE_RF", [("R14", "2"), (58.45, 39.0), (54.6, 39.0), (54.6, "J4.1"), (55.9, "J4.1")], RF_W),
    ("LTE_RF", [(55.9, "J4.1"), ("J4", "1")], 0.5),     # U.FL keep-out right of pin 1: enter from the side
    ("GNSS_RF", [("U5", "11"), (12.3, 2.6), ("J5", "1")], 0.5),     # 4 mm long (0.035 lambda): 0.5 mm fits the LCC pitch
]


def pad_of(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(ref + "." + num)


def _xy(board, p):
    if isinstance(p[0], str):
        q = pad_of(board, *p).GetPosition()
        return pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY
    x, y = p
    if isinstance(y, str):                       # (x, "REF.PAD") = that pad's y
        y = _xy(board, tuple(y.split(".")))[1]
    return x, y


def add_track(board, a, b, w, layer, net, locked=True):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net); t.SetLocked(locked)
    board.Add(t)
    return t


def route_rf(board):
    for net, pts, w in RF_ROUTES:
        ni = board.FindNet(net)
        xy = [_xy(board, p) for p in pts]
        for p0, p1 in zip(xy, xy[1:]):
            add_track(board, pt(*p0), pt(*p1), w, pcbnew.F_Cu, ni)


FANOUT = {"GND": 0.4}   # net: stub width (mm)
VIA_D, VIA_DRILL, CLR = 0.6, 0.3, 0.2


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
        lay = it.GetLayer() if not isinstance(it, pcbnew.PAD) else (pcbnew.F_Cu if it.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
        return max(CLR, pcbnew.ToMM(it.GetOwnClearance(lay)))
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


def via_ok(board, pos, kos, items, netcode):
    x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
    if not in_outline(x, y, 0.8):
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
            if it.HitTest(pos, r + mm(0.35 if it.GetNetCode() == netcode else max(0.25, _clr(it) + 0.05))):
                return False
        else:
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


def all_items(board):
    return [p for p in board.GetPads()] + [t for t in board.GetTracks()]


def add_via(board, pos, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(net); board.Add(v)
    return v


def fanout(board):
    """every top-side GND SMD pad gets a short stub + via into the bottom GND plane"""
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    added = 0; failed = []
    for fp in board.GetFootprints():
        c0 = fp.GetPosition()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in FANOUT or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or fp.GetReference() in ("J4", "J5"):
                continue
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
                for extra in (0.0, 0.15, 0.3, 0.5, 0.75, 1.0):
                    d = edge + VIA_D / 2 + 0.12 + extra
                    pos = pcbnew.VECTOR2I(int(c.x + mm(d * ca)), int(c.y + mm(d * sa)))
                    if not via_ok(board, pos, kos, items, pad.GetNetCode()):
                        continue
                    if not seg_ok(board, c, pos, w, pcbnew.F_Cu, items, pad.GetNetCode(), pad):
                        continue
                    v = add_via(board, pos, pad.GetNet()); v.SetLocked(True)
                    t = add_track(board, c, pos, w, pcbnew.F_Cu, pad.GetNet())
                    items += [v, t]
                    added += 1; done = True
                    break
                if done:
                    break
            if not done:
                failed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    print(f"fanout: {added} vias, {len(failed)} GND pads left to the top pour: {' '.join(failed[:60])}")


def lga_vias(board):
    """GND vias in the gaps of the EC200U LGA grid (2.2 mm pitch pads): ties them to the bottom plane"""
    gnd = board.FindNet("GND")
    fp = board.FindFootprintByReference("U3")
    c = fp.GetPosition()
    n = 0
    for i in range(7):
        for j in range(7):
            pos = pcbnew.VECTOR2I(c.x + mm(-6.6 + 2.2 * i), c.y + mm(-6.6 + 2.2 * j))
            v = add_via(board, pos, gnd); v.SetLocked(True); n += 1
    return n


def purge_violating_vias(board):
    """drop GND fan-out vias (and their stubs) that break another net's clearance after routing"""
    pads = list(board.GetPads())
    tracks = list(board.GetTracks())
    bad = []
    for v in tracks:
        if not isinstance(v, pcbnew.PCB_VIA) or v.GetNetname() not in FANOUT:
            continue
        r = pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2
        hit = False
        for p in pads:
            if p.GetNetCode() == v.GetNetCode():
                continue
            lay = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            if p.GetEffectiveShape(lay).Collide(v.GetPosition(), mm(r + _clr(p) - 0.001)):
                hit = True; break
        if not hit:
            for t in tracks:
                if t is v or t.GetNetCode() == v.GetNetCode():
                    continue
                if t.GetEffectiveShape().Collide(v.GetPosition(), mm(r + _clr(t) - 0.001)):
                    hit = True; break
        if hit:
            bad.append(v)
    gone = set()
    for v in bad:
        for t in tracks:
            if id(t) in gone or isinstance(t, pcbnew.PCB_VIA) or t.GetNetCode() != v.GetNetCode():
                continue
            if t.GetStart() == v.GetPosition() or t.GetEnd() == v.GetPosition():
                board.Remove(t); gone.add(id(t))
        board.Remove(v); gone.add(id(v))
    return len(bad)


def stitch(board):
    """RF via fences, edge ring and an area grid tying the top GND pour to the bottom plane"""
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    n = 0

    def try_add(x, y):
        nonlocal n
        pos = pt(x, y)
        if via_ok(board, pos, kos, items, gnd.GetNetCode()):
            items.append(add_via(board, pos, gnd)); n += 1
            return True
        return False
    for t in list(board.GetTracks()):
        if t.GetNetClassName() != "RF50" or isinstance(t, pcbnew.PCB_VIA):
            continue
        a, b = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = (pcbnew.ToMM(a.x) - OX, pcbnew.ToMM(a.y) - OY, pcbnew.ToMM(b.x) - OX, pcbnew.ToMM(b.y) - OY)
        L = math.hypot(bx - ax, by - ay)
        if L < 0.3:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        off = pcbnew.ToMM(t.GetWidth()) / 2 + 0.25 + VIA_D / 2 + 0.05
        k = 0.0
        while k <= L:
            for sgn in (1, -1):
                try_add(ax + ux * k - uy * off * sgn, ay + uy * k + ux * off * sgn)
            k += 1.5
    e = 1.0
    for x in [e + i * 3.0 for i in range(int((BW - 2 * e) / 3.0) + 1)]:
        try_add(x, e); try_add(x, BH - e)
    for y in [e + i * 3.0 for i in range(int((BH - 2 * e) / 3.0) + 1)]:
        try_add(e, y); try_add(BW - e, y)
    for i in range(1, int(BW / 4)):
        for j in range(1, int(BH / 4) + 1):
            for dx, dy in ((0, 0), (0.6, 0), (0, 0.6), (-0.6, 0), (0, -0.6)):
                if try_add(i * 4.0 + dx, j * 4.0 - 1.0 + dy):
                    break
    return n


def stitch_islands(board):
    """put a GND via into every pour fragment (either layer) that has no via / THT pad in it"""
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    vias = [t.GetPosition() for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
    vias += [p.GetPosition() for p in board.GetPads() if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    added = 0
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetZoneName() not in ("F_GND", "B_GND"):
            continue
        polys = z.GetFilledPolysList(z.GetLayer())
        for k in range(polys.OutlineCount()):
            sub = pcbnew.SHAPE_POLY_SET(); sub.AddOutline(polys.Outline(k))
            if any(sub.Contains(v) for v in vias):
                continue
            bb = polys.Outline(k).BBox()
            done = False
            step = mm(0.2)
            y = bb.GetTop() + step
            while y < bb.GetBottom() and not done:
                x = bb.GetLeft() + step
                while x < bb.GetRight() and not done:
                    p = pcbnew.VECTOR2I(int(x), int(y))
                    if sub.Contains(p, -1, mm(0.4)) and via_ok(board, p, kos, items, gnd.GetNetCode()):
                        v = add_via(board, p, gnd); items.append(v); vias.append(p); added += 1; done = True
                    x += step
                y += step
    return added


def silk(board):
    """designators live on F.Fab (assembly drawing), silk keeps outlines, pin-1 marks and a few labels"""
    for fp in board.GetFootprints():
        for f in (fp.Reference(), fp.Value()):
            f.SetLayer(pcbnew.F_Fab); f.SetVisible(True)
            f.SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5))); f.SetTextThickness(mm(0.08))
        fp.Value().SetVisible(False)
        fp.Reference().SetPosition(fp.GetPosition())

    def text(s, x, y, layer, size=0.8):
        t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(pt(x, y)); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        board.Add(t)
    if not any(isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith("CRL-TRK") for d in board.GetDrawings()):
        text(f"{D.PN} {D.REV}", 30.0, 20.0, pcbnew.B_SilkS, 1.5)
        text("Samay Track 2W Lite", 30.0, 23.0, pcbnew.B_SilkS, 1.2)


def finish_ses():
    board = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ImportSpecctraSES(board, os.path.join(KDIR, "tracker_lite.ses"))
    print("SES import", ok, "tracks", len(board.GetTracks()))
    print("purged vias", purge_violating_vias(board))
    board.Save(PCB)


def finish():
    board = pcbnew.LoadBoard(PCB)
    silk(board)
    if not any(z.GetZoneName() == "F_GND" for z in board.Zones()):
        zone(board, "GND", pcbnew.F_Cu, FULL, 0, "F_GND", clearance=0.2, minw=0.2)
    # RF lines: wider clearance in the top pour (CPWG gap)
    print("stitching vias", stitch(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("island vias", stitch_islands(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("saved")


class Placer:
    """Anchor placement + greedy nearest-free placement of small parts (courtyard rectangles)."""

    def __init__(self, board, fps):
        self.board, self.fps, self.done = board, fps, set()
        self.obs = {"F": [], "B": []}

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
        for z in fp.Zones():                        # rule areas forbidding footprints / pads
            if z.GetIsRuleArea() and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads()):
                bb = z.GetBoundingBox()
                self.obs[side].append((ref + ":ko", pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                                       pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY))

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
        if side == "B":                           # bottom test pads: keep clear of top THT pads and the holes
            for o in self.obs["F"]:
                if o[0].startswith(("H", "J1")) and x0 < o[3] and o[1] < x1 and y0 < o[4] and o[2] < y1:
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
            shapes.append((rot, self._bbox(fp, side)))
        best = None
        step = 0.2
        for ring in range(0, 150):
            rad = ring * step
            n = max(1, int(2 * math.pi * rad / step))
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = round((tx + rad * math.cos(a)) / 0.05) * 0.05, round((ty + rad * math.sin(a)) / 0.05) * 0.05
                for rot, (a0, b0, a1, b1) in shapes:
                    if self.free(side, (x + a0, y + b0, x + a1, y + b1)):
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
    z.SetLayerSet(pcbnew.LSET.AllCuMask(2))
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


def courtyard_check(board):
    items = []
    for fp in board.GetFootprints():
        cy = fp.GetCourtyard(pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
        if cy.OutlineCount() == 0:
            continue
        bb = cy.BBox()
        items.append((fp.GetReference(), pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                      pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY, cy, fp.GetLayer()))
    bad = []
    for i, a in enumerate(items):
        if a[1] < 0 or a[2] < 0 or a[3] > BW or a[4] > BH:
            bad.append(f"EDGE {a[0]} ({a[1]:.2f},{a[2]:.2f})-({a[3]:.2f},{a[4]:.2f})")
        for b in items[i + 1:]:
            if a[6] != b[6] and not (a[0].startswith("H") or b[0].startswith("H")):
                continue
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4] and a[5].Collide(b[5]):
                bad.append(f"OVERLAP {a[0]} / {b[0]}")
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
    pro = os.path.join(KDIR, "tracker_lite.kicad_pro")
    try:
        data = json.load(open(pro))
    except Exception:
        data = {}
    data["meta"] = {"filename": "tracker_lite.kicad_pro", "version": 3}
    classes = []
    for name, (cl, tw, vd, vdr) in NETCLASS.items():
        classes.append({"name": name, "clearance": cl, "track_width": tw, "via_diameter": vd, "via_drill": vdr,
                        "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.2,
                        "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                        "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
                        "priority": 2147483647 if name == "Default" else 10})
    pats = [{"netclass": k, "pattern": p} for k, v in NET_PATTERNS.items() for p in v]
    data["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                            "netclass_assignments": None, "netclass_patterns": pats}
    bd = data.setdefault("board", {}).setdefault("design_settings", {})
    bd["rules"] = {"min_clearance": 0.127, "min_track_width": 0.127, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
                   "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
                   "min_via_annular_width": 0.1, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
                   "solder_mask_to_copper_clearance": 0.0, "min_silk_clearance": 0.0, "min_text_height": 0.6,
                   "min_text_thickness": 0.08, "max_error": 0.005, "min_resolved_spokes": 1, "allow_blind_buried_vias": False,
                   "allow_microvias": False, "use_height_for_length_calcs": True}
    json.dump(data, open(pro, "w"), indent=2)


MODELS = {"Quectel_EC200U_LCC-144": "Quectel_EC200U", "Quectel_L76K": "Quectel_L76K",
          "MFF2_eSIM_DFN-8_6x5mm": "MFF2_eSIM",
          "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal": "JST_PH_S2B-PH-SM4-TB",
          "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical": "JST_XH_B4B-XH-A"}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "place"
    if mode in ("place", "dsn"):
        b = build(top_pour=(mode == "place"))
        bad = courtyard_check(b)
        print("\n".join(bad) if bad else "courtyards OK")
        route_rf(b)
        apply_netclasses(b)
        write_project()
        if mode == "dsn":
            print("LGA vias", lga_vias(b))
            fanout(b)
        b.Save(PCB)
        print("saved", PCB, len(b.GetFootprints()), "footprints", b.GetNetCount(), "nets")
        if mode == "dsn":
            b2 = pcbnew.LoadBoard(PCB)
            print("dsn", pcbnew.ExportSpecctraDSN(b2, os.path.join(KDIR, "tracker_lite.dsn")))
    if mode == "ses":
        finish_ses()
    if mode == "finish":
        finish()
    if mode == "dsn2":          # continue routing the current board: pours out, DSN again (then ses + finish)
        b = pcbnew.LoadBoard(PCB)
        for z in list(b.Zones()):
            if not z.GetIsRuleArea():
                b.Remove(z)
        b.Save(PCB)
        print("dsn", pcbnew.ExportSpecctraDSN(b, os.path.join(KDIR, "tracker_lite.dsn")))
    if mode == "ses2":          # import a continued route: keep the B.Cu plane, redo pours in finish
        b = pcbnew.LoadBoard(PCB)
        print("SES import", pcbnew.ImportSpecctraSES(b, os.path.join(KDIR, "tracker_lite.ses")))
        add_pours(b, top=False)
        b.Save(PCB)
    if mode == "islands":
        b = pcbnew.LoadBoard(PCB)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        print("island vias", stitch_islands(b))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB)
    if mode == "patch":         # A* finisher for the DRC 'unconnected' list in /tmp/drc.json
        import patch_route
        patch_route.run(PCB)
    if mode == "models":
        b = pcbnew.LoadBoard(PCB)
        n = 0
        for fp in b.GetFootprints():
            name = fp.GetFPID().GetUniStringLibItemName()
            if name in MODELS:
                ms = fp.Models()
                while len(ms):
                    ms.pop()
                m = pcbnew.FP_3DMODEL(); m.m_Filename = "${KIPRJMOD}/3d/" + MODELS[name] + ".step"
                ms.append(m); n += 1
        b.Save(PCB)
        print("models assigned", n)
