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

### 13.56 MHz NFC
- **ST25R3916** reader on SPI-R with its EMC filter + matching network to a PCB loop antenna (standard ST app-note
  topology; tune Q and the series/parallel caps to the loop).

> All RF values above are the reference device's. For an original board, treat them as a starting point, then
> re-match to your own antennas and stack-up in a simulator (openEMS / Hertzon, see `docs/`).
