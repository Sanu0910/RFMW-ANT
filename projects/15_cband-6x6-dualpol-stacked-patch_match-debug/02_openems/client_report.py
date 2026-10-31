"""Client-facing report (Telmart branding): 04_docs/Telmart_CBand_Array_VSWR_Report.pdf

Same results as the engineering report (build_report.py), written for the client: summary, issue, design,
process, findings, root causes, recommendations, next steps.  Figures come from 03_results and 04_docs.

    python client_report.py          (needs node + Playwright Chromium, like build_report.py)
"""
import os, base64, subprocess, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, '..', '03_results'); D = os.path.join(HERE, '..', '04_docs')
OUT_HTML = os.path.join(D, 'Telmart_CBand_Array_VSWR_Report.html')
OUT_PDF = os.path.join(D, 'Telmart_CBand_Array_VSWR_Report.pdf')
DOC_REF, REV = 'TM-RF-15-001', 'A'
BLUE, RED = '#0f6cbd', '#e31e24'


def b64(path):
    ext = os.path.splitext(path)[1].lstrip('.').replace('jpg', 'jpeg')
    return f'data:image/{ext};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def fig(path, n, cap, width='92%'):
    if not os.path.exists(path):
        return ''
    return f'<figure><img src="{b64(path)}" style="width:{width}"><figcaption><b>Figure {n}.</b> {cap}</figcaption></figure>'


def interim_stats():
    p = os.path.join(R, 'array_interim_S.csv')
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p, delimiter=','); f = d[:, 0]; m = (f >= 4) & (f <= 7)
    out = {}
    for name, col in (('V', 1), ('H', 3)):
        if d.shape[1] > col:
            g = 10 ** (d[m, col] / 20); v = (1 + g) / (1 - g)
            out[name] = (v <= 3).mean() * 100
    return out


def measured_table():
    """HTML table of the bench measurements (05_measured/measured_2026-10-30.csv) with aperture efficiency."""
    p = os.path.join(HERE, '..', '05_measured', 'measured_2026-10-30.csv')
    if not os.path.exists(p):
        return ''
    m = np.genfromtxt(p, delimiter=',', comments='#', skip_header=4, names=True)
    extra = {5800: (-14.687, -13.329), 6000: (-14.039, -8.103)}   # nearest S11 markers (5.7 / 5.9 GHz)
    rows = ''
    for r in m:
        f = r['f_MHz']; ceil = 10 * np.log10(4 * np.pi * 0.27686 ** 2 / (3e8 / (f * 1e6)) ** 2)
        a, b = r['S11_A_dB'], r['S11_B_dB']
        sa = f'{a:.1f}' if np.isfinite(a) else f'{extra[int(f)][0]:.1f}*'
        sb = f'{b:.1f}' if np.isfinite(b) else f'{extra[int(f)][1]:.1f}*'
        eff = lambda g: f'{10 ** ((g - ceil) / 10) * 100:.0f} %'
        rows += (f'<tr><td>{f / 1e3:.1f}</td><td>{sa}</td><td>{sb}</td><td>{r["gain_V_dBi"]:.1f}</td><td>{r["gain_H_dBi"]:.1f}</td>'
                 f'<td>{ceil:.1f}</td><td>{eff(r["gain_V_dBi"])} / {eff(r["gain_H_dBi"])}</td></tr>')
    return ('<table><tr><th>f (GHz)</th><th>S11 port A (dB)</th><th>S11 port B (dB)</th><th>Gain V (dBi)</th><th>Gain H (dBi)</th>'
            '<th>Aperture limit (dBi)</th><th>Aperture efficiency V / H</th></tr>' + rows + '</table>'
            '<p class="small">* nearest S11 marker (5.7 / 5.9 GHz). Gain by substitution against a reference horn at ~5 m. '
            'Port A/B to V/H mapping and radome condition during the gain test to be confirmed.</p>')


CSS = f"""
@page {{ size: A4; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1d2733; margin: 0; }}
.cover {{ height: 255mm; position: relative; page-break-after: always; }}
.cover .logo {{ width: 62%; margin-top: 18mm; }}
.cover .band {{ height: 6px; background: linear-gradient(90deg, {BLUE} 0 78%, {RED} 78% 100%); margin: 16mm 0 12mm 0; }}
.cover h1 {{ font-size: 25pt; color: {BLUE}; margin: 0 0 6px 0; line-height: 1.15; }}
.cover .subtitle {{ font-size: 13pt; color: #44505c; margin-bottom: 18mm; }}
.cover table.meta {{ width: 70%; font-size: 9.5pt; border: none; }}
.cover table.meta td {{ border: none; border-bottom: 1px solid #dde3ea; padding: 5px 4px; }}
.cover table.meta td:first-child {{ color: #6b7785; width: 38%; }}
.cover .conf {{ position: absolute; bottom: 0; left: 0; right: 0; font-size: 8pt; color: #6b7785; border-top: 1px solid #dde3ea; padding-top: 6px; }}
.status {{ display: inline-block; background: #fff4e5; color: #9a5b00; border: 1px solid #f0c27a; border-radius: 3px; padding: 1px 8px; font-size: 9pt; }}
.hdr {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid {BLUE}; padding-bottom: 4px; margin-bottom: 10px; }}
.hdr img {{ height: 22px; }} .hdr span {{ font-size: 8pt; color: #6b7785; }}
h2 {{ font-size: 14pt; color: {BLUE}; margin: 18px 0 6px 0; page-break-after: avoid; }}
h2 .num {{ color: {RED}; margin-right: 6px; }}
h3 {{ font-size: 11pt; color: #23476b; margin: 12px 0 4px 0; page-break-after: avoid; }}
p {{ margin: 5px 0 7px 0; text-align: justify; }}
.pb {{ page-break-before: always; }}
.kpi {{ display: flex; gap: 8px; margin: 10px 0 12px 0; }}
.kpi div {{ flex: 1; border: 1px solid #dde3ea; border-top: 4px solid {BLUE}; padding: 7px 9px; border-radius: 3px; }}
.kpi div.bad {{ border-top-color: {RED}; }}
.kpi b {{ display: block; font-size: 15pt; color: #1d2733; }} .kpi span {{ font-size: 8.3pt; color: #5b6774; }}
.callout {{ border-left: 5px solid {BLUE}; background: #eef5fc; padding: 8px 12px; margin: 10px 0; page-break-inside: avoid; }}
.callout.red {{ border-left-color: {RED}; background: #fdeeee; }}
.callout.amber {{ border-left-color: #d98b00; background: #fff6e8; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0 12px 0; font-size: 8.9pt; page-break-inside: avoid; }}
th {{ background: {BLUE}; color: white; text-align: left; padding: 5px 7px; font-weight: 600; }}
td {{ border-bottom: 1px solid #dde3ea; padding: 4px 7px; vertical-align: top; }}
tr:nth-child(even) td {{ background: #f6f9fc; }}
figure {{ margin: 10px 0; text-align: center; page-break-inside: avoid; }}
figcaption {{ font-size: 8.5pt; color: #4d5966; margin-top: 4px; text-align: left; padding: 0 4%; }}
.flow {{ display: flex; flex-wrap: wrap; gap: 0; margin: 12px 0; align-items: stretch; page-break-inside: avoid; }}
.step {{ width: 22.5%; border: 1px solid #c9d6e3; border-radius: 4px; padding: 7px 8px; background: #f7fafd; font-size: 8.5pt; box-sizing: border-box; margin: 0 0 8px 0; }}
.step b {{ display: block; color: {BLUE}; font-size: 9pt; margin-bottom: 2px; }}
.step i {{ display: inline-block; background: {RED}; color: white; font-style: normal; border-radius: 50%; width: 16px; height: 16px; text-align: center; font-size: 8pt; line-height: 16px; margin-right: 4px; }}
.arrow {{ width: 3.3%; display: flex; align-items: center; justify-content: center; color: {BLUE}; font-size: 13pt; margin-bottom: 8px; }}
ul, ol {{ margin: 4px 0 8px 0; padding-left: 20px; }} li {{ margin-bottom: 3px; }}
.small {{ font-size: 8.5pt; color: #5b6774; }}
"""


def header():
    return (f'<div class="hdr"><img src="{LOGO}"><span>{DOC_REF} Rev. {REV} &middot; C-band 6&times;6 array &middot; '
            f'VSWR investigation</span></div>')


def flow():
    steps = [('Design inputs', 'Gerber/DXF layers and stack-up decoded; feed networks traced'),
             ('3D EM model', 'Full-wave FDTD model of one element built straight from the layout'),
             ('Element analysis', 'Input match, impedance and gain of the element as built'),
             ('Diagnostics', 'Parasitic removed / resized to separate the causes'),
             ('Matching study', 'Best possible feed-network match computed from the element impedance'),
             ('Full-array model', 'Complete 276 mm board with both 36-way feed networks (12 M cells)'),
             ('Redesign study', 'Wideband aperture-coupled element explored (40 simulations)'),
             ('Recommendations', 'Root causes ranked; corrective actions and next steps')]
    html = '<div class="flow">'
    for i, (t, d) in enumerate(steps):
        html += f'<div class="step"><b><i>{i + 1}</i>{t}</b>{d}</div>'
        if i % 4 != 3:
            html += '<div class="arrow">&#10140;</div>'
    return html + '</div>'


def body():
    st = interim_stats() or {}
    date = datetime.date.today().strftime('%d %B %Y')
    n = iter(range(1, 20))
    return f"""
<div class="cover">
  <img class="logo" src="{LOGO}">
  <div class="band"></div>
  <h1>C-Band 6&times;6 Dual-Polarised Antenna Array</h1>
  <div class="subtitle">Input-match (VSWR) investigation: root cause, findings and corrective actions</div>
  <table class="meta">
    <tr><td>Document</td><td>{DOC_REF}, Revision {REV}</td></tr>
    <tr><td>Date</td><td>{date}</td></tr>
    <tr><td>Report type</td><td>Technical investigation report</td></tr>
    <tr><td>Frequency band</td><td>4.0&ndash;7.0 GHz (C-band)</td></tr>
    <tr><td>Prepared by</td><td>Telmart RF &amp; Microwave Engineering</td></tr>
    <tr><td>Status</td><td><span class="status">Interim: full-array verification in progress</span></td></tr>
  </table>
  <div class="conf">This report contains confidential technical information prepared for the client. It may not be
  reproduced or passed to third parties without the written consent of Telmart.</div>
</div>

{header()}
<h2><span class="num">1</span>Executive summary</h2>
<p>The 6&times;6 dual-polarised stacked-patch array radiates with the expected broadside gain, but its input match is poor:
the VSWR does not stay below 3:1 across the 4&ndash;7 GHz band. Telmart analysed the design with full-wave electromagnetic
simulation built directly from the supplied layout files, at element level and for the complete array.</p>
<div class="kpi">
  <div class="bad"><b>~16 %</b><span>Element bandwidth (VSWR &le; 3), 5.35&ndash;6.26 GHz</span></div>
  <div><b>54 %</b><span>Bandwidth required for 4&ndash;7 GHz</span></div>
  <div><b>8.7&ndash;9.8 dBi</b><span>Element gain referred to accepted power: the radiator works</span></div>
  <div class="bad"><b>VSWR &asymp; 9</b><span>Best achievable with any feed-network match (worst case 4&ndash;7 GHz)</span></div>
</div>
<div class="callout red"><b>Root cause.</b> The radiating element is inherently narrow-band. The edge-fed driven patch and the
parasitic patch are nearly the same size and produce a single merged resonance near 5.8 GHz, instead of two separate resonances
spread across the band. Outside about 5.35&ndash;6.26 GHz most of the power is reflected. That is why the gain looks correct
while the VSWR is poor.</div>
<div class="callout"><b>Conclusion.</b> The problem cannot be fixed in the feed network alone. Meeting VSWR &lt; 3 over 4&ndash;7 GHz requires a
redesigned wideband radiating element. Short-term improvements (equal parasitic sizes, per-element transformers, assembly
tolerances) centre and stabilise the present band but will not widen it to 4&ndash;7 GHz.</div>
<div class="callout amber"><b>Status.</b> The element-level analysis is complete. The full-array simulation is still running;
the preliminary array results in section 5.4 agree with the element-level conclusions, and bench measurements of the built panel
(section 5.6) confirm the input-match behaviour. The measurements also show a gain shortfall of about 3 dB mid-band and a
strong gain drop above 6 GHz, which is now part of the investigation. A first wideband redesign iteration
has been completed and has defined the requirements for the next design iteration (section 7).</div>

<h2><span class="num">2</span>Reported issue and scope</h2>
<table>
<tr><th style="width:28%">Item</th><th>Description</th></tr>
<tr><td>Symptom</td><td>Broadside gain as expected; input VSWR above 3:1 over most of 4&ndash;7 GHz on both polarisations</td></tr>
<tr><td>Product</td><td>6&times;6 dual-linear-polarised stacked-patch array, 276.86 &times; 276.86 mm, two coaxial inputs (V-pol and H-pol)</td></tr>
<tr><td>Objective</td><td>Identify the root cause of the poor match, assess whether it can be corrected, and define corrective actions</td></tr>
<tr><td>Inputs received</td><td>Layer files F.Cu (parasitic patches), In2.Cu (driven patches and feed networks), B.Cu (ground) and the stack-up drawing</td></tr>
<tr><td>Out of scope</td><td>Measurement on the physical board, connector and mechanical spacer modelling, production tolerance analysis</td></tr>
</table>

<h2><span class="num">3</span>Design under review</h2>
<p>The array uses 36 identical driven patches (17.07 mm) on a 0.8 mm RT5880 laminate. Each driven patch has a parasitic patch
(16.2&ndash;17.8 mm, graded by row) on 0.4 mm FR4, held 4 mm above it by an air gap. Two independent 36-way corporate networks on
the driven-patch layer feed the top/bottom edges (port 1, V-pol) and the left/right edges (port 2, H-pol) of every patch.</p>
{fig(os.path.join(D, 'fig_layout.png'), next(n), 'Driven-patch layer with the two feed networks highlighted (red: port 1 / V-pol, blue: port 2 / H-pol). Dashed outlines are the parasitic patches.', '56%')}
<table>
<tr><th style="width:28%">Parameter</th><th>Value</th></tr>
<tr><td>Element pitch</td><td>&asymp; 44 mm (0.59 &lambda; at 4 GHz, 1.03 &lambda; at 7 GHz)</td></tr>
<tr><td>Stack-up</td><td>Ground / RT5880 0.8 mm / driven patches + feeds / 4 mm air / FR4 0.4 mm / parasitic patches</td></tr>
<tr><td>Feed lines</td><td>0.73 mm (100 &Omega;), 1.38 mm (70.7 &Omega; quarter-wave transformers), 2.48 mm (50 &Omega;)</td></tr>
<tr><td>Element feed</td><td>Direct edge feed through a short 50 &Omega; stub, no matching section</td></tr>
</table>
{fig(os.path.join(D, 'fig_stackup.png'), next(n), 'Stack-up as built and simulated.', '48%')}

<div class="pb"></div>{header()}
<h2><span class="num">4</span>Investigation process</h2>
<p>The investigation followed a cause-isolation approach: first establish what one element does on its own, then rule out or
confirm the feed network, and finally confirm on the complete array.</p>
{flow()}
<table>
<tr><th style="width:28%">Method</th><th>Details</th></tr>
<tr><td>Solver</td><td>Full-wave FDTD electromagnetic simulation (openEMS), 2.5&ndash;8.5 GHz excitation, absorbing boundaries, near-to-far-field transform for gain</td></tr>
<tr><td>Geometry</td><td>Imported directly from the supplied layer files, no manual redrawing; copper as perfect conductor</td></tr>
<tr><td>Materials</td><td>RT5880 &epsilon;<sub>r</sub> 2.2, tan&delta; 0.0004; FR4 &epsilon;<sub>r</sub> 4.5, tan&delta; 0.02; air gap &epsilon;<sub>r</sub> 1.0</td></tr>
<tr><td>Element model</td><td>One element with both feeds, 0.25 mm mesh, 2.9 M cells</td></tr>
<tr><td>Array model</td><td>Complete board with both networks and ports, 0.5 mm mesh, 12 M cells</td></tr>
<tr><td>Matching study</td><td>Optimised line / transformer / stub networks applied to the simulated element impedance</td></tr>
</table>

<h2><span class="num">5</span>Findings</h2>
<h3>5.1 Element performance as built</h3>
<p>A single element, simulated with its own feed stubs, is matched (VSWR &le; 3) only from about 5.35 to 6.26 GHz, with a
best return loss of 10.8 dB at 5.84 GHz. The element still radiates efficiently (8.7&ndash;9.8 dBi referred to accepted power), but
the realised gain drops at the band edges because of the mismatch.</p>
{fig(os.path.join(R, 'element_S11.png'), next(n), 'Element return loss: as built (bold) and diagnostic variants. Dashed line: VSWR 3:1; dotted: VSWR 2:1; shaded: 4&ndash;7 GHz target band.')}

<h3>5.2 Diagnostic variants</h3>
<table>
<tr><th>Variant</th><th>Result</th><th>What it shows</th></tr>
<tr><td>Parasitic patch removed</td><td>No match anywhere in 4&ndash;7 GHz</td><td>The edge feed is not matched to the patch; the match relies entirely on the parasitic</td></tr>
<tr><td>Parasitic enlarged &times;1.15 / 1.25 / 1.35</td><td>Matched window moves down and becomes narrower (12 %, 4 %, none)</td><td>Resizing tunes <i>where</i> the element works, not <i>how wide</i></td></tr>
<tr><td>Parasitic graded by row (as built)</td><td>Each row matched at a slightly different frequency</td><td>Part of the aperture is always mismatched</td></tr>
</table>

<h3>5.3 Can the feed network correct it?</h3>
<p>The best possible passive match was computed from the simulated element impedance (any series line, quarter-wave transformer
and shunt stub). The worst-case VSWR over 4&ndash;7 GHz improves only from 28.6 to about 9.4. The element's impedance varies too much
across the band to be compensated by a passive network (Bode&ndash;Fano limit). <b>The correction must be made in the radiating element.</b></p>

<div class="pb"></div>{header()}
<h3>5.4 Full array (preliminary)</h3>
<p>The complete board, with both 36-way networks, is being simulated. Because the long feed networks ring for a long time, the
run takes many hours. The preliminary results below are taken from the data recorded so far.</p>
{fig(os.path.join(R, 'array_interim.png'), next(n), 'Preliminary full-array input reflection (S11 V-pol, S22 H-pol) and port-to-port coupling. Sharp dips and ripple are partly due to the run not yet being complete.', '80%')}
<ul>
<li>Both inputs are best in the middle of the band (about 5.0&ndash;6.2 GHz) and mostly at VSWR 3:1 or worse below ~4.8 GHz and above ~6.3 GHz, matching the element result.</li>
<li>The V/H isolation is better than 20 dB over most of the band.</li>
<li>Final array figures will be issued in the next revision of this report.</li>
</ul>

<div class="pb"></div>{header()}
<h3>5.5 Wideband redesign: first iteration</h3>
<p>To define the corrective design, an aperture-coupled stacked patch, the established route to about 50 % bandwidth, was explored
in 40 full-wave simulations, including automatic optimisation. The best candidate so far is matched from 4.95 to 5.75 GHz. It is a
valid design but not yet wider than the present element. The iteration identified clearly what the next design must change:</p>
<ul>
<li>Patches must be printed on thin low-loss laminates over foam rather than suspended in air, so the two resonances can be separated across the band.</li>
<li>A resonant (dog-bone or H-shaped) coupling slot is needed to add a third resonance at the top of the band; H-slots also provide the second polarisation.</li>
<li>The element must be optimised in its array environment (periodic unit cell at the 44 mm pitch).</li>
</ul>
{fig(os.path.join(R, 'wb_S11.png'), next(n), 'First-iteration wideband candidate compared with the present element.', '64%')}

<div class="pb"></div>{header()}
<h3>5.6 Measured results of the built panel</h3>
<p>The client's built panel was measured on the bench: input match of both ports with a calibrated network analyser, and
broadside gain by substitution against a reference horn.</p>
{fig(os.path.join(R, 'measured_vs_sim.png'), next(n), 'Measured panel against simulation. Left: measured input match (markers) over the simulated array curves. Right: measured gain against the aperture limit of the 276.86 mm panel and the 23 dBi rating.', '100%')}
{measured_table()}
<ul>
<li><b>Input match confirms the analysis.</b> Both ports show the same rippled response as the simulated array and are best in the middle
of the band. Port A meets VSWR &le; 3 at all markers except 6.2 GHz; port B is at about VSWR 3 at 4.9&ndash;5.2 GHz.</li>
<li><b>Gain is below the rating.</b> Peak gain is 20.4 dBi (V) and 20.0 dBi (H), about 3 dB under 23 dBi, corresponding to 25&ndash;35 %
aperture efficiency mid-band (a well-designed panel reaches 50&ndash;70 %).</li>
<li><b>Gain collapses at the top of the band:</b> 11&ndash;15 dBi at 6.2&ndash;6.4 GHz (3&ndash;8 % efficiency). Mismatch explains at most
about 1.5 dB of this. The remaining shortfall points to losses or phase errors (feed network, FR4 parasitic layer, radome) and is
being investigated.</li>
</ul>

<h2><span class="num">6</span>Root causes</h2>
<table>
<tr><th style="width:5%">#</th><th style="width:33%">Cause</th><th style="width:30%">Evidence</th><th>Impact</th></tr>
<tr><td>1</td><td>Element bandwidth (~16 %) far below the 54 % target</td><td>Element simulation, impedance locus, matching study</td><td>VSWR &gt; 3 over most of 4&ndash;7 GHz, whatever the feed network</td></tr>
<tr><td>2</td><td>Driven patch edge-fed directly from a 50 &Omega; stub, without a matching section</td><td>No match at all without the parasitic</td><td>Match depends entirely on the parasitic loading</td></tr>
<tr><td>3</td><td>Driven and parasitic resonances merge (similar sizes)</td><td>Single resonance; resizing only shifts the window</td><td>No double-tuned wideband response</td></tr>
<tr><td>4</td><td>Parasitic sizes graded by row (16.2&ndash;17.8 mm)</td><td>Layout; parasitic-size sweep</td><td>Rows matched at different frequencies</td></tr>
<tr><td>5</td><td>Element pitch &asymp; 1.03 &lambda; at 7 GHz</td><td>Layout geometry</td><td>Grating lobes and gain reduction near 7 GHz (affects gain, not VSWR)</td></tr>
<tr><td>6</td><td>Gain shortfall and high-band gain drop (under investigation)</td><td>Bench measurement: 25&ndash;35 % aperture efficiency, 3&ndash;8 % at 6.2&ndash;6.4 GHz</td><td>About 3 dB below the 23 dBi rating mid-band; 6&ndash;9 dB further loss at 6.2&ndash;6.4 GHz</td></tr>
</table>

<h2><span class="num">7</span>Recommendations and next steps</h2>
<h3>7.1 Corrective actions</h3>
<table>
<tr><th style="width:5%">#</th><th style="width:30%">Action</th><th>Expected result</th><th style="width:13%">Type</th></tr>
<tr><td>1</td><td>Redesign the radiating element as a wideband dual-polarised element (aperture-coupled stacked patch on laminate/foam, or L-probe / crossed-dipole alternative)</td><td>Only route to VSWR &lt; 3 (target &lt; 2) over 4&ndash;7 GHz</td><td>Required</td></tr>
<tr><td>2</td><td>Use one parasitic size on all rows unless a taper is intended</td><td>All rows matched at the same frequency</td><td>Quick fix</td></tr>
<tr><td>3</td><td>Add a quarter-wave transformer on each element feed (edge resistance to 100 &Omega;)</td><td>Present band centred and deeper; not wider</td><td>Quick fix</td></tr>
<tr><td>4</td><td>Control the 4 mm air-gap spacer tolerance (&plusmn;0.1 mm)</td><td>Stable, repeatable match between boards</td><td>Production</td></tr>
<tr><td>5</td><td>Reduce the pitch to &le; 30 mm if the full band must be free of grating lobes</td><td>Clean patterns up to 7 GHz (needs the smaller wideband element)</td><td>Design</td></tr>
</table>
<h3>7.2 Plan for the next phase</h3>
<table>
<tr><th style="width:5%">Phase</th><th style="width:30%">Activity</th><th>Deliverable</th></tr>
<tr><td>1</td><td>Complete the full-array simulation of the present design and compare its gain with the measurement</td><td>Final array S-parameters and gain; cause of the gain shortfall; report revision B</td></tr>
<tr><td>1b</td><td>Bench checks: gain and S11 with and without radome, without the parasitic layer, and pattern cuts at 5.5 and 6.4 GHz</td><td>Separates radome, parasitic-layer and feed-phase effects</td></tr>
<tr><td>2</td><td>Wideband element, iteration 2: unit-cell model, laminate/foam stack, resonant H-slots, dual polarisation, systematic optimisation</td><td>Element meeting VSWR &lt; 3 (target &lt; 2) over 4&ndash;7 GHz, with isolation and pattern data</td></tr>
<tr><td>3</td><td>Array integration: feed network redesign for the new element, full-array verification</td><td>Array layout files and simulated performance</td></tr>
<tr><td>4</td><td>Prototype and measurement: element test coupon, network with resistive loads, full array</td><td>Measured S-parameters and patterns; correlation with simulation</td></tr>
</table>
<div class="callout"><b>Recommended immediate bench check:</b> measure one element on a test coupon and the bare feed network loaded with
100 &Omega; resistors. This separates element and network on the bench and confirms the findings of this report on hardware.</div>

<h2><span class="num">8</span>Assumptions and limitations</h2>
<ul>
<li>Bench measurements were made by the client team on a bench range (~5 m), not in an anechoic chamber; gain values carry an estimated &plusmn;1&ndash;2 dB uncertainty.
The port A/B to V/H mapping and the radome condition during the gain test are to be confirmed.</li>
<li>The air gap is modelled as 4.0 mm of air (&epsilon;<sub>r</sub> 1.0), as built.</li>
<li>Copper thickness, solder mask, connectors and the mechanical spacers are not modelled.</li>
<li>The array mesh (0.5 mm) approximates the 0.73 mm lines, which can shift network resonances by a few percent.</li>
<li>Full-array results in this revision are preliminary (simulation still running).</li>
</ul>
"""


LOGO = b64(os.path.join(D, 'telmart_logo.jpg'))
if __name__ == '__main__':
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>C-band array VSWR report</title><style>{CSS}</style></head><body>{body()}</body></html>'
    open(OUT_HTML, 'w', encoding='utf-8').write(html)
    subprocess.run(['node', os.path.join(HERE, 'html2pdf.js'), OUT_HTML, OUT_PDF,
                    f'Telmart &middot; {DOC_REF} Rev. {REV} &middot; Confidential'], check=True)
    print('wrote', OUT_PDF)
