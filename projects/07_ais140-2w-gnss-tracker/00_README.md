# 07 — AIS-140 two-wheeler GNSS / LTE tracker (two variants)

Two tracker PCBs for motorcycles and scooters, sharing the same product family but
targeting different price/feature points. Each variant is a self-contained design
(schematic, routed PCB, fab package, 3D and docs) in its own subfolder.

| Variant | Board | Folder | Summary |
|---|---|---|---|
| **Premium** | `CRL-TRK-2W-01` | [`premium/`](premium/) | 60×45 mm, 4-layer, AIS-140 production board: ESP32-S3-WROOM-1, SIM7080G LTE-M/NB-IoT, u-blox NEO-F10N (L1/L5 + NavIC), IIM-42652 IMU, BQ24074 + 18650 backup, automotive front-end (LM74700-Q1, LM5164-Q1), W25Q128 log flash, RV-3028 RTC |
| **Lite** | `CRL-TRK-2W-L1` | [`lite/`](lite/) | cost-reduced 2-layer board: Quectel EC200U modem, L76K GNSS, MFF2 eSIM — smaller BOM for a lower price point |

Open each subfolder's `00_README.md` for that variant's details, folder map and
regenerate/build steps.
