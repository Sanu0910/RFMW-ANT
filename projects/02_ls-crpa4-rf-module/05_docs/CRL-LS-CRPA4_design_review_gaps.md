# CRL-LS-CRPA4 - design review: open gaps (RF design + product engineering)

_Recorded 2026-11-06 at the user's request. Status per item is tracked in `../STATUS.md`._

## Inputs still needed
- S patch **CRL-LS-SP01** (BEL CRL in-house): drawing, feed-pin labelling (F0 / F90 sense), measured S11 and axial ratio on this board
- L patch fixing: board D3.6 / D1.35 (combine_model_2.0) vs GPDF6010.A data sheet D1.8 / D1.1
- Supply: +5 V only, or a 28 V bus (MIL-STD-1275 vehicle / MIL-STD-704 aircraft)
- Platform / environment (ground, vehicle, airborne, naval): sets the MIL-STD-810 / 461 test levels
- CRPA processor interface: required channel gain / phase / group-delay match, gain at the SMA, NF, cable loss to the receiver

## RF / system
- Measured array data: element S11, patterns, mutual coupling (S patches about 1 mm from the L patches), with cover and radome
- Channel match spec (typically +-1 dB / +-5-10 deg over temperature); plan for per-unit calibration tables
- Group delay match: 3 SAWs per chain = large absolute delay and part-to-part spread
- Interference (rf_budget.py): S chain rejects WiFi ch11 4 dB, ch13 / BT 2 dB, LTE B41 2506 0 dB, B7 2535 6 dB;
  L band: Iridium 1616-1626, Inmarsat, LTE, DME/TACAN 960-1215 (inside the wide L2/L5 band)
- Jamming linearity: P1dB / IIP3 per stage, jammer-to-signal headroom, limiter recovery time
- SAW ratings vs gain: an in-band jammer above -40 dBm (L2/L5, B8889 5 dBm) / -26 dBm (S) / -27 dBm (L1) at the antenna
  overdrives the 2nd SAW; chain input P1dB -20...-24 dBm (L), -15 dBm (S) - too low for a CRPA under jamming
- Isolation: L-to-S inside the cover (> 40 dB), channel-to-channel (> 30 dB); cavity resonance (eigenmode) check
- LNA stability in the closed cavities: K / mu > 1 out to 10 GHz with the cover fitted
- System NF and G/T, including the loss ahead of LNA1
- BIT: per-LNA current monitor (24 LNAs) so the processor can flag a dead channel

## Power / thermal / EMC
- Thermal: about 8.4 W in a sealed Al cover; LNA junction temperature at +70 / +85 C ambient
- Power entry: reverse polarity, surge and transient protection for the platform bus
- Regulator / DC-DC spurs inside the GNSS bands; feed-through filtering at the DC connector
- MIL-STD-461G: CE102, CS101, RE102, RS103

## Mechanical / environment
- Radome on the antenna side (detunes the patches: include it in the simulation)
- IP67 / MIL-STD-810: humidity, salt fog, vibration, shock, thermal cycling; O-ring cover-to-radome, breather vent
- Conformal coating kept off the RF lines (or tuned for); screw torque, thread locking, PCB support, SMA strain relief

## Product / manufacturing
- Test fixture + acceptance test procedure (ATP) with pass / fail limits, production calibration, phase-matched cable set
- Interface control document (ICD), specification sheet, schematic PDF, assembly drawing, fab drawing
- Dual source for RO4350B; obsolescence / second source for TA1442A, Xinger C2327J5003AHF, B8889
- Export-control check and indigenous-content requirements
- MTBF (MIL-HDBK-217), FMECA, derating report, ESD handling (SAWs are ESD sensitive), traceability label / S/N, revision control
