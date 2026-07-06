#!/usr/bin/env python3
"""
Panel 6 — "progress": SMIL snake eats the GitHub contribution calendar.
v2: roomier layout, month/day labels, 4 green intensity levels, inset screen,
beveled pixel cells, diamond tail segments, spawn-above head pop, centered
multicolor score (value = total CONTRIBUTIONS eaten, not cells), longer
gradient highscore flash, black prompt, per-cell <title> tooltips (work when
the SVG is opened directly; GitHub <img> embeds cannot hover).
"""
import sys, os, json, argparse, random, datetime, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fonts as F
import palette as P

WHITE=P.PALETTE["white"]; BLACK=P.PALETTE["black"]
PLUM=P.PANEL_SHADOW; PL=P.PLUM_LIGHT; PD=P.PLUM_DARK; PDEEP=P.PLUM_DEEP
MAROON=P.PANELS["progress"]            # #4F2E39
GREEN=P.PALETTE["classic_green"]       # base green
RED  =P.PALETTE["fireball_red"]
GOLD =P.PALETTE["curry_gold"]; CYAN=P.PALETTE["aqueduct_cyan"]
IPA  =P.PALETTE["ipa_D1C02B"]

def _shade(hexc,f):
    r=int(hexc[1:3],16); g=int(hexc[3:5],16); b=int(hexc[5:7],16)
    t=255 if f>0 else 0; f=abs(f)
    mix=lambda v:int(round(v+(t-v)*f))
    return f"#{mix(r):02X}{mix(g):02X}{mix(b):02X}"

CELL_EMPTY=_shade(MAROON,0.22)          # muted mauve empties (quieter than gray)
SCREEN=_shade(MAROON,-0.30)             # inset screen behind the calendar
GREENS=[_shade(GREEN,0.42),_shade(GREEN,0.20),GREEN,_shade(GREEN,-0.28)]  # L1..L4
REDS  =[_shade(RED,0.35),_shade(RED,0.15),RED,_shade(RED,-0.25)]          # L1..L4

OFF=9; BEV=5; BW=18
M=6; MT=6; ML=30; MR=22    # minimal top margin (dividers handle spacing)
PW=865
COLS,ROWS=53,7
PITCH=15; CELL=13
DAY_W=34; MONTH_H=24
GRID_W=COLS*PITCH-(PITCH-CELL)          # 739
GRID_H=ROWS*PITCH-(PITCH-CELL)          # 95
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
CXC=OX+PW/2                             # panel centre for centred texts

# ---- timeline ---------------------------------------------------------------
PROMPT_TXT="> python eat my-progress.py"
T0=0.35; CPS=0.05
T_TYPE_DONE=T0+len(PROMPT_TXT)*CPS
T_POP=T_TYPE_DONE+0.35                  # head pops ABOVE the calendar
T_HOP=T_POP+0.75                        # hop toward the first cell
T_F0=T_HOP+0.55                         # forward eating starts
DT_F=0.062
N_STEPS=COLS*ROWS
T_FEND=T_F0+(N_STEPS-1)*DT_F
T_FLASH0=T_FEND+0.25
T_FLASH1=T_FLASH0+5.2                   # longer highscore celebration
T_R0=T_FLASH1+0.25
DT_R=0.0062
T_REND=T_R0+(N_STEPS-1)*DT_R
T=T_REND+0.7

def px(v): return f"{v:.1f}"
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
                     f'begin="{T0+i*CPS:.2f}s" fill="freeze"/>{g}</g>')
    s.append(f'<g>{"".join(chars)}'
             f'<animate attributeName="opacity" values="1;0.35;1" dur="1.1s" '
             f'begin="{T_TYPE_DONE+0.3:.2f}s" repeatCount="indefinite"/></g>')
    return s

# ---- calendar data: grid[c][r] = (count, iso_date) --------------------------
def mock_calendar(seed=7):
    rnd=random.Random(seed)
    end=datetime.date.today()
    start=end-datetime.timedelta(days=(COLS*ROWS-1))
    start-=datetime.timedelta(days=(start.weekday()+1)%7)   # back to Sunday
    grid=[]
    for c in range(COLS):
        col=[]
        for r in range(ROWS):
            d=start+datetime.timedelta(days=c*7+r)
            cnt = rnd.choice([0,0,0,0,1,1,2,2,3,4,5,6,8,11]) if rnd.random()<0.55 else 0
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
    """GitHub-style quartile levels 0..3 among non-zero counts."""
    if not counts_nonzero: return 0
    qs=sorted(counts_nonzero)
    def q(p): return qs[min(len(qs)-1,int(p*len(qs)))]
    if cnt<=q(0.25): return 0
    if cnt<=q(0.5):  return 1
    if cnt<=q(0.75): return 2
    return 3

# ---- serpentine + simulation -------------------------------------------------
def build_path():
    path=[]
    for r in range(ROWS):
        cols=range(COLS) if r%2==0 else range(COLS-1,-1,-1)
        for c in cols: path.append((c,r))
    return path

def cell_xy(c,r):
    return GX+c*PITCH, GY+r*PITCH

def simulate(grid):
    path=build_path()
    counts={ (c,r):grid[c][r][0] for c in range(COLS) for r in range(ROWS) }
    greens={cell for cell,v in counts.items() if v>0}
    t_eat={}; L=0; Lf=[0]*N_STEPS
    for k,cell in enumerate(path):
        if cell in greens:
            t_eat[cell]=T_F0+k*DT_F; L+=1
        Lf[k]=L
    seg_total=L
    t_dep={}; Lr=[0]*N_STEPS
    L=seg_total
    for m in range(N_STEPS):
        h=N_STEPS-1-m; cell=path[h]
        if cell in greens:
            t_dep[cell]=T_R0+m*DT_R; L-=1
        Lr[h]=L
    # head keyframes: spawn ABOVE the calendar (above col 1, clear of the
    # corner squares), pop, then hop diagonally into the first cell
    c0=cell_xy(*path[0]); c1=cell_xy(1,0)
    spawn=(c1[0]+CELL/2+PITCH, GY-MONTH_H-26)
    mid  =(c0[0]+CELL/2+PITCH*0.5, GY-12)
    home =(c0[0]+CELL/2, c0[1]+CELL/2)
    frames=[(0.0,*spawn),(T_HOP,*mid),(T_HOP+0.28,*home)]
    for k,cell in enumerate(path):
        x,y=cell_xy(*cell)
        frames.append((T_F0+k*DT_F, x+CELL/2, y+CELL/2))
    xe,ye=cell_xy(*path[-1])
    frames.append((T_R0-0.01, xe+CELL/2, ye+CELL/2))
    for m in range(N_STEPS):
        h=N_STEPS-1-m; x,y=cell_xy(*path[h])
        frames.append((T_R0+m*DT_R, x+CELL/2, y+CELL/2))
    frames.append((T-0.01,*spawn))
    # tail cover
    cover_raw={cell:[] for cell in path}
    def add(cell,a,b): cover_raw[cell].append((a,b))
    for k in range(N_STEPS):
        t0=T_F0+k*DT_F
        for i in range(max(0,k-Lf[k]),k):
            add(path[i],t0,t0+DT_F)
    for i in range(max(0,N_STEPS-1-seg_total),N_STEPS-1):
        add(path[i],T_FEND,T_R0)
    for m in range(N_STEPS):
        h=N_STEPS-1-m; t0=T_R0+m*DT_R
        for i in range(h+1,min(N_STEPS,h+1+Lr[h])):
            add(path[i],t0,t0+DT_R)
    cover={}
    for cell,ivs in cover_raw.items():
        if not ivs: cover[cell]=[]; continue
        ivs.sort(); merged=[list(ivs[0])]
        for a,b in ivs[1:]:
            if a<=merged[-1][1]+1e-6: merged[-1][1]=max(merged[-1][1],b)
            else: merged.append([a,b])
        cover[cell]=[(a,b) for a,b in merged]
    # score = SUM of contribution counts eaten
    sc=[(0.0,0)]
    for k,cell in enumerate(path):
        if cell in greens: sc.append((T_F0+k*DT_F, sc[-1][1]+counts[cell]))
    for m in range(N_STEPS):
        h=N_STEPS-1-m; cell=path[h]
        if cell in greens: sc.append((T_R0+m*DT_R, sc[-1][1]-counts[cell]))
    total=sum(counts[c] for c in greens)
    return path,t_eat,t_dep,frames,cover,sc,total

# ---- layers ------------------------------------------------------------------
MONTHS=["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

def screen_and_labels(grid):
    s=[]
    # month labels: first column entering a new month; skip labels that would
    # crowd the previous one (fixes the JUN/JUL pile-up at the left edge)
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
    # day labels
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
            # translucent pixel bevel (works over any fill state)
            s.append(f'<path d="M{x},{y+CELL} V{y} H{x+CELL}" fill="none" stroke="#FFFFFF" stroke-opacity="0.30" stroke-width="1.6"/>')
            s.append(f'<path d="M{x},{y+CELL} H{x+CELL} V{y}" fill="none" stroke="#000000" stroke-opacity="0.28" stroke-width="1.6"/>')
    return s

def tail_dot(cx,cy,rad,fill,edge,horiz=False):
    """Nokia snake link: stepped parallelogram (2x4 with two OPPOSITE corners
    removed) with a light/dark bezel outline for texture. Cheap: 6 fill rects
    + 2 bezel polylines."""
    p=CELL/3.5                              # bigger links, allowed to overflow the cell
    lite=_shade(fill,0.36); dk=_shade(fill,-0.42)
    bmp=[(1,0),(0,1),(1,1),(0,2),(1,2),(0,3)]
    cols,rows=2,4
    def coords(c,r):
        if horiz: return (r,(cols-1-c))
        return (c,r)
    ox=cx-((rows if horiz else cols)*p)/2
    oy=cy-((cols if horiz else rows)*p)/2
    q=p+0.4
    rects=[]
    occ=set()
    for (c,r) in bmp:
        nc,nr=coords(c,r); occ.add((nc,nr))
        rects.append(f'<rect x="{px(ox+nc*p)}" y="{px(oy+nr*p)}" width="{px(q)}" height="{px(q)}" fill="{fill}"/>')
    # bezel: light on top+left exposed edges, dark on bottom+right exposed edges
    lite_seg=[]; dk_seg=[]
    for (nc,nr) in occ:
        x=ox+nc*p; y=oy+nr*p
        if (nc,nr-1) not in occ: lite_seg.append(f'M{px(x)},{px(y)} h{px(q)}')      # top
        if (nc-1,nr) not in occ: lite_seg.append(f'M{px(x)},{px(y)} v{px(q)}')      # left
        if (nc,nr+1) not in occ: dk_seg.append(f'M{px(x)},{px(y+q)} h{px(q)}')      # bottom
        if (nc+1,nr) not in occ: dk_seg.append(f'M{px(x+q)},{px(y)} v{px(q)}')      # right
    b=(f'<path d="{" ".join(lite_seg)}" stroke="{lite}" stroke-width="1.6" fill="none"/>'
       f'<path d="{" ".join(dk_seg)}" stroke="{dk}" stroke-width="1.6" fill="none"/>')
    return ''.join(rects)+b

def tail_layer(cover,static):
    if static: return []
    s=[]
    # map each cell to its predecessor/successor in the path to know orientation
    path=build_path(); idx={c:i for i,c in enumerate(path)}
    for cell,ivs in cover.items():
        if not ivs: continue
        c,r=cell
        x,y=cell_xy(c,r)
        i=idx[cell]
        prevc=path[i-1] if i>0 else cell
        nextc=path[i+1] if i+1<len(path) else cell
        # horizontal unless this cell is a row-turn (col unchanged between
        # neighbours) -> then it's the vertical drop link
        turn = (prevc[0]==cell[0]==nextc[0]) or (prevc[1]!=nextc[1] and prevc[0]==cell[0])
        horiz = not (cell[0]==prevc[0] and cell[0]==nextc[0] or cell[0]==nextc[0])
        # simpler: vertical only when the successor is directly below (drop)
        vertical = (nextc[0]==cell[0] and nextc[1]!=cell[1]) or (prevc[0]==cell[0] and prevc[1]!=cell[1])
        d=tail_dot(x+CELL/2,y+CELL/2,4.3,GREEN,None,horiz=not vertical)
        vals=["0"]; kts=["0"]
        for a,b in ivs:
            vals+=["1","0"]; kts+=[f"{kt(a):.5f}",f"{kt(b):.5f}"]
        s.append(f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" '
                 f'values="{";".join(vals)}" keyTimes="{";".join(kts)}" '
                 f'dur="{T:.2f}s" repeatCount="indefinite"/>{d}</g>')
    return s

def python_head(animate=False):
    """pixel-rhombus python head (points +x): stepped diamond body, a lighter
    top-left facet for 8-bit shading, two eyes, and a red forked tongue that
    flicks when animate=True."""
    body=_shade(PLUM,0.0)
    # stepped diamond outline (chunky 8-bit silhouette), points at +x / -x
    pts="13,0 9,-3 5,-6 0,-8 -5,-6 -9,-3 -13,0 -9,3 -5,6 0,8 5,6 9,3"
    facet="0,-8 -5,-6 -9,-3 -13,0 -6,0 0,-4"     # upper-left light facet
    tongue=('<path d="M13,0 H19 M19,0 L23,-3 M19,0 L23,3" '
            'fill="none" stroke="'+RED+'" stroke-width="2"'
            + ('><animate attributeName="d" dur="0.5s" repeatCount="indefinite" '
               'values="M13,0 H19 M19,0 L23,-3 M19,0 L23,3;'
               'M13,0 H21 M21,0 L25,-4 M21,0 L25,4;'
               'M13,0 H19 M19,0 L23,-3 M19,0 L23,3"/></path>'
               if animate else '/>'))
    return (f'{tongue}'
            f'<polygon points="{pts}" fill="{body}" stroke="{PL}" stroke-width="2.4"/>'
            f'<polygon points="{facet}" fill="{PL}" opacity="0.55"/>'
            f'<rect x="0.5" y="-4.4" width="4" height="4" fill="{WHITE}"/>'
            f'<rect x="0.5" y="0.4" width="4" height="4" fill="{WHITE}"/>'
            f'<rect x="2.3" y="-3.2" width="1.8" height="1.8" fill="{BLACK}"/>'
            f'<rect x="2.3" y="1.8" width="1.8" height="1.8" fill="{BLACK}"/>')

def head_angles(frames):
    """travel direction per keyframe: art points +x -> right=0 left=180
    down=90 up=270."""
    angs=[]
    prev=90.0
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
    # HIGHSCORE (centred, moving gradient, blinking through the window)
    hs_txt=f"HIGHSCORE! : {total}"
    hw=F.measure(hs_txt,'gb',size)
    hx=CXC-hw/2
    # vertical arcade gradient (top->bottom, like classic HIGH SCORE screens),
    # whose two ends BREATHE through the palette out of phase (RGB-keyboard feel)
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
    # RESETTING... right corner, dots loop 1->2->3
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
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" '
         f'width="{CW}" height="{CH}">']
    out+=frame()
    out+=prompt(static)
    out+=screen_and_labels(grid)
    out+=cells_layer(grid,t_eat,t_dep,static)
    out+=tail_layer(cover,static)
    out+=head_layer(frames,static)
    out+=score_layer(sc,total,static)
    out.append('</svg>')
    return ''.join(out), total

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
