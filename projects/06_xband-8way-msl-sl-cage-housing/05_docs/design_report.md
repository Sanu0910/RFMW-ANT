# X-band 8-way MSL-SL stripline divider - cage housing (CRL-XB-PD8-01)

| Item | Value |
|---|---|
| Board (from the customer DXF) | 52.265 x 132.779 mm, 2 mm corner chamfers, 4 x d3.2 holes; thickness 1.524 mm **[ASSUMED]** |
| Ports | IN on the west wall; outputs 1-8 on the east wall at y = +54.39, +38.07, +23.57, +7.25, -7.25, -23.57, -38.07, -54.39 mm (board centre) |
| Launch | top-layer microstrip 1.686 mm wide, 0.3 mm set back from the board edge |
| Outside | 62.47 x 142.98 x 18.42 mm (base 14.42 + lid plate 4.0) |
| Cavity | 52.466 x 132.979 mm, floor 4.66, connector axis 6.850 above the bottom |
| Cage | block 8.0 mm tall under the lid, face 0.20 above the PCB (0.25 mm conductive elastomer sheet recommended); ribs 2.0 mm on a 13.0 mm grid; 52 cells |
| Lid screws | 50 x M2.5 x 8 ISO 7380; largest gap 14.50 mm |
| Board screws | 4 x M3 x 6 ISO 4762 through the board's own holes into the floor (pockets in the cage clear the heads) |
| Connectors | 9 x HUBER+SUHNER 23_SMA-50-0-272/133_N, 36 x M2.5 x 5 ISO 4762 |
| Lid location | 2 x d2 h6 dowels ISO 8734 2x8 pressed in the N/S walls at [(-18.733, 68.989), (18.733, -68.989)]; lid: d2 H7 hole + d2 H7 x 1 slot |
| Lid removal | 2 x M3 jacking holes through the lid at [(0.0, 68.989), (0.0, -68.989)] (push on the wall top) |
| Earth point | M3 tapped 4 deep, west wall, y = +40 mm, at the connector-axis height |
| Edges | lid top 0.6 x 45 deg, base bottom 0.5 x 45 deg, vertical edges R2 |

## Checks

| Check | Value (mm) | Rule | Result |
|---|---|---|---|
| flange bottom above box bottom | 0.50 | >= 0.50 | OK |
| flange top below lid top | 5.22 | >= 0 | OK |
| upper flange thread below lid seat | 2.00 | >= 0.5 | OK |
| lower flange thread above box bottom | 1.28 | >= 0.5 | OK |
| spigot length vs wall | 0.09 | 0 .. 0.2 (spigot reaches the cavity) | OK |
| pin length lying on the trace | 2.91 | >= 2.0 | OK |
| pin axis above trace (pin resting on copper) | 0.63 | = pin radius 0.63 | OK |
| floor thickness | 4.66 | >= 3.0 | OK |
| PCB screw thread in floor | 1.16 | >= 0.8 (blind) | OK |
| lid screw clear of the lid edge | 1.05 | >= 0.8 | OK |
| lid under absorber recess | 2.70 | >= 2.0 | OK |
| lid screw thread engagement | 4.00 | >= 1.4 d = 3.5 (light load; helicoil optional) | OK |
| lid screw hole bottom vs tap depth | 0.60 | >= 0.5 | OK |
| lid tap above the spigot bore | 0.84 | >= 0.8 | OK |
| largest lid-screw gap | 14.50 | <= lambda/4 at f_max = 6.2 (else conductive gasket) | **WARN** |
| flange gap 1-2 | 3.62 | >= 2 (spanner/fingers) | OK |
| flange gap 1-3 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 1-4 | 34.44 | >= 2 (spanner/fingers) | OK |
| flange gap 1-5 | 48.94 | >= 2 (spanner/fingers) | OK |
| flange gap 1-6 | 65.26 | >= 2 (spanner/fingers) | OK |
| flange gap 1-7 | 79.76 | >= 2 (spanner/fingers) | OK |
| flange gap 1-8 | 96.08 | >= 2 (spanner/fingers) | OK |
| flange gap 2-3 | 1.80 | >= 2 (spanner/fingers) | **WARN** |
| flange gap 2-4 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 2-5 | 32.62 | >= 2 (spanner/fingers) | OK |
| flange gap 2-6 | 48.94 | >= 2 (spanner/fingers) | OK |
| flange gap 2-7 | 63.44 | >= 2 (spanner/fingers) | OK |
| flange gap 2-8 | 79.76 | >= 2 (spanner/fingers) | OK |
| flange gap 3-4 | 3.62 | >= 2 (spanner/fingers) | OK |
| flange gap 3-5 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 3-6 | 34.44 | >= 2 (spanner/fingers) | OK |
| flange gap 3-7 | 48.94 | >= 2 (spanner/fingers) | OK |
| flange gap 3-8 | 65.26 | >= 2 (spanner/fingers) | OK |
| flange gap 4-5 | 1.80 | >= 2 (spanner/fingers) | **WARN** |
| flange gap 4-6 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 4-7 | 32.62 | >= 2 (spanner/fingers) | OK |
| flange gap 4-8 | 48.94 | >= 2 (spanner/fingers) | OK |
| flange gap 5-6 | 3.62 | >= 2 (spanner/fingers) | OK |
| flange gap 5-7 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 5-8 | 34.44 | >= 2 (spanner/fingers) | OK |
| flange gap 6-7 | 1.80 | >= 2 (spanner/fingers) | **WARN** |
| flange gap 6-8 | 18.12 | >= 2 (spanner/fingers) | OK |
| flange gap 7-8 | 3.62 | >= 2 (spanner/fingers) | OK |
| flange inside box outline (IN) | 65.14 | >= 0 | OK |
| flange inside box outline (1) | 10.75 | >= 0 | OK |
| flange inside box outline (2) | 27.07 | >= 0 | OK |
| flange inside box outline (3) | 41.57 | >= 0 | OK |
| flange inside box outline (4) | 57.89 | >= 0 | OK |
| flange inside box outline (5) | 57.89 | >= 0 | OK |
| flange inside box outline (6) | 41.57 | >= 0 | OK |
| flange inside box outline (7) | 27.07 | >= 0 | OK |
| flange inside box outline (8) | 10.75 | >= 0 | OK |
| lowest cage-cell resonance (largest cell 11.1 x 11.9) | 18.51 GHz | > 1.3 x f_max = 15.6 GHz | OK |
| (for comparison) open cavity without the cage, TE110 | 3.07 GHz | - | in band: the cage is what removes it |

## Cage cells (largest first)

| Cell (a x b mm) | TE110 (GHz) |
|---|---|
| 11.1 x 11.9 | 18.5 |
| 11.1 x 11.9 | 18.5 |
| 8.9 x 16.1 | 19.2 |
| 8.9 x 16.1 | 19.2 |
| 11.1 x 10.9 | 19.3 |
| 11.1 x 10.9 | 19.3 |
| 11.1 x 10.9 | 19.3 |
| 11.1 x 10.9 | 19.3 |
| 11.1 x 10.9 | 19.3 |
| 11.1 x 10.9 | 19.3 |

Machined mass (Al): base 158 g, lid 148 g.
