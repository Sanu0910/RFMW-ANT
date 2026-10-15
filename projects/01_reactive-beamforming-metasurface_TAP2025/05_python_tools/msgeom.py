"""Geometry library for the reactive beamforming metasurface (Almunif/Alsolamy/Grbic, IEEE TAP 2025).
All units mm.  Global frame: array centre at (0,0); cell (r,c) r=1 top..11 bottom, c=1 left..11 right.
Cell convention follows Fig.3: cell centred on the patch cross-gap, patches sit on cell corners,
coupling slot straddles the cell TOP edge, strip runs from port (0.7 mm below top edge) up across the
slot to a shorting via 0.4 mm into the cell above."""
import math, ezdxf
from shapely.geometry import LineString, box, Polygon
from shapely.ops import unary_union

# ---------------- Parameters (Fig.3 + Fig.10, assumptions flagged) ----------------
P       = 5.7    # cell period
GAP     = 0.55   # patch gap (L1)
PATCH   = P-GAP  # 5.15 patch side
SL      = 4.8    # slot length (L2)
SW_HALF = 0.3    # slot width per cell side (Fig.3); full slot at a boundary = 0.6  [ASSUMED interpretation]
MSW     = 0.4    # strip width (L3)  (~54 ohm on 0.203 mm RO4003C)
PORT_IN = 0.7    # port plane distance below cell top edge (Fig.3 '0.7 mm')
VIA_EXT = 0.4    # strip extension into cell above (Fig.3 '0.4 mm')
VIA_D   = 0.2    # via drill diameter [ASSUMED]
H1, H2  = 0.813, 0.203   # RO4003C thicknesses (patch/ground, ground/strip)
ER, TAND= 3.55, 0.0027
F0      = 10e9
N       = 11

def cell_centre(r,c):
    return ((c-6)*P, (6-r)*P)

# ---------------- microstrip model (Hammerstad) ----------------
def ms_model(w=MSW,h=H2,er=ER):
    u=w/h
    ee=(er+1)/2+(er-1)/2*(1+12/u)**-0.5
    if u<=1: z0=60/math.sqrt(ee)*math.log(8/u+u/4)
    else:    z0=120*math.pi/(math.sqrt(ee)*(u+1.393+0.667*math.log(u+1.444)))
    dloc=0.412*h*(ee+0.3)*(u+0.264)/((ee-0.258)*(u+0.8))   # open-end extension
    return ee,z0,dloc
EEFF,ZC,DL_OC = ms_model()
LAMG = 299.792458/(F0/1e9)/math.sqrt(EEFF)   # mm

def stub_length(X, zc=ZC, lamg=LAMG, dl=DL_OC, table=None):
    """Physical open-stub length (mm) whose input reactance at the port plane is X (ohm).
    Zin = -j Zc cot(beta l)  ->  beta l = atan2(1, -X/Zc) in (0,pi).
    If an HFSS-extracted table [(L_mm, X_ohm),...] is given (monotonic), interpolate it instead."""
    if table:
        T=sorted(table,key=lambda t:t[1])
        for (l0,x0),(l1,x1) in zip(T,T[1:]):
            if x0<=X<=x1: return l0+(X-x0)*(l1-l0)/(x1-x0)
        return T[0][0] if X<T[0][1] else T[-1][0]
    bl=math.atan2(1.0,-X/zc)
    return max(bl/(2*math.pi)*lamg-dl, 0.3)

# ---------------- meander (Fig.10 topology) ----------------
X_LIMIT        = P/2-0.55    # centreline half-span limit (0.35 mm edge clearance to cell edge)
PITCH          = 0.8         # vertical pitch between meander runs (0.4 mm gap)
LEAD           = 0.3         # lead below port plane before first bend (=> 1.0 mm from top edge, Fig.10)
TAIL           = 0.5         # final open tail (Fig.10 '0.5 mm')

def meander_path(L, x0, y0):
    """Centreline of an open stub of length L starting at port plane (x0,y0), running downward."""
    straight_max = P-PORT_IN-0.75   # port plane to clearance line above the cell-below's slot/via strip
    if L <= min(4.0, straight_max):
        return [(x0,y0),(x0,y0-L)], 0
    for n in range(2,7):
        # L = LEAD + W/2 + (n-1)W + (n-1)PITCH + TAIL
        W=(L-LEAD-TAIL-(n-1)*PITCH)/(n-0.5)
        if W<=2*X_LIMIT and LEAD+(n-1)*PITCH+TAIL<=straight_max: break
    else: raise ValueError(f"stub {L:.2f} mm does not fit")
    W=max(W,PITCH)
    pts=[(x0,y0)]; x=x0; y=y0-LEAD; pts.append((x,y))
    x=x0-W/2; pts.append((x,y)); d=+1
    for k in range(n-1):
        y-=PITCH; pts.append((x,y)); x+=d*W; pts.append((x,y)); d=-d
    y-=TAIL; pts.append((x,y))
    return pts, n

def thick(pts,w=MSW):
    return LineString(pts).buffer(w/2,cap_style="flat",join_style="mitre",mitre_limit=3)

# ---------------- per-cell features ----------------
def cell_features(r,c,mode="port",L=None,last_row=False):
    """mode: 'port' (lumped port at port plane), 'feed' (50-ohm excited port), 'meander' (open stub length L)."""
    cx,cy=cell_centre(r,c); top=cy+P/2
    f={}
    yp=top-PORT_IN
    strip=thick([(cx,yp),(cx,top+VIA_EXT)])
    f["via"]=(cx,top+VIA_EXT-VIA_D/2-0.05)
    f["slot"]=box(cx-SL/2,top-SW_HALF,cx+SL/2,top+SW_HALF)
    if mode=="meander":
        pts,_=meander_path(L,cx,yp)
        strip=unary_union([strip,thick(pts)])
    f["port"]=(mode,box(cx-MSW/2,yp-0.02,cx+MSW/2,yp+0.02),(cx,yp))
    f["strip"]=strip
    return f

# ---------------- DXF writer ----------------
LAYERS=[("L1_PATCH",1),("L2_GND_BOARD",3),("L2_GND_SLOT",3),("L3_STRIP",5),("VIA",6),
        ("PORT_FEED_50ohm",2),("PORT_LOAD_jX",4),("BOARD_OUTLINE",7),("TEXT",8)]
def new_doc():
    d=ezdxf.new("R2010"); d.units=ezdxf.units.MM; d.header["$INSUNITS"]=4
    for n,col in LAYERS: d.layers.add(n,color=col)
    return d
def add_poly(msp,geom,layer):
    gs=getattr(geom,"geoms",[geom])
    for g in gs:
        msp.add_lwpolyline(list(g.exterior.coords)[:-1],close=True,dxfattribs={"layer":layer})
        for hole in g.interiors:
            msp.add_lwpolyline(list(hole.coords)[:-1],close=True,dxfattribs={"layer":layer})

def build_array(path, feeds=(), loads=None, label=True, margin=2.0, layers_only=None):
    """feeds: list of (r,c) fed cells. loads: dict (r,c)->L_mm for meander realisation (None = lumped ports)."""
    d=new_doc(); m=d.modelspace()
    half=6*P+ (PATCH/2-P/2) + margin   # patches on 12x12 corner grid extend half a cell beyond cells
    ext=6*P+margin
    add_poly(m,box(-ext,-ext,ext,ext),"BOARD_OUTLINE")
    add_poly(m,box(-ext,-ext,ext,ext),"L2_GND_BOARD")
    for i in range(12):
        for j in range(12):
            x=(j-5.5)*P; y=(5.5-i)*P
            add_poly(m,box(x-PATCH/2,y-PATCH/2,x+PATCH/2,y+PATCH/2),"L1_PATCH")
    for r in range(1,N+1):
        for c in range(1,N+1):
            if (r,c) in feeds: mode,L="feed",None
            elif loads is not None: mode,L="meander",loads[(r,c)]
            else: mode,L="port",None
            f=cell_features(r,c,mode,L)
            add_poly(m,f["slot"],"L2_GND_SLOT"); add_poly(m,f["strip"],"L3_STRIP")
            m.add_circle(f["via"],VIA_D/2,dxfattribs={"layer":"VIA"})
            pm,pg,_=f["port"]
            if pm=="feed": add_poly(m,pg,"PORT_FEED_50ohm")
            elif pm=="port": add_poly(m,pg,"PORT_LOAD_jX")
            if label:
                cx,cy=cell_centre(r,c)
                m.add_text(f"R{r}C{c}",height=0.35,dxfattribs={"layer":"TEXT"}).set_placement((cx-2.7,cy-2.7))
    if layers_only:
        for e in list(m):
            if e.dxf.layer not in layers_only: m.delete_entity(e)
    d.saveas(path); return d

def build_unitcell(path, mode="port", L=None, layers_only=None):
    """Single cell exactly as Fig.3: centred on patch cross-gap; quarter patches; half slots at top &
    bottom edges; strip top piece (0.7 mm, port) and via piece (0.4 mm) at bottom edge (belongs to cell below)."""
    d=new_doc(); m=d.modelspace(); h=P/2
    cellbox=box(-h,-h,h,h)
    add_poly(m,cellbox,"BOARD_OUTLINE"); add_poly(m,cellbox,"L2_GND_BOARD")
    for sx in (-1,1):
        for sy in (-1,1):
            q=box(sx*h-PATCH/2,sy*h-PATCH/2,sx*h+PATCH/2,sy*h+PATCH/2).intersection(cellbox)
            add_poly(m,q,"L1_PATCH")
    for yy in (h,-h):
        add_poly(m,box(-SL/2,yy-SW_HALF,SL/2,yy+SW_HALF).intersection(cellbox),"L2_GND_SLOT")
    yp=h-PORT_IN
    top_piece=thick([(0,yp),(0,h)])
    if mode=="meander":
        pts,_=meander_path(L,0,yp); top_piece=unary_union([top_piece,thick(pts)])
    add_poly(m,top_piece,"L3_STRIP")
    add_poly(m,thick([(0,-h),(0,-h+VIA_EXT)]),"L3_STRIP")
    m.add_circle((0,-h+VIA_EXT-VIA_D/2-0.05),VIA_D/2,dxfattribs={"layer":"VIA"})
    if mode!="meander":
        add_poly(m,box(-MSW/2,yp-0.02,MSW/2,yp+0.02),"PORT_FEED_50ohm" if mode=="feed" else "PORT_LOAD_jX")
    if layers_only:
        for e in list(m):
            if e.dxf.layer not in layers_only: m.delete_entity(e)
    d.saveas(path); return d
