# Status: 01_xband-8way-msl-wpd-housing

_Last updated: 2026-11-05._

**State:** Base, lid (with channel cage and engraving) and gasket STEP files are built and checked in renders. PCB V3 DXF is done.
All 26 mechanical checks pass; the lowest channel resonance is 15.9 GHz (> 1.3 x 12 GHz). The assembly STEPs are not built yet.

## Done
- Customer board read from the DXF: ports, 21 resistors, ground pour (clearance 4.215 mm = 2.5 W).
- PCB V3: 15 x M2 PTH d2.4 in the pour, 33 vias removed.
- Housing: base with 9 connector bores and flange taps, 35 x M2.5 lid taps, 15 x M2 PCB taps, 4 x M3 mounting taps,
  dowels, earth point. Lid with cage channels, head pockets, dowel hole and slot, jacking holes, and the engraving.
- RF sizing: 2D eigenmode solve of the channel network; 2D finite-difference Z0 of the line in its channel (49.2 vs 50.2 ohm open).
- Drawings (4 A3 sheets), design report, BOM and hole table regenerated from the current code. Mass: base 263 g, lid 342 g.
- Pushed to the public repo with the customer DXF (user decision, 2026-11-05).

## Open items
1. **Rebuild the box / assembly / exploded STEPs.** That run was stopped because the PC was low on memory. Run
   `build_all.py box`, then `assy`, then `exploded`, one at a time; zip any STEP over 20 MB.
2. Confirm with the customer that the bottom layer is solid ground [ASSUMED].
3. Recommended: full-wave check (openEMS / HFSS) of one output branch inside its channel before production.

## Next step
Item 1 (close other programs first), then item 2 with the customer.
