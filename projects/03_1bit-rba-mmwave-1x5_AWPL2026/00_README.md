# Compact 1-Bit Reconfigurable 1×5 mm-Wave Array: HFSS + MATLAB + Python Pack
Rebuild of Jiao, Wang & Xu, IEEE AWPL 25(6), Jun 2026. RCSPA element, PIN-diode 0/180° switching, 1×5 array at D = 4.5 mm, fixed-phase preloading, 25–29 GHz.

**Read first: `05_docs/DESIGN_GUIDE.pdf`.** It covers terminology, a table checking the paper's claims, geometry assumptions, component values, HFSS steps and plots to check, and the design steps the paper leaves out.

| Folder | What |
|---|---|
| `01_dxf/A_element_alone` | Single element (10 × 10 mm), 1 port |
| `01_dxf/B_array_without_divider` | 1×5 array, 5 ports (paper Fig. 5) |
| `01_dxf/C_array_with_divider` | 1×5 array with a 1:5 divider that builds in the fixed preload (Fig. 6), plus the divider design table |
| `01_dxf/D_split_boards_for_fab` | Antenna board (M1/M2/pins) and feed board (M3/M4/divider), as the paper assembles them |
| `02_python` | `rba_array.py` (beam table, element-width study, squint, Monte Carlo, own PSO), `rbageom.py` + `build_rba.py` (regenerate every DXF) |
| `03_matlab` | `rba_demo` and its functions; output identical to Python (checked in Octave 8.4) |
| `04_hfss` | `hfss_rba_build.py`: PyAEDT build of the element, the 5-port array and the array with divider. Each diode has R/L/C variables so you set beam codes by changing variables. |

**DXF layers** (units mm, x = scan axis):

| Layer | Contents |
|---|---|
| M1 / M2 | patch / coupled shorted strip |
| M3 / M3_SLOT | ground / slots to subtract |
| M4 | feed, switch loop, diodes, bias |
| VIA | pins M2–M3 and DC-return vias M3–M4 |
| NPTH | screw holes |
| PORT | port reference lines |
| SILK_M1 / SILK_M4 | silkscreen |
| ASSY_M4 | assembly drawing |
| FAB | fabrication notes |
