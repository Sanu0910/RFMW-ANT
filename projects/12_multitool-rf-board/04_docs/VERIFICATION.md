# NOVA-RF1 — Level-1 design verification (no hardware)

Run: `python3 02_python/verify_design.py`, `kicad-cli sch erc`, `kicad-cli pcb drc`.
These confirm the **design** is self-consistent and firmware-compatible. They do **not** prove
it works on real silicon — that needs a built prototype (see "Hardware bring-up" below).

## Results (2026-10-24)

| Check | Result |
|---|---|
| **Firmware pin-map** (STM32WB55 vs Flipper F7 `furi_hal_resources`) | **38/38 PASS** — every GPIO the firmware expects is wired to the right net |
| **Power + ground** (15 ICs) | **15/15 PASS** — each IC has its supply rail(s) + GND |
| **Decoupling** | **PASS** — a cap on every IC supply (USBLC6 ESD array exempt) |
| **Net sanity** | **PASS** — no single-pad rails; GND is the largest net (78 nodes) |
| **Schematic ERC** | **0 errors** (warnings are box-symbol/footprint-link only) |
| **Board DRC** | run on the routed board; see PCB_STATUS.md |

## Bugs this pass caught and fixed
1. Analog LDO output `+3V3_LDO` and the RFID op-amp rail `A3V3` were different net names — the
   op-amps' clean rail wasn't actually driven. **Fixed:** RS3221 now outputs `A3V3`.
2. The 125 kHz coil driver's `+5V` had no source. **Fixed:** driven from `VSYS`.
3. No decoupling on the analog rail. **Fixed:** added `C_A3V3` (1 uF).

## How to check it yourself
- **KiCad (free):** open `01_kicad/nova-rf1.kicad_sch` / `.kicad_pcb` → run ERC and DRC, use the 3D viewer.
- **Gerber preview:** upload `03_fab/NOVA-RF1_gerbers.zip` to jlcpcb.com or gerblook.org to see the real board.
- **Firmware:** compare pins against `targets/f7/furi_hal/furi_hal_resources.c` in flipperzero-firmware.

## Hardware bring-up (needs a built prototype)
1. Flash: write the board OTP, load firmware (port a board target if needed).
2. Measure the 3.3 V / VSYS rails with a multimeter.
3. Read a known RFID card, IR remote, and sub-GHz fob — one radio at a time.
4. Spectrum-analyze + tune the CC1101 / NFC / 125 kHz matching networks.
5. Certify radios (FCC/CE/WPC-ETA+BIS) before any transmit for sale.
