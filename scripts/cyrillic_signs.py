"""Draw the italic Cyrillic sign family at its final weight.

The bowl, counter and stem are drawn together, rather than thickening a
joined outline. The Bulgarian ascenders enter that same bowl continuously.
Run on an existing italic master for a focused redesign; both full style
generators also call redraw after spacing, before collision kerning.
"""

import argparse
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import with_extremes

NAMES = ('uni044C', 'uni044B', 'uni044A', 'uni044C.loclBGR', 'uni044A.loclBGR')
# Final advances and anchor x coordinates, in NAMES order. These drawings
# bypass optical fitting of the temporary emboldened outlines; retain the
# established text metrics instead of inheriting that outline's fit offsets.
# Anchor order: Top, Acute/Grave, Dotaccent, Bottom, DotBelow.
METRICS = (
    ((871, 393, 388, 399, 420, 414), (1318, 781, 776, 787, 622, 616),
     (887, 504, 498, 510, 435, 430), (871, 393, 388, 399, 420, 414),
     (871, 393, 388, 399, 420, 414)),
    ((960, 425, 420, 431, 464, 458), (1425, 828, 823, 834, 674, 668),
     (969, 533, 527, 539, 472, 467), (951, 420, 415, 426, 459, 453),
     (949, 418, 413, 424, 457, 451)),
)


def outline(p, kind, b):
    """Coordinates in the upright frame, interpolated between two drawings."""
    right, left = 400 + 50*b, 235 - 50*b
    top, bottom = 540 + 30*b, 532 + 30*b
    # Start where the stem turns into the shoulder of the bowl.
    p.moveTo((right, 500))
    p.curveTo((445 + 45*b, 545), (490 + 30*b, 564), (top, 564))
    p.curveTo((725 + 70*b, 564), (840 + 80*b, 470), (840 + 80*b, 310))
    p.curveTo((840 + 80*b, 110), (700 + 60*b, -23), (bottom, -23))
    p.curveTo((350 + 5*b, -23), (left, 105), (left, 280))
    if kind in ('soft', 'yeru'):
        # One continuous outside edge from the bowl into the entry stroke.
        p.curveTo((left, 450), (270 - 40*b, 675), (270 - 40*b, 755))
        p.curveTo((270 - 40*b, 805), (250 - 30*b, 826 - 8*b), (225 - 25*b, 826 - 8*b))
        p.curveTo((125 - 25*b, 826 - 8*b), (86 - 15*b, 609), (77 - 15*b, 508))
        p.lineTo((33 - 15*b, 520))
        p.curveTo((48 - 15*b, 702), (103 - 15*b, 884), (231, 884))
        p.curveTo((350 + 40*b, 884), (right + 10, 790), (right + 10, 690))
        p.curveTo((right + 10, 625), (right, 560), (right, 500))
    elif kind == 'hard':
        # Retain the hard sign's waving flag and diagonal rise, not a soft
        # sign with a pasted-on flag. The wave has no small curled ear.
        p.curveTo((left, 430), (425 + 10*b, 565), (465 + 10*b, 715))
        p.curveTo((390 + 10*b, 675), (330, 695), (245, 747))
        p.curveTo((205, 773), (180, 788), (145, 788))
        p.curveTo((85, 788), (58, 751), (58, 710))
        p.curveTo((58, 678), (90, 655), (90, 630))
        p.curveTo((90, 610), (75, 607), (65, 622))
        p.curveTo((32, 660), (25, 700), (25, 739))
        p.curveTo((25, 830), (82, 884), (192, 884))
        p.curveTo((292, 884), (349, 770 - 10*b), (425, 770 - 10*b))
        p.curveTo((467, 770 - 10*b), (472 + 10*b, 815), (472 + 10*b, 844))
        p.curveTo((472 + 10*b, 870), (480 + 10*b, 884), (500 + 10*b, 884))
        p.curveTo((528 + 20*b, 884), (545 + 20*b, 863), (545 + 20*b, 833))
        p.curveTo((545 + 20*b, 740), (right + 35, 570), (right, 500))
    else:
        # No splice at x-height: both sides run from bowl to ascender.
        p.curveTo((left, 440), (250 - 40*b, 550), (250 - 40*b, 720))
        if kind == 'bgr_soft':
            p.lineTo((250 - 40*b, 1335))
            p.curveTo((250 - 40*b, 1372), (243 - 40*b, 1382 - 4*b), (213 - 40*b, 1382 - 4*b))
            p.lineTo((36 - 20*b, 1382 - 4*b))
            p.lineTo((36 - 20*b, 1434))
        else:
            p.lineTo((250 - 40*b, 1275))
            p.curveTo((200 - 30*b, 1305), (165 - 20*b, 1325), (117 - 20*b, 1325))
            p.curveTo((60 - 20*b, 1325), (30 - 20*b, 1290), (30 - 20*b, 1255))
            p.curveTo((30 - 20*b, 1217), (70 - 20*b, 1198), (70 - 20*b, 1170))
            p.lineTo((25 - 20*b, 1170))
            p.curveTo((-5 - 20*b, 1212), (-12 - 20*b, 1254), (-12 - 20*b, 1290))
            p.curveTo((-12 - 20*b, 1375), (40 - 20*b, 1434), (130 - 20*b, 1434))
        p.lineTo((right, 1434))
        p.lineTo((right, 500))
    p.closePath()
    # A single open, rounded counter; its left edge has no straight/curve
    # corner for emboldening to turn into a spur.
    # The diagonal rise of ъ leaves less ink on the bowl's left than the
    # upright stem. In Bold Italic give that bowl a slightly smaller counter.
    counter = TransformPen(p, (.92, 0, 0, 1, 45, 0)) if kind == 'hard' and b else p
    counter.moveTo((535 + 30*b, 23 + 7*b))
    counter.curveTo((650 + 20*b, 23 + 7*b), (685 + 10*b, 180), (685 + 10*b, 295))
    counter.curveTo((685 + 10*b, 425), (625 + 20*b, 518 - 8*b), (531 + 30*b, 518 - 8*b))
    counter.curveTo((435 + 50*b, 518 - 8*b), (370 + 60*b, 382), (370 + 60*b, 260))
    counter.curveTo((370 + 60*b, 120), (425 + 50*b, 23 + 7*b), (535 + 30*b, 23 + 7*b))
    counter.closePath()
    if kind == 'yeru':
        p.moveTo((942 - 5*b, 861))
        p.lineTo((1084 + 95*b, 861))
        p.lineTo((1080 + 95*b, 268))
        p.curveTo((1080 + 95*b, 100), (1100 + 95*b, 43), (1141 + 95*b, 43))
        p.curveTo((1223 + 95*b, 43), (1260 + 95*b, 204), (1271 + 95*b, 353))
        p.lineTo((1314 + 95*b, 341))
        p.curveTo((1302 + 95*b, 217), (1278 + 95*b, -23), (1122 + 75*b, -23))
        p.curveTo((985 + 20*b, -23), (937 - 5*b, 120), (937 - 5*b, 291))
        p.lineTo((942 - 5*b, 861))
        p.closePath()


def redraw(font):
    from make_bold import round_smoothly

    if not font.info.italicAngle:
        raise ValueError('Cyrillic sign drawings require an italic master')
    b = 1 if font.info.openTypeOS2WeightClass >= 600 else 0
    slant = math.tan(math.radians(-font.info.italicAngle))
    kinds = ('soft', 'yeru', 'hard', 'bgr_soft', 'bgr_hard')
    for name, kind, metrics in zip(NAMES, kinds, METRICS[b], strict=True):
        g = font[name]
        g.width, top, acute, dot, bottom, below = metrics
        anchor_x = dict(Top=top, Acute=acute, Grave=acute, Dotaccent=dot, Bottom=bottom, DotBelow=below)
        for anchor in g.anchors:
            if anchor.name in anchor_x:
                anchor.x = anchor_x[anchor.name]
        g.clearContours()
        g.clearComponents()
        rec = RecordingPen()
        pen = TransformPen(rec, (1, 0, slant, 1, 0, 0))
        outline(TransformPen(pen, (1, 0, 0, 1, -slant*440 + 24*b, 0)), kind, b)
        with_extremes(rec, g.getPen(), round_points=False)
        for contour in g.contours:
            round_smoothly(contour.points)
        g.lib['org.myiadidot.italicSource'] = 'cyrillic sign drawing'
        g.lib.pop('org.myiadidot.builtFrom', None)
        font.lib.get('org.myiadidot.emboldenedWhole', {}).pop(name, None)
    return list(NAMES)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('ufo')
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    redraw(font)
    font.save()


if __name__ == '__main__':
    main()
