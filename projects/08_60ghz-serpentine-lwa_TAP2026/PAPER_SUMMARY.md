# Paper summary

**J. Gabsteiger, C. Robisch, A. Koelpin, F. Lurz, "Advancing 60-GHz SISO Radar: Additively Manufactured Leaky Wave
Antenna With Enhanced Beam Steering", IEEE Trans. Antennas Propag., vol. 74, no. 7, pp. 6130–6145, July 2026.**
DOI 10.1109/TAP.2026.3681348 (open access, CC BY 4.0).

## In one paragraph
A 3D-printed, silver-coated WR15 waveguide is folded into a **serpentine** (meander) and given **16 inclined
narrow-wall slots**. Because the wave travels l = 10.9 mm between slots that are only d = 2.38 mm apart, the phase
between slots changes quickly with frequency, so the main beam swings by about **34° per port over 58–63.5 GHz**.
Feeding it alternately from both ends through a waveguide switch adds the mirror-image sector, for **76° in total**
with 5.5 GHz of bandwidth (9.1 % relative). Used with an FMCW radar chip (Infineon BGT60TR13), one transmit and one
receive channel (SISO) then measure **range** from the beat frequency and **angle** from which part of the chirp
lit the target. Measured gain is 13–15 dBi and angle accuracy is about 1°.

## Design chain (paper equations)
| Step | Equation | Value |
|---|---|---|
| WR15 phase constant | eq. 6, β = √(k² − (π/a)²) | a = 3.76 mm, cutoff 39.9 GHz |
| grating-lobe limit | eq. 12, d < λ0/2 at 63.5 GHz | d < 2.36 mm |
| slot spacing | eq. 13, d = b + 0.5 mm | 2.38 mm |
| straight slotted guide | eq. 10 | 111.1° → 102.4°, only 8.7° squint |
| serpentine beam angle | eq. 11, θ0 = arccos((βl − 2π(m+½))/(kd)), m = 1 | l = 10.9 mm: 86° at 58 GHz, 53.8° at 63.5 GHz |
| amplitude taper | Dolph–Chebyshev, N = 16, 20 dB | a_n in Table I |
| slot conductance | eq. 16, g_n = a_n² / Σa_i² | 0.023 … 0.092 |
| slot tilt / depth | eq. 17/18 (polynomial fits of CST data, natural log) | Table I |
| radiation boost | tilts × 1.5, depth from eq. 20, width 0.34 mm | Table II, S21 ≈ −6.5 dB |
| FMCW range resolution | eq. 1–4 | ΔR = c/2B; ΔR·θ3dB = c·θs/(2B) |

## Fabrication and measurement
- Formlabs Form 3+ SLA, clear resin, 25 µm layers, part tilted 5–12° on the build plate.
- Cleaning with isopropanol and compressed air, UV cure.
- Electroless silver (Tollens' reaction), three cycles. Pumping the reagent through the guide with a peristaltic
  pump avoids deposits in the bends. Silver thickness is 14–22 µm, about 50+ skin depths (δ ≈ 0.25 µm).
- The prints shrank (a 3.38 × 1.72 mm opening instead of 3.76 × 1.88). The authors compensated by widening the
  opening 100 µm and lengthening each half loop by 200 µm.
- Measured with a PNA-X and a 24 dBi horn at 1 m. Final prototype: 76° coverage, 13–15 dBi, mean angle error
  1–2°. Angle test: 9° measured against a 10° target.
- Open-stopband (OSB) gain dip near broadside (≈ 58–59 GHz). Accepted, because the horn receiver compensates it.

## What this repository adds
- `02_python/lwa_design.py` recomputes all of the above. Beam angles match to 0.1° and the taper matches Table I.
- `01_cad/build_lwa_cad.py` builds a parametric STEP/STL replica (shell + slots + flanges) and a separate air
  volume.
- `03_sim/slot_unit_cell.py` is a full-wave unit-slot check in Hertzon/EMerge.
- `04_docs/` holds the brief (basic → advanced) as a PDF.
