# CRL-TRK-2W-L1 rev A0: DRC / ERC

KiCad 9.0.9 `kicad-cli`, run on `01_kicad/tracker_lite.kicad_pcb` / `tracker_lite.kicad_sch` (2026-10-20).

| Check | Result |
|---|---|
| ERC (all severities) | **0 violations** |
| DRC errors | **0** |
| DRC unconnected items | **0** |
| Schematic ↔ PCB parity | **0 issues** |
| DRC warnings | 6, all silkscreen: board text on B.Silk overlaps two test-pad circles; U7 / C20 silk outlines over copper or each other. Cosmetic; the fab clips silk at pads. |

**Board:** 60 x 45 mm, 2 layers, 109 footprints (85 assembled, all top side; 18 test pads on the bottom), 353 vias (0.6 / 0.3 mm),
~1.05 m of track on F.Cu and ~0.85 m on B.Cu.

**Rules (JLC standard 2-layer):** 0.127 mm minimum track and space, 0.3 mm minimum drill, 0.3 mm copper-to-edge, 0.25 mm hole-to-hole.
Net classes: Default 0.2 / 0.15, Power 0.4 / 0.2, HV 0.35 / 0.25, RF50 1.2 / 0.2.

**DRC clean is not the same as fab-ready.** The EC200U land pattern is a reconstruction (`VERIFY_LIST.md` #1). The
bottom GND plane is cut into many pieces by the signal jumpers. They are stitched together with vias, but the plane is not
continuous under the modem. See `05_renders/CRL-TRK-2W-L1_copper.png`.
