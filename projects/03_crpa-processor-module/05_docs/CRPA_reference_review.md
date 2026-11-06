# CRPA processor module: review of the reference projects

_2026-11-06. Read for project 03: the compact CRPA electronics (digitizer + anti-jam processor) that goes behind
the project 02 antenna CRL-LS-CRPA4. Numbers marked [ESTIMATE] are hand calculations here; [VERIFY] = check the data sheet._

## 1. What our antenna gives the processor (project 02, Rev A)

| Item | Value |
|---|---|
| Elements | 4, square, L patches at (±45.5, ±45.5) mm: 91 mm pitch = 0.48 λ at L1, 0.36 λ at L5; S patches on the axes, 60.15 mm (λ/2 at 2492 MHz) |
| Outputs | 8 × SMA: 4 × OUT_L (L1 + L2/L5 **combined** in one coax by the DXP.02.A), 4 × OUT_S (NavIC S 2492 MHz) |
| Gain at the SMA | 33-41 dB, NF about 1.2-1.6 dB; Rev B plan: 25-28 dB with input P1dB about -10 dBm |
| Power | +5 V on a separate DC connector (8.4 W for 4 channels) |
| Calibration path | **none**: no coupler for calibration injection |
| Channel matching target | ≤ 0.5 dB / ≤ 5° [ASSUMED in the design basis] |

So the processor must split L1 from L2/L5 on each OUT_L, digitize up to 12 channels (4 elements × L1, L5, S)
and keep them phase coherent.

## 2. The five references

### 2.1 PocketSDR (T. Takasu), github.com/tomojitakasu/PocketSDR. The strongest reference
- Open GNSS SDR: hardware (KiCad), FX3 firmware, C library, receiver apps. FE 2CH / 4CH / **8CH** boards with one
  **MAX2771** per channel, one 24 MHz TCXO, Cypress **FX3 USB 3.0** to a host PC or Raspberry Pi 5.
- MAX2771 per channel: LNA + mixer + IF filter + ADC + synthesizer. LO 1525-1610 MHz **or** 1160-1290 MHz (one band
  per chip), IF bandwidth 2.5-36 MHz, up to 48 Msps, **2- or 3-bit samples**. FE 8CH: 5 V, 330 mA from USB.
  **NavIC S (2492 MHz) is not covered.**
- Software: every GPS / GLONASS / Galileo / QZSS / BeiDou / **NavIC L1 and L5** / SBAS signal; acquisition, tracking,
  PVT, RTCM3 / NMEA, GUI and web UI. Runs on x86 (AVX2 / AVX-512) and on ARM (NEON, Raspberry Pi 5).
- **Array support since v0.15 (2026-05):**
  - `pocket_calib` and `sdr_array.c`: estimates array attitude (roll / pitch / yaw) and each channel's bias against
    CH1, with an EKF on single-difference carrier phase, from live signals or per-element RINEX files. The antenna
    geometry comes from a text file (`x y z` per element, CH1 = 0 0 0).
  - `-arch N` makes N "array channels": the RF channels combined with int16 (Q8) weights pointing at an azimuth /
    elevation. The combined channel is tracked like any other.
  - This is **deterministic beam steering toward satellites**. There is **no adaptive nulling** (no power inversion
    or MVDR) and no STAP.
- The README flags FE 8CH + array calibration + beam-forming as possibly **dual-use**. BEL does its own classification.
- **Use for us:** a ready, cheap, coherent multi-channel L1 + L5 bench receiver. It gives the array calibration,
  CP / phase-centre checks and recorded raw IF to develop algorithms on. **Not** the anti-jam product: with 2-3-bit
  samples a strong jammer takes over the AGC and the ADC range, so nulling after the ADC only works against weak
  jammers. A rough guess is J/N up to about 20 dB [ESTIMATE].

### 2.2 max2771_fx2lp (J.-M. Friedt), github.com/jmfriedt/max2771_fx2lp
- A dual-MAX2771 board (PocketSDR v2.3 circuit) on a cheap FX2LP USB 2.0 board, up to 44 MS/s in total, driven by
  the PocketSDR tools. Uses: dual-band from one antenna, **or a 2-element CRPA**.
- `CRPA/`: two antennas at λ/2 used for **spoof detection by direction of arrival**. Real satellites show different
  inter-antenna phases; a single spoofer (PlutoSDR `pluto-gps-sim`) shows the same phase for every satellite.
  This is codeless: the phase is taken from the squared BPSK signal.
- `250610_calibrate_phase/`: **the phase between two MAX2771 on the same clock is random after each power-up and
  each re-tune between upper and lower L-band.** It stays fixed during continuous streaming, but drifts as the chip
  warms up (1 rad = 100 ps). Their fix: switch an on-board oscillator into both inputs and calibrate every few
  measurements.
- HW note: the MAX2771 input match (L/C) is band-specific: 5.6 nH / 1.7 pF upper L, 8.4 nH / 1.1 pF lower L.
- **Lessons for us:** (1) the module needs a **built-in calibration source** and must recalibrate at every power-up
  and periodically. (2) A DC block is needed where a bias-carrying input meets a DC-passing combiner.
  (3) DoA-based spoof detection is a cheap extra feature for our 4-element array.

### 2.3 CRPA-Enabled Airborne GNSS Anti-Jamming (STK study), github.com/ihalhashem/...
- STK scenario: an airliner at 10 kft, a jammer on a rooftop (5 W dipole; stress case 20 W into a 10 dBi panel),
  5 MHz noise at L1. Compares a single patch (FRPA) with a **2-element λ/2 MVDR** CRPA.
- Median C/N0 loss: 8.2 dB-Hz (FRPA) vs 0.4 (CRPA) at 5 W; 23.9 vs 4.1 dB-Hz in the stress case.
  The null sometimes falls on a satellite.
- Ideal array: no channel mismatch, no quantization, no coupling, so the numbers are optimistic. A 2-element array
  places only one null.
- **Use for us:** the method for deriving requirements: jammer EIRP and distance give J/S at the element. Examples
  [ESTIMATE, free space, L1, 0 dBic element]:

  | Jammer | Distance | Power at the element | J/N in 20 MHz (noise -99 dBm) |
  |---|---|---|---|
  | 10 W, 0 dBi | 1 km | -56 dBm | 43 dB |
  | 10 W, 0 dBi | 100 m | -36 dBm | 63 dB |
  | 100 W, 13 dBi | 10 km | -53 dBm | 46 dB |

  So the receive chain must stay **linear and unclipped to about -35 dBm per element**. That needs at least 70 dB of
  dynamic range after the antenna.

### 2.4 polarization-crpa (12 channels, simulation stage), github.com/ajisrawi/polarization-crpa
- A simulator (Python) of space-polarization-time adaptive processing on raw IQ. **Power inversion** is blind: it
  needs no satellite directions, attitude or calibration. **MVDR** forms one beam per satellite and needs a
  calibrated array, attitude and ephemeris. 1 or 5 taps per channel, diagonal loading 0.1 × noise.
  `crpa_dsp.py` is about 100 lines and easy to port.
- Proposed hardware: per channel limiter → **20 dB coupler (calibration injection)** → LNA → BPF → gain block →
  **RFSoC ZU49DR direct RF sampling** at 2 GSPS (2nd Nyquist covers 1.0-2.0 GHz, no LO). STAP runs in the FPGA, and
  an RF-DAC re-synthesizes clean L-band into a **COTS receiver (u-blox ZED-X20P)**. Proposed headroom: about
  -40 dBm per element, more with a 0-31.5 dB step attenuator under AGC. **Nothing is built or measured.**
- Findings that matter for us:
  - **Channel matching is the hidden requirement.** Without per-channel FIR equalization (64 taps, fitted to a
    calibration-noise injection) every design collapses after about 6 jammers. With it, the degradation is gradual.
  - MVDR keeps more satellites than power inversion and adds up to about 10 dB of array gain, but needs calibration,
    attitude and ephemeris.
  - Space-only nulling loses a satellite that sits within a few degrees of a jammer. Dual-polarized elements fix this
    at 2× the channel count.
- **Use for us:** the system shape (cal coupler, equalizer, PI first then MVDR, RF re-synthesis to a COTS receiver)
  and the DSP code. The RFSoC is too big and power-hungry for "compact" (tens of W) and its 2 GSPS plan does not
  reach 2492 MHz in the same Nyquist zone.

### 2.5 Gist "Accurate GPS Anti-Jamming with STM32", gist.github.com/nazlibehrouz/...
- A generic survey that reads as auto-generated: unsourced headline numbers ("73 %", "100x", "40-50 dB"), and code
  fragments that are not a working design. An STM32 cannot digitize or beam-form GNSS signals: its ADCs are a few
  Msps with no RF front end, and the CRPA code shown is only a skeleton.
- Usable ideas: multi-constellation + dual frequency, spectrum monitoring / jammer classification, GNSS/INS
  coasting. Commercial units named: NovAtel GAJT-710ML, Chelton DACU8b, TUALCOM. **Not a design basis.** An STM32
  could at most be the housekeeping controller (power, AGC, BIT, telemetry).

## 3. What this means for the module

1. **Null capacity:** 4 elements give at most **3 spatial nulls**. STAP taps help wideband jammers and channel
   mismatch but do not add null directions.
2. **Null depth is set by channel matching** [ESTIMATE, residual error vector of one channel]:

   | Residual mismatch | Null depth |
   |---|---|
   | 5° / 0.5 dB (project 02 target) | about 20 dB |
   | 2° / 0.2 dB | about 28 dB |
   | 1° / 0.1 dB | about 34 dB |
   | 0.5° / 0.05 dB | about 40 dB |

   SAW group-delay ripple makes the mismatch frequency dependent, so the 35-40 dB that commercial CRPAs quote
   needs **calibration injection plus per-channel FIR equalization**, not only matched parts.
3. **ADC resolution:** at least 12 bit (about 74 dB SNR) at 20-60 Msps, so a -35 dBm jammer and the noise floor both
   fit with crest-factor margin. 2-3-bit MAX2771 samples are for the bench only.
4. **Linearity:** the antenna gain and the ADC full scale must be planned together (project 02 Rev B). A jammer that
   compresses an LNA or SAW creates intermodulation that no null can remove.
5. **Coherence:** one reference clock for all chips, phase calibration after every power-up / re-tune and periodically
   over temperature (MAX2771 finding). The same applies to multi-chip transceivers.
6. **NavIC S** needs a digitizer that tunes to 2.5 GHz. A wideband transceiver (70 MHz-6 GHz class) covers
   L1 / L5 / S by tuning; the MAX2771 does not.
7. **Output to the user:** (a) re-synthesized RF into a COTS GNSS / NavIC receiver (how commercial AJ units work,
   easiest to integrate), or (b) beam-formed baseband into an embedded receiver (PocketSDR on the ARM cores),
   giving PVT out. (a) is the lower-risk first product.

## 4. Candidate architectures

| | A. Bench: PocketSDR FE 8CH | B. Compact AJ module (proposed) | C. Direct RF sampling (RFSoC) |
|---|---|---|---|
| Digitizer | 8 × MAX2771, 2-3 bit | multi-channel transceivers, 12-16 bit, e.g. 2 × AD9361 (FMCOMMS5-class 4-ch coherent) or a quad-RX transceiver [VERIFY LO / sync scheme] | RF-ADC 12-14 bit, GSPS |
| Bands at once | L1 + L5, 4 elements each | one band × 4 elements per 4-ch digitizer; L1 + L5 + S needs 3 sets (12 RX) | all L-band in one zone; S needs another fs |
| Processing | host PC / RPi 5: PocketSDR calibration + beam steering | FPGA (Zynq-class): power inversion → MVDR / STAP, cal + FIR equalizer, AGC | FPGA STAP (polarization-crpa plan) |
| Output | PVT, RINEX, raw IF files | RF out to a COTS GNSS / NavIC receiver (via DAC) and / or digital PVT | RF out via RF-DAC |
| Size / power | small, < 2 W | medium, about 10-15 W [ESTIMATE] | large, 20-30 W+ [ESTIMATE] |
| Anti-jam | weak (low-bit ADC) | target 3 nulls, 30-40 dB with equalization | best, costly |
| Role | **Phase 0**: verify the array, calibration, data for algorithms | **Phase 1 product** | not "compact" |

## 5. Proposed path

1. **Phase 0 (bench, low cost):** OUT_L → splitter / diplexer → PocketSDR FE 8CH (4 × L1 + 4 × L5 MAX2771).
   Geometry file from project 02, `pocket_calib` for biases and attitude, beam steering, raw IF recording. Port
   `crpa_dsp.py` (PI / MVDR) and run it offline on the recordings and on simulated jammers.
2. **Project 02 Rev B inputs:** add a **calibration-injection coupler per element** (after the limiter, before
   LNA1); set the gain plan from the ADC full scale (section 3.4); keep identical layouts per channel.
3. **Phase 1 (module):** 4- or 12-channel coherent digitizer + Zynq-class FPGA, power inversion first, cal tone /
   noise source + per-channel FIR equalizer, AGC / step attenuators, RF output to a COTS receiver, BIT. One
   enclosure sized to sit behind the D200 antenna, or a separate box.

## 6. Open inputs needed from BEL CRL
1. Bands that must be protected **at the same time** (L1 + L5 + S, or L1 + S first?).
2. Output wanted: RF to an existing receiver (which one, NavIC-capable?) or PVT / timing out of the module.
3. Threat: number of jammers, J/S to survive, jammer types (CW / wideband / pulsed / spoofer).
4. Platform, size, power, supply (5 V or 28 V), environment (MIL-STD-810 / 461).
5. FPGA / SoC family and in-house IP preference (Xilinx / Microchip / Intel; indigenous parts requirement).
6. Export / security classification handling for the design data (repo is public: keep sensitive detail private).
