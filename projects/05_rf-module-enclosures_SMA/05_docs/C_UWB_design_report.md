# C_UWB - UWB POWER DIVIDER (RFE-PD-UWB-01)

| Item | Value |
|---|---|
| Board (ASSUMED until the layout is supplied) | 50.00 x 45.00 x 0.508 mm, RO4003C 0.508 mm (20 mil) |
| Band | 3.1-10.6 GHz |
| Outside | 60.20 x 55.20 x 18.42 mm (base 14.42 + lid 4.0) |
| Cavity | 50.20 x 45.20 mm, depth 8.74 mm from the wall top, floor 5.68 mm |
| Air above PCB | 8.2 mm (lid lip 1.5 mm, absorber recess 1.0 mm) |
| Connector axis | 6.850 mm above the base bottom (= PCB top + pin radius) |
| Ports | P1 IN on W wall at +0.0 mm; P2 on E wall at +12.0 mm; P3 on E wall at -12.0 mm |
| Lid screws | 27 x M2.5 x 8 ISO 7380 button head on d2.9 holes; max gap 13.10 mm (pitch target 7.07) |
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
| floor thickness | 5.68 | >= 3.0 | OK |
| PCB screw thread in floor | 2.18 | >= 0.8 (blind) | OK |
| lid screw clear of the lid edge | 1.05 | >= 0.8 | OK |
| lid under absorber recess | 2.70 | >= 2.0 | OK |
| lid screw thread engagement | 4.00 | >= 1.4 d = 3.5 (light load; helicoil optional) | OK |
| lid screw hole bottom vs tap depth | 0.60 | >= 0.5 | OK |
| lid tap above the spigot bore | 0.84 | >= 0.8 | OK |
| largest lid-screw gap | 13.10 | <= lambda/4 at f_max = 7.1 (else conductive gasket) | **WARN** |
| flange gap P2-P3 | 11.30 | >= 2 (spanner/fingers) | OK |
| flange inside box outline (P1 IN) | 21.25 | >= 0 | OK |
| flange inside box outline (P2) | 9.25 | >= 0 | OK |
| flange inside box outline (P3) | 9.25 | >= 0 | OK |

## Cavity resonances (air cavity 50.2 x 45.2 mm; PCB-loaded estimate eps_eff 1.044)

| Mode | Empty (GHz) | With PCB (GHz) | In band? |
|---|---|---|---|
| TE110-type | 4.46 | 4.37 | **YES** - fit absorber |
| TE210-type | 6.83 | 6.69 | **YES** - fit absorber |
| TE120-type | 7.27 | 7.12 | **YES** - fit absorber |
| TE220-type | 8.92 | 8.74 | **YES** - fit absorber |
| TE310-type | 9.55 | 9.35 | **YES** - fit absorber |
| TE130-type | 10.39 | 10.17 | **YES** - fit absorber |

## Bodies in the assembly (SolidCraft)

| Part | Bodies | Volume (mm3) |
|---|---|---|
| BASE | 1 | 27077.5 |
| PCB_RFE-PD-UWB-01 | 1 | 1124.0 |
| TRACE_P1 | 1 | 0.3 |
| TRACE_P2 | 1 | 0.3 |
| TRACE_P3 | 1 | 0.3 |
| SP | 8 | 264.8 |
| LID | 1 | 10905.3 |
| SL | 27 | 1631.4 |
| J1_P1 | 1 | 456.2 |
| S | 12 | 714.4 |
| J2_P2 | 1 | 456.2 |
| J3_P3 | 1 | 456.2 |

Machined mass (Al 2.70 g/cm3): base 73.1 g, lid 29.4 g.

## Files

- `01_step/C_UWB/RFE-PD-UWB-01_ASSY.solidcraft.json`
- `01_step/C_UWB/RFE-PD-UWB-01_ASSY.step`
- `01_step/C_UWB/RFE-PD-UWB-01_ASSY_EXPLODED.solidcraft.json`
- `01_step/C_UWB/RFE-PD-UWB-01_ASSY_EXPLODED.step`
- `01_step/C_UWB/RFE-PD-UWB-01_BASE.solidcraft.json`
- `01_step/C_UWB/RFE-PD-UWB-01_BASE.step`
- `01_step/C_UWB/RFE-PD-UWB-01_BOM.csv`
- `01_step/C_UWB/RFE-PD-UWB-01_LID.solidcraft.json`
- `01_step/C_UWB/RFE-PD-UWB-01_LID.step`
- `01_step/C_UWB/RFE-PD-UWB-01_exploded.png`
- `01_step/C_UWB/RFE-PD-UWB-01_iso.png`
- `01_step/C_UWB/RFE-PD-UWB-01_lid_top.png`
- `01_step/C_UWB/dxf_src`
