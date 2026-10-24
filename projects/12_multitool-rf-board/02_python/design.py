#!/usr/bin/env python3
"""CRL-MT1 multi-tool RF board: schematic netlist (original firmware-compatible design).

Parts and connections reflect the public chip datasheets and the GPIO/peripheral map the open Flipper Zero
firmware expects (see ../04_docs/ARCHITECTURE.md). This is an original board, not a Flipper Zero, and uses none
of its trademarks or layout. Run to emit ../03_fab/BOM_engineering.csv and a netlist summary.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "..", "03_fab")
os.makedirs(FAB, exist_ok=True)

PARTS = []   # (ref, value, mpn, mfr, footprint, group, desc)
NETS = {}    # net name -> list of "REF.pin"


def part(ref, value, mpn, mfr, fp, group, desc, pins):
    PARTS.append((ref, value, mpn, mfr, fp, group, desc))
    for pin, net in pins.items():
        NETS.setdefault(net, []).append(f"{ref}.{pin}")


# ============================================================ 1. MCU + BLE
part("U1", "STM32WB55RG", "STM32WB55RGV6", "STMicroelectronics", "QFN-68", "mcu",
     "Cortex-M4 + M0 BLE 5, 1MB flash, USB, 2.4GHz radio",
     {"VDD": "+3V3", "VSS": "GND", "VBAT": "+3V3", "NRST": "NRST",
      # SPI-R radio bus
      "PA5": "SPI_R_SCK", "PB4": "SPI_R_MISO", "PB5": "SPI_R_MOSI",
      "PD0": "CC1101_CS", "PA1": "CC1101_GDO0", "PC4": "RF_SW_0", "PE4": "NFC_CS",
      # SPI-D display bus
      "PD1": "SPI_D_SCK", "PC2": "SPI_D_MISO", "PB15": "SPI_D_MOSI",
      "PC11": "DISP_CS", "PB1": "DISP_DI", "PB0": "DISP_RST", "PC12": "SD_CS", "PC10": "SD_CD",
      # 125k RFID
      "PA15": "RFID_CARRIER_OUT", "PA2": "RFID_CARRIER", "PC5": "RFID_RF_IN",
      # IR, iButton
      "PB9": "IR_TX", "PA0": "IR_RX", "PB14": "IBTN",
      # buttons
      "PB10": "BTN_UP", "PC6": "BTN_DOWN", "PB11": "BTN_LEFT", "PB12": "BTN_RIGHT",
      "PH3": "BTN_OK", "PC13": "BTN_BACK",
      # haptics/sound/power
      "PA8": "VIBRO", "PB8": "SPEAKER", "PA3": "PERIPH_EN",
      "PA10": "I2C_PWR_SDA", "PA9": "I2C_PWR_SCL",
      # USB / SWD / UART
      "PA11": "USB_DM", "PA12": "USB_DP", "PA13": "SWDIO", "PA14": "SWCLK",
      "PB6": "UART_TX", "PB7": "UART_RX",
      # external header user pins
      "PA7": "EXT_PA7", "PA6": "EXT_PA6", "PA4": "EXT_PA4", "PB3": "EXT_PB3",
      "PB2": "EXT_PB2", "PC3": "EXT_PC3", "PC1": "EXT_PC1", "PC0": "EXT_PC0",
      # 32MHz radio xtal + 32.768k LSE
      "PC14": "LSE_IN", "PC15": "LSE_OUT", "PB13_OSC": "HSE_IN"})
part("Y1", "32MHz", "ABM8-32.000MHZ", "Abracon", "Xtal_3225", "mcu", "HSE 32 MHz for the radio",
     {"1": "HSE_IN", "2": "GND"})
part("Y2", "32.768kHz", "ABS07-32.768KHZ", "Abracon", "Xtal_ABS07", "mcu", "LSE RTC crystal",
     {"1": "LSE_IN", "2": "LSE_OUT"})
part("ANT1", "2.4GHz", "2450AT18A100", "Johanson", "Antenna_Chip", "mcu", "BLE chip antenna + pi match",
     {"1": "BLE_RF"})

# ============================================================ 2. Sub-GHz (CC1101)
part("U2", "CC1101", "CC1101RGPR", "Texas Instruments", "QFN-20", "subghz",
     "sub-GHz transceiver 300-928 MHz",
     {"SI": "SPI_R_MOSI", "SO": "SPI_R_MISO", "SCLK": "SPI_R_SCK", "CSn": "CC1101_CS",
      "GDO0": "CC1101_GDO0", "RF_P": "SUBG_RF_P", "RF_N": "SUBG_RF_N",
      "AVDD": "+3V3", "DVDD": "+3V3", "GND": "GND", "DGUARD": "+3V3"})
part("FL1", "balun+LC", "JTI matching", "Johanson/discrete", "RF_match", "subghz",
     "CC1101 differential-to-SE balun and LC band filter",
     {"IN_P": "SUBG_RF_P", "IN_N": "SUBG_RF_N", "OUT": "SUBG_SE"})
part("SW1", "RFswitch", "BGS12PN10", "Infineon", "TSNP-10", "subghz", "antenna RF switch",
     {"RFC": "SUBG_ANT", "RF1": "SUBG_SE", "CTRL": "RF_SW_0", "VDD": "+3V3", "GND": "GND"})
part("J_SUBG", "ANT", "U.FL-R-SMT-1", "Hirose", "U.FL", "subghz", "sub-GHz antenna connector",
     {"1": "SUBG_ANT", "2": "GND"})

# ============================================================ 3. NFC (ST25R3916)
part("U3", "ST25R3916", "ST25R3916-AQWT", "STMicroelectronics", "QFN-32", "nfc",
     "13.56 MHz NFC reader/card/peer front-end",
     {"SCLK": "SPI_R_SCK", "MISO": "SPI_R_MISO", "MOSI": "SPI_R_MOSI", "SS": "NFC_CS",
      "IRQ": "RFID_CARRIER", "TX1": "NFC_TX1", "TX2": "NFC_TX2",
      "RFI1": "NFC_RFI1", "RFI2": "NFC_RFI2", "VDD": "+3V3", "VSP": "+3V3", "VSS": "GND"})
part("L_NFC", "EMIfilter", "NFC EMC LC", "discrete", "EMC_net", "nfc", "NFC EMC + matching network",
     {"TX1": "NFC_TX1", "TX2": "NFC_TX2", "ANT_P": "NFC_ANT_P", "ANT_N": "NFC_ANT_N",
      "RFI1": "NFC_RFI1", "RFI2": "NFC_RFI2"})
part("ANT_NFC", "13.56MHz loop", "PCB spiral", "PCB", "Antenna_Loop", "nfc", "13.56 MHz PCB loop antenna",
     {"1": "NFC_ANT_P", "2": "NFC_ANT_N"})

# ============================================================ 4. 125 kHz RFID AFE
part("Q_LF", "coildriver", "2x 2N7002 H-bridge", "discrete", "SOT-23", "rfid125",
     "125 kHz coil driver from the timer carrier",
     {"IN": "RFID_CARRIER_OUT", "COIL_P": "LF_COIL_P", "COIL_N": "GND", "VDD": "+3V3"})
part("ANT_LF", "125kHz coil", "wound coil + C", "discrete", "Coil", "rfid125", "125 kHz LC antenna",
     {"1": "LF_COIL_P", "2": "LF_RX"})
part("U4", "comparator", "TLV7011", "Texas Instruments", "SOT-23-5", "rfid125",
     "125 kHz envelope comparator to the MCU",
     {"IN+": "LF_RX", "IN-": "LF_REF", "OUT": "RFID_RF_IN", "VDD": "+3V3", "GND": "GND"})

# ============================================================ 5. Display + SD
part("U5", "ST7565R", "ST7565R", "Sitronix", "COG_128x64", "io", "128x64 monochrome LCD (COG)",
     {"CS": "DISP_CS", "A0": "DISP_DI", "RST": "DISP_RST", "SCL": "SPI_D_SCK", "SI": "SPI_D_MOSI",
      "VDD": "+3V3", "VSS": "GND"})
part("J_SD", "microSD", "DM3D-SF", "Hirose", "microSD", "io", "microSD card holder",
     {"CLK": "SPI_D_SCK", "DO": "SPI_D_MISO", "DI": "SPI_D_MOSI", "CS": "SD_CS",
      "CD": "SD_CD", "VDD": "+3V3", "VSS": "GND"})

# ============================================================ 6. IR, iButton
part("D_IR", "IR LED", "SFH4550", "Osram", "LED_IR", "io", "IR transmit LED",
     {"A": "IR_LED_A", "K": "GND"})
part("Q_IR", "drive", "2N7002", "Nexperia", "SOT-23", "io", "IR LED driver FET",
     {"G": "IR_TX", "D": "IR_LED_A", "S": "GND"})
part("U_IR", "IR RX", "TSOP75238", "Vishay", "IR_receiver", "io", "38 kHz IR demodulator",
     {"OUT": "IR_RX", "VS": "+3V3", "GND": "GND"})
part("J_IBTN", "iButton", "1-Wire pads", "PCB", "Pads", "io", "iButton / 1-Wire contacts",
     {"DATA": "IBTN", "GND": "GND"})
part("Q_IBTN", "1W driver", "DMN2075U", "Diodes", "SOT-23", "io", "iButton open-drain driver + protection",
     {"G": "IBTN", "D": "IBTN_EXT", "S": "GND"})

# ============================================================ 7. Buttons, haptics, sound
for ref, net in [("SW_U", "BTN_UP"), ("SW_D", "BTN_DOWN"), ("SW_L", "BTN_LEFT"),
                 ("SW_R", "BTN_RIGHT"), ("SW_O", "BTN_OK"), ("SW_B", "BTN_BACK")]:
    part(ref, "tact", "EVQ-P7", "Panasonic", "SW_SMD_4p", "ui", "tact switch", {"1": net, "2": "GND"})
part("M1", "vibro", "coin ERM", "generic", "Vibro", "ui", "haptic motor",
     {"+": "VIBRO_DRV", "-": "GND"})
part("Q_VIB", "drive", "2N7002", "Nexperia", "SOT-23", "ui", "vibro driver FET",
     {"G": "VIBRO", "D": "VIBRO_DRV", "S": "GND"})
part("LS1", "speaker", "magnetic 8ohm", "generic", "Speaker", "ui", "speaker",
     {"+": "SPK_DRV", "-": "GND"})
part("Q_SPK", "drive", "2N7002", "Nexperia", "SOT-23", "ui", "speaker driver FET",
     {"G": "SPEAKER", "D": "SPK_DRV", "S": "GND"})

# ============================================================ 8. Power
part("J_USB", "USB-C", "TYPE-C-31-M-12", "GCT", "USB_C", "power", "USB-C receptacle",
     {"VBUS": "VBUS", "DM": "USB_DM", "DP": "USB_DP", "CC1": "USB_CC1", "CC2": "USB_CC2",
      "SHIELD": "GND", "GND": "GND"})
part("U6", "BQ25896", "BQ25896", "Texas Instruments", "QFN-24", "power",
     "1-cell Li-ion charger with 5V boost, I2C",
     {"VBUS": "VBUS", "SYS": "VSYS", "BAT": "VBAT", "SDA": "I2C_PWR_SDA", "SCL": "I2C_PWR_SCL",
      "PGND": "GND", "GND": "GND"})
part("BT1", "Li-Po 1S", "2000mAh 503450", "generic", "JST_PH_2", "power", "single-cell battery",
     {"+": "VBAT", "-": "GND"})
part("U7", "BQ27220", "BQ27220", "Texas Instruments", "WCSP", "power", "battery fuel gauge, I2C",
     {"BAT": "VBAT", "SDA": "I2C_PWR_SDA", "SCL": "I2C_PWR_SCL", "SRP": "VBAT_SNS", "SRN": "GND",
      "VSS": "GND"})
part("U8", "TPS63802", "TPS63802", "Texas Instruments", "QFN-10", "power",
     "buck-boost 3.3V/2A (holds 3V3 across Li-Po range)",
     {"VIN": "VSYS", "VOUT": "+3V3", "EN": "VBAT", "GND": "GND", "L1": "SW_L1", "L2": "SW_L2"})
part("L1", "1.5uH", "DFE252012", "Murata", "Inductor_1008", "power", "buck-boost inductor",
     {"1": "SW_L1", "2": "SW_L2"})
part("U9", "loadsw", "TPS22917", "Texas Instruments", "SOT-23-6", "power",
     "peripheral-rail load switch (SD/display/radios)",
     {"VIN": "+3V3", "VOUT": "+3V3_PERIPH", "ON": "PERIPH_EN", "GND": "GND"})
part("U10", "ESD", "USBLC6-2SC6", "STMicroelectronics", "SOT-23-6", "power", "USB + CC ESD protection",
     {"IO1": "USB_DM", "IO2": "USB_DP", "VBUS": "VBUS", "GND": "GND"})
part("R_CC1", "5.1k", "5.1k", "Yageo", "R_0402", "power", "USB-C CC pulldown", {"1": "USB_CC1", "2": "GND"})
part("R_CC2", "5.1k", "5.1k", "Yageo", "R_0402", "power", "USB-C CC pulldown", {"1": "USB_CC2", "2": "GND"})

# ============================================================ 9. Debug + GPIO header
part("J_SWD", "SWD", "Tag-Connect TC2030", "TagConnect", "TC2030", "io", "SWD programming",
     {"SWDIO": "SWDIO", "SWCLK": "SWCLK", "NRST": "NRST", "VCC": "+3V3", "GND": "GND"})
part("J_GPIO", "header 2x9", "Conn_2x09", "generic", "Header_2x09", "io", "external GPIO / module header",
     {"1": "+3V3", "2": "EXT_PA7", "3": "EXT_PA6", "4": "EXT_PA4", "5": "EXT_PB3", "6": "EXT_PB2",
      "7": "EXT_PC3", "8": "EXT_PC1", "9": "EXT_PC0", "10": "SWCLK", "11": "SWDIO",
      "12": "UART_TX", "13": "UART_RX", "14": "I2C_PWR_SDA", "15": "I2C_PWR_SCL",
      "16": "VBUS", "17": "VIBRO", "18": "GND"})

# ---- decoupling (one per supply pin group, representative) ----
for i, net in enumerate(["+3V3", "+3V3", "+3V3", "+3V3_PERIPH", "VSYS", "VBAT"], 1):
    part(f"C{i}", "100nF", "100nF", "Murata", "C_0402", "passive", "decoupling", {"1": net, "2": "GND"})
for i, net in enumerate(["+3V3", "VSYS", "VBAT", "+3V3_PERIPH"], 7):
    part(f"C{i}", "10uF", "10uF", "Murata", "C_0805", "passive", "bulk", {"1": net, "2": "GND"})


def main():
    with open(os.path.join(FAB, "BOM_engineering.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Ref", "Value", "MPN", "Manufacturer", "Footprint", "Group", "Description"])
        for p in sorted(PARTS):
            w.writerow(p)
    multi = {n: v for n, v in NETS.items() if len(v) >= 2}
    with open(os.path.join(FAB, "netlist.txt"), "w") as fh:
        for n in sorted(multi):
            fh.write(f"{n}: {', '.join(sorted(multi[n]))}\n")
    print(f"parts: {len(PARTS)}   nets: {len(NETS)} ({len(multi)} with >=2 nodes)")
    singles = [n for n, v in NETS.items() if len(v) == 1]
    if singles:
        print("single-node nets (header/antenna/test endpoints, expected):", ", ".join(sorted(singles)))


if __name__ == "__main__":
    main()
