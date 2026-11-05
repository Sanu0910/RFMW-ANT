# Changelog: 01_xband-8way-msl-wpd-housing

Newest first.

## 2026-11-05 - Drawings and report refreshed, pushed
- Wall elevations on sheet 1 were mirrored; they now show the view from outside (E wall: north on the right).
- Report mass came from STEP import with no material (default density); now volume x Al 2.70: base 263 g, lid 342 g.
- BOM: gasket listed as 9 die-cut pieces.
- Commits 9910d1c (first build) and 44c0b2a (this refresh), pushed to origin/projects-v2.

## 2026-11-05 - Housing V3 first build
- New project: housing CRL-XB-PD8-03 for the X-band 8-way microstrip Wilkinson board (RO4350B 30 mil), with
  HUBER+SUHNER 23_SMA-50-0-272/133_N connectors.
- PCB V3: 15 x M2 plated holes added (the customer board had none), 33 vias removed.
- Lid cage: channel walls first placed on the pour edge (4.5 mm from the copper) gave channel resonances at 10.6 GHz.
  Moved to 2.5 mm, 5 mm air: lowest mode 15.9 GHz, Z0 shift about 1 ohm (2D FD solve).
- Gasket gap set to 0.35 mm with a 0.5 mm sheet (the board thickness tolerance of +/-0.05 mm needs that range).
- Earth M3 moved into the solid floor zone (at connector height it broke through the 5 mm wall).
- Built: BASE, LID and GASKET STEP files, PCB V3 DXF, drawings, report, BOM. Assembly STEPs not yet built (low memory).
