# Status: 15_cband-6x6-dualpol-stacked-patch_match-debug

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Report delivered: `04_docs/CBand_6x6_Array_S11_Analysis_Report.pdf`. Root cause is the element bandwidth (edge-fed stacked patch, one merged resonance, ~16 %). The full-array openEMS run is not finished.

## Done
- Inputs decoded (`01_input/`): F.Cu parasitics, In2.Cu driven patches + two 36-way corporate feeds, B.Cu ground, stack-up
- Topology: port 1 feeds top/bottom edges (V-pol), port 2 left/right edges (H-pol); line widths 0.73 / 1.38 / 2.48 mm = 100 / 70.7 / 50 ohm on RT5880 0.8 mm
- Single-element openEMS (`02_openems/sim_element.py`): best S11 -10.8 dB at 5.84 GHz, VSWR<3 only ~5.35-6.26 GHz; realised gain 5.8-9.3 dBi
- Matching study (`match_study.py`): no line/stub/transformer network reaches VSWR<3 over 4-7 GHz -> radiator bandwidth is the limit
- Variants: without the parasitic there is no match anywhere; a larger parasitic (x1.15/1.25/1.35) moves the window down and narrows it
- Stack-up used: 4 mm air gap, er 1.0 (as built, per the user)
- PDF report (`02_openems/build_report.py`), 9 pages

## Open items
- Full-array runs (`sim_array.py --port 1/2`): about 3 h per port on 4 cores. Two attempts were lost (disk full from time-domain NF2FF dumps, now FD-only; then a worker restart)
- A redesigned wideband element (aperture-coupled or L-probe stacked patch) is not started

## Resume here
`cd 02_openems && source /opt/openEMS/venv/bin/activate && python sim_element.py` (needs `bash tools/install_openems.sh` + `pip install ezdxf shapely` in the venv), then `python plot_results.py`.
