"""SPS-24G-01 - "Smart Bathroom Presence Sensor Switch": single source of truth for the circuit.

A standalone (no WiFi / no BLE) automatic light switch for a standard Indian modular wall box (86 x 86 mm):

  * 24 GHz mmWave presence radar (Hi-Link HLK-LD2410B, 5-pin module) detects a person - moving or still.
  * ATtiny13A-SU (SOIC-8) reads the radar OUT line, drives the lamp through a zero-cross opto-triac and
    a BTA16-600B triac, and holds the lamp on for an adjustable "no-one" delay (10 s ... 10 min, trimmer).
  * Mains power from a Hi-Link HLK-PM01 isolated 5 V / 3 W AC-DC module (85-265 VAC in).
  * Input protection: T500 mA fuse, 14D471K MOV, 5D-9 NTC inrush limiter, 100 nF X2 class-Y EMI cap + bleeder.
  * UI: 6 x 6 mm manual-override push button, status/fault LED, 10 k delay trimmer.
  * 45 x 45 mm, 2-layer 1.6 mm FR-4, 1 oz, ENIG. HIGH-VOLTAGE (AC) section and LOW-VOLTAGE (SELV) section
    are kept apart with >= 6 mm creepage / >= 3 mm clearance and a routed isolation slot; the only parts that
    cross the barrier are the two isolating devices (HLK-PM01 and the MOC3063 opto).

!! MAINS VOLTAGE !! This is an engineering design, not a certified product. Every value marked VERIFY and the
whole mains section must be reviewed by a qualified engineer and type-tested (IEC 60669-2-1 / IEC 61058,
BIS IS 60669, creepage/clearance per IEC 60664-1, HIPOT, EMC) before any board is connected to the mains.
See 04_docs/SAFETY_REVIEW.md. Every component is declared once with its KiCad symbol, footprint, value, MPN
and a pin->net map; make_schematic.py turns this into the schematic and make_pcb.py into the board.
"""
from collections import OrderedDict

PROJECT = "bps_switch"
PN = "SPS-24G-01"
TITLE = "SPS-24G-01  Smart Presence Sensor Switch"
REV = "A0"
COMPANY = "SAMAY ELECTRONICS"
LIB = "bps"               # project symbol / footprint library nickname

SHEETS = OrderedDict([
    ("power", "AC Input Protection, Isolated 5 V Supply"),
    ("load", "Zero-Cross Opto-Triac AC Load Control"),
    ("mcu", "ATtiny13A Controller & ISP"),
    ("io", "Radar, Button, LED, Delay Trimmer"),
])

PARTS = []


def part(sheet, ref, lib, value, fp, nets, mpn="", mfr="", desc="", dnp=False, note="", group=""):
    PARTS.append(dict(sheet=sheet, ref=ref, lib=lib, value=value, fp=fp, nets=nets, mpn=mpn, mfr=mfr,
                      desc=desc, dnp=dnp, note=note, group=group))


# ------------------------------------------------------------------ package helpers
R0603 = "Resistor_SMD:R_0603_1608Metric"
R0805 = "Resistor_SMD:R_0805_2012Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
# through-hole axial resistors for the HV side (voltage rating + creepage)
RAX_P10 = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"       # ~0.25-0.4 W
RAX_P1524 = "Resistor_THT:R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal"     # ~1-2 W


def R(sheet, ref, val, a, b, fp=R0603, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        size = {R0805: "0805", RAX_P10: "axial 0.4 W", RAX_P1524: "axial 2 W MO"}.get(fp, "0603")
        mpn = f"{size} 1% thick film" if "axial" not in str(size) else size
    part(sheet, ref, "Device:R", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Yageo / Uniroyal", dnp=dnp, note=note, group=group)


def C(sheet, ref, val, a, b, fp=C0603, mpn=None, dnp=False, note="", group=""):
    if mpn is None:
        mpn = {C0603: "0603", C0805: "0805"}.get(fp, "0603") + " MLCC X7R 50V"
    part(sheet, ref, "Device:C", val, fp, {"1": a, "2": b}, mpn=mpn, mfr="Samsung / Murata", dnp=dnp, note=note, group=group)


def TP(sheet, ref, net, group="tp"):
    part(sheet, ref, "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.5mm", {"1": net},
         mpn="Test pad 1.5 mm (no part)", group=group)


# ================================================================== 1. AC INPUT + ISOLATED SUPPLY  (HIGH VOLTAGE)
S = "power"
part(S, "J1", "Connector:Screw_Terminal_01x03", "L / N / LAMP",
     "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal",
     {"1": "ACL_IN", "2": "ACN", "3": "LAMP"},
     mpn="MKDS 1,5/3-5.08 (or MX126-5.0-03P)", mfr="Phoenix Contact / MaiXu",
     desc="3-pole 5.0 mm rising-cage screw terminal, >=300 V / 10 A: 1=Line in, 2=Neutral, 3=Lamp (switched Line out)",
     note="Lamp returns to Neutral externally. Mark L/N/LAMP on the lid; wire per the install card.", group="acin")
part(S, "F1", "Device:Fuse", "T500mA 250V", "bps:Fuse_TR5_P5.08mm", {"1": "ACL_IN", "2": "ACL_F"},
     mpn="0382.500HAT1 (TR5, T 500 mA 250 V)", mfr="Littelfuse",
     desc="Time-lag (slow-blow) fuse 500 mA, 250 VAC, TR5 radial. Protects against PSU/triac fault, not lamp overload.",
     note="VERIFY breaking capacity >= prospective fault current; a user-serviceable 5x20 holder is the alt.", group="acin")
part(S, "MOV1", "Device:Varistor", "14D471K", "bps:Varistor_Disc_D16mm_P7.5mm", {"1": "ACL_F", "2": "ACN"},
     mpn="B72214S0471K101 (S14K300) / 14D471K", mfr="EPCOS/TDK / generic",
     desc="MOV, 300 VAC rms / 470 V varistor voltage, 14 mm disc: surge clamp L-N after the fuse",
     note="VERIFY energy rating for the site; a fused MOV or MOV+GDT improves end-of-life safety.", group="acin")
part(S, "CX1", "Device:C", "100nF X2", "Capacitor_THT:C_Rect_L11.0mm_W5.1mm_P10.00mm_MKT", {"1": "ACL_F", "2": "ACN"},
     mpn="R46KI31000001M (100 nF 275 VAC X2)", mfr="KEMET / Vishay",
     desc="X2 safety EMI cap across L-N, 275 VAC. Differential-mode filtering.", group="acin")
R(S, "RB1", "1M", "ACL_F", "ACN", fp=RAX_P10, mpn="axial 0.5 W 350 V", group="acin",
  note="Bleeder: discharges CX1 when unplugged (< 1 s). Rated for continuous 230 Vrms.")
part(S, "NTC1", "Device:Thermistor", "5D-9", "bps:NTC_Disc_D11mm_P5mm", {"1": "ACL_F", "2": "PSU_L"},
     mpn="MF72-5D9", mfr="Cantherm / generic",
     desc="NTC inrush limiter 5 ohm cold, 9 mm disc, in series with the HLK-PM01 only (not the lamp path)",
     note="Limits turn-on surge into the HLK input cap; the lamp inrush goes through the triac, not here.", group="acin")
part(S, "PS1", "Converter_ACDC:HLK-PM01", "HLK-PM01", "Converter_ACDC:Converter_ACDC_Hi-Link_HLK-PMxx",
     {"1": "PSU_L", "2": "ACN", "3": "GND", "4": "+5V"},
     mpn="HLK-PM01", mfr="Hi-Link",
     desc="Isolated AC-DC module, 85-265 VAC in -> 5 V / 0.6 A (3 W), reinforced isolation 4 kVAC (1 min typ)",
     note="Reinforced AC-DC isolation is the primary SELV barrier. Keep AC and DC pins' copper apart (slot).", group="psu")
part(S, "CB1", "Device:C_Polarized", "220uF/10V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", {"1": "+5V", "2": "GND"},
     mpn="220uF 10V radial (105C, low-ESR)", mfr="Rubycon / Nichicon",
     desc="Bulk on 5 V: supplies the LD2410B (~79 mA avg, bursty) and the opto LED", group="psu")
C(S, "C5", "100nF", "+5V", "GND", group="psu")
# PWR_FLAG only on nets with no power-output pin (the mains nets); +5V/GND are driven by PS1 (power_out)
for i, n in enumerate(["ACL_F", "ACN", "PSU_L"]):
    part(S, f"#FLG{10 + i}", "power:PWR_FLAG", "PWR_FLAG", "", {"1": n})

# ================================================================== 2. AC LOAD CONTROL  (ISOLATION BARRIER + HV)
S = "load"
part(S, "U2", f"{LIB}:MOC3063", "MOC3063", "Package_DIP:SMDIP-6_W9.53mm_Clearance8mm",
     {"1": "OPTO_A", "2": "GND", "4": "TRIAC_MT", "6": "ACL_F"},
     mpn="MOC3063SR2M (gull-wing SMD)", mfr="onsemi / Liteon",
     desc="Zero-cross opto-triac driver, SMD-DIP6 with 8 mm pad-row creepage, 7.5 kVrms isolation, Vdrm 600 V",
     note="Input LED (1,2) = SELV side; output triac (4,6) = mains side. Pins 3,5 NC. 8 mm land spacing keeps "
          "the opto's own primary-secondary PCB creepage >= 6 mm.",
     group="opto")
R("load", "R1", "330R", "MOSI", "OPTO_A", fp=R0805, group="opto",
  note="Opto LED current = (5 - 1.2 V)/330 ~ 11.5 mA > IFT(10 mA) of MOC3063. Driven by MCU PB0/MOSI.")
part(S, "RG1", "Device:R", "180R", RAX_P10, {"1": "TRIAC_MT", "2": "TRIAC_G"},
     mpn="axial 0.5 W 350 V", mfr="Yageo", desc="Triac gate resistor (MOC3063 pin4 -> BTA16 gate)",
     note="180 ohm per the brief; ON AN-3004 suggests >=360 ohm for 230 V non-ZC - OK here because MOC3063 is "
          "zero-crossing (fires near 0 V). VERIFY peak opto current < ITSM(1 A).", group="opto_hv")
part(S, "Q1", "Triac_Thyristor:BTA16-600B", "BTA16-600B", "Package_TO_SOT_THT:TO-220-3_Vertical",
     {"1": "ACL_F", "2": "LAMP", "3": "TRIAC_G"},
     mpn="BTA16-600B", mfr="STMicroelectronics",
     desc="Triac 16 A / 600 V, isolated tab TO-220. MT1(A1)=Line, MT2(A2)=Lamp, Gate from MOC3063.",
     note="Non-snubberless part -> external snubber fitted (RS1/CS1). Derate: ~6 A continuous no heatsink. "
          "VERIFY heatsinking / lamp current; add a clip-on sink for >2 A loads.", group="triac")
part(S, "RS1", "Device:R", "100R 2W", RAX_P1524, {"1": "ACL_F", "2": "SNUB_M"},
     mpn="axial 2 W MO 350 V", mfr="Vishay", desc="Snubber resistor (dv/dt)", group="snub")
part(S, "CS1", "Device:C", "10nF 400VAC", "Capacitor_THT:C_Rect_L10.0mm_W4.0mm_P7.50mm_FKS3_FKP3",
     {"1": "SNUB_M", "2": "LAMP"},
     mpn="10 nF 400 VAC X1 film (e.g. BFC233820103)", mfr="Vishay / KEMET",
     desc="Snubber cap across the triac (with RS1): dv/dt suppression", group="snub")
TP("load", "TP3", "TRIAC_G", group="ltp")

# ================================================================== 3. MCU + ISP  (LOW VOLTAGE / SELV)
S = "mcu"
part(S, "U1", "MCU_Microchip_ATtiny:ATtiny13A-SS", "ATtiny13A-SU", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RESET", "2": "DELAY_ADJ", "3": "RADAR_OUT", "4": "GND", "5": "MOSI", "6": "MISO", "7": "SCK", "8": "+5V"},
     mpn="ATTINY13A-SU", mfr="Microchip",
     desc="8-bit AVR MCU, SOIC-8, 1 kB flash. PB5=RESET, PB3=ADC3(delay pot), PB4=radar in, PB0=opto drive, "
          "PB1=LED, PB2=button.",
     note="Runs at 5 V. Reads LD2410B OUT (3.3 V logic: VIH@5V = 3.0 V, margin ~0.3 V - OK). 9.6 MHz int. RC.",
     group="mcu")
C(S, "C1", "100nF", "+5V", "GND", group="mcu", note="MCU decoupling, close to pin 8")
C(S, "C2", "10uF", "+5V", "GND", fp=C0805, group="mcu")
R(S, "RR1", "10k", "+5V", "RESET", group="mcu", note="RESET pull-up (ISP needs RESET released)")
C(S, "C3", "10nF", "RESET", "GND", dnp=True, group="mcu", note="DNP: RESET noise cap; keep small or omit so ISP works")
part(S, "J2", "Connector_Generic:Conn_02x03_Odd_Even", "AVR-ISP", "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
     {"1": "MISO", "2": "+5V", "3": "SCK", "4": "MOSI", "5": "RESET", "6": "GND"},
     mpn="2x3 2.54 mm header (or pads only / pogo)", mfr="generic",
     desc="Standard 6-pin AVR ISP: 1 MISO 2 VCC 3 SCK 4 MOSI 5 RST 6 GND", group="isp")
TP(S, "TP1", "+5V", group="mtp")
TP(S, "TP2", "GND", group="mtp")

# ================================================================== 4. RADAR, BUTTON, LED, TRIMMER  (SELV)
S = "io"
part(S, "J3", "Connector_Generic:Conn_01x05", "LD2410B", "bps:LD2410B_Module",
     {"1": "RADAR_OUT", "2": "RADAR_TX", "3": "RADAR_RX", "4": "GND", "5": "+5V"},
     mpn="HLK-LD2410B", mfr="Hi-Link",
     desc="24 GHz mmWave presence radar module on a 1.27 mm 5-pin header at the board edge, antenna facing the "
          "front cover. 1=OUT(3.3V) 2=TX 3=RX 4=GND 5=VCC(5V).",
     note="Keep the antenna end clear of copper (no pour under it) and of metal in the lid. OUT high = presence.",
     group="radar")
C(S, "C4", "100nF", "+5V", "GND", group="radar", note="local decoupling at the radar header")
# manual override button on PB2 (shared with SCK): debounce before the 1k series into the MCU
part(S, "SW1", "Switch:SW_Push", "OVERRIDE", "Button_Switch_THT:SW_PUSH_6mm", {"1": "BTN_SW", "2": "GND"},
     mpn="6x6x5 mm tactile (TS-1101 / PTS645)", mfr="XKB / C&K",
     desc="Momentary push button: short = toggle Auto/Manual, long = force lamp off (firmware)", group="btn")
R(S, "RP1", "10k", "+5V", "BTN_SW", group="btn", note="button pull-up (active-low)")
C(S, "CB2", "100nF", "BTN_SW", "GND", group="btn", note="debounce; on the switch side, not on SCK")
R(S, "RS2", "1k", "BTN_SW", "SCK", group="btn", note="series into PB2/SCK; isolates the button during ISP")
# status / fault LED on PB1 (shared MISO)
R(S, "RL1", "1k", "MISO", "LED_A", group="led", note="LED current ~ (5-2)/1k = 3 mA")
part(S, "D1", "Device:LED", "STATUS", "LED_SMD:LED_0805_2012Metric", {"1": "LED_A", "2": "GND"},
     mpn="green 0805 (fault = red/blink pattern in firmware)", mfr="Kingbright",
     desc="Status LED: on=presence, slow blink=manual, fast blink=fault", group="led")
# delay trimmer: 10 s ... 10 min via ADC3
part(S, "RV1", "Device:R_Potentiometer_Trim", "10k", "Potentiometer_THT:Potentiometer_Bourns_3386P_Vertical",
     {"1": "+5V", "2": "DELAY_ADJ", "3": "GND"},
     mpn="3386P-1-103 (10 k)", mfr="Bourns",
     desc="Top-adjust 10 k trimmer: wiper (2) -> ADC3 sets the no-one delay 10 s..10 min", group="pot")
C(S, "C6", "100nF", "DELAY_ADJ", "GND", group="pot", note="ADC filter on the wiper")
# config header: expose the LD2410B UART (3.3 V TTL) for the Hi-Link PC tool
part(S, "J4", "Connector_Generic:Conn_01x03", "CFG UART", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     {"1": "RADAR_TX", "2": "RADAR_RX", "3": "GND"},
     mpn="1x3 2.54 mm (pads only)", mfr="generic",
     desc="Radar config/debug UART (3.3 V): 1=TX 2=RX 3=GND. For the LD2410B host tool.", group="cfg")
for x, n in enumerate(["H1", "H2", "H3", "H4"]):
    part(S, n, "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {},
         mpn="M3 screw to the modular plate / enclosure boss", group="mech")
TP(S, "TP4", "RADAR_OUT", group="tp")
TP(S, "TP5", "DELAY_ADJ", group="tp")


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
    placed = [p for p in PARTS if not p["ref"].startswith("#")]
    print(len(placed), "parts", len(n), "nets")
    for k, v in sorted(n.items()):
        if len(v) < 2:
            print("SINGLE-PIN NET", k, v)
