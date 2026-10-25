# SPS-24G-01 — Verify-Before-Release Checklist

**SAMAY ELECTRONICS** · Rev A0. Items a qualified engineer must confirm before fabrication / energising.
Values below were set from datasheets and standard practice; each VERIFY must be signed off.

## Components / footprints
- [ ] **U2 MOC3063** — confirm `MOC3063SR2M` gull-wing SMD part matches the `SMDIP-6_W9.53mm_Clearance8mm`
      land, pins 1 anode / 2 cathode / 4,6 main terminals / 3,5 NC. Verify zero-cross variant (not MOC3061/3052).
- [ ] **Q1 BTA16-600B** — pinout A1(MT1)=pin1, A2(MT2)=pin2, Gate=pin3, isolated tab; derating & heatsink for
      the target lamp current.
- [ ] **PS1 HLK-PM01** — genuine Hi-Link; footprint `Converter_ACDC_Hi-Link_HLK-PMxx` pad map (AC 1,2 / DC 3,4).
- [ ] **F1** — TR5 land vs chosen fuse body (Littelfuse 382 / Bel); breaking capacity for the branch circuit.
- [ ] **MOV1 14D471K** — 14 mm disc fits the `Varistor_Disc_D16mm_P7.5mm` land (7.5 mm leads); energy rating.
- [ ] **NTC1 5D-9** — 9 mm disc fits `NTC_Disc_D11mm_P5mm` (5 mm leads); steady-state temperature.
- [ ] **CX1** — must be an **X2** safety cap (275 VAC), not an MLCC. **CS1** — **X1/400 VAC** film, not ceramic.
- [ ] **J1** — Phoenix MKDS-1,5/3-5.08 (or MX126-5.0) footprint and current/voltage rating for the lamp load.
- [ ] **RV1** — Bourns 3386P pinout (pin 2 = wiper) matches `Device:R_Potentiometer_Trim`.
- [ ] **LD2410B (J3)** — 5-pin 1.27 mm order OUT/TX/RX/GND/VCC; vertical mount mechanics and antenna clearance.

## Electrical
- [ ] Radar OUT (3.3 V) read reliably as logic HIGH by the 5 V ATtiny13A (VIH margin ~0.3 V) — add a pull-up or
      3.3 V level buffer if marginal across temperature.
- [ ] Opto LED current via R1 330 Ω (~11.5 mA) > IFT; and peak opto-output current < 1 A ITSM (ON AN-3004) with
      the 180 Ω gate resistor; raise RG1 to 360 Ω if a non-zero-cross opto is substituted.
- [ ] Snubber RS1/CS1 values for the actual load (LED driver vs resistive vs inductive).
- [ ] HLK-PM01 5 V rail headroom for radar 79 mA (bursty) + MCU + opto; bulk CB1 220 µF adequate.
- [ ] Minimum-load triac latching with the real LED lamp (add bleeder if it flickers).

## Layout / isolation
- [ ] Primary↔secondary ≥ 6 mm creepage — **met at ≥ 9.5 mm** (confirm on the fab panel; HIPOT 3 kVAC).
- [ ] Primary live-to-live routed creepage — **widen to ≥ 2.5 mm and/or conformal-coat** (currently 0.8 mm DRC).
- [ ] TO-220 / opto pin-pitch clearances accepted + coated (DRC_ERC_REPORT §clearance).
- [ ] No metal in the enclosure over the radar antenna; RF-transparent window.

## Firmware
- [ ] Power-on safe state (lamp OFF, Auto). Delay mapping 10 s–10 min across the trimmer.
- [ ] Debounce + long-press override. Radar-loss fail-safe (lamp OFF) and LED fault pattern.
- [ ] ISP lines shared with opto/LED/button do not misbehave during programming (program with mains OFF).

## Before ordering
- [ ] Fill LCSC columns in `SPS-24G-01_BOM_JLCPCB.csv`.
- [ ] Check JLCPCB CPL rotations (SOIC/DIP/SOT/module) in the 3D preview; set `ROT_FIX` in `make_cpl.py`.
- [ ] Specify 2-layer, 1.6 mm, 1 oz, ENIG, green; confirm the routed isolation slot in the Edge.Cuts gerber.
