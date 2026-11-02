"""Build the project footprint library KiCad/CRPA17.pretty.

Sources
  * HC125A, TQP3M9037 (DFN-8 2x2), B7504, B8889, DXP.02.A, antenna module:
    land patterns copied from the customer board Input/Gerber_4CH_GNSS.zip
    (KiCad 10 Gerber X2 with pad attributes). The parts sit on the bottom of
    that board, so the observed pads are mirrored back to a top view here.
  * RLM-63-2W+ (Mini-Circuits case TT1224): from the datasheet land pattern
    (Input/RLM-63-2W+.pdf, PL-258): pads K x H = 1.52 x 1.65 mm, pitch D = 2.54,
    outer span J = 7.62. Top view: 1-2-3 on one edge, 6-5-4 opposite,
    IN = 1, OUT = 4, GND = 2,3,5,6.

Run with any Python 3 (no KiCad needed). Units mm, KiCad frame (y down).
"""
import io
import math
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
ZIP = PROJ / "Input" / "Gerber_4CH_GNSS.zip"
LIB = PROJ / "KiCad" / "CRPA17.pretty"

# --------------------------------------------------------------------------- gerber pads

def read_gerber(name):
    with zipfile.ZipFile(ZIP) as z:
        return z.read("Gerber_4CH_GNSS/" + name).decode()


def flashes(txt):
    """Return [(ref, pin, net, x, y, aperture)] for every attributed pad flash."""
    aps = {m.group(1): (m.group(2), m.group(3)) for m in
           re.finditer(r"%ADD(\d+)([A-Za-z_0-9]+),?([^*]*)\*%", txt)}
    cur, attrs, x, y, out = None, {}, 0.0, 0.0, []
    for line in txt.splitlines():
        m = re.match(r"%TO\.(\w+),(.*)\*%", line)
        if m:
            attrs[m.group(1)] = m.group(2)
            continue
        if line.startswith("%TD"):
            k = line[3:].strip("*%")
            attrs.pop(k, None) if k else attrs.clear()
            continue
        m = re.match(r"^D(\d+)\*$", line)
        if m and int(m.group(1)) >= 10:
            cur = m.group(1)
            continue
        m = re.match(r"^(?:X(-?\d+))?(?:Y(-?\d+))?D03\*", line)
        if m:
            if m.group(1):
                x = int(m.group(1)) / 1e6
            if m.group(2):
                y = int(m.group(2)) / 1e6
            if "P" in attrs:
                ref, _, pin = attrs["P"].partition(",")
                if cur in aps:
                    out.append((ref, pin.split(",")[0], attrs.get("N"), x, y, aps[cur]))
    return out


def pad_corners(x, y, ap):
    """Gerber (y up) pad -> 4 corners, or None for a circle."""
    kind, p = ap
    v = [float(s) for s in p.split("X")] if p else []
    if kind == "R":
        w, h, a = v[0], v[1], 0.0
    elif kind == "RotRect":
        w, h, a = v[0], v[1], v[2]
    elif kind == "C":
        return None
    else:
        raise ValueError(kind)
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(x + dx * c - dy * s, y + dx * s + dy * c)
            for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def to_local(pads, pin_a, pin_b, mirror, origin_pin=None, extra_rot=0.0):
    """Gerber pads of one footprint -> local KiCad top-view rect pads.

    1. y -> -y (KiCad frame); 2. mirror x if the part was on the bottom;
    3. origin at the pad-centre bounding-box centre; 4. rotate so pin_a -> pin_b is +x.
    """
    def kc(px, py):
        return (-px if mirror else px, -py)
    cen = {}
    for ref, pin, net, x, y, ap in pads:
        cen.setdefault(pin, kc(x, y))
    xs = [kc(p[3], p[4])[0] for p in pads]
    ys = [kc(p[3], p[4])[1] for p in pads]
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    if origin_pin:
        ox, oy = cen[origin_pin]
    ax, ay = cen[pin_a]
    bx, by = cen[pin_b]
    th = -math.atan2(by - ay, bx - ax) + math.radians(extra_rot)
    c, s = math.cos(th), math.sin(th)

    def tf(px, py):
        qx, qy = kc(px, py)
        qx, qy = qx - ox, qy - oy
        return (qx * c - qy * s, qx * s + qy * c)

    res = []
    for ref, pin, net, x, y, ap in pads:
        cr = pad_corners(x, y, ap)
        cx, cy = tf(x, y)
        if cr is None:
            res.append(dict(pin=pin, x=cx, y=cy, shape="circle", w=float(ap[1]), h=float(ap[1]), a=0))
            continue
        q = [tf(*p) for p in cr]
        w = math.dist(q[0], q[1])
        h = math.dist(q[1], q[2])
        a = math.degrees(math.atan2(q[1][1] - q[0][1], q[1][0] - q[0][0])) % 180
        if abs(a - 90) < 1:
            w, h, a = h, w, 0.0
        elif a < 1 or a > 179:
            a = 0.0
        res.append(dict(pin=pin, x=cx, y=cy, shape="rect", w=w, h=h, a=round(-a, 3)))
    return res


# --------------------------------------------------------------------------- kicad_mod writer

def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"


def write_mod(name, descr, pads, body, smd=True, attr="smd", extra="", crt_margin=0.25, ref_side="F"):
    """pads: dicts with pin, x, y, shape, w, h, a, [drill], [layers], [type]."""
    xs = [p["x"] - p["w"] / 2 for p in pads] + [p["x"] + p["w"] / 2 for p in pads] + [-body[0] / 2, body[0] / 2]
    ys = [p["y"] - p["h"] / 2 for p in pads] + [p["y"] + p["h"] / 2 for p in pads] + [-body[1] / 2, body[1] / 2]
    cx0, cx1 = min(xs) - crt_margin, max(xs) + crt_margin
    cy0, cy1 = min(ys) - crt_margin, max(ys) + crt_margin
    bw, bh = body[0] / 2, body[1] / 2
    L = [f'(footprint "{name}"', '  (version 20241229)', '  (generator "crpa17_build_footprints")',
         '  (layer "F.Cu")', f'  (descr "{descr}")', f'  (attr {attr})',
         f'  (property "Reference" "REF**" (at 0 {fmt(cy0 - 0.8)} 0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))',
         f'  (property "Value" "{name}" (at 0 {fmt(cy1 + 0.8)} 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))']
    # fab body, courtyard
    L.append(f'  (fp_rect (start {fmt(-bw)} {fmt(-bh)}) (end {fmt(bw)} {fmt(bh)}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))')
    L.append(f'  (fp_rect (start {fmt(cx0)} {fmt(cy0)}) (end {fmt(cx1)} {fmt(cy1)}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
    # pin-1 dot on silk, outside the courtyard corner nearest pad 1
    p1 = next((p for p in pads if p["pin"] == "1"), None)
    if p1 is not None:
        sx = cx0 - 0.3 if p1["x"] <= 0 else cx1 + 0.3
        sy = cy0 - 0.3 if p1["y"] <= 0 else cy1 + 0.3
        L.append(f'  (fp_circle (center {fmt(sx)} {fmt(sy)}) (end {fmt(sx + 0.15)} {fmt(sy)}) (stroke (width 0.3) (type solid)) (fill yes) (layer "F.SilkS"))')
    L.append(extra)
    for p in pads:
        ptype = p.get("type", "smd")
        layers = p.get("layers", '"F.Cu" "F.Paste" "F.Mask"')
        shape = p["shape"]
        size = f'(size {fmt(p["w"])} {fmt(p["h"])})'
        rot = f' {fmt(p["a"])}' if p.get("a") else ""
        drill = f' (drill {fmt(p["drill"])})' if "drill" in p else ""
        num = p["pin"]
        L.append(f'  (pad "{num}" {ptype} {shape} (at {fmt(p["x"])} {fmt(p["y"])}{rot}) {size}{drill} (layers {layers}))')
    L.append(")")
    (LIB / f"{name}.kicad_mod").write_text("\n".join(L) + "\n")
    return (cx0, cy0, cx1, cy1)


def merge_gnd(pads):
    """Unnamed / 'GND' pads of the customer footprints become pin 'GND' (exposed paddle)."""
    for p in pads:
        if p["pin"] in ("", "GND"):
            p["pin"] = "GND"
    return pads


# --------------------------------------------------------------------------- build

def main():
    LIB.mkdir(parents=True, exist_ok=True)
    bcu = flashes(read_gerber("Combine_Model-B_Cu.gbr"))
    fcu = flashes(read_gerber("Combine_Model-F_Cu.gbr"))

    # Element 1 (top-left, the instance named Antenna_footprint): x < 120.8, y > -122.1 (gerber)
    def inst(ref, src):
        return [p for p in src if p[0] == ref and p[3] < 120.8 and p[4] > -122.1]

    report = []

    # HC125A hybrid: customer refs "Coupler" (L1) and "CP1" (L2) share one land pattern.
    hc = merge_gnd(to_local(inst("Coupler", bcu), "1", "2", mirror=True))
    bb = write_mod("HC125A", "Taoglas HC125A 90deg hybrid 1150-1630 MHz, 6.35x5.08 mm. Land pattern from CRL Combine_Model board",
                   hc, (6.35, 5.08))
    report.append(("HC125A", hc, bb))

    tq = to_local(inst("U3", bcu), "1", "4", mirror=True)
    for p in tq:
        if p["pin"] == "9":
            p["pin"] = "9"
    bb = write_mod("TQP3M9037_DFN8_2x2", "Qorvo TQP3M9037 LNA, DFN-8 2x2 mm + EP (pad 9 = GND). Land pattern from CRL board",
                   tq, (2.0, 2.0))
    report.append(("TQP3M9037", tq, bb))

    b75 = to_local(inst("FL1", bcu), "1", "2", mirror=True)
    bb = write_mod("B7504_SAW_0.9x0.7", "Qualcomm RF360 B7504 GNSS L1 SAW, 0.9x0.7 mm 4 pads (1 in, 3 out, 2/4 GND). From CRL board",
                   b75, (0.9, 0.7), crt_margin=0.2)
    report.append(("B7504", b75, bb))

    b88 = to_local(inst("FL2", bcu), "1", "4", mirror=True, extra_rot=-17.987)
    bb = write_mod("B8889_SAW_1.1x0.9", "Qualcomm RF360 B8889 GNSS L2/L5 SAW, 1.1x0.9 mm 5 pads (1 in, 4 out, 2/3/5 GND). From CRL board",
                   b88, (1.1, 0.9), crt_margin=0.2)
    report.append(("B8889", b88, bb))

    dx = to_local(inst("DXP.02.A", bcu), "1", "3", mirror=True)
    bb = write_mod("DXP.02.A", "Taoglas DXP.02.A GNSS diplexer (2 common, 7 L1, 5 L2/L5, 1/3/4/6/8 GND). From CRL board",
                   dx, (3.2, 3.2))
    report.append(("DXP.02.A", dx, bb))

    # RLM-63-2W+ limiter, TT1224, from the datasheet land pattern (top view)
    rl = []
    for pin, (x, y) in {"1": (-2.54, -2.985), "2": (0, -2.985), "3": (2.54, -2.985),
                        "4": (2.54, 2.985), "5": (0, 2.985), "6": (-2.54, 2.985)}.items():
        rl.append(dict(pin=pin, x=x, y=y, shape="rect", w=1.52, h=1.65, a=0))
    bb = write_mod("MiniCircuits_TT1224", "Mini-Circuits case TT1224 (RLM-63-2W+ limiter), PL-258 land pattern: 1 IN, 4 OUT, 2/3/5/6 GND",
                   rl, (7.87, 6.35))
    report.append(("TT1224", rl, bb))

    # Antenna module (top side, through-hole pins). Customer F.Cu, element 1, not mirrored.
    an = to_local(inst("Antenna_footprint", fcu), "L1(0)", "L2(90)", mirror=False, origin_pin="1")
    ant = []
    names = {"1": "C", "L1(0)": "L1_0", "L1(90)": "L1_90", "L2(0)": "L2_0", "L2(90)": "L2_90"}
    for p in an:
        q = dict(pin=names[p["pin"]], x=round(p["x"], 3), y=round(p["y"], 3), shape="circle",
                 w=p["w"], h=p["w"], a=0, type="thru_hole", layers='"*.Cu" "*.Mask"')
        q["drill"] = 3.2 if q["pin"] == "C" else 1.1          # GPDF6010.A DS 4.3: D3.20 screw, D0.90 pins
        ant.append(q)
    holes = ""
    for hx, hy in ((-29, 0), (29, 0), (0, -29), (0, 29)):
        holes += (f'  (pad "" np_thru_hole circle (at {hx} {hy}) (size 1.8 1.8) (drill 1.8) (layers "*.Cu" "*.Mask"))\n')
    write_mod("GNSS_StackedPatch_L1L2_4feed", "Stacked L1/L2 patch module, 4 probe feeds (L1 0/90 at 5.5 mm, L2 0/90 at 12.25 mm), "
              "centre screw (GND), 4x D1.8 locating holes at 29 mm. Taoglas GPDF6010.A, DS SPE-21-8-111-G sec. 4.3",
              ant, (64, 64), attr="through_hole", extra=holes.rstrip("\n"))
    report.append(("Antenna", ant, None))

    for name, pads, bb in report:
        print(f"== {name}")
        for p in sorted(pads, key=lambda q: q["pin"]):
            print(f"   pin {p['pin']:>6}  ({p['x']:7.3f},{p['y']:7.3f})  {p['shape']} {p['w']:.3f}x{p['h']:.3f} a={p['a']}")


if __name__ == "__main__":
    main()
