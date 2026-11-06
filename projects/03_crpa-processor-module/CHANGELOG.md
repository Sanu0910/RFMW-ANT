# Changelog: 03_crpa-processor-module

Newest first.

## 2026-11-06 - Case tube: 3 LED windows
- Tube -01: 3 x Ø2.0 through holes in the top wall (L1-L3), centred on LED1 PWR / LED2 PLL / LED3 DATA from the
  v2.3 board (KiCad/Gerber: X 46.70 / 46.70 / 44.35, Y +4.25 / +7.75 / +7.75 from the ANT end face and centre line).
- Logo on the top face 40 -> 34 mm wide (still centred) so the holes clear the engraving by 1.22 mm; new fit check.
- Drawing sheet 1: LED windows in the top view and the hole table, note 3. STEP, renders, drawings rebuilt.

## 2026-11-06 - GNSS_JAM_PRO v1.0 case (PocketSDR v2.3 case, CNC): STEP + drawings
- PocketSDR FE 2CH v2.3 hardware copied to `00_reference/pocketsdr_v2.3/`. The `.f3d` bodies are Autodesk ASM
  binary (not readable without Fusion), so the case was rebuilt from the parts list (Al tube 25 x 15 x 1.5 x 55,
  M2 x 10 + nuts) and the panel `.3mf` mesh (every panel dimension measured on sections). Design unchanged (user);
  panels machined instead of printed.
- `02_python/build_case.py`: SolidCraft STEP of the tube, the ANT and USB panels, assembly (KiCad USB4105 model,
  simplified PCB / SMA / shield) and exploded assembly; fit checks; 4-sheet A3 CNC drawing set.
- Tube marking: new BEL CRL logo (`make_logo.py`: 'CENTRAL RESEARCH LABORATORY' built from the BHARAT ELECTRONICS
  letters, enlarged), 'GNSS_JAM_PRO_v1.0', '06-11-2026'. Screws and nuts supplied by the vendor with 2 spares each.
- Findings: original spigot 11.8 in a 12.0 tube leaves 0.05 a side (drawing: spigot 0/-0.1); the KiCad USB4105
  shell top is 0.08 above the original USB slot (source design kept, check on the first article).

## 2026-11-06 - Project started, reference review
- New project for the CRPA digitizer / anti-jam processor behind the project 02 antenna.
- `05_docs/CRPA_reference_review.md`: what PocketSDR, max2771_fx2lp, the airborne STK study, polarization-crpa and
  the STM32 gist offer; consequences (null count, null depth vs channel matching, ADC bits, linearity, coherence,
  NavIC S coverage); three candidate architectures; proposed phased path; open inputs.
