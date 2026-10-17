"""Finish the connections the autorouter left open (driven by the KiCad DRC 'unconnected' list).

Grid A* over three routing layers (F.Cu, In2.Cu, B.Cu) with via transitions. In1 stays a solid GND
plane; In2 is the +3V3 plane, so tracks there carry a cost penalty and the pour refills around them.
GND / +3V3 copper that is only isolated from its plane gets a fan-out via instead.
Clearances: max(net-class clearance of both nets) + margin; obstacles are inflated pads, tracks, vias.
"""
import heapq, json, math
import pcbnew
import make_pcb as M
from patch_fan import via_near

G = 0.05
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
VIA_COST = 12.0
L3_PENALTY = 0.6
MARGIN = 0.045
RIPUP = False             # set by run(): allow ripping up other nets' autorouted copper
SOFTCOST = 6.0


def ncl(item):
    try:
        name = item.GetNetClassName()
    except Exception:
        name = "Default"
    return M.NETCLASS.get(name, M.NETCLASS["Default"])[0]


class Grid:
    def __init__(self, board, net):
        self.board, self.net = board, net
        ni = board.FindNet(net)
        self.nc = ni.GetNetCode()
        self.cl = M.NETCLASS.get(ni.GetNetClassName(), M.NETCLASS["Default"])[0]
        self.w = 0.3 if ni.GetNetClassName() == "Power" else 0.15
        self.nx, self.ny = int(M.BW / G) + 1, int(M.BH / G) + 1
        self.blk = [bytearray(self.nx * self.ny) for _ in LAYERS]
        self.viablk = bytearray(self.nx * self.ny)
        self.soft = {}            # cell index -> list of removable GND items (all layers)
        self.build()

    def _disk(self, arr, x, y, r):
        nx = self.nx
        i0, i1 = max(0, int((x - r) / G)), min(nx - 1, int((x + r) / G) + 1)
        j0, j1 = max(0, int((y - r) / G)), min(self.ny - 1, int((y + r) / G) + 1)
        r2 = r * r
        for j in range(j0, j1 + 1):
            dy2 = (j * G - y) ** 2
            for i in range(i0, i1 + 1):
                if (i * G - x) ** 2 + dy2 <= r2:
                    arr[j * nx + i] = 1

    def _rect(self, arr, x0, y0, x1, y1, r):
        nx = self.nx
        for j in range(max(0, math.ceil((y0 - r) / G)), min(self.ny - 1, math.floor((y1 + r) / G)) + 1):
            for i in range(max(0, math.ceil((x0 - r) / G)), min(nx - 1, math.floor((x1 + r) / G)) + 1):
                arr[j * nx + i] = 1

    def _seg(self, arr, x0, y0, x1, y1, r):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / (G / 2)))
        for k in range(n + 1):
            self._disk(arr, x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n, r)

    @staticmethod
    def xy(p):
        return pcbnew.ToMM(p.x) - M.OX, pcbnew.ToMM(p.y) - M.OY

    def build(self):
        hw, vr = self.w / 2, M.VIA_D / 2
        for i in range(self.nx):
            for j in range(self.ny):
                if not M.in_outline(i * G, j * G, 0.5 + hw):
                    for a in self.blk:
                        a[j * self.nx + i] = 1
                if not M.in_outline(i * G, j * G, 0.75):
                    self.viablk[j * self.nx + i] = 1
        gnd = self.board.FindNet("GND").GetNetCode()
        for t in self.board.GetTracks():
            if t.GetNetCode() == self.nc:
                continue
            c = max(self.cl, ncl(t)) + MARGIN
            ripable = (not t.IsLocked()) and t.GetNetClassName() != "RF50" and t.GetNetCode() != gnd
            if (t.GetNetCode() == gnd and self.nc != gnd and t.IsLocked()) or (RIPUP and ripable):
                # GND fan-out copper is "soft": recorded, not blocking (pours re-connect GND pads)
                tmp = bytearray(self.nx * self.ny)
                if isinstance(t, pcbnew.PCB_VIA):
                    x, y = self.xy(t.GetPosition()); rv = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
                    self._disk(tmp, x, y, rv + c + max(hw, vr))
                elif t.GetLayer() in LAYERS:
                    x0, y0 = self.xy(t.GetStart()); x1, y1 = self.xy(t.GetEnd()); rt = pcbnew.ToMM(t.GetWidth()) / 2
                    self._seg(tmp, x0, y0, x1, y1, rt + c + max(hw, vr))
                for k, val in enumerate(tmp):
                    if val:
                        self.soft.setdefault(k, []).append(t)
                continue
            if isinstance(t, pcbnew.PCB_VIA):
                x, y = self.xy(t.GetPosition()); rv = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
                for a in self.blk:
                    self._disk(a, x, y, rv + c + hw)
                self._disk(self.viablk, x, y, rv + max(c, 0.25) + vr)
            elif t.GetLayer() in LAYERS:
                x0, y0 = self.xy(t.GetStart()); x1, y1 = self.xy(t.GetEnd()); rt = pcbnew.ToMM(t.GetWidth()) / 2
                self._seg(self.blk[LAYERS.index(t.GetLayer())], x0, y0, x1, y1, rt + c + hw)
                self._seg(self.viablk, x0, y0, x1, y1, rt + c + vr)
        for p in self.board.GetPads():
            if p.GetNetCode() == self.nc and self.nc > 0:
                continue
            c = max(self.cl, ncl(p)) + MARGIN
            bb = p.GetBoundingBox()
            x0, y0 = self.xy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
            x1, y1 = self.xy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            for li, L in enumerate(LAYERS):
                if th or p.IsOnLayer(L):
                    self._rect(self.blk[li], x0, y0, x1, y1, c + hw)
            self._rect(self.viablk, x0, y0, x1, y1, c + vr)
        for z in list(self.board.Zones()) + [z for fp in self.board.GetFootprints() for z in fp.Zones()]:
            if not z.GetIsRuleArea() or z.GetZoneName() == "EDGE_KEEPOUT":
                continue
            bb = z.GetBoundingBox()
            x0, y0 = self.xy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
            x1, y1 = self.xy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            for li, L in enumerate(LAYERS):
                if z.GetDoNotAllowTracks() and z.IsOnLayer(L):
                    self._rect(self.blk[li], x0, y0, x1, y1, hw)
            if z.GetDoNotAllowVias():
                self._rect(self.viablk, x0, y0, x1, y1, vr)

    def cell(self, x, y):
        return (min(self.nx - 1, max(0, round(x / G))), min(self.ny - 1, max(0, round(y / G))))

    def route(self, starts, goals):
        nx, ny = self.nx, self.ny
        gset = set(goals)
        for (l, i, j) in list(starts) + list(goals):      # endpoints sit inside their own pad
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if 0 <= i + di < nx and 0 <= j + dj < ny:
                        self.blk[l][(j + dj) * nx + i + di] = 0
        tx = sum(g[1] for g in goals) / len(goals); ty = sum(g[2] for g in goals) / len(goals)

        def h(s):
            return math.hypot(s[1] - tx, s[2] - ty) * 0.98
        openq = [(h(s), 0.0, s) for s in starts]
        heapq.heapify(openq)
        prev, cost = {s: None for s in starts}, {s: 0.0 for s in starts}
        dirs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        n = 0
        while openq:
            f, g, s = heapq.heappop(openq)
            if g > cost.get(s, 1e18) + 1e-9:
                continue
            if s in gset:
                path = [s]
                while prev[path[-1]] is not None:
                    path.append(prev[path[-1]])
                return path[::-1]
            n += 1
            if n > 1500000:
                return None
            l, i, j = s
            for dx, dy, c in dirs:
                a, b = i + dx, j + dy
                if 0 <= a < nx and 0 <= b < ny and not self.blk[l][b * nx + a]:
                    ns = (l, a, b)
                    ng = g + c + (L3_PENALTY if l == 1 else 0) + (SOFTCOST if (b * nx + a) in self.soft else 0)
                    if ng < cost.get(ns, 1e18):
                        cost[ns] = ng; prev[ns] = s
                        heapq.heappush(openq, (ng + h(ns), ng, ns))
            if not self.viablk[j * nx + i] and (j * nx + i) not in self.soft:
                for l2 in range(3):
                    if l2 != l and not self.blk[l2][j * nx + i]:
                        ns = (l2, i, j)
                        ng = g + VIA_COST
                        if ng < cost.get(ns, 1e18):
                            cost[ns] = ng; prev[ns] = s
                            heapq.heappush(openq, (ng + h(ns), ng, ns))
        return None


def _pad(board, desc):
    ref = desc.split(" of ")[-1].split(" ")[0]
    num = desc.split("[")[0].split()[-1]
    return [p for p in board.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]


def endpoints(grid, board, it):
    desc = it["description"]
    net = desc[desc.find("[") + 1:desc.find("]")]
    if desc.startswith("Zone"):
        return None
    if "pad" in desc.split("[")[0].lower():
        pad = _pad(board, desc)
        x, y = Grid.xy(pad.GetPosition())
        i, j = grid.cell(x, y)
        th = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        lays = [li for li, L in enumerate(LAYERS) if th or pad.IsOnLayer(L)]
        bb = pad.GetBoundingBox()
        x0, y0 = Grid.xy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())); x1, y1 = Grid.xy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
        for li in lays:                       # the pad itself is free copper for its own net
            for jj in range(math.ceil(y0 / G), math.floor(y1 / G) + 1):
                for ii in range(math.ceil(x0 / G), math.floor(x1 / G) + 1):
                    if pad.HitTest(M.pt(ii * G, jj * G)):
                        grid.blk[li][jj * grid.nx + ii] = 0
        return [(li, i, j) for li in lays]
    x, y = it["pos"]["x"] - M.OX, it["pos"]["y"] - M.OY
    if desc.startswith("Via"):
        i, j = grid.cell(x, y)
        return [(li, i, j) for li in range(3)]
    best = None
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net or t.GetLayer() not in LAYERS:
            continue
        for e in (t.GetStart(), t.GetEnd()):
            ex, ey = Grid.xy(e)
            d = math.hypot(ex - x, ey - y)
            if best is None or d < best[0]:
                best = (d, ex, ey, LAYERS.index(t.GetLayer()), e)
    if best is None:
        return None
    i, j = grid.cell(best[1], best[2])
    e = best[4]
    if any(isinstance(v, pcbnew.PCB_VIA) and v.GetNetname() == net and (v.GetPosition() - e).EuclideanNorm() < M.mm(0.05)
           for v in board.GetTracks()):
        return [(li, i, j, e) for li in range(3)]
    return [(best[3], i, j, e)]


def commit(board, grid, path, net, sa, sb):
    ni = board.FindNet(net)
    pts = []
    for s in path:
        if len(pts) >= 2 and pts[-1][0] == s[0] and pts[-2][0] == s[0]:
            (l0, a0, b0), (l1, a1, b1) = pts[-2], pts[-1]
            if (a1 - a0, b1 - b0) == (s[1] - a1, s[2] - b1):
                pts[-1] = s
                continue
        pts.append(s)
    xy = [M.pt(i * G, j * G) for (_, i, j) in pts]
    # snap the first / last point exactly onto the real endpoint
    for idx, ends in ((0, sa), (-1, sb)):
        for e in ends:
            if len(e) == 4 and (e[0], e[1], e[2]) == pts[idx]:
                xy[idx] = e[3]
    for k in range(len(pts) - 1):
        (l0, _, _), (l1, _, _) = pts[k], pts[k + 1]
        if l0 != l1:
            M.add_via(board, xy[k], ni)
        elif xy[k] != xy[k + 1]:
            M.add_track(board, xy[k], xy[k + 1], grid.w, LAYERS[l0], ni, locked=False)


def run(pcb, drc_json="/work/.drc.json", ripup=None):
    global RIPUP, SOFTCOST
    import os
    if ripup is None:
        ripup = os.environ.get("RIPUP") == "1"
    RIPUP = ripup
    SOFTCOST = 150.0 if ripup else 6.0
    board = pcbnew.LoadBoard(pcb)
    data = json.load(open(drc_json))
    kos = M._keepouts(board)
    done, fail = [], []
    for uc in data.get("unconnected_items", []):
        a, b = uc["items"][0], uc["items"][1]
        net = a["description"][a["description"].find("[") + 1:a["description"].find("]")]
        if net in M.FANOUT and (a["description"].startswith("Zone") or b["description"].startswith("Zone")):
            items = M.all_items(board)
            ok = False
            for it in (a, b):
                if "pad" in it["description"].split("[")[0].lower():
                    ok = via_near(board, _pad(board, it["description"]), items, kos) is not None or ok
            (done if ok else fail).append(net)
            continue
        grid = Grid(board, net)
        sa, sb = endpoints(grid, board, a), endpoints(grid, board, b)
        if not sa or not sb:
            fail.append(net); continue
        path = grid.route([s[:3] for s in sa], [s[:3] for s in sb])
        if not path:
            fail.append(net); continue
        victims = {}
        for (_, i, j) in path:
            for t in grid.soft.get(j * grid.nx + i, []):
                victims[id(t)] = t
        for t in victims.values():
            board.Remove(t)
        commit(board, grid, path, net, sa, sb)
        done.append(net + (f"(-{len(victims)} gnd)" if victims else ""))
        if victims:          # SWIG track lists are stale after Remove(): save and let the caller re-run
            break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("island vias", M.stitch_islands(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(pcb)
    print(f"patched {len(done)}: {' '.join(done)}")
    print(f"failed {len(fail)}: {' '.join(fail)}")
