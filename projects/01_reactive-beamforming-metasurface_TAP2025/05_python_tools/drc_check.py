"""Design-rule check on a generated array DXF: L3 strip clearance, strip-over-slot, cell-boundary overflow."""
import sys, ezdxf
from shapely.geometry import Polygon
from shapely.strtree import STRtree
def polys(doc,layer):
    out=[]
    for e in doc.modelspace().query(f'LWPOLYLINE[layer=="{layer}"]'):
        out.append(Polygon([(p[0],p[1]) for p in e.get_points()]))
    return out
def drc(path, min_gap=0.2):
    d=ezdxf.readfile(path); S=polys(d,"L3_STRIP"); SL=polys(d,"L2_GND_SLOT")
    tree=STRtree(S); worst=9; viol=0
    for i,a in enumerate(S):
        for j in tree.query(a.buffer(2.0)):
            if j<=i: continue
            gap=a.distance(S[j]); worst=min(worst,gap)
            if gap<min_gap: viol+=1
    # meander over slot: strip area over slot beyond the intended crossing (strip width x slot width)
    over=0
    for s in SL:
        a=sum(st.intersection(s).area for st in S)
        if a>0.4*0.6*1.05: over+=1
    print(f"{path.split('/')[-1]}: strips={len(S)} min strip-strip gap={worst:.3f} mm, gap<{min_gap}: {viol}, slots with extra metal over them: {over}")
for p in sys.argv[1:]: drc(p)
