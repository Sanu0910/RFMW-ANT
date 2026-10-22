#!/usr/bin/env python3
"""Derive AERIS-10 radar performance numbers from the constants in its firmware (upstream_snapshot/).

Every input below is copied from the upstream source (file:line in the comment). The outputs are first-order
textbook formulas, not measurements; the upstream hardware had not been brought up when the snapshot was taken.
Writes aeris10_numbers.json and aeris10_beam_phases.csv next to this script.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
C = 299_792_458.0

# ---- upstream constants -------------------------------------------------------------------------
F_TX = 10.5e9                 # adf4382a_manager.h:35  TX LO
F_RX_LO = 10.38e9             # adf4382a_manager.h:36  RX LO  -> IF = 120 MHz
F_IF = 120e6                  # ddc_400m.v:38, main.cpp:194
FS_ADC = 400e6                # ddc_400m.v:39 (AD9484, 8-bit)
CIC_DEC = 4                   # cic_decimator_4x_enhanced.v:15 -> 100 MSPS baseband
FS_BB = FS_ADC / CIC_DEC
FS_DAC = 120e6                # plfm_chirp_controller.v:38
F_START, F_END = 30e6, 10e6   # plfm_chirp_controller.v:36-37 (down-chirp in the DAC band)
T_LONG = 30e-6                # plfm_chirp_controller.v:41  (3600 samples @ 120 MHz)
T_LONG_LISTEN = 137e-6        # :42
T_SHORT = 0.5e-6              # :43
T_SHORT_LISTEN = 174.5e-6     # :44
T_GUARD = 175.4e-6            # :45
CHIRPS_PER_FRAME = 32         # doppler_processor.v:38 (16 long-PRI + 16 short-PRI sub-frames)
DOPPLER_FFT = 16              # doppler_processor.v:36
MF_FFT = 1024                 # matched_filter_processing_chain.v:69
RANGE_BINS_OUT = 64           # range_bin_decimator.v:35
RANGE_DEC = 16                # range_bin_decimator.v:36
ELEV_PER_AZ, AZ_PER_SCAN = 31, 50   # radar_mode_controller.v:35-36
PHASE_STATES = 128            # ADAR1000_Manager.cpp:23 (2.8125 deg)
N_PATCH = (8, 16)             # README: AERIS-10N 8x16 patch array
PATCH_DIR_DBI, PATCH_EFF = 7.19, 0.567   # docs/AERIS_Antenna_Report.pdf p.1
WG_EPS, WG_A, WG_SLOTS, WG_COLS = 9.8, 8.5e-3, 32, 16   # 5_Simulations/Slotted_DielectricFilled_Waveguide.m
KAISER_BETA = 1.65            # 5_Simulations/array_pattern_Kaiser25dB_like.py:20


def main():
    lam = C / F_TX
    bw = abs(F_START - F_END)
    r = {}
    r["IF_MHz"] = (F_TX - F_RX_LO) / 1e6
    r["wavelength_mm"] = lam * 1e3
    r["chirp_bandwidth_MHz"] = bw / 1e6
    r["range_resolution_m"] = C / (2 * bw)
    r["long_chirp_TB_product"] = bw * T_LONG
    r["pulse_compression_gain_dB"] = 10 * math.log10(bw * T_LONG)
    r["blind_range_long_chirp_m"] = C * T_LONG / 2
    r["blind_range_short_chirp_m"] = C * T_SHORT / 2
    r["max_range_long_listen_km"] = C * T_LONG_LISTEN / 2 / 1e3
    r["max_range_short_listen_km"] = C * T_SHORT_LISTEN / 2 / 1e3
    t_slot = T_LONG + T_LONG_LISTEN + T_GUARD + T_SHORT + T_SHORT_LISTEN
    r["chirp_slot_us"] = t_slot * 1e6
    r["PRF_Hz"] = 1 / t_slot
    r["frame_ms"] = CHIRPS_PER_FRAME * t_slot * 1e3
    r["v_unambiguous_mps"] = lam / (4 * t_slot)          # +/- at the slot PRF
    r["v_resolution_16pt_mps"] = lam / (2 * DOPPLER_FFT * t_slot)
    r["mf_bin_m"] = C / (2 * FS_BB)
    r["decimated_range_bin_m"] = r["mf_bin_m"] * RANGE_DEC
    r["range_window_64bins_m"] = r["decimated_range_bin_m"] * RANGE_BINS_OUT
    r["scan_beams"] = ELEV_PER_AZ * AZ_PER_SCAN
    r["full_scan_s"] = r["scan_beams"] * r["frame_ms"] / 1e3
    n = N_PATCH[0] * N_PATCH[1]
    r["patch_array_gain_dBi"] = PATCH_DIR_DBI + 10 * math.log10(n) + 10 * math.log10(PATCH_EFF)
    fc = C / (2 * WG_A * math.sqrt(WG_EPS))
    lam_g = (C / F_TX / math.sqrt(WG_EPS)) / math.sqrt(1 - (fc / F_TX) ** 2)
    r["alumina_wg_cutoff_GHz"] = fc / 1e9
    r["alumina_wg_lambda_g_mm"] = lam_g * 1e3
    r["alumina_slot_pitch_mm"] = lam_g / 2 * 1e3
    r["phase_step_deg"] = 360 / PHASE_STATES
    with open(os.path.join(HERE, "aeris10_numbers.json"), "w") as fh:
        json.dump({k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}, fh, indent=1)

    # beam-steering phase words, as ADAR1000Manager::calculatePhaseSettings computes them (lambda/2 spacing)
    with open(os.path.join(HERE, "aeris10_beam_phases.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["angle_deg"] + [f"elem{i}" for i in range(16)] + ["note"])
        for ang in range(-45, 46, 15):
            dphi = math.pi * math.sin(math.radians(ang))        # 2*pi*(lambda/2)*sin/lambda
            words = [int(((i * dphi) % (2 * math.pi)) / (2 * math.pi) * PHASE_STATES) for i in range(16)]
            w.writerow([ang] + words + ["16-element progression; upstream writes only i = 0..3 per ADAR1000"])
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
