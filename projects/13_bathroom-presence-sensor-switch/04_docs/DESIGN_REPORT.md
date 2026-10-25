# SPS-24G-01 — Design Report

**SAMAY ELECTRONICS** · Smart Presence Sensor Switch · Rev A0 · 2026-10-25

## 1. Requirement → design mapping
| Requirement | Implementation |
|---|---|
| 24 GHz presence radar, OUT high = human | HLK-LD2410B on vertical 5-pin header J3 → MCU PB4 |
| Standalone, no Wi-Fi/BLE | ATtiny13A local control only |
| Light ON on entry, stays ON when still | mmWave micro-motion detection (not PIR) |
| Adjustable OFF delay | 10 kΩ trimmer RV1 → ADC3, mapped 10 s…10 min in firmware |
| Manual override + status LED | SW1 (PB2) + D1 (PB1) |
| 85–265 VAC input, isolated 5 V | HLK-PM01 |
| Input protection | F1 (T500 mA), MOV1 (14D471K), NTC1 (5D-9), CX1 (100 nF X2), RB1 (1 MΩ bleeder) |
| Silent TRIAC load control | MOC3063 zero-cross opto + BTA16-600B, RG1 180 Ω gate, RS1/CS1 snubber |
| HV/LV separation, ≥6 mm creepage, ≥3 mm clearance, slot, HV marking | horizontal split + 6 mm corridor + routed slot + silk warnings |
| Fits 86×86 modular box | 70×56 mm board |
| ISP 6-pin | J2 (standard AVR) |
| SMD where possible | all SELV passives SMD (0603/0805); mains parts are THT by necessity |

## 2. Architecture
- **Single 5 V rail.** The LD2410B, ATtiny13A and MOC3063 LED all run at 5 V — no LDO needed. The radar's
  3.3 V OUT is read as a logic HIGH by the 5 V MCU (VIH = 0.6·Vcc = 3.0 V < 3.3 V, ~0.3 V margin; documented).
- **Zero-cross switching.** The MOC3063 only fires near the mains zero crossing → silent, low-EMI, long triac
  life. A snubber (RS1 100 Ω + CS1 10 nF) handles dv/dt for mildly inductive/LED loads.
- **Neutral-required.** The HLK-PM01 is powered from L+N so the electronics work with the lamp off.
- **Pin budget (ATtiny13A, 6 I/O + RESET):** PB4=radar, PB3=delay pot (ADC3), PB0=opto drive (also MOSI),
  PB1=LED (also MISO), PB2=button (also SCK, 1 kΩ series so it doesn't fight ISP), PB5=RESET/ISP.

## 3. Board / stack-up
- 70 × 56 mm, 2-layer FR-4, 1.6 mm, 1 oz, ENIG, green.
- Top = signals + SELV GND pour (bottom half only); Bottom = SELV GND plane (bottom half only).
- Primary side carries no ground pour (mains uses wide discrete traces).
- Isolation corridor: 6 mm no-copper band (y = 28…34 mm) with a two-segment Edge.Cuts slot.

### Why not 45 × 45 mm?
The mandated through-hole mains parts dominate the area: HLK-PM01 (37 × 23 mm courtyard), 14 mm MOV
(~17 × 17), BTA16 TO-220, 5.08 mm 3-pole terminal, 2 W snubber resistor, X2/X1 film caps. Their combined
footprint (~1000 mm²) plus the mandatory ≥ 6 mm isolation corridor cannot fit inside 45 × 45 mm (2025 mm²)
with routable spacing. 70 × 56 mm is the compact result that still fits the 86 × 86 box (internal ≈ 75 mm).
A ~50 × 50 mm version is feasible by substituting an SMD 3 W supply, a 10 mm MOV and a surface-mount triac —
listed as a cost/size-down path, but it departs from the specified BOM.

## 4. Toolchain & reproducibility
Everything is generated from one source of truth, `02_python/design.py`:
- `make_lib.py` → MOC3063 symbol + 4 custom footprints (TR5 fuse, 14 mm MOV disc, 9 mm NTC disc, LD2410B header).
- `make_schematic.py` → hierarchical KiCad 9 schematic (4 sheets). **ERC: 0 errors, 0 warnings.**
- `make_pcb.py` → placement (region-constrained greedy, isolation-aware), netclasses, corridor & antenna
  keep-outs, GND fan-out, pours, stitching; exports DSN for Freerouting; imports SES; `patch` = A* finisher.
- `make_bom.py` / `make_cpl.py` → BOMs and pick-and-place.
- `make_models.py` → STEP envelope for the LD2410B.
- `route_all.sh` → one-shot place→route→finish.

Run order: `make_lib.py` → `make_schematic.py` → `route_all.sh` → `make_bom.py` → fab exports.

## 5. Verification performed
- **ERC** clean (0/0).
- **Isolation check** (custom, every build): min primary↔SELV pad distance ≥ 7 mm; zero primary copper in
  the corridor/SELV region; build fails otherwise.
- **DRC** (KiCad, schematic parity): parity clean; see `DRC_ERC_REPORT.md` for the routed-board status and
  the documented package-pin clearance notes.
- Netlist self-check: no single-pin nets.

## 6. Known limitations / follow-ups
See `SAFETY_REVIEW.md` §7. Headlines: HV primary-side routed spacing needs a manual pass to ≥ 2.5 mm +
conformal coating; MOV not thermally fused; firmware fail-safe and minimum-LED-load latching need bench
validation; no formal type testing yet. The triac gate trace (RG1) is longer than ideal in this autoplaced
revision — acceptable for 50/60 Hz gate drive but worth shortening in a layout revision.
