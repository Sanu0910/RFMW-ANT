# NOVA-RF1 PCB build status

Target: a full datasheet-accurate, routable, fab-ready 4-layer board. Built in stages from
`02_python/design.py` (netlist) via `02_python/pinmap.py` (footprint + pad->net engine) and
`02_python/make_pcb.py` (board generator, in progress).

## Pad->net resolution engine (`pinmap.py`)
Every part's pad-number -> net mapping comes from one of three mechanisms, so no pad numbers are
guessed:
1. **Official KiCad symbol** (pin NAME -> pad NUMBER, maintained by KiCad): `U1` STM32WB55RGVx,
   `U9` TPS22917, `U10` USBLC6-2SC6.
2. **Authored standard tables**: dual op-amp VSSOP-8 (`DA3`,`DA4` LMV358), comparator SC-70-5
   (`DA5` LMV331), SOT-23 MOSFETs, USB-C receptacle.
3. **Direct numeric / custom named pads**: passives, crystals, headers, FFCs, and custom
   footprints whose pads are named to match the design pins.

Current coverage: **88 parts, 0 unresolved, 0 pending** — all pinouts resolved.

## Datasheet pinouts transcribed (2026-10-24)
All eight chips' exact pads were read from the uploaded datasheets and added to `pinmap.AUTHORED`,
with the mandatory support components added to `design.py`:

| Ref | Part | Package | Source | Support added |
|---|---|---|---|---|
| U2 | CC1101RGPR | QFN-20 (EP=21) | SWRS061I Table 19 | DCOUPL cap |
| U3 | ST25R3916-AQWT | UFQFPN-32 (EP=33) | DS12484 Fig.4 | I2C_EN=GND, AGDC cap |
| U6 | BQ25896 | WQFN-24 (EP=25) | SLUSC76C | buck inductor, bootstrap, REGN cap, ILIM R, TS divider, CE=GND |
| U7 | BQ27220 | DSBGA-9 YZF | SLUSCB7A | VDD cap, GPOUT pull-up, BIN pull-down |
| U8, U8B | LM3281 | DSBGA-6 YFQ | SNVSA38 | MODE=VIN |
| DA7 | LP5562 | DSBGA-12 YQE | SNVS820B | ADDR_SEL0/1=GND (custom 3x4 ball footprint) |
| DA8 | RS3221-3.3 | SOT-23-3 | RS3221 RevA.3 | — |

Validation: all 88 parts cross-check clean (every pad->net lands on a real footprint pad).
Multi-pad supply/ground nets (e.g. CC1101 AVDD x4, ST25R3916 VDD x8 / VSS x6) are mapped.

## Done, in this order (project-07 flow)
- [x] Netlist (`design.py`), verified vs the official STM32WB55 symbol (power/SMPS/osc complete)
- [x] KiCad schematic + ERC (0 errors), netlist export = 108 nets
- [x] Footprint library map + pad->net resolution engine (`pinmap.py`), 69/77 resolved
- [x] Custom footprints (`01_kicad/nova-rf1.pretty`, `make_footprints.py`) for the mechanical/RF
      parts (coil, loop/chip antennas, iButton pads, speaker, vibro, battery, display FFC, TSOP,
      Tag-Connect, balun, RF filter, RF switch, RGB LED, microSD). All 69 resolved parts now
      pass a pad-name cross-check: every net lands on a real footprint pad (0 mismatches).
- [x] Datasheet pinouts for all 8 chips (transcribed from uploaded PDFs, + support parts)
- [x] `make_pcb.py`: load all 87 footprints, assign nets (178 nets), initial grouped placement
- [ ] Board outline + real floor-plan (RF blocks by antennas, power cluster, MCU central)
- [ ] RF matching (CC1101 50 ohm + LC, NFC 13.56 MHz, 125 kHz LC) and controlled-impedance stackup
- [ ] Route (4-layer), zones, DRC clean
- [ ] Gerbers, drill, CPL, costed BOM, 3D render

## Routing (KiCadRoutingTools, 2026-10-24)
Compact 110x66mm 4-layer, two-sided. GND plane poured on In1.Cu; autorouted with
rip-up/reroute. Result: **104 of 105 nets routed** (2935 segments, 520 vias) ->
`01_kicad/nova-rf1-routed.kicad_pcb`.

Remaining to DRC-clean / fab-ready (the last mile):
- **LSE_OUT open (1 net):** the 32.768kHz LSE crystal Y2 is not adjacent to the MCU, so
  the net is walled in. Fix = place crystals (Y1/Y2) touching U1's OSC pins, then re-route.
- **GND plane stitching:** ~60 GND pads not yet tapped to the pour; needs a GND return-via
  stitch pass.
- **Fab rules relaxed** to fit the compact board: vias 0.25mm, drills 0.15mm, clearance 0.1mm
  (HDI-class). For standard low-cost fab, grow the board (~130x75mm) and re-route at 0.2mm.
- 4 clearance DRC violations at the relaxed floor.

## Final compact route (NOVA-RF1, 100x60mm, 2026-10-24)
Two-sided 4-layer. GND plane on In1.Cu + **+3V3 plane on In2.Cu**. Crystals clustered under
their ICs. **103 of 104 nets routed** (2965 segments, 530 vias), silkscreen added, fab package
exported (`03_fab/NOVA-RF1_gerbers.zip`, `NOVA-RF1_CPL.csv`, `NOVA-RF1_BOM_*.csv`).

Remaining for a 100%-clean sign-off:
- **NFC_CS (1 net):** walled in on the dense board - with both inner layers used as planes,
  signals have only top+bottom; this last chip-select needs a short manual trace in KiCad (or
  ~5mm more board width). Normal final-1% hand-finish.
- **GND via stitching:** ~44 GND pads to tap to the pour.
- 4 clearance DRC violations at the 0.1mm floor.
Component cost ~$34.75/board; ~$55-60 built at low volume (see NOVA-RF1_product.pdf).

## Elegant-outline corrected board (2026-10-24)
Rounded handheld outline (R9 top / R18 bottom grip), netlist corrected (3 bugs fixed per
VERIFICATION.md). GND + +3V3 planes poured. **101/104 nets routed** (3051 segments, 554 vias) ->
`01_kicad/nova-rf1-routed.kicad_pcb`, fab package re-exported. 3 signals (I2C_PWR_SCL, USB_DP,
VIBRO) remain for manual trace - normal final hand-finish on a dense 2-plane 4-layer board
(only top+bottom free for signals). Plus GND via-stitching and a few 0.1mm clearance nits.
