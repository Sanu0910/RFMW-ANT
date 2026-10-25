"""BOM outputs from design.py: engineering BOM, JLCPCB assembly BOM, costed BOM (CSV) and 04_docs/BOM.md.

Unit costs are order-of-magnitude estimates at 1 000 pcs (LCSC / Indian-distributor level, 2026, Rs 86 / USD,
excl. GST). LCSC part numbers are left blank: fill them from the JLC parts search at quotation time.
DNP parts are listed separately and excluded from the assembly BOM. The mains THT parts (fuse, MOV, NTC,
triac, opto, HLK-PM01, screw terminal, film caps) are hand-placed / wave- or hand-soldered, not SMT.
"""
import csv, os, re
from collections import OrderedDict
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "03_fab")
DOCS = os.path.join(HERE, "..", "04_docs")
INR = 86.0

# (match on MPN or value, unit USD, category); first match wins
COST = [
    ("HLK-PM01", 1.80, "Power (mains)"), ("ATTINY13A", 0.45, "ICs"), ("MOC3063", 0.35, "Opto / isolation"),
    ("BTA16", 0.42, "Triac / power"), ("0382.500", 0.18, "Protection (mains)"),
    ("14D471K", 0.06, "Protection (mains)"), ("B72214", 0.06, "Protection (mains)"),
    ("MF72-5D9", 0.05, "Protection (mains)"), ("R46KI", 0.12, "Protection (mains)"),
    ("MKDS", 0.35, "Connectors"), ("MX126", 0.12, "Connectors"),
    ("3386P", 0.28, "UI"), ("tactile", 0.04, "UI"), ("PTS645", 0.04, "UI"), ("TS-1101", 0.04, "UI"),
    ("green 0805", 0.01, "UI"), ("HLK-LD2410B", 2.60, "Sensor (radar)"),
    ("X1 film", 0.09, "Passives (mains)"), ("X2", 0.08, "Passives (mains)"),
    ("axial 2 W", 0.03, "Passives (mains)"), ("axial 0.5 W", 0.015, "Passives (mains)"),
    ("axial 0.4 W", 0.01, "Passives (mains)"), ("220uF", 0.03, "Passives"),
    ("header", 0.03, "Connectors"), ("2x3", 0.05, "Connectors"), ("1x3", 0.03, "Connectors"),
    ("Test pad", 0.0, "Test"), ("0805", 0.004, "Passives"), ("0603", 0.0015, "Passives"),
]
# off-board items (Rs per unit at 1k)
OFFBOARD = [
    ("Bare PCB", "70 x 56 mm 2-layer FR-4 1.6 mm, 1 oz, ENIG, green, isolation slot routed", 40),
    ("Assembly", "mixed SMT (SELV) + THT (mains), single-sided, ~40 placements + hand-solder mains", 70),
    ("Radar module", "HLK-LD2410B 24 GHz on vertical header (listed in BOM; cost dominates)", 0),
    ("Enclosure", "FR-ABS modular front plate + back shell, RF-transparent sensor window, IP44 bathroom", 95),
    ("Wiring / label", "L/N/LAMP ferrules, HIGH-VOLTAGE label, install card", 20),
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
    return 0.01, "Passives"


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for (val, fp, mpn), ps in groups().items():
        usd, cat = cost(val, mpn)
        rows.append(dict(refs=",".join(p["ref"] for p in ps), qty=len(ps), value=val, footprint=fp.split(":")[-1],
                         mpn=mpn, mfr=ps[0]["mfr"], desc=ps[0]["desc"] or "", usd=usd, cat=cat,
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
        w.writerow(["Designators", "Qty", "Value", "MPN", "Manufacturer", "Unit USD (est @1k)", "Ext USD", "Ext INR", "Category"])
        for r in rows:
            ext = r["usd"] * r["qty"]
            cats[r["cat"]] = cats.get(r["cat"], 0) + ext
            w.writerow([r["refs"], r["qty"], r["value"], r["mpn"], r["mfr"], f"{r['usd']:.4f}", f"{ext:.3f}",
                        f"{ext * INR:.1f}", r["cat"]])
        for item, desc, rs in OFFBOARD:
            w.writerow(["", 1, item, desc, "", f"{rs / INR:.3f}", f"{rs / INR:.3f}", f"{rs:.1f}", "Off-board"])
    parts_inr = sum(cats.values()) * INR
    off_inr = sum(rs for _, _, rs in OFFBOARD)
    dnp = list(groups(True).items())
    n = sum(r["qty"] for r in rows)
    with open(os.path.join(DOCS, "BOM.md"), "w") as f:
        f.write(f"# {pn} Bill of Materials (rev {D.REV}) - Smart Bathroom Presence Sensor Switch\n\n")
        f.write("Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: "
                f"`03_fab/{pn}_BOM_JLCPCB.csv` (fill the LCSC column at quotation); costed BOM: "
                f"`03_fab/{pn}_BOM_costed.csv`.\n\n")
        f.write(f"**{len(rows)} line items, {n} placed parts**, plus {sum(len(v) for _, v in dnp)} DNP and "
                f"{sum(1 for p in D.PARTS if p['lib'] == 'Connector:TestPoint')} test pads and "
                f"{sum(1 for p in D.PARTS if p['lib'].startswith('Mechanical'))} mounting holes.\n\n")
        f.write("> **Mains parts** (F1, MOV1, NTC1, CX1, RB1, PS1, U2, Q1, RG1, RS1, CS1, J1) carry live voltage. "
                "Use only the rated MPNs (X2/X1 safety caps, 250 V+ fuse, reinforced-isolation PSU). "
                "See `SAFETY_REVIEW.md` before procurement.\n\n")
        f.write("## Cost summary (estimate, 1 000 pcs, Rs 86 / USD, excl. GST)\n\n| Group | Rs |\n|---|---|\n")
        for c, usd in sorted(cats.items(), key=lambda kv: -kv[1]):
            f.write(f"| {c} | {usd * INR:,.0f} |\n")
        f.write(f"| **Board parts total** | **{parts_inr:,.0f}** |\n")
        for item, desc, rs in OFFBOARD:
            f.write(f"| {item} - {desc} | {rs} |\n")
        f.write(f"| **Total hardware per unit (est.)** | **{parts_inr + off_inr:,.0f}** |\n\n")
        f.write("Cost is dominated by the LD2410B radar and the HLK-PM01 supply. A WiFi-less premium sensor switch "
                "retails Rs 1,200-2,500 in India, so the BOM leaves healthy margin.\n\n")
        f.write("## Placed parts\n\n| Designators | Qty | Value | Package | MPN | Manufacturer | Unit Rs | Description |\n"
                "|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['refs']} | {r['qty']} | {r['value']} | {r['footprint']} | {r['mpn']} | {r['mfr']} | "
                    f"{r['usd'] * INR:.2f} | {r['desc']} |\n")
        if dnp:
            f.write("\n## Not populated (options)\n\n| Designators | Value | Package | Purpose |\n|---|---|---|---|\n")
            for (val, fp, mpn), ps in dnp:
                f.write(f"| {','.join(p['ref'] for p in ps)} | {val} | {fp.split(':')[-1]} | {ps[0]['note'] or mpn} |\n")
    print("BOM rows", len(rows), "parts", n, f"board Rs {parts_inr:.0f}, total Rs {parts_inr + off_inr:.0f}")


if __name__ == "__main__":
    main()
