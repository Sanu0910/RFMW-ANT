#!/bin/sh
# KICAD_PYTHON wrapper: run KiCad 9's python (official kicad/kicad:9.0 image unpacked in /opt/kicad9)
R=/opt/kicad9
for d in proc dev tmp; do mountpoint -q $R/$d || mount --rbind /$d $R/$d; done
mkdir -p $R/home/user $R/opt/KiCAD-MCP-Server
mountpoint -q $R/home/user || mount --bind /home/user $R/home/user
mountpoint -q $R/opt/KiCAD-MCP-Server || mount --bind /opt/KiCAD-MCP-Server $R/opt/KiCAD-MCP-Server
exec chroot $R /usr/bin/env HOME=/root PYTHONPATH=/opt/mcp-pylib:/opt/KiCAD-MCP-Server/python \
  KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels SSL_CERT_FILE=/etc/ssl/certs/ccr-ca.crt \
  /usr/bin/python3 "$@"
