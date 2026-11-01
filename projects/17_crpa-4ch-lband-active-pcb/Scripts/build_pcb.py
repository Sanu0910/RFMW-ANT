"""Build KiCad/CRPA17_4CH_LBAND.kicad_pcb with the KiCad 10 pcbnew API.

Run with KiCad's own Python:
    "C:/Program Files/KiCad/10.0/bin/python.exe" build_pcb.py

One channel (element 0, top-left) is placed and routed in its local frame; the other
three are the same layout rotated by -90/-180/-270 deg about the array centre, so all
four channels are electrically identical (sequential rotation, as the antenna modules).
Every track ends on a pad read back from the board, so connectivity follows the
footprints, not hand-typed coordinates.
"""
import json
import math
import os
import sys
from pathlib import Path

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import crpa_design as D  # noqa: E402

PROJ = HERE.parent
KDIR = PROJ / "KiCad"
PCB_FILE = KDIR / "CRPA17_4CH_LBAND.kicad_pcb"
STD_FP = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", "C:/Program Files/KiCad/10.0/share/kicad/footprints"))

board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
NETS = {}
ITEMS = []          # every item created for the current element (for the rotation copy)
FPS = {}            # ref -> footprint
BOM = []            # (ref, part key, channel)
RF_TRACKS = []      # (x1, y1, x2, y2) board mm, for the via fence


def net(name):
    if name not in NETS:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        NETS[name] = n
    return NETS[name]


def P(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def xy(v):
    return (ToMM(v.x), ToMM(v.y))


# ----------------------------------------------------------------------------- frames
CX, CY = D.ARRAY_CENTER
EX, EY = D.ELEMENT0_OFFSET


def L(lx, ly):
    """element-0 local -> board (before the per-element rotation)."""
    return (CX + EX + lx, CY + EY + ly)


def toL(bx, by):
    return (bx - CX - EX, by - CY - EY)


# ----------------------------------------------------------------------------- footprints
def load_fp(lib, name):
    path = str(KDIR / f"{lib}.pretty") if lib == D.LIB else str(STD_FP / f"{lib}.pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"footprint {lib}:{name} not found")
    return fp


def add_fp(ref, key, ch, back=True, at=(0, 0), rot=0.0, pads=None, show_ref=True):
    lib, name, value, *_ = D.PARTS[key]
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)
    fp.SetPosition(P(*L(*at)))
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    fp.Reference().SetTextSize(P(0.5, 0.5))
    fp.Reference().SetTextThickness(FromMM(0.08))
    fp.Reference().SetVisible(show_ref)
    fp.Value().SetVisible(False)
    for pnum, nname in (pads or {}).items():
        for pad in fp.Pads():
            if pad.GetNumber() == pnum:
                pad.SetNet(net(nname))
    FPS[ref] = fp
    ITEMS.append(fp)
    BOM.append((ref, key, ch))
    return fp


def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(f"{fp.GetReference()} pad {num}")


def padL(fp, num):
    return toL(*xy(pad(fp, num).GetPosition()))


def orient(fp, a, b, ux, uy, step=45):
    """Rotate fp so the pad vector a->b points as close as possible to (ux, uy)."""
    best = None
    for deg in range(0, 360, step):
        fp.SetOrientationDegrees(deg)
        ax, ay = padL(fp, a)
        bx, by = padL(fp, b)
        vx, vy = bx - ax, by - ay
        n = math.hypot(vx, vy) or 1
        score = (vx * ux + vy * uy) / n
        if best is None or score > best[0] + 1e-6:
            best = (score, deg)
    fp.SetOrientationDegrees(best[1])
    return best[1]


def move_pad_to(fp, num, lx, ly):
    px, py = padL(fp, num)
    fx, fy = toL(*xy(fp.GetPosition()))
    fp.SetPosition(P(*L(fx + lx - px, fy + ly - py)))


# ----------------------------------------------------------------------------- copper
def track(pts, nname, w=D.RF_W, layer=pcbnew.B_Cu, rf=False):
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        if math.hypot(x2 - x1, y2 - y1) < 1e-4:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(*L(x1, y1)))
        t.SetEnd(P(*L(x2, y2)))
        t.SetWidth(FromMM(w))
        t.SetLayer(layer)
        t.SetNet(net(nname))
        board.Add(t)
        ITEMS.append(t)
        if rf:
            RF_TRACKS.append(t)


def via(lx, ly, nname, d=D.VIA_D, drill=D.VIA_DRILL):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(*L(lx, ly)))
    v.SetWidth(FromMM(d))
    v.SetDrill(FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net(nname))
    board.Add(v)
    ITEMS.append(v)
    return v


def rf_link(a, b, nname, neck_a=False, neck_b=False, mid=None):
    """50-ohm link between two local points; optional 0.6 mm neck-down at either end."""
    pts = [a] + (mid or []) + [b]
    segs = list(zip(pts[:-1], pts[1:]))
    out = []
    for i, (p, q) in enumerate(segs):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy)
        ux, uy = (dx / n, dy / n) if n else (0, 0)
        s, e = p, q
        if i == 0 and neck_a and n > 0.7:
            s = (p[0] + 0.6 * ux, p[1] + 0.6 * uy)
            track([p, s], nname, D.RF_NECK_W)
        if i == len(segs) - 1 and neck_b and n > 0.7:
            e = (q[0] - 0.6 * ux, q[1] - 0.6 * uy)
            track([e, q], nname, D.RF_NECK_W)
        out.append((s, e))
    for s, e in out:
        track([s, e], nname, D.RF_W, rf=True)


FINE = {"TQP3M9037_DFN8_2x2", "B7504_SAW_0.9x0.7", "B8889_SAW_1.1x0.9", "DXP.02.A"}


def is_fine(fp):
    return fp.GetFPID().GetLibItemName().wx_str() in FINE


class Chain:
    """Walks an RF chain: current point + direction; parts are placed in-line."""

    def __init__(self, fp, pin, nname, u):
        self.fp, self.pin, self.net = fp, pin, nname
        self.p = padL(fp, pin)
        self.u = u

    def to(self, lx, ly):
        """Track from the current point to a corner (local), then continue from there."""
        self._pending = getattr(self, "_pending", []) + [(lx, ly)]
        self.p = (lx, ly)

    def turn(self, ux, uy):
        self.u = (ux, uy)

    def part(self, fp, pin_in, pin_out, gap, out_net, keep=False):
        ux, uy = self.u
        if not keep:
            orient(fp, pin_in, pin_out, ux, uy, step=90 if abs(ux * uy) < 1e-9 else 45)
        tx, ty = self.p[0] + gap * ux, self.p[1] + gap * uy
        move_pad_to(fp, pin_in, tx, ty)
        start = padL(self.fp, self.pin)
        mids = getattr(self, "_pending", [])
        rf_link(start, (tx, ty), self.net, neck_a=is_fine(self.fp), neck_b=is_fine(fp), mid=mids)
        self._pending = []
        self.fp, self.pin, self.net = fp, pin_out, out_net
        self.p = padL(fp, pin_out)
        return fp

    def end(self, fp, pin, mid=None):
        start = padL(self.fp, self.pin)
        rf_link(start, padL(fp, pin), self.net, neck_a=is_fine(self.fp), neck_b=is_fine(fp),
                mid=(getattr(self, "_pending", []) + (mid or [])))
        self._pending = []


def shunt(ref, key, ch, node_fp, node_pin, sig_net, nx, ny, off=0.9, gnd_net="GND", other=None, via_d=0.75,
          shift=0.0):
    """Two-pad part from a signal pad to GND (or `other` net), perpendicular to the line."""
    fp = add_fp(ref, key, ch, pads={"1": sig_net, "2": other or gnd_net}, show_ref=False)
    orient(fp, "1", "2", nx, ny, step=45)
    sx, sy = padL(node_fp, node_pin)
    move_pad_to(fp, "1", sx + off * nx - shift * ny, sy + off * ny + shift * nx)
    track([(sx, sy), padL(fp, "1")], sig_net, D.RF_W if other is None else D.PWR_W)
    gx, gy = padL(fp, "2")
    if other is None:
        vx, vy = gx + via_d * nx, gy + via_d * ny
        track([(gx, gy), (vx, vy)], gnd_net, D.GND_W)
        via(vx, vy, gnd_net)
    return fp


def gnd_stub(fp, num, nx, ny, dist=0.75):
    gx, gy = padL(fp, num)
    vx, vy = gx + dist * nx, gy + dist * ny
    track([(gx, gy), (vx, vy)], "GND", D.GND_W)
    via(vx, vy, "GND")


# ----------------------------------------------------------------------------- one element
def build_element(k):
    ch = D.CHANNEL_NAMES[k]
    n = k + 1
    s = lambda name: f"{ch}_{name}"  # noqa: E731
    r = lambda base: f"{base}{n}"    # noqa: E731  (refs: e.g. U1x -> U11.. per channel)

    # antenna module (top side), customer orientation for element 0
    ant = add_fp(f"ANT{n}", "ANT", ch, back=False, at=(0, 0), rot=0,
                 pads={"C": s("ANT_STUD"), "L1_0": s("L1_F0"), "L1_90": s("L1_F90"),
                       "L2_0": s("L2_F0"), "L2_90": s("L2_F90")})
    for p in ant.Pads():
        p.SetLocalClearance(D.ANT_FEED_ANTIPAD and FromMM(D.ANT_FEED_ANTIPAD))

    # ---- L1 hybrid: pins 3/4 face the L1 feeds (L1_90 -> 3, L1_0 -> 4: customer mapping)
    d1 = (-1 / math.sqrt(2), 1 / math.sqrt(2))     # outward diagonal of the L1 feeds
    h1 = add_fp(f"HY{n}1", "HYB", ch, pads={"1": s("L1_HYB"), "2": s("L1_ISO"), "3": s("L1_F90"),
                                              "4": s("L1_F0"), "GND": "GND"})
    orient(h1, "4", "3", 1 / math.sqrt(2), 1 / math.sqrt(2))
    m = 6.45
    a4, a3 = padL(h1, "4"), padL(h1, "3")
    mx, my = (a4[0] + a3[0]) / 2, (a4[1] + a3[1]) / 2
    fx, fy = toL(*xy(h1.GetPosition()))
    h1.SetPosition(P(*L(fx + m * d1[0] - mx, fy + m * d1[1] - my)))
    _check_far(h1, ("1", "2"), ("3", "4"))
    rf_link(padL(ant, "L1_0"), padL(h1, "4"), s("L1_F0"))
    rf_link(padL(ant, "L1_90"), padL(h1, "3"), s("L1_F90"))
    hyb_gnd_vias(h1)

    # ---- L2 hybrid (customer pose): pins 3/4 face the L2 feeds (L2_0 -> 3, L2_90 -> 4)
    d2 = (1 / math.sqrt(2), -1 / math.sqrt(2))
    h2 = add_fp(f"HY{n}2", "HYB", ch, pads={"1": s("L2_HYB"), "2": s("L2_ISO"), "3": s("L2_F0"),
                                              "4": s("L2_F90"), "GND": "GND"})
    orient(h2, "3", "4", 1 / math.sqrt(2), 1 / math.sqrt(2))
    m = 8.66 + 1.4
    a4, a3 = padL(h2, "4"), padL(h2, "3")
    mx, my = (a4[0] + a3[0]) / 2, (a4[1] + a3[1]) / 2
    fx, fy = toL(*xy(h2.GetPosition()))
    h2.SetPosition(P(*L(fx + m * d2[0] - mx, fy + m * d2[1] - my)))
    _check_far(h2, ("1", "2"), ("3", "4"))
    # feeds are 17.3 mm apart, pins 5.96 mm: equal-length L-shaped links
    for fpin, hpin in (("L2_0", "3"), ("L2_90", "4")):
        fpx, fpy = padL(ant, fpin)
        hpx, hpy = padL(h2, hpin)
        # leave the feed along the hybrid row direction, then straight onto the pin
        t = ((hpx - fpx) * d2[0] + (hpy - fpy) * d2[1])
        corner = (fpx + t * d2[0], fpy + t * d2[1])
        rf_link((fpx, fpy), (hpx, hpy), s("L2_F0" if fpin == "L2_0" else "L2_F90"), mid=[corner])
    hyb_gnd_vias(h2)

    # isolated-port loads
    for h, band, d in ((h1, "L1", d1), (h2, "L2", d2)):
        # load leaves pin 2 sideways (along the pin row, away from pin 1), clear of the limiter
        a1, a2 = padL(h, "1"), padL(h, "2")
        ln = math.hypot(a2[0] - a1[0], a2[1] - a1[1])
        shunt(f"R{n}{'1' if band == 'L1' else '2'}", "R50", ch, h, "2", s(f"{band}_ISO"),
              (a2[0] - a1[0]) / ln, (a2[1] - a1[1]) / ln, off=2.9)

    # ---- L1 chain -----------------------------------------------------------------
    c = Chain(h1, "1", s("L1_HYB"), (0.0, 1.0))
    p1 = padL(h1, "1")
    q1 = (p1[0] + 1.6 * d1[0], p1[1] + 1.6 * d1[1])    # leave pin 1 outward, clear of the GND cross
    c.to(*q1)
    LINE1 = 24.0
    c.to(q1[0], LINE1 - 5.08 - 2.2)                      # limiter OUT then lands on LINE1
    lim = add_fp(f"LM{n}1", "LIM", ch, pads={"1": s("L1_HYB"), "4": s("L1_LIM"), "2": "GND", "3": "GND",
                                              "5": "GND", "6": "GND"})
    lim_place(c, lim, pref_dx=+1)
    c.turn(1.0, 0.0)                                     # east along y = LINE1
    lna_stage(c, n, ch, "L1", 1, s)
    saw(c, n, ch, "L1", 1, s)
    lna_stage(c, n, ch, "L1", 2, s)
    saw(c, n, ch, "L1", 2, s)
    saw_link(c, n, ch, "L1", s)          # 3rd SAW before the diplexer (customer request, Rev B)
    saw(c, n, ch, "L1", 3, s)
    l1_end = c

    # ---- L2 chain -----------------------------------------------------------------
    c2 = Chain(h2, "1", s("L2_HYB"), (1.0, 0.0))
    lim2 = add_fp(f"LM{n}2", "LIM", ch, pads={"1": s("L2_HYB"), "4": s("L2_LIM"), "2": "GND", "3": "GND",
                                               "5": "GND", "6": "GND"})
    c2.u = (1.0, 0.0)
    lim_place(c2, lim2, pref_dy=+1, gap=4.5)
    c2.turn(0.0, 1.0)                                    # south from the limiter OUT pin
    lna_stage(c2, n, ch, "L2", 1, s)
    saw(c2, n, ch, "L2", 1, s)
    lna_stage(c2, n, ch, "L2", 2, s)
    saw(c2, n, ch, "L2", 2, s)
    Y2TURN = c2.p[1] + 1.4                       # just below the last L2 SAW
    assert Y2TURN + 2.7 < LINE1 - 0.5, f"L2 run ({Y2TURN:.2f}) too close to the L1 line ({LINE1})"
    c2.to(c2.p[0], Y2TURN)
    c2.turn(1.0, 0.0)
    saw_link(c2, n, ch, "L2", s)         # 3rd SAW on the east run toward the diplexer
    saw(c2, n, ch, "L2", 3, s)

    # ---- diplexer + output ---------------------------------------------------------
    dxp = add_fp(f"DX{n}", "DXP", ch, pads={"2": s("COM"), "7": s("L1_DXP"), "5": s("L2_DXP"),
                                            "1": "GND", "3": "GND", "4": "GND", "6": "GND", "8": "GND"})
    orient(dxp, "2", "6", -1 / math.sqrt(2), -1 / math.sqrt(2))
    # band pins face north-west; place so pin 6 sits at the chain meeting point
    move_pad_to(dxp, "6", 30.0, 30.0)
    p7, p5 = padL(dxp, "7"), padL(dxp, "5")
    assert p7[0] < p5[0] and p7[1] > p5[1], f"DXP band pins mirrored: L1 {p7}, L2 {p5}"
    # L1 port: series 4.7 nH (DNP shunt C at its chain side)
    l1s = add_fp(f"L{n}41", "L4N7", ch, pads={"1": s("L1_S3OUT"), "2": s("L1_DXP")}, show_ref=False)
    c.part(l1s, "1", "2", 1.3, s("L1_DXP"))
    shunt(f"C{n}41", "CDNP", ch, l1s, "1", s("L1_S3OUT"), 0, 1, off=1.0)
    c.end(dxp, "7", mid=[(p7[0] - 1.6, c.p[1]), (p7[0] - 1.6, p7[1])])
    # L2 port: shunt 6.8 nH (SAW match) + shunt 1 pF, series 3.3 nH
    l2s = add_fp(f"L{n}42", "L3N3", ch, pads={"1": s("L2_S3OUT"), "2": s("L2_DXP")}, show_ref=False)
    c2.part(l2s, "1", "2", 2.8, s("L2_DXP"))
    c2._b8889_out = None
    # both port shunts hang south of the run, side by side (north is the LNA bias cluster)
    shunt(f"C{n}42", "C1P0", ch, l2s, "1", s("L2_S3OUT"), 0, 1, off=1.0, via_d=0.65)
    shunt(f"L{n}44", "L6N8", ch, l2s, "1", s("L2_S3OUT"), 0, 1, off=1.0, via_d=0.65, shift=1.25)
    c2.end(dxp, "5", mid=[(p5[0], c2.p[1])])
    dxp_gnd(dxp)

    # common: series 4.3 nH -> node (shunt 1.5 pF) -> 100 pF DC block -> SMA
    cc = Chain(dxp, "2", s("COM"), (1 / math.sqrt(2), 1 / math.sqrt(2)))
    lc = add_fp(f"L{n}43", "L4N3", ch, pads={"1": s("COM"), "2": s("COM_M")}, show_ref=False)
    cc.part(lc, "1", "2", 1.5, s("COM_M"))
    cb = add_fp(f"C{n}43", "C100P", ch, pads={"1": s("COM_M"), "2": s("RFOUT")}, show_ref=False)
    cc.part(cb, "1", "2", 1.2, s("RFOUT"))
    shunt(f"C{n}44", "C1P5", ch, lc, "2", s("COM_M"), 1 / math.sqrt(2), -1 / math.sqrt(2), off=1.0)
    sma = add_fp(f"J{n}", "SMA", ch, at=(40.5, 40.5), rot=0, pads={"1": s("RFOUT"), "2": "GND"})
    sp = padL(sma, "1")
    cc.end(sma, "1", mid=[(cc.p[0], sp[1])])     # enter the SMA pin on-axis, between its GND legs

    # local bulk decoupling for the 4 LNAs of this channel
    blk = add_fp(f"C{n}90", "C10U", ch, at=(8.0, 14.5), rot=0, pads={"1": "+5V", "2": "GND"}, show_ref=False)
    via(*_off(padL(blk, "1"), 0, -0.9), "+5V")
    track([padL(blk, "1"), _off(padL(blk, "1"), 0, -0.9)], "+5V", D.PWR_W)
    gnd_stub(blk, "2", 0, -1, 0.9)


def _off(p, dx, dy):
    return (p[0] + dx, p[1] + dy)


def _check_far(fp, far, near):
    dist = lambda q: math.hypot(*padL(fp, q))  # noqa: E731
    assert min(dist(a) for a in far) > max(dist(b) for b in near), \
        f"{fp.GetReference()}: output pins not on the outer side (handedness)"


def hyb_gnd_vias(h):
    """GND vias in the HC125A ground cross (plugged + capped)."""
    g = [p for p in h.Pads() if p.GetNumber() == "GND"]
    cx, cy = toL(*xy(g[0].GetPosition()))
    # cross arms: one along pin1->pin2, one perpendicular
    a1, a2 = padL(h, "1"), padL(h, "2")
    ux, uy = a2[0] - a1[0], a2[1] - a1[1]
    nrm = math.hypot(ux, uy)
    ux, uy = ux / nrm, uy / nrm
    vx, vy = -uy, ux
    for t in (-3.6, -2.4, -1.2, 0.0, 1.2, 2.4, 3.6):
        via(cx + t * ux, cy + t * uy, "GND", D.EPVIA_D, D.EPVIA_DRILL)
    for t in (-3.1, -1.9, 1.9, 3.1):
        via(cx + t * vx, cy + t * vy, "GND", D.EPVIA_D, D.EPVIA_DRILL)


def dxp_gnd(dxp):
    cxy = toL(*xy(dxp.GetPosition()))
    for num in ("1", "3", "4", "8"):
        px, py = padL(dxp, num)
        dx, dy = px - cxy[0], py - cxy[1]
        nn = math.hypot(dx, dy)
        gnd_stub(dxp, num, dx / nn, dy / nn, 1.0)


def lim_place(c, lim, pref_dx=0, pref_dy=0, gap=2.2):
    """RLM-63-2W+: IN (1) and OUT (4) are diagonal; keep the body square to the chain and
    accept the 5.08 mm lateral jog, toward the preferred side."""
    ux, uy = c.u
    best = None
    for deg in (0, 90, 180, 270):
        lim.SetOrientationDegrees(deg)
        a, b = padL(lim, "1"), padL(lim, "4")
        vx, vy = b[0] - a[0], b[1] - a[1]
        along = vx * ux + vy * uy
        lat = vx * pref_dx + vy * pref_dy
        sc = (along > 4.0) * 100 + (lat > 0) * 10 + along
        if best is None or sc > best[0]:
            best = (sc, deg)
    lim.SetOrientationDegrees(best[1])
    c.part(lim, "1", "4", gap, c.net.replace("_HYB", "_LIM"), keep=True)
    for num in ("2", "3", "5", "6"):
        px, py = padL(lim, num)
        cxy = toL(*xy(lim.GetPosition()))
        dx, dy = px - cxy[0], py - cxy[1]
        nn = math.hypot(dx, dy)
        via(px + 0.35 * dx / nn, py + 0.35 * dy / nn, "GND")


def lna_stage(c, n, ch, band, idx, s):
    """100 pF in -> TQP3M9037 -> 100 pF out, 18 nH choke from the out node to +5V
    with 100 pF + 1 uF to GND (TQP3M9037 eval board, as project 16)."""
    b = "1" if band == "L1" else "2"
    tag = f"{band}_A{idx}"
    cin = add_fp(f"C{n}{b}{idx}1", "C100P", ch, pads={"1": c.net, "2": s(f"{tag}IN")}, show_ref=False)
    c.part(cin, "1", "2", 2.4 if c.fp.GetValue() == "RLM-63-2W+" else 1.2, s(f"{tag}IN"))
    pend = getattr(c, "_b8889_out", None)
    if pend:   # B8889 output shunt 6.8 nH sits on the next stage's input-cap pad
        ref, (qx, qy) = pend
        shunt(ref, "L6N8", ch, cin, "1", pad(cin, "1").GetNetname(), qx, qy, off=1.0)
        c._b8889_out = None
    u = add_fp(f"U{n}{b}{idx}", "LNA", ch, pads={"2": s(f"{tag}IN"), "7": s(f"{tag}OUT"),
                                                 **{q: "GND" for q in ("1", "3", "4", "5", "6", "8", "9")}})
    c.part(u, "2", "7", 1.3, s(f"{tag}OUT"))
    ux, uy = c.u
    vx, vy = -uy, ux
    # EP: 2 plugged vias. GND pins: 3-4 and 5-6 tied along the row (they reach the pour);
    # 1 and 8 sit next to the RF pins, so each gets its own stub + via. Pin 6 (VPD shutdown, 0 V = ON)
    # is tied to pin 5 and GND: the LNA is always on (project 16, TQP3M9037 data sheet).
    ex, ey = padL(u, "9")
    for t in (-0.42, 0.42):
        via(ex + t * vx, ey + t * vy, "GND", D.EPVIA_D, D.EPVIA_DRILL)
    for a, bb in (("3", "4"), ("5", "6")):
        track([padL(u, a), padL(u, bb)], "GND", 0.2)
    for q, rf in (("1", "2"), ("8", "7")):
        px, py = padL(u, q)
        rx, ry = padL(u, rf)
        ox, oy = px - ex, py - ey                         # outward from the EP (row side)
        al = ox * ux + oy * uy
        sgn = 1 if al > 0 else -1
        lx, ly = px - rx, py - ry                         # away from the RF neighbour
        ln = math.hypot(lx, ly)
        lx, ly = lx / ln, ly / ln
        k1 = (px + sgn * 0.55 * ux, py + sgn * 0.55 * uy)
        k2 = (k1[0] + 0.75 * lx + sgn * 0.25 * ux, k1[1] + 0.75 * ly + sgn * 0.25 * uy)
        track([(px, py), k1, k2], "GND", 0.2)
        via(*k2, "GND", D.EPVIA_D, D.EPVIA_DRILL)
    cout = add_fp(f"C{n}{b}{idx}2", "C100P", ch, pads={"1": s(f"{tag}OUT"), "2": s(f"{tag}OUTC")},
                  show_ref=False)
    c.part(cout, "1", "2", 1.4, s(f"{tag}OUTC"))
    # bias T: 18 nH choke perpendicular to the line, +5V via straight beyond it, 100 pF and
    # 1 uF either side of the choke end, each with its own GND via further out.
    side = (-vx, -vy)            # L1 line runs east: bias north; L2 line runs south: bias east
    lb = shunt(f"L{n}{b}{idx}", "L18N", ch, cout, "1", s(f"{tag}OUT"), side[0], side[1], off=1.3,
               other="+5V")
    bx, by = padL(lb, "2")
    nx, ny = bx + 1.0 * side[0], by + 1.0 * side[1]
    track([(bx, by), (nx, ny)], "+5V", D.PWR_W)
    via(nx, ny, "+5V")
    for j, (key, dist) in enumerate((("C100P", -1.4), ("C1U", 1.4))):
        cp = add_fp(f"C{n}{b}{idx}{3 + j}", key, ch, pads={"1": "+5V", "2": "GND"}, show_ref=False)
        orient(cp, "1", "2", side[0], side[1], step=45)
        move_pad_to(cp, "1", bx + dist * ux, by + dist * uy)
        track([(bx, by), padL(cp, "1")], "+5V", D.PWR_W)
        gnd_stub(cp, "2", side[0], side[1], 0.8)


def saw_link(c, n, ch, band, s):
    """100 pF between SAW 2 and SAW 3: gives each B8889 port its own 6.8 nH shunt pad and keeps
    the SAWs DC-isolated from each other."""
    b = "1" if band == "L1" else "2"
    k = add_fp(f"C{n}{b}31", "C100P", ch, pads={"1": c.net, "2": s(f"{band}_S3IN")}, show_ref=False)
    c.part(k, "1", "2", 1.4, s(f"{band}_S3IN"))
    pend = getattr(c, "_b8889_out", None)
    if pend:   # SAW 2 output shunt, on the side of the line away from the bias network
        ux, uy = c.u
        shunt(pend[0], "L6N8", ch, k, "1", pad(k, "1").GetNetname(), -uy, ux, off=1.0)
        c._b8889_out = None


def saw(c, n, ch, band, idx, s):
    b = "1" if band == "L1" else "2"
    key = "SAW_L1" if band == "L1" else "SAW_L2"
    out_pin = "3" if band == "L1" else "4"
    gnds = ("2", "4") if band == "L1" else ("2", "3", "5")
    tag = f"{band}_S{idx}"
    f = add_fp(f"FL{n}{b}{idx}", key, ch, pads={"1": c.net, out_pin: s(f"{tag}OUT"),
                                                 **{q: "GND" for q in gnds}})
    node_fp, node_pin, in_net = c.fp, c.pin, c.net
    c.part(f, "1", out_pin, 1.8, s(f"{tag}OUT"))
    ux, uy = c.u
    vx, vy = -uy, ux
    # GND pads: radial stub away from the in/out diagonal, 0.2 mm wide, to a 0.25 mm via
    a, bq = padL(f, "1"), padL(f, out_pin)
    mx, my = (a[0] + bq[0]) / 2, (a[1] + bq[1]) / 2
    for q in gnds:
        px, py = padL(f, q)
        dx, dy = px - mx, py - my
        dn = math.hypot(dx, dy) or 1
        k = (px + 0.75 * dx / dn, py + 0.75 * dy / dn)
        track([(px, py), k], "GND", 0.2)
        via(*k, "GND", D.EPVIA_D, D.EPVIA_DRILL)
    if band == "L2":
        # B8889 needs a 6.8 nH shunt at input and output (50 ohm // 6.8 nH terminations);
        # both go on the side opposite the LNA bias network.
        shunt(f"L{n}{b}{idx}5", "L6N8", ch, node_fp, node_pin, in_net, vx, vy, off=1.0)
        c._b8889_out = (f"L{n}{b}{idx}6", (vx, vy))
    return f


# ----------------------------------------------------------------------------- whole board
def rotate_items(items, deg):
    if deg == 0:
        return
    ang = pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T)
    for it in items:
        it.Rotate(P(CX, CY), ang)


def outline():
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(P(*D.BOARD_CENTER))
    s.SetEnd(P(D.BOARD_CENTER[0] + D.BOARD_RADIUS, D.BOARD_CENTER[1]))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(FromMM(0.1))
    board.Add(s)


# ----------------------------------------------------------------------------- DC input
def power_block():
    """Single bias point: J5 (+5 V in) -> F1 PTC -> Q1 P-FET (reverse polarity) -> +5V,
    with D1 TVS, C1/C2 bulk and 8 vias into the In1.Cu +5V plane. It sits in the free strip
    between the CH1 and CH2 modules near the board edge (top side there is clear of patches)."""
    ch = "PWR"
    X0, Y0 = 46.0, -38.17          # local frame of element 0 -> board (120.83, 38.0)
    j = add_fp("J5", "JDC", ch, pads={"1": "VIN", "2": "GND"})
    orient(j, "2", "1", 1, 0, step=90)
    move_pad_to(j, "1", X0 + 1.5, Y0)
    p1 = padL(j, "1")
    f = add_fp("F1", "PTC", ch, pads={"1": "VIN", "2": "VIN_F"})
    orient(f, "1", "2", 0, 1, step=90)
    move_pad_to(f, "1", p1[0], p1[1] + 6.0)
    track([p1, padL(f, "1")], "VIN", D.VIN_W)
    q = add_fp("Q1", "PFET", ch, pads={"1": "QG", "2": "+5V", "3": "VIN_F"})
    orient(q, "3", "2", 0, 1, step=90)
    fx, fy = padL(f, "2")
    move_pad_to(q, "3", fx, fy + 3.0)
    track([(fx, fy), padL(q, "3")], "VIN_F", D.VIN_W)
    sx, sy = padL(q, "2")
    gx, gy = padL(q, "1")
    g = 1 if gx > sx else -1                 # side of the gate pin
    rg = add_fp("R5", "R10K", ch, pads={"1": "QG", "2": "GND"})
    orient(rg, "1", "2", 0, 1, step=90)
    move_pad_to(rg, "1", gx, gy + 1.8)
    track([(gx, gy), padL(rg, "1")], "QG", 0.3)
    gnd_stub(rg, "2", 0, 1, 0.9)
    node = (sx, sy + 3.2)
    track([(sx, sy), node], "+5V", D.VIN_W)
    tv = add_fp("D1", "TVS", ch, pads={"1": "+5V", "2": "GND"})       # away from the gate
    orient(tv, "1", "2", -g, 0, step=90)
    move_pad_to(tv, "1", node[0] - g * 2.8, node[1])
    track([node, padL(tv, "1")], "+5V", D.VIN_W)
    gnd_stub(tv, "2", -g, 0, 1.9)
    spine = (sx, node[1] + 3.2)
    track([node, spine], "+5V", D.VIN_W)
    cb = add_fp("C1", "C22U", ch, pads={"1": "+5V", "2": "GND"})
    orient(cb, "1", "2", -g, 0, step=90)
    move_pad_to(cb, "1", sx - g * 2.2, spine[1])
    track([spine, padL(cb, "1")], "+5V", D.VIN_W)
    gnd_stub(cb, "2", -g, 0, 1.5)
    cs = add_fp("C2", "C100N", ch, pads={"1": "+5V", "2": "GND"})
    orient(cs, "1", "2", g, 0, step=90)
    move_pad_to(cs, "1", sx + g * 1.6, spine[1])
    track([spine, padL(cs, "1")], "+5V", D.PWR_W)
    gnd_stub(cs, "2", g, 0, 0.9)
    # +5V into the plane: 8 x 0.3 mm vias (about 0.5 A each, 1.44 A worst case total)
    last = spine
    for i in range(4):
        vy = spine[1] + 1.8 + 1.4 * i
        track([last, (sx, vy)], "+5V", D.VIN_W)
        last = (sx, vy)
        for sgn in (-1, 1):
            via(sx + sgn * 0.95, vy, "+5V")
            track([(sx, vy), (sx + sgn * 0.95, vy)], "+5V", D.PWR_W)
    tp1 = add_fp("TP1", "TP", ch, pads={"1": "+5V"})
    move_pad_to(tp1, "1", sx, last[1] + 2.4)
    track([last, padL(tp1, "1")], "+5V", D.PWR_W)
    tp2 = add_fp("TP2", "TP", ch, pads={"1": "GND"})
    move_pad_to(tp2, "1", sx - g * 3.6, last[1] + 2.4)


# ----------------------------------------------------------------------------- planes, vias
def zones():
    cx, cy = D.BOARD_CENTER
    r = D.BOARD_RADIUS - 0.5
    for layer, nname in ((pcbnew.F_Cu, "GND"), (pcbnew.In1_Cu, "+5V"), (pcbnew.In2_Cu, "GND"),
                         (pcbnew.B_Cu, "GND")):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(net(nname))
        ol = z.Outline()
        ol.NewOutline()
        for i in range(180):
            a = 2 * math.pi * i / 180
            ol.Append(FromMM(cx + r * math.cos(a)), FromMM(cy + r * math.sin(a)))
        z.SetLocalClearance(FromMM(D.RF_GAP))
        z.SetMinThickness(FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetThermalReliefGap(FromMM(0.3))
        z.SetThermalReliefSpokeWidth(FromMM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)
    # THT pins (SMA, J5) use thermal spokes so they can be hand-soldered
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() == "GND":
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0 if l2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


class Obstacles:
    def __init__(self):
        self.pads, self.tracks, self.vias = [], [], []
        for fp in board.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                self.pads.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()),
                                  p.GetNetname(), p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD))
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                self.vias.append((*xy(t.GetPosition()), ToMM(t.GetWidth(pcbnew.F_Cu)) / 2))
            else:
                self.tracks.append((*xy(t.GetStart()), *xy(t.GetEnd()), ToMM(t.GetWidth()) / 2, t.GetNetname()))

    def free(self, x, y, r=D.VIA_D / 2, clr=0.25):
        for x0, y0, x1, y1, nn, tht in self.pads:
            extra = 0.8 if tht else 0.0
            if math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1)) < r + clr + extra:
                return False
        for vx, vy, vr in self.vias:
            if math.hypot(vx - x, vy - y) < r + vr + 0.35:
                return False
        for x1, y1, x2, y2, hw, nn in self.tracks:
            gap = D.RF_GAP if nn.startswith("CH") else clr
            if nn == "GND":
                gap = 0.1
            if seg_dist(x, y, x1, y1, x2, y2) < r + hw + gap:
                return False
        return True

    def add(self, x, y):
        self.vias.append((x, y, D.VIA_D / 2))


def board_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetWidth(FromMM(D.VIA_D))
    v.SetDrill(FromMM(D.VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net("GND"))
    board.Add(v)


def stitch(all_rf):
    obs = Obstacles()
    cx, cy = D.BOARD_CENTER
    n_f = n_g = 0
    for t in all_rf:                      # 1. fences along both sides of every 50-ohm segment
        (x1, y1), (x2, y2) = xy(t.GetStart()), xy(t.GetEnd())
        ln = math.hypot(x2 - x1, y2 - y1)
        if ln < 1.0:
            continue
        ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
        k = max(1, int(ln / D.FENCE_PITCH))
        for i in range(k + 1):
            for sg in (1, -1):
                x = x1 + ux * ln * i / k - sg * D.FENCE_OFFSET * uy
                y = y1 + uy * ln * i / k + sg * D.FENCE_OFFSET * ux
                if obs.free(x, y):
                    board_via(x, y)
                    obs.add(x, y)
                    n_f += 1
    step = 5.0                            # 2. board-wide staggered stitching grid
    for iy in range(-25, 26):
        for ix in range(-22, 23):
            x = cx + ix * step + (step / 2 if iy % 2 else 0)
            y = cy + iy * step * 0.866
            if math.hypot(x - cx, y - cy) > D.BOARD_RADIUS - 2.0:
                continue
            if obs.free(x, y, clr=0.35):
                board_via(x, y)
                obs.add(x, y)
                n_g += 1
    print(f"fence vias {n_f}, stitching vias {n_g}")


# ----------------------------------------------------------------------------- silk / fab
def text(s, x, y, layer, size=1.5, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(P(size, size))
    t.SetTextThickness(FromMM(size * 0.15))
    t.SetMirrored(mirror)
    board.Add(t)


def rot_k(x, y, k):
    a = math.radians(-90 * k)
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def silk():
    cx, cy = D.ARRAY_CENTER
    text("CRL-BEL  CRPA 4CH L-BAND ACTIVE ANTENNA FE  REV A", cx, cy + 84, pcbnew.B_SilkS, 1.6, True)
    text("FR-4 1.6 mm 4L: L1 GND / L2 +5V / L3 GND / L4 RF", cx, cy + 87.5, pcbnew.B_SilkS, 1.1, True)
    text("+5V IN", cx - 7.0, cy - 84.0, pcbnew.B_SilkS, 1.2, True)
    text("CRL-BEL CRPA 4CH L-BAND - ANTENNA SIDE", cx, cy + 4.0, pcbnew.F_SilkS, 1.4, False)
    for k, name in enumerate(D.CHANNEL_NAMES):
        rx, ry = rot_k(-13.5, -13.5, k)
        text(name, cx + rx, cy + ry, pcbnew.B_SilkS, 1.5, True)
        rx, ry = rot_k(-46.0 - 22.0, -46.0 - 36.0, k)
        text(name, cx + rx, cy + ry, pcbnew.F_SilkS, 2.0, False)


def fiducials():
    cx, cy = D.ARRAY_CENTER
    for i, (dx, dy) in enumerate(((0, 72), (-90, 18), (90, -18))):
        f = load_fp(*D.PARTS["FID"][:2])
        f.SetReference(f"FID{i + 1}")
        board.Add(f)
        f.SetPosition(P(cx + dx, cy + dy))
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)


def stackup_patch(path):
    """pcbnew's SWIG layer does not expose BOARD_STACKUP; write the block into the file."""
    t = "\t"
    lines = [f"{t}{t}(stackup",
             f'{t}{t}{t}(layer "F.SilkS" (type "Top Silk Screen"))',
             f'{t}{t}{t}(layer "F.Paste" (type "Top Solder Paste"))',
             f'{t}{t}{t}(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))']
    di = 0
    for name, typ, th, er, note in D.STACKUP:
        if typ == "copper":
            lines.append(f'{t}{t}{t}(layer "{name}" (type "copper") (thickness {th}))')
        elif typ in ("prepreg", "core"):
            di += 1
            mat = "FR4 7628" if typ == "prepreg" else "FR4"
            lines.append(f'{t}{t}{t}(layer "dielectric {di}" (type "{typ}") (thickness {th}) '
                         f'(material "{mat}") (epsilon_r {er}) (loss_tangent 0.02))')
    lines += [f'{t}{t}{t}(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))',
              f'{t}{t}{t}(layer "B.Paste" (type "Bottom Solder Paste"))',
              f'{t}{t}{t}(layer "B.SilkS" (type "Bottom Silk Screen"))',
              f'{t}{t}{t}(copper_finish "ENIG")',
              f'{t}{t}{t}(dielectric_constraints yes)',
              f"{t}{t})"]
    txt = path.read_text()
    i = txt.index("(setup") + len("(setup")
    txt = txt[:i] + "\n" + "\n".join(lines) + txt[i:]
    gi = txt.index("(general")
    gj = txt.index("(thickness", gi)
    ge = txt.index(")", gj)
    txt = txt[:gj] + f"(thickness {D.BOARD_THICKNESS}" + txt[ge:]
    path.write_text(txt)


def write_parts():
    """Placement list for the BOM / CPL builder (made from the same objects)."""
    rows = []
    for ref, key, ch in BOM:
        fp = FPS[ref]
        x, y = xy(fp.GetPosition())
        rows.append(dict(ref=ref, key=key, ch=ch, x=round(x, 3), y=round(y, 3),
                         rot=round(fp.GetOrientationDegrees(), 1), side="bottom" if fp.IsFlipped() else "top",
                         nets={p.GetNumber(): p.GetNetname() for p in fp.Pads()}))
    (PROJ / "Fab" / "_parts.json").write_text(json.dumps(rows, indent=0))
    lens = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            lens[t.GetNetname()] = lens.get(t.GetNetname(), 0.0) + ToMM(t.GetLength())
    bias = dict(pads=sum(1 for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == "+5V"),
                chokes=sum(1 for fp in board.GetFootprints() if fp.GetValue() == "18nH"),
                vias=sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "+5V"),
                plane="In1.Cu")
    (PROJ / "Fab" / "_bias.json").write_text(json.dumps(bias))
    (PROJ / "Fab" / "_netlen.json").write_text(json.dumps({k: round(v, 3) for k, v in sorted(lens.items())}, indent=0))


def write_project():
    """KiCad project file: design rules (JLCPCB 4-layer standard capability) and net classes.
    Zones are filled by kicad-cli (pcbnew's ZONE_FILLER crashes when run standalone)."""
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "silk_line_width": 0.12,
                         "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
            "rules": {"min_clearance": 0.15, "min_track_width": 0.15, "min_via_annular_width": 0.1,
                      "min_via_diameter": 0.45, "min_through_hole_diameter": 0.25, "min_hole_clearance": 0.25,
                      "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.5, "min_silk_clearance": 0.0,
                      "min_text_height": 0.5, "min_text_thickness": 0.08, "solder_mask_to_copper_clearance": 0.0,
                      "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 1},
            "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "ignore", "silk_edge_clearance": "ignore",
                                "text_height": "ignore", "lib_footprint_issues": "ignore",
                                "lib_footprint_mismatch": "ignore", "footprint_symbol_mismatch": "ignore"},
        }},
        "meta": {"filename": "CRPA17_4CH_LBAND.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.15, "track_width": 0.25, "via_diameter": D.VIA_D,
                 "via_drill": D.VIA_DRILL, "wire_width": 6, "bus_width": 12, "line_style": 0,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
                 "diff_pair_via_gap": 0.25, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                 "priority": 2147483647},
                {"name": "RF50", "clearance": 0.15, "track_width": D.RF_W, "via_diameter": D.VIA_D,
                 "via_drill": D.VIA_DRILL, "priority": 0},
                {"name": "PWR", "clearance": 0.2, "track_width": D.PWR_W, "via_diameter": D.VIA_D,
                 "via_drill": D.VIA_DRILL, "priority": 1},
            ],
            "meta": {"version": 4},
            "netclass_patterns": [{"netclass": "RF50", "pattern": "CH*"},
                                  {"netclass": "PWR", "pattern": "+5V"}, {"netclass": "PWR", "pattern": "VIN*"}],
        },
    }
    (KDIR / "CRPA17_4CH_LBAND.kicad_pro").write_text(json.dumps(pro, indent=2))
    (KDIR / "CRPA17_4CH_LBAND.kicad_dru").write_text(
        "(version 1)\n"
        "# B7504 / B8889 SAW land patterns (from the customer board) have a 0.14 mm pad-to-pad gap\n"
        "(rule \"SAW land pattern\"\n"
        "  (condition \"A.memberOfFootprint('FL*') && B.memberOfFootprint('FL*')\")\n"
        "  (constraint clearance (min 0.10mm)))\n")


def main():
    outline()
    all_rf = []
    for k in range(4):
        ITEMS.clear()
        RF_TRACKS.clear()
        build_element(k)
        rotate_items(ITEMS, -90 * k)
        all_rf.extend(RF_TRACKS)
    ITEMS.clear()
    power_block()
    fiducials()
    silk()
    zones()
    stitch(all_rf)
    pcbnew.SaveBoard(str(PCB_FILE), board)
    stackup_patch(PCB_FILE)
    write_parts()
    write_project()
    dump_debug()


def dump_debug():
    out = {"pads": [], "tracks": [], "vias": []}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            out["pads"].append(dict(ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(),
                                    x0=ToMM(bb.GetLeft()), y0=ToMM(bb.GetTop()), x1=ToMM(bb.GetRight()),
                                    y1=ToMM(bb.GetBottom()), back=fp.IsFlipped()))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            out["vias"].append(dict(x=ToMM(t.GetPosition().x), y=ToMM(t.GetPosition().y), d=ToMM(t.GetWidth(pcbnew.F_Cu)),
                                    net=t.GetNetname()))
        else:
            out["tracks"].append(dict(x1=ToMM(t.GetStart().x), y1=ToMM(t.GetStart().y), x2=ToMM(t.GetEnd().x),
                                      y2=ToMM(t.GetEnd().y), w=ToMM(t.GetWidth()), net=t.GetNetname()))
    (PROJ / "Images" / "_debug_layout.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
