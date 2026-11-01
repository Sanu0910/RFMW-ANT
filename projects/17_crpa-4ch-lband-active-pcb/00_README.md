# 17 - CRPA 4-channel L-band active antenna front end (PCB)

Production PCB for the CRL BEL 4-element GNSS CRPA, L-band only (L1 + L2/L5). The antenna geometry is kept
from the customer board `Gerber_4CH_GNSS.zip` (Ø200 mm round board, 4 stacked L1/L2 patch modules on a 92 mm
square pitch with sequential 90° rotation, dual 0°/90° feeds per band). The RF chain is the one from
project 16, with an RLM-63-2W+ limiter added in front of each LNA (Rev A) and a third SAW per band before the
diplexer (Rev B):

```
            L1 0/90 feeds -> HC125A -> RLM-63-2W+ -> TQP3M9037 -> B7504 -> TQP3M9037 -> B7504 -> B7504 ---+
patch (xN)                                                                                                  +-> DXP.02.A -> SMA  (CHn out)
            L2 0/90 feeds -> HC125A -> RLM-63-2W+ -> TQP3M9037 -> B8889 -> TQP3M9037 -> B8889 -> B8889 ---+
x4 channels; all 16 LNAs biased from ONE +5 V input (J5) through the In1.Cu plane
```

## Key results
| Item | Value |
|---|---|
| Board | Ø200 mm (outline kept), **4-layer FR-4, 1.6 mm**, ENIG. L1 GND (antenna ground) / L2 +5V / L3 GND / L4 RF + all SMD |
| 50 Ω line | 0.38 mm on L4 over L3 (0.21 mm 7628 prepreg), 0.30 mm gap to pour, via fences |
| Channels | 4 identical (one layout rotated 4×): equal length per net; hybrid feed pairs matched (L1 2.718/2.718 mm, L2 7.082/7.082 mm) |
| Gain / NF (CH, at RF out) | L1 37.2 dB / 1.06 dB, L5 40.9 dB / 0.82 dB, L2 38.4 dB / 0.86 dB (project 16 chain + limiter + 3rd SAW + routed lines) |
| Bias | single +5 V input J5 (Micro-Fit 3.0): PTC, reverse-polarity P-FET, TVS; 1.12 A typ / 1.44 A max. Distributed by a solid **+5V plane on In1.Cu** (no tracks): 8 vias from J5, one via at each of the 16 LNA chokes; one connected island (`Images/bias_plane_In1Cu.png`) |
| Check | kicad-cli DRC (zones refilled): **0 violations, 0 unconnected**; kicad-happy PCB + Gerber analyzers |

## Substrate choice (0.8 vs 1.6 mm)
1.6 mm, 4 layers. A Ø200 mm board with four antenna modules needs the stiffness, and the thin 0.21 mm prepreg
between L4 and L3 gives a 0.38 mm 50 Ω line that matches the 0402 / DFN / SAW pads. On 2-layer boards a 50 Ω line
would be about 1.5 mm (0.8 mm board) or 3 mm (1.6 mm board), wider than every pad, and the bias would cut the
ground. Details in `Docs/CRPA17_PCB_Design_Report.pdf` §2.

## Folders
| Folder | Content |
|---|---|
| `Fab/` | **`CRPA17_4CH_LBAND_Gerbers.zip`** (Gerber X2, Excellon PTH/NPTH, drill map, job file), `Gerbers/`, **BOM** (`.csv`, `.xlsx`), CPL (bottom), IPC-D-356 |
| `KiCad/` | `CRPA17_4CH_LBAND.kicad_pcb/.kicad_pro/.kicad_dru`, footprint library `CRPA17.pretty`, `fp-lib-table` |
| `Docs/` | `CRPA17_PCB_Design_Report.pdf` (decisions, stack-up, schematic, budget, power, verification, assumptions, BOM), `CRPA17_layers.pdf`, `CRPA17_netlist.csv`, RF budget CSVs |
| `Images/` | schematics (channel, power; project 16 style), stack-up, 3D renders top/bottom |
| `Scripts/` | `crpa_design.py` (all parameters), `build_footprints.py`, `build_pcb.py`, `run_drc.sh`, `export_fab.sh`, `make_docs.py`, `plot_debug.py`, `build_all.sh` |
| `Input/` | customer Gerber + RLM-63-2W+ data sheet, **not in git**: copy `Gerber_4CH_GNSS.zip` and `RLM-63-2W+.pdf` here to rebuild the footprints |

## Rebuild
```bash
bash Scripts/build_all.sh      # KiCad 10 (C:/Program Files/KiCad/10.0, or set KICAD10), system Python 3.12
```
`build_pcb.py` runs in KiCad's Python (pcbnew); zones are filled by `kicad-cli pcb drc --refill-zones --save-board`.

## Before ordering (see report §8)
1. Confirm the antenna module drills and pin length (feed 1.1 mm, stud 3.2 mm, M3 3.2 mm NPTH are **[ASSUMED]**: the customer zip has no drill file; pins must pass 1.6 mm instead of 0.85 mm).
2. Order impedance control on L4 and resin-plugged + capped vias in the HC125A / TQP3M9037 / SAW ground pads.
3. Supply J5 with 5.0-5.25 V (no regulator on board).
