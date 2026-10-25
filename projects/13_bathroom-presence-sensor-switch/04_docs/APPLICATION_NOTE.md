# SPS-24G-01 — Application & Installation Note

**SAMAY ELECTRONICS** · 24 GHz Smart Presence Sensor Switch · Rev A0

> ⚠️ Installation involves **230 V mains**. A licensed electrician must do it, with the circuit breaker OFF.
> This product is not yet safety-certified — see `SAFETY_REVIEW.md`.

## 1. Wiring

The switch needs **Line, Neutral and the Lamp wire** (a neutral-required smart switch).

```
   Consumer unit / MCB
        │  Live (L)
        ▼
   ┌─────────────┐
   │ J1-1  L     │◄── mains Live
   │ J1-2  N     │◄── mains Neutral ──┐
   │ J1-3  LAMP  │──► lamp wire 1     │
   └─────────────┘                    │
                     lamp wire 2 ──────┘  (lamp returns to Neutral)
```

- **J1-1 (L):** incoming live from the MCB.
- **J1-2 (N):** neutral — powers the electronics even when the lamp is off.
- **J1-3 (LAMP):** switched live to the light. The light's other terminal connects to Neutral.

Use correctly rated conductors and ferrules; torque the screw terminals to spec; sleeve/insulate before
closing the modular plate. Keep the low-voltage (bottom) half of the board away from any exposed metal.

## 2. Mounting & orientation
- Fits a standard 86 × 86 mm modular box. Secure the PCB to the modular frame via the four M3 holes.
- The **LD2410B radar stands vertical on header J3**, antenna facing the **front cover** (the room).
- Mount height: **wall 1.1–1.5 m** or **ceiling 2.4–3 m**. Avoid aiming through thin walls into corridors.
- The front cover must be **RF-transparent plastic** with **no metallised paint or foil** over the antenna.

## 3. Commissioning
1. With mains OFF, fit the module and close the plate. Restore power.
2. The LED shows the state (solid = lamp on / presence, slow blink = manual, fast blink = fault).
3. **Off-delay:** adjust trimmer **RV1** — CCW ≈ 10 s, CW ≈ 10 min.
4. **Range / sensitivity:** plug a 3.3 V USB-UART into **J4** (TX/RX/GND) and run the Hi-Link LD2410B PC
   tool. Set the furthest detection gate (0.75 m per gate, gate 8 = 6 m) and per-gate sensitivity so the
   switch ignores motion outside the room. Settings persist in the radar.
5. **Manual override (SW1):** short press = Auto↔Manual (and toggle in Manual); long press = force OFF.

## 4. Load compatibility
| Load | Notes |
|---|---|
| LED lamp / driver | On-board snubber fitted. If a low-power (<3 W) driver flickers when "off", add a 0.1 µF X2 + 100 kΩ bleeder across the lamp, or use the relay-output variant. |
| Incandescent / halogen | OK to ~2 A without heatsink; fit a TO-220 clip heatsink for 2–6 A. |
| CFL | Works, but CFLs dislike rapid cycling — set a longer off-delay. |
| Inductive (fan) | Keep the snubber; prefer the snubberless BTA16-600BW for heavy inductive loads. |

Minimum load ~3 W for reliable triac latching.

## 5. Troubleshooting
| Symptom | Likely cause / action |
|---|---|
| Light never turns on | Check Lamp wiring (J1-3), minimum load, radar OUT at TP4, triac gate TP3. |
| Light won't turn off | Radar seeing motion outside the room → reduce range/sensitivity via J4; check off-delay (RV1). |
| Flicker when off | Low-power LED driver leakage → add bleeder / dummy load across the lamp. |
| Fast-blink LED | Radar not responding → check 5 V at the header, radar seated, UART config. |
| No LED, dead | Check F1 fuse, HLK-PM01 5 V at TP1. **De-energise first.** |

## 6. Firmware / programming
Program the ATtiny13A via the **J2** 6-pin AVR ISP header with an ISP programmer (USBasp etc.),
**mains disconnected**. Reference firmware and pin map are in `../06_firmware/`.
