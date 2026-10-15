# STEP models (AP242, mm)
Made with [SolidCraft](https://github.com/bherbruck/solidcraft) `solidcraft-cli` 0.11.1 by `02_python/build_step.py`, from the same geometry as the DXFs.

| File | Content |
|---|---|
| `RLSA_feed_assembly.step` | Al ground plate (SMA + 24 spacer holes), TLY-5 laminate with the 0.6 mm probe pocket, slotted top copper (1920 slots), probe pin + disc head |
| `HM1.step.zip`, `HM2.step.zip` | One metasurface each, in its own frame (input face at z = 0, x = phase-delay axis): bonded TLY-5 stack with Type II holes, rim holes, notch; copper M1–M4 |
| `NFMS_system_psi1_0_psi2_120.step.zip` | The full stack with HM I at ψ1 = 0° and HM II at ψ2 = 120° (beam θ 19.5°, φ 60°), plus nylon spacers |
| `STEP_report.txt` | volume and z-range of every part (checked against hand calculations) |
| `*.png` | SolidCraft renders |
| `*.solidcraft.json` | the SolidCraft command scripts (they read DXFs that `build_step.py` writes into `dxf_src/` during the build) |

- Other angles: `python build_step.py <psi1> <psi2>`.
- Copper is 17 µm. M2 and M3 copper overlaps the dielectric solid, because the paper ignores the prepreg. Give copper priority on import into HFSS or CST, or import the DXFs instead.
- Patches and spacers are separate bodies. CAD tools may take a minute to open the system file (about 12,800 bodies).
