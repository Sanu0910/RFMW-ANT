"""Add professional silkscreen + title block to the routed board (run in KiCad 9 Python).

  python3 make_fab.py <in.kicad_pcb> <out.kicad_pcb>

Adds board name / revision / date, an original-design notice, and a fab mark on the
silkscreen. Keeps it original: our own name and markings, no trademark or mascot.
"""
import os
import sys

import pcbnew

NAME = "CRL-MT1"
REV = "v0.1"
DATE = "2026-10-24"
NOTE = "Original firmware-compatible multi-tool - not a Flipper Zero"


def mm(v):
    return pcbnew.FromMM(v)


def text(board, s, x, y, layer, size=1.2, thick=0.2, mirror=False, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick))
    t.SetMirrored(mirror)
    if bold:
        t.SetBold(True)
    board.Add(t)


def build(inp, outp):
    board = pcbnew.LoadBoard(inp)
    box = board.GetBoardEdgesBoundingBox()
    x0 = pcbnew.ToMM(box.GetX())
    y0 = pcbnew.ToMM(box.GetY())
    w = pcbnew.ToMM(box.GetWidth())
    h = pcbnew.ToMM(box.GetHeight())
    # top silkscreen title block (lower-left corner, inside the edge)
    text(board, f"{NAME}  {REV}", x0 + 3, y0 + h - 5.5, pcbnew.F_SilkS, size=1.6, thick=0.25, bold=True)
    text(board, DATE, x0 + 3, y0 + h - 3.0, pcbnew.F_SilkS, size=1.0, thick=0.15)
    # bottom silkscreen: the original-design notice (mirrored)
    text(board, NOTE, x0 + w - 3, y0 + h - 3.0, pcbnew.B_SilkS, size=1.0, thick=0.15, mirror=True)
    text(board, f"{NAME} {REV}", x0 + w - 3, y0 + h - 5.0, pcbnew.B_SilkS, size=1.2, thick=0.2, mirror=True)
    pcbnew.SaveBoard(outp, board)
    print(f"fab silkscreen added -> {outp}  (board {w:.2f} x {h:.2f} mm)")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
