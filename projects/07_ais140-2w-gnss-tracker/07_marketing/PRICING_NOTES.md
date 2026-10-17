# Samay Track 2W: launch poster and pricing notes

Files:
- `poster.html` is the editable source (Inter fonts, 1200 × 1880 px).
- `SamayTrack2W_poster.png` (2400 × 3760) is for WhatsApp and social posts.
- `SamayTrack2W_poster.pdf` is for print.

Re-render with Chromium (headless window is ~90 px shorter than `--window-size`, so render taller and crop to 3760 px):

    chrome --headless=new --force-device-scale-factor=2 --window-size=1200,2000 --screenshot=raw.png poster.html
    chrome --headless=new --no-pdf-header-footer --print-to-pdf=SamayTrack2W_poster.pdf poster.html

Fill in the phone number and web address in the CTA line before you print.

## Estimated unit cost at 1 000 pcs (INR, rough, excl. GST)

| Item | ₹ |
|---|---|
| NEO-F10N GNSS (L1/L5 + NavIC) | 1 900 |
| SIM7080G LTE-M/NB-IoT | 850 |
| ESP32-S3-WROOM-1-N8R2 | 260 |
| IMU, charger, buck, ideal diode, LDO, flash, RTC, gauge, passives | 950 |
| 4-layer PCB + double-sided SMT (JLC) | 350 |
| IP67 enclosure + gasket + gland | 250 |
| Active L1/L5 GNSS antenna + LTE flex antenna | 670 |
| 18650 pack with PCM and NTC | 220 |
| Harness, fuse, SOS button, relay | 300 |
| **Hardware total** | **≈ 5 750** |
| Data SIM + cloud, per vehicle per year | ≈ 500–700 |

## Poster prices and profit per unit (indicative, ex-GST)

Costs per unit, beyond the ≈ ₹5,750 hardware:
- year-1 data and cloud: ₹600
- installation: ₹300 (Rider only)
- warranty reserve: 3 % of price
- packaging and shipping: ₹150

| Plan | Price | Total cost | Profit / unit | Margin |
|---|---|---|---|---|
| Rider, sold direct | ₹9,499 | ≈ ₹7,085 | ≈ ₹2,400 | ≈ 25 % |
| Rider, via dealer (18 % dealer cut) | ₹9,499 | ≈ ₹8,795 | ≈ ₹700 | ≈ 7 % |
| Fleet AIS-140, 25+ units | ₹7,499 | ≈ ₹6,125 | ≈ ₹1,375 | ≈ 18 % |
| Fleet platform fee, per year | ₹1,499 | ₹600 | ≈ ₹900 | ≈ 60 % |
| Renewal, per year | ₹1,999 | ₹600 | ≈ ₹1,400 | ≈ 70 % |

Three years of one direct Rider customer:
- profit ≈ ₹2,400 + 2 × ₹1,400 = ₹5,200
- revenue ≈ ₹13,500
- margin ≈ 39 %

Not included above are fixed costs:
- AIS-140 type approval (ICAT/ARAI), BIS, WPC and TEC
- app and server development
- moulds, test fixture, staff and marketing

Break-even at ₹2,400 profit per unit: about 1,250 units for every ₹30 lakh of fixed cost.

The NEO-F10N is the biggest cost. A "Lite" version could drop to ≈ ₹3 900 hardware cost and a ≈ ₹5,999 retail price, using:
- an L1-only GNSS without NavIC (not AIS-140);
- a cheaper antenna.

Market check needed: AIS-140 VLTDs in India usually sell for about ₹4,000–9,000. Basic 2W trackers sell for ₹2,000–4,000, but they are mostly 2G with no backup battery.

Claims on the poster are kept to the design (AIS-140 *ready*, approval pending). Battery and sleep figures are calculations until they are measured on first articles.
