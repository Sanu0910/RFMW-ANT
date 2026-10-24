# Two ways to build it

There are two routes to a working firmware-compatible multi-tool. Both use the same GPIO pin map
(`06_firmware/board_pins.h`); they differ only in whether you design a PCB or wire modules.

Keep both legal: your own name and silkscreen (no Flipper Devices trademark, logo or dolphin mascot artwork — the
mascot and its animations are copyrighted), and transmit only on bands/powers you are licensed for.

---

## Route A — simple DIY build from off-the-shelf modules (buildable today)
This is the fast path, like the community "DIY STM32WB55" guides. You solder ready-made modules to a core board and
flash the firmware. No custom PCB, no RF matching to design.

**Modules**
| Function | Module | Notes |
|---|---|---|
| MCU + BLE | WeAct **STM32WB55CGU6** core board | the brain; USB + BLE on board |
| Sub-GHz | **CC1101** module (e.g. E07-M1101D) | 433/868/915 MHz |
| Storage | **microSD** SPI module | firmware assets |
| Display | SPI LCD: **ST7735** 1.8" TFT, or a 128×64 ST7565/UC1701 for the closest match | the firmware's native panel is 128×64 mono |
| IR | IR LED + driver transistor, and a **TSOP** 38 kHz receiver | |
| Power | **TP4056** charge module + 1S Li-Po | add a boost/LDO for a clean 3.3 V |
| Buttons | 6 tact switches | 5-way + back |

**Wiring** (module pin → STM32WB55 pin, from `board_pins.h`)
| Module | Signal | STM32WB55 |
|---|---|---|
| CC1101 | SCK / MISO / MOSI | PA5 / PB4 / PB5 (SPI-R) |
| CC1101 | CSN / GDO0 | PD0 / PA1 |
| microSD | SCK / MISO / MOSI / CS | PD1 / PC2 / PB15 / PC12 (SPI-D) |
| Display | SCK / MOSI / CS / DC / RST | PD1 / PB15 / PC11 / PB1 / PB0 |
| IR | TX / RX | PB9 / PA0 |
| iButton | data | PB14 |
| Buttons | Up/Dn/L/R/OK/Back | PB10 / PC6 / PB11 / PB12 / PH3 / PC13 |

**Flash**: write the Flipper OTP region for your board, then load the firmware over USB (qFlipper / STM32CubeProgrammer).
Community guides such as `ajvizganapathy-pixel/FlipperZero-DIY-STM32WB55-NucleusDark` and the
`FuckingCheapFlipperZero` project document the OTP-and-flash steps. This route omits the 13.56 MHz NFC and 125 kHz
RFID front-ends (those need the ST25R3916 / analog AFE, hard to do with generic modules).

## Route B — the full custom PCB (this project)
A single 4-layer board that integrates everything, including NFC and 125 kHz RFID, like the reference product.
`02_python/design.py` is its netlist; `04_docs/ARCHITECTURE.md` the plan. This is the larger job (schematic → ERC →
RF matching → routing → Gerbers), done over several steps as in project 07.

---

## Reference facts (official Flipper hardware docs)
Flipper Devices publishes the main-board schematic (docs.flipper.net → development → hardware → schematic) and the
assembly drawing (`MAIN_PCB_12.1.F7B9C6`). Useful facts confirmed from the assembly drawing provided:
- **Main board outline ≈ 95.43 × 36.15 mm.**
- Big edge headers **X8 / X9** carry the GPIO and the display/coprocessor connections; **ANT2** is the sub-GHz
  helical antenna; **HG3** the 128×64 display; **DD1** the STM32WB55; **X1** USB-C; **X7** microSD; **X10** the IR
  area; a NTC note ("remove R43 if NTC") marks the battery temperature option.
- These confirm the architecture in `ARCHITECTURE.md`. Use them to size your own (differently shaped, differently
  branded) board — do not copy the outline art, the silkscreen or the mascot.
