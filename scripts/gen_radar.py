#!/usr/bin/env python3
"""
Panel 4 generator — GitHub activity RADAR + TROPHIES in the Game Boy theme.

Runs inside a GitHub Action (GITHUB_TOKEN -> GraphQL) on a schedule, renders
panel4_radar.svg, and the workflow commits it so the profile README stays
fresh without any live elements in the SVG.

Usage:
  python scripts/gen_radar.py --user McVarHQ --out panel4_radar.svg
  python scripts/gen_radar.py --mock --out panel4_radar.svg          # no API
  python scripts/gen_radar.py --mock --static --out preview.svg      # no SMIL
"""
import sys, os, json, argparse, math, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fonts as F
import palette as P

# ---------------------------------------------------------------- theme ----
WHITE=P.PALETTE["white"]; BLACK=P.PALETTE["black"]
PLUM=P.PANEL_SHADOW; PL=P.PLUM_LIGHT; PD=P.PLUM_DARK; PDEEP=P.PLUM_DEEP
GOLD=P.PANELS["radar"]                  # curry gold interior  #D7A32E
BLUEB=P.PALETTE["blackberry"]           # radar polygon        #31407B
GREEN=P.PALETTE["classic_green"]
CYAN =P.PALETTE["aqueduct_cyan"]
RED  =P.PALETTE["fireball_red"]

OFF=9; BEV=5; BW=18                     # locked bevel recipe (make_panels.py)

# ------------------------------------------------------------- geometry ----
# native 880-wide canvas to match the other panels' display scale.
M=20
PW,PH = 840,490                         # L outer size (720x420 spec x 7/6)
NW,NH = 350,350                         # bottom-right notch (300x300 x 7/6)
CW = M*2+PW+OFF-9                       # 880
CH = M+PH+OFF+M                         # canvas
OX,OY = M,M

def l_frame():
    """Locked raised-bevel L (deep shadow, plum base, light/dark bevel, fill)."""
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

# interior bounds (abs): top band + left arm
IX0,IY0 = OX+BW, OY+BW                          # 38,38
IX1     = OX+PW-BW                              # 822
BAND_B  = OY+PH-NH                              # 160  (interior band bottom)
ARM_X1  = OX+PW-NW-BW                           # 472
ARM_Y1  = OY+PH-BW                              # 492

def corner_prompt(static):
    """white corner squares + big pulsing prompt (panel-3 style, black)."""
    s=[]
    big=40
    sx,sy = IX0+14, IY0+12
    s.append(f'<rect x="{sx}" y="{sy}" width="{big}" height="{big}" fill="{WHITE}"/>')
    sm=round(big*0.57); dg=round(big*0.09)
    s.append(f'<rect x="{sx+big+dg}" y="{sy+big+dg}" width="{sm}" height="{sm}" fill="{WHITE}"/>')
    fs=40
    tx=sx+big+round(big*1.0); ty=sy+big*0.5+fs*0.34
    g,w=F.text_svg("> github.exe -RADAR",'vt',fs,tx,ty,BLACK)
    if static: s.append(g)
    else: s.append(f'<g><animate attributeName="opacity" values="1;0.35;1" '
                   f'dur="1.1s" repeatCount="indefinite"/>{g}</g>')
    return s, tx+w

# ---------------------------------------------------------------- stats ----
def gql(token, query, variables):
    req=urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query":query,"variables":variables}).encode(),
        headers={"Authorization":f"bearer {token}","User-Agent":"radar-gen",
                 "Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

QUERY="""
query($login:String!){
  user(login:$login){
    followers{ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC){
      totalCount nodes{ stargazerCount } }
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions }
  }
}"""

def fetch_stats(user, token):
    d=gql(token, QUERY, {"login":user})["data"]["user"]
    cc=d["contributionsCollection"]
    return {
      "commits":  cc["totalCommitContributions"],
      "prs":      cc["totalPullRequestContributions"],
      "issues":   cc["totalIssueContributions"],
      "reviews":  cc["totalPullRequestReviewContributions"],
      "stars":    sum(n["stargazerCount"] for n in d["repositories"]["nodes"]),
      "repos":    d["repositories"]["totalCount"],
      "followers":d["followers"]["totalCount"],
    }

MOCK={"commits":412,"prs":18,"issues":9,"reviews":4,
      "stars":6,"repos":15,"followers":12}

# radar axis caps: value/cap (capped at 1.0) = how far the vertex reaches.
CAPS={"commits":600,"prs":40,"issues":30,"reviews":20}

# ---------------------------------------------------------------- radar ----
def px(v): return f"{v:.1f}"

def radar(stats, static):
    """4-axis pixel spider chart in the L's left arm."""
    s=[]
    cx=(IX0+ARM_X1)/2                    # arm centre x
    cy=(BAND_B+ARM_Y1)/2+6
    Rmax=132
    axes=[("COMMITS","commits",(0,-1)),  # up
          ("PRS","prs",(1,0)),           # right
          ("ISSUES","issues",(0,1)),     # down
          ("REVIEWS","reviews",(-1,0))]  # left
    # rings (25/50/75/100%) as diamonds
    for k in (0.25,0.5,0.75,1.0):
        r=Rmax*k
        pts=f"{px(cx)},{px(cy-r)} {px(cx+r)},{px(cy)} {px(cx)},{px(cy+r)} {px(cx-r)},{px(cy)}"
        wd = 3 if k==1.0 else 1.5
        s.append(f'<polygon points="{pts}" fill="none" stroke="{BLACK}" '
                 f'stroke-width="{wd}"/>')
    # axis lines
    s.append(f'<line x1="{px(cx)}" y1="{px(cy-Rmax)}" x2="{px(cx)}" y2="{px(cy+Rmax)}" stroke="{BLACK}" stroke-width="1.5"/>')
    s.append(f'<line x1="{px(cx-Rmax)}" y1="{px(cy)}" x2="{px(cx+Rmax)}" y2="{px(cy)}" stroke="{BLACK}" stroke-width="1.5"/>')
    # data polygon (relative coords so it can grow from the centre)
    rel=[]
    for _,k,(dx,dy) in axes:
        v=min(1.0, stats[k]/CAPS[k]); r=Rmax*max(v,0.04)
        rel.append((dx*r, dy*r))
    pts=" ".join(f"{px(a)},{px(b)}" for a,b in rel)
    poly=(f'<polygon points="{pts}" fill="{BLUEB}" fill-opacity="0.78" '
          f'stroke="{BLACK}" stroke-width="3"/>')
    dots="".join(f'<rect x="{px(a-4)}" y="{px(b-4)}" width="8" height="8" '
                 f'fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>' for a,b in rel)
    if static:
        s.append(f'<g transform="translate({px(cx)},{px(cy)})">{poly}{dots}</g>')
    else:
        s.append(
          f'<g transform="translate({px(cx)},{px(cy)})">'
          f'<g transform="scale(0)">'
          f'<animateTransform attributeName="transform" type="scale" '
          f'values="0;1.06;1" keyTimes="0;0.8;1" dur="0.9s" begin="0.5s" '
          f'calcMode="spline" keySplines="0.2 0.7 0.3 1;0.4 0 0.6 1" fill="freeze"/>'
          f'{poly}{dots}</g></g>')
    # labels + counts
    lab=[("COMMITS", cx, cy-Rmax-26, 'middle', stats["commits"], cx, cy-Rmax-8),
         ("PRS",     cx+Rmax+14, cy-14, 'start', stats["prs"], cx+Rmax+14, cy+6),
         ("ISSUES",  cx, cy+Rmax+22, 'middle', stats["issues"], cx, cy+Rmax+40),
         ("REVIEWS", cx-Rmax-14, cy-14, 'end', stats["reviews"], cx-Rmax-14, cy+6)]
    for name,lx,ly,anc,val,vx,vy in lab:
        s.append(F.text_svg(name,'gb',15,lx,ly,BLACK,anchor=anc)[0])
        s.append(F.text_svg(str(val),'vt',20,vx,vy,BLACK,anchor=anc)[0])
    s.append(F.text_svg("LAST 12 MONTHS",'vt',17,cx,ARM_Y1-10,BLACK,anchor='middle')[0])
    return s

# -------------------------------------------------------------- trophies ---
TROPHY=[  # pixel bitmap, X = cup cell
 "XXXXXXX",
 "XXXXXXX",
 ".XXXXX.",
 "..XXX..",
 "...X...",
 "..XXX..",
 ".XXXXX.",
]
RANKS=[("S",P.PALETTE["fireball_red"]),("A",CYAN),("B",GREEN),("C",WHITE)]
THRESH={ # metric: (C,B,A,S) minimums
 "stars":(1,5,20,50), "commits":(1,100,400,1000), "prs":(1,10,30,100),
 "followers":(1,10,40,100),
}
def rank_of(metric,val):
    c,b,a,s = THRESH[metric]
    if val>=s: return RANKS[0]
    if val>=a: return RANKS[1]
    if val>=b: return RANKS[2]
    if val>=c: return RANKS[3]
    return ("-", PD)

def trophies(stats, static, x_from):
    """compact trophy row in the top band, right of the prompt."""
    s=[]
    items=[("STARS","stars"),("COMMITS","commits"),
           ("PRS","prs"),("FOLLOWERS","followers")]
    cell=6; tw=7*cell                     # 42px cup
    slot=(IX1-14-x_from)/len(items)
    for i,(label,key) in enumerate(items):
        val=stats[key]; letter,colr=rank_of(key,val)
        gx=x_from+slot*i+slot/2           # slot centre
        ty=IY0+10
        cup=[]
        ox=gx-tw/2
        for r,row in enumerate(TROPHY):
            for c,ch in enumerate(row):
                if ch=='X':
                    cup.append(f'<rect x="{px(ox+c*cell)}" y="{px(ty+r*cell)}" '
                               f'width="{cell}" height="{cell}" fill="{colr}"/>')
        # handles
        cup.append(f'<rect x="{px(ox-cell)}" y="{px(ty)}" width="{cell}" height="{cell*2}" fill="{colr}"/>')
        cup.append(f'<rect x="{px(ox+tw)}" y="{px(ty)}" width="{cell}" height="{cell*2}" fill="{colr}"/>')
        # base
        cup.append(f'<rect x="{px(ox+cell)}" y="{px(ty+7*cell)}" width="{tw-2*cell}" height="{cell}" fill="{BLACK}"/>')
        # rank letter on the cup
        cup.append(F.text_svg(letter,'gb',15,gx,ty+2*cell+12,BLACK,anchor='middle')[0])
        # label + value
        cup.append(F.text_svg(label,'gb',9,gx,ty+8*cell+13,BLACK,anchor='middle')[0])
        cup.append(F.text_svg(str(val),'vt',16,gx,ty+8*cell+30,BLACK,anchor='middle')[0])
        if static:
            s.append(f'<g>{"".join(cup)}</g>')
        else:
            b=0.6+i*0.18
            s.append(f'<g opacity="0"><set attributeName="opacity" to="1" '
                     f'begin="{b:.2f}s" fill="freeze"/>{"".join(cup)}</g>')
    return s

# ----------------------------------------------------------------- main ----
def build(stats, static=False):
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" '
         f'width="{CW}" height="{CH}">']
    out+=l_frame()
    cp,pend=corner_prompt(static)
    out+=cp
    out+=trophies(stats, static, max(pend+26, IX0+400))
    out+=radar(stats, static)
    out.append('</svg>')
    return ''.join(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("RADAR_USER","McVarHQ"))
    ap.add_argument("--out",  default="panel4_radar.svg")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--static", action="store_true",
                    help="no SMIL (for raster preview)")
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
    svg=build(stats, static=a.static)
    open(a.out,'w').write(svg)
    print(f"wrote {a.out}  ({len(svg)} bytes)  stats={stats}")

if __name__=="__main__":
    main()
