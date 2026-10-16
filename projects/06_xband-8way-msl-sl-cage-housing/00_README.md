# X-Band 8-Way Stripline Power Divider (MSL→SL launches): Cage Housing
Machined aluminium **cage box** for the CRL BEL Antenna / RFM Lab X-band 8-way divider. The board is `XBand_8Way_MSL_to_SL_Transition`: 52.27 × 132.78 mm, 3-stage stripline divider with 21 isolation resistors, microstrip launches, 1 input and 8 outputs.

**Lid engraving:** **CRL BEL** only, 18 mm letters along the lid. Small port numbers IN and 1–8 sit beside the connectors; set `FEATURES["port_labels"] = False` to drop them. The west wall carries "RF IN" and "GND".

## Concept
- **Base**
  - Pocket for the board (+0.1 mm per side).
  - 5 mm walls, so the connector spigot reaches the board edge.
  - 9 × HUBER+SUHNER 23_SMA-50-0-272/133_N: IN on the west wall, 1–8 on the east wall, at the board's own launch positions.
  - The floor height puts the Ø1.26 pin on the 1.686 mm MSL launch.
  - The board is screwed to the floor with 4 × M3 through its own Ø3.2 holes.
- **Lid = cage**
  - Under a 4 mm plate sits an 8.0 mm cage block, with a grid of 2 mm ribs on a 13 mm pitch.
  - The ribs stand 0.2 mm above the PCB top ground. A 0.25 mm conductive elastomer sheet closes that gap.
  - Each MSL launch, each resistor group and each M3 screw head gets its own pocket, ringed by rib.
  - **52 cells, lowest cell resonance 18.5 GHz.** Without the cage, the open cavity has modes from 3.1 GHz up, with 19 TE-type modes inside 8–12 GHz.
- **Screws:** 50 × M2.5 ISO 7380 button heads on the lid, one directly above every connector. 4 × M3 tapped holes in the bottom for mounting.
- **Lid location:** 2 × Ø2 h6 × 8 dowels (ISO 8734) pressed into the N/S walls. The lid has an H7 hole and an H7 slot. The dowels keep the cage pockets aligned over the resistors and launches.
- **Lid removal:** 2 × M3 jacking holes through the lid, pushing on the wall top, because the lid is held by the elastomer gasket. Never pry it.
- **Earth point:** M3 × 4 tapped hole on the west wall, engraved GND.
- **Finish details:** lid top edge 0.6 × 45°, base bottom edge 0.5 × 45°, vertical edges R2.

## Files
| Folder | Content |
|---|---|
| `01_step/` | `CRL-XB-PD8-01_BASE.step`, `_LID.step` (with cage), **`_BOX_ONLY.step`** (base + lid + dowels + lid screws, nothing else), `_ASSY.step` (adds board, 21 resistors, 9 connectors, all screws), `_ASSY_EXPLODED.step`, renders |
| `03_drawings/` | `CRL-XB-PD8-01_DRAWING.pdf/.png` (A3: base top, cage from below, lid engraving, east-wall view, section, notes, title block), `*_cage_from_below.png` |
| `05_docs/design_report.md` | All checks, cage-cell resonances, masses |
| `02_python/` | `cage_config.py` (edit: thickness, cage pitch/rib/gap, text), `cage_build.py`, `make_cage_drawing.py`. They reuse `projects/05_rf-module-enclosures_SMA/02_python`. |
| `00_input/` | The customer DXF package. **Not in git** (kept local). Copy `XBand_8Way_Stripline_DXF_Package/` here to rebuild. |

## Rebuild
```bash
cd 02_python && python cage_build.py && python make_cage_drawing.py    # solidcraft-cli on PATH, ~15 min
```

## Open points
1. **Board thickness:** set to 1.524 mm (2 × 0.762 RO4350B, inferred from the 1.686 mm 50 Ω MSL) **[ASSUMED]**. Send the stack-up; the floor and cage height follow it.
2. **Output flange spacing:** outputs 2-3, 4-5 and 6-7 are 14.5 mm apart, which leaves 1.8 mm between the 12.7 mm flanges. That's tight but it fits.
   - Assemble the flanges in order.
   - The alternative is a 2-hole or end-launch connector.
3. **Seam:** between the output connectors only the screws above each port are possible (gap 14.5 mm, more than λ/4 at 12 GHz). Use a conductive gasket on the lid seat. The cage's perimeter rib is a second barrier.
4. **Resistors:** modelled as 0603 parts, 0.45 mm high. They have 7.8 mm of cell height above them.
