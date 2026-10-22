#!/usr/bin/env python3
"""Render the CAD (STL) to PNG views with pyvista (offscreen)."""
import os
import sys

import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "04_docs", "img")
os.makedirs(OUT, exist_ok=True)
mesh = pv.read(os.path.join(HERE, "lwa_shell.stl"))
views = {"iso": [(55, 70, 45), (0, 0, -3), (0, 0, 1)],
         "top_slots": [(0, 90, 0), (0, 0, -3), (0, 0, 1)],
         "front": [(0, 0, 0.1), (0, 0, -3), (0, 1, 0)],
         "slots_closeup": [(-6, 22, 6), (-8, 2, 0), (0, 0, 1)]}
for name, cam in views.items():
    p = pv.Plotter(off_screen=True, window_size=(1600, 1000))
    p.set_background("white")
    p.add_mesh(mesh, color="#C9CDD2", specular=0.6, specular_power=20, smooth_shading=False)
    if name == "front":
        p.camera_position = [(0, -120, -3), (0, 0, -3), (0, 0, 1)]
    elif name == "top_slots":
        p.camera_position = [(0, 120, 0), (0, 0, 0), (0, 0, 1)]
    else:
        p.camera_position = cam
        if name == "iso":
            p.camera.zoom(1.0)
    p.enable_anti_aliasing()
    p.screenshot(os.path.join(OUT, f"cad_{name}.png"))
    p.close()
print("ok")

# trim the white margins of the renders
from PIL import Image, ImageChops  # noqa: E402

for f in os.listdir(OUT):
    if f.startswith("cad_"):
        im = Image.open(os.path.join(OUT, f)).convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
        if bbox:
            pad = 20
            im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.width),
                     min(bbox[3] + pad, im.height))).save(os.path.join(OUT, f))
