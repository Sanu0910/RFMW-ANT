# CRL-TRK-2W-L1 - "Samay Track 2W Lite": low-cost Cat-1 / 2G two-wheeler tracker

The consumer variant of CRL-TRK-2W-01, from `../premium/07_marketing/BUSINESS_PLAN_NOTES.md` section 5.
**60 x 45 mm, 2-layer, single-sided SMT, about Rs 1,440 hardware at 1 000 pcs**, same outline, holes and enclosure as the full version.

Quectel EC200U-CN Cat-1 bis + GSM (runs the firmware, no separate MCU) · Quectel L76K GPS/BDS/GLONASS · LIS3DH ·
XL1509 40 V buck · MCP73831 + 300 mAh LiPo with PMOS power path · MFF2 eSIM · IGN input · relay output

> **Not ready for fabrication.** The EC200U land pattern is a parametric reconstruction, because the vendor
> drawing could not be downloaded on the build machine. Replace it first: see `04_docs/VERIFY_LIST.md` #1.

## Folders

| Folder | Content |
|---|---|
| `01_kicad/` | KiCad 9 project `tracker_lite.kicad_pro`: hierarchical schematic (5 sheets), 2-layer PCB, project library (`tracker_lite.kicad_sym`, `lite.pretty`), envelope STEPs in `3d/` |
| `02_python/` | **Source of truth.** `design.py` (circuit), `make_lib.py`, `make_schematic.py`, `make_pcb.py` (placement, RF lines, fan-out, pours), `route_all.sh`, `patch_route.py` (A* finisher), `make_bom.py` (engineering / JLC / costed BOM), `make_cpl.py`, `make_pins.py`, `make_models.py`, `rf_calc.py` (CPWG) |
| `03_fab/` | Gerbers + drill (`CRL-TRK-2W-L1_gerbers.zip` and `gerbers/`), JLC pick-and-place (`_CPL_JLCPCB.csv`), assembly BOM (JLC format), engineering BOM, costed BOM |
| `04_docs/` | `DESIGN_REPORT.md` (Lite vs. full, power path and budget, RF, PCB, protection, test), `BOM.md` (with cost roll-up), `VERIFY_LIST.md`, `DRC_ERC_REPORT.md`, schematic PDF, assembly drawing |
| `05_renders/` | 3D STEP of the assembled board, top / bottom / iso renders, copper-layer plot |
| `06_firmware/` | `board_pins.h`: EC200U QuecOpen pin map generated from the netlist |

## Regenerate

```bash
cd 02_python
python3 make_lib.py && python3 make_schematic.py && python3 make_bom.py && python3 make_pins.py && python3 make_models.py
./route_all.sh   # KiCad 9 python (tools/install_kicad_mcp.sh) + Freerouting 1.9 + Xvfb: place, route, pour, 3D,
                 # then DRC-driven finishing (A* patcher, dangling GND clean-up, pour-fragment ties)
./make_fab.sh    # Gerbers, drill, CPL, STEP, renders, assembly + schematic PDFs
```

## Status

Rev A0, pre-prototype. Layout complete: **ERC 0, DRC 0 errors / 0 unconnected, schematic-PCB parity clean** (6 cosmetic silk
warnings). Read `04_docs/VERIFY_LIST.md` before ordering: the EC200U land pattern must be replaced with Quectel's drawing first.
