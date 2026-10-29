"""Narrative of the PDF report (numbers in tables are filled in from 03_results by build_report.py)."""

VARIANTS = [
    ('element_air', 'A. As built: air gap, parasitic 16.2 mm (row 1)'),
    ('element_nopar', 'B. Driven patch only (parasitic + FR4 removed)'),
    ('element_par1.15', 'C. Parasitic scaled x1.15 (18.6 mm)'),
    ('element_par1.25', 'D. Parasitic scaled x1.25 (20.3 mm)'),
    ('element_par1.35', 'E. Parasitic scaled x1.35 (21.9 mm)'),
]

ARRAY_PENDING = """
<div class="box note"><b>Full-array run still in progress.</b> The complete 276.86 mm board (12 M FDTD cells, both
36-way networks, 72 feed points) decays slowly because of the long corporate feed lines. Its S11/S22/S21 will be
added to this report in a later revision. The element-level results below already explain the measured behaviour:
the array input match cannot be better than the match of the elements it is feeding through a reciprocal, near-lossless
corporate network built from 100 &Omega; branches and 70.7 &Omega; quarter-wave transformers.</div>
"""

ARRAY_TEXT = """
<p>The array result follows the element result: wherever the element is mismatched, the quarter-wave-transformer
corporate network passes the reflection straight back to the connector (in-phase reflections from 36 identical elements
add up at the input). Ripple on top of the element curve comes from the network's transformers and the unequal
line lengths.</p>
"""

BODY = r"""
<h1>C-band 6&times;6 Dual-Polarised Stacked-Patch Array</h1>
<div class="sub">S11 / VSWR root-cause analysis with openEMS (FDTD) &middot; project <code>15_cband-6x6-dualpol-stacked-patch_match-debug</code> &middot; {date}<br>
Inputs: <code>F_CU.dxf</code>, <code>IN2_CU.dxf</code>, <code>GND.dxf</code>, <code>C_Band_Stackup.pdf</code> &middot; Target band 4&ndash;7 GHz</div>

<h2>1. Summary</h2>
<div class="box"><b>Problem reported:</b> broadside gain is as expected, but the input match is poor; VSWR never gets below 3:1 over 4&ndash;7 GHz.</div>
<div class="box good"><b>Answer, in short:</b>
<ol>
<li><b>The radiating element itself is narrow-band.</b> One element cut out of the board, with its own feed stubs, is
matched (VSWR &le; 3) only from about 5.35 to 6.26 GHz, which is ~16 % bandwidth. The 4&ndash;7 GHz target is 54 %.
Outside that window most of the power is reflected, so the <i>realised</i> gain drops even though the element still
radiates well (its gain referred to accepted power is 8.7&ndash;9.8 dBi).
That is exactly "gain is OK but VSWR is bad".</li>
<li><b>The driven patches are edge-fed with no matching.</b> Each feed joins the radiating edge through a 2.48 mm
(50 &Omega;) stub that is only a few mm long. A radiating edge has a resistance of a few hundred ohms. Without the parasitic
patch the element is not matched anywhere in 4&ndash;7 GHz (worst-case VSWR above 8 everywhere). The parasitic patch is the only
reason there is a usable window around 5.8 GHz.</li>
<li><b>The driven and parasitic resonances merge into one.</b> The parasitics (16.2&ndash;17.8 mm) are about the same size as
the driven patches (17.07 mm). The simulation shows a single resonance loop, and the matched window simply follows the parasitic size:
16.2 mm gives a window around 5.8 GHz, 18.6 mm moves it down to about 5.0&ndash;5.5 GHz, and the window stays narrow in both cases.
A broadband stacked patch needs two <i>separate</i>, properly coupled resonances inside the band. This geometry does not have them.
Because the parasitics are graded row by row (16.2 to 17.8 mm), each row is matched at a slightly different frequency, so at any one
frequency part of the aperture is mismatched.</li>
<li><b>No feed-network change can fix this on its own.</b> A best-case circuit optimisation on the simulated element impedance
(line + transformer + stub) still leaves a worst-case VSWR of about 9 across 4&ndash;7 GHz (section 5).</li>

</ol></div>

<h2>2. The design under test</h2>
{fig_layout}
<table>
<tr><th>Item</th><th>Value (from the DXFs)</th></tr>
<tr><td>Board / ground</td><td>276.86 &times; 276.86 mm, solid ground on B.Cu</td></tr>
<tr><td>Array</td><td>6 &times; 6, pitch &asymp; 44&ndash;45 mm (0.59 &lambda; at 4 GHz, 1.03 &lambda; at 7 GHz)</td></tr>
<tr><td>Driven patches (In2.Cu)</td><td>17.07 &times; 17.07 mm, all 36 the same, on RT5880 0.8 mm</td></tr>
<tr><td>Parasitic patches (F.Cu)</td><td>16.2 / 16.5 / 16.9 / 17.2 / 17.5 / 17.8 mm by row (graded top to bottom), on FR4 0.4 mm, 4.4 mm above the driven layer</td></tr>
<tr><td>Polarisation</td><td>Dual linear. Port 1 feeds the top/bottom edge of every patch (V-pol); port 2 feeds the left/right edge (H-pol).</td></tr>
<tr><td>Feed network</td><td>Two 36-way corporate networks on In2.Cu. Trace widths: 0.73 mm (&asymp;100 &Omega;), 1.38 mm (&asymp;70.7 &Omega;, &lambda;/4 transformers), 2.48 mm (&asymp;50 &Omega;). Half the patches are fed from the opposite edge, with meander lines for the 180&deg; correction.</td></tr>
<tr><td>Ports</td><td>Open ends of the two 2.48 mm launch lines at (&minus;77.6, &minus;2.1) and (&minus;1.5, &minus;2.1) mm. Modelled as 50 &Omega; coax-like vertical ports.</td></tr>
</table>
{fig_stack}
{fig_elem}

<h2 class="pb">3. How it was simulated</h2>
<ul>
<li><b>Solver:</b> openEMS v0.37 (FDTD), Gaussian excitation 2.5&ndash;8.5 GHz, 8-cell PML on all sides, near-field to far-field box for broadside gain.</li>
<li><b>Geometry</b> read directly from the DXFs (<code>cbgeom.py</code>). Copper is modelled as zero-thickness PEC. RT5880: &epsilon;<sub>r</sub> 2.2, tan&delta; 0.0004. FR4: &epsilon;<sub>r</sub> 4.5, tan&delta; 0.02. The gap is air.</li>
<li><b>Element model</b> (<code>sim_element.py</code>): the row-1/col-1 element is clipped out of In2.Cu with both edge feeds, up to where each becomes a 0.73 mm
(100 &Omega;) branch. Each branch ends in a 100 &Omega; lumped port. |S11| there is the reflection the element sends into its own branch of the network,
and it does not depend on where along the lossless line the cut is made. It sits on a 60 &times; 60 mm ground with 0.25 mm in-plane cells (2.9 M cells).</li>
<li><b>Full array</b> (<code>sim_array.py</code>): the whole board with both ports, 0.5 mm in-plane cells (12 M cells).</li>
<li><b>Matching study</b> (<code>match_study.py</code>): circuit optimisation on the simulated element impedance.</li>
</ul>

<h2>4. Element results (as built)</h2>
{elem_table}
{fig_s11}
{fig_smith}
<p>On the Smith chart the element traces one large, high-Q resonance loop (Fig. 5). It passes through the VSWR 3 circle only between about
5.35 and 6.26 GHz, with a small kink near 5.8 GHz. That kink is the parasitic patch coupling weakly. A well-designed stacked patch shows a
tight loop that stays <i>around the centre</i> of the chart across the band. This one does not.</p>

<h3>Diagnostic variants</h3>
{variant_table}
<ul>
<li><b>B (no parasitic):</b> the bare edge-fed patch is badly mismatched at every frequency. The edge feed was never transformed to the line impedance.</li>

<li><b>C&ndash;E (larger parasitic):</b> the matched window moves down in frequency as the parasitic grows, and it gets narrower
(16 % at 16.2 mm, 12 % at 18.6 mm, 4 % at 20.3 mm, none at 21.9 mm).
Resizing the parasitic tunes <i>where</i> the element works. It does not make it work over 4&ndash;7 GHz.</li>
</ul>

<h2 class="pb">5. Can the feed network alone fix it?</h2>
<p>The simulated element impedance was taken from 4 to 7 GHz, and the best possible match was searched for with ideal lossless lines on RT5880
(any impedance 40&ndash;150 &Omega;, any length 0&ndash;25 mm):</p>
{match}
<p><b>No.</b> Even a series line plus a transformer plus a shunt stub leaves a worst-case VSWR of about 9. The element's own reactance swing across 4&ndash;7 GHz
is too large to compensate with a passive network (Bode&ndash;Fano limit). The fix has to be made in the radiator.</p>

<h2>6. Full array</h2>
{array}

<h2 class="pb">7. Root causes, ranked</h2>
<table>
<tr><th>#</th><th>Cause</th><th>Evidence</th><th>Effect</th></tr>
<tr><td>1</td><td>Element bandwidth (~16 %) far below the 54 % target</td><td>Element S11, Smith chart, matching study</td><td>VSWR &gt; 3 over ~70 % of 4&ndash;7 GHz, regardless of the network</td></tr>
<tr><td>2</td><td>Driven patch edge-fed straight from a 50 &Omega; stub, with no inset and no transformer</td><td>Variant B: no match anywhere without the parasitic</td><td>The match depends entirely on the parasitic loading</td></tr>
<tr><td>3</td><td>Driven and parasitic resonances merge (similar sizes, edge feed); the window position is set by the parasitic size</td><td>Single loop with only a small kink; variants C&ndash;E move the window without widening it</td><td>No wideband double-tuned response. Rows with different parasitic sizes are matched at different frequencies.</td></tr>

<tr><td>4</td><td>Element pitch &asymp; 44 mm = 1.03 &lambda; at 7 GHz</td><td>Geometry</td><td>Grating lobes and gain drop near the top of the band. This affects gain, not S11.</td></tr>
</table>

<h2>8. What to change</h2>
<ol>
<li><b>Hold the 4 mm air gap tightly.</b> Check the spacer height on the built board: a 0.3 mm error in a 4 mm gap moves the
driven-parasitic coupling noticeably.</li>
<li><b>Re-tune the element as a true double-resonance stacked patch</b> in a unit-cell (periodic) simulation before touching the network:
<ul><li>Separate the two resonances: one near 4.5 GHz and one near 6.5 GHz. That needs the driven patch, the parasitic and the gap (3&ndash;6 mm)
to be tuned together. Scaling one patch alone only moves a single narrow window (variants C&ndash;E).</li>
<li>Use the same parasitic size on every row unless a row-by-row taper is deliberately part of the design. The present 16.2&ndash;17.8 mm
grading detunes the rows from one another.</li>
<li>Aim for a tight loop around the chart centre over 4&ndash;7 GHz, then use one quarter-wave transformer per element to bring it to 100 &Omega;.</li></ul></li>
<li><b>Change the feed type if 4&ndash;7 GHz at VSWR &lt; 2 is required.</b> 54 % bandwidth is very hard for a direct edge-fed stacked patch.
Proven routes for this bandwidth are:
<ul><li>aperture-coupled stacked patch (H-shaped or cross slots for dual polarisation), with the feed on a separate layer below the ground;</li>
<li>L-probe or meandered-probe feed into a thick air/foam patch;</li>
<li>a probe-fed stacked patch with capacitive-disc compensation.</li></ul>
All of these also improve V/H isolation; the edge feeds here couple at only about &minus;7 dB at 7 GHz.</li>
<li><b>If you keep the edge feed:</b> add an inset or a &lambda;/4 transformer from the edge resistance (100&ndash;300 &Omega;) to 100 &Omega; on each feed.
That centres the existing narrow band on one frequency. It will not widen it to 4&ndash;7 GHz.</li>
<li><b>Reduce the pitch</b> to &le; 0.7 &lambda; at 7 GHz (&asymp; 30 mm) if the upper band must be free of grating lobes. This needs the smaller
element that a wideband feed allows.</li>
<li><b>Measurement check:</b> measure S11 of one element on a test coupon and the bare network loaded with 100 &Omega; resistors. That separates
element and network on the bench and confirms this analysis.</li>
</ol>

<h2>9. Limits of this analysis</h2>
<ul>
<li>The element was simulated alone on a 60 mm ground. Mutual coupling in the array shifts the embedded impedance a little. The full-array model includes it.</li>
<li>The full-array mesh (0.5 mm) snaps the 0.73 mm lines to 0.5 or 1.0 mm, which shifts the network's own resonances by a few percent.</li>
<li>Copper thickness, solder mask, connector transitions and the spacers holding the 4 mm gap are not modelled.</li>
<li>No measured data was available. The comparison is with the reported symptom (VSWR &gt; 3, gain OK).</li>
</ul>

<h2>10. Reproduce</h2>
<pre>bash tools/install_openems.sh
/opt/openEMS/venv/bin/pip install ezdxf shapely matplotlib
cd projects/15_cband-6x6-dualpol-stacked-patch_match-debug/02_openems
source /opt/openEMS/venv/bin/activate
python sim_element.py --tag element_air                 # as built (~5 min, 4 cores)
python sim_element.py --tag element_nopar --no-par
python sim_element.py --tag element_par1.25 --par-scale 1.25
python match_study.py
python sim_array.py --port 1 ; python sim_array.py --port 2   # full board, hours
python make_figures.py ; python plot_results.py ; python build_report.py</pre>
"""
