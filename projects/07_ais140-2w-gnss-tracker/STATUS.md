# Status: 07_ais140-2w-gnss-tracker

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Two Rev A0 pre-prototype boards. Premium: layout complete, DRC/ERC clean. Lite: layout complete, **not fab-ready** (EC200U footprint).

## Done
- **Premium (CRL-TRK-2W-01):** 4-layer 60×45 mm board, ERC clean, DRC 0 errors / 0 unconnected, parity clean; Gerbers, CPL, BOMs, STEP, workflow PDF
- **Lite (CRL-TRK-2W-L1):** 2-layer board, ERC 0, DRC 0 errors / 0 unconnected (6 silk warnings); fab package and costed BOM
- Marketing: posters, pricing notes, business plan PDF, Lite plan PDF

## Open items
- **Lite:** replace the reconstructed EC200U land pattern with Quectel's drawing (`lite/04_docs/VERIFY_LIST.md` #1)
- **Premium:** several component values set without the datasheet: check `premium/04_docs/VERIFY_LIST.md`
- AIS-140 certification, enclosure and firmware not started

## Next step
Work through both VERIFY_LISTs, fix the Lite EC200U footprint, rerun DRC, then order prototypes.

## Resume here
`00_README.md`, then each variant's `00_README.md` and `04_docs/VERIFY_LIST.md`.

## Tools needed
KiCad 9 (`tools/install_kicad_mcp.sh`), Freerouting 1.9, Xvfb, SolidCraft (envelope STEPs), Python.

History: see `CHANGELOG.md`.
