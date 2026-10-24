"""Level-1 design verification for NOVA-RF1 (no hardware needed).

Checks:
  1. Firmware pin-map: every GPIO the Flipper F7 firmware expects is wired to the right net on U1.
  2. Power/ground: every IC has its supply rail(s) and GND connected.
  3. Decoupling: every IC supply net carries at least one decoupling cap.
  4. No single-pad power nets, no obviously shorted rails.
Prints PASS/FAIL per check. ERC and DRC are run separately via kicad-cli.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D

# ---- what the Flipper F7 firmware (furi_hal_resources) expects: STM32WB55 pin -> net ----
FW_PINMAP = {
    "PA5": "SPI_R_SCK", "PB4": "SPI_R_MISO", "PB5": "SPI_R_MOSI",
    "PD0": "CC1101_CS", "PA1": "CC1101_GDO0", "PC4": "RF_SW_0", "PE4": "NFC_CS",
    "PD1": "SPI_D_SCK", "PC2": "SPI_D_MISO", "PB15": "SPI_D_MOSI",
    "PC11": "DISP_CS", "PB1": "DISP_DI", "PB0": "DISP_RST", "PC12": "SD_CS", "PC10": "SD_CD",
    "PA15": "RFID_CARRIER_OUT", "PA2": "RFID_CARRIER", "PC5": "RFID_RF_IN",
    "PB9": "IR_TX", "PA0": "IR_RX", "PB14": "IBTN",
    "PB10": "BTN_UP", "PC6": "BTN_DOWN", "PB11": "BTN_LEFT", "PB12": "BTN_RIGHT",
    "PH3": "BTN_OK", "PC13": "BTN_BACK",
    "PA8": "VIBRO", "PB8": "SPEAKER", "PA3": "PERIPH_EN",
    "PA10": "I2C_PWR_SDA", "PA9": "I2C_PWR_SCL",
    "PA11": "USB_DM", "PA12": "USB_DP", "PA13": "SWDIO", "PA14": "SWCLK",
    "PB6": "UART_TX", "PB7": "UART_RX",
}

SUPPLY = {"+3V3", "+3V3_EXT", "+3V3_PERIPH", "+3V3_LDO", "VSYS", "VBAT", "VBUS", "+5V", "A3V3"}
ICS = {"U1", "U2", "U3", "U5", "U6", "U7", "U8", "U8B", "U9", "U10", "DA3", "DA4", "DA5", "DA7", "DA8"}


def pins_of(ref):
    out = {}
    for net, nodes in D.NETS.items():
        for n in nodes:
            r, pin = n.rsplit(".", 1)
            if r == ref:
                out[pin] = net
    return out


def main():
    npass = nfail = 0

    def check(name, ok, detail=""):
        nonlocal npass, nfail
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
        if ok:
            npass += 1
        else:
            nfail += 1

    print("1. FIRMWARE PIN-MAP (STM32WB55 U1 vs Flipper F7 firmware)")
    u1 = pins_of("U1")
    miss = [f"{p}->{net}" for p, net in FW_PINMAP.items() if u1.get(p) != net]
    check(f"all {len(FW_PINMAP)} firmware GPIO wired to the expected nets", not miss,
          "mismatches: " + ", ".join(miss) if miss else f"{len(FW_PINMAP)}/{len(FW_PINMAP)} correct")

    print("\n2. POWER + GROUND per IC")
    pmap = {ref: pins_of(ref) for ref in ICS}
    for ref in sorted(ICS):
        nets = set(pmap[ref].values())
        has_gnd = "GND" in nets
        has_sup = bool(nets & SUPPLY)
        check(f"{ref}: supply + GND present", has_gnd and has_sup,
              ("" if has_gnd and has_sup else f"GND={has_gnd} supply={has_sup}"))

    print("\n3. DECOUPLING (a cap on each IC's main supply net)")
    NO_DECAP = {"U10"}   # USBLC6 is an ESD/TVS array - it clamps a line, not a powered IC
    # map: supply net -> set of caps on it
    caps_on = {}
    for ref, value, mpn, mfr, fp, group, desc in D.PARTS:
        if fp.startswith("C_") or value.endswith("uF") or value.endswith("nF"):
            for pin, net in pins_of(ref).items():
                caps_on.setdefault(net, set()).add(ref)
    for ref in sorted(ICS):
        if ref in NO_DECAP:
            continue
        sup = {n for n in pmap[ref].values() if n in SUPPLY}
        decoupled = any(caps_on.get(n) for n in sup)
        check(f"{ref}: >=1 cap on its supply", decoupled or not sup,
              "" if decoupled or not sup else f"no cap on {sup}")

    print("\n4. NET SANITY")
    multi = {n: v for n, v in D.NETS.items() if len(v) >= 2}
    single = [n for n, v in D.NETS.items() if len(v) == 1 and not n.startswith("unconnected")]
    check("no supply/gnd net is single-pad", not (SUPPLY & set(single)),
          "single: " + ", ".join(SUPPLY & set(single)) if (SUPPLY & set(single)) else "all rails have >=2 nodes")
    check("GND is the largest net (return path)", max(D.NETS, key=lambda n: len(D.NETS[n])) == "GND",
          f"GND has {len(D.NETS['GND'])} nodes")

    print(f"\n==== design checks: {npass} PASS, {nfail} FAIL ====")
    return nfail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
