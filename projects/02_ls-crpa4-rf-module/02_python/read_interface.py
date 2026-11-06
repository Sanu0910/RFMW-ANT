"""Decode the customer board combine_model_2.0 (PCB_FAB_LS_4E) into the RF-module interface.

Writes (05_docs/):
  CRL-LS_module_footprint.csv   26 pads of the module footprint in MODULE coordinates (bottom view of the main
                                board = top view of the module footprint), with the signal on each pad
  CRL-LS_module_placement.csv   centre and rotation of the 4 modules on the main board (board-centre frame)
  CRL-LS_main_board_holes.csv   every drill > 0.5 mm, board-centre frame, with its probable function
  img/input_*.png               layer renders
Frame: origin = centre of the D200 board outline, x right, y up, mm (Gerber coordinates minus the centre).
"""
import csv, math, os, collections
from gerbonara import GerberFile
from gerbonara.graphic_objects import Flash, Line, Arc

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
SRC = os.path.join(PRJ, "00_input", "PCB_FAB_LS_4E", "combine_model_2.0-")
OUT = os.path.join(PRJ, "05_docs")
PAD_W, PAD_L = 1.35, 2.54          # module pad, from the B_Cu aperture
TOL = 0.05


def board_centre():
    arcs = [o for o in GerberFile.open(SRC + "Edge_Cuts.gbr").objects if isinstance(o, Arc)]
    xs = [o.x1 for o in arcs] + [o.x2 for o in arcs]
    ys = [o.y1 for o in arcs] + [o.y2 for o in arcs]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2


def main():
    cx, cy, R = board_centre()
    cu = GerberFile.open(SRC + "B_Cu.gbr").objects
    pads = [(o.x - cx, o.y - cy, "H" if "2.54x1.35" in str(o.aperture) else "V")
            for o in cu if isinstance(o, Flash) and ("1.35x2.54" in str(o.aperture) or "2.54x1.35" in str(o.aperture))]
    tracks = [(o.x1 - cx, o.y1 - cy, o.x2 - cx, o.y2 - cy, round(o.aperture.equivalent_width("mm"), 3))
              for o in cu if isinstance(o, (Line, Arc))]

    # group the 104 pads into 4 modules by quadrant
    mods = collections.defaultdict(list)
    for x, y, k in pads:
        mods[(x > 0, y > 0)].append((x, y, k))
    width_name = {1.1: "RF 50 ohm (1.1 mm)", 1.21: "DC (1.21 mm, via to In2 ring)", 0.3: "0.3 mm tie", 0.53: "0.53 mm"}
    # signal names for the reference module (top-left, x<0,y>0), confirmed from B_Silkscreen labels + routing
    SIG = {("T", 2): "IN_L1", ("T", 3): "TIE_A", ("T", 4): "IN_L2L5", ("T", 7): "VDC_5V", ("T", 10): "IN_S",
           ("B", 10): "OUT_L", ("B", 11): "TIE_B", ("B", 12): "OUT_S"}
    place, fp_rows = [], []
    for key, pl in sorted(mods.items()):
        xs = [p[0] for p in pl]; ys = [p[1] for p in pl]
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        # rotation that maps this module onto the reference (top-left) one: rows horizontal, inputs on the side
        # facing the array centre's diagonal; the reference has rows along x with the input row at larger |y|.
        ang = math.degrees(math.atan2(my, mx))           # TL module at 135 deg
        rot = (round((ang - 135) / 90) * 90) % 360
        place.append(dict(module=len(place) + 1, quadrant=("E" if key[0] else "W") + ("N" if key[1] else "S"),
                          cx=round(mx, 3), cy=round(my, 3), rot_deg=rot, r_centre=round(math.hypot(mx, my), 2)))
        if key != (False, True):
            continue
        # module frame for the reference module: origin = footprint centre, x along rows, y toward input row
        for x, y, k in sorted(pl, key=lambda p: (-p[1], p[0])):
            u, v = x - mx, y - my
            row = "T" if v > 0 else "B"
            idx = 1 + round((u - (min(xs) - mx)) / 1.829)
            hit = collections.Counter()
            for t in tracks:
                for ex, ey in ((t[0], t[1]), (t[2], t[3])):
                    if abs(ex - x) <= PAD_W / 2 + TOL and abs(ey - y) <= PAD_L / 2 + TOL:
                        hit[t[4]] += 1
            fp_rows.append(dict(row=row, pin=("%s%02d" % (row, idx)), x_mod=round(u, 3), y_mod=round(v, 3),
                                pad_w=PAD_W, pad_l=PAD_L, signal=SIG.get((row, idx), "GND [ASSUMED: pour, no trace]"),
                                main_board_trace="; ".join(width_name.get(w, str(w)) for w in hit) or "none"))
    with open(os.path.join(OUT, "CRL-LS_module_footprint.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fp_rows[0])); w.writeheader(); w.writerows(fp_rows)
    with open(os.path.join(OUT, "CRL-LS_module_placement.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(place[0])); w.writeheader(); w.writerows(place)

    # holes
    FUN = {0.5: "via", 0.77: "S-band patch feed pin (4 per S element, 4.0 mm from its centre)",
           1.0: "DC input header J (VDC/GND)", 1.1: "S element / misc. [OPEN]",
           1.35: "L-band patch feed pin (GPDF6010: L1 at 5.5 mm, L2 at 12.25 mm from centre)",
           1.36: "L-band patch feed pin (L1 90 deg)", 2.2: "S element fixing / misc. M2 [ASSUMED]",
           3.2: "L patch centre grounding screw (GPDF6010)", 3.6: "L patch fixing screw M3 (4 per element, +-29 mm)"}
    rows = []
    for o in GerberFile.open(SRC + "PTH-drl.gbr").objects:
        pr = next(iter(o.to_primitives())); d = round(2 * pr.r, 2)
        if d > 0.5:
            x, y = pr.x - cx, pr.y - cy
            rows.append(dict(d_mm=d, x=round(x, 3), y=round(y, 3), r=round(math.hypot(x, y), 2), function=FUN.get(d, "")))
    rows.sort(key=lambda r: (r["d_mm"], r["x"], r["y"]))
    with open(os.path.join(OUT, "CRL-LS_main_board_holes.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("board centre (%.3f, %.3f), R = %.3f mm" % (cx, cy, R))
    for p in place:
        print(p)
    for r in fp_rows:
        if r["main_board_trace"] != "none":
            print(r["pin"], r["x_mod"], r["y_mod"], r["signal"], "|", r["main_board_trace"])
    print(len(rows), "holes > 0.5 mm;", collections.Counter(r["d_mm"] for r in rows))


if __name__ == "__main__":
    main()
