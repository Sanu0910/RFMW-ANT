# KiCadRoutingTools — autorouter + placer for KiCad

[drandyhaas/KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools) — a fast,
grid-based **A\* autorouter** with a native Rust core (~10× faster than pure Python) plus a
**functional-group placer**, for KiCad 9/10 `.kicad_pcb` files. MIT-licensed. Usable as a KiCad
plugin or a CLI; it also ships Claude Code skills (`/plan-pcb-routing`, `/plan-pcb-placement`).

Installed here by `tools/install_krt.sh`:
- code at `/opt/KiCadRoutingTools`, Python venv at `/opt/krt-venv`
- Rust router `rust_router/grid_router.so` (built from source, v0.23.7)
- verified: routed the bundled `cap_chain` sample 4/4 nets, exit 0

## CLI flow (what we use for project 12)
```bash
V=/opt/krt-venv/bin/python; cd /opt/KiCadRoutingTools
# place by functional groups (6 scattered + 6 gathered seeds, route-judged)
$V py_placer/place_simple.py board.kicad_pcb 's{seed}.kicad_pcb' --groups groups.json --intent intent.json
# pour planes first, fan out fine-pitch parts, then route everything
$V py_router/route_planes.py placed.kicad_pcb poured.kicad_pcb --nets GND --plane-layers B.Cu
$V py_router/bga_fanout.py   poured.kicad_pcb -c U1 -o fanned.kicad_pcb --clearance 0.1
$V py_router/route.py        fanned.kicad_pcb routed.kicad_pcb --nets "*" \
      --power-nets GND --power-nets-widths 0.3
```

Key capabilities: multi-layer octilinear routing with auto vias, rip-up/reroute, differential
pairs with length/time matching, power-net widening + neck-down, plane pours and stitching,
board-edge/keep-out clearance, BGA/QFN fanout. Inputs it reads beside the board: `groups.json`
(ref → functional group) and a floor-plan `intent.json` / `*.design-brief.json` (which connectors
face which edge).

## Note on running it
It is third-party downloaded code. Run it from the venv with explicit file-path arguments (as
above); the auto-mode classifier may prompt before executing it the first time.
