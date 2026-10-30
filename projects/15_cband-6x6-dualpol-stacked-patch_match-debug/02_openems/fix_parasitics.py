"""Fix B (final, feed lines unchanged): every parasitic patch on F.Cu set to the row-1 size, 16.2 mm square.

The supplied parasitics are graded by row (16.2 / 16.5 / 16.9 / 17.2 / 17.5 / 17.8 mm). The element study
(sim_element_fix.py, ps_* runs) shows 16.2 mm with the 4.0 mm gap is the best point for the drawn feed; larger
parasitics detune the rows (16.8 mm: worst VSWR 5.2 vs 3.5 over 5.1-6.2 GHz). In2.Cu and B.Cu are copied unchanged.

    python fix_parasitics.py      -> 06_fixB/F_CU_fixB.dxf, IN2_CU_fixB.dxf (= IN2_CU.dxf), GND.dxf, fixB_check.txt
"""
import os, shutil
import ezdxf
from shapely.geometry import box
import cbgeom as g

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '06_fixB'); os.makedirs(OUT, exist_ok=True)
PAR = 16.2

L = g.layers()
doc = ezdxf.new('R2004'); doc.header['$INSUNITS'] = 4; ms = doc.modelspace()
lines = []
for p in sorted(g.parts(L['par']), key=lambda p: (-round(p.centroid.y), p.centroid.x)):
    c = p.centroid; q = box(c.x - PAR / 2, c.y - PAR / 2, c.x + PAR / 2, c.y + PAR / 2)
    ms.add_lwpolyline(list(q.exterior.coords)[:-1], close=True, dxfattribs={'layer': 'cond'})
    lines.append(f'parasitic at ({c.x:8.3f}, {c.y:8.3f}): {p.bounds[2] - p.bounds[0]:.2f} mm -> {PAR:.2f} mm')
doc.saveas(os.path.join(OUT, 'F_CU_fixB.dxf'))
shutil.copy(os.path.join(g.INP, 'IN2_CU.dxf'), os.path.join(OUT, 'IN2_CU_fixB.dxf'))
shutil.copy(os.path.join(g.INP, 'GND.dxf'), os.path.join(OUT, 'GND.dxf'))
open(os.path.join(OUT, 'fixB_check.txt'), 'w').write(
    f'Fix B: {len(lines)} parasitic patches set to {PAR} mm (centres unchanged); In2.Cu and B.Cu unchanged; air gap 4.0 mm unchanged.\n'
    + '\n'.join(lines) + '\n')
print(f'{len(lines)} parasitics -> {PAR} mm; In2.Cu, B.Cu copied unchanged')
