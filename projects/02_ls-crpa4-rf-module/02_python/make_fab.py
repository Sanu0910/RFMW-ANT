"""Fabrication package for CRL-LS-CRPA4 (run after run_drc.sh). Writes 04_fab/:
  Gerbers/ + CRL-LS-CRPA4_Gerbers.zip (Gerber X2, Excellon PTH/NPTH + map), CRL-LS-CRPA4_CPL_bottom.csv,
  CRL-LS-CRPA4.d356 (IPC-D-356), CRL-LS-CRPA4_BOM.csv/.xlsx (grouped by MPN, incl. mechanical items),
  CRL-LS-CRPA4_FAB_NOTES.md (stack-up, impedance, finish, via plugging, tests); 06_step/CRL-LS-CRPA4_PCB.step
  (board + parts, cover frame) and 05_docs/img/render_top/bottom.png.
Run with the repo .venv:  python make_fab.py
"""
import collections, csv, json, os, subprocess, zipfile
import ls_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
FAB, STEP, IMG = (os.path.join(PRJ, d) for d in ("04_fab", "06_step", os.path.join("05_docs", "img")))
PCB = os.path.join(PRJ, "03_kicad", "CRL-LS-CRPA4.kicad_pcb")
KI = os.path.join(os.environ.get("KICAD10", r"C:\Program Files\KiCad\10.0"), "bin", "kicad-cli.exe")
PN = "CRL-LS-CRPA4"

# items that are not on the PCB pick-and-place but belong to the assembly
MECH = [
    ("BC01", 1, "CRL-LS-CRPA4-BC01", "project 02 drawing", "Back cover L+S, Al 6061-T6, chromate conversion MIL-DTL-5541 Ty II Cl 3", "06_step/CRL-LS-CRPA4-BC01.step"),
    ("GSK1", 1, "CHOFORM 5575 [ASSUMED]", "Parker Chomerics", "Form-in-place conductive gasket on the BC01 wall tops, 0.8 mm bead, compressed to 0.30 mm", ""),
    ("ANT-L", 4, "GPDF6010.A", "Taoglas", "L1/L2 stacked patch, fitted on top (customer supplied)", ""),
    ("ANT-S", 4, "CRL-LS-SP01", "BEL CRL (in-house)", "NavIC S patch 2492.028 MHz RHCP, <= 25 x 25 mm, 4 pins D0.77 at 4 mm + centre GND, lambda/2 spacing (r 42.53 mm)", ""),
    ("SCR1", 16, "ISO 4762 M3x12 A2", "-", "Back cover -> board -> L patch, through the D3.6 M holes [ASSUMED length]", ""),
    ("SCR2", 4, "ISO 4762 M2.5x6 A2", "-", "DC receptacle flange", ""),
    ("J-DC", 1, "[ASSUMED] flange receptacle, 2+ pins, IP67", "Amphenol / Binder", "Sealed DC input on BC01 (D16.2 cut-out, 20 mm square M2.5)", ""),
    ("W1", 1, "Harness J-DC -> J5", "-", "Molex Micro-Fit 3.0 43645-0200 housing + 2 x 46235 crimps, AWG22, 60 mm", ""),
]


def sh(args):
    r = subprocess.run([KI] + args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("kicad-cli failed: " + " ".join(args) + "\n" + r.stderr[-1500:])


def exports():
    g = os.path.join(FAB, "Gerbers")
    os.makedirs(g, exist_ok=True)
    for f in os.listdir(g): os.remove(os.path.join(g, f))
    sh(["pcb", "export", "gerbers", "--output", g + os.sep, "--layers",
        "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts",
        "--subtract-soldermask", PCB])
    sh(["pcb", "export", "drill", "--output", g + os.sep, "--format", "excellon", "--excellon-separate-th",
        "--generate-map", "--map-format", "gerberx2", "--excellon-units", "mm", PCB])
    sh(["pcb", "export", "pos", "--output", os.path.join(FAB, PN + "_CPL_bottom.csv"), "--format", "csv", "--units", "mm",
        "--side", "back", "--exclude-dnp", PCB])
    sh(["pcb", "export", "ipcd356", "--output", os.path.join(FAB, PN + ".d356"), PCB])
    with zipfile.ZipFile(os.path.join(FAB, PN + "_Gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
    os.makedirs(STEP, exist_ok=True)
    sh(["pcb", "export", "step", "--output", os.path.join(STEP, PN + "_PCB.step"), "--force", "--subst-models",
        "--user-origin", f"{D.BOARD_CENTER[0]}x{D.BOARD_CENTER[1]}mm", PCB])
    for side in ("top", "bottom"):
        sh(["pcb", "render", "--side", side, "-w", "2000", "-h", "2000", "--quality", "high", "--background", "opaque",
            "-o", os.path.join(IMG, f"render_{side}.png"), PCB])


def bom():
    parts = json.load(open(os.path.join(FAB, "_parts.json")))
    grp = collections.OrderedDict()
    for p in parts:
        key = p["key"]
        if key not in D.PARTS or key in ("ANT", "SANT"): continue      # antennas: assembly lines ANT-L / ANT-S
        lib, fp, val, mpn, mfr, desc = D.PARTS[key]
        if mpn in ("-",) and key not in ("TP",): continue
        g = grp.setdefault((mpn, val, fp), dict(refs=[], mfr=mfr, desc=desc, side=p["side"]))
        g["refs"].append(p["ref"])
    rows = []
    for i, ((mpn, val, fp), g) in enumerate(sorted(grp.items(), key=lambda kv: (kv[1]["refs"][0][0], kv[0][0])), 1):
        dnp = val == "DNP"
        rows.append(dict(item=i, qty=0 if dnp else len(g["refs"]), refs=" ".join(sorted(g["refs"])), value=val, mpn=mpn,
                         manufacturer=g["mfr"], footprint=fp, side=g["side"], description=g["desc"] + (" (not fitted)" if dnp else "")))
    n0 = len(rows)
    for j, (ref, q, mpn, mfr, desc, f) in enumerate(MECH, n0 + 1):
        rows.append(dict(item=j, qty=q, refs=ref, value="", mpn=mpn, manufacturer=mfr, footprint=f or "mechanical",
                         side="assembly", description=desc))
    path = os.path.join(FAB, PN + "_BOM.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    try:
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "BOM"
        ws.append(list(rows[0]))
        for r in rows: ws.append(list(r.values()))
        for col, wdt in zip("ABCDEFGHI", (5, 5, 60, 12, 26, 18, 34, 9, 80)): ws.column_dimensions[col].width = wdt
        wb.save(path.replace(".csv", ".xlsx"))
    except ImportError:
        pass
    return rows


def notes(rows):
    smd = sum(r["qty"] for r in rows if r["side"] == "bottom")
    st = "\n".join(f"| {n} | {t} | {th:.3f} | {er if er else ''} | {note} |" for n, t, th, er, note in D.STACKUP)
    txt = f"""# {PN} REV A - fabrication and assembly notes

Board: D200.0 mm round, 4 copper layers, {D.BOARD_THICKNESS} mm, all SMD parts on the bottom (L4 / B.Cu), {smd} placements.
Files: `{PN}_Gerbers.zip` (Gerber X2 + Excellon PTH/NPTH + drill map), `{PN}_CPL_bottom.csv`, `{PN}.d356`, `{PN}_BOM.csv/.xlsx`.

## Stack-up (hybrid build: order exactly this)
| Layer | Type | Thickness mm | er | Note |
|---|---|---|---|---|
{st}

## Fabrication requirements
1. IPC-6012 Class 2 (Class 3 if the CRPA is for airborne use), IPC-A-600 Class 2; UL 94V-0.
2. Materials: FR-4 high Tg >= 170 C (IT-180A / S1000-2 or equal) + Rogers RO4350B 0.168 mm (6.6 mil) core, 1 oz both sides.
   Hybrid lamination FR-4 prepreg to RO4350B: plasma desmear before plating.
3. **Controlled impedance on L4: 50 ohm +-10 % single-ended, {D.RF_W} mm track over L3 (RO4350B 0.168 mm), 35 um finished Cu,
   with solder mask.** Coupon on the panel; report TDR.
4. Finish ENIG (Ni 3-6 um, Au 0.05-0.10 um); soldermask green LPI both sides; legend white both sides; no mask on the
   exposed shield-frame lands ({D.SHIELD_W} mm GND rings on L4) - they carry the back-cover gasket.
5. Vias: 0.30 mm drill / 0.60 mm pad standard. **Vias in pads (0.25 / 0.50 mm in the TQP3M9037, CLM-83-2W+ and SAW ground
   pads) resin-filled and capped, IPC-4761 Type VII.** Min. annular ring 0.125 mm.
6. Min track / space 0.15 / 0.15 mm, min drill 0.25 mm; board edge to copper >= 0.5 mm.
7. Bow and twist <= 0.5 % (D200 thin hybrid: panel with copper balancing, bake before assembly).
8. 100 % electrical test against `{PN}.d356`.
9. RoHS / REACH.

## Assembly
1. Bottom side reflow (SAC305, type 4 paste; 0.10-0.12 mm stencil, window reduction 10 % on 0402, 50 % paste on exposed
   pads in a window grid). MSL: B7504 / B8889 MSL3 - bake per J-STD-033 if exposed > 168 h.
   TA1442A (S SAW): peak 260 C per the Tai-Saw profile; ESD sensitive; max DC 3 V on the pads (all S SAWs sit between
   DC-block capacitors). C2327J5003AHF and TA1442A land patterns are the vendor drawings (00_vendor/).
2. THT: 8 SMA (Amphenol 132134), J5 Micro-Fit - selective or hand solder after reflow.
3. Clean (no-clean flux residue must stay off the SAW lids), 100 % AOI, X-ray of the DFN-8 and DL1721 ground pads.
4. Top side: fit the 4 GPDF6010.A L patches and 4 S patches; solder the feed pins from the bottom.
5. Back cover: FIP gasket on the wall tops, cure, then 16 x M3 through cover, board and L patches (0.9 N m [ASSUMED]).
6. Test each module with the test board / per channel: S21 gain and phase at L1, L5, L2, S; NF; record the
   channel-to-channel gain/phase table (calibration data delivered with the unit).

## Open items before release
- S patch CRL-LS-SP01 (BEL CRL in-house): drawing, fixing and measured S11 / AR still to be issued. The S hybrid wiring is RHCP for a patch whose F90 pin sits +90 deg CCW (top view)
  from F0: F0 -> C2327J5003AHF pin 4 (direct), F90 -> pin 6 (coupled), pin 1 out, pin 3 -> 50 ohm. Confirm with the patch drawing.
- GPDF6010.A fixing: customer board D3.6 / D1.35 vs data sheet D1.8 / D1.1.
"""
    open(os.path.join(FAB, PN + "_FAB_NOTES.md"), "w", encoding="utf-8").write(txt)


if __name__ == "__main__":
    exports()
    rows = bom()
    notes(rows)
    print("BOM lines", len(rows), "placements", sum(r["qty"] for r in rows if r["side"] == "bottom"))
    print(sorted(os.listdir(FAB)))
