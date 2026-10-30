"""Assemble 04_docs/CBand_6x6_Array_S11_Analysis_Report.pdf from the results and figures.

    python3 plot_results.py && python3 build_report.py      (needs node + Playwright Chromium)
Narrative lives in report_text.py; numbers are read from 03_results so a re-run updates them.
"""
import os, re, base64, subprocess, datetime, html as htmllib
import numpy as np
import report_text as T

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, '..', '03_results')
D = os.path.join(HERE, '..', '04_docs')
OUT_HTML = os.path.join(D, 'CBand_6x6_Array_S11_Analysis_Report.html')
OUT_PDF = os.path.join(D, 'CBand_6x6_Array_S11_Analysis_Report.pdf')


def img(path, width='100%', cap=''):
    if not os.path.exists(path):
        return f'<p class="missing">[figure not available: {os.path.basename(path)}]</p>'
    b = base64.b64encode(open(path, 'rb').read()).decode()
    return f'<figure><img src="data:image/png;base64,{b}" style="width:{width}"><figcaption>{cap}</figcaption></figure>'


def csv(tag):
    p = os.path.join(R, f'{tag}_S.csv')
    return np.loadtxt(p, delimiter=',') if os.path.exists(p) else None


def band_stats(d, col=1):
    f, s = d[:, 0], d[:, col]
    m = (f >= 4) & (f <= 7)
    g = 10 ** (s / 20)
    v = (1 + g) / (1 - g)
    i = np.argmin(s)
    def span(lim):
        ok = (v <= lim)
        if not ok.any():
            return '-'
        fs = f[ok]
        # report the contiguous run containing the best point
        runs, cur = [], [fs[0]]
        for a, b in zip(fs[:-1], fs[1:]):
            if b - a > 0.011:
                runs.append(cur); cur = [b]
            else:
                cur.append(b)
        runs.append(cur)
        r = max(runs, key=len)
        return f'{r[0]:.2f}-{r[-1]:.2f} GHz ({(r[-1]-r[0])/((r[-1]+r[0])/2)*100:.0f} %)'
    in3 = (v[m] <= 3).mean() * 100
    return dict(best=f'{s[i]:.1f} dB @ {f[i]:.2f} GHz', bw3=span(3), bw2=span(2.0),
                cover3=f'{in3:.0f} %', worst=f'{v[m].max():.1f}')


def gains(tag):
    p = os.path.join(R, f'{tag}_summary.txt')
    if not os.path.exists(p):
        return {}
    out = {}
    for ln in open(p):
        m = re.search(r'([\d.]+) GHz\s+broadside.*?([-\d.]+) dBi.*?([-\d.]+) dBi', ln)
        if m:
            out[float(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    return out


def variant_table():
    rows = []
    for tag, name in T.VARIANTS:
        d = csv(tag)
        if d is None:
            rows.append(f'<tr><td>{name}</td><td colspan=5 class="missing">not run</td></tr>'); continue
        s = band_stats(d)
        rows.append(f'<tr><td>{name}</td><td>{s["best"]}</td><td>{s["bw3"]}</td><td>{s["bw2"]}</td>'
                    f'<td>{s["cover3"]}</td><td>{s["worst"]}</td></tr>')
    return ('<table><tr><th>Element model</th><th>Best S11</th><th>VSWR&le;3 band</th><th>VSWR&le;2 band</th>'
            '<th>4-7 GHz with VSWR&le;3</th><th>Worst VSWR 4-7 GHz</th></tr>' + ''.join(rows) + '</table>')


def element_table(tag):
    p = os.path.join(R, f'{tag}_summary.txt')
    if not os.path.exists(p):
        return ''
    rows = []
    for ln in open(p):
        m = re.match(r'\s*([\d.]+) GHz\s+S11\s+([-\d.]+) dB\s+VSWR\s+([\d.]+)\s+S21\s+([-\d.]+) dB\s+Zin\s+([-\d.]+)\s*([+-][\d.]+)j', ln)
        if m:
            rows.append('<tr>' + ''.join(f'<td>{x}</td>' for x in
                        (m.group(1), m.group(2), m.group(3), m.group(4), f'{m.group(5)} {m.group(6)}j')) + '</tr>')
    g = gains(tag)
    grow = ''.join(f'<tr><td>{f:.1f}</td><td>{a:.2f}</td><td>{b:.2f}</td><td>{a-b:.2f}</td></tr>' for f, (a, b) in sorted(g.items()))
    return ('<table><tr><th>f (GHz)</th><th>S11 (dB)</th><th>VSWR</th><th>V-H coupling S21 (dB)</th><th>Z<sub>in</sub> (&Omega;)</th></tr>'
            + ''.join(rows) + '</table>'
            '<table><tr><th>f (GHz)</th><th>Broadside gain, accepted power (dBi)</th><th>Realised gain (dBi)</th><th>Mismatch loss (dB)</th></tr>'
            + grow + '</table>')


def array_section():
    d1, d2 = csv('array_p1'), csv('array_p2')
    if d1 is None and d2 is None:
        pre = os.path.join(R, 'array_interim.png')
        return T.ARRAY_PENDING + (img(pre, '92%', 'Fig. 6 - PRELIMINARY full-array S-parameters from the runs still in progress (truncated time signals: '
                                     'the sharp dips and the ripple are partly truncation artefacts, and late reflections are not yet included).')
                                 + T.ARRAY_INTERIM if os.path.exists(pre) else '')
    html = img(os.path.join(R, 'array_S.png'), '92%', 'Full 6x6 array as drawn: port reflections and port-to-port coupling (50 &Omega;).')
    rows = []
    for d, name in ((d1, 'Port 1 (V-pol) S11'), (d2, 'Port 2 (H-pol) S22')):
        if d is None:
            continue
        s = band_stats(d)
        rows.append(f'<tr><td>{name}</td><td>{s["best"]}</td><td>{s["bw3"]}</td><td>{s["cover3"]}</td><td>{s["worst"]}</td></tr>')
    html += ('<table><tr><th>Array port</th><th>Best</th><th>VSWR&le;3 band</th><th>4-7 GHz with VSWR&le;3</th><th>Worst VSWR</th></tr>'
             + ''.join(rows) + '</table>')
    for tag in ('array_p1', 'array_p2'):
        p = os.path.join(R, f'{tag}_summary.txt')
        if os.path.exists(p):
            html += f'<pre>{open(p).read()}</pre>'
    return html + T.ARRAY_TEXT


def wb_table(tag):
    p = os.path.join(R, f'{tag}_summary.txt')
    if not os.path.exists(p):
        return f'<p class="missing">[{tag} not run]</p>'
    rows, gain = [], []
    for ln in open(p):
        m = re.match(r'\s*([\d.]+) GHz\s+S(\d\d)\s+([-\d.]+) dB\s+VSWR\s+([\d.]+)(?:\s+S\d\d\s+([-\d.]+) dB)?\s+Zin\s+([-\d.]+)\s*([+-][\d.]+)j', ln)
        if m:
            rows.append('<tr>' + ''.join(f'<td>{x}</td>' for x in
                        (m.group(1), m.group(3), m.group(4), m.group(5) or '-', f'{m.group(6)} {m.group(7)}j')) + '</tr>')
        m = re.match(r'\s*([\d.]+) GHz\s+broadside realised gain\s+([-\d.]+) dBi\s+front/back\s+([-\d.]+) dB', ln)
        if m:
            gain.append(f'<tr><td>{m.group(1)}</td><td>{m.group(2)}</td><td>{m.group(3)}</td></tr>')
    head = htmllib.escape(open(p).readlines()[1])
    return (f'<p><b>{tag}:</b> {head}</p><table><tr><th>f (GHz)</th><th>S11 (dB)</th><th>VSWR</th><th>Isolation (dB)</th>'
            '<th>Z<sub>in</sub> (&Omega;)</th></tr>' + ''.join(rows) + '</table>'
            + ('<table><tr><th>f (GHz)</th><th>Broadside realised gain (dBi)</th><th>Front/back (dB)</th></tr>' + ''.join(gain) + '</table>' if gain else ''))


def wb_section(best='wbN4'):
    if not os.path.exists(os.path.join(R, f'{best}_S.csv')):
        return '<p class="missing">[wideband element study not run]</p>'
    html = T.WB_INTRO
    html += img(os.path.join(D, 'fig_wb_geometry.png'), '96%', f'Fig. 8 - Best aperture-coupled candidate so far ({best}): feed under the ground, coupling slot, driven and parasitic patches.')
    html += img(os.path.join(R, 'wb_study.png'), '98%', 'Fig. 9 - Representative candidates from the study (|S11| at the 50 &Omega; feed).')
    html += img(os.path.join(R, 'wb_S11.png'), '88%', 'Fig. 10 - Best candidate, with and without its best feed-layer network, against the present element.')
    rows = []
    for tag, name in (('element_air', 'Present element (as built)'), (best, f'Best candidate ({best})'),
                      (f'{best}_matched', f'{best} + feed-layer network')):
        d = csv(tag)
        if d is None:
            continue
        s = band_stats(d)
        rows.append(f'<tr><td>{name}</td><td>{s["best"]}</td><td>{s["bw3"]}</td><td>{s["bw2"]}</td><td>{s["cover3"]}</td><td>{s["worst"]}</td></tr>')
    html += ('<table><tr><th>Element</th><th>Best</th><th>VSWR&le;3 band</th><th>VSWR&le;2 band</th><th>4-7 GHz with VSWR&le;3</th><th>Worst VSWR 4-7 GHz</th></tr>'
             + ''.join(rows) + '</table>')
    html += wb_table(best)
    for name in ('match_wb.txt', 'opt_wb_log.txt'):
        p = os.path.join(R, name)
        if not os.path.exists(p):
            continue
        if name == 'match_wb.txt':
            lines = open(p).read().splitlines()[:9]
            html += '<p>Top candidates, worst VSWR over 4&ndash;7 GHz without and with the best feed-layer network:</p><pre>' + '\n'.join(lines) + '</pre>'
        else:
            gens = list(dict.fromkeys(ln.strip() for ln in open(p) if ln.startswith('-- gen')))   # resumed runs repeat lines
            html += '<p>Optimiser history (best cost per generation; cost = mean |S11|&sup2; + 0.5&middot;max |S11|&sup2; over 4&ndash;7 GHz):</p><pre>' + '\n'.join(gens) + '</pre>'
    return html + T.WB_TEXT


def main():
    match = open(os.path.join(R, 'match_study.txt')).read() if os.path.exists(os.path.join(R, 'match_study.txt')) else ''
    css = open(os.path.join(HERE, 'report.css')).read()
    body = T.BODY.format(
        date=datetime.date.today().isoformat(),
        fig_layout=img(os.path.join(D, 'fig_layout.png'), '78%', 'Fig. 1 - In2.Cu split into the two feed networks (red: port 1, blue: port 2), driven patches (grey) and parasitic outlines (orange). Yellow dots: the two coax launch points.'),
        fig_stack=img(os.path.join(D, 'fig_stackup.png'), '62%', 'Fig. 2 - Stack-up as built and simulated: 4 mm air gap (&epsilon;<sub>r</sub> 1.0).'),
        fig_elem=img(os.path.join(D, 'fig_element.png'), '70%', 'Fig. 3 - One element: both feeds land directly on the patch edges through a short 2.48 mm (50 &Omega;) stub.'),
        elem_table=element_table('element_air'),
        fig_s11=img(os.path.join(R, 'element_S11.png'), '92%', 'Fig. 4 - Element |S11| at the 100 &Omega; branch: as built and the diagnostic variants.'),
        fig_smith=img(os.path.join(R, 'element_smith.png'), '60%', 'Fig. 5 - As-built element on the Smith chart (100 &Omega;), 4-7 GHz.'),
        variant_table=variant_table(),
        match=f'<pre>{match}</pre>',
        array=array_section(),
        wb=wb_section())
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>C-band array S11 report</title><style>{css}</style></head><body>{body}</body></html>'
    open(OUT_HTML, 'w').write(html)
    subprocess.run(['node', os.path.join(HERE, 'html2pdf.js'), OUT_HTML, OUT_PDF], check=True)
    print('wrote', OUT_PDF)


if __name__ == '__main__':
    main()
