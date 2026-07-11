
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import palette as P

COLORS=[P.PALETTE["curry_gold"], P.PALETTE["fireball_red"],
        P.PALETTE["aqueduct_cyan"], P.PALETTE["classic_green"],
        P.PALETTE["ipa_D1C02B"], P.PLUM_LIGHT, P.PALETTE["blackberry"]]
CURSOR=P.PLUM_LIGHT

ML=30; MR=22; OFF=9; PW=865; CW=ML+PW+OFF+MR
DASH_W=14; DASH_H=6; GAP=8; PITCH=DASH_W+GAP
VTOP=int(os.environ.get('VTOP','0')); VBOT=int(os.environ.get('VBOT','0'))
BASE=16; CH=BASE+VTOP+VBOT; CY=BASE/2+VTOP

def px(v): return f"{v:.1f}"

def _sh(hexc,f):
    r=int(hexc[1:3],16); g=int(hexc[3:5],16); b=int(hexc[5:7],16)
    t=255 if f>0 else 0; f=abs(f)
    m=lambda v:int(round(v+(t-v)*f))
    return f"#{m(r):02X}{m(g):02X}{m(b):02X}"

def build(phase=0.0):
    x0=ML; x1=ML+PW; span=x1-x0
    n=int((span+GAP)//PITCH)
    x0=ML+(span-(n*PITCH-GAP))/2
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}">']
    dash_y=CY-DASH_H/2
    for i in range(n):
        c=COLORS[i%len(COLORS)]
        x=x0+i*PITCH
        s.append(f'<rect x="{px(x)}" y="{px(dash_y)}" width="{DASH_W}" height="{DASH_H}" rx="1" fill="{c}"/>')

    cw=DASH_W*2+GAP+6; ch=DASH_H+4
    lite=_sh(CURSOR,0.34); dk=_sh(CURSOR,-0.36)
    left=x0-3; right=x0+(n-1)*PITCH+DASH_W-cw+3
    cyt=CY-ch/2

    beg=f' begin="-{phase:.2f}s"' if phase>0 else ''
    cur=(f'<g>'
         f'<rect x="0" y="{px(cyt)}" width="{cw}" height="{ch}" rx="1" fill="{CURSOR}"/>'
         f'<rect x="0" y="{px(cyt)}" width="{cw}" height="1.4" fill="{lite}"/>'
         f'<rect x="0" y="{px(cyt)}" width="1.4" height="{ch}" fill="{lite}"/>'
         f'<rect x="0" y="{px(cyt+ch-1.4)}" width="{cw}" height="1.4" fill="{dk}"/>'
         f'<rect x="{px(cw-1.4)}" y="{px(cyt)}" width="1.4" height="{ch}" fill="{dk}"/>'
         f'<animateTransform attributeName="transform" type="translate" '
         f'values="{px(left)},0;{px(right)},0;{px(left)},0" '
         f'keyTimes="0;0.5;1" dur="3.2s" calcMode="spline" '
         f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1" repeatCount="indefinite"{beg}/>'
         f'</g>')
    s.append(cur)
    s.append('</svg>')
    return ''.join(s)

def main():

    out=os.environ.get("OUT","divider.svg")
    base=os.path.dirname(out)
    stem=os.path.join(base,'divider') if base else 'divider'
    files=[(out,0.0),(f'{stem}2.svg',3.2/3),(f'{stem}3.svg',2*3.2/3)]
    for fn,ph in files:
        open(fn,'w').write(build(phase=ph))
        print(f"wrote {fn} {CW}x{CH} phase=-{ph:.2f}s")

if __name__=="__main__":
    main()
