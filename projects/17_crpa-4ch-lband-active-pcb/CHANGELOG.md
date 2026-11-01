# Changelog: 17_crpa-4ch-lband-active-pcb

Newest first.

## 2026-11-01 - Rev A layout and fab package
- New project on branch `proj17-crpa-4ch-lband-pcb`: 4-channel L-band CRPA active antenna PCB from the customer
  board `Gerber_4CH_GNSS.zip` (antenna spacing and board radius kept) and the project 16 chain, plus an
  RLM-63-2W+ limiter per band per channel.
- Substrate changed from 2-layer RO4350B 0.76 mm to 4-layer FR-4 1.6 mm (L1 GND / L2 +5V / L3 GND / L4 RF).
- Single +5 V bias point (J5) with PTC, reverse-polarity P-FET and TVS; no DC on RF outputs.
- Outputs: kicad-cli DRC 0/0, Gerbers + drill + CPL + IPC-D-356, BOM, report, schematics, renders.
