# AERIS-10 (PLFM_RADAR): what it is and what we can learn from it

Source: https://github.com/NawfalMotii79/PLFM_RADAR, commit `62d4c55` (14 Oct 2026), by Nawfal Motii and contributors.
Hardware: CERN-OHL-P v2. Software/firmware: MIT. Status upstream: **alpha**. The FPGA builds are timing-clean and the
regressions pass, but the radar hardware had not been brought up yet (the docs describe the board-day plan).

Numbers marked *(derived)* come from `analysis/aeris10_numbers.py`, which recomputes them from the firmware
constants. Everything else is quoted from the upstream files named in brackets.

---

## 1. The system in one paragraph
AERIS-10 is an open-source **10.5 GHz (X-band) pulse-LFM phased-array radar**. A DAC makes a 20 MHz chirp, which is
mixed up to 10.5 GHz and transmitted through 16 front-end channels. Each channel has an ADTR1107 T/R chip, and the
16 channels are steered electronically by four 4-channel ADAR1000 beamformers (±45°). A stepper motor and slip ring
add 360° mechanical rotation. The echo is mixed down to a 120 MHz IF and sampled at 400 MSPS by an 8-bit AD9484. A
Xilinx Artix-7 FPGA then does DDC → pulse compression → range decimation → MTI → Doppler FFT → CFAR and streams the
detections over USB to a Python GUI. An STM32F746 sequences the power rails, programs the clocks, LOs and
beamformers, closes the PA-bias loop, and reads GPS, IMU and temperature.

| Version | Antenna | Power | Range |
|---|---|---|---|
| AERIS-10N "Nexus" | 8 × 16 patch array on RO4350B | ≈ 1 W × 16 | 3 km |
| AERIS-10E "Extended" | 32 × 16 alumina-filled slotted-waveguide array | 10 W × 16 (QPA2962 GaN) | 20 km |

## 2. Frequency plan and waveform
- **Clocks.** AD9523-1 jitter cleaner from a 100 MHz VCXO feeds both ADF4382A LOs, the DAC, the ADC and the FPGA.
  This keeps everything phase-coherent, which Doppler processing needs. [README, main.cpp `configure_ad9523`]
- **LOs.** TX LO 10.5 GHz, RX LO 10.38 GHz, so the IF is 120 MHz. [adf4382a_manager.h:35-36]
- **Chirp.** The DAC runs at 120 MSPS and sweeps 30 → 10 MHz (B = 20 MHz). The two LTC5552 mixers handle the up- and
  down-conversion. [plfm_chirp_controller.v:36-45]
- **Two pulses per slot.** Each "chirp slot" holds a long pulse and a short pulse:

  | Pulse | Length | Listen time | Purpose |
  |---|---|---|---|
  | Long | 30 µs | 137 µs | far targets, with big pulse-compression gain |
  | Guard | 175.4 µs | — | separates the two pulses |
  | Short | 0.5 µs | 174.5 µs | near targets inside the long pulse's blind zone |

- **Performance** *(derived)*:

  | Quantity | Value |
  |---|---|
  | Range resolution c/2B | **7.5 m** |
  | Long-pulse time–bandwidth product | 600, i.e. **27.8 dB** compression gain |
  | Long-pulse blind zone (TX on) | **4.5 km** |
  | Short-pulse blind zone | 75 m |
  | Long listen window | 20.5 km (matches the 20 km version) |
  | Slot period | 517.4 µs, so PRF = **1932.7 Hz** |
  | One frame (32 slots) | 16.6 ms |
  | Unambiguous velocity | ±13.8 m/s at λ = 28.6 mm |
  | Velocity resolution (16-point FFT) | 1.7 m/s |

- **Scan.** 32 chirps per beam position × 31 elevations × 50 azimuths. A full electronic raster is 1550 beams, about
  **25.7 s per scan** *(derived)*. [radar_mode_controller.v:34-36]

## 3. FPGA signal chain (9_Firmware/9_2_FPGA)
| Stage | Module | Key facts |
|---|---|---|
| ADC capture | `ad9484_interface_400m.v`, `adc_clk_mmcm.v`, `cdc_modules.v` | 400 MHz domain, MMCM jitter cleaning (Build 20), toggle/handshake CDC into the 100 MHz processing domain |
| DDC | `ddc_400m.v`, `nco_400m_enhanced.v` | 8-bit ADC, 16-bit NCO, 18-bit mixer, phase increment 0x4CCCCCCD = 120 MHz / 400 MHz, dithering |
| Decimation | `cic_decimator_4x_enhanced.v`, `fir_lowpass.v` | 5-stage CIC ÷4 (48-bit accumulators, CREG-pipelined DSP48 combs), then a 32-tap FIR (18-bit) at 100 MSPS |
| Pulse compression | `matched_filter_processing_chain.v`, `matched_filter_multi_segment.v`, `*.mem` | frequency domain: 1024-point FFT of the signal and reference, conjugate multiply, IFFT; the 3000-sample long chirp is processed in 4 overlapping segments (128-sample overlap); the reference chirps are in `long_chirp_seg*_i/q.mem`, `short_chirp_*.mem` |
| FFT core | `fft_engine.v`, `xfft_16.v` | home-made radix-2; 4-cycle butterfly (+20 % throughput), twiddle index by barrel shift (−1 DSP) |
| Range decimation | `range_bin_decimator.v` | 1024 → 64 bins (÷16), start-bin skip, watchdog; ≈ 24 m bins and a 1.5 km window per mode *(derived)* |
| Clutter | `mti_canceller.v` + DC notch in top | 2-pulse canceller H(z) = 1 − z⁻¹; post-Doppler notch of ±N bins around zero (registers 0x26/0x27) |
| Doppler | `doppler_processor.v` | **staggered PRF**: two 16-point Hamming FFTs, one per sub-frame (16 long-PRI + 16 short-PRI), because one 32-point FFT over non-uniform sampling would be invalid; outputs tagged {sub_frame, bin} for later ambiguity resolution |
| Detection | `cfar_ca.v` | CA / GO / SO-CFAR on \|I\|+\|Q\|, 64 × 32 BRAM map, up to 8 guard and 16 training cells, alpha in Q4.4 pre-divided by the cell count (example: Pfa 1e-4 with T = 8 per side → alpha ≈ 0x05); 3-cycle pipelined CUT (THR→MUL→CMP), about 85 µs per frame |
| Gain | `rx_gain_control.v` + STM32 `ADAR1000_AGC.cpp` | hybrid AGC: FPGA saturation flag → MCU outer loop → ADAR1000 RX VGA gain; target/attack/decay/hold-off registers 0x28–0x2C |
| Host link | `usb_data_interface.v` (FT601, 32-bit USB 3), `usb_data_interface_ft2232h.v` (8-bit USB 2) | 11-byte data packet `AA, range I/Q, Doppler re/im, det, 55`; 26-byte status packet `BB … 55`; 4-byte commands {opcode, addr, value_hi, value_lo} |
| Self test | `fpga_self_test.v` | opcode 0x30; status readback with 0x31 or 0xFF |

**Host register map** (radar_system_top.v ≈ 951-997):

| Opcode | Function |
|---|---|
| 0x01 | mode |
| 0x02 | trigger |
| 0x03 | threshold |
| 0x04 | stream control |
| 0x10–0x15 | chirp timing and chirps per elevation |
| 0x16 | digital gain shift |
| 0x20 | range mode |
| 0x21–0x25 | CFAR guard / train / alpha / mode / enable |
| 0x26–0x27 | MTI and DC notch |
| 0x28–0x2C | AGC |
| 0x30, 0x31, 0xFF | self test and status |

**Targets.** Production is an xc7a200t-2fbg484i. There is also a 50T board (FT2232H), plus Trenz TE0712/TE0713 + TE0701
dev wrappers with separate XDC files. Build 25 (v0.1.6-mti) uses 9252 LUTs, 12488 FFs, 17 BRAM and 142 DSP48 at
0.75 W, with WNS +0.132 ns. [docs/release-notes.html]

## 4. STM32F746 firmware (9_Firmware/9_1_Microcontroller)
- Bare-metal HAL with Analog Devices **no-OS** drivers for the AD9523, ADF4382A and ADAR1000. `main.cpp` is about
  2900 lines.
- **Power sequencing.** Follows `3_Power Management/Power Management V6.xlsx`. The IWDG watchdog,
  `Emergency_Stop` (cuts the PA rails), a temperature-max guard and periodic Idq re-reads were added under "Gap 3".
- **PA bias loop.** 16 channels, each with a 5 mΩ shunt and an INA241 (×50) read by two ADS7830 I²C ADCs, and Vg
  set by two DAC5578. Idq is calibrated closed-loop at boot.
- **Thermal.** 8 thermistors on a third ADS7830, with one fan GPIO.
- **Beam steering.** `ADAR1000Manager::calculatePhaseSettings` uses λ/2 spacing at 10.5 GHz and 7-bit words (128
  states, 2.8125°). There are also beam-sequence and sweep APIs and custom 16-element patterns.
- **Sensors.** UM982 GPS (TinyGPS++), GY-85 IMU (pitch/roll correction of target coordinates), BMP180 barometer,
  stepper motor.
- **Tests.** `tests/` holds host-side unit tests with HAL/driver mocks. **One test per fixed bug** (bug1…bug15, the
  gap3 safety tests, GPS, AGC), run with a Makefile. This is an excellent pattern.

## 5. GUI (9_Firmware/9_3_GUI)
- `radar_protocol.py` is the pure-logic packet parser and command builder, with no GUI imports, so it is testable.
- `GUI_V65_Tk.py` is a bring-up dashboard:
  - live range–Doppler heat map with the CFAR overlay;
  - waterfall;
  - host commands;
  - HDF5 recording, replay and a demo mode.
- `v7/` is a PyQt6 application in modules: `dashboard`, `hardware`, `map_widget`, `processing`, `software_fpga.py`
  (a software model of the FPGA chain), `replay`, `agc_sim`.
- `smoke_test.py` triggers the FPGA self test.

## 6. Antennas and RF simulations (5_Simulations, docs/*.pdf)
- **Patch element** (openEMS FDTD, docs/AERIS_Antenna_Report.pdf):

  | Quantity | Value |
  |---|---|
  | Substrate | RO4350B, εr 3.48, 0.102 mm |
  | Resonance | 10.495 GHz |
  | S11 | −30.6 dB |
  | Bandwidth | 50 MHz (0.48 %) |
  | Directivity | 7.19 dBi |
  | Efficiency | 56.7 % |
  | 128-element array gain | ≈ 25.8 dBi |

  The 50 MHz bandwidth is narrow, but enough for a 20 MHz chirp.
- **Slotted waveguide array** (`Slotted_DielectricFilled_Waveguide.m`, `wg_alumina_slotted_openems.m`,
  `array_pattern_Kaiser25dB_like.py`, `slot_layout_taper32.csv`):
  - alumina-filled guide (εr 9.8), a = 8.5 mm, b = 3.5 mm;
  - 32 longitudinal offset slots per column, 16 columns at 14.28 mm;
  - Kaiser β = 1.65 amplitude taper set through the slot offsets (0.22–0.30 a);
  - **standing-wave design** (slot pitch λg/2, backshort λg/4 behind the feed), so the beam is fixed at broadside
    in the waveguide plane and steered electronically across the columns.
- **Other ADS / openEMS work:** IF band-pass filters (including a balanced one), stub BPF, DAC reconstruction filter,
  anti-alias filter, RF switch, via fencing, QPA2962 PA match.

## 7. Findings worth reporting upstream (checked by us)
1. **Guide wavelength in the alumina-filled waveguide ignores εr.**
   - Where: `Slotted_DielectricFilled_Waveguide.m` line 22 and `wg_alumina_slotted_openems.m` line 64 both compute
     λg = λ0 / √(1 − (fc/f)²) with the free-space λ0.
   - The correct formula for a filled guide uses λ0/√εr: λg = (λ0/√εr) / √(1 − (fc/f)²) =
     **10.81 mm, not 33.83 mm** *(derived)*.
   - Consequence: the slot pitch λg/2 should be 5.40 mm, not 16.9 mm. With 16.9 mm the slots are about 1.6 λg
     apart, so they are not in phase and the array will not radiate at broadside as intended.
   - The slot-length rule 0.47 λg is tied to the wrong λg too. A slot backed by the dielectric resonates somewhere
     between λ0/2 ≈ 14.3 mm (air) and about λ0 / (2√((εr+1)/2)) ≈ 6 mm. So re-derive the length and the
     offset-conductance table with an openEMS / FEM unit-cell sweep instead of scaling it.
   - `slot_layout_taper32.csv` (z pitch 16.915 mm) inherits the error.
2. **Beam-steering phases repeat every 4 elements.**
   - Where: `ADAR1000Manager::setBeamAngle` computes phases for i = 0…3 only and writes the same 4 words to every
     ADAR1000.
   - If the 16 channels form one line across the four chips, elements 4–15 get the wrong progression (0, φ, 2φ, 3φ,
     0, φ, …). The correct 16-element words are in `analysis/aeris10_beam_phases.csv`.
   - This is only correct if each ADAR1000 drives a separate row or column, which the schematic should confirm.
3. **The long pulse is blind out to 4.5 km**, and its 137 µs listen window ends at 20.5 km. Targets between 75 m and
   4.5 km depend on the 0.5 µs short pulse, which has no compression gain, so sensitivity is much lower there. Worth
   stating clearly in the range spec of the 3 km version.

## 8. Techniques worth reusing in our projects
- **Golden-model co-simulation.** Python reference vs RTL, bit-exact on recorded ADC data (5137 checks), plus a
  46-check end-to-end testbench and a regression script.
- **Bug-numbered regression tests** for MCU firmware, with HAL mocks on the host.
- **Clean separation.** DSP core modules stay board-agnostic. Per-board top wrappers and XDCs live separately, and
  bring-up starts with a minimal heartbeat image.
- **Timing closure, documented per build.** WNS/WHS and resources are logged in the release notes, the cause of a
  timing failure is pinned down (Build 23 CFAR combinational path → 3-stage pipeline), and DSP48 CREG/PREG
  pipelining is used.
- **Radar-architecture choices:**
  - long + short pulse to cover the blind zone;
  - staggered PRF with separate FFTs;
  - MTI + DC notch before CFAR;
  - hybrid FPGA/MCU AGC.
- **Bring-up discipline.** Pre-arrival gates, a smoke-test order, explicit abort criteria
  (docs/bring-up.html, board-day-worksheet.html).

## 9. Links to this repository
- `projects/08_60ghz-serpentine-lwa_TAP2026` is also a slotted waveguide array, but a *travelling-wave* one whose
  beam steers with frequency. AERIS-10 uses the *standing-wave* (λg/2, broadside) variant and steers with phase
  shifters instead.
- `docs/GDS2OPENEMS.md` / `docs/HERTZON.md`: the same openEMS / FEM tools can re-simulate the AERIS-10 patch and the
  corrected alumina slot array.
