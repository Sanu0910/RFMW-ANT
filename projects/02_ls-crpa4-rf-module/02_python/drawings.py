"""Drawing set for CRL-LS-CRPA4 (A3 landscape, multi-sheet PDF + one PNG per sheet) -> 07_drawings/.
  1 PCB fabrication (outline, drill map + table, stack-up, notes)   2 Array / interface layout (antenna side)
  3 Assembly, bottom (components)   4 Assembly, top (antennas)   5 Back cover BC01   6 Block diagram + RF summary
Frame for every coordinate: board outline centre, X east, Y north, top view (as the STEP files).
Run after run_drc.sh, make_fab.py, covers.py and rf_budget.py:  python drawings.py
"""
import json, math, os, subprocess, tempfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon as MPoly, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import ls_design as D
import covers as CVm

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
OUTD = os.path.join(PRJ, "07_drawings")
FAB = os.path.join(PRJ, "04_fab")
PCB = os.path.join(PRJ, "03_kicad", "CRL-LS-CRPA4.kicad_pcb")
KIBIN = os.path.join(os.environ.get("KICAD10", r"C:\Program Files\KiCad\10.0"), "bin")
PN = "CRL-LS-CRPA4"
DATE = "06-11-2026"
REV = "A"
INK = "#111"
A3 = (16.54, 11.69)
SHEETS = 6


# ----------------------------------------------------------------------------- helpers
def frame(fig, n, title, part):
    fig.add_artist(Rectangle((0.01, 0.01), 0.98, 0.98, fill=False, lw=1.4, transform=fig.transFigure))
    tb = (0.70, 0.02, 0.28, 0.115)
    fig.add_artist(Rectangle(tb[:2], tb[2], tb[3], fill=False, lw=1.0, transform=fig.transFigure))
    fig.text(tb[0] + 0.008, tb[1] + 0.085, "BEL - CRL", fontsize=13, weight="bold")
    fig.text(tb[0] + 0.008, tb[1] + 0.068, "ANTENNA / RFM LAB", fontsize=7, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.090, "L1 + L2/L5 + NavIC S 4-ch CRPA front end", fontsize=7.6, weight="bold")
    fig.text(tb[0] + 0.105, tb[1] + 0.073, title, fontsize=6.6)
    items = (("PART", part), ("DWG", PN + "-DWG"), ("REV", REV), ("SHEET", f"{n} / {SHEETS}"),
             ("DATE", DATE), ("UNITS", "mm"), ("PROJ.", "1st angle"), ("TOL.", "ISO 2768-mK"))
    for i, (k, v) in enumerate(items):
        fig.text(tb[0] + 0.008 + (i % 4) * 0.069, tb[1] + 0.040 - (i // 4) * 0.028, f"{k}\n{v}", fontsize=5.6)


def notes(fig, x, y, lines, title="NOTES", fs=6.4, dy=0.0165):
    fig.text(x, y, title, fontsize=fs + 1.5, weight="bold")
    for i, t in enumerate(lines):
        fig.text(x, y - (i + 1) * dy, t, fontsize=fs, va="top")


def table(fig, x, y, cols, widths, rows, fs=6.2, rh=0.0175, title=None):
    if title: fig.text(x, y + 0.006, title, fontsize=fs + 1.5, weight="bold")
    for j, c in enumerate([cols] + rows):
        cx = x
        for w, v in zip(widths, c):
            fig.add_artist(Rectangle((cx, y - (j + 1) * rh), w, rh, fill=(j == 0), fc="#e8ecef", ec=INK, lw=0.4,
                                     transform=fig.transFigure))
            fig.text(cx + 0.003, y - (j + 0.5) * rh, str(v), fontsize=fs, va="center", weight="bold" if j == 0 else None)
            cx += w
    return y - (len(rows) + 1) * rh


def dim(ax, p0, p1, off, text, fs=6.5, color=INK):
    """Aligned dimension p0 -> p1, offset 'off' to the left of the direction."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    a = (x0 + nx * off, y0 + ny * off); b = (x1 + nx * off, y1 + ny * off)
    ax.plot([x0, a[0]], [y0, a[1]], lw=0.3, color=color); ax.plot([x1, b[0]], [y1, b[1]], lw=0.3, color=color)
    ax.annotate("", a, b, arrowprops=dict(arrowstyle="<->", lw=0.5, color=color, shrinkA=0, shrinkB=0))
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang < -90: ang += 180
    ax.text((a[0] + b[0]) / 2 + nx * 1.5, (a[1] + b[1]) / 2 + ny * 1.5, text, fontsize=fs, ha="center", va="center",
            rotation=ang, color=color, bbox=dict(fc="white", ec="none", pad=0.3))


def board_ax(fig, rect=(0.03, 0.05, 0.62, 0.9)):
    ax = fig.add_axes(rect); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Circle((0, 0), D.BOARD_RADIUS, fill=False, lw=1.0, ec=INK))
    ax.plot([-6, 6], [0, 0], lw=0.5, color=INK); ax.plot([0, 0], [-6, 6], lw=0.5, color=INK)
    ax.text(1.5, -4.5, "DATUM 0,0\n(outline centre)", fontsize=5.5)
    ax.set_xlim(-118, 118); ax.set_ylim(-118, 118)
    return ax


def holes():
    """All drilled holes from the board (KiCad python): x, y (frame), drill, plated, kind."""
    code = f'''
import pcbnew, json
b = pcbnew.LoadBoard(r"{PCB}")
out = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSizeX() > 0:
            q = p.GetPosition()
            out.append([pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), round(pcbnew.ToMM(p.GetDrillSizeX()), 3),
                        p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH, fp.GetReference()])
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        q = t.GetPosition()
        out.append([pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), round(pcbnew.ToMM(t.GetDrillValue()), 3), True, "VIA"])
json.dump(out, open(r"{os.path.join(FAB, '_holes.json')}", "w"))
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(code)
    subprocess.run([os.path.join(KIBIN, "python.exe"), fh.name], check=True)
    os.remove(fh.name)
    return [(*CVm.bxy(x, y), d, pl, r) for x, y, d, pl, r in json.load(open(os.path.join(FAB, "_holes.json")))]


def kicad_layers_png(layers, mirror, name):
    pdf = os.path.join(tempfile.gettempdir(), name + ".pdf")
    args = [os.path.join(KIBIN, "kicad-cli.exe"), "pcb", "export", "pdf", "--mode-single", "-o", pdf, "--layers", layers,
            "--black-and-white", "--drill-shape-opt", "0", "--sp", "--scale", "0"]
    if mirror: args.append("--mirror")
    subprocess.run(args + [PCB], check=True, capture_output=True)
    import pymupdf
    doc = pymupdf.open(pdf); pg = doc[0]
    # crop to the board (KiCad plots at 1:1 on its page; find the drawn area)
    bb = pg.get_text("blocks") and None
    pix = pg.get_pixmap(dpi=400)
    png = os.path.join(tempfile.gettempdir(), name + ".png"); pix.save(png); doc.close(); os.remove(pdf)
    im = plt.imread(png)
    g = im[..., :3].mean(axis=2) if im.ndim == 3 else im
    ys, xs = np.where(g < 0.9)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


# ----------------------------------------------------------------------------- sheet 1: PCB fabrication
def sheet_fab(pdf, H):
    fig = plt.figure(figsize=A3); frame(fig, 1, "PCB fabrication drawing (top view)", PN + " PCB")
    ax = board_ax(fig)
    groups = {}
    for x, y, d, pl, r in H:
        groups.setdefault((d, pl), []).append((x, y))
    marks = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "<", ">", "p", "8", "d"]
    rows = []
    for i, ((d, pl), pts) in enumerate(sorted(groups.items())):
        m = marks[i % len(marks)]
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=4 if d < 0.5 else 9, marker=m, facecolors="none", edgecolors=INK, linewidths=0.35)
        rows.append([m, f"{d:.2f}", "PTH" if pl else "NPTH", len(pts), "vias" if d <= 0.30 else ""])
    dim(ax, (-100, -103), (100, -103), -6, "D200.0 +0/-0.2 (outline)")
    ax.text(-100, 108, "Holes shown with the drill symbol of the table; via fence and stitching vias D0.30 / D0.25.",
            fontsize=6)
    y = table(fig, 0.66, 0.95, ["SYM", "DRILL", "TYPE", "QTY", "NOTE"], [0.03, 0.04, 0.04, 0.035, 0.05], rows,
              title="DRILL TABLE (finished hole, mm)")
    st = [[n, t, f"{th:.3f}", "" if er is None else er, note[:44]] for n, t, th, er, note in D.STACKUP if th or t == "copper"]
    y = table(fig, 0.66, y - 0.03, ["LAYER", "TYPE", "mm", "er", "NOTE"], [0.05, 0.04, 0.035, 0.025, 0.17], st, fs=5.6,
              rh=0.0155, title=f"STACK-UP ({D.BOARD_THICKNESS} mm, order exactly this)")
    notes(fig, 0.66, y - 0.025, [
        "1. IPC-6012 / IPC-A-600 Class 2 (Class 3 if airborne). UL 94V-0. RoHS.",
        "2. FR-4 high Tg >= 170 C (IT-180A / S1000-2) + Rogers RO4350B 0.168 mm core, 1 oz. Plasma desmear.",
        f"3. 50 ohm +-10 % on L4: {D.RF_W} mm track over L3 (RO4350B), with mask. TDR coupon on the panel.",
        "4. ENIG. Green LPI mask, white legend both sides. No mask on the shield-frame GND lands (gasket).",
        "5. Vias in pads (D0.25 / 0.50) resin filled and capped, IPC-4761 Type VII. Annular ring >= 0.125.",
        "6. Track / space >= 0.15 / 0.15 mm. Copper to board edge >= 0.5 mm.",
        "7. Bow and twist <= 0.5 %. 100 % electrical test against CRL-LS-CRPA4.d356.",
        "8. Data: CRL-LS-CRPA4_Gerbers.zip (Gerber X2 + Excellon), drill map, IPC-D-356.",
    ], fs=6.0)
    pdf.savefig(fig); fig.savefig(os.path.join(OUTD, f"{PN}_sheet1.png"), dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------- sheet 2: array / interface
def sheet_array(pdf):
    fig = plt.figure(figsize=A3); frame(fig, 2, "Array and interface layout (antenna side, top view)", PN)
    ax = board_ax(fig)
    P = {p["ref"]: p for p in json.load(open(os.path.join(FAB, "_parts.json")))}
    Lc, Sc = [], []
    for k in range(4):
        x, y = CVm.bxy(P[f"ANT{k + 1}"]["x"], P[f"ANT{k + 1}"]["y"]); Lc.append((x, y))
        ax.add_patch(Rectangle((x - 32, y - 32), 64, 64, fill=False, lw=0.8, ec="#1f4e79"))
        ax.add_patch(Circle((x, y), 1.0, color="#1f4e79"))
        ax.text(x, y + 14, f"CH{k + 1}  L1/L2 patch\nGPDF6010.A", ha="center", fontsize=6.5, color="#1f4e79", weight="bold")
        for dx, dy in ((-29, 0), (29, 0), (0, -29), (0, 29)):
            ax.add_patch(Circle((x + dx, y + dy), D.ANT_MOUNT_DRILL / 2, fill=False, lw=0.5))
    sants = sorted([r for r in P if P[r]["key"] == "SANT"])
    for r in sants:
        x, y = CVm.bxy(P[r]["x"], P[r]["y"]); Sc.append((x, y))
        ax.add_patch(Rectangle((x - 12.5, y - 12.5), 25, 25, fill=False, lw=0.8, ec="#c0392b"))
        ax.text(x, y, f"{P[r]['ch']} S\nCRL-LS-SP01", ha="center", va="center", fontsize=6, color="#c0392b", weight="bold")
    acx, acy = CVm.bxy(*D.ARRAY_CENTER)
    ax.add_patch(Circle((acx, acy), D.S_RADIUS, fill=False, lw=0.4, ls="--", ec="#c0392b"))
    dim(ax, Lc[0], Lc[1], 40, f"{D.ELEMENT_PITCH:.1f} (L pitch, 0.48 lambda @L1)")
    Ss = sorted(Sc, key=lambda p: math.atan2(p[1] - acy, p[0] - acx))
    dim(ax, Ss[0], Ss[1], -4, f"{D.S_SPACING:.2f} = lambda/2 @2492.028", color="#c0392b")
    ax.text(acx + 2, acy + D.S_RADIUS + 1.5, f"S on R{D.S_RADIUS:.2f}", fontsize=6, color="#c0392b")
    for r in P:
        if r.startswith("J") and r != "J5":
            x, y = CVm.bxy(P[r]["x"], P[r]["y"])
            ax.add_patch(Circle((x, y), 3.2, fill=False, lw=0.6, ls=":", ec="#555"))
            ax.text(x, y - 5, r + f"\nR{math.hypot(x, y):.1f}", ha="center", va="top", fontsize=5.5, color="#555")
    jx, jy = CVm.bxy(P["J5"]["x"], P["J5"]["y"])
    ax.add_patch(Rectangle((jx - 4, jy - 4), 8, 8, fill=False, lw=0.6, ls=":", ec="#555"))
    ax.text(jx, jy + 5.5, "J5 +5V (bottom)", ha="center", fontsize=5.5, color="#555")
    rows = []
    for k, (x, y) in enumerate(Lc): rows.append([f"CH{k + 1} L patch", f"{x:+.2f}", f"{y:+.2f}", f"{math.hypot(x - acx, y - acy):.2f}"])
    for r, (x, y) in zip(sants, Sc): rows.append([f"{P[r]['ch']} S patch", f"{x:+.2f}", f"{y:+.2f}", f"{math.hypot(x - acx, y - acy):.2f}"])
    for r in sorted(P):
        if r.startswith("J"):
            x, y = CVm.bxy(P[r]["x"], P[r]["y"]); rows.append([r + (" SMA" if r != "J5" else " DC"), f"{x:+.2f}", f"{y:+.2f}", "-"])
    y = table(fig, 0.66, 0.95, ["ITEM", "X", "Y", "R array"], [0.075, 0.05, 0.05, 0.05], rows, title="POSITIONS (frame above)")
    notes(fig, 0.66, y - 0.03, [
        f"1. Array centre ({acx:+.3f}, {acy:+.3f}) from the customer board combine_model_2.0.",
        "2. Sequential rotation: element k is element 0 turned -90 deg x k about the array centre.",
        "3. L patches: 4 x M3 through D3.6 PTH GND at +-29 mm; centre screw D3.2 grounded.",
        f"4. S patches CRL-LS-SP01 (BEL CRL): <= 25 x 25 mm, 4 pins D{D.S_FEED_DRILL} on R{D.S_FEED_R:.0f},",
        "   centre D2.2 GND; feeds F0 (+x, N element) -> hybrid pin 4, F90 (-y) -> pin 6 = RHCP.",
        "5. Dotted: parts on the bottom side (SMA, DC) shown for reference.",
        "6. 8-element growth path: see the project notes (D260-280 mm board or smaller patches).",
    ])
    pdf.savefig(fig); fig.savefig(os.path.join(OUTD, f"{PN}_sheet2.png"), dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------- sheets 3/4: assembly
def sheet_assy(pdf, n, side):
    fig = plt.figure(figsize=A3)
    frame(fig, n, f"Assembly drawing, {'bottom (component side, viewed from below)' if side == 'B' else 'top (antenna side)'}", PN + " PCA")
    im = kicad_layers_png(f"{side}.Fab,{side}.Silkscreen,Edge.Cuts", side == "B", f"assy_{side}")
    ax = fig.add_axes((0.02, 0.04, 0.66, 0.92)); ax.imshow(im); ax.axis("off")
    if side == "B":
        lines = ["1. All SMD parts on the bottom (L4). Reflow SAC305, type 4 paste, 0.10-0.12 mm stencil.",
                 "2. B7504 / B8889 MSL3: bake per J-STD-033 if exposed > 168 h. TA1442A peak 260 C, ESD sensitive.",
                 "3. THT after reflow: 8 x SMA Amphenol 132134, J5 Micro-Fit (selective / hand solder).",
                 "4. No flux residue on SAW lids. 100 % AOI; X-ray of the DFN-8, DL1721 and SAW ground pads.",
                 "5. Keep the exposed shield-frame lands free of solder, flux and coating (gasket seat).",
                 "6. Reference designators: CH n blocks repeat with sequential rotation; see BOM for values.",
                 "7. Parts list: CRL-LS-CRPA4_BOM.xlsx (40 lines, 313 placements); CPL: _CPL_bottom.csv."]
    else:
        lines = ["1. Fit after bottom-side assembly and test.",
                 "2. 4 x GPDF6010.A L1/L2 patches: M3 through the D3.6 holes into the back cover bosses.",
                 "3. 4 x CRL-LS-SP01 NavIC S patches: pins through D0.77, solder from the bottom; centre D2.2 GND.",
                 "4. Solder the L feed pins (D1.35) from the bottom; trim pins <= 1.0 mm proud.",
                 "5. Top copper L1 is the solid antenna ground plane: no damage, no coating under the patches.",
                 "6. BEL logo and title on the top legend."]
    notes(fig, 0.70, 0.95, lines)
    pdf.savefig(fig); fig.savefig(os.path.join(OUTD, f"{PN}_sheet{n}.png"), dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------- sheet 5: back cover
def sheet_cover(pdf):
    fig = plt.figure(figsize=A3); frame(fig, 5, "Back cover BC01 (L + S), machined", PN + "-BC01")
    walls, tunnels, m3, smas, j5 = CVm.main_geometry()
    C = CVm.CV
    ax = board_ax(fig, (0.02, 0.24, 0.50, 0.72))
    ax.add_patch(Circle((0, 0), C["rim_in"], fill=False, lw=0.6, ls="--"))
    for w in walls:
        for g in (w.geoms if hasattr(w, "geoms") else [w]):
            ax.add_patch(MPoly(list(g.exterior.coords), fc="#c9d0d6", ec=INK, lw=0.3))
            for hole in g.interiors:
                ax.add_patch(MPoly(list(hole.coords), fc="white", ec=INK, lw=0.3))
    for t in tunnels:
        ax.add_patch(MPoly(list(t.exterior.coords), fc="white", ec="#c0392b", lw=0.4))
    for x, y in m3:
        ax.add_patch(Circle((x, y), C["boss_d"] / 2, fc="#dfe3e7", ec=INK, lw=0.4))
        ax.add_patch(Circle((x, y), C["m3_clear"] / 2, fc="white", ec=INK, lw=0.4))
    for x, y in smas:
        ax.add_patch(Circle((x, y), C["sma_hole"] / 2, fc="white", ec="b", lw=0.6))
    dcx, dcy = CVm.bxy(D.ARRAY_CENTER[0] + C["dc_at"][0], D.ARRAY_CENTER[1] + C["dc_at"][1])
    ax.add_patch(Circle((dcx, dcy), C["dc_hole"] / 2, fc="white", ec="g", lw=0.7))
    ax.text(dcx + 6, dcy, "DC D8.2 (M8)", fontsize=6, color="g", va="center")
    dim(ax, (-100, -104), (100, -104), -5, "D200")
    dim(ax, (-C["rim_in"], 104), (C["rim_in"], 104), 5, f"D{2 * C['rim_in']:.0f} pocket edge (rim 3.0)")
    ax.set_title("VIEW FROM THE BOARD SIDE (inside)", fontsize=8)
    # section sketch
    sx = fig.add_axes((0.04, 0.05, 0.46, 0.17)); sx.set_aspect("equal"); sx.axis("off")
    Hh, pk = C["H"], C["pocket"]
    sx.add_patch(Rectangle((0, 0), 60, Hh - pk, fc="#dfe3e7", ec=INK, lw=0.5))          # floor
    sx.add_patch(Rectangle((0, Hh - pk), 3, pk, fc="#dfe3e7", ec=INK, lw=0.5))           # rim
    sx.add_patch(Rectangle((25, Hh - pk), C["wall_w"], pk - C["gasket_gap"], fc="#c9d0d6", ec=INK, lw=0.5))
    sx.add_patch(Rectangle((44, 0), 4.5, Hh - pk, fc="#dfe3e7", ec=INK, lw=0.5))
    sx.add_patch(Rectangle((-2, Hh), 64, 1.6, fc="#7fb069", ec=INK, lw=0.4)); sx.text(30, Hh + 0.8, "PCB 1.6 (B.Cu down)", fontsize=5.5, ha="center", va="center")
    sx.plot([25, 26.2], [Hh - 0.15, Hh - 0.15], lw=2, color="#e67e22"); sx.text(27, Hh - 1.3, "FIP gasket, 0.30 gap", fontsize=5.5, color="#e67e22")
    dim(sx, (62, 0), (62, Hh), -0.0001 - 2, f"{Hh:.1f}", fs=5.5)
    dim(sx, (-3, Hh - pk), (-3, Hh), 0.001 + 2, f"pocket {pk:.1f}", fs=5.5)
    dim(sx, (25, Hh - pk - 0.5), (25 + C["wall_w"], Hh - pk - 0.5), -1.5, f"wall {C['wall_w']}", fs=5.0)
    sx.set_xlim(-12, 72); sx.set_ylim(-4, Hh + 4); sx.set_title("SECTION (schematic, not to scale in X)", fontsize=7)
    for i, (img, tt) in enumerate(((os.path.join(PRJ, "06_step", "CRL-LS-CRPA4-BC01_inside.png"), "ISO, inside"),
                                   (os.path.join(PRJ, "06_step", "CRL-LS-CRPA4-BC01_outside.png"), "outside face"))):
        if os.path.exists(img):
            a = fig.add_axes((0.52, 0.62 - i * 0.30, 0.18, 0.30)); im = plt.imread(img)
            h, w = im.shape[:2]; a.imshow(im[int(h * 0.15):int(h * 0.85), int(w * 0.2):int(w * 0.8)]); a.axis("off"); a.set_title(tt, fontsize=7)
    rows = [["M3 clearance + c'bore", f"D{C['m3_clear']} thru, D{C['m3_cb_d']} x {C['m3_cb_depth']} outside", len(m3)],
            ["SMA opening", f"D{C['sma_hole']} thru, D{C['sma_cb_d']} x {C['sma_cb_depth']} outside", len(smas)],
            ["DC receptacle", f"D{C['dc_hole']} thru (M8 panel)", 1],
            ["RF tunnel under wall", f"{C['tunnel_w']} x {C['tunnel_h']} mm", len(tunnels)],
            ["Boss at M3", f"D{C['boss_d']} to the wall top", len(m3)]]
    y = table(fig, 0.72, 0.95, ["FEATURE", "SIZE", "QTY"], [0.08, 0.14, 0.03], rows, title="FEATURES")
    notes(fig, 0.72, y - 0.03, [
        "1. Material Al 6061-T6. Chromate conversion MIL-DTL-5541 Type II Class 3 (conductive).",
        f"2. Mass {463.7:.0f} g (STEP). STEP: 06_step/CRL-LS-CRPA4-BC01.step, same frame as the PCB STEP.",
        "3. Wall tops = shield-frame lands of the PCB (04_fab/_shield.json); flatness 0.05 over each wall.",
        "4. Form-in-place conductive gasket CHOFORM 5575 [ASSUMED]: 0.8 bead, 0.30 compressed.",
        "5. 16 x ISO 4762 M3 x 12 A2 (cover, board, L patch), 0.9 N m [ASSUMED], cross pattern.",
        "6. Engraving 0.3 deep on the outside face: BEL logo, P/N, date, S/N, channel labels, +5V DC.",
        "7. Break edges 0.2. ISO 2768-mK. Hole positions +-0.05 to datum 0,0.",
        "8. DC receptacle and M2.5 flange holes per the chosen part [ASSUMED type].",
    ])
    pdf.savefig(fig); fig.savefig(os.path.join(OUTD, f"{PN}_sheet5.png"), dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------- sheet 6: block diagram + RF summary
def block(ax, x, y, w, h, txt, fc="#eef3f8"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=INK, lw=0.6))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=6)


def sheet_block(pdf):
    fig = plt.figure(figsize=A3); frame(fig, 6, "Block diagram (one channel, x4) and RF summary", PN)
    ax = fig.add_axes((0.03, 0.42, 0.94, 0.53)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 55)
    rowsdef = [
        (44, "L1/L2 patch\nGPDF6010.A\nL1 feeds", "HC125A\n90 deg hyb", "B7504\nL1 SAW", "L1"),
        (30, "L1/L2 patch\nL2 feeds", "HC125A\n90 deg hyb", "B8889\nL2/L5 SAW", "L2/L5"),
        (12, "S patch\nCRL-LS-SP01", "C2327J5003AHF\n90 deg hyb", "TA1442A\nS SAW", "S"),
    ]
    for y, ant, hyb, saw, b in rowsdef:
        xs = [1, 10.5, 20, 29.5, 39, 48.5, 58, 67.5]
        labels = [ant, hyb, "CLM-83-2W+\nlimiter", "TQP3M9037\nLNA1", saw + " #1", "TQP3M9037\nLNA2", saw + " #2", saw + " #3"]
        for i, (x, t) in enumerate(zip(xs, labels)):
            block(ax, x, y, 7.5, 7, t, fc="#fdecea" if "SAW" in t else ("#eaf5ea" if "LNA" in t else "#eef3f8"))
            if i: ax.annotate("", (x, y + 3.5), (xs[i - 1] + 7.5, y + 3.5), arrowprops=dict(arrowstyle="->", lw=0.6))
        if b != "S":
            ax.annotate("", (82, 37 + 3.5), (75, y + 3.5), arrowprops=dict(arrowstyle="->", lw=0.6))
        else:
            ax.annotate("", (92, y + 3.5), (75, y + 3.5), arrowprops=dict(arrowstyle="->", lw=0.6))
            block(ax, 92, y, 7, 7, "SMA\nCHn S out", fc="#fff8e1")
        ax.text(0.5, y + 8, b + " branch", fontsize=7, weight="bold")
    block(ax, 82, 34, 8, 10, "DXP.02.A\nL1 + L2/L5\ndiplexer", fc="#eef3f8")
    ax.annotate("", (92, 39), (90, 39), arrowprops=dict(arrowstyle="->", lw=0.6)); block(ax, 92, 35.5, 7, 7, "SMA\nCHn L out", fc="#fff8e1")
    ax.text(28, 2, "+5 V (J5, F1, Q1 reverse protection, D1 TVS) -> star bias on In1 to all 24 LNAs (18 nH / 5.6 nH chokes, 100 pF + 1 uF)",
            fontsize=6.5)
    S = json.load(open(os.path.join(PRJ, "05_docs", PN + "_rf_summary.json")))
    rows = [[v["case"], f"{v['gain_db']:.1f}", f"{v['nf_db']:.2f}", f"{v['ip1db_dbm']:.1f}", f"{v['iip3_dbm']:.1f}",
             f"{v['saw_rating_dbm']:.0f}", f"{v['p_ant_saw2_dbm']:.1f}"] for v in S["chains"].values()]
    y = table(fig, 0.04, 0.38, ["CASE", "GAIN dB", "NF dB", "IP1dB dBm", "IIP3 dBm", "SAW max dBm", "P ant -> SAW2 max"],
              [0.16, 0.05, 0.05, 0.06, 0.06, 0.06, 0.08], rows, title="RF SUMMARY (antenna feed -> SMA, 25 C typ; rf_budget.py)")
    p, t = S["power"], S["thermal"]
    notes(fig, 0.04, y - 0.03, [
        f"Power: {p['i_typ_a']:.2f} A typ / {p['i_max_a']:.2f} A max at 5 V = {p['p_typ_w']:.1f} W typ / {p['p_max_w']:.1f} W max (24 x TQP3M9037).",
        f"LNA junction: {t['p_lna_w']:.2f} W x {t['theta_jc']} C/W = +{t['dT_jc']} C over case; Tj {t['tj_85']} C at 85 C case (limit {t['tj_limit']:.0f} C).",
        "Rejection table: 05_docs/CRL-LS-CRPA4_rejection.csv; full report: 05_docs/CRL-LS-CRPA4_design_report.pdf.",
    ], title="POWER / THERMAL", fs=6.6)
    pdf.savefig(fig); fig.savefig(os.path.join(OUTD, f"{PN}_sheet6.png"), dpi=110); plt.close(fig)


def main():
    os.makedirs(OUTD, exist_ok=True)
    H = holes()
    with PdfPages(os.path.join(OUTD, f"{PN}_DRAWINGS.pdf")) as pdf:
        sheet_fab(pdf, H)
        sheet_array(pdf)
        sheet_assy(pdf, 3, "B")
        sheet_assy(pdf, 4, "F")
        sheet_cover(pdf)
        sheet_block(pdf)
    print(sorted(os.listdir(OUTD)))


if __name__ == "__main__":
    main()
