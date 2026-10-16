"""slant.py UFO ANGLE: the lean of the long straight upright edges in each glyph,
against the italic angle; lists glyphs whose stems lean differently."""
import math
import statistics
import sys
import unicodedata

import ufoLib2

font = ufoLib2.Font.open(sys.argv[1]); target = float(sys.argv[2])
off = []
allv = []
for g in font:
    if not g.contours:
        continue
    u = g.unicodes[0] if g.unicodes else None
    if u is not None and unicodedata.category(chr(u))[0] not in "LN":
        continue
    angs = []
    for c in g.contours:
        P = list(c.points); n = len(P)
        for i, p in enumerate(P):
            q = P[(i + 1) % n]
            if p.type is None or q.type != "line":
                continue
            dx, dy = q.x - p.x, q.y - p.y
            L = math.hypot(dx, dy)
            if L < 250 or abs(dy) < 0.9 * L:
                continue
            a = math.degrees(math.atan2(dx, dy)) if dy > 0 else math.degrees(math.atan2(-dx, -dy))
            if abs(a - target) < 10:
                angs.append((L, a))
    if not angs:
        continue
    a = sum(L * a for L, a in angs) / sum(L for L, _ in angs)
    allv.append(a)
    if abs(a - target) > 1.5:
        off.append((round(a - target, 1), g.name, chr(u) if u else ""))
print(sys.argv[1].split("/")[-1], f"stems in {len(allv)} glyphs: median lean {statistics.median(allv):.2f}° (target {target}), {len(off)} more than 1.5° off")
off.sort()
print("  ", " ".join(f"{c or n}{d:+}" for d, n, c in off[:40]))
print("  ", " ".join(f"{c or n}{d:+}" for d, n, c in off[-40:]))
