"""X-band 8-way stripline power divider (MSL-to-SL launches) - cage housing.  The ONE file to edit.
Board data are read from the customer DXF package in ../00_input (kept out of git); values here are the housing rules.
Units mm.  Frame of the STEP files: box centred on the board centre, x = east (outputs), y = north, z up (z = 0 base bottom)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..", "00_input", "XBand_8Way_Stripline_DXF_Package")
DXF_ALL = os.path.join(PKG, "XBand_8Way_MSL_to_SL_Transition_ALL_LAYERS.dxf")
RES_CSV = os.path.join(PKG, "XBand_8Way_MSL_to_SL_Transition_Resistors.csv")

BOARD = dict(
    t=1.524,               # [ASSUMED] L1 | RO4350B 0.762 | L2 stripline | RO4350B 0.762 | L3  (1.686 mm MSL = 50 ohm on 0.762 RO4350B)
    cu=0.035, er=3.66, band=(8.0, 12.0),
    resistor=dict(L=1.6, W=0.8, H=0.45),     # 0603 thick-film [ASSUMED from the pad pattern]
)
CAGE = dict(
    rib=2.0,               # rib width touching the top ground pour
    pitch=13.0,            # rib grid pitch -> 11 mm cells (TE110 ~19 GHz, well above X band)
    frame=2.0,             # perimeter rib
    gap=0.20,              # cage face above the PCB top (0.25 mm conductive elastomer sheet takes it up)
    launch_len=9.0, launch_halfw=4.5,       # launch pocket = board KEEP_OUT (5 x 9) + room for the pin/solder
    res_margin=1.0,        # pocket margin around each resistor group
    screw_head_r=3.6,      # pocket around the M3 board-mounting screw heads (board keep-out r = 3.0)
)
TEXT = dict(
    logo="CRL BEL",
    lab="ANTENNA / RFM LAB",
    title="X-BAND 8-WAY POWER DIVIDER",
    sub="MSL-SL STRIPLINE  8-12 GHz",
    pn="CRL-XB-PD8-01",
)
