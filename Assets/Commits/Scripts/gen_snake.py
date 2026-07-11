
import sys, os, json, argparse, random, datetime, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fonts as F
import palette as P

WHITE=P.PALETTE["white"]; BLACK=P.PALETTE["black"]
PLUM=P.PANEL_SHADOW; PL=P.PLUM_LIGHT; PD=P.PLUM_DARK; PDEEP=P.PLUM_DEEP
MAROON=P.PANELS["progress"]
GREEN=P.PALETTE["classic_green"]
RED  =P.PALETTE["fireball_red"]
GOLD =P.PALETTE["curry_gold"]; CYAN=P.PALETTE["aqueduct_cyan"]
IPA  =P.PALETTE["ipa_D1C02B"]

def _shade(hexc,f):
    r=int(hexc[1:3],16); g=int(hexc[3:5],16); b=int(hexc[5:7],16)
    t=255 if f>0 else 0; f=abs(f)
    mix=lambda v:int(round(v+(t-v)*f))
    return f"#{mix(r):02X}{mix(g):02X}{mix(b):02X}"

CELL_EMPTY=_shade(MAROON,0.22)
SCREEN=_shade(MAROON,-0.30)
GREENS=[_shade(GREEN,0.42),_shade(GREEN,0.20),GREEN,_shade(GREEN,-0.28)]
REDS  =[_shade(RED,0.35),_shade(RED,0.15),RED,_shade(RED,-0.25)]

OFF=9; BEV=5; BW=18
M=6; MT=6; ML=30; MR=22
PW=865
COLS,ROWS=53,7
PITCH=14; CELL=12
DAY_W=40; MONTH_H=24
GRID_W=COLS*PITCH-(PITCH-CELL)
GRID_H=ROWS*PITCH-(PITCH-CELL)
PROMPT_H=96; GAP1=32; SCORE_H=42; PADB=8
IH=PROMPT_H+MONTH_H+GRID_H+GAP1+SCORE_H+PADB
PH=IH+2*BW
CW=ML+PW+OFF+MR; CH=MT+PH+OFF+M
OX,OY=ML,MT
IX0,IY0=OX+BW,OY+BW; IX1=OX+PW-BW
_inner=PW-2*BW
GX=IX0+( _inner-(DAY_W+GRID_W) )//2+DAY_W
GY=IY0+PROMPT_H+MONTH_H
SCORE_Y=GY+GRID_H+GAP1
CXC=OX+PW/2

PROMPT_TXT="> python eat my-progress.py"
T0=0.35; CPS=0.05

T_TYPE_DONE=T0+len(PROMPT_TXT)*CPS

T0_ABS=16.36
T_TYPE_DONE_ABS=T0_ABS+len(PROMPT_TXT)*CPS
T_PULSE_ABS=T_TYPE_DONE_ABS+0.3
T_REVEAL=T_PULSE_ABS+0.15
T_POP=T_TYPE_DONE+0.35
T_HOP=T_POP+0.75
T_F0=T_HOP+0.55
DT_F=0.062
N_STEPS=COLS*ROWS
T_FEND=T_F0+(N_STEPS-1)*DT_F
T_FLASH0=T_FEND+0.25
T_FLASH1=T_FLASH0+5.2
T_R0=T_FLASH1+0.25
DT_R=0.0062
T_REND=T_R0+(N_STEPS-1)*DT_R
T=T_REND+0.7

def px(v): return f"{v:.1f}"
_SIM={'Lf':[0]*(COLS*ROWS),'Lr':[0]*(COLS*ROWS)}
def kt(t): return max(0.0,min(1.0,t/T))

def frame():
    s=[]; x0,y0,x1,y1=OX,OY,OX+PW,OY+PH; b=BEV
    s.append(f'<rect x="{x0+OFF}" y="{y0+OFF}" width="{PW}" height="{PH}" fill="{PDEEP}"/>')
    s.append(f'<rect x="{x0}" y="{y0}" width="{PW}" height="{PH}" fill="{PLUM}"/>')
    s.append(f'<path d="M{x0},{y0} H{x1} L{x1-b},{y0+b} H{x0+b} V{y1-b} L{x0},{y1} Z" fill="{PL}"/>')
    s.append(f'<path d="M{x1},{y0} V{y1} H{x0} L{x0+b},{y1-b} H{x1-b} V{y0+b} Z" fill="{PD}"/>')
    s.append(f'<rect x="{x0+BW}" y="{y0+BW}" width="{PW-2*BW}" height="{PH-2*BW}" fill="{MAROON}"/>')
    return s

def prompt(static):
    s=[]
    big=34; sx,sy=IX0+12,IY0+14
    s.append(f'<rect x="{sx}" y="{sy}" width="{big}" height="{big}" fill="{WHITE}"/>')
    sm=round(big*0.57); dg=round(big*0.09)
    s.append(f'<rect x="{sx+big+dg}" y="{sy+big+dg}" width="{sm}" height="{sm}" fill="{WHITE}"/>')
    fs=26; tx=sx+big+20; ty=sy+big*0.5+fs*0.34
    if static:
        s.append(F.text_svg(PROMPT_TXT,'vt',fs,tx,ty,BLACK)[0])
        return s
    chars=[]
    for i,ch in enumerate(PROMPT_TXT):
        if ch==' ': continue
        xoff=tx+F.measure(PROMPT_TXT[:i],'vt',fs)
        g,_=F.text_svg(ch,'vt',fs,xoff,ty,BLACK)
        chars.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
                     f'begin="{T0_ABS+i*CPS:.2f}s" fill="freeze"/>{g}</g>')
    s.append(f'<g>{"".join(chars)}'
             f'<animate attributeName="opacity" values="1;0.35;1" dur="1.1s" '
             f'begin="{T_PULSE_ABS:.2f}s" repeatCount="indefinite"/></g>')
    return s

def mock_calendar(seed=7):
    rnd=random.Random(seed)
    end=datetime.date.today()
    start=end-datetime.timedelta(days=(COLS*ROWS-1))
    start-=datetime.timedelta(days=(start.weekday()+1)%7)
    grid=[]
    for c in range(COLS):
        col=[]
        for r in range(ROWS):
            d=start+datetime.timedelta(days=c*7+r)
            cnt = rnd.choice([1,1,2,2,3,4,5,6,8,11])
            col.append((cnt, d.isoformat()))
        grid.append(col)
    return grid

def gql(token, query, variables):
    req=urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query":query,"variables":variables}).encode(),
        headers={"Authorization":f"bearer {token}","User-Agent":"snake-gen",
                 "Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

CAL_QUERY="""
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        weeks{ contributionDays{ contributionCount date } }
      }
    }
  }
}"""

def fetch_calendar(user, token):
    d=gql(token, CAL_QUERY, {"login":user})
    weeks=d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid=[]
    for w in weeks[-COLS:]:
        col=[(day["contributionCount"], day["date"]) for day in w["contributionDays"]]
        while len(col)<ROWS: col.append((0,""))
        grid.append(col)
    while len(grid)<COLS: grid.insert(0,[(0,"")]*ROWS)
    return grid

def green_level(counts_nonzero, cnt):
    if not counts_nonzero: return 0
    qs=sorted(counts_nonzero)
    def q(p): return qs[min(len(qs)-1,int(p*len(qs)))]
    if cnt<=q(0.25): return 0
    if cnt<=q(0.5):  return 1
    if cnt<=q(0.75): return 2
    return 3

def build_path():
    path=[]
    for r in range(ROWS):
        cols=range(COLS) if r%2==0 else range(COLS-1,-1,-1)
        for c in cols: path.append((c,r,'cell'))
        if r<ROWS-1:
            if r%2==0: path.append((COLS,   r,'mid'))
            else:      path.append((-1,     r,'mid'))
    return path

def cell_xy(c,r,kind='cell'):
    if kind=='mid':

        u=CELL/6.0
        if c>=COLS: x=GX+(COLS-1)*PITCH+CELL+u
        else:       x=GX-u
        return x, GY+r*PITCH+PITCH*0.5
    return GX+c*PITCH, GY+r*PITCH

def park_route():
    drive=[]; up=[]
    lastx,lasty=cell_xy(COLS-1,ROWS-1); lastx+=CELL/2; lasty+=CELL/2
    startx,starty=cell_xy(0,0); startx+=CELL/2; starty+=CELL/2
    xL,xR=startx,lastx
    baseY=GY+GRID_H+PITCH*0.9

    y=lasty
    while y<baseY:
        y+=PITCH; drive.append((lastx,min(y,baseY)))

    lanes=8
    for ln in range(lanes):
        yy=baseY+ln*PITCH
        if ln%2==0:
            x=xR
            while x>xL: x-=PITCH; drive.append((max(x,xL),yy))
        else:
            x=xL
            while x<xR: x+=PITCH; drive.append((min(x,xR),yy))
        if ln<lanes-1: drive.append((drive[-1][0],yy+PITCH))

    xUp=startx; y=drive[-1][1]
    while y>starty:
        y-=PITCH; up.append((xUp,max(y,starty)))
    return drive, up

_NPATH=len(build_path())
T_REND=T_R0+(_NPATH-1)*DT_R
T=T_REND+0.7

def simulate(grid):
    path=build_path()
    NC=len(path)
    HALF=COLS//2
    counts={}
    for c in range(COLS):
        for r in range(ROWS): counts[(c,r)]=grid[c][r][0]
    def cnt_at(i):
        c,r,k=path[i]; return counts.get((c,r),0) if k=='cell' else 0

    Lvis=[0]*NC; length=0; folds=[0]*NC; f=0
    lastfold=[-1]*NC; lf=-1
    for k in range(NC):
        if cnt_at(k)>0: length+=1
        if length>COLS:
            length=HALF; f+=1; lf=k
        Lvis[k]=max(length,1); folds[k]=f; lastfold[k]=lf
    BASE=3.0
    INC=BASE/6.0
    total_thick=BASE+folds[-1]*INC

    def th_of(i,k):
        return (BASE+folds[k]*INC) if (k-i) < HALF else BASE

    t_eat={}; t_dep={}
    for k in range(NC):
        c,r,kind=path[k]
        if kind=='cell': t_eat[(c,r)]=T_F0+k*DT_F

    for m in range(NC):
        k=NC-1-m; c,r,kind=path[k]
        if kind=='cell': t_dep[(c,r)]=T_R0+m*DT_R

    cover=[[] for _ in range(NC)]
    for k in range(NC):
        t0=T_F0+k*DT_F; t1=t0+DT_F
        for i in range(max(0,k-Lvis[k]+1), k+1):
            cover[i].append((t0,t1,th_of(i,k)))

    Lf=Lvis[NC-1]
    lo=max(0,(NC-1)-Lf+1)
    hold_tiles=set(range(lo,NC))
    for i in range(NC):
        newivs=[]
        for (a,b,th) in cover[i]:
            if a>=T_FEND: continue
            if b>T_FEND: b=T_FEND
            if b>a: newivs.append((a,b,th))
        cover[i]=newivs
    for i in hold_tiles:
        cover[i].append((T_FEND,T_R0,th_of(i,NC-1)))
    for m in range(NC):
        k=NC-1-m
        t0=T_R0+m*DT_R; t1=t0+DT_R

        for i in range(k, min(NC, k+Lvis[k])):
            cover[i].append((t0,t1,th_of(i,k)))
    merged=[]
    for ivs in cover:
        if not ivs: merged.append([]); continue
        ivs.sort()
        out=[list(ivs[0])]
        for a,b,th in ivs[1:]:
            if a<=out[-1][1]+1e-6 and abs(th-out[-1][2])<1e-9:
                out[-1][1]=max(out[-1][1],b)
            else:

                if a < out[-1][1]:
                    out[-1][1]=a
                if b>a: out.append([a,b,th])

        out=[iv for iv in out if iv[1]-iv[0]>1e-6]
        merged.append([(a,b,th) for a,b,th in out])

    def P(i):
        c,r,k=path[i]; x,y=cell_xy(c,r,k)
        return (x+CELL/2, y+CELL/2) if k=='cell' else (x,y)
    c0=cell_xy(*build_path()[0][:2]); c1=cell_xy(1,0)
    spawn=(c1[0]+CELL/2+PITCH, GY-MONTH_H-26)
    mid  =(c0[0]+CELL/2+PITCH*0.5, GY-12)
    frames=[(0.0,*spawn),(T_HOP,*mid),(T_HOP+0.28, *P(0))]
    for k in range(NC): frames.append((T_F0+k*DT_F, *P(k)))
    for m in range(NC): frames.append((T_R0+m*DT_R, *P(NC-1-m)))
    frames.append((T-0.01,*spawn))

    sc=[(0.0,0)]
    for k in range(NC): sc.append((T_F0+k*DT_F, sc[-1][1]+cnt_at(k)))
    total=sc[-1][1]; running=total
    for m in range(NC):
        running-=cnt_at(NC-1-m); sc.append((T_R0+m*DT_R, running))
    sc.sort()
    global _SIM
    _SIM={'Lvis':Lvis,'folds':folds,'cover':merged,'path':path,'total_thick':total_thick,'BASE':BASE}
    return path,t_eat,t_dep,frames,merged,sc,total

MONTHS=["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

def screen_and_labels(grid):
    s=[]

    seen=None; last_c=-99
    for c in range(COLS):
        d=grid[c][0][1]
        if not d: continue
        mo=int(d[5:7])
        if mo!=seen:
            seen=mo
            if c-last_c>=4:
                x,_=cell_xy(c,0)
                s.append(F.text_svg(MONTHS[mo-1],'gb',8,x,GY-9,PL,anchor='start')[0])
                last_c=c

    for r,name in [(1,"MON"),(3,"WED"),(5,"FRI")]:
        _,y=cell_xy(0,r)
        s.append(F.text_svg(name,'gb',8,GX-12,y+CELL-2,PL,anchor='end')[0])
    return s

def cells_layer(grid,t_eat,t_dep,static):
    s=[]
    nz=[grid[c][r][0] for c in range(COLS) for r in range(ROWS) if grid[c][r][0]>0]
    hi=f'rgba-unused'
    for c in range(COLS):
        for r in range(ROWS):
            x,y=cell_xy(c,r)
            cnt,date=grid[c][r]
            title=f'<title>{date}: {cnt} contribution{"s" if cnt!=1 else ""}</title>'
            if cnt<=0:
                s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{CELL_EMPTY}">{title}</rect>')
            else:
                lvl=green_level(nz,cnt)
                col=GREENS[lvl]; rcol=REDS[lvl]
                if static:
                    s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{col}">{title}</rect>')
                else:
                    te=t_eat[(c,r)]; td=t_dep[(c,r)]
                    s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{col}">{title}'
                             f'<animate attributeName="fill" calcMode="discrete" '
                             f'values="{col};{rcol};{col}" '
                             f'keyTimes="0;{kt(te):.5f};{kt(td):.5f}" '
                             f'dur="{T:.2f}s" repeatCount="indefinite"/></rect>')

            s.append(f'<path d="M{x},{y+CELL} V{y} H{x+CELL}" fill="none" stroke="#FFFFFF" stroke-opacity="0.30" stroke-width="1.6"/>')
            s.append(f'<path d="M{x},{y+CELL} H{x+CELL} V{y}" fill="none" stroke="#000000" stroke-opacity="0.28" stroke-width="1.6"/>')
    return s

def _bevel_outline(cells, u, ox, oy, fill):
    occ=set(cells)
    lite=_shade(fill,0.34); dk=_shade(fill,-0.46)
    rects=[]
    for (c,r) in occ:
        rects.append(f'<rect x="{px(ox+c*u)}" y="{px(oy+r*u)}" width="{px(u+0.5)}" height="{px(u+0.5)}" fill="{fill}"/>')
    lite_seg=[]; dk_seg=[]
    for (c,r) in occ:
        x=ox+c*u; y=oy+r*u
        if (c,r-1) not in occ: lite_seg.append(f'M{px(x)},{px(y)} h{px(u)}')
        if (c-1,r) not in occ: lite_seg.append(f'M{px(x)},{px(y)} v{px(u)}')
        if (c,r+1) not in occ: dk_seg.append(f'M{px(x)},{px(y+u)} h{px(u)}')
        if (c+1,r) not in occ: dk_seg.append(f'M{px(x+u)},{px(y)} v{px(u)}')
    bev=(f'<path d="{" ".join(lite_seg)}" stroke="{lite}" stroke-width="1.4" fill="none"/>'
         f'<path d="{" ".join(dk_seg)}" stroke="{dk}" stroke-width="1.4" fill="none"/>')
    return ''.join(rects)+bev

Z_UNITS      =[(0,0),(1,0),(2,0),(3,0),(2,1),(3,1),(4,1),(5,1)]
Z_UNITS_MIR  =[(0,1),(1,1),(2,1),(3,1),(2,0),(3,0),(4,0),(5,0)]

def tail_dot(cx,cy,rad,fill,edge,horiz=False,mirror=False,over=1.0,thick=1.0):
    base=Z_UNITS_MIR if mirror else Z_UNITS
    cols=6; rows=2
    u=(CELL/6.0)
    W=cols*u; H=rows*u*thick
    if horiz:
        ox=cx-W/2; oy=cy-H/2
        cells=[(c, r) for (c,r) in base]

        return _bevel_outline_scaled(cells,u,ox,oy,fill,thick,axis='y')
    else:

        ox=cx-H/2; oy=cy-W/2
        cells=[(r, cols-1-c) for (c,r) in base]
        return _bevel_outline_scaled(cells,u,ox,oy,fill,thick,axis='x')

def _bevel_outline_scaled(cells,u,ox,oy,fill,thick,axis):
    occ=set(cells)
    lite=_shade(fill,0.34); dk=_shade(fill,-0.46)

    def rect(c,r):
        if axis=='y':
            h=u*thick; yy=oy+r*u - (h-u)/2*0
            return (ox+c*u, oy+r*u*thick, u+0.5, u*thick+0.5)
        else:
            return (ox+c*u*thick, oy+r*u, u*thick+0.5, u+0.5)
    rects=[]
    for (c,r) in occ:
        x,y,w,h=rect(c,r)
        rects.append(f'<rect x="{px(x)}" y="{px(y)}" width="{px(w)}" height="{px(h)}" fill="{fill}"/>')
    lite_seg=[]; dk_seg=[]
    for (c,r) in occ:
        x,y,w,h=rect(c,r)
        if (c,r-1) not in occ: lite_seg.append(f'M{px(x)},{px(y)} h{px(w)}')
        if (c-1,r) not in occ: lite_seg.append(f'M{px(x)},{px(y)} v{px(h)}')
        if (c,r+1) not in occ: dk_seg.append(f'M{px(x)},{px(y+h)} h{px(w)}')
        if (c+1,r) not in occ: dk_seg.append(f'M{px(x+w)},{px(y)} v{px(h)}')
    bev=(f'<path d="{" ".join(lite_seg)}" stroke="{lite}" stroke-width="1.4" fill="none"/>'
         f'<path d="{" ".join(dk_seg)}" stroke="{dk}" stroke-width="1.4" fill="none"/>')
    return ''.join(rects)+bev

def turn_link(cx,cy,fill,which,thick=1.0):
    u=CELL/6.0
    if which=='top':      cells=[(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(2,1),(3,1)]
    elif which=='bottom': cells=[(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(2,0),(3,0)]
    elif which=='mid_l':  cells=[(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(0,2),(0,3)]
    else:                 cells=[(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(1,2),(1,3)]
    cols=max(c for c,r in cells)+1; rows=max(r for c,r in cells)+1
    ox=cx-cols*u/2; oy=cy-rows*u/2
    return _bevel_outline(cells,u,ox,oy,fill)

def tail_layer(cover_unused,static):
    if static: return []
    S=_SIM; cover=S['cover']; path=S['path']
    NC=len(path)
    s=[]
    for i in range(NC):
        ivs=cover[i]
        if not ivs: continue
        c,r,kind=path[i]; x,y=cell_xy(c,r,kind)
        cx,cy=(x+CELL/2,y+CELL/2) if kind=='cell' else (x,y)
        pv=path[i-1] if i>0 else path[i]
        nx=path[i+1] if i+1<NC else path[i]
        if kind=='mid':
            base=turn_link(cx,cy,GREEN,'mid_l' if c>=COLS else 'mid_r')
            vertical=True
        elif nx[2]=='mid':
            base=turn_link(cx,cy,GREEN,'top'); vertical=False
        elif pv[2]=='mid':
            base=turn_link(cx,cy,GREEN,'bottom'); vertical=False
        else:
            base=tail_dot(cx,cy,4,GREEN,None,horiz=True,mirror=(r%2==1)); vertical=False

        ovals=["0"]; okts=["0"]
        for a,b,th in ivs:
            ovals+=["1","0"]; okts+=[f"{kt(a):.5f}",f"{kt(b):.5f}"]
        seq=[]
        for a,b,th in ivs:
            seq.append((kt(a),th))

        BASE=S['BASE']
        thvals=[]; thkts=[]
        for ktv,th in seq:
            m=th
            thvals.append(f"{'%.3f'%m} 1" if vertical else f"1 {'%.3f'%m}")
            thkts.append(f"{ktv:.5f}")
        if thkts[0]!="0.00000": thvals.insert(0,thvals[0]); thkts.insert(0,"0")
        if thkts[-1]!="1.00000": thvals.append(thvals[-1]); thkts.append("1.00000")
        g=(f'<g opacity="0">'
           f'<animate attributeName="opacity" calcMode="discrete" values="{";".join(ovals)}" '
           f'keyTimes="{";".join(okts)}" dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<g transform="translate({px(cx)},{px(cy)})">'
           f'<animateTransform attributeName="transform" type="scale" additive="sum" '
           f'calcMode="discrete" values="{";".join(thvals)}" keyTimes="{";".join(thkts)}" '
           f'dur="{T:.2f}s" repeatCount="indefinite"/>'
           f'<g transform="translate({px(-cx)},{px(-cy)})">{base}</g></g></g>')
        s.append(g)
    return s

def python_head(animate=False):
    pts="13,0 9,-3 5,-6 0,-8 -5,-6 -9,-3 -13,0 -9,3 -5,6 0,8 5,6 9,3"
    facet="0,-8 -5,-6 -9,-3 -13,0 -6,0 0,-4"
    tongue=('<path d="M13,0 H15 M15,0 L17,-1 M15,0 L17,1" fill="none" stroke="'+RED+'" '
            'stroke-width="2" stroke-linecap="round"'
            + ('><animate attributeName="d" dur="1.15s" repeatCount="indefinite" '
               'calcMode="spline" keyTimes="0;0.10;0.20;0.30;0.42;1" '
               'keySplines="0.3 0 0.2 1;0.3 0 0.2 1;0.3 0 0.2 1;0.3 0 0.2 1;0.3 0 0.2 1" '
               'values="'
               'M13,0 H15 M15,0 L17,-1 M15,0 L17,1;'
               'M13,0 H24 M24,0 L29,-5 M24,0 L29,5;'
               'M13,0 H19 M19,0 L23,-3 M19,0 L23,3;'
               'M13,0 H24 M24,0 L29,-5 M24,0 L29,5;'
               'M13,0 H15 M15,0 L17,-1 M15,0 L17,1;'
               'M13,0 H15 M15,0 L17,-1 M15,0 L17,1'
               '"/></path>'
               if animate else '/>'))
    return (f'{tongue}'
            f'<polygon points="{pts}" fill="{PLUM}" stroke="{PL}" stroke-width="2.4"/>'
            f'<polygon points="{facet}" fill="{PL}" opacity="0.55"/>'
            f'<rect x="0.5" y="-4.4" width="4" height="4" fill="{WHITE}"/>'
            f'<rect x="0.5" y="0.4" width="4" height="4" fill="{WHITE}"/>'
            f'<rect x="2.3" y="-3.2" width="1.8" height="1.8" fill="{BLACK}"/>'
            f'<rect x="2.3" y="1.8" width="1.8" height="1.8" fill="{BLACK}"/>')

def head_angles(frames):
    angs=[]; prev=90.0
    for i in range(len(frames)):
        if i+1<len(frames):
            dx=frames[i+1][1]-frames[i][1]; dy=frames[i+1][2]-frames[i][2]
            if abs(dx)>abs(dy) and abs(dx)>0.5: a=0.0 if dx>0 else 180.0
            elif abs(dy)>0.5: a=90.0 if dy>0 else 270.0
            else: a=prev
        else: a=prev
        angs.append(a); prev=a
    return angs

def head_layer(frames,static):
    if static:
        x,y=frames[0][1],frames[0][2]
        return [f'<g transform="translate({px(x)},{px(y)})"><g transform="rotate(90)">{python_head()}</g></g>']
    tvals=[];kts=[]
    for t,x,y in frames:
        tvals.append(f"{px(x)},{px(y)}"); kts.append(f"{kt(t):.5f}")
    angs=head_angles(frames)
    avals=[f"{a:.0f}" for a in angs]
    if kts[-1]!="1.00000":
        tvals.append(tvals[-1]); avals.append(avals[-1]); kts.append("1.00000")
    return [
      f'<g opacity="0"><set attributeName="opacity" to="1" begin="{T_POP:.2f}s" fill="freeze"/>'
      f'<g transform="translate({tvals[0].split(",")[0]},{tvals[0].split(",")[1]})">'
      f'<animateTransform attributeName="transform" type="translate" calcMode="linear" '
      f'values="{";".join(tvals)}" keyTimes="{";".join(kts)}" '
      f'dur="{T:.2f}s" repeatCount="indefinite"/>'
      f'<g transform="rotate(90)">'
      f'<animateTransform attributeName="transform" type="rotate" calcMode="discrete" '
      f'values="{";".join(avals)}" keyTimes="{";".join(kts)}" '
      f'dur="{T:.2f}s" repeatCount="indefinite"/>'
      f'<g transform="scale(0)">'
      f'<animateTransform attributeName="transform" type="scale" '
      f'values="0;1.4;0.85;1.1;1" keyTimes="0;0.4;0.65;0.85;1" dur="0.55s" '
      f'begin="{T_POP:.2f}s" fill="freeze"/>'
      f'{python_head(animate=True)}'
      f'</g></g></g></g>']

SCORE_COLORS=[GOLD,RED,CYAN,GREENS[1],IPA,P.PLUM_LIGHT,WHITE]
def colored_text(txt, size, x, y, ci0=0):
    out=[]; cx=x; ci=ci0
    for ch in txt:
        w=F.measure(ch,'gb',size)
        if ch!=' ':
            col=SCORE_COLORS[ci%len(SCORE_COLORS)]; ci+=1
            out.append(F.text_svg(ch,'gb',size,cx,y,col)[0])
        cx+=w
    return ''.join(out), cx-x, ci

def score_layer(sc,total,static):
    s=[]
    size=22
    ndig=len(str(max(total,1)))
    full_w=F.measure("SCORE : ",'gb',size)+ndig*size
    x0=CXC-full_w/2
    by=SCORE_Y+size*0.85
    label,lw,ci=colored_text("SCORE : ",size,x0,by)
    if static:
        s.append(label)
        s.append(F.text_svg("0",'gb',size,x0+lw,by,SCORE_COLORS[ci%len(SCORE_COLORS)])[0])
        return s
    vis=(f'<animate attributeName="opacity" calcMode="discrete" '
         f'values="1;0;1" keyTimes="0;{kt(T_FLASH0):.5f};{kt(T_FLASH1):.5f}" '
         f'dur="{T:.2f}s" repeatCount="indefinite"/>')
    digs=[]
    segs=[]
    for i,(t,v) in enumerate(sc):
        te=sc[i+1][0] if i+1<len(sc) else T
        segs.append((t,te,v))
    for slot in range(ndig):
        glyph_iv={}
        for a,b,v in segs:
            txt=str(v)
            ch=txt[::-1][slot] if slot<len(txt) else None
            glyph_iv.setdefault(ch,[]).append((a,b))
        xslot=x0+lw+(ndig-1-slot)*size
        colr=SCORE_COLORS[(ci+(ndig-1-slot))%len(SCORE_COLORS)]
        for ch,ivs in glyph_iv.items():
            if ch is None: continue
            merged=[]
            for a,b in sorted(ivs):
                if merged and a<=merged[-1][1]+1e-9: merged[-1]=(merged[-1][0],max(merged[-1][1],b))
                else: merged.append((a,b))
            vals=["0"]; kts=["0"]
            for a,b in merged:
                if a<=0.001: vals[0]="1"; vals.append("0"); kts.append(f"{kt(b):.5f}")
                else: vals+=["1","0"]; kts+=[f"{kt(a):.5f}",f"{kt(b):.5f}"]
            g=F.text_svg(ch,'gb',size,xslot,by,colr)[0]
            digs.append(f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" '
                        f'values="{";".join(vals)}" keyTimes="{";".join(kts)}" '
                        f'dur="{T:.2f}s" repeatCount="indefinite"/>{g}</g>')
    s.append(f'<g>{vis}{label}{"".join(digs)}</g>')

    hs_txt=f"HIGHSCORE! : {total}"
    hw=F.measure(hs_txt,'gb',size)
    hx=CXC-hw/2

    cyc_top=f"{GOLD};{RED};{CYAN};{GREENS[1]};{GOLD}"
    cyc_bot=f"{RED};{CYAN};{GREENS[1]};{GOLD};{RED}"
    grad=(f'<linearGradient id="hsgrad" x1="0" y1="{px(by-size)}" x2="0" y2="{px(by+4)}" '
          f'gradientUnits="userSpaceOnUse">'
          f'<stop offset="0" stop-color="{GOLD}">'
          f'<animate attributeName="stop-color" values="{cyc_top}" dur="2.6s" '
          f'repeatCount="indefinite"/></stop>'
          f'<stop offset="1" stop-color="{RED}">'
          f'<animate attributeName="stop-color" values="{cyc_bot}" dur="2.6s" '
          f'repeatCount="indefinite"/></stop>'
          f'</linearGradient>')
    hg=F.text_svg(hs_txt,'gb',size,hx,by,'url(#hsgrad)')[0]
    blink=[]; t=T_FLASH0; on=True
    vals=["0"]; kts=["0"]
    while t<T_FLASH1-0.01:
        vals.append("1" if on else "0"); kts.append(f"{kt(t):.5f}")
        t+=0.30 if on else 0.14
        on=not on
    vals.append("0"); kts.append(f"{kt(T_FLASH1):.5f}")
    flash=(f'<animate attributeName="opacity" calcMode="discrete" '
           f'values="{";".join(vals)}" keyTimes="{";".join(kts)}" '
           f'dur="{T:.2f}s" repeatCount="indefinite"/>')
    s.append(f'<defs>{grad}</defs><g opacity="0">{flash}{hg}</g>')

    rs="RESETTING"; rsz=16
    rw=F.measure(rs,'gb',rsz); dw=F.measure(".",'gb',rsz)
    rx=IX1-16-rw-3*dw
    rg=F.text_svg(rs,'gb',rsz,rx,by,WHITE)[0]
    rvis=(f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
          f'keyTimes="0;{kt(T_R0-0.15):.5f};{kt(T_REND+0.25):.5f}" '
          f'dur="{T:.2f}s" repeatCount="indefinite"/>')
    dots=[]
    dperiod=0.45
    for di in range(3):
        dx=rx+rw+di*dw
        dg=F.text_svg(".",'gb',rsz,dx,by,WHITE)[0]
        vals=["0"]; kts=["0"]; state=0; t=T_R0-0.15
        while t<T_REND+0.25:
            phase=int(((t-(T_R0-0.15))/dperiod))%3
            on=1 if di<=phase else 0
            if on!=state:
                vals.append(str(on)); kts.append(f"{kt(t):.5f}"); state=on
            t+=dperiod
        vals.append("0"); kts.append(f"{kt(T_REND+0.25):.5f}")
        dots.append(f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" '
                    f'values="{";".join(vals)}" keyTimes="{";".join(kts)}" '
                    f'dur="{T:.2f}s" repeatCount="indefinite"/>{dg}</g>')
    s.append(f'<g opacity="0">{rvis}{rg}</g>{"".join(dots)}')
    return s

def build(grid, static=False):
    path,t_eat,t_dep,frames,cover,sc,total=simulate(grid)
    ix,iy=OX+BW,OY+BW; iw=PW-2*BW; ih=PH-2*BW
    cid='panelclip_A'
    out=[f'<defs><clipPath id="{cid}">'
         f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}"/></clipPath></defs>']
    out+=frame()
    out+=prompt(static)

    game=[]
    game+=screen_and_labels(grid)
    game+=cells_layer(grid,t_eat,t_dep,static)
    snake=tail_layer(cover,static)+head_layer(frames,static)
    game.append(f'<g clip-path="url(#{cid})">{"".join(snake)}</g>')
    game+=score_layer(sc,total,static)
    gbody="".join(game)
    if not static:

        gbody=gbody.replace(f'dur="{T:.2f}s" repeatCount="indefinite"',
                            f'dur="{T:.2f}s" begin="{T_REVEAL:.2f}s" repeatCount="indefinite"')
        out.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
                   f'begin="{T_REVEAL:.2f}s" fill="freeze"/>{gbody}</g>')
    else:
        out.append(gbody)
    body="".join(out)
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" '
         f'width="{CW}" height="{CH}">{body}</svg>')
    return svg, total

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("RADAR_USER","McVarHQ"))
    ap.add_argument("--out",  default="panel6_snake.svg")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--static", action="store_true")
    a=ap.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if a.mock or not token:
        grid=mock_calendar()
    else:
        grid=fetch_calendar(a.user, token)
    svg,total=build(grid, static=a.static)
    open(a.out,'w').write(svg)
    print(f"wrote {a.out} ({len(svg)}B) score_total={total} loop={T:.1f}s canvas={CW}x{CH}")

if __name__=="__main__":
    main()
