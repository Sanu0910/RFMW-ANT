# 07 — CRL-TRK-2W-01: AIS-140 two-wheeler GNSS / LTE-M tracker

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
| `04_docs/` | `DESIGN_REPORT.md` (power tree, budget, SI, EMC, DFM, automotive, AIS-140, test, production checklist), `BOM.md`, `VERIFY_LIST.md`, schematic PDF, assembly drawings |
| `05_renders/` | 3D STEP of the assembled board and rendered views |
| `06_firmware/` | `board_pins.h` generated from the netlist |

## Regenerate

```bash
cd 02_python
python3 make_lib.py && python3 make_schematic.py && python3 make_bom.py && python3 make_pins.py
# PCB (needs KiCad 9 pcbnew python):  place -> dsn -> Freerouting -> ses
python3 make_pcb.py dsn
java -jar freerouting-1.9.0.jar -de ../01_kicad/tracker.dsn -do ../01_kicad/tracker.ses -mp 40
python3 make_pcb.py ses
kicad-cli pcb drc ../01_kicad/tracker.kicad_pcb
```

## Altium

Altium Designer (21+) opens this design directly: *File → Import Wizard → KiCad Design Files*, select
`01_kicad/tracker.kicad_pro` — schematic, PCB, rules and stack-up are imported. A native `.PrjPcb` cannot be
generated outside Altium, so this is the supported path.

## Status

Rev A0 — pre-prototype. Read `04_docs/VERIFY_LIST.md` before ordering: several component values were set
without the vendor datasheet at hand (no web access on the build machine) and must be checked.
