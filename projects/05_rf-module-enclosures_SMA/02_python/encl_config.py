"""Parametric RF module enclosures - the ONE file to edit.
Three machined aluminium boxes (base + screwed lid with RF lip) for:
  A  PD_MSL  power divider, microstrip only
  B  MSL_SL  microstrip-to-stripline transition (back-to-back)
  C  UWB     UWB power divider
Connector: HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310), SMA jack, 4-hole 12.7 mm square flange, 18 GHz.
Units mm.  Values marked [ASSUMED] are placeholders until the real board files are supplied - change them here and
run build_enclosures.py; every STEP, drawing, PCB-interface DXF and check is regenerated."""

# ---------------- connector (measured from the H+S STEP 3D-outline_00051629-B, see 05_docs) ----------------
CONN = dict(
    part="HUBER+SUHNER 23_SMA-50-0-272/133_N (item 23030310)",
    step="00_vendor/HS_23_SMA-50-0-272-133_N_3D-outline_00051629-B.stp",
    x_contact=-6.369,      # flange face that sits on the box wall (STEP frame: axis = x, mating side = -x)
    flange=12.7, flange_t=1.59,
    hole_sq=8.64, hole_d=2.6, screw="M2.5", screw_len=5.0,
    spigot_d=4.16, spigot_len=5.09,           # rear spigot through the wall, from the flange face
    pin_d=1.26, pin_proj=2.92,                # pin beyond the spigot end (lies on the trace)
    bore_d=4.25,                              # wall bore for the spigot (H7-ish slip fit, ream if needed)
)

# ---------------- common box rules ----------------
BOX = dict(
    wall=5.0,              # = spigot length, so the pin lands on the board edge (all four walls, also carries M2.5 lid threads)
    clr=0.10,              # PCB-to-wall gap each side
    cav_r=1.0,             # pocket corner radius (D2 end mill); PCB corners need >= 1.2 radius or chamfer
    outer_r=2.0,           # outer vertical-edge radius
    h_air=8.2,             # air from PCB top to lid underside (room for a lid screw right above each port, see checks)
    floor_min=3.0,
    flange_margin=0.5,     # flange stays this far above the box bottom (box sits flat)
    t_lid=4.0,
    lip_h=1.5, lip_w=1.2, lip_clr=0.05,      # RF tongue on the lid, into the cavity (labyrinth seal)
    absorber_depth=1.0, absorber_inset=0.6,  # recess under the lid for 1 mm RF absorber sheet (optional)
    lid_screw="M2.5", lid_screw_std="ISO 7380 button head", lid_screw_pitch_max=15.0, lid_screw_pitch_min=7.0, lid_screw_len=8.0,
    lid_cb_d=6.0, lid_clear_d=2.9, lid_tap_depth=4.6,   # pitch = lambda/4 at f_max, clamped; tap keeps 0.8 mm above the spigot bore
                                                       # (no counterbore: a 5 mm wall cannot take an M2.5 head pocket)
    pcb_screw="M2", pcb_screw_len=4.0, pcb_clear_d=2.4, pcb_tap_depth=3.5,
    pcb_corner_inset=2.5, launch_screw_dx=3.0, launch_screw_dy=4.0,   # ground screws flanking every launch
    mount_screw="M3", mount_tap_depth=6.0,   # 4 x M3 in the bottom (fixture / heat sink)
    engrave_depth=0.3,
    material="Aluminium 6061-T6 (EN AW-6061 T6)",
    finish="Chromate conversion MIL-DTL-5541 Type II Class 3 (conductive), clear; or Ni plating",
    tolerance="ISO 2768-mK; bores and cavity +/-0.05; flatness of lid seat 0.05",
    company="BEL",         # title block; logo engraving below
    logo_svg="logo/BEL_logo.svg",   # put the outlined (filled paths, no strokes) logo here; else text is engraved
    logo_text="BEL", logo_w=26.0, logo_h=9.0,
    font_bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

# ---------------- the three boards [ASSUMED until the real layouts are supplied] ----------------
# ports: (label, wall W/E/N/S, offset along the wall from the board centre, trace width of the 50-ohm line)
BOARDS = {
    "A_PD_MSL": dict(
        title="2-WAY POWER DIVIDER (MICROSTRIP)", pn="RFE-PD-MSL-01",
        L=50.0, W=40.0, t=0.762, cu=0.035, substrate="RO4350B 0.762 mm (30 mil)", er=3.66,
        band=(2.0, 6.0),
        ports=[("P1 IN", "W", 0.0, 1.68), ("P2", "E", 10.0, 1.68), ("P3", "E", -10.0, 1.68)]),
    "B_MSL_SL": dict(
        title="MSL TO STRIPLINE TRANSITION", pn="RFE-TR-MSLSL-01",
        L=60.0, W=30.0, t=1.524, cu=0.035, substrate="2 x RO4350B 0.762 bonded (stripline inner layer)", er=3.66,
        band=(0.5, 12.0),
        ports=[("P1", "W", 0.0, 1.68), ("P2", "E", 0.0, 1.68)]),
    "C_UWB": dict(
        title="UWB POWER DIVIDER", pn="RFE-PD-UWB-01",
        L=50.0, W=45.0, t=0.508, cu=0.035, substrate="RO4003C 0.508 mm (20 mil)", er=3.55,
        band=(3.1, 10.6),
        ports=[("P1 IN", "W", 0.0, 1.10), ("P2", "E", 12.0, 1.10), ("P3", "E", -12.0, 1.10)]),
}
