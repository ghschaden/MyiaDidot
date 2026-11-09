"""Give the italics' dotted derivatives of i and j their base's dot, where
the base has it.

The Italic makes ɨ ɉ ʝ ⁱ ʲ ᶤ from i and j before i's and j's dots are set
from their anchors (the composites rebuilt at the end), so they kept a dot
standing 84-113 units right of i's and j's (seen 2026-11-09: ɨ "a bit too
far to the east", then ɉ ʝ and the superscripts); in the Bold Italic,
emboldened whole, ɨ's dot also came out larger than i's (368 x 279 against
288 x 256). The Bold Italic's ɉ ʝ ⁱ ʲ ᶤ, made on its own final letters, have
theirs right ("ok as is", 2026-11-09). In the Bold, emboldened whole, the
dots of ɨ ɉ ʝ came out 347 wide against i's and j's 278, those of ⁱ ʲ ᶤ 229
x 155 (2026-11-09): there ɨ ɉ ʝ take i's and j's dot as it stands, ⁱ ʲ ᶤ
theirs made small as the Regular makes the superscripts' dot of i's
(SMALL_DOT), about the centre theirs has (emboldening grows a dot evenly).
"""

import pathops
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from italic_geometry import SLANT, XH

# letter: the letter whose dot it takes, in the order they are set (ᶤ after ɨ)
SAME = {"uni0268": "i", "uni0249": "j", "uni029D": "j"}  # bodies on the base's
SMALL = {"uni2071": "i", "uni02B2": "j", "uni1DA4": "uni0268"}  # made small from the base
STYLES = {"Italic": (*SAME, *SMALL), "Bold Italic": ("uni0268",), "Bold": (*SAME, *SMALL)}
# the Regular's superscript dot against i's: 162 x 147 of 248 x 248
SMALL_DOT = (162 / 248, 147 / 248)


def _upright(font, glyph):
    """the glyph's outline unslanted, as pathops contours (dot last)"""
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    path = pathops.Path()
    s = SLANT if font.info.italicAngle else 0
    rec.replay(TransformPen(path.getPen(), (1, 0, -s, 1, s * XH / 2, 0)))
    return sorted(path.contours, key=lambda c: c.bounds[1])


def _box(contours):
    return (min(c.bounds[0] for c in contours), min(c.bounds[1] for c in contours),
            max(c.bounds[2] for c in contours), max(c.bounds[3] for c in contours))


def _set_dot(font, name, base):
    glyph = font[name]
    xh = font.info.xHeight or XH
    above = [c for c in glyph.contours if min(p.y for p in c.points) > xh]
    if len(above) != 1:
        return
    have, want = _upright(font, glyph), _upright(font, font[base])
    body, dot = _box(have[:-1]), have[-1].bounds
    bbody, bdot = _box(want[:-1]), want[-1].bounds
    if not font.info.italicAngle and name in SMALL:
        # the base's dot made small as in the Regular, about this one's centre
        kx, ky = SMALL_DOT
        cx, cy = (dot[0] + dot[2]) / 2, (dot[1] + dot[3]) / 2
        bx, by = (bdot[0] + bdot[2]) / 2, (bdot[1] + bdot[3]) / 2
        glyph.contours.remove(above[0])
        rec = DecomposingRecordingPen(font)
        font[base].draw(rec)
        piece = pathops.Path()
        rec.replay(piece.getPen())
        top = max(piece.contours, key=lambda c: c.bounds[1])
        top.draw(TransformPen(RoundingPen(glyph.getPen()), (kx, 0, 0, ky, cx - kx * bx, cy - ky * by)))
        return
    if name in SMALL:
        # placed as the body was made small from the base's: scaled by the
        # dots' ratio, the bodies' left and bottom in line
        k = (dot[3] - dot[1]) / (bdot[3] - bdot[1])
        tx, ty = body[0] - k * bbody[0], body[1] - k * bbody[1]
        cx, cy = k * (bdot[0] + bdot[2]) / 2 + tx, k * (bdot[1] + bdot[3]) / 2 + ty
    else:
        cx, cy = (bdot[0] + bdot[2]) / 2, (bdot[1] + bdot[3]) / 2
    dx, dy = cx - (dot[0] + dot[2]) / 2, cy - (dot[1] + dot[3]) / 2
    if name not in SMALL and abs(dot[2] - dot[0] - (bdot[2] - bdot[0])) > 2:
        # its own dot not the base's (emboldened whole): the base's drawn in
        glyph.contours.remove(above[0])
        rec = DecomposingRecordingPen(font)
        font[base].draw(rec)
        piece = pathops.Path()
        rec.replay(piece.getPen())
        top = max(piece.contours, key=lambda c: c.bounds[1])
        top.draw(glyph.getPen())
        return
    # a move in the upright frame, slanted
    s = SLANT if font.info.italicAngle else 0
    sx, sy = dx + s * dy, dy
    for p in above[0].points:
        p.x, p.y = round(p.x + sx), round(p.y + sy)


def finish(font):
    names = STYLES.get(font.info.styleName, ())
    for name in names:
        base = {**SAME, **SMALL}[name]
        if name in font and base in font:
            _set_dot(font, name, base)
