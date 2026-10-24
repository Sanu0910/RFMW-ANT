"""Footprint assignment and pad->net resolution for the NOVA-RF1 PCB.

Three mechanisms give every part's pad-number -> net mapping:
  1. KiCad official symbol  (U1/U9/U10): pin NAME -> pad NUMBER read straight from the
     maintained KiCad symbol, so the pad numbers are authoritative, not transcribed by hand.
  2. AUTHORED tables        : explicit {signal: pad}. Used for standard parts (dual op-amp,
     comparator, SOT-23 transistors, USB-C, display) and, once their datasheets are supplied,
     the six chips in PENDING.
  3. Direct numeric         : the part's pin keys are already pad numbers (passives, crystals,
     headers, FFCs, 2-pin modules).

design.py keeps pins by SIGNAL name; here we turn signal -> pad so footprint pads carry nets.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
from libsym import get_symbol, pins

# -------------------------------------------------------------- 1. footprint library map
# design.py footprint string -> real KiCad footprint "Library:Footprint"
FOOTPRINT = {
    "R_0402": "Resistor_SMD:R_0402_1005Metric",
    "C_0402": "Capacitor_SMD:C_0402_1005Metric",
    "C_0805": "Capacitor_SMD:C_0805_2012Metric",
    "R_1206": "Resistor_SMD:R_1206_3216Metric",
    "0201": "Resistor_SMD:R_0201_0603Metric",
    "ESD_0201": "Resistor_SMD:R_0201_0603Metric",
    "R_array_4x0402": "Resistor_SMD:R_Array_Convex_4x0402",
    "SOT-23": "Package_TO_SOT_SMD:SOT-23",
    "SOT-23-6": "Package_TO_SOT_SMD:SOT-23-6",
    "SC-70-5": "Package_TO_SOT_SMD:SOT-353_SC-70-5",
    "VSSOP-8": "Package_SO:VSSOP-8_3x3mm_P0.65mm",
    "QFN-68": "Package_DFN_QFN:QFN-68-1EP_8x8mm_P0.4mm_EP5.2x5.2mm",
    "QFN-32": "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm",
    "QFN-24": "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.65x2.65mm",
    "QFN-20": "Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm",
    "DFN-6": "Package_DFN_QFN:DFN-6-1EP_1.2x1.2mm_P0.4mm_EP0.3x0.94mm_PullBack",
    "DSBGA-6": "Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm",
    "DSBGA-12": "nova-rf1:LP5562_DSBGA12",   # 3 rows x 4 cols (A1-C4), KiCad stock is 4x3
    "WCSP": "Package_BGA:BGA-9_1.6x1.6mm_Layout3x3_P0.5mm",
    "TSNP-9": "nova-rf1:RF_Switch_TSNP9",
    "Xtal_3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "Xtal_2520": "Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm",
    "XTAL_2520": "Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm",
    "Xtal_ABS07": "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    "Inductor_0806": "Inductor_SMD:L_0805_2012Metric",
    "USB_C": "Connector_USB:USB_C_Receptacle_Amphenol_12401610E4-2A",
    "FFC_18_0.5mm": "Connector_FFC-FPC:Hirose_FH12-18S-0.5SH_1x18-1MP_P0.50mm_Horizontal",
    "FFC_2p": "Connector_PinHeader_1.00mm:PinHeader_1x02_P1.00mm_Vertical",
    "Header_2x09": "Connector_PinHeader_2.54mm:PinHeader_2x09_P2.54mm_Vertical",
    "Conn_1x03_1.25mm": "Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal",
    "SW_SMD_4p": "Button_Switch_SMD:SW_SPST_B3U-1000P",
    "LED_RGB_0606": "nova-rf1:LED_RGB_4p",                       # custom named-pad (A/R/G/B)
    "LED_IR": "LED_SMD:LED_0805_2012Metric",
    "U.FL": "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
    "Balun_0310": "nova-rf1:Johanson_0310_Balun",               # custom named-pad
    "RF_filter": "nova-rf1:RF_filter",                          # custom named-pad
    "Antenna_Chip": "nova-rf1:Antenna_Chip",                    # custom 1-pad feed
    "Antenna_Loop": "nova-rf1:NFC_Loop_Antenna",                # custom (PCB loop)
    "Coil": "nova-rf1:RFID_125k_Coil",                          # custom (wound/PCB coil)
    "Pads": "nova-rf1:iButton_Contacts",                        # custom (spring pads)
    "Speaker": "nova-rf1:Speaker_2p",                           # custom 2-pad
    "Vibro": "nova-rf1:Vibro_2p",                               # custom 2-pad
    "pack": "nova-rf1:Battery_3p",                              # custom 3-pad (BAT/NTC/GND)
    "microSD": "nova-rf1:microSD_7p",                           # custom named-pad (SPI mode)
    "COG_128x64": "nova-rf1:Display_ST7565_FFC",                # custom display FFC
    "IR_receiver": "nova-rf1:TSOP_IR_3p",                       # custom 3-pad
    "TC2030": "nova-rf1:TagConnect_TC2030",                     # custom named-pad Tag-Connect
    "EMC_net": None,  # the NFC EMC net is discrete L/C; represented by the ANT loop + caps
}

# -------------------------------------------------------------- 2. live KiCad symbols (name -> pad)
SYMBOL = {
    "U1":  "MCU_ST_STM32WB:STM32WB55RGVx",
    "U9":  "Power_Management:TPS22917DBV",
    "U10": "Power_Protection:USBLC6-2SC6",
}

# -------------------------------------------------------------- 3. authored {signal: pad}
# dual op-amp VSSOP-8 (industry-standard, matches KiCad LMV358 symbol exactly)
_DUAL_OPAMP = {"OUT1": "1", "IN1-": "2", "IN1+": "3", "V-": "4",
               "IN2+": "5", "IN2-": "6", "OUT2": "7", "V+": "8"}
# single comparator SC-70-5 (matches KiCad LMV331 symbol)
_COMP = {"IN+": "1", "V-": "2", "IN-": "3", "OUT": "4", "V+": "5"}
# SOT-23 small-signal MOSFET (G=1, S=2, D=3) — the common JEDEC SOT-23 MOSFET pinout
_MOSFET_SOT23 = {"G": "1", "S": "2", "D": "3"}

AUTHORED = {
    "DA3": _DUAL_OPAMP, "DA4": _DUAL_OPAMP,     # LMV358 (DA4 is the RFID stage-2 op-amp)
    "DA5": _COMP,                               # LMV331 comparator
    "Q_IR": _MOSFET_SOT23, "Q_IBTN": _MOSFET_SOT23, "Q_VIB": _MOSFET_SOT23,
    "Q_SPK": _MOSFET_SOT23, "VT4": _MOSFET_SOT23, "VT6": _MOSFET_SOT23,
    # USB-C receptacle (Amphenol 12401610E4-2A): only the pads we use
    "J_USB": {"VBUS": "A4", "GND": "A1", "DP": "A6", "DM": "A7", "CC1": "A5", "CC2": "B5",
              "SHIELD": "S1"},
    # IR LED on a stock LED_0805 (KiCad pad 1 = cathode K, pad 2 = anode A)
    "D_IR": {"K": "1", "A": "2"},

    # ---- transcribed from the uploaded datasheets (exact pads) ----
    # CC1101RGPR QFN-20 (SWRS061I Table 19); EP pad 21 = GND
    "U2": {"SCLK": "1", "SO": "2", "DVDD": "4", "DCOUPL": "5", "GDO0": "6", "CSn": "7",
           "XOSC_Q1": "8", "AVDD": ["9", "11", "14", "15"], "XOSC_Q2": "10", "RF_P": "12",
           "RF_N": "13", "GND": ["16", "19", "21"], "RBIAS": "17", "DGUARD": "18", "SI": "20"},
    # ST25R3916 UFQFPN-32 (DS12484 Fig.4); EP pad 33 = VSS
    "U3": {"SCLK": "30", "MISO": "32", "MOSI": "31", "SS": "29", "IRQ": "27", "TX1": "13",
           "TX2": "15", "RFI1": "22", "RFI2": "23", "OSCI": "5", "OSCO": "4",
           "VDD": ["1", "3", "7", "8", "9", "10", "11", "14"],
           "VSS": ["6", "12", "16", "21", "26", "33"], "I2C_EN": "20", "AGDC": "24"},
    # BQ25896 WQFN-24 (SLUSC76C); EP pad 25 = GND
    "U6": {"VBUS": "1", "SCL": "5", "SDA": "6", "CE": "9", "ILIM": "10", "TS": "11",
           "BAT": ["13", "14"], "SYS": ["15", "16"], "PGND": ["17", "18"], "SW": ["19", "20"],
           "BTST": "21", "REGN": "22", "PMID": "23", "GND": "25"},
    # BQ27220 DSBGA-9 YZF (SLUSCB7A)
    "U7": {"GPOUT": "A1", "SDA": "A2", "SCL": "A3", "BIN": "B1", "VSS": "B2", "VDD": "B3",
           "SRP": "C1", "SRN": "C2", "BAT": "C3"},
    # LM3281 DSBGA-6 YFQ (SNVSA38)
    "U8": {"FB": "A1", "VIN": "A2", "MODE": "B1", "SW": "B2", "EN": "C1", "GND": "C2"},
    "U8B": {"FB": "A1", "VIN": "A2", "MODE": "B1", "SW": "B2", "EN": "C1", "GND": "C2"},
    # LP5562 DSBGA-12 YQE (SNVS820B)
    "DA7": {"W": "A1", "VDD": "A2", "CLK_32K": "A3", "B": "A4", "ADDR_SEL1": "B1",
            "ADDR_SEL0": "B2", "GND": "B3", "G": "B4", "SDA": "C1", "SCL": "C2",
            "EN": "C3", "R": "C4"},
    # RS3221-3.3 SOT-23-3 fixed 3.3V (RS3221 RevA.3)
    "DA8": {"GND": "1", "VOUT": "2", "VIN": "3"},
}

# all datasheets received and transcribed (2026-10-24); none pending
PENDING = set()

_symcache = {}


def _sym_name_to_pads(libid):
    if libid not in _symcache:
        pl = pins(get_symbol(libid))
        m = {}
        for num, name, *_ in pl:
            m.setdefault(name, []).append(num)
        _symcache[libid] = m
    return _symcache[libid]


def part_signal_pins(ref):
    """ref -> {signal: net} as declared in design.py."""
    out = {}
    for net, nodes in D.NETS.items():
        for node in nodes:
            r, pin = node.rsplit(".", 1)
            if r == ref:
                out[pin] = net
    return out


def pad_nets(ref):
    """ref -> {pad_number: net}, or None if the part is PENDING a datasheet."""
    if ref in PENDING:
        return None
    sig = part_signal_pins(ref)
    if ref in SYMBOL:
        name2pad = _sym_name_to_pads(SYMBOL[ref])
        out = {}
        for s, net in sig.items():
            for pad in name2pad.get(s, []):
                out[pad] = net
        return out
    if ref in AUTHORED:
        amap = AUTHORED[ref]
        out = {}
        for s, net in sig.items():
            if s not in amap:
                continue
            pads = amap[s]
            for pad in ([pads] if isinstance(pads, str) else pads):
                out[pad] = net
        return out
    # direct numeric: pin keys already are pad numbers
    return {s: net for s, net in sig.items()}


def coverage():
    parts = {p[0]: p for p in D.PARTS}
    done, pending, unresolved = [], [], []
    for ref, p in parts.items():
        if ref in PENDING:
            pending.append(ref)
            continue
        sig = part_signal_pins(ref)
        pn = pad_nets(ref)
        # a signal is unresolved if it produced no pad
        resolved_signals = set()
        if ref in SYMBOL:
            name2pad = _sym_name_to_pads(SYMBOL[ref])
            resolved_signals = {s for s in sig if name2pad.get(s)}
        elif ref in AUTHORED:
            resolved_signals = {s for s in sig if s in AUTHORED[ref]}
        else:
            resolved_signals = set(sig)
        miss = set(sig) - resolved_signals
        fp = FOOTPRINT.get(p[4], "MISSING")
        if miss or fp == "MISSING":
            unresolved.append((ref, p[4], fp, sorted(miss)))
        else:
            done.append(ref)
    return done, pending, unresolved


if __name__ == "__main__":
    done, pending, unresolved = coverage()
    print(f"resolved parts : {len(done)}")
    print(f"pending (need datasheet): {len(pending)} -> {sorted(pending)}")
    print(f"unresolved     : {len(unresolved)}")
    for ref, fp, kfp, miss in unresolved:
        print(f"  {ref:8s} fp={fp:16s} kfp={kfp}  missing_pins={miss}")
