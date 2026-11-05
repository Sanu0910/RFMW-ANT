"""X-band 8-way microstrip Wilkinson divider housing (V3) - the ONE file to edit.
Every output (PCB v3 DXF, STEP parts and assembly, drawings, report, BOM) is regenerated from this file by
    python build_all.py
Units: mm, GHz.  [ASSUMED] marks values not given by the customer; change them here."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# ---------------- inputs ----------------
PCB_DXF_IN = os.path.join(ROOT, "00_input", "Wilkinson_8Way_XBand_RO4350B_30mil_FabricationReady.dxf")
LOGO_PNG = os.path.join(ROOT, "00_input", "BEL_logo.png")
CONN_STEP = os.path.join(ROOT, "00_vendor", "HS_23_SMA-50-0-272-133_N_3D-outline_00051629-B.stp")

# ---------------- board (from the DXF and its generator script wilkinson_8way_fabrication_dxf.py) ----------------
BOARD = dict(
    substrate="Rogers RO4350B 0.762 mm (30 mil), er 3.48 (design) / 3.66 (process)",
    h=0.762, cu=0.035,                      # 1 oz copper both sides; bottom = solid ground [ASSUMED: bottom layer not in the DXF]
    er=3.48,
    gnd_clearance=2.5 * 1.686,              # pour set-back from the signal copper = 2.5 x W50 (generator default)
    band=(8.0, 12.0),
    resistor=dict(L=1.0, W=0.5, H=0.35),    # 0402 thin-film isolation resistors (21 x)
)
BOARD["t"] = BOARD["h"] + 2 * BOARD["cu"]   # 0.832 mm over copper

# ---------------- PCB v3: mounting holes added to the customer board ----------------
PCB_HOLES = dict(
    drill=2.40,             # finished plated hole for M2 (ISO 273 medium 2.4)
    head_r=1.90,            # ISO 4762 M2 head d3.8: the head must sit fully on top ground
    head_margin=0.60,       # extra copper beyond the head edge
    edge_min=2.6,           # hole centre to board edge
    via_clear=0.35,         # via pad edge to hole edge (vias closer are removed)
    min_spacing=10.0,       # between holes
    launch_dx=4.0,          # hole row inside each connector edge (from the board edge)
)

# ---------------- connector: HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310), data sheet in 00_vendor ----------------
CONN = dict(
    part="HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310)",
    x_contact=-6.369,       # flange face in the vendor STEP frame (axis = x, mating side = -x)
    flange=12.7, flange_t=1.59, hole_sq=8.64, screw="M2.5", screw_len=5.0, screw_tap_depth=4.0,
    spigot_d=4.16, spigot_len=5.09, pin_d=1.26, pin_proj=2.92, bore_d=4.25,
)

# ---------------- housing ----------------
BOX = dict(
    wall=5.0,               # = spigot length: the spigot face reaches the cavity, the pin lies on the trace
    clr=0.10,               # board edge to cavity wall, each side
    cav_r=1.0,              # pocket corner radius (D2 end mill) ...
    corner_relief_d=2.4,    # ... plus a D2.4 relief at each corner so the square board corners fit
    outer_r=2.0,            # outside vertical edges
    flange_margin=0.5,      # connector flange stays this far above the base bottom
    h_air=7.0,              # PCB top to lid-plate underside (the cage block fills it)
    t_lid=4.0,              # lid plate
    floor_min=3.0,
    material="Aluminium EN AW-6061-T6",
    finish="Chromate conversion MIL-DTL-5541 Type II Class 3, clear (conductive), all over",
    tolerance="ISO 2768-mK; cavity, bores, dowel holes +/-0.02; lid seat and cage face flatness 0.03",
    lid_screw="M2.5", lid_screw_len=8.0, lid_clear_d=2.9, lid_tap_depth=4.6, lid_screw_pitch=12.0,
    lid_head_d=4.7,         # ISO 7380 button head
    pcb_screw="M2", pcb_screw_len=5.0, pcb_tap_depth=4.5,
    mount_screw="M3", mount_tap_depth=6.0,
    dowel_d=2.0, dowel_len=8.0, dowel_depth=5.0,     # ISO 8734 2 m6 x 8, pressed into the base
    jack="M3",
    earth="M3", earth_depth=5.0,
    chamfer_lid=0.6, chamfer_base=0.5,
    engrave_depth=0.3,
)

# ---------------- lid cage (channels over the RF lines) ----------------
CAGE = dict(
    gap=0.35,               # cage face to PCB top (nominal); a 0.5 mm conductive elastomer sheet fills it:
    gasket_t=0.50,          #   compression 0.15 +/- 0.05 (board 0.762 +/- 0.051) = 20-40 %
    gasket="Conductive elastomer sheet 0.5 mm, Ag/Al filled silicone (e.g. Parker Chomerics CHO-SEAL 1285), die-cut",
    wall_offset=2.5,        # channel wall to the nearest signal copper (2D FD: Z0 49.2 vs 50.2 ohm open, see report)
    ch_air=5.0,             # air above the lines inside the channels (6.6 h); lowest channel mode then > 1.3 f_max
    screw_pocket_d=5.2,     # pocket in the cage face over every M2 head
    screw_pocket_h=2.6,     # from the PCB top (head 2.0 + 0.6)
    tool_r=1.0,             # D2 end mill: smallest concave radius in the channel outline
)

# ---------------- engraving ----------------
TEXT = dict(
    title="X-BAND 8-WAY MSL POWER DIVIDER V3",
    pn="CRL-XB-PD8-03",
    date="05-11-2026",
    band="8-12 GHz",
    logo_w=78.0,            # logo width on the lid
)
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT = r"C:\Windows\Fonts\arial.ttf"
