"""Draft new characters from existing glyphs: same shape, turned, mirrored.

    python scripts/derive.py UFO [--redraft] [CHARS...]

Each recipe below makes one encoded glyph from a source glyph (a glyph name,
or an earlier recipe's character):

    alias     a component of the source (ɑ = α, ɪ = small-cap I); follows
              any later change to the source
    turn      outlines turned 180° about the middle of the band given
              (x: x-height, c: cap height, s: small-cap height)
    mirror    outlines mirrored left-right
    flip      outlines mirrored top-bottom about the middle of the band
    nodot     the source without its lowest contour, the stem run down to
              the baseline (? -> ʔ)
    double    two copies side by side (| -> ǁ)
    bar       a horizontal bar merged into the outlines (Ɨ ʉ Ө): across the
              stems the ink crosses at that height, stretching OVER past
              them but not past the letter's ink (ħ, Đ, Ŧ have 168/220)
    slash     a diagonal stroke merged in: corner to corner like Ø (Ⱥ ȼ),
              or short through one stem like ł (ƛ)
    midtilde  a tilde across the letter at mid height (ɫ ᵬ)

A recipe for "ɔ.sc" makes the small cap uni0254.sc (unencoded, reached
through smcp/c2sc once smallcaps.py has run); it is marked as a small-cap
draft and reviewed with the other small caps.

Transformed glyphs get plain outlines, not components, since they are
meant to be redrawn (a turned serif sits on the wrong side). Every glyph
is marked as a draft (lib DRAFT_KEY) and appears under "Other drafts" in
the small-caps review sheet. Existing glyphs are never touched, except
unreviewed drafts with --redraft. CHARS limits the run to those characters.
"""

import argparse
import math
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smallcaps import DEFAULT_HEIGHT, HEIGHT_KEY, ink_bounds, ink_slice
from smallcaps import DRAFT_KEY as SMALLCAP_DRAFT_KEY

DRAFT_KEY = "org.myiadidot.draft"
DERIVED_KEY = "org.myiadidot.derived"

# (character, operation, source, band) -- band only for turn/flip
RECIPES = [
    # same shape as an existing letter
    ("ɑ", "alias", "alpha", None),
    ("ɛ", "alias", "epsilon", None),
    ("ɣ", "alias", "gamma", None),
    ("ɸ", "alias", "phi", None),
    ("ɩ", "alias", "iota", None),
    ("ꞵ", "alias", "beta", None),
    ("ꭓ", "alias", "chi", None),
    ("ꞷ", "alias", "omega", None),
    ("һ", "alias", "h", None),
    ("Ү", "alias", "Y", None),
    ("Ɪ", "alias", "I", None),
    # IPA small capitals are the small caps
    ("ɢ", "alias", "g.sc", None),
    ("ɪ", "alias", "i.sc", None),
    ("ʟ", "alias", "l.sc", None),
    ("ɴ", "alias", "n.sc", None),
    ("ʀ", "alias", "r.sc", None),
    ("ʏ", "alias", "y.sc", None),
    ("ʙ", "alias", "b.sc", None),
    ("ʜ", "alias", "h.sc", None),
    ("ᴅ", "alias", "d.sc", None),
    ("ɶ", "alias", "oe.sc", None),
    ("ʁ", "flip", "r.sc", "s"),
    # turned
    ("ɐ", "turn", "a", "x"),
    ("ǝ", "turn", "e", "x"),
    ("ə", "alias", "ǝ", None),
    ("ә", "alias", "ǝ", None),
    ("ɥ", "turn", "h", "x"),
    ("ɯ", "turn", "m", "x"),
    ("ɹ", "turn", "r", "x"),
    ("ʌ", "turn", "v", "x"),
    ("ʍ", "turn", "w", "x"),
    ("ʎ", "turn", "y", "x"),
    ("ɒ", "mirror", "alpha", None),
    ("Ʌ", "turn", "V", "c"),
    ("Ɐ", "turn", "A", "c"),
    ("Ɯ", "turn", "M", "c"),
    ("⅄", "turn", "Y", "c"),
    # mirrored
    ("ɔ", "mirror", "c", None),
    ("Ɔ", "mirror", "C", None),
    ("Ǝ", "mirror", "E", None),
    ("ɘ", "mirror", "e", None),
    ("ɜ", "mirror", "epsilon", None),
    # glottal stops and clicks
    ("ʔ", "nodot", "question", None),
    ("Ɂ", "alias", "ʔ", None),
    ("ʕ", "mirror", "ʔ", None),
    ("ǀ", "alias", "bar", None),
    ("ǁ", "double", "bar", None),
    ("ǃ", "alias", "exclam", None),
    # with a bar (band, y or None for the band's bar height, which stems)
    ("Ɨ", "bar", "I", ("c",)),
    ("ɨ", "bar", "i", ("x",)),
    ("Ʉ", "bar", "U", ("c",)),
    ("ʉ", "bar", "u", ("x",)),
    ("Ƚ", "bar", "L", ("c",)),
    ("ƚ", "bar", "l", ("x",)),
    ("Ɉ", "bar", "J", ("c",)),
    ("ɉ", "bar", "j", ("x",)),
    ("ɟ", "bar", "uni0237", ("x",)),
    ("Ɍ", "bar", "R", ("c", 360, "first")),
    ("ɍ", "bar", "r", ("x", None, "first")),
    ("Ᵽ", "bar", "P", ("c", 360)),
    ("ᵽ", "bar", "p", ("x", -290)),
    ("Ǥ", "bar", "G", ("c", 260, "last")),
    ("ǥ", "bar", "g", ("x", -300, "last")),
    ("Ғ", "bar", "uni0413", ("c", None, "first")),
    ("ғ", "bar", "uni0433", ("x", None, "first")),
    ("Ұ", "bar", "uni04AE", ("c", 360)),
    ("Ө", "bar", "O", ("c", 717, "inside")),
    ("ө", "bar", "o", ("x", None, "inside")),
    ("Ɵ", "alias", "Ө", None),
    ("ɵ", "alias", "ө", None),
    ("Ꟈ", "bar", "D", ("c", None, "first")),
    ("ꟈ", "bar", "d", ("x", None, "last")),
    ("ʡ", "bar", "ʔ", ("x", 300)),
    ("ʢ", "bar", "ʕ", ("x", 300)),
    # with a slash (band, 'box', x and y of both ends) or ('short', ...)
    ("Ⱥ", "slash", "A", ("c", "box", 0.2, -80, 0.85, 1542)),
    ("ⱥ", "slash", "a", ("x", "box", 0.1, -80, 0.9, 980)),
    ("Ȼ", "slash", "C", ("c", "box", 0.25, -120, 0.8, 1580)),
    ("ȼ", "slash", "c", ("x", "box", 0.2, -100, 0.8, 1000)),
    ("Ⱦ", "slash", "T", ("c", "box", 0.25, -80, 0.75, 1434)),
    ("ⱦ", "slash", "t", ("x", "box", 0.05, -80, 0.95, 960)),
    ("ƛ", "slash", "lambda", ("x", "short", 1150, 560, 30, "first")),
    # with a middle tilde
    ("ɫ", "midtilde", "l", ("x",)),
    ("Ɫ", "midtilde", "L", ("c", 717, "first")),
    ("ᵬ", "midtilde", "b", ("x",)),
    ("ᵭ", "midtilde", "d", ("x",)),
    ("ᵮ", "midtilde", "f", ("x",)),
    ("ᵯ", "midtilde", "m", ("x",)),
    ("ᵰ", "midtilde", "n", ("x",)),
    ("ᵱ", "midtilde", "p", ("x",)),
    ("ᵲ", "midtilde", "r", ("x",)),
    ("ᵴ", "midtilde", "s", ("x",)),
    ("ᵵ", "midtilde", "t", ("x",)),
    ("ᵶ", "midtilde", "z", ("x",)),
    # small caps for the new case pairs, derived like their capitals
    ("ɔ.sc", "mirror", "c.sc", None),
    ("ǝ.sc", "mirror", "e.sc", None),
    # ə/ә: no small cap until the capital Ə is drawn (a turned E.sc would be Ǝ)
    ("ɐ.sc", "turn", "a.sc", "s"),
    ("ʌ.sc", "turn", "v.sc", "s"),
    ("ɯ.sc", "turn", "m.sc", "s"),
    ("ɪ.sc", "alias", "i.sc", None),
    ("ɨ.sc", "bar", "i.sc", ("s",)),
    ("ʉ.sc", "bar", "u.sc", ("s",)),
    ("ƚ.sc", "bar", "l.sc", ("s",)),
    ("ɉ.sc", "bar", "j.sc", ("s",)),
    ("ɍ.sc", "bar", "r.sc", ("s", 260, "first")),
    ("ᵽ.sc", "bar", "p.sc", ("s", 260)),
    ("ǥ.sc", "bar", "g.sc", ("s", 190, "last")),
    ("ғ.sc", "bar", "uni0433.sc", ("s", None, "first")),
    ("ө.sc", "bar", "o.sc", ("s", None, "inside")),
    ("ɵ.sc", "alias", "ө.sc", None),
    ("ꟈ.sc", "bar", "d.sc", ("s", None, "first")),
    ("ⱥ.sc", "slash", "a.sc", ("s", "box", 0.2, -60, 0.85, 1100)),
    ("ȼ.sc", "slash", "c.sc", ("s", "box", 0.25, -90, 0.8, 1130)),
    ("ⱦ.sc", "slash", "t.sc", ("s", "box", 0.25, -60, 0.75, 1040)),
    ("ɫ.sc", "midtilde", "l.sc", ("s", None, "first")),
    # the IPA small capitals with a stroke are those small caps
    ("ᵻ", "alias", "ɨ.sc", None),
    ("ᵾ", "alias", "ʉ.sc", None),
]

# anchors that keep their meaning when the shape is mirrored left-right
# within the same vertical band
KEEP_ANCHORS = ("Top", "Acute", "Grave", "Dotaccent", "TopCap", "Bottom", "DotBelow")


def glyph_name(ch):
    if ch.endswith(".sc") and len(ch) == 4:
        return glyph_name(ch[0]) + ".sc"
    return f"uni{ord(ch):04X}" if ord(ch) <= 0xFFFF else f"u{ord(ch):05X}"


def band_middle(font, band):
    return {
        "x": font.info.xHeight,
        "c": font.info.capHeight,
        "s": font.lib.get(HEIGHT_KEY, DEFAULT_HEIGHT),
    }[band] / 2


def draw_transformed(font, src, dst, transform, reverse):
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    pen = dst.getPen()
    if reverse:
        pen = ReverseContourPen(pen)
    rec.replay(TransformPen(pen, transform))


# bar thickness and how far a bar runs past the stems, as in ħ ŧ / Đ Ŧ
BARS = {"x": (56, 168), "c": (64, 220), "s": (60, 190)}
# the y a bar sits at for each band; capitals as in Đ Ŧ (714-778)
BAR_Y = {"x": 442, "c": 746}
SLASH = {"x": 55, "c": 77, "s": 66}  # perpendicular thickness of Ø ø


def bar_y(font, band, y):
    if y is not None:
        return y
    return BAR_Y.get(band) or band_middle(font, band)


def stems_at(font, name, y):
    """The ink intervals at height y, as (x0, x1) pairs."""
    xs = ink_slice(font, name, y + 0.01)  # off the nodes at the extremes
    return list(zip(xs[::2], xs[1::2]))


def rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def stroke(pen, p0, p1, t):
    """A straight stroke of perpendicular thickness t, ends cut square."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * t / 2, dx / n * t / 2
    pen.moveTo((p0[0] + ox, p0[1] + oy))
    pen.lineTo((p1[0] + ox, p1[1] + oy))
    pen.lineTo((p1[0] - ox, p1[1] - oy))
    pen.lineTo((p0[0] - ox, p0[1] - oy))
    pen.closePath()


def bar_shape(font, source, band, arg):
    """Pen commands for the bar: arg is (y or None, which stems, overhang or
    None); which is 'all', 'first', 'last' or 'inside' (Ө: the counter only)."""
    y, which, over = (arg + (None, None, None))[:3]
    t, default_over = BARS[band]
    over = default_over if over is None else over
    y = bar_y(font, band, y)
    stems = stems_at(font, source, y)
    if which == "first":
        stems = stems[:1]
    elif which == "last":
        stems = stems[-1:]
    x0, x1 = stems[0][0], stems[-1][1]
    if which == "inside":
        x0, x1 = stems[0][1] - 20, stems[-1][0] + 20
    else:
        ink = ink_bounds(font, source)
        x0, x1 = max(x0 - over, min(ink[0], x0)), min(x1 + over, max(ink[2], x1))
    rec = RecordingPen()
    rect(rec, x0, y - t / 2, x1, y + t / 2)
    return rec


def slash_shape(font, source, band, arg):
    """arg ('box', fx0, y0, fx1, y1): from (x0 + fx0*w, y0) to (x0 + fx1*w,
    y1) in the ink box, like Ø; or ('short', y, length, angle, which): a
    stroke of that length centred on a stem at height y, like ł."""
    t = SLASH[band]
    rec = RecordingPen()
    if arg[0] == "box":
        _, fx0, y0, fx1, y1 = arg
        x0, _, x1, _ = ink_bounds(font, source)
        w = x1 - x0
        stroke(rec, (x0 + fx0 * w, y0), (x0 + fx1 * w, y1), t)
    else:
        _, y, length, angle, which = arg
        stems = stems_at(font, source, y)
        s = stems[0] if which == "first" else stems[-1]
        cx = (s[0] + s[1]) / 2
        dx, dy = math.cos(math.radians(angle)) * length / 2, math.sin(math.radians(angle)) * length / 2
        stroke(rec, (cx - dx, y - dy), (cx + dx, y + dy), t)
    return rec


def midtilde_shape(font, source, band, arg):
    """The spacing tilde squeezed to 85% height, centred at the bar height
    and stretched across the ink there plus a bit (arg: (y or None, which))."""
    y, which = (arg + (None, None))[:2]
    y = bar_y(font, band, y)
    stems = stems_at(font, source, y)
    if which == "first":
        stems = stems[:1]
    over = BARS[band][1] * 0.8
    x0, x1 = stems[0][0] - over, stems[-1][1] + over
    tx0, ty0, tx1, ty1 = ink_bounds(font, "tilde")
    sx = (x1 - x0) / (tx1 - tx0)
    sy = 0.85 * (1 if band != "s" else 0.9)
    rec = RecordingPen()
    tp = TransformPen(rec, (sx, 0, 0, sy, x0 - tx0 * sx, y - (ty0 + ty1) / 2 * sy))
    font["tilde"].draw(tp)
    return rec


def merged(font, src, extra):
    """The source outlines and the extra shape merged into one outline."""
    path = pathops.Path()
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    rec.replay(path.getPen())
    extra.replay(path.getPen())
    out = RecordingPen()
    pathops.union([path], out)
    return out


def orientation(rec):
    """Sign of the largest contour's area."""
    best = 0
    for op, args in rec.value:
        if op == "moveTo":
            pen = AreaPen()
        getattr(pen, op)(*args)
        if op in ("closePath", "endPath"):
            best = max(best, pen.value, key=abs)
    return best > 0


def draw_merged(font, src, dst, extra):
    out = merged(font, src, extra)
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    pen = RoundingPen(dst.getPen())
    if orientation(out) != orientation(rec):
        pen = ReverseContourPen(pen)
    out.replay(pen)


SHAPES = {"bar": bar_shape, "slash": slash_shape, "midtilde": midtilde_shape}


def mirrored_anchors(src, dst, width):
    for a in src.anchors:
        if a.name in KEEP_ANCHORS:
            dst.appendAnchor({"name": a.name, "x": width - a.x, "y": a.y})


def build(font, ch, op, source, band):
    src = font[source]
    small_cap = ch.endswith(".sc")
    g = font.newGlyph(glyph_name(ch))
    if not small_cap:
        g.unicodes = [ord(ch)]
    w = src.width
    if op == "alias":
        g.width = w
        g.getPen().addComponent(source, (1, 0, 0, 1, 0, 0))
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "turn":
        g.width = w
        cy = band_middle(font, band)
        draw_transformed(font, src, g, (-1, 0, 0, -1, w, 2 * cy), reverse=False)
        if band != "x" or source not in ("h", "y"):  # ascender <-> descender: no anchor fits
            mirrored_anchors(src, g, w)
    elif op == "mirror":
        g.width = w
        draw_transformed(font, src, g, (-1, 0, 0, 1, w, 0), reverse=True)
        mirrored_anchors(src, g, w)
    elif op == "flip":
        g.width = w
        cy = band_middle(font, band)
        draw_transformed(font, src, g, (1, 0, 0, -1, 0, 2 * cy), reverse=True)
    elif op == "nodot":
        g.width = w
        rec = DecomposingRecordingPen(font)
        src.draw(rec)
        tmp = ufoLib2.objects.Glyph()
        rec.replay(tmp.getPen())
        lowest = min(tmp.contours, key=lambda c: min(p.y for p in c.points))
        rest = [c for c in tmp.contours if c is not lowest]
        # the stem stopped above the dot: run its foot down to the baseline
        foot = min(p.y for c in rest for p in c.points)
        for c in rest:
            for pt in c.points:
                if pt.y == foot:
                    pt.y = 0
            c.drawPoints(g.getPointPen())
    elif op == "double":
        g.width = 2 * w
        pen = g.getPen()
        pen.addComponent(source, (1, 0, 0, 1, 0, 0))
        pen.addComponent(source, (1, 0, 0, 1, w, 0))
    elif op in SHAPES:
        g.width = w
        sband, *rest = band
        draw_merged(font, src, g, SHAPES[op](font, source, sband, tuple(rest)))
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    else:
        raise ValueError(op)
    if small_cap:
        # reviewed with the small caps; smallcaps.py never redrafts it
        g.lib[SMALLCAP_DRAFT_KEY] = True
        g.lib[DERIVED_KEY] = True
    else:
        g.lib[DRAFT_KEY] = True
    font.lib.setdefault("public.openTypeCategories", {})[g.name] = "base"
    if g.name not in font.glyphOrder:
        font.glyphOrder = [*font.glyphOrder, g.name]
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("chars", nargs="*")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    only = set("".join(args.chars))

    font = ufoLib2.Font.open(args.ufo)
    cmap = {u: g.name for g in font for u in g.unicodes}
    made, kept = [], []
    for ch, op, source, band in RECIPES:
        if only and ch not in only:
            continue
        if len(source) == 1:  # an earlier recipe's character
            source = cmap.get(ord(source), glyph_name(source))
        elif source.endswith(".sc") and len(source) == 4 and not source[0].isascii():
            source = glyph_name(source)
        if source not in font:
            sys.exit(f"{ch}: source {source} missing")
        name = glyph_name(ch) if ch.endswith(".sc") else cmap.get(ord(ch), glyph_name(ch))
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(ch)
                continue
            del font[name]
        g = build(font, ch, op, source, band)
        if not ch.endswith(".sc"):
            cmap[ord(ch)] = g.name
        made.append(ch)
    font.save()
    print(f"drafted {len(made)}: {''.join(made)}")
    if kept:
        print(f"kept {len(kept)} existing: {''.join(kept)}")


if __name__ == "__main__":
    main()
