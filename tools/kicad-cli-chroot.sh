#!/bin/sh
# Run KiCad 9 kicad-cli inside the unpacked kicad/kicad:9.0 rootfs (/opt/kicad9).
R=/opt/kicad9
for d in proc dev tmp; do mountpoint -q $R/$d || mount --rbind /$d $R/$d; done
mkdir -p $R/home/user
mountpoint -q $R/home/user || mount --bind /home/user $R/home/user
exec chroot $R /usr/bin/env HOME=/root \
  KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels \
  /usr/bin/kicad-cli "$@"
