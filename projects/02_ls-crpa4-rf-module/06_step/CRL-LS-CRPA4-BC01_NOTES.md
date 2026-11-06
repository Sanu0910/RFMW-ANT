# CRL-LS-CRPA4-BC01 - combined L + S back cover (machining notes)

STEP: `CRL-LS-CRPA4-BC01.step` (built by `02_python/covers.py`, SolidCraft 0.26.1). Same frame as
`CRL-LS-CRPA4_PCB.step`: origin = board outline centre, X east / Y north (top view), board bottom (B.Cu) at z = 0.

| Item | Value |
|---|---|
| Material / finish | Al EN AW-6061-T6, chromate conversion MIL-DTL-5541 Type II Class 3 (conductive), all over |
| Envelope | D200.0 x 10.7 mm (z -11.0 .. -0.3); machined mass 464 g (171.7 cm3 x 2.70 g/cm3) |
| General pocket | depth 5.7 below the wall tops (6.0 below the board), inside r 97.0 rim |
| RF walls | 1.2 mm wide on every shield-frame land (4 L octagons + 4 S strips, shared walls), top 0.30 mm below the board |
| Gasket | form-in-place conductive elastomer bead on all wall tops and the rim (Chomerics CHOFORM 5575 or equal [ASSUMED]), 0.8 mm bead, compressed to 0.30 |
| RF tunnels | 2.6 x 1.0 mm (h) under the walls where the 8 RF output lines leave their cavities |
| SMA openings (8) | D6.8 through + D11.5 x 5.0 counterbore from outside (mating plug coupling nut reaches the jack thread) |
| Fixing (16) | D3.4 through + D6.2 x 3.4 counterbore, bosses D8 inside; ISO 4762 M3 through the board into the GPDF6010.A [ASSUMED] |
| DC | D8.2 through for an M8 IP67 panel receptacle [ASSUMED type], harness to J5; J5 pocket 16 x 14 x 10 deep (1.0 floor) |
| Engraving 0.3 deep, outside | BEL logo, CRL-LS-CRPA4-BC01, title, DATE 05-11-2026, S/N field, +5V DC, CH1-4 S labels (mirrored: readable from below) |
| Tolerances | ISO 2768-mK; wall tops flat 0.05 over each cavity; break sharp edges 0.2 |

Cavity resonances (air, rectangular estimate): L octagon ~55 mm across -> TE110 ~3.9 GHz (> L band, > NavIC S);
S strip ~12 x 50 mm -> lowest mode ~13 GHz. The L and S chains do not share a cavity.
