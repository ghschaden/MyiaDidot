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
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smallcaps import DEFAULT_HEIGHT, HEIGHT_KEY, ink_bounds, ink_slice
from smallcaps import DRAFT_KEY as SMALLCAP_DRAFT_KEY

DRAFT_KEY = "org.myiadidot.draft"
DERIVED_KEY = "org.myiadidot.derived"

BIG = 10000
# parts of f and ȷ used as hooks by "attach"
F_TOP = (-BIG, 1000, BIG, BIG)
F_HOOK = (-BIG, 1100, BIG, BIG)
J_TAIL = (-BIG, -BIG, BIG, 100)

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
    # ǥ: bar across the right of the lower loop; easy to miss, to revisit
    # (the person kept it for now)
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
    # Cyrillic with a descender: the tail of Ц under the right stem
    ("Ң", "tail", "uni041D", ("c", "stem")),
    ("ң", "tail", "uni043D", ("x", "stem")),
    ("Ҷ", "tail", "uni0427", ("c", "stem")),
    ("ҷ", "tail", "uni0447", ("x", "stem")),
    ("Қ", "tail", "uni041A", ("c", "foot")),
    ("қ", "tail", "uni043A", ("x", "foot")),
    ("Җ", "tail", "uni0416", ("c", "foot")),
    ("җ", "tail", "uni0436", ("x", "foot")),
    ("Ҳ", "tail", "uni0425", ("c", "foot")),
    ("ҳ", "tail", "uni0445", ("x", "foot")),
    ("Һ", "turn", "uni0427", "c"),
    ("ү", "descend", "v", ("x", "p")),
    ("ұ", "bar", "ү", ("x", -200)),
    # capital schwa: the turned e at capital size and weight
    ("Ә", "enlarge", "ǝ", ("o", "O")),
    ("Ə", "alias", "Ә", None),
    # hooks from the font: (band, kind, stem, cut, removed left/right of it)
    ("ɓ", "hook", "b", ("x", "up-right", "first", 1000, 300, 0)),
    ("ɗ", "hook", "d", ("x", "up-right", "last", 1000, 300, 0)),
    ("ƙ", "hook", "k", ("x", "up-right", "first", 1000, 300, 0)),
    ("ɦ", "hook", "h", ("x", "up-right", "first", 1000, 300, 0)),
    ("ƭ", "hook", "t", ("x", "up-right", "first", 900, 300, 0)),
    # Ɓ Ɗ keep their stem (the top bar meets it); only the serif goes
    ("Ɓ", "hook", "B", ("c", "up-left", "first", 1100, 300, -208)),
    ("Ɗ", "hook", "D", ("c", "up-left", "first", 1100, 300, -208)),
    ("ɲ", "hook", "n", ("x", "down-left", "first", 48, 160, 160)),
    ("ɱ", "hook", "m", ("x", "down-left", "last", 48, 160, 160)),
    ("Ƒ", "hook", "F", ("c", "down-left", "first", 52, 200, 200)),
    ("ʈ", "hook", "t", ("x", "down-right", "first", 290, 20, 400)),
    ("Ʈ", "hook", "T", ("c", "down-right", "first", 52, 200, 200)),
    ("ɖ", "hook", "d", ("x", "down-right", "last", 48, 0, 200)),
    ("Ɖ", "alias", "Eth", None),
    ("ɭ", "hook", "l", ("x", "down-right", "first", 48, 160, 160)),
    ("ɳ", "hook", "n", ("x", "down-right", "last", 48, 160, 160)),
    ("ɽ", "hook", "r", ("x", "down-right", "first", 48, 160, 160)),
    ("Ɽ", "hook", "R", ("c", "down-right", "first", 52, 200, 200)),
    # capitals of lowercase-only shapes: enlarged to capital weight
    ("Ɛ", "enlarge", "ɛ", ("o", "O")),
    ("Ɑ", "enlarge", "ɑ", ("o", "O")),
    ("Ɩ", "enlarge", "ɩ", ("o", "O")),
    ("Ꞷ", "enlarge", "ꞷ", ("o", "O")),
    ("ɂ", "enlarge", "ʔ", ("O", "o")),
    ("Ʃ", "alias", "Sigma", None),
    # esh, ezh
    ("ʃ", "esh", "f", ("x", "uni0237")),
    ("Ʒ", "ezh", "Z", ("c", 760, 1.0, 1.0)),
    ("ʒ", "ezh", "z", ("x", 400, 0.9, 1.08)),
    ("ƹ", "mirror", "ʒ", None),
    ("Ƹ", "mirror", "Ʒ", None),
    # script g, upsilon, gamma, turned m with long leg
    ("ɡ", "hook", "q", ("x", "down-left", "last", -100, 200, 200)),
    ("ɠ", "hook", "ɡ", ("x", "up-right", "last", 900, 300, 200)),
    ("Ʊ", "turn", "Omega", "c"),
    ("ʊ", "enlarge", "Ʊ", ("O", "o")),
    ("Ɣ", "enlarge", "ɣ", ("o", "O", 0, 1462)),
    ("ɰ", "descend", "ɯ", ("x", "p", "last")),
    # modifier letters: the letters at the size of the superior figures
    ("ʰ", "superior", "h", None),
    ("ʲ", "superior", "j", None),
    ("ʷ", "superior", "w", None),
    ("ʸ", "superior", "y", None),
    ("ˡ", "superior", "l", None),
    ("ˠ", "superior", "gamma", None),
    ("ᵃ", "superior", "a", None),
    ("ᵉ", "superior", "e", None),
    ("ᵒ", "superior", "o", None),
    ("ᵘ", "superior", "u", None),
    ("ⁱ", "superior", "i", None),
    ("ⁿ", "superior", "n", None),
    ("ᵍ", "superior", "ɡ", None),
    ("ᶻ", "superior", "z", None),
    ("ᶿ", "superior", "theta", None),
    ("ˀ", "superior", "ɂ", None),
    ("ˁ", "superior", "ʕ", None),
    ("ᵋ", "superior", "ɛ", None),
    ("ᵓ", "superior", "ɔ", None),
    ("ᶤ", "superior", "ɨ", None),
    ("ᶶ", "superior", "ʉ", None),
    # hooks placed by hand: (band, cut boxes, pieces, [width]); F_TOP is the
    # top of f from its straight stem (centre 312 at y 1000), J_TAIL the
    # descender of ȷ (stem centre 320 at y 100)
    ("ʋ", "attach", "u", ("x", [(940, -BIG, BIG, 60), (620, 780, 960, BIG)],
                          [("f", (-BIG, 1000, 600, BIG), (312, 1000), (-0.5, 0.5, 864, 760))])),
    ("Ʋ", "attach", "U", ("c", [(1000, 1180, BIG, BIG)],
                          [("f", F_TOP, (312, 1000), (-0.55, 0.55, 1256, 1170))])),
    ("ƴ", "attach", "y", ("x", [(660, 700, 1000, BIG)],
                          [("f", F_TOP, (312, 1000), (0.5, 0.5, 785, 690))], 1080)),
    ("Ƴ", "attach", "Y", ("c", [(960, 1150, 1460, BIG)],
                          [("f", F_TOP, (312, 1000), (0.55, 0.55, 1111, 1140))])),
    ("Ɲ", "attach", "N", ("c", [(90, -BIG, 590, 60)],
                          [("uni0237", J_TAIL, (320, 100), (0.6, 0.6, 338, 80))])),
    ("Ƈ", "attach", "C", ("c", [(1150, 1300, 1400, BIG)],
                          [("f", F_HOOK, (312, 1100), (0.6, 0.6, 1170, 1360))])),
    ("Ɠ", "attach", "G", ("c", [(1150, 1300, 1400, BIG)],
                          [("f", F_HOOK, (312, 1100), (0.6, 0.6, 1170, 1360))])),
    ("ƈ", "attach", "c", ("x", [(600, 500, 900, BIG)],
                          [("f", F_HOOK, (312, 1100), (0.5, 0.5, 630, 800))])),
    # spacing modifiers made of existing glyphs
    ("ˮ", "double", "uni02BC", None),
    ("꞉", "alias", "colon", None),
    ("ʹ", "alias", "uni0374", None),  # U+0374 decomposes to U+02B9: same glyph
    ("″", "double", "uni2032", None),
    # small caps for the new case pairs, derived like their capitals
    ("ɔ.sc", "mirror", "c.sc", None),
    ("ǝ.sc", "mirror", "e.sc", None),
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
    ("ң.sc", "tail", "h.sc", ("s", "stem")),
    ("ҷ.sc", "tail", "uni0447.sc", ("s", "stem")),
    ("қ.sc", "tail", "k.sc", ("s", "foot")),
    ("җ.sc", "tail", "uni0436.sc", ("s", "foot")),
    ("ҳ.sc", "tail", "uni0445.sc", ("s", "foot")),
    ("һ.sc", "turn", "uni0447.sc", "s"),
    ("ү.sc", "alias", "y.sc", None),
    ("ұ.sc", "bar", "y.sc", ("s", 260)),
    ("ә.sc", "enlarge", "ǝ", ("o", "o.sc")),
    ("ə.sc", "alias", "ә.sc", None),
    ("ɓ.sc", "hook", "b.sc", ("s", "up-left", "first", 760, 260, -176)),
    ("ɗ.sc", "hook", "d.sc", ("s", "up-left", "first", 760, 260, -176)),
    ("ɖ.sc", "alias", "dcroat.sc", None),
    # ɲ.sc: no small cap until Ɲ is drawn (the thin left stem of N needs its own hook)
    ("ƒ.sc", "hook", "f.sc", ("s", "down-left", "first", 48, 160, 160)),
    ("ʈ.sc", "hook", "t.sc", ("s", "down-right", "first", 48, 160, 160)),
    ("ɽ.sc", "hook", "r.sc", ("s", "down-right", "first", 48, 160, 160)),
    ("ɛ.sc", "enlarge", "ɛ", ("o", "o.sc")),
    ("ɑ.sc", "enlarge", "ɑ", ("o", "o.sc")),
    ("ɩ.sc", "enlarge", "ɩ", ("o", "o.sc")),
    ("ꞷ.sc", "enlarge", "ꞷ", ("o", "o.sc")),
    ("ɂ.sc", "enlarge", "ʔ", ("O", "o.sc")),
    ("ʃ.sc", "alias", "sigma.sc", None),
    ("ʒ.sc", "enlarge", "Ʒ", ("O", "o.sc")),
    ("ƹ.sc", "mirror", "ʒ.sc", None),
    ("ʊ.sc", "enlarge", "Ʊ", ("O", "o.sc")),
    ("ɣ.sc", "enlarge", "ɣ", ("o", "o.sc", 0, 1062)),
    # small caps of hand-placed hooks: the capital at small-cap size
    ("ʋ.sc", "enlarge", "Ʋ", ("O", "o.sc")),
    ("ƴ.sc", "enlarge", "Ƴ", ("O", "o.sc")),
    ("ƈ.sc", "enlarge", "Ƈ", ("O", "o.sc")),
    ("ɠ.sc", "enlarge", "Ɠ", ("O", "o.sc")),
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

# the descender of Ц ц (and the small cap) is the model for Қ Ң Җ Ҳ Ҷ
TAIL = {"c": "uni0426", "x": "uni0446", "s": "uni0446.sc"}
TAIL_Y = 300  # straight stem in all three


def to_path(font, glyph=None, rec=None):
    path = pathops.Path()
    if glyph is not None:
        rec = DecomposingRecordingPen(font)
        glyph.draw(rec)
    rec.replay(path.getPen())
    return path


def rect_path(x0, y0, x1, y1):
    rec = RecordingPen()
    rect(rec, x0, y0, x1, y1)
    return to_path(None, rec=rec)


def path_op(a, b, op):
    return pathops.op(a, b, getattr(pathops.PathOp, op))


def shifted(path, dx, dy=0):
    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, dy)))
    return to_path(None, rec=rec)


def foot_top(font, name, stem):
    """Height of the foot serif under a stem (x0, x1): the lowest y where the
    ink there is no wider than the stem."""
    for y in range(2, 200, 2):
        s = [iv for iv in stems_at(font, name, y) if iv[0] <= stem[1] and iv[1] >= stem[0]]
        if s and s[0][1] - s[0][0] <= stem[1] - stem[0] + 2:
            return y - 2
    return 0


def tail_path(font, source, band, mode):
    """The letter with the descender of Ц: 'stem' replaces the foot of the
    right stem (Ң Ҷ); 'foot' hangs it under the right foot serif (Қ Җ Ҳ)."""
    tsrc = TAIL[band]
    sa, sb = stems_at(font, tsrc, TAIL_Y)[-1]
    letter = to_path(font, font[source])
    if mode == "stem":
        ta, tb = stems_at(font, source, TAIL_Y)[-1]
        letter = path_op(letter, rect_path(ta, -BIG, BIG, foot_top(font, source, (ta, tb))), "DIFFERENCE")
        keep = rect_path(sa, -BIG, BIG, TAIL_Y)
        dx = ta - sa
    else:
        fb = stems_at(font, source, 10)[-1][1]
        keep = rect_path(sa, -BIG, BIG, 30)
        dx = fb - sb - (sb - sa) / 2
    keep = path_op(keep, rect_path(-BIG, -BIG, BIG, 0), "UNION")
    piece = shifted(path_op(to_path(font, font[tsrc]), keep, "INTERSECTION"), dx)
    out = path_op(letter, piece, "UNION")
    rsb = font[tsrc].width - ink_bounds(font, tsrc)[2]
    return out, piece.bounds[2] + rsb


def vertical_runs(font, name, x):
    """(y0, y1) of the ink crossed by a vertical line at x, bottom to top."""
    cut = path_op(to_path(font, font[name]), rect_path(x - 0.5, -BIG, x + 0.5, BIG), "INTERSECTION")
    runs = []
    for contour in cut.contours:
        b = contour.bounds
        runs.append((b[1], b[3]))
    return sorted(runs)


def strokes(font, name):
    """(ink box, round stem at mid height, top hairline) of an o-like glyph."""
    b = ink_bounds(font, name)
    s = stems_at(font, name, (b[1] + b[3]) / 2)[0]
    top = vertical_runs(font, name, (b[0] + b[2]) / 2)[-1]
    return b, s[1] - s[0], top[1] - top[0]


def embolden(rec, ax, ay):
    """Thicken vertical strokes by ax and horizontal ones by ay (negative:
    thinner), moving each point along its outline's normal."""
    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())
    for contour in glyph.contours:
        pts = [(p.x, p.y) for p in contour.points]
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))
        sign = 1 if area > 0 else -1
        n = len(pts)
        moved = []
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i - 1], pts[(i + 1) % n]
            length = math.hypot(x1 - x0, y1 - y0) or 1.0
            nx, ny = (y1 - y0) / length, -(x1 - x0) / length
            moved.append((pts[i][0] + sign * nx * ax / 2, pts[i][1] + sign * ny * ay / 2))
        for p, (x, y) in zip(contour.points, moved, strict=True):
            p.x, p.y = x, y
    return glyph


def enlarge(font, source, src_ref, dst_ref, fit=None):
    """The source scaled so that src_ref's strokes and height become
    dst_ref's (ə -> Ә with o -> O): scaled uniformly, then the stems and
    hairlines brought to dst_ref's weight; sidebearings of dst_ref. With
    fit (y0, y1) the source's ink is scaled into that band instead (γ with
    its loop on the baseline for Ɣ)."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, src_ref), strokes(font, dst_ref)
    k = ((b1[3] - b1[1]) - h1) / ((b0[3] - b0[1]) - h0)
    if fit:
        sb = ink_bounds(font, source)
        k = (fit[1] - fit[0]) / (sb[3] - sb[1])
        b1 = (b1[0], fit[0], b1[2], fit[1])
    rec = DecomposingRecordingPen(font)
    font[source].draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
    glyph = embolden(rec, s1 - k * s0, h1 - k * h0)
    out = RecordingPen()
    glyph.draw(out)
    bp = BoundsPen(None)
    out.replay(bp)
    x0, y0, x1, _ = bp.bounds
    lsb, rsb = b1[0], font[dst_ref].width - b1[2]
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, lsb - x0, b1[1] - y0)))
    return moved, round(lsb + (x1 - x0) + rsb)


def draw_path(font, src, dst, out):
    """Draw a merged outline (a pathops Path or a recording) into dst,
    rounded and in the source's contour direction."""
    rec = RecordingPen()
    out.draw(rec) if hasattr(out, "draw") else out.replay(rec)
    ref = DecomposingRecordingPen(font)
    src.draw(ref)
    pen = RoundingPen(dst.getPen())
    if orientation(rec) != orientation(ref):
        pen = ReverseContourPen(pen)
    rec.replay(pen)


# hooks are taken from the font: the top of f (up), the descender of ȷ (down)
HOOK_SRC = {"up": ("f", 1512), "down": ("uni0237", -628)}
# top or bottom the hook reaches, per band (up) and for descenders (down)
HOOK_TOP = {"x": 1512, "c": 1462, "s": 1062}
HOOK_BOTTOM = {"x": -628, "c": -628, "s": -500}


def hook_path(font, source, band, kind, pick, cut, left, right):
    """The letter with a stem's end replaced by a hook from the font: kind
    'up-right' (ɓ: the top of f), 'up-left' (Ɓ: f mirrored), 'down-left'
    (ɲ: the descender of ȷ) or 'down-right' (ʈ: ȷ mirrored). The stem
    (first/last at mid height) loses its ink beyond cut, from left of it to
    right of it; the hook is scaled by the stem ratio to reach the band's
    top (or the descender)."""
    up = kind.startswith("up")
    mirror = kind in ("up-left", "down-right")  # f hooks right, ȷ left
    hsrc, hend = HOOK_SRC["up" if up else "down"]
    probe = 300 if not up else max(cut - 150, 400)
    stems = stems_at(font, source, probe)
    ta, tb = stems[0] if pick == "first" else stems[-1]
    # f: stem first, ball to the right; ȷ: stem last, ball to the left
    hs = stems_at(font, hsrc, 900)[0] if up else stems_at(font, hsrc, -200)[-1]
    k = (tb - ta) / (hs[1] - hs[0])
    if up:
        # start the hook where f's stem is still straight (below 1000)
        cut = min(cut, HOOK_TOP[band] - (hend - 1000) * k)
        reach = HOOK_TOP[band] - cut
        s0, s1 = hend - reach / k, BIG
    else:
        reach = cut - HOOK_BOTTOM[band]
        s0, s1 = -BIG, hend + reach / k
    piece = path_op(to_path(font, font[hsrc]), rect_path(-BIG, s0, BIG, s1), "INTERSECTION")
    # stem of the hook source where it meets the letter
    js = stems_at(font, hsrc, s0 + 2)[0] if up else stems_at(font, hsrc, s1 - 2)[-1]
    jx = (js[0] + js[1]) / 2
    sx = -k if mirror else k
    tx = (ta + tb) / 2 - sx * jx
    ty = cut - k * (s0 if up else s1)
    rec = RecordingPen()
    piece.draw(TransformPen(rec, (sx, 0, 0, k, tx, ty)))
    piece = to_path(None, rec=rec)
    if mirror:
        piece = path_op(piece, piece, "UNION")  # fix the reversed winding
    cut_box = (rect_path(ta - left, cut, tb + right, BIG) if up
               else rect_path(ta - left, -BIG, tb + right, cut))
    letter = path_op(to_path(font, font[source]), cut_box, "DIFFERENCE")
    return path_op(letter, piece, "UNION"), piece.bounds


def ezh(font, source, band, ym, kx, ky):
    """Ʒ ʒ: the top bar and diagonal of Z/z down to ym, and the lower bowl
    of the figure 3 from its middle tongue, scaled (kx, ky) and hung on the
    end of the diagonal."""
    top = path_op(to_path(font, font[source]), rect_path(-BIG, ym, BIG, BIG), "INTERSECTION")
    tongue_y = 760
    tx0 = stems_at(font, "three", tongue_y)[0][0]
    bowl = path_op(to_path(font, font["three"]), rect_path(-BIG, -BIG, BIG, tongue_y + 30),
                   "INTERSECTION")
    dx = stems_at(font, source, ym)[-1][0]
    rec = RecordingPen()
    bowl.draw(TransformPen(rec, (kx, 0, 0, ky, dx - kx * tx0, ym - ky * tongue_y)))
    out = path_op(top, to_path(None, rec=rec), "UNION")
    return out


def esh(font, source, band, bottom_model):
    """ʃ: the top of f (no crossbar), its stem run down, and the descender
    of ȷ at the bottom."""
    top = path_op(to_path(font, font[source]), rect_path(-BIG, 900, BIG, BIG), "INTERSECTION")
    fa, fb = stems_at(font, source, 920)[0]
    ja, _ = stems_at(font, bottom_model, -100)[-1]
    tail = path_op(to_path(font, font[bottom_model]), rect_path(-BIG, -BIG, BIG, -80), "INTERSECTION")
    tail = shifted(tail, fa - ja)
    stem = rect_path(fa, -100, fb, 920)
    out = path_op(path_op(top, stem, "UNION"), tail, "UNION")
    return shifted(out, 40 - out.bounds[0])


def superior(font, source):
    """A modifier letter (ʰ ⁿ ᵃ): the letter at the size and weight of the
    superior figures (0 -> ⁰ gives the scale and the stroke changes), on
    their baseline."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, "zero"), strokes(font, "zerosuperior")
    k = ((b1[3] - b1[1]) - h1) / ((b0[3] - b0[1]) - h0)
    ax, ay = s1 - k * s0, h1 - k * h0
    rec = DecomposingRecordingPen(font)
    font[source].draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
    out = RecordingPen()
    embolden(rec, ax, ay).draw(out)
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, ax / 2, b1[1] - (k * b0[1] - ay / 2))))
    return moved, round(k * font[source].width + ax)


def attach(font, source, cuts, pieces):
    """The letter minus the boxes in cuts, merged with pieces: each a part
    of a glyph (name, clip box) whose point (px, py) goes to (x, y),
    scaled (sx, sy); a negative sx mirrors. For hooks that need placing by
    hand (ʋ Ƴ Ɲ Ƈ)."""
    out = to_path(font, font[source])
    for box in cuts:
        out = path_op(out, rect_path(*box), "DIFFERENCE")
    for name, clip, (px, py), (sx, sy, x, y) in pieces:
        part = path_op(to_path(font, font[name]), rect_path(*clip), "INTERSECTION")
        rec = RecordingPen()
        part.draw(TransformPen(rec, (sx, 0, 0, sy, x - sx * px, y - sy * py)))
        out = path_op(out, path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG),
                                   "INTERSECTION"), "UNION")
    return out


def descend(font, source, band, model, pick=None):
    """A v with a stem down to the descender (ү): the stem and foot serif
    of the model's descender (p) under the vertex; with pick (first/last)
    under that stem instead (ɰ)."""
    if pick:
        stems = stems_at(font, source, 300)
        vx = sum(stems[0] if pick == "first" else stems[-1]) / 2
    else:
        vx = sum(stems_at(font, source, 26)[0]) / 2
    ma, mb = stems_at(font, model, -200)[0]
    piece = path_op(to_path(font, font[model]), rect_path(-BIG, -BIG, BIG, -60), "INTERSECTION")
    stem = rect_path(ma, -80, mb, 120)
    piece = shifted(path_op(piece, stem, "UNION"), vx - (ma + mb) / 2)
    return path_op(to_path(font, font[source]), piece, "UNION")


def mirrored_anchors(src, dst, width):
    for a in src.anchors:
        if a.name in KEEP_ANCHORS:
            dst.appendAnchor({"name": a.name, "x": width - a.x, "y": a.y})


def build(font, ch, op, source, band, name=None):
    src = font[source]
    small_cap = ch.endswith(".sc")
    g = font.newGlyph(name or glyph_name(ch))
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
    elif op == "tail":
        sband, mode = band
        out, right = tail_path(font, source, sband, mode)
        g.width = max(w, round(right))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "hook":
        sband, kind, pick, cut, left, right = band
        out, (_, _, x1, _) = hook_path(font, source, sband, kind, pick, cut, left, right)
        rsb = w - ink_bounds(font, source)[2]
        g.width = max(w, round(x1 + rsb))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "descend":
        sband, model, *pick = band
        g.width = w
        draw_path(font, src, g, descend(font, source, sband, model, *pick))
        for a in src.anchors:
            if a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "attach":
        _band, cuts, pieces, *width = band
        out = attach(font, source, cuts, pieces)
        rsb = w - ink_bounds(font, source)[2]
        g.width = width[0] if width else max(w, round(out.bounds[2] + rsb))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op in ("ezh", "esh"):
        out = (ezh(font, source, *band) if op == "ezh" else esh(font, source, *band))
        rsb = w - ink_bounds(font, source)[2]
        g.width = max(w, round(out.bounds[2] + rsb)) if op == "ezh" else round(out.bounds[2] + 40)
        draw_path(font, src, g, out)
        for a in src.anchors:
            if op == "ezh" and a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "superior":
        out, g.width = superior(font, source)
        draw_path(font, src, g, out)
    elif op == "enlarge":
        src_ref, dst_ref, *fit = band
        out, g.width = enlarge(font, source, src_ref, dst_ref, tuple(fit) or None)
        draw_path(font, src, g, out)
        ref = font[dst_ref]
        for a in ref.anchors:
            g.appendAnchor({"name": a.name, "x": round(a.x * g.width / ref.width), "y": a.y})
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

    def resolve(c):
        """Glyph name of a character, or of its small cap ("ƒ.sc" -> florin.sc)."""
        if c.endswith(".sc") and len(c) == 4:
            return cmap.get(ord(c[0]), glyph_name(c[0])) + ".sc"
        return cmap.get(ord(c), glyph_name(c))

    for ch, op, source, band in RECIPES:
        if only and ch not in only:
            continue
        if len(source) == 1 or (source.endswith(".sc") and len(source) == 4
                                and not source[0].isascii()):
            source = resolve(source)  # an earlier recipe's character
        if source not in font:
            sys.exit(f"{ch}: source {source} missing")
        name = resolve(ch)
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(ch)
                continue
            del font[name]
        try:
            g = build(font, ch, op, source, band, name)
        except (IndexError, KeyError, ValueError) as e:
            sys.exit(f"{ch}: {e!r}")
        if not ch.endswith(".sc"):
            cmap[ord(ch)] = g.name
        made.append(ch)
    font.save()
    print(f"drafted {len(made)}: {''.join(made)}")
    if kept:
        print(f"kept {len(kept)} existing: {''.join(kept)}")


if __name__ == "__main__":
    main()
