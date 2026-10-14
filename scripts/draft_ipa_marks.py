"""Draft the IPA diacritics and symbols: combining marks below and above
(tacks, bridges, half rings, x above, contour tones, double marks,
overlays) and spacing symbols (stress marks, length marks, tone bars,
saltillo, prime).

    python scripts/draft_ipa_marks.py UFO [--redraft]

Shapes are geometric (straight strokes of the font's accent weight, or
parts of existing accents: the ring, the breve below, the tilde, ʼ).
Combining marks follow the font's convention: zero width, centred at
x = -440, with _Top (-440, 1000) above or _Bottom (-440, 0) below; the
double marks (͜ ͟ ͡) have only _Double, matching no base, and straddle the two letters. Every
glyph is marked as a draft. Existing glyphs are kept unless they are
unreviewed drafts and --redraft is given. Afterwards: composites.py
--stack-anchors.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import BIG, draw_path, path_op, rect, rect_path, stroke, to_path

DRAFT_KEY = "org.myiadidot.draft"
C = -440  # centre of a combining mark
T = 64  # stroke of the geometric marks (the macron is 88, the bar 108)
LO, HI = -420, -150  # band of the marks below
ALO, AHI = 1060, 1330  # band of the marks above
TOP = ("_Top", C, 1000)
# the double marks attach to no base: they straddle the two letters, from
# the end of the first; the anchor only says they are marks
DOUBLE = ("_Double", 0, 0)
BOTTOM = ("_Bottom", C, 0)


def rects(*boxes):
    def draw(font, pen):
        for b in boxes:
            rect(pen, *b)
    return draw


def strokes(*segs, t=T):
    def draw(font, pen):
        for p0, p1 in segs:
            stroke(pen, p0, p1, t)
    return draw


def polygon(*pts):
    def draw(font, pen):
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    return draw


def part(name, transform, clip=None):
    """An existing glyph (or the part of it in clip), transformed."""
    def draw(font, pen):
        path = to_path(font, font[name])
        if clip:
            path = path_op(path, rect_path(*clip), "INTERSECTION")
        path.draw(TransformPen(pen, transform))
    return draw


def square(font, pen):
    rect(pen, C - 150, LO, C + 150, HI)


def hollow(outer, inner):
    """outer minus inner, as a drawing (the square below)."""
    def draw(font, pen):
        a, b = RecordingPen(), RecordingPen()
        outer(font, a)
        inner(font, b)
        path_op(to_path(None, rec=a), to_path(None, rec=b), "DIFFERENCE").draw(pen)
    return draw


MID = (LO + HI) / 2
TICK = (1402, 1076, 717, 358, 32)  # tone bar levels, extra-high to extra-low

# (glyph name, code point, width, category, anchors, shapes)
GLYPHS = [
    # vertical lines
    # vertical strokes are the heavy ones in a Didot: stem-like, not hairlines
    ("uni030D", 0x030D, 0, "mark", [TOP], [rects((C - 50, ALO, C + 50, AHI))]),
    ("uni0329", 0x0329, 0, "mark", [BOTTOM], [rects((C - 50, LO, C + 50, HI))]),
    ("uni0348", 0x0348, 0, "mark", [BOTTOM],
     [rects((C - 132, LO, C - 68, HI), (C + 68, LO, C + 132, HI))]),
    # tacks, plus, minus
    ("uni031D", 0x031D, 0, "mark", [BOTTOM],
     [rects((C - 170, LO, C + 170, LO + T), (C - 32, LO, C + 32, HI))]),
    ("uni031E", 0x031E, 0, "mark", [BOTTOM],
     [rects((C - 170, HI - T, C + 170, HI), (C - 32, LO, C + 32, HI))]),
    ("uni0318", 0x0318, 0, "mark", [BOTTOM],
     [rects((C - 170, MID - 32, C + 170, MID + 32), (C + 106, LO, C + 170, HI))]),
    ("uni0319", 0x0319, 0, "mark", [BOTTOM],
     [rects((C - 170, MID - 32, C + 170, MID + 32), (C - 170, LO, C - 106, HI))]),
    ("uni031F", 0x031F, 0, "mark", [BOTTOM],
     [rects((C - 150, MID - 32, C + 150, MID + 32), (C - 32, MID - 150, C + 32, MID + 150))]),
    ("uni0320", 0x0320, 0, "mark", [BOTTOM], [rects((C - 150, MID - 32, C + 150, MID + 32))]),
    # bridges, square
    ("uni032A", 0x032A, 0, "mark", [BOTTOM],
     [rects((C - 180, HI - T, C + 180, HI), (C - 180, LO + 40, C - 124, HI),
            (C + 124, LO + 40, C + 180, HI))]),
    ("uni033A", 0x033A, 0, "mark", [BOTTOM],
     [rects((C - 180, LO + 40, C + 180, LO + 40 + T), (C - 180, LO + 40, C - 124, HI),
            (C + 124, LO + 40, C + 180, HI))]),
    ("uni033B", 0x033B, 0, "mark", [BOTTOM],
     [hollow(square, rects((C - 94, LO + 56, C + 94, HI - 56)))]),
    # seagull: two breves below side by side
    ("uni033C", 0x033C, 0, "mark", [BOTTOM],
     [part("uni032E", (0.5, 0, 0, 0.8, C - 136 + 0.5 * 440, -60)),   # the two touching
      part("uni032E", (0.5, 0, 0, 0.8, C + 136 + 0.5 * 440, -60))]),
    # half rings below: halves of the ring below
    ("uni031C", 0x031C, 0, "mark", [BOTTOM],
     [part("uni0325", (1, 0, 0, 1, 0, 0), (-BIG, -BIG, C, BIG))]),
    ("uni0339", 0x0339, 0, "mark", [BOTTOM],
     [part("uni0325", (1, 0, 0, 1, 0, 0), (C, -BIG, BIG, BIG))]),
    # low line, and the double marks (no anchor: they straddle two letters)
    ("uni0332", 0x0332, 0, "mark", [BOTTOM], [rects((-880, -360, 0, -360 + T))]),
    ("uni035F", 0x035F, 0, "mark", [DOUBLE], [rects((-700, -360, 700, -360 + T))]),
    ("uni035C", 0x035C, 0, "mark", [DOUBLE], [part("uni032E", (2.4, 0, 0, 1, 2.4 * 440, 0))]),
    ("uni0361", 0x0361, 0, "mark", [DOUBLE], [part("uni032E", (2.4, 0, 0, -1, 2.4 * 440, 1100 - 116))]),
    # above: x, left angle, comma above right
    ("uni033D", 0x033D, 0, "mark", [TOP],
     [strokes(((C - 130, ALO), (C + 130, AHI)), ((C - 130, AHI), (C + 130, ALO)))]),
    ("uni031A", 0x031A, 0, "mark", [TOP],
     [rects((C + 50, AHI - T, C + 330, AHI), (C + 266, ALO + 40, C + 330, AHI))]),
    ("uni0315", 0x0315, 0, "mark", [TOP], [part("uni02BC", (1, 0, 0, 1, C + 330 - 213, 0))]),
    # overlays, at the middle of the x-height
    ("uni0334", 0x0334, 0, "mark", [TOP],
     [part("tilde", (0.9, 0, 0, 0.85, C - 0.9 * 440, 442 - 0.85 * 1181))]),
    ("uni0335", 0x0335, 0, "mark", [TOP], [rects((C - 200, 414, C + 200, 470))]),
    # contour tones above (mid = the macron's height)
    ("uni1DC4", 0x1DC4, 0, "mark", [TOP],
     [strokes(((C - 230, 1210), (C, 1210)), ((C - 20, 1210), (C + 220, 1420)), t=60)]),
    ("uni1DC5", 0x1DC5, 0, "mark", [TOP],
     [strokes(((C - 220, 1420), (C + 20, 1210)), ((C, 1210), (C + 230, 1210)), t=60)]),
    ("uni1DC6", 0x1DC6, 0, "mark", [TOP],
     [strokes(((C - 230, 1210), (C, 1210)), ((C - 20, 1210), (C + 220, 1040)), t=60)]),
    ("uni1DC7", 0x1DC7, 0, "mark", [TOP],
     [strokes(((C - 220, 1040), (C + 20, 1210)), ((C, 1210), (C + 230, 1210)), t=60)]),
    ("uni1DC8", 0x1DC8, 0, "mark", [TOP],
     [strokes(((C - 240, 1400), (C - 80, 1100)), ((C - 80, 1100), (C + 80, 1400)),
              ((C + 80, 1400), (C + 240, 1100)), t=56)]),
    ("uni1DC9", 0x1DC9, 0, "mark", [TOP],
     [strokes(((C - 240, 1100), (C - 80, 1400)), ((C - 80, 1400), (C + 80, 1100)),
              ((C + 80, 1100), (C + 240, 1400)), t=56)]),
    # spacing: stress, length, minus, short equals, prime, saltillo
    ("uni02C8", 0x02C8, 300, "base", [], [rects((100, 1000, 200, 1434))]),
    ("uni02CC", 0x02CC, 300, "base", [], [rects((100, -434, 200, 0))]),
    ("uni02D0", 0x02D0, 400, "base", [],
     [polygon((100, 884), (300, 884), (200, 664)), polygon((100, 0), (200, 220), (300, 0))]),
    ("uni02D1", 0x02D1, 400, "base", [], [polygon((100, 884), (300, 884), (200, 664))]),
    ("uni02D7", 0x02D7, 560, "base", [], [rects((80, 414, 480, 478))]),
    ("uniA78A", 0xA78A, 600, "base", [], [rects((90, 330, 510, 394), (90, 530, 510, 594))]),
    ("uni2032", 0x2032, 480, "base", [], [polygon((250, 1460), (380, 1460), (190, 1000), (140, 1012))]),
    ("uniA78B", 0xA78B, 528, "base", [], [part("quotesingle", (1, 0, 0, 1, 0, 1434 - 1518))]),
    ("uniA78C", 0xA78C, 528, "base", [], [part("quotesingle", (1, 0, 0, 1, 0, 884 - 1518))]),
    # tone bars: the stem on the right, a tick to the left at five levels
    *[(f"uni{0x02E5 + i:04X}", 0x02E5 + i, 560, "base", [],
       [rects((420, 0, 484, 1434), (120, y - 32, 484, y + 32))]) for i, y in enumerate(TICK)],
    # low ring, undertie
    ("uni02F3", 0x02F3, 600, "base", [], [part("ring", (0.85, 0, 0, 0.85, 300 - 0.85 * 440, -440 - 0.85 * 1028 + 0.85 * 0))]),
    ("uni203F", 0x203F, 1000, "base", [], [part("uni032E", (1.6, 0, 0, 1, 500 + 1.6 * 440, 0))]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    made, kept = [], []
    for name, cp, width, cat, anchors, shapes in GLYPHS:
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(name)
                continue
            del font[name]
        rec = RecordingPen()
        for draw in shapes:
            draw(font, rec)
        out = path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")
        g = font.newGlyph(name)
        g.unicodes = [cp]
        g.width = width
        draw_path(font, font["period"], g, out)
        for a, x, y in anchors:
            g.appendAnchor({"name": a, "x": x, "y": y})
        g.lib[DRAFT_KEY] = True
        cats[name] = cat
        if name not in font.glyphOrder:
            font.glyphOrder = [*font.glyphOrder, name]
        made.append(chr(cp))
    font.save()
    print(f"drafted {len(made)}: {' '.join(made)}")
    if kept:
        print(f"kept {len(kept)}: {' '.join(kept)}")


if __name__ == "__main__":
    main()
