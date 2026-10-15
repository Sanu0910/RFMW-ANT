# Paper Summary: Reconfigurable Modular Antenna System With Null Steering and Circular Polarization
K. M. Younus, K. Sultan, C. Fumeaux, A. Abbosh, *IEEE Trans. Antennas Propag.*, vol. 73, no. 5, May 2025, DOI 10.1109/TAP.2024.3519765.

## Problem
Null steering (interference suppression, angle-of-arrival) usually means either expensive phased-array chips or compact antennas with narrow steering range, shallow nulls and narrow bandwidth.

## Idea
A **modular unit** = a wideband varactor-tuned phase shifter + a wideband printed dipole on one board. A mirrored copy of the unit radiates at 180°. Arranging units gives three systems:
- **1-D:** two units side by side form an antiphase pair with a broadside null, steered by the differential phase.
- **2-D:** 2×2 units give null planes in u and v.
- **CP:** four units in a cross with 90° on one pair give RHCP or LHCP.

## Phase shifter
- Two elliptical patches on the outer layers, broadside-coupled through an elliptical slot in the inner ground, act as a 3-dB backward coupler.
- Two ports are terminated in a λ/4 stub + DC block + varactor (MAVR-000120-14110P, 0.14–1.7 pF), so it is effectively a **reflection-type phase shifter**.
- Analysed with eqs. 1–7. Claimed: 145° range, ±2° imbalance, IL < 1 dB over 5–7 GHz (33%), one bias voltage per phase shifter.

## Antenna
Printed dipole with an integrated microstrip-to-slotline balun, 45° angled arms, endfire, about 5 dBi, 5–7 GHz.

## Results
| System | Result |
|---|---|
| 1-D | ±40°, null depth > 15 dB, gain 4.6–7.8 dBi |
| 2-D | ±40° per plane, null depth > 10 dB |
| CP | AR < 2.3 dB over 5–7 GHz |

## Our verification and contributions (this folder)
- **Phase-shifter range:** the paper's eqs. with ideal parts give **116°**, the theoretical limit of a single 12:1 varactor reflection-type phase shifter. 145° needs about 0.35 nH of package/pad inductance. The bias choke (100 nH) and DC block (39 pF) are past their self-resonance at 5–7 GHz.
- **1-D null squint:** with a fixed bias the null moves from 50.5° to 33.4° across 5–7 GHz, so the look-up table must be per frequency (generated here).
- **2-D steering envelope:** |u0| + |v0| ≤ 0.79, so both planes cannot reach ±40° at the same time.
- **CP wiring:** with the Fig. 1(c) assignment and identically mounted wings, opposite wings cancel at broadside; a co-phased assignment is provided.
- **Paper inconsistencies:** the dipole substrate is listed as εr 2.2 but RO4003C is 3.55; slot Sw is listed as 8.8 but drawn as an ellipse; the MID-ground transition under the antenna is unclear. Variants are provided for each.
- **Deliverables:**
  - 22 DXFs with silkscreen (phase shifter alone, dipole alone, units A/B, 1-D/2-D/CP systems, Wilkinson dividers, fab panel)
  - Python and MATLAB models (identical outputs) and a PyAEDT build script
  - Monte Carlo of null depth
  - first-simulation component values and the plots to check (`05_docs/FIRST_SIMULATIONS.md`)

See `05_docs/DESIGN_GUIDE.pdf`.
