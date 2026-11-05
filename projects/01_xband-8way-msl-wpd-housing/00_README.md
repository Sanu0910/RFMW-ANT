# 01 - X-band 8-way microstrip Wilkinson divider: machined housing (V3)

Production housing for the customer board `Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady.dxf` (8-12 GHz, 1 input,
8 outputs, RO4350B 0.762 mm / 30 mil, 99.28 x 126.90 mm). Part number **CRL-XB-PD8-03**.

- **Base**: Al 6061-T6 with Alodine (MIL-DTL-5541 Type II Class 3). 109.48 x 137.10 mm outside, 17.22 mm high with the lid.
  It carries 9 x HUBER+SUHNER 23_SMA-50-0-272/133_N connectors; each pin rests on its 50 ohm trace.
- **Lid with channel cage**: a solid block under the lid fills the cavity. Each RF line runs in its own milled channel,
  2.5 mm from the copper with 5 mm of air above. This pushes the lowest box resonance to 15.9 GHz; an empty box would
  resonate from 1.75 GHz. Engraved with the BEL logo, title, P/N, date 05-11-2026, S/N field and port labels.
- **Gasket**: 0.5 mm conductive elastomer between the cage face and the board, in 9 die-cut pieces.
- **PCB V3**: the customer layout plus 15 x M2 plated mounting holes in the ground pour, with 33 vias removed.

## Files
| Folder | Content |
|---|---|
| `00_input/` | Customer board DXF + its generator script, BEL logo |
| `00_vendor/` | H+S connector STEP + data sheet |
| `01_pcb_v3/` | PCB V3 fab DXF (layer `MOUNT_HOLES_PTH`), hole table CSV, preview |
| `02_python/` | `config.py` (edit), `build_all.py` (regenerates everything), `geom.py`, `housing.py`, `pcb_v3.py`, `artwork.py`, `z0_2d.py`, `report.py`, `drawing.py` |
| `03_step/` | `CRL-XB-PD8-03_BASE.step`, `_LID.step`, `_GASKET.step`, renders, `*.solidcraft.json` scripts, `dxf_src/` (channel, engraving, gasket DXFs for CAM) |
| `04_drawings/` | `CRL-XB-PD8-03_DRAWINGS.pdf`, 4 A3 sheets: base, lid, gasket / PCB / assembly, hole table |
| `05_docs/` | Design report (checks, resonances, Z0), BOM, hole table CSV |

## Rebuild
```bash
cd 02_python
../../../.venv/Scripts/python.exe build_all.py              # everything (~30 min; the assembly needs plenty of RAM)
../../../.venv/Scripts/python.exe build_all.py report drawing   # drawings + report only (< 1 min)
```
Needs SolidCraft `solidcraft-cli` (0.26.1 used) and the Python packages ezdxf, shapely, scipy, contourpy and matplotlib.
