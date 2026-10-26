"""Round italic r's inner shoulder and give retroflex r a full U-shaped hook."""

import math
from copy import deepcopy
from pathlib import Path

import ufoLib2
from ufoLib2.objects import Point

ROOT = Path(__file__).resolve().parent.parent
DERIVATIVES = ("r", "uni024D", "uni0279", "uni027A", "uni027B", "uni027D", "uni027E", "uni1D72", "uni1D73")


def round_shoulder(font, skip=()):
    """Fair the short return into r's ball before its derivatives are built.

    Keep the top of the return, the ball's leftmost node and its lower
    curve. Replace the two small intermediate turns with one cubic whose
    handles preserve the horizontal top and vertical lower tangent.
    """
    if "r" in skip:
        return
    points = font["r"].contours[0].points
    right = max(p.x for p in points)
    lower = [i for i, p in enumerate(points) if p.type and 690 < p.y < 710 and p.x > .64 * right]
    tips = [i for i, p in enumerate(points) if p.type and 800 < p.y < 825 and p.x > .64 * right]
    if len(lower) != 1 or not tips:
        raise ValueError("r's shoulder landmarks changed; review the rounded return")
    a, b = lower[0], max(tips, key=lambda i: points[i].y)
    if a >= b:
        raise ValueError("r's shoulder direction changed; review the rounded return")
    lo, tip = points[a], points[b]
    points[a + 1:b] = [Point(lo.x, lo.y + (tip.y - lo.y) * .7), Point(tip.x + 29, tip.y)]
    lo.smooth = tip.smooth = True
    from italic_contours import _add_extrema

    _add_extrema(points, lambda x, y: x >= lo.x and lo.y <= y <= tip.y)


def finish_shoulders(font):
    """Keep extrema and shallow joins after reflection, Boolean work and rounding."""
    if font.info.styleName not in ("Italic", "Bold Italic"):
        return
    for name in DERIVATIVES:
        if name in font and name != "uni027D":  # rebuilt from r below
            glyph = font[name]
            _finish_geometry(glyph, lambda x, y, width=glyph.width: (
                font.info.styleName == "Bold Italic" or (x > .6 * width and 650 < y < 850)))


def finish_turned_r_top(font):
    """Give Bold Italic ɺ the bracket of its l's top serif.

    ɺ is ɹ with l's top (make_italic.ITALIC_RECIPES); emboldened as one
    letter by weight, the bracket under the serif swelled 10 units past l's
    and came out in three curves. The stems' left edges coincide (l's
    shifted by dx at every height), so l's bracket, from its stem's end to
    the serif's underside, replaces ɺ's there exactly.
    """
    import derive

    if font.info.styleName != "Bold Italic" or "uni027A" not in font:
        return
    lp = font["l"].contours[0].points
    starts = [i for i, p in enumerate(lp) if p.type == "line" and 1320 <= p.y <= 1340]
    if len(starts) != 1 or not lp[starts[0] + 3].type or lp[starts[0] + 4].type != "line":
        raise ValueError("l's top bracket landmarks changed; review ɺ's top")
    s = starts[0]
    bracket = lp[s + 1:s + 4]  # two handles and the curve's end under the serif
    corner = lp[s + 4]
    dx = round(derive.stems_at(font, "uni027A", 1300)[-1][0] - derive.stems_at(font, "l", 1300)[0][0])
    points = font["uni027A"].contours[0].points
    a = [i for i, p in enumerate(points) if p.type == "line" and (p.x, p.y) == (lp[s].x + dx, lp[s].y)]
    b = [i for i, p in enumerate(points) if p.type == "line" and (p.x, p.y) == (corner.x + dx, corner.y)]
    if len(a) != 1 or len(b) != 1 or not a[0] < b[0]:
        raise ValueError("ɺ's top no longer meets l's stem edge; review ɺ's top")
    new = []
    for p in bracket:
        q = deepcopy(p)
        q.x += dx
        new.append(q)
    points[a[0] + 1:b[0]] = new


def _finish_geometry(glyph, region):
    from italic_contours import _add_extrema, _align_handles
    from make_bold import round_smoothly

    for contour in glyph.contours:
        for _ in range(4):
            before = deepcopy(contour.points)
            _align_handles(contour.points, region)
            _add_extrema(contour.points, lambda x, y: True)
            round_smoothly(contour.points)
            if before == contour.points:
                break
        else:
            raise ValueError(f"{glyph.name}: r contour finishing did not settle")


def finish(font):
    """Build ɽ from the final r body and the corresponding roman hook.

    The Regular/Bold hooks supply the U turn and rounded upright terminal
    requested for the italics. Calibrate their width to r's actual stem,
    then shear them by this font's slant; keep the roman depth and hairline
    thickness. The body follows r exactly. Only outlines are replaced:
    ɽ keeps its own advance, anchors and glyph metadata.
    """
    if font.info.styleName not in ("Italic", "Bold Italic") or "uni027D" not in font:
        return
    body = deepcopy(font["r"])
    points = body.contours[0].points
    inner = [i for i, p in enumerate(points) if p.type and 115 <= p.y <= 130 and p.x > 300]
    outer = [i for i, p in enumerate(points) if p.type and 0 <= p.y <= 4 and p.x < 200]
    if len(inner) != 1 or len(outer) != 1 or inner[0] >= outer[0]:
        raise ValueError("r's stem landmarks changed; review the retroflex hook")
    a, b = inner[0], outer[0]
    roman_style = "Regular" if font.info.styleName == "Italic" else "Bold"
    roman = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{roman_style}.ufo")
    source = roman["uni027D"].contours[0].points
    starts = [i for i, p in enumerate(source) if p.type and -125 <= p.y <= -110]
    # (the Bold's hook joins at 56: cut above its taller foot serif, make_bold.rederive)
    ends = [i for i, p in enumerate(source) if p.type == "curve" and 40 <= p.y <= 60]
    if len(starts) != 1 or len(ends) != 1 or starts[0] <= ends[0]:
        raise ValueError("roman retroflex hook landmarks changed; review the transplant")
    start, end = starts[0], ends[0]
    hook = deepcopy(source[start:] + source[:end + 1])
    slope = math.tan(math.radians(-font.info.italicAngle))
    left, right = source[end].x, source[start].x
    origin = points[b].x - slope * points[b].y
    scale = (points[a].x - slope * points[a].y - origin) / (right - left)
    for p in hook:
        p.x = round(origin + (p.x - left) * scale + slope * p.y)
    # Ease the stem into its slanted continuation with the existing
    # shoulder tangent, avoiding a new corner at the attachment height.
    node, incoming = points[a], points[a - 1]
    target = hook[0]
    handles = [Point(round(node.x + (node.x - incoming.x) * .35),
                     round(node.y + (node.y - incoming.y) * .35)),
               Point(round(target.x + slope * 80), target.y + 80)]
    target.type, target.smooth = "curve", True
    hook[-1].x, hook[-1].y = points[b].x, points[b].y
    hook[-1].smooth = True
    points[a + 1:b + 1] = handles + hook
    glyph = font["uni027D"]
    glyph.clearContours()
    body.drawPoints(glyph.getPointPen())
    _finish_geometry(glyph, lambda x, y: y < 130)


def fair_bold_stem(font):
    """Keep the roman inner stem monotonic as it enters the shoulder.

    The weighted return had a control point left of the straight stem,
    making an inward bump. Shorten that handle along the incoming tangent.
    """
    if font.info.styleName != "Bold":
        return
    for name in ("r", "uni027D"):
        for contour in font[name].contours:
            points = contour.points
            for i, node in enumerate(points):
                if node.type == "curve" and node.y == 699:
                    handle, lower, end = points[i + 1:i + 4]
                    if end.type == "curve" and end.y != 412 and len(points) > i + 6:
                        # ɽ remade from its recipe (make_bold.rederive): the
                        # union split the return in two; one curve again
                        after = points[i + 6]
                        if after.type == "curve" and after.y == 412:
                            del points[i + 3:i + 6]
                            handle, lower, end = points[i + 1:i + 4]
                            lower.y = 513
                    if end.type == "curve" and end.y == 412:
                        handle.x, handle.y = end.x, 667
                        lower.x = end.x


def round_left_shoulder(font):
    """Replace Bold Italic r's stepped inner arch with one round turn."""
    if font.info.styleName != "Bold Italic":
        return
    points = font["r"].contours[0].points
    starts = [i for i, p in enumerate(points) if p.type and 595 <= p.y <= 605 and 250 < p.x < 330]
    ends = [i for i, p in enumerate(points) if p.type and 808 <= p.y <= 815 and 320 < p.x < 370]
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("r's left shoulder landmarks changed; review its rounding")
    a, b = starts[0], ends[0]
    if a >= b:
        raise ValueError("r's left shoulder direction changed")
    start, end = points[a], points[b]
    points[a + 1:b] = [Point(start.x + 27, start.y + 96), Point(end.x + 45, end.y)]
    end.smooth = True
    from italic_contours import _add_extrema

    _add_extrema(points, lambda x, y: start.y <= y <= end.y and x < 420)
