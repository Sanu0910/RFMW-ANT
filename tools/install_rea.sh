#!/usr/bin/env bash
# Install REA - Reverse Engineer Anything (https://github.com/morluto/rea, MIT; npm package rea-agents).
# REA needs Node.js 22.23.4+ / 24.22.1+, newer than the container's Node 22.22, so a checksum-verified Node 24 goes
# to /opt/node24 first. The CLI is installed with npm (`rea`). Registering REA as an MCP server is left to
# `rea setup`: it edits ~/.claude.json, so run it yourself.
set -euo pipefail
NODE_DIR=${NODE_DIR:-/opt/node24}
REA_VERSION=${REA_VERSION:-6.7.0}
if ! "$NODE_DIR/bin/node" --version 2>/dev/null | grep -q '^v24'; then
  D=$(mktemp -d)
  curl -fsSL -o "$D/SHASUMS256.txt" https://nodejs.org/dist/latest-v24.x/SHASUMS256.txt
  F=$(grep -o 'node-v24[0-9.]*-linux-x64.tar.xz' "$D/SHASUMS256.txt" | head -1)
  curl -fsSL -o "$D/$F" "https://nodejs.org/dist/latest-v24.x/$F"
  (cd "$D" && grep " $F\$" SHASUMS256.txt | sha256sum -c -)
  rm -rf "$NODE_DIR" && mkdir -p "$NODE_DIR" && tar -xJf "$D/$F" -C "$NODE_DIR" --strip-components=1
fi
export PATH="$NODE_DIR/bin:$PATH"
npm install --global "rea-agents@$REA_VERSION"     # frida's install script stays blocked (runtime tracing only)
rea --version
echo "Register with Claude Code (edits ~/.claude.json + installs a skill): rea setup --client claude_code"
