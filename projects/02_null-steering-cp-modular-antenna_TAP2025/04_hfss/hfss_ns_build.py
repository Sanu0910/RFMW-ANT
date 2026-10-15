"""PyAEDT build of the modular null-steering / CP antenna in HFSS, from the SAME geometry used for the DXFs.

    pip install ansys-aedt-core shapely ezdxf numpy        (PyAEDT >= 0.10)
    python hfss_ns_build.py ps          # phase shifter alone (2 wave/lumped ports), varactors as lumped RLC
    python hfss_ns_build.py dipole      # antenna alone
    python hfss_ns_build.py unit        # one unit (PS + dipole), 1 port
    python hfss_ns_build.py 1D | 2D | CP | CPcophased   # systems placed per 01_dxf/assembly_3D_placement.csv
Every varactor is a lumped RLC sheet with series R = Rp, L = Lp and C = design variable Cv<unit>_<1|2>,
so a parametric sweep of Cv... reproduces the phase-shifter tuning; for the arrays set per-unit values from
02_python/results/LUT_1D_null_angle_to_bias.csv.
NOT executed here (no HFSS licence). PyAEDT renames keyword arguments between releases - if a call fails,
use the equivalent GUI step from 05_docs/DESIGN_GUIDE section 7."""
import os, sys, csv, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "02_python"))
import nsgeom as G
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

AEDT_VERSION = "2024.2"
OUT = os.path.abspath("hfss_out"); os.makedirs(OUT, exist_ok=True)
LAYER_Z = {"TOP": G.Z_TOP, "MID": G.Z_MID, "BOT": G.Z_BOT}

class Placement:
    """board (bx, by, bz) -> world: centre (cx, cy), azimuth az of the board x axis; board y -> world +z;
    board thickness bz along the board normal n = (-sin az, cos az, 0)."""
    def __init__(self, cx=0.0, cy=0.0, az=0.0, mirror=False):
        self.c = (cx, cy); a = math.radians(az); self.ux = (math.cos(a), math.sin(a)); self.n = (-math.sin(a), math.cos(a))
    def w(self, bx, by, bz):
        return [self.c[0] + bx * self.ux[0] + bz * self.n[0], self.c[1] + bx * self.ux[1] + bz * self.n[1], by]

def open_hfss(name):
    from ansys.aedt.core import Hfss
    h = Hfss(project=os.path.join(OUT, name + ".aedt"), design=name, solution_type="Modal",
             version=AEDT_VERSION, non_graphical=False, new_desktop=True)
    h.modeler.model_units = "mm"
    for nm, er, tg in (("RO4003C_ns", 3.55, 0.0027), ("RO4450F_ns", 3.52, 0.004)):
        m = h.materials.add_material(nm); m.permittivity = er; m.dielectric_loss_tangent = tg
    return h

def sheet(h, pts, name):
    return h.modeler.create_polyline(pts + [pts[0]], cover_surface=True, close_surface=True, name=name)

def add_layer(h, board, layer, pl, tag):
    g = unary_union(board.L.get(layer, []))
    polys = list(g.geoms) if isinstance(g, MultiPolygon) else ([g] if not g.is_empty else [])
    names = []
    for i, p in enumerate(polys):
        ext = [pl.w(x, y, LAYER_Z[layer]) for x, y in list(p.exterior.coords)[:-1]]
        s = sheet(h, ext, f"{tag}_{layer}_{i}")
        holes = [sheet(h, [pl.w(x, y, LAYER_Z[layer]) for x, y in list(hh.coords)[:-1]], f"{tag}_{layer}_{i}_h{j}") for j, hh in enumerate(p.interiors)]
        if holes: h.modeler.subtract(s.name, [x.name for x in holes], keep_originals=False)
        names.append(s.name)
    if names:
        if len(names) > 1: h.modeler.unite(names)
        h.assign_perfecte_to_sheets(names[0], name=f"PEC_{tag}_{layer}")
    return names[:1]

def substrates(h, board, pl, tag):
    x0, y0, x1, y1 = board.L["OUTLINE"][0].bounds
    corners = lambda z0: [pl.w(x0, y0, z0)]
    # boxes are created axis-aligned in board frame via a rotated coordinate system
    cs = h.modeler.create_coordinate_system(origin=pl.w(0, 0, 0), x_pointing=[pl.ux[0], pl.ux[1], 0], y_pointing=[0, 0, 1], name=f"CS_{tag}")
    h.modeler.set_working_coordinate_system(cs.name)
    # in CS: x = board x, y = board y, z = -board thickness direction (right-handed: x cross y = -n) -> use negative z
    h.modeler.create_box([x0, y0, -G.Z_MID], [x1 - x0, y1 - y0, -(G.Z_TOP - G.Z_MID)], name=f"{tag}_core1", material="RO4003C_ns")
    h.modeler.create_box([x0, y0, -G.H_CORE], [x1 - x0, y1 - y0, -G.H_PREPREG], name=f"{tag}_prepreg", material="RO4450F_ns")
    h.modeler.create_box([x0, y0, 0], [x1 - x0, y1 - y0, -G.H_CORE], name=f"{tag}_core2", material="RO4003C_ns")
    h.modeler.set_working_coordinate_system("Global")

def vias(h, board, pl, tag):
    for i, (x, y, d, span) in enumerate(board.vias):
        z0 = G.Z_BOT if span.startswith("MID-BOT") or span.startswith("TOP-MID-BOT") else G.Z_MID
        z1 = G.Z_MID if span == "MID-BOT" else G.Z_TOP
        p0 = pl.w(x, y, z0)
        h.modeler.create_cylinder(orientation="Y" if abs(pl.n[1]) > 0.99 else "X", origin=p0, radius=d / 2,
                                  height=(z1 - z0) * (pl.n[1] if abs(pl.n[1]) > 0.99 else pl.n[0]), name=f"{tag}_via{i}", material="pec")

def lumped_rlc(h, board, pl, tag, unit, Cvar):
    """Varactors (series Rp + Lp + Cv) and DC blocks / chokes on the gaps found in board.comp."""
    for c in board.comp:
        ref = c["ref"]; lay = c["side"]; z = LAYER_Z[lay]
        x, y, w_, l_ = c["x"], c["y"], max(c["w"], 0.5), c["h"]
        if ref[0] not in "DCLR": continue
        horiz = ref[0] in "LR"                                 # chokes/resistors run along board x
        if horiz: pts = [(x - 0.2, y - 0.3), (x + 0.2, y - 0.3), (x + 0.2, y + 0.3), (x - 0.2, y + 0.3)]
        else:     pts = [(x - 0.3, y - 0.2), (x + 0.3, y - 0.2), (x + 0.3, y + 0.2), (x - 0.3, y + 0.2)]
        s = sheet(h, [pl.w(a, b, z) for a, b in pts], f"{tag}_{ref}")
        line = [pl.w(x - 0.2, y, z), pl.w(x + 0.2, y, z)] if horiz else [pl.w(x, y - 0.2, z), pl.w(x, y + 0.2, z)]
        if ref[0] == "D":
            kw = dict(rlc_type="Series", resistance=2.0, inductance=0.35e-9, capacitance=f"Cv{unit}_{ref[1:]}")
            h[f"Cv{unit}_{ref[1:]}"] = Cvar
        elif ref[0] == "C": kw = dict(rlc_type="Series", capacitance=39e-12, inductance=0.4e-9)
        elif ref[0] == "L": kw = dict(rlc_type="Parallel", inductance=100e-9, capacitance=0.11e-12)   # 0402 SRF ~1.5 GHz
        else:               kw = dict(rlc_type="Series", resistance=10e3)
        try:
            h.assign_lumped_rlc_to_sheet(assignment=s.name, start_direction=line, name=f"RLC_{tag}_{ref}", **kw)
        except TypeError:
            h.assign_lumped_rlc_to_sheet(s.name, line, name=f"RLC_{tag}_{ref}", **kw)

def rf_port(h, pl, tag, y_edge, lay_sig, lay_ref, width, name):
    zs, zr = LAYER_Z[lay_sig], LAYER_Z[lay_ref]
    pts = [pl.w(-width / 2, y_edge, zr), pl.w(width / 2, y_edge, zr), pl.w(width / 2, y_edge, zs), pl.w(-width / 2, y_edge, zs)]
    s = sheet(h, pts, f"{tag}_psheet_{name}")
    line = [pl.w(0, y_edge, zr), pl.w(0, y_edge, zs)]
    try:
        return h.lumped_port(assignment=s.name, integration_line=line, impedance=50, name=name, renormalize=True)
    except TypeError:
        return h.lumped_port(s.name, integration_line=line, impedance=50, name=name)

def build_board(h, board, pl, tag, unit, Cvar="1.0pF"):
    substrates(h, board, pl, tag)
    for lay in ("TOP", "MID", "BOT"): add_layer(h, board, lay, pl, tag)
    vias(h, board, pl, tag); lumped_rlc(h, board, pl, tag, unit, Cvar)

def finish(h, f_lo=5.0, f_hi=7.0, pad=13.0, ff=True):
    h.create_open_region(frequency="6GHz", boundary="Radiation") if hasattr(h, "create_open_region") else None
    if ff: h.insert_infinite_sphere(x_start=-180, x_stop=180, x_step=2, y_start=0, y_stop=180, y_step=2, name="FF", definition="Theta-Phi")
    s = h.create_setup("Setup1"); s.props["Frequency"] = "6GHz"; s.props["MaximumPasses"] = 15; s.props["MaxDeltaS"] = 0.01; s.update()
    h.create_linear_count_sweep("Setup1", units="GHz", start_frequency=f_lo, stop_frequency=f_hi, num_of_freq_points=41, name="Sweep", sweep_type="Interpolating")
    h.save_project()

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "unit"
    if what == "ps":
        h = open_hfss("PS_alone"); b = G.board_phase_shifter("paper", "L"); pl = Placement()
        build_board(h, b, pl, "ps", 1)
        rf_port(h, pl, "ps", 0.0, "TOP", "MID", G.W_TOP50, "P1_IN"); rf_port(h, pl, "ps", G.PS["L"], "BOT", "MID", G.W_BOT50, "P2_OUT")
        finish(h, ff=False)
        # sweep Cv1_1 = Cv1_2 together: Optimetrics > Parametric, values 0.14..1.7 pF (both varactors equal - paper)
    elif what == "dipole":
        h = open_hfss("Dipole_alone"); b = G.board_dipole(); pl = Placement()
        for lay in ("TOP", "BOT"): add_layer(h, b, lay, pl, "ant")
        x0, y0, x1, y1 = b.L["OUTLINE"][0].bounds
        cs = h.modeler.create_coordinate_system(origin=[0, 0, 0], x_pointing=[1, 0, 0], y_pointing=[0, 0, 1], name="CS_ant")
        h.modeler.set_working_coordinate_system(cs.name)
        h.modeler.create_box([x0, y0, -G.Z_TOP], [x1 - x0, y1 - y0, 0], name="ant_sub", material="RO4003C_ns")   # 2-layer board: see guide
        h.modeler.set_working_coordinate_system("Global")
        rf_port(h, pl, "ant", 0.0, "BOT", "TOP", G.DP["w2"], "P1"); finish(h)
    else:
        rows = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "01_dxf", "assembly_3D_placement.csv"))))
        sysmap = {"unit": None, "1D": "SYS_1D", "2D": "SYS_2D", "CP": "SYS_CP", "CPcophased": "SYS_CP_cophased"}
        h = open_hfss("NS_" + what)
        if what == "unit":
            b = G.board_unit("A"); pl = Placement(); build_board(h, b, pl, "u1", 1)
            rf_port(h, pl, "u1", 0.0, "TOP", "MID", G.W_TOP50, "P1")
        else:
            for r in [r for r in rows if r["system"] == sysmap[what]]:
                u = int(r["unit"]); b = G.board_unit(r["type"], unit_no=u)
                if what.startswith("CP"):
                    az = float(r["azimuth_deg"]); pl = Placement(12.5 * math.cos(math.radians(az)), 12.5 * math.sin(math.radians(az)), az)
                else:
                    pl = Placement(float(r["x_world_mm"]), float(r["y_world_mm"]), 0.0)
                build_board(h, b, pl, f"u{u}", u)
                rf_port(h, pl, f"u{u}", 0.0, "TOP", "MID", G.W_TOP50, f"P{u}")
        finish(h)
        # Array excitation: Edit Sources -> all ports 1 W, 0 deg (the paper's equal-split splitter);
        # null steering is set by the Cv<unit>_<n> variables (one value per unit; both varactors equal).
