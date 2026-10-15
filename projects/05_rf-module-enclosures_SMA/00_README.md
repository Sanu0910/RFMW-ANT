# RF Module Enclosures: Power Divider (MSL), MSL→Stripline Transition, UWB Power Divider
Three machined aluminium housings, each a **base with an RF cavity and a screwed lid with an RF lip**, for:

| Key | Module | Ports | Board (ASSUMED, see below) | Outside (mm) |
|---|---|---|---|---|
| `A_PD_MSL` | 2-way power divider, microstrip only | 3 | 50 × 40 × 0.762 RO4350B | 60.2 × 50.2 × 18.4 |
| `B_MSL_SL` | Microstrip-to-stripline transition (back-to-back) | 2 | 60 × 30 × 1.524 (2 × RO4350B) | 70.2 × 40.2 × 18.4 |
| `C_UWB` | UWB power divider 3.1–10.6 GHz | 3 | 50 × 45 × 0.508 RO4003C | 60.2 × 55.2 × 18.4 |

**Connector:** HUBER+SUHNER **23_SMA-50-0-272/133_N** (item 23030310), SMA jack, 4-hole 12.7 mm square flange, 18 GHz. The geometry is measured from the vendor STEP in `00_vendor/`, and that STEP is placed in every assembly.

**Logo:** the lid engraves "BEL" as text until the outlined logo is supplied. To use the logo, drop `logo/BEL_logo.svg` in and rebuild (see `logo/README.md`).

## What is in each box
- **Base**
  - Cavity pocket: board + 0.1 mm per side, corner radius R1.
  - 5 mm walls. 5 mm is the connector's spigot length, so the Ø1.26 pin lands 2.8 mm onto the trace.
  - Floor raised so the connector axis sits exactly on the trace and the flange stays above the bottom face.
  - Connector bores Ø4.25 with 4 × M2.5 tapped holes per port.
  - Lid: M2.5 tapped holes in the walls, one directly above every port.
  - PCB hold-down: M2 tapped holes in the floor. One at each corner, plus two flanking every launch to ground it.
  - Mounting: 4 × M3 tapped holes in the bottom.
  - Port labels engraved on the outside walls.
- **Lid**
  - 4 mm thick, with a 1.2 × 1.5 mm RF lip (tongue) into the cavity.
  - 1 mm absorber recess on the underside.
  - Clearance holes for ISO 7380 M2.5 button-head screws.
  - Engraved top: logo, title, P/N + REV, S/N + band. 0.3 mm deep.
- **Assembly STEP:** base, lid, PCB dummy with 50 Ω launch stubs, the H+S connectors, and every screw (ISO 4762 / ISO 7380). Also an **exploded** version.

## Folders
| Folder | Content |
|---|---|
| `01_step/<key>/` | `*_BASE.step`, `*_LID.step` (go to the machine shop), `*_ASSY.step`, `*_ASSY_EXPLODED.step`, renders, BOM CSV, SolidCraft scripts |
| `03_drawings/` | A3 drawing per box (PDF/PNG): base top view, connector-wall view, section A-A, lid top, notes, BOM, title block. Also `*_LID_ENGRAVING.dxf` and `*_WALL_LABELS.dxf` (engraving artwork for CAM). |
| `04_pcb_interface/` | DXF for the PCB designer: board outline, M2 hole positions and ground pads, port centre lines, cavity |
| `05_docs/` | `DESIGN_NOTES.md` (rules, what was added, what to supply) and one `*_design_report.md` per box (all checks, cavity resonances, part volumes and masses, files) |
| `02_python/` | `encl_config.py` (**the only file to edit**), `encl_geom.py` (geometry and checks), `build_enclosures.py` (STEP via SolidCraft), `make_drawings.py`, `engraving_dxf.py` |

## Rebuild
```bash
# solidcraft-cli on PATH (see docs/CONVENTIONS.md), plus pip install ezdxf shapely matplotlib pillow
cd 02_python
python build_enclosures.py        # all three (or: python build_enclosures.py C_UWB)
python make_drawings.py
```

## Needs your input (the shared chat could not be read here)
The board sizes, thicknesses, port positions and frequency bands in `encl_config.py` are **placeholders**. Send the latest layout of each board (Gerber, DXF outline, or just L × W × t plus the port positions) and the boxes regenerate in about 5 minutes.
