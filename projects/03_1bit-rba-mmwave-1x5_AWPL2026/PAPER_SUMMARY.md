# Paper Summary: Compact Low-Cost 1-Bit Reconfigurable Wide Beam-Steering mm-Wave Array for Mobile Terminals
J. Jiao, Y. Wang, F. Xu, *IEEE Antennas Wireless Propag. Lett.*, vol. 25, no. 6, Jun. 2026, DOI 10.1109/LAWP.2026.3686232.

## Problem
Phones need wide-angle mm-wave beam steering in a tiny volume and at low cost. A phase shifter per element is expensive. A 1-bit array (0/180° per element) is cheap, but its periodic quantisation error creates grating (mirror) lobes.

## Idea
1. **Compact element (RCSPA).** A patch is coupled to a shorted quarter-wave patch and fed through a ground slot. It is small (2.4 × 3.1 mm) and has an almost hemispherical E-plane, which is what allows wide scanning.
2. **1-bit switch.** Two PIN diodes (MA4AGFCP910) select which end of a U-loop under the slot is fed, reversing the slot current. This gives 0° or −180°, frequency-independent, set by one bias voltage per element (+V or −V).
3. **Small spacing.** D = 4.5 mm (0.398λ0 at 26.5 GHz), five elements.
4. **Fixed-phase preloading.** Constant offsets per element (55.78, −5.79, −73.37, 0, −111.72°, found by PSO) are built into the 1:5 divider line lengths. They de-correlate the quantisation error and remove the mirror lobe.

## Results
- 25–29 GHz with 7 beams.
- Measured: 9.23 dBi peak, steering −57° to +55°, SLL < −4.64 dB, XPL < −13.5 dB.
- Simulated: scan loss < 3.5 dB.

## Our verification and contributions (this folder)
- **Beam table:** with the element E-plane fitted to Fig. 3a, the model reproduces all 7 beams within about 3° of the paper. Sidelobes match within about 2 dB except at ±60°, where the model gives −3.5 to −3.8 dB against the paper's −4.7 to −5 dB (mutual coupling, not captured).
- **Why the preload matters:** without it every steered beam has a 0 dB mirror lobe.
- **Why the shorted patch matters:** a normal patch (narrow E-plane) limits scanning to about 46°.
- **PSO is not unique:** our own PSO finds a different preload set that also meets −5 dB SLL.
- **Beam squint:** the +60° code moves from 57° to 48.5° across 25–29 GHz.
- **Tolerance:** about 10° rms preload error (≈ 0.19 mm of line) costs about 0.6 dB of SLL.
- **Paper inconsistencies:** D = 0.375λ0 is exact only at 25 GHz; the two quoted array sizes disagree; w1 is missing; the loop dimensions are ambiguous.
- **Divider check:** the reconstructed 1:5 divider reproduces the paper's line widths from first principles (0.2 / 0.33 / 0.44 mm), and its serpentines realise the preload exactly in the model.
- **Deliverables:** DXFs with silkscreen and assembly (element, 5-port array, array + divider, split boards), Python and MATLAB models (identical), PyAEDT build script with per-diode state variables, and the guide.

See `05_docs/DESIGN_GUIDE.pdf`.
