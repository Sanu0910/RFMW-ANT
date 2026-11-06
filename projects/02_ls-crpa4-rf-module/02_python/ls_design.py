"""Single source of design data for project 02: CRL-LS-CRPA4, 4-channel L1 + L2/L5 + NavIC S CRPA active antenna board.
Derived from project 17 (crpa_design.py); geometry from the customer board combine_model_2.0 (00_input/PCB_FAB_LS_4E).

Everything the builders need (geometry, stack-up, parts, values) lives here.
Units: mm, GHz. KiCad board frame (x right, y down). [ASSUMED] marks values not
fixed by a datasheet or by the customer Gerber.
"""

# ----------------------------------------------------------------------------- board / array
# Kept from the customer board (Input/Gerber_4CH_GNSS.zip, Edge_Cuts + F.Cu pads):
BOARD_CENTER = (132.881, 122.331)    # Edge.Cuts circle centre of combine_model_2.0 (gerber X, -Y)
BOARD_RADIUS = 100.0                 # Edge.Cuts circle, D = 200 mm
ARRAY_CENTER = (133.161, 122.161)    # centre of the 4 L patches (gerber offset +0.28, +0.17 from the outline centre)
ELEMENT_PITCH = 91.0                 # L patch spacing, x and y (combine_model_2.0)
# Element k (0..3) = element 0 rotated by -90*k deg about ARRAY_CENTER (sequential rotation,
# exactly as on the customer board). Element 0 is the top-left one at (74.83, 76.17).
ELEMENT0_OFFSET = (-45.5, -45.5)
CHANNEL_NAMES = ["CH1", "CH2", "CH3", "CH4"]   # CH1 TL, CH2 TR, CH3 BR, CH4 BL (seen from top)
# NavIC S patch of channel k sits on the axis clockwise next to its L patch (CH1 L=TL, S=N), as on the customer board.
# Element-0 local frame (origin = CH1 L patch centre, KiCad axes): S patch centre and its holes.
# S patch spacing = lambda/2 at NavIC S (user, 2026-11-05): 299.792458 / 2.492028 / 2 = 60.15 mm between adjacent
# S elements (N-E-S-W square) -> radius 60.15 / sqrt(2) = 42.53 mm on the axes. (L patches: 91 mm = 0.48 lambda at L1.)
S_F0_MHZ = 2492.028
S_SPACING = 299792.458 / S_F0_MHZ / 2                        # mm, lambda/2 = 60.15
S_RADIUS = S_SPACING / 2 ** 0.5
S_CENTER = (-ELEMENT0_OFFSET[0], -ELEMENT0_OFFSET[1] - S_RADIUS)   # element-0 local (N element)
S_FEED_R = 4.0                       # 4 pins D0.77 on D2.0 pads (customer S patch site)
S_FEED_DRILL, S_FEED_PAD = 0.77, 2.0
S_CENTRE_DRILL, S_CENTRE_PAD = 2.2, 4.0
S_MOUNT = []                         # customer D2.2 fixing holes belonged to the S patch at r 70.8: not reused [OPEN]
S_HYB_T = 8.0                       # hybrid centre distance from the S patch centre along the outward feed bisector
S_SMA_MAX_R = 93.0                   # S output SMA centre radius limit (flange + back-cover wall)

# ----------------------------------------------------------------------------- stack-up
# 4-layer hybrid, 1.60 mm: FR-4 high-Tg (IT-180A / S1000-2) for L1-L3, Rogers RO4350B 0.168 mm (6.6 mil) core
# between L3 (GND reference) and L4 (RF + all SMD). Combines project 17 (4L, star bias on L2, 0.38 mm line) with the
# customer board (RF on RO4350B over a solid GND). Line loss before the LNAs 0.066 dB/cm @2.5 GHz vs 0.121 on 7628.
STACKUP = [
    # name,        type,         thickness, er,  note
    ("F.SilkS",    "silk",       0.0,   None, ""),
    ("F.Mask",     "mask",       0.010, 3.8,  "green LPI"),
    ("F.Cu",       "copper",     0.035, None, "L1: solid GND = antenna ground plane"),
    ("Core1",      "core",       0.710, 4.4,  "FR-4 high-Tg core (IT-180A)"),
    ("In1.Cu",     "copper",     0.035, None, "L2: GND + per-channel +5V star traces"),
    ("PP1",        "prepreg",    0.540, 4.3,  "FR-4 prepreg 2x2116 + 1x1080 (bonds FR-4 to RO4350B)"),
    ("In2.Cu",     "copper",     0.035, None, "L3: solid GND, RF reference for L4"),
    ("Core2",      "core",       0.168, 3.66, "Rogers RO4350B 0.168 mm (6.6 mil), tan d 0.0037"),
    ("B.Cu",       "copper",     0.035, None, "L4: RF lines + all SMD parts, ENIG"),
    ("B.Mask",     "mask",       0.010, 3.8,  "green LPI"),
    ("B.SilkS",    "silk",       0.0,   None, ""),
]
BOARD_THICKNESS = 1.6

# 50 ohm line on L4 over L3 across RO4350B 0.168 mm, 35 um Cu: Hammerstad-Jensen (scikit-rf) 0.340 mm -> 49.8 ohm
# (02_python/rf_budget.py prints the check).
RF_W = 0.34          # 50 ohm track width
RF_NECK_W = 0.20     # neck-down into fine-pitch pads (DFN-8, SAW)
RF_GAP = 0.30        # RF copper to GND pour (zone clearance on B.Cu), ~1.8 h: < 0.5 ohm CPWG shift
PWR_W = 0.60         # +5V / bias track width (L4 stubs)
TRUNK_W = 0.80       # In1.Cu star trunk per channel (0.56 A typ / 0.72 A max per channel incl. S, 35 um Cu)
BIAS_W = 0.40        # In1.Cu branch FB -> each LNA bias via (0.09 A)
FB_AT = (12.0, 12.5) # element-local position of the channel ferrite FB{n} pad 1
VIN_W = 1.50         # DC input tracks (2.9 A max)
GND_W = 0.30         # short GND stubs to vias
VIA_D, VIA_DRILL = 0.60, 0.30      # standard through via
EPVIA_D, EPVIA_DRILL = 0.50, 0.25  # vias in exposed pads / SAW GND (plugged + capped, IPC-4761 VII), 0.125 ring
FENCE_PITCH = 2.5    # GND via fence pitch along RF lines (< lambda/20 in RO4350B at 2.5 GHz = 4.5 mm)
FENCE_OFFSET = 1.00  # fence via centre to track centre

# L antenna = Taoglas GPDF6010.A (p17, data sheet SPE-21-8-111-G); drills as on the customer board combine_model_2.0
ANT_MODULE = "Taoglas GPDF6010.A"
ANT_FEED_DRILL = 1.35   # combine_model_2.0 drills D1.35 (GPDF6010.A DS: pins D0.90; p17 used 1.1) - customer board wins
ANT_STUD_DRILL = 3.2    # centre screw hole D3.20 - must be GROUNDED (DS sec. 4.5 note)
ANT_MOUNT_DRILL = 3.6   # combine_model_2.0: 4x D3.6 PTH at +/-29 mm (M3); GPDF6010.A DS gives D1.8 locating holes [CONFIRM]
ANT_MOUNT_PAD = 6.0     # GND ring: the M3 screws also clamp the back cover (CRL-LS-CRPA4-BC01)
ANT_FEED_ANTIPAD = 0.75 # 2.0 pad + 0.75 = D3.5 copper-free on all layers (DS: D3.0 top/inner, D3.5 bottom)
# Channel shielding: the machined back cover CRL-LS-CRPA4-BC01 carries walls that land on these exposed GND frames
# (conductive gasket), one octagon per L channel and one rectangle per S chain (replaces p17's soldered cans).
SHIELD_W = 1.5          # exposed GND frame land on B.Cu (cover wall 1.2 mm + gasket)
SHIELD_MARGIN = 1.6     # frame centreline outside the outermost channel courtyard
SHIELD_NOTCH = 2.6      # gap in the frame where the RF output leaves; the cover wall has a 2.6 x 1.0 mm tunnel there
SHIELD_H = 6.0          # cavity depth in the back cover above B.Cu

# ----------------------------------------------------------------------------- parts
LIB = "CRL_LS"
PARTS = {
    # key: (footprint lib, footprint, value, MPN, manufacturer, description)
    "ANT":   (LIB, "GNSS_StackedPatch_L1L2_4feed", "L1/L2 stacked patch", "existing module", "customer",
              "Stacked L1/L2 patch module, 4 probe feeds (supplied, fitted on top)"),
    "HYB":   (LIB, "HC125A", "HC125A", "HC125A", "Taoglas", "90 deg hybrid coupler 1150-1630 MHz"),
    "LIM":   (LIB, "MiniCircuits_DL1721", "CLM-83-2W+", "CLM-83-2W+", "Mini-Circuits",
              "RF limiter 30-8200 MHz, 2 W, +11.5 dBm out, DL1721 3x3 mm hermetic"),
    "LNA":   (LIB, "TQP3M9037_DFN8_2x2", "TQP3M9037", "TQP3M9037", "Qorvo", "LNA 0.4 dB NF, 5 V / 70 mA"),
    "SAW_L1": (LIB, "B7504_SAW_0.9x0.7", "B7504", "B39162B7504L210", "Qualcomm RF360", "SAW, GNSS L1/B1/G1"),
    "SAW_L2": (LIB, "B8889_SAW_1.1x0.9", "B8889", "B39122B8889P810", "Qualcomm RF360", "SAW, GNSS L2/L5"),
    "SANT":  (LIB, "NavIC_S_Patch_4feed_combine_model", "NavIC S patch", "CRL-LS-SP01", "BEL CRL (in-house)",
              "NavIC S patch, 4 pins D0.77 at 4 mm (S0/S90 used), centre D2.2 GND - geometry from combine_model_2.0"),
    "MH22":  (LIB, "MountingHole_2.2_PTH_GND", "MH 2.2", "-", "-", "D2.2 plated hole, GND (customer board position)"),
    "XHYB":  (LIB, "Xinger_C2327J5003AHF", "C2327J5003AHF", "C2327J5003AHF", "TTM Technologies",
              "Xinger 90 deg hybrid 2300-2700 MHz, IL 0.3 dB, iso 22 dB, 0.68 mm (TTM Rev K land pattern); config 1: F0 -> 4, F90 -> 6 = RHCP"),
    "SAW_S": (LIB, "TA1442A_SAW_3x3", "TA1442A", "TA1442A", "Tai-Saw",
              "SAW 2492 MHz NavIC S, 3.0x3.0x1.4 mm, IL 1.55 dB, Pin max +10 dBm, DC max 3 V (Tai-Saw Rev 1 land pattern)"),
    "C2P4":  ("Capacitor_SMD", "C_0402_1005Metric", "2.4pF", "GJM1555C1H2R4BB01D", "Murata",
              "C0G hi-Q 0402, S LNA input series (Qorvo 2.3-2.6 GHz ref. design)"),
    "L2N7":  ("Inductor_SMD", "L_0402_1005Metric", "2.7nH", "LQP15MN2N7B02D", "Murata",
              "S LNA input shunt (Qorvo 2.3-2.6 GHz ref. design) [verify MPN]"),
    "L5N6":  ("Inductor_SMD", "L_0603_1608Metric", "5.6nH", "LQW18AN5N6D00D", "Murata",
              "S LNA bias choke (Qorvo 2.3-2.6 GHz ref. design), 0603 wirewound [verify MPN]"),
    "LOGO":  (LIB, "BEL_Logo_Silk", "BEL", "-", "-", "BEL logo, silkscreen"),
    "DXP":   (LIB, "DXP.02.A", "DXP.02.A", "DXP.02.A", "Taoglas", "GNSS diplexer L1 / L2-L5"),
    "C100P": ("Capacitor_SMD", "C_0402_1005Metric", "100pF", "GRM1555C1H101JA01D", "Murata", "C0G 50 V 0402"),
    "C1U":   ("Capacitor_SMD", "C_0402_1005Metric", "1uF", "GRM155R61A105KE15D", "Murata", "X5R 10 V 0402"),
    "C1P0":  ("Capacitor_SMD", "C_0402_1005Metric", "1.0pF", "GJM1555C1H1R0BB01D", "Murata", "C0G hi-Q 0402"),
    "C1P5":  ("Capacitor_SMD", "C_0402_1005Metric", "1.5pF", "GJM1555C1H1R5BB01D", "Murata", "C0G hi-Q 0402"),
    "CDNP":  ("Capacitor_SMD", "C_0402_1005Metric", "DNP", "-", "-", "tuning position (not fitted)"),
    "C10U":  ("Capacitor_SMD", "C_0805_2012Metric", "10uF", "GRM21BR61A106KE19L", "Murata", "X5R 10 V 0805"),
    "C22U":  ("Capacitor_SMD", "C_1206_3216Metric", "22uF", "GRM31CR61A226KE15L", "Murata", "X5R 10 V 1206"),
    "C100N": ("Capacitor_SMD", "C_0402_1005Metric", "100nF", "GRM155R71C104KA88D", "Murata", "X7R 16 V 0402"),
    "L18N":  ("Inductor_SMD", "L_0603_1608Metric", "18nH", "LQW18AN18NG00D", "Murata",
              "LNA bias choke (eval-board value), 0603 wirewound"),
    "L6N8":  ("Inductor_SMD", "L_0402_1005Metric", "6.8nH", "LQW15AN6N8G00D", "Murata", "B8889 shunt match"),
    "L4N7":  ("Inductor_SMD", "L_0402_1005Metric", "4.7nH", "LQW15AN4N7B00D", "Murata", "DXP L1 port series"),
    "L3N3":  ("Inductor_SMD", "L_0402_1005Metric", "3.3nH", "LQW15AN3N3B00D", "Murata", "DXP L2/L5 port series"),
    "L4N3":  ("Inductor_SMD", "L_0402_1005Metric", "4.3nH", "LQW15AN4N3B00D", "Murata", "DXP common port series"),
    "FB":    ("Inductor_SMD", "L_0603_1608Metric", "600R@100MHz", "BLM18KG601SN1D", "Murata",
              "ferrite bead 1.3 A, per-channel bias isolation (star branch)"),
    "R50":   ("Resistor_SMD", "R_0402_1005Metric", "49.9R", "ERJ-2RKF49R9X", "Panasonic", "hybrid isolated-port load"),
    "R10K":  ("Resistor_SMD", "R_0402_1005Metric", "10k", "ERJ-2RKF1002X", "Panasonic", "P-FET gate"),
    "SMA":   ("Connector_Coaxial", "SMA_Amphenol_132134_Vertical", "SMA", "132134", "Amphenol RF",
              "SMA jack, vertical PCB, 50 ohm (fitted on bottom)"),
    "JDC":   ("Connector_Molex", "Molex_Micro-Fit_3.0_43650-0215_1x02_P3.00mm_Vertical", "+5V IN",
              "43650-0215", "Molex", "Micro-Fit 3.0, 2 pos, single DC bias input"),
    "PTC":   ("Fuse", "Fuse_1812_4532Metric", "2A hold", "MF-MSMF200-2", "Bourns", "resettable fuse 1812"),
    "PFET":  ("Package_TO_SOT_SMD", "SOT-23", "AO3401A", "AO3401A", "Alpha & Omega",
              "P-MOSFET -30 V -4 A, reverse-polarity protection (1 G, 2 S, 3 D)"),
    "TVS":   ("Diode_SMD", "D_SMC", "1.5SMC6.8A", "1.5SMC6.8A", "Littelfuse",
              "TVS 1500 W, 5.8 V standoff / 6.8 V breakdown, SMC (DO-214AB)"),
    "FID":   ("Fiducial", "Fiducial_1mm_Mask2mm", "FID", "-", "-", "fiducial"),
    "TP":    ("TestPoint", "TestPoint_Pad_D1.5mm", "TP", "-", "-", "test pad"),
}

# LNA operating point used for the budget (project 16, TQP3M9037 datasheet at 5 V)
VDD = 5.0
IDD_TYP, IDD_MAX = 0.070, 0.090   # A per LNA
N_LNA = 24                        # 4 x (L1 2 + L2/L5 2 + S 2)
