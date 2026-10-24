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
BW, BH = 110.0, 46.0          # single-board envelope (mm) holding all 87 parts; refined later


def mm(v):
    return pcbnew.FromMM(v)


def add_outline(board):
    """Rounded-rectangle board edge on Edge.Cuts."""
    r = 3.0
    x0, y0, x1, y1 = OX, OY, OX + BW, OY + BH
    segs = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
            ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    for a, b in segs:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
    corners = [((x0 + r, y0 + r), (x0 + r, y0), 90), ((x1 - r, y0 + r), (x1, y0 + r), 90),
               ((x1 - r, y1 - r), (x1 - r, y1), 90), ((x0 + r, y1 - r), (x0, y1 - r), 90)]
    for c, start, ang in corners:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetCenter(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
        s.SetStart(pcbnew.VECTOR2I(mm(start[0]), mm(start[1])))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
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
        "J_USB":  (BW / 2, BH - 2.0, 0),      # USB-C centered on bottom edge
        "X6":     (20.0, 2.0, 0),             # 18-pin FFC on top edge (sub-board link)
        "J_GPIO": (BW - 2.5, BH / 2, 90),     # 2x9 GPIO header on right edge
        "J_SWD":  (BW - 10.0, BH - 2.5, 0),   # Tag-Connect SWD near bottom-right
        "X10":    (2.0, BH / 2, 90),          # battery connector on left edge
        "J_SUBG": (10.0, 2.0, 0),             # sub-GHz U.FL top-left
        "ANT1":   (BW / 2 - 10, 2.0, 0),      # BLE chip antenna top
        "ANT_NFC":(BW / 2 + 6, 2.0, 0),       # NFC loop top
        "ANT_LF": (BW / 2 + 16, 2.0, 0),      # 125k coil top
        "SW_U": (BW - 30, 2.0, 0), "SW_D": (BW - 24, 2.0, 0), "SW_L": (BW - 18, 2.0, 0),
        "SW_R": (BW - 12, 2.0, 0), "SW_O": (BW - 36, 2.0, 0), "SW_B": (BW - 42, 2.0, 0),
    }

    parts = {p[0]: p for p in D.PARTS}
    # group parts by functional group for placement
    groups = {}
    placed_refs = []
    for ref, p in parts.items():
        if ref in pinmap.PENDING:
            continue
        groups.setdefault(p[5], []).append((ref, p))

    # pile the unlocked (placer-movable) parts BELOW the board outline
    x, y, shelf = OX, OY + BH + 8.0, 0.0
    PAGE_W = 260.0
    unconn = 0
    for gname, members in groups.items():
        for ref, p in members:
            libid = pinmap.FOOTPRINT.get(p[4])
            if libid is None:
                continue
            fp = load_fp(board, libid)
            fp.SetReference(ref)
            fp.SetValue(p[1])
            board.Add(fp)
            # assign pad nets
            padmap = pinmap.pad_nets(ref) or {}
            for pad in fp.Pads():
                num = pad.GetNumber()
                if num in padmap:
                    pad.SetNet(net(padmap[num]))
                else:
                    unconn += 1
                    pad.SetNet(net(f"unconnected-({ref}-{num})"))
            # place
            bb = fp.GetBoundingBox()
            w = pcbnew.ToMM(bb.GetWidth()) + 2.5
            h = pcbnew.ToMM(bb.GetHeight()) + 2.5
            if ref in FIXED:
                fx, fy, frot = FIXED[ref]
                fp.SetPosition(pcbnew.VECTOR2I(mm(OX + fx), mm(OY + fy)))
                if frot:
                    fp.SetOrientationDegrees(frot)
                fp.SetLocked(True)
                placed_refs.append(ref)
                continue
            if x + w > OX + PAGE_W and x > OX:
                x = OX
                y += shelf + 3.0
                shelf = 0.0
            fp.SetPosition(pcbnew.VECTOR2I(mm(x + w / 2), mm(y + h / 2)))
            x += w + 2.0
            shelf = max(shelf, h)
            placed_refs.append(ref)
        x = OX
        y += shelf + 5.0
        shelf = 0.0

    add_outline(board)
    board.BuildListOfNets()
    pcbnew.SaveBoard(PCB, board)
    print(f"placed {len(placed_refs)} parts, {board.GetNetCount()} nets, "
          f"{unconn} unconnected pads; skipped {len(pinmap.PENDING)} pending")


if __name__ == "__main__":
    build()
