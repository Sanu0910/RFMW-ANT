# Reactive Beamforming Metasurface: HFSS + MATLAB Design Pack
Rebuild of Almunif, Alsolamy & Grbic, "Network-Based Design of Reactive Beamforming Metasurfaces", IEEE TAP 73(8), Aug 2025.
11×11 aperture-coupled cells, 5.7 mm (λ0/5) at 10 GHz, RO4003C 0.813 + 0.203 mm.

**Read first: `06_docs/DESIGN_GUIDE.pdf`.** It covers terminology, the corrected geometry, ports and feeds, HFSS steps, the MATLAB equation map, items the paper glosses over, and the prototype checklist.

## What's inside
| Folder | Highlights |
|---|---|
| `01_dxf_base/` | Fig. 3 unit cell (all layers and per layer), 3 lumped-port 11×11 arrays (Design I/II centre feed, Design III 2-feed MIMO, Design IV/V reflective), meander library for Zin extraction, X→stub table |
| `02_reactance_data/` | Per-cell reactances digitised from Figs. 4a/6a/7a/8b/9b, with a side-by-side check image |
| `03_dxf_realized/` | **Fig. 11 rebuild** (Design I meanders) and **Fig. 12 rebuild** (Design IV beam splitter), plus Designs II/III/V, per-cell tables |
| `04_matlab/` | Eq. 1–25 pipeline with analytic gradients; toy-array demo; real-HFSS template; self-tests |
| `05_python_tools/` | Geometry library, DXF builder, DRC, digitiser, PyAEDT HFSS automation |
| `06_docs/` | Designer's guide (PDF / HTML / MD) |

## Quick start
1. **HFSS:** import `01_dxf_base/array11x11_designI_II_centrefed_lumped.dxf`, then follow guide §6. Alternatively run `python 05_python_tools/hfss_build_and_export.py array`.
2. **MATLAB:**
   - Run `mtsf_selftest`, then `mtsf_demo_paper_designs` (no HFSS needed).
   - Then run `mtsf_design_from_hfss` on your exports.
3. **Realise:** `python 05_python_tools/build_dxf.py realise designI_X_optimised.csv my_fig11.dxf --feeds 6,6` builds the meander DXF. Then `python drc_check.py my_fig11.dxf`.
4. **Verify:** put the loads back as lumped RLC (`hfss_build_and_export.py verify designI_loads.csv`), then simulate the meander DXF.

## Conventions
- All dimensions in mm, array centre at the origin.
- Row 1 is at the top (+y) and column 1 at the left; port index m = (row−1)·11 + col.
- Feeds: Design I/II at R6C6; Design III at R6C4 and R6C8.

**DXF layers:**

| Layer | Contents |
|---|---|
| L1_PATCH | patches |
| L2_GND_BOARD | full ground outline |
| L2_GND_SLOT | slots, subtract from the ground |
| L3_STRIP | strips and meanders |
| VIA | via circles |
| PORT_FEED_50ohm | feed port planes |
| PORT_LOAD_jX | load port planes |
| BOARD_OUTLINE | board edge |
| TEXT | cell labels |

## Accuracy and limitations
- The geometry follows the published Fig. 3 and Fig. 10 dimensions. Where the paper is silent, the assumed values are listed in guide §3 and live in one file: `msgeom.py`.
- Reactances were digitised from colour maps: about ±3 Ω, with the extremes of each colourbar possibly clipped. Use them as a starting layout and re-optimise on your geometry.
- Meander lengths come from an analytic open-stub model (Hammerstad, open-end corrected). Replace them with HFSS-extracted Zin (`hfss_build_and_export.py meander`, then `--table`) before fabrication.
- The MATLAB code was run and checked in GNU Octave 8.4. In MATLAB it uses `fmincon` automatically.
- The PyAEDT script was written against `ansys.aedt.core` but not executed here (no HFSS licence).
