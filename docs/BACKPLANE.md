# Backplane: agentic hardware-development workspace

[Backplane](https://github.com/i2cjak/Backplane) (MIT) is a desktop and web workspace for AI-assisted electronics and
mechanical design:
- KiCad and FreeCAD viewers that show every step the agent takes;
- clickable components and pads that you can reference in the chat ("workbar");
- a [KiCad fork](https://github.com/i2cjak/Backplane_KiCad) with extra IPC instrumentation, including a
  schematic API;
- multi-agent orchestration: projects, threads, bots and an "uberbot";
- persistent bots with webhooks, a mailbox and a small web-app space.

It works with Claude Code, Codex, Grok, OpenCode and others.

## Installed in this environment
| Item | Value |
|---|---|
| Version | v0.10.0 (linux-x64), installed by `tools/install_backplane.sh`, i.e. the upstream sha256-checked installer |
| Files | `~/.local/share/backplane/` (backplane, backplane-serve, backplane-browser, backplane-step2glb, backplane-voice, web/), about 300 MB |
| Commands | `~/.local/bin/backplane`, `~/.local/bin/backplane-serve` |
| State | `~/.backplane-bend/`; model cache in `~/.cache/backplane-bend/` |
| Test | `backplane --headless` started the hub; the web UI answered on http://127.0.0.1:3787 with HTTP 200 and showed the project list |

This cloud container has no display, so only the headless hub / web UI runs here. On a desktop, plain `backplane`
opens the window.

## Use
```bash
BACKPLANE_NO_UPDATE=1 BACKPLANE_TELEMETRY=0 ~/.local/bin/backplane --headless   # then open http://127.0.0.1:3787
```

Requirements:
- at least one agent CLI (`claude` is installed here);
- KiCad (KiCad 9 is in `/opt/kicad9`, see `docs/KICAD_MCP.md`), for the PCB and schematic features. Backplane's own
  KiCad fork can be set up from its Settings;
- FreeCAD, for mechanical work.

Settings worth knowing:
- `BACKPLANE_NO_UPDATE=1` stops the automatic self-update.
- `BACKPLANE_TELEMETRY=0` or `DO_NOT_TRACK=1` turns off the anonymous usage telemetry.
- `BACKPLANE_NO_DESKTOP=1` skips the application-menu entry.

## Security notes (from the upstream docs)
- Pairing links and QR codes are credentials.
- "Full Access" threads run agent tools with your user's rights, so choose a more restrictive thread permission mode
  for untrusted work.

## Uninstall
```bash
rm -rf ~/.local/share/backplane ~/.local/bin/backplane ~/.local/bin/backplane-serve
rm -rf ~/.backplane-bend ~/.cache/backplane-bend        # threads, settings, keys, cache
```
