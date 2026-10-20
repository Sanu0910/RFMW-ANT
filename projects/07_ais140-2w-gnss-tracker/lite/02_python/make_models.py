"""Envelope 3D models (STEP) for parts without a KiCad library model in the headless install, built with SolidCraft.

Dimensions are the vendor body sizes (mm), placed in footprint coordinates (origin = footprint origin,
z = 0 on the board surface). They are for enclosure / collision checks, not photorealism.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "01_kicad", "3d")
COL = {"pcb": [0.10, 0.35, 0.18], "can": [0.78, 0.78, 0.80], "black": [0.12, 0.12, 0.12], "white": [0.92, 0.92, 0.90],
       "gold": [0.85, 0.70, 0.30], "ivory": [0.88, 0.84, 0.72]}

# name: list of (x0, y0, x1, y1, z0, height, colour)
MODELS = {
    "Quectel_EC200U": [(-14.0, -15.5, 14.0, 15.5, 0.0, 0.9, "pcb"), (-13.5, -15.0, 13.5, 15.0, 0.9, 1.5, "can")],
    "Quectel_L76K": [(-4.85, -5.05, 4.85, 5.05, 0.0, 0.8, "pcb"), (-4.6, -4.8, 4.6, 4.8, 0.8, 1.6, "can")],
    "MFF2_eSIM": [(-2.5, -3.0, 2.5, 3.0, 0.0, 0.9, "black")],
    "JST_PH_S2B-PH-SM4-TB": [(-3.95, -2.2, 3.95, 4.4, 0.0, 4.8, "white")],
    "JST_XH_B4B-XH-A": [(-2.45, -2.35, 9.95, 3.4, 0.0, 7.0, "white")],
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
