# SPS-24G-01 — Smart Presence Sensor Switch
### 24 GHz mmWave Automatic Light Switch · Standalone (No Wi-Fi / No Bluetooth)

**SAMAY ELECTRONICS** · Preliminary Datasheet · Rev A0 · 2026-10-25

> ⚠️ **MAINS VOLTAGE PRODUCT.** This datasheet describes an engineering design. The board carries
> 85–265 VAC on its primary side. It must be reviewed by a qualified engineer and type-tested
> (IEC 60669 / IEC 61058, BIS IS 60669, creepage/clearance per IEC 60664-1, HIPOT, EMC) before any
> unit is energised or sold. See `SAFETY_REVIEW.md`.

---

## 1. General Description

The **SPS-24G-01** is a self-contained automatic light switch that replaces a standard wall switch in an
Indian 86 × 86 mm modular box. A **24 GHz millimetre-wave radar** (Hi-Link HLK-LD2410B) detects a human —
moving *or* completely still — and an on-board **ATtiny13A** microcontroller switches the lamp through a
**zero-cross opto-triac + BTA16-600B triac**. When the room empties, an adjustable timer (10 s … 10 min)
turns the lamp off automatically. No app, no cloud, no radio pairing — it works out of the box.

Unlike PIR switches, the mmWave radar keeps the light **on while a person sits or stands still** (e.g. on a
toilet, in a shower), eliminating the classic "lights-off-while-I'm-not-moving" problem. The radar also sees
**through the plastic front cover**, so there is no visible lens.

### Key Features
- 24 GHz FMCW presence radar; detects motion and micro-motion (breathing), range up to 6 m, ±60° coverage.
- Universal mains input **85–265 VAC, 50/60 Hz** via isolated HLK-PM01 5 V supply.
- Silent **zero-cross TRIAC** switching (no relay click, long life, low EMI).
- Adjustable OFF delay **10 s – 10 min** (on-board trimmer).
- **Manual override** button (Auto / Forced-ON / Forced-OFF) and a status/fault LED.
- Reinforced **primary↔secondary isolation** (HLK-PM01 + 7.5 kVrms opto), ≥ 6 mm creepage barrier + routed slot.
- Input protection: slow-blow fuse, MOV surge clamp, NTC inrush limiter, X2 EMI cap + bleeder.
- 70 × 56 mm 2-layer FR-4, fits the standard 86 × 86 modular back box.

---

## 2. Absolute Maximum Ratings
*(Stresses beyond these may cause permanent damage. Not continuous operating conditions.)*

| Parameter | Symbol | Min | Max | Unit |
|---|---|---|---|---|
| Mains input voltage | V_AC | — | 265 | VAC rms |
| Mains frequency | f | 45 | 65 | Hz |
| Triac repetitive off-state voltage (BTA16-600B) | V_DRM | — | 600 | V |
| Load current through triac (with adequate heatsink) | I_T(RMS) | — | 16 | A |
| Load current, **no heatsink** (this board) | I_T | — | ~2 | A |
| Fuse rating (F1) | — | — | 0.5 (T) | A |
| MCU / logic supply | +5V | -0.3 | 5.5 | V |
| Operating ambient | T_A | -10 | +55 | °C |
| Storage temperature | T_STG | -40 | +85 | °C |

---

## 3. Recommended Operating Conditions / Electrical Characteristics

| Parameter | Conditions | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| Mains input | — | 85 | 230 | 265 | VAC |
| Standby power (lamp off) | 230 VAC, radar active | — | 0.4 | 0.7 | W |
| Isolated rail | HLK-PM01 output | 4.75 | 5.0 | 5.25 | V |
| Rail current budget | radar 79 mA + MCU + opto | — | 110 | 600 | mA |
| Switched load (resistive/LED) | no heatsink | — | — | 2 | A |
| Switched load (with clip heatsink) | TO-220 + sink | — | — | 6 | A |
| Minimum load | for reliable triac latch | 3 | — | — | W |
| Presence detection range | configurable | 0.75 | — | 6 | m |
| Detection angle | — | — | ±60 | — | ° |
| Distance resolution | per gate | — | 0.75 | — | m |
| OFF delay (no-one timer) | trimmer RV1 | 10 | — | 600 | s |
| Turn-on latency (person enters) | — | — | <0.5 | 1 | s |
| Radar logic OUT level | — | — | 3.3 | — | V |

**Note on minimum load:** a TRIAC needs a holding current to stay latched. Very low-power LED lamps
(< ~3 W) or electronic drivers with tiny input current may flicker or fail to switch cleanly. Fit a
snubber (already on board) and, for problem loads, a bleeder/dummy load across the lamp terminals.

---

## 4. Pin / Terminal Description

### 4.1 Mains screw terminal — J1 (3-pole, 5.08 mm)
| Pin | Name | Direction | Function |
|---|---|---|---|
| 1 | **L** | Input | Mains Live (Phase) in |
| 2 | **N** | Input | Mains Neutral (feeds the power supply) |
| 3 | **LAMP** | Output | Switched Live to the lamp. The lamp's other wire goes to Neutral. |

> The switch is a **neutral-required** design: the HLK-PM01 supply is powered from L+N so the electronics
> work even when the lamp is off. Both N and the lamp-return Neutral come from the same mains neutral.

### 4.2 Radar module header — J3 (1×5, 1.27 mm, vertical)
| Pin | Name | Function |
|---|---|---|
| 1 | OUT | Presence output, 3.3 V logic. **HIGH = human present**, LOW = vacant → MCU PB4 |
| 2 | TX | LD2410B UART transmit (config/debug) → J4 |
| 3 | RX | LD2410B UART receive (config) → J4 |
| 4 | GND | Ground |
| 5 | VCC | +5 V supply to the radar |

### 4.3 ISP programming header — J2 (2×3, 2.54 mm, standard AVR)
`1 MISO · 2 VCC(+5V) · 3 SCK · 4 MOSI · 5 RESET · 6 GND` — program with **mains disconnected**.

### 4.4 Radar config UART — J4 (1×3, 2.54 mm)
`1 TX · 2 RX · 3 GND` — connect a 3.3 V USB-UART adapter and the Hi-Link PC tool to set detection
range, per-gate sensitivity and the radar's own "no-one duration".

### 4.5 Controls / indicators
- **SW1** — momentary push button: short press toggles Auto ↔ Manual; long press forces lamp OFF.
- **D1** — status LED: solid = presence, slow blink = manual mode, fast blink = fault (radar not responding).
- **RV1** — 10 kΩ trimmer: sets the auto OFF delay (10 s fully CCW … 10 min fully CW), read by the MCU ADC.

---

## 5. Theory of Operation

```
          85-265 VAC
   L ──┬───[F1 500mA]──┬───────────────┬─────────────[ MT1 ]  Q1 BTA16-600B
       │               │               │                │  (triac)
       │             [MOV]           [NTC 5D-9]          │ gate ← RG1 180Ω ← MOC3063 pin4
       │             [X2 ]              │                │        (zero-cross opto)
       │             [1M ]           HLK-PM01 L     [ MT2 ]──── LAMP ──→ (lamp) ──→ N
   N ──┴───────────────┴──────────────HLK-PM01 N          snubber RS1 100Ω + CS1 10nF across MT1-MT2
                                          │
                                      +5V / GND (SELV, isolated)
                                          │
   ┌──────────────────────────────────────┴───────────────────────────────┐
   │  ATtiny13A:  PB4 ← LD2410B OUT      PB0 → MOC3063 LED (via R1 330Ω)     │
   │              PB3 ← RV1 delay pot    PB1 → status LED D1                  │
   │              PB2 ← SW1 button       PB5 = RESET/ISP                      │
   └───────────────────────────────────────────────────────────────────────┘
```

**Sequence**
1. **Person enters** — radar OUT goes HIGH → MCU drives the opto → triac fires at the next mains
   zero-crossing → **lamp ON** (< 0.5 s, silent).
2. **Person stays (even still)** — radar continues to report presence (micro-motion/breathing) → lamp
   stays ON; the OFF timer is held reset.
3. **Person leaves** — radar OUT goes LOW → MCU starts the OFF delay (set by RV1). If no presence returns
   before the delay expires, the opto is released and the triac turns off at the next current zero →
   **lamp OFF**.
4. **Manual override** — a button press forces ON or OFF regardless of the radar; another press (or a
   timeout) returns to Auto. On power-up the firmware initialises to a safe **OFF, Auto** state.
5. **Fail-safe** — if the radar stops responding, the firmware blinks the LED and defaults the lamp OFF
   (configurable to last-known-state).

The **MOC3063 is a zero-crossing opto-triac**: it only triggers the main triac near the mains zero-crossing,
which minimises inrush, EMI and switching stress — this is why silent, flicker-free switching is possible.

---

## 6. Mechanical

| Item | Value |
|---|---|
| PCB size | **70 × 56 mm**, rounded corners R3 |
| Thickness | 1.6 mm |
| Layers / copper | 2-layer FR-4, 1 oz |
| Finish | ENIG |
| Mounting holes | 4 × Ø3.2 mm (M3), 4.0 mm from corners |
| Radar mounting | vertical daughter-board on J3, antenna faces the front cover |
| Board outline | includes a **routed isolation slot** in the primary↔secondary corridor |
| Enclosure | fits standard Indian 86 × 86 modular back box (internal cavity ≈ 75 mm) |

> **Design note on size:** 45 × 45 mm was the preferred target, but the mandated through-hole mains parts
> (HLK-PM01 34 × 20 mm, 14 mm MOV, TO-220 triac, 5.08 mm terminal) plus a ≥ 6 mm isolation barrier do not
> physically fit that area. 70 × 56 mm is the compact result that still drops into the 86 × 86 box. To reach
> ~50 × 50 mm, substitute a smaller supply (e.g. 3 W SMD module), a 10 mm MOV and an SMD triac — see
> `DESIGN_REPORT.md`.

---

## 7. Isolation & Safety Summary
- **Primary (mains) section** and **secondary (SELV 5 V) section** are kept on opposite halves of the board,
  separated by a ≥ 6 mm no-copper corridor with a milled slot.
- The only parts crossing the barrier are the **HLK-PM01** (reinforced AC-DC isolation) and the **MOC3063**
  (7.5 kVrms opto) — both certified isolation devices.
- Primary-side live-to-live (L–N–Lamp) spacing is set by routing and the component packages; conformal
  coating is required where it is below 2.5 mm. Full creepage/clearance analysis is in `SAFETY_REVIEW.md`.
- Board is silk-marked **"⚠ HIGH VOLTAGE — RISK OF SHOCK"** on the primary side.

---

## 8. Application Information

### 8.1 Typical wiring (ceiling light in a bathroom)
```
  Mains Live  ───────────────► J1-1 (L)
  Mains Neutral ──┬──────────► J1-2 (N)
                  └───────────► lamp terminal 2
  Lamp terminal 1 ◄─────────── J1-3 (LAMP)
```
Install the module in the wall box with the radar facing the room through the plastic front plate. Keep
**metal objects and foil away from the antenna window**. Mount at 1.1–1.5 m height (wall) or on the ceiling.

### 8.2 Setting the delay and sensitivity
- **OFF delay:** turn RV1 CW for longer, CCW for shorter (10 s … 10 min).
- **Range / sensitivity:** connect J4 to a 3.3 V USB-UART and run the Hi-Link LD2410B PC tool; set the
  maximum detection gate (0.75 m per gate, up to gate 8 = 6 m) and per-gate sensitivity to reject
  movement outside the room (e.g. a corridor behind a thin wall). Settings are stored in the radar.

### 8.3 Load guidance
- **LED lamps:** use the on-board snubber; for < 3 W drivers that flicker, add a 0.1 µF X2 + 100 kΩ
  bleeder across the lamp, or use the relay-output variant.
- **Resistive / halogen:** fine up to ~2 A without a heatsink; fit a TO-220 clip heatsink for 2–6 A.
- **Inductive (fans/transformers):** keep the snubber; verify dv/dt; prefer a snubberless triac
  (BTA16-600BW) for heavily inductive loads.

### 8.4 Firmware
The ATtiny13A firmware implements power-on init, presence read, the adjustable OFF timer, manual override
and fail-safe OFF. Pin map and build/flash instructions are in `../06_firmware/`. Program via J2 with an
AVR ISP programmer, **mains disconnected**.

---

## 9. Ordering Information

| Part number | Description |
|---|---|
| **SPS-24G-01** | Smart Presence Sensor Switch, 24 GHz, triac output, 85–265 VAC, modular form factor |
| SPS-24G-01-R | Variant with relay output (for difficult LED drivers) — *planned* |

Manufactured by **SAMAY ELECTRONICS**. This is a preliminary datasheet for an engineering sample;
specifications are subject to change and to safety certification.
