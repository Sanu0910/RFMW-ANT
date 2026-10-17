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

## Poster prices (indicative)

| Plan | Price | Gross margin on hardware |
|---|---|---|
| Rider: device + 1 yr app and data | ₹9,499 | ≈ 30 % before dealer margin |
| Fleet AIS-140, 25+ units | ₹7,499 / unit + ₹1,499 / vehicle / yr | ≈ 23 % + recurring |
| Renewal | ₹1,999 / yr or ₹199 / month | ≈ 65–70 % |

The NEO-F10N is the biggest cost. A "Lite" version could drop to ≈ ₹3 900 hardware cost and a ≈ ₹5,999 retail price, using:
- an L1-only GNSS without NavIC (not AIS-140);
- a cheaper antenna.

Market check needed: AIS-140 VLTDs in India usually sell for about ₹4,000–9,000. Basic 2W trackers sell for ₹2,000–4,000, but they are mostly 2G with no backup battery.

Claims on the poster are kept to the design (AIS-140 *ready*, approval pending). Battery and sleep figures are calculations until they are measured on first articles.
