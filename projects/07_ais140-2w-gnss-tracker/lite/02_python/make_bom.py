"""BOM outputs from design.py: engineering BOM, JLCPCB assembly BOM, costed BOM (CSV) and 04_docs/BOM.md.

Unit costs are estimates at 1 000 pcs (LCSC / distributor price level, October 2026, Rs 88 / USD, excl. GST).
LCSC part numbers are left blank: fill them from the JLC parts search at quotation time (MPN + package given).
DNP parts are listed separately and excluded from the assembly BOM.
"""
import csv, os, re
from collections import OrderedDict
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "03_fab")
DOCS = os.path.join(HERE, "..", "04_docs")
INR = 88.0

# (match on MPN or value, unit USD, category); first match wins
COST = [
    ("EC200U", 6.50, "Modules"), ("L76K", 2.40, "Modules"), ("eUICC", 0.50, "Modules"),
    ("LIS3DH", 0.45, "ICs"), ("XL1509", 0.10, "ICs"), ("MCP73831", 0.35, "ICs"), ("AP2112K", 0.08, "ICs"),
    ("AO340", 0.025, "Discretes"), ("2N7002", 0.012, "Discretes"), ("BSS138", 0.015, "Discretes"),
    ("MMBT3904", 0.010, "Discretes"), ("SS34", 0.020, "Discretes"), ("SMBJ24CA", 0.050, "Discretes"),
    ("SMF5.0A", 0.030, "Discretes"), ("1N4148W", 0.006, "Discretes"), ("KT-0603", 0.010, "Discretes"),
    ("0466002", 0.20, "Passives"), ("SRN6045", 0.25, "Passives"), ("LQG15", 0.02, "Passives"),
    ("B4B-XH", 0.04, "Connectors"), ("S2B-PH", 0.06, "Connectors"), ("U.FL", 0.28, "Connectors"),
    ("100uF/6.3V", 0.15, "Passives"), ("10uF/50V", 0.08, "Passives"), ("4.7uF/50V", 0.03, "Passives"),
    ("22uF/10V", 0.03, "Passives"), ("10uF/10V", 0.01, "Passives"), ("4.7uF/10V", 0.006, "Passives"),
    ("10nF/100V", 0.004, "Passives"), ("/50V", 0.003, "Passives"), ("1uF", 0.002, "Passives"),
    ("0603", 0.0015, "Passives"), ("1206", 0.003, "Passives"), ("0402", 0.0008, "Passives"),
]
# off-board items (Rs per unit at 1k)
OFFBOARD = [
    ("Bare PCB", "60 x 45 mm 2-layer FR-4 1.6 mm, HASL lead-free, green", 25),
    ("SMT assembly", "single-sided, ~95 placements, stencil amortised", 55),
    ("Battery", "1S LiPo 300 mAh 402535 with PCM, JST PH 2-pin lead, BIS IS 16046", 55),
    ("LTE/GSM antenna", "FPC 698-2700 MHz, 100 mm IPEX/U.FL lead, adhesive", 35),
    ("GNSS antenna", "active 25 x 25 mm L1 patch, 28 dB LNA, 80 mm U.FL lead", 85),
    ("Enclosure", "ABS/PC 70 x 55 x 22 mm, IP65 gasket, cable gland (or the 2W-01 IP67 box)", 70),
    ("Harness", "4-core 0.5 mm2, JST XH 4P housing, inline 2 A ATO fuse holder, 1 m", 45),
    ("Relay (optional)", "12 V 30 A automotive relay + socket for the immobiliser kit", 0),
    ("Packaging + manual", "box, foam, Quick-start card, IMEI label", 25),
]


def natural(ref):
    m = re.match(r"([A-Z#]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def groups(dnp=False):
    g = OrderedDict()
    for p in sorted(D.PARTS, key=lambda p: natural(p["ref"])):
        if p["ref"].startswith("#") or p["dnp"] != dnp:
            continue
        if p["lib"] == "Connector:TestPoint" or p["lib"].startswith("Mechanical:"):
            continue
        g.setdefault((p["value"], p["fp"], p["mpn"]), []).append(p)
    return g


def cost(val, mpn):
    for key, usd, cat in COST:
        if key in mpn or key in val:
            return usd, cat
    raise KeyError(f"no cost for {val} / {mpn}")


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for (val, fp, mpn), ps in groups().items():
        usd, cat = cost(val, mpn)
        rows.append(dict(refs=",".join(p["ref"] for p in ps), qty=len(ps), value=val, footprint=fp.split(":")[-1], mpn=mpn,
                         mfr=ps[0]["mfr"], desc=ps[0]["desc"] or "", usd=usd, cat=cat,
                         note="; ".join(sorted({p["note"] for p in ps if p["note"]}))))
    pn = D.PN
    with open(os.path.join(OUT, f"{pn}_BOM_engineering.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Value", "Footprint", "MPN", "Manufacturer", "Description", "Notes"])
        for r in rows:
            w.writerow([r["refs"], r["qty"], r["value"], r["footprint"], r["mpn"], r["mfr"], r["desc"], r["note"]])
    with open(os.path.join(OUT, f"{pn}_BOM_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part Number"])
        for r in rows:
            w.writerow([r["value"], r["refs"], r["footprint"], "", r["mpn"]])
    cats = OrderedDict()
    with open(os.path.join(OUT, f"{pn}_BOM_costed.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Value", "MPN", "Manufacturer", "Unit USD (est. @1k)", "Ext USD", "Ext INR", "Category"])
        for r in rows:
            ext = r["usd"] * r["qty"]
            cats[r["cat"]] = cats.get(r["cat"], 0) + ext
            w.writerow([r["refs"], r["qty"], r["value"], r["mpn"], r["mfr"], f"{r['usd']:.4f}", f"{ext:.3f}", f"{ext * INR:.1f}", r["cat"]])
        for item, desc, rs in OFFBOARD:
            w.writerow(["", 1, item, desc, "", f"{rs / INR:.3f}", f"{rs / INR:.3f}", f"{rs:.1f}", "Off-board"])
    parts_inr = sum(cats.values()) * INR
    off_inr = sum(rs for _, _, rs in OFFBOARD)
    dnp = list(groups(True).items())
    n = sum(r["qty"] for r in rows)
    with open(os.path.join(DOCS, "BOM.md"), "w") as f:
        f.write(f"# {pn} Bill of Materials (rev {D.REV}) - Samay Track 2W Lite\n\n")
        f.write("Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: "
                f"`03_fab/{pn}_BOM_JLCPCB.csv` (fill the LCSC column at quotation); costed BOM: `03_fab/{pn}_BOM_costed.csv`.\n\n")
        f.write(f"**{len(rows)} line items, {n} placed parts (all top side)**, plus {sum(len(v) for _, v in dnp)} DNP and "
                f"{sum(1 for p in D.PARTS if p['lib'] == 'Connector:TestPoint')} test pads.\n\n")
        f.write("## Cost summary (estimate, 1 000 pcs, Rs 88 / USD, excl. GST)\n\n| Group | Rs |\n|---|---|\n")
        for c, usd in cats.items():
            f.write(f"| {c} | {usd * INR:,.0f} |\n")
        f.write(f"| **Board parts** | **{parts_inr:,.0f}** |\n")
        for item, desc, rs in OFFBOARD:
            f.write(f"| {item} - {desc} | {rs} |\n")
        f.write(f"| **Total hardware per unit** | **{parts_inr + off_inr:,.0f}** |\n\n")
        f.write("Business-plan target for the Lite (07_marketing/BUSINESS_PLAN_NOTES.md section 5): Rs 1,200-1,500. "
                "Cost-down options: SC7A20 for the LIS3DH (-Rs 30), TP4054 for the MCP73831 (-Rs 28), generic IPEX "
                "connectors (-Rs 40), passive GNSS patch on the lid (-Rs 45).\n\n")
        f.write("## Placed parts\n\n| Designators | Qty | Value | Package | MPN | Manufacturer | Unit Rs | Description |\n"
                "|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['refs']} | {r['qty']} | {r['value']} | {r['footprint']} | {r['mpn']} | {r['mfr']} | "
                    f"{r['usd'] * INR:.2f} | {r['desc']} |\n")
        f.write("\n## Not populated (tuning / options)\n\n| Designators | Value | Package | Purpose |\n|---|---|---|---|\n")
        for (val, fp, mpn), ps in dnp:
            f.write(f"| {','.join(p['ref'] for p in ps)} | {val} | {fp.split(':')[-1]} | {ps[0]['note'] or mpn} |\n")
    print("BOM rows", len(rows), "parts", n, f"board parts Rs {parts_inr:.0f}, total Rs {parts_inr + off_inr:.0f}")


if __name__ == "__main__":
    main()
