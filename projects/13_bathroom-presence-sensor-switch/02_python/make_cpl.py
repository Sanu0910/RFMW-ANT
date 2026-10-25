"""Convert the KiCad position CSV (kicad-cli pcb export pos) to a JLCPCB CPL file.

JLC's rotation reference differs for some packages (SOT, SOIC, DIP, modules, connectors): check the 3D
preview on JLC's order page and correct with ROT_FIX before ordering. Test pads and mounting holes are
dropped. THT mains parts are typically hand-soldered, not placed by the SMT line - keep or drop per your
assembly house (here they are kept so the file is complete; move them to a hand-solder list if needed).
"""
import csv, os
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "..", "03_fab")
PN = D.PN
ROT_FIX = {}          # e.g. {"U1": 90} after checking JLC's preview

src = os.path.join(FAB, f"{PN}_CPL_raw.csv")
rows = list(csv.DictReader(open(src)))
with open(os.path.join(FAB, f"{PN}_CPL_JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        ref = r["Ref"]
        if ref.startswith(("TP", "H")) or r["Package"].startswith(("MountingHole", "TestPoint")):
            continue
        rot = (float(r["Rot"]) + ROT_FIX.get(ref, 0)) % 360
        w.writerow([ref, f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm",
                    "Top" if r["Side"] == "top" else "Bottom", f"{rot:g}"])
print("CPL rows", len(rows))
