"""zones.py UFO: where letters meet the alignment zones. For each zone the
font's own flat value (from x, H, l, p ...) and overshoot (from o, O ...);
a glyph whose ink edge is near a zone but neither flat nor overshooting
(nor in between by design) is listed."""
import collections
import math
import sys
import unicodedata

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

font = ufoLib2.Font.open(sys.argv[1])
cm = {u: g.name for g in font for u in g.unicodes}

slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
def bounds(name):
    p = pathops.Path(); r = DecomposingRecordingPen(font); font[name].draw(r); r.replay(p.getPen())
    return p.bounds if p.bounds != (0, 0, 0, 0) else None
def b(ch): return bounds(cm[ord(ch)])
zones = {
    "baseline": (b("x")[1], b("o")[1]), "x-height": (b("x")[3], b("o")[3]),
    "cap": (b("H")[3], b("O")[3]), "cap-base": (b("H")[1], b("O")[1]),
    "ascender": (b("l")[3], None), "descender": (b("p")[1], None),
}
if "o.sc" in font:
    ob = bounds("o.sc"); hb = bounds("h.sc")
    zones["small-cap"] = (hb[3], ob[3])
print(sys.argv[1].split("/")[-1], {k: (round(v[0]), round(v[1]) if v[1] is not None else None) for k, v in zones.items()})
found = collections.defaultdict(list)
for g in font:
    u = g.unicodes[0] if g.unicodes else None
    sc = g.name.endswith(".sc")
    if u is None and not sc:
        continue
    if u is not None and unicodedata.category(chr(u)) not in ("Lu", "Ll", "Lt", "Lo", "Nd"):
        continue
    bb = bounds(g.name)
    if not bb:
        continue
    _, y0, _, y1 = bb
    lower = u is not None and unicodedata.category(chr(u)) == "Ll" or sc
    for edge, y in (("bottom", y0), ("top", y1)):
        cands = []
        for z, (flat, over) in zones.items():
            if z == "small-cap" and not sc:
                continue
            if z in ("cap", "cap-base") and lower:
                continue
            if z in ("x-height",) and not lower:
                continue
            if z == "small-cap" and edge == "bottom":
                continue
            cands.append((abs(y - flat), z, flat, over))
        d, z, flat, over = min(cands)
        if d > 60:
            continue
        ok = abs(y - flat) <= 2 or (over is not None and abs(y - over) <= 4)
        if over is not None and min(flat, over) - 1 <= y <= max(flat, over) + 1:
            ok = ok or False  # between flat and overshoot: half an overshoot
        if not ok:
            found[(z, edge)].append((round(y - flat), g.name, chr(u) if u else g.name))
for (z, edge), items in sorted(found.items()):
    items.sort()
    print(f"  {z:10} {edge:6}: {len(items):3} glyphs off  " + " ".join(f"{c}{d:+}" for d, n, c in items[:40]) + (" ..." if len(items) > 40 else ""))
