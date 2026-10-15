# RF Enclosure Design Notes

## 1. Connector interface (from the H+S STEP)
| Feature | Value | Consequence in the housing |
|---|---|---|
| Flange | 12.7 × 12.7 × 1.59 mm, 4 × Ø2.6 on 8.64 mm square | 4 × M2.5 tapped 4 deep per port; connectors on one wall ≥ 14.7 mm apart |
| Rear spigot | Ø4.16, 5.09 mm from the flange face | wall = 5.0 mm, bore Ø4.25 H8 |
| Pin | Ø1.26, 2.92 mm beyond the spigot | 2.82 mm lies on the trace; pin axis = PCB copper top + 0.63 mm |
| Flange vs box | flange ±6.35 about the pin axis | floor raised so the flange clears the bottom by 0.5 mm |

## 2. Rules applied (and checked in every `*_design_report.md`)
- **Floor:** floor = max(3, 6.85 − t_pcb − 0.035 − 0.63). That gives 5.42 (A), 4.66 (B) and 5.68 mm (C).
- **Air above the PCB, 8.2 mm.** It does two jobs:
  - It keeps the lid seat 1.8 mm above the upper flange threads.
  - It lets a lid screw sit right above each port, with its tap 0.8 mm clear of the spigot bore.
- **Lid screw pitch:** λ/4 at f_max, clamped to 7–15 mm. Lid screws are not placed where their tap would cut a flange thread.
  - **A (6 GHz):** 18 screws, largest gap 12.6 mm, which meets λ/4.
  - **B (12 GHz) and C (10.6 GHz):** 28 and 27 screws, largest gaps 10.2 and 13.1 mm, which exceed λ/4. A **conductive elastomer gasket** on the lid seat is recommended. The report flags it as WARN.
- **RF lip** 1.2 × 1.5 mm with a 0.05 mm side clearance. It forms a labyrinth with the cavity wall.
- **Absorber recess** 1 mm deep on the lid underside. The lowest cavity modes fall inside every band:
  - A: 4.6 GHz
  - B: 5.2 GHz
  - C: 4.4 GHz

  Without absorber (or a channelised lid), expect spikes in S21 and isolation at those frequencies.
- **PCB grounding:**
  - The bottom copper is pressed onto the floor by M2 screws at the corners.
  - Two more screws sit 3 mm from the edge and ±4 mm beside each launch, giving a short ground return at the transition.
  - The PCB needs solid ground pads, with stitching vias, around these holes. `04_pcb_interface/*.dxf` has the positions.
- **Fasteners:**
  - ISO 4762 M2.5 × 5 for the connector flanges.
  - ISO 7380 M2.5 × 8 button heads for the lid. A 5 mm wall is too narrow for an M2.5 counterbore.
  - ISO 4762 M2 × 4 for the PCB.
- **Material / finish:** Al 6061-T6 with conductive chromate conversion (MIL-DTL-5541 Class 3), or Ni plating. Keep the lid seat and lip free of paint or anodise: they are the RF contact surfaces.

## 3. What I added beyond the request
1. **Lid-screw spacing tied to wavelength**, with a gasket recommendation where the spacing alone isn't enough (B, C).
2. **Cavity resonance check** and an **absorber recess**.
3. **Launch ground screws** and a **PCB interface DXF** for the board designer.
4. **Engraved port labels** on the walls, plus a P/N, revision, S/N field and band on the lid.
5. **Engraving artwork DXFs** for CAM, from the exact glyph outlines.
6. **Bottom M3 mounting holes** for a fixture or heat sink.
7. **Drawings** with notes for material, finish, tolerances (ISO 2768-mK), threads, surface finish of the RF contact faces, coaxiality of bores and tapped patterns, and a BOM.
8. **Exploded assembly** for assembly instructions.

## 4. What to supply / confirm
1. **Latest board files** (outline L × W × t, substrate, port positions, frequency band) for A, B and C. The chat link could not be opened from this environment, so every board value is a placeholder.
2. **The BEL logo** as an outlined SVG (`logo/BEL_logo.svg`).
3. **Whether "UWB model" is a 2-port or 3-port circuit**, and whether it is an antenna. An antenna must not go in a closed metal box; it would need a radome or an open aperture instead.
4. **For the stripline board (B):** the via-fence and through-ground layout. The housing grounds only the bottom copper.
5. **Torques and whether thread-locker or helicoils are wanted.** The lid thread engages 4.0 mm (1.6 d) in aluminium.

## 5. Modelling notes
- The models are built with SolidCraft (`solidcraft-cli`) from command scripts.
- Engraving uses polyline glyph outlines rather than font curves. SolidCraft's booleans proved reliable on polylines, while font-curve text failed against the cylindrical holes.
- Threads are tap-drill holes. Thread callouts are on the drawings and in the reports.
