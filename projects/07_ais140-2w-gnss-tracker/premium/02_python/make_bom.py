"""BOM outputs from design.py: engineering BOM (markdown + CSV) and a JLCPCB-format assembly BOM.

LCSC part numbers are intentionally left blank: fill them from the JLC parts search at quotation time
(MPN + package are given). DNP parts are listed separately and excluded from the assembly BOM.
"""
import csv, os, re
from collections import OrderedDict
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "03_fab")
DOCS = os.path.join(HERE, "..", "04_docs")


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
        key = (p["value"], p["fp"], p["mpn"])
        g.setdefault(key, []).append(p)
    return g


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for (val, fp, mpn), ps in groups().items():
        refs = ",".join(p["ref"] for p in ps)
        rows.append(dict(refs=refs, qty=len(ps), value=val, footprint=fp.split(":")[-1], mpn=mpn,
                         mfr=ps[0]["mfr"], desc=ps[0]["desc"] or "", note="; ".join(sorted({p["note"] for p in ps if p["note"]}))))
    with open(os.path.join(OUT, "CRL-TRK-2W-01_BOM_engineering.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Value", "Footprint", "MPN", "Manufacturer", "Description", "Notes"])
        for r in rows:
            w.writerow([r["refs"], r["qty"], r["value"], r["footprint"], r["mpn"], r["mfr"], r["desc"], r["note"]])
    with open(os.path.join(OUT, "CRL-TRK-2W-01_BOM_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part Number"])
        for r in rows:
            w.writerow([r["value"], r["refs"], r["footprint"], "", r["mpn"]])
    dnp = [(k, v) for k, v in groups(True).items()]
    with open(os.path.join(DOCS, "BOM.md"), "w") as f:
        f.write("# CRL-TRK-2W-01 Bill of Materials (rev A0)\n\n")
        f.write("Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: "
                "`03_fab/CRL-TRK-2W-01_BOM_JLCPCB.csv` (fill the LCSC column at quotation).\n\n")
        n = sum(r["qty"] for r in rows)
        f.write(f"**{len(rows)} line items, {n} placed parts**, plus {sum(len(v) for _, v in dnp)} DNP and "
                f"{sum(1 for p in D.PARTS if p['lib']=='Connector:TestPoint')} test pads.\n\n")
        f.write("| Designators | Qty | Value | Package | MPN | Manufacturer | Description |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['refs']} | {r['qty']} | {r['value']} | {r['footprint']} | {r['mpn']} | {r['mfr']} | {r['desc']} |\n")
        f.write("\n## Not populated (tuning / variant options)\n\n| Designators | Value | Package | Purpose |\n|---|---|---|---|\n")
        for (val, fp, mpn), ps in dnp:
            f.write(f"| {','.join(p['ref'] for p in ps)} | {val} | {fp.split(':')[-1]} | {ps[0]['note'] or mpn} |\n")
        f.write("\n## Off-board items (harness / enclosure)\n\n"
                "| Item | Recommended part | Notes |\n|---|---|---|\n"
                "| LTE antenna | Taoglas FXUB63 (698-3000 MHz flex, U.FL, 100 mm) | stick to the enclosure wall opposite the GNSS antenna |\n"
                "| GNSS antenna | active L1/L5 patch with U.FL lead (gain <= 25 dB, 3.0-3.3 V) | lid, sky-facing, >= 15 mm from LTE antenna |\n"
                "| Battery | 1S 18650 Li-ion 2500-3500 mAh with PCM + 10k NTC (B=3435), JST PH 3-pin | cell holder / foam in the enclosure |\n"
                "| Harness | Molex Micro-Fit 3.0 43025-0800 receptacle + 43030 crimps, 0.5-0.75 mm2 | inline 3 A ATO blade fuse on +12 V |\n"
                "| Enclosure | IP67 ABS/PC-ABS, 80x60x30 mm class, M12 cable gland, Gore vent | UV-stabilised |\n")
    print("BOM rows", len(rows), "parts", sum(r["qty"] for r in rows))


if __name__ == "__main__":
    main()
