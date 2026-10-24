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
