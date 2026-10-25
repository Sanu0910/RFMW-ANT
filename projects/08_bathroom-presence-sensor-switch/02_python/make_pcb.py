"""Build the 2-layer SPS-24G-01 mains PCB from design.py with pcbnew (run inside the KiCad 9 Python).

  python3 make_pcb.py place   -> place footprints, nets, outline, isolation slot, keep-outs; report overlaps + isolation
  python3 make_pcb.py dsn     -> place + hand-routed mains tracks + export Specctra DSN for Freerouting (SELV nets)
  python3 make_pcb.py ses     -> import routed SES
  python3 make_pcb.py finish  -> LV-only GND pours, stitching, fill, silk, save
  python3 make_pcb.py models  -> assign envelope STEP models

Coordinates in PLACE are board-local mm (origin = top-left board corner, +y down). All parts on the top side.

ISOLATION PLAN (see 04_docs/SAFETY_REVIEW.md):
  * HIGH-VOLTAGE (mains) section:  x in [0.8 .. HV_MAX]      - AC input, protection, triac, opto output.
  * isolation corridor (no copper): x in [HV_MAX .. LV_MIN]  - >= 6 mm, with a routed Edge.Cuts slot.
  * LOW-VOLTAGE (SELV) section:    x in [LV_MIN .. BW-0.8]    - MCU, radar, UI, 5 V rail, opto input.
  Only PS1 (HLK-PM01) and U2 (MOC3063) bridge the corridor; no copper net crosses it.
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
PCB = os.path.join(KDIR, "bps_switch.kicad_pcb")
STOCKFP = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0           # board origin on the KiCad page
BW, BH, BR = 70.0, 56.0, 3.0    # board size and corner radius
# HORIZONTAL isolation split: HV = top strip (y < HVY), SELV = bottom (y > LVY), 6 mm corridor between.
HVY, LVY = 34.0, 40.0

# mains nets (all live/switched copper) and the SELV nets
HV_NETS = {"ACL_IN", "ACL_F", "ACN", "LAMP", "PSU_L", "TRIAC_MT", "TRIAC_G", "SNUB_M"}
HV_REFS = {"J1", "F1", "MOV1", "CX1", "RB1", "NTC1", "Q1", "RG1", "RS1", "CS1", "TP3"}   # fully-HV parts

# ---------------------------------------------------------------- placement anchors: ref -> (x, y, rot)
# Only the two parts that BRIDGE the isolation corridor and the corner holes are hard-anchored; everything
# else is greedy-placed (region-constrained) from a target seed, big parts first.
PLACE = {
    # HLK-PM01 stands vertical and bridges top->bottom: AC pads in HV (y<24), DC pads in SELV (y>30)
    "PS1": (18.0, 13.0, 270),
    # MOC3063 straddles the corridor: pins 4-6 (mains) in HV (y<28), pins 1-3 (SELV input) in LV (y>34)
    "U2": (40.0, 37.0, 90),
    # mounting holes (M3) in the corners
    "H1": (4.0, 4.0, 0), "H2": (4.0, 52.0, 0), "H3": (66.0, 4.0, 0), "H4": (66.0, 52.0, 0),
}

# greedy placement, big parts first: (ref, target) with target = (ref, pad) or (x, y). Region = HV_REFS else LV.
SMALL = [
    # --- big HV parts first (so the 17 mm MOV + 12 mm NTC claim contiguous space), across the top strip ---
    ("MOV1", (35.0, 20.0)), ("NTC1", (49.0, 20.0)), ("J1", (45.0, 6.0)), ("RS1", (59.0, 30.0)),
    ("Q1", (62.0, 4.0)), ("F1", (29.0, 6.0)), ("CX1", (62.0, 12.0)), ("RB1", (62.0, 16.0)),
    ("RG1", (50.0, 30.0)), ("CS1", (56.0, 25.0)), ("TP3", (33.0, 30.0)),
    # --- big SELV parts across the bottom ---
    ("CB1", (10.0, 40.0)), ("U1", (26.0, 40.0)), ("J3", (48.0, 54.0)), ("RV1", (6.0, 46.0)),
    ("SW1", (64.0, 47.0)), ("J2", (60.0, 36.0)), ("J4", (67.5, 43.0)), ("D1", (67.5, 37.0)),
    # --- small SELV passives near their devices ---
    ("C5", ("PS1", "4")), ("C1", ("U1", "8")), ("C2", ("U1", "8")), ("RR1", ("U1", "1")), ("C3", ("U1", "1")),
    ("R1", ("U2", "1")), ("C4", ("J3", "5")), ("C6", ("RV1", "2")),
    ("RL1", ("D1", "1")), ("RP1", ("SW1", "1")), ("RS2", ("SW1", "1")), ("CB2", ("SW1", "1")),
    ("TP1", (35.0, 35.0)), ("TP2", (39.0, 35.0)), ("TP4", (45.0, 35.0)), ("TP5", (54.0, 35.0)),
]

NETCLASS = {
    # name: (clearance, track, via_dia, via_drill)
    "Default": (0.2, 0.25, 0.6, 0.3),
    "SELV": (0.2, 0.4, 0.6, 0.3),
    # Mains: 0.8 mm functional clearance (routable past TO-220 / DIP pin pitches). The safety-critical
    # PRIMARY<->SECONDARY 6 mm creepage is enforced by the isolation corridor, not this value. Live-live
    # creepage on routed traces is reported in SAFETY_REVIEW (conformal coating required for < 2.5 mm).
    "Mains": (0.8, 1.2, 1.2, 0.6),
}
NET_PATTERNS = {
    "SELV": ["+5V", "GND"],
    "Mains": ["ACL_IN", "ACL_F", "ACN", "LAMP", "PSU_L", "TRIAC_MT", "TRIAC_G", "SNUB_M"],
}
MAINS_W = 1.2


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(KDIR, "bps.pretty") if lib == D.LIB else os.path.join(STOCKFP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def _seg(board, a, b):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a)); s.SetEnd(pt(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)


def _arc(board, c, start, ang):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetCenter(pt(*c)); s.SetStart(pt(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)


def outline(board):
    r = BR
    _seg(board, (r, 0), (BW - r, 0)); _seg(board, (BW, r), (BW, BH - r))
    _seg(board, (BW - r, BH), (r, BH)); _seg(board, (0, BH - r), (0, r))
    _arc(board, (BW - r, r), (BW - r, 0), 90); _arc(board, (BW - r, BH - r), (BW, BH - r), 90)
    _arc(board, (r, BH - r), (r, BH), 90); _arc(board, (r, r), (0, r), 90)
    # isolation slot: milled slots along the middle of the corridor, leaving bridges where PS1/U2 cross
    ys = (HVY + LVY) / 2
    w = 1.6
    for (x0, x1) in [(6.0, 36.0), (44.0, 64.0)]:          # bridges kept at the edges and around U2 (x~40)
        _seg(board, (x0, ys - w / 2), (x1, ys - w / 2)); _seg(board, (x0, ys + w / 2), (x1, ys + w / 2))
        _arc(board, (x0, ys), (x0, ys - w / 2), 180); _arc(board, (x1, ys), (x1, ys + w / 2), 180)


def zone_rect(board, net, layer, x0, y0, x1, y1, prio=0, name="", clearance=0.3, minw=0.25):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if net:
        z.SetNet(board.FindNet(net))
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        ol.Append(mm(OX + x), mm(OY + y))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(minw))
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


# SELV-only GND pour rectangle (the whole bottom section), minus the antenna keep-out handled separately
LVPOUR = (0.6, LVY + 0.2, BW - 0.6, BH - 0.6)


def add_pours(board, top=True):
    x0, y0, x1, y1 = LVPOUR
    zone_rect(board, "GND", pcbnew.B_Cu, x0, y0, x1, y1, 0, "B_GND", clearance=0.3, minw=0.25)
    if top:
        zone_rect(board, "F_GND", pcbnew.F_Cu, x0, y0, x1, y1, 0, "F_GND", clearance=0.25, minw=0.25)
        board.Zones()[-1].SetNet(board.FindNet("GND"))


def corridor_keepout(board):
    """no tracks / vias / pours in the isolation corridor (y HVY..LVY) on any layer"""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayerSet(pcbnew.LSET.AllCuMask(2))
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(True)
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(-1, HVY), (BW + 1, HVY), (BW + 1, LVY), (-1, LVY)]:
        ol.Append(mm(OX + x), mm(OY + y))
    z.SetZoneName("ISO_CORRIDOR")
    board.Add(z)


def antenna_keepout(board):
    """no copper pour in front of the standing LD2410B antenna (around J3)"""
    fp = board.FindFootprintByReference("J3")
    c = fp.GetPosition()
    cx, cy = pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayerSet(pcbnew.LSET.AllCuMask(2))
    z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(cx - 6, cy - 4), (cx + 6, cy - 4), (cx + 6, cy + 4), (cx - 6, cy + 4)]:
        ol.Append(mm(OX + min(BW - 0.3, max(0.3, x))), mm(OY + max(LVY + 0.1, y)))
    z.SetZoneName("ANTENNA_KEEPOUT")
    board.Add(z)


def build(top_pour=False):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.2); ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3); ds.m_HoleToHoleMin = mm(0.25); ds.m_CopperEdgeClearance = mm(0.3)
    ds.SetBoardThickness(mm(1.6))
    ds.m_MinResolvedSpokes = 1
    outline(board)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni); nets[n] = ni
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
                f.SetText(v); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab); fp.Add(f)
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
    for ref, tgt in SMALL:
        placer.auto(ref, "F", tgt)
    missing = [r for r in fps if r not in placer.done]
    if missing:
        print("NOT PLACED:", " ".join(missing))
    corridor_keepout(board)
    antenna_keepout(board)
    add_pours(board, top=top_pour)
    return board


# ---------------------------------------------------------------- explicit mains routing (top layer, wide, locked)
# each entry: (net, (refA,padA), (refB,padB)) -> one wide track between the two pad centres
MAINS_SEGS = [
    ("ACL_IN", ("J1", "1"), ("F1", "1")),
    ("ACL_F", ("F1", "2"), ("NTC1", "1")),
    ("ACL_F", ("NTC1", "1"), ("MOV1", "1")),
    ("ACL_F", ("MOV1", "1"), ("CX1", "1")),
    ("ACL_F", ("CX1", "1"), ("RB1", "1")),
    ("ACL_F", ("F1", "2"), ("Q1", "1")),
    ("ACL_F", ("Q1", "1"), ("U2", "6")),
    ("ACL_F", ("Q1", "1"), ("RS1", "1")),
    ("ACN", ("J1", "2"), ("MOV1", "2")),
    ("ACN", ("MOV1", "2"), ("CX1", "2")),
    ("ACN", ("CX1", "2"), ("RB1", "2")),
    ("ACN", ("MOV1", "2"), ("PS1", "2")),
    ("PSU_L", ("NTC1", "2"), ("PS1", "1")),
    ("LAMP", ("J1", "3"), ("Q1", "2")),
    ("LAMP", ("Q1", "2"), ("CS1", "2")),
    ("TRIAC_MT", ("U2", "4"), ("RG1", "1")),
    ("TRIAC_G", ("RG1", "2"), ("Q1", "3")),
    ("SNUB_M", ("RS1", "2"), ("CS1", "1")),
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


def route_mains(board):
    for netn, (ra, pa), (rb, pb) in MAINS_SEGS:
        ni = board.FindNet(netn)
        add_track(board, pad_of(board, ra, pa).GetPosition(), pad_of(board, rb, pb).GetPosition(),
                  MAINS_W, pcbnew.F_Cu, ni)


# ---------------------------------------------------------------- GND fan-out + stitching (LV section only)
FANOUT_W, VIA_D, VIA_DRILL, CLR = 0.4, 0.6, 0.3, 0.2


def in_lv(x, y, m=0.6):
    return m <= x <= BW - m and LVY + m <= y <= BH - m


FANOUT = {"GND": FANOUT_W}


def in_outline(x, y, m):
    """inside the rounded-rectangle board outline with margin m"""
    if x < m or y < m or x > BW - m or y > BH - m:
        return False
    for cx, cy in ((BR, BR), (BW - BR, BR), (BR, BH - BR), (BW - BR, BH - BR)):
        if abs(x - cx) <= BR and abs(y - cy) <= BR and ((x < BR) == (cx == BR)) and ((y < BR) == (cy == BR)):
            if math.hypot(x - cx, y - cy) > BR - m:
                return False
    return True


def all_items(board):
    return [p for p in board.GetPads()] + [t for t in board.GetTracks()]


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


def stitch_islands(board):
    """put a GND via into every pour fragment (either layer) that has no via / THT pad in it"""
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = all_items(board)
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
            bb = polys.Outline(k).BBox(); done = False; step = mm(0.2)
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


def _keepouts(board):
    return [z for z in board.Zones() if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowCopperPour())]


def _clr(it):
    try:
        lay = it.GetLayer() if not isinstance(it, pcbnew.PAD) else (pcbnew.F_Cu if it.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
        return max(CLR, pcbnew.ToMM(it.GetOwnClearance(lay)))
    except Exception:
        return CLR


def via_ok(board, pos, kos, items, netcode):
    x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
    if not in_lv(x, y, 0.8):
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


def add_via(board, pos, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(net); board.Add(v)
    return v


def fanout(board):
    """every LV GND SMD pad gets a short stub + via into the bottom GND plane"""
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    added, failed = 0, []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            c = pad.GetPosition()
            if not in_lv(pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY, 0.8):
                continue
            bb = pad.GetBoundingBox()
            hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
            done = False
            for dang in (0, 90, -90, 45, -45, 135, -135, 180):
                a = math.radians(dang); ca, sa = math.cos(a), math.sin(a)
                edge = 1.0 / max(1e-6, max(abs(ca) / max(hw, 1e-3), abs(sa) / max(hh, 1e-3)))
                for extra in (0.0, 0.2, 0.4, 0.7):
                    d = edge + VIA_D / 2 + 0.15 + extra
                    pos = pcbnew.VECTOR2I(int(c.x + mm(d * ca)), int(c.y + mm(d * sa)))
                    if via_ok(board, pos, kos, items, pad.GetNetCode()):
                        v = add_via(board, pos, gnd); v.SetLocked(True)
                        t = add_track(board, c, pos, FANOUT_W, pcbnew.F_Cu, gnd)
                        items += [v, t]; added += 1; done = True; break
                if done:
                    break
            if not done:
                failed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    print(f"fanout: {added} vias, {len(failed)} GND pads left to the pour: {' '.join(failed[:40])}")


def stitch(board):
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = [p for p in board.GetPads()] + [t for t in board.GetTracks()]
    n = 0
    for i in range(1, int(BW / 4)):
        for j in range(1, int(BH / 4) + 1):
            x, y = i * 4.0, j * 4.0 - 1.0
            if in_lv(x, y, 1.5):
                pos = pt(x, y)
                if via_ok(board, pos, kos, items, gnd.GetNetCode()):
                    items.append(add_via(board, pos, gnd)); n += 1
    return n


# ---------------------------------------------------------------- Placer (region-constrained)
class Placer:
    def __init__(self, board, fps):
        self.board, self.fps, self.done = board, fps, set()
        self.obs = []

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

    def put(self, ref, x, y, rot, side):
        self._set(self.fps[ref], x, y, rot, side)
        self.obs.append((ref,) + self._bbox(self.fps[ref], side))
        self.done.add(ref)

    def pad_xy(self, ref, num):
        for pad in self.fps[ref].Pads():
            if pad.GetNumber() == num:
                p = pad.GetPosition()
                return pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY
        raise KeyError(f"{ref}.{num}")

    def region(self, ref):
        return "HV" if ref in HV_REFS else "LV"

    def free(self, ref, r):
        x0, y0, x1, y1 = r
        if x0 < 0.6 or y0 < 0.6 or x1 > BW - 0.6 or y1 > BH - 0.6:
            return False
        if self.region(ref) == "HV":                 # keep HV parts above the corridor
            if y1 > HVY - 0.2:
                return False
        else:                                         # keep SELV parts below the corridor
            if y0 < LVY + 0.2:
                return False
        for o in self.obs:
            if x0 < o[3] and o[1] < x1 and y0 < o[4] and o[2] < y1:
                return False
        return True

    def auto(self, ref, side, tgt):
        fp = self.fps[ref]
        tx, ty = self.pad_xy(*tgt) if isinstance(tgt[0], str) else tgt
        shapes = []
        for rot in (0, 90, 180, 270):
            self._set(fp, 0.0, 0.0, rot, side)
            shapes.append((rot, self._bbox(fp, side)))
        best = None
        for ring in range(0, 240):
            rad = ring * 0.2
            n = max(1, int(2 * math.pi * rad / 0.2))
            for k in range(n):
                a = 2 * math.pi * k / n
                x = round((tx + rad * math.cos(a)) / 0.05) * 0.05
                y = round((ty + rad * math.sin(a)) / 0.05) * 0.05
                for rot, (a0, b0, a1, b1) in shapes:
                    if self.free(ref, (x + a0, y + b0, x + a1, y + b1)):
                        best = (x, y, rot); break
                if best:
                    break
            if best:
                break
        if not best:                                  # fallback: exhaustive grid scan of the allowed region
            ys = (0.8, HVY) if self.region(ref) == "HV" else (LVY, BH - 0.8)
            gy = ys[0]
            while gy < ys[1] and not best:
                gx = 0.8
                while gx < BW - 0.8 and not best:
                    for rot, (a0, b0, a1, b1) in shapes:
                        if self.free(ref, (gx + a0, gy + b0, gx + a1, gy + b1)):
                            best = (gx, gy, rot); break
                    gx += 0.5
                gy += 0.5
        if not best:
            print("NO ROOM for", ref); return
        self.put(ref, best[0], best[1], best[2], side)


# ---------------------------------------------------------------- checks
def courtyard_check(board):
    items = []
    for fp in board.GetFootprints():
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() == 0:
            continue
        bb = cy.BBox()
        items.append((fp.GetReference(), pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                      pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY, cy))
    bad = []
    for i, a in enumerate(items):
        if a[1] < 0 or a[2] < 0 or a[3] > BW or a[4] > BH:
            bad.append(f"EDGE {a[0]} ({a[1]:.1f},{a[2]:.1f})-({a[3]:.1f},{a[4]:.1f})")
        for b in items[i + 1:]:
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4] and a[5].Collide(b[5]):
                bad.append(f"OVERLAP {a[0]} / {b[0]}")
    return bad


def isolation_check(board):
    """report any HV-net copper below HVY, or SELV copper above LVY, and the min HV<->SELV gap"""
    bad = []
    for pad in board.GetPads():
        n = pad.GetNetname()
        y = pcbnew.ToMM(pad.GetPosition().y) - OY
        ref = pad.GetParentFootprint().GetReference()
        if n in HV_NETS:
            if y > HVY:
                bad.append(f"HV pad in corridor/SELV: {ref}.{pad.GetNumber()} ({n}) y={y:.1f}")
        elif n and not n.startswith("unconnected"):
            # SELV nets (incl. the bridging parts' SELV pins) must sit at or below the SELV boundary
            if y < LVY:
                bad.append(f"SELV pad in corridor/HV: {ref}.{pad.GetNumber()} ({n}) y={y:.1f}")
    # min centre distance HV-pad to any SELV-pad
    mind = 999
    for pad in board.GetPads():
        if pad.GetNetname() not in HV_NETS:
            continue
        pa = pad.GetPosition()
        for q in board.GetPads():
            nq = q.GetNetname()
            if nq in HV_NETS or not nq or nq.startswith("unconnected"):
                continue
            d = (pa - q.GetPosition()).EuclideanNorm()
            mind = min(mind, pcbnew.ToMM(d))
    return bad, mind


def apply_netclasses(board):
    ns = board.GetDesignSettings().m_NetSettings
    for name, (cl, tw, vd, vdr) in NETCLASS.items():
        nc = ns.GetDefaultNetclass() if name == "Default" else pcbnew.NETCLASS(name)
        nc.SetClearance(mm(cl)); nc.SetTrackWidth(mm(tw)); nc.SetViaDiameter(mm(vd)); nc.SetViaDrill(mm(vdr))
        if name != "Default":
            nc.SetPriority(10); ns.SetNetclass(name, nc)
    ns.ClearNetclassPatternAssignments()
    for cls, pats in NET_PATTERNS.items():
        for p in pats:
            ns.SetNetclassPatternAssignment(p, cls)
    ns.RecomputeEffectiveNetclasses()
    board.SynchronizeNetsAndNetClasses(True)


def write_project():
    pro = os.path.join(KDIR, "bps_switch.kicad_pro")
    try:
        data = json.load(open(pro))
    except Exception:
        data = {}
    data["meta"] = {"filename": "bps_switch.kicad_pro", "version": 3}
    classes = []
    for name, (cl, tw, vd, vdr) in NETCLASS.items():
        classes.append({"name": name, "clearance": cl, "track_width": tw, "via_diameter": vd, "via_drill": vdr,
                        "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
                        "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                        "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
                        "priority": 2147483647 if name == "Default" else 10})
    pats = [{"netclass": k, "pattern": p} for k, v in NET_PATTERNS.items() for p in v]
    data["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                            "netclass_assignments": None, "netclass_patterns": pats}
    bd = data.setdefault("board", {}).setdefault("design_settings", {})
    bd["rules"] = {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
                   "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
                   "min_via_annular_width": 0.1, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
                   "solder_mask_to_copper_clearance": 0.0, "min_silk_clearance": 0.0, "min_text_height": 0.6,
                   "min_text_thickness": 0.08, "max_error": 0.005, "min_resolved_spokes": 1,
                   "allow_blind_buried_vias": False, "allow_microvias": False, "use_height_for_length_calcs": True}
    json.dump(data, open(pro, "w"), indent=2)


def silk(board):
    for fp in board.GetFootprints():
        for f in (fp.Reference(), fp.Value()):
            f.SetLayer(pcbnew.F_Fab); f.SetVisible(True)
            f.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6))); f.SetTextThickness(mm(0.1))
        fp.Value().SetVisible(False)
        fp.Reference().SetPosition(fp.GetPosition())

    def text(s, x, y, layer, size=1.0, angle=0):
        t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(pt(x, y)); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
        if angle:
            t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        board.Add(t)
    if not any(isinstance(d, pcbnew.PCB_TEXT) and "HIGH VOLTAGE" in d.GetText() for d in board.GetDrawings()):
        text(f"SAMAY ELECTRONICS  {D.PN} {D.REV}", 38.0, 26.9, pcbnew.F_SilkS, 0.9)
        text("!! HIGH VOLTAGE - RISK OF SHOCK !!", 33.0, 1.4, pcbnew.F_SilkS, 1.1)
        text("SELV / ISOLATED 5V", 3.0, 51.0, pcbnew.F_SilkS, 0.9)
        text(f"{D.PN} {D.REV}  Do not energise without isolation/HIPOT test", 10.0, 27.0, pcbnew.B_SilkS, 1.0)


def finish():
    board = pcbnew.LoadBoard(PCB)
    silk(board)
    names = {z.GetZoneName() for z in board.Zones()}
    x0, y0, x1, y1 = LVPOUR
    if "B_GND" not in names:
        zone_rect(board, "GND", pcbnew.B_Cu, x0, y0, x1, y1, 0, "B_GND", clearance=0.3, minw=0.25)
    if "F_GND" not in names:
        z = zone_rect(board, "GND", pcbnew.F_Cu, x0, y0, x1, y1, 0, "F_GND", clearance=0.25, minw=0.25)
    print("fanout + stitch:")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("  stitch vias", stitch(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("saved", PCB)


def tie_fragments(board):
    """join all GND pour fragments (both layers) into one net: union-find over the fragments, existing vias and
    THT pads are the edges, then a via goes into the overlap of any top/bottom pair still in different groups"""
    gnd = board.FindNet("GND")
    kos = _keepouts(board)
    items = all_items(board)
    frags = []                                   # (layer, SHAPE_POLY_SET)
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetZoneName() not in ("F_GND", "B_GND"):
            continue
        ps = z.GetFilledPolysList(z.GetLayer())
        for k in range(ps.OutlineCount()):
            s = pcbnew.SHAPE_POLY_SET(); s.AddOutline(ps.Outline(k))
            frags.append((z.GetLayer(), s))
    par = list(range(len(frags)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i

    def union(i, j):
        par[find(i)] = find(j)
    links = [t.GetPosition() for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
    links += [q.GetPosition() for q in board.GetPads() if q.GetNetname() == "GND" and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for pos in links:
        hit = [i for i, (_, s) in enumerate(frags) if s.Contains(pos)]
        for i in hit[1:]:
            union(hit[0], i)
    added = 0
    tops = [i for i, f in enumerate(frags) if f[0] == pcbnew.F_Cu]
    bots = [i for i, f in enumerate(frags) if f[0] == pcbnew.B_Cu]
    for i in sorted(tops, key=lambda i: frags[i][1].Area()):
        for j in sorted(bots, key=lambda j: -frags[j][1].Area()):
            if find(i) == find(j):
                continue
            inter = pcbnew.SHAPE_POLY_SET(frags[i][1]); inter.BooleanIntersection(frags[j][1])
            if inter.OutlineCount() == 0:
                continue
            bb = inter.BBox(); step = mm(0.15); done = False
            y = bb.GetTop() + step
            while y < bb.GetBottom() and not done:
                x = bb.GetLeft() + step
                while x < bb.GetRight() and not done:
                    q = pcbnew.VECTOR2I(int(x), int(y))
                    if inter.Contains(q, -1, mm(0.35)) and via_ok(board, q, kos, items, gnd.GetNetCode()):
                        items.append(add_via(board, q, gnd)); added += 1; done = True
                        union(i, j)
                    x += step
                y += step
    groups = len({find(i) for i in range(len(frags))})
    print("GND pour groups after tie:", groups)
    return added


def merge_close_vias(board):
    """two same-net vias closer than the hole-to-hole rule: move the track ends of one onto the other"""
    vias = [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
    gone, n = set(), 0
    for i, a in enumerate(vias):
        for b in vias[i + 1:]:
            if id(a) in gone or id(b) in gone or a.GetNetCode() != b.GetNetCode():
                continue
            if (a.GetPosition() - b.GetPosition()).EuclideanNorm() < mm(0.9):
                pa, pb = a.GetPosition(), b.GetPosition()
                for t in board.GetTracks():
                    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetCode() != a.GetNetCode():
                        continue
                    if t.GetStart() == pb:
                        t.SetStart(pa)
                    if t.GetEnd() == pb:
                        t.SetEnd(pa)
                board.Remove(b); gone.add(id(b)); n += 1
    return n


MODELS = {"LD2410B_Module": "LD2410B_Module", "Varistor_Disc_D16mm_P7.5mm": "Varistor_Disc_D16mm_P7.5mm", "NTC_Disc_D11mm_P5mm": "NTC_Disc_D11mm_P5mm", "Fuse_TR5_P5.08mm": "Fuse_TR5_P5.08mm"}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "place"
    if mode in ("place", "dsn"):
        b = build(top_pour=(mode == "place"))
        bad = courtyard_check(b)
        print("COURTYARD:", "\n ".join(bad) if bad else "OK")
        isob, mind = isolation_check(b)
        print("ISOLATION:", "\n ".join(isob) if isob else "no HV copper in corridor/LV")
        print(f"min HV<->SELV pad-centre distance: {mind:.2f} mm (target >= 6 mm creepage edge-to-edge)")
        apply_netclasses(b)
        write_project()
        if mode == "dsn":
            fanout(b)
        b.Save(PCB)
        print("saved", PCB, len(b.GetFootprints()), "footprints", b.GetNetCount(), "nets")
        if mode == "dsn":
            b2 = pcbnew.LoadBoard(PCB)
            print("dsn", pcbnew.ExportSpecctraDSN(b2, os.path.join(KDIR, "bps_switch.dsn")))
    if mode == "ses":
        b = pcbnew.LoadBoard(PCB)
        print("SES import", pcbnew.ImportSpecctraSES(b, os.path.join(KDIR, "bps_switch.ses")))
        for z in list(b.Zones()):               # drop any existing pours so they don't stack across re-runs
            if not z.GetIsRuleArea():
                b.Remove(z)
        add_pours(b, top=False)
        b.Save(PCB)
    if mode == "finish":
        finish()
    if mode == "tie":
        b = pcbnew.LoadBoard(PCB)
        silk(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        print("fragment vias", tie_fragments(b))
        print("merged vias", merge_close_vias(b))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB); print("saved")
    if mode == "patch":          # A* finisher for the DRC 'unconnected' list in /tmp/drc.json
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
        b.Save(PCB); print("models assigned", n)
