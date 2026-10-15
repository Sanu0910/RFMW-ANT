# First HFSS Simulations: Component Values and Plots to Check

## Run 1: paper values, ideal parts
| Part | Ref | HFSS lumped RLC | Value |
|---|---|---|---|
| Varactor | D1, D2 | Series R + L + C | R = 2 Ω, L = 0, C = variable `Cv` |
| DC block | C1, C2 | Series C | 39 pF |
| Bias choke | L1, L2 | Series L | 100 nH (or omit: about 3.8 kΩ at 6 GHz, effectively open) |
| Ports | J1/J2 | Lumped | 50 Ω |
| Wilkinson isolation resistor | R | Series R | 100 Ω |

- **Cv sweep:** 0.14, 0.2, 0.3, 0.5, 0.8, 1.2, 1.7 pF over 5–7 GHz. Both varactors in a phase shifter take the same value.
- **Expect** about 116° of range (the ideal-part limit).

## Run 2: realistic parts
| Part | HFSS lumped RLC |
|---|---|
| Varactor | Series: R = 2 Ω, L = 0.35 nH, C = `Cv` |
| DC block | Series: 39 pF + 0.4 nH |
| Choke | Parallel: 100 nH ‖ 0.11 pF (self-resonant at 1.5 GHz) |

**Expect** about 136–147° of range.

## Cv per unit for 1-D null steering (pF, U1 / U2)
| Null | 5 GHz | 6 GHz | 7 GHz |
|---|---|---|---|
| 0° | 0.554 / 0.554 | 0.502 / 0.502 | 0.458 / 0.458 |
| +25° | 0.341 / 0.873 | 0.289 / 0.861 | 0.249 / 0.867 |
| −25° | 0.873 / 0.341 | 0.861 / 0.289 | 0.867 / 0.249 |
| +40° | 0.247 / 1.138 | 0.199 / 1.230 | 0.162 / 1.423 |
| −40° | 1.138 / 0.247 | 1.230 / 0.199 | 1.423 / 0.162 |

For the first array run set every unit to Cv = 0.5 pF. That should put the null at broadside and checks the A/B antiphase setup.

## Plots to check, in order

**1. Phase shifter alone**
- **Coupler first.** Replace the varactors with opens and check |S21| ≈ |S31| ≈ −3 dB at 6 GHz. If not, the slot shape is wrong.
- **dB(S11):** below −15 dB (Figs. 4a, 5a).
- **dB(S21):** above −1 dB (Fig. 5a).
- **Relative phase:** ang_deg(S21) − ang_deg(S21 at 1.7 pF). Curves should be flat and parallel, reaching about 116° (Run 1) or 140–145° (Run 2) (Figs. 4b, 5b).
- **Phase vs Cv at 6 GHz:** smooth and monotonic. Use it to fix the look-up table.

**2. Dipole alone, then one unit**
- dB(S11) below −10 dB over 5–7 GHz (Figs. 7a, 9a).
- Realized gain about 5 dBi, with a broad endfire beam.
- Cross-pol at least 15 dB below co-pol (Fig. 7b).

**3. 1-D system**
- φ = 0° cut for the 0°, ±25° and ±40° states: null within ±3° of target, depth above 15 dB (Fig. 10).
- Squint check at 5 and 7 GHz using the 6 GHz Cv values.
- Peak gain 4.6–7.8 dBi; mutual coupling S21 below −15 dB.

**4. 2-D system**
- 3D gain pattern and uv contour plot: null lines at u0 and v0, depth above 10 dB, gain 6.1–8.1 dBi (Fig. 12).

**5. CP system**
- Excite one opposite pair alone first, to check it adds at broadside rather than cancelling.
- RealizedGainLHCP and RealizedGainRHCP: wanted sense at least 15 dB above the other at boresight (Fig. 14).
- AxialRatioValue at θ = 0°: below 2.3 dB over 5–7 GHz (Fig. 15).
