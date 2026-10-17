# Items to verify against vendor documents before release

The build machine could not reach vendor websites, so these values come from design experience and family
knowledge rather than the exact datasheet page. Each must be checked and signed off before ordering production.

| # | Ref | Item | Current value | Check against |
|---|---|---|---|---|
| 1 | R3 | LM5164 RON for ≈ 300 kHz at 5 V out | 160 k | LM5164-Q1 datasheet, "Switching frequency (RON)" equation |
| 2 | R1/R2 | LM5164 EN/UVLO divider (EN threshold) | 1 M / 330 k → ≈ 6 V | EN/UVLO rising threshold |
| 3 | R4/R5 | LM5164 FB reference 1.2 V | 316 k / 100 k → 5.0 V | VREF |
| 4 | C7, L1 | BST cap 2.2 nF, L = 22 µH ripple and Isat | — | LM5164 application section |
| 5 | R9 | BQ24074 K_ILIM | 1550 AΩ → 1.03 A | BQ24074 datasheet |
| 6 | R10 | BQ24074 K_ISET | 890 AΩ → 500 mA | BQ24074 datasheet |
| 7 | R11, R12 | ITERM and TMR programming | 15 k / 46.4 k | BQ24074 datasheet (TMR open = default timer?) |
| 8 | U3 | BQ24074 VO(REG) = 4.4 V (variant table) | assumed | bq2407x selection table; if 5.5 V, SIM7080G VBAT max 4.8 V is exceeded → choose BQ24079/BQ24074 accordingly |
| 9 | U4 | LC709203F TSW/TSENSE unused, TEST to VSS | NC / GND | LC709203F datasheet |
| 10 | U16 | RV-3028 VBACKUP to VBAT (≤ 5.5 V), EVI input levels | VBAT | RV-3028-C7 application manual |
| 11 | U6/U7 | TPS22917 QOD via 100 Ω to VOUT | 100 R | TPS22917 datasheet QOD options |
| 12 | F1 | Littelfuse 0466 2 A MPN suffix | 0466002.NRHF | Littelfuse catalogue |
| 13 | FB1 | BLM21PG601SN1D current rating ≥ 1 A, automotive variant | — | Murata |
| 14 | U11 | SIM7080G land pattern: outer pad toe 17.3/19.2 mm vs SIMCom 16.7/18.6 mm | dev-board pads | SIMCom SIM7080G HD V1.05 fig. "Recommended footprint" |
| 15 | U11 | "Forbidden area" keep-out position | approx. 5.9–6.95 × −7.9…−4.6 mm | same figure |
| 16 | U14 | NEO-F10N on the generic `ublox_NEO` land pattern | KiCad lib | u-blox NEO-F10N integration manual, land pattern |
| 17 | U8 | ESP32 antenna keep-out reduced to ±12 mm (board-edge antenna) | — | Espressif HW design guide; verify BLE range ≥ 5 m in enclosure |
| 18 | J5 | Hinged nano-SIM holder under vibration | dev only | replace by MFF2 eSIM (AIS-140) |
| 19 | — | AIS-140 acceptance of LTE-M/NB-IoT without 2G fallback | — | CDAC / ICAT |
| 20 | — | Final LTE / GNSS antenna matching | π pads DNP | VNA in the final enclosure |
