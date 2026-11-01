"""Single source of design data for project 17: 4-channel L-band CRPA active antenna board.

Everything the builders need (geometry, stack-up, parts, values) lives here.
Units: mm, GHz. KiCad board frame (x right, y down). [ASSUMED] marks values not
fixed by a datasheet or by the customer Gerber.
"""

# ----------------------------------------------------------------------------- board / array
# Kept from the customer board (Input/Gerber_4CH_GNSS.zip, Edge_Cuts + F.Cu pads):
BOARD_CENTER = (120.69, 122.04)      # Edge.Cuts circle centre (gerber X, -Y)
BOARD_RADIUS = 100.0                 # Edge.Cuts circle, D = 200 mm
ARRAY_CENTER = (120.83, 122.17)      # centre of the 4 antenna modules
ELEMENT_PITCH = 92.0                 # module-to-module spacing, x and y
# Element k (0..3) = element 0 rotated by -90*k deg about ARRAY_CENTER (sequential rotation,
# exactly as on the customer board). Element 0 is the top-left one at (74.83, 76.17).
ELEMENT0_OFFSET = (-46.0, -46.0)
CHANNEL_NAMES = ["CH1", "CH2", "CH3", "CH4"]   # CH1 TL, CH2 TR, CH3 BR, CH4 BL (seen from top)

# ----------------------------------------------------------------------------- stack-up
# 4-layer, 1.6 mm, FR-4 (Tg170), JLCPCB JLC04161H-7628 equivalent. RF on L4 (bottom)
# referenced to L3 GND across one 7628 prepreg.
STACKUP = [
    # name,        type,         thickness, er,  note
    ("F.SilkS",    "silk",       0.0,   None, ""),
    ("F.Mask",     "mask",       0.010, 3.8,  "green LPI"),
    ("F.Cu",       "copper",     0.035, None, "L1: solid GND = antenna ground plane"),
    ("PP1",        "prepreg",    0.2104, 4.4, "7628 RC49%"),
    ("In1.Cu",     "copper",     0.0152, None, "L2: +5V bias plane"),
    ("Core",       "core",       1.065, 4.6,  "FR-4 core"),
    ("In2.Cu",     "copper",     0.0152, None, "L3: solid GND, RF reference for L4"),
    ("PP2",        "prepreg",    0.2104, 4.4, "7628 RC49%"),
    ("B.Cu",       "copper",     0.035, None, "L4: RF lines + all SMD parts"),
    ("B.Mask",     "mask",       0.010, 3.8,  "green LPI"),
    ("B.SilkS",    "silk",       0.0,   None, ""),
]
BOARD_THICKNESS = 1.6

# 50 ohm line on L4 over L3, 0.2104 mm 7628 (er 4.4), 35 um Cu, mask on top.
# Hammerstad-Jensen (scikit-rf): 0.38 mm -> 49.5 ohm (Scripts/stackup_check.py).
RF_W = 0.38          # 50 ohm track width
RF_NECK_W = 0.20     # neck-down into fine-pitch pads (DFN-8, SAW)
RF_GAP = 0.30        # RF copper to GND pour (zone clearance on B.Cu)
PWR_W = 0.60         # +5V / bias track width
VIN_W = 1.00         # DC input tracks
GND_W = 0.30         # short GND stubs to vias
VIA_D, VIA_DRILL = 0.60, 0.30      # standard through via
EPVIA_D, EPVIA_DRILL = 0.50, 0.25  # vias in exposed pads / SAW GND (plugged + capped, IPC-4761 VII), 0.125 ring
FENCE_PITCH = 2.5    # GND via fence pitch along RF lines
FENCE_OFFSET = 1.05  # fence via centre to track centre

# Assumed module drills (not in the customer Gerber, which has no drill file)
ANT_FEED_DRILL = 1.1   # [ASSUMED] feed pin hole (2.0 mm pad kept from customer board)
ANT_STUD_DRILL = 3.2   # [ASSUMED] centre stud hole (7.0 mm pad kept)
ANT_MOUNT_DRILL = 3.2  # [ASSUMED] 4x M3 clearance, NPTH (3.6 mm mask opening on customer board)
ANT_FEED_ANTIPAD = 0.60  # copper clearance around feed pins on GND / +5V planes

# ----------------------------------------------------------------------------- parts
LIB = "CRPA17"
PARTS = {
    # key: (footprint lib, footprint, value, MPN, manufacturer, description)
    "ANT":   (LIB, "GNSS_StackedPatch_L1L2_4feed", "L1/L2 stacked patch", "existing module", "customer",
              "Stacked L1/L2 patch module, 4 probe feeds (supplied, fitted on top)"),
    "HYB":   (LIB, "HC125A", "HC125A", "HC125A", "Taoglas", "90 deg hybrid coupler 1150-1630 MHz"),
    "LIM":   (LIB, "MiniCircuits_TT1224", "RLM-63-2W+", "RLM-63-2W+", "Mini-Circuits",
              "RF limiter 30-6000 MHz, 2 W, +11.5 dBm out"),
    "LNA":   (LIB, "TQP3M9037_DFN8_2x2", "TQP3M9037", "TQP3M9037", "Qorvo", "LNA 0.4 dB NF, 5 V / 70 mA"),
    "SAW_L1": (LIB, "B7504_SAW_0.9x0.7", "B7504", "B39162B7504L210", "Qualcomm RF360", "SAW, GNSS L1/B1/G1"),
    "SAW_L2": (LIB, "B8889_SAW_1.1x0.9", "B8889", "B39122B8889P810", "Qualcomm RF360", "SAW, GNSS L2/L5"),
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
    "R50":   ("Resistor_SMD", "R_0402_1005Metric", "49.9R", "ERJ-2RKF49R9X", "Panasonic", "hybrid isolated-port load"),
    "R10K":  ("Resistor_SMD", "R_0402_1005Metric", "10k", "ERJ-2RKF1002X", "Panasonic", "P-FET gate"),
    "SMA":   ("Connector_Coaxial", "SMA_Amphenol_132134_Vertical", "SMA", "132134", "Amphenol RF",
              "SMA jack, vertical PCB, 50 ohm (fitted on bottom)"),
    "JDC":   ("Connector_Molex", "Molex_Micro-Fit_3.0_43650-0215_1x02_P3.00mm_Vertical", "+5V IN",
              "43650-0215", "Molex", "Micro-Fit 3.0, 2 pos, single DC bias input"),
    "PTC":   ("Fuse", "Fuse_1812_4532Metric", "2A hold", "MF-MSMF200-2", "Bourns", "resettable fuse 1812"),
    "PFET":  ("Package_TO_SOT_SMD", "SOT-23", "AO3401A", "AO3401A", "Alpha & Omega",
              "P-MOSFET -30 V -4 A, reverse-polarity protection (1 G, 2 S, 3 D)"),
    "TVS":   ("Diode_SMD", "D_SMA", "SMAJ5.0A", "SMAJ5.0A", "Littelfuse", "TVS 5.0 V standoff"),
    "FID":   ("Fiducial", "Fiducial_1mm_Mask2mm", "FID", "-", "-", "fiducial"),
    "TP":    ("TestPoint", "TestPoint_Pad_D1.5mm", "TP", "-", "-", "test pad"),
}

# LNA operating point used for the budget (project 16, TQP3M9037 datasheet at 5 V)
VDD = 5.0
IDD_TYP, IDD_MAX = 0.070, 0.090   # A per LNA
N_LNA = 16
