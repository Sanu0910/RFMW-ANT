# Status: 09_aeris10-plfm-radar_study

_Last updated: 2026-10-29. Update this file whenever the project changes (see `docs/CONVENTIONS.md`)._

**State:** Study complete (notes + derived numbers). Read-only upstream snapshot; nothing built.

## Done
- `LEARNING_NOTES.md`: system, waveform, FPGA chain, firmware, GUI, antennas, findings
- `analysis/aeris10_numbers.py` recomputes range resolution, blind zones, PRF, Doppler, scan time, gain
- Upstream snapshot at commit `62d4c55` (datasheets, bitstreams and large media left out)

## Open items
- Upstream is alpha and not hardware-validated
- Transmitting needs a licence and RF-safety precautions

## Next step
None planned. Reuse techniques listed in `LEARNING_NOTES.md` in other projects.

## Resume here
`LEARNING_NOTES.md`.

## Tools needed
Python (numpy) for `analysis/`.

History: see `CHANGELOG.md`.
