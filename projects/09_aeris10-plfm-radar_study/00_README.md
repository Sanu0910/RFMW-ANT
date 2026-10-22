# 09: AERIS-10 open-source X-band phased-array radar (study + saved copy)

A study of **[NawfalMotii79/PLFM_RADAR](https://github.com/NawfalMotii79/PLFM_RADAR)**. It is a 10.5 GHz pulse-LFM
phased-array radar with these parts:
- an Artix-7 FPGA DSP chain;
- an STM32F746 controller;
- four ADAR1000 beamformers and 16 ADTR1107 T/R front ends;
- a Python GUI;
- patch or alumina slotted-waveguide antenna arrays.

| Path | Content |
|---|---|
| `LEARNING_NOTES.md` | **Start here.** System, frequency plan and waveform, FPGA chain module by module, MCU firmware, GUI and protocol, antennas and simulations, our findings, techniques to reuse |
| `analysis/aeris10_numbers.py` | recomputes range resolution, blind zones, PRF, Doppler limits, scan time, array gain and alumina-guide λg from the upstream constants → `aeris10_numbers.json`, `aeris10_beam_phases.csv` |
| `upstream_snapshot/` | copy of upstream commit `62d4c556508927a4192acca24422bd16a979c7dc` (2026-10-14) |

## About the snapshot
It is the upstream tree at that commit, unmodified, minus:
- `7_Components Datasheets and Application notes/` and `6_Application Notes/`: vendor datasheets (Analog Devices,
  Qorvo, TI, Mini-Circuits …). These are copyrighted by the chip makers and not covered by the project licence;
  download them from the vendors.
- `docs/artifacts/*.bit`: FPGA bitstreams, a build output (rebuild with Vivado from `9_Firmware/9_2_FPGA/scripts`).
- `5_Simulations/IF_BPF_Balanced/IF_BPF_Balanced.dat` (20 MB ADS dataset), `*.mp4` videos and the author's
  photo.

To get the complete original: `git clone https://github.com/NawfalMotii79/PLFM_RADAR && git -C PLFM_RADAR checkout 62d4c55`.

## Licence
- Hardware design files (schematics, layouts, Gerbers, BOM, mechanical): **CERN-OHL-P v2** (`upstream_snapshot/Licence`).
- Software, firmware, FPGA code and the Python GUI: **MIT**.
- The copyright notices of the original authors are kept. Our own files (`LEARNING_NOTES.md`, `analysis/`) are
  separate and do not modify the snapshot.
- Upstream status is **alpha** (not yet hardware-validated). Their RF power (up to 10 W × 16 at X-band) needs a
  licence and RF-safety precautions to transmit.
