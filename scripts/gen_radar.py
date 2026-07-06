#!/usr/bin/env python3
"""
Panel 4 — one L composition (prompt + trophies in the band, radar in the arm),
emitted as TWO horizontally-cut SVGs:
  panel4_band.svg — full-width band (886x189): prompt + trophy fan
  panel4_arm.svg  — arm (515x357): radar (its top rows live in the band piece;
                    float-stacked rows butt at 0px so the cut is invisible)
more(me) (static, square) floats beside the arm in the pocket.
"""
import sys, os, json, argparse, math, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fonts as F
import palette as P

WHITE=P.PALETTE["white"]; BLACK=P.PALETTE["black"]
PLUM=P.PANEL_SHADOW; PL=P.PLUM_LIGHT; PD=P.PLUM_DARK; PDEEP=P.PLUM_DEEP
GOLD=P.PANELS["radar"]
BLUEB=P.PALETTE["blackberry"]
GREEN=P.PALETTE["classic_green"]
CYAN =P.PALETTE["aqueduct_cyan"]
RED  =P.PALETTE["fireball_red"]

OFF=9; BEV=5; BW=18

# ------------------------------------------------------------- geometry ----
M=6; MT=6; ML=30; MR=22              # minimal top margin (dividers handle spacing)
PW,PH = 865,543
NW,NH = 374,369
OX,OY = ML,MT
CW = ML+PW+OFF+MR                    # 926
CH = MT+PH+OFF+M                     # arm piece height stays NH+6 = mm canvas
CUTY = OY+(PH-NH)+OFF                # 189: horizontal cut (band piece height)
ARM_W = 532                          # arm piece width (mm right edge lands on band art right)

IX0,IY0 = OX+BW, OY+BW
IX1     = OX+PW-BW                   # 853
ARM_X1  = OX+PW-NW-BW                # 478
ARM_Y1  = OY+PH-BW                   # 519
BAND_IB = OY+(PH-NH)-BW              # 162 (interior band bottom)

def px(v): return f"{v:.1f}"

def l_frame():
    s=[]
    x0,y0,x1,y1 = OX,OY,OX+PW,OY+PH
    nx,ny = x1-NW, y1-NH
    Lp=lambda dx,dy:(f"M{x0+dx},{y0+dy} H{x1+dx} V{ny+dy} H{nx+dx} V{y1+dy} "
                     f"H{x0+dx} Z")
    s.append(f'<path d="{Lp(OFF,OFF)}" fill="{PDEEP}"/>')
    s.append(f'<path d="{Lp(0,0)}" fill="{PLUM}"/>')
    b=BEV
    s.append(f'<path d="M{x0},{y0} H{x1} L{x1-b},{y0+b} H{x0+b} V{y1-b} '
             f'L{x0},{y1} Z" fill="{PL}"/>')
    s.append(f'<path d="M{x1},{y0} V{ny} H{nx} V{y1} H{x0} L{x0+b},{y1-b} '
             f'H{nx-b} V{ny-b} H{x1-b} V{y0+b} Z" fill="{PD}"/>')
    s.append(f'<path d="M{x0+BW},{y0+BW} H{x1-BW} V{ny-BW} H{nx-BW} '
             f'V{y1-BW} H{x0+BW} Z" fill="{GOLD}"/>')
    return s

# --------------------------------------------------------- typed prompt ----
PROMPT_TXT="> github.exe -RDR -TRPH"
T0=0.35; CPS=0.05
T_DONE=T0+len(PROMPT_TXT)*CPS        # 1.5s
T_PULSE=T_DONE+0.30                  # prompt starts pulsing
T_GRID=T_DONE+0.25                   # empty graph pops
T_SON=T_DONE+0.90                    # first sonar wave launches
T_POLY=T_SON+0.55                    # wave "paints" the data polygon

def corner_prompt(static):
    s=[]
    big=40
    sx,sy = IX0+14, IY0+12
    s.append(f'<rect x="{sx}" y="{sy}" width="{big}" height="{big}" fill="{WHITE}"/>')
    sm=round(big*0.57); dg=round(big*0.09)
    s.append(f'<rect x="{sx+big+dg}" y="{sy+big+dg}" width="{sm}" height="{sm}" fill="{WHITE}"/>')
    fs=28
    tx=sx+big+22
    ty=sy+big*0.5+fs*0.34
    if static:
        s.append(F.text_svg(PROMPT_TXT,'vt',fs,tx,ty,BLACK)[0])
        return s
    chars=[]
    for i,ch in enumerate(PROMPT_TXT):
        if ch==' ': continue
        xoff=tx+F.measure(PROMPT_TXT[:i],'vt',fs)
        g,_=F.text_svg(ch,'vt',fs,xoff,ty,BLACK)
        t=T0+i*CPS
        chars.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
                     f'begin="{t:.2f}s" fill="freeze"/>{g}</g>')
    s.append(f'<g>{"".join(chars)}'
             f'<animate attributeName="opacity" values="1;0.35;1" dur="1.1s" '
             f'begin="{T_PULSE:.2f}s" repeatCount="indefinite"/></g>')
    return s

def gql(token, query, variables):
    req=urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query":query,"variables":variables}).encode(),
        headers={"Authorization":f"bearer {token}","User-Agent":"radar-gen",
                 "Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

QUERY_BASE="""
query($login:String!){
  user(login:$login){
    createdAt
    followers{ totalCount }
    pullRequests{ totalCount }
    issues{ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC){
      totalCount nodes{ stargazerCount } }
    repositoriesContributedTo(
      contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,PULL_REQUEST_REVIEW]){
      totalCount }
  }
}"""

QUERY_YEAR="""
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      totalCommitContributions
      totalPullRequestReviewContributions }
  }
}"""

def fetch_stats(user, token):
    """ALL-TIME stats. contributionsCollection is capped to a 1-year window
    (GitHub restriction), so commits/reviews are summed over one query per
    account-year; PRs/issues/stars/followers have direct all-time totals."""
    import datetime as dt
    d=gql(token, QUERY_BASE, {"login":user})["data"]["user"]
    created=dt.datetime.fromisoformat(d["createdAt"].replace("Z","+00:00"))
    now=dt.datetime.now(dt.timezone.utc)
    commits=reviews=0
    a=created
    while a<now:
        b=min(a+dt.timedelta(days=365), now)
        cc=gql(token, QUERY_YEAR, {"login":user,
              "from":a.isoformat(), "to":b.isoformat()}
              )["data"]["user"]["contributionsCollection"]
        commits+=cc["totalCommitContributions"]
        reviews+=cc["totalPullRequestReviewContributions"]
        a=b
    return {
      "commits":  commits,
      "prs":      d["pullRequests"]["totalCount"],
      "issues":   d["issues"]["totalCount"],
      "reviews":  reviews,
      "stars":    sum(n["stargazerCount"] for n in d["repositories"]["nodes"]),
      "repos":    d["repositories"]["totalCount"],
      "followers":d["followers"]["totalCount"],
      "contrib":  d["repositoriesContributedTo"]["totalCount"],
    }

MOCK={"commits":412,"prs":34,"issues":9,"reviews":4,
      "stars":17,"repos":15,"followers":1,"contrib":3}

# ------------------------------------------------- rank-based scaling ------
def rank_radius(key, val):
    c,b,a,s = THRESH[key]
    pts=[(0,0.0),(c,0.25),(b,0.50),(a,0.75),(s,1.00)]
    if val>=s: return 1.0
    for (x0,r0),(x1,r1) in zip(pts,pts[1:]):
        if val<x1:
            if x1==x0: return r1
            return r0+(r1-r0)*(val-x0)/(x1-x0)
    return 1.0

# -------------------------------------------------------------- trophies ---
TROPHIES_SHOW=["stars","commits","prs","followers"]

LABELS={"stars":"STARS","commits":"COMMITS","prs":"PRS","issues":"ISSUES",
        "reviews":"REVIEWS","followers":"FOLLOWERS","repos":"REPOS",
        "contrib":"CONTRIB"}
RANKS=[("S",P.PALETTE["fireball_red"]),("A",CYAN),("B",GREEN),("C",WHITE)]
THRESH={
 "stars":(1,5,20,50), "commits":(1,100,400,1000), "prs":(1,10,30,100),
 "issues":(1,5,20,50), "reviews":(1,5,20,50), "followers":(1,10,40,100),
 "repos":(1,10,25,50), "contrib":(1,3,10,25),
}
def rank_of(metric,val):
    c,b,a,s = THRESH[metric]
    if val>=s: return RANKS[0]
    if val>=a: return RANKS[1]
    if val>=b: return RANKS[2]
    if val>=c: return RANKS[3]
    return ("-", PD)

def _shade(hexc,f):
    r=int(hexc[1:3],16); g=int(hexc[3:5],16); b=int(hexc[5:7],16)
    t=255 if f>0 else 0; f=abs(f)
    mix=lambda v:int(round(v+(t-v)*f))
    return f"#{mix(r):02X}{mix(g):02X}{mix(b):02X}"

TROPHY=[
 "XXXXXXX",
 "XXXXXXX",
 ".XXXXX.",
 "..XXX..",
 "...X...",
 "..XXX..",
]
CELL=8                                  # bigger trophies

def draw_trophy(gx, ty, key, val, static=True, glim_begin=None):
    letter,colr=rank_of(key,val)
    lite=_shade(colr,0.30); dark=_shade(colr,-0.25)
    cell=CELL; tw=7*cell; ox=gx-tw/2
    cup=[]
    for r,row in enumerate(TROPHY):
        rowcol = lite if r<2 else (colr if r<4 else dark)
        cells=[c for c,ch in enumerate(row) if ch=='X']
        for c in cells:
            fill = dark if c==cells[-1] else rowcol
            cup.append(f'<rect x="{px(ox+c*cell)}" y="{px(ty+r*cell)}" '
                       f'width="{cell}" height="{cell}" fill="{fill}"/>')
    glint=(f'<rect x="{px(ox+1*cell)}" y="{px(ty)}" width="{cell}" height="{cell}" fill="{WHITE}"/>'
           f'<rect x="{px(ox+1*cell)}" y="{px(ty+cell)}" width="{cell}" height="{cell*0.5}" fill="{WHITE}"/>')
    if static or glim_begin is None:
        cup.append(glint)
    else:
        cup.append(f'<g>{glint}<animate attributeName="opacity" '
                   f'values="1;1;0.15;1;1" keyTimes="0;0.42;0.5;0.58;1" '
                   f'dur="2.8s" begin="{glim_begin:.2f}s" '
                   f'repeatCount="indefinite"/></g>')
    cup.append(f'<rect x="{px(ox-cell)}" y="{px(ty)}" width="{cell}" height="{cell*2}" fill="{dark}"/>')
    cup.append(f'<rect x="{px(ox+tw)}" y="{px(ty)}" width="{cell}" height="{cell*2}" fill="{dark}"/>')
    cup.append(F.text_svg(letter,'gb',18,gx,ty+2*cell+14,BLACK,anchor='middle')[0])
    pw=max(tw+4*cell, F.measure(LABELS[key],'gb',10)+18)
    pxq=gx-pw/2; pyq=ty+6*cell+3
    edge=_shade(GOLD,-0.35)
    cup.append(f'<rect x="{px(pxq)}" y="{px(pyq)}" width="{px(pw)}" height="34" '
               f'fill="{BLACK}" stroke="{edge}" stroke-width="2"/>')
    cup.append(f'<rect x="{px(pxq)}" y="{px(pyq)}" width="{px(pw)}" height="3" fill="{edge}"/>')
    cup.append(F.text_svg(LABELS[key],'gb',10,gx,pyq+15,WHITE,anchor='middle')[0])
    cup.append(F.text_svg(str(val),'vt',17,gx,pyq+30,WHITE,anchor='middle')[0])
    return cup, pw

def trophies(stats, static):
    """bigger, spread fan in the band's right region. Animated entry: centre
    card(s) pop first, others fan outward from centre; then glimmer loop."""
    s=[]
    items=TROPHIES_SHOW; n=len(items)
    ty=IY0+12
    TH=6*CELL+3+34
    step=30.0/n
    centre=(n-1)/2.0
    pitch=64                             # spread out (still overlapping)
    outer=max(abs(0-centre),abs(n-1-centre))*step
    Rpiv=( (n-1)/2.0*pitch )/max(math.sin(math.radians(outer)),1e-6) if n>1 else 0
    gxc=((OX+PW-NW)+IX1)/2               # centred over the pocket column
    pivx, pivy = gxc, ty+TH+Rpiv
    for i,key in enumerate(items):
        tilt=(i-centre)*step
        d=abs(i-centre)
        cup,_=draw_trophy(gxc,ty,key,stats[key], static=static,
                          glim_begin=None if static else T_DONE+2.2+i*0.5)
        if static:
            s.append(f'<g transform="rotate({tilt:.2f} {px(pivx)} {px(pivy)})">{"".join(cup)}</g>')
        else:
            b=T_DONE+0.35+d*0.25          # centre first, then outward
            s.append(
              f'<g opacity="0"><set attributeName="opacity" to="1" '
              f'begin="{b:.2f}s" fill="freeze"/>'
              f'<g transform="rotate(0 {px(pivx)} {px(pivy)})">'
              f'<animateTransform attributeName="transform" type="rotate" '
              f'values="0 {px(pivx)} {px(pivy)};{tilt:.2f} {px(pivx)} {px(pivy)}" '
              f'begin="{b:.2f}s" dur="0.45s" calcMode="spline" '
              f'keySplines="0.2 0.8 0.3 1" fill="freeze"/>'
              f'{"".join(cup)}</g></g>')
    return s

# ---------------------------------------------------------------- radar ----
def radar(stats, static):
    """sequence: empty grid pops (T_GRID) -> first sonar wave (T_SON) paints
    the polygon (T_POLY) -> resting loop of waves over the static radar."""
    s=[]
    Rmax=120; LS=13
    lext=12+F.measure("REVIEWS",'gb',LS)
    rext=12+F.measure("PRS",'gb',LS)
    cx=(IX0+ARM_X1)/2 + (lext-rext)/2
    cy=(CUTY+ARM_Y1)/2                   # radar lives FULLY in the arm piece (below the cut)
    axes=[("COMMITS","commits",(0,-1)),
          ("PRS","prs",(1,0)),
          ("ISSUES","issues",(0,1)),
          ("REVIEWS","reviews",(-1,0))]
    # grid (rings + axis lines) in RELATIVE coords so it can pop from centre
    grid=[]
    for k in (0.25,0.5,0.75,1.0):
        r=Rmax*k
        wd = 3 if k==1.0 else 1.5
        grid.append(f'<polygon points="0,{px(-r)} {px(r)},0 0,{px(r)} {px(-r)},0" '
                    f'fill="none" stroke="{BLACK}" stroke-width="{wd}"/>')
    grid.append(f'<line x1="0" y1="{px(-Rmax)}" x2="0" y2="{px(Rmax)}" stroke="{BLACK}" stroke-width="1.5"/>')
    grid.append(f'<line x1="{px(-Rmax)}" y1="0" x2="{px(Rmax)}" y2="0" stroke="{BLACK}" stroke-width="1.5"/>')
    rel=[]
    for _,k,(dx,dy) in axes:
        v=rank_radius(k, stats[k]); r=Rmax*max(v,0.04)
        rel.append((dx*r, dy*r))
    pts=" ".join(f"{px(a)},{px(b)}" for a,b in rel)
    poly=(f'<polygon points="{pts}" fill="{BLUEB}" fill-opacity="0.78" '
          f'stroke="{BLACK}" stroke-width="3"/>')
    dots="".join(f'<rect x="{px(a-4)}" y="{px(b-4)}" width="8" height="8" '
                 f'fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>' for a,b in rel)
    labs=[]; vals_static=[]; ticks=[]
    lab=[("COMMITS","commits", cx, cy-Rmax-26, 'middle', cx, cy-Rmax-8),
         ("PRS","prs",     cx+Rmax+12, cy-12, 'start', cx+Rmax+12, cy+8),
         ("ISSUES","issues",  cx, cy+Rmax+22, 'middle', cx, cy+Rmax+40),
         ("REVIEWS","reviews", cx-Rmax-12, cy-12, 'end', cx-Rmax-12, cy+8)]
    for name,key,lx,ly,anc,vx,vy in lab:
        labs.append(F.text_svg(name,'gb',LS,lx,ly,BLACK,anchor=anc)[0])
        N=stats[key]
        vals_static.append(F.text_svg(str(N),'vt',18,vx,vy,BLACK,anchor=anc)[0])
        # animated: value TICKS UP from 0 while the wave reveals this axis's
        # vertex, then freezes at the real number forever
        vfrac=max(rank_radius(key,N),0.04)
        t_end=T_SON+3.4*vfrac
        steps=12
        seq=[]
        for i in range(steps+1):
            v=round(N*i/steps)
            t=T_SON+(t_end-T_SON)*i/steps
            if seq and seq[-1][1]==v: continue
            seq.append((t,v))
        for j,(t,v) in enumerate(seq):
            g=F.text_svg(str(v),'vt',18,vx,vy,BLACK,anchor=anc)[0]
            offs=(f'<set attributeName="opacity" to="0" begin="{seq[j+1][0]:.2f}s" fill="freeze"/>'
                  if j+1<len(seq) else '')
            ticks.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
                         f'begin="{t:.2f}s" fill="freeze"/>{offs}{g}</g>')
    if static:
        s.append(f'<g transform="translate({px(cx)},{px(cy)})">{"".join(grid)}{poly}{dots}</g>')
        s+=labs; s+=vals_static
        return s
    # 1) empty grid + labels pop
    s.append(
      f'<g transform="translate({px(cx)},{px(cy)})">'
      f'<g transform="scale(0)">'
      f'<animateTransform attributeName="transform" type="scale" '
      f'values="0;1.06;1" keyTimes="0;0.8;1" dur="0.55s" begin="{T_GRID:.2f}s" '
      f'calcMode="spline" keySplines="0.2 0.7 0.3 1;0.4 0 0.6 1" fill="freeze"/>'
      f'{"".join(grid)}'
      # 2) data polygon GROWS with the first sonar wave: same begin+duration,
      #    so its vertices ride just inside the expanding wavefront
      f'<g transform="scale(0)">'
      f'<animateTransform attributeName="transform" type="scale" '
      f'values="0;1" dur="3.4s" begin="{T_SON:.2f}s" fill="freeze"/>'
      f'{poly}{dots}</g>'
      # 3) sonar waves, from the first (painting) one onward
      f'<g><animateTransform attributeName="transform" type="scale" '
      f'values="0.1;1" dur="3.4s" begin="{T_SON:.2f}s" '
      f'repeatCount="indefinite"/>'
      f'<polygon points="0,{px(-Rmax)} {px(Rmax)},0 0,{px(Rmax)} {px(-Rmax)},0" '
      f'fill="none" stroke="{BLUEB}" stroke-width="4" stroke-opacity="0">'
      f'<animate attributeName="stroke-opacity" values="0.55;0" '
      f'dur="3.4s" begin="{T_SON:.2f}s" repeatCount="indefinite"/>'
      f'</polygon></g>'
      f'</g></g>')
    s.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
             f'begin="{T_GRID:.2f}s" fill="freeze"/>{"".join(labs)}</g>')
    s.append(''.join(ticks))
    return s

# ----------------------------------------------------------------- main ----
def compose(stats, static=False):
    body=[]
    body+=l_frame()
    body+=corner_prompt(static)
    body+=trophies(stats, static)
    body+=radar(stats, static)
    return ''.join(body)

def build_band(stats, static=False):
    body=compose(stats, static)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CUTY}" '
            f'width="{CW}" height="{CUTY}">{body}</svg>')

def build_arm(stats, static=False):
    body=compose(stats, static)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 {CUTY} {ARM_W} {CH-CUTY}" '
            f'width="{ARM_W}" height="{CH-CUTY}">{body}</svg>')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("RADAR_USER","McVarHQ"))
    ap.add_argument("--out",  default="panel4_band.svg")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--static", action="store_true")
    a=ap.parse_args()
    if a.mock:
        stats=MOCK
    else:
        token=os.environ.get("GITHUB_TOKEN")
        if not token:
            print("no GITHUB_TOKEN; falling back to --mock stats", file=sys.stderr)
            stats=MOCK
        else:
            stats=fetch_stats(a.user, token)
    band=build_band(stats, static=a.static)
    open(a.out,'w').write(band)
    arm_out=os.path.join(os.path.dirname(a.out) or ".",
                         os.path.basename(a.out).replace("band","arm"))
    arm=build_arm(stats, static=a.static)
    open(arm_out,'w').write(arm)
    print(f"wrote {a.out} ({len(band)}B) + {arm_out} ({len(arm)}B)  stats={stats}")

if __name__=="__main__":
    main()
