# CRL-LS-CRPA4: L/S-band 4-channel CRPA front end - design basis (draft, 2026-11-05)

What is known, decided and still open before the RF module, its shield cover, the test board and the back cover
are designed. Everything here is either read from the customer Gerbers (`00_input/PCB_FAB_LS_4E`, decoded by
`02_python/read_interface.py`), taken from projects 16 / 17, or marked `[ASSUMED]` / `[OPEN]`.

## 1. Customer board `combine_model_2.0` (BEL CRL "Antenna / RFM", 14-08-2026)
| Item | Value (source) |
|---|---|
| Outline | Ø200.0 mm round, centre at Gerber (132.881, -122.331) |
| Stack-up | 6 layers, 1.751 mm: F.Cu / FR4 0.508 / In1 / FR4 0.2 / In2 / FR4 0.2 / In3 / FR4 0.2 / In4 / **RO4350B 0.508** / B.Cu; Cu 18 µm (In2 25 µm); ENIG; impedance controlled; IPC-6012 class 2 (job file + fab note) |
| F.Cu (antenna side) | solid ground disk, antenna ground plane; silk "GPDF6010" marks at the patch sites |
| In1 / In3 | via pads only (stitching / fences); In2: +VDC ring (1.21 mm trace), In4: solid ground = reference of B.Cu |
| B.Cu (RF side) | 50 Ω microstrip **1.1 mm** on RO4350B 0.508 over In4; lumped 90° hybrids per element and band; via fences |
| L-band elements | 4 × Taoglas **GPDF6010** stacked L1/L2 patch (as identified in project 17) at (±45.5, ±45.5) mm, r = 64.3 mm, 91 mm pitch; centre screw Ø3.2, 4 × M3 fixing Ø3.6 at ±29 mm; feed pins Ø1.35: **L1 at 5.5 mm**, **L2 at 12.25 mm** from the centre (0° / 90°) |
| S-band elements | 4 sites on the axes at r = 70.8 mm, 4 feed pins Ø0.77 at 4.0 mm (S(0), S(90) routed), small lumped hybrid each |
| RF module sites | **4 footprints**, one per channel, r = 34.72 mm, rotated 0/90/180/270 deg (`CRL-LS_module_placement.csv`) |
| Outputs | L_OUT / S_OUT per channel: Ø1.73 SMD centre pad + 2 ground pads at ±2.8 mm (coax pigtail launch) |
| DC input | 2-pin header (Ø1.0 holes) "VDC GND" near the north edge, feeding the In2 ring |

### Module footprint (`CRL-LS_module_footprint.csv`)
2 rows × 13 pads, 1.35 × 2.54 mm, **pitch 1.829 mm**, rows **25.474 mm** apart (pad centres), row length 21.95 mm.
Silk box ≈ 24.4 × 30 mm. Pads with traces on the main board (reference module, module frame, inputs at +y):

| Pad | x (mm) | Signal | Main-board trace |
|---|---|---|---|
| T02 | -9.145 | IN_L1 (RHCP, after on-board hybrid) | 1.1 mm 50 Ω |
| T03 | -7.316 | TIE_A `[OPEN]` | 0.3 mm |
| T04 | -5.487 | IN_L2L5 (RHCP) | 1.1 mm 50 Ω |
| T07 | 0.000 | VDC +5 V | 1.21 mm via to In2 ring (+ 0.3 mm tie) |
| T10 | +5.487 | IN_S (RHCP) | 1.1 mm 50 Ω |
| B10 | +5.487 | OUT_L (L1 + L2/L5 combined) | 1.1 mm to L_OUT pad |
| B11 | +7.316 | TIE_B `[OPEN]` | 0.3 mm |
| B12 | +9.145 | OUT_S | 1.1 mm to S_OUT pad |
| others | | GND `[ASSUMED]` (in the ground pour) | none |

Open: what the three 0.3 mm traces are for (DC sense / control / ground ties). Ask BEL CRL.

## 2. Decisions taken with the user (2026-11-05)
| # | Decision |
|---|---|
| D1 | Bands: **L1** 1559-1610 MHz (GPS L1, Galileo E1, BeiDou B1, NavIC L1, GLONASS G1 partly), **wide L2/L5** 1164-1240 MHz (L5/E5a/E5b/B2/L2), **NavIC S** 2483.5-2500 MHz (2492.028 MHz centre) |
| D2 | **Plug-in shielded RF module**, 4 identical, soldered on the existing 24-pad (2 × 13) footprint; the customer main board is not changed |
| D3 | Supply **+5 V** on the VDC ring; module regulates / filters locally |
| D4 | Back cover: **8 × SMA bulkheads** (4 × L, 4 × S) + 1 sealed circular DC connector |
| D5 | **Use the project 16 / 17 components** (user instruction, 2026-11-05); "2 LNA + 3 filters" per band as in project 17 |

## 3. RF chain per module (from projects 16 + 17)
```
IN_L1    -> CLM-83-2W+ -> TQP3M9037 -> B7504 -> TQP3M9037 -> B7504 -> B7504 ---+
                                                                               +-> DXP.02.A -> OUT_L
IN_L2L5  -> CLM-83-2W+ -> TQP3M9037 -> B8889 -> TQP3M9037 -> B8889 -> B8889 ---+
IN_S     -> CLM-83-2W+ -> TQP3M9037 -> TA1442A -> TQP3M9037 -> TA1442A -> TA1442A -> OUT_S
```
The 90° hybrids (project 16/17: HC125A, C2327J5003AHF) are **not** on the module: the customer board already has
lumped hybrids per element and band. Module = 3 limiters, 6 LNAs, 9 SAWs, 1 diplexer + bias.

| Part | Function | Package | Key data (source) |
|---|---|---|---|
| Mini-Circuits **CLM-83-2W+** | limiter, 30-8200 MHz | DL1721 ceramic, 3.0 × 3.0 × 1.14 mm | IL 0.14 @1.2 GHz, 0.18 @1.8, 0.22 @2.4 GHz; limits to +11.5 dBm out; 2 W max; pin 2 IN / 7 OUT (`00_vendor/CLM-83-2W+.pdf`) |
| Qorvo **TQP3M9037** | LNA, 0.7-6 GHz | DFN-8 2 × 2 mm | 20 dB / 0.4 dB NF / OIP3 +35 / OP1dB +20 dBm @1950 MHz, 5 V 70 mA (p16 `ds_data.py`, Touchstone with noise) |
| Qualcomm **B7504** (B39162B7504L210) | L1/B1/G1 SAW | 0.9 × 0.7 × 0.5 mm, 4 pads | IL 0.89 dB @1575; no matching (p16) |
| Qualcomm **B8889** (B39122B8889P810) | L2/L5/B2 SAW | 1.1 × 0.9 × 0.45 mm, 5 pads | 1166-1229 MHz spec band; needs 6.8 nH shunt in/out; IL 0.91 @L5, 1.45 @L2 (p16) |
| Taoglas **DXP.02.A** | L1 / L2+L5 diplexer (combiner) | Taoglas DXP.02.A footprint | IL 3.8 (L1) / 4.2 dB (L2L5) typ; 4.3 nH + 1.5 pF match on common port (p16) |
| Tai-Saw **TA1442A** | NavIC S SAW, 2492 MHz | 3.0 × 3.0 × 1.4 mm, 6 pads | IL 1.55 dB typ (2489.5-2494.5), rej. 33 dB DC-2390, 43 dB 2575-3000; Pmax +10 dBm, Vdc max 3 V (p16) |

Project results to carry over (25 °C, element input):
| Branch | Gain | NF | Source |
|---|---|---|---|
| L1 1575.42 | 37.2 dB | 1.09 dB | p17 (limiter + 3rd SAW + routing) |
| L5 1176.45 | 40.9 dB | 0.86 dB | p17 |
| L2 1227.60 | 38.4 dB | 0.89 dB | p17 |
| S 2492.028 | 35.0 dB, NF 1.17 dB, IIP3 -1.4 dBm, OP1dB +18.1 dBm | | p16 (2 SAW, no limiter: to be updated with limiter + 3rd SAW) |

Power: 6 × TQP3M9037 at 5 V / 70 mA = **420 mA per module, 2.1 W**; 4 modules **1.68 A, 8.4 W** (max 90 mA each:
2.16 A, 10.8 W). Project 17 drew 1.12 A typ for 16 LNAs. This is the main thermal load of the closed CRPA, see §5.

## 4. Things checked on the web this session (not used, kept for the record)
| Part | Finding |
|---|---|
| Infineon BGA524N6 | GNSS LNA 1550-1615 MHz only (not L2/L5), 19.6 dB, 0.55 dB NF, 2.5 mA, input P1dB -12 dBm: too little linearity for anti-jam |
| Mini-Circuits PSA4-5043+ | 50 MHz-4 GHz, NF 0.75 @1 GHz / 0.98 @2 GHz, gain 18.4 @1 GHz / 13.3 dB @2 GHz (5 V, 56-66 mA): low gain at S |
| Qorvo QPL9503 | 0.6-6 GHz flat-gain LNA, optimised 3-6 GHz (21.6 dB, 0.9 dB @5.5 GHz), OIP3 +35 dBm, 3.3-5 V 65 mA: no 2.5 GHz data |
| Qualcomm B2642 | L2/L5/E6 SAW, 1166-1284 MHz usable, 1.4 × 1.1, IL 1.1-2.2 dB: alternative if E6 / wider L2 is wanted |
| Qualcomm B2637, B2651, B2627 | L5/E5 (1164-1219), L1+L2L5 comb, L2/L5 (1207.5 MHz centre): alternatives |
| Qualcomm B39162B3913U410 | L1 SAW 1588 MHz, 56 MHz BW, 2 dB, 3 × 3 mm: larger than B7504 |
| Qorvo 856611 | 2491.75 MHz, 16.5 MHz BW, IL 3.4 dB, 3 × 3 mm: **end of life (PCN 17-0033)** |
| Akoustis SF2381E / SF2669K | 2492 / 2491.75 MHz SAW listings, bandwidth unclear |
| Fujicrystal FSF-3030 | 3 × 3 mm SAW with 2492 MHz standard centre, 6/10/15/50 MHz BW options: second source for TA1442A footprint |
| Abracon AFII-SW-0065 / -0095-Q | GNSS L2/L5/L6 SAW, L1/L2/L5/L6 SAW diplexer: alternatives to B8889 / DXP.02.A |
| Mini-Circuits RLM-63-2W+ | limiter 30-6000 MHz, TT1224 7.62 × 6.35 mm: too large for the module (CLM-83-2W+ used) |

## 5. RF-engineering points that are not yet covered (to settle during the design)
1. **Channel matching is the CRPA's key spec.** Nulling depth depends on gain/phase tracking between the 4 channels
   (target ≤ 0.5 dB / ≤ 5° over temperature after calibration [ASSUMED], or as the CRPA processor needs). Same parts
   from the same reel/lot per set, identical module layout, equal-length pigtails, factory S21 phase measurement of
   each module (the test board does this), and a calibration table delivered with each unit.
2. **Linearity / jammer headroom.** With ~37-41 dB gain the cascade IIP3 is about -8 to -12 dBm (p16): a strong
   in-band jammer compresses LNA2 before the processor can null it. Decide the receiver-side gain and whether one LNA
   per band can run at lower gain; the limiter only protects against damage (+12 dBm), not compression.
3. **Out-of-band interferers**: DME/TACAN 960-1215 MHz and L-band radar 1215-1400 MHz sit inside/next to the wide
   L2/L5 band; LTE B7/B40/B41 and Wi-Fi 2.4 GHz are next to NavIC S (2483.5); Iridium 1616-1626 and Inmarsat next to L1.
   The first filter is after LNA1, so LNA1 sees them unfiltered: check LNA1 P1dB against the worst field.
4. **SAW power limits**: TA1442A +10 dBm and 3 V DC max, B8889 +5 dBm: every SAW needs a series DC block, and the
   output of LNA2 (OP1dB +20 dBm) can exceed the SAW rating under jamming.
5. **Stability**: 6 LNAs with ~20 dB each in a 25 × 30 mm box. Each band needs its own shielded compartment, the
   S chain separated from L, and lid resonances above 3 × 2.5 GHz (cavity design as in project 01).
6. **Thermal**: 8.4 W in a sealed Ø200 mm CRPA. The module ground must sink through the main-board vias into the
   back cover; consider running the LNAs at 3.3-4.2 V (TQP3M9037 is specified 3.0-5.25 V) to halve the dissipation.
7. **ESD / lightning** at the antenna: the limiter helps; add a DC-grounded path (the hybrids may already DC-ground the probes).
8. **Group delay ripple** of 3 SAWs in series and of the DXP: matters for the CRPA's wideband STAP; include in channel matching.
9. **Output level**: 35-41 dB gain + pigtail + cable: confirm what the CRPA electronics expects (often 25-30 dB).
10. **Test board**: same RO4350B 0.508 mm / 1.1 mm 50 Ω as the main board B.Cu, with a THRU/LINE calibration
    structure, so the module is measured exactly as it is fed.

## 6. Open questions for BEL CRL
- [OPEN] The three 0.3 mm traces at T03, T07, B11 (and the 2-pin header at the north edge).
- [OPEN] Module height allowed under the back cover / shield cover; clearance to the pigtails.
- [OPEN] Required gain, NF, channel-matching and jammer (J/S) specs of the CRPA processor.
- [OPEN] Coax type for the L_OUT/S_OUT pigtails (pad Ø1.73 + ground pads at ±2.8 mm suggests 0.086" semi-rigid).
- [OPEN] Lot-level availability of TA1442A (Tai-Saw approval sheet dated 2011) and DXP.02.A.

## Sources (web, 2026-11-05)
- Infineon BGA524N6: <https://www.mouser.ee/new/infineon/infineon-bga524n6-amps>
- Mini-Circuits PSA4-5043+: <https://www.minicircuits.com/pdfs/PSA4-5043+.pdf>
- Qorvo QPL9503: <https://www.qorvo.com/products/p/QPL9503>
- Qualcomm B2642 / B2637 / B2627: <https://www.mouser.com/catalog/specsheets/Qualcomm_B2642.pdf>, <https://www.mouser.com/catalog/specsheets/Qualcomm_B2637.pdf>, <https://www.mouser.lt/datasheet/2/842/Qualcomm_B2627-3463400.pdf>
- Qualcomm GNSS SAW tables: <https://shop.richardsonrfpd.com/docs/rfpd/SAW_filters_GNSS_Industrial_IoT.pdf>
- Qualcomm B39162B3913U410: <https://www.digikey.co.uk/en/products/detail/qualcomm-rf-front-end-rffe-filters-/B39162B3913U410/3915487>
- Qorvo 856611: <https://qorvo.com/products/p/856611>, <https://rfmw.com/products/detail/856611-qorvo/592892/>
- Akoustis SAW list: <https://akoustis.com/saw-filters/>
- Fujicrystal FSF-3030: <https://www.fujicrystal.com/product_details/83.html>
- Abracon AFII-SW-0065 / AFII-SW-0095-Q: <https://abracon.com/datasheets/AFII-SW-0065.pdf>, <https://abracon.com/datasheets/AFII-SW-0095-Q.pdf>
- NavIC S band 2483.5-2500 MHz: <https://gssc.esa.int/navipedia/index.php/IRNSS_Signal_Plan>
