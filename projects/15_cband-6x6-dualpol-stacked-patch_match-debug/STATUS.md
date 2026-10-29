# Status: 15_cband-6x6-dualpol-stacked-patch_match-debug

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** In progress. User-supplied C-band (4-7 GHz) 6x6 dual-pol stacked-patch array: gain OK, VSWR never below 3:1. openEMS element model done; full-array and element-variant runs in progress.

## Done
- Inputs decoded (`01_input/`): F.Cu parasitics, In2.Cu driven patches + two 36-way corporate feeds, B.Cu ground, stack-up
- Topology: port 1 feeds top/bottom edges (V-pol), port 2 left/right edges (H-pol); line widths 0.73 / 1.38 / 2.48 mm = 100 / 70.7 / 50 ohm on RT5880 0.8 mm
- Single-element openEMS (`02_openems/sim_element.py`): best S11 -10.8 dB at 5.84 GHz, VSWR<3 only ~5.35-6.26 GHz; realised gain 5.8-9.3 dBi
- Matching study (`match_study.py`): no line/stub/transformer network reaches VSWR<3 over 4-7 GHz -> radiator bandwidth is the limit
- Stack-up PDF error found: the 4 mm air layer is listed as er 4.5 / tand 0.02

## Open items
- Full-array runs (`sim_array.py --port 1/2`)
- Element variants: no parasitic, gap er 4.5, parasitic x1.15/1.25/1.35
- Write-up with fix recommendations

## Resume here
`cd 02_openems && source /opt/openEMS/venv/bin/activate && python sim_element.py` (needs `bash tools/install_openems.sh` + `pip install ezdxf shapely` in the venv), then `python plot_results.py`.
