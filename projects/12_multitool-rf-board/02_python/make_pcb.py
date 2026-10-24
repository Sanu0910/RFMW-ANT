"""Build the CRL-MT1 PCB from design.py + pinmap.py (run inside KiCad 9 Python / pcbnew).

Stage 1 (this file): load every resolved part onto its real footprint, create all nets, assign
pad nets, and place parts grouped by functional block with a board outline. Pending-datasheet
chips are skipped. Routing, zones and RF matching come after the remaining pinouts arrive.

  python3 make_pcb.py        -> ../01_kicad/crl-mt1.kicad_pcb (placement + ratsnest, unrouted)
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import pinmap

KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
PCB = os.path.join(KDIR, "crl-mt1.kicad_pcb")
FPROOT = "/usr/share/kicad/footprints"
CUSTOM = os.path.join(KDIR, "crl-mt1.pretty")
OX, OY = 30.0, 30.0            # board origin on the KiCad page
BW, BH = 110.0, 66.0           # compact envelope (mm), reference-device proportions; 2-sided
INSET = 6.0                   # interior margin: edge band for the locked connectors


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
    path = CUSTOM if lib == "crl-mt1" else os.path.join(FPROOT, lib + ".pretty")
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
        "J_USB":  (BW / 2, BH - 7.0, 0),      # USB-C centered on bottom edge
        "J_SWD":  (BW - 20.0, BH - 7.0, 0),   # Tag-Connect SWD near bottom-right
        "X10":    (7.0, BH / 2, 90),          # battery connector on left edge
        "J_GPIO": (BW - 6.0, BH / 2, 0),      # 2x9 GPIO header on right edge (native tall axis)
        "J_SUBG": (10.0, 6.5, 0),             # sub-GHz U.FL top-left
        "X6":     (27.0, 6.5, 0),             # 18-pin FFC on top edge (sub-board link)
        "ANT1":   (44.0, 6.5, 0), "ANT_NFC": (52.0, 6.5, 0), "ANT_LF": (60.0, 6.5, 0),  # antennas top
        "SW_O": (69.0, 6.5, 0), "SW_B": (76.0, 6.5, 0), "SW_U": (83.0, 6.5, 0),
        "SW_D": (90.0, 6.5, 0), "SW_L": (97.0, 6.5, 0), "SW_R": (104.0, 6.5, 0),
    }

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
    GAP = 1.2
    x0 = OX + INSET
    x1 = OX + BW - INSET
    unconn = 0
    # footprint strings whose parts go on the bottom (small 2-pin passives)
    BOTTOM_FP = {"R_0402", "C_0402", "C_0805", "R_1206", "0201", "ESD_0201",
                 "R_array_4x0402", "Inductor_0806", "SOT-23", "SOT-23-6", "SC-70-5"}

    # 1. create every footprint, assign nets, split into fixed / top / bottom
    fixed_fps, top_fps, bot_fps = [], [], []
    for gname, members in groups.items():
        for ref, p in members:
            libid = pinmap.FOOTPRINT.get(p[4])
            if libid is None:
                continue
            fp = load_fp(board, libid)
            fp.SetReference(ref)
            fp.SetValue(p[1])
            board.Add(fp)
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

    def shelf_pack(fps, xa, xb, y_start, flip):
        x, y, shelf = xa, y_start, 0.0
        # largest-first for tighter rows
        for ref, fp in sorted(fps, key=lambda rf: -pcbnew.ToMM(rf[1].GetBoundingBox().GetWidth())):
            if flip:
                fp.Flip(fp.GetPosition(), False)
            bb = fp.GetBoundingBox()
            w = pcbnew.ToMM(bb.GetWidth()) + GAP
            h = pcbnew.ToMM(bb.GetHeight()) + GAP
            if x + w > xb and x > xa:
                x = xa; y += shelf + GAP; shelf = 0.0
            fp.SetPosition(pcbnew.VECTOR2I(mm(x + w / 2), mm(y + h / 2)))
            x += w
            shelf = max(shelf, h)
            placed_refs.append(ref)
        return y + shelf

    # TOP: inset clear of the left (X10) and right (J_GPIO) edge connectors, below the top band
    top_bottom = shelf_pack(top_fps, OX + 15.0, OX + BW - 15.0, OY + 13.0, flip=False)
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
