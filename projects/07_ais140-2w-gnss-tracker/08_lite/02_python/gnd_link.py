"""Find GND pour fragments that are not tied to the main ground and route each to the nearest main-ground via.

Run in the KiCad python after `make_pcb.py tie`:  python3 gnd_link.py   (writes /tmp/drc_gnd.json, runs patch_route)
"""
import json, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_pcb as M
b = pcbnew.LoadBoard(M.PCB)
frags=[]
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetZoneName() not in ("F_GND","B_GND"): continue
    ps=z.GetFilledPolysList(z.GetLayer())
    for k in range(ps.OutlineCount()):
        s=pcbnew.SHAPE_POLY_SET(); s.AddOutline(ps.Outline(k)); frags.append((z.GetZoneName(),s))
par=list(range(len(frags)))
def f(i):
    while par[i]!=i: i=par[i]
    return i
links=[t.GetPosition() for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA) and t.GetNetname()=="GND"]
links+=[q.GetPosition() for q in b.GetPads() if q.GetNetname()=="GND" and q.GetAttribute()==pcbnew.PAD_ATTRIB_PTH]
for pos in links:
    hit=[i for i,(_,s) in enumerate(frags) if s.Contains(pos)]
    for i in hit[1:]: par[f(hit[0])]=f(i)
g={}
for i in range(len(frags)): g.setdefault(f(i),[]).append(i)
main=max(g.values(),key=lambda v:sum(frags[i][1].Area() for i in v))
pads=[p for p in b.GetPads() if p.GetNetname()=="GND"]
for v in g.values():
    if v is main: continue
    for i in v:
        n,s=frags[i]; bb=s.BBox()
        print("isolated", n, round(s.Area() / 1e12, 2), "mm2",
              [p.GetParentFootprint().GetReference() + "." + p.GetNumber() for p in pads if s.Contains(p.GetPosition())])
viap=[t.GetPosition() for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA) and t.GetNetname()=="GND"]
mainvias=[v for v in viap if any(frags[i][1].Contains(v) for i in main)]
out=[]
for v in g.values():
    if v is main: continue
    ps=[p for p in pads if any(frags[i][1].Contains(p.GetPosition()) for i in v) and p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    p=ps[0]; c=p.GetPosition()
    tgt=sorted(mainvias,key=lambda q:(q-c).EuclideanNorm())[:3]
    for t in tgt:
        out.append({"items":[{"description":f"Pad {p.GetNumber()} [GND] of {p.GetParentFootprint().GetReference()} on F.Cu","pos":{"x":pcbnew.ToMM(c.x),"y":pcbnew.ToMM(c.y)}},
                             {"description":"Via [GND] on F.Cu - B.Cu","pos":{"x":pcbnew.ToMM(t.x),"y":pcbnew.ToMM(t.y)}}]})
        break
json.dump({"unconnected_items":out},open("/tmp/drc_gnd.json","w"))
print(len(out),"gnd jobs")
del b
import patch_route
patch_route.run(M.PCB, drc_json="/tmp/drc_gnd.json")
