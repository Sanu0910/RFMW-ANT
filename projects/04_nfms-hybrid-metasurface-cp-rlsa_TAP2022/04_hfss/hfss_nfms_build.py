"""PyAEDT builds for the NFMS RLSA + hybrid-metasurface system (20 GHz), from the same geometry as the DXFs.
    pip install ansys-aedt-core shapely ezdxf
    python hfss_nfms_build.py cell1           # Type I unit cell, Floquet ports, sweep a, b 0.2..7.2  -> cell table CSV
    python hfss_nfms_build.py cell2           # Type II unit cell, sweep hole radius r 0..3.4
    python hfss_nfms_build.py rlsa            # RLSA alone: Al ground, air, TLY-5, slotted copper, probe + wave port
    python hfss_nfms_build.py system 0 120    # RLSA + HM I (psi1) + HM II (psi2) ; angles in degrees
Notes
  * cell1/cell2 export results/hfss_cell_table.csv in the columns of 02_python/results/cell_library.csv.  Put it in
    place of the model library (cells.load_table) and rerun build_nfms.py so the DXFs use full-wave cells.
  * Phase reference = the two cell faces (deembed the Floquet ports to z = 0 and z = 4.8 mm), as in the paper.
  * rlsa / system are large (~350 mm = 23 lambda0 at 20 GHz).  Use FE-BI or a radiation boundary lambda0/4 away,
    or run the RLSA in the time domain (paper: CST transient).  HFSS SBR+ / IE region for the HMs is an option.
  * The full system is about 4 x 1800 patches + 1920 slots: import the DXFs (step 7 of the guide) if scripted creation
    is too slow.
NOT executed here (no HFSS licence).  PyAEDT renames keyword arguments between releases; if a call fails use the
GUI steps in 05_docs/DESIGN_GUIDE.md section 7."""
import os, sys, math, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "02_python"))
import nfmsgeom as G
import cells as CL

OUT = os.path.abspath("hfss_out"); os.makedirs(OUT, exist_ok=True)

def open_hfss(name, solution="Modal"):
    from ansys.aedt.core import Hfss
    h = Hfss(project=os.path.join(OUT, name + ".aedt"), design=name, solution_type=solution, version="2024.2", new_desktop=True)
    h.modeler.model_units = "mm"
    m = h.materials.add_material("TLY5_nfms"); m.permittivity = CL.ER; m.dielectric_loss_tangent = CL.TAND
    return h

def unit_cell(kind):
    h = open_hfss("HM_cell_type%d" % kind)
    d, t, n = CL.D_CELL, CL.T_LAM, CL.N_LAM
    h["d"] = "%gmm" % d; h["t"] = "%gmm" % t; h["air"] = "15mm"
    h.modeler.create_box(["-d/2", "-d/2", "0"], ["d", "d", "3*t"], name="diel", material="TLY5_nfms")
    if kind == 1:
        h["a"] = "4mm"; h["b"] = "3.7mm"
        for k, (v, z) in enumerate((("a", "0"), ("b", "t"), ("a", "2*t"), ("b", "3*t"))):
            r = h.modeler.create_rectangle("XY", ["-%s/2" % v, "-%s/2" % v, z], [v, v], name="M%d" % (k + 1))
            h.assign_perfecte_to_sheets([r.name], name="PEC_M%d" % (k + 1))      # final run: 17 um copper boxes
    else:
        h["r"] = "1.4mm"
        hole = h.modeler.create_cylinder("Z", [0, 0, 0], "r", "3*t", name="hole", material="vacuum")
        h.modeler.subtract("diel", [hole.name], keep_originals=False)
    box = h.modeler.create_box(["-d/2", "-d/2", "-air"], ["d", "d", "3*t+2*air"], name="airbox", material="vacuum")
    # master/slave pairs on x and y, Floquet ports top and bottom (normal incidence)
    fx = [f.id for f in box.faces if abs(f.center[0] + d / 2) < 1e-6][0]; fx2 = [f.id for f in box.faces if abs(f.center[0] - d / 2) < 1e-6][0]
    fy = [f.id for f in box.faces if abs(f.center[1] + d / 2) < 1e-6][0]; fy2 = [f.id for f in box.faces if abs(f.center[1] - d / 2) < 1e-6][0]
    h.assign_primary(fx, [-d / 2, -d / 2, -15], [-d / 2, d / 2, -15], name="MX"); h.assign_secondary(fx2, "MX", [d / 2, -d / 2, -15], [d / 2, d / 2, -15], name="SX")
    h.assign_primary(fy, [-d / 2, -d / 2, -15], [d / 2, -d / 2, -15], name="MY"); h.assign_secondary(fy2, "MY", [-d / 2, d / 2, -15], [d / 2, d / 2, -15], name="SY")
    zb = [f.id for f in box.faces if abs(f.center[2] + 15) < 1e-6][0]; zt = [f.id for f in box.faces if abs(f.center[2] - (3 * t + 15)) < 1e-6][0]
    h.create_floquet_port(zb, deembed_distance="air", nummodes=2, name="P_in")
    h.create_floquet_port(zt, deembed_distance="air", nummodes=2, name="P_out")
    s = h.create_setup("S20", Frequency="20GHz", MaximumPasses=15, MaximumDeltaS=0.005)
    s.create_frequency_sweep(unit="GHz", start_frequency=18.5, stop_frequency=21.5, num_of_freq_points=31, sweep_type="Interpolating", name="band")
    if kind == 1:
        h.parametrics.add("a", "0.2mm", "7.2mm", "0.1mm", variation_type="LinearStep", name="sweep_ab").add_variation("b", "0.2mm", "7.2mm", "0.1mm", variation_type="LinearStep")
    else:
        h.parametrics.add("r", "0mm", "3.4mm", "0.05mm", variation_type="LinearStep", name="sweep_r")
    h.save_project()
    print("Run the parametric sweep, then export S(P_out:1,P_in:1) magnitude (dB) and phase (deg) at 20 GHz for every variation,")
    print("normalise phase to Type II r = 3.4 mm, and write results/hfss_cell_table.csv (type,a_mm,b_mm,r_mm,phase_unwrapped_deg,phase_norm_deg,S21_dB).")
    return h

def poly_sheet(h, poly, z, name):
    pts = [[x, y, z] for x, y in list(poly.exterior.coords)[:-1]]
    return h.modeler.create_polyline(pts + [pts[0]], cover_surface=True, close_surface=True, name=name)

def rlsa(h=None, with_air=True):
    R = G.R; own = h is None
    if own: h = open_hfss("RLSA_20GHz", "Terminal")
    for k, v in (("h_air", R["h_air"]), ("h_d", R["h_diel"]), ("t_gnd", R["t_ground"]), ("head_z0", R["head_z0"]), ("head_h", R["head_h"]), ("head_d", R["head_d"])):
        h[k] = "%gmm" % v
    b = G.board_rlsa()
    rcu = b.r_cu; rd = R["D_diel"] / 2
    h.modeler.create_cylinder("Z", [0, 0, "-t_gnd"], rd, "t_gnd", name="ground", material="aluminum")
    h.modeler.create_cylinder("Z", [0, 0, "h_air"], rd, "h_d", name="tly5", material="TLY5_nfms")
    pocket = h.modeler.create_cylinder("Z", [0, 0, "h_air"], "head_d/2", "head_z0+head_h-h_air", name="pocket", material="vacuum")
    h.modeler.subtract("tly5", [pocket.name], keep_originals=False)
    top = h.modeler.create_circle("XY", [0, 0, "h_air+h_d"], rcu, name="top_cu")
    slots = []
    for k, p in enumerate(b.L["TOP_SLOT"]): slots.append(poly_sheet(h, p, R["h_air"] + R["h_diel"], "s%04d" % k).name)
    for i in range(0, len(slots), 200): h.modeler.subtract(top.name, slots[i:i + 200], keep_originals=False)
    h.assign_perfecte_to_sheets([top.name], name="PEC_top")
    # radial waveguide side wall: the paper does not say; an absorbing/shorted rim is common. Leave open (radiation box).
    pin = h.modeler.create_cylinder("Z", [0, 0, "-t_gnd"], R["probe_pin_d"] / 2, "t_gnd+head_z0", name="pin", material="copper")
    head = h.modeler.create_cylinder("Z", [0, 0, "head_z0"], "head_d/2", "head_h", name="head", material="copper")
    h.modeler.unite([pin.name, head.name])
    ptfe = h.modeler.create_cylinder("Z", [0, 0, "-t_gnd"], R["sma_ptfe_d"] / 2, "t_gnd", name="ptfe", material="Teflon (tm)")
    h.modeler.subtract("ground", [ptfe.name], keep_originals=True); h.modeler.subtract(ptfe.name, [pin.name], keep_originals=True)
    port_face = h.modeler.create_circle("XY", [0, 0, "-t_gnd"], R["sma_ptfe_d"] / 2, name="port_face")
    h.wave_port(port_face.name, reference="ground", name="P1")
    if own:
        air = h.modeler.create_cylinder("Z", [0, 0, "-t_gnd-4mm"], rd + 4, "t_gnd+h_air+h_d+8mm", name="rad", material="vacuum")
        h.assign_radiation_boundary_to_objects(air.name)
        s = h.create_setup("S20", Frequency="20GHz", MaximumPasses=8, MaximumDeltaS=0.02)
        s.create_frequency_sweep(unit="GHz", start_frequency=18, stop_frequency=21, num_of_freq_points=61, sweep_type="Interpolating", name="band")
        h.insert_infinite_sphere(x_start=-90, x_stop=90, x_step=0.5, y_start=0, y_stop=90, y_step=90, name="cuts")
        h.save_project()
        print("Check (guide sec. 8): |S11| < -10 dB 18-21 GHz (Fig. 18), D ~ 34 dBic at 20.1 GHz (Fig. 10), AR < 1 dB, Ey phase 15 mm above (Fig. 12a).")
    return h

def hm(h, which, psi, z0):
    b = G.board_hm(which, CL.library())
    nm = "HM%d" % which; t = CL.T_LAM
    disc = h.modeler.create_cylinder("Z", [0, 0, z0], G.H["D_diel"] / 2, 3 * t, name=nm + "_diel", material="TLY5_nfms")
    holes = [h.modeler.create_cylinder("Z", [x, y, z0], d / 2, 3 * t, name="%s_h%04d" % (nm, k), material="vacuum").name
             for k, (lay, x, y, d, n) in enumerate(b.holes) if lay == "DRILL"]
    if holes: h.modeler.subtract(disc.name, holes, keep_originals=False)
    for k, lay in enumerate(("M1", "M2", "M3", "M4")):
        sh = [poly_sheet(h, p, z0 + k * t, "%s_%s_%04d" % (nm, lay, n)).name for n, p in enumerate(b.L[lay])]
        u = h.modeler.unite(sh) if len(sh) > 1 else sh[0]
        h.assign_perfecte_to_sheets([sh[0]], name="PEC_%s_%s" % (nm, lay))
    objs = [o for o in h.modeler.object_names if o.startswith(nm)]
    h.modeler.rotate(objs, "Z", psi)
    return h

def system(psi1, psi2):
    h = open_hfss("NFMS_psi1_%g_psi2_%g" % (psi1, psi2), "Terminal")
    rlsa(h)
    z1 = G.R["Wh"] + G.H["gap_rlsa"]; z2 = z1 + G.H["t"] + G.H["gap_hm"]
    hm(h, 1, psi1, z1); hm(h, 2, psi2, z2)
    air = h.modeler.create_cylinder("Z", [0, 0, -G.R["t_ground"] - 4], G.H["D_diel"] / 2 + 5, z2 + G.H["t"] + G.R["t_ground"] + 12, name="rad", material="vacuum")
    h.assign_radiation_boundary_to_objects(air.name)
    s = h.create_setup("S20", Frequency="20GHz", MaximumPasses=6, MaximumDeltaS=0.03)
    s.create_frequency_sweep(unit="GHz", start_frequency=19, stop_frequency=20.5, num_of_freq_points=7, sweep_type="Discrete", name="pts")
    h.insert_infinite_sphere(x_start=-60, x_stop=60, x_step=0.5, y_start=0, y_stop=180, y_step=15, name="hemi")
    h.save_project()
    import nfms_study as S
    p = S.K0 * math.sin(math.radians(G.H["theta0"])); th, ph = S.beam(p, p, psi1, psi2)
    print("Expected beam (eqs. 1, 6): theta %.1f deg, phi %.1f deg" % (th, ph))
    return h

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "cell1"
    if arg == "cell1": unit_cell(1)
    elif arg == "cell2": unit_cell(2)
    elif arg == "rlsa": rlsa()
    elif arg == "system": system(float(sys.argv[2]), float(sys.argv[3]))
    else: print(__doc__)
