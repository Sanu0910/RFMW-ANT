# SPS-24G-01 Bill of Materials (rev A0) - Smart Bathroom Presence Sensor Switch

Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: `03_fab/SPS-24G-01_BOM_JLCPCB.csv` (fill the LCSC column at quotation); costed BOM: `03_fab/SPS-24G-01_BOM_costed.csv`.

**25 line items, 31 placed parts**, plus 1 DNP and 5 test pads and 4 mounting holes.

> **Mains parts** (F1, MOV1, NTC1, CX1, RB1, PS1, U2, Q1, RG1, RS1, CS1, J1) carry live voltage. Use only the rated MPNs (X2/X1 safety caps, 250 V+ fuse, reinforced-isolation PSU). See `SAFETY_REVIEW.md` before procurement.

## Cost summary (estimate, 1 000 pcs, Rs 86 / USD, excl. GST)

| Group | Rs |
|---|---|
| Sensor (radar) | 224 |
| Power (mains) | 155 |
| ICs | 39 |
| Triac / power | 36 |
| Connectors | 35 |
| Protection (mains) | 35 |
| Opto / isolation | 30 |
| UI | 28 |
| Passives (mains) | 13 |
| Passives | 4 |
| **Board parts total** | **600** |
| Bare PCB - 70 x 56 mm 2-layer FR-4 1.6 mm, 1 oz, ENIG, green, isolation slot routed | 40 |
| Assembly - mixed SMT (SELV) + THT (mains), single-sided, ~40 placements + hand-solder mains | 70 |
| Radar module - HLK-LD2410B 24 GHz on vertical header (listed in BOM; cost dominates) | 0 |
| Enclosure - FR-ABS modular front plate + back shell, RF-transparent sensor window, IP44 bathroom | 95 |
| Wiring / label - L/N/LAMP ferrules, HIGH-VOLTAGE label, install card | 20 |
| **Total hardware per unit (est.)** | **825** |

Cost is dominated by the LD2410B radar and the HLK-PM01 supply. A WiFi-less premium sensor switch retails Rs 1,200-2,500 in India, so the BOM leaves healthy margin.

## Placed parts

| Designators | Qty | Value | Package | MPN | Manufacturer | Unit Rs | Description |
|---|---|---|---|---|---|---|---|
| C1,C4,C5,C6,CB2 | 5 | 100nF | C_0603_1608Metric | 0603 MLCC X7R 50V | Samsung / Murata | 0.13 |  |
| C2 | 1 | 10uF | C_0805_2012Metric | 0805 MLCC X7R 50V | Samsung / Murata | 0.34 |  |
| CB1 | 1 | 220uF/10V | CP_Radial_D6.3mm_P2.50mm | 220uF 10V radial (105C, low-ESR) | Rubycon / Nichicon | 2.58 | Bulk on 5 V: supplies the LD2410B (~79 mA avg, bursty) and the opto LED |
| CS1 | 1 | 10nF 400VAC | C_Rect_L10.0mm_W4.0mm_P7.50mm_FKS3_FKP3 | 10 nF 400 VAC X1 film (e.g. BFC233820103) | Vishay / KEMET | 7.74 | Snubber cap across the triac (with RS1): dv/dt suppression |
| CX1 | 1 | 100nF X2 | C_Rect_L11.0mm_W5.1mm_P10.00mm_MKT | R46KI31000001M (100 nF 275 VAC X2) | KEMET / Vishay | 10.32 | X2 safety EMI cap across L-N, 275 VAC. Differential-mode filtering. |
| D1 | 1 | STATUS | LED_0805_2012Metric | green 0805 (fault = red/blink pattern in firmware) | Kingbright | 0.86 | Status LED: on=presence, slow blink=manual, fast blink=fault |
| F1 | 1 | T500mA 250V | Fuse_TR5_P5.08mm | 0382.500HAT1 (TR5, T 500 mA 250 V) | Littelfuse | 15.48 | Time-lag (slow-blow) fuse 500 mA, 250 VAC, TR5 radial. Protects against PSU/triac fault, not lamp overload. |
| J1 | 1 | L / N / LAMP | TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal | MKDS 1,5/3-5.08 (or MX126-5.0-03P) | Phoenix Contact / MaiXu | 30.10 | 3-pole 5.0 mm rising-cage screw terminal, >=300 V / 10 A: 1=Line in, 2=Neutral, 3=Lamp (switched Line out) |
| J2 | 1 | AVR-ISP | PinHeader_2x03_P2.54mm_Vertical | 2x3 2.54 mm header (or pads only / pogo) | generic | 2.58 | Standard 6-pin AVR ISP: 1 MISO 2 VCC 3 SCK 4 MOSI 5 RST 6 GND |
| J3 | 1 | LD2410B | LD2410B_Module | HLK-LD2410B | Hi-Link | 223.60 | 24 GHz mmWave presence radar module on a 1.27 mm 5-pin header at the board edge, antenna facing the front cover. 1=OUT(3.3V) 2=TX 3=RX 4=GND 5=VCC(5V). |
| J4 | 1 | CFG UART | PinHeader_1x03_P2.54mm_Vertical | 1x3 2.54 mm (pads only) | generic | 2.58 | Radar config/debug UART (3.3 V): 1=TX 2=RX 3=GND. For the LD2410B host tool. |
| MOV1 | 1 | 14D471K | Varistor_Disc_D16mm_P7.5mm | B72214S0471K101 (S14K300) / 14D471K | EPCOS/TDK / generic | 5.16 | MOV, 300 VAC rms / 470 V varistor voltage, 14 mm disc: surge clamp L-N after the fuse |
| NTC1 | 1 | 5D-9 | NTC_Disc_D11mm_P5mm | MF72-5D9 | Cantherm / generic | 4.30 | NTC inrush limiter 5 ohm cold, 9 mm disc, in series with the HLK-PM01 only (not the lamp path) |
| PS1 | 1 | HLK-PM01 | Converter_ACDC_Hi-Link_HLK-PMxx | HLK-PM01 | Hi-Link | 154.80 | Isolated AC-DC module, 85-265 VAC in -> 5 V / 0.6 A (3 W), reinforced isolation 4 kVAC (1 min typ) |
| Q1 | 1 | BTA16-600B | TO-220-3_Vertical | BTA16-600B | STMicroelectronics | 36.12 | Triac 16 A / 600 V, isolated tab TO-220. MT1(A1)=Line, MT2(A2)=Lamp, Gate from MOC3063. |
| R1 | 1 | 330R | R_0805_2012Metric | 0805 1% thick film | Yageo / Uniroyal | 0.34 |  |
| RB1 | 1 | 1M | R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | axial 0.5 W 350 V | Yageo / Uniroyal | 1.29 |  |
| RG1 | 1 | 180R | R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal | axial 0.5 W 350 V | Yageo | 1.29 | Triac gate resistor (MOC3063 pin4 -> BTA16 gate) |
| RL1,RS2 | 2 | 1k | R_0603_1608Metric | 0603 1% thick film | Yageo / Uniroyal | 0.13 |  |
| RP1,RR1 | 2 | 10k | R_0603_1608Metric | 0603 1% thick film | Yageo / Uniroyal | 0.13 |  |
| RS1 | 1 | 100R 2W | R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal | axial 2 W MO 350 V | Vishay | 2.58 | Snubber resistor (dv/dt) |
| RV1 | 1 | 10k | Potentiometer_Bourns_3386P_Vertical | 3386P-1-103 (10 k) | Bourns | 24.08 | Top-adjust 10 k trimmer: wiper (2) -> ADC3 sets the no-one delay 10 s..10 min |
| SW1 | 1 | OVERRIDE | SW_PUSH_6mm | 6x6x5 mm tactile (TS-1101 / PTS645) | XKB / C&K | 3.44 | Momentary push button: short = toggle Auto/Manual, long = force lamp off (firmware) |
| U1 | 1 | ATtiny13A-SU | SOIC-8_3.9x4.9mm_P1.27mm | ATTINY13A-SU | Microchip | 38.70 | 8-bit AVR MCU, SOIC-8, 1 kB flash. PB5=RESET, PB3=ADC3(delay pot), PB4=radar in, PB0=opto drive, PB1=LED, PB2=button. |
| U2 | 1 | MOC3063 | SMDIP-6_W9.53mm_Clearance8mm | MOC3063SR2M (gull-wing SMD) | onsemi / Liteon | 30.10 | Zero-cross opto-triac driver, SMD-DIP6 with 8 mm pad-row creepage, 7.5 kVrms isolation, Vdrm 600 V |

## Not populated (options)

| Designators | Value | Package | Purpose |
|---|---|---|---|
| C3 | 10nF | C_0603_1608Metric | DNP: RESET noise cap; keep small or omit so ISP works |
