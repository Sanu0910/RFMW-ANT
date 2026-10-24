# CRL-MT1 — fabrication notes

Original firmware-compatible multi-tool RF board. **Not a Flipper Zero** — own outline,
silkscreen and name; no trademark, logo or mascot. Read `ARCHITECTURE.md` for the legal /
RF-certification boundaries before any build or sale.

## Board
| Item | Value |
|---|---|
| Size | 100 × 60 mm |
| Layers | 4 (signal / GND / PWR / signal) |
| Thickness | 1.6 mm |
| Copper | 1 oz outer, 0.5 oz inner |
| Finish | ENIG (fine-pitch QFN/BGA) |
| Soldermask | both sides |
| Silkscreen | both sides (white) |
| Min trace / space | 0.1 mm |
| Min via | 0.25 mm pad / 0.15 mm drill |
| Assembly | double-sided SMT (ICs/connectors top, passives bottom) |

These rules are within JLCPCB / PCBWay 4-layer advanced capability. If a cheaper standard
process is required (0.2 mm space, 0.3 mm drill), grow the board to ~120 × 70 mm and re-route.

## Stackup (JLC04161H-7628 or equivalent)
```
L1  Signal (F.Cu)      1 oz   ── components, RF, short signals
    prepreg 7628        ~0.2 mm
L2  GND plane (In1.Cu)  0.5 oz ── solid reference for RF + digital return
    core               ~1.065 mm
L3  PWR (In2.Cu)        0.5 oz ── +3V3 / VSYS / power distribution
    prepreg 7628        ~0.2 mm
L4  Signal (B.Cu)      1 oz   ── passives, secondary routing
```
Controlled impedance: 50 Ω single-ended on L1 over L2 for the RF nets
(CC1101 SUBG, BLE, NFC) — verify microstrip width with the final stackup before release.

## Fab files (`../03_fab/`)
| File | Purpose |
|---|---|
| `CRL-MT1_gerbers.zip` | Gerber X2 set (all copper, mask, paste, silk, Edge.Cuts) + Excellon drill + map |
| `CRL-MT1_CPL.csv` | pick-and-place (centroid), both sides |
| `CRL-MT1_BOM_JLCPCB.csv` | grouped assembly BOM (fill the LCSC column) |
| `BOM_engineering.csv` | full engineering BOM (per-ref) |

## Assembly notes
- Battery pack is **external**, wired to `X10` (BAT / NTC / GND) — not on the board.
- QFN/BGA exposed pads (U1 STM32WB55, U3 ST25R3916, U6 BQ25896) tie to GND; add thermal vias.
- RF: keep the CC1101 balun + LC and the NFC 13.56 MHz matching network tight; re-tune to the
  final antennas in a simulator (openEMS / Hertzon).
- Crystals (Y1/Y2, ZQ1, ZQ3) are placed directly under their ICs — keep the short loops.

## Before ordering
1. Open in KiCad, run DRC against the fab's rule set.
2. Confirm the fab supports 0.15 mm drills / 0.1 mm space (or re-route to its floor).
3. Radios (CC1101 sub-GHz, BLE) need type approval (FCC / CE / WPC-ETA + BIS in India) before sale.
