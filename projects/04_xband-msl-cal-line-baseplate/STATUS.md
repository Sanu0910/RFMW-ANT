# Status: 04_xband-msl-cal-line-baseplate

_Last updated: 2026-11-06._

**State:** Both base plates (CRL-XB-CALP-15 for the 15 mm THRU, CRL-XB-CALP-65 for the 65 mm THRU) are modelled, checked
and drawn: plate STEP for CNC, assembly and exploded STEP, A3 CNC drawing (2 sheets each), design report, BOM and hole
table. All 11 mechanical checks pass. Mass 16.0 g and 29.0 g (6061-T6).

## Done
- Read the customer cal-line zip: 4 boards, all MSL launch → via → stripline → via → MSL. The two X-band RO4350B 30 mil
  boards are built here.
- Plate: board locating pocket (1.0 deep, +0.2 ends / +0.1 sides, R2.2), two 5 mm connector walls with Ø4.25 bore
  and 4 x M2.5 flange taps for the H+S 23_SMA-50-0-272/133_N (same jack and wall/spigot rule as project 01),
  4 x M3 through taps at the board's own holes, finger notches, underside lightening pockets (2.0 skin), engraving.
- Drawings: section A-A, view J1, top view, view from below, section B-B, hole table (datum SW bottom corner),
  notes with datum A = pocket floor and the critical bore height 2.36 ±0.02.

## Open items
1. **Confirm the cal PCB finished thickness with the fab** (used 1.73 mm [ASSUMED]: 2 x 0.762 RO4350B + bond ply).
   It sets the pocket floor to bore axis height (t + 0.63). Change `PCB["t"]` in `config.py` and run `build_all.py`.
2. UWB RT5880 10 mil boards in the same zip are not covered (different launch width and thickness). Add on request.

## Next step
Item 1, then release the drawings to the machine shop.

## Resume
`cd 02_python && ../../../.venv/Scripts/python.exe build_all.py` (≈6 min, needs `solidcraft-cli`); `build_all.py drawing report` only re-draws.
