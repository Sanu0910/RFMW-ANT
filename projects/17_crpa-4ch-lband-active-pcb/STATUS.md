# Status: 17_crpa-4ch-lband-active-pcb

_Last updated: 2026-11-05. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Rev D (CLM-83-2W+ limiters, 1.5SMC6.8A input TVS; on top of Rev C star bias, shield cans,
GPDF6010.A footprint) layout complete and DRC-clean (0 violations, 0 unconnected); fab package (Gerbers, drill, BOM,
CPL, IPC-D-356) and design report generated. Not yet ordered. L-band only (NavIC S-band not built, as requested).

## Done
- Customer Gerber decoded (Gerber X2 attributes): outline Ø200 mm, 4 module positions, feed-pin positions and nets,
  land patterns of HC125A / TQP3M9037 / B7504 / B8889 / DXP.02.A (mirrored back to top view)
- Limiter land pattern from its data sheet: CLM-83-2W+ DL1721 / PL-377 (Rev D), pin 2 IN / pin 7 OUT in-line, paddle GND
- 4-layer 1.6 mm FR-4 stack-up, 50 Ω = 0.38 mm on L4 (scikit-rf Hammerstad-Jensen)
- Scripted placement + routing of one channel, rotated 4× about the array centre; single +5 V entry
- GND via fences along all RF lines + 5 mm stitching grid; 4 solid planes
- kicad-cli DRC clean; kicad-happy analyze_pcb / analyze_gerbers run and triaged
- Rev B: 3rd SAW per band (B7504 / B8889) + 100 pF before the DXP; +5V plane connectivity verified (1 island, 57 pads, 28 vias)
- Rev C: star bias on In1.Cu (4 trunks + FB1-4 + 10 uF per channel, In1 otherwise GND); shield-can frame per
  channel (octagon, via fence, RF notch); GPDF6010.A data sheet applied: centre screw grounded, D1.8 locating
  holes, D3.5 feed clearance
- Rev D: limiter RLM-63-2W+ -> CLM-83-2W+ (in-line, no jog; paddle + tab GND vias), TVS SMAJ5.0A -> 1.5SMC6.8A
  (SMC; C1/C2 moved 1.4 mm down to clear it). NF +0.03 dB vs Rev C (limiter IL 0.14-0.17 dB, pre-LNA line +0.6-1.7 mm)
- RF budget from the project 16 cascade + limiter IL + routed line lengths; power budget
- Schematics (project 16 style), cross-checked against the PCB part list; BOM CSV/XLSX; report PDF

## Open items
- Order / design the 4 shield cans to the outline file (6 mm high, RF exit notch)
- NavIC S-band patches (product photo, on the axes) not on this board: decide before Rev D (A3)
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
