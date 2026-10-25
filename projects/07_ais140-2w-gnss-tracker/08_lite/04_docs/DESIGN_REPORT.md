# CRL-TRK-2W-L1 "Samay Track 2W Lite": design report (rev A0)

The Lite is the low-cost consumer tracker described in `07_marketing/BUSINESS_PLAN_NOTES.md` section 5: Cat-1 4G with
2G fallback, GPS + BeiDou, a small backup cell, ignition sense and engine-lock relay output, and a target hardware
cost of Rs 1,200-1,500. It is sold on Amazon / Flipkart / direct, **not** for AIS-140.

## 1. Lite vs. full version

| | CRL-TRK-2W-01 (full) | **CRL-TRK-2W-L1 (Lite)** |
|---|---|---|
| Cellular | SIM7080G LTE-M / NB-IoT, no 2G | **EC200U-CN LTE Cat-1 bis + GSM/GPRS fallback** (B1/3/5/8/34/38/39/40/41, GSM 900/1800) |
| Processor | ESP32-S3 module | **none - firmware runs in the modem (QuecOpen / QuecPython)** |
| GNSS | NEO-F10N L1/L5 + NavIC | **L76K L1: GPS + BeiDou + GLONASS + QZSS, no NavIC** |
| Motion | IIM-42652 6-axis IMU (crash) | **LIS3DH 3-axis (motion / tow / fall)** |
| Backup | 18650, ~40 h | **300 mAh LiPo, 2-4 h** |
| Input | 9-36 V, LM74700 ideal diode, 100 V buck | **9-30 V (12 V two-wheelers), series Schottky, 40 V buck** |
| Log memory | 16 MB NOR | module flash (8 MB file system) |
| SIM | nano-SIM holder | **soldered MFF2 M2M eSIM** (year-1 data bundled) |
| I/O | IGN, SOS, DIN, AIN, DOUT | IGN, relay output |
| PCB | 60 x 45, 4-layer, double-sided | **60 x 45, 2-layer, single-sided SMT**, same holes and enclosure |
| Hardware cost @1k | ~Rs 6,180 | **~Rs 1,440** (`BOM.md`) |

## 2. Block diagram

```
VEHICLE 9-30 V -> F1 2 A -> D1 SMBJ24CA -> D2 SS34 -> VIN_PROT -> U1 XL1509 buck -> V4_BUCK 4.44 V
                                                                          |-> D4 SS34 ---------> VSYS 3.3-4.3 V
                                                                          |-> U2 MCP73831 -> VBAT (300 mAh LiPo)
                                                                                         VBAT -> Q1 AO3401A -> VSYS
VSYS -> U3 EC200U-CN VBAT_BB/RF (220 uF ceramic + 100n/33p/10p + SMF5.0A)
VSYS -> U6 AP2112K-3.3 (EN = GPIO3) -> +3V3_GNSS -> U5 L76K -> U.FL J5 -> passive 25 mm L1 patch
U3 MAIN UART 1.8 V <-> Q3/Q4 BSS138 <-> L76K UART 3.3 V (NMEA)
U3 VDD_EXT 1.8 V -> U7 LIS3DH (I2C 0x18, INT1 -> GPIO2), I2C pull-ups, IGN pull-up
U3 ANT_MAIN -> 51 ohm CPWG -> L-match R14 (series) / C19 (shunt, DNP) -> U.FL J4 -> FPC LTE/GSM antenna
U3 USIM -> 22 R -> U8 MFF2 eSIM
IGN 12 V -> R24/R25 -> Q5 -> IGN_DET_N (GPIO1)        GPIO4 -> Q6 AO3400A -> RELAY_OUT (coil to +12 V, flyback D6)
NET_STATUS -> Q7 -> yellow LED   STATUS -> Q8 -> green LED   MCP73831 STAT -> red LED
```

## 3. Power

**Rails**
| Rail | Source | Range | Peak | Notes |
|---|---|---|---|---|
| VIN_PROT | vehicle | 9-30 V | 0.9 A (GSM burst at 12 V) | load dump clamped to 38.9 V by D1 |
| V4_BUCK | XL1509 | 4.44 V | 2 A | 150 kHz non-sync buck, 22 uH, D3 catch diode |
| VSYS | D4 or Q1 | 3.3-4.3 V | 2 A for 577 us (GSM) | 2 x 100 uF ceramic reservoir |
| VBAT | LiPo | 3.0-4.1 V | 2 A (on battery) | charged at 147 mA, tops out ~4.1 V (charger input 4.44 V) |
| +3V3_GNSS | AP2112K | 3.3 V | 40 mA | switched off when parked |
| MDM_1V8 | EC200U VDD_EXT | 1.8 V | 50 mA max | LIS3DH, pull-ups, level shifters |

**Current budget (estimates; measure on the prototype)**
| Mode | EC200U | L76K | Rest | From a 12 V battery | From the 300 mAh cell |
|---|---|---|---|---|---|
| Driving, 10 s reports on LTE | ~25 mA avg | ~25 mA | ~5 mA | ~25 mA | ~5 h |
| Driving, on GSM | ~60 mA avg | ~25 mA | ~5 mA | ~40 mA | ~3 h |
| Parked, modem sleep (DRX), GNSS off, motion wake | ~2 mA | 0 | XL1509 Iq ~3 mA, LIS3DH 2 uA | **~5 mA** (~120 mAh/day: a 5 Ah bike battery lasts ~40 days) | ~60 h |

The parked current is the Lite's weak point compared with the full version (0.11 mA). It is dominated by the non-synchronous
XL1509. A cost-equal option with a low-Iq buck (for example SY8303 or MP2451 class) can bring it to ~2.5 mA. It is listed for rev A1.

**Power path:** with external power, V4_BUCK (4.44 V) gates Q1 off, so VSYS = V4_BUCK - V_D4 (~4.1 V). If the vehicle
supply is lost, V4_BUCK collapses (R4 discharges it), Q1's gate goes to 0 V and the battery feeds VSYS through ~50 mOhm.
Q1's body diode carries VSYS during the switch-over, so the modem never browns out.

## 4. Modem as the application processor

The EC200U-CN runs the tracker firmware itself (QuecOpen C SDK or QuecPython):
- **UART0 (MAIN, pins 67/68):** NMEA from the L76K at 9600 baud.
- **I2C (41/42):** LIS3DH.
- **GPIO1-4 (27/26/24/25):** IGN_DET_N, ACC_INT, GNSS_EN, RELAY_CTL. Pin map in `06_firmware/board_pins.h`.
- **ADC0/ADC1 (45/44):** battery and input voltage.
- **Firmware download:** USB (TP3-TP5, pogo fixture) with QFlash. Debug log on DBG UART (TP6/TP7).
- **Auto power-on:** C16/R9/Q2 pull PWRKEY low for ~1.5 s whenever VSYS comes up. R10 (DNP) is a permanent auto-on option.

The BOM drops the ESP32, the TXS0108E translator, the log flash, the RTC and the fuel gauge. The modem has an RTC, a
file system for store-and-forward, and the ADC reads the battery.

## 5. RF

| Line | Geometry | Z0 (rf_calc.py) | Length |
|---|---|---|---|
| LTE / GSM (U3 pad 49 -> J4) | 0.5 mm neck between the module's GND pads, then 1.2 mm / 0.2 mm CPWG on L1 over the L2 plane, via fence every 1.5 mm | 51 ohm | ~20 mm |
| GNSS (U5 pad 11 -> J5) | 0.5 mm, no stubs | 72 ohm | 4 mm (0.035 lambda, < 0.1 dB) |

- **LTE:** R14 (0603 0R, series) and C19 (0603 DNP shunt, its pad sits on the line) form an L-match for the chosen FPC antenna. Tune it on the bench with a VNA through the U.FL.
- **GNSS:** the L76K has an internal LNA. The Lite uses a passive 25 x 25 x 4 mm ceramic patch on a short U.FL lead, so there is no bias-T. An active antenna would need a bias-T added in rev A1.
- **Separation:** the GNSS corner (top-left) is about 45 mm from the LTE feed (bottom-right) and away from the buck (left-middle).

## 6. PCB

- 60 x 45 mm, R2 corners, 2-layer FR-4 1.6 mm, 1 oz, HASL, green / white. JLC standard rules: 0.127 mm track and space, 0.3 mm vias.
- All parts on the top side (single-sided SMT). The bottom layer carries the GND plane, the signal jumpers and the 18 test pads.
- Net classes: Default 0.2 / 0.15. Power (VSYS, VBAT, V4_BUCK, BUCK_SW, +3V3_GNSS) 0.6 mm. HV (VIN_*, IGN_RAW, RELAY_OUT) 0.5 mm with 0.3 mm clearance. RF50 1.2 mm with 0.2 mm gap.
- GND: top and bottom pours, fan-out vias at every GND pad, 49 vias in the EC200U LGA field, an edge ring and a 4 mm stitching grid.
- Same 60 x 45 mm outline and M2 mounting holes (H1-H4) as CRL-TRK-2W-01, so the Lite fits the full version's IP67 enclosure. A cheaper 70 x 55 x 22 mm ABS box is in the BOM.
- Connectors: J1 JST XH 4-pin (vehicle: +12V / GND / IGN / RELAY), J2 JST PH 2-pin SMD (battery), J4 / J5 U.FL.
- LEDs D7-D9 sit on the top edge, under the lid's light pipes.

## 7. Protection (two-wheeler, 12 V)

| Event | Handling |
|---|---|
| Reverse battery | D2 blocks it; D1 conducts and clears F1 if the reversal persists |
| Load dump / ISO 7637-2 pulse 2a/3 | D1 SMBJ24CA (600 W) clamps at 38.9 V, below the XL1509's 40 V maximum |
| 24 V jump start | not supported: the Lite is specified for 12 V systems only (marked on the label) |
| IGN line spikes / reversal | R24 47k into Q5's base; reverse current is limited by R24 |
| Relay coil flyback | D6 to VIN_PROT |
| ESD on the antenna / harness | U.FL shields grounded at the board edge; harness inputs go through R24, C28 and D1 |

## 8. Test and production

- **Bed of nails** on TP1-TP18 (1 mm pads, all on the bottom side, so they cost nothing in assembly): rails (VIN_PROT, V4_BUCK, VSYS, VBAT, MDM_1V8, +3V3_GNSS), modem USB for flashing and IMEI read-out, debug UART, PWRKEY / RESET, GNSS reset / 1PPS, IGN.
- **Flow:**
  1. Power up at 12 V and check the rails.
  2. Flash QuecOpen firmware over USB.
  3. Read the IMEI and eSIM ICCID and print the label.
  4. GNSS: fix from a GPS re-radiator.
  5. Cellular: attach and send a test packet on LTE, then on GSM.
  6. Accelerometer: WHO_AM_I = 0x33.
  7. IGN: toggle and check.
  8. Relay output: switch a load.
  9. Battery: check that it charges.
- **Certification (consumer, from the business notes):** WPC ETA, BIS IS 16046 (cell), TEC/MTCTE if applicable, EPR, Legal Metrology labelling. The EC200U-CN carries its own module certifications; check its India approval status (WPC) with Quectel.

## 9. Open points (rev A1)

1. Replace the EC200U land pattern with Quectel's drawing (`VERIFY_LIST.md` #1). **Blocking for fabrication.**
2. Low-Iq buck to cut parked current from ~5 mA to ~2.5 mA.
3. Re-route the bottom-layer jumpers to keep the GND plane whole under the modem.
4. Optional nano-SIM holder footprint (DNP) next to the eSIM, for customers who bring their own SIM.
5. Cost-down options in `BOM.md`: SC7A20 accelerometer, TP4054 charger, generic IPEX connectors, passive GNSS patch.
