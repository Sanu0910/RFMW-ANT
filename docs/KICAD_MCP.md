# KiCad 9 + KiCAD-MCP-Server (headless)

`sudo bash tools/install_kicad_mcp.sh` installs KiCad 9.0.9 (official `kicad/kicad:9.0` image unpacked to
`/opt/kicad9`, no Docker daemon, no PPA) and [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)
2.8.2 in `/opt/KiCAD-MCP-Server`. KiCad's Python runs through `tools/kicad-python-chroot.sh`, which the
server uses as `KICAD_PYTHON`; `/home/user` is bind-mounted at the same path, so project paths are identical
inside and outside.

Verified: MCP `initialize`, `tools/list` (244 tools), `open_project` and `get_board_info` on
`projects/07_ais140-2w-gnss-tracker`. Real-time IPC (live KiCad GUI) is not available headless — the server
uses the SWIG backend on files.

Register it:

```bash
claude mcp add kicad -e KICAD_PYTHON=/opt/KiCAD-MCP-Server/kicad-python-chroot.sh -- node /opt/KiCAD-MCP-Server/dist/index.js
```

The same image also gives `kicad-cli` (ERC, DRC, Gerbers, STEP, renders) used by project 07:
`chroot /opt/kicad9 kicad-cli ...`. Cloud containers are ephemeral — re-run the install script in a new session.
