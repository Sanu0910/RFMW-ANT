"""X-band MSL cal-line (THRU) base plates - the ONE file to edit.
Every output (STEP parts + assembly, drawings, report, BOM) is regenerated from this file by
    python build_all.py
Units: mm, GHz.  [ASSUMED] marks values not given by the customer; change them here.
Frame: the cal board's DXF frame (x along the line, origin = J1 signal via, y = 0 on the line), z = 0 on the plate bottom."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
INP = os.path.join(ROOT, "00_input")

# ---------------- cal boards (customer DXFs, 00_input/MSL_SL_Cal_Lines.zip) ----------------
BOARDS = {
    "15": dict(name="XBand_RO4350B_30mil_Thru_SHORT_15mm", line=15.0, pn="CRL-XB-CALP-15"),
    "65": dict(name="XBand_RO4350B_30mil_Thru_LONG_65mm", line=65.0, pn="CRL-XB-CALP-65"),
}
for _k, _b in BOARDS.items():
    _b["mech"] = os.path.join(INP, _b["name"] + "_MECHANICAL.dxf")
    _b["all"] = os.path.join(INP, _b["name"] + "_ALL_LAYERS.dxf")

PCB = dict(
    # L1 MSL / ground, L2 stripline + launch ground, L3 ground. The DXFs give no stack-up; the 50 ohm widths fit
    # 2 x RO4350B 0.762 mm (MSL W 1.686 on 0.762; stripline W 0.844 in b = 1.524 -> 49.5 ohm at er 3.66).
    t=1.73,                 # [ASSUMED] 2 x 0.762 RO4350B + 0.102 RO4450F bond ply + 3 x 0.035 Cu. CONFIRM WITH THE FAB.
    cu=0.035,
    t_tol=0.08,             # [ASSUMED] fab thickness tolerance (pin rides on the trace, see report)
)

# ---------------- connector: HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310), same part as project 01 ----------------
CONN = dict(
    part="HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310)",
    step=os.path.join(ROOT, "00_vendor", "HS_23_SMA-50-0-272-133_N_3D-outline_00051629-B.stp"),
    x_contact=-6.369,       # flange face in the vendor STEP frame (axis = x, mating side = -x)
    flange=12.7, flange_t=1.59, hole_sq=8.64, screw="M2.5", screw_len=5.0, tap_depth=4.0,
    spigot_d=4.16, spigot_len=5.09, pin_d=1.26, pin_proj=2.92, bore_d=4.25,
)

# ---------------- plate ----------------
PLATE = dict(
    clr_x=0.20,             # board end to pocket end (wall inner face): the spigot stands 0.09 proud of the wall
    clr_y=0.10,             # board side to pocket side (board routed +/-0.1)
    wall=5.0,               # connector wall = spigot length 5.09 - 0.09: spigot face flush with the pocket end, pin on the trace
    wall_w=16.0,            # wall width (flange 12.7 + 1.65 each side)
    wall_above_flange=0.65, # wall top above the flange top edge
    rim=3.4,                # plate rim beside the board pocket (y)
    pocket=1.0,             # board locating pocket depth (board stands 0.73 proud)
    flange_margin=0.5,      # connector flange bottom stays this far above the plate bottom (bench)
    corner_r=3.0,           # plate outline corners (vertical edges)
    # lightening from below
    skin=2.0,               # metal left under the pocket floor
    under_rim=2.5,          # side rims (y) of the underside pockets
    under_end=1.5,          # underside pocket ends this far inboard of the wall inner face (M2.5 taps + bore stay in solid)
    boss_r=4.0,             # solid boss round each M3 board tap
    rib=3.0,                # rib width
    rib_x=25.0,             # longest bay along x before a cross rib is added
    tool_r=2.0,             # D4 end mill: smallest concave radius of the underside pockets
    notch_w=8.0,            # finger notches (both long sides, mid-board) to lift the board out
    m3_screw_len=6.0,       # ISO 4762 M3 x 6 through the board into the plate
    chamfer=0.5,            # bottom outside edges
    engrave_depth=0.2,
    material="Aluminium EN AW-6061-T6",
    finish="Chromate conversion MIL-DTL-5541 Type II Class 3, clear (conductive), all over",
    tolerance="ISO 2768-mK unless stated",
)

TEXT = dict(title="X-BAND MSL CAL LINE BASE PLATE", date="06-11-2026", band="8-12 GHz", rev="A")
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT = r"C:\Windows\Fonts\arial.ttf"
