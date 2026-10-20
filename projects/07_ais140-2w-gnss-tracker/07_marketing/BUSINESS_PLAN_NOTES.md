# Samay Track 2W: business and product notes

These notes collect the discussion about turning CRL-TRK-2W-01 into a product for Samay Electronics.
All prices are **estimates** made in October 2026, excluding GST. Check them against real quotes before you commit money.
Detailed cost tables are in `PRICING_NOTES.md`. The line-by-line BOM is in `../03_fab/CRL-TRK-2W-01_BOM_costed.csv`.

---

## 1. What it is, range, and how it works

- **What:** a 4G LTE-M / NB-IoT tracker for motorcycles and scooters. It has:
  - dual-band GPS + NavIC;
  - a motion sensor;
  - an SOS input;
  - an engine-lock relay output;
  - an 18650 backup battery.
- **Range:** no distance limit. It sends data over the mobile network, so it works anywhere in India with LTE-M / NB-IoT coverage. Coverage is good in cities and thinner in rural areas. With no network it stores about 4 lakh points and uploads them later. Bluetooth (about 10 m) is used only for setup.
- **Battery:** about 40 h of tracking after a power cut, and more than 12 months asleep while parked (about 0.11 mA).
- **How it works:**
  1. Satellites give the position, and the IMU senses motion and crashes.
  2. It sends the position every 10 s over 4G to the cloud server.
  3. The server stores the data, applies rules (geofence, alarms) and sends push alerts to the app and, for AIS-140, to the state control room.
  4. When parked it sleeps. Movement wakes it and it sends a theft alert.
  5. SOS, crash, power cut and tamper each send an alert.
  6. Commands come back from the app: engine lock, settings, OTA update.
- **Network risk:** the SIM7080G has no 2G fallback.

## 2. What makes us different

**Real hardware advantages:**
1. Dual-band L1 + L5 GPS + NavIC, for better accuracy in cities. NavIC is required for AIS-140.
2. A 40-hour backup battery. Others run for minutes or hours, or have none.
3. Crash and fall detection with an industrial IMU. Others mostly offer a "vibration alert".
4. A 16 MB black box with about 4 lakh points.
5. Protection against reverse wiring, 36 V spikes and a 9–36 V input range.
6. About 0.11 mA sleep current. Others often draw 2–10 mA.
7. AIS-140 features in a 60 × 45 mm box. Other AIS-140 units are large boxes for buses and trucks.

**Not different:** 4G, live tracking, app, engine lock, SOS, geofence and ignition alerts. Everyone has these.

**Weaker:**
- price;
- no 2G;
- not certified yet;
- LTE-M coverage in rural areas.

Pitch: *"The only two-wheeler tracker with dual-band NavIC, a 40-hour backup and crash detection in a box that fits under the seat."*
Verify that claim against competitors' spec sheets before you use it.

## 3. Competitors (web listings, October 2026)

| Segment | Examples | Price |
|---|---|---|
| Budget 4G bike trackers | SeTrack, Ajjas 4G Lite, Onelap Micro / LocoShield, Fleettrack 4G | ₹900–2,900, then ≈ ₹999/yr |
| Mid-range | Alike GPS VT05R | from ₹3,999 |
| AIS-140 VLTD | Atlanta WP 30L, Gtropy, Algotrack and many others | ₹4,500–13,000, mostly ₹5–8k, + installation ₹300–1,500 + renewal ₹1,000–2,500/yr |
| Premium imported | Monimoto 9 | ≈ ₹47,000 |
| Built-in on EVs | Ather, Ola, TVS iQube, Bajaj Chetak | bundled with the scooter |

## 4. Cost of the full version (1 000 units)

| Item | ₹ |
|---|---|
| Modules: NEO-F10N ₹1,848, SIM7080G ₹836, ESP32-S3 ₹273 | 2,957 |
| Other ICs and sensors | 986 |
| Connectors, passives, discretes | 450 |
| PCB + assembly | 300 |
| **Assembled PCB** | **≈ 4,690** |
| Enclosure, antennas, battery pack, harness, packaging | ≈ 1,490 |
| **Total hardware** | **≈ 6,180** (≈ 6,600 landed with freight and customs) |
| Data SIM + cloud per year | ≈ 500–700 |

**Margins at the poster prices:**

| Plan | Margin |
|---|---|
| Rider ₹9,499, sold direct | ≈ 21 % |
| Rider ₹9,499, via a dealer | ≈ 3 % |
| Fleet ₹7,499 | ≈ 13 % |
| Renewal ₹1,999/yr | ≈ 70 % |

**Suggested prices:**

| Plan | Margin |
|---|---|
| Rider ₹10,999, sold direct | ≈ 31 % |
| Rider ₹10,999, via a dealer | ≈ 13 % |
| Fleet ₹7,999 | ≈ 18 % |

Most of the profit comes from renewals.

## 5. Lite version (designed: `lite/`, CRL-TRK-2W-L1)

The design is in `../lite/` (EC200U-CN + L76K + LIS3DH, 2-layer, single-sided). Its costed BOM comes to about Rs 1,440 per unit
including PCB, assembly, battery, antennas, enclosure, harness and packaging (`../lite/04_docs/BOM.md`). The table below is the original estimate.


| Part | Choice | ₹ |
|---|---|---|
| 4G modem | Cat-1 + 2G fallback, runs the firmware (A7672S / EC200U), so no ESP32 | 500–650 |
| GPS | L76K-class GPS + BeiDou, no NavIC | 200–250 |
| Accelerometer, power, 300 mAh cell, antennas, memory, SIM, protection | | 280–370 |
| 2-layer PCB + assembly | | 80–100 |
| Enclosure, harness, packaging | | 130–170 |
| **Total** | | **≈ 1,200–1,500** |

- Adding a NavIC-capable GPS adds ≈ ₹300–400, for a total of ≈ ₹1,600–1,800.
- You lose:
  - AIS-140 eligibility;
  - the 40-hour battery (only 2–4 h);
  - crash detection;
  - the large black box;
  - full 36 V protection.
- You gain 2G fallback and normal 4G coverage.
- Retail ₹2,999–3,499 including year 1 gives ≈ 35–40 % margin direct. Renewals at ₹999/yr give ≈ 50–60 %.

## 6. Selling on Amazon India

Yes, it can be sold on Amazon.

**Seller setup:**
- GSTIN, PAN, bank account;
- a trademark for "Samay" and Amazon Brand Registry;
- shipping through FBA or Easy Ship.

**Product approvals.** Confirm the full list with a compliance consultant.
- WPC ETA (radio);
- BIS IS 16046 for the lithium battery;
- TEC / MTCTE, if it applies;
- CPCB e-waste and battery EPR;
- DoT M2M service provider registration, if you sell the SIM or data;
- Legal Metrology labelling;
- a DPDP Act privacy policy and consent.

AIS-140 is not needed for consumer sales.

**Fees:** ≈ 12–20 % of the price, plus 5–10 % for ads at launch. A ₹2,999 Lite leaves ≈ ₹500–1,000 profit per unit.

**Recommendation:** Lite on Amazon for consumers. The full version sold directly to fleets and AIS-140 customers.

## 7. AIS-140

- **What it is:** an Indian standard (ARAI / MoRTH) for vehicle location tracking devices in public and commercial vehicles.
- **What it requires:**
  - GPS + NavIC;
  - a panic button linked to the state control room / 112;
  - live data to the state backend;
  - tamper and power-cut alerts, plus a backup battery;
  - store-and-forward and SMS fallback;
  - an embedded SIM with multiple operators;
  - OTA updates;
  - inputs and outputs.
- **Who must fit it:** buses, taxis, cabs, school vans and trucks with permits. Type approval comes from ARAI or ICAT, and the device must then be listed by each state.
- **Two-wheelers, three-wheelers and e-rickshaws are exempt** under the 2018 MoRTH notification. Bike-taxi rules vary by state, so check each one.

**Cost to get AIS-140 (estimates, apart from the state fees):**

| Item | Rough cost |
|---|---|
| Type-approval testing at ARAI / ICAT, 3–6 months | ≈ ₹5–15 lakh |
| Yearly Conformity of Production audit | ≈ ₹2–5 lakh/yr |
| State registration | ₹10,000 + ₹10,000 per model (Sikkim, West Bengal documents) |
| Performance bank guarantee | up to ₹25 lakh per state, refundable but locked |
| Integration with each state's backend | ≈ ₹1–3 lakh per state |
| WPC / BIS / TEC certification | ≈ ₹3–8 lakh |
| Board revision (eSIM, 2G question) | ≈ ₹2–5 lakh |
| **Total** | **≈ ₹15–25 lakh spent + ₹10–25 lakh+ in guarantees for 1–2 states** |

Do this only once a fleet or commercial customer is ready to buy.

## 8. How to sell (go-to-market)

1. **Get ready:**
   - 50–100 working units;
   - the app and server live;
   - WPC, BIS and EPR in place;
   - trademark, GST and website;
   - an IoT SIM deal with Jio or Airtel.
2. **B2B first** (the biggest orders):

   | Buyer | Why they buy |
   |---|---|
   | Two-wheeler loan companies (NBFCs, banks) | recovery of bikes on unpaid loans |
   | Bike rental firms | theft protection and tracking renters |
   | Delivery and bike-taxi fleets | rider safety and route proof |
   | Small EV makers | white-label tracking at ₹1,500–3,000 in bulk |
   | Insurers | lower premiums when a tracker is fitted |

   Start with free pilots of 10–50 units.
3. **Retail:**
   - bike showrooms and accessory shops, which install it for a 15–20 % margin;
   - Amazon / Flipkart for the Lite;
   - your own website and WhatsApp, with cash on delivery;
   - Instagram / YouTube demos and moto vloggers.
4. **Grow:**
   - renewals at ₹999–1,999/yr;
   - AIS-140 later;
   - expansion city by city with installer partners.

## 9. App and cloud: how it works on Android and iOS

```
Tracker --4G (MQTT over TLS)--> Cloud server (store, rules, push) --internet--> App (Android + iOS)
   ^                                                                                  |
   +------------------- commands (engine lock, settings, OTA) <-----------------------+
```

| Part | Choice |
|---|---|
| App, one code base for both | Flutter (or React Native) |
| Maps | Mappls (MapmyIndia) or Google Maps |
| Push alerts | Firebase Cloud Messaging (Android + iOS) |
| Device link | MQTT broker (EMQX / Mosquitto) |
| Server + database | Node.js / Python + PostgreSQL / TimescaleDB |
| Login | phone number + OTP |
| Hosting | AWS / Azure Mumbai or DigitalOcean Bangalore |
| Shortcut | open-source **Traccar** server, customised |

**Version 1 screens:**
- OTP login;
- live map;
- trip history;
- alerts: theft, SOS, crash, power cut, geofence;
- engine lock with PIN;
- geofence setup;
- battery and device status;
- share location with family;
- renewal via Razorpay.

A web dashboard for fleets uses the same server.

**Publishing:**
- Google Play: $25 one-time, review 1–3 days.
- Apple: $99/yr, review 1–7 days. The phone does not need background location.

**Cost and time:**

| Option | Cost | Time |
|---|---|---|
| Traccar + custom Flutter app | ₹2–4 lakh | 1–2 months |
| Fully custom | ₹5–10 lakh | 3–5 months |
| Server running cost | ₹3,000–10,000/month for the first few thousand devices | |

**Security essentials:**
- TLS everywhere;
- a unique key per device;
- PIN / OTP for engine lock;
- a privacy policy and consent (DPDP Act).

## 10. Things needed to make the app

**Accounts (in the company's name):**

| Account | Cost |
|---|---|
| Google Play Console | $25 |
| Apple Developer | $99/yr |
| Firebase | free |
| Cloud server | ₹3–10k/month |
| Domain | ₹800–1,500/yr |
| Maps API (Mappls / Google) | free tier, then pay per use |
| SMS OTP (MSG91 / Twilio / Firebase Auth) | ≈ ₹0.15–0.25 per SMS |
| Razorpay | 2 % per payment |
| Jio / Airtel IoT SIM plan | ≈ ₹300–600 per device per year |
| GitHub | already in place |

**Devices:**
- an Android phone;
- an iPhone **and a Mac with Xcode** (required for the iOS build);
- 2–3 assembled tracker boards (≈ ₹6–7k each). A simulator can stand in until then.

**Content:**
- app name and logo;
- colours (from the poster);
- privacy policy and terms (a draft can be written, but get it checked by a lawyer);
- support contact.

**Decisions:**
1. Traccar or custom server.
2. Mappls or Google Maps.
3. Renewal pricing.
4. Riders only, or a fleet dashboard too.
5. English only, or English + Hindi.

**Year-one running budget:** ≈ ₹60,000–1,50,000 (accounts, server, SMS), not counting hardware and SIM data.

Keep passwords and API keys out of chat and out of the repo. The code uses placeholder settings.

## 11. What Claude can and cannot build

**Can build (software, pushed to GitHub):**
- the Flutter app for Android and iOS;
- the cloud server, database, alert rules, push notifications and fleet dashboard;
- ESP32 tracker firmware: GPS, modem, alerts, sleep, offline log, OTA;
- a GPS simulator;
- setup guides, a privacy policy draft and store listing text;
- the Android APK, if the Flutter tools can be installed in this environment.

**Cannot do (needs the owner):**
- create or pay for accounts (stores, cloud, Firebase, Razorpay, SIM);
- build the iOS app (needs a Mac);
- order, assemble or test hardware;
- upload the app to the stores;
- obtain WPC / BIS / AIS-140 certification or legal sign-off.

Suggested start: the server, the Android app and the simulator. Then the tracker firmware.

## Sources

- [Amazon.in bike GPS tracker listings](https://www.amazon.in/Bike-GPS-Tracker/s?k=Bike+GPS+Tracker)
- [Kingsway: Best GPS trackers for cars and bikes in India 2026](https://kingswayaccessories.com/blog/best-affordable-gps-trackers-for-bike-and-car-security-india/)
- [Alike GPS: GPS tracker for bike](https://alikegps.com/gps-tracker-for-bike)
- [Sahaj GPS: top 10 GPS trackers India 2026](https://sahajgps.com/best-gps-trackers-india-2026-top-10-devices-compared)
- [Fleetx: AIS-140 GPS device price in India 2026](https://blog.fleetx.ai/blog-ais-140-gps-device-price-in-india-2026/)
- [Fleetx: AIS-140 full guide](https://blog.fleetx.ai/blog-ais140-guide/)
- [IndiaMART: AIS-140 VLTD 4G eSIM ₹10,999](https://www.indiamart.com/proddetail/algotrack-ais-140-gps-tracking-system-2853441771991.html)
- [IndiaMART: Atlanta WP 30L ₹6,608](https://www.indiamart.com/proddetail/atlanta-rto-dto-approved-ais-140-vltd-gps-23107433791.html)
- [IndiaMART: Gtropy VLTD ₹5,000](https://www.indiamart.com/proddetail/vltd-gtropy-gps-ais-140-27601807633.html)
- [TradeIndia: AIS-140 VLTD ₹4,500](https://www.tradeindia.com/products/ais-140-vltd-gps-device-8364149.html)
- [Sikkim Transport: AIS-140 empanelment SOP](https://transportdepartment.sikkim.gov.in/notificationdoc/notificationdoc-Rj9zY6O79NlvOCDgzpPERAbqzXweBXFCctlJLE56.pdf)
- [West Bengal Transport: VLTD registration](https://transport.wb.gov.in/wp-content/uploads/2023/02/VLTD-2-1.pdf)
- [Maxtrax: AIS-140 compliance guide](https://gps.maxtrax.in/ais-140-vehicle-tracking)
