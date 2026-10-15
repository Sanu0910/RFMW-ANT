# Paper Summary: Network-Based Design of Reactive Beamforming Metasurfaces
M. Almunif, F. Alsolamy, A. Grbic, *IEEE Trans. Antennas Propag.*, vol. 73, no. 8, Aug. 2025.

## Problem
Classical metasurface design uses the **local periodicity approximation**: each cell is designed as if it sat in an infinite array of identical cells. That ignores coupling between unlike neighbours, cannot control amplitude, and breaks down for strong field transformations.

## Idea
Treat the whole surface as a **multiport microwave network**, one port per cell, with a reactive load behind each port.
- One full-wave run of the 11×11 board (121 lumped ports) gives the impedance matrix Z and each port's element pattern.
- After that, the design is circuit algebra plus optimisation. No more full-wave runs are needed until verification.

## Design flow (eq. numbers from the paper)
1. Partition Z into loaded (L) and excited (E) ports (eq. 1).
2. Choose a desired far field: array factor × element pattern (eqs. 21–24).
3. Project onto the element patterns, giving a Gram-matrix system for the port currents (eqs. 6–8).
4. Convert the currents to the complex loads that force them (eq. 5).
5. Drop the real part (it would be loss or gain); the imaginary part becomes the seed.
6. Optimise the reactances (fmincon) on pattern error + Σ|S_ii| + Σ|S_ij| (eq. 11), using the reduced S-matrix at the feeds (eqs. 12–14).
7. Reflective mode: drive with open-circuit voltages from a plane wave (eqs. 15–20).
8. Realise each reactance as a **meandered open-circuit microstrip stub** (Sec. VII, Fig. 10).

## Hardware
- Cell: 5.7 mm (λ0/5 at 10 GHz), 3 metal layers on RO4003C (0.813 + 0.203 mm).
- Layers: patch (L1), slotted ground (L2), microstrip + shorting via + port (L3).
- The ground isolates the loads, so the **same board** works as a directly fed antenna or as a reflector.

## Results
| Design | Result |
|---|---|
| I: beam to −30° | S11 −14 dB; realised version directivity 16.1 dB, gain 14 dB, efficiency 62.5% |
| II | Flat-top beam |
| III | MIMO ±28.5° beams with −30 dB isolation |
| IV / V | Reflective beam splitter (efficiency 75%) and two-wave reflector |

## Our verification and contributions (this folder)
- Fig. 3 geometry re-read at 600 dpi. The cell is centred on the patch cross-gap and the slot straddles the cell edge; an earlier draft had this wrong.
- Reactances digitised from Figs. 4a, 6a, 7a, 8b and 9b (±3 Ω).
- **Fig. 11 and Fig. 12 rebuilt** as meander DXFs; all five designs built and DRC-checked.
- MATLAB pipeline for eqs. 1–25 with analytic gradients, checked in Octave:
  - power consistency 5e-5
  - gradient vs finite difference 1e-9
- Items the paper leaves out: HFSS embedded patterns are 50 Ω-terminated and must be converted to the open-circuit current basis; the Gram matrix is ill-conditioned; the optimisation is multimodal; meander Zin must be extracted in-situ.

See `06_docs/DESIGN_GUIDE.pdf` for the full designer guide.
