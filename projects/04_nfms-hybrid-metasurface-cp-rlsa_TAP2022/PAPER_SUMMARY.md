# Paper Summary: A Beam-Steering Solution With Highly Transmitting Hybrid Metasurfaces and CP High-Gain RLSA Antennas
M. U. Afzal, K. P. Esselle, M. N. Y. Koli, *IEEE Trans. Antennas Propag.*, vol. 70, no. 1, pp. 365–377, Jan. 2022, DOI 10.1109/TAP.2021.3111522.

## Problem
High-gain (30 dB class) CP terminals for satellite communication on the move need continuous 2-D beam steering. Rotating dishes is bulky. Phased arrays at this gain are lossy and power-hungry. RLSAs are thin and efficient but have a fixed beam.

## Idea
1. **Near-field meta-steering (NFMS):** keep a CP RLSA (Ø345 mm, 20 GHz) fixed. Rotate two phase-gradient metasurfaces placed λ0 above it.
   - Each one tilts the beam by 19.5°.
   - Their rotation angles ψ1 and ψ2 set θ = asin(2 sin θ0 cos((ψ1−ψ2)/2)) and φ = (ψ1+ψ2)/2.
2. **Hybrid metasurfaces:** a patch-type cell (Type I, 4 metal layers) and an all-dielectric holed cell (Type II) have non-overlapping phase ranges. Together they cover 325° of phase with |S21| > −1 dB, where a conventional cell covers only 289°.
3. **HM I also corrects the RLSA's near-field phase.** The correction is made circularly symmetric so HM I can still rotate. That costs 0.5 dB, but saves a third metasurface.

## Results
- Steering to 40.6° elevation at any azimuth.
- Peak 30.9 dBic (31.5 dBic in Table II), and 26–27 dBic at 40.6°.
- AR < 3 dB within the 3 dB beamwidth. 3 dB gain bandwidth ≥ 0.89 GHz.
- Height 4.5 cm (3λ0). Power is needed only while rotating.

## Our verification and contributions (this folder)
- **Equations:** Table I is reproduced to 0.05°.
  - The paper's inverse formulas (3)–(4) are **wrong by a factor 2** (undefined above about 28°). A corrected form and a beam-to-rotation lookup table are provided.
  - The true elevation limit is 41.9°.
- **Steering model** using the actual chosen cells and a rotated HM II: beam directions within 0.6° of the measured values in all six cases.
- **Radial line:** the paper's ε_eff = 1.41 is a volume average. The exact TM0 value of the air + TLY-5 guide is 1.294 (λg 13.18 mm, against the 12.6 mm spiral pitch).
  - That mismatch costs about 3.7 dB at broadside in our slot model. It plausibly explains the 190° near-field phase ripple the paper has to correct, and its 34 dBi directivity against 37 dBi ideal.
- **Cells:** a closed-form Type II model reproduces the paper's −169…−134° to within 1°.
  - It shows the edge-cell "hole diameter 2.8 mm" should be a *radius*.
  - A Type I quasi-static model is calibrated to the paper's −171° example cell.
  - Inconsistencies: the 36 % patch-area limit contradicts the 7.2 mm sweep, and "1/3 metal-free" is 1/6 for HM II.
- **Geometry:** with the paper's spiral numbers, 960 pairs fall on 13.02 turns, confirming the reading. The outer slots reach 3.2 mm beyond the quoted 345 mm aperture.
- **Deliverables:**
  - DXFs: RLSA with 1920 slots, ground plate, HM I and HM II with all 4 metal layers and drill, per-laminate fab files, and unit cells.
  - Cell-assignment, slot and drill tables, plus BOM and DRC.
  - Python and MATLAB models (identical, checked in Octave 8.4).
  - PyAEDT unit-cell, RLSA and full-system builds. If an HFSS cell table is provided, the DXFs are rebuilt from it automatically.
  - **STEP models** made with SolidCraft.
  - The design guide.

See `05_docs/DESIGN_GUIDE.pdf`.
