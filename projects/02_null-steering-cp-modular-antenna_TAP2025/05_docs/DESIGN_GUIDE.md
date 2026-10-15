# Reconfigurable Modular Null-Steering / CP Antenna — Designer & Verification Guide

Companion to: K. M. Younus, K. Sultan, C. Fumeaux, A. Abbosh, "Reconfigurable Modular Antenna System With Null Steering and Circular Polarization", IEEE Trans. Antennas Propag., vol. 73, no. 5, May 2025.

This guide is laid out the way a design review would go: what the system is, what each claim rests on, what the paper leaves out, and how to verify every block in HFSS, MATLAB and Python before building hardware.

---

## 1. The system in one page

**One unit = phase shifter (PS) + printed dipole on one 25 × 60 mm board.**
- **Phase shifter:** two elliptical patches on the outer layers, broadside-coupled through an elliptical slot in the inner ground. Each patch's free end has a stub, a DC-block capacitor and a varactor to ground, and one bias voltage tunes both varactors. The quoted performance is 145° tuning range, ±2° imbalance and IL < 1 dB over 5–7 GHz.
- **Antenna:** a wideband printed dipole with an integrated microstrip-to-slotline balun. It fires endfire (off the board tip) with a broad beam of about 5 dBi.
- **Built-in 180°:** a mirror-image board (type B) radiates in antiphase with type A for the same feed.

**Systems:** units fed by an equal-split power divider.

| System | Layout | Claimed performance |
|---|---|---|
| **1-D** | 2 units coplanar (A, B), spacing d = 25 mm = λ0/2 at 6 GHz | The antiphase pair has a null at broadside; tuning the two PSs steers it to ±40° with > 15 dB depth |
| **2-D** | 2 × 2 units (A, B / B, A); every x-pair and y-pair is antiphase | Null planes at u = u0 and v = v0; ±40° per plane with > 10 dB depth |
| **CP** | 4 units as a cross (X), 90° set on one orthogonal pair | RHCP or LHCP, AR < 2.3 dB over 5–7 GHz |

---

## 2. Terminology (how an RF designer describes this design)

| Term | Meaning here |
|---|---|
| **Reflection-type phase shifter (RTPS)** | What the PS really is. A quadrature (3-dB backward) coupler whose through and coupled ports see identical reflective loads Γ. Then S21 = 2ΓTK and S11 = Γ(T² + K²), which are paper eqs. 6–7. The phase of S21 follows the phase of Γ. |
| **Broadside-coupled coupler** | Two strips/patches on opposite sides of a thin dielectric, coupled through an aperture in the ground between them. It gives tight (3 dB), wideband coupling in a small area (Abbosh, ref. [30]). |
| **Even/odd-mode analysis, Z0e/Z0o, coupling factor C** | Standard coupled-line analysis behind eqs. 1–2. C = (Z0e − Z0o)/(Z0e + Z0o); 3 dB means C = 0.707. |
| **Reflective load / transformer stub** | The ~λg/4 stub transforms the varactor impedance. This widens the reflection-phase swing (Fig. 3). |
| **Varactor (hyperabrupt GaAs)** | MAVR-000120-14110P, Ci 0.14–1.7 pF (12:1 ratio), Rp ≈ 2 Ω. It is reverse-biased: cathode to the bias node, anode to ground. |
| **Bias tee / RF choke / DC block** | Choke (paper 100 nH) feeds DC to the varactor while blocking RF. The DC block (paper 39 pF) keeps bias off the RF path. |
| **Self-resonant frequency (SRF)** | Above its SRF a real inductor looks capacitive and a real capacitor looks inductive. A 0402 100 nH part has SRF ≈ 1–2 GHz and 39 pF ≈ 2 GHz, both far below 5–7 GHz (section 9). |
| **Phase imbalance / in-band phase error** | Deviation of a state's phase shift across 5–7 GHz from its band-average. |
| **Microstrip-to-slotline balun** | The back-side microstrip crosses the front-side slot line and ends in an open stub. The slot ends in a square cavity (open). Together they convert unbalanced feed to balanced dipole drive. |
| **Endfire printed dipole** | Arms beyond the ground edge; the ground acts as a reflector, so the beam points off the board tip (+y board, +z world). |
| **Decoupling stub** | The ls strip on the ground edge between neighbouring antennas, which reduces mutual coupling (paper "stub between the two antennas"). |
| **Antiphase pair / difference pattern** | Two identical elements fed 180° apart give a broad pattern with a null broadside to the pair axis. |
| **Null steering** | Moving that null by a differential phase Δφ = k·d·sinθ_null. |
| **Null depth** | Pattern level at the null relative to the beam peak in the same cut. |
| **Rejection at the interferer angle** | What matters in practice: the level *at the jammer's direction*, not the deepest point of the null anywhere. |
| **uv-space** | u = sinθ·cosφ, v = sinθ·sinφ. The 2-D nulls are straight lines u = u0 and v = v0 (Fig. 12). |
| **Beam / null squint** | A phase shifter is not a true-time delay, so a fixed phase setting gives a null angle that changes with frequency. |
| **Axial ratio (AR), LHCP / RHCP** | CP purity and sense. They come from two orthogonal linear components in quadrature (90°). |
| **Crossed-dipole (turnstile) CP** | Two orthogonal dipole pairs fed 90° apart. Here each "dipole" is a pair of opposite wings. |
| **Embedded element pattern** | One unit's pattern measured or simulated inside the array with the others terminated. It includes mutual coupling and is what you feed into the array model for verification. |
| **Phase-matched cables, splitter imbalance** | External feed errors that add to the PS errors (ZX10-2-183-S+ 2-way, ZN4PD-5R183-S+ 4-way in the paper). |
| **Bias look-up table (LUT)** | Mapping from wanted null angle and frequency to phase, then capacitance, then voltage, per unit. |

---

## 3. Verification of the paper's claims (done here)

| Claim | Check | Result |
|---|---|---|
| PS 145–150° range (analytic) | Eqs. 3–7 with paper values (Zcl = Zstub = 50 Ω, 3-dB coupler, Lp = 0, ideal 100 nH / 39 pF) | **114–116°.** For any single-varactor RTPS the limit is 4·atan(√r) − 180° = **116°** for r = 1.7/0.14. 145° needs ≈ 0.3–0.4 nH series inductance (package + pads), which gives 136–147° (`rtps_model.py`, `ns_demo_phase_shifter.m`). |
| ±2° imbalance | Same model, worst state deviation over 5–7 GHz | ±4° (ideal) to ±6–8° with the inductance that gives 145°. Each source defines imbalance differently, so compare like with like in HFSS. |
| IL < 1 dB | Rp = 2 Ω alone | ≈ 0.65–0.70 dB worst state. Substrate and conductor loss come on top, so the measured 0.8 ± 0.15 dB is plausible. |
| ±40° 1-D steering | Δφ = k·d·sin40° = 116° at 6 GHz, split ±58° over the two PSs | Feasible. Max steering ±52° at 6 GHz, ±44° at 7 GHz, ±65° at 5 GHz. **Both** PSs must be tuned; one alone gives only 0–145°, i.e. a one-sided null. |
| Null over 5–7 GHz | Fixed bias set for 40° at 6 GHz | **Squint:** the null sits at 50.5° at 5 GHz and 33.4° at 7 GHz. The bias LUT must be frequency-dependent (`LUT_1D_null_angle_to_bias.csv`). |
| > 15 dB null depth | Monte Carlo, 0.5 dB / 4° rms per channel | Rejection at the interferer angle: median 26 dB, 10th percentile 20 dB, null pointing error under 3.5° (90th pct). **Amplitude error fills the null; phase error moves it.** |
| 2-D ±40° in both planes | Element phases ±αx ± αy must fit in the PS range | Envelope **\|u0\| + \|v0\| ≤ 0.79** at 6 GHz. ±40° in one plane is fine, but simultaneous steering is limited (e.g. about 23.6° in both). |
| CP with Fig. 1(c) colours (U1, U4 red; U2, U3 blue) | Array model, all wings mounted the same way (board x radially outward) | **Opposite wings cancel at broadside**, giving a null instead of CP. Opposite wings must radiate co-phased, i.e. be opposite types (A / B), giving AR = 0 dB ideal. See `SYS_CP_cophased` in the placement table. Verify the sense mapping (which pair gets +90° for RHCP) in HFSS; it depends on numbering and mounting. |
| AR < 2.3 dB | AR vs quadrature / amplitude error | 10° quadrature error gives 1.5 dB; plus 1 dB amplitude imbalance gives 1.8 dB. Consistent with the measurement. |

---

## 4. Geometry, stack-up and what had to be assumed

**Stack-up (unit and PS boards):**

| Layer | z (mm) | Contents |
|---|---|---|
| TOP (front) | 1.116 | PS input feeder, top patch, top stub chain; dipole arms and ground |
| RO4003C | 0.608–1.116 | εr 3.55, tanδ 0.0027, 0.508 mm |
| MID (GND) | 0.608 | PS ground with elliptical slot |
| RO4450F prepreg | 0.508–0.608 | εr 3.52, tanδ 0.004, 0.1 mm |
| RO4003C | 0–0.508 | 0.508 mm |
| BOT (back) | 0 | PS output feeder, bottom patch, bottom stub chain; dipole feed loop |

The 50 Ω widths are 1.145 mm on TOP (0.508 mm to MID) and 1.37 mm on BOT (0.608 mm to MID).

**Dimensions used from the paper:**
- **Phase shifter (Fig. 2):** L 36, W 25, Fl 13.7, Pl 8.8 (listed as "l"), Pw 4.9, Sl 8.8, lstub 9.4, Stl 6.1, h 0.508, prepreg 0.1.
- **Stub chain:** Stl = 6.1 mm is the line from the patch to the DC block; the DC block plus junction pad brings the total to the varactor to lstub = 9.4 mm. This reading makes the top (Stl1) and bottom (Stl2) chains identical, as the paper's symmetry statement requires.
- **Dipole (Fig. 6):** Lant 24, W 25, w1 1.6, w2 1.07, l1 1.65, l2 3.1, l3 14.2, l4 4.5, l5 4, l6 4.1 (printed as "li"), l7 0.43, gs 0.11.

| Item | Problem in the paper | What this pack does |
|---|---|---|
| Dipole substrate | Text says "RT/Duroid 4003C εr = 2.2". RO4003C is εr 3.55; 2.2 is RT/duroid 5880. | εr 3.55. Supporting evidence: w2 = 1.07 mm is 50 Ω on 0.508 mm εr 3.55, but would be ≈ 64 Ω on εr 2.2. |
| Slot Sw | Listed Sw = Sl = 8.8 (a circle), but Fig. 2(e) shows an ellipse with Sw/Sl ≈ 0.6 | Both variants: `PS_slot-paper-8p8x8p8` and `PS_slot-drawing-ratio-8p8x5p3`. Simulate both; the one giving 3-dB coupling at 6 GHz is the intended one. |
| l6 / ls | Both appear in Fig. 6; only one "li = 4.1" is listed. The ls strip width is not given. | l6 = 4.1, ls = 4.1, ls width 1.2 [ASSUMED]. ls is the decoupling stub, so tune it for minimum S21 between neighbouring units. |
| Fig. 6 scale | The drawing is not to scale (its vertical scale differs from the horizontal) | Dimensions taken from the list, never from the drawing. |
| Feed-loop open end | Tail length not stated | Right leg = l5 − l7. Tune for S11 < −10 dB over 5–7 GHz. |
| MID ground under the antenna | Fig. 8 shows the MID ground ending at the dash-dot line (y = 36). The dipole then sits on the full 1.116 mm stack with no inner ground, so the back feed line is referenced to the front ground 1.116 mm away (≈ 80 Ω for 1.07 mm). | Two unit variants: `mid-paper` (as drawn) and `mid-extended` (MID continues under the dipole ground with the same square slot and slot line, stitched by vias). The extended version keeps the 1.07 mm feed at ≈ 58 Ω. The dipole must be re-tuned on the 3-metal stack either way, because the 0.508 mm standalone dimensions do not carry over unchanged. |
| Parts | 100 nH / 39 pF / varactor footprints not given | 0402-class footprints. Check the MACOM land pattern for "-14110P". |
| Vias | Count and diameter not given | 0.3 mm, 3 per connector side, 6 per DC pad. **Through-vias are feasible:** every through-via conflict lands on ground copper (checked), so no blind vias or sequential lamination are needed. |

---

## 5. Boards in this pack

All boards include silkscreen with refdes, port labels, varactor polarity bar, bias labels, unit number, type A/B, beam direction and polarisation arrow. The `<ORG> <PROJECT> REV YYYY-WW` field is a placeholder for your own marking.

| Folder | Board | Purpose |
|---|---|---|
| A_without_antenna | PS standalone, 3 versions (slot per text, slot per drawing, resistor bias) | 2-port VNA characterisation: S21 phase vs bias, IL, RL; builds the LUT. |
| B_antenna_only | Dipole on 0.508 mm, 2 layers | S11 and pattern of the bare antenna (paper Fig. 7). |
| C_units_with_antenna | Unit A / B × MID paper / extended | The integrated element (Fig. 8). |
| D_system_1D_2units | Coplanar panel U1 (A) + U2 (B), plus top-view assembly drawing | 1-D null steering (Fig. 8). |
| E_system_2D_4units | Two coplanar rows (front: U4 A, U3 B; back: U2 B, U1 A) 25 mm apart, plus assembly drawing | 2-D null steering (Fig. 11). |
| F_system_CP_4units | Four wing boards, plus assembly drawings for both type assignments | CP (Fig. 13). |
| G_feed_dividers | Wilkinson 1:2 and 1:4, 6 GHz, 25 mm output pitch, 100 Ω 0402 | Integrated, phase-equal replacement for the external splitters. |
| H_fab_panel | U1–U4 + PS coupon + dipole coupon, fiducials | One fabrication order covering all builds and test coupons. |

**Supporting files:**
- `assembly_3D_placement.csv`: world position and azimuth of every board for each system.
- `BOM_and_placement.csv`: refdes, value, side, x/y, polarity.
- `DRC_report.txt`: copper gaps, thin features, silkscreen over copper.

**DXF layers:**

| Layer | Contents |
|---|---|
| OUTLINE | board edge |
| TOP / MID / BOT | merged copper |
| *_CUTOUT | holes, to subtract in HFSS |
| VIA | drill circles |
| PORT | port reference |
| SILK_TOP / SILK_BOT | silkscreen |
| ASSY_TOP / ASSY_BOT | component bodies |
| FAB | stack-up notes |

---

## 6. Ports, feeds and bias: with and without antenna

| Test | Port definition |
|---|---|
| PS alone | J1 edge SMA on TOP at y = 0 (input), J2 edge SMA on BOT at y = 36 (output). In HFSS: lumped ports, a 0.508 mm (TOP–MID) and a 0.608 mm (BOT–MID) sheet. Prefer wave ports with a de-embedded launch for final numbers. |
| Dipole alone | Edge SMA at y = 0: centre pin on the BOT feeder, body on the front ground. |
| Unit | Only J1 (TOP, y = 0). The PS output continues directly into the dipole feed on BOT. |
| 1-D | U1 and U2 inputs from a 2-way divider through phase-matched cables (or the Wilkinson board). Two bias voltages, one per unit. |
| 2-D / CP | 4-way divider, four bias voltages. |

**Bias wiring:**
- Each unit has VB1 (TOP) and VB2 (BOT) at the same board edge. Tie them together: both varactors of a PS must see the same voltage, which is the paper's "single bias per phase shifter".
- Add 100 pF + 100 nF decoupling at the connector.
- Route bias wires along the board edge, perpendicular to the E-plane and away from the antennas. Long wires near a dipole re-radiate and fill nulls; resistive or ferrite-loaded wires are best.

---

## 7. HFSS workflow

1. **Import.** Import the DXF and map TOP to z = 1.116, MID to z = 0.608 and BOT to z = 0. Subtract each *_CUTOUT from its layer, assign PerfE (finite-conductivity Cu in the final run), and add the three dielectric boxes. Model vias as PEC cylinders.
2. **Components as lumped RLC sheets** across the pad gaps (positions in `BOM_and_placement.csv`):

   | Part | Model |
   |---|---|
   | Varactor | Series Rp = 2 Ω, Lp = 0.35 nH [assumed], C = variable `Cv` |
   | DC block | Series 39 pF + 0.4 nH |
   | Choke | Parallel 100 nH ‖ 0.11 pF (SRF 1.5 GHz) or the vendor S2P; alternatively the recommended 10 kΩ |

   Better still, import the vendor S2P/SPICE models via Circuit co-simulation.
3. **Phase shifter.** Parametric sweep of `Cv` from 0.14 to 1.7 pF (both varactors equal) over 5–7 GHz. Extract ∠S21 relative to the 1.7 pF state, \|S21\| and \|S11\|. Compare with `rtps_cases.png` and the paper's Fig. 5.
4. **Dipole.** Air box with ≥ λ/4 at 5 GHz (15 mm) of clearance, radiation boundary (or PML), 5–7 GHz sweep. Check S11 < −10 dB and broad endfire beam around 5 dBi (paper Fig. 7).
5. **Systems.** Place the boards from `assembly_3D_placement.csv`, or run `04_hfss/hfss_ns_build.py 1D|2D|CP|CPcophased`. Drive all ports with 1 W at 0° (an ideal splitter). Set each unit's `Cv` from the LUT.
6. **Verification sequence:**
   1. Both PSs at mid-range should put the null at broadside.
   2. Step to the LUT values for ±25° and ±40° at 5, 6 and 7 GHz.
   3. Read the null angle, depth and gain (paper Fig. 10).
   4. 2-D: plot the uv map (paper Fig. 12).
   5. CP: first excite **one opposite pair only** and confirm co-phasing at broadside, then add the 90° pair and read AR and sense (paper Figs. 14–15).
7. **Embedded patterns.** Export each unit's embedded pattern (others terminated) to CSV. `array_models.load_element_csv()` replaces the analytic element, so the Python and MATLAB array results become verification-grade, including mutual coupling.

---

## 8. Python and MATLAB

| File | What it does |
|---|---|
| `02_python/rtps_model.py` | Eqs. 1–7 RTPS model, varactor C(V), bias-network parasitics (cases A–D), phase-to-C-to-V LUT. Writes `rtps_cases.png`. |
| `02_python/array_models.py` | 1-D / 2-D / CP systems, steering limits, squint, uv maps, CP co-phasing check, AR sensitivity, Monte Carlo. Writes results/*.png and *.csv. |
| `02_python/nsgeom.py`, `build_boards.py` | Single geometry source; regenerates every DXF, preview, BOM, DRC and assembly file. |
| `03_matlab/ns_demo_phase_shifter.m` | MATLAB copy of the RTPS study. Numbers identical to Python (checked in Octave 8.4). |
| `03_matlab/ns_demo_system.m` | MATLAB copy of the system study: null placement, squint, 2-D envelope, CP check, Monte Carlo. |
| `04_hfss/hfss_ns_build.py` | PyAEDT build of PS / dipole / unit / 1-D / 2-D / CP with variables per varactor. Not executed here (no licence). |

**Equation map:**

| Paper | Python | MATLAB |
|---|---|---|
| eqs. 1–2 | `coupler_TK` | inside `ns_rtps` |
| eq. 3 | `load_gamma` | `ns_rtps` (G) |
| eq. 4 | `tline_zin` | `ns_rtps` (Zin) |
| eq. 5 | `Z_varactor` | `ns_rtps` (Zv) |
| eqs. 6–7 | `rtps_S` | `ns_rtps` |
| Δφ = k·d·sinθ (1-D) | `phases_1d` | `ns_phases_1d` |
| 2-D | `phases_2d` | `ns_phases_2d` |
| AR | `axial_ratio_db` | `ns_axial_ratio` |

---

## 9. Important design steps the paper does not cover

1. **Component SRF.**
   - **Choke:** a 0402 100 nH part resonates at about 1–2 GHz, so at 5–7 GHz it is a small capacitor (≈ 0.1 pF) across the varactor. That reduces the effective C ratio.
   - **DC block:** 39 pF resonates near 2 GHz, so at 6 GHz it looks like +14 Ω of series inductance. Together with the pads this is what makes 145° possible at all (case C).
   - **Recommendation:** co-simulate with the vendor S-parameter files, or bias through a 10 kΩ resistor (the varactor draws only nA). A resistor has no SRF problem; it increases the range in the model (case D) but also the imbalance. Choose by simulation.
2. **The varactor C(V) curve and its spread.** Use the datasheet table, not the fitted model in this pack, and measure every PS coupon. The LUT is per unit, per frequency.
3. **Temperature.** Varactor capacitance drifts with temperature, so the null angle and depth drift too. Include a calibration or temperature-compensation step if the null must hold over temperature.
4. **Linearity under interference.** The interferer you want to null passes through each phase shifter at full power *before* the cancellation at the combiner. Strong signals self-bias the varactors, causing phase modulation and IMD that fill the null. Check P1dB / IIP3 of the PS at the expected interferer level; back-to-back varactors are the usual fix.
5. **Amplitude vs state.** The PS loss changes by up to ≈ 0.6 dB with state. Mismatched states in the two arms fill the null (≈ 0.5 dB rms caps rejection near 25 dB). Choose LUT pairs that also equalise \|S21\|, or add an amplitude trim.
6. **Frequency-dependent LUT.** The null squints by ±8° over 5–7 GHz for a fixed bias.
7. **2-D steering envelope.** \|u0\| + \|v0\| ≤ 0.79 with a 143° PS. State this as the specification, not "±40° in both planes".
8. **CP co-phasing.** Opposite wings must add at broadside; check single pairs first and confirm the sense mapping.
9. **External feed errors.** Splitter imbalance (typically ±0.3 dB / ±3°) and cable phase add directly to the null error budget. Use phase-matched cables (or the Wilkinson boards in G_feed_dividers) and calibrate them out.
10. **Mutual coupling and decoupling stub.** Edge units have different embedded patterns. Verify with embedded patterns, not the isolated element.
11. **Stack-up reality.** RO4003C design Dk is 3.55, while the process (clamped stripline) value is 3.38; the prepreg adds about 0.1 mm. The slot line gs = 0.11 mm is at the limit of standard etching, so specify ±0.02 mm or widen it and re-tune.
12. **MID ground termination** under the antenna and the feed-reference transition at y = 36 (section 4).
13. **Bias-line radiation, ESD, decoupling** (section 6).
14. **Measurement.**
    - Null-depth measurement needs ≥ 40 dB chamber dynamic range and ≤ 0.5° angular resolution near the null.
    - Use uv raster scans for 2-D.
    - Measure CP with a rotating linear source or dual-pol probe.
    - Measure realized gain with a reference horn (paper: 4.6–8.1 dBi).

---

## 10. Researcher's verification checklist

| Step | Pass criterion |
|---|---|
| 1. HFSS: PS alone, both slot variants, Cv sweep | Coupler ≈ 3 dB at 6 GHz; range ≥ 140°; IL ≤ 1 dB; RL ≥ 15 dB over 5–7 GHz |
| 2. Fab + VNA: PS coupon | ∠S21(V) table at 5/6/7 GHz → per-unit LUT |
| 3. HFSS: dipole alone (0.508 mm), then inside the unit (both MID variants) | S11 < −10 dB over 5–7 GHz; endfire gain ≈ 5 dBi |
| 4. HFSS: 1-D with LUT states | Null at 0, ±25, ±40° ± 3°; depth ≥ 15 dB at 5/6/7 GHz |
| 5. HFSS: 2-D | Null planes in uv; depth ≥ 10 dB; states inside the \|u0\| + \|v0\| envelope |
| 6. HFSS: CP (co-phased) | AR ≤ 2.3 dB at broadside over 5–7 GHz; both senses |
| 7. Python/MATLAB with HFSS embedded patterns | Network model agrees with full-wave within 1 dB / 2° |
| 8. Chamber | Patterns vs simulation; null pointing ≤ 3°; realized gain 4.6–8.1 dBi |

---

## 11. Paper targets

| Item | Paper |
|---|---|
| PS | 145° range (sim), ±2° imbalance, IL 0.8 ± 0.15 dB, RL > 20 dB (analytic), 5–7 GHz (33.3%) |
| Dipole | S11 < −10 dB 5–7 GHz, realized gain ≈ 5 dB |
| 1-D | ±40°, depth > 15 dB, gain 4.6–7.8 dBi, sim/meas null shift < ±3° |
| 2-D | ±40° in xz and yz, depth > 10 dB, gain 6.1–8.1 dBi |
| CP | AR < 2.3 dB (meas.) 5–7 GHz, LHCP and RHCP |
| Varactor biasing | 1-D: 4 varactors, 2 voltages; 2-D / CP: 8 varactors, 4 voltages |
