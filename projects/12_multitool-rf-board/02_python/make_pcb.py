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
BW, BH = 100.0, 40.0          # rough main-board envelope (mm); refined later


def mm(v):
    return pcbnew.FromMM(v)


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

    parts = {p[0]: p for p in D.PARTS}
    # group parts by functional group for placement
    groups = {}
    placed_refs = []
    for ref, p in parts.items():
        if ref in pinmap.PENDING:
            continue
        groups.setdefault(p[5], []).append((ref, p))

    # shelf-pack footprints row by row, grouped
    x, y, shelf = OX, OY, 0.0
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

    board.BuildListOfNets()
    pcbnew.SaveBoard(PCB, board)
    print(f"placed {len(placed_refs)} parts, {board.GetNetCount()} nets, "
          f"{unconn} unconnected pads; skipped {len(pinmap.PENDING)} pending")


if __name__ == "__main__":
    build()
