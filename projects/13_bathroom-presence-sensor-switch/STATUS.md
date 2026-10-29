# Status: 13_bathroom-presence-sensor-switch

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** SPS-24G-01 Rev A0: board routed and fab package generated. **Mains design, not certified.**

## Done
- Schematic ERC 0 errors / 0 warnings
- PCB 100 % routed, 0 unconnected, schematic parity clean
- ≥ 9.5 mm primary↔secondary creepage, 6 mm corridor + routed slot
- Gerbers, drill, CPL, BOMs, STEP, renders, datasheet, application note, safety review
- Reference firmware `06_firmware/main.c`

## Open items
- DRC: 4 package-inherent clearances (pad gaps inside the MOC3063 U2 and BTA16 Q1 footprints, 0.635–0.76 mm vs the 0.8 mm Mains rule). Re-checked with KiCad 9.0.9 on 2026-10-29: still 4.
- HV primary-trace creepage to ≥ 2.5 mm or conformal coating (SAFETY_REVIEW §7)
- Firmware bench test and type certification not done

## Next step
Close the SAFETY_REVIEW §7 items, bench-test the firmware, then get a qualified review before powering from mains.

## Resume here
`00_README.md` status table, then `04_docs/SAFETY_REVIEW.md` and `04_docs/VERIFY_LIST.md`.

## Tools needed
KiCad 9 (`tools/kicad-python-chroot.sh`), Freerouting, Python, avr-gcc for firmware.

History: see `CHANGELOG.md`.
