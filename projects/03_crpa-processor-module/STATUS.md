# Status: 03_crpa-processor-module

_Last updated: 2026-11-06._

**State:** study. Five reference projects read; review written (`05_docs/CRPA_reference_review.md`).
GNSS_JAM_PRO v1.0 case (PocketSDR v2.3 case design, CNC) modelled: STEP parts + assembly and a 4-sheet CNC
drawing set (`06_step/`, `07_drawings/`), committed on projects-v2. Tube has 3 x Ø2.0 LED windows over
LED1-3 (PWR / PLL / DATA); logo 34 mm wide to clear them.

## Done
- Review of PocketSDR (incl. v0.15 array calibration / beam steering), max2771_fx2lp (2-element CRPA, spoof
  detection, MAX2771 phase reset at power-up), airborne STK CRPA study, polarization-crpa (STAP simulator, RFSoC
  plan, channel-equalization finding) and the STM32 gist (not a design basis).
- Matched against project 02: 4 elements, 91 mm L pitch (0.48 λ L1), OUT_L carries L1 + L2/L5, no calibration coupler.
- Key numbers [ESTIMATE]: 3 nulls max; null depth about 20 dB at the project 02 matching target (5° / 0.5 dB),
  about 34 dB at 1° / 0.1 dB; chain must stay linear to about -35 dBm per element (≥ 70 dB dynamic range, ≥ 12-bit ADC).

## Open items
0. Case: confirm tube corner radii (R1.0 / R0.5 [ASSUMED]), panel material (Al 6061 [ASSUMED] vs machined nylon /
   POM as the original print) and finish (black anodize [ASSUMED]); first article: USB-C plug fit (shell 0.08 above
   the original slot per the KiCad model) and spigot fit in the actual tube. Rebuild: `python 02_python/build_case.py`.
1. User inputs (review section 6): simultaneous bands, output type, threat / J/S, platform / size / power, FPGA family.
2. Decide architecture B details (digitizer part, channel count) once item 1 is answered.
3. Feed back to project 02 Rev B: calibration-injection coupler per element; gain plan against the ADC full scale.
4. Phase 0 bench: PocketSDR FE 8CH with the project 02 array (calibration, beam steering, raw IF recordings).

## Next step
Item 1 with the user.
