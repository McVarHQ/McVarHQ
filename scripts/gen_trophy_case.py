#!/usr/bin/env python3
"""
Trophy case — renders EVERY available trophy with your current value + rank
(S/A/B/C) in one SVG, so you can pick which ones the radar panel should show.

Pick by editing TROPHIES_SHOW at the top of scripts/gen_radar.py, e.g.:
    TROPHIES_SHOW=["stars","commits","prs","followers"]

Runs in the same workflow as the radar (same stats fetch). Also writes a
markdown table (trophy_case.md) next to the SVG.

Usage:
  python scripts/gen_trophy_case.py --out trophy_case.svg          # real stats
  python scripts/gen_trophy_case.py --mock --out trophy_case.svg   # no API
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fonts as F
import palette as P
import gen_radar as G   # reuse theme, stats fetch, trophy drawing, thresholds

WHITE=P.PALETTE["white"]; BLACK=P.PALETTE["black"]
PLUM=P.PANEL_SHADOW; PL=P.PLUM_LIGHT; PD=P.PLUM_DARK; PDEEP=P.PLUM_DEEP
GOLD=P.PANELS["radar"]
OFF,BEV,BW = G.OFF, G.BEV, G.BW

ORDER=["stars","commits","prs","issues","reviews","followers","repos","contrib"]

def build(stats):
    # simple rect panel, same locked bevel recipe, 2 rows x 4 trophies
    M=20; PW=840
    COLS=4; SLOT=PW//COLS
    ROWH=150
    PH=BW*2+70+2*ROWH
    CW=M*2+PW+OFF-9; CH=M+PH+OFF+M
    OX=OY=M
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}">']
    x0,y0,x1,y1=OX,OY,OX+PW,OY+PH
    s.append(f'<rect x="{x0+OFF}" y="{y0+OFF}" width="{PW}" height="{PH}" fill="{PDEEP}"/>')
    s.append(f'<rect x="{x0}" y="{y0}" width="{PW}" height="{PH}" fill="{PLUM}"/>')
    b=BEV
    s.append(f'<path d="M{x0},{y0} H{x1} L{x1-b},{y0+b} H{x0+b} V{y1-b} L{x0},{y1} Z" fill="{PL}"/>')
    s.append(f'<path d="M{x1},{y0} V{y1} H{x0} L{x0+b},{y1-b} H{x1-b} V{y0+b} Z" fill="{PD}"/>')
    s.append(f'<rect x="{x0+BW}" y="{y0+BW}" width="{PW-2*BW}" height="{PH-2*BW}" fill="{GOLD}"/>')
    # header prompt
    big=32; sx,sy=x0+BW+14,y0+BW+12
    s.append(f'<rect x="{sx}" y="{sy}" width="{big}" height="{big}" fill="{WHITE}"/>')
    fs=26
    g,_=F.text_svg("> trophy.case --all",'vt',fs,sx+big+26,sy+big*0.5+fs*0.34,BLACK)
    s.append(g)
    # trophies grid with rank thresholds note
    top=y0+BW+70
    for i,key in enumerate(ORDER):
        r,c = divmod(i,COLS)
        gx = x0+BW+SLOT*c+SLOT/2-BW
        ty = top+r*ROWH
        cup,_=G.draw_trophy(gx,ty,key,stats[key])
        s.append(f'<g>{"".join(cup)}</g>')
        # thresholds line under each: C/B/A/S cutoffs
        cth,bth,ath,sth=G.THRESH[key]
        s.append(F.text_svg(f"C{cth} B{bth} A{ath} S{sth}",'vt',14,gx,ty+6*6+3+28+16,BLACK,anchor='middle')[0])
    s.append('</svg>')
    return ''.join(s)

def table(stats):
    rows=["| trophy | value | rank | thresholds (C/B/A/S) |","|---|---|---|---|"]
    for key in ORDER:
        letter,_=G.rank_of(key,stats[key])
        c,b,a,sx=G.THRESH[key]
        rows.append(f"| {G.LABELS[key]} | {stats[key]} | **{letter}** | {c}/{b}/{a}/{sx} |")
    rows.append("")
    rows.append("Pick trophies by editing `TROPHIES_SHOW` in `scripts/gen_radar.py`.")
    return "\n".join(rows)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("RADAR_USER","McVarHQ"))
    ap.add_argument("--out",  default="trophy_case.svg")
    ap.add_argument("--mock", action="store_true")
    a=ap.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if a.mock or not token:
        stats=G.MOCK
    else:
        stats=G.fetch_stats(a.user, token)
    open(a.out,'w').write(build(stats))
    md=os.path.splitext(a.out)[0]+".md"
    open(md,'w').write(table(stats))
    print(f"wrote {a.out} + {md}  stats={stats}")

if __name__=="__main__":
    main()
