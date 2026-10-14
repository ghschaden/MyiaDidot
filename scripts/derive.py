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

Transformed glyphs get plain outlines, not components, since they are
meant to be redrawn (a turned serif sits on the wrong side). Every glyph
is marked as a draft (lib DRAFT_KEY) and appears under "Other drafts" in
the small-caps review sheet. Existing glyphs are never touched, except
unreviewed drafts with --redraft. CHARS limits the run to those characters.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smallcaps import DEFAULT_HEIGHT, HEIGHT_KEY

DRAFT_KEY = "org.myiadidot.draft"

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
    ("ɒ", "turn", "alpha", "x"),
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
]

# anchors that keep their meaning when the shape is mirrored left-right
# within the same vertical band
KEEP_ANCHORS = ("Top", "Acute", "Grave", "Dotaccent", "TopCap", "Bottom", "DotBelow")


def glyph_name(ch):
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


def mirrored_anchors(src, dst, width):
    for a in src.anchors:
        if a.name in KEEP_ANCHORS:
            dst.appendAnchor({"name": a.name, "x": width - a.x, "y": a.y})


def build(font, ch, op, source, band):
    src = font[source]
    g = font.newGlyph(glyph_name(ch))
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
    else:
        raise ValueError(op)
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
        if source not in font:
            sys.exit(f"{ch}: source {source} missing")
        name = cmap.get(ord(ch), glyph_name(ch))
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(ch)
                continue
            del font[name]
        g = build(font, ch, op, source, band)
        cmap[ord(ch)] = g.name
        made.append(ch)
    font.save()
    print(f"drafted {len(made)}: {''.join(made)}")
    if kept:
        print(f"kept {len(kept)} existing: {''.join(kept)}")


if __name__ == "__main__":
    main()
