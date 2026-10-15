"""PyAEDT build of the 1-bit RCSPA element / 1x5 array (25-29 GHz), from the same geometry as the DXFs.
    pip install ansys-aedt-core shapely ezdxf
    python hfss_rba_build.py element          # single element, 1 lumped port, both diode states as variables
    python hfss_rba_build.py array5           # 1x5, 5 lumped ports (Fig.5) - preload/state applied in post-processing
    python hfss_rba_build.py array_div        # 1x5 + 1:5 divider (Fig.6), 1 port
PIN diode MA4AGFCP910 models (paper):  ON = 5.2 ohm + 0.2 nH (series RLC)   OFF = 0.018 pF + 0.2 nH (series RLC)
Each diode sheet gets design variables R_Dna, L_Dna, C_Dna so a state code is applied by setting variables:
    state 0 (SW1 ON):  Dna = ON,  Dnb = OFF      state 1 (SW2 ON):  Dna = OFF, Dnb = ON
DC block 3.6 pF (series C, + 0.15 nH ESL for 0201), bias R = 100 ohm (series R).
NOT executed here (no HFSS licence).  PyAEDT renames keyword arguments between releases; if a call fails use the
GUI steps in 05_docs/DESIGN_GUIDE.md section 7."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "02_python"))
import rbageom as G
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

OUT = os.path.abspath("hfss_out"); os.makedirs(OUT, exist_ok=True)
ON, OFF = dict(R="5.2ohm", L="0.2nH", C="1e6pF"), dict(R="0.001ohm", L="0.2nH", C="0.018pF")

def open_hfss(name):
    from ansys.aedt.core import Hfss
    h = Hfss(project=os.path.join(OUT, name + ".aedt"), design=name, solution_type="Modal", version="2024.2", new_desktop=True)
    h.modeler.model_units = "mm"
    for nm, er, tg in (("RT5880_rba", 2.2, 0.0009), ("RO4003C_rba", 3.55, 0.0027)):
        m = h.materials.add_material(nm); m.permittivity = er; m.dielectric_loss_tangent = tg
    return h

def sheet(h, poly, z, name):
    pts = [[x, y, z] for x, y in list(poly.exterior.coords)[:-1]]
    s = h.modeler.create_polyline(pts + [pts[0]], cover_surface=True, close_surface=True, name=name)
    holes = []
    for j, hh in enumerate(poly.interiors):
        hp = [[x, y, z] for x, y in list(hh.coords)[:-1]]
        holes.append(h.modeler.create_polyline(hp + [hp[0]], cover_surface=True, close_surface=True, name=f"{name}_h{j}"))
    if holes: h.modeler.subtract(s.name, [x.name for x in holes], keep_originals=False)
    return s

def layer(h, b, lay, z, extra_sub=None):
    g = unary_union(b.L.get(lay, []))
    if extra_sub is not None: g = g.difference(extra_sub)
    ps = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    names = [sheet(h, p, z, f"{lay}_{i}").name for i, p in enumerate(ps)]
    if len(names) > 1: h.modeler.unite(names)
    h.assign_perfecte_to_sheets(names[0], name=f"PEC_{lay}")

def build(b, name):
    h = open_hfss(name); x0, y0, x1, y1 = b.L["OUTLINE"][0].bounds
    if "ANT_OUTLINE" in b.L: ax0, ay0, ax1, ay1 = b.L["ANT_OUTLINE"][0].bounds; ax0 += .05; ay0 += .05; ax1 -= .05; ay1 -= .05
    else: ax0, ay0, ax1, ay1 = x0, y0, x1, y1
    h.modeler.create_box([x0, y0, 0], [x1 - x0, y1 - y0, G.H3], name="Sub3", material="RO4003C_rba")
    h.modeler.create_box([ax0, ay0, G.H3], [ax1 - ax0, ay1 - ay0, G.H2], name="Sub2", material="RT5880_rba")
    h.modeler.create_box([ax0, ay0, G.H3 + G.H2], [ax1 - ax0, ay1 - ay0, G.H1], name="Sub1", material="RT5880_rba")
    layer(h, b, "M1", G.Z["M1"]); layer(h, b, "M2", G.Z["M2"]); layer(h, b, "M4", G.Z["M4"])
    layer(h, b, "M3", G.Z["M3"], unary_union(b.L.get("M3_SLOT", []) + b.L.get("NPTH", [])))
    for i, (x, y, d, span) in enumerate(b.vias):
        z0, z1 = (G.Z["M3"], G.Z["M2"]) if span == "M2-M3" else (G.Z["M4"], G.Z["M3"])
        h.modeler.create_cylinder("Z", [x, y, z0], d / 2, z1 - z0, name=f"via{i}", material="pec")
    for c in b.comp:                                   # lumped RLC sheets across each component gap on M4
        x, y, w, hh = c["x"], c["y"], c["w"], c["h"]; ref = c["ref"]
        horiz = ref.startswith("D")                    # diodes bridge gaps along x; C and R along y
        from shapely.geometry import box
        s = sheet(h, box(x - w / 2, y - hh / 2, x + w / 2, y + hh / 2), 0.0, f"S_{ref}")
        line = [[x - w / 2, y, 0], [x + w / 2, y, 0]] if horiz else [[x, y - hh / 2, 0], [x, y + hh / 2, 0]]
        if ref.startswith("D"):
            st = ON if ref.endswith("a") else OFF                         # default code 0 (SW1 ON)
            for k, v in st.items(): h[f"{k}_{ref}"] = v
            kw = dict(rlc_type="Series", resistance=f"R_{ref}", inductance=f"L_{ref}", capacitance=f"C_{ref}")
        elif ref.startswith("C"): kw = dict(rlc_type="Series", capacitance="3.6pF", inductance="0.15nH")
        else: kw = dict(rlc_type="Series", resistance="100ohm")
        try: h.assign_lumped_rlc_to_sheet(assignment=s.name, start_direction=line, name=f"RLC_{ref}", **kw)
        except TypeError: h.assign_lumped_rlc_to_sheet(s.name, line, name=f"RLC_{ref}", **kw)
    for k, g in enumerate(b.L.get("PORT", []), 1):  # vertical lumped port sheet: M4 line -> M3 ground
        px0, py0, px1, py1 = g.bounds
        from shapely.geometry import Polygon
        pts = [[px0, py0, 0], [px1, py0, 0], [px1, py0, G.H3], [px0, py0, G.H3]]
        s = h.modeler.create_polyline(pts + [pts[0]], cover_surface=True, close_surface=True, name=f"Psheet{k}")
        try: h.lumped_port(assignment=s.name, integration_line=[[(px0 + px1) / 2, py0, 0], [(px0 + px1) / 2, py0, G.H3]], impedance=50, name=f"P{k}")
        except TypeError: h.lumped_port(s.name, integration_line=[[(px0 + px1) / 2, py0, 0], [(px0 + px1) / 2, py0, G.H3]], impedance=50, name=f"P{k}")
    pad = 3.0   # lambda0/4 at 25 GHz
    air = h.modeler.create_box([x0 - pad, y0 - pad, -pad], [x1 - x0 + 2 * pad, y1 - y0 + 2 * pad, G.Z["M1"] + 2 * pad], name="Air", material="air")
    h.assign_radiation_boundary_to_objects(air.name, name="Rad")
    h.insert_infinite_sphere(x_start=-180, x_stop=180, x_step=1, y_start=0, y_stop=90, y_step=90, name="Ecut_Hcut")
    s = h.create_setup("Setup1"); s.props["Frequency"] = "26.5GHz"; s.props["MaximumPasses"] = 15; s.props["MaxDeltaS"] = 0.01; s.update()
    h.create_linear_count_sweep("Setup1", units="GHz", start_frequency=24, stop_frequency=30, num_of_freq_points=61, name="Sweep", sweep_type="Interpolating")
    h.save_project(); return h

def set_code(h, code):
    """code '00101': per element 0 -> SW1 ON, 1 -> SW2 ON."""
    for n, bit in enumerate(code, 1):
        a, bb = (ON, OFF) if bit == "0" else (OFF, ON)
        for k in "RLC": h[f"{k}_D{n}a"] = a[k]; h[f"{k}_D{n}b"] = bb[k]

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "element"
    if what == "element": h = build(G.board_element(), "RCSPA_element")
    elif what == "array5": h = build(G.board_array(False), "RBA_1x5_5port")
    else:
        h = build(G.board_array(True), "RBA_1x5_divider")
        # beam codes from 02_python/results/scan_table_26p5GHz.csv (paper preload); e.g. +40 deg:
        set_code(h, "00011"); h.save_project()
