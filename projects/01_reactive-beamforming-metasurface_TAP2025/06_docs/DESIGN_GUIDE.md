# Reactive Beamforming Metasurface — Designer's Guide

Companion to: M. Almunif, F. Alsolamy, A. Grbic, "Network-Based Design of Reactive Beamforming Metasurfaces", IEEE Trans. Antennas Propag., vol. 73, no. 8, Aug. 2025.

This guide covers the full design loop: geometry, simulation, synthesis, optimisation, realisation and prototype. It is written the way an RF design review would walk through it, and every equation number refers to the paper.

---

## 1. The design in one paragraph

An 11×11 grid of λ0/5 cells (5.7 mm at 10 GHz) is treated as a **121-port microwave network**. One full-wave run gives the 121×121 **impedance matrix Z** and the **element pattern of every port**. After that, everything is circuit algebra:

1. Pick a far-field pattern.
2. Solve for the port currents that produce it (eq. 8).
3. Convert those currents into the load impedances that force them (eq. 5).
4. Throw away the real (lossy/active) part.
5. Optimise the reactances so the surface stays **passive and lossless** while still meeting the pattern and the port match (eq. 11).

Because the loads sit behind a ground plane (aperture coupling), the **same board** becomes a directly fed antenna or a reflector just by changing the loads. The final loads are printed as **meandered open-circuit microstrip stubs**.

---

## 2. Terminology a professional designer uses for this work

| Term | Meaning in this design |
|---|---|
| **Unit cell** | One 5.7 × 5.7 mm tile: patch (L1), slotted ground (L2), microstrip + via (L3). |
| **Aperture coupling** | Energy passes from the patch gaps to the microstrip through a slot in the ground. The ground shields the load from free space, so the load does not radiate. |
| **Lumped port** | A 2-D sheet port between the strip and the ground (here 0.4 × 0.203 mm, vertical). It defines the **reference plane** where the load "sits". |
| **Reference plane** | The physical point where Z_L is defined. The meander must present X at *this* plane, which is why stub lengths are measured from it. |
| **Impedance matrix Z (Z-parameters)** | V = Z·I for all 121 ports. Off-diagonal terms = **mutual coupling**. It comes from HFSS as S-parameters and is converted with Z = Z0(I+S)(I−S)⁻¹. |
| **Block partition Z_LL, Z_LE, Z_EL, Z_EE** | L = loaded (terminated) ports, E = excited ports (eq. 1). |
| **Embedded (active) element pattern** | Far field when one port is driven and all others are terminated. HFSS terminates them in 50 Ω by default. |
| **Current-basis / open-circuit element pattern** | Far field for 1 A at port m with every other port **open** (I = 0). The paper uses this basis, so E_tot = Σ I_m E_m exactly. Convert HFSS data with `mtsf_embedded_to_open.m`. |
| **Pattern synthesis by projection** | Taking inner products of eq. 6 with each element pattern (eq. 7) gives the **Gram matrix** system of eq. 8. |
| **Gram matrix** | G_mn = ⟨E_m, E_n⟩. For a lossless array it is proportional to Re{Z}, i.e. radiated power. It is ill-conditioned for sub-wavelength cells, so we regularise it. |
| **Hadamard division (⊘)** | Element-by-element division used in eqs. 4–5. |
| **Passive / lossless / reactive load** | Re{Z_L} = 0. Re > 0 dissipates power; Re < 0 would need gain (an active element). |
| **Seed** | Starting point of the optimiser: Im of the analytic complex loads (Sec. IV). |
| **Reduced impedance matrix** | The K×K matrix seen at the feeds once all loads are attached (eq. 13). It gives S11 and isolation (eq. 14). |
| **Return loss / S11, mismatch loss** | Feed match. Mismatch loss = −10·log10(1−\|S11\|²); Table I gives 0.26 dB. |
| **Isolation (S21)** | Coupling between the two MIMO feeds (Design III: −34 dB network, −30 dB HFSS). |
| **Array factor, pattern multiplication** | Edes = AF · element pattern (eqs. 21–23), assuming y-directed magnetic-dipole cells (eq. 22). |
| **E-plane / H-plane** | φ = 0 (E-field of the cell lies in it) / φ = 90°. |
| **Visible region, evanescent spectrum** | The DFT of the port currents (Fig. 5). Only \|k\| < k0 radiates. The reactive loads use the evanescent (\|k\| > k0) part to shuttle power across the aperture, which is how a passive surface reaches the needed amplitude taper from one feed. |
| **Local periodicity approximation (LPA)** | The classical alternative: design each cell as if it sat in an infinite periodic array. It ignores coupling between unlike neighbours and cannot control amplitude, which is what this method fixes. |
| **Method of moments / homogenisation** | The other alternative (refs [12]–[20]): many basis functions per cell, needs fast matrix inversion, then cells are "extracted" into geometry. The network method uses 1 port per cell instead. |
| **Directly fed metasurface** | K feeds drive the surface, and the other N cells are loaded (Designs I–III). |
| **Reflective metasurface / reflectarray** | All ports are loaded and a plane wave or horn illuminates the surface (Designs IV–V). |
| **Open-circuit voltage, vector effective length** | Receive-mode drive of each port by the incident wave (eqs. 17–20). It is the Thevenin source of each cell. |
| **Scattered field with ports open, E_s\|open** | Structural scattering of the board when no current flows in the ports (eq. 15). It needs one extra HFSS run. |
| **Orthogonal beams** | Beams spaced so their patterns are orthogonal over the aperture (eq. 25). This minimises feed-to-feed coupling. |
| **Mask synthesis** | A flat-top region, a transition region and a sidelobe region (Design II, SLL < −13 dB). |
| **Directivity, gain, radiation efficiency** | Table I: D = 16.1 dB, G = 14 dB, η_rad = 62.5% (Design I realised). Design IV gives η = 75%. |
| **ε_eff, λg, Zc** | Microstrip effective permittivity (≈ 2.75), guided wavelength (≈ 18.1 mm at 10 GHz), line impedance (≈ 54 Ω for 0.4 mm on 0.203 mm RO4003C). |
| **Open stub, open-end extension Δl** | Zin = −jZc·cot(βl). The fringing field makes the stub look ≈ 0.08 mm longer, so we subtract it. |
| **Meander** | A folded stub so a λg/2-class length fits in a λ0/5 cell (Fig. 10). |
| **Multistart** | Running the optimiser from several start points, because reactive-load landscapes are multimodal. |
| **DRC** | Design-rule check: copper-to-copper gaps, metal over slots, cell overflow (`drc_check.py`). |

---

## 3. Geometry (rebuilt from Fig. 3 at 600 dpi)

The cell is drawn exactly as Fig. 3:

- **L1 patch layer:** the cell is centred on the 0.55 mm cross-shaped gap, so the four patch quarters belong to patches centred on the cell **corners**. The array therefore has a 12 × 12 patch grid.
- **L2 slotted ground:** a 4.8 mm slot straddles the cell's **top edge**. It is 0.3 mm on each side, so 0.6 mm in total.
- **L3 strip layer:** a 0.4 mm strip runs from the **port** (0.7 mm below the top edge) up across the slot to a **shorting via** 0.4 mm into the cell above. The via boosts the slot's magnetic field and therefore the coupling (paper ref. [25]).

| z (mm) | Layer |
|---|---|
| 1.016 | L1 patches (copper) |
| 0.203–1.016 | RO4003C, εr 3.55, tanδ 0.0027, h = 0.813 mm (32 mil) |
| 0.203 | L2 ground with slots |
| 0–0.203 | RO4003C, h = 0.203 mm (8 mil) |
| 0 | L3 strips, ports, meander loads (bottom side) |
| 0–0.203 | vias L3 → L2 |

**Values the paper does not state** (all are parameters in `05_python_tools/msgeom.py`; change them in one place and rebuild):

| Parameter | Value used | How to settle it |
|---|---|---|
| Slot width per side | 0.3 mm (0.6 mm total) | Fig. 3 shows 0.3 mm at each edge. If your cell sim mismatches badly, try 0.3 mm total. |
| Via drill | 0.2 mm | Fab capability on 8 mil core. |
| Strip width | 0.4 mm (≈ 54 Ω) | The paper says a 50 Ω line; 0.45 mm gives ≈ 50 Ω. Re-run if you change it. |
| Port position | 0.7 mm below the top edge | From Fig. 3. |
| Meander pitch / lead / tail | 0.8 / 0.3 / 0.5 mm | Fig. 10 gives 1 mm lead from the edge, 0.4 mm width, 0.5 mm tail. |
| Array patch boundary | 12 × 12 full patches | The edge cells' slots need a patch above them. |

**Earlier versions of these DXFs** placed the patch at the cell centre and the slot under it. That was wrong; every file in this pack uses the corrected Fig. 3 geometry.

---

## 4. How the ports and feeds work

### In simulation
- **Every cell has one lumped port** (a vertical sheet strip → ground at the port plane, integration line upward, 50 Ω reference). Solve once with all 121 ports present to get Z and the patterns.
- **Directly fed designs:**

  | Design | Feed cell(s) | Feed | Loads |
  |---|---|---|---|
  | I, II | R6C6 (centre) | 50 Ω source | the other 120 ports |
  | III (MIMO) | R6C4 and R6C8, 0.6 λ0 apart | 50 Ω source on each | the other 119 ports |

  In the verification run the load ports become **lumped RLC boundaries**: L = X/ω for X > 0, C = −1/(ωX) for X < 0.
- **Reflective designs (IV, V):** all 121 ports carry loads. The excitation is an **incident plane wave** from (θi, φi) = (30°, 0°), θ-polarised (E along x, matching the cell's E-plane). Design V adds a second incidence from (30°, 90°), φ-polarised.
- The paper's network model treats an **inactive feed as open** (I_E = 0). On a real board it is terminated in 50 Ω. With −30 dB isolation the difference is negligible, but check it in the final HFSS verification.

### On a prototype
- **Fed cell:** the strips are on the exposed bottom layer, so the feed is a **vertical SMA (or 2.92 mm) launch from the back**. The centre pin lands on the strip at the port plane and the outer conductor goes to the ground through a back-drilled via fence.

  Model the connector footprint in the final HFSS run: it adds a pad capacitance that detunes S11.
- **Load cells:** the meander replaces the lumped load. Nothing is soldered, so the surface is fully printed.
- **Reflective measurement:** horn illumination in a bistatic setup in an anechoic chamber. The far-field distance 2D²/λ with D ≈ 89 mm (diagonal) is about 0.53 m at 10 GHz. Gate the direct horn-to-horn path in time.
- **Reconfigurable version:** replace the meanders with **varactors** (for example a 0.1–1 pF varactor spans only about −160 to −16 Ω at 10 GHz, so add a series inductive line to shift the range across −150…+150 Ω). Model the ESR, because it cuts efficiency, and bias through the via/ground or with RF chokes.

---

## 5. Files in this pack

| Folder | Content |
|---|---|
| 01_dxf_base | Fig. 3 unit cell (all layers and per layer); three lumped-port 11×11 arrays (centre-fed, 2-feed MIMO, reflective); `meander_lib/` single cells with stub length 1.5–8.5 mm for Zin extraction; reactance → stub length table; previews. |
| 02_reactance_data | Per-cell reactances digitised from Figs. 4a, 6a, 7a, 8b, 9b; side-by-side check image; source crops. |
| 03_dxf_realized | **Fig. 11 rebuild** (Design I, meanders, centre feed) and **Fig. 12 rebuild** (Design IV beam splitter), plus Designs II, III, V; per-cell tables (row, col, X, stub length, turns); previews. |
| 04_matlab | Full eq. 1–25 pipeline, toy-array demo (runs without HFSS), real-data template, self-tests, reference plots. |
| 05_python_tools | `msgeom.py` (single source of geometry), `build_dxf.py` (regenerate or realise from your X), `drc_check.py`, `digitize_reactance_maps.py`, `hfss_build_and_export.py` (PyAEDT). |

**DXF layers:**

| Layer | Contents |
|---|---|
| L1_PATCH | patches |
| L2_GND_BOARD | full ground outline |
| L2_GND_SLOT | slots to subtract from the ground |
| L3_STRIP | strips and meanders |
| VIA | circles, to extrude 0–0.203 mm |
| PORT_FEED_50ohm | thin rectangles marking feed port planes |
| PORT_LOAD_jX | thin rectangles marking load port planes |
| BOARD_OUTLINE | board edge |
| TEXT | R/C labels |

All coordinates are in mm and the array centre is at the origin. Row 1 is at the top (+y) and column 1 at the left (−x). The port index used everywhere is m = (row−1)·11 + col.

---

## 6. HFSS setup (GUI route; `hfss_build_and_export.py` automates the same)

1. **Import.** Modeler → Import → DXF. Map L1_PATCH to z = 1.016, L2_GND_BOARD and L2_GND_SLOT to z = 0.203, L3_STRIP to z = 0. Skip TEXT and the port marker layers, or keep them only as guides.
2. **Ground.** Subtract L2_GND_SLOT from L2_GND_BOARD, then assign **Perfect E** to the ground, patches and strips. Use finite conductivity (copper, 17.5 µm roughness-free) only in the final efficiency run.
3. **Substrates.** Two RO4003C boxes. The real board also needs **bonding film** between them (for example RO4450F, εr ≈ 3.5, ≈ 0.1 mm). It changes the total thickness and εr, so include it before fabrication.
4. **Vias.** PEC cylinders, 0.2 mm diameter, z 0 → 0.203, at the VIA circles.
5. **Ports.** At each port marker draw an XZ sheet, 0.4 mm wide (x) × 0.203 mm tall (z), from the strip edge up to the ground. Assign a **lumped port**, 50 Ω, with the integration line from strip to ground, so 121 ports in total.
6. **Boundary.** Air box with λ0/4 (7.5 mm) clearance on every side and a radiation boundary, or PML / FE-BI for a tighter box. Add an infinite sphere with θ 0–180° step 2° and φ 0–356° step 4°. These must match `dth`/`dph` in MATLAB.
7. **Solve.** Single frequency 10 GHz, max ΔS 0.01, at least 12 passes. Use "Port only" Z output if memory is tight; a 121-port run benefits from HPC/DDM.
8. **Export Z.** Results → Solution Data → Export Matrix Data → Touchstone `metasurface_121port.s121p`, 50 Ω, design frequency only.
9. **Export patterns.** For each port, Edit Sources (that port 1 W, others 0 W) and export a Far-Field data table of re/im of rETheta and rEPhi versus θ, φ to `ff/port_###.csv`. The script writes the exact column format `mtsf_load_hfss_patterns.m` reads.
10. **Reflective only.** A second design with **no port excitations and the port sheets left open** (no boundary), plus an incident plane wave from (30°, 0°), θ-pol. Export the scattered far field to `ff/scat_open.csv`. This is E_s|open of eq. 15.

### Meander Zin extraction
This is how the paper realises the loads in Sec. VII.

1. Run `python hfss_build_and_export.py meander`. For each stub length it builds a 3×3 cell patch with the measured cell's via-side strip removed, so the port sees only the stub (as in Fig. 10).
2. It writes `meander_Zin_table.csv` with columns L, X, R.
3. `build_dxf.py realise ... --table meander_Zin_table.csv` then uses those in-situ values instead of the analytic first guess.

---

## 7. MATLAB pipeline: equation map

| Paper | Function | Notes |
|---|---|---|
| eq. 1 | `mtsf_read_touchstone` | S → Z at f0 |
| eqs. 2–5 | `mtsf_loads_from_currents` | Z_L = (V_exc − Z_LL I_L) ⊘ I_L |
| eqs. 6–8 | `mtsf_synth_currents` | Gram system with Tikhonov regularisation |
| eq. 9 | `mtsf_currents_from_loads` | I_L = (jX + Z_LL)⁻¹ V_exc |
| eq. 10 / eq. 15 | inside `mtsf_cost` | E = E0 + sgn·F_L I_L |
| eq. 11 | `mtsf_cost` | pattern + Σ\|S_ii\| + Σ\|S_ij\|, **analytic gradient** |
| eqs. 12–14 | `mtsf_reduced_S` | reduced Z and S at the feeds |
| eqs. 17–20 | `mtsf_voc_planewave` | open-circuit voltages for a plane wave |
| eqs. 21–24 | `mtsf_array_factor`, `mtsf_desired_pattern` | uniform or multibeam |
| eq. 22 | `mtsf_magdipole_pattern` | element model |
| eq. 25 | `mtsf_orthogonal_beams` | MIMO beam angles |
| Sec. IV | `mtsf_seed`, `mtsf_optimize`, `mtsf_multistart` | fmincon (MATLAB) or projected L-BFGS (Octave) |
| Sec. VII | `mtsf_X_to_stub`, `mtsf_X_to_LC`, `mtsf_write_X_csv` | realisation outputs |

**Run order:**

1. `mtsf_selftest` checks power consistency, gradients and the pattern conversion.
2. `mtsf_demo_paper_designs` runs Designs I–IV on an analytic 11×11 array in about 2–3 minutes.
3. `mtsf_design_from_hfss` is the same flow on your HFSS exports. Set `design = 'I'...'V'`.

It writes `designX_X_optimised.csv`, which goes into `python build_dxf.py realise designX_X_optimised.csv out.dxf --feeds 6,6`, giving the realised DXF.

**Verified here** (GNU Octave 8.4, toy array):

| Check | Result |
|---|---|
| Re{Z} vs Gram/η | 5e-5 |
| Analytic vs finite-difference gradient | 1e-9 |
| Touchstone round trip | 8e-13 |

| Design | Toy result |
|---|---|
| I | pattern mismatch 0.96 → 0.016 |
| II | ripple 0.5 dB, sidelobe −8.4 dB (toy cannot reach −13 dB) |
| III | beams ±28.6°, isolation −31 dB |
| IV | mismatch 0.054 |

The toy uses free-space dipoles, so its S11 values are unrealistically good. Only real HFSS data gives true numbers.

---

## 8. What the paper glosses over (important for a real design)

1. **Pattern basis.** Eq. 8 needs open-circuit (current-basis) patterns. HFSS gives 50 Ω-terminated embedded patterns, so you must convert them with Fopen = Fhfss(Z + Z0·I)/vs. Skipping this silently corrupts the synthesis.
2. **Gram-matrix conditioning.** For λ0/5 cells, eq. 8 is close to singular, because evanescent current modes have no far field. Use the regularised solve in `mtsf_synth_currents`, otherwise the seed loads blow up.
3. **Inner-product weight.** Eq. 7 integrates dθdφ without sinθ, which over-weights the poles. The solid-angle weighting used here keeps the Gram matrix ∝ Re{Z}. You can switch to the literal form in `mtsf_angle_grid`.
4. **Field scale in eq. 11.** \|Edes − Etot\|² depends on absolute field level (source power, plane-wave amplitude). The cost here uses the optimal free complex scale, which gives a normalised error, so α, β and γ are comparable.
5. **Multimodality.** A lossless load limits each cell's current phase to roughly 180° relative to its drive. Full control comes from coupling, so the landscape has many minima. Always multistart. The toy demo shows a spread of J = 0.05 to 0.8 between starts.
6. **Realisable range.** Bound X to what fits. A λ0/5 cell holds stubs up to about λg/2, giving roughly −150 to +150 Ω with useful sensitivity. Near ±∞ (stub ≈ λg/4 or λg/2) the length sensitivity explodes, so avoid those values.
7. **Load dispersion and bandwidth.** Stub reactance changes with frequency (dX/df is large near resonance). Sweep 9.5–10.5 GHz in the verification run. A beam squint and pattern break-up of a few percent bandwidth is typical for this class of surface.
8. **Finite-array edges.** Patterns must come from the full 11×11 run, not a periodic cell. Edge cells behave differently, and that is exactly the coupling this method captures.
9. **In-situ load extraction.** The meander couples to the slot, to neighbours and to the via strip. Extract Zin in a 3×3 environment (the script does this), not as an isolated line.
10. **Stack-up reality.** Bonding film, copper thickness, via plating, and etch tolerance of ±25 µm on 0.4 mm lines all matter. A 2% εr shift at 10 GHz moves the stub phase noticeably, so re-run Z with the fab's actual stack-up.
11. **Losses.** Table I gives 1.8 dB dielectric + ohmic loss, because the stubs store energy (high Q). Use RO4003C or a lower-loss alternative, keep the meanders short where X allows, and include copper roughness in the final run.
12. **Inactive MIMO port.** It is open in the model but 50 Ω on the board; verify in HFSS.
13. **Digitised loads are seeds.** The reactance maps in 02_reactance_data come from colour images. Accuracy is about ±3 Ω, values at the ends of each colourbar may be clipped (for example 99 Ω and −114 Ω), and they belong to the paper's exact geometry. On your geometry, re-optimise with `mtsf_design_from_hfss`.

---

## 9. Paper targets to check against

| Design | Network model | HFSS |
|---|---|---|
| I: beam to (−30°, 0°), centre feed | S11 −14.02 dB | −14.37 dB |
| II: flat-top ±20°, SLL < −13 dB | S11 −14.65 dB | −15 dB |
| III: beams ±28.5° (H-plane) | S11 −11.3 dB, S21 −34 dB | S11 = S22 = −11 dB, S21 −30 dB |
| IV: (30°, 0°) → (±30°, 90°) | pattern match | pattern match |
| V: two incidences to two directions | pattern match | pattern match |
| Realised I (meanders) | S11 −13.7 dB | D 16.1 dB, G 14 dB, η 62.5%, mismatch 0.26 dB |
| Realised IV | — | η_rad 75% |

---

## 10. Prototype checklist

- [ ] Re-run the cell with the fab's real stack-up (bondply, copper, εr at 10 GHz).
- [ ] Full 121-port Z and patterns, then convert to current basis, then optimise with bounds and multistart.
- [ ] Verification run with lumped RLC, then with meanders (realised DXF).
- [ ] Frequency sweep 9–11 GHz: S11, gain, beam direction.
- [ ] DRC: line/space ≥ 0.1 mm (this pack's realised layouts have ≥ 0.65 mm), no metal over slots, via annular ring ≥ 0.1 mm.
- [ ] Add the connector footprint and back-drill on the fed cell; add alignment marks and a board edge margin of ≥ 2 mm.
- [ ] Gerbers: import the DXF layers into KiCad/Altium as L1 (top copper), L2 (inner copper, slots as voids), L3 (bottom copper), plus a drill file from the VIA layer.
- [ ] Measurement plan: chamber, far-field distance ≥ 0.53 m, time gating for the reflective case, and a reference horn for gain.
