# A_PD_MSL - 2-WAY POWER DIVIDER (MICROSTRIP) (RFE-PD-MSL-01)

| Item | Value |
|---|---|
| Board (ASSUMED until the layout is supplied) | 50.00 x 40.00 x 0.762 mm, RO4350B 0.762 mm (30 mil) |
| Band | 2.0-6.0 GHz |
| Outside | 60.20 x 50.20 x 18.42 mm (base 14.42 + lid 4.0) |
| Cavity | 50.20 x 40.20 mm, depth 9.00 mm from the wall top, floor 5.42 mm |
| Air above PCB | 8.2 mm (lid lip 1.5 mm, absorber recess 1.0 mm) |
| Connector axis | 6.850 mm above the base bottom (= PCB top + pin radius) |
| Ports | P1 IN on W wall at +0.0 mm; P2 on E wall at +10.0 mm; P3 on E wall at -10.0 mm |
| Lid screws | 18 x M2.5 x 8 ISO 7380 button head on d2.9 holes; max gap 12.60 mm (pitch target 12.49) |
| PCB screws | 8 x M2 x 4 ISO 4762 (4 corners + 2 per launch) |
| Connector screws | 12 x M2.5 x 5 ISO 4762 |
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
| floor thickness | 5.42 | >= 3.0 | OK |
| PCB screw thread in floor | 1.92 | >= 0.8 (blind) | OK |
| lid screw clear of the lid edge | 1.05 | >= 0.8 | OK |
| lid under absorber recess | 2.70 | >= 2.0 | OK |
| lid screw thread engagement | 4.00 | >= 1.4 d = 3.5 (light load; helicoil optional) | OK |
| lid screw hole bottom vs tap depth | 0.60 | >= 0.5 | OK |
| lid tap above the spigot bore | 0.84 | >= 0.8 | OK |
| largest lid-screw gap | 12.60 | <= lambda/4 at f_max = 12.5 (else conductive gasket) | OK |
| flange gap P2-P3 | 7.30 | >= 2 (spanner/fingers) | OK |
| flange inside box outline (P1 IN) | 18.75 | >= 0 | OK |
| flange inside box outline (P2) | 8.75 | >= 0 | OK |
| flange inside box outline (P3) | 8.75 | >= 0 | OK |

## Cavity resonances (air cavity 50.2 x 40.2 mm; PCB-loaded estimate eps_eff 1.066)

| Mode | Empty (GHz) | With PCB (GHz) | In band? |
|---|---|---|---|
| TE110-type | 4.78 | 4.63 | **YES** - fit absorber |
| TE210-type | 7.04 | 6.82 | no |
| TE120-type | 8.03 | 7.78 | no |
| TE220-type | 9.55 | 9.25 | no |
| TE310-type | 9.70 | 9.40 | no |
| TE130-type | 11.58 | 11.21 | no |

## Bodies in the assembly (SolidCraft)

| Part | Bodies | Volume (mm3) |
|---|---|---|
| BASE | 1 | 24556.2 |
| PCB_RFE-PD-MSL-01 | 1 | 1495.5 |
| TRACE_P1 | 1 | 0.4 |
| TRACE_P2 | 1 | 0.4 |
| TRACE_P3 | 1 | 0.4 |
| SP | 8 | 264.8 |
| LID | 1 | 10146.9 |
| SL | 18 | 1087.6 |
| J1_P1 | 1 | 456.2 |
| S | 12 | 714.4 |
| J2_P2 | 1 | 456.2 |
| J3_P3 | 1 | 456.2 |

Machined mass (Al 2.70 g/cm3): base 66.3 g, lid 27.4 g.

## Files

- `01_step/A_PD_MSL/RFE-PD-MSL-01_ASSY.solidcraft.json`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_ASSY.step`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_ASSY_EXPLODED.solidcraft.json`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_ASSY_EXPLODED.step`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_BASE.solidcraft.json`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_BASE.step`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_BOM.csv`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_LID.solidcraft.json`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_LID.step`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_exploded.png`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_iso.png`
- `01_step/A_PD_MSL/RFE-PD-MSL-01_lid_top.png`
- `01_step/A_PD_MSL/dxf_src`
