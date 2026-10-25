"""Envelope 3D models (STEP) for the custom footprints that have no KiCad 3D model, built with SolidCraft.

Boxes/cylinders are the vendor body sizes (mm) in footprint coordinates (origin = footprint origin, z = 0 on
the board surface). For enclosure / collision checks and a readable 3D render, not photorealism.
The LD2410B stands VERTICAL on its header, so its body rises in +z.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "01_kicad", "3d")
COL = {"pcb": [0.10, 0.35, 0.18], "blue": [0.12, 0.22, 0.55], "black": [0.12, 0.12, 0.12],
       "metal": [0.72, 0.72, 0.74], "ivory": [0.88, 0.84, 0.72], "blk2": [0.08, 0.08, 0.08]}

# name: list of (x0, y0, x1, y1, z0, height, colour)  -- axis-aligned boxes
MODELS = {
    # LD2410B 7 x 35 mm board standing on the header, antenna side up; a small base + the tall board
    "LD2410B_Module": [(-3.5, -0.8, 3.5, 0.8, 0.0, 2.0, "black"),         # header/base block
                       (-3.5, -0.7, 3.5, 0.7, 2.0, 35.0, "blue")],       # the module PCB standing up
    # 14 mm MOV disc ~ 18 x 5 x 18 mm body on radial leads
    "Varistor_Disc_D16mm_P7.5mm": [(-8.5, -2.5, 8.5, 2.5, 1.0, 17.0, "blue")],
    # 9 mm NTC disc
    "NTC_Disc_D11mm_P5mm": [(-5.5, -2.0, 5.5, 2.0, 1.0, 11.0, "black")],
    # TR5 fuse body ~7.5 x 7.5 x 10 mm
    "Fuse_TR5_P5.08mm": [(-3.8, -3.8, 3.8, 3.8, 0.0, 10.0, "ivory")],
}


def script(boxes):
    c = []
    for k, (x0, y0, x1, y1, z0, h, col) in enumerate(boxes):
        c.append({"command": "sketch.create", "params": {"plane": "XY", "offset": z0}})
        c.append({"command": "sketch.rectangle.rounded", "params": {"p0": [x0, -y1], "p1": [x1, -y0], "radius": 0.15}})
        c.append({"command": "sketch.finish", "params": {}})
        c.append({"command": "solid.extrude", "params": {"distance": h, "operation": "new", "body_name": f"b{k}"}})
        c.append({"command": "appearance.assign", "params": {"bodies": [f"b{k}"], "color": COL[col]}})
    return {"commands": c}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, boxes in MODELS.items():
        js = os.path.join(OUT, name + ".json")
        json.dump(script(boxes), open(js, "w"))
        r = subprocess.run(["solidcraft-cli", "run", js, "--out", os.path.join(OUT, name + ".step"), "--quiet"],
                           capture_output=True, text=True)
        os.remove(js)
        print(name, "ok" if r.returncode == 0 else r.stderr[-300:])


if __name__ == "__main__":
    main()
