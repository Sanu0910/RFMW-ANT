# Samay Track Lite (preliminary)

A low-cost 4G Cat-1 + 2G bike tracker. **Not designed yet.** This folder holds the plan, the preliminary BOM and the poster.

| File | Content |
|---|---|
| `LITE_BOM_preliminary.csv` | Candidate parts with estimated 1k prices (≈ ₹1,362 per unit) |
| `poster_lite.html` / `SamayTrackLite_poster.png` / `.pdf` | Launch poster (₹3,499 incl. year 1, then ₹999/yr) |
| `../07_marketing/SamayTrack_Lite_Plan.pdf` | 3-page plan: design, cost, price, money, timeline |

## BOM summary (estimate at 1,000 pcs, INR, excl. GST)

| Group | Main parts | ₹ |
|---|---|---|
| Modules | A7672S LTE Cat-1 + GSM (runs the firmware) · Quectel L76K GPS + BeiDou | 780 |
| ICs | LIS2DH12 accelerometer · LMR16010 60 V buck · BQ21040 charger · TLV75533 LDO · W25Q32 flash | 151 |
| Protection + I/O | SMBJ33CA TVS · reverse-polarity MOSFET · PTC fuse · SIM ESD · input clamps · relay MOSFET · LEDs | 35 |
| Connectors | nano-SIM, battery, harness, IPEX | 26 |
| Antennas | 25 mm GNSS ceramic patch · LTE FPC | 70 |
| Battery | 300 mAh Li-po with PCM (BIS registered) | 55 |
| Passives | ≈ 60 R/C/L + 2× 220 µF bulk caps for 2G bursts | 45 |
| PCB + SMT | 2-layer ≈ 50 × 35 mm, single-sided | 65 |
| Box build | IP65 enclosure, 4-wire harness with fuse, packaging | 135 |
| **Total** | | **≈ 1,362** |

Options:
- NavIC GNSS: + ₹300–400
- SOS push-button: + ₹25
- MFF2 eSIM instead of the nano-SIM holder

Prices are typical distributor or China-sourcing prices from memory, not quotes. Get real quotes before you commit.

**Design note:** in 2G the modem draws ≈ 2 A peaks, so the power path needs the battery plus the bulk capacitors. Size the buck and the charger for that.

Regenerate the poster (render taller and crop, because the headless window is ≈ 90 px shorter than `--window-size`):

    chrome --headless=new --force-device-scale-factor=2 --window-size=1200,1760 --screenshot=raw.png poster_lite.html   # crop to 2400 × 3280
    chrome --headless=new --no-pdf-header-footer --print-to-pdf=SamayTrackLite_poster.pdf poster_lite.html
