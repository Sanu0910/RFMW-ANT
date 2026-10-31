"""Results-only client report (Telmart branding): 04_docs/Telmart_CBand_Array_Results_Status.pdf

For sharing with the client without disclosing how the work is done: no solver/tool names, models, diagnostic
method, optimisation or redesign concept. Shows the client's own design, the measured-style results (re-plotted
with neutral labels), the conclusions and the project status.

    python client_results_report.py      (needs node + Playwright Chromium; reuses client_report.py styling)
"""
import os, re, subprocess, datetime
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import client_report as C

HERE = C.HERE; R = C.R; D = C.D
OUT_HTML = os.path.join(D, 'Telmart_CBand_Array_Results_Status.html')
OUT_PDF = os.path.join(D, 'Telmart_CBand_Array_Results_Status.pdf')
DOC_REF, REV = 'TM-RF-15-002', 'A'
BLUE, RED, GREEN = C.BLUE, C.RED, '#2e8b57'


def load(tag):
    p = os.path.join(R, f'{tag}_S.csv')
    return np.loadtxt(p, delimiter=',') if os.path.exists(p) else None


def vswr_lines(ax, xmax=7.5):
    for v, ls in ((3, '--'), (2, ':')):
        g = (v - 1) / (v + 1); ax.axhline(20 * np.log10(g), color='k', ls=ls, lw=0.8)
        ax.text(xmax - 0.05, 20 * np.log10(g) + 0.4, f'VSWR {v}:1', ha='right', fontsize=8)
    ax.axvspan(4, 7, color=GREEN, alpha=0.07)
    ax.text(5.5, -1.2, 'target band 4-7 GHz', ha='center', fontsize=8, color=GREEN)


def figures():
    out = {}
    # 1. element return loss (present design only)
    d = load('element_air')
    if d is not None:
        fig, ax = plt.subplots(figsize=(8.5, 4.3))
        ax.plot(d[:, 0], d[:, 1], color=BLUE, lw=2.2, label='Present design, single element')
        vswr_lines(ax); ax.set(xlabel='Frequency (GHz)', ylabel='Return loss |S11| (dB)', xlim=(3.5, 7.5), ylim=(-25, 0),
                               title='Element input match - present design')
        ax.grid(alpha=0.3); ax.legend(fontsize=8.5, loc='lower left')
        fig.tight_layout(); out['elem'] = os.path.join(D, 'res_element.png'); fig.savefig(out['elem'], dpi=140); plt.close(fig)
    # 2. full array (preliminary)
    d = load('array_interim')
    if d is not None:
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        ax.plot(d[:, 0], d[:, 1], color=BLUE, lw=1.5, label='Input 1 (V-pol)')
        if d.shape[1] > 3:
            ax.plot(d[:, 0], d[:, 3], color=RED, lw=1.5, label='Input 2 (H-pol)')
        ax.plot(d[:, 0], d[:, 2], color='0.45', lw=1.0, ls='--', label='Isolation between inputs')
        vswr_lines(ax); ax.set(xlabel='Frequency (GHz)', ylabel='dB', xlim=(3.5, 7.5), ylim=(-40, 0),
                               title='Complete 6x6 array - input match and isolation (preliminary)')
        ax.grid(alpha=0.3); ax.legend(fontsize=8.5, loc='lower left')
        fig.tight_layout(); out['array'] = os.path.join(D, 'res_array.png'); fig.savefig(out['array'], dpi=140); plt.close(fig)
    # 3. development progress: present design vs development iteration 1
    a, b = load('element_air'), load('wbN4')
    if a is not None and b is not None:
        fig, ax = plt.subplots(figsize=(8.5, 4.3))
        ax.plot(a[:, 0], a[:, 1], color='0.5', lw=1.8, label='Present design')
        ax.plot(b[:, 0], b[:, 1], color=BLUE, lw=2.0, label='Development iteration 1')
        vswr_lines(ax); ax.set(xlabel='Frequency (GHz)', ylabel='Return loss |S11| (dB)', xlim=(3.5, 7.5), ylim=(-25, 0),
                               title='Element development - iteration 1 vs present design')
        ax.grid(alpha=0.3); ax.legend(fontsize=8.5, loc='lower left')
        fig.tight_layout(); out['dev'] = os.path.join(D, 'res_development.png'); fig.savefig(out['dev'], dpi=140); plt.close(fig)
    return out


def band(tag, lim=3.0):
    d = load(tag)
    f, g = d[:, 0], 10 ** (d[:, 1] / 20); v = (1 + g) / (1 - g)
    ok = f[(v <= lim)]
    runs, cur = [], [ok[0]]
    for x, y in zip(ok[:-1], ok[1:]):
        if y - x > 0.011:
            runs.append(cur); cur = [y]
        else:
            cur.append(y)
    runs.append(cur); r = max(runs, key=len)
    return r[0], r[-1], (r[-1] - r[0]) / ((r[-1] + r[0]) / 2) * 100


def element_rows():
    p = os.path.join(R, 'element_air_summary.txt'); rows, gains = [], []
    for ln in open(p):
        m = re.match(r'\s*([\d.]+) GHz\s+S11\s+([-\d.]+) dB\s+VSWR\s+([\d.]+)', ln)
        if m:
            rows.append(f'<tr><td>{float(m.group(1)):.1f}</td><td>{m.group(2)}</td><td>{float(m.group(3)):.1f}</td></tr>')
        m = re.match(r'\s*([\d.]+) GHz\s+broadside G\(accepted\)\s+([-\d.]+) dBi\s+realised G\s+([-\d.]+) dBi', ln)
        if m:
            gains.append(f'<tr><td>{m.group(1)}</td><td>{m.group(2)}</td><td>{m.group(3)}</td></tr>')
    return ''.join(rows), ''.join(gains)


def body(F):
    date = datetime.date.today().strftime('%d %B %Y')
    hdr = (f'<div class="hdr"><img src="{C.LOGO}"><span>{DOC_REF} Rev. {REV} &middot; C-band 6&times;6 array &middot; '
           f'Results and project status</span></div>')
    n = iter(range(1, 20))
    e0, e1, ep = band('element_air'); w0, w1, wp = band('wbN4')
    srows, grows = element_rows()
    fig = lambda key, cap, width='90%': C.fig(F[key], next(n), cap, width) if key in F else ''
    return f"""
<div class="cover">
  <img class="logo" src="{C.LOGO}">
  <div class="band"></div>
  <h1>C-Band 6&times;6 Dual-Polarised Antenna Array</h1>
  <div class="subtitle">Results summary and project status</div>
  <table class="meta">
    <tr><td>Document</td><td>{DOC_REF}, Revision {REV}</td></tr>
    <tr><td>Date</td><td>{date}</td></tr>
    <tr><td>Report type</td><td>Results and status report</td></tr>
    <tr><td>Frequency band</td><td>4.0&ndash;7.0 GHz (C-band)</td></tr>
    <tr><td>Prepared by</td><td>Telmart RF &amp; Microwave Engineering</td></tr>
    <tr><td>Status</td><td><span class="status">In progress: full-array verification and element development</span></td></tr>
  </table>
  <div class="conf">Confidential. This document presents results only. Methods, analysis models and design concepts are
  proprietary to Telmart and are not disclosed. Not to be reproduced or passed to third parties without the written consent of Telmart.</div>
</div>

{hdr}
<h2><span class="num">1</span>Summary of results</h2>
<div class="kpi">
  <div class="bad"><b>{e0:.2f}&ndash;{e1:.2f} GHz</b><span>Present element matched (VSWR &le; 3): {ep:.0f} % bandwidth</span></div>
  <div><b>54 %</b><span>Bandwidth required for 4&ndash;7 GHz</span></div>
  <div><b>8.7&ndash;9.8 dBi</b><span>Element gain (accepted power), 5&ndash;6.5 GHz</span></div>
  <div><b>&gt; 20 dB</b><span>Isolation between V and H inputs over most of the band (array)</span></div>
</div>
<div class="callout red"><b>Main result.</b> The poor input match reported on the array is caused by the radiating element
itself, whose matched bandwidth is about {ep:.0f} %, well below the 54 % needed for 4&ndash;7 GHz. The radiator works correctly
inside its band, which is why the gain is as expected while the VSWR is poor.</div>
<div class="callout"><b>Consequence.</b> A change to the feed network alone cannot bring the VSWR below 3:1 across 4&ndash;7 GHz.
A new wideband radiating element is required; its development has started (section 5).</div>
<div class="callout amber"><b>Measured panel.</b> Bench measurements confirm the input-match behaviour and show a gain of 20.4 dBi peak,
about 3 dB below the 23 dBi rating, with a strong drop above 6 GHz (section 6).</div>

<h2><span class="num">2</span>Design reviewed</h2>
<table>
<tr><th style="width:30%">Item</th><th>Value</th></tr>
<tr><td>Array</td><td>6 &times; 6 dual-linear-polarised stacked patches, 276.86 &times; 276.86 mm, pitch &asymp; 44 mm</td></tr>
<tr><td>Inputs</td><td>Input 1: V-polarisation; Input 2: H-polarisation (one 36-way feed network each)</td></tr>
<tr><td>Stack-up</td><td>Ground / RT5880 0.8 mm / driven patches and feeds / 4 mm air / FR4 0.4 mm / parasitic patches</td></tr>
<tr><td>Reported symptom</td><td>Gain as expected; VSWR above 3:1 over most of 4&ndash;7 GHz</td></tr>
</table>
{C.fig(os.path.join(D, 'fig_layout.png'), next(n), 'Array layout reviewed (client design). Red: input 1 feed network; blue: input 2 feed network.', '40%')}

<div class="pb"></div>{hdr}
<h2><span class="num">3</span>Element results (present design)</h2>
{fig('elem', 'Input match of one element of the present design. Dashed line: VSWR 3:1; dotted: VSWR 2:1; shaded: 4&ndash;7 GHz target band.')}
<table>
<tr><th>Frequency (GHz)</th><th>Return loss |S11| (dB)</th><th>VSWR</th></tr>
{srows}
</table>
<table>
<tr><th>Frequency (GHz)</th><th>Gain, accepted power (dBi)</th><th>Realised gain incl. mismatch (dBi)</th></tr>
{grows}
</table>
<p>The element is matched only between {e0:.2f} and {e1:.2f} GHz. Outside this window the realised gain falls because of the
mismatch, while the gain referred to accepted power stays at 8.7&ndash;9.8 dBi.</p>

<div class="pb"></div>{hdr}
<h2><span class="num">4</span>Complete array results (preliminary)</h2>
{fig('array', 'Complete 6&times;6 array: input match of both inputs and isolation between them. Preliminary: final values follow in the next revision.', '78%')}
<ul>
<li>Both inputs are best in the middle of the band (about 5.0&ndash;6.2 GHz).</li>
<li>Below about 4.8 GHz and above about 6.3 GHz both inputs are mostly at VSWR 3:1 or worse, consistent with the element result.</li>
<li>Isolation between the V and H inputs is better than 20 dB over most of the band.</li>
<li>The array result confirms that the element bandwidth is the limiting factor.</li>
</ul>

<h2><span class="num">5</span>Element development (in progress)</h2>
<p>A new wideband element is being developed to meet VSWR &lt; 3 (target &lt; 2) over the full 4&ndash;7 GHz band on both polarisations.
Iteration 1 has been completed; it is matched from {w0:.2f} to {w1:.2f} GHz and has defined the design direction for iteration 2.</p>
{fig('dev', 'Element development: iteration 1 compared with the present design.', '66%')}

<div class="pb"></div>{hdr}
<h2><span class="num">6</span>Measured results of the built panel</h2>
{C.fig(os.path.join(R, 'measured_vs_sim.png'), next(n), 'Built panel: measured input match (markers) against the predicted array response (left), and measured gain against the aperture limit and the 23 dBi rating (right).', '100%')}
{C.measured_table()}
<ul>
<li>The measured input match agrees with the predicted array response: best in the middle of the band, poorer at the band edges.</li>
<li>Measured peak gain is 20.4 dBi (V) and 20.0 dBi (H), about 3 dB below the 23 dBi rating.</li>
<li>Gain drops to 11&ndash;15 dBi at 6.2&ndash;6.4 GHz. The input mismatch accounts for at most about 1.5 dB of this; the cause of the
remaining drop is under investigation.</li>
</ul>

<div class="pb"></div>{hdr}
<h2><span class="num">7</span>Project status</h2>
<table>
<tr><th style="width:5%">#</th><th style="width:38%">Work package</th><th style="width:17%">Status</th><th>Result / next output</th></tr>
<tr><td>1</td><td>Design data review (layout and stack-up)</td><td>&#9679; Completed</td><td>Design decoded, both feed networks traced</td></tr>
<tr><td>2</td><td>Element performance analysis, present design</td><td>&#9679; Completed</td><td>Root cause identified: element bandwidth ~{ep:.0f} %</td></tr>
<tr><td>3</td><td>Feed-network correction assessment</td><td>&#9679; Completed</td><td>Feed-network change alone is not sufficient</td></tr>
<tr><td>3b</td><td>Bench measurement of the built panel (input match, gain)</td><td>&#9679; Completed</td><td>Input match confirmed; gain shortfall identified (section 6)</td></tr>
<tr><td>3c</td><td>Gain shortfall investigation</td><td>&#9680; In progress</td><td>Cause of the ~3 dB shortfall and the high-band drop</td></tr>
<tr><td>4</td><td>Complete-array verification, present design</td><td>&#9680; In progress</td><td>Preliminary results issued (section 4); final values in Rev. B</td></tr>
<tr><td>5</td><td>Wideband element development</td><td>&#9680; In progress</td><td>Iteration 1 completed; iteration 2 is the next step</td></tr>
<tr><td>6</td><td>Array integration of the new element</td><td>&#9675; Planned</td><td>Updated array layout and simulated performance</td></tr>
<tr><td>7</td><td>Prototype and measurement</td><td>&#9675; Planned</td><td>Measured input match, isolation and patterns</td></tr>
</table>
<p class="small">&#9679; completed &nbsp; &#9680; in progress &nbsp; &#9675; planned</p>

<h2><span class="num">8</span>Actions requested from the client</h2>
<ul>
<li>Confirm the required specification: VSWR limit (3:1 or 2:1), band edges, gain and isolation targets.</li>
<li>Confirm any mechanical constraints for the new element (total height, materials, array size and pitch).</li>
<li>Confirm which panel port is V and which is H, and whether the gain was measured with the radome fitted.</li>
<li>If possible, repeat the gain measurement with and without the radome, and provide pattern cuts at 5.5 and 6.4 GHz.</li>
</ul>
"""


if __name__ == '__main__':
    F = figures()
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>C-band array results and status</title>'
            f'<style>{C.CSS}</style></head><body>{body(F)}</body></html>')
    open(OUT_HTML, 'w', encoding='utf-8').write(html)
    subprocess.run(['node', os.path.join(HERE, 'html2pdf.js'), OUT_HTML, OUT_PDF,
                    f'Telmart &middot; {DOC_REF} Rev. {REV} &middot; Confidential'], check=True)
    print('wrote', OUT_PDF)
