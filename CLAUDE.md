# RFMW-ANT: instructions for Claude Code

RF / microwave antenna design projects: one folder per project under `projects/NN_name/`.

## Setup
- Local machine: see `LOCAL_SETUP.md`. Tools install with `bash tools/setup_local.sh`; check them with
  `python3 tools/doctor.py` (also checks the MCP servers in `.mcp.json`: solidcraft, kicad, hertzon).
- Cloud container: tools are not preinstalled; reinstall what a task needs with the `tools/install_*.sh` scripts
  (root `STATUS.md` lists them).
- Python: project scripts use `.venv/bin/python` (local) or the system python; openEMS scripts use
  `/opt/openEMS/venv/bin/python`.

## Rules
- Follow `docs/CONVENTIONS.md`: units mm/GHz, DXF layer names, `[ASSUMED]` values, builders regenerate every output.
- New project: next free number `NN`, folder `projects/NN_short-name/` with `00_README.md`, `STATUS.md`,
  `CHANGELOG.md`, and a row in the root `README.md` and root `STATUS.md` tables.
- Update the project's `STATUS.md` and `CHANGELOG.md` in the same commit as any change.
- Never commit raw solver output (`sim/` folders), virtualenvs or files over 50 MB (zip large STEP files).

## When the user says a project is done / "push it"
1. Re-run the project's builder scripts so outputs match the code.
2. Update the project's `STATUS.md` (state, `Last updated`) and `CHANGELOG.md`, and the root `README.md` / `STATUS.md` rows.
3. Run `bash tools/finish_project.sh projects/NN_name "short summary"`. It checks the above, commits only that
   project and the root tables, and pushes the current branch.
4. Report the commit hash and branch. Do not open a pull request unless the user asks for one.
