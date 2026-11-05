#!/bin/sh
# KICAD_PYTHON wrapper: run KiCad 9's python (official kicad/kicad:9.0 image unpacked in /opt/kicad9)
R=/opt/kicad9
for d in proc dev tmp; do mountpoint -q $R/$d || mount --rbind /$d $R/$d; done
# bind the working tree so project paths are the same inside and outside the chroot
for d in /home/user "$HOME" "$PWD"; do
  case "$d" in ""|/|/root|$R*) continue;; esac
  [ -d "$d" ] || continue
  mkdir -p "$R$d"; mountpoint -q "$R$d" || mount --bind "$d" "$R$d"
done
mkdir -p $R/opt/KiCAD-MCP-Server
mountpoint -q $R/opt/KiCAD-MCP-Server || mount --bind /opt/KiCAD-MCP-Server $R/opt/KiCAD-MCP-Server
CERT=""; [ -f $R/etc/ssl/certs/ccr-ca.crt ] && CERT="SSL_CERT_FILE=/etc/ssl/certs/ccr-ca.crt"
exec chroot $R /usr/bin/env HOME=/root $CERT PYTHONPATH=/opt/mcp-pylib:/opt/KiCAD-MCP-Server/python \
  KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels \
  /usr/bin/python3 "$@"
