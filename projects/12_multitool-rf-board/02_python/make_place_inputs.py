"""Emit a KiCadRoutingTools groups.json from design.py's functional groups."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import pinmap

KDIR = os.path.normpath(os.path.join(HERE, "..", "01_kicad"))
PCB = os.path.join(KDIR, "crl-mt1.kicad_pcb")

ROLE = {"mcu": "core", "subghz": "rf", "nfc": "rf", "rfid125": "analog",
        "io": "io", "power": "power", "passive": "decoupling", "ui": "io"}
WHY = {
    "mcu": "STM32WB55 MCU + BLE, its HSE/LSE crystals, SMPS inductor, BLE filter/antenna and decaps",
    "subghz": "CC1101 sub-GHz radio, balun, RF switches, 26 MHz xtal, RBIAS, U.FL",
    "nfc": "ST25R3916 NFC reader, 27.12 MHz xtal, EMC/matching network and loop antenna",
    "rfid125": "125 kHz RFID discrete AFE: coil drivers, op-amps, comparator, mid-rail divider",
    "io": "display, microSD, IR, iButton, FFC, GPIO header, RGB LED driver, Tag-Connect, ESD",
    "power": "USB-C, BQ25896 charger + buck, BQ27220 gauge, LM3281 bucks, RS3221 LDO, battery conn",
    "passive": "bulk + decoupling capacitors across the supply rails",
    "ui": "buttons, vibro motor, speaker and their driver FETs",
}


def build():
    buckets = {}
    for ref, value, mpn, mfr, fp, group, desc in D.PARTS:
        if pinmap.FOOTPRINT.get(fp) is None:
            continue  # parts with no footprint are not on the board
        buckets.setdefault(group, []).append(ref)
    groups = []
    for g, refs in buckets.items():
        groups.append({"name": g, "role": ROLE.get(g, "other"),
                       "refs": sorted(refs), "why": WHY.get(g, g)})
    out = {"schema": 1, "board": PCB, "groups": groups}
    path = os.path.join(KDIR, "crl-mt1.groups.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {path}: {len(groups)} groups, {sum(len(g['refs']) for g in groups)} parts")


if __name__ == "__main__":
    build()
