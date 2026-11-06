"""Build 03_kicad/CRL-LS-CRPA4.kicad_pcb (project 02) with the KiCad 10 pcbnew API. Derived from project 17 build_pcb.py.

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
import ls_design as D  # noqa: E402

PROJ = HERE.parent
KDIR = PROJ / "03_kicad"
PCB_FILE = KDIR / "CRL-LS-CRPA4.kicad_pcb"
FAB = PROJ / "04_fab"
IMG = PROJ / "05_docs" / "img"
STD_FP = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", "C:/Program Files/KiCad/10.0/share/kicad/footprints"))

board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
NETS = {}
ITEMS = []          # every item created for the current element (for the rotation copy)
FPS = {}            # ref -> footprint
BOM = []            # (ref, part key, channel)
RF_TRACKS = []      # (x1, y1, x2, y2) board mm, for the via fence
BIAS_VIAS = []      # LNA bias vias of the element being built (local)
LOCAL_BIAS_ROUTES = []   # In1.Cu routes FB -> LNA bias vias, found on CH1 (board coords, k=0 frame)
TRUNK_END = {}      # k -> local point of the +5V trunk via at FB{n} pad 1
POWER_VIAS = []     # +5V vias at the star point (power block), board coords
POWER_VIA_OBJS = []
POWER_J5_AT = (-36.0, -86.0)   # J5 pin 1, array-centre frame (project 02: arc NNW of CH1, block runs east)


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
LIM_SPAN = 2.21      # CLM-83-2W+ (DL1721) pad 2 -> pad 7 centre distance, in-line
LIM_EXIT = 1.8       # straight run past the limiter OUT before the chain may turn (clears the GND vias)
LIM_GND = {q: "GND" for q in ("1", "3", "4", "5", "6", "8", "9")}


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


# ----------------------------------------------------------------------------- inner-layer router
def _obstacles(net_name, layer=pcbnew.In1_Cu):
    """(x, y, r) circles for every through-hole of another net, plus In1 segments of other nets."""
    circ, segs = [], []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                if p.GetNetname() and p.GetNetname() == net_name:
                    continue
                bb = p.GetBoundingBox()
                r = max(ToMM(bb.GetWidth()), ToMM(bb.GetHeight())) / 2
                if fp.GetReference().startswith("ANT"):     # antenna pads carry a 0.6 mm local clearance
                    r += D.ANT_FEED_ANTIPAD
                circ.append((*xy(p.GetPosition()), r))
    for t in board.GetTracks():
        if t.GetNetname() == net_name:
            continue
        if t.GetClass() == "PCB_VIA":
            circ.append((*xy(t.GetPosition()), ToMM(t.GetWidth(pcbnew.F_Cu)) / 2))
        elif t.GetLayer() == layer:
            segs.append((*xy(t.GetStart()), *xy(t.GetEnd()), ToMM(t.GetWidth()) / 2))
    return circ, segs


def route_inner(a, b, net_name, width, local_bbox=False, res=0.2, clr=0.40):
    """Grid A* (8-connected) on In1.Cu from board point a to b, then line-of-sight smoothing.
    Returns the polyline in board coordinates."""
    import heapq
    import numpy as np
    circ, segs = _obstacles(net_name)
    if local_bbox:
        x0, y0 = L(-50, -50)
        x1, y1 = L(60, 60)          # project 02: includes the S chain in the axis strip
    else:
        cx, cy = D.BOARD_CENTER
        x0, y0, x1, y1 = cx - 100, cy - 100, cx + 100, cy + 100
    nx, ny = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    blk = np.zeros((ny, nx), dtype=bool)
    gx = x0 + np.arange(nx) * res
    gy = y0 + np.arange(ny) * res
    inf = clr + width / 2
    for (px, py, r) in circ:
        rr = r + inf
        i0, i1 = max(0, int((px - rr - x0) / res)), min(nx, int((px + rr - x0) / res) + 2)
        j0, j1 = max(0, int((py - rr - y0) / res)), min(ny, int((py + rr - y0) / res) + 2)
        if i0 >= i1 or j0 >= j1:
            continue
        X, Y = np.meshgrid(gx[i0:i1], gy[j0:j1])
        blk[j0:j1, i0:i1] |= (X - px) ** 2 + (Y - py) ** 2 < rr * rr
    for (sx1, sy1, sx2, sy2, hw) in segs:
        rr = hw + inf
        i0 = max(0, int((min(sx1, sx2) - rr - x0) / res))
        i1 = min(nx, int((max(sx1, sx2) + rr - x0) / res) + 2)
        j0 = max(0, int((min(sy1, sy2) - rr - y0) / res))
        j1 = min(ny, int((max(sy1, sy2) + rr - y0) / res) + 2)
        if i0 >= i1 or j0 >= j1:
            continue
        X, Y = np.meshgrid(gx[i0:i1], gy[j0:j1])
        dx, dy = sx2 - sx1, sy2 - sy1
        l2 = dx * dx + dy * dy or 1e-12
        t = np.clip(((X - sx1) * dx + (Y - sy1) * dy) / l2, 0, 1)
        blk[j0:j1, i0:i1] |= (X - sx1 - t * dx) ** 2 + (Y - sy1 - t * dy) ** 2 < rr * rr
    X, Y = np.meshgrid(gx, gy)
    bcx, bcy = D.BOARD_CENTER
    blk |= (X - bcx) ** 2 + (Y - bcy) ** 2 > (D.BOARD_RADIUS - 1.0 - width / 2) ** 2
    st = (int(round((a[1] - y0) / res)), int(round((a[0] - x0) / res)))
    gl = (int(round((b[1] - y0) / res)), int(round((b[0] - x0) / res)))
    for c in (st, gl):           # the end vias are on this net: clear a small disc around them
        blk[max(0, c[0] - 2):c[0] + 3, max(0, c[1] - 2):c[1] + 3] = False
    g = np.full((ny, nx), np.inf, dtype=np.float32)
    par = {}
    g[st] = 0

    def h(q):
        dj, di = abs(q[0] - gl[0]), abs(q[1] - gl[1])
        return max(dj, di) + 0.4142 * min(dj, di)
    pq = [(h(st), st)]
    steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.4142), (-1, 1, 1.4142),
             (1, -1, 1.4142), (1, 1, 1.4142)]
    pops = 0
    while pq:
        f, q = heapq.heappop(pq)
        pops += 1
        if q == gl or pops > 400000:          # cap: a blocked route fails fast (debug image below)
            break
        gq = g[q]
        if f - h(q) > gq + 1e-3:
            continue
        for dj, di, cst in steps:
            r_ = (q[0] + dj, q[1] + di)
            if not (0 <= r_[0] < ny and 0 <= r_[1] < nx) or blk[r_]:
                continue
            ng = gq + cst
            if ng < g[r_]:
                g[r_] = ng
                par[r_] = q
                heapq.heappush(pq, (ng + h(r_), r_))
    if gl not in par:
        try:
            from PIL import Image as _I
            im = np.stack([blk * 255] * 3, -1).astype("uint8")
            seen = np.isfinite(g)
            im[seen] = (80, 160, 255)
            for c in (st, gl):
                im[max(0, c[0] - 6):c[0] + 7, max(0, c[1] - 6):c[1] + 7] = (255, 0, 0)
            _I.fromarray(im).save(str(FAB / "_route_fail.png"))
        except Exception as e:  # noqa: BLE001
            print("debug image failed", e)
        raise RuntimeError(f"no inner route for {net_name} from {a} to {b}")
    cells = [gl]
    while cells[-1] != st:
        cells.append(par[cells[-1]])
    cells.reverse()

    def free_line(p, q):
        n_ = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) * 2 + 1
        for k_ in range(n_ + 1):
            j = int(round(p[0] + (q[0] - p[0]) * k_ / n_))
            i = int(round(p[1] + (q[1] - p[1]) * k_ / n_))
            if blk[j, i]:
                return False
        return True
    pts = [cells[0]]
    i = 0
    while i < len(cells) - 1:
        j = len(cells) - 1
        while j > i + 1 and not free_line(cells[i], cells[j]):
            j -= 1
        pts.append(cells[j])
        i = j
    out = [(x0 + c[1] * res, y0 + c[0] * res) for c in pts]
    out[0], out[-1] = a, b
    return out


def inner_track(pts, nname, w):
    track(pts, nname, w, layer=pcbnew.In1_Cu)


def shield_geometry(n, ch, items, rfout, sma):
    """Octagon (8-DOP, 45 deg corners) around every bottom-side item of this channel except the SMA
    and the RF-output track, SHIELD_MARGIN outside the outermost copper. Returns (vertices, notches)
    in element-local coordinates; notches = points where the RF output track crosses the frame."""
    pts = []
    for it in items:
        if isinstance(it, pcbnew.FOOTPRINT):
            ref = it.GetReference()
            if ref.startswith("J"):
                continue
            if ref.startswith("ANT"):           # top-side module: only its feed / screw pads matter
                if ref.endswith("S"):           # NavIC S patch: only the feed cross, and only for the S frame
                    for p in it.Pads():
                        if p.GetNumber() not in ("M", "C"):
                            bb = p.GetBoundingBox()
                            g_ = D.ANT_FEED_ANTIPAD + 0.3
                            for X in (ToMM(bb.GetLeft()) - g_, ToMM(bb.GetRight()) + g_):
                                for Y in (ToMM(bb.GetTop()) - g_, ToMM(bb.GetBottom()) + g_):
                                    pts.append(toL(X, Y))
                    continue
                for p in it.Pads():
                    if p.GetNumber() and p.GetNumber() != "M":
                        bb = p.GetBoundingBox()
                        pts += [toL(ToMM(bb.GetLeft()), ToMM(bb.GetTop())), toL(ToMM(bb.GetRight()), ToMM(bb.GetBottom()))]
                continue
            boxes = []                          # pads + courtyard polygon, never the text
            cy_ = it.GetCourtyard(pcbnew.B_CrtYd if it.IsFlipped() else pcbnew.F_CrtYd)
            if cy_.OutlineCount():
                boxes.append(cy_.BBox())
            boxes += [p.GetBoundingBox() for p in it.Pads()]
            for bb in boxes:
                for X in (bb.GetLeft(), bb.GetRight()):
                    for Y in (bb.GetTop(), bb.GetBottom()):
                        pts.append(toL(ToMM(X), ToMM(Y)))
        elif isinstance(it, pcbnew.PCB_TRACK):
            if it.GetNetname() == rfout or it.GetLayer() == pcbnew.In1_Cu:
                continue
            hw = ToMM(it.GetWidth(pcbnew.F_Cu) if it.GetClass() == "PCB_VIA" else it.GetWidth()) / 2
            for q in ((it.GetStart(), it.GetEnd()) if it.GetClass() != "PCB_VIA" else (it.GetPosition(),)):
                x, y = toL(*xy(q))
                pts += [(x - hw, y - hw), (x + hw, y + hw), (x - hw, y + hw), (x + hw, y - hw)]
    m = D.SHIELD_MARGIN
    dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]
    h = [max(px * dx + py * dy for px, py in pts) + m for dx, dy in dirs]
    oct_ = []
    for i in range(8):
        (a1, b1), c1 = dirs[i], h[i]
        (a2, b2), c2 = dirs[(i + 1) % 8], h[(i + 1) % 8]
        det = a1 * b2 - a2 * b1
        oct_.append(((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det))
    # keep the can clear of the SMA body (6.35 mm square flange on the bottom): octagon minus a box
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for x, y in oct_:
        poly.Append(FromMM(x), FromMM(y))
    if sma is None and "L" in SHIELD:         # S frame: share the wall with this channel's and the next channel's L octagon
        for kk in (0, 1):
            vb = [_rot_pt(L(*v), kk) for v in SHIELD["L"]["verts"]]
            lp = pcbnew.SHAPE_POLY_SET()
            lp.NewOutline()
            for x, y in vb:
                lx, ly = toL(x, y)
                lp.Append(FromMM(lx), FromMM(ly))
            poly.BooleanSubtract(lp)
        if poly.OutlineCount() > 1:            # keep the piece that holds the chain
            big = max(range(poly.OutlineCount()), key=lambda i: abs(poly.Outline(i).Area()))
            keep = pcbnew.SHAPE_POLY_SET()
            keep.AddOutline(poly.Outline(big))
            poly = keep
    if sma is not None:                       # L octagon: keep clear of the SMA flange at its corner
        sx, sy = toL(*xy(sma.GetPosition()))
        kb = 3.175 + 0.6 + D.SHIELD_W / 2
        box = pcbnew.SHAPE_POLY_SET()
        box.NewOutline()
        for x, y in ((sx - kb, sy - kb), (sx + 50, sy - kb), (sx + 50, sy + 50), (sx - kb, sy + 50)):
            box.Append(FromMM(x), FromMM(y))
        poly.BooleanSubtract(box)
    ol = poly.Outline(0)
    verts = [(ToMM(ol.CPoint(i).x), ToMM(ol.CPoint(i).y)) for i in range(ol.PointCount())]
    verts = _merge_short_edges(verts, 1.0)     # no sub-mm jogs in a sheet-metal outline
    nv = len(verts)
    # where the RF output track leaves the octagon
    notches = []
    rf = [it for it in items if isinstance(it, pcbnew.PCB_TRACK) and it.GetClass() != "PCB_VIA"
          and it.GetNetname() == rfout]
    for t in rf:
        p1, p2 = toL(*xy(t.GetStart())), toL(*xy(t.GetEnd()))
        for i in range(nv):
            q1, q2 = verts[i], verts[(i + 1) % nv]
            x = _seg_cross(p1, p2, q1, q2)
            if x:
                notches.append((i, x))
    return verts, notches


def _merge_short_edges(v, lmin):
    """Replace each edge shorter than lmin by the intersection of its two neighbouring edges."""
    changed = True
    guard = 0
    while changed and len(v) > 4 and guard < 200:      # guard: clipped S frames can oscillate
        guard += 1
        changed = False
        n_ = len(v)
        for i in range(n_):
            a, b = v[i], v[(i + 1) % n_]
            if math.dist(a, b) >= lmin:
                continue
            p0, p1 = v[(i - 1) % n_], a
            q0, q1 = b, v[(i + 2) % n_]
            d1 = (p1[0] - p0[0], p1[1] - p0[1])
            d2 = (q1[0] - q0[0], q1[1] - q0[1])
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) < 1e-9:
                new = b
            else:
                t = ((q0[0] - p0[0]) * d2[1] - (q0[1] - p0[1]) * d2[0]) / den
                new = (p0[0] + t * d1[0], p0[1] + t * d1[1])
                if math.dist(new, a) > 3.0:          # near-parallel neighbours: use the edge midpoint
                    new = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            v = [w for j, w in enumerate(v) if j not in (i, (i + 1) % n_)]
            v.insert(i if i < len(v) + 1 else len(v), new)
            changed = True
            break
    return v


def _seg_cross(p1, p2, q1, q2):
    d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if abs(d) < 1e-12:
        return None
    t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
    u = ((q1[0] - p1[0]) * (p2[1] - p1[1]) - (q1[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


SHIELD = {}
SANT = {}
S_SMA_LOCAL = {}


def shield_frame(k, n, ch, key, items, rfout, sma):
    """Exposed GND frame land (B.Cu + B.Mask opening) with stitching vias, notch at the RF exit.
    key 'L' = L-band channel octagon, 'S' = NavIC S chain frame (project 02)."""
    if k == 0:
        verts, notches = shield_geometry(n, ch, items, rfout, sma)
        obs = Obstacles()
        segs, vias_ = [], []
        nv = len(verts)
        for i in range(nv):
            a, b = verts[i], verts[(i + 1) % nv]
            cuts = sorted([x for j, x in notches if j == i], key=lambda q: math.dist(a, q))
            pieces, cur = [], a
            for x in cuts:
                ln = math.dist(a, b)
                ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
                g = D.SHIELD_NOTCH / 2
                pieces.append((cur, (x[0] - g * ux, x[1] - g * uy)))
                cur = (x[0] + g * ux, x[1] + g * uy)
            pieces.append((cur, b))
            for p, q in pieces:
                ln = math.dist(p, q)
                if ln < 0.3:
                    continue
                segs.append((p, q))
                kk = max(1, int(ln / 2.5))      # 2.5 mm pitch: < lambda/20 at 2.5 GHz, lets In1 trunks pass
                for t in range(kk + 1):
                    vx, vy = p[0] + (q[0] - p[0]) * t / kk, p[1] + (q[1] - p[1]) * t / kk
                    bx, by = L(vx, vy)
                    if obs.free(bx, by, clr=0.3) and all(math.dist((vx, vy), w) > 1.2 for w in vias_):
                        vias_.append((vx, vy))
        SHIELD[key] = dict(verts=verts, segs=segs, vias=vias_, notches=[x for _, x in notches])
    SH = SHIELD[key]
    for p, q in SH["segs"]:
        track([p, q], "GND", D.SHIELD_W)
        m = pcbnew.PCB_SHAPE(board)                      # solder-mask opening over the frame land
        m.SetShape(pcbnew.SHAPE_T_SEGMENT)
        m.SetStart(P(*L(*p)))
        m.SetEnd(P(*L(*q)))
        m.SetLayer(pcbnew.B_Mask)
        m.SetWidth(FromMM(D.SHIELD_W + 0.1))
        board.Add(m)
        ITEMS.append(m)
    for v in SH["vias"]:
        via(*v, "GND")
    SHIELD_OUTLINES[f"{ch}_{key}"] = [toL(*_rot_pt(L(*v), k)) for v in SH["verts"]]


SHIELD_OUTLINES = {}


def _rot_pt(b, k):
    dx, dy = b[0] - CX, b[1] - CY
    a = math.radians(-90 * k)
    return (CX + dx * math.cos(a) + dy * math.sin(a), CY - dx * math.sin(a) + dy * math.cos(a))


# ----------------------------------------------------------------------------- one element
def build_element(k):
    ch = D.CHANNEL_NAMES[k]
    n = k + 1
    s = lambda name: f"{ch}_{name}"  # noqa: E731
    r = lambda base: f"{base}{n}"    # noqa: E731  (refs: e.g. U1x -> U11.. per channel)

    # antenna module (top side), customer orientation for element 0
    ant = add_fp(f"ANT{n}", "ANT", ch, back=False, at=(0, 0), rot=0,
                 pads={"C": "GND", "M": "GND", "L1_0": s("L1_F0"), "L1_90": s("L1_F90"),
                       "L2_0": s("L2_F0"), "L2_90": s("L2_F90")})
    sant = add_fp(f"ANT{n}S", "SANT", ch, back=False, at=D.S_CENTER, rot=0,
                  pads={"C": "GND", "M": "GND", "F0": s("S_F0"), "F90": s("S_F90")})
    for p in sant.Pads():
        if p.GetNumber().startswith(("F", "NC")):
            p.SetLocalClearance(FromMM(D.ANT_FEED_ANTIPAD))
    SANT[k] = sant
    for p in ant.Pads():
        if p.GetNumber().startswith("L"):        # feed pins: D3.5 copper keep-out (GPDF6010.A DS 4.5)
            p.SetLocalClearance(FromMM(D.ANT_FEED_ANTIPAD))
        elif p.GetNumber() == "C":               # centre screw: grounding point, solid to all planes
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

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
    c.to(q1[0], LINE1 - LIM_EXIT - LIM_SPAN - 2.2)       # limiter OUT, then LIM_EXIT on to LINE1
    lim = add_fp(f"LM{n}1", "LIM", ch, pads={"2": s("L1_HYB"), "7": s("L1_LIM"), **LIM_GND})
    lim_place(c, lim)
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
    lim2 = add_fp(f"LM{n}2", "LIM", ch, pads={"2": s("L2_HYB"), "7": s("L2_LIM"), **LIM_GND})
    c2.u = (1.0, 0.0)
    lim_place(c2, lim2, gap=4.5)
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
    # common port: leave pin 2 diagonally, run EAST (inside the shield can), then drop onto the SMA
    # from the north. Keeps the can's 45 deg corner clear of the SMA body.
    cc = Chain(dxp, "2", s("COM"), (1 / math.sqrt(2), 1 / math.sqrt(2)))
    p2 = padL(dxp, "2")
    cc.to(p2[0] + 0.6, p2[1] + 0.6)
    cc.turn(1.0, 0.0)
    lc = add_fp(f"L{n}43", "L4N3", ch, pads={"1": s("COM"), "2": s("COM_M")}, show_ref=False)
    cc.part(lc, "1", "2", 0.9, s("COM_M"))
    cb = add_fp(f"C{n}43", "C100P", ch, pads={"1": s("COM_M"), "2": s("RFOUT")}, show_ref=False)
    cc.part(cb, "1", "2", 1.0, s("RFOUT"))
    shunt(f"C{n}44", "C1P5", ch, cb, "1", s("COM_M"), 0, -1, off=1.0)   # same node as L43 pin 2
    sma = add_fp(f"J{n}", "SMA", ch, at=(40.5, 40.5), rot=0, pads={"1": s("RFOUT"), "2": "GND"})
    sp = padL(sma, "1")
    cc.end(sma, "1", mid=[(sp[0], cc.p[1])])     # east, then down onto the SMA pin between its GND legs

    l_items = list(ITEMS)
    s_items, s_sma = s_chain(k, n, ch, s)

    # star branch entry: +5V trunk (In1.Cu) -> FB{n} ferrite -> +5V_CHn, 10 uF bulk, then In1.Cu
    # traces to this channel's 4 LNA bias vias (routed once on CH1, replayed on CH2..CH4)
    bnet = f"+5V_{ch}"
    fb = add_fp(f"FB{n}", "FB", ch, pads={"1": "+5V", "2": bnet})
    orient(fb, "1", "2", 1, 0, step=90)
    move_pad_to(fb, "1", *D.FB_AT)
    vin = _off(padL(fb, "1"), -1.1, 0)
    track([padL(fb, "1"), vin], "+5V", D.PWR_W)
    via(*vin, "+5V")
    TRUNK_END[k] = vin
    blk = add_fp(f"C{n}90", "C10U", ch, pads={"1": bnet, "2": "GND"}, show_ref=False)
    orient(blk, "1", "2", 0, 1, step=90)
    move_pad_to(blk, "1", padL(fb, "2")[0] + 2.4, padL(fb, "2")[1])
    track([padL(fb, "2"), padL(blk, "1")], bnet, D.PWR_W)
    gnd_stub(blk, "2", 0, 1, 1.0)
    vch = _off(padL(fb, "2"), 0, -1.2)
    track([padL(fb, "2"), vch], bnet, D.PWR_W)
    via(*vch, bnet)
    if k == 0:
        for bv in BIAS_VIAS:
            print("  bias route ->", tuple(round(v, 1) for v in bv[:2]), flush=True)
            LOCAL_BIAS_ROUTES.append(route_inner(L(*vch), L(*bv[:2]), bnet, D.BIAS_W, local_bbox=True))
    for path in LOCAL_BIAS_ROUTES:
        inner_track([toL(*p) for p in path], bnet, D.BIAS_W)
    BIAS_VIAS.clear()
    sma = FPS[f"J{n}"]
    shield_frame(k, n, ch, "L", [it for it in l_items if not (isinstance(it, pcbnew.FOOTPRINT)
                                                         and it.GetReference().endswith("S"))], f"{ch}_RFOUT", sma)
    shield_frame(k, n, ch, "S", s_items + [SANT[k]], f"{ch}_S_RFOUT", None)


def s_chain(k, n, ch, s):
    """NavIC S branch (project 02 Rev B): S patch at lambda/2 spacing (r 42.53 mm), outer feed pair F0 (+x) / F90 (-y)
    -> Xinger C2327J5003AHF on the outward bisector (equal-length feeds) -> CLM-83-2W+ -> [2.4 pF / 2.7 nH] TQP3M9037
    -> TA1442A -> TQP3M9037 -> TA1442A -> TA1442A -> 100 pF -> SMA near the board rim. Returns (items, sma)."""
    start = len(ITEMS)
    sant = SANT[k]
    sc = D.S_CENTER
    r2 = 1 / math.sqrt(2)
    xh = add_fp(f"HY{n}3", "XHYB", ch, pads={"1": s("S_HYB"), "3": s("S_ISO"), "2": "GND", "5": "GND"})
    for pa, pb in (("6", "4"), ("4", "6")):            # pin to F0, pin to F90
        orient(xh, pa, pb, -r2, -r2)
        xh.SetPosition(P(*L(sc[0] + D.S_HYB_T * r2, sc[1] - D.S_HYB_T * r2)))
        m_ab = [(padL(xh, pa)[i_] + padL(xh, pb)[i_]) / 2 for i_ in (0, 1)]
        m_13 = [(padL(xh, "1")[i_] + padL(xh, "3")[i_]) / 2 for i_ in (0, 1)]
        if math.dist(m_ab, sc) < math.dist(m_13, sc):
            break
    # RHCP: F90 sits +90 deg (CCW, top view) from F0, so F0 must lead: F0 -> DIRECT (4), F90 -> COUPLED (6)
    assert (pa, pb) == ("4", "6"), f"S hybrid orientation gives F0 -> pin {pa}: use config 2 (pin 3 IN) instead"
    pad(xh, pa).SetNet(net(s("S_F0")))
    pad(xh, pb).SetNet(net(s("S_F90")))
    lf0 = math.dist(padL(sant, "F0"), padL(xh, pa))
    lf90 = math.dist(padL(sant, "F90"), padL(xh, pb))
    assert abs(lf0 - lf90) < 0.02, f"S feed lengths differ: {lf0:.3f} / {lf90:.3f}"
    rf_link(padL(sant, "F0"), padL(xh, pa), s("S_F0"))
    rf_link(padL(sant, "F90"), padL(xh, pb), s("S_F90"))
    a1, a3 = padL(xh, "1"), padL(xh, "3")
    ln = math.dist(a1, a3)
    dx_, dy_ = (a3[0] - a1[0]) / ln, (a3[1] - a1[1]) / ln       # row direction pin 1 -> pin 3
    shunt(f"R{n}3", "R50", ch, xh, "3", s("S_ISO"), r2, -r2, off=1.2)   # ISO load straight outward from pin 3
    track([padL(xh, "2"), padL(xh, "5")], "GND", 0.2)  # pin 2 tied to pin 5 under the body (pad gap 0.65 mm)
    gnd_stub(xh, "5", -r2, r2, 0.9)
    c = Chain(xh, "1", s("S_HYB"), (0.0, -1.0))
    q = (a1[0] - 1.6 * dx_, a1[1] - 1.6 * dy_)        # off pin 1, away from pins 2/3, then straight out
    c.to(*q)
    lim = add_fp(f"LM{n}3", "LIM", ch, pads={"2": s("S_HYB"), "7": s("S_LIM"), **LIM_GND})
    lim_place(c, lim, gap=6.0)
    c.turn(0.0, -1.0)
    lna_stage(c, n, ch, "S", 1, s)
    saw(c, n, ch, "S", 1, s)
    lna_stage(c, n, ch, "S", 2, s)
    saw(c, n, ch, "S", 2, s)
    c.to(c.p[0], c.p[1] - 3.1)            # turn east onto the free arc beside the next L patch (rim limit)
    c.turn(1.0, 0.0)
    saw(c, n, ch, "S", 3, s)              # SAW2 -> SAW3 direct: both sit between DC blocks (LNA2 out, C{n}35)
    cb = add_fp(f"C{n}35", "C100P", ch, pads={"1": c.net, "2": s("S_RFOUT")}, show_ref=False)
    c.part(cb, "1", "2", 1.4, s("S_RFOUT"))
    sma = add_fp(f"J{n}S", "SMA", ch, at=(c.p[0] + 5.0, c.p[1]), rot=0, pads={"1": s("S_RFOUT"), "2": "GND"})
    c.end(sma, "1")
    bx, by = L(*toL(*xy(sma.GetPosition())))
    rr = math.hypot(bx - CX, by - CY)
    print(f"S chain {ch}: feeds {lf0:.3f}/{lf90:.3f} mm, SMA at r {rr:.1f} mm")
    assert rr <= D.S_SMA_MAX_R, f"S SMA at r {rr:.1f} > {D.S_SMA_MAX_R}"
    S_SMA_LOCAL[k] = toL(*xy(sma.GetPosition()))
    return ITEMS[start:], sma


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
        gnd_stub(dxp, num, dx / nn, dy / nn, 1.6 if num == "8" else 1.0)


def lim_place(c, lim, gap=2.2):
    """CLM-83-2W+ (DL1721): IN (2) and OUT (7) face each other, so the limiter sits in-line.
    GND as PL-377: 3 plugged vias in the paddle, a via off each paddle tab, pins 3-4 and 5-6 tied
    with one via each, pins 1 and 8 their own via; all vias leave diagonally, away from the RF row.
    The chain then runs LIM_EXIT straight on, so a following turn clears the GND pins 6/8."""
    c.part(lim, "2", "7", gap, c.net.replace("_HYB", "_LIM"))
    a, b = padL(lim, "2"), padL(lim, "7")
    ux, uy = (b[0] - a[0]) / LIM_SPAN, (b[1] - a[1]) / LIM_SPAN
    cx, cy = toL(*xy(lim.GetPosition()))
    for t in (-0.66, 0.0, 0.66):                       # paddle, along the tab axis
        via(cx - t * uy, cy + t * ux, "GND", D.EPVIA_D, D.EPVIA_DRILL)
    for num, tied, along in (("1", None, -1), ("4", "3", -1), ("8", None, 1), ("5", "6", 1)):
        px, py = padL(lim, num)
        if tied:
            track([padL(lim, tied), (px, py)], "GND", D.GND_W)
        lat = (px - a[0]) * -uy + (py - a[1]) * ux        # side of the RF row
        sx, sy = -uy * math.copysign(1, lat), ux * math.copysign(1, lat)
        vx, vy = px + 0.85 * (along * ux + sx), py + 0.85 * (along * uy + sy)
        track([(px, py), (vx, vy)], "GND", D.GND_W)
        via(vx, vy, "GND")
    for sg in (-1, 1):                                  # paddle tabs, outward past the body
        tx, ty = cx - sg * 1.5 * uy, cy + sg * 1.5 * ux
        vx, vy = cx - sg * 2.3 * uy, cy + sg * 2.3 * ux
        track([(tx, ty), (vx, vy)], "GND", D.GND_W)
        via(vx, vy, "GND")
    c.to(b[0] + LIM_EXIT * ux, b[1] + LIM_EXIT * uy)


def lna_stage(c, n, ch, band, idx, s):
    """100 pF in -> TQP3M9037 -> 100 pF out, 18 nH choke from the out node to +5V
    with 100 pF + 1 uF to GND (TQP3M9037 eval board, as project 16)."""
    b = {"L1": "1", "L2": "2", "S": "3"}[band]
    tag = f"{band}_A{idx}"
    cin = add_fp(f"C{n}{b}{idx}1", "C2P4" if band == "S" else "C100P", ch,
                 pads={"1": c.net, "2": s(f"{tag}IN")}, show_ref=False)
    c.part(cin, "1", "2", 1.2, s(f"{tag}IN"))
    if band == "S":   # Qorvo 2.3-2.6 GHz ref. design: 2.7 nH shunt at the LNA input (opposite the bias side)
        ux_, uy_ = c.u
        shunt(f"L{n}{b}{idx}7", "L2N7", ch, cin, "2", s(f"{tag}IN"), uy_, -ux_, off=0.9)
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
    bnet = f"+5V_{ch}"           # this channel's own bias net (star branch behind FB{n})
    lb = shunt(f"L{n}{b}{idx}", "L5N6" if band == "S" else "L18N", ch, cout, "1", s(f"{tag}OUT"), side[0], side[1],
               off=1.3, other=bnet)
    bx, by = padL(lb, "2")
    nx, ny = bx + 1.0 * side[0], by + 1.0 * side[1]
    track([(bx, by), (nx, ny)], bnet, D.PWR_W)
    via(nx, ny, bnet)
    BIAS_VIAS.append((nx, ny, side))
    for j, (key, dist) in enumerate((("C100P", -1.4), ("C1U", 1.4))):
        cp = add_fp(f"C{n}{b}{idx}{3 + j}", key, ch, pads={"1": bnet, "2": "GND"}, show_ref=False)
        orient(cp, "1", "2", side[0], side[1], step=45)
        move_pad_to(cp, "1", bx + dist * ux, by + dist * uy)
        track([(bx, by), padL(cp, "1")], bnet, D.PWR_W)
        gnd_stub(cp, "2", side[0], side[1], 0.8)


def saw_link(c, n, ch, band, s):
    """100 pF between SAW 2 and SAW 3: gives each B8889 port its own 6.8 nH shunt pad and keeps
    the SAWs DC-isolated from each other."""
    b = {"L1": "1", "L2": "2", "S": "3"}[band]
    k = add_fp(f"C{n}{b}31", "C100P", ch, pads={"1": c.net, "2": s(f"{band}_S3IN")}, show_ref=False)
    c.part(k, "1", "2", 1.4, s(f"{band}_S3IN"))
    pend = getattr(c, "_b8889_out", None)
    if pend:   # SAW 2 output shunt, on the side of the line away from the bias network
        ux, uy = c.u
        shunt(pend[0], "L6N8", ch, k, "1", pad(k, "1").GetNetname(), -uy, ux, off=1.0)
        c._b8889_out = None


def saw(c, n, ch, band, idx, s):
    b = {"L1": "1", "L2": "2", "S": "3"}[band]
    key = {"L1": "SAW_L1", "L2": "SAW_L2", "S": "SAW_S"}[band]
    out_pin = {"L1": "3", "L2": "4", "S": "5"}[band]
    gnds = {"L1": ("2", "4"), "L2": ("2", "3", "5"), "S": ("1", "3", "4", "6")}[band]
    tag = f"{band}_S{idx}"
    f = add_fp(f"FL{n}{b}{idx}", key, ch, pads={("2" if band == "S" else "1"): c.net, out_pin: s(f"{tag}OUT"),
                                                 **{q: "GND" for q in gnds}})
    node_fp, node_pin, in_net = c.fp, c.pin, c.net
    c.part(f, "2" if band == "S" else "1", out_pin, 2.6 if band == "S" else 1.8, s(f"{tag}OUT"))
    ux, uy = c.u
    vx, vy = -uy, ux
    # GND pads: radial stub away from the in/out diagonal, 0.2 mm wide, to a 0.25 mm via
    a, bq = padL(f, "2" if band == "S" else "1"), padL(f, out_pin)
    mx, my = (a[0] + bq[0]) / 2, (a[1] + bq[1]) / 2
    if band == "S":
        # TA1442A: large GND pads -> plugged vias in the pads (lowest ground inductance = stop-band depth);
        # the 1.70 mm A pad (1) gets two
        for q in gnds:
            px, py = padL(f, q)
            if q == "1":
                ax_, ay_ = padL(f, "2")
                hx, hy = padL(f, "6")        # pad 6 sits in the same column as pad 1
                cx_, cy_ = px - hx, py - hy
                cn = math.hypot(cx_, cy_)
                for t in (-0.42, 0.42):
                    via(px + t * cx_ / cn, py + t * cy_ / cn, "GND", D.EPVIA_D, D.EPVIA_DRILL)
            else:
                via(px, py, "GND", D.EPVIA_D, D.EPVIA_DRILL)
        gnds = ()
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
    X0, Y0 = 18.0, -41.0           # element-0 local: NNW of CH1, clear of the N NavIC S patch (project 02)
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
    spine = (sx, node[1] + 4.6)                # clears the SMC (DO-214AB) TVS body
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
    for i in range(2):                  # 4 vias = the star point, one per channel trunk
        vy = spine[1] + 1.8 + 1.4 * i
        track([last, (sx, vy)], "+5V", D.VIN_W)
        last = (sx, vy)
        for sgn in (-1, 1):
            POWER_VIA_OBJS.append(via(sx + sgn * 0.95, vy, "+5V"))
            track([(sx, vy), (sx + sgn * 0.95, vy)], "+5V", D.PWR_W)
    tp1 = add_fp("TP1", "TP", ch, pads={"1": "+5V"})
    move_pad_to(tp1, "1", sx, last[1] + 2.4)
    track([last, padL(tp1, "1")], "+5V", D.PWR_W)
    tp2 = add_fp("TP2", "TP", ch, pads={"1": "GND"})
    move_pad_to(tp2, "1", sx - g * 3.6, last[1] + 2.4)


def dedupe_vias(min_c2c=D.VIA_D + 0.30):
    """Adjacent shield frames (S strip next to the neighbouring L octagon) each place frame vias on the shared wall:
    delete any GND via closer than min_c2c to one already kept."""
    kept, dele = [], []
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "GND":
            continue
        p = xy(t.GetPosition())
        r = ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
        if any(math.dist(p, q) < r + rq + 0.30 for q, rq in kept):
            dele.append(t)
        else:
            kept.append((p, r))
    for t in dele:
        board.Remove(t)
    print(f"dedupe: removed {len(dele)} overlapping GND vias")


def place_power_block():
    """Turn the (vertically built) power block so it runs along +x, J5 pin 1 at POWER_J5_AT."""
    items = list(ITEMS)
    p = pad(FPS["J5"], "1").GetPosition()
    f = pad(FPS["F1"], "1").GetPosition()
    for deg in (90, -90):
        for it in items:
            it.Rotate(p, pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
        f2 = pad(FPS["F1"], "1").GetPosition()
        if f2.x - p.x > 0:
            break
        for it in items:
            it.Rotate(p, pcbnew.EDA_ANGLE(-deg, pcbnew.DEGREES_T))
    tx, ty = CX + POWER_J5_AT[0], CY + POWER_J5_AT[1]
    d = VECTOR2I(FromMM(tx) - p.x, FromMM(ty) - p.y)
    for it in items:
        it.Move(d)
    POWER_VIAS[:] = [xy(v.GetPosition()) for v in POWER_VIA_OBJS]
    ITEMS.clear()


# ----------------------------------------------------------------------------- planes, vias
def zones():
    cx, cy = D.BOARD_CENTER
    r = D.BOARD_RADIUS - 0.5
    for layer, nname in ((pcbnew.F_Cu, "GND"), (pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "GND"),
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
            if (p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() == "GND"
                    and not fp.GetReference().startswith("ANT")):
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


def logo(name, x, y, back):
    f = load_fp(D.LIB, name)
    f.SetReference("LOGO" + ("B" if back else "T"))
    board.Add(f)
    f.SetPosition(P(x, y))
    if back:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.Reference().SetVisible(False)
    f.Value().SetVisible(False)


def silk():
    """Project 02 legends. Bottom (component side, read mirrored from the top): title + stack-up on the south arc
    below the S patch, BEL logo SE, +5V IN at J5, L/S channel labels at the SMAs. Top: BEL logo + title at the centre
    (free square between the four L patches), channel labels at the patches."""
    cx, cy = D.ARRAY_CENTER
    B, F = pcbnew.B_SilkS, pcbnew.F_SilkS
    text("BEL CRL  CRL-LS-CRPA4  L1 + L2/L5 + NavIC S CRPA FE  REV A", cx, cy + 91.6, B, 1.1, True)
    text("4L 1.6 mm  FR-4 / RO4350B 0.168 (L3-L4)  RF on L4", cx, cy + 94.3, B, 0.9, True)
    logo("BEL_Logo_Silk_Small", cx - 28.0, cy + 83.0, True)        # bottom view: mirrored, appears at SE
    jx, jy = POWER_J5_AT
    text("+5V IN", cx + jx + 8.0, cy + jy + 8.0, B, 1.1, True)            # between J5 and D1 (clear of the TVS)
    text("4.75-5.25 V  2.3 A", cx + jx + 8.0, cy + jy + 9.8, B, 0.8, True)
    logo("BEL_Logo_Silk", cx, cy - 4.0, False)
    text("CRL-LS-CRPA4  ANTENNA SIDE", cx, cy + 3.5, F, 1.4, False)
    text("L1 + L2/L5 + NavIC S  REV A", cx, cy + 6.4, F, 1.1, False)
    for k, name in enumerate(D.CHANNEL_NAMES):
        rx, ry = rot_k(-5.5, -11.6, k)          # L SMA (inner corner of the L frame)
        text(name + " L", cx + rx, cy + ry, B, 1.2, True)
        sx_, sy_ = S_SMA_LOCAL[0]
        rx, ry = rot_k(sx_ + EX + 6.5, sy_ + EY, k)
        text(name + " S", cx + rx, cy + ry, B, 1.2, True)
        rx, ry = rot_k(-45.5, -45.5 - 35.0, k)  # outside the L patch
        text(name + " L", cx + rx, cy + ry, F, 2.0, False)
        rx, ry = rot_k(D.S_CENTER[0] + D.ELEMENT0_OFFSET[0], D.S_CENTER[1] + D.ELEMENT0_OFFSET[1] - 15.5, k)
        text(name + " S", cx + rx, cy + ry, F, 1.6, False)


def fiducials():
    cx, cy = D.ARRAY_CENTER
    for i, (dx, dy) in enumerate(((30, -86), (-90, 18), (90, -18))):
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
    (FAB / "_parts.json").write_text(json.dumps(rows, indent=0))
    lens = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            lens[t.GetNetname()] = lens.get(t.GetNetname(), 0.0) + ToMM(t.GetLength())
    bias = dict(pads=sum(1 for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname().startswith("+5V")),
                chokes=sum(1 for fp in board.GetFootprints() if fp.GetValue() == "18nH"),
                vias=sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname().startswith("+5V")),
                plane="none: star traces on In1.Cu", trunks_mm={k: round(v, 1) for k, v in TRUNK_PATHS.items()},
                ferrites=sum(1 for fp in board.GetFootprints() if fp.GetReference().startswith("FB")))
    (FAB / "_bias.json").write_text(json.dumps(bias))
    (FAB / "_shield.json").write_text(json.dumps(
        {"outline_board": {c: [[round(x + CX + EX, 3), round(y + CY + EY, 3)] for x, y in v]
                           for c, v in SHIELD_OUTLINES.items()},
         "notches_board_ch1": {kk: [[round(x + CX + EX, 3), round(y + CY + EY, 3)] for x, y in SHIELD[kk]["notches"]]
                               for kk in SHIELD},
         "frame_vias_per_channel": {kk: len(SHIELD[kk]["vias"]) for kk in SHIELD}, "frame_w": D.SHIELD_W,
         "height": D.SHIELD_H}, indent=1))
    (FAB / "_netlen.json").write_text(json.dumps({k: round(v, 3) for k, v in sorted(lens.items())}, indent=0))


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
        "meta": {"filename": "CRL-LS-CRPA4.kicad_pro", "version": 3},
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
                                  {"netclass": "PWR", "pattern": "+5V*"}, {"netclass": "PWR", "pattern": "VIN*"}],
        },
    }
    (KDIR / "CRL-LS-CRPA4.kicad_pro").write_text(json.dumps(pro, indent=2))
    (KDIR / "CRL-LS-CRPA4.kicad_dru").write_text(
        "(version 1)\n"
        "# B7504 / B8889 SAW land patterns (from the customer board) have a 0.14 mm pad-to-pad gap\n"
        "(rule \"SAW land pattern\"\n"
        "  (condition \"A.memberOfFootprint('FL*') && B.memberOfFootprint('FL*')\")\n"
        "  (constraint clearance (min 0.10mm)))\n")


def star_trunks():
    """Star point = the +5V via ladder after Q1. One 0.8 mm In1.Cu trunk per channel to FB{n}."""
    ends = {k: _rot_end(k) for k in range(4)}
    used = set()
    for k in sorted(range(4), key=lambda k: -math.dist(ends[k], POWER_VIAS[0])):   # longest first
        best = min((i for i in range(len(POWER_VIAS)) if i not in used),
                   key=lambda i: math.dist(POWER_VIAS[i], ends[k]))
        used.add(best)
        path = route_inner(POWER_VIAS[best], ends[k], "+5V", D.TRUNK_W)
        ITEMS.clear()
        track([toL(*p) for p in path], "+5V", D.TRUNK_W, layer=pcbnew.In1_Cu)
        TRUNK_PATHS[D.CHANNEL_NAMES[k]] = sum(math.dist(p, q) for p, q in zip(path[:-1], path[1:]))
    ITEMS.clear()


def _rot_end(k):
    """board coordinates of channel k's trunk via (element-local point rotated by -90k about the array centre)."""
    bx, by = L(*TRUNK_END[k])
    dx, dy = bx - CX, by - CY
    a = math.radians(-90 * k)
    return (CX + dx * math.cos(a) + dy * math.sin(a), CY - dx * math.sin(a) + dy * math.cos(a))


TRUNK_PATHS = {}


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
    dedupe_vias()
    power_block()
    place_power_block()
    star_trunks()
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
    (FAB / "_debug_layout.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
