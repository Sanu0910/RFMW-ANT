"""STEP (AP242) model of the C-band 6x6 array with fix B and the two 4-hole flange SMA jacks, built with SolidCraft.

    python build_step.py --prepare      (needs ezdxf + shapely; writes 07_step/dxf_src/*.dxf and the command script)
    python build_step.py --run          (needs solidcraft-cli on PATH; writes 07_step/*.step and STEP_report.txt)
    python build_step.py                (both)

Variant: fix B layers from 06_fixB/ (In2.Cu with the new feed sections, F.Cu with all parasitics 16.2 mm).
Frame: mm, board centre at (0, 0), z = 0 on top of the ground copper's lower face ... see stack below; +z to the sky.

Stack (z, mm):                  B.Cu ground          -0.035 .. 0
                                RT5880 0.8           0 .. 0.8
                                In2.Cu (fix B)       0.8 .. 0.835
                                air gap 4.0          (spacers not modelled)
                                FR4 0.4              4.8 .. 5.2
                                F.Cu (fix B)         5.2 .. 5.235
Copper 35 um [ASSUMED 1 oz]. FR4 sheet = board outline [ASSUMED, same as the ground outline].
SMA jacks [ASSUMED generic 4-hole flange panel jack, dimensions below] on the ground side (-z) at the two coax launch
points found in IN2_CU.dxf; the 1.27 mm centre pin passes through a 1.3 mm hole in the RT5880 and a 4.2 mm antipad in
the ground copper and ends flush with the top of the In2.Cu line.
Every body is measured by SolidCraft and compared with area x thickness (STEP_report.txt); > 0.05 % error fails.
"""
import os, sys, json, math, shutil, subprocess, zipfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '07_step')); TMP = os.path.join(OUT, 'dxf_src')
NAME = 'CBand_6x6_fixB_with_SMA'
CU, H_SUB, Z_FR4, H_FR4 = 0.035, 0.8, 4.8, 0.4
TOL = 5e-4
COL = {'cu': '#c8823a', 'rt5880': '#e9e1c6', 'fr4': '#b9c27a', 'brass': '#d4af37', 'ptfe': '#f2f2f2', 'pin': '#e6c35c'}
# generic 4-hole flange SMA jack (panel mount), mm  [ASSUMED]
SMA = dict(flange=12.7, t_flange=1.6, hole_d=2.69, hole_sp=8.64, body_d=6.35, body_l=9.5, ptfe_d=4.1, pin_d=1.27,
           antipad_d=4.2, pin_hole_d=1.3)


def prepare():
    import ezdxf
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    sys.path.insert(0, HERE)
    import cbgeom as g
    os.makedirs(TMP, exist_ok=True)
    L = g.layers('fixB'); P = g.find_ports(g.layers()['drv'])
    pins = [(round(P[k]['x'] + 0.6, 3), round(sum(P[k]['y']) / 2, 3)) for k in (1, 2)]   # 0.6 mm in from the line end

    def write(name, geom, circles=()):
        d = ezdxf.new('R2010'); d.header['$INSUNITS'] = 4; m = d.modelspace()
        ps = [p for p in g.parts(geom) if p.geom_type == 'Polygon' and p.area > 1e-9] if geom is not None else []
        for p in ps:
            for ring in [p.exterior, *p.interiors]:
                m.add_lwpolyline(list(ring.coords)[:-1], close=True)
        for x, y, r in circles:
            m.add_circle((x, y), r)
        d.saveas(os.path.join(TMP, name + '.dxf'))
        return ps

    S, expect = [], []
    def body(name, geom, z0, t, color, circles=()):
        ps = write(name, geom, circles)
        pts = [p.representative_point().coords[0] for p in ps] + [(x, y) for x, y, _ in circles]
        area = sum(p.area for p in ps) + sum(math.pi * r * r for _, _, r in circles)
        S.extend([{'command': 'sketch.create', 'params': {'plane': 'XY', 'offset': z0, 'name': name + '_sk'}},
                  {'command': 'sketch.insert_dxf', 'params': {'path': os.path.relpath(os.path.join(TMP, name + '.dxf'), OUT)}},
                  {'command': 'sketch.finish', 'params': {}},
                  {'command': 'solid.extrude', 'params': {'distance': t, 'profiles': [{'point': list(p)} for p in pts],
                                                           'operation': 'new', 'body_name': name}}])
        n = len(pts)
        names = [name] + ['%s (%d)' % (name, k) for k in range(2, n + 1)]
        S.append({'command': 'appearance.assign', 'params': {'bodies': names, 'color': COL[color]}})
        expect.append((name, area * t, n))

    outline = L['gnd']
    holes_pin = unary_union([Point(x, y).buffer(SMA['pin_hole_d'] / 2, 64) for x, y in pins])
    antipads = unary_union([Point(x, y).buffer(SMA['antipad_d'] / 2, 64) for x, y in pins])
    body('B_Cu_ground', outline.difference(antipads), -CU, CU, 'cu')
    body('RT5880_0p8', outline.difference(holes_pin), 0.0, H_SUB, 'rt5880')
    body('In2_Cu_fixB', L['drv'], H_SUB, CU, 'cu')
    body('FR4_0p4', outline, Z_FR4, H_FR4, 'fr4')
    body('F_Cu_fixB', L['par'], Z_FR4 + H_FR4, CU, 'cu')
    for k, (x, y) in enumerate(pins, start=1):
        f2, hs = SMA['flange'] / 2, SMA['hole_sp'] / 2
        flange = box(x - f2, y - f2, x + f2, y + f2).difference(unary_union(
            [Point(x + sx * hs, y + sy * hs).buffer(SMA['hole_d'] / 2, 64) for sx in (-1, 1) for sy in (-1, 1)]
            + [Point(x, y).buffer(SMA['ptfe_d'] / 2, 64)]))
        z_f = -CU - SMA['t_flange']
        body(f'SMA{k}_flange', flange, z_f, SMA['t_flange'], 'brass')
        shell = Point(x, y).buffer(SMA['body_d'] / 2, 64).difference(Point(x, y).buffer(SMA['ptfe_d'] / 2, 64))
        body(f'SMA{k}_body', shell, z_f - SMA['body_l'], SMA['body_l'], 'brass')
        ptfe = Point(x, y).buffer(SMA['ptfe_d'] / 2, 64).difference(Point(x, y).buffer(SMA['pin_d'] / 2, 64))
        body(f'SMA{k}_ptfe', ptfe, z_f - SMA['body_l'], SMA['body_l'] + SMA['t_flange'], 'ptfe')
        body(f'SMA{k}_pin', None, z_f - SMA['body_l'] + 1.0, (H_SUB + CU) - (z_f - SMA['body_l'] + 1.0), 'pin',
             circles=[(x, y, SMA['pin_d'] / 2)])
    json.dump({'commands': S}, open(os.path.join(OUT, NAME + '.solidcraft.json'), 'w'), indent=0)
    json.dump({'expect': expect, 'pins': pins}, open(os.path.join(OUT, NAME + '.expect.json'), 'w'), indent=1)
    print('prepared', len(expect), 'bodies; SMA pins at', pins)


def run():
    js = os.path.join(OUT, NAME + '.solidcraft.json'); step = os.path.join(OUT, NAME + '.step')
    exe = shutil.which('solidcraft-cli')
    if not exe:
        raise SystemExit('solidcraft-cli not on PATH')
    r = subprocess.run([exe, 'run', js, '--out', step], capture_output=True, text=True, cwd=OUT)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit('solidcraft failed')
    res = json.loads(r.stdout[r.stdout.index('{'):])
    E = json.load(open(os.path.join(OUT, NAME + '.expect.json')))
    got = {}
    for bd in res['bodies']:
        k = re.sub(r' \(\d+\)$', '', bd['name']); v = got.setdefault(k, [0, 0.0]); v[0] += 1; v[1] += bd['volume_mm3']
    ok, lines = True, [f'STEP build report: {NAME}.step ({res["body_count"]} bodies)',
                       '%-18s %7s %14s %14s %9s' % ('body', 'count', 'expected mm3', 'SolidCraft mm3', 'error')]
    for name, vol, n in E['expect']:
        v = got.get(name, [0, 0.0]); err = (v[1] - vol) / vol if vol else 0.0
        good = v[0] == n and abs(err) < TOL; ok &= good
        lines.append('%-18s %3d/%-3d %14.4f %14.4f %+8.4f%%  %s' % (name, v[0], n, vol, v[1], 100 * err, 'PASS' if good else 'FAIL'))
    lo = [min(b['bbox']['min'][i] for b in res['bodies']) for i in range(3)]
    hi = [max(b['bbox']['max'][i] for b in res['bodies']) for i in range(3)]
    lines.append('extents x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f mm' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    lines.append('SMA centre pins at ' + ', '.join('(%.3f, %.3f)' % tuple(p) for p in E['pins']))
    lines.append('ALL PASS' if ok else 'CHECK FAILED')
    open(os.path.join(OUT, 'STEP_report.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    if os.path.getsize(step) > 20e6:
        with zipfile.ZipFile(step + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            z.write(step, os.path.basename(step))
        os.remove(step)
    if not ok:
        raise SystemExit('STEP check failed')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if '--run' not in sys.argv:
        prepare()
    if '--prepare' not in sys.argv:
        run()
