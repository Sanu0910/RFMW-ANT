# Status: 15_cband-6x6-dualpol-stacked-patch_match-debug

_Last updated: 2026-10-30 (evening). Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** VSWR fixes within the present design (option 1: parasitic sizes / gap; option 2: feed widths) were checked full-wave and give no real improvement: the element bandwidth is the limit. Next: new wideband element (option 3) if the full band is needed. STEP model with SMA jacks: `07_step/CBand_6x6_asbuilt_with_SMA.step`. Full-array runs of the present design in progress.

## Done
- Inputs decoded (`01_input/`): F.Cu parasitics, In2.Cu driven patches + two 36-way corporate feeds, B.Cu ground, stack-up
- Topology: port 1 feeds top/bottom edges (V-pol), port 2 left/right edges (H-pol); line widths 0.73 / 1.38 / 2.48 mm = 100 / 70.7 / 50 ohm on RT5880 0.8 mm
- Single-element openEMS (`02_openems/sim_element.py`): best S11 -10.8 dB at 5.84 GHz, VSWR<3 only ~5.35-6.26 GHz; realised gain 5.8-9.3 dBi
- Matching study (`match_study.py`): no line/stub/transformer network reaches VSWR<3 over 4-7 GHz -> radiator bandwidth is the limit
- Variants: without the parasitic there is no match anywhere; a larger parasitic (x1.15/1.25/1.35) moves the window down and narrows it
- Stack-up used: 4 mm air gap, er 1.0 (as built, per the user)
- Wideband redesign study (`sim_wb_element.py`, `opt_wb_element.py`, `match_wb.py`, `wb_figures.py`): aperture-coupled stacked patch, single-pol, 40 runs. Best candidate `wbN4` VSWR<=3 4.95-5.75 GHz (15 %), no better than the present element; feed-layer matching cannot widen it. Findings and the plan for iteration 2 are in report sections 7 and 9
- Array model fixes (`sim_array.py`): port coordinates rounded to the mesh grid (port 2 injected no energy before), `--threads` / `--nrts` options
- Preliminary array S-parameters (`array_interim.py`) from the running full-array models: best mid-band (S22 mostly < -10 dB at ~5.2-6.2 GHz), VSWR >= 3 mostly below ~4.8 and above ~6.3 GHz, V/H coupling < -20 dB over most of the band
- PDF report (`02_openems/build_report.py`), 15 pages (measured section in 6), with "What can be done next" plan
- Client report for sharing: `04_docs/Telmart_CBand_Array_VSWR_Report.pdf` (`02_openems/client_report.py`, TM-RF-15-001 Rev. A, interim); issue Rev. B when the full-array runs finish
- Results-only client report (protects methods/IP): `04_docs/Telmart_CBand_Array_Results_Status.pdf` (`02_openems/client_results_report.py`, TM-RF-15-002 Rev. A)

- Measured panel data (`05_measured/`, `compare_measured.py`): S11 matches the simulated array character; gain 20.4 dBi peak vs 23 dBi rating, aperture efficiency 25-35 % mid-band and 3-8 % at 6.2-6.4 GHz (mismatch explains <= 1.5 dB of that)

- VSWR fix (element retune + matching section on each 100-ohm branch, same build): fix B gives VSWR <= 2 at ~5.17-6.17 GHz and VSWR <= 3 at ~5.05-6.25 GHz on both ports; fix A gives VSWR <= 3 at ~4.98-6.22 GHz. Figure `03_results/fix_vswr.png`

## Open items
- Option 3 (new wideband element) awaiting the user's go-ahead; options 1 and 2 closed (no improvement)
- Clarify with the user: V/H port mapping, S11 calibration plane, horn gain table, radome on/off during gain test, test range (indoor ~5 m), real spec band (4.9-6.4 GHz?) and gain target (23 dBi?)
- Full-array runs (`sim_array.py --port 1/2`): restarted 2026-10-30 in WSL on the local PC (6 + 10 threads); ~35-45 k steps each, several hours per port. Final results replace the preliminary curves in report section 6 (`python array_interim.py` gives an update at any time)
- Wideband element iteration 2: unit cell with periodic boundaries, dielectric-loaded patches, resonant dog-bone/H slots, dual-pol, ~150-250 evaluations (report section 9)
- Plan B element: L-probe / differential-probe patch or crossed dipole

## Resume here
Local (Windows + WSL Ubuntu): openEMS is in `/opt/openEMS` inside WSL, run folder `/root/p15` (copy of this project).
Array runs: `wsl -d Ubuntu -u root -- tail -1 /root/p15/02_openems/log_array_p1.txt` (and `_p2`). When both have finished:
`wsl -d Ubuntu -u root -- bash /root/pull.sh` (copies results back, see `02_openems/_pull_wsl.sh`), then in `02_openems`:
`python plot_results.py && python build_report.py`.
