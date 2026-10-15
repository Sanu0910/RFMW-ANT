# B_MSL_SL - MSL TO STRIPLINE TRANSITION (RFE-TR-MSLSL-01)

| Item | Value |
|---|---|
| Board (ASSUMED until the layout is supplied) | 60.00 x 30.00 x 1.524 mm, 2 x RO4350B 0.762 bonded (stripline inner layer) |
| Band | 0.5-12.0 GHz |
| Outside | 70.20 x 40.20 x 18.42 mm (base 14.42 + lid 4.0) |
| Cavity | 60.20 x 30.20 mm, depth 9.76 mm from the wall top, floor 4.66 mm |
| Air above PCB | 8.2 mm (lid lip 1.5 mm, absorber recess 1.0 mm) |
| Connector axis | 6.850 mm above the base bottom (= PCB top + pin radius) |
| Ports | P1 on W wall at +0.0 mm; P2 on E wall at +0.0 mm |
| Lid screws | 28 x M2.5 x 8 ISO 7380 button head on d2.9 holes; max gap 10.23 mm (pitch target 7.00) |
| PCB screws | 8 x M2 x 4 ISO 4762 (4 corners + 2 per launch) |
| Connector screws | 8 x M2.5 x 5 ISO 4762 |
| Mounting | 4 x M3 tapped 6 deep in the bottom |

## Design checks

| Check | Value (mm) | Rule | Result |
|---|---|---|---|
| flange bottom above box bottom | 0.50 | >= 0.50 | OK |
| flange top below lid top | 5.22 | >= 0 | OK |
| upper flange thread below lid seat | 2.00 | >= 0.5 | OK |
| lower flange thread above box bottom | 1.28 | >= 0.5 | OK |
| spigot length vs wall | 0.09 | 0 .. 0.2 (spigot reaches the cavity) | OK |
| pin length lying on the trace | 2.91 | >= 2.0 | OK |
| pin axis above trace (pin resting on copper) | 0.63 | = pin radius 0.63 | OK |
| floor thickness | 4.66 | >= 3.0 | OK |
| PCB screw thread in floor | 1.16 | >= 0.8 (blind) | OK |
| lid screw clear of the lid edge | 1.05 | >= 0.8 | OK |
| lid under absorber recess | 2.70 | >= 2.0 | OK |
| lid screw thread engagement | 4.00 | >= 1.4 d = 3.5 (light load; helicoil optional) | OK |
| lid screw hole bottom vs tap depth | 0.60 | >= 0.5 | OK |
| lid tap above the spigot bore | 0.84 | >= 0.8 | OK |
| largest lid-screw gap | 10.23 | <= lambda/4 at f_max = 6.2 (else conductive gasket) | **WARN** |
| flange inside box outline (P1) | 13.75 | >= 0 | OK |
| flange inside box outline (P2) | 13.75 | >= 0 | OK |

## Cavity resonances (air cavity 60.2 x 30.2 mm; PCB-loaded estimate eps_eff 1.129)

| Mode | Empty (GHz) | With PCB (GHz) | In band? |
|---|---|---|---|
| TE110-type | 5.55 | 5.23 | **YES** - fit absorber |
| TE210-type | 7.03 | 6.62 | **YES** - fit absorber |
| TE310-type | 8.97 | 8.44 | **YES** - fit absorber |
| TE120-type | 10.23 | 9.63 | **YES** - fit absorber |
| TE220-type | 11.11 | 10.45 | **YES** - fit absorber |
| TE410-type | 11.13 | 10.48 | **YES** - fit absorber |

## Bodies in the assembly (SolidCraft)

| Part | Bodies | Volume (mm3) |
|---|---|---|
| BASE | 1 | 22060.5 |
| PCB_RFE-TR-MSLSL-01 | 1 | 2686.2 |
| TRACE_P1 | 1 | 0.4 |
| TRACE_P2 | 1 | 0.4 |
| SP | 8 | 264.8 |
| LID | 1 | 9289.1 |
| SL | 28 | 1691.8 |
| J1_P1 | 1 | 456.2 |
| S | 8 | 476.3 |
| J2_P2 | 1 | 456.2 |

Machined mass (Al 2.70 g/cm3): base 59.6 g, lid 25.1 g.

## Files

- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_ASSY.solidcraft.json`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_ASSY.step`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_ASSY_EXPLODED.solidcraft.json`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_ASSY_EXPLODED.step`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_BASE.solidcraft.json`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_BASE.step`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_BOM.csv`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_LID.solidcraft.json`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_LID.step`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_exploded.png`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_iso.png`
- `01_step/B_MSL_SL/RFE-TR-MSLSL-01_lid_top.png`
- `01_step/B_MSL_SL/dxf_src`
