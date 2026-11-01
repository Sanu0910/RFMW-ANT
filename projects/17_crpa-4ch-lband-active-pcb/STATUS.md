# Status: 17_crpa-4ch-lband-active-pcb

_Last updated: 2026-11-01. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Rev A layout complete and DRC-clean (0 violations, 0 unconnected); fab package (Gerbers, drill, BOM,
CPL, IPC-D-356) and design report generated. Not yet ordered. L-band only (NavIC S-band not built, as requested).

## Done
- Customer Gerber decoded (Gerber X2 attributes): outline Ø200 mm, 4 module positions, feed-pin positions and nets,
  land patterns of HC125A / TQP3M9037 / B7504 / B8889 / DXP.02.A (mirrored back to top view)
- RLM-63-2W+ land pattern from its data sheet (TT1224 / PL-258), pin 1 IN / pin 4 OUT diagonal
- 4-layer 1.6 mm FR-4 stack-up, 50 Ω = 0.38 mm on L4 (scikit-rf Hammerstad-Jensen)
- Scripted placement + routing of one channel, rotated 4× about the array centre; single +5 V entry
- GND via fences along all RF lines + 5 mm stitching grid; 4 solid planes
- kicad-cli DRC clean; kicad-happy analyze_pcb / analyze_gerbers run and triaged
- RF budget from the project 16 cascade + limiter IL + routed line lengths; power budget
- Schematics (project 16 style), cross-checked against the PCB part list; BOM CSV/XLSX; report PDF

## Open items
- **Confirm antenna module drills / pin length** (A1, A2 in the report) - drills are [ASSUMED]
- Confirm module outline <= 70 × 70 mm (SMA legs and J5 are in the free cross between modules)
- Cross-check copied land patterns against vendor drawings (A5)
- Pre-LNA band filtering and output gain level remain project 16 design decisions (O1, O2)
- Optional: L3-L4 in RO4350B 0.254 mm (hybrid build) to save ~0.07 dB NF; shorten the 13.6 mm L1 hybrid->limiter line
- No KiCad schematic (.kicad_sch): the netlist is defined in `build_pcb.py`; drawn schematics in `Images/`

## Tools
- KiCad 10.0.3 (Windows, `C:/Program Files/KiCad/10.0`): pcbnew Python + kicad-cli (DRC, Gerber, render)
- Python 3.12 with numpy, matplotlib, scikit-rf, openpyxl, reportlab, Pillow
- kicad-happy skill 2.2.1 analyzers (PCB, Gerber)

## Resume
`bash Scripts/build_all.sh` regenerates the board, DRC, fab files and documents. Edit parameters in
`Scripts/crpa_design.py`; placement/routing in `Scripts/build_pcb.py` (`build_element`, `power_block`).
