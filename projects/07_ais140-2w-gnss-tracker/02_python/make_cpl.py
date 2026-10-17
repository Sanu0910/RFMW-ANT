"""Convert KiCad position CSV to JLCPCB CPL format (Designator, Mid X, Mid Y, Layer, Rotation).

JLC's rotation reference differs for some packages (SOT-23, SOIC, QFN, LCC modules, connectors):
check the 3D preview in JLC's order page and correct with ROT_FIX before ordering.
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "..", "03_fab")
ROT_FIX = {}          # e.g. {"U3": 90} after checking JLC's preview

rows = list(csv.DictReader(open(os.path.join(FAB, "CRL-TRK-2W-01_CPL_raw.csv"))))
with open(os.path.join(FAB, "CRL-TRK-2W-01_CPL_JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        ref = r["Ref"]
        if ref.startswith(("TP", "H")) or r["Package"].startswith("Tag-Connect"):
            continue
        rot = (float(r["Rot"]) + ROT_FIX.get(ref, 0)) % 360
        w.writerow([ref, f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm",
                    "Top" if r["Side"] == "top" else "Bottom", f"{rot:g}"])
print("CPL rows", len(rows))
