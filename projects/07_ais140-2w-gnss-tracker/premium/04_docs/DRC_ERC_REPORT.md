# DRC / ERC report (KiCad 9.0.9 kicad-cli)

| Check | Result |
|---|---|
| ERC (schematic) | 0 violations |
| DRC errors | 0 |
| Unconnected items | 0 |
| Schematic parity (PCB vs schematic) | 0 issues |

Remaining **warnings** (no fabrication impact):

| Type | Count | Note |
|---|---|---|
| silk_over_copper | 10 | reference text of bottom test pads / IC outline over copper - clipped by the fab |
| silk_overlap | 11 | dense bottom side; designators are on the fab layers (assembly drawings) |
| track_dangling | 3 | short stubs reported by the connectivity checker; removing them breaks a connection, so they are kept |
| via_dangling | 1 | one ALERT_N via flagged as stub (connected track chain), harmless |

Raw report: run `kicad-cli pcb drc --schematic-parity 01_kicad/tracker.kicad_pcb`.
