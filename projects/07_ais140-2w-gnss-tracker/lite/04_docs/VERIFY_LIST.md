# CRL-TRK-2W-L1 - check before ordering

The build machine could search the web but not download vendor PDFs. Pin numbers marked "confirmed" were
checked against search excerpts of the vendor documents. Everything else comes from the vendor family table
or from memory, and must be checked against the PDF before any board is ordered.

## Blocking: must be fixed before fabrication

| # | Item | Status | Action |
|---|---|---|---|
| 1 | **EC200U land pattern** (`lite.pretty/Quectel_EC200U_LCC-144`) | **Parametric reconstruction**: 28.0 x 31.0 mm body, 80 LCC pads at 1.0 mm pitch (24 / 16 / 24 / 16 per side, counter-clockwise from top-left), 64 LGA pads on an 8 x 8, 2.2 mm grid. Pitch, pad size, LGA positions and the pin-1 corner are NOT from the vendor drawing. | Replace with "Recommended Footprint (Top View)" from the Quectel *EC200U Series Hardware Design* (V1.0 fig. 40 / V1.2 fig. 41). Keep the pad numbers and re-run `make_pcb.py` (dsn, Freerouting, ses, finish). The LTE RF line in `RF_ROUTES` follows pad 49, wherever it lands. |
| 2 | EC200U pins not yet confirmed: VDD_EXT 7, MAIN_RXD 68, USB_DP/DM/VBUS 69/70/71, DBG_RXD/TXD 11/12, USIM_GND 10, GND list (8, 9, 19, 22, 36, 46, 48, 50-54, 56, 72, 85-112) | EC2x family table | Check against the EC200U pin table. Confirmed by excerpt: VBAT_RF 57/58, VBAT_BB 59/60, PWRKEY 21, RESET_N 20, ANT_MAIN 49, USIM_VDD/DATA/CLK/RST 14-17, STATUS 61, NET_STATUS 6, RI 62, DTR 66, TXD 67, I2C 41/42, ADC1 44 / ADC0 45, GPIO1-4 = 27/26/24/25. |
| 3 | L76K pin-out (stock KiCad `Quectel_L76` land pattern) | L76 family: 1/10/12 GND, 2 TXD, 3 RXD, 4 1PPS, 6 V_BCKP, 8 VCC, 9 RESET_N, 11 RF_IN, 14 VCC_RF. Confirmed by excerpt for 1, 2, 3, 6, 8, 11 and 14 (on the L76). | Check pins 9 and 14 (VDD_RF on the L76K) and the I/O level (3.3 V assumed) in the *L76K Hardware Design V1.0*. |
| 4 | MFF2 eSIM land pattern and pin-out | Stock WSON-8 6x5 pads without the EP; pins 1 GND, 2 VPP, 3 I/O, 6 CLK, 7 RST, 8 VCC (ETSI TS 102 671) | Check against the drawing from the SIM / eUICC supplier (Jio / Airtel / Vi IoT, Thales, G+D). |
| 5 | XL1509-ADJ pin-out and EN polarity | 1 VIN, 2 SW, 3 GND, 4 FB, 5 EN (low = on), 6-8 GND; VFB 1.23 V | Check against the XLSEMI datasheet. If EN is active-high, change U1 pin 5 to VIN_PROT through 100k. |

## Values to confirm

| Ref | Value | Reason |
|---|---|---|
| R1/R2 | 2.61k / 1k | 4.44 V buck output (XL1509 VFB 1.23 V). Must stay below the EC200U VBAT maximum (4.3 V) after D4: 4.44 V - 0.3 V = 4.1 V at light load. |
| L1 | 22 uH SRN6045TA | Isat must be >= 2.2 A for the GSM burst; ripple 0.85 App at 12 V in. |
| C8/C9 | 2 x 100 uF 1210 | X5R loses ~40 % at 4 V bias; GSM bursts (2 A, 577 us) droop VSYS by about 0.3 V when only the buck supplies them. Add a 470 uF polymer cap if the field test shows brown-outs. |
| R3 | 6.8k | MCP73831 charge current 147 mA = 0.5 C for the 300 mAh cell. |
| R5/R6, R7/R8 | 1M/33k, 300k/100k | EC200U ADC input range assumed 0-1.2 V. Check it in the HD; scale the dividers if the range differs. |
| C16/R9 | 10 uF / 220k | PWRKEY low for about 1.5 s after VSYS rises (EC200U needs >= 500 ms). Check that the module does not toggle back off if PWRKEY is held low too long. If it does, use R10 (DNP 0R, permanent auto power-on) instead. |
| Q6 | AO3400A on a 1.8 V gate | Rds(on) is only specified from 2.5 V. At 1.8 V expect ~0.1 ohm, fine for a relay coil of up to 300 mA. Check it on the bench. |
| D1 | SMBJ24CA | 38.9 V clamp at Ipp. The XL1509 is rated 40 V absolute maximum, so there is little margin on a 24 V vehicle. The Lite is specified for 12 V two-wheelers only. |
| L76K V_BCKP | tied to VCC | GNSS loses its almanac while GNSS_EN is low. Firmware uses AGNSS on cold start. If time-to-first-fix after parking is too long, keep GNSS_EN high in sleep (+~10 mA). |

## Layout points

- Bottom layer: Freerouting put signal jumpers on the bottom GND plane, so the plane is slotted in places (see `05_renders/CRL-TRK-2W-L1_copper.png`). The RF lines run on the right edge and the top-left corner, over unbroken ground. Rev A1: re-route the long bottom jumpers on top by hand.
- LTE line: 1.2 mm / 0.2 mm CPWG (51 ohm, `rf_calc.py`) with a 0.5 mm neck between the module's GND pads 48/50, via fence every 1.5 mm. The pi pad C18/R14/C19 is for antenna matching on the bench.
- GNSS line: 4 mm, 0.5 mm wide (72 ohm, 0.035 lambda at 1575 MHz, mismatch loss < 0.1 dB).
