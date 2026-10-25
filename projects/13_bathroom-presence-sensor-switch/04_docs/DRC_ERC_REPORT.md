# SPS-24G-01 — ERC / DRC Report

**SAMAY ELECTRONICS** · Rev A0 · 2026-10-25 · KiCad 9.0.9

## ERC (schematic)
`kicad-cli sch erc` — **0 errors, 0 warnings.** Every pin has an explicit net; no power/driver conflicts;
no single-pin nets (checked in `design.py`).

## DRC (PCB, with schematic parity)
`kicad-cli pcb drc --schematic-parity`

| Metric | Result |
|---|---|
| **Unconnected items** | **0** ✔ |
| **Schematic parity** | **0** ✔ (board netlist == schematic) |
| Copper **clearance** | 4 — all package-inherent (see below) |
| Silkscreen (overlap / edge / over-copper / text size) | 53 — cosmetic (see below) |
| Board | 70 × 56 mm, 2-layer, 1822 track segments, 69 vias |
| Isolation (custom check) | min primary↔SELV pad distance **9.53 mm** (≥ 6 mm required) ✔; zero primary copper in the corridor/SELV region ✔ |

### The 4 clearance items — accepted, package-inherent
All four are between pins **of a single mains component**, fixed by the package pin pitch and impossible to
widen on the PCB:
| Pins | Spacing | Why accepted |
|---|---|---|
| Q1 BTA16 MT1↔MT2 (ACL_F↔LAMP) | TO-220 2.54 mm pitch, ~0.63 mm copper gap | Standard TO-220; MT1–MT2 see mains only when the lamp is OFF |
| Q1 BTA16 MT2↔Gate (LAMP↔TRIAC_G) | TO-220 2.54 mm pitch | Gate is driven relative to MT1; standard |
| U2 MOC3063 pin4↔pin5(NC) | SMD-DIP 2.54 mm pitch | Pin 5 is a **no-connect** (floating) — no live-live risk |
| U2 MOC3063 pin5(NC)↔pin6 | SMD-DIP 2.54 mm pitch | as above |

These are the same package limits every through-hole TRIAC light switch has. They are handled in production
by **conformal coating** of the primary side (IEC 60664-3) and by the components' own voltage ratings.
See `SAFETY_REVIEW.md` §3.2. The safety-critical **primary↔secondary** creepage is ≥ 9.5 mm (the opto's
8 mm land + the 6 mm corridor), well above requirement.

### The 53 silkscreen items — cosmetic
Reference designators sit on the **F.Fab** assembly layer; the silk layer keeps part outlines, pin-1 marks,
the HIGH-VOLTAGE / SELV warnings and the L/N/LAMP legend. The overlaps are between part outlines and legends
in the dense areas and a few sub-0.6 mm module labels. They do **not** affect copper, isolation or function
and are trimmed/merged at fabrication (JLCPCB et al. accept them). A production spin would hand-tidy the silk.

## Isolation / safety DRC summary
- No net crosses the 6 mm isolation corridor (enforced by a DRC keep-out rule area + the `isolation_check`
  build gate).
- Primary↔secondary creepage ≥ 9.5 mm (opto land 8 mm + corridor 6 mm) — exceeds the IEC 60664-1 reinforced
  requirement for 250 V.
- Primary live-to-live routed-trace clearance ≥ 0.8 mm (DRC rule); package pins as tabulated above;
  conformal coating required — see `SAFETY_REVIEW.md`.

## Reproduce
```
cd 02_python
python3 make_lib.py && python3 make_schematic.py       # ERC-clean schematic
./build_board.sh                                       # place -> Freerouting -> finish -> patch
make_pcb.py tie                                        # unify GND pour (if needed)
python3 make_bom.py && python3 make_models.py
make_pcb.py models && ./make_fab.sh                    # gerbers, drill, CPL, STEP, renders, PDFs
```
DRC: `kicad-cli pcb drc --schematic-parity 01_kicad/bps_switch.kicad_pcb`
