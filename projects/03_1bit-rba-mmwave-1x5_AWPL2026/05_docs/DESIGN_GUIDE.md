# Compact 1-Bit Reconfigurable 1×5 mm-Wave Array: Designer & Verification Guide

Companion to: J. Jiao, Y. Wang, F. Xu, "Compact Low-Cost 1-Bit Reconfigurable Wide Beam-Steering mm-Wave Array for Mobile Terminals", IEEE Antennas Wireless Propag. Lett., vol. 25, no. 6, Jun. 2026, DOI 10.1109/LAWP.2026.3686232.

---

## 1. The design in one page

- **Element (RCSPA):** a patch on M1 sits over a *coupled shorted patch* on M2, which is shorted to ground by a row of pins.
  - The element resonates at a quarter wavelength, so it is small (2.4 × 3.1 mm) and its E-plane beam is very wide.
  - It is fed through a slot in the ground (M3) by a microstrip on M4.
- **1-bit phase:** on M4 the feed line ends in a T between two PIN diodes (SW1, SW2) that drive a U-shaped loop crossing the slot.
  - SW1 ON: current crosses the slot in +x, which is 0°.
  - SW2 ON: current crosses in −x, which is −180°.
  - One bias voltage per element picks the state: +V turns SW1 on, −V turns SW2 on.
- **Array:** 5 elements at D = 4.5 mm in x, covering 25–29 GHz.
  - With only 0°/180° per element, a plain 1-bit array has quantisation grating lobes.
  - The fix is a **fixed preload phase** per element (55.78°, −5.79°, −73.37°, 0°, −111.72°, found by PSO). It is built into the feed lines of a 1:5 divider.
  - The preload breaks the periodic quantisation error, so 7 beams (0, ±20, ±40, ±60°) reach −57° to +55° with SLL around −5 dB.
- **Claimed performance:** 25–29 GHz; peak gain 9.8 dBi simulated, 9.23 dBi measured; XPL < −13.5 dB; size 1.87λ0 × 0.66λ0.

---

## 2. Terminology

| Term | Meaning here |
|---|---|
| **RBA, reconfigurable bit array** | An array where each element has only 2ⁿ discrete phase states set by switches instead of a continuous phase shifter |
| **1-bit** | Two states per element, 0° and 180° |
| **RCSPA** | Reconfigurable coupled shorted patch antenna: the element |
| **Shorted (quarter-wave) patch** | A patch shorted along one edge resonates at λg/4. It is half the size of a normal patch and has one radiating edge, so its E-plane pattern is nearly hemispherical. That width is what lets the array scan to ±55–60°. |
| **Aperture (slot) coupling** | The feed line on M4 couples to the patch through a slot in the M3 ground. The ground separates the radiator from the feed and switch circuitry. |
| **Feed-direction (polarity) switching** | Reversing which end of the loop is driven reverses current across the slot, giving a frequency-independent 180°. This is why the paper's state difference stays at −176° to −178° over the band (Fig. 4). |
| **PIN diode ON / OFF model** | MA4AGFCP910 (AlGaAs flip-chip). ON = 5.2 Ω + 0.2 nH; OFF = 0.018 pF + 0.2 nH (paper). |
| **Bias tee** | 100 Ω resistor plus a high-impedance line with a **radial stub** (wideband RF short at the tap) feeds DC. The **3.6 pF DC block** in the feed line keeps bias out of the RF source. |
| **DC return / shorting via** | Loop-to-ground thin line and via. It closes the diode DC circuit. |
| **Phase quantisation error** | Difference between the ideal progressive phase and the nearest available 1-bit phase. If periodic, it radiates **quantisation (grating) lobes**. |
| **Fixed-phase preloading** | Constant, element-specific phase offsets (here in the divider line lengths) that de-correlate the quantisation error. Related to "phase randomisation" (ref. [27] of the paper). |
| **Particle swarm optimisation (PSO)** | Global optimiser used to choose the preload values. |
| **Beam code** | The 5-bit pattern of states, e.g. 00011 for +40°. Each code and its complement give the *same* pattern, so every beam has two equivalent codes. |
| **Scan loss** | Gain drop versus broadside; the paper reports < 3.5 dB within ±60°. |
| **SLL / XPL** | Side-lobe level / cross-polarisation level |
| **Beam squint** | Beam angle moving with frequency. Element spacing in wavelengths changes with f while the 1-bit and preload phases do not. |
| **Corporate 1:5 divider** | Tree of T-junctions with quarter-wave transformers giving equal power to five outputs |
| **Unequal T-junction** | A branch carrying power fraction p uses a λg/4 line of Zq = √(Z0 · Z0/p). |
| **Embedded element pattern** | One element's pattern inside the array with the others terminated. Use it in the array model for verification. |

---

## 3. Verification of the paper's claims (done here)

| Claim | Check | Result |
|---|---|---|
| D = 4.5 mm = 0.375λ0 | λ0 at 26.5 GHz is 11.31 mm | 4.5 mm is **0.398λ0 at 26.5 GHz**; 0.375λ0 holds at 25.0 GHz. The design and results are unaffected; only the quoted ratio is off. |
| Size "1.87λ0 × 0.66λ0" and "1.87λ0 × 1.36λ0" | ALg × AWg = 32 × 12 mm at 26.5 GHz = 2.83λ0 × 1.06λ0 | The two quoted sizes disagree, and neither matches 32 × 12 mm at 26.5 GHz. They probably refer to different regions (patch-row span vs board). Confirm against your own board. |
| 7 beams with the PSO preload | Array model, element E-plane fitted to Fig. 3a (−1.7 dB at 60°, −4 dB at 90°), best of 32 codes | Peaks −1.2 / +20.0 / −22.5 / +35.8 / −38.8 / +53.8 / −57.0° vs paper −1 / 19 / −21 / 38 / −41 / 56 / −54°. 0°/±20°/±40° SLL within about 2 dB. **±60° SLL −3.5 to −3.8 dB vs paper −4.7 to −5.0**: the isolated-element model misses mutual coupling, so check with embedded patterns in HFSS. |
| Wide scanning needs the shorted patch | Element-width sweep | +60° beam reaches 56° only with a hemispherical element (≤ 2–4 dB taper at 90°); a normal patch (≈ 12 dB taper) stops at about 46°. |
| Grating-lobe suppression | No-preload case | Without preload, every steered beam has an **equal-level mirror lobe** (SLL = 0 dB; e.g. +21.5° and −21.5° at once), the classic 1-bit quantisation lobe. With the preload the mirror lobe drops to −5…−9 dB (`scan_patterns_26p5GHz.png`). |
| PSO is reproducible | Own PSO (24 particles, 50 iterations) | Found a different preload set (−29.3, 1.1, 84.5, 0, 150.8°) with worst SLL −5.1 dB and pointing error ≤ 4°. The solution is **not unique**, so the paper's numbers are one of many. |
| Band 25–29 GHz | Beam squint of fixed codes | The +60° code moves from 57° (25 GHz) to 48.5° (29 GHz). Plan the code table per sub-band or accept ±5° pointing. |
| ~180° state difference | Loop reversal | Frequency-independent by construction. The −2° to −4° error (Fig. 4) costs < 0.5 dB SLL (Monte Carlo). |
| Preload tolerance | Monte Carlo | SLL (90th pct, all beams) degrades from −3.6 dB at 0° rms preload error to −3.0 dB at 10° and −1.8 dB at 15°. **10° at 26.5 GHz is only ≈ 0.19 mm of line**, so etch and εr tolerance matter. |
| Divider widths | Recomputed from first principles | 50 Ω = 0.458 mm (paper w1 = 0.44); 79 Ω (2/5 branch) = 0.198 mm (paper w2 = 0.2); 61 Ω (2/3 branch) = 0.325 mm (paper w4 = w5 = 0.33). This confirms the split tree 2/5–3/5, 1/2, 1/3–2/3, 1/2. |

---

## 4. Geometry and assumptions

**Stack-up:**

| Layer | z (mm) | Contents |
|---|---|---|
| M1 | 0.965 | patch |
| Sub.1 | 0.457–0.965 | RT5880, εr 2.2, 0.508 mm |
| M2 | 0.457 | coupled shorted strip |
| Sub.2 | 0.203–0.457 | RT5880, 0.254 mm; pins M2 → M3 |
| M3 | 0.203 | ground with slot |
| Sub.3 | 0–0.203 | RO4003C, εr 3.55, 0.203 mm |
| M4 | 0 | feed, loop, diodes, bias |

**From the paper:**
- Element: Lg = Wg = 10, Lp 2.4, Wp 3.1, Sl 2.4, Sw 0.2, Ls 0.6, Dp 0.2, Dv 0.2, l1 0.9, l2 0.5, l3 2.4, w2 0.45, w3 2, w4 2.8.
- Array: D 4.5, ALg 32, AWg 12.
- Parts: R 100 Ω, C 3.6 pF.
- Divider widths: 0.44 / 0.2 / 0.1 / 0.33 / 0.33 / 0.46.

**Assumed (all are parameters in `02_python/rbageom.py`):**

| Item | Problem | Used |
|---|---|---|
| w1 (feed width) | Printed "w1 =" with no value | 50 Ω on 0.203 RO4003C = 0.458 mm (the paper's divider w1 = 0.44 agrees) |
| Ls/Ws | Text says "Ls × Ws = 2.4 × 0.6" but the figure shows Ls = 0.6 as the narrow side | 0.6 (x) × 2.4 (y) |
| Slot and pin position | Not dimensioned | Pins at x = −0.75 inside the M2 strip; slot centre at x = −0.35 (just right of the pins, under the patch). **Tune the slot offset in HFSS for S11.** |
| Loop | w3 = 2 and w4 = 2.8 are drawn on the loop but cannot be line widths in a 4.5 mm cell | Read as loop height (2.0) and outer width (2.8); loop line 0.2 mm. **Tune l2 / w3 / w4 for the two-state S11 overlap (24.8–28 GHz).** |
| l1, l2, l3 | Fig. 1d annotations are ambiguous | l1 = 0.9 used as T-to-DC-block distance. Diode gaps 0.25 mm centred at ±0.45 mm (flip-chip footprint; check the MACOM land pattern). |
| Board split | Pins M2 → M3 cross the antenna/feed board interface (the paper assembles two boards with plastic screws) | Split DXFs provided as in the paper, **plus** a note recommending a single laminated build. A pressure-contact pin is unreliable at 26 GHz. |
| Divider layout | Fig. 6c gives widths and some lengths but not a full layout | Topology reconstructed (widths agree); preload realised by serpentines computed with ε_eff per segment. Achieved preload equals target in the model; **re-check in HFSS**, because junction parasitics shift phase by a few degrees. |

---

## 5. Boards

| Folder | Board | Use |
|---|---|---|
| A_element_alone | 10 × 10 element, 1 port | Element S11 in both states, E/H patterns, state phase difference (paper Figs. 2–4) |
| B_array_without_divider | 32 × 12, 5 ports | Array S-parameters and coupling (Fig. 5c); apply preload and codes in post-processing (Fig. 5d) |
| C_array_with_divider | 32 × 31, 1 port, 1:5 divider with preload | Full system (Figs. 6–8) |
| D_split_boards_for_fab | Antenna board (M1/M2/pins) and feed board (M3/M4/divider) | Two-board build as in the paper |

Silkscreen and assembly are on M4, the component side:
- C1–C5, R1–R5, SW1/SW2 per element, with cathode bars and V1–V5 pads
- the state legend: STATE0: V > 0 (SW1 ON, 0°); STATE1: V < 0 (SW2 ON, −180°)
- per-element preload values and the scan direction

Element numbers and the title are on top. Supporting files are `BOM_and_placement.csv`, `DRC_report.txt` and `C_array_with_divider/divider_design_table.csv`.

---

## 6. Component values for the first simulations

| Part | HFSS lumped RLC | Value |
|---|---|---|
| PIN diode ON | Series R + L | 5.2 Ω, 0.2 nH |
| PIN diode OFF | Series C + L | 0.018 pF, 0.2 nH |
| DC block | Series C (+ ESL) | 3.6 pF (+ 0.15 nH for 0201) |
| Bias resistor | Series R | 100 Ω |
| Ports | Lumped, M4 line to M3 | 50 Ω |

**Codes** (bit n = element n, 0 = SW1 ON, 1 = SW2 ON; each code's complement is equivalent):

| Beam | 0° | +20° | −20° | +40° | −40° | +60° | −60° |
|---|---|---|---|---|---|---|---|
| Code | 00101 | 00010 | 00110 | 00011 | 01001 | 01100 | 10111 |

**Bias:** V_n = ±(V_F + I·R). With V_F ≈ 1.4 V (check the datasheet) and 10 mA through 100 Ω, that is **≈ ±2.4 V**.

---

## 7. HFSS steps and plots to check

1. **Element.** Build with `04_hfss/hfss_rba_build.py element` or import `A_element_alone`.
   - Map layers to z per section 4. Subtract M3_SLOT from M3, add the PEC pins, use a vertical lumped port at the feed end, radiation box ≥ 3 mm, 24–30 GHz.
   - **Plots:**
     - S11 for state 0 and state 1: both below −10 dB over 24.8–28 GHz (Fig. 2).
     - E- and H-plane gain: about 4.6 dBi; E-plane only about 4 dB down at ±90° (Fig. 3).
     - ∠S21-equivalent: the phase of rE at broadside for the two states should differ by 180° ± 4° (Fig. 4).
2. **Array, 5 ports.**
   - **Plots:** Sii below −10 dB and adjacent Sij below −15 dB (Fig. 5c).
   - Export each port's embedded E-plane pattern, apply preload plus code with Edit Sources (magnitude 1, phase = preload + 0/−180), and read the 7 beams (Fig. 5d).
3. **Array with divider.**
   - Set the code variables, run S11 for all 7 codes (Fig. 7), and plot E-plane realized gain (Fig. 8).
   - Check peak gain about 9.8 dBi at 0°, scan loss < 3.5 dB, SLL ≤ −5 dB, XPL < −15 dB.
4. **Feed into the models.** Embedded patterns go into `rba_array.load_pattern` (Python) or replace `rba_elem` (MATLAB) for verification-grade beam tables.

---

## 8. What the paper leaves out (important for a real build)

1. **Pin contact across two boards.** Shorting pins must make a reliable connection to ground at 26 GHz. Prefer a single laminated stack with plated pins and back-drilled or sequential lamination, or at least solder bumps or conductive epoxy rather than pressure.
2. **Alignment.** The slot (0.2 mm wide) must sit under the loop arm and next to the pins. A ±0.1 mm misregistration between the two boards shifts S11 and the state phase, so add alignment pins and fiducials.
3. **Preload accuracy.** 10° of preload error is ≈ 0.19 mm of 50 Ω line at 26.5 GHz. Use the actual RO4003C Dk at 26 GHz (design Dk 3.55, but process Dk is ≈ 3.38) and verify the divider phase on a coupon with five outputs.
4. **The divider adds loss** (paper: 0.35 dB) and the larger ground changes the patterns (paper notes a gain drop). Simulate the full board, not only the antenna region.
5. **Diode parasitics.** Use the vendor S2P files at 26 GHz instead of the lumped values for the final run. The pad and solder-bump capacitance of a flip-chip is comparable to C_off.
6. **Bias network.** The radial-stub angle and radius set the RF short over 25–29 GHz; check that it stays below −20 dB isolation into the bias line across the band. The bias wires (Fig. 6) run past the antenna: route them on the feed side and shield or filter them so they don't re-radiate.
7. **Switching speed and power.** Each element draws about 10 mA in either state, so 5 elements is about 50 mA. Switching time is set by diode recovery plus the R and line capacitance (sub-µs). Check power handling if the array transmits.
8. **Code table and squint.** Generate codes per sub-band. The best code at 25 GHz is not always the best at 29 GHz.
9. **Equivalent codes.** Pick between a code and its complement by S11 at the feed (the structure is not symmetric, Fig. 2) or by diode current.
10. **Mutual coupling at 0.4λ.** Isolated-element models over-predict ±60° SLL. Use embedded patterns from HFSS.
11. **Measurement.** At 26 GHz, use a 2.92 mm or 2.4 mm end-launch connector and de-embed its launch. Keep cables and DC bias wires out of the measurement plane; the paper's photo shows wires above the antenna.

---

## 9. Paper targets

| Item | Paper |
|---|---|
| Element S11 | < −10 dB, 24.8–28 GHz, both states |
| Element gain | 4.6 dBi; XPL < −14.6 dB (E-plane), < −15.2 dB (H-plane) |
| State difference | −176° (24.8 GHz) to −178° (28 GHz) |
| Array (no divider) | Overlapped bandwidth 25–28 GHz, adjacent coupling < −15 dB, peak 9.8 dBi at −1°, scan loss < 3.5 dB within ±60° |
| Array (with divider), simulated | 0°: 9.8 dBi; 23 / −18°: 8.9 / 7.8; 42 / −37°: 7.7 / 7.39; 57 / −57°: 7.09 / 5.72 dBi; SLL < −5 dB; XPL < −15 dB |
| Measured | 9.23 dBi at −1°; ±21°: 8.2 / 7.69; 42 / −43°: 7.56 / 7.14; 55 / −57°: 6.52 / 5.02 dBi; SLL < −4.64 dB; XPL < −13.5 dB; S11 < −10 dB 25–29 GHz |
