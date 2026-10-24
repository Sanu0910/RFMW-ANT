"""Build the NOVA-RF1 PCB from design.py + pinmap.py (run inside KiCad 9 Python / pcbnew).

Stage 1 (this file): load every resolved part onto its real footprint, create all nets, assign
pad nets, and place parts grouped by functional block with a board outline. Pending-datasheet
chips are skipped. Routing, zones and RF matching come after the remaining pinouts arrive.

  python3 make_pcb.py        -> ../01_kicad/nova-rf1.kicad_pcb (placement + ratsnest, unrouted)
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import pinmap

KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
PCB = os.path.join(KDIR, "nova-rf1.kicad_pcb")
FPROOT = "/usr/share/kicad/footprints"
CUSTOM = os.path.join(KDIR, "nova-rf1.pretty")
OX, OY = 30.0, 30.0            # board origin on the KiCad page
BW, BH = 100.0, 60.0           # compact envelope (mm), reference-device proportions; 2-sided
INSET = 5.0                   # interior margin: edge band for the locked connectors


def mm(v):
    return pcbnew.FromMM(v)


def add_outline(board):
    """Closed rectangular board edge on Edge.Cuts (4 connected segments)."""
    x0, y0, x1, y1 = OX, OY, OX + BW, OY + BH
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for a, b in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)


def load_fp(board, libid):
    lib, name = libid.split(":")
    path = CUSTOM if lib == "nova-rf1" else os.path.join(FPROOT, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {libid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def build():
    board = pcbnew.BOARD()
    # 4-layer stackup
    board.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "GND")
    board.SetLayerName(pcbnew.In2_Cu, "PWR")

    # create all nets up front
    netinfo = {}
    for n in sorted(D.NETS):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netinfo[n] = ni

    def net(n):
        if n not in netinfo:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            netinfo[n] = ni
        return netinfo[n]

    # Edge-anchored parts: connectors, antennas, buttons placed on the board
    # perimeter (board-local mm from the outline origin) and LOCKED, so the
    # functional-group placer organizes the interior around real anchors.
    # (x, y, rot) local to the outline; x in [0,BW], y in [0,BH].
    FIXED = {
        "J_USB":  (BW / 2, BH - 6.0, 0),      # USB-C centered on bottom edge
        "J_SWD":  (BW - 16.0, BH - 6.0, 0),   # Tag-Connect SWD near bottom-right
        "X10":    (6.0, BH / 2, 90),          # battery connector on left edge
        "J_GPIO": (BW - 5.0, BH / 2, 0),      # 2x9 GPIO header on right edge (native tall axis)
        "J_SUBG": (9.0, 5.5, 0),              # sub-GHz U.FL top-left
        "X6":     (23.0, 5.5, 0),             # 18-pin FFC on top edge (sub-board link)
    }
    # spread antennas + buttons across the rest of the top edge, scaled to BW
    _top = ["ANT1", "ANT_NFC", "ANT_LF", "SW_O", "SW_B", "SW_U", "SW_D", "SW_L", "SW_R"]
    _xa, _xb = 33.0, BW - 8.0
    for i, r in enumerate(_top):
        FIXED[r] = (_xa + (_xb - _xa) * i / (len(_top) - 1), 5.5, 0)

    parts = {p[0]: p for p in D.PARTS}
    # group parts by functional group for placement
    groups = {}
    placed_refs = []
    for ref, p in parts.items():
        if ref in pinmap.PENDING:
            continue
        groups.setdefault(p[5], []).append((ref, p))

    # Compact two-sided placement, legal by construction: ICs/connectors/larger
    # parts on the TOP side, small passives on the BOTTOM side. Each pass shelf-
    # packs the interior with slot = bbox + GAP, so courtyards never overlap on
    # a side; top and bottom share XY (different layers). No stochastic anneal.
    GAP = 0.7
    x0 = OX + INSET
    x1 = OX + BW - INSET
    unconn = 0
    # footprint strings whose parts go on the bottom (small 2-pin passives)
    BOTTOM_FP = {"R_0402", "C_0402", "C_0805", "R_1206", "0201", "ESD_0201",
                 "R_array_4x0402", "Inductor_0806", "SOT-23", "SOT-23-6", "SC-70-5", "VSSOP-8", "DFN-6"}
    # crystals/osc parts placed as a vertical cluster directly below their chip
    # (signal integrity + makes the OSC nets route short; fixes the LSE_OUT open)
    CLUSTER = {"U1": ["Y1", "Y2"], "U2": ["ZQ3"], "U3": ["ZQ1"]}
    cluster_children = {c for v in CLUSTER.values() for c in v}
    # external parts not populated on the board (battery pack is wired via X10)
    OFFBOARD = {"BT1"}

    # 1. create every footprint, assign nets, split into fixed / top / bottom / cluster-children
    fp_by_ref = {}
    fixed_fps, top_fps, bot_fps = [], [], []
    for gname, members in groups.items():
        for ref, p in members:
            libid = pinmap.FOOTPRINT.get(p[4])
            if libid is None or ref in OFFBOARD:
                continue
            fp = load_fp(board, libid)
            fp.SetReference(ref)
            fp.SetValue(p[1])
            board.Add(fp)
            fp_by_ref[ref] = fp
            padmap = pinmap.pad_nets(ref) or {}
            for pad in fp.Pads():
                num = pad.GetNumber()
                if num in padmap:
                    pad.SetNet(net(padmap[num]))
                else:
                    unconn += 1
                    pad.SetNet(net(f"unconnected-({ref}-{num})"))
            if ref in FIXED:
                fixed_fps.append((ref, fp))
            elif ref in cluster_children:
                continue  # placed with its parent IC
            elif p[4] in BOTTOM_FP:
                bot_fps.append((ref, fp))
            else:
                top_fps.append((ref, fp))

    # 2. fixed edge connectors
    for ref, fp in fixed_fps:
        fx, fy, frot = FIXED[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(OX + fx), mm(OY + fy)))
        if frot:
            fp.SetOrientationDegrees(frot)
        fp.SetLocked(True)
        placed_refs.append(ref)

    def bbw(fp):
        return pcbnew.ToMM(fp.GetBoundingBox().GetWidth())

    def bbh(fp):
        return pcbnew.ToMM(fp.GetBoundingBox().GetHeight())

    def shelf_pack(fps, xa, xb, y_start, flip):
        x, y, shelf = xa, y_start, 0.0
        for ref, fp in sorted(fps, key=lambda rf: -bbw(rf[1])):
            if flip:
                fp.Flip(fp.GetPosition(), False)
            kids = CLUSTER.get(ref, [])
            w = max([bbw(fp)] + [bbw(fp_by_ref[k]) for k in kids]) + GAP
            h = bbh(fp) + sum(bbh(fp_by_ref[k]) + GAP for k in kids) + GAP
            if x + w > xb and x > xa:
                x = xa; y += shelf + GAP; shelf = 0.0
            cx = x + w / 2
            fp.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(y + bbh(fp) / 2)))
            placed_refs.append(ref)
            cy = y + bbh(fp) + GAP
            for k in kids:                       # stack crystals under the chip
                kfp = fp_by_ref[k]
                kfp.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy + bbh(kfp) / 2)))
                placed_refs.append(k)
                cy += bbh(kfp) + GAP
            x += w
            shelf = max(shelf, h)
        return y + shelf

    # TOP: inset clear of the left (X10) and right (J_GPIO) edge connectors, below the top band
    top_bottom = shelf_pack(top_fps, OX + 12.0, OX + BW - 10.0, OY + 9.0, flip=False)
    # BOTTOM: full interior width
    bot_bottom = shelf_pack(bot_fps, x0, x1, OY + INSET, flip=True)
    print(f"  top packed to y={top_bottom - OY:.1f}mm, bottom to y={bot_bottom - OY:.1f}mm (BH={BH})")

    add_outline(board)
    board.BuildListOfNets()
    pcbnew.SaveBoard(PCB, board)
    print(f"placed {len(placed_refs)} parts, {board.GetNetCount()} nets, "
          f"{unconn} unconnected pads; skipped {len(pinmap.PENDING)} pending")


if __name__ == "__main__":
    build()
