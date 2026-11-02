"""Debug/preview plot of the generated layout (pads, tracks, vias) from Images/_debug_layout.json."""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
PROJ = Path(__file__).resolve().parent.parent
d = json.loads((PROJ / "Images" / "_debug_layout.json").read_text())
xlim = [float(v) for v in sys.argv[1:5]] if len(sys.argv) >= 5 else [18, 224, 20, 226]
out = sys.argv[5] if len(sys.argv) > 5 else "layout_debug.png"
fig, ax = plt.subplots(figsize=(14, 14))
for p in d["pads"]:
    col = "#c0392b" if p["net"].startswith("CH") else ("#e67e22" if p["net"] == "+5V" else "#7f8c8d")
    ax.add_patch(Rectangle((p["x0"], p["y0"]), p["x1"] - p["x0"], p["y1"] - p["y0"], fc=col, ec="k", lw=0.2, alpha=0.8))
for t in d["tracks"]:
    col = "#2980b9" if t["net"].startswith("CH") else ("#e67e22" if t["net"] == "+5V" else "#27ae60")
    ax.plot([t["x1"], t["x2"]], [t["y1"], t["y2"]], color=col, lw=max(0.5, t["w"] * 72 / 25.4 * 14 / (xlim[1] - xlim[0]) * 10), solid_capstyle="round")
for v in d["vias"]:
    ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, fc="#27ae60" if v["net"] == "GND" else "#e67e22", ec="k", lw=0.2))
if (xlim[1]-xlim[0]) < 80:
    seen=set()
    for p in d["pads"]:
        if p["ref"] in seen: continue
        seen.add(p["ref"])
        if xlim[0] < p["x0"] < xlim[1] and xlim[2] < p["y0"] < xlim[3]:
            ax.text(p["x0"], p["y0"], p["ref"], fontsize=6)
ax.set_xlim(xlim[0], xlim[1]); ax.set_ylim(xlim[3], xlim[2]); ax.set_aspect("equal"); ax.grid(alpha=.3)
fig.savefig(PROJ / "Images" / out, dpi=110, bbox_inches="tight")
