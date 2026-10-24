"""Costed BOM for NOVA-RF1 (estimated unit prices, USD).

Prices are typical small-quantity distributor estimates (LCSC/Digikey ballpark, 2025) for
rough budgeting only - get a live quote for production. Battery is external (listed separately).
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

# estimated unit price (USD, qty ~10-100) keyed by MPN substring; first match wins
PRICE = [
    ("STM32WB55", 6.50), ("CC1101", 2.80), ("ST25R3916", 3.60), ("BQ25896", 2.20),
    ("BQ27220", 1.80), ("LM3281", 0.90), ("RS3221", 0.15), ("LP5562", 1.20),
    ("TPS22917", 0.40), ("USBLC6", 0.25), ("LMV358", 0.20), ("LMV331", 0.15),
    ("ST7565", 3.80), ("DM3D", 0.55),            # microSD holder
    ("TYPE-C", 0.45), ("USB", 0.45),
    ("ABM8", 0.30), ("ABS07", 0.15), ("CXD2-026", 0.20), ("XRCGB27M", 0.30),
    ("CXD2-032", 0.30),
    ("B0310J", 0.55), ("LFL182", 0.45), ("1001312", 0.30),   # balun / BLE filter / chip ant
    ("BGS13", 0.65), ("U.FL", 0.30),
    ("FH34SRJ", 0.70), ("FH12", 0.70), ("Conn_2x09", 0.30), ("1.25-3P", 0.20),
    ("TC2030", 0.00),                               # Tag-Connect: pads only, no part
    ("VSMY14940", 0.15), ("TSOP", 0.50),            # IR LED / receiver
    ("BCE-MX8530", 0.45), ("ERM", 0.50),            # speaker / vibro
    ("LTST", 0.18),                                 # RGB LED
    ("ESD", 0.10), ("DMP", 0.06), ("DMN", 0.06), ("2N7002", 0.04), ("MMDT", 0.08),
    ("470nH", 0.10), ("10uH", 0.12), ("2.2uH", 0.10), ("nH", 0.10), ("uH", 0.12),
    ("mOhm", 0.05), ("ohm", 0.02), ("array", 0.05),
    ("uF", 0.03), ("nF", 0.02), ("pF", 0.02), ("k", 0.01), ("m", 0.02),
]
DEFAULT = 0.03


def unit_price(mpn, value):
    hay = f"{mpn} {value}"
    for key, pr in PRICE:
        if key.lower() in hay.lower():
            return pr
    return DEFAULT


def build():
    groups = {}
    for ref, value, mpn, mfr, fp, group, desc in D.PARTS:
        if ref in OFFBOARD or pinmap.FOOTPRINT.get(fp) is None:
            continue
        key = (value, mpn, mfr, fp)
        groups.setdefault(key, []).append(ref)
    rows = []
    total = 0.0
    for (value, mpn, mfr, fp), refs in sorted(groups.items(), key=lambda kv: -unit_price(kv[0][1], kv[0][0]) * len(kv[1])):
        qty = len(refs)
        up = unit_price(mpn, value)
        ext = up * qty
        total += ext
        rows.append([value, mpn, ",".join(sorted(refs)), qty, f"{up:.2f}", f"{ext:.2f}"])
    path = os.path.join(FAB, "NOVA-RF1_BOM_costed.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Value", "MPN", "Designators", "Qty", "UnitUSD", "ExtUSD"])
        w.writerows(rows)
        w.writerow([])
        w.writerow(["", "", "COMPONENTS SUBTOTAL", sum(int(r[3]) for r in rows), "", f"{total:.2f}"])
    print(f"wrote {path}: {len(rows)} lines, {sum(int(r[3]) for r in rows)} placements, parts ${total:.2f}/board")
    return total


if __name__ == "__main__":
    build()
