"""CRL-TRK-2W-L1 - "Samay Track 2W Lite": single source of truth for the circuit.

Lite = the low-cost consumer variant described in 07_marketing/BUSINESS_PLAN_NOTES.md section 5:
  * LTE Cat-1 modem with GSM/GPRS fallback that runs the firmware itself (Quectel EC200U-CN, QuecOpen /
    QuecPython) - no separate MCU, no level-shifted modem UART, no external log flash (8 MB module flash).
  * Quectel L76K GPS + BeiDou + GLONASS receiver (no NavIC, so not AIS-140).
  * LIS3DH accelerometer (wake-on-motion / tow / fall alert), ignition sense, one relay output.
  * 9-30 V input, XL1509 40 V buck, 300 mAh LiPo backup (2-4 h), MCP73831 charger, PMOS power path.
  * 60 x 45 mm 2-layer 1.6 mm FR-4, all parts on the top side (single-sided SMT), same enclosure and
    mounting holes as the full CRL-TRK-2W-01.

Every component is declared once with its KiCad symbol, footprint, value, MPN and a pin->net map.
make_schematic.py turns this into a hierarchical KiCad schematic; make_pcb.py into the board.

Values marked VERIFY in `note` were set from search-engine excerpts of the vendor documents or from
family-compatible parts (vendor PDFs were not reachable from the build machine). They are listed in
04_docs/VERIFY_LIST.md and must be checked before ordering. The EC200U land pattern in particular is a
parametric reconstruction - replace it with Quectel's recommended footprint before fabrication.
"""
from collections import OrderedDict

PROJECT = "tracker_lite"
PN = "CRL-TRK-2W-L1"
TITLE = "CRL-TRK-2W-L1  Two-Wheeler Tracker Lite"
REV = "A0"
COMPANY = "CRL / BEL - RFM Lab"
LIB = "lite"              # project symbol / footprint library nickname

SHEETS = OrderedDict([
    ("power", "Power Input, Buck, Charger & Power Path"),
    ("modem", "Cat-1 / GSM Modem, SIM & LTE RF"),
    ("gnss", "GNSS (L76K) & Level Shift"),
    ("io", "Accelerometer, Vehicle I/O & LEDs"),
])

PARTS = []


def part(sheet, ref, lib, value, fp, nets, mpn="", mfr="", desc="", dnp=False, note="", group=""):
    PARTS.append(dict(sheet=sheet, ref=ref, lib=lib, value=value, fp=fp, nets=nets, mpn=mpn, mfr=mfr,
                      desc=desc, dnp=dnp, note=note, group=group))


# ------------------------------------------------------------------ passive helpers
R0402 = "Resistor_SMD:R_0402_1005Metric"
R0603 = "Resistor_SMD:R_0603_1608Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
L0402 = "Inductor_SMD:L_0402_1005Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"


def R(sheet, ref, val, a, b, fp=R0402, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        size = {R1206: "1206", R0603: "0603"}.get(fp, "0402")
        mpn = f"{size} 1% thick film"
    part(sheet, ref, "Device:R", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Uniroyal / Yageo", dnp=dnp, note=note, group=group)


def C(sheet, ref, val, a, b, fp=C0402, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        mpn = {C0402: "0402", C0603: "0603", C0805: "0805", C1206: "1206", C1210: "1210"}[fp] + " MLCC X5R/X7R"
    part(sheet, ref, "Device:C", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Samsung / Murata", dnp=dnp, note=note, group=group)


def TP(sheet, ref, net, group="tp"):
    part(sheet, ref, "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.0mm", {"1": net},
         mpn="Test pad 1.0 mm (no part)", group=group)


# ================================================================== 1. POWER
S = "power"
part(S, "J1", "Connector_Generic:Conn_01x04", "VEHICLE 4P", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
     {"1": "VIN_RAW", "2": "GND", "3": "IGN_RAW", "4": "RELAY_OUT"},
     mpn="B4B-XH-A(LF)(SN)", mfr="JST", desc="XH 2.5 mm 4-pin header; harness: red +12V, black GND, yellow IGN, blue relay",
     note="1 +12V(BAT) 2 GND 3 IGN 4 RELAY (low side, coil to +12V)", group="vin")
part(S, "F1", "Device:Fuse", "2A", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VIN_F"},
     mpn="0466002.NRHF", mfr="Littelfuse", desc="Fuse 2 A fast 63 V 1206 (plus 2 A blade fuse in harness)", group="vin")
part(S, "D1", "Device:D_TVS", "SMBJ24CA", "Diode_SMD:D_SMB", {"1": "VIN_F", "2": "GND"},
     mpn="SMBJ24CA", mfr="Littelfuse / MDD", desc="TVS 600 W bidirectional 24 V stand-off, 38.9 V clamp (load dump)",
     note="clamp 38.9 V < XL1509 40 V abs max; reverse battery blows F1 via D1", group="vin")
part(S, "D2", "Diode:SS34", "SS34", "Diode_SMD:D_SMA", {"1": "VIN_PROT", "2": "VIN_F"},
     mpn="SS34", mfr="MDD", desc="Schottky 40 V 3 A series reverse-polarity diode", group="vin")
C(S, "C1", "10uF/50V", "VIN_PROT", "GND", fp=C1210, group="vin", note="input bulk; the harness inductance is damped by D1 + F1")
C(S, "C2", "4.7uF/50V", "VIN_PROT", "GND", fp=C1206, group="buck")
C(S, "C3", "100nF/50V", "VIN_PROT", "GND", fp=C0603, group="buck")
part(S, "U1", f"{LIB}:XL1509-ADJ", "XL1509-ADJ", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "VIN_PROT", "2": "BUCK_SW", "3": "GND", "4": "BUCK_FB", "5": "GND", "6": "GND", "7": "GND", "8": "GND"},
     mpn="XL1509-ADJE1", mfr="XLSEMI", desc="Buck 4.5-40 V in, 2 A, 150 kHz, adjustable (VFB 1.23 V)",
     note="EN (pin 5) low = on, tied to GND; pins 6-8 GND heat-spreader - VERIFY pinout vs XLSEMI datasheet", group="buck")
part(S, "D3", "Diode:SS34", "SS34", "Diode_SMD:D_SMA", {"1": "BUCK_SW", "2": "GND"},
     mpn="SS34", mfr="MDD", desc="Schottky 40 V 3 A buck catch diode", group="buck")
part(S, "L1", "Device:L", "22uH", "Inductor_SMD:L_Bourns_SRN6045TA", {"1": "BUCK_SW", "2": "V4_BUCK"},
     mpn="SRN6045TA-220M", mfr="Bourns", desc="22 uH semi-shielded power inductor 6x6 mm, Isat ~2 A",
     note="VERIFY Isat >= 2.2 A (GSM burst); alt. CYNTEC / Sunlord 6045 22 uH", group="buck")
R(S, "R1", "2.61k", "V4_BUCK", "BUCK_FB", group="buck", note="VOUT = 1.23 V x (1 + R1/R2) = 4.44 V")
R(S, "R2", "1k", "BUCK_FB", "GND", group="buck")
C(S, "C4", "22uF/10V", "V4_BUCK", "GND", fp=C1206, group="buck")
C(S, "C5", "22uF/10V", "V4_BUCK", "GND", fp=C1206, group="buck")
# charger
part(S, "U2", "Battery_Management:MCP73831-2-OT", "MCP73831-2", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "CHG_STAT", "2": "GND", "3": "VBAT", "4": "V4_BUCK", "5": "CHG_PROG"},
     mpn="MCP73831T-2ACI/OT", mfr="Microchip", desc="Li-ion linear charger 4.20 V, 500 mA max",
     note="Input is the 4.44 V buck rail: the cell tops out ~4.1 V (longer life in a hot under-seat box)", group="chg")
R(S, "R3", "6.8k", "CHG_PROG", "GND", group="chg", note="ICHG = 1000 V / R = 147 mA (0.5 C for 300 mAh)")
C(S, "C6", "4.7uF/10V", "V4_BUCK", "GND", fp=C0603, group="chg")
C(S, "C7", "4.7uF/10V", "VBAT", "GND", fp=C0603, group="chg")
part(S, "J2", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "LiPo 300mAh",
     "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
     {"1": "VBAT", "2": "GND", "MP": "GND"}, mpn="S2B-PH-SM4-TB(LF)(SN)", mfr="JST",
     desc="Battery: 1S LiPo 300 mAh (402535 class) with PCM, JST PH 2-pin - 1 BAT+ 2 BAT-", group="bat")
# power path: buck -> D4 -> VSYS; battery -> Q1 (on when the buck is off) -> VSYS
part(S, "D4", "Diode:SS34", "SS34", "Diode_SMD:D_SMA", {"1": "VSYS", "2": "V4_BUCK"},
     mpn="SS34", mfr="MDD", desc="Schottky OR-ing buck -> VSYS (2 A GSM bursts)", group="path")
part(S, "Q1", "Transistor_FET:AO3401A", "AO3401A", SOT23, {"1": "V4_BUCK", "2": "VSYS", "3": "VBAT"},
     mpn="AO3401A", mfr="AOS", desc="P-MOSFET 30 V 4 A, 50 mOhm: battery -> VSYS when external power is gone",
     note="Gate = buck rail: off while the buck runs (Vgs = +0.35 V), on (Vgs = -VBAT) when it stops", group="path")
R(S, "R4", "100k", "V4_BUCK", "GND", group="path", note="discharges the buck rail so Q1 turns on fast")
C(S, "C8", "100uF/6.3V", "VSYS", "GND", fp=C1210, group="vsys", note="C8 + C9 = 200 uF ceramic GSM burst reservoir (~120 uF at 4 V bias)")
C(S, "C9", "100uF/6.3V", "VSYS", "GND", fp=C1210, group="vsys")
C(S, "C10", "100nF", "VSYS", "GND", group="vsys")
C(S, "C11", "33pF", "VSYS", "GND", mpn="0402 C0G 50V", group="vsys")
C(S, "C12", "10pF", "VSYS", "GND", mpn="0402 C0G 50V", group="vsys")
part(S, "D5", "Device:D_Zener", "SMF5.0A", "Diode_SMD:D_SOD-123F", {"1": "VSYS", "2": "GND"},
     mpn="SMF5.0A", mfr="Littelfuse", desc="TVS 200 W 5 V on modem VBAT (Quectel recommendation)", group="vsys")
# monitoring dividers (modem ADC0 / ADC1, range 0-1.2 V VERIFY)
R(S, "R5", "1M", "VIN_PROT", "VIN_SENSE", fp=R0603, group="sense")
R(S, "R6", "33k", "VIN_SENSE", "GND", group="sense", note="VIN 0-37 V -> 0-1.18 V (ADC1)")
C(S, "C13", "100nF", "VIN_SENSE", "GND", group="sense")
R(S, "R7", "300k", "VBAT", "VBAT_SENSE", group="sense")
R(S, "R8", "100k", "VBAT_SENSE", "GND", group="sense", note="VBAT/4 -> ADC0, 10 uA")
C(S, "C14", "100nF", "VBAT_SENSE", "GND", group="sense")
for i, n in enumerate(["VIN_RAW", "VIN_F", "V4_BUCK", "GND", "VSYS", "VIN_PROT"]):
    part(S, f"#FLG{10 + i}", "power:PWR_FLAG", "PWR_FLAG", "", {"1": n})

# ================================================================== 2. MODEM
S = "modem"
# Quectel EC200U-CN, LCC 80 + LGA 64 pads. Pin numbers per EC200U Hardware Design (EC2x-compatible table).
ec = {"57": "VSYS", "58": "VSYS", "59": "VSYS", "60": "VSYS", "7": "MDM_1V8",
      "21": "MDM_PWRKEY", "20": "MDM_RESET_N", "61": "MDM_STATUS", "6": "NET_STATUS",
      "67": "MDM_TX_1V8", "68": "MDM_RX_1V8", "62": "", "66": "", "63": "", "64": "", "65": "",
      "11": "MDM_DBG_RX", "12": "MDM_DBG_TX", "10": "GND", "13": "",
      "14": "SIM_VDD", "15": "SIM_DATA_M", "16": "SIM_CLK_M", "17": "SIM_RST_M",
      "69": "MDM_USB_DP", "70": "MDM_USB_DM", "71": "MDM_USB_VBUS",
      "27": "IGN_DET_N", "26": "ACC_INT", "24": "GNSS_EN", "25": "RELAY_CTL",
      "41": "I2C_SCL", "42": "I2C_SDA", "45": "VBAT_SENSE", "44": "VIN_SENSE", "49": "LTE_RF_M"}
for n in [8, 9, 19, 22, 36, 46, 48, 50, 51, 52, 53, 54, 56, 72] + list(range(85, 113)):
    ec[str(n)] = "GND"
part(S, "U3", f"{LIB}:EC200U", "EC200U-CN", f"{LIB}:Quectel_EC200U_LCC-144", ec,
     mpn="EC200UCNAA-N05-SNNSA", mfr="Quectel", desc="LTE Cat-1 bis + GSM/GPRS, QuecOpen, B1/3/5/8/34/38/39/40/41 + GSM 900/1800",
     note="Runs the tracker firmware (QuecOpen / QuecPython). Land pattern is a reconstruction - VERIFY", group="mdm")
C(S, "C15", "1uF", "MDM_1V8", "GND", fp=C0402, group="mdm")
# auto power-on: VSYS step -> C16 -> Q2 gate holds PWRKEY low ~1.5 s, then releases
part(S, "Q2", "Transistor_FET:2N7002", "2N7002", SOT23, {"1": "PWRKEY_G", "2": "GND", "3": "MDM_PWRKEY"},
     mpn="2N7002K-7", mfr="Diodes Inc", desc="Open-drain PWRKEY driver (PWRKEY has an internal pull-up)", group="pwk")
C(S, "C16", "10uF/10V", "VSYS", "PWRKEY_G", fp=C0603, group="pwk", note="power-on pulse: tau = C16 x R9 = 2.2 s, PWRKEY low >= 500 ms")
R(S, "R9", "220k", "PWRKEY_G", "GND", group="pwk")
R(S, "R10", "0R", "MDM_PWRKEY", "GND", dnp=True, group="pwk", note="fit for permanent auto power-on (no PWRKEY shutdown)")
TP(S, "TP1", "MDM_PWRKEY", group="mtp")
TP(S, "TP2", "MDM_RESET_N", group="mtp")
for net, ref in [("MDM_USB_VBUS", "TP3"), ("MDM_USB_DP", "TP4"), ("MDM_USB_DM", "TP5"), ("MDM_DBG_TX", "TP6"),
                 ("MDM_DBG_RX", "TP7")]:
    TP(S, ref, net, group="mtp")
# SIM: soldered M2M eSIM (MFF2) - the Lite ships with year-1 data on a bundled multi-operator M2M profile
part(S, "U8", f"{LIB}:MFF2_eSIM", "MFF2 eSIM", f"{LIB}:MFF2_eSIM_DFN-8_6x5mm",
     {"8": "SIM_VDD", "7": "SIM_RST", "6": "SIM_CLK", "3": "SIM_DATA", "1": "GND", "2": "", "4": "", "5": ""},
     mpn="M2M MFF2 eUICC (operator-supplied, e.g. Jio / Airtel / Vi IoT)", mfr="Operator / Thales / G+D",
     desc="Embedded SIM, MFF2 DFN-8, -40..105 C, soldered (vibration-proof, no holder)",
     note="Pin-out per ETSI TS 102 671 MFF2 (1 GND 2 VPP 3 I/O 6 CLK 7 RST 8 VCC) - VERIFY with the SIM vendor", group="sim")
R(S, "R11", "22R", "SIM_DATA_M", "SIM_DATA", group="sim")
R(S, "R12", "22R", "SIM_CLK_M", "SIM_CLK", group="sim")
R(S, "R13", "22R", "SIM_RST_M", "SIM_RST", group="sim")
C(S, "C17", "100nF", "SIM_VDD", "GND", group="sim")
# LTE RF: 50 R CPWG -> L-match (R14 series, C19 shunt) -> U.FL
R(S, "R14", "0R", "LTE_RF_M", "LTE_RF", fp=R0603, mpn="0603 0R jumper", group="lte")
C(S, "C19", "DNP", "LTE_RF", "GND", fp=C0603, dnp=True, mpn="0603 C0G (tune)", group="lte", note="L-match with R14: shunt C or L on the bench")
part(S, "J4", "Connector:Conn_Coaxial", "LTE ANT", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
     {"1": "LTE_RF", "2": "GND"}, mpn="U.FL-R-SMT-1(10)", mfr="Hirose",
     desc="LTE/GSM antenna: 698-2700 MHz FPC antenna with U.FL lead on the enclosure wall", group="lte")

# ================================================================== 3. GNSS
S = "gnss"
part(S, "U5", f"{LIB}:L76K", "L76K", f"{LIB}:Quectel_L76K",
     {"1": "GND", "2": "GNSS_TXD", "3": "GNSS_RXD", "4": "GNSS_1PPS", "5": "", "6": "+3V3_GNSS", "7": "",
      "8": "+3V3_GNSS", "9": "GNSS_RST_N", "10": "GND", "11": "GNSS_RF", "12": "GND", "13": "",
      "14": "", "15": "", "16": "", "17": "", "18": ""},
     mpn="L76KB-A58", mfr="Quectel", desc="GPS + BeiDou + GLONASS + QZSS receiver, L1, 10.1 x 9.7 mm LCC-18",
     note="V_BCKP tied to VCC: hot start only while GNSS_EN is high (AGNSS on cold start) - VERIFY pins vs L76K HD", group="gnss")
part(S, "U6", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "VSYS", "2": "GND", "3": "GNSS_EN", "4": "", "5": "+3V3_GNSS"},
     mpn="AP2112K-3.3TRG1", mfr="Diodes Inc", desc="LDO 3.3 V 600 mA, EN from modem GPIO (GNSS power gate)", group="gldo")
C(S, "C20", "1uF", "VSYS", "GND", fp=C0402, group="gldo")
C(S, "C21", "10uF/10V", "+3V3_GNSS", "GND", fp=C0603, group="gldo")
C(S, "C22", "100nF", "+3V3_GNSS", "GND", group="gnss")
R(S, "R15", "100k", "GNSS_EN", "GND", group="gldo")
part(S, "J5", "Connector:Conn_Coaxial", "GNSS ANT", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
     {"1": "GNSS_RF", "2": "GND"}, mpn="U.FL-R-SMT-1(10)", mfr="Hirose",
     desc="GNSS antenna: passive 25x25x4 mm ceramic L1 patch with U.FL lead, under the lid, sky-facing (L76K has an internal LNA)", group="grf")
# 1.8 V (modem) <-> 3.3 V (L76K) UART, BSS138 bidirectional shifters
part(S, "Q3", "Transistor_FET:BSS138", "BSS138", SOT23, {"1": "MDM_1V8", "2": "MDM_TX_1V8", "3": "GNSS_RXD"},
     mpn="BSS138", mfr="onsemi", desc="Level shifter: modem TXD (1.8 V) -> L76K RXD (3.3 V)", group="lvl")
part(S, "Q4", "Transistor_FET:BSS138", "BSS138", SOT23, {"1": "MDM_1V8", "2": "MDM_RX_1V8", "3": "GNSS_TXD"},
     mpn="BSS138", mfr="onsemi", desc="Level shifter: L76K TXD (3.3 V) -> modem RXD (1.8 V)", group="lvl")
R(S, "R18", "10k", "MDM_1V8", "MDM_TX_1V8", group="lvl")
R(S, "R19", "10k", "+3V3_GNSS", "GNSS_RXD", group="lvl")
R(S, "R20", "10k", "MDM_1V8", "MDM_RX_1V8", group="lvl")
R(S, "R21", "10k", "+3V3_GNSS", "GNSS_TXD", group="lvl")
TP(S, "TP8", "GNSS_RST_N", group="gtp")
TP(S, "TP9", "GNSS_1PPS", group="gtp")

# ================================================================== 4. SENSORS, VEHICLE I/O, LEDs
S = "io"
part(S, "U7", "Sensor_Motion:LIS3DH", "LIS3DH", "Package_LGA:LGA-16_3x3mm_P0.5mm_LayoutBorder3x5y",
     {"1": "MDM_1V8", "14": "MDM_1V8", "5": "GND", "10": "GND", "12": "GND", "4": "I2C_SCL", "6": "I2C_SDA",
      "7": "ACC_SA0", "8": "MDM_1V8", "11": "ACC_INT", "9": "", "2": "", "3": "", "13": "", "15": "", "16": ""},
     mpn="LIS3DHTR", mfr="STMicroelectronics", desc="3-axis accelerometer, I2C 0x18 (SA0 = GND), 2 uA low-power, wake-on-motion",
     note="Runs from VDD_EXT 1.8 V, no level shifting", group="acc")
R(S, "R34", "10k", "ACC_SA0", "GND", group="acc", note="SDO/SA0 low -> I2C address 0x18")
C(S, "C26", "100nF", "MDM_1V8", "GND", group="acc")
C(S, "C27", "1uF", "MDM_1V8", "GND", group="acc")
R(S, "R22", "4.7k", "MDM_1V8", "I2C_SDA", group="acc")
R(S, "R23", "4.7k", "MDM_1V8", "I2C_SCL", group="acc")
# ignition: NPN level translator, active-low to the modem, tolerates 0-60 V and reverse battery
C(S, "C28", "10nF/100V", "IGN_RAW", "GND", fp=C0603, group="ign")
R(S, "R24", "47k", "IGN_RAW", "IGN_B", fp=R1206, group="ign", note="IGN > ~3.5 V reads as ON")
R(S, "R25", "10k", "IGN_B", "GND", group="ign")
part(S, "Q5", "Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {"1": "IGN_B", "2": "GND", "3": "IGN_DET_N"},
     mpn="MMBT3904", mfr="onsemi", desc="Ignition sense transistor", group="ign")
R(S, "R26", "100k", "MDM_1V8", "IGN_DET_N", group="ign")
C(S, "C29", "1nF", "IGN_DET_N", "GND", group="ign")
# relay (immobiliser) low-side driver
part(S, "Q6", "Transistor_FET:AO3400A", "AO3400A", SOT23, {"1": "RELAY_G", "2": "GND", "3": "RELAY_OUT"},
     mpn="AO3400A", mfr="AOS", desc="N-MOSFET 30 V 5.7 A logic-level, relay coil <= 300 mA",
     note="Gate from 1.8 V GPIO: Rds(on) ~0.1 R at 1.8 V - VERIFY for the coil current", group="rly")
R(S, "R27", "100R", "RELAY_CTL", "RELAY_G", group="rly")
R(S, "R28", "100k", "RELAY_G", "GND", group="rly")
part(S, "D6", "Device:D", "1N4148W", "Diode_SMD:D_SOD-123", {"1": "VIN_PROT", "2": "RELAY_OUT"},
     mpn="1N4148W-7-F", mfr="Diodes Inc", desc="Relay flyback to protected supply", group="rly")
# LEDs from VSYS, driven by the modem's own NET_STATUS / STATUS pins and the charger
part(S, "Q7", "Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {"1": "NET_B", "2": "GND", "3": "LED_NET_K"},
     mpn="MMBT3904", mfr="onsemi", desc="NET LED driver", group="led1")
R(S, "R29", "4.7k", "NET_STATUS", "NET_B", group="led1")
R(S, "R30", "1k", "VSYS", "LED_NET_A", group="led1")
part(S, "D7", "Device:LED", "YELLOW", "LED_SMD:LED_0603_1608Metric", {"1": "LED_NET_K", "2": "LED_NET_A"},
     mpn="KT-0603Y", mfr="Kingbright / Hubei KENTO", desc="LED yellow 0603 - network", group="led1")
part(S, "Q8", "Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {"1": "STAT_B", "2": "GND", "3": "LED_PWR_K"},
     mpn="MMBT3904", mfr="onsemi", desc="Power LED driver", group="led2")
R(S, "R31", "4.7k", "MDM_STATUS", "STAT_B", group="led2")
R(S, "R32", "1k", "VSYS", "LED_PWR_A", group="led2")
part(S, "D8", "Device:LED", "GREEN", "LED_SMD:LED_0603_1608Metric", {"1": "LED_PWR_K", "2": "LED_PWR_A"},
     mpn="KT-0603G", mfr="Kingbright / Hubei KENTO", desc="LED green 0603 - modem on", group="led2")
R(S, "R33", "1k", "V4_BUCK", "LED_CHG_A", group="led3")
part(S, "D9", "Device:LED", "RED", "LED_SMD:LED_0603_1608Metric", {"1": "CHG_STAT", "2": "LED_CHG_A"},
     mpn="KT-0603R", mfr="Kingbright / Hubei KENTO", desc="LED red 0603 - charging", group="led3")
for x, n in enumerate(["H1", "H2", "H3", "H4"]):
    part(S, n, "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad_Via", {"1": "GND"},
         mpn="M2 self-tapping screw (enclosure boss)", group="mech")
for net, ref in [("VIN_PROT", "TP10"), ("V4_BUCK", "TP11"), ("VSYS", "TP12"), ("VBAT", "TP13"), ("MDM_1V8", "TP14"),
                 ("+3V3_GNSS", "TP15"), ("GND", "TP16"), ("GND", "TP17"), ("IGN_DET_N", "TP18")]:
    TP(S, ref, net, group="tp")


def by_ref():
    return {p["ref"]: p for p in PARTS}


def nets():
    out = {}
    for p in PARTS:
        if p["ref"].startswith("#"):
            continue
        for pin, n in p["nets"].items():
            if n:
                out.setdefault(n, []).append((p["ref"], pin))
    return out


if __name__ == "__main__":
    n = nets()
    print(len([p for p in PARTS if not p["ref"].startswith("#")]), "parts", len(n), "nets")
    for k, v in sorted(n.items()):
        if len(v) < 2:
            print("SINGLE-PIN NET", k, v)
