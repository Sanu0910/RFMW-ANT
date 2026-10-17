# CRL-TRK-2W-01 Bill of Materials (rev A0)

Generated from `02_python/design.py` by `make_bom.py`. Assembly BOM for JLCPCB: `03_fab/CRL-TRK-2W-01_BOM_JLCPCB.csv` (fill the LCSC column at quotation).

**85 line items, 145 placed parts**, plus 5 DNP and 20 test pads.

| Designators | Qty | Value | Package | MPN | Manufacturer | Description |
|---|---|---|---|---|---|---|
| C1 | 1 | 100nF/16V | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C2,C6 | 2 | 100nF/100V | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C3 | 1 | 22uF/63V | CP_Elec_6.3x7.7 | EEE-FK1J220P | Panasonic | Al-electrolytic 22 uF 63 V, AEC-Q200, bulk / input damping |
| C4,C5 | 2 | 2.2uF/100V | C_1210_3225Metric | 1210 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C7 | 1 | 2.2nF/50V | C_0402_1005Metric | 0402 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C8,C9 | 2 | 22uF/10V | C_1206_3216Metric | 1206 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C10 | 1 | 100nF | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C11 | 1 | 1uF/25V | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C12,C17,C25,C34 | 4 | 10uF/10V | C_0805_2012Metric | 0805 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C13 | 1 | 4.7uF/10V | C_0805_2012Metric | 0805 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C14,C15,C21,C23,C26,C29,C30,C31,C35,C36,C40,C41,C42,C44,C46,C48,C50 | 17 | 100nF | C_0402_1005Metric | 0402 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C16 | 1 | 1uF/10V | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C18,C19 | 2 | 1nF | C_0402_1005Metric | 0402 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C20 | 1 | 22uF/10V | C_0805_2012Metric | 0805 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C22 | 1 | 1uF | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C24 | 1 | 100uF/6.3V | C_1210_3225Metric | 1210 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C27 | 1 | 33pF | C_0402_1005Metric | 0402 C0G 50V | Murata / Samsung |  |
| C28 | 1 | 10pF | C_0402_1005Metric | 0402 C0G 50V | Murata / Samsung |  |
| C37 | 1 | 10nF | C_0402_1005Metric | 0402 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| C43,C45,C47,C49 | 4 | 10nF/100V | C_0603_1608Metric | 0603 MLCC X7R/X5R, AEC-Q200 | Murata / Samsung |  |
| D1 | 1 | SMBJ33CA | D_SMB | SMBJ33CA | Littelfuse | TVS 600 W bidirectional 33 V stand-off (reverse battery safe) |
| D2,D4 | 2 | B5819W | D_SOD-123 | B5819W | MDD / Diodes Inc | Schottky 40 V 1 A, OR-ing buck -> charger |
| D3,D9,D10,D11,D12 | 5 | BAT54S | SOT-23 | BAT54S | Nexperia | Dual Schottky clamp to rails |
| D5 | 1 | GREEN | LED_0603_1608Metric | LTST-C191KGKT | Lite-On | LED green 0603 - system status |
| D6 | 1 | RED | LED_0603_1608Metric | LTST-C191KRKT | Lite-On | LED red 0603 - charging |
| D7 | 1 | SMF5.0A | D_SOD-123F | SMF5.0A | Littelfuse | TVS 200 W 5 V on modem VBAT (SIMCom recommendation) |
| D8 | 1 | YELLOW | LED_0603_1608Metric | LTST-C191KSKT | Lite-On | LED yellow 0603 - network |
| D13 | 1 | 1N4148W | D_SOD-123 | 1N4148W-7-F | Diodes Inc | Relay flyback to protected supply |
| F1 | 1 | 2A | Fuse_1206_3216Metric | 0466002.NRHF | Littelfuse | Fuse 2 A fast 63 V 1206 (plus 3 A blade fuse in harness) |
| FB1 | 1 | 600R@100M | L_0805_2012Metric | BLM21PG601SN1D | Murata | Ferrite bead 600 R 0805 1.5 A, conducted-EMI pi filter |
| J1 | 1 | VEHICLE 2x4 | Molex_Micro-Fit_3.0_43045-0812_2x04_P3.00mm_Vertical | 43045-0812 | Molex | Micro-Fit 3.0 2x4 vertical header, harness via IP67 gland |
| J2 | 1 | BATTERY 18650 | JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal | S3B-PH-SM4-TB(LF)(SN) | JST | Battery pack: 1S 18650 with PCM + 10k NTC (103AT) - 1 BAT+ 2 NTC 3 BAT- |
| J3 | 1 | USB-C | USB_C_Receptacle_HRO_TYPE-C-31-M-12 | TYPE-C-31-M-12 | Korean Hroparts | USB-C 2.0 receptacle (service: flash, JTAG, logs, charge) |
| J4 | 1 | DEBUG TC2050 | Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical | Tag-Connect TC2050-IDC-NL (footprint only) | Tag-Connect | JTAG + UART0 + EN production header |
| J5 | 1 | NANO-SIM | nanoSIM_GCT_SIM8060-6-0-14-00 | SIM8060-6-0-14-00-A | GCT | Nano-SIM push-pull holder (dev / non-eSIM builds) |
| J6 | 1 | LTE ANT | U.FL_Hirose_U.FL-R-SMT-1_Vertical | U.FL-R-SMT-1(10) | Hirose | LTE antenna: 698-2700 MHz flex PCB antenna on enclosure wall (e.g. Taoglas FXUB63) |
| J7 | 1 | GNSS ANT | U.FL_Hirose_U.FL-R-SMT-1_Vertical | U.FL-R-SMT-1(10) | Hirose | GNSS antenna: active L1/L5 patch (gain <= 25 dB) under the lid, sky-facing |
| L1 | 1 | 22uH | L_Bourns_SRN6045TA | SRN6045TA-220M | Bourns | 22 uH semi-shielded power inductor 6x6 mm |
| L2 | 1 | 47nH | L_0402_1005Metric | LQG15HS47NJ02D | Murata | Bias-T choke, >500 R at L1/L5 (u-blox integration manual) |
| Q1 | 1 | BUK7M12-60EX | LFPAK33 | BUK7M12-60EX | Nexperia | N-MOSFET 60 V 12 mOhm AEC-Q101, ideal-diode pass FET |
| Q2 | 1 | 2N7002 | SOT-23 | 2N7002K-7 | Diodes Inc | Open-drain PWRKEY driver (PWRKEY has internal pull-up, never tie to GND) |
| Q3 | 1 | MMBT3904 | SOT-23 | MMBT3904 | onsemi | NETLIGHT LED driver |
| Q4 | 1 | BUK9M53-60EX | LFPAK33 | BUK9M53-60EX | Nexperia | Logic-level N-MOSFET 60 V AEC-Q101, relay coil <= 500 mA |
| R1 | 1 | 1M | R_0603_1608Metric | 0603 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R2 | 1 | 330k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R3 | 1 | 160k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R4 | 1 | 316k | R_0603_1608Metric | 0603 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R5,R14,R17,R18,R26,R50 | 6 | 100k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R6 | 1 | 100k | R_0603_1608Metric | 0603 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R7 | 1 | 1M | R_1206_3216Metric | 1206 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R8 | 1 | 68k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R9 | 1 | 1.5k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R10 | 1 | 1.78k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R11 | 1 | 15k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R12 | 1 | 46.4k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R15,R16 | 2 | 1M | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R19,R20,R23,R37,R40,R48,R53,R54 | 8 | 10k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R21,R22 | 2 | 5.1k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R24,R25,R28,R33,R34 | 5 | 1k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R27,R38,R39 | 3 | 4.7k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R29,R30,R31 | 3 | 22R | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R32,R36 | 2 | 0R | R_0402_1005Metric | 0402 0R jumper | Yageo / Vishay |  |
| R35 | 1 | 10R | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R41,R45,R47 | 3 | 100k | R_1206_3216Metric | 1206 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R42,R46 | 2 | 22k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R43 | 1 | 4.7k | R_1206_3216Metric | 1206 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R44 | 1 | 47k | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| R49,R51,R52 | 3 | 100R | R_0402_1005Metric | 0402 1% thick film, AEC-Q200 | Yageo / Vishay |  |
| SW1 | 1 | RESET | SW_Push_1P1T_XKB_TS-1187A | TS-1187A-B-A-B | XKB | Tact switch 5.1x5.1 mm |
| SW2 | 1 | BOOT | SW_Push_1P1T_XKB_TS-1187A | TS-1187A-B-A-B | XKB | Tact switch 5.1x5.1 mm |
| U1 | 1 | LM74700-Q1 | SOT-23-6 | LM74700QDBVRQ1 | TI | Ideal diode controller, reverse battery protection, AEC-Q100 |
| U2 | 1 | LM5164-Q1 | HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm_ThermalVias | LM5164QDDARQ1 | TI | 100 V 1 A sync buck, 10 uA IQ, AEC-Q100 |
| U3 | 1 | BQ24074 | VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm | BQ24074RGTR | TI | 1-cell Li-ion charger with power path, 10.5 V OVP, OUT reg 4.4 V |
| U4 | 1 | LC709203F | WDFN-8-1EP_4x3mm_P0.65mm_EP2.4x1.8mm | LC709203FQH-01TWG | onsemi | Fuel gauge, I2C 0x0B, 2 uA sleep (stands in for MAX17048) |
| U5 | 1 | TLV75733P | SOT-23-5 | TLV75733PDBVR | TI | LDO 3.3 V 1 A, 25 uA IQ, always-on logic rail |
| U6,U7 | 2 | TPS22917 | SOT-23-6 | TPS22917DBVR | TI | Load switch 2 A: modem VBAT hard power-cycle (watchdog) |
| U8 | 1 | ESP32-S3-WROOM-1-N8R2 | ESP32-S3-WROOM-1_EdgeAntenna | ESP32-S3-WROOM-1-N8R2 | Espressif | Wi-Fi/BLE5 MCU module, 8 MB flash, 2 MB quad PSRAM |
| U9 | 1 | USBLC6-2SC6 | SOT-23-6 | USBLC6-2SC6 | STMicroelectronics | USB ESD protection |
| U10 | 1 | W25Q128JV | SOIC-8_5.3x5.3mm_P1.27mm | W25Q128JVSIQ | Winbond | 128 Mbit SPI NOR flash - offline track log (AIS-140 store-and-forward) |
| U11 | 1 | SIM7080G | SIMCom_SIM7080G_LCC-77 | SIM7080G | SIMCom | LTE Cat-M1/NB-IoT module, 3 uA PSM, India bands B3/B5/B8/B28 |
| U12 | 1 | TXS0108E | TSSOP-20_4.4x6.5mm_P0.65mm | TXS0108EPWR | TI | 1.8 V <-> 3.3 V translator; OE from VDD_EXT so it is Hi-Z while modem is off |
| U13 | 1 | ESDA6V1-5SC6 | SOT-23-6 | ESDA6V1-5SC6 | STMicroelectronics | SIM ESD array (<50 pF) |
| U14 | 1 | NEO-F10N | ublox_NEO | NEO-F10N-00B | u-blox | L1/L5 dual-band GNSS, GPS/GAL/BDS/QZSS + NavIC (AIS-140), -167 dBm |
| U15 | 1 | IIM-42652 | Bosch_LGA-14_3x2.5mm_P0.5mm | IIM-42652 | TDK InvenSense | 6-axis IMU, -40..105 C industrial (ICM-42688 family), I2C 0x68 |
| U16 | 1 | RV-3028-C7 | MicroCrystal_C7_SON-8_1.5x3.2mm_P0.9mm | RV-3028-C7 32.768kHz 1ppm-TA-QC | Micro Crystal | RTC 45 nA, I2C 0x52, EVI = lid tamper time-stamp |

## Not populated (tuning / variant options)

| Designators | Value | Package | Purpose |
|---|---|---|---|
| C32,C33,C38,C39 | DNP | C_0402_1005Metric | 0402 C0G (tune) |
| R13 | 10k | R_0402_1005Metric | fit only when the pack has no NTC |

## Off-board items (harness / enclosure)

| Item | Recommended part | Notes |
|---|---|---|
| LTE antenna | Taoglas FXUB63 (698-3000 MHz flex, U.FL, 100 mm) | stick to the enclosure wall opposite the GNSS antenna |
| GNSS antenna | active L1/L5 patch with U.FL lead (gain <= 25 dB, 3.0-3.3 V) | lid, sky-facing, >= 15 mm from LTE antenna |
| Battery | 1S 18650 Li-ion 2500-3500 mAh with PCM + 10k NTC (B=3435), JST PH 3-pin | cell holder / foam in the enclosure |
| Harness | Molex Micro-Fit 3.0 43025-0800 receptacle + 43030 crimps, 0.5-0.75 mm2 | inline 3 A ATO blade fuse on +12 V |
| Enclosure | IP67 ABS/PC-ABS, 80x60x30 mm class, M12 cable gland, Gore vent | UV-stabilised |
