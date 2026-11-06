"""Design report for CRL-LS-CRPA4 -> 05_docs/CRL-LS-CRPA4_design_report.md + .html + .pdf (Chrome headless print).
Reads the outputs of rf_budget.py, make_fab.py, covers.py and drawings.py; run those first.
Run with the repo .venv:  python report.py
"""
import csv, json, os, shutil, subprocess
import markdown
import ls_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
DOCS = os.path.join(PRJ, "05_docs")
PN = "CRL-LS-CRPA4"
DATE = "06-11-2026"


def rows(name):
    return list(csv.DictReader(open(os.path.join(DOCS, name), encoding="utf-8")))


def mdtable(head, body):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in body]
    return "\n".join(out)


def build():
    S = json.load(open(os.path.join(DOCS, PN + "_rf_summary.json")))
    ch, pw, th = S["chains"], S["power"], S["thermal"]
    bud = rows(PN + "_rf_budget.csv")
    rej = rows(PN + "_rejection.csv")
    bom = list(csv.DictReader(open(os.path.join(PRJ, "04_fab", PN + "_BOM.csv"), encoding="utf-8")))
    n_place = sum(int(r["qty"]) for r in bom if r["side"] == "bottom")
    summ = mdtable(["Case", "Gain dB", "NF dB", "Input P1dB dBm", "IIP3 dBm", "2nd SAW rating dBm", "Antenna CW that reaches it dBm"],
                   [[v["case"], f"{v['gain_db']:.1f}", f"{v['nf_db']:.2f}", f"{v['ip1db_dbm']:.1f}", f"{v['iip3_dbm']:.1f}",
                     f"{v['saw_rating_dbm']:.0f}", f"{v['p_ant_saw2_dbm']:.1f}"] for v in ch.values()])
    budget_md = ""
    for case in dict.fromkeys(r["case"] for r in bud):
        rr = [r for r in bud if r["case"] == case]
        budget_md += f"\n**{case}**\n\n" + mdtable(["#", "Stage", "G dB", "NF dB", "Cum. G dB", "Cum. NF dB", "Note"],
                                                   [[i, r["stage"], r["gain_db"], r["nf_db"], r["cum_gain_db"], r["cum_nf_db"], r["note"]]
                                                    for i, r in enumerate(rr)]) + "\n"
    rej_md = mdtable(["Branch", "Interferer", "MHz", "Rejection dB (rel. pass band)"],
                     [[r["band"].replace("L2", "L2/L5"), r["interferer"], r["f_mhz"], r["rejection_db"]] for r in rej])
    st = mdtable(["Layer", "Type", "mm", "er", "Note"],
                 [[n, t, f"{thk:.3f}", "" if er is None else er, note] for n, t, thk, er, note in D.STACKUP if thk or t == "copper"])
    weak = [r for r in rej if r["rejection_db"] not in (">80",) and float(r["rejection_db"]) < 20]
    weak_txt = "; ".join(f"{r['interferer']} {r['rejection_db']} dB" for r in weak)

    md = f"""# {PN} - L1 + L2/L5 + NavIC S 4-channel CRPA front end
## Design report, Rev A

BEL - CRL, Antenna / RFM lab. Date {DATE}. Project folder `projects/02_ls-crpa4-rf-module`.

## 1. Summary

{PN} is a D200 mm, 4-layer active antenna board for a 4-element controlled-reception-pattern antenna (CRPA). Each
element has a stacked GPS L1/L2 patch (GPDF6010.A) and a NavIC S patch (CRL-LS-SP01, BEL CRL). Every element feeds
three filtered, amplified branches (L1, L2/L5, S): 2 LNAs and 3 SAW filters per branch, as in projects 16 and 17.
L1 and L2/L5 are combined in a DXP.02.A diplexer per channel. Outputs: 4 L SMA + 4 S SMA, +5 V on one DC connector.
A machined aluminium back cover (BC01) gives every chain its own shielded cavity.

{summ}

Supply {pw['i_typ_a']:.2f} A typ / {pw['i_max_a']:.2f} A max at 5 V ({pw['p_typ_w']:.1f} W typ). Board DRC: 0 violations, 0 unconnected.
Fabrication package complete (Gerber X2, Excellon, pick-and-place, IPC-D-356, BOM with {len(bom)} lines / {n_place} placements).

**Key findings (section 7):**

1. Weak rejection close to the bands: {weak_txt}.
2. Gain and filter ratings: an in-band CW jammer of {ch['L5']['p_ant_saw2_dbm']:.0f} dBm (L2/L5),
   {ch['L1']['p_ant_saw2_dbm']:.0f} dBm (L1) or {ch['S']['p_ant_saw2_dbm']:.0f} dBm (S) at the antenna drives the 2nd SAW to its
   power rating. The input 1 dB compression point is {ch['L5']['ip1db_dbm']:.0f} to {ch['L1']['ip1db_dbm']:.0f} dBm (L) and
   {ch['S']['ip1db_dbm']:.0f} dBm (S). For a CRPA, which must stay linear under jamming, this is the main Rev B item.

## 2. Design basis and decisions

| Item | Decision | Source |
|---|---|---|
| Bands | GPS L1 1575.42; wide L2/L5 1164-1240; NavIC S 2492.028 MHz | user, 2026-11-05 |
| Elements | 4, square, sequential rotation (-90 deg x k) | customer board combine_model_2.0 |
| L spacing | {D.ELEMENT_PITCH} mm (0.48 lambda at L1) | customer board |
| S spacing | {D.S_SPACING:.2f} mm = lambda/2 at 2492.028 MHz, R {D.S_RADIUS:.2f} mm | user, 2026-11-06 |
| Chain | limiter -> LNA -> SAW -> LNA -> SAW -> SAW per branch | projects 16 / 17 |
| Supply | +5 V, one DC connector, reverse-polarity PFET, fuse, TVS | user |
| Outputs | 8 SMA (L and S separate) + DC | user |
| Board | D200 mm, same size as the L-band board | user |

## 3. Architecture

![block diagram](../07_drawings/{PN}_sheet6.png)

Per element: the patch feeds go to a 90 deg hybrid (HC125A for L1 and L2, Xinger C2327J5003AHF for S), which combines
them into RHCP. The hybrid's isolated port goes to 50 ohm. Next comes a CLM-83-2W+ PIN limiter (CW +32 dBm, limited
output +11.5 dBm typ), then the LNA / SAW cascade. S hybrid wiring: F0 -> pin 4 (direct), F90 -> pin 6 (coupled).
This is RHCP because F90 sits +90 deg counter-clockwise (top view) from F0. `build_pcb.py` checks it on every build.

### Array geometry

![array](../07_drawings/{PN}_sheet2.png)

The S patches sit at lambda/2 ({D.S_SPACING:.2f} mm) so the S sub-array has no grating lobes and keeps full nulling
depth. Each S patch clears its L neighbours by about 1 mm (25 x 25 mm patch). Mutual coupling L-to-S must be measured
(section 9).

## 4. Stack-up and transmission lines

{st}

The 50 ohm microstrip on L4 is {D.RF_W} mm over the RO4350B 0.168 mm core to the L3 ground. Loss is 0.066 dB/cm at
2.5 GHz, against 0.121 dB/cm for the same line on FR-4 7628. L1 is the solid antenna ground plane. L2 carries the
per-channel +5 V star traces inside GND. Fence vias run along every RF line; frame vias sit at 2.5 mm pitch on every
shield land.

## 5. Layout

![bottom](img/render_bottom.png)

All SMD parts are on L4 (bottom); the patches are on L1 (top). Each L channel sits inside an octagonal ground frame,
and each S chain inside a strip frame in the axis gap between L channels. Neighbouring frames share walls, so one
cover wall serves both cavities. The TA1442A and C2327J5003AHF land patterns follow the vendor drawings (Tai-Saw Rev 1,
TTM Rev K). Ground pads carry filled vias (IPC-4761 VII) for the lowest ground inductance.

## 6. RF budget (antenna feed -> SMA, 25 C typical)

Data: project 16 Touchstone models (LNA, SAW, hybrid, diplexer), project 17 stage values for the L chain, this
board's RF track lengths. Line loss is scaled with f^0.75 from 0.066 dB/cm at 2.5 GHz [ESTIMATE]. The CLM-83-2W+
loss at S is 0.30 dB [ESTIMATE]. The S LNA noise figure is 0.60 dB (NFmin 0.51 dB at 2.5 GHz + 0.1 dB match) [ESTIMATE].
{budget_md}

![cascade](img/rf_cascade.png)

The system noise figure is set ahead of LNA1: hybrid, limiter and lines add 0.4-0.7 dB. Gain at the SMA is 33-41 dB,
before the cable to the CRPA electronics.

## 7. Interference rejection, linearity and filter power

### 7.1 Rejection

{rej_md}

![rejection](img/rf_rejection.png)

The cascaded model gives over 100 dB far from the bands. A real board leaks around the filters (cover cavities,
ground, bias lines), so anything above 80 dB is quoted as ">80". Near-band results that matter:
- **NavIC S:** the TA1442A curve stays within about 3 dB loss from roughly 2445 to 2540 MHz. The "5 MHz bandwidth"
  in its datasheet is only the window it is specified over. WiFi channels 11-13, Bluetooth, LTE B41 (2496-2690,
  used in India) and B7 uplink (2500-2570) therefore pass almost unattenuated. Wi-Fi ch6 gets 45 dB.
- **L2/L5:** DME / TACAN replies up to 1150-1213 MHz overlap the wide 1164-1240 MHz band; only about 10 dB at 1150 MHz.
- **L1:** Iridium (1616-1626 MHz) 43 dB; Inmarsat uplink > 80 dB.

### 7.2 Linearity and SAW power rating

| Branch | 2nd SAW | Rating | Gain ahead of SAW #1 / #2 | CW at antenna that reaches the rating (SAW #1 / #2) |
|---|---|---|---|---|
| L1 | B7504 | 15 dBm (out of band, 5000 h) | about 21 / 42 dB | {ch['L1']['p_ant_saw1_dbm']} / {ch['L1']['p_ant_saw2_dbm']} dBm |
| L2/L5 | B8889 | 5 dBm CW (2000 h at 55 C) | about 23 / 45 dB | {ch['L5']['p_ant_saw1_dbm']} / {ch['L5']['p_ant_saw2_dbm']} dBm |
| S | TA1442A | 10 dBm | about 17 / 35 dB | {ch['S']['p_ant_saw1_dbm']} / {ch['S']['p_ant_saw2_dbm']} dBm |

The limiter caps the LNA1 input at about +11.5 dBm, but LNA2 can still deliver +20 dBm into SAW #2. A jammer
30-40 dB above the noise floor near the antenna is normal for a CRPA. The present gain distribution then overdrives
SAW #2 and compresses the chain before the nulling electronics see the signal.

**Rev B recommendations:**

1. Cut the gain to about 25-28 dB per branch. Use one LNA ahead of the first SAW and a lower-gain second stage, or a
   3-6 dB pad between LNA2 and SAW #2. This raises the input P1dB to about -10 dBm and keeps SAW #2 below rating.
2. For S, add a second-stage filter with a sharp upper skirt (ceramic / BAW, LTE B41 and B7 rejection) or a
   tighter S SAW. For L2/L5, decide whether the band must start at 1164 MHz (DME); 1166-1240 with a steeper
   filter removes DME.
3. Specify the receiver-side requirement: required gain at the antenna port, J/S to survive, recovery time.

## 8. Power and thermal

| Item | Value |
|---|---|
| LNAs | 24 x TQP3M9037, 70 mA typ / 90 mA max at 5 V |
| Supply current | {pw['i_typ_a']:.2f} A typ / {pw['i_max_a']:.2f} A max |
| Power | {pw['p_typ_w']:.1f} W typ / {pw['p_max_w']:.1f} W max (5.25 V) |
| LNA dissipation | {th['p_lna_w']:.2f} W each, theta_jc {th['theta_jc']} C/W -> +{th['dT_jc']} C over the case |
| Tj at 85 C case | {th['tj_85']} C (limit for > 1e6 h MTTF: {th['tj_limit']:.0f} C) |
| Heat path | exposed pad -> filled vias -> L3 / L2 GND -> cover walls through the conductive gasket |

The thermal margin is large. The open point is the case temperature inside the sealed cover at the platform's maximum
ambient (section 9).

## 9. Back cover BC01 (L + S)

![cover](../07_drawings/{PN}_sheet5.png)

One machined Al 6061-T6 part, D200 mm, 11 mm high, 464 g, chromate conversion (conductive). Walls 1.2 mm wide run on
every shield-frame land, so each L channel and each S chain has its own cavity. A form-in-place conductive gasket goes
on the wall tops. RF tunnels 2.6 x 1.0 mm pass under the walls. There are 8 recessed SMA openings, an M8 DC
receptacle, and 16 x M3 through cover, board and L patch. The outside face is engraved with the BEL logo, P/N,
date, S/N and channel labels.

## 10. Manufacturing package

| File | Content |
|---|---|
| `04_fab/{PN}_Gerbers.zip` | Gerber X2 (4 Cu, mask, paste, silk, outline), Excellon PTH/NPTH + drill map |
| `04_fab/{PN}_CPL_bottom.csv` | pick-and-place, bottom side |
| `04_fab/{PN}.d356` | IPC-D-356 netlist for the bare-board electrical test |
| `04_fab/{PN}_BOM.csv / .xlsx` | {len(bom)} lines incl. mechanical items |
| `04_fab/{PN}_FAB_NOTES.md` | stack-up, impedance, finish, via plugging, assembly and test |
| `06_step/{PN}_PCB.step`, `06_step/{PN}-BC01.step` | board and cover in one frame |
| `07_drawings/{PN}_DRAWINGS.pdf` | 6 sheets: fab, array, assembly bottom / top, cover, block diagram |

## 11. Open items and review gaps

- Inputs needed: CRL-LS-SP01 drawing and measured S11 / axial ratio; L patch fixing holes (board D3.6 / D1.35 vs
  GPDF6010.A D1.8 / D1.1); supply bus (5 V or 28 V); platform (MIL-STD-810 / 461 levels); CRPA processor gain /
  match / delay requirements; radome; interference environment.
- Not yet built: test boards (one L channel, one S chain, THRU line) and their cover.
- Full list: `05_docs/{PN}_design_review_gaps.md`.

## 12. Assumptions

Values marked [ESTIMATE] / [ASSUMED] in the tables; project 16 `assumptions_log.md` (copied in `00_reference/p16`) for
the component models. All data at 25 C typical; no temperature, part-to-part or ageing spread.
"""
    p_md = os.path.join(DOCS, PN + "_design_report.md")
    open(p_md, "w", encoding="utf-8").write(md)
    html = markdown.markdown(md, extensions=["tables"])
    css = """body{font-family:Segoe UI,Arial,sans-serif;font-size:10.5pt;line-height:1.38;margin:18mm 16mm;color:#111}
h1{font-size:19pt;border-bottom:2px solid #1f4e79;padding-bottom:4px;color:#1f4e79}h2{font-size:13.5pt;color:#1f4e79;
margin-top:20px;border-bottom:1px solid #c9d0d6}h3{font-size:11.5pt}table{border-collapse:collapse;margin:8px 0;font-size:8.6pt}
td,th{border:1px solid #999;padding:2px 6px}th{background:#e8ecef}img{max-width:100%;border:1px solid #ddd;margin:6px 0}
code{font-size:9pt;background:#f3f3f3;padding:0 2px}@page{size:A4;margin:12mm}"""
    p_html = os.path.join(DOCS, PN + "_design_report.html")
    open(p_html, "w", encoding="utf-8").write(f"<!doctype html><html><head><meta charset='utf-8'><title>{PN} design report</title>"
                                             f"<style>{css}</style></head><body>{html}</body></html>")
    chrome = next((c for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if os.path.exists(c)), None)
    if chrome:
        p_pdf = os.path.join(DOCS, PN + "_design_report.pdf")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={p_pdf}", "file:///" + p_html.replace("\\", "/")], capture_output=True, timeout=120)
        print("pdf", os.path.exists(p_pdf), os.path.getsize(p_pdf) if os.path.exists(p_pdf) else 0)
    print(p_md)


if __name__ == "__main__":
    build()
