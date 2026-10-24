# 12: CRL-MT1 — original firmware-compatible multi-tool RF board

An **original open-hardware** hand-held multi-tool for RFID/NFC, infrared, sub-GHz, 1-Wire/iButton and general
embedded work, designed to run the open-source Flipper Zero firmware (GPLv3) and its community forks.

**It is not a Flipper Zero and must not be presented as one.** It uses none of Flipper Devices' trademarks, logo,
dolphin mascot, trade dress, or hardware design files. The interconnect is derived only from public chip datasheets
and the GPIO/peripheral map the open firmware declares. See `04_docs/ARCHITECTURE.md` for the full reasoning and the
legal / RF-certification boundaries (sub-GHz and BLE radios need type approval before sale; transmit only where
licensed).

## Status
- **Done:** architecture from the firmware pin map, schematic netlist (`02_python/design.py`), engineering BOM,
  firmware GPIO header (`06_firmware/board_pins.h`).
- **Not done yet:** KiCad schematic + ERC, placement, RF matching design, routing, Gerbers. These are a multi-step
  follow-up, as in project 07 (which took a full design cycle). This project is at the **schematic-netlist** stage.

| Folder | Content |
|---|---|
| `02_python/design.py` | parts + nets (source of truth) → `03_fab/BOM_engineering.csv`, `netlist.txt` |
| `03_fab/` | engineering BOM and flat netlist |
| `04_docs/ARCHITECTURE.md` | chip list, GPIO→peripheral map, power tree, board plan, legal notes |
| `06_firmware/board_pins.h` | GPIO map for porting firmware |

## Key parts
STM32WB55RG (MCU + BLE) · CC1101 (sub-GHz) · ST25R3916 (13.56 MHz NFC) · 125 kHz RFID AFE · ST7565R display ·
microSD · IR TX/RX · iButton · BQ25896 charger + BQ27220 gauge + TPS63802 buck-boost · USB-C · GPIO/module header.

## Regenerate
```bash
cd 02_python && python3 design.py
```

## Next steps (ask to continue)
1. KiCad symbol/footprint library for the non-stock parts, then a hierarchical schematic + ERC.
2. RF matching: CC1101 50 Ω filter, ST25R3916 13.56 MHz antenna tuning, 125 kHz LC.
3. 4-layer placement and routing, DRC, Gerbers, 3D — the project-07 flow.
4. Optional ESP32-S3 Wi-Fi/BLE add-on module (can run ESP32 Marauder) on the GPIO header — a separate board.
