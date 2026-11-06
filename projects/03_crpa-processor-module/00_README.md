# 03 - CRPA processor module (digitizer + anti-jam processing) for CRL-LS-CRPA4

Compact CRPA electronics behind the project 02 antenna `CRL-LS-CRPA4` (4 elements, L1 + L2/L5 on OUT_L,
NavIC S on OUT_S, 8 × SMA). Scope: phase-coherent digitizing of the 4 elements, calibration, adaptive nulling /
beam-forming (power inversion → MVDR / STAP) and the output to a GNSS / NavIC receiver.

**State:** study stage. Reference projects read and summarised; architecture proposed; requirements open.

## Files
| Folder / file | Content |
|---|---|
| `02_python/` | `build_case.py` (builds everything below), `config.py` (all case dimensions), `case.py` (SolidCraft parts + assembly), `drawing.py` (CNC drawings), `make_logo.py` (BEL CRL logo) |
| `06_step/` | GNSS_JAM_PRO v1.0 case = PocketSDR v2.3 case design, CNC: `CRL-PSDR23-CASE-01` tube, `-02` ANT panel, `-03` USB panel, `_ASSY` / `_ASSY_EXPLODED` STEP + renders |
| `07_drawings/CRL-PSDR23-CASE_DRAWINGS.pdf` | 4-sheet A3 CNC drawing set (tube, two panels, assembly + parts list) |
| `00_reference/pocketsdr_v2.3/` | PocketSDR FE 2CH v2.3 source: kicad_pcb, schematic / PCB PDF, parts list, case + panel `.f3d`, panel `.3mf` |
| `00_input/BEL_CRL_logo.png` | BEL logo with 'CENTRAL RESEARCH LABORATORY' in the BHARAT ELECTRONICS lettering (case marking) |
| `05_docs/CRPA_reference_review.md` | Review of PocketSDR, max2771_fx2lp, the airborne STK CRPA study, polarization-crpa and the STM32 anti-jam gist; what each means for this module; candidate architectures; open inputs |

## References
- PocketSDR: https://github.com/tomojitakasu/PocketSDR
- max2771_fx2lp: https://github.com/jmfriedt/max2771_fx2lp
- CRPA airborne anti-jamming (STK): https://github.com/ihalhashem/CRPA-Enabled-Airborne-GNSS-Anti-Jamming
- polarization-crpa: https://github.com/ajisrawi/polarization-crpa
- STM32 anti-jam gist: https://gist.github.com/nazlibehrouz/3a767275e77a04bdbac8fc5b28de92ae
- Antenna: `projects/02_ls-crpa4-rf-module`
