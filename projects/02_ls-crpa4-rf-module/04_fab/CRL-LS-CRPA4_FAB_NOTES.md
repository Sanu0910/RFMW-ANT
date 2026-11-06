# CRL-LS-CRPA4 REV A - fabrication and assembly notes

Board: D200.0 mm round, 4 copper layers, 1.6 mm, all SMD parts on the bottom (L4 / B.Cu), 313 placements.
Files: `CRL-LS-CRPA4_Gerbers.zip` (Gerber X2 + Excellon PTH/NPTH + drill map), `CRL-LS-CRPA4_CPL_bottom.csv`, `CRL-LS-CRPA4.d356`, `CRL-LS-CRPA4_BOM.csv/.xlsx`.

## Stack-up (hybrid build: order exactly this)
| Layer | Type | Thickness mm | er | Note |
|---|---|---|---|---|
| F.SilkS | silk | 0.000 |  |  |
| F.Mask | mask | 0.010 | 3.8 | green LPI |
| F.Cu | copper | 0.035 |  | L1: solid GND = antenna ground plane |
| Core1 | core | 0.710 | 4.4 | FR-4 high-Tg core (IT-180A) |
| In1.Cu | copper | 0.035 |  | L2: GND + per-channel +5V star traces |
| PP1 | prepreg | 0.540 | 4.3 | FR-4 prepreg 2x2116 + 1x1080 (bonds FR-4 to RO4350B) |
| In2.Cu | copper | 0.035 |  | L3: solid GND, RF reference for L4 |
| Core2 | core | 0.168 | 3.66 | Rogers RO4350B 0.168 mm (6.6 mil), tan d 0.0037 |
| B.Cu | copper | 0.035 |  | L4: RF lines + all SMD parts, ENIG |
| B.Mask | mask | 0.010 | 3.8 | green LPI |
| B.SilkS | silk | 0.000 |  |  |

## Fabrication requirements
1. IPC-6012 Class 2 (Class 3 if the CRPA is for airborne use), IPC-A-600 Class 2; UL 94V-0.
2. Materials: FR-4 high Tg >= 170 C (IT-180A / S1000-2 or equal) + Rogers RO4350B 0.168 mm (6.6 mil) core, 1 oz both sides.
   Hybrid lamination FR-4 prepreg to RO4350B: plasma desmear before plating.
3. **Controlled impedance on L4: 50 ohm +-10 % single-ended, 0.34 mm track over L3 (RO4350B 0.168 mm), 35 um finished Cu,
   with solder mask.** Coupon on the panel; report TDR.
4. Finish ENIG (Ni 3-6 um, Au 0.05-0.10 um); soldermask green LPI both sides; legend white both sides; no mask on the
   exposed shield-frame lands (1.5 mm GND rings on L4) - they carry the back-cover gasket. **Top side (L1): no
   solder mask at all** - the L1 GND plane under the L and S patches is bare ENIG.
5. Vias: 0.30 mm drill / 0.60 mm pad standard. **Vias in pads (0.25 / 0.50 mm in the TQP3M9037, CLM-83-2W+ and SAW ground
   pads) resin-filled and capped, IPC-4761 Type VII.** Min. annular ring 0.125 mm.
6. Min track / space 0.15 / 0.15 mm, min drill 0.25 mm; board edge to copper >= 0.5 mm.
7. Bow and twist <= 0.5 % (D200 thin hybrid: panel with copper balancing, bake before assembly).
8. 100 % electrical test against `CRL-LS-CRPA4.d356`.
9. RoHS / REACH.

## Assembly
1. Bottom side reflow (SAC305, type 4 paste; 0.10-0.12 mm stencil, window reduction 10 % on 0402, 50 % paste on exposed
   pads in a window grid). MSL: B7504 / B8889 MSL3 - bake per J-STD-033 if exposed > 168 h.
   TA1442A (S SAW): peak 260 C per the Tai-Saw profile; ESD sensitive; max DC 3 V on the pads (all S SAWs sit between
   DC-block capacitors). C2327J5003AHF and TA1442A land patterns are the vendor drawings (00_vendor/).
2. THT: 8 SMA (Amphenol 132134), J5 Micro-Fit - selective or hand solder after reflow.
3. Clean (no-clean flux residue must stay off the SAW lids), 100 % AOI, X-ray of the DFN-8 and DL1721 ground pads.
4. Top side: fit the 4 GPDF6010.A L patches and 4 S patches; solder the feed pins from the bottom.
5. Back cover: FIP gasket on the wall tops, cure, then 16 x M3 through cover, board and L patches (0.9 N m [ASSUMED]).
6. Test each module with the test board / per channel: S21 gain and phase at L1, L5, L2, S; NF; record the
   channel-to-channel gain/phase table (calibration data delivered with the unit).

## Open items before release
- S patch CRL-LS-SP01 (BEL CRL in-house): drawing, fixing and measured S11 / AR still to be issued. The S hybrid wiring is RHCP for a patch whose F90 pin sits +90 deg CCW (top view)
  from F0: F0 -> C2327J5003AHF pin 4 (direct), F90 -> pin 6 (coupled), pin 1 out, pin 3 -> 50 ohm. Confirm with the patch drawing.
- GPDF6010.A fixing: customer board D3.6 / D1.35 vs data sheet D1.8 / D1.1.
