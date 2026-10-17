"""Envelope 3D models (STEP) for parts without a KiCad library model, built with SolidCraft.

Dimensions are the vendor body sizes (mm), placed in footprint coordinates (origin = footprint origin,
z = 0 on the board surface). They are for enclosure / collision checks, not photorealism.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "01_kicad", "3d")
COL = {"pcb": [0.10, 0.35, 0.18], "can": [0.78, 0.78, 0.80], "black": [0.12, 0.12, 0.12], "white": [0.92, 0.92, 0.90],
       "metal": [0.72, 0.72, 0.74], "ivory": [0.88, 0.84, 0.72]}

# name: list of (x0, y0, x1, y1, z0, height, colour)
MODELS = {
    "SIMCom_SIM7080G": [(-7.85, -8.8, 7.85, 8.8, 0.0, 0.9, "pcb"), (-7.5, -8.45, 7.5, 8.45, 0.9, 1.4, "can")],
    "ublox_NEO-F10N": [(-6.1, -8.0, 6.1, 8.0, 0.0, 0.8, "pcb"), (-5.8, -7.7, 5.8, 7.7, 0.8, 1.6, "can")],
    "SW_TS-1187A": [(-2.55, -2.55, 2.55, 2.55, 0.0, 1.0, "black"), (-1.2, -1.2, 1.2, 1.2, 1.0, 0.5, "black")],
    "nanoSIM_GCT_SIM8060": [(-5.85, -7.0, 5.85, 7.0, 0.0, 1.45, "metal")],
    "JST_PH_S3B-PH-SM4-TB": [(-3.95, -1.6, 3.95, 4.4, 0.0, 4.8, "white")],
    "Molex_43045-0812": [(-3.6, -2.4, 12.6, 6.0, 0.0, 9.4, "black")],
    "USB_C_HRO_TYPE-C-31-M-12": [(-4.47, -3.9, 4.47, 3.45, 0.0, 3.26, "metal")],
    "VQFN-16_3x3": [(-1.5, -1.5, 1.5, 1.5, 0.0, 0.9, "black")],
    "MicroCrystal_C7": [(-0.75, -1.6, 0.75, 1.6, 0.0, 0.8, "ivory")],
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
