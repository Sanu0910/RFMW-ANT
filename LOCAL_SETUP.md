# Running RFMW-ANT on your own computer

This guide takes you from an empty machine to a working copy of the repository with every tool and MCP server
running, and explains how to send finished projects back to GitHub.

| Step | What | Time |
|---|---|---|
| 1 | Get a supported machine (Ubuntu 22.04/24.04, or Windows with WSL2) | 10 min |
| 2 | Clone the repository | 1 min |
| 3 | Run `tools/setup_local.sh` (installs everything) | 30–45 min, mostly the openEMS build |
| 4 | Log in to GitHub (`gh auth login`) | 2 min |
| 5 | Check with `tools/doctor.py` | 2 min |
| 6 | Work with Claude Code: `claude` in the repo folder | — |
| 7 | When a project is done: "push project NN" | 1 min |

---

## 1. Machine

The install scripts target **Ubuntu 22.04 or 24.04 on x86-64**, the same as the cloud sessions.

| You have | Do this |
|---|---|
| Ubuntu 22.04 / 24.04 | Nothing extra. |
| Windows 10/11 | Install WSL2 with Ubuntu 24.04: in PowerShell (admin) run `wsl --install -d Ubuntu-24.04`, reboot, open "Ubuntu". Do **everything below inside Ubuntu**, and keep the repository in the Linux home (`~/RFMW-ANT`), not under `/mnt/c` (much faster). GUI apps (KiCad, SolidCraft, Hertzon) open through WSLg. |
| macOS | The scripts do not support macOS. Run Ubuntu 24.04 in a VM (UTM, Parallels) or use the cloud sessions. |

You need about **15 GB free disk** and **8 GB RAM** (16 GB for full-array openEMS runs).

## 2. Clone

```bash
cd ~
git clone https://github.com/Sanu0910/RFMW-ANT.git
cd RFMW-ANT
```

Cloud sessions push their work to `claude/...` branches, not to `main`. If a cloud project is not on `main` yet, merge
its pull request on GitHub, or merge the branch locally:

```bash
git fetch origin
git branch -r                                   # lists e.g. origin/claude/eager-euler-x3csl7
git merge origin/claude/eager-euler-x3csl7      # brings that work into your current branch
```

## 3. Install everything

```bash
bash tools/setup_local.sh
```

It asks for your sudo password once and is safe to run again (it skips what is already installed).
At the end it runs the check from step 5.

| Installs | Where | Used for |
|---|---|---|
| git, build tools, Python 3, Qt/GL libs, GitHub CLI `gh` | apt | everything |
| Node.js ≥ 18 | apt / NodeSource | MCP servers, Claude Code, PDF reports |
| Claude Code CLI (`claude`) | npm global | the assistant |
| Python venv with `docs/requirements.txt` + scikit-rf | `./.venv` | project scripts (`build_*.py`, models) |
| openEMS v0.37 + CSXCAD (+ ezdxf, shapely) | `/opt/openEMS` | FDTD simulations (project 15 etc.) |
| KiCad 9 (official PPA) | system | PCB projects 07, 12, 13 |
| KiCAD-MCP-Server + venv over KiCad's `pcbnew` | `/opt/KiCAD-MCP-Server` | **kicad** MCP server |
| SolidCraft (`solidcraft-cli`, .deb from GitHub releases) | system | STEP models, **solidcraft** MCP server |
| Hertzon (EMerge FEM) | `/opt/hertzon-venv` | FEM checks, **hertzon** MCP server |
| gds2openEMS, KiCadRoutingTools, Playwright Chromium, GNU Octave | various | optional extras |

Skip parts you do not need, for example on a small laptop:

```bash
SKIP_OPENEMS=1 SKIP_HERTZON=1 bash tools/setup_local.sh
```

Variables: `SKIP_APT SKIP_NODE SKIP_CLAUDE SKIP_PYTHON SKIP_OPENEMS SKIP_KICAD SKIP_SOLIDCRAFT SKIP_HERTZON SKIP_EXTRAS`.

Not installable locally without a licence: **Ansys HFSS** (the `hfss_*.py` PyAEDT scripts need AEDT 2024.x) and
**MATLAB** (use GNU Octave for the `.m` files).

## 4. GitHub login and git identity (needed to push)

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"     # the e-mail of your GitHub account
gh auth login            # GitHub.com -> HTTPS -> Login with a web browser
gh auth setup-git        # lets plain `git push` use that login
```

## 5. Check that everything runs

```bash
python3 tools/doctor.py
```

It checks every tool and starts each MCP server from `.mcp.json` exactly as Claude Code does, asking it for its tool
list. A good result looks like:

```
MCP servers (.mcp.json)
  OK   solidcraft                   19 tools
  OK   kicad                        244 tools
  OK   hertzon                      33 tools
All required checks passed.
```

`WARN` lines are optional tools. Anything marked `FAIL` is explained in the troubleshooting section below.

## 6. Working with Claude Code

```bash
cd ~/RFMW-ANT
claude
```

- The MCP servers are registered **for this repository** in `.mcp.json` and pre-approved in `.claude/settings.json`,
  so they connect automatically when `claude` starts in this folder. Type `/mcp` inside Claude Code to see them.
- `.mcp.json` launches KiCad and Hertzon through `tools/mcp/kicad.sh` and `tools/mcp/hertzon.sh`. These find the
  local installs, so the same file works on your PC and in cloud sessions.
- **kicad-pro** ([kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro)) runs with `uvx kicad-mcp-pro` in
  write mode with the `full` profile (289 tools). It needs `uv` (`pip install uv`, or `winget install astral-sh.uv` on Windows) and finds `kicad-cli`
  by itself (set `KICAD_CLI_PATH` if not). It also works on native Windows with KiCad 9/10. For live board
  context, start KiCad, enable the IPC API server (Preferences > Plugins) and open the board.
- The SolidCraft skills in `.claude/skills/` load automatically.
- `CLAUDE.md` tells Claude Code the repository rules (conventions, status files, how to push).

Running things by hand:

```bash
source .venv/bin/activate                         # project Python scripts
cd projects/03_1bit-rba-mmwave-1x5_AWPL2026/02_python && python rba_array.py

source /opt/openEMS/venv/bin/activate             # openEMS simulations
cd projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems && python sim_element.py

kicad projects/13_bathroom-presence-sensor-switch/...   # KiCad GUI
/opt/hertzon-venv/bin/hertzon                     # Hertzon GUI
```

## 7. When a project is finished: push it to GitHub

Tell Claude Code, for example: **"project 15 is done, push it"**. It follows this checklist (also in `CLAUDE.md`), and
you can run the same steps yourself:

1. **Regenerate** outputs with the project's builder scripts (`build_*.py`, `build_report.py`, ...) so DXFs, PDFs and
   CSVs match the code.
2. **Update the status files** (see `docs/CONVENTIONS.md`):
   - `projects/NN_*/STATUS.md`: state, done, open items, next step, `Last updated` date
   - `projects/NN_*/CHANGELOG.md`: a dated entry at the top
   - root `README.md` project table and root `STATUS.md` project table: add or update the row
3. **No huge files**: GitHub rejects files over 100 MB. Raw solver output (`sim/` folders, `.venv/`) is already in
   `.gitignore`. Zip big STEP files (>20 MB) as the other projects do.
4. **Commit and push** with the helper. It checks steps 2–3, commits only that project plus the root tables, and
   pushes the current branch:

   ```bash
   bash tools/finish_project.sh projects/15_cband-6x6-dualpol-stacked-patch_match-debug "S11 analysis report"
   ```

   Or by hand:

   ```bash
   git add projects/15_cband-6x6-dualpol-stacked-patch_match-debug README.md STATUS.md
   git commit -m "proj15: S11 analysis report"
   git push
   ```

5. **Branches**: working directly on `main` is fine for a single-person repository. If you prefer review first, use a
   branch (`git switch -c proj15-report`), push it, and open a pull request on GitHub (`gh pr create --fill`).

Getting changes made in a cloud session: `git pull` (same branch) or `git fetch origin && git merge origin/<branch>`.
Always `git pull` before you start work if you also use cloud sessions, so the two copies do not diverge.

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `doctor.py`: **kicad FAIL**, "dist/index.js not found" | `SKIP_APT=1 SKIP_NODE=1 SKIP_CLAUDE=1 SKIP_PYTHON=1 SKIP_OPENEMS=1 SKIP_SOLIDCRAFT=1 SKIP_HERTZON=1 SKIP_EXTRAS=1 bash tools/setup_local.sh` (re-runs only the KiCad step) |
| kicad MCP starts but tools fail with `No module named pcbnew` | KiCad not from the PPA. Check `/usr/bin/python3 -c "import pcbnew"`. Then delete `/opt/KiCAD-MCP-Server/venv` and re-run the KiCad step. |
| **solidcraft FAIL**, `solidcraft-cli` not found | Download the Linux `.deb` from https://github.com/bherbruck/solidcraft/releases and run `sudo apt install ./solidcraft_*.deb` |
| **hertzon FAIL** | Re-run `bash tools/install_hertzon.sh` with `PYTHON=python3`, then `sudo chown -R $USER /opt/hertzon-venv` |
| MCP servers missing in `/mcp` | Start `claude` from the repository root. If it asked to approve project MCP servers and you declined, run `claude mcp reset-project-choices`. |
| openEMS build fails | Re-run `sudo bash tools/install_openems.sh`. It needs the apt packages from step 3 (`libvtk9-dev`, `libhdf5-dev`, `libcgal-dev`, ...). |
| `build_report.py`: "Cannot find module 'playwright'" | `sudo npm install -g playwright && sudo npx playwright install --with-deps chromium` |
| `git push` asks for a password, or 403 | `gh auth login && gh auth setup-git` |
| Push rejected (non-fast-forward) | `git pull --rebase` (or `git pull`), then push again |
| Disk full during openEMS runs | Delete the `sim/` folders of finished runs. Their results are in `03_results`. |
| WSL is slow | Keep the repo in `~/`, not `/mnt/c/...` |

## 9. What is where

| Path | What |
|---|---|
| `projects/NN_*/` | one folder per project: `00_README.md`, `STATUS.md`, `CHANGELOG.md`, code, outputs |
| `docs/` | conventions, tool notes (openEMS, Hertzon, KiCad MCP, ...), Python requirements |
| `tools/setup_local.sh` | the local installer |
| `tools/doctor.py` | tool + MCP check |
| `tools/finish_project.sh` | commit-and-push helper |
| `tools/mcp/` | MCP launchers used by `.mcp.json` |
| `tools/install_*.sh` | single-tool installers (also used in cloud sessions) |
| `.mcp.json`, `.claude/` | MCP servers, Claude Code settings and skills for this repo |
| `CLAUDE.md` | rules Claude Code follows in this repo |
