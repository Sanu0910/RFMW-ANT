# Reference part list (from the official published schematics)

Facts extracted from the Flipper Devices main-board schematics the user provided (Power sheet 2/7, Peripherals
sheet 5/7, top block sheet 1/7, rev 12.1.F7B9C6 / 2023-02-08) and the public docs.flipper.net schematic. These are
the actual device's key parts and topology. Use them to make an **original** board's part selection accurate — do
not copy the layout, outline, silkscreen or mascot.

## Two-board architecture (important)
The product is **two PCBs joined by an 18-pin 0.5 mm FFC** (connector `FH34SRJ-18S-0.5SH`, ref X6):
- **Main PCB:** MCU, display, CC1101 sub-GHz, microSD, power, buttons, RGB LED driver, two GPIO headers.
- **Sub / antenna board:** 13.56 MHz NFC (ST25R3916), 125 kHz RFID coil + AFE, IR TX/RX, speaker, vibro motor,
  iButton contacts — all reached over the X6 flex (signals: SYS, ST25 SCLK/MISO/MOSI + BSS/CS, RFID IN/PULL/OUT/
  CARRIER, IR_TX/RX, SPEAKER, VIBRO, iBTN).

## Power (sheet 2/7)
| Ref | Part | Role |
|---|---|---|
| DD6 | **BQ25896RTWR** | 1-cell Li-ion charger + 5 V OTG boost, I²C |
| DD5 | **BQ27220YZFR** | battery fuel gauge, I²C; sense resistor R37 = **10 mΩ** |
| DD7, DA6 | **LM3281YFQR** | buck DC-DC → 3.3 V and ext-3.3 V (L13/L14/L15 = 470 nH) |
| DA5 | **RS3221-3.3YF3** | 3.3 V LDO (LDO_3.3V) |
| VT1 | **DMP1045U-7** | USB/BAT P-channel power-path FET |
| VT2 | **MMDT2907A** | dual PNP, power-path control |
| VT5 | **DMN313DLT7** | N-FET, OTG/VBUS control |
| X10 | **1.25-3P** | battery + NTC thermistor connector (remove R43 if the pack has an NTC) |

## Peripherals (sheet 5/7)
| Ref | Part | Role |
|---|---|---|
| DA4 | **LP5562** | 4-channel RGB LED driver (notification LED + LCD backlight), I²C |
| VD4 | **LTST-C19HE1WT** | RGB notification LED |
| X7 | **Molex 5033981892** | microSD push-pull holder |
| X9 | 2.54 mm 1×8 | GPIO header: +5V, PA7, PA6, PA4, PB3, PB2, PC3, GND |
| X8 | 2.54 mm 1×10 | GPIO header: ext3V3, SWCLK, GND, SWDIO, UART_TX, UART_RX, PC1, PC0, PB14, GND |
| X6 | FH34SRJ-18S-0.5SH | 18-pin FFC to the NFC/RFID/IR sub-board |
| VD5–VD25 | **ESD230/ESD241B1W0201** | ESD arrays on USB, SD and every exposed GPIO line |
| R10/R11/R32/R33 | **51 Ω** arrays | series resistors on exposed/FFC signals |
| VD36 | 1N4148 | iButton line protection (R69 = 1 kΩ) |

## Radios (public docs schematic)
| Part | Role |
|---|---|
| **STM32WB55** | MCU + BLE 5 (on-chip 2.4 GHz) |
| **CC1101** | sub-GHz, on SPI-R, with an antenna RF switch (RF_SW_0) to the helical antenna |
| **ST25R3916** | 13.56 MHz NFC reader/card/peer, on SPI-R, on the sub-board |

These confirm and refine `02_python/design.py`. The design now uses the real regulators (LM3281 + RS3221), the
LP5562 LED driver, the two-header GPIO split, ESD arrays, 51 Ω series resistors, and the 3-pin battery+NTC
connector; and documents the main/sub two-board split.

## RF and analog front-ends (sheets 4, 6, and the RFID sub-board)
These are the hard-to-get-right networks. Values are from the provided official schematics; they are a good
starting point for an original board (re-simulate and re-tune for your own layout and antennas).

### MCU + 2.4 GHz BLE (sheet 4/7)
- MCU **STM32WB55RGV6TR** (QFN-68). 32 MHz HSE crystal **CXD2-032000000** (ZQ2) with 18 pF loads (C4/C10);
  32.768 kHz LSE **SF32K32768D31T** (ZQ1, 12.5 pF).
- BLE antenna path: chip antenna **1001312** (ANT1) → π-match L1 2.7 nH, C5 0.8 pF, C6 0.3 pF, R72 0 Ω → BLE band
  filter **LFL182G45TC1A108** (FLT1) → MCU RF1.
- USB-C **Molex 105450-0101** (X1), CC pulldowns R1/R2 5.1 kΩ, D± series R8/R9 22 Ω, ESD VD1/VD2/VD3/VD26.
- Supply decoupling: 100 nF per VDD (C12–C14, C18, C22, C24) + 4.7 µF bulk (C15/C19/C20); SMPS inductor L3 10 µH.

### Sub-GHz CC1101 (sheet 6/7)
- **CC1101RGPR** (DD2), 26 MHz crystal **CXD2-026000000** (ZQ3), RBIAS R13 56 kΩ, 100 pF supply caps.
- Differential balun **Johanson B0310J50100AHF** (FLT2) to a single-ended RF path.
- Match: L4 3.3 nH, L5 6.8 nH, C32 1.2 pF, C33 0.6 pF, C34/C35 9 pF, C29/C38 100 pF.
- Two SPDT RF switches **Infineon BGS13S4N9** (SW1, SW2), controlled by RF_SW_0 / RF_SW_1, select band/antenna with
  an LC filter bank (L6/L9 2.2 nH, L11 2.7 nH, L16 56 nH, L17 27 nH, L19 27 nH, C42/C43 10 pF, C45 8.2 pF, C91 22 pF).
- Helical **sub-GHz antenna** (ANT2).

### 125 kHz RFID analog front-end (RFID sub-board)
Not a single chip — a discrete read/write channel:
- Coil driver H-bridge: **DMP2004 / DMN2004** FETs driving the read coil (ANT3/ANT4), carrier gated by RFID_CARRIER.
- Receive chain: two **LMV358** dual op-amps (DA3/DA4) forming a multi-stage band-pass/amplifier, then a
  **LMV331** comparator (DA5) producing the digital RFID_RF_IN; 1.65 V mid-rail reference (R28/R30/R32 divider),
  C42/C43 4.7 nF, C41 220 nF, etc.
- IR: **TSOP** 38 kHz receiver + IR LED with a driver FET; **iButton** via a 1 kΩ + 1N4148 protected line; speaker.
- Reached from the main board over a 6-pin FFC **FH34SRJ-6S** (older sub-board rev) / the 18-pin X6 on the current one.

### 13.56 MHz NFC (NFC sheet 3/4, 2022-08-03)
- Reader **ST25R3916-AQWT** (DD1), 27.12 MHz crystal **XRCGB27M120F3M00R0** (ZQ1), VDD decoupling 2.2 µF + 10 nF.
- Two antenna connectors **X6/X7** (FDX0022A1) feed the PCB loop antenna (ANT1/ANT2, ≈ 1.37 µH).
- Differential drive RFO1/RFO2 → EMC + matching network → RFI_P/RFI_N differential receive. Reference values:
  L1/L2 **270 nH** (EMC), series/parallel caps C5/C7 **62 pF**, C3/C8 **100 pF**, C1/C10 **100 pF**, C2/C9 **10 pF**,
  C4/C6 **680 pF**, C11/C15 **6 pF**, R1/R2 **0 Ω**.
- Standard ST app-note topology; tune Q and the series/parallel caps to **your own** loop and stack-up.

### iButton + speaker + IR sub-board (iButton sheet)
- **Speaker** BA1b = **BCE-MX8530A-03627** magnetic buzzer, driven by N-FET **DMN2058UW-7** (VT1b), gate 10 kΩ (R3b),
  series 150 Ω (R2b), SYS series 22 Ω (R1b).
- **iButton** three spring contacts X1b/X2b/X3b (mechanical pads PG-2.5-9.5-SM / PG-2.5-8.0-SM / PG-3.0-10.0-SM),
  ESD **ESD230B1W0201** (VD1b) on the 1-Wire line.
- **IR TX**: three IR LEDs **VSMY14940** (VD2b/VD3b/VD4b) each with a 39 Ω series resistor (R5b/R9b/R10b).
- **IR RX**: **TSOP75338TR** 38 kHz demodulator, 100 nF decoupling (C1b), 10 kΩ pull-up.
- Joined to the main board by a **6-pin FFC** X4b (SYS, SPEAKER, iButton, IR_TX, IR_RX, GND).

> All RF values above are the reference device's. For an original board, treat them as a starting point, then
> re-match to your own antennas and stack-up in a simulator (openEMS / Hertzon, see `docs/`).

## Physical board set (from the official assembly drawings / docs images)
The reference product is **four stacked PCBs**, joined by FFCs. Sizes and roles (facts from the assembly drawings):

| Board | Size | Holds | Key labels |
|---|---|---|---|
| Main PCB | 95.43 × 36.15 mm | MCU, display, CC1101 sub-GHz, microSD, power, buttons, LED driver, GPIO headers | — |
| NFC/RFID PCB | 74.00 × 31.92 mm | ST25R3916 NFC + 125 kHz RFID AFE (two QFNs) | ANT1/ANT2 (NFC), ANT3/ANT4 (125 kHz), SYS2, 3V_1, 5V_1, GND_2, BAT +/− |
| iButton PCB | 15.83 × 24.27 mm | iButton contacts, speaker, IR TX/RX | SPEAKER, BTN, R_TX, R_RX, SYS |
| Antenna PCB | (long spiral) | 125 kHz read coil (large PCB spiral) + 13.56 MHz NFC loop | — |

So the "sub-board" in the earlier notes is really these three boards (NFC/RFID + iButton + antenna coil), each on its
own flex. An original design can keep this 4-board stack **or** fold it onto fewer boards; the netlist here is drawn
as one logical design and can be partitioned at layout time.

> Dimensions and labels only — the assembly artwork, outlines, silkscreen and mascot are not reproduced here. Give
> your own board its own outline and name.
