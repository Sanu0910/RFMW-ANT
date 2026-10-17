# Samay Track 2W: launch poster and pricing notes

Files:
- `poster.html` is the editable source (Inter fonts, 1200 × 1880 px).
- `SamayTrack2W_poster.png` (2400 × 3760) is for WhatsApp and social posts.
- `SamayTrack2W_poster.pdf` is for print.

Re-render with Chromium (headless window is ~90 px shorter than `--window-size`, so render taller and crop to 3760 px):

    chrome --headless=new --force-device-scale-factor=2 --window-size=1200,2000 --screenshot=raw.png poster.html
    chrome --headless=new --no-pdf-header-footer --print-to-pdf=SamayTrack2W_poster.pdf poster.html

Fill in the phone number and web address in the CTA line before you print.

## BOM cost per unit at 1 000 pcs (estimate, ₹88 / USD, excl. GST)

Line-by-line costing: `03_fab/CRL-TRK-2W-01_BOM_costed.csv`. Prices are typical LCSC / DigiKey 1k-qty prices
from memory, not quotes. Get real quotes before committing.

**A. PCB assembly (180 parts)**

| Group | ₹ |
|---|---|
| Modules: NEO-F10N ₹1,848, SIM7080G ₹836, ESP32-S3 ₹273 | 2,957 |
| ICs & sensors: IMU, charger, buck, ideal diode, gauge, RTC, flash, level shifter, ESD | 986 |
| Connectors: Micro-Fit, USB-C, SIM holder, battery, 2× U.FL | 208 |
| Passives: 112 R / C / L / fuse | 143 |
| Discretes & misc: MOSFETs, TVS, diodes, LEDs, buttons | 99 |
| **Board parts** | **4,392** |
| 4-layer PCB, ENIG, impedance control | 80 |
| SMT assembly, double-sided (JLC) | 220 |
| **Assembled PCB** | **≈ 4,690** |

**B. Box build**

| Item | ₹ |
|---|---|
| IP67 enclosure, gasket, cable gland | 250 |
| Active L1/L5 GNSS antenna | 550 |
| LTE flex antenna | 120 |
| 18650 pack with PCM and NTC | 220 |
| Harness, inline fuse, SOS button, relay | 300 |
| Box, label, manual | 50 |
| **Box build** | **≈ 1,490** |

**Total hardware ≈ ₹6,180 per unit.** Import freight and customs on the parts add ≈ ₹400–500, which brings
the landed cost to ≈ ₹6,600. Data SIM and cloud cost ≈ ₹500–700 per vehicle per year.

Cost-down options:
- Buying 10k units cuts module prices by 15–20 %.
- The ICM-42670 is a cheaper IMU than the IIM-42652.
- Generic U.FL connectors instead of Hirose.
- A "Lite" board with an L1-only GNSS and no NavIC would cost ≈ ₹4,000 in hardware, but it is not AIS-140.

## Poster prices and profit per unit (indicative, ex-GST)

Costs per unit, on top of ₹6,180 hardware:
- year-1 data and cloud: ₹600
- installation: ₹300 (Rider only)
- warranty reserve: 3 % of price
- packaging and shipping: ₹150

| Plan | Price | Total cost | Profit / unit | Margin |
|---|---|---|---|---|
| Rider, sold direct | ₹9,499 | ≈ ₹7,515 | ≈ ₹1,980 | ≈ 21 % |
| Rider, via dealer (18 % cut) | ₹9,499 | ≈ ₹9,225 | ≈ ₹270 | ≈ 3 % |
| Fleet AIS-140, 25+ units | ₹7,499 | ≈ ₹6,555 | ≈ ₹945 | ≈ 13 % |
| Fleet platform fee, per year | ₹1,499 | ₹600 | ≈ ₹900 | ≈ 60 % |
| Renewal, per year | ₹1,999 | ₹600 | ≈ ₹1,400 | ≈ 70 % |

Hardware margins are thin at these prices. Two suggested prices:

| Plan | New price | Profit / unit | Margin |
|---|---|---|---|
| Rider, sold direct | ₹10,999 | ≈ ₹3,435 | ≈ 31 % |
| Rider, via dealer | ₹10,999 | ≈ ₹1,455 | ≈ 13 % |
| Fleet AIS-140 | ₹7,999 | ≈ ₹1,430 | ≈ 18 % |

The real profit comes from renewals. Fixed costs are not included:
- AIS-140 / BIS / WPC / TEC approval
- app and server development
- moulds, fixture, staff and marketing

Market check needed: AIS-140 VLTDs in India usually sell for about ₹4,000–9,000. Basic 2W trackers sell for ₹2,000–4,000, but they are mostly 2G with no backup battery.

Claims on the poster are kept to the design (AIS-140 *ready*, approval pending). Battery and sleep figures are calculations until they are measured on first articles.
