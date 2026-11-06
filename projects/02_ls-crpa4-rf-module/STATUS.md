# Status: 02_ls-crpa4-rf-module

_Last updated: 2026-11-06._

**State:** Rev A main board CRL-LS-CRPA4 DRC clean (0 violations, 0 unconnected) with the NavIC S patches at
lambda/2 (60.15 mm adjacent spacing, r 42.53 mm); fab package (Gerber X2 + Excellon zip, CPL, IPC-D-356, BOM CSV/XLSX
40 lines / 313 placements, fab + assembly notes), PCB STEP and the combined L + S back cover STEP CRL-LS-CRPA4-BC01
(464 g Al), RF budget (`rf_budget.py`), 6-sheet drawing set (`07_drawings/`) and design report
(`05_docs/CRL-LS-CRPA4_design_report.pdf`) done. Test boards not built.

## Done
- Design basis, interface tables (`05_docs/`); the plug-in module idea is superseded by a full board (user, 2026-11-05)
- Stack-up: 4L 1.6 mm, FR-4 high-Tg L1-L3 + RO4350B 0.168 mm L3-L4, 50 ohm = 0.34 mm (`ls_design.py`)
- `build_footprints_ls.py`: GPDF6010 with the customer drills, S patch site, TA1442A, Xinger C2327J5003AHF, BEL logo
- `build_pcb.py` (from project 17): 4 L channels (p17 chain) + 4 S chains in the axis strips (Xinger on the feed
  bisector, so both feeds are equal length; CLM-83 -> TQP3M9037 -> TA1442A x3 with 2 LNAs), 8 SMA, shield frames
  (L octagon + S frame sharing walls), star bias, power entry moved NNW, BEL logo top + bottom
- `04_fab/Gerbers/` (14 files), `04_fab/CRL-LS-CRPA4_CPL_bottom.csv`, `06_step/CRL-LS-CRPA4_PCB.step`

- Top side (L1) has no solder mask: bare ENIG GND under the L and S patch bases (user, 2026-11-06). The top legend
  (BEL logo, title) is clipped by the mask opening in the Gerbers - decide whether to keep a top legend

## Open items
1. Done 2026-11-06: combined back cover BC01 (`06_step/`, notes in `CRL-LS-CRPA4-BC01_NOTES.md`)
2. Test boards (one L channel + one S chain + THRU line, same stack-up) and their cover STEP
3. Done 2026-11-06: RF budget / rejection / power, drawings (`drawings.py`), report (`report.py`).
   Rev B item from it: gain too high for jamming (SAW #2 overdriven, input P1dB -20...-24 dBm) - see report sec. 7
4. Done 2026-11-06: TA1442A (Tai-Saw Rev 1) and C2327J5003AHF (TTM Rev K) land patterns from the data sheets
   (`00_vendor/`). S patch = CRL-LS-SP01 (BEL CRL in-house, 2026-11-06). Still open: D3.6 / D1.35 drills vs GPDF6010.A
5. CP sense: F0 -> pin 4 (direct), F90 -> pin 6 (coupled) = RHCP for F90 at +90 deg CCW (top view); asserted in
   `build_pcb.py`. Confirm the pin labelling on the S patch drawing
7. RF budget (`rf_budget.py`, 2026-11-06): S chain rejects WiFi ch11 only 4 dB, ch13 / BT 2 dB, LTE B41 2506 0 dB,
   B7 2535 6 dB (WiFi ch6 45 dB). L2/L5 rejects DME 1150 MHz only 10 dB. In-band jammer at the antenna above
   -40 dBm (L2/L5) / -26 dBm (S) / -27 dBm (L1) overdrives the 2nd SAW rating; input P1dB -20 to -24 dBm (L), -15 (S)
6. 8-element circular version (future): plan from this layout
8. Design review gaps (RF + product): `05_docs/CRL-LS-CRPA4_design_review_gaps.md`

## Next step
Item 2 (test boards + cover); decide the Rev B gain plan (report sec. 7). Rebuild: `bash 02_python/run_drc.sh`.
