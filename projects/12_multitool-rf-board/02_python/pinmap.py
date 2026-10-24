"""Footprint assignment and pad->net resolution for the CRL-MT1 PCB.

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
    "DSBGA-5": "Package_BGA:Texas_DSBGA-5_0.822x1.116mm_Layout2x1x2_P0.4mm",
    "DSBGA-12": "Package_BGA:Texas_DSBGA-12_1.36x1.86mm_Layout3x4_P0.5mm",
    "WCSP": "Package_BGA:BGA-9_1.6x1.6mm_Layout3x3_P0.5mm",
    "TSNP-9": "crl-mt1:RF_Switch_TSNP9",
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
    "LED_RGB_0606": "crl-mt1:LED_RGB_4p",                       # custom named-pad (A/R/G/B)
    "LED_IR": "LED_SMD:LED_0805_2012Metric",
    "U.FL": "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
    "Balun_0310": "crl-mt1:Johanson_0310_Balun",               # custom named-pad
    "RF_filter": "crl-mt1:RF_filter",                          # custom named-pad
    "Antenna_Chip": "crl-mt1:Antenna_Chip",                    # custom 1-pad feed
    "Antenna_Loop": "crl-mt1:NFC_Loop_Antenna",                # custom (PCB loop)
    "Coil": "crl-mt1:RFID_125k_Coil",                          # custom (wound/PCB coil)
    "Pads": "crl-mt1:iButton_Contacts",                        # custom (spring pads)
    "Speaker": "crl-mt1:Speaker_2p",                           # custom 2-pad
    "Vibro": "crl-mt1:Vibro_2p",                               # custom 2-pad
    "pack": "crl-mt1:Battery_3p",                              # custom 3-pad (BAT/NTC/GND)
    "microSD": "crl-mt1:microSD_7p",                           # custom named-pad (SPI mode)
    "COG_128x64": "crl-mt1:Display_ST7565_FFC",                # custom display FFC
    "IR_receiver": "crl-mt1:TSOP_IR_3p",                       # custom 3-pad
    "TC2030": "crl-mt1:TagConnect_TC2030",                     # custom named-pad Tag-Connect
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
}

# chips still waiting on datasheet uploads for exact pads (see 04_docs/PCB_STATUS.md)
PENDING = {"U2", "U3", "U6", "U7", "U8", "U8B", "DA7", "DA8"}
#          CC1101, ST25R3916, BQ25896, BQ27220, LM3281 x2, LP5562, RS3221

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
        return {amap[s]: net for s, net in sig.items() if s in amap}
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
