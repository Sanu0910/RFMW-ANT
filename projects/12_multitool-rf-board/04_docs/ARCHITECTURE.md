# CRL-MT1: an original firmware-compatible multi-tool RF board

This project is an **original open-hardware design** for a hand-held multi-tool used in RFID/NFC development,
infrared remote work, sub-GHz radio experiments, 1-Wire/iButton work and general embedded hacking and education.

It is designed to be **firmware-compatible with the open-source Flipper Zero firmware** (GPLv3,
`flipperdevices/flipperzero-firmware`, and the community forks `DarkFlippers/unleashed-firmware`,
`RogueMaster/awesome-flipperzero-withModules`), because that firmware is free software anyone may run and port.
It is **not** a Flipper Zero and must not be presented as one:

- **No trademark, no trade dress.** The name "Flipper Zero", the Flipper Devices logo and the dolphin mascot are
  trademarks of Flipper Devices. This board uses none of them. It has its own name (CRL-MT1), its own case and its
  own silkscreen.
- **Original schematic and layout.** Flipper Devices has not published the Flipper Zero schematic, PCB or Gerbers.
  Nothing here is copied from their hardware files. The interconnect below is derived only from **public chip
  datasheets** and the **GPIO/peripheral assignments declared in the GPLv3 firmware** (`targets/f7/furi_hal/
  furi_hal_resources.{c,h}`), which are facts about how the firmware expects pins to be wired, not a hardware
  design file.
- **The ESP32 Marauder** (`justcallmekoko/ESP32Marauder`) is separate software for ESP32 Wi-Fi/BLE boards. It is
  **not** part of this board; it can run on an optional ESP32-S3 Wi-Fi add-on that plugs into the GPIO header, as a
  future module.

## Intended use and the limits
This is dual-use security-research and education hardware (RFID/NFC/IR/sub-GHz development, CTFs, teaching). Build and
use it only where you are authorised to:
- **Radios need certification before sale.** The CC1101 sub-GHz transmitter and the BLE radio require RF type
  approval (FCC / CE / in India WPC-ETA and BIS) before a product may be sold or, for some bands, operated.
- **Transmit only on bands and powers you are licensed for.** Sub-GHz TX, RFID emulation and IR can break radio,
  spectrum and access-control law depending on frequency, power and intent.
- Keep a copy of the firmware's own licences (GPLv3) with any firmware you ship.

---

## 1. Reference architecture (from the firmware)
The firmware's `furi_hal_resources.{c,h}` on the F7 target (STM32WB55) declares this wiring. The table is the
GPIO → peripheral map that any firmware-compatible board must honour.

### Main controller
- **STM32WB55RG** (QFN-68 or the module variant): Cortex-M4 application core + Cortex-M0+ running the BLE 5 stack,
  1 MB flash, 256 KB RAM, USB, on-chip 2.4 GHz radio. This single chip provides the MCU **and** Bluetooth LE.

### Two SPI buses
| Bus | MCU pins | On it |
|---|---|---|
| **SPI-R** ("radio"): SCK PA5, MISO PB4, MOSI PB5 | CC1101 (sub-GHz), ST25R3916 (NFC) | each with its own chip-select |
| **SPI-D** ("display"): SCK PD1, MISO PC2, MOSI PB15 | display controller, microSD card | each with its own chip-select |

### Subsystem pin map
| Subsystem | Part | Signals → STM32WB55 pin |
|---|---|---|
| Sub-GHz radio | **CC1101** | CS PD0, GDO0 PA1, (SPI-R); RF switch RF_SW_0 PC4 to the antenna |
| NFC (13.56 MHz) | **ST25R3916** | CS PE4, IRQ shares RFID_PULL PA2 (SPI-R) |
| 125 kHz RFID | analog front-end | carrier out PA15 (timer), carrier sense PA2, RF in PC5, data in via comparator |
| Display | **ST7565R / UC1701** 128×64 | CS PC11, DC/DI PB1, RST PB0 (SPI-D) |
| microSD | push-pull holder | CS PC12, card-detect PC10 (SPI-D) |
| Infrared | TX LED PB9 (timer), RX demod PA0 | 38 kHz remote work |
| 1-Wire / iButton | PB14 (open-drain, iBTN) | Dallas/iButton |
| Buttons | 5-way + back | Up PB10, Down PC6, Left PB11, Right PB12, OK PH3, Back PC13 |
| Haptics | vibromotor | PA8 (timer) |
| Sound | magnetic speaker | PB8 (timer PWM) |
| USB | STM32 USB-FS | DM PA11, DP PA12 |
| Debug | SWD | SWDIO PA13, SWCLK PA14 |
| Peripheral power | load switch | PA3 enables power to the SD/display/radio rail |
| I²C power bus | fuel gauge + charger | SDA PA10, SCL PA9 |
| External UART | USART1 | TX PB6, RX PB7 (on the GPIO header) |

### GPIO header (the "GPIO 1–18" style connector)
Eight user GPIO plus power and the buses are on a header: PA7, PA6, PA4, PB3, PB2, PC3, PC1, PC0, plus SWC/SWD,
USART1 TX/RX, the I²C power bus, 3V3, 5V and GND. This is what add-on modules (e.g. a Wi-Fi/BLE ESP32-S3 board
running ESP32 Marauder) plug into.

---

## 2. Power tree (original design)
Built around a single-cell Li-Po, as on comparable hand-helds:

```
USB-C VBUS 5V ─┬─ battery charger (BQ25896 / MCP73831-class) ── 1S Li-Po (2000 mAh) ── VBAT
               │                                                   │
               └─ 5V to GPIO header (switched)          fuel gauge (BQ27220 / MAX17048) on I²C power bus
                                                                   │
                      VBAT ── LM3281 buck 3.3V (+ RS3221 LDO for clean analog) ── +3V3 (MCU, display, SD, radios via load switch PA3)
```
- Buck-boost so 3.3 V holds across the whole Li-Po range (3.0–4.2 V).
- Load switch on PA3 cuts the peripheral rail in deep sleep for long standby.
- Fuel gauge and charger sit on the I²C "power" bus (PA9/PA10), matching the firmware's `i2c_power` bus.

## 2b. Board set (as on the reference design)
The reference product is **four FFC-joined PCBs** (sizes in `REFERENCE_PARTS.md`): the main board, an NFC/RFID board (74.0 × 31.92 mm), a small iButton/speaker/IR board (15.83 × 24.27 mm), and a PCB-spiral antenna board (125 kHz coil + 13.56 MHz loop). Summary of the split:
The reference product is **two PCBs joined by an 18-pin 0.5 mm FFC** (see `04_docs/REFERENCE_PARTS.md`):
- **Main board:** MCU, display, CC1101 sub-GHz, microSD, power (BQ25896 charger, BQ27220 gauge, LM3281 bucks,
  RS3221 LDO), buttons, LP5562 RGB-LED driver, two GPIO headers.
- **Sub board:** ST25R3916 NFC, 125 kHz RFID coil + AFE, IR TX/RX, speaker, vibro, iButton, over the FFC.
An original board may keep this split or integrate everything on one 4-layer board (the netlist here is one board).

## 3. Board plan (original)
| Item | Plan |
|---|---|
| Size | hand-held, 4-layer, 1.6 mm, ENIG (the reference product's main board is ≈ 95.43 × 36.15 mm; use your own outline) |
| Stack-up | L1 signal, L2 GND, L3 power, L4 signal |
| RF | CC1101 50 Ω match + LC filter to the sub-GHz antenna via the RF switch; ST25R3916 to a 13.56 MHz PCB loop antenna with its tuning network; 125 kHz coil driver + LC |
| Antennas | sub-GHz helical / PCB whip; 13.56 MHz PCB spiral; 125 kHz wound coil |
| Assembly | double-sided SMT, JLCPCB/PCBWay |

## 4. How this maps to the five linked repos
| Repo | What it is | Role here |
|---|---|---|
| `flipperdevices/flipperzero-firmware` | official firmware (GPLv3) | source of the GPIO/peripheral map; target firmware |
| `DarkFlippers/unleashed-firmware` | community firmware fork | alternative firmware; same pin map |
| `RogueMaster/awesome-flipperzero-withModules` | firmware build + app pack | alternative firmware |
| `djsime1/awesome-flipperzero` | curated link list | reference / apps |
| `justcallmekoko/ESP32Marauder` | ESP32 Wi-Fi/BLE tool (separate) | optional GPIO-header add-on module, not on this board |

None of these contain a PCB; all are software. This board is the original hardware that the first three can run on.

## 5. Status
Design in progress. `02_python/design.py` holds the netlist; `06_firmware/board_pins.h` the GPIO map for porting.
Full placement and routing is a follow-up (as in project 07). See `00_README.md`.
