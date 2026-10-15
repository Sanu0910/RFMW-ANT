"""Build every DXF in the pack, or a realised array from YOUR optimised reactances.
Usage:
  python build_dxf.py all                                   # regenerate the whole pack
  python build_dxf.py realise my_X.csv out.dxf --feeds 6,6  # after MATLAB re-optimisation
         [--half] (CSV holds rows y=1..6 only; mirrored about centre row)  [--table meander_Zin.csv]
CSV format: header 'y_index\\x_index,1..11', then one row per y index (paper axis, y up), X in ohm."""
import sys, os, csv, argparse
import msgeom as g
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

def read_X(path, half):
    X={}
    with open(path) as fh:
        rd=csv.reader(fh); next(rd)
        for row in rd:
            if not row or not row[0].strip(): continue
            j=int(row[0]); vals=[float(v) for v in row[1:12]]
            rows=[12-j] if not half else sorted({12-j, j})   # y index j -> array row r=12-j (y up), mirror r=j
            for r in rows:
                for c in range(1,12): X[(r,c)]=vals[c-1]
    assert len(X)==121, f"got {len(X)} cells"
    return X

def read_table(path):
    if not path: return None
    with open(path) as fh:
        rd=csv.reader(fh); next(rd); return [(float(a),float(b)) for a,b,*_ in rd]

def realise(xcsv, out, feeds, half, table=None, lencsv=None):
    X=read_X(xcsv,half); tab=read_table(table)
    L={k:g.stub_length(v,table=tab) for k,v in X.items()}
    g.build_array(out,feeds=feeds,loads=L)
    if lencsv:
        with open(lencsv,"w",newline="") as fh:
            w=csv.writer(fh); w.writerow(["row","col","role","X_ohm","stub_len_mm","meander_turns"])
            for r in range(1,12):
                for c in range(1,12):
                    if (r,c) in feeds: w.writerow([r,c,"FEED_50ohm","","",""]); continue
                    _,n=g.meander_path(L[(r,c)],0,0)
                    w.writerow([r,c,"load",round(X[(r,c)],1),round(L[(r,c)],3),n])
    return X,L

def all_():
    B=f"{ROOT}/01_dxf_base"; R=f"{ROOT}/03_dxf_realized"; D=f"{ROOT}/02_reactance_data"
    # --- base (lumped-port) models ---
    g.build_unitcell(f"{B}/unitcell_fig3_all_layers.dxf","feed")
    for lay in ("L1_PATCH","L2_GND_SLOT","L3_STRIP"):
        keep={lay,"BOARD_OUTLINE"} | ({"VIA","PORT_FEED_50ohm"} if lay=="L3_STRIP" else set()) | ({"L2_GND_BOARD"} if lay=="L2_GND_SLOT" else set())
        g.build_unitcell(f"{B}/unitcell_fig3_{lay}.dxf","feed",layers_only=keep)
    g.build_array(f"{B}/array11x11_designI_II_centrefed_lumped.dxf",feeds=[(6,6)])
    g.build_array(f"{B}/array11x11_designIII_MIMO_2feeds_lumped.dxf",feeds=[(6,4),(6,8)])
    g.build_array(f"{B}/array11x11_designIV_V_reflective_lumped.dxf",feeds=[])
    # meander library for HFSS Zin extraction (single cell, lengths 1..8 mm)
    for Lm in (1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5):
        g.build_unitcell(f"{B}/meander_lib/unitcell_meander_L{Lm:.1f}mm.dxf","meander",L=Lm)
    # --- realised (Fig.11 / Fig.12 and the other designs) ---
    jobs=[("designI_fig4a",[(6,6)],True,"Fig11_designI_directfed_beam-30deg_realized"),
          ("designIV_fig8b",[],True,"Fig12_designIV_reflective_beamsplitter_realized"),
          ("designII_fig6a",[(6,6)],True,"designII_flattop_realized"),
          ("designIII_fig7a",[(6,4),(6,8)],True,"designIII_MIMO_realized"),
          ("designV_fig9b",[],False,"designV_reflective_MIMO_realized")]
    for src,feeds,half,name in jobs:
        realise(f"{D}/{src}_reactance_ohm.csv",f"{R}/{name}.dxf",feeds,half,lencsv=f"{R}/{name}_cell_table.csv")
    with open(f"{B}/reactance_to_stub_length.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["X_ohm","stub_len_mm (Hammerstad, open-end corrected)","beta_l_deg"])
        import math
        for X in range(-120,121,5):
            w.writerow([X,round(g.stub_length(X),3),round(math.degrees(math.atan2(1,-X/g.ZC)),1)])
    print("eeff=%.3f Zc=%.1f lam_g=%.2f dl=%.3f"%(g.EEFF,g.ZC,g.LAMG,g.DL_OC))

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="all":
        os.makedirs(f"{ROOT}/01_dxf_base/meander_lib",exist_ok=True); all_(); sys.exit()
    ap=argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("xcsv"); ap.add_argument("out")
    ap.add_argument("--feeds",nargs="*",default=[]); ap.add_argument("--half",action="store_true")
    ap.add_argument("--table"); a=ap.parse_args()
    feeds=[tuple(int(v) for v in f.split(",")) for f in a.feeds]
    realise(a.xcsv,a.out,feeds,a.half,a.table,a.out.replace(".dxf","_cell_table.csv"))
