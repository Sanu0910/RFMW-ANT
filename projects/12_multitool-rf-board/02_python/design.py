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
part("FLT1", "BLE filter", "LFL182G45TC1A108", "Murata", "RF_filter", "mcu", "2.4GHz BLE band-pass filter",
     {"IN": "BLE_RF", "OUT": "BLE_ANT", "GND": "GND"})
part("ANT1", "2.4GHz", "1001312", "Johanson", "Antenna_Chip", "mcu", "BLE chip antenna + pi-match (L1/C5/C6)",
     {"1": "BLE_ANT"})

# ============================================================ 2. Sub-GHz (CC1101)
part("U2", "CC1101", "CC1101RGPR", "Texas Instruments", "QFN-20", "subghz",
     "sub-GHz transceiver 300-928 MHz",
     {"SI": "SPI_R_MOSI", "SO": "SPI_R_MISO", "SCLK": "SPI_R_SCK", "CSn": "CC1101_CS",
      "GDO0": "CC1101_GDO0", "RF_P": "SUBG_RF_P", "RF_N": "SUBG_RF_N",
      "XOSC_Q1": "CC_XO1", "XOSC_Q2": "CC_XO2", "RBIAS": "CC_RBIAS",
      "AVDD": "+3V3", "DVDD": "+3V3", "GND": "GND", "DGUARD": "+3V3"})
part("FLT2", "balun", "B0310J50100AHF", "Johanson", "Balun_0310", "subghz",
     "CC1101 differential-to-SE balun + LC match (L4 3.3nH, L5 6.8nH, C32 1.2pF)",
     {"BAL1": "SUBG_RF_P", "BAL2": "SUBG_RF_N", "UNBAL": "SUBG_SE", "GND": "GND"})
part("SW1", "RFswitch", "BGS13S4N9", "Infineon", "TSNP-9", "subghz", "SPDT RF switch (band/antenna select)",
     {"RFin": "SUBG_SE", "RF1": "SUBG_F1", "RF2": "SUBG_F2", "V1": "RF_SW_0", "V2": "RF_SW_1",
      "VDD": "+3V3", "GND": "GND"})
part("SW2", "RFswitch", "BGS13S4N9", "Infineon", "TSNP-9", "subghz", "SPDT RF switch (antenna side)",
     {"RF1": "SUBG_F1", "RF2": "SUBG_F2", "RFin": "SUBG_ANT", "V1": "RF_SW_0", "V2": "RF_SW_1",
      "VDD": "+3V3", "GND": "GND"})
part("ZQ3", "26MHz", "CXD2-026000000", "generic", "Xtal_2520", "subghz", "CC1101 26 MHz crystal",
     {"1": "CC_XO1", "2": "CC_XO2"})
part("R13", "56k", "56k", "Yageo", "R_0402", "subghz", "CC1101 RBIAS", {"1": "CC_RBIAS", "2": "GND"})
part("J_SUBG", "ANT", "U.FL-R-SMT-1", "Hirose", "U.FL", "subghz", "sub-GHz antenna connector",
     {"1": "SUBG_ANT", "2": "GND"})

# ============================================================ 2b. FFC link to NFC/RFID/IR sub-board
# As on the reference design, the NFC, 125k RFID, IR, speaker, vibro and iButton live on a separate board
# reached over an 18-pin 0.5mm FFC. Below, those blocks hang off these FFC nets.
part("X6", "FFC 18p", "FH34SRJ-18S-0.5SH", "Hirose", "FFC_18_0.5mm", "io",
     "flex link to the NFC/RFID/IR sub-board",
     {"1": "VSYS", "2": "VSYS", "3": "+3V3_EXT", "4": "NFC_CS", "5": "RFID_RF_IN", "6": "GND",
      "7": "SPI_R_SCK", "8": "GND", "9": "SPI_R_MISO", "10": "VIBRO", "11": "RFID_CARRIER_OUT",
      "12": "RFID_CARRIER", "13": "SPI_R_MOSI", "14": "IBTN", "15": "SPEAKER", "16": "IR_TX",
      "17": "IR_RX", "18": "RFID_CARRIER"})
part("VD_USB", "ESD", "ESD241B1W0201", "Nexperia", "0201", "io", "USB line ESD array", {"1": "USB_DM", "2": "GND"})
part("RN1", "51x4", "51ohm array", "Yageo", "R_array_4x0402", "io",
     "series resistors on exposed GPIO/FFC signals (one of several)",
     {"1": "SPI_R_SCK", "2": "SPI_R_MISO", "3": "SPI_R_MOSI", "4": "NFC_CS"})

# ============================================================ 3. NFC (ST25R3916) [on the sub-board]
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

# ============================================================ 4. 125 kHz RFID AFE (discrete, as on the sub-board)
part("VT4", "coildrv P", "DMP2004TK", "Diodes", "SOT-23", "rfid125", "125 kHz coil driver, high side",
     {"G": "RFID_CARRIER_OUT", "S": "+5V", "D": "LF_COIL_P"})
part("VT6", "coildrv N", "DMN2004TK", "Diodes", "SOT-23", "rfid125", "125 kHz coil driver, low side",
     {"G": "RFID_PULL", "D": "LF_COIL_P", "S": "GND"})
part("ANT_LF", "125kHz coil", "wound coil + C", "discrete", "Coil", "rfid125", "125 kHz read coil (ANT3/ANT4) + C",
     {"1": "LF_COIL_P", "2": "LF_RX"})
part("DA3", "LMV358", "LMV358AIDGKR", "Texas Instruments", "VSSOP-8", "rfid125",
     "RFID RX band-pass/amplifier stage 1 (dual op-amp)",
     {"V+": "A3V3", "V-": "GND", "IN1+": "LF_RX", "IN1-": "LF_MID", "OUT1": "LF_A1",
      "IN2+": "LF_A1", "IN2-": "LF_FB2", "OUT2": "LF_A2"})
part("DA4", "LMV358", "LMV358AIDGKR", "Texas Instruments", "VSSOP-8", "rfid125",
     "RFID RX amplifier stage 2 (dual op-amp)",
     {"V+": "A3V3", "V-": "GND", "IN1+": "LF_A2", "IN1-": "LF_FB3", "OUT1": "LF_A3",
      "IN2+": "LF_A3", "IN2-": "LF_FB4", "OUT2": "LF_ENV"})
part("DA5", "LMV331", "LMV331IDCKR", "Texas Instruments", "SC-70-5", "rfid125",
     "RFID envelope comparator -> digital",
     {"IN+": "LF_ENV", "IN-": "LF_MID", "OUT": "RFID_RF_IN", "V+": "A3V3", "V-": "GND"})
part("R_MID1", "33k", "33k", "Yageo", "R_0402", "rfid125", "1.65V mid-rail divider", {"1": "A3V3", "2": "LF_MID"})
part("R_MID2", "33k", "33k", "Yageo", "R_0402", "rfid125", "1.65V mid-rail divider", {"1": "LF_MID", "2": "GND"})

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
part("X10", "BAT+NTC", "1.25-3P", "generic", "Conn_1x03_1.25mm", "power",
     "battery + NTC thermistor (BAT / TEMP / GND)", {"1": "VBAT", "2": "BAT_NTC", "3": "GND"})
part("BT1", "Li-Po 1S", "2000mAh 503450", "generic", "pack", "power", "single-cell battery pack w/ NTC",
     {"+": "VBAT", "NTC": "BAT_NTC", "-": "GND"})
part("U7", "BQ27220", "BQ27220", "Texas Instruments", "WCSP", "power", "battery fuel gauge, I2C",
     {"BAT": "VBAT", "SDA": "I2C_PWR_SDA", "SCL": "I2C_PWR_SCL", "SRP": "VBAT_SNS", "SRN": "GND",
      "VSS": "GND"})
# regulators as on the reference design: two LM3281 bucks (3V3 core + ext-3V3) and an RS3221 LDO
part("U8", "LM3281", "LM3281YFQR", "Texas Instruments", "DSBGA-5", "power",
     "buck DC-DC -> +3V3 core rail", {"VIN": "VSYS", "SW": "SW_L13", "FB": "+3V3", "EN": "+3V3", "GND": "GND"})
part("L13", "470nH", "470nH", "Murata", "Inductor_0806", "power", "buck inductor (core)",
     {"1": "SW_L13", "2": "+3V3"})
part("U8B", "LM3281", "LM3281YFQR", "Texas Instruments", "DSBGA-5", "power",
     "buck DC-DC -> ext-3V3 (header/peripherals)",
     {"VIN": "VSYS", "SW": "SW_L14", "FB": "+3V3_EXT", "EN": "PERIPH_EN", "GND": "GND"})
part("L14", "470nH", "470nH", "Murata", "Inductor_0806", "power", "buck inductor (ext)",
     {"1": "SW_L14", "2": "+3V3_EXT"})
part("DA5", "RS3221-3.3", "RS3221-3.3YF3", "Runic", "DFN-6", "power", "3.3V LDO (clean analog/LDO rail)",
     {"VIN": "VSYS", "VOUT": "+3V3_LDO", "GND": "GND"})
part("R37", "10m", "10mOhm", "Yageo", "R_1206", "power", "battery current-sense (fuel gauge)",
     {"1": "VBAT", "2": "VBAT_SNS"})
part("DA4", "LP5562", "LP5562TMX", "Texas Instruments", "DSBGA-12", "io",
     "RGB LED driver (notification LED + backlight), I2C",
     {"SDA": "I2C_PWR_SDA", "SCL": "I2C_PWR_SCL", "EN": "+3V3", "R": "LED_R", "G": "LED_G", "B": "LED_B",
      "W": "LCD_LED", "VDD": "+3V3", "GND": "GND"})
part("VD4", "RGB LED", "LTST-C19HE1WT", "Lite-On", "LED_RGB_0606", "io", "notification RGB LED",
     {"R": "LED_R", "G": "LED_G", "B": "LED_B", "A": "+3V3"})
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
