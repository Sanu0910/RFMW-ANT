"""Fan-out via helper for isolated GND / +3V3 pads (used by patch_route)."""
import math
import pcbnew
import make_pcb as M


def via_near(board, pad, items, kos):
    layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    c = pad.GetPosition()
    bb = pad.GetBoundingBox()
    hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
    w = min(0.2, 2 * min(hw, hh))
    for extra in (0.0, 0.2, 0.4, 0.7, 1.0, 1.4, 1.8):
        for ang in range(0, 360, 15):
            a = math.radians(ang)
            ca, sa = math.cos(a), math.sin(a)
            edge = 1.0 / max(1e-6, max(abs(ca) / max(hw, 1e-3), abs(sa) / max(hh, 1e-3)))
            d = edge + M.VIA_D / 2 + 0.12 + extra
            pos = pcbnew.VECTOR2I(int(c.x + M.mm(d * ca)), int(c.y + M.mm(d * sa)))
            if M.via_ok(board, pos, kos, items, pad.GetNetCode()) and \
                    M.seg_ok(board, c, pos, w, layer, items, pad.GetNetCode(), pad):
                v = M.add_via(board, pos, pad.GetNet())
                t = M.add_track(board, c, pos, w, layer, pad.GetNet(), locked=False)
                items += [v, t]
                return pos
    return None
