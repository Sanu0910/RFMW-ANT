"""CRL-TRK-2W-01 - AIS-140 two-wheeler GNSS/LTE-M tracker: single source of truth for the circuit.

Every component is declared once with its KiCad symbol, footprint, value, MPN and a pin->net map.
make_schematic.py turns this into a hierarchical KiCad schematic; make_pcb.py into the board.

Values marked VERIFY in `note` were set without the vendor datasheet at hand (vendor sites were not
reachable from the build machine) and must be checked against the datasheet before release; they are
also listed in 04_docs/VERIFY_LIST.md.
"""
from collections import OrderedDict

PROJECT = "tracker"
TITLE = "CRL-TRK-2W-01  AIS-140 Two-Wheeler Tracker"
REV = "A0"
COMPANY = "CRL / BEL - RFM Lab"

SHEETS = OrderedDict([
    ("power_in", "Power Input & Protection"),
    ("power_rails", "Charger, Battery & Rails"),
    ("mcu", "MCU, USB, Flash & Debug"),
    ("cellular", "LTE-M / NB-IoT Modem"),
    ("gnss", "GNSS L1/L5 + NavIC"),
    ("io", "Sensors & Vehicle I/O"),
])

PARTS = []


def part(sheet, ref, lib, value, fp, nets, mpn="", mfr="", desc="", dnp=False, note="", group=""):
    PARTS.append(dict(sheet=sheet, ref=ref, lib=lib, value=value, fp=fp, nets=nets, mpn=mpn, mfr=mfr,
                      desc=desc, dnp=dnp, note=note, group=group))


# ------------------------------------------------------------------ passive helpers
R0603 = "Resistor_SMD:R_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
L0402 = "Inductor_SMD:L_0402_1005Metric"


def R(sheet, ref, val, a, b, fp=R0402, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        size = {R1206: "1206", R0603: "0603"}.get(fp, "0402")
        mpn = f"{size} 1% thick film, AEC-Q200"
    part(sheet, ref, "Device:R", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Yageo / Vishay", dnp=dnp, note=note, group=group)


def C(sheet, ref, val, a, b, fp=C0402, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        mpn = {C0402: "0402", C0603: "0603", C0805: "0805", C1206: "1206", C1210: "1210"}[fp] + " MLCC X7R/X5R, AEC-Q200"
    part(sheet, ref, "Device:C", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Murata / Samsung", dnp=dnp, note=note, group=group)


def TP(sheet, ref, net, group=""):
    part(sheet, ref, "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.0mm", {"1": net},
         mpn="Test pad 1.0 mm (no part)", group=group)


# ================================================================== 1. POWER INPUT
S = "power_in"
part(S, "J1", "Connector_Generic:Conn_02x04_Top_Bottom", "VEHICLE 2x4",
     "Connector_Molex:Molex_Micro-Fit_3.0_43045-0812_2x04_P3.00mm_Vertical",
     {"1": "VIN_RAW", "2": "IGN_RAW", "3": "PANIC_RAW", "4": "DIN1_RAW",
      "5": "GND", "6": "AIN1_RAW", "7": "DOUT1", "8": "GND"},
     mpn="43045-0812", mfr="Molex", desc="Micro-Fit 3.0 2x4 vertical header, harness via IP67 gland",
     note="1 +12V(BAT) 2 IGN 3 PANIC(SOS, to GND) 4 DIN1 5 GND 6 AIN1 7 DOUT1(relay low side) 8 GND", group="vin")
part(S, "F1", "Device:Fuse", "2A", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VIN_F"},
     mpn="0466002.NRHF", mfr="Littelfuse", desc="Fuse 2 A fast 63 V 1206 (plus 3 A blade fuse in harness)",
     note="VERIFY MPN suffix", group="vin")
part(S, "D1", "Device:D_TVS", "SMBJ33CA", "Diode_SMD:D_SMB", {"1": "VIN_F", "2": "GND"},
     mpn="SMBJ33CA", mfr="Littelfuse", desc="TVS 600 W bidirectional 33 V stand-off (reverse battery safe)", group="vin")
part(S, "Q1", "Transistor_FET:BUK7M12-60EX", "BUK7M12-60EX", "Package_TO_SOT_SMD:LFPAK33",
     {"4": "RP_GATE", "5": "VIN_PROT", "1": "VIN_F", "2": "VIN_F", "3": "VIN_F"},
     mpn="BUK7M12-60EX", mfr="Nexperia", desc="N-MOSFET 60 V 12 mOhm AEC-Q101, ideal-diode pass FET", group="vin")
part(S, "U1", "Power_Management:LM74700", "LM74700-Q1", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "RP_VCAP", "2": "GND", "3": "VIN_F", "4": "VIN_PROT", "5": "RP_GATE", "6": "VIN_F"},
     mpn="LM74700QDBVRQ1", mfr="TI", desc="Ideal diode controller, reverse battery protection, AEC-Q100",
     note="EN tied to ANODE (always on)", group="vin")
C(S, "C1", "100nF/16V", "RP_VCAP", "VIN_F", note="VCAP to ANODE", group="vin", fp=C0603)
C(S, "C2", "100nF/100V", "VIN_PROT", "GND", group="vin", fp=C0603)
part(S, "C3", "Device:C_Polarized", "22uF/63V", "Capacitor_SMD:CP_Elec_6.3x7.7", {"1": "VIN_PROT", "2": "GND"},
     mpn="EEE-FK1J220P", mfr="Panasonic", desc="Al-electrolytic 22 uF 63 V, AEC-Q200, bulk / input damping", group="vin")
part(S, "FB1", "Device:FerriteBead_Small", "600R@100M", "Inductor_SMD:L_0805_2012Metric",
     {"1": "VIN_PROT", "2": "VIN_BUCK"}, mpn="BLM21PG601SN1D", mfr="Murata",
     desc="Ferrite bead 600 R 0805 1.5 A, conducted-EMI pi filter", note="VERIFY MPN / AEC-Q200 variant", group="buck")
C(S, "C4", "2.2uF/100V", "VIN_BUCK", "GND", fp=C1210, group="buck")
C(S, "C5", "2.2uF/100V", "VIN_BUCK", "GND", fp=C1210, group="buck")
C(S, "C6", "100nF/100V", "VIN_BUCK", "GND", group="buck", fp=C0603)
part(S, "U2", "Regulator_Switching:LM5164DDA", "LM5164-Q1",
     "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm_ThermalVias",
     {"1": "GND", "2": "VIN_BUCK", "3": "BUCK_EN", "4": "BUCK_RON", "5": "BUCK_FB", "6": "BUCK_PG",
      "7": "BUCK_BST", "8": "BUCK_SW", "9": "GND"},
     mpn="LM5164QDDARQ1", mfr="TI", desc="100 V 1 A sync buck, 10 uA IQ, AEC-Q100", group="buck")
R(S, "R1", "1M", "VIN_BUCK", "BUCK_EN", fp=R0603, group="buck", note="UVLO start ~6.0 V with R2 (EN 1.5 V), 10 uA VERIFY")
R(S, "R2", "330k", "BUCK_EN", "GND", group="buck")
R(S, "R3", "160k", "BUCK_RON", "GND", group="buck", note="RON sets COT fsw ~300 kHz - VERIFY with LM5164 eq.")
R(S, "R4", "316k", "V5_BUCK", "BUCK_FB", fp=R0603, group="buck", note="VOUT = 1.2 V x (1 + R4/R5) = 5.0 V")
R(S, "R5", "100k", "BUCK_FB", "GND", group="buck")
C(S, "C7", "2.2nF/50V", "BUCK_BST", "BUCK_SW", group="buck")
R(S, "R6", "100k", "BUCK_PG", "V5_BUCK", fp=R0603, group="buck")
part(S, "L1", "Device:L", "22uH", "Inductor_SMD:L_Bourns_SRN6045TA", {"1": "BUCK_SW", "2": "V5_BUCK"},
     mpn="SRN6045TA-220M", mfr="Bourns", desc="22 uH semi-shielded power inductor 6x6 mm", group="buck")
C(S, "C8", "22uF/10V", "V5_BUCK", "GND", fp=C1206, group="buck")
C(S, "C9", "22uF/10V", "V5_BUCK", "GND", fp=C1206, group="buck")
part(S, "D2", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123", {"1": "V5_IN", "2": "V5_BUCK"},
     mpn="B5819W", mfr="MDD / Diodes Inc", desc="Schottky 40 V 1 A, OR-ing buck -> charger", group="buck")
R(S, "R7", "1M", "VIN_PROT", "VIN_SENSE", fp=R1206, group="vsense")
R(S, "R8", "68k", "VIN_SENSE", "GND", group="vsense", note="VIN 0-50 V -> 0-3.2 V (ADC1_CH0), 12 uA")
C(S, "C10", "100nF", "VIN_SENSE", "GND", group="vsense", fp=C0603)
part(S, "D3", "Diode:BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "+3V3", "3": "VIN_SENSE"},
     mpn="BAT54S", mfr="Nexperia", desc="Dual Schottky clamp to rails", group="vsense")
for i, n in enumerate(["VIN_RAW", "VIN_F", "V5_BUCK", "GND", "VIN_BUCK"]):
    part(S, f"#FLG{10 + i}", "power:PWR_FLAG", "PWR_FLAG", "", {"1": n})

# ================================================================== 2. CHARGER & RAILS
S = "power_rails"
part(S, "D4", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123", {"1": "V5_IN", "2": "VBUS"},
     mpn="B5819W", mfr="MDD / Diodes Inc", desc="Schottky OR-ing USB VBUS -> charger", group="chg")
part(S, "U3", "Battery_Management:BQ24074RGT", "BQ24074", "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm",
     {"1": "BAT_TS", "2": "VBAT", "3": "VBAT", "4": "GND", "5": "VSYS", "6": "GND", "7": "PGOOD_N",
      "8": "GND", "9": "CHG_N", "10": "VSYS", "11": "VSYS", "12": "CHG_ILIM", "13": "V5_IN",
      "14": "", "15": "CHG_ITERM", "16": "CHG_ISET", "17": "GND"},
     mpn="BQ24074RGTR", mfr="TI", desc="1-cell Li-ion charger with power path, 10.5 V OVP, OUT reg 4.4 V",
     note="EN2=1/EN1=0 -> ILIM resistor mode; CE low = charge enabled; TMR open = default safety timers (VERIFY)", group="chg")
C(S, "C11", "1uF/25V", "V5_IN", "GND", group="chg", fp=C0603)
C(S, "C12", "10uF/10V", "VSYS", "GND", fp=C0805, group="chg")
C(S, "C13", "4.7uF/10V", "VBAT", "GND", fp=C0805, group="chg")
R(S, "R9", "1.5k", "CHG_ILIM", "GND", group="chg", note="IIN_MAX = 1550/R = 1.03 A  VERIFY K_ILIM")
R(S, "R10", "1.78k", "CHG_ISET", "GND", group="chg", note="ICHG = 890/R = 500 mA  VERIFY K_ISET")
R(S, "R11", "15k", "CHG_ITERM", "GND", group="chg", note="termination ~10 % ICHG VERIFY")
R(S, "R13", "10k", "BAT_TS", "GND", dnp=True, group="chg", note="fit only when the pack has no NTC")
R(S, "R14", "100k", "PGOOD_N", "+3V3", group="chg")
part(S, "J2", "Connector_Generic_MountingPin:Conn_01x03_MountingPin", "BATTERY 18650",
     "Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal",
     {"1": "VBAT", "2": "BAT_TS", "3": "GND", "MP": "GND"}, mpn="S3B-PH-SM4-TB(LF)(SN)", mfr="JST",
     desc="Battery pack: 1S 18650 with PCM + 10k NTC (103AT) - 1 BAT+ 2 NTC 3 BAT-", group="bat")
R(S, "R15", "1M", "VBAT", "VBAT_SENSE", group="bat")
R(S, "R16", "1M", "VBAT_SENSE", "GND", group="bat", note="VBAT/2 -> ADC1_CH1, 2.1 uA")
C(S, "C14", "100nF", "VBAT_SENSE", "GND", group="bat")
part(S, "U4", "Battery_Management:LC709203FQH-01TWG", "LC709203F", "Package_DFN_QFN:WDFN-8-1EP_4x3mm_P0.65mm_EP2.4x1.8mm",
     {"1": "GND", "2": "GND", "3": "VBAT", "4": "ALERT_N", "5": "", "6": "", "7": "I2C_SDA", "8": "I2C_SCL", "9": "GND"},
     mpn="LC709203FQH-01TWG", mfr="onsemi", desc="Fuel gauge, I2C 0x0B, 2 uA sleep (stands in for MAX17048)",
     note="Temperature via I2C (host writes IMU temp); TSW/TSENSE unused VERIFY", group="bat")
C(S, "C15", "100nF", "VBAT", "GND", group="bat")
part(S, "U5", "Regulator_Linear:TLV75733PDBV", "TLV75733P", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "VSYS", "2": "GND", "3": "VSYS", "4": "", "5": "+3V3"},
     mpn="TLV75733PDBVR", mfr="TI", desc="LDO 3.3 V 1 A, 25 uA IQ, always-on logic rail", group="ldo")
C(S, "C16", "1uF/10V", "VSYS", "GND", group="ldo", fp=C0603)
C(S, "C17", "10uF/10V", "+3V3", "GND", fp=C0805, group="ldo")
part(S, "U6", "Power_Management:TPS22917DBV", "TPS22917", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "VSYS", "2": "GND", "3": "MDM_PWR_EN", "4": "MDM_SW_CT", "5": "MDM_SW_QOD", "6": "VBAT_MDM"},
     mpn="TPS22917DBVR", mfr="TI", desc="Load switch 2 A: modem VBAT hard power-cycle (watchdog)",
     note="QOD via R to VOUT = quick output discharge", group="msw")
R(S, "R51", "100R", "MDM_SW_QOD", "VBAT_MDM", group="msw")
C(S, "C18", "1nF", "MDM_SW_CT", "GND", group="msw")
R(S, "R17", "100k", "MDM_PWR_EN", "GND", group="msw")
part(S, "U7", "Power_Management:TPS22917DBV", "TPS22917", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "+3V3", "2": "GND", "3": "GNSS_PWR_EN", "4": "GNSS_SW_CT", "5": "GNSS_SW_QOD", "6": "+3V3_GNSS"},
     mpn="TPS22917DBVR", mfr="TI", desc="Load switch: GNSS VCC (V_BCKP stays on for hot start)", group="gsw")
C(S, "C19", "1nF", "GNSS_SW_CT", "GND", group="gsw")
R(S, "R52", "100R", "GNSS_SW_QOD", "+3V3_GNSS", group="gsw")
R(S, "R18", "100k", "GNSS_PWR_EN", "GND", group="gsw")
for i, n in enumerate(["V5_IN"]):
    part(S, f"#FLG{20 + i}", "power:PWR_FLAG", "PWR_FLAG", "", {"1": n})

# ================================================================== 3. MCU
S = "mcu"
esp = {"1": "GND", "40": "GND", "41": "GND", "2": "+3V3", "3": "ESP_EN",
       "39": "VIN_SENSE", "38": "VBAT_SENSE", "15": "PGOOD_N", "4": "AIN1_SENSE", "5": "IGN_DET", "6": "PANIC_DET",
       "7": "DIN1_DET", "12": "I2C_SDA", "17": "I2C_SCL", "18": "FLASH_CS", "19": "FLASH_MOSI", "20": "FLASH_SCK",
       "21": "FLASH_MISO", "22": "IMU_INT", "8": "MCU_TX_MDM", "9": "MCU_RX_MDM", "10": "MDM_DTR_3V3",
       "11": "MDM_RI_3V3", "13": "USB_DM", "14": "USB_DP", "23": "MDM_PWRKEY_CTL", "28": "MDM_STATUS_3V3",
       "29": "MDM_PWR_EN", "30": "GNSS_PWR_EN", "31": "ALERT_N", "32": "JTAG_TCK", "33": "JTAG_TDO",
       "34": "JTAG_TDI", "35": "JTAG_TMS", "36": "U0RXD", "37": "U0TXD", "26": "LED_STAT", "16": "DOUT1_CTL",
       "24": "GNSS_TXD_MCU", "25": "GNSS_RXD_MCU", "27": "BOOT"}
part(S, "U8", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N8R2", "tracker:ESP32-S3-WROOM-1_EdgeAntenna", esp,
     mpn="ESP32-S3-WROOM-1-N8R2", mfr="Espressif", desc="Wi-Fi/BLE5 MCU module, 8 MB flash, 2 MB quad PSRAM",
     note="Quad PSRAM keeps IO35-37 free", group="mcu")
C(S, "C20", "22uF/10V", "+3V3", "GND", fp=C0805, group="mcu")
C(S, "C21", "100nF", "+3V3", "GND", group="mcu")
R(S, "R19", "10k", "+3V3", "ESP_EN", group="mcu")
C(S, "C22", "1uF", "ESP_EN", "GND", group="mcu", fp=C0603)
R(S, "R20", "10k", "+3V3", "BOOT", group="mcu")
part(S, "SW1", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "ESP_EN", "2": "GND"},
     mpn="TS-1187A-B-A-B", mfr="XKB", desc="Tact switch 5.1x5.1 mm", group="mcu")
part(S, "SW2", "Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "BOOT", "2": "GND"},
     mpn="TS-1187A-B-A-B", mfr="XKB", desc="Tact switch 5.1x5.1 mm", group="mcu")
part(S, "J3", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A5": "USB_CC1", "B5": "USB_CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
      "A8": "", "B8": "", "S1": "GND"},
     mpn="TYPE-C-31-M-12", mfr="Korean Hroparts", desc="USB-C 2.0 receptacle (service: flash, JTAG, logs, charge)", group="usb")
R(S, "R21", "5.1k", "USB_CC1", "GND", group="usb")
R(S, "R22", "5.1k", "USB_CC2", "GND", group="usb")
part(S, "U9", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "VBUS"},
     mpn="USBLC6-2SC6", mfr="STMicroelectronics", desc="USB ESD protection", group="usb")
part(S, "U10", "Memory_Flash:W25Q128JVS", "W25Q128JV", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
     {"1": "FLASH_CS", "2": "FLASH_MISO", "3": "FLASH_WP", "4": "GND", "5": "FLASH_MOSI", "6": "FLASH_SCK",
      "7": "FLASH_HOLD", "8": "+3V3"},
     mpn="W25Q128JVSIQ", mfr="Winbond", desc="128 Mbit SPI NOR flash - offline track log (AIS-140 store-and-forward)", group="flash")
C(S, "C23", "100nF", "+3V3", "GND", group="flash")
R(S, "R23", "10k", "+3V3", "FLASH_CS", group="flash")
R(S, "R53", "10k", "+3V3", "FLASH_WP", group="flash")
R(S, "R54", "10k", "+3V3", "FLASH_HOLD", group="flash")
# Production programming / JTAG header: pogo test pads (fixture) - native USB-C covers bench use
for ref, net in (("TP21", "JTAG_TMS"), ("TP22", "JTAG_TCK"), ("TP23", "JTAG_TDO"), ("TP24", "JTAG_TDI"),
                 ("TP25", "U0TXD"), ("TP26", "U0RXD"), ("TP27", "ESP_EN"), ("TP28", "BOOT")):
    TP(S, ref, net, group="dbg")
R(S, "R24", "1k", "LED_STAT", "LED_STAT_A", group="led")
part(S, "D5", "Device:LED", "GREEN", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LED_STAT_A"},
     mpn="LTST-C191KGKT", mfr="Lite-On", desc="LED green 0603 - system status", group="led")
R(S, "R25", "1k", "+3V3", "LED_CHG_A", group="led")
part(S, "D6", "Device:LED", "RED", "LED_SMD:LED_0603_1608Metric", {"1": "CHG_N", "2": "LED_CHG_A"},
     mpn="LTST-C191KRKT", mfr="Lite-On", desc="LED red 0603 - charging", group="led")

# ================================================================== 4. CELLULAR
S = "cellular"
sim = {"34": "VBAT_MDM", "35": "VBAT_MDM", "40": "MDM_1V8",
       "1": "MDM_TXD_1V8", "2": "MDM_RXD_1V8", "6": "MDM_DTR_1V8", "7": "MDM_RI_1V8", "42": "MDM_STATUS_1V8",
       "41": "NETLIGHT", "39": "MDM_PWRKEY", "15": "SIM_DATA_M", "16": "SIM_CLK_M", "17": "SIM_RST_M", "18": "SIM_VDD",
       "32": "LTE_RF_M", "24": "MDM_USB_VBUS", "25": "MDM_USB_DP", "26": "MDM_USB_DM", "20": "MDM_USB_BOOT",
       "22": "MDM_DBG_TX"}
for n in [8, 13, 19, 21, 27, 30, 31, 33, 36, 37, 45, 63, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77]:
    sim[str(n)] = "GND"
for n in [3, 4, 5, 9, 10, 11, 12, 14, 23, 28, 29, 38, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
          59, 60, 61, 62, 64, 65, 68]:
    sim[str(n)] = ""
part(S, "U11", "tracker:SIM7080G", "SIM7080G", "tracker:SIMCom_SIM7080G_LCC-77", sim,
     mpn="SIM7080G", mfr="SIMCom", desc="LTE Cat-M1/NB-IoT module, 3 uA PSM, India bands B3/B5/B8/B28",
     note="Internal GNSS unused (no NavIC); NEO-F10N used instead", group="mdm")
C(S, "C24", "100uF/6.3V", "VBAT_MDM", "GND", fp=C1210, group="mdm")
C(S, "C25", "10uF/10V", "VBAT_MDM", "GND", fp=C0805, group="mdm")
C(S, "C26", "100nF", "VBAT_MDM", "GND", fp=C0402, group="mdm")
C(S, "C27", "33pF", "VBAT_MDM", "GND", fp=C0402, mpn="0402 C0G 50V", group="mdm")
C(S, "C28", "10pF", "VBAT_MDM", "GND", fp=C0402, mpn="0402 C0G 50V", group="mdm")
part(S, "D7", "Device:D_Zener", "SMF5.0A", "Diode_SMD:D_SOD-123F", {"1": "VBAT_MDM", "2": "GND"},
     mpn="SMF5.0A", mfr="Littelfuse", desc="TVS 200 W 5 V on modem VBAT (SIMCom recommendation)", group="mdm")
C(S, "C29", "100nF", "MDM_1V8", "GND", fp=C0402, group="lvl")
part(S, "U12", "Logic_LevelTranslator:TXS0108EPW", "TXS0108E", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
     {"1": "MDM_TXD_1V8", "2": "MDM_1V8", "3": "MDM_RXD_1V8", "4": "MDM_DTR_1V8", "5": "MDM_RI_1V8",
      "6": "MDM_STATUS_1V8", "7": "", "8": "", "9": "", "10": "MDM_1V8", "11": "GND",
      "12": "", "13": "", "14": "", "15": "MDM_STATUS_3V3", "16": "MDM_RI_3V3", "17": "MDM_DTR_3V3",
      "18": "MCU_TX_MDM", "19": "+3V3", "20": "MCU_RX_MDM"},
     mpn="TXS0108EPWR", mfr="TI", desc="1.8 V <-> 3.3 V translator; OE from VDD_EXT so it is Hi-Z while modem is off",
     group="lvl")
C(S, "C30", "100nF", "+3V3", "GND", fp=C0402, group="lvl")
part(S, "Q2", "Transistor_FET:2N7002", "2N7002", "Package_TO_SOT_SMD:SOT-23",
     {"1": "MDM_PWRKEY_CTL", "2": "GND", "3": "MDM_PWRKEY"}, mpn="2N7002K-7", mfr="Diodes Inc",
     desc="Open-drain PWRKEY driver (PWRKEY has internal pull-up, never tie to GND)", group="pwk")
R(S, "R26", "100k", "MDM_PWRKEY_CTL", "GND", group="pwk")
part(S, "Q3", "Transistor_BJT:MMBT3904", "MMBT3904", "Package_TO_SOT_SMD:SOT-23",
     {"1": "NETLIGHT_B", "2": "GND", "3": "LED_NET_K"}, mpn="MMBT3904", mfr="onsemi", desc="NETLIGHT LED driver", group="net")
R(S, "R27", "4.7k", "NETLIGHT", "NETLIGHT_B", group="net")
R(S, "R28", "1k", "+3V3", "LED_NET_A", group="net")
part(S, "D8", "Device:LED", "YELLOW", "LED_SMD:LED_0603_1608Metric", {"1": "LED_NET_K", "2": "LED_NET_A"},
     mpn="LTST-C191KSKT", mfr="Lite-On", desc="LED yellow 0603 - network", group="net")
part(S, "J5", "Connector:SIM_Card_Shielded", "NANO-SIM", "Connector_Card:nanoSIM_GCT_SIM8060-6-0-14-00",
     {"1": "SIM_VDD", "2": "SIM_RST", "3": "SIM_CLK", "5": "GND", "6": "", "7": "SIM_DATA", "SH": "GND"},
     mpn="SIM8060-6-0-14-00-A", mfr="GCT", desc="Nano-SIM push-pull holder (dev / non-eSIM builds)",
     note="AIS-140 production: replace by MFF2 eSIM on the same SIM bus (rev B footprint)", group="sim")
R(S, "R29", "22R", "SIM_DATA_M", "SIM_DATA", group="sim")
R(S, "R30", "22R", "SIM_CLK_M", "SIM_CLK", group="sim")
R(S, "R31", "22R", "SIM_RST_M", "SIM_RST", group="sim")
C(S, "C31", "100nF", "SIM_VDD", "GND", fp=C0402, group="sim")
part(S, "U13", "Power_Protection:ESDA6V1-5SC6", "ESDA6V1-5SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "SIM_DATA", "2": "GND", "3": "SIM_CLK", "4": "SIM_RST", "5": "SIM_VDD", "6": ""},
     mpn="ESDA6V1-5SC6", mfr="STMicroelectronics", desc="SIM ESD array (<50 pF)", group="sim")
C(S, "C32", "DNP", "LTE_RF_M", "GND", fp=C0402, dnp=True, mpn="0402 C0G (tune)", group="lte")
R(S, "R32", "0R", "LTE_RF_M", "LTE_RF", fp="Resistor_SMD:R_0402_1005Metric", mpn="0402 0R jumper", group="lte")
C(S, "C33", "DNP", "LTE_RF", "GND", fp=C0402, dnp=True, mpn="0402 C0G (tune)", group="lte")
part(S, "J6", "Connector:Conn_Coaxial", "LTE ANT", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
     {"1": "LTE_RF", "2": "GND"}, mpn="U.FL-R-SMT-1(10)", mfr="Hirose",
     desc="LTE antenna: 698-2700 MHz flex PCB antenna on enclosure wall (e.g. Taoglas FXUB63)", group="lte")
for net, ref in [("MDM_USB_VBUS", "TP1"), ("MDM_USB_DP", "TP2"), ("MDM_USB_DM", "TP3"), ("MDM_USB_BOOT", "TP4"),
                 ("MDM_DBG_TX", "TP5")]:
    TP(S, ref, net, group="mtp")

# ================================================================== 5. GNSS
S = "gnss"
part(S, "U14", "tracker:NEO-F10N", "NEO-F10N", "RF_GPS:ublox_NEO",
     {"23": "+3V3_GNSS", "22": "+3V3", "9": "GNSS_VCC_RF", "8": "GNSS_RST_N", "1": "GNSS_SAFEBOOT_N",
      "4": "", "14": "", "11": "GNSS_RF_M", "20": "GNSS_TXD", "21": "GNSS_RXD", "3": "GNSS_TP",
      "2": "", "5": "", "6": "", "7": "", "15": "", "16": "", "17": "", "18": "", "19": "",
      "10": "GND", "12": "GND", "13": "GND", "24": "GND"},
     mpn="NEO-F10N-00B", mfr="u-blox", desc="L1/L5 dual-band GNSS, GPS/GAL/BDS/QZSS + NavIC (AIS-140), -167 dBm",
     group="gnss")
C(S, "C34", "10uF/10V", "+3V3_GNSS", "GND", fp=C0805, group="gnss")
C(S, "C35", "100nF", "+3V3_GNSS", "GND", fp=C0402, group="gnss")
C(S, "C36", "100nF", "+3V3", "GND", fp=C0402, group="gnss", note="V_BCKP: always-on for hot start")
R(S, "R33", "1k", "GNSS_TXD", "GNSS_TXD_MCU", group="gnss", note="limits back-power while GNSS VCC is off")
R(S, "R34", "1k", "GNSS_RXD_MCU", "GNSS_RXD", group="gnss")
R(S, "R35", "10R", "GNSS_VCC_RF", "GNSS_BIAS", group="bias", note="u-blox R17 10 R short-circuit limiter")
C(S, "C37", "10nF", "GNSS_BIAS", "GND", fp=C0402, group="bias")
part(S, "L2", "Device:L", "47nH", L0402, {"1": "GNSS_BIAS", "2": "GNSS_RF"}, mpn="LQG15HS47NJ02D", mfr="Murata",
     desc="Bias-T choke, >500 R at L1/L5 (u-blox integration manual)", note="DNP L2+R35 for a passive antenna", group="bias")
C(S, "C38", "DNP", "GNSS_RF_M", "GND", fp=C0402, dnp=True, mpn="0402 C0G (tune)", group="grf")
R(S, "R36", "0R", "GNSS_RF_M", "GNSS_RF", fp="Resistor_SMD:R_0402_1005Metric", mpn="0402 0R jumper", group="grf")
C(S, "C39", "DNP", "GNSS_RF", "GND", fp=C0402, dnp=True, mpn="0402 C0G (tune)", group="grf")
part(S, "J7", "Connector:Conn_Coaxial", "GNSS ANT", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
     {"1": "GNSS_RF", "2": "GND"}, mpn="U.FL-R-SMT-1(10)", mfr="Hirose",
     desc="GNSS antenna: active L1/L5 patch (gain <= 25 dB) under the lid, sky-facing", group="grf")
TP(S, "TP6", "GNSS_RST_N", group="gtp")
TP(S, "TP7", "GNSS_SAFEBOOT_N", group="gtp")
TP(S, "TP8", "GNSS_TP", group="gtp")

# ================================================================== 6. SENSORS & VEHICLE I/O
S = "io"
part(S, "U15", "Sensor_Motion:IIM-42652", "IIM-42652", "Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm",
     {"1": "GND", "2": "", "3": "", "4": "IMU_INT", "5": "+3V3", "6": "GND", "7": "GND", "8": "+3V3",
      "9": "", "10": "", "11": "", "12": "+3V3", "13": "I2C_SCL", "14": "I2C_SDA"},
     mpn="IIM-42652", mfr="TDK InvenSense", desc="6-axis IMU, -40..105 C industrial (ICM-42688 family), I2C 0x68",
     note="Wake-on-motion, tilt/fall + crash (+-16 g) detection", group="imu")
C(S, "C40", "100nF", "+3V3", "GND", fp=C0402, group="imu")
C(S, "C41", "100nF", "+3V3", "GND", fp=C0402, group="imu")
part(S, "U16", "Timer_RTC:RV-3028-C7", "RV-3028-C7", "Package_SON:MicroCrystal_C7_SON-8_1.5x3.2mm_P0.9mm",
     {"1": "", "2": "ALERT_N", "3": "I2C_SCL", "4": "I2C_SDA", "5": "GND", "6": "VBAT", "7": "+3V3", "8": "TAMPER_N"},
     mpn="RV-3028-C7 32.768kHz 1ppm-TA-QC", mfr="Micro Crystal", desc="RTC 45 nA, I2C 0x52, EVI = lid tamper time-stamp",
     group="rtc")
C(S, "C42", "100nF", "+3V3", "GND", fp=C0402, group="rtc")
R(S, "R37", "10k", "+3V3", "TAMPER_N", group="rtc")
TP(S, "TP9", "TAMPER_N", group="rtc")
R(S, "R38", "4.7k", "+3V3", "I2C_SDA", group="i2c")
R(S, "R39", "4.7k", "+3V3", "I2C_SCL", group="i2c")
R(S, "R40", "10k", "+3V3", "ALERT_N", group="i2c")
# ignition (active high 12 V)
C(S, "C43", "10nF/100V", "IGN_RAW", "GND", group="ign", fp=C0603)
R(S, "R41", "100k", "IGN_RAW", "IGN_DET", fp=R1206, group="ign")
R(S, "R42", "22k", "IGN_DET", "GND", group="ign", note="14.4 V -> 2.6 V; IGN > ~7 V reads high")
C(S, "C44", "100nF", "IGN_DET", "GND", group="ign")
part(S, "D9", "Diode:BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "+3V3", "3": "IGN_DET"},
     mpn="BAT54S", mfr="Nexperia", desc="Clamp", group="ign")
# panic / SOS button to GND
C(S, "C45", "10nF/100V", "PANIC_RAW", "GND", group="pan", fp=C0603)
R(S, "R43", "4.7k", "PANIC_RAW", "PANIC_DET", fp=R1206, group="pan")
R(S, "R44", "47k", "+3V3", "PANIC_DET", group="pan")
C(S, "C46", "100nF", "PANIC_DET", "GND", group="pan")
part(S, "D10", "Diode:BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "+3V3", "3": "PANIC_DET"},
     mpn="BAT54S", mfr="Nexperia", desc="Clamp", group="pan")
# digital input 1 (active high 12 V)
C(S, "C47", "10nF/100V", "DIN1_RAW", "GND", group="din", fp=C0603)
R(S, "R45", "100k", "DIN1_RAW", "DIN1_DET", fp=R1206, group="din")
R(S, "R46", "22k", "DIN1_DET", "GND", group="din")
C(S, "C48", "100nF", "DIN1_DET", "GND", group="din")
part(S, "D11", "Diode:BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "+3V3", "3": "DIN1_DET"},
     mpn="BAT54S", mfr="Nexperia", desc="Clamp", group="din")
# analog input 0-30 V
C(S, "C49", "10nF/100V", "AIN1_RAW", "GND", group="ain", fp=C0603)
R(S, "R47", "100k", "AIN1_RAW", "AIN1_SENSE", fp=R1206, group="ain")
R(S, "R48", "10k", "AIN1_SENSE", "GND", group="ain", note="0-30 V -> 0-2.73 V (ADC1_CH3)")
C(S, "C50", "100nF", "AIN1_SENSE", "GND", group="ain")
part(S, "D12", "Diode:BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "+3V3", "3": "AIN1_SENSE"},
     mpn="BAT54S", mfr="Nexperia", desc="Clamp", group="ain")
# digital output: immobiliser relay low-side driver
part(S, "Q4", "Transistor_FET:BUK9M53-60EX", "BUK9M53-60EX", "Package_TO_SOT_SMD:LFPAK33",
     {"4": "DOUT1_G", "5": "DOUT1", "1": "GND", "2": "GND", "3": "GND"}, mpn="BUK9M53-60EX", mfr="Nexperia",
     desc="Logic-level N-MOSFET 60 V AEC-Q101, relay coil <= 500 mA", group="dout")
R(S, "R49", "100R", "DOUT1_CTL", "DOUT1_G", group="dout")
R(S, "R50", "100k", "DOUT1_G", "GND", group="dout", note="holds IO46 strap low at boot")
part(S, "D13", "Device:D", "1N4148W", "Diode_SMD:D_SOD-123", {"1": "VIN_PROT", "2": "DOUT1"},
     mpn="1N4148W-7-F", mfr="Diodes Inc", desc="Relay flyback to protected supply", group="dout")
for i, (x, n) in enumerate([(0, "H1"), (1, "H2"), (2, "H3"), (3, "H4")]):
    part(S, n, "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad_Via", {"1": "GND"},
         mpn="M2 self-tapping screw (enclosure boss)", group="mech")
for net, ref in [("VIN_PROT", "TP10"), ("V5_IN", "TP11"), ("VSYS", "TP12"), ("VBAT", "TP13"), ("+3V3", "TP14"),
                 ("VBAT_MDM", "TP15"), ("+3V3_GNSS", "TP16"), ("GND", "TP17"), ("GND", "TP18"), ("IGN_DET", "TP19"),
                 ("PANIC_DET", "TP20")]:
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
