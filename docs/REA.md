# REA: Reverse Engineer Anything

[REA](https://github.com/morluto/rea) (MIT, npm package `rea-agents`) is a CLI and MCP server that lets an agent
inspect software without its source code and report findings with evidence. It covers:
- native binaries, through Hopper, Ghidra or IDA;
- JavaScript and Electron apps, .NET assemblies and websites;
- ELF, PE, Mach-O, WASM and Go/Rust build metadata;
- firmware, Android APKs, model files (GGUF / safetensors) and more.

Use it on software you own or are licensed to analyse; see the upstream `DISCLAIMER.md`.

## Installed in this environment
| Item | Value |
|---|---|
| Node.js | 24.22.1 in `/opt/node24` (sha256-checked against nodejs.org); REA needs Node ≥ 22.23.4 and the container has 22.22.0 |
| REA | `rea` 6.7.0, installed with `npm install -g rea-agents@6.7.0` → `/opt/node24/bin/rea` |
| Install script | `tools/install_rea.sh` |
| Blocked by npm | `frida`'s install script (live runtime instrumentation only); static analysis does not need it |
| Test | `rea analyze-javascript-application <dir> --json` parsed an 82-file Electron app; `rea doctor` passes Node and host checks |
| Not available | native engines: Hopper, Ghidra and IDA are not installed, so native decompilation is unavailable until one is configured |

## Use
```bash
export PATH=/opt/node24/bin:$PATH
rea --help                                   # all commands
rea doctor                                   # what is ready
rea analyze-javascript-application /abs/path/to/app --json
rea analyze /abs/path/to/binary              # needs a native engine (e.g. Ghidra: set GHIDRA_INSTALL_DIR)
```

## Register with Claude Code (not done automatically)
```bash
rea setup --client claude_code --dry-run     # shows the plan
rea setup --client claude_code               # applies it
```
The plan has two steps:
1. Add `mcpServers.rea` (command `/opt/node24/bin/rea mcp`) to `~/.claude.json`, with a backup in
   `~/.claude.json.rea.backup`.
2. Install the skill `~/.claude/skills/reverse-engineer-anything`.

Restart Claude Code afterwards.

## Uninstall
```bash
/opt/node24/bin/npm uninstall -g rea-agents
rm -rf /opt/node24        # only if nothing else uses this Node
```
