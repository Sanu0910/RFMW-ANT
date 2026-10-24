"""Original antenna PCB for NOVA-RF1: a 125 kHz RFID spiral coil and a 13.56 MHz NFC loop,
drawn as real copper traces with computed inductance + resonant-cap values (run in KiCad Python).

Design is original (own size/silk; no Flipper outline art, name or markings). Inductance uses the
modified-Wheeler planar-spiral formula; re-measure/tune on the real stack-up before release.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
OUT = os.path.join(KDIR, "nova-rf1-antenna.kicad_pcb")
MU0 = 4e-7 * math.pi

OX, OY = 40.0, 40.0
BW, BH = 70.0, 34.0          # antenna board outline (mm)


def mm(v):
    return pcbnew.FromMM(v)


def wheeler_L(n, dout, din):
    """Modified-Wheeler inductance (H) for a square planar spiral. dout/din in metres."""
    davg = (dout + din) / 2.0
    rho = (dout - din) / (dout + din)
    k1, k2 = 2.34, 2.75
    return k1 * MU0 * n * n * davg / (1.0 + k2 * rho)


def res_cap(L, f):
    """Parallel resonant cap (F) for inductance L at frequency f."""
    return 1.0 / ((2 * math.pi * f) ** 2 * L)


def spiral_pts(cx, cy, w, h, turns, pitch):
    """Rectangular inward spiral centre path; returns point list (mm)."""
    pts = []
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    for t in range(turns):
        d = t * pitch
        a, b, c, e = x0 + d, y0 + d, x1 - d, y1 - d
        if c - a < 2 * pitch or e - b < 2 * pitch:
            break
        pts += [(a, b), (c, b), (c, e), (a, e), (a, b + pitch)]
    return pts


def draw_track(board, pts, net, width, layer):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(ax), mm(ay)))
        t.SetEnd(pcbnew.VECTOR2I(mm(bx), mm(by)))
        t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(net); board.Add(t)


def outline(board):
    pts = [(OX, OY), (OX + BW, OY), (OX + BW, OY + BH), (OX, OY + BH), (OX, OY)]
    for a, b in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.15)); board.Add(s)


def silk(board, s, x, y, size=1.2):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2)); board.Add(t)


def build():
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
        return nets[n]

    # ---- 125 kHz RFID spiral (big, many turns) ----
    lf_w, lf_h, lf_pitch = 38.0, 26.0, 0.45     # 0.25mm trace + 0.20mm gap
    lf_turns = 46
    lf_pts = spiral_pts(OX + 21, OY + BH / 2, lf_w, lf_h, lf_turns, lf_pitch)
    nturn_lf = len([1 for i in range(0, len(lf_pts), 5)])
    draw_track(board, lf_pts, net("LF_COIL_P"), 0.25, pcbnew.F_Cu)
    L_lf = wheeler_L(nturn_lf, lf_w / 1000, (lf_w - 2 * nturn_lf * lf_pitch) / 1000)
    C_lf = res_cap(L_lf, 125e3)

    # ---- 13.56 MHz NFC loop (few turns, rectangular) ----
    nfc_w, nfc_h, nfc_pitch = 20.0, 24.0, 0.8
    nfc_turns = 5
    nfc_pts = spiral_pts(OX + BW - 13, OY + BH / 2, nfc_w, nfc_h, nfc_turns, nfc_pitch)
    nturn_nfc = len([1 for i in range(0, len(nfc_pts), 5)])
    draw_track(board, nfc_pts, net("NFC_ANT_P"), 0.4, pcbnew.F_Cu)
    L_nfc = wheeler_L(nturn_nfc, nfc_w / 1000, (nfc_w - 2 * nturn_nfc * nfc_pitch) / 1000)
    C_nfc = res_cap(L_nfc, 13.56e6)

    outline(board)
    silk(board, "NOVA-RF1 ANTENNA v0.1", OX + 2, OY + 1.5, 1.4)
    silk(board, f"125kHz coil ~{L_lf*1e6:.0f}uH  Cres~{C_lf*1e9:.1f}nF", OX + 2, OY + BH - 4.5, 1.0)
    silk(board, f"13.56MHz loop ~{L_nfc*1e6:.2f}uH  Cres~{C_nfc*1e12:.0f}pF", OX + 2, OY + BH - 2.3, 1.0)

    board.BuildListOfNets()
    pcbnew.SaveBoard(OUT, board)
    print(f"125kHz coil: {nturn_lf} turns, L~{L_lf*1e6:.0f} uH -> Cres~{C_lf*1e9:.2f} nF at 125 kHz")
    print(f"13.56MHz loop: {nturn_nfc} turns, L~{L_nfc*1e6:.2f} uH -> Cres~{C_nfc*1e12:.0f} pF at 13.56 MHz")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
