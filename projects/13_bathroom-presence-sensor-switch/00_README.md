# SPS-24G-01 — Smart Presence Sensor Switch

**SAMAY ELECTRONICS** · 24 GHz mmWave automatic light switch · standalone (no Wi-Fi / no BLE) · Rev A0

A production-intent PCB design that replaces a wall switch in a standard Indian 86 × 86 mm modular box.
An HLK-LD2410B 24 GHz radar detects a person (moving *or* still); an ATtiny13A switches the lamp through a
zero-cross opto-triac + BTA16-600B with an adjustable 10 s–10 min off-delay. 70 × 56 mm, 2-layer FR-4,
mains-isolated.

> ⚠️ **MAINS DESIGN — NOT A CERTIFIED PRODUCT.** Do not energise or sell without a qualified engineer's
> review and formal type testing. See `04_docs/SAFETY_REVIEW.md`.

## What is where
| Folder | Contents |
|---|---|
| `01_kicad/` | KiCad 9 project: `bps_switch.kicad_sch` (4-sheet schematic), `bps_switch.kicad_pcb`, `bps.pretty/` custom footprints, `bps_switch.kicad_sym`, `3d/` STEP envelopes |
| `02_python/` | **Single source of truth** `design.py` + generators (`make_lib`, `make_schematic`, `make_pcb`, `make_bom`, `make_cpl`, `make_models`) and build scripts (`build_board.sh`, `make_fab.sh`) |
| `03_fab/` | **Gerbers** (`*_gerbers.zip` + `gerbers/`), **drill**, **pick-and-place** (`*_CPL_JLCPCB.csv`), **BOM** (engineering / JLCPCB / costed) |
| `04_docs/` | **DATASHEET**, DESIGN_REPORT, **SAFETY_REVIEW**, DRC_ERC_REPORT, BOM.md, APPLICATION_NOTE, VERIFY_LIST, schematic & assembly **PDFs** |
| `05_renders/` | 3D **STEP** of the assembled board + top/bottom/iso **PNG** renders |
| `06_firmware/` | ATtiny13A pin map (`board_pins.h`) + reference firmware (`main.c`) |

## Status (verified in this build)
| Item | Status |
|---|---|
| Schematic ERC | **0 errors / 0 warnings** |
| PCB routed | **100 % — 0 unconnected, schematic parity clean** |
| Isolation | primary↔secondary ≥ **9.5 mm** creepage; 6 mm corridor + routed slot; no copper crosses |
| DRC | 0 unconnected; 4 package-inherent clearances (documented); 53 silkscreen cosmetic |
| Fab outputs | gerbers, drill, CPL, STEP, renders, assembly + schematic PDF — all generated |
| Open items | HV primary-trace creepage to ≥ 2.5 mm / conformal coating; firmware bench test; type certification — see SAFETY_REVIEW §7 |

## Quick start
```bash
cd 02_python
python3 make_lib.py && python3 make_schematic.py      # libraries + ERC-clean schematic
./build_board.sh                                      # place -> route -> finish -> patch (needs KiCad 9 + Freerouting)
/home/user/RFMW-ANT/tools/kicad-python-chroot.sh "$PWD/make_pcb.py" tie   # unify GND pour
python3 make_bom.py && python3 make_models.py && \
  /home/user/RFMW-ANT/tools/kicad-python-chroot.sh "$PWD/make_pcb.py" models && ./make_fab.sh
```

## Key specs
- Input 85–265 VAC 50/60 Hz · isolated 5 V (HLK-PM01) · TRIAC load output (≤ 2 A no heatsink, ≤ 6 A with sink)
- 24 GHz radar, range 0.75–6 m, ±60°, detects micro-motion (stays on when still)
- Off-delay 10 s – 10 min (trimmer) · manual override button · status LED · AVR ISP header
- 70 × 56 mm, 2-layer 1.6 mm FR-4, 1 oz, ENIG, fits the 86 × 86 modular box
