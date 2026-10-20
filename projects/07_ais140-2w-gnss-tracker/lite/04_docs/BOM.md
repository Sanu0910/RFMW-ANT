# CRL-TRK-2W-L1 Bill of Materials (rev A0) - Samay Track 2W Lite

Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: `03_fab/CRL-TRK-2W-L1_BOM_JLCPCB.csv` (fill the LCSC column at quotation); costed BOM: `03_fab/CRL-TRK-2W-L1_BOM_costed.csv`.

**52 line items, 85 placed parts (all top side)**, plus 2 DNP and 18 test pads.

## Cost summary (estimate, 1 000 pcs, Rs 88 / USD, excl. GST)

| Group | Rs |
|---|---|
| Passives | 88 |
| Discretes | 26 |
| Connectors | 58 |
| ICs | 86 |
| Modules | 827 |
| **Board parts** | **1,086** |
| Bare PCB - 60 x 45 mm 2-layer FR-4 1.6 mm, HASL lead-free, green | 25 |
| SMT assembly - single-sided, ~95 placements, stencil amortised | 55 |
| Battery - 1S LiPo 300 mAh 402535 with PCM, JST PH 2-pin lead, BIS IS 16046 | 55 |
| LTE/GSM antenna - FPC 698-2700 MHz, 100 mm IPEX/U.FL lead, adhesive | 35 |
| GNSS antenna - passive 25 x 25 x 4 mm ceramic L1 patch, 80 mm U.FL lead | 45 |
| Enclosure - ABS/PC 70 x 55 x 22 mm, IP65 gasket, cable gland (or the 2W-01 IP67 box) | 70 |
| Harness - 4-core 0.5 mm2, JST XH 4P housing, inline 2 A ATO fuse holder, 1 m | 45 |
| Relay (optional) - 12 V 30 A automotive relay + socket for the immobiliser kit | 0 |
| Packaging + manual - box, foam, Quick-start card, IMEI label | 25 |
| **Total hardware per unit** | **1,441** |

Business-plan target for the Lite (07_marketing/BUSINESS_PLAN_NOTES.md section 5): Rs 1,200-1,500. Cost-down options: SC7A20 for the LIS3DH (-Rs 30), TP4054 for the MCP73831 (-Rs 28), generic IPEX connectors (-Rs 40).

## Placed parts

| Designators | Qty | Value | Package | MPN | Manufacturer | Unit Rs | Description |
|---|---|---|---|---|---|---|---|
| C1 | 1 | 10uF/50V | C_1210_3225Metric | 1210 MLCC X5R/X7R | Samsung / Murata | 7.04 |  |
| C2 | 1 | 4.7uF/50V | C_1206_3216Metric | 1206 MLCC X5R/X7R | Samsung / Murata | 2.64 |  |
| C3 | 1 | 100nF/50V | C_0603_1608Metric | 0603 MLCC X5R/X7R | Samsung / Murata | 0.26 |  |
| C4,C5 | 2 | 22uF/10V | C_1206_3216Metric | 1206 MLCC X5R/X7R | Samsung / Murata | 2.64 |  |
| C6,C7 | 2 | 4.7uF/10V | C_0603_1608Metric | 0603 MLCC X5R/X7R | Samsung / Murata | 0.53 |  |
| C8,C9 | 2 | 100uF/6.3V | C_1210_3225Metric | 1210 MLCC X5R/X7R | Samsung / Murata | 13.20 |  |
| C10,C13,C14,C17,C22,C26 | 6 | 100nF | C_0402_1005Metric | 0402 MLCC X5R/X7R | Samsung / Murata | 0.07 |  |
| C11 | 1 | 33pF | C_0402_1005Metric | 0402 C0G 50V | Samsung / Murata | 0.07 |  |
| C12 | 1 | 10pF | C_0402_1005Metric | 0402 C0G 50V | Samsung / Murata | 0.07 |  |
| C15,C20,C27 | 3 | 1uF | C_0402_1005Metric | 0402 MLCC X5R/X7R | Samsung / Murata | 0.18 |  |
| C16,C21 | 2 | 10uF/10V | C_0603_1608Metric | 0603 MLCC X5R/X7R | Samsung / Murata | 0.88 |  |
| C28 | 1 | 10nF/100V | C_0603_1608Metric | 0603 MLCC X5R/X7R | Samsung / Murata | 0.35 |  |
| C29 | 1 | 1nF | C_0402_1005Metric | 0402 MLCC X5R/X7R | Samsung / Murata | 0.07 |  |
| D1 | 1 | SMBJ24CA | D_SMB | SMBJ24CA | Littelfuse / MDD | 4.40 | TVS 600 W bidirectional 24 V stand-off, 38.9 V clamp (load dump) |
| D2,D3,D4 | 3 | SS34 | D_SMA | SS34 | MDD | 1.76 | Schottky 40 V 3 A series reverse-polarity diode |
| D5 | 1 | SMF5.0A | D_SOD-123F | SMF5.0A | Littelfuse | 2.64 | TVS 200 W 5 V on modem VBAT (Quectel recommendation) |
| D6 | 1 | 1N4148W | D_SOD-123 | 1N4148W-7-F | Diodes Inc | 0.53 | Relay flyback to protected supply |
| D7 | 1 | YELLOW | LED_0603_1608Metric | KT-0603Y | Kingbright / Hubei KENTO | 0.88 | LED yellow 0603 - network |
| D8 | 1 | GREEN | LED_0603_1608Metric | KT-0603G | Kingbright / Hubei KENTO | 0.88 | LED green 0603 - modem on |
| D9 | 1 | RED | LED_0603_1608Metric | KT-0603R | Kingbright / Hubei KENTO | 0.88 | LED red 0603 - charging |
| F1 | 1 | 2A | Fuse_1206_3216Metric | 0466002.NRHF | Littelfuse | 17.60 | Fuse 2 A fast 63 V 1206 (plus 2 A blade fuse in harness) |
| J1 | 1 | VEHICLE 4P | JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical | B4B-XH-A(LF)(SN) | JST | 3.52 | XH 2.5 mm 4-pin header; harness: red +12V, black GND, yellow IGN, blue relay |
| J2 | 1 | LiPo 300mAh | JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal | S2B-PH-SM4-TB(LF)(SN) | JST | 5.28 | Battery: 1S LiPo 300 mAh (402535 class) with PCM, JST PH 2-pin - 1 BAT+ 2 BAT- |
| J4 | 1 | LTE ANT | U.FL_Hirose_U.FL-R-SMT-1_Vertical | U.FL-R-SMT-1(10) | Hirose | 24.64 | LTE/GSM antenna: 698-2700 MHz FPC antenna with U.FL lead on the enclosure wall |
| J5 | 1 | GNSS ANT | U.FL_Hirose_U.FL-R-SMT-1_Vertical | U.FL-R-SMT-1(10) | Hirose | 24.64 | GNSS antenna: passive 25x25x4 mm ceramic L1 patch with U.FL lead, under the lid, sky-facing (L76K has an internal LNA) |
| L1 | 1 | 22uH | L_Bourns_SRN6045TA | SRN6045TA-220M | Bourns | 22.00 | 22 uH semi-shielded power inductor 6x6 mm, Isat ~2 A |
| Q1 | 1 | AO3401A | SOT-23 | AO3401A | AOS | 2.20 | P-MOSFET 30 V 4 A, 50 mOhm: battery -> VSYS when external power is gone |
| Q2 | 1 | 2N7002 | SOT-23 | 2N7002K-7 | Diodes Inc | 1.06 | Open-drain PWRKEY driver (PWRKEY has an internal pull-up) |
| Q3,Q4 | 2 | BSS138 | SOT-23 | BSS138 | onsemi | 1.32 | Level shifter: modem TXD (1.8 V) -> L76K RXD (3.3 V) |
| Q5,Q7,Q8 | 3 | MMBT3904 | SOT-23 | MMBT3904 | onsemi | 0.88 | Ignition sense transistor |
| Q6 | 1 | AO3400A | SOT-23 | AO3400A | AOS | 2.20 | N-MOSFET 30 V 5.7 A logic-level, relay coil <= 300 mA |
| R1 | 1 | 2.61k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R2,R30,R32,R33 | 4 | 1k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R3 | 1 | 6.8k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R4,R8,R15,R26,R28 | 5 | 100k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R5 | 1 | 1M | R_0603_1608Metric | 0603 1% thick film | Uniroyal / Yageo | 0.13 |  |
| R6 | 1 | 33k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R7 | 1 | 300k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R9 | 1 | 220k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R11,R12,R13 | 3 | 22R | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R14 | 1 | 0R | R_0603_1608Metric | 0603 0R jumper | Uniroyal / Yageo | 0.13 |  |
| R18,R19,R20,R21,R25,R34 | 6 | 10k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R22,R23,R29,R31 | 4 | 4.7k | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| R24 | 1 | 47k | R_1206_3216Metric | 1206 1% thick film | Uniroyal / Yageo | 0.26 |  |
| R27 | 1 | 100R | R_0402_1005Metric | 0402 1% thick film | Uniroyal / Yageo | 0.07 |  |
| U1 | 1 | XL1509-ADJ | SOIC-8_3.9x4.9mm_P1.27mm | XL1509-ADJE1 | XLSEMI | 8.80 | Buck 4.5-40 V in, 2 A, 150 kHz, adjustable (VFB 1.23 V) |
| U2 | 1 | MCP73831-2 | SOT-23-5 | MCP73831T-2ACI/OT | Microchip | 30.80 | Li-ion linear charger 4.20 V, 500 mA max |
| U3 | 1 | EC200U-CN | Quectel_EC200U_LCC-144 | EC200UCNAA-N05-SNNSA | Quectel | 572.00 | LTE Cat-1 bis + GSM/GPRS, QuecOpen, B1/3/5/8/34/38/39/40/41 + GSM 900/1800 |
| U5 | 1 | L76K | Quectel_L76K | L76KB-A58 | Quectel | 211.20 | GPS + BeiDou + GLONASS + QZSS receiver, L1, 10.1 x 9.7 mm LCC-18 |
| U6 | 1 | AP2112K-3.3 | SOT-23-5 | AP2112K-3.3TRG1 | Diodes Inc | 7.04 | LDO 3.3 V 600 mA, EN from modem GPIO (GNSS power gate) |
| U7 | 1 | LIS3DH | LGA-16_3x3mm_P0.5mm_LayoutBorder3x5y | LIS3DHTR | STMicroelectronics | 39.60 | 3-axis accelerometer, I2C 0x18 (SA0 = GND), 2 uA low-power, wake-on-motion |
| U8 | 1 | MFF2 eSIM | MFF2_eSIM_DFN-8_6x5mm | M2M MFF2 eUICC (operator-supplied, e.g. Jio / Airtel / Vi IoT) | Operator / Thales / G+D | 44.00 | Embedded SIM, MFF2 DFN-8, -40..105 C, soldered (vibration-proof, no holder) |

## Not populated (tuning / options)

| Designators | Value | Package | Purpose |
|---|---|---|---|
| C19 | DNP | C_0603_1608Metric | L-match with R14: shunt C or L on the bench |
| R10 | 0R | R_0402_1005Metric | fit for permanent auto power-on (no PWRKEY shutdown) |
