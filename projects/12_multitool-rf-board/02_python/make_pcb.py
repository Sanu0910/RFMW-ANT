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
BW, BH = 150.0, 150.0         # envelope (mm) sized to hold all 87 parts + routing room
INSET = 11.0                  # interior margin: edge band for the locked connectors


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
        "X6":     (26.0, 7.0, 0),             # 18-pin FFC on top edge (sub-board link)
        "J_GPIO": (BW - 6.0, BH / 2, 0),      # 2x9 GPIO header on right edge (native tall axis)
        "J_SWD":  (BW - 18.0, BH - 7.0, 0),   # Tag-Connect SWD near bottom-right
        "X10":    (7.0, BH / 2, 90),          # battery connector on left edge
        "J_SUBG": (12.0, 7.0, 0),             # sub-GHz U.FL top-left
        "ANT1":   (BW / 2 - 12, 6.0, 0),      # BLE chip antenna top
        "ANT_NFC":(BW / 2 + 4, 6.0, 0),       # NFC loop top
        "ANT_LF": (BW / 2 + 16, 6.0, 0),      # 125k coil top
        "SW_U": (BW - 34, 7.0, 0), "SW_D": (BW - 27, 7.0, 0), "SW_L": (BW - 20, 7.0, 0),
        "SW_R": (BW - 13, 7.0, 0), "SW_O": (BW - 41, 7.0, 0), "SW_B": (BW - 48, 7.0, 0),
    }

    parts = {p[0]: p for p in D.PARTS}
    # group parts by functional group for placement
    groups = {}
    placed_refs = []
    for ref, p in parts.items():
        if ref in pinmap.PENDING:
            continue
        groups.setdefault(p[5], []).append((ref, p))

    # Deterministic, legal-by-construction placement: unlocked parts flow in
    # grouped rows inside the interior rectangle (inset from the edge band that
    # holds the locked connectors), each part's slot = its bounding box + GAP so
    # courtyards never overlap. Legal by construction -> no stochastic anneal.
    GAP = 2.8
    x0 = OX + INSET
    x1 = OX + BW - INSET
    x, y, shelf = x0, OY + INSET, 0.0
    unconn = 0
    for gname, members in groups.items():
        # new band per functional group
        if x > x0:
            x = x0; y += shelf + GAP; shelf = 0.0
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
            if ref in FIXED:
                fx, fy, frot = FIXED[ref]
                fp.SetPosition(pcbnew.VECTOR2I(mm(OX + fx), mm(OY + fy)))
                if frot:
                    fp.SetOrientationDegrees(frot)
                fp.SetLocked(True)
                placed_refs.append(ref)
                continue
            bb = fp.GetBoundingBox()
            w = pcbnew.ToMM(bb.GetWidth()) + GAP
            h = pcbnew.ToMM(bb.GetHeight()) + GAP
            if x + w > x1 and x > x0:
                x = x0
                y += shelf + GAP
                shelf = 0.0
            fp.SetPosition(pcbnew.VECTOR2I(mm(x + w / 2), mm(y + h / 2)))
            x += w
            shelf = max(shelf, h)
            placed_refs.append(ref)
        x = x0
        y += shelf + GAP
        shelf = 0.0
    interior_bottom = y
    print(f"  interior packed to y={interior_bottom - OY:.1f}mm (board BH={BH})")

    add_outline(board)
    board.BuildListOfNets()
    pcbnew.SaveBoard(PCB, board)
    print(f"placed {len(placed_refs)} parts, {board.GetNetCount()} nets, "
          f"{unconn} unconnected pads; skipped {len(pinmap.PENDING)} pending")


if __name__ == "__main__":
    build()
