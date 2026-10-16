# gds2openEMS: GDSII → openEMS FDTD

[gds2openEMS](https://github.com/VolkerMuehlhaus/gds2openEMS) (V. Mühlhaus) builds an openEMS
FDTD model straight from a GDSII layout plus an XML stackup. It handles automatic meshing,
lumped, via and GSG ports, and Touchstone export. It was written for IHP SG13G2 RFIC, but any
stackup XML works, so it can be used for PCB/MMIC layouts too (GDSII export from KiCad/ADS).

## Install

```bash
sudo bash tools/install_gds2openems.sh     # builds openEMS v0.37.0 headless if missing, then pip installs gds2openEMS
source /opt/openEMS/venv/bin/activate
```

Verified 2026-10-16 (Ubuntu 24.04, Python 3.13): openEMS v0.37.0, gds2openEMS 0.5.0.
The examples and stackups are cloned to `~/gds2openEMS/workflow`.

## Headless use (cloud / no display)

AppCSXCAD is not built (`--disable-GUI`), so set these before running any example:

```python
settings['preview_only'] = False
settings['no_gui'] = True        # skip the AppCSXCAD viewer, always simulate
```

and run with `MPLBACKEND=Agg` and `plt.savefig(...)` in place of `plt.show()`.

## Smoke test

`workflow/run_line_viaport.py` (thru line, via ports, 0–110 GHz, 267 k cells):

| Result | Value |
|---|---|
| Run time | 51 s on 4 cores, ~270 MCells/s |
| S11 | < −29 dB over 0–110 GHz |
| S21 | −0.12 dB at DC, −0.48 dB at 109 GHz |

## Stackup editor

`stackupEditor my.xml` is a Qt GUI and needs a display. On a headless box, edit the XML
directly; the format is in `~/gds2openEMS/doc/XML_stackup_format.md`.
