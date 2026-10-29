# Status: 12_multitool-rf-board

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** NOVA-RF1: schematic ERC-clean, 4-layer board routed **101/104 nets**, fab package exported. 3 nets still need manual routing.

## Done
- Netlist (`02_python/design.py`) checked against the official STM32WB55 symbol; 3 netlist bugs fixed
- KiCad 9 schematic, ERC 0 errors
- Pad→net engine `pinmap.py`: 88 parts, 0 unresolved; chip pinouts transcribed from datasheets
- Rounded handheld outline, GND + 3V3 planes, 101/104 nets routed (3051 segments, 554 vias)
- Gerbers, drill, CPL, JLCPCB and costed BOMs; product and datasheet PDFs
- Separate antenna PCB (125 kHz spiral + 13.56 MHz NFC loop) and a two-part enclosure model

## Open items
- **3 signals unrouted**: route by hand (see `04_docs/PCB_STATUS.md`)
- RF matching (CC1101 filter, ST25R3916 antenna tuning, 125 kHz LC) not designed or verified
- Sub-GHz and BLE radios need type approval before sale
- `00_README.md` Status section is out of date (says routing not done)

## Next step
Route the last 3 nets, rerun DRC, then design and simulate the RF matching networks.

## Resume here
`04_docs/PCB_STATUS.md` and `04_docs/FAB_NOTES.md`.

## Tools needed
KiCad 9, KiCadRoutingTools (`tools/install_krt.sh`), Python, gmsh (enclosure).

History: see `CHANGELOG.md`.
