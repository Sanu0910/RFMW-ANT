#!/usr/bin/env bash
# Install SolidCraft (parametric 3-D CAD, https://github.com/tangency-labs/solidcraft)
# and its headless MCP server `solidcraft-cli mcp` on Ubuntu/Debian x86_64.
# Used by the repo-level .mcp.json so every project in RFMW-ANT can drive SolidCraft.
# Safe to re-run: skips the download when the installed version is already current.
set -euo pipefail

URL="https://github.com/tangency-labs/solidcraft/releases/latest/download/solidcraft-linux-x86_64.deb"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "[solidcraft] downloading latest .deb"
curl -fsSL --retry 4 --retry-delay 2 -o "$TMP/solidcraft.deb" "$URL"
NEW_VER="$(dpkg-deb -f "$TMP/solidcraft.deb" Version)"
CUR_VER="$(dpkg-query -W -f='${Version}' solidcraft 2>/dev/null || true)"
if [ "$CUR_VER" = "$NEW_VER" ]; then
  echo "[solidcraft] $CUR_VER already installed"
else
  echo "[solidcraft] installing $NEW_VER (was: ${CUR_VER:-none})"
  $SUDO apt-get update -qq
  $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$TMP/solidcraft.deb"
fi

# an older standalone solidcraft-cli in /usr/local/bin would shadow the packaged one
if [ -e /usr/local/bin/solidcraft-cli ] && [ "$(readlink -f /usr/local/bin/solidcraft-cli)" != "/usr/bin/solidcraft-cli" ]; then
  $SUDO mv /usr/local/bin/solidcraft-cli /usr/local/bin/solidcraft-cli.old
fi
[ -e /usr/local/bin/solidcraft-cli ] || $SUDO ln -s /usr/bin/solidcraft-cli /usr/local/bin/solidcraft-cli

solidcraft-cli --version
echo "[solidcraft] MCP server: solidcraft-cli mcp --allow-path <repo>   (registered in .mcp.json)"
