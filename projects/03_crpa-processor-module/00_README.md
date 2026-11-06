# 03 - CRPA processor module (digitizer + anti-jam processing) for CRL-LS-CRPA4

Compact CRPA electronics behind the project 02 antenna `CRL-LS-CRPA4` (4 elements, L1 + L2/L5 on OUT_L,
NavIC S on OUT_S, 8 × SMA). Scope: phase-coherent digitizing of the 4 elements, calibration, adaptive nulling /
beam-forming (power inversion → MVDR / STAP) and the output to a GNSS / NavIC receiver.

**State:** study stage. Reference projects read and summarised; architecture proposed; requirements open.

## Files
| Folder / file | Content |
|---|---|
| `05_docs/CRPA_reference_review.md` | Review of PocketSDR, max2771_fx2lp, the airborne STK CRPA study, polarization-crpa and the STM32 anti-jam gist; what each means for this module; candidate architectures; open inputs |

## References
- PocketSDR: https://github.com/tomojitakasu/PocketSDR
- max2771_fx2lp: https://github.com/jmfriedt/max2771_fx2lp
- CRPA airborne anti-jamming (STK): https://github.com/ihalhashem/CRPA-Enabled-Airborne-GNSS-Anti-Jamming
- polarization-crpa: https://github.com/ajisrawi/polarization-crpa
- STM32 anti-jam gist: https://gist.github.com/nazlibehrouz/3a767275e77a04bdbac8fc5b28de92ae
- Antenna: `projects/02_ls-crpa4-rf-module`
