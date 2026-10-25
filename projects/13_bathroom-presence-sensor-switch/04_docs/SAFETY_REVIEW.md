# SPS-24G-01 — Electrical Safety Review

**SAMAY ELECTRONICS** · Rev A0 · 2026-10-25

> This is an engineering safety review of a mains-connected design, not a certification. It identifies what
> the layout achieves, what must still be verified, and the standards that apply. **No unit may be energised
> on mains, sold, or installed until a qualified engineer has reviewed it and the product has passed formal
> type testing.** Working on 230 VAC is lethal — only trained personnel, with the board de-energised and
> discharged, and an isolation transformer on the bench.

---

## 1. Applicable standards (India + international)
| Area | Standard |
|---|---|
| Household automatic/electronic switches | **IEC 60669-1 / 60669-2-1**, BIS **IS 60669** |
| Electronic switches for appliances | IEC 61058-1 |
| Insulation coordination (creepage/clearance) | **IEC 60664-1** |
| Safety of SELV / isolation | IEC 61140, IEC 62368-1 (reference) |
| Surge / EMC | IEC 61000-4-5 (surge), CISPR 14 / IEC 55014 (emissions), 24 GHz ISM radar: FCC Part 15 / CE EN 300 440 (met by the HLK-LD2410B module) |
| Safety-critical components | Fuse IEC 60127, MOV IEC 61051, X-cap IEC 60384-14 (X2/Y), opto UL1577 / IEC 60747-5-5 |

---

## 2. Isolation architecture (the core safety feature)

Two galvanically separate domains:

- **PRIMARY (hazardous live):** J1 terminal, F1, MOV1, CX1, RB1, NTC1, the HLK-PM01 **input**, the MOC3063
  **output** (pins 4/6), Q1 triac, RG1, snubber RS1/CS1.
- **SECONDARY / SELV (safe to touch):** +5 V rail, ATtiny13A, LD2410B radar, button, LED, trimmer, ISP and
  config headers, the HLK-PM01 **output**, the MOC3063 **input** (pins 1/2).

They are placed on **opposite halves** of the board (primary = top strip, SELV = bottom strip) separated by a
**6 mm no-copper corridor** that runs the full width, reinforced by a **routed milling slot** (two segments,
Edge.Cuts). No copper net crosses the corridor. The only two components bridging it are:

| Device | Isolation rating | Role |
|---|---|---|
| **HLK-PM01** | 4 kVAC reinforced (AC-DC) | Powers the SELV side from mains |
| **MOC3063** | 7.5 kVrms (opto) | Carries the MCU's ON/OFF command to the triac gate |

Both are the **reinforced/double-insulation barrier** between live mains and the user-touchable SELV
electronics. This is the primary protection against electric shock.

### Enforced separation (from the layout script `isolation_check`)
- Minimum **primary-pad ↔ SELV-pad centre distance: ≥ 7.0 mm** (target ≥ 6 mm creepage edge-to-edge → met,
  because the 6 mm corridor keepout forbids any copper between the domains).
- **No primary-net copper exists below the HV/SELV boundary**, and no SELV copper above it (verified
  automatically every build; the check fails the build otherwise).
- Corridor keep-out is a DRC rule area (no tracks / vias / pours), so the autorouter cannot bridge it.

**Requirement to confirm at test:** HIPOT **3 kVAC, 1 min, primary-to-secondary**, leakage < 5 mA, no
breakdown. The HLK-PM01 and MOC3063 ratings support this; the PCB barrier (≥ 6 mm + slot) supports ≥ 6 mm
creepage which exceeds the IEC 60664-1 reinforced requirement for 250 V working (≈ 5.0 mm, PD2, group IIIb).

---

## 3. Creepage & clearance analysis

### 3.1 Primary ↔ Secondary (reinforced) — **PASS by design**
| Metric | Required (250 V, reinforced, PD2) | This board |
|---|---|---|
| Clearance | ≈ 3.0 mm | ≥ 6 mm (corridor) ✔ |
| Creepage | ≈ 5.0 mm | ≥ 6 mm (corridor) + slot ✔ |

### 3.2 Primary live-to-live (L / N / LAMP — functional/basic) — **REVIEW + COATING**
For 250 V working, basic insulation, PD2, material group IIIb: clearance ≈ 1.5 mm, **creepage ≈ 2.5 mm**.

The limiting spots are **component pin pitches**, which are fixed by the packages and *cannot* be widened:

| Location | Spacing | Note |
|---|---|---|
| BTA16 TO-220 MT1–MT2–Gate | 2.54 mm pitch → ~1.0 mm copper gap | Inherent to TO-220. Gate–MT1 carry the gate trigger; MT1–MT2 see mains only when OFF. |
| MOC3063 output pins 4–6 | 2.54 mm pitch → ~1.0 mm gap | Inherent to DIP. |
| HLK-PM01 AC pins 1–2 | 5.0 mm → ~3 mm gap | OK |
| J1 terminal L–N–LAMP | 5.08 mm pitch | Terminal body provides creepage; OK |
| Routed L vs N/LAMP traces | ≥ 0.8 mm (DRC rule) | **Below 2.5 mm in places** |

**Mitigations (mandatory for production):**
1. Apply **conformal coating** (acrylic/urethane) to the primary side — IEC 60664-3 allows reduced spacing
   under type-2 coating.
2. Manually widen routed L↔N / L↔LAMP spacing to ≥ 2.5 mm where board area allows (the current board is
   autorouted at 0.8 mm functional clearance; a HV hand-route pass is a required follow-up).
3. Optionally add **slots between the BTA16 pins** and under the opto to raise pin-pin creepage.
4. Keep pollution degree 2 (sealed bathroom enclosure, IP44+).

---

## 4. Component-level protection review
| Part | Function | Verify |
|---|---|---|
| **F1** 500 mA T, 250 V, TR5 | Fault/overcurrent — protects PSU & triac, isolates a shorted board | Breaking capacity ≥ prospective fault current (≥ 1.5 kA for a branch circuit); time-lag so it survives lamp inrush |
| **MOV1** 14D471K (S14K300) | Surge clamp L-N, 6 kV/3 kA test | Energy rating for the install; consider a **thermally-fused MOV** for end-of-life safety (MOVs can fail short/overheat) |
| **NTC1** 5D-9 | Inrush limiter into the PSU cap | In series with the HLK-PM01 only (not the lamp). Hot-restart derating OK for a bathroom |
| **CX1** 100 nF **X2** 275 VAC | Differential EMI | Must be an **X2 safety cap**, not a general MLCC |
| **RB1** 1 MΩ | Discharges CX1 when unplugged | < 1 s discharge; rated ≥ 350 V working |
| **Q1** BTA16-600B | Load switch | Derate to ~2 A without heatsink; snubber fitted; isolated tab (TO-220 ins.) |
| **RG1/RS1/CS1** | Gate + snubber | RS1 ≥ 2 W; CS1 must be an **X1/400 VAC film** cap, not ceramic |
| **PS1** HLK-PM01 | Isolated SELV supply | Genuine Hi-Link part; reinforced isolation is the main barrier |
| **U2** MOC3063 | Isolated gate drive | Zero-cross type; per ON AN-3004 verify peak opto current < 1 A ITSM (180 Ω gate R is acceptable for a zero-cross opto; raise to 360 Ω if substituting a random-phase opto) |

---

## 5. Protective-earth / enclosure
This is a **Class II (double-insulated)** design — there is **no protective earth** on the PCB. That places
the full shock-protection burden on the primary↔secondary isolation (Section 2). The enclosure must be
all-insulating (FR-ABS/PC), with no exposed metal reachable by the user, and the sensor window must be
RF-transparent plastic with no metallised coating.

---

## 6. Required type tests before release
1. **HIPOT** 3 kVAC 1 min primary↔secondary (and to any accessible metal) — no breakdown, < 5 mA.
2. **Insulation resistance** > 2 MΩ at 500 VDC primary↔secondary.
3. **Creepage/clearance** physical measurement vs IEC 60664-1, with coating accounted per 60664-3.
4. **Surge** IEC 61000-4-5: 2 kV L-N, 4 kV L-PE (if applicable), 5 strikes each polarity — survives.
5. **Inrush & fuse coordination**: confirm F1 does not nuisance-trip on cold lamp inrush; confirm a bolted
   output fault opens F1 without the triac/PCB catching fire.
6. **Thermal**: full-load triac + PSU temperature rise under worst-case ambient (sealed box, 40 °C).
7. **EMC**: conducted/radiated emissions (CISPR 14); the 24 GHz radar uses its module's existing
   FCC/CE certification (do not modify the antenna).
8. **Ball-pressure / glow-wire** on the enclosure and PCB per IS 60669.

---

## 7. Open items / known limitations (this revision)
- [ ] HV primary routed-trace creepage auto-routed at 0.8 mm — **needs a manual HV routing pass to ≥ 2.5 mm
      and/or conformal coating** (Section 3.2).
- [ ] MOV is not thermally fused — consider TMOV or series thermal fuse.
- [ ] No in-rush/short-circuit test performed (simulation/paper only).
- [ ] Firmware fail-safe behaviour (radar loss → lamp OFF) must be validated on hardware.
- [ ] Minimum-load behaviour with real LED lamps must be bench-verified (triac latching).
- [ ] BIS/IEC certification not performed.

**Bottom line:** the isolation barrier (the thing that keeps users safe) is designed correctly and
verifiably — ≥ 6 mm creepage, reinforced-rated bridging parts, slot, no copper crossing. The primary-side
*internal* spacing and the formal test campaign are the outstanding work before this can be a product.
