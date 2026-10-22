# Full-wave unit-slot check (Hertzon / EMerge)

`slot_unit_cell.py` models one inclined narrow-wall slot:
- straight WR15, a × b = 3.76 × 1.88 mm, wall 0.2 mm;
- slot 0.261 mm wide, cut into both broad walls to depth d;
- two wave ports;
- an air box with a first-order absorbing boundary.

The radiated fraction P_rad = 1 − |S11|² − |S21|² is converted to a normalised shunt conductance with
P_rad = 4g/(2+g)². Solver settings: adaptive mesh at 60.75 GHz, ΔS ≤ 0.002, initial edge length 0.8 mm.
Each case converged in 3–5 passes with 33k–55k tetrahedra and took about 1–2 min on 4 cores.

| tilt | depth | g @ 58 GHz | g @ 60.75 GHz | g @ 63.5 GHz | paper Fig. 4 |
|---|---|---|---|---|---|
| 10° | 0.38 mm | 0.011 | 0.0067 | 0.0043 | ≈ 0.018 |
| 20° | 0.29 mm | 0.059 | 0.035 | 0.021 | ≈ 0.075 |
| 30° | 0.20 mm | 0.150 | 0.083 | 0.047 | ≈ 0.16 |

Mesh check, 10° slot at 60.75 GHz:

| Tetrahedra | P_rad |
|---|---|
| 5.5k | 0.0062 |
| 33k | 0.0067 |
| 75k | 0.0067 |

## Interpretation
- **Reproduced:** conductance rises steeply with tilt, roughly as sin²θ, and S11 stays small. This is why the paper
  can set the taper with the tilt alone.
- **Lower than the paper:** at 60.75 GHz the values are about 0.4–0.5× the paper's. At 58 GHz they come within
  20–35 % for the 20° and 30° slots. Our slot radiates most strongly below the band, so its resonance sits lower
  than in the paper's cell.
- **Likely reasons:**
  - The paper does not state the exact definition of slot depth or the frequency of its Fig. 4.
  - Our cell has open air beside the broad walls, where the real antenna has a 0.1 mm gap and a neighbouring leg.
  - The paper's CST cell probably included the neighbouring legs (mutual coupling, eq. 5).
- **For a build:** use this script to re-tune the depths, or tilts, until each slot reaches its g_n
  (Table I, or the ×1.5 radiation boost of Table II) at the centre frequency. Then simulate the complete antenna
  (`01_cad/lwa_air.step`) on a workstation with 32–64 GB of RAM.
