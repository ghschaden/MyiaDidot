"""The Regular's `attach` family mended letter by letter (longtail.md family 6,
2026-11-24): no fault the operation shares, each a node of its own.

    python scripts/regular_attach.py UFO [--small-caps]

(--small-caps: step 4 alone, on letters already mended.)

1. The asterisk's four smooth nodes where the arms meet (2.3 degrees) put
   in line; ⁂, made of it at 0.55, and Ʈ (whose ball derive.curl now puts
   on the outer edge's normal: its 6.2 degree corner gone) made again by
   derive.py --redraft.
2. Ɲ: the ȷ tail's edges lean a degree more than N's stem, a kink where
   they meet (280,80 and 344,60): the tail's top nodes moved onto N's edge
   lines carried down, the nodes between dropped.
3. The other corners and broken smooth nodes: smooth_joins.align (the
   handles put in line with the line or with each other).
4. ɲ.sc ʝ.sc ϗ.sc, enlarged from Ɲ Ʝ Ϗ, made again on them (ϗ.sc's new
   smooth node at 836,-269 aligned).

The Regular's derived letters are kept once made (derive.py), so this
mends the kept glyphs; their recipes are not changed by it. Run once on
the Regular, then make normalize; the Bold and the italics follow in
make generate.
"""
import math
import subprocess
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smooth_joins  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DRAFT_KEY = "org.myiadidot.draft"

ASTERISK = [(495, 1329), (609, 1329), (609, 805), (495, 805)]
REDERIVE = {"uni01AE": "Ʈ", "uni2042": "⁂"}
# glyph: [(top of N's edge, the node dropped, the tail's node moved onto the line)]
STRAIGHTEN = {"uni019D": [((286, 1382), (280, 80), (274, -177)), ((350, 1382), (344, 60), (338, -75))]}
ALIGN = {
    "uni01AE": [(688, -162)],  # Ʈ: the stem's edge into the curl
    "uni0291": [(446, 200)],  # ʑ: the curl's edge off the bar
    "uniA7B2": [(640, 260), (33, -524)],  # Ʝ: the stem's edge, the ball
    "uni026E": [(534, -133), (492, -225), (495, 121)],  # ɮ: ʒ's joins
    "uni03CF": [(1272, 200), (880, -195)],  # Ϗ: the leg into the curl
    "uni025E": [(380, -7), (380, 142)],  # ɞ: the halves' seams
    "uni0290": [(680, 48)],  # ʐ: the bar into the tail
    "uni019D": [(343, -75)],  # Ɲ: the tail's node after step 2
}
# the small caps enlarged from Ɲ Ʝ Ϗ (data_regular.py), made on the mended letters
SMALL_CAPS = {"uni0272.sc": "ɲ.sc", "uni029D.sc": "ʝ.sc", "uni03D7.sc": "ϗ.sc"}
# (their nodes made smooth too: made again, ϗ.sc's 656,-138 came out a corner
# and ʝ.sc's 119,-379 1.2 degrees off its line, 5.5-degree kinks in the Bold)
SC_ALIGN = {"uni03D7.sc": [(836, -269), (656, -138)], "uni029D.sc": [(119, -379)]}


def node(glyph, x, y, r=3):
    for c in glyph.contours:
        for i, p in enumerate(c.points):
            if p.type and math.dist((p.x, p.y), (x, y)) <= r:
                return c, i
    raise ValueError(f"{glyph.name}: no node at {x},{y}")


def straighten(glyph, top, mid, low):
    """mid dropped, low (with its handles) moved along x onto the line top-mid"""
    c, i = node(glyph, *low)
    p = c.points[i]
    x = round(top[0] + (mid[0] - top[0]) * (p.y - top[1]) / (mid[1] - top[1]))
    dx = x - p.x
    n = len(c.points)
    for j in (i - 1, i, (i + 1) % n):
        q = c.points[j]
        if j == i or q.type is None:
            q.x += dx
    c2, k = node(glyph, *mid)
    del c2.points[k]


def rederive(path, glyphs):
    """glyphs ({name: char}) made again by derive.py, their draft mark as it was"""
    font = ufoLib2.Font.open(path)
    was = {name: font[name].lib.get(DRAFT_KEY) for name in glyphs}
    for name in glyphs:
        font[name].lib[DRAFT_KEY] = True
    font.save()
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts/derive.py"), path, "--redraft", *glyphs.values()],
                   check=True)
    font = ufoLib2.Font.open(path)
    for name, draft in was.items():
        if not draft:
            font[name].lib.pop(DRAFT_KEY, None)
    return font


def letters(path):
    """step 1: the letters"""
    font = ufoLib2.Font.open(path)
    for x, y in ASTERISK:
        smooth_joins.align(font["asterisk"], x, y)
    font.save()
    font = rederive(path, REDERIVE)
    for name, lines in STRAIGHTEN.items():
        for top, mid, low in lines:
            straighten(font[name], top, mid, low)
    for name, places in ALIGN.items():
        for x, y in places:
            smooth_joins.align(font[name], x, y)
    font.save()


def small_caps(path):
    """step 2: the small caps enlarged from the mended letters, made again"""
    font = rederive(path, SMALL_CAPS)
    for name, places in SC_ALIGN.items():
        for x, y in places:
            smooth_joins.align(font[name], x, y)
            c, i = node(font[name], x, y)
            c.points[i].smooth = True
    font.save()


def main():
    path = sys.argv[1]
    if "--small-caps" not in sys.argv[2:]:
        letters(path)
    small_caps(path)


if __name__ == "__main__":
    main()
