# CRL-MT1 PCB build status

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

Current coverage: **69 parts fully resolved, 0 unresolved, 8 pending** datasheet uploads.

## Pending — datasheets needed for exact pads
These eight chips have **no KiCad symbol** and this container cannot reach ti.com / st.com, so
their exact pad numbers must come from the datasheets (upload the PDFs):

| Ref | Part | Package | Why |
|---|---|---|---|
| U2 | CC1101RGPR | QFN-20 | sub-GHz radio — pads must be exact |
| U3 | ST25R3916-AQWT | QFN-32 | 13.56 MHz NFC reader |
| U6 | BQ25896 | WQFN-24 | charger |
| U7 | BQ27220 | DSBGA-9 | fuel gauge |
| U8, U8B | LM3281 | DSBGA-5 | 3V3 bucks |
| DA7 | LP5562 | DSBGA-12 | RGB LED driver |
| DA8 | RS3221-3.3 | DFN-6 | LDO |

Once uploaded, each pinout is transcribed into `pinmap.AUTHORED` and the part leaves `PENDING`.

## Done, in this order (project-07 flow)
- [x] Netlist (`design.py`), verified vs the official STM32WB55 symbol (power/SMPS/osc complete)
- [x] KiCad schematic + ERC (0 errors), netlist export = 108 nets
- [x] Footprint library map + pad->net resolution engine (`pinmap.py`), 69/77 resolved
- [ ] Custom footprints for the mechanical/RF parts (coil, loop/chip antennas, iButton pads,
      speaker, vibro, battery, display FFC, TSOP, Tag-Connect, balun, RF filter, RF switch)
- [ ] Datasheet pinouts for the 8 pending chips
- [ ] `make_pcb.py`: load footprints, assign nets, place, board outline
- [ ] RF matching (CC1101 50 ohm + LC, NFC 13.56 MHz, 125 kHz LC) and controlled-impedance stackup
- [ ] Route (4-layer), zones, DRC clean
- [ ] Gerbers, drill, CPL, costed BOM, 3D render
