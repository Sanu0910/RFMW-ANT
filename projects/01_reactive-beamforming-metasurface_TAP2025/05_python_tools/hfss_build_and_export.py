"""PyAEDT automation for the reactive beamforming metasurface (run on the PC with Ansys HFSS).

    pip install ansys-aedt-core            (PyAEDT >= 0.10)
    python hfss_build_and_export.py array      # build 11x11, 121 lumped ports, solve, export Z + far fields
    python hfss_build_and_export.py meander    # Zin(L) of open meander stubs -> meander_Zin_table.csv
    python hfss_build_and_export.py verify designI_loads.csv   # put optimised X as lumped RLC, solve

Written against the ansys.aedt.core API; it has NOT been executed here (no HFSS licence). PyAEDT
renames keyword arguments between releases - if a call fails, the GUI steps in
06_docs/DESIGN_GUIDE.md section 6 do the same thing by hand.
Geometry parameters are imported from msgeom.py so HFSS, the DXFs and MATLAB stay consistent."""
import os, sys, csv, re, math
import msgeom as g

AEDT_VERSION = "2024.2"
F0 = "10GHz"
OUT = os.path.abspath("hfss_out"); os.makedirs(OUT, exist_ok=True)
Z_STRIP, Z_GND, Z_PATCH = 0.0, g.H2, g.H2 + g.H1      # strip on bottom, ground in middle, patch on top

def open_hfss(name):
    from ansys.aedt.core import Hfss
    h = Hfss(project=os.path.join(OUT, name + ".aedt"), design=name, solution_type="Modal",
             version=AEDT_VERSION, non_graphical=False, new_desktop=True)
    h.modeler.model_units = "mm"
    m = h.materials.add_material("RO4003C_ms")
    m.permittivity = g.ER; m.dielectric_loss_tangent = g.TAND
    return h

def stack(h, half):
    """Substrates, full ground sheet, radiation box (lambda/4 = 7.5 mm clearance)."""
    h.modeler.create_box([-half, -half, Z_STRIP], [2*half, 2*half, g.H2], name="sub_low", material="RO4003C_ms")
    h.modeler.create_box([-half, -half, Z_GND], [2*half, 2*half, g.H1], name="sub_top", material="RO4003C_ms")
    gnd = h.modeler.create_rectangle("XY", [-half, -half, Z_GND], [2*half, 2*half], name="GND")
    pad = 7.5
    air = h.modeler.create_box([-half-pad, -half-pad, Z_STRIP-pad], [2*(half+pad), 2*(half+pad), g.H1+g.H2+2*pad],
                               name="Air", material="air")
    h.assign_radiation_boundary_to_objects(air.name, name="Rad")
    return gnd

def cell(h, r, c, gnd_slots, with_port=True, meander_L=None, keep_via_strip=True):
    cx, cy = g.cell_centre(r, c); top = cy + g.P/2; yp = top - g.PORT_IN
    tag = f"{r}_{c}"
    gnd_slots.append(h.modeler.create_rectangle("XY", [cx-g.SL/2, top-g.SW_HALF, Z_GND], [g.SL, 2*g.SW_HALF], name=f"slot_{tag}"))
    y0 = yp if keep_via_strip else yp
    y1 = top + g.VIA_EXT if keep_via_strip else yp + 0.02
    strips = [h.modeler.create_rectangle("XY", [cx-g.MSW/2, y0, Z_STRIP], [g.MSW, y1-y0], name=f"strip_{tag}")]
    if meander_L:
        pts, _ = g.meander_path(meander_L, cx, yp)
        poly = g.thick(pts)
        xyz = [[x, y, Z_STRIP] for x, y in list(poly.exterior.coords)]
        strips.append(h.modeler.create_polyline(xyz, cover_surface=True, close_surface=True, name=f"mndr_{tag}"))
    if len(strips) > 1: h.modeler.unite(strips)
    h.assign_perfecte_to_sheets(strips[0].name, name=f"PEC_{tag}")
    if keep_via_strip:
        vx, vy = g.cell_features(r, c)["via"]
        h.modeler.create_cylinder("Z", [vx, vy, Z_STRIP], g.VIA_D/2, g.H2, name=f"via_{tag}", material="pec")
    port = None
    if with_port:   # vertical sheet strip -> ground at the port plane (XZ plane)
        port = h.modeler.create_rectangle("XZ", [cx-g.MSW/2, yp, Z_STRIP], [g.H2, g.MSW], name=f"psheet_{tag}")
    return port

def lumped(h, sheet, name):
    x = sheet.bounding_box; xc = (x[0]+x[3])/2; y = x[1]
    line = [[xc, y, Z_STRIP], [xc, y, Z_GND]]
    try:
        return h.lumped_port(assignment=sheet.name, integration_line=line, impedance=50, name=name, renormalize=True)
    except TypeError:   # older PyAEDT keyword names
        return h.lumped_port(sheet.name, integration_line=line, impedance=50, name=name)

def build_array(loads=None):
    """loads: dict (r,c)->X ohm -> lumped RLC on those sheets instead of ports (verification run)."""
    h = open_hfss("MTS_array" if loads is None else "MTS_verify")
    half = 6*g.P + 1.0
    gnd = stack(h, half)
    for i in range(12):
        for j in range(12):
            x = (j-5.5)*g.P; y = (5.5-i)*g.P
            p = h.modeler.create_rectangle("XY", [x-g.PATCH/2, y-g.PATCH/2, Z_PATCH], [g.PATCH, g.PATCH], name=f"patch_{i}_{j}")
            h.assign_perfecte_to_sheets(p.name, name=f"PECp_{i}_{j}")
    slots = []; ports = {}
    for r in range(1, 12):
        for c in range(1, 12):
            ports[(r, c)] = cell(h, r, c, slots)
    h.modeler.subtract(gnd.name, [s.name for s in slots], keep_originals=False)
    h.assign_perfecte_to_sheets("GND", name="PEC_GND")
    for (r, c), sh in ports.items():
        m = (r-1)*11 + c
        if loads is not None and (r, c) in loads:
            X = loads[(r, c)]; w = 2*math.pi*10e9
            kw = {"inductance": X/w} if X >= 0 else {"capacitance": -1/(w*X)}
            h.assign_lumped_rlc_to_sheet(sh.name, start_direction=h.axis_directions.ZPos if hasattr(h,"axis_directions") else 2,
                                         rlc_type="Series", name=f"Load_{r}_{c}", **kw)
        else:
            lumped(h, sh, f"P{m:03d}")
    h.insert_infinite_sphere(x_start=0, x_stop=180, x_step=2, y_start=0, y_stop=356, y_step=4, name="FF")
    s = h.create_setup("Setup1"); s.props["Frequency"] = F0; s.props["MaximumPasses"] = 15; s.props["MaxDeltaS"] = 0.01
    s.update()
    h.save_project()
    return h

def export_all(h):
    h.analyze_setup("Setup1")
    h.export_touchstone(setup="Setup1", sweep="LastAdaptive", output_file=os.path.join(OUT, "metasurface_121port.s121p"))
    expr = ["re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)"]
    rep = h.post.create_report(expressions=expr, setup_sweep_name="Setup1 : LastAdaptive", report_category="Far Fields",
                               context="FF", primary_sweep_variable="Theta", plot_type="Data Table", plot_name="FFtab",
                               variations={"Theta": ["All"], "Phi": ["All"], "Freq": [F0]})
    ff = os.path.join(OUT, "ff"); os.makedirs(ff, exist_ok=True)
    ports = sorted(h.excitations)
    for k, p in enumerate(ports, 1):     # drive one port (1 W), others terminated in 50 ohm (HFSS default)
        h.edit_sources({q + ":1": ("1W" if q == p else "0W", "0deg") for q in ports})
        raw = h.post.export_report_to_csv(ff, "FFtab")
        to_mtsf_csv(raw, os.path.join(ff, f"port_{int(p[1:]):03d}.csv"))
    print("Exported Z-matrix and", len(ports), "embedded patterns to", OUT)

UNIT = {"V": 1.0, "mV": 1e-3, "uV": 1e-6, "kV": 1e3}
def to_mtsf_csv(raw, out):
    """HFSS data-table CSV -> Theta_deg,Phi_deg,Re_rETheta,Im_rETheta,Re_rEPhi,Im_rEPhi (volts)."""
    with open(raw) as fh:
        rd = csv.reader(fh); hdr = next(rd); rows = [list(map(float, r)) for r in rd if r]
    def col(key):
        for i, hname in enumerate(hdr):
            if key.lower() in hname.lower().replace(" ", ""):
                u = re.search(r"\[(\w+)\]", hname); return i, UNIT.get(u.group(1), 1.0) if u else 1.0
        raise KeyError(key)
    it, _ = col("Theta"); ip, _ = col("Phi")
    cols = [col(k) for k in ("re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)")]
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["Theta_deg", "Phi_deg", "Re_rETheta", "Im_rETheta", "Re_rEPhi", "Im_rEPhi"])
        for r in rows:
            w.writerow([r[it], r[ip]] + [r[i]*s for i, s in cols])

def meander_table(lengths=(1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5)):
    """Zin of the open meander alone at the port plane, inside one cell with ground + slots and
    PERIODIC (master/slave) side walls would be ideal; here: 3x3 cells, centre one measured, the
    8 neighbours carry 50-ohm-terminated ports - close to the in-array environment.
    The via-side strip of the measured cell is removed so the port sees only the stub (as in Fig.10)."""
    rows = [("L_mm", "X_ohm", "R_ohm")]
    for L in lengths:
        h = open_hfss(f"Mndr_{L:.1f}".replace(".", "p"))
        half = 1.5*g.P + 1.0; gnd = stack(h, half); slots = []; sheets = {}
        for r in (5, 6, 7):
            for c in (5, 6, 7):
                centre = (r, c) == (6, 6)
                sheets[(r, c)] = cell(h, r, c, slots, meander_L=L if centre else None, keep_via_strip=not centre)
        h.modeler.subtract(gnd.name, [s.name for s in slots], keep_originals=False)
        h.assign_perfecte_to_sheets("GND", name="PEC_GND")
        for k, ((r, c), sh) in enumerate(sheets.items(), 1):
            lumped(h, sh, "Pmeas" if (r, c) == (6, 6) else f"Pn{k}")
        s = h.create_setup("Setup1"); s.props["Frequency"] = F0; s.update()
        h.analyze_setup("Setup1")
        d = h.post.get_solution_data(expressions=["re(Z(Pmeas,Pmeas))", "im(Z(Pmeas,Pmeas))"], setup_sweep_name="Setup1 : LastAdaptive")
        R = d.data_real("re(Z(Pmeas,Pmeas))")[0]; X = d.data_real("im(Z(Pmeas,Pmeas))")[0]
        rows.append((L, X, R)); h.release_desktop(close_projects=True, close_desktop=False)
    with open(os.path.join(OUT, "meander_Zin_table.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print("Use with: python build_dxf.py realise X.csv out.dxf --table hfss_out/meander_Zin_table.csv")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "array"
    if cmd == "array":
        export_all(build_array())
    elif cmd == "meander":
        meander_table()
    elif cmd == "verify":
        loads = {}
        with open(sys.argv[2]) as fh:
            for row in csv.DictReader(fh): loads[(int(row["row"]), int(row["col"]))] = float(row["X_ohm"])
        h = build_array(loads); h.analyze_setup("Setup1"); h.save_project()
