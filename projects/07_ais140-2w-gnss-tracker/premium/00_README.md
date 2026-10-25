# 07 — CRL-TRK-2W-01: AIS-140 two-wheeler GNSS / LTE-M tracker (Premium)

The **premium** board of this project. The cost-reduced **Lite** variant (CRL-TRK-2W-L1) is a sibling folder: [`../lite/`](../lite/).

Production-oriented tracker PCB for motorcycles and scooters (IP67 enclosure, 12/24 V vehicles).
**60 × 45 mm, 4-layer, double-sided assembly, JLCPCB / PCBWay ready.**

ESP32-S3-WROOM-1 · SIMCom SIM7080G LTE-M/NB-IoT · u-blox NEO-F10N L1/L5 + NavIC · IIM-42652 IMU ·
BQ24074 + 18650 backup · LM74700-Q1 reverse protection · LM5164-Q1 100 V buck · W25Q128 log flash · RV-3028 RTC

## Folders

| Folder | Content |
|---|---|
| `01_kicad/` | KiCad 9 project `tracker.kicad_pro` (hierarchical schematic, 6 sheets, 4-layer PCB, project library) |
| `02_python/` | **source of truth**: `design.py` (circuit), `make_schematic.py`, `make_pcb.py` (placement, rules, RF routes, fan-out, stitching), `make_bom.py`, `make_pins.py`, `rf_calc.py`, `make_lib.py` |
| `03_fab/` | Gerbers + drill (zip), pick-and-place (CPL) for JLC, assembly BOM (JLC format) and engineering BOM |
| `04_docs/` | **`CRL-TRK-2W-01_Workflow_UseCases.pdf` (plain-language guide: use cases, operating modes, alert flows, installation, design & production workflow)**, `DESIGN_REPORT.md` (power tree, budget, SI, EMC, DFM, automotive, AIS-140, test, production checklist), `BOM.md`, `VERIFY_LIST.md`, schematic PDF, assembly drawings |
| `05_renders/` | 3D STEP of the assembled board and rendered views (modules/connectors without a KiCad model use envelope STEPs from `make_models.py`, SolidCraft) |
| `06_firmware/` | `board_pins.h` generated from the netlist |
| `07_marketing/` | launch poster (PNG/PDF/HTML), `PRICING_NOTES.md` (BOM cost, margins, competitors), `BUSINESS_PLAN_NOTES.md` (range, USP, Lite version, Amazon, AIS-140 cost, go-to-market, app plan), **`SamayTrack2W_Business_Plan.pdf`** (16-page product, design, cost, investment and timeline plan; source `02_python/make_business_pdf.py`) |

The Lite variant lives in the sibling [`../lite/`](../lite/) folder (board `CRL-TRK-2W-L1`).

## Regenerate

```bash
cd 02_python
python3 make_lib.py && python3 make_schematic.py && python3 make_bom.py && python3 make_pins.py && python3 make_models.py
python3 make_workflow_pdf.py                  # workflow & use-case guide PDF
# PCB (KiCad 9 pcbnew python + Freerouting 1.9):
python3 make_pcb.py dsn                       # placement, RF routes, GND/+3V3 fan-out, rules -> tracker.dsn
java -jar freerouting-1.9.0.jar -de ../01_kicad/tracker.dsn -do ../01_kicad/tracker.ses -mp 40
python3 make_pcb.py ses && python3 make_pcb.py finish   # import, purge, EP/stitch/island vias, pours
kicad-cli pcb drc --schematic-parity --format json -o drc.json ../01_kicad/tracker.kicad_pcb
python3 make_pcb.py patch                     # A* finisher for DRC-unconnected items (RIPUP=1 allows rip-up)
python3 make_pcb.py models && python3 make_cpl.py
```

## Altium

Altium Designer (21+) opens this design directly: *File → Import Wizard → KiCad Design Files*, select
`01_kicad/tracker.kicad_pro` — schematic, PCB, rules and stack-up are imported. A native `.PrjPcb` cannot be
generated outside Altium, so this is the supported path.

## Status

Rev A0 — pre-prototype. Layout complete: DRC 0 errors / 0 unconnected, ERC clean, schematic ↔ PCB parity clean. Read `04_docs/VERIFY_LIST.md` before ordering: several component values were set
without the vendor datasheet at hand (no web access on the build machine) and must be checked.
