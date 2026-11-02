# Changelog: 17_crpa-4ch-lband-active-pcb

Newest first.

## 2026-11-02 - Rev D: CLM-83-2W+ limiter, 1.5SMC6.8A input TVS (485c727)
- Limiter RLM-63-2W+ (TT1224) -> Mini-Circuits CLM-83-2W+ (customer choice; data sheet Input/CLM-83-2W+.pdf).
  New footprint MiniCircuits_DL1721 from the DL1721 table + PL-377: 8 pads 0.46 x 0.76 mm at 0.66 pitch, GND paddle
  1.04 x 1.91 + 0.46 x 3.00 tabs (pad 9). IN 2 / OUT 7 face each other, so the limiter now sits in-line (the 5 mm
  diagonal jog is gone); GND: 3 plugged paddle vias, a via off each tab, pins 3-4 / 5-6 tied + 1 via, pins 1 / 8 own via.
  The chain runs 1.8 mm straight past OUT before turning (clears the GND vias). MiniCircuits_TT1224 removed.
- Input TVS SMAJ5.0A -> 1.5SMC6.8A (customer asked for "1.5SMC600A"; a 600 V part would not clamp a 5 V rail, the
  6.8 V breakdown / 5.8 V standoff version was confirmed). Footprint D_SMA -> D_SMC; C1/C2/+5V star vias moved
  1.4 mm down to clear the larger body. PTC F1 unchanged.
- Budget: limiter IL 0.14-0.17 dB (data sheet, was 0.11-0.15), pre-LNA line L1 21.7 mm (was 20.0), L2/L5 15.9 mm
  (was 15.3): NF L1 1.09 / L5 0.86 / L2 0.89 dB (+0.03 dB), gain -0.04 dB.
- DRC 0 violations / 0 unconnected; Gerbers, drill, CPL, IPC-D-356, BOM, schematics, report regenerated.

## 2026-11-02 - Rev C: star bias, shield cans, GPDF6010.A footprint from its data sheet (b33eeda)
- Bias changed from a full +5V plane to a star: In1.Cu is now GND except 4 separate 0.8 mm trunks from the star
  point after Q1, one per channel, each into its own ferrite FB{n} (BLM18KG601SN1D) + 10 uF, then 0.4 mm
  branches to that channel's 4 LNA chokes. Routed by a grid router in build_pcb.py (avoids every through-hole);
  CH1's branches replayed on CH2-4. Better channel-to-channel isolation, no plane cavity, third RF ground.
- Shield can per channel (as on the customer product photo): octagonal 1.0 mm exposed GND frame land with GND
  vias every 2 mm, 2.6 mm RF exit notch, SMA keep-out step. Outline CSV + drawing for the can maker.
- Antenna module identified as Taoglas GPDF6010.A; data sheet SPE-21-8-111-G applied: centre screw pad is now
  GND (DS: required for grounding), locating holes D1.8 (was 3.2 [ASSUMED]), feed clearance D3.5 (was D3.2).
- Common-port chain (4.3 nH, 1.5 pF, 100 pF) re-routed east so the can clears the SMA body.
- DRC 0 violations / 0 unconnected; BOM +4 ferrites.

## 2026-11-01 - Rev B: third SAW per band before the diplexer (cceb0af)
- Customer request: one more filter before the DXP. Each band gets a 3rd SAW of the same type (B7504 on L1,
  B8889 on L2/L5), with a 100 pF between SAW 2 and SAW 3 so each B8889 port keeps its own 6.8 nH shunt.
  +8 SAWs, +8 x 100 pF, +4 x 6.8 nH on the board. Gain -0.9 dB (L1/L5) / -1.5 dB (L2), NF unchanged.
- DXP moved 1.5 mm outward to make room; DRC still 0 violations / 0 unconnected.
- Bias question answered in the report (new section 6a): +5 V is a full plane on In1.Cu, not tracks; one island,
  57 pads, 28 vias. New image `Images/bias_plane_In1Cu.png`; layer PDF now multipage with title blocks.

## 2026-11-01 - Rev A layout and fab package (130ba32)
- New project on branch `proj17-crpa-4ch-lband-pcb`: 4-channel L-band CRPA active antenna PCB from the customer
  board `Gerber_4CH_GNSS.zip` (antenna spacing and board radius kept) and the project 16 chain, plus an
  RLM-63-2W+ limiter per band per channel.
- Substrate changed from 2-layer RO4350B 0.76 mm to 4-layer FR-4 1.6 mm (L1 GND / L2 +5V / L3 GND / L4 RF).
- Single +5 V bias point (J5) with PTC, reverse-polarity P-FET and TVS; no DC on RF outputs.
- Outputs: kicad-cli DRC 0/0, Gerbers + drill + CPL + IPC-D-356, BOM, report, schematics, renders.
