# CRL-TRK-2W-01 — AIS-140 Two-Wheeler GNSS / LTE-M Tracker
### Engineering design report, rev A0 (pre-prototype)

| | |
|---|---|
| Board | 60.0 × 45.0 mm, 4-layer, 1.6 mm, JLC04161H-7628, ENIG, double-sided SMT |
| MCU | ESP32-S3-WROOM-1-N8R2 (BLE config, OTA, TLS) |
| Cellular | SIMCom SIM7080G — LTE Cat-M1 / NB-IoT, PSM 3 µA |
| GNSS | u-blox NEO-F10N — L1/L5 dual band, GPS/Galileo/BeiDou/QZSS **+ NavIC** (AIS-140) |
| Supply | 9–36 V vehicle input, −33 V reverse, ISO 7637-2 / ISO 16750-2 oriented protection |
| Backup | external 1S 18650 pack with PCM and 10 k NTC |
| Sleep current | ≈ 110 µA from the pack, ≈ 25 µA from the vehicle battery (calc., see §2) |

Sources of truth: `02_python/design.py` (circuit), `02_python/make_pcb.py` (placement, rules, routing flow).
Everything in `01_kicad/` and `03_fab/` is regenerated from them.

---

## 0. Changes against the original request (and why)

| Requested | Implemented | Reason |
|---|---|---|
| SIM7600G-H | **SIM7080G** | You chose it. 17.6 × 15.7 mm instead of 30 × 30 mm, 0.5 A peaks instead of 2 A, PSM 3 µA; the only way to fit 60 × 45 mm. |
| MAX-M10S / NEO-M10N | **NEO-F10N** | AIS-140 requires IRNSS/NavIC. M10 has no NavIC; NEO-F10N receives NavIC SPS-L5 plus L1/L5 multipath robustness. |
| MP1584EN buck | **LM5164-Q1** (100 V, 10 µA IQ, AEC-Q100) | MP1584 is 28 V abs-max and not automotive; the TVS clamp after a load dump is ≈ 53 V. |
| BQ24075 | **BQ24074** | Same family/footprint; 10.5 V input OVP and 4.4 V system regulation, so VSYS can feed SIM7080G VBAT (2.7–4.8 V) directly. |
| ICM-42688-P | **IIM-42652** | TDK industrial member of the same family (−40…105 °C), pin-compatible LGA-14; pinout taken from KiCad's reviewed library. |
| MAX17048 | **LC709203F** | Same class (no sense resistor, ~2 µA), library-verified footprint. Footprint swap to MAX17048 (TDFN-8) is a rev-B option. |
| DS3231 (optional) | **RV-3028-C7** | 45 nA instead of ~100 µA, 1.5 × 3.2 mm; EVI pin time-stamps lid tamper. |
| "No copper under ceramic GPS antenna" | external **active L1/L5 patch on U.FL** | A dual-band ceramic patch does not fit beside three modules on 60 × 45 mm, and a 25 mm patch needs its own ground plane. A lid-mounted, sky-facing active patch gives better sensitivity than any on-board antenna under a seat cowl. |
| LTE antenna on board | external **flex antenna on U.FL** | 700–900 MHz needs ≥ 100 mm ground length for usable efficiency. |
| SWD header | **pogo test-pad header TP21–TP28** (TMS, TCK, TDO, TDI, U0TXD, U0RXD, EN, BOOT) + native USB-JTAG on USB-C | ESP32-S3 has JTAG, not SWD. A Tag-Connect footprint was tried but its pad keep-out could not be escaped on this density; pads cost no BOM part and suit the production fixture. |
| Single-sided | **double-sided assembly** | Courtyard area of all parts = 2936 mm² > board area 2700 mm². Heavy parts top; bottom only small SMDs, SIM holder, USB-C, battery connector, test pads. |

## 1. Block diagram and power tree (deliverable 11)

```
 VEHICLE 9–36 V ─ F1 2 A ─┬─ D1 SMBJ33CA (bi) ─ Q1/U1 LM74700-Q1 ideal diode ─ VIN_PROT ─ FB1+C4/C5 π ─ VIN_BUCK
 (Micro-Fit J1)           │                                                          │                     │
                          └ IGN/PANIC/DIN1/AIN1/DOUT1 → R-clamp-RC → ESP32          C3 22 µF/63 V      LM5164-Q1 5.0 V/1 A
                                                                                                           │ D2
 USB-C VBUS 5 V ─────────────────────────────── D4 ──────────────────────────────────────────────────── V5_IN
                                                                                                           │
                                                 BQ24074 (ILIM 1.0 A, ICHG 500 mA, NTC 0–45 °C) ── BAT ── 18650 pack
                                                     │ OUT = VSYS (4.4 V ext. / VBAT on battery)
                       ┌─────────────────────────────┼──────────────────────────────┐
              TPS22917 (MDM_PWR_EN)          TLV75733 3.3 V/1 A (always on)    LC709203F gauge, VBAT/2 → ADC
                       │                             │
              SIM7080G VBAT 0.5 A pk         +3V3 ── ESP32-S3, IMU, RTC, flash, TXS0108E-B, V_BCKP
                                                     └ TPS22917 (GNSS_PWR_EN) → +3V3_GNSS → NEO-F10N VCC (+ active antenna via VCC_RF)
```

| Rail | Source | Typ. load | Peak | Notes |
|---|---|---|---|---|
| VIN_PROT | vehicle | 0.15 A @ 12 V active | 0.45 A (charging + TX) | 60 V-rated path, TVS-clamped |
| V5_IN | LM5164 / USB | 0.3 A | 1.0 A (ILIM) | D2/D4 OR-ing |
| VSYS | BQ24074 OUT | 60 mA | 0.65 A | modem burst 0.5 A + logic |
| VBAT_MDM | U6 | 18 mA idle | 0.5 A | 100 µF + 10 µF + HF caps, SMF5.0A |
| +3V3 | TLV75733 | 30 mA | 0.35 A (Wi-Fi OTA) | LDO drop 1.1 V × 0.15 A = 0.17 W |
| +3V3_GNSS | U7 | 25 mA (+ antenna ≈ 10 mA) | 40 mA | VCC_RF bias, 10 Ω limit |

## 2. Power budget (calculated)

**Parked, ignition off** (modem PSM, GNSS off with V_BCKP, ESP32 deep sleep, IMU wake-on-motion):

| Item | µA |
|---|---|
| TLV75733 IQ | 25 |
| ESP32-S3 deep sleep (RTC timer + EXT1) | 8 |
| IIM-42652 low-power accel, WoM | ≈ 30 |
| NEO-F10N hardware backup (V_BCKP) | 31 |
| SIM7080G PSM | 3 |
| BQ24074 battery leakage, U6/U7, flash, RTC, gauge | ≈ 12 |
| VBAT/2 divider | 2 |
| **Total from the pack** | **≈ 110 µA** |
| Vehicle side: LM5164 IQ + EN/VIN dividers (1 M + 68 k, 1 M + 330 k) | **≈ 25 µA** (+ charging when needed) |

A 3000 mAh pack therefore covers > 12 months parked (self-discharge dominates); vehicle drain stays far
below the usual 1 mA aftermarket limit. **Active tracking on battery** (AIS-140 power-cut case): GNSS 25 mA,
modem eDRX/idle 18 mA + one report every 10 s, ESP32 light-sleep ≈ 5 mA → ≈ 70 mA average → **≈ 40 h**
(AIS-140 asks for ≥ 4 h).

Measure on the first articles at the TP pads (TP12 VSYS, TP13 VBAT, TP14 +3V3) with a µA-range logger.

## 3. PCB stack-up and rules

| Layer | Use | Copper |
|---|---|---|
| L1 F.Cu | components, RF (50 Ω CPWG), short signals, GND pour | 1 oz |
| L2 In1.Cu | **solid GND** reference plane (no splits) | 0.5 oz |
| L3 In2.Cu | **+3V3 power plane** (plus 123 mm of short signal links where L1/L4 were full; plane stays in 2 connected pieces) | 0.5 oz |
| L4 B.Cu | components (light), signals, GND pour | 1 oz |

JLC04161H-7628: L1–L2 prepreg 0.2104 mm (εr 4.4), core 1.065 mm, L3–L4 prepreg 0.2104 mm.

| Net class | Track | Clearance | Via | Nets |
|---|---|---|---|---|
| Default | 0.127 | 0.127 | 0.45/0.2 | logic |
| Power | 0.3 | 0.15 | 0.6/0.3 | GND, VSYS, VBAT*, +3V3*, V5*, BUCK_SW |
| HV | 0.3 | 0.25 | 0.6/0.3 | VIN_*, harness inputs (60 V) |
| RF50 | **0.36** | **0.20 gap** | 0.45/0.2 | LTE_RF*, GNSS_RF* |

**50 Ω**: CPWG on L1 over L2, w = 0.36 mm, gap 0.20 mm → 50.5 Ω (conformal mapping,
`02_python/rf_calc.py`; microstrip alone would be 0.365 mm). Order the board **with impedance control**
on L1 (JLC: "impedance control: yes", target 50 Ω ± 10 %, reference L2).

## 4. Signal-integrity review (deliverable 12)

| Interface | Speed | Topology / length | Assessment |
|---|---|---|---|
| GNSS RF (1.17/1.58 GHz) | — | RF_IN → series 0 R → U.FL, ≈ 8 mm, straight, shunt pads C38/C39 | λg ≈ 107 mm, line ≪ λ/10; via fence 1.2 mm pitch both sides; bias-T tap at the connector side. OK |
| LTE RF (700–2200 MHz) | — | pin 32 → π (C32/R32/C33) → U.FL, ≈ 10 mm, one 90° corner | at 2.2 GHz λg ≈ 77 mm, corner effect negligible; π pad lets the flex antenna be matched in the enclosure. OK |
| USB 2.0 FS | 12 Mb/s | USB-C → USBLC6 → ESP32, < 25 mm | full speed only: 90 Ω not critical; pair kept together, no stubs. OK |
| SPI flash | 20–40 MHz | < 20 mm, bottom side | series R not needed at this length. OK |
| UART modem (1.8 V) | 115.2 kb/s | via TXS0108E | TXS0108E edge-rate accelerators, fine at ≤ 1 Mb/s. Do not exceed 1 Mb/s. |
| I²C | 400 kHz | 3 devices, 4.7 k pull-ups, < 60 pF | OK |
| SIM | 3.25–5 MHz | 22 Ω series + ESD at the holder | SIMCom layout rules applied. |
| Buck switch node | 300 kHz COT | SW copper minimised, L1 next to U2, input loop C4/C5–U2 ≈ 6 mm | placed 35+ mm from GNSS. |

Return paths: every signal layer is adjacent to L2 GND (L1) or L3 +3V3 (L4, decoupled to GND every few mm by
the 177 fan-out vias + stitching), so no high-speed signal crosses a split.

## 5. EMC recommendations (deliverable 14) — CISPR 25 / ISO 11452 / ISO 7637-2 / IEC 61000-4-2

1. **Conducted emissions**: FB1 + C4/C5 π-filter in front of the buck; keep C3 (electrolytic) — it damps the
   harness inductance. If 150 kHz–30 MHz fails, add a common-mode choke in the harness (or rev B footprint).
2. **Radiated**: the GND pours on L1/L4 are stitched to L2 every ≤ 4 mm and along the board edge every 3 mm
   (λ/20 at 2.5 GHz = 6 mm). The SIM7080G and NEO-F10N are shielded modules — do not remove their cans.
3. **GNSS desense**: buck, modem and ESP32 antenna are ≥ 20 mm from the GNSS module; LTE U.FL is on the
   opposite board corner. Cable-route the LTE antenna away from the GNSS patch (≥ 15 mm, ideally opposite
   enclosure walls). Check C/N0 with the modem transmitting (u-center, `UBX-MON-RF` jamming indicator).
4. **Transients**: D1 SMBJ33CA (600 W) at the connector; every harness input sees a 1206 series resistor
   (200 V rating), a BAT54S clamp and an RC filter; DOUT1 has a flyback diode to VIN_PROT.
5. **ESD**: USBLC6 on USB, ESDA6V1 on SIM, 10 nF/100 V at every harness pin; enclosure is plastic — tie the
   M2 mounting pads to GND only (no chassis connection needed).
6. **Immunity**: 100 nF + bulk at every IC, firmware glitch filtering on IGN/PANIC (≥ 50 ms), watchdog +
   modem hard power-cycle through U6.

## 6. Automotive design notes (deliverable 15)

- Input range 9–36 V covers 12 V bikes (14.6 V charging, 24 V jump start) and 24 V commercial vehicles.
- Reverse battery: LM74700-Q1 + BUK7M12-60EX block −33 V with < 15 mV forward drop (no diode loss).
  D1 is **bidirectional**, so a reversed battery does not blow F1.
- Load dump: suppressed load dump (ISO 16750-2 test B, 35 V for 12 V systems) is clamped by D1; all parts
  on VIN_PROT are rated ≥ 60 V (LM5164 100 V, Q1 60 V, LM74700 65 V, C3 63 V, C4/C5 100 V).
- Temperature: all ICs −40…85 °C or better; the 18650 is the weak point — charging is inhibited outside
  0–45 °C by the pack NTC, and firmware should also stop discharge-heavy operations above 60 °C.
- Vibration: Micro-Fit with positive latch; the hinged nano-SIM holder is for development only — use the
  soldered MFF2 eSIM in production (also an AIS-140 requirement, see §9). Bond the battery and antenna
  cables; underfill/conformal-coat after first vibration test if needed.
- Moisture: IP67 enclosure with Gore vent; conformal coating (acrylic, keep U.FL, Tag-Connect, test pads,
  SIM holder and USB-C masked).
- Use AEC-Q200 passives (MLCC flex-crack: no MLCC within 2 mm of the board edge or the connector).

## 7. DFM review (deliverable 13) — JLCPCB / PCBWay

| Check | Value | Capability | |
|---|---|---|---|
| Min track / space | 0.127 / 0.127 mm | 0.09 / 0.09 (4-layer) | ✔ |
| Min via | 0.45 / 0.2 mm | 0.45 / 0.2 (some fabs 0.3 drill standard; via-in-pad not used) | ✔ |
| Annular ring | 0.125 mm | 0.1 | ✔ |
| Copper to edge | ≥ 0.3 mm | 0.3 | ✔ |
| Smallest parts | 0402, LGA-14 0.5 mm, VQFN 0.5 mm, LCC-77 | standard | ✔ |
| Double-sided SMT | bottom: light parts only (heaviest J5 SIM holder, J3 USB-C, C3) | supported | ✔ (+cost) |
| THT | J1 Micro-Fit (8 pins), USB-C shell tabs | wave/selective or hand | ✔ |
| Panel | 2 × 3 with 5 mm rails + mouse-bites, fiducials on rails | | recommended |
| Fiducials | add 3 global fiducials on the panel rails | | — |
| Stencil | 0.12 mm; SIM7080G centre pads 56 % paste (built into footprint) | | ✔ |

## 8. Test points, programming and production test (deliverables 16, 17, 18)

**Programming / debug**: native USB-C (ESP32-S3 USB-Serial-JTAG: flashing, logs, JTAG) and the bottom-side
pogo header TP21 TMS, TP22 TCK, TP23 TDO, TP24 TDI, TP25 U0TXD, TP26 U0RXD, TP27 EN, TP28 BOOT (+ TP14 3V3,
TP17/18 GND) for the production fixture.
Flash with `esptool.py --chip esp32s3 write_flash` (USB) or OpenOCD (`board/esp32s3-builtin.cfg`).
Modem firmware: TP1–TP4 (SIM7080G USB + USB_BOOT) — SIMCom QDL tool.

**Test pads** (all on the bottom, ≥ 2.0 mm pitch for a bed-of-nails):

| TP | Net | Purpose |
|---|---|---|
| TP10 | VIN_PROT | input after protection |
| TP11 | V5_IN | buck / USB OR-ed 5 V |
| TP12 | VSYS | system rail (charger OUT) |
| TP13 | VBAT | battery |
| TP14 | +3V3 | logic rail |
| TP15 | VBAT_MDM | modem rail |
| TP16 | +3V3_GNSS | GNSS rail |
| TP17, TP18 | GND | probes |
| TP19, TP20 | IGN_DET, PANIC_DET | input conditioning check |
| TP1–TP5 | MDM USB VBUS/D+/D−, USB_BOOT, UART2 debug TX | modem upgrade / logs |
| TP6–TP8 | GNSS RESET_N, SAFEBOOT_N, TIMEPULSE | GNSS recovery / timing |
| TP9 | TAMPER_N | lid switch / RTC EVI |
| TP21–TP28 | JTAG TMS/TCK/TDO/TDI, U0TXD/RXD, EN, BOOT | programming / JTAG pogo header |

**Production checklist**
1. AOI + X-ray on SIM7080G (LCC), NEO-F10N, ESP32-S3 GND pad, VQFN/LGA parts (sample per lot).
2. Bed-of-nails, no battery: apply 13.5 V / 1 A limit on J1 → check TP10, TP11 (5.0 ± 0.1 V), TP12 (4.4 V),
   TP14 (3.30 ± 0.05 V); input current < 30 mA with modules held in reset.
3. Reverse 13.5 V on J1 for 1 s → < 1 mA, no damage. 30 V on J1 → rails unchanged.
4. Flash production firmware over USB / pogo header TP21–TP28; write serial number, IMEI ↔ device ID, keys to NVS
   (flash encryption + secure boot v2 enabled in production builds).
5. Self-test firmware: I²C scan (0x0B, 0x52, 0x68), flash JEDEC ID, IMU WHO_AM_I, GNSS UBX-MON-VER,
   modem `ATI`/`AT+CCID`, LED walk, ADC of VIN/VBAT/AIN1 against fixture references, DOUT1 load test.
6. RF: GNSS conducted test (−130 dBm L1/L5 generator → C/N0 ≥ 40 dB-Hz); LTE: network attach in a shielded
   box or call-box, RSSI, TX power at the U.FL.
7. Sleep current with battery only: < 150 µA after 60 s.
8. Battery charge start/stop with NTC simulated at 25 °C / 50 °C.
9. Final assembly: antennas, battery, gasket, IP67 leak test (pressure decay), label with IMEI/QR.
10. Traceability: lot of SIM7080G / NEO-F10N / PCB date code stored with the serial number.

## 9. AIS-140 compliance notes (India, commercial vehicles)

| Requirement (AIS-140 / CDAC test) | Design status |
|---|---|
| IRNSS/NavIC positioning | ✔ NEO-F10N (NavIC SPS-L5) |
| Emergency (panic) button | ✔ PANIC input, wakes MCU (RTC IO) |
| Internal backup battery ≥ 4 h | ✔ external pack in the enclosure, ≈ 40 h estimated |
| Embedded SIM with multi-operator profiles | ⚠ rev A has a nano-SIM holder; **rev B must add an MFF2 eSIM footprint** on the same SIM bus |
| Tamper / main power disconnect alerts | ✔ VIN_SENSE ADC, RTC EVI lid tamper, IMU motion |
| Ignition, digital/analog inputs, digital output | ✔ IGN, DIN1, AIN1, DOUT1 (immobiliser) |
| Store-and-forward, OTA, SMS fallback | firmware (W25Q128 log; SIM7080G supports SMS on LTE-M where the network allows) |
| 2G fallback | ✘ SIM7080G has no 2G — confirm with the test agency that LTE-M/NB-IoT-only devices are accepted, or move to an LTE Cat-1 module with 2G fallback |
| Certification | CDAC / ICAT type approval, BIS, WPC ETA, TEC (MTCTE) — plan pre-compliance on rev A |

## 10. Firmware architecture (features requested)

| Feature | Implementation hook |
|---|---|
| Live GPS | NEO-F10N UBX-NAV-PVT @ 1 Hz → MQTT/TLS `trk/<id>/pos` |
| Motion detection / theft alert | IIM-42652 wake-on-motion → IO14 (EXT1 wake) while IGN off → alert + GNSS fix |
| Geo-fence | polygon/circle list in NVS, evaluated on each fix, hysteresis 20 m |
| Crash detection | IMU 1 kHz, ‖a‖ > 6 g peak + roll/pitch > 60° for > 2 s → crash event |
| Sleep mode | ESP32 deep sleep, modem PSM (T3412/T3324), GNSS off with V_BCKP, LDO only |
| OTA | ESP-IDF `esp_https_ota` over the modem PPP link, A/B partitions, rollback |
| MQTT / HTTPS | ESP-IDF over PPPoS (esp_modem) — TLS in ESP32, modem as data pipe |
| BLE configuration | NimBLE GATT service, bonded + passkey, only within 5 min of power-up / button |
| Offline logging | W25Q128 ring buffer (LittleFS), ≈ 400 k positions, replay on reconnect |
| Auto restart | task WDT + RTC WDT; modem watchdog via `AT` timeout → PWRKEY → U6 power cycle |
| Ignition detection | IO5 RTC GPIO, 50 ms debounce, also VIN > 13.2 V heuristic |
| Battery monitoring | LC709203F RSOC + VBAT ADC + BQ24074 PGOOD/CHG |

`06_firmware/board_pins.h` is generated from the netlist and is the only pin map firmware should use.

## 11. Layout summary (as built)

| Item | Value |
|---|---|
| Parts placed | 180 footprints: 69 top, 111 bottom (incl. 28 test pads, 4 mounting holes) |
| Routing | 4121 track segments (F 1038 mm, B 1286 mm, In2 123 mm), 399 vias (371 × 0.2 mm, 28 × 0.3 mm drill) |
| RF | GNSS + LTE 50 Ω CPWG, 20 mm total on L1, GND via fences at 1.2 mm pitch |
| Planes | L2 GND one piece (2352 mm²); L3 +3V3 2 pieces (2148 mm²); L1/L4 GND pours stitched to L2 |
| Flow | anchors by hand → greedy placer → GND/+3V3 fan-out → Freerouting 1.9 (2 rounds) → grid A* finisher with rip-up → stitching / island vias |
| DRC | 0 errors, 0 unconnected, 0 schematic-parity issues (warnings only, see `DRC_ERC_REPORT.md`) |
| ERC | 0 errors, 0 warnings |

Before ordering, open the board in KiCad 9 and review the auto-routed L3 links and the A*-finished tracks
(they follow a 0.05 mm grid, so some show small zig-zags — electrically fine, cosmetically worth a manual
clean-up with *Interactive Router → Optimise*).

## 12. Open items / to verify before release

See `VERIFY_LIST.md`. In short: every value marked VERIFY in the schematic (LM5164 RON, UVLO, BQ24074 ITERM/TMR,
fuse and ferrite MPN suffixes, LC709203F unused pins), the SIM7080G outer-pad toe length against SIMCom
HD V1.05, antenna matching (π pads) with the final enclosure, and the eSIM footprint for AIS-140.
