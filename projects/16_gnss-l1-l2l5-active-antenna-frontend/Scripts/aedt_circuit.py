"""PyAEDT automation: build, run and save the ANSYS Electronics Desktop Circuit project.

    python aedt_circuit.py [--version 2026.1] [--gui]

Creates ../ANSYS_Project/GNSS_L1_L2L5_FrontEnd.aedt with designs "FrontEnd_3port" and "SBand_2port":
  * imports every Touchstone model from ../Touchstone (LNA table, HC125A, B7504, B8889, DXP.02.A,
    ideal RHCP patch feed),
  * places them on a schematic in two rows (L1 branch on top, L2/L5 below) plus the DXP combiner,
  * adds the LNA bias networks (100 pF DC blocks with ESL/ESR, 18 nH choke, 100 pF + 1 uF bypass,
    +5 V VDD source), 50 ohm terminations and grounds,
  * connects everything (wires where possible, page ports otherwise),
  * adds 3 interface ports (P1 L1 RHCP in, P2 L2/L5 RHCP in, P3 RF out),
  * creates a Nexxim linear network analysis 0.6-2.2 GHz (3201 points), runs it, exports
    ../ANSYS_Project/AEDT_System_3port.s3p and dB(S) reports, and saves the project.
Requires AEDT (tested target 2026 R1) and pyaedt >= 0.10 (package ansys-aedt-core / pyaedt 1.x).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ansys.aedt.core import Circuit

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "Touchstone"
OUT = ROOT / "ANSYS_Project"
OUT.mkdir(exist_ok=True)

DX = 1200          # schematic step between blocks (mil)
ROW = {"L1": 0, "L2": -4000}


def connect(a, b):
    """Wire two pins; fall back to a page-port pair (same net name) if routing fails."""
    try:
        if a.connect_to_component(b, use_wire=True):
            return
    except Exception:
        pass
    a.connect_to_component(b, use_wire=False)


def build(cir: Circuit):
    sch = cir.modeler.schematic
    # make sure lumped parameters are in SI with units
    def cap(name, val, x, y, ang=0):
        return sch.create_capacitor(name=name, value=val, location=[x, y], angle=ang)

    def ind(name, val, x, y, ang=0):
        return sch.create_inductor(name=name, value=val, location=[x, y], angle=ang)

    def res(name, val, x, y, ang=0):
        return sch.create_resistor(name=name, value=val, location=[x, y], angle=ang)

    def gnd_at(pin):
        g = sch.create_gnd(location=[pin.location[0], pin.location[1] - 300])
        connect(pin, g.pins[0])

    def snp(fname, x, y):
        return sch.create_touchstone_component(str(TS / fname), location=[x, y])

    vdd = sch.create_voltage_dc(name="VDD", value=5, location=[-2 * DX, 2500])
    gnd_at(vdd.pins[1] if len(vdd.pins) > 1 else vdd.pins[0])
    vdd_pin = vdd.pins[0]

    def lna_stage(tag, x, y, prev_pin):
        c1 = cap(f"C1_{tag}", "100pF", x, y)
        connect(prev_pin, c1.pins[0])
        lna = snp("TQP3M9037_5V.s2p", x + DX, y)
        connect(c1.pins[1], lna.pins[0])
        for extra in lna.pins[2:]:
            gnd_at(extra)
        # bias tee: choke from LNA output to VDD rail, bypassed by 100 pF + 1 uF
        l1 = ind(f"L1_{tag}", "18nH", x + 2 * DX, y + 800, ang=90)
        connect(lna.pins[1], l1.pins[0])
        c3 = cap(f"C3_{tag}", "100pF", x + 2.6 * DX, y + 1500, ang=90)
        c4 = cap(f"C4_{tag}", "1uF", x + 3.2 * DX, y + 1500, ang=90)
        connect(l1.pins[1], c3.pins[0])
        connect(c3.pins[0], c4.pins[0])
        gnd_at(c3.pins[1])
        gnd_at(c4.pins[1])
        connect(l1.pins[1], vdd_pin)
        c2 = cap(f"C2_{tag}", "100pF", x + 3 * DX, y)
        connect(lna.pins[1], c2.pins[0])
        return c2.pins[1]

    out_pins = {}
    for br, saw in (("L1", "B7504.s2p"), ("L2", "B8889_matched.s2p")):
        y = ROW[br]
        port = sch.create_interface_port(f"P{1 if br == 'L1' else 2}_{br}_RHCP", location=[-3 * DX, y])
        cp = snp("PatchCP_ideal_RHCP_feed.s4p", -2 * DX, y)
        connect(port.pins[0], cp.pins[0])
        r_lh = res(f"R_LHCP_{br}", 50, -2 * DX, y - 900, ang=90)
        connect(cp.pins[1], r_lh.pins[0]); gnd_at(r_lh.pins[1])
        hyb = snp("HC125A.s4p", 0, y)
        connect(cp.pins[2], hyb.pins[2])
        connect(cp.pins[3], hyb.pins[3])
        r_iso = res(f"R_ISO_{br}", 50, 0, y - 900, ang=90)
        connect(hyb.pins[1], r_iso.pins[0]); gnd_at(r_iso.pins[1])
        for comp in (cp, hyb):
            for extra in comp.pins[4:]:
                gnd_at(extra)
        p = lna_stage(f"{br}A", DX, y, hyb.pins[0])
        s1 = snp(saw, 5 * DX, y)
        connect(p, s1.pins[0])
        p = lna_stage(f"{br}B", 6 * DX, y, s1.pins[1])
        s2 = snp(saw, 10 * DX, y)
        connect(p, s2.pins[0])
        for comp in (s1, s2):
            for extra in comp.pins[2:]:
                gnd_at(extra)
        out_pins[br] = s2.pins[1]

    dxp = snp("DXP02A.s3p", 12 * DX, (ROW["L1"] + ROW["L2"]) / 2)
    connect(out_pins["L1"], dxp.pins[1])
    connect(out_pins["L2"], dxp.pins[2])
    for extra in dxp.pins[3:]:
        gnd_at(extra)
    pout = sch.create_interface_port("P3_RF_OUT", location=[13.5 * DX, (ROW["L1"] + ROW["L2"]) / 2])
    connect(dxp.pins[0], pout.pins[0])


def build_sband(cir: Circuit):
    """S-band branch: patch -> C2327J5003AHF -> LNA (Qorvo 2.3-2.6 GHz ref. design) -> TA1442A -> LNA -> TA1442A."""
    sch = cir.modeler.schematic

    def gnd_at(pin):
        connect(pin, sch.create_gnd(location=[pin.location[0], pin.location[1] - 300]).pins[0])

    def snp(fname, x, y):
        return sch.create_touchstone_component(str(TS / fname), location=[x, y])

    vdd = sch.create_voltage_dc(name="VDD_S", value=5, location=[-2 * DX, 2500])
    gnd_at(vdd.pins[1] if len(vdd.pins) > 1 else vdd.pins[0])
    port = sch.create_interface_port("P1_S_RHCP", location=[-3 * DX, 0])
    cp = snp("PatchCP_ideal_RHCP_feed.s4p", -2 * DX, 0)
    connect(port.pins[0], cp.pins[0])
    r1 = sch.create_resistor(name="R_LHCP_S", value=50, location=[-2 * DX, -900], angle=90)
    connect(cp.pins[1], r1.pins[0]); gnd_at(r1.pins[1])
    hyb = snp("C2327J5003AHF.s4p", 0, 0)          # 1 in, 2 iso, 3 coupled, 4 direct
    connect(cp.pins[2], hyb.pins[3])
    connect(cp.pins[3], hyb.pins[2])
    r2 = sch.create_resistor(name="R_ISO_S", value=50, location=[0, -900], angle=90)
    connect(hyb.pins[1], r2.pins[0]); gnd_at(r2.pins[1])
    for comp in (cp, hyb):
        for extra in comp.pins[4:]:
            gnd_at(extra)
    prev = hyb.pins[0]
    x = DX
    for tag in ("SA", "SB"):
        l2 = sch.create_inductor(name=f"L2_{tag}", value="2.7nH", location=[x, -800], angle=90)
        connect(prev, l2.pins[0]); gnd_at(l2.pins[1])
        c5 = sch.create_capacitor(name=f"C5_{tag}", value="2.4pF", location=[x + 0.6 * DX, 0])
        connect(prev, c5.pins[0])
        lna = snp("TQP3M9037_5V.s2p", x + 1.6 * DX, 0)
        connect(c5.pins[1], lna.pins[0])
        for extra in lna.pins[2:]:
            gnd_at(extra)
        l1 = sch.create_inductor(name=f"L1_{tag}", value="5.6nH", location=[x + 2.6 * DX, 800], angle=90)
        connect(lna.pins[1], l1.pins[0])
        c3 = sch.create_capacitor(name=f"C3_{tag}", value="100pF", location=[x + 3.2 * DX, 1500], angle=90)
        connect(l1.pins[1], c3.pins[0]); gnd_at(c3.pins[1]); connect(l1.pins[1], vdd.pins[0])
        c2 = sch.create_capacitor(name=f"C2_{tag}", value="100pF", location=[x + 3.6 * DX, 0])
        connect(lna.pins[1], c2.pins[0])
        saw = snp("TA1442A.s2p", x + 5 * DX, 0)
        connect(c2.pins[1], saw.pins[0])
        for extra in saw.pins[2:]:
            gnd_at(extra)
        prev = saw.pins[1]
        x += 6.5 * DX
    pout = sch.create_interface_port("P2_S_OUT", location=[x, 0])
    connect(prev, pout.pins[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="2026.1")
    ap.add_argument("--gui", action="store_true")
    args = ap.parse_args()

    project = OUT / "GNSS_L1_L2L5_FrontEnd.aedt"
    cir = Circuit(project=str(project), design="FrontEnd_3port", version=args.version,
                  non_graphical=not args.gui, new_desktop=True, close_on_exit=True, remove_lock=True)
    try:
        build(cir)
        setup = cir.create_setup("SP_0p6_2p2GHz", setup_type="NexximLNA")
        setup.props["SweepDefinition"]["Data"] = "LINC 0.6GHz 2.2GHz 3201"
        setup.update()
        cir.save_project()
        ok = cir.analyze(setup="SP_0p6_2p2GHz")
        ports = list(cir.excitation_names)
        exprs = []
        for a in ports:
            for b in ports:
                exprs.append(f"dB(S({a},{b}))")
        cir.post.create_report(exprs, setup_sweep_name="SP_0p6_2p2GHz", plot_name="S-parameters (dB)")
        gains = [e for e in exprs if "P3_RF_OUT," in e and "P3_RF_OUT,P3" not in e]
        cir.post.create_report(gains, setup_sweep_name="SP_0p6_2p2GHz", plot_name="Branch gain")
        ts = cir.export_touchstone(setup="SP_0p6_2p2GHz", output_file=str(OUT / "AEDT_System_3port.s3p"))
        cir.save_project()
        (OUT / "aedt_run.json").write_text(json.dumps(
            {"analyze_ok": bool(ok), "ports": ports, "touchstone": str(ts), "version": args.version}, indent=1))
        print("analyze:", ok, "ports:", ports, "touchstone:", ts)
        # second design in the same project: S-band branch
        cs = Circuit(project=cir.project_name, design="SBand_2port")
        build_sband(cs)
        su = cs.create_setup("SP_SBand", setup_type="NexximLNA")
        su.props["SweepDefinition"]["Data"] = "LINC 0.5GHz 4GHz 7001"
        su.update()
        ok_s = cs.analyze(setup="SP_SBand")
        cs.post.create_report(["dB(S(P2_S_OUT,P1_S_RHCP))", "dB(S(P1_S_RHCP,P1_S_RHCP))", "dB(S(P2_S_OUT,P2_S_OUT))"],
                              setup_sweep_name="SP_SBand", plot_name="S-band S-parameters (dB)")
        ts_s = cs.export_touchstone(setup="SP_SBand", output_file=str(OUT / "AEDT_SBand_2port.s2p"))
        cs.save_project()
        print("S-band analyze:", ok_s, "touchstone:", ts_s)
    finally:
        cir.release_desktop(close_projects=True, close_desktop=True)


if __name__ == "__main__":
    main()
