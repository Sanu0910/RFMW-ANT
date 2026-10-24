"""Generate a JLCPCB-style assembly BOM (grouped) from design.py.

Columns: Comment, Designator, Footprint, MPN, Manufacturer, LCSC  (LCSC left blank to fill in).
Battery pack (external) is excluded. Groups identical value+footprint into one line.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import pinmap

FAB = os.path.normpath(os.path.join(HERE, "..", "03_fab"))
OFFBOARD = {"BT1"}


def build():
    groups = {}
    for ref, value, mpn, mfr, fp, group, desc in D.PARTS:
        if ref in OFFBOARD or pinmap.FOOTPRINT.get(fp) is None:
            continue
        kfp = pinmap.FOOTPRINT.get(fp, fp).split(":")[-1]
        key = (value, mpn, mfr, kfp)
        groups.setdefault(key, []).append(ref)
    rows = []
    for (value, mpn, mfr, kfp), refs in sorted(groups.items(), key=lambda kv: kv[0][3]):
        rows.append([value, ",".join(sorted(refs)), kfp, mpn, mfr, ""])
    path = os.path.join(FAB, "NOVA-RF1_BOM_JLCPCB.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "MPN", "Manufacturer", "LCSC"])
        w.writerows(rows)
    print(f"wrote {path}: {len(rows)} BOM lines, {sum(len(r[1].split(',')) for r in rows)} placements")


if __name__ == "__main__":
    build()
