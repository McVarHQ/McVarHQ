#!/usr/bin/env python3
"""
Render text as SVG vector outlines using the two project fonts, so custom
typefaces survive GitHub's <img>-SVG sandbox (which blocks embedded fonts).
"""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import html

import os
_FD = os.environ.get('FONT_DIR', os.path.join(os.path.dirname(__file__), '..', 'fonts'))
FONTS = {
    'gb': os.path.join(_FD, 'Early_GameBoy.ttf'),   # Early-GameBoy (headings)
    'vt': os.path.join(_FD, 'VT323-Regular.ttf'),   # VT323 (> code lines)
}
_cache = {}

def _load(key):
    if key not in _cache:
        f = TTFont(FONTS[key])
        _cache[key] = (f, f.getBestCmap(), f.getGlyphSet(),
                       f['hmtx'], f['head'].unitsPerEm, f['hhea'])
    return _cache[key]

def measure(s, key, size):
    f, cmap, gs, hmtx, upm, hhea = _load(key)
    sc = size / upm
    w = 0
    for ch in s:
        gn = cmap.get(ord(ch))
        if gn is None:
            w += 0.5 * upm * sc; continue
        w += hmtx[gn][0] * sc
    return w

def ascent(key, size):
    f, cmap, gs, hmtx, upm, hhea = _load(key)
    return hhea.ascent * size / upm

def text_svg(s, key, size, x, y, fill, anchor='start', extra_tracking=0.0,
             opacity=None, _id=None):
    """y is the BASELINE. extra_tracking in px added per glyph."""
    f, cmap, gs, hmtx, upm, hhea = _load(key)
    sc = size / upm
    total = measure(s, key, size) + extra_tracking * max(0, len(s) - 1)
    if anchor == 'middle': x -= total / 2
    elif anchor == 'end':  x -= total
    glyphs = []
    penx = 0.0  # font units
    for ch in s:
        gn = cmap.get(ord(ch))
        if gn and ch != ' ':
            pen = SVGPathPen(gs)
            gs[gn].draw(pen)
            d = pen.getCommands()
            if d:
                glyphs.append(f'<path transform="translate({penx:.1f},0)" d="{d}"/>')
        adv = (hmtx[gn][0] if gn else 0.5 * upm)
        penx += adv + (extra_tracking / sc)
    op = f' opacity="{opacity}"' if opacity is not None else ''
    idattr = f' id="{_id}"' if _id else ''
    return (f'<g{idattr} fill="{fill}"{op} transform="translate({x:.2f},{y:.2f}) '
            f'scale({sc:.5f},{-sc:.5f})">{"".join(glyphs)}</g>'), total

if __name__ == "__main__":
    g, w = text_svg("VAROON", 'gb', 60, 10, 70, '#803F64')
    print("width", round(w,1), "len", len(g))
    g2, w2 = text_svg("> boot.sys", 'vt', 24, 10, 30, '#000000')
    print("vt width", round(w2,1))
