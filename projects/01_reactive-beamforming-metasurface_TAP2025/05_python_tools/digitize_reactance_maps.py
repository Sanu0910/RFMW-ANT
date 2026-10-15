"""Digitize the reactance colour maps (Figs. 4a, 6a, 7a, 8b, 9b) of the paper into per-cell CSVs.
Steps: pdftoppm -r 400 the PDF -> crop each map (map + its colourbar) to PNG -> run:
    python digitize_reactance_maps.py <folder_with_crops> <out_folder>
The colourbar's tick marks are detected automatically and fitted linearly to the tick values below,
each cell's median colour is matched to the nearest colourbar colour (parula), giving X in ohm.
Typical accuracy ~ +-1 colour step (~ +-3 ohm) plus PDF rendering error -> treat as a seed."""
import numpy as np, csv, sys
from PIL import Image
from scipy import ndimage
P=(sys.argv[1] if len(sys.argv)>1 else ".")+"/"; OUT=(sys.argv[2] if len(sys.argv)>2 else ".")+"/"
def analyze(path):
    a=np.asarray(Image.open(path).convert('RGB')).astype(float)
    mx=a.max(2); mn=a.min(2); sat=(mx-mn)/(mx+1e-6)
    col=(sat>0.3)&(mx>60)
    lab,n=ndimage.label(col)
    objs=ndimage.find_objects(lab)
    boxes=[]
    for i,s in enumerate(objs):
        h=s[0].stop-s[0].start; w=s[1].stop-s[1].start
        if h*w>2000: boxes.append((s[0].start,s[0].stop,s[1].start,s[1].stop,(lab[s]==i+1).sum()))
    return a,boxes

figs={ # name: (png, tick values, ny rows shown, design label)
 "designI_fig4a":("f4a.png",[-60,-40,-20,0,20,40,60,80],6),
 "designII_fig6a":("f6a.png",[-80,-48,-16,16,48,80],6),
 "designIII_fig7a":("f7a.png",[-100,-70,-40,-10,20,50,80],6),
 "designIV_fig8b":("f8b.png",[-48,-16,16,48,80],6),
 "designV_fig9b":("f9b.png",[-28,4,36,68],11),
}
report=[]
for name,(png,ticks,ny) in figs.items():
    a,boxes=analyze(P+png)
    boxes=sorted(boxes,key=lambda b:-b[4])[:2]
    hm=max(boxes,key=lambda b:b[1]-b[0]); cb=min(boxes,key=lambda b:b[1]-b[0])
    y0,y1,x0,x1=cb[:4]
    # tick marks: grey pixels on colorbar top rows
    row=a[y0+1,x0:x1]; g=(row.max(1)-row.min(1))<40
    xs=np.where(g)[0]+x0
    groups=np.split(xs,np.where(np.diff(xs)>3)[0]+1)
    tpx=[grp.mean() for grp in groups if len(grp)]
    assert len(tpx)==len(ticks),(name,tpx)
    k,c=np.polyfit(tpx,ticks,1)
    resid=np.abs(np.polyval([k,c],tpx)-ticks).max()
    strip=a[y0+int((y1-y0)*0.3):y0+int((y1-y0)*0.7),x0+2:x1-2].mean(0)   # colour vs x
    sx=np.arange(x0+2,x1-2); svals=k*sx+c
    hy0,hy1,hx0,hx1=hm[:4]; cw=(hx1-hx0)/11; ch=(hy1-hy0)/ny
    grid=np.zeros((ny,11)); err=np.zeros((ny,11))
    for r in range(ny):        # r=0 top row of image = y index ny
        for q in range(11):
            ya=int(hy0+(r+0.3)*ch); yb=int(hy0+(r+0.7)*ch)
            xa=int(hx0+(q+0.3)*cw); xb=int(hx0+(q+0.7)*cw)
            px=np.median(a[ya:yb,xa:xb].reshape(-1,3),0)
            d=np.linalg.norm(strip-px,axis=1); i=d.argmin()
            grid[r,q]=svals[i]; err[r,q]=d[i]
    # store with y index (paper axis): y=ny at top
    with open(OUT+name+"_reactance_ohm.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["y_index\\x_index"]+list(range(1,12)))
        for r in range(ny): w.writerow([ny-r]+[round(v,1) for v in grid[r]])
    report.append(f"{name}: ticks fit resid {resid:.2f} ohm, colour match max dist {err.max():.1f}/441, range {grid.min():.0f}..{grid.max():.0f} ohm, {k:.4f} ohm/px")
print("\n".join(report))
