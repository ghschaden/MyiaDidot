"""Draft new characters from existing glyphs: same shape, turned, mirrored.

    python scripts/derive.py UFO [--redraft] [CHARS...]

Each recipe below makes one encoded glyph from a source glyph (a glyph name,
or an earlier recipe's character):

    alias     a component of the source (ɑ = α, ɪ = small-cap I); follows
              any later change to the source (its width on a run)
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
Each glyph drawn records the glyphs its recipe read, as they are saved
(lib org.myiadidot.builtFrom, scripts/built_from.py), so that a base edited
later is noticed; existing ones without the record get it on a run.
"""

import argparse
import itertools
import math
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import BasePen
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
# font lib: (stems, hairlines) of the font against the style the recipes'
# drawn thicknesses are for (make_bold.rederive sets it for the Bold's)
STROKE_KEY = "org.myiadidot.strokeScale"

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
    # ɸ: not the open Greek φ of this font, but o with a stem through it
    # (as in Charis): the top serif of l, the foot of q's descender
    ("ɸ", "attach", "o", ("x", [], [("rect", (438, -560, 602, 1400), (0, 0), (1, 1, 0, 0)),
                                     ("l", (-BIG, 1300, BIG, BIG), (0, 0), (1, 1, 218, 0)),
                                     ("q", (-BIG, -BIG, BIG, -540), (0, 0), (1, 1, -328, 0))])),
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
    # u with q's descender (and its foot serif) under the last stem
    ("ɥ", "attach", "u", ("x", [(946, -BIG, BIG, 60)],
                          [("q", (-BIG, -BIG, BIG, -100), (0, 0), (1, 1, 16, 0)),
                           ("rect", (782, -120, 946, 100), (0, 0), (1, 1, 0, 0))])),
    ("ɯ", "twin", "u", 600),
    # r's stem turned to the right: its own top serif and foot, the arm
    # and ball turned below
    # ɹ: r's stem turned to the right, its top serif and the right half of its
    # foot; the arm drawn as a Didot terminal: a hairline leaving the stem low,
    # turning down to the left, upright and thick into a ball on the baseline
    # (r's own ear turned upside down hangs as a hairline)
    ("ɹ", "attach", "space", ("x", [],
                              [("rect", (494, 30, 658, 860), (0, 0), (1, 1, 0, 0)),
                               ("r", (-BIG, 700, 390, BIG), (0, 0), (1, 1, 268, 0)),
                               ("r", (226, -BIG, BIG, 60), (0, 0), (1, 1, 268, 0)),
                               ("curl", {"at": ("pt", 540, 330, 56), "dir": 180, "turn": "ccw",
                                         "r": (230, 250), "sweep": 100, "ball": 80,
                                         "t": (160, 56)}, (0, 0), (1, 1, 0, 0))], 884)),
    ("ʌ", "turn", "v", "x"),
    ("ʍ", "turn", "w", "x"),
    ("ʎ", "turn", "y", "x"),
    ("ɒ", "mirror", "alpha", None),
    ("Ʌ", "turn", "V", "c"),
    ("Ɐ", "turn", "A", "c"),
    ("Ɯ", "twin", "U", 1000),
    ("⅄", "turn", "Y", "c"),
    ("ɔ", "turn", "c", "x"),  # not mirrored: the ball low, as Charis and Libertinus
    # mirrored
    ("Ɔ", "mirror", "C", None),
    ("Ǝ", "mirror", "E", None),
    ("ɘ", "mirror", "e", None),
    ("ɜ", "mirror", "epsilon", None),
    # glottal stops and clicks
    ("ʔ", "nodot", "question", None),
    ("Ɂ", "alias", "ʔ", None),
    ("ʕ", "mirror", "ʔ", None),
    # the clicks stand on the baseline (| itself descends); ǁ's bars closer than two |
    ("ǀ", "attach", "bar", ("x", [(-BIG, -BIG, BIG, 0)], [])),
    ("ǁ", "attach", "bar", ("x", [(-BIG, -BIG, BIG, 0)],
                            [("bar", (-BIG, 0, BIG, BIG), (0, 0), (1, 1, 230, 0))])),
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
    # (the bar op stops at the ink, which for ȷ ends at the stem: drawn across)
    ("ɟ", "lines", "uni0237", ("x", 56, [(70, 414, 570, 470)])),
    ("Ɍ", "bar", "R", ("c", 360, "first")),
    ("ɍ", "bar", "r", ("x", None, "first")),
    ("Ᵽ", "bar", "P", ("c", 360)),
    ("ᵽ", "bar", "p", ("x", -290)),
    ("Ǥ", "bar", "G", ("c", 260, "last")),
    # ǥ: the bar across the whole lower loop at its middle, standing out on
    # both sides, as in Charis, EB Garamond, Noto and Libertinus (across
    # its right side only, it was easy to miss)
    ("ǥ", "bar", "g", ("x", -340, "all", (45, 55))),
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
    # Serbian and Macedonian (locl SRB, MKD): б with its ascender leaning
    # back, ∂ set upright; the others differ only in the italic
    # (make_italic.ITALIC_RECIPES) and are the plain letters here
    ("б.loclSRB", "upright", "partialdiff", (13, "uni0431")),
    ("г.loclSRB", "alias", "uni0433", None),
    ("д.loclSRB", "alias", "uni0434", None),
    ("п.loclSRB", "alias", "uni043F", None),
    ("т.loclSRB", "alias", "uni0442", None),
    ("ѓ.loclSRB", "alias", "uni0453", None),
    # Bulgarian (locl BGR): the lowercase that follows handwriting, letters
    # of Latin shape: д ɡ, и u, к k, л ʌ, п n, т m, ш ɯ, ц щ with Ц's tail
    # (з stays: Bulgarian typographers differ on it)
    # (й ѝ are и with their mark, in the features); the italic keeps its
    # own (make_italic.ITALIC_RECIPES)
    ("д.loclBGR", "alias", "uni0261", None),
    ("и.loclBGR", "alias", "u", None),
    ("к.loclBGR", "alias", "k", None),
    ("л.loclBGR", "alias", "uni028C", None),
    ("п.loclBGR", "alias", "n", None),
    ("т.loclBGR", "alias", "m", None),
    ("ц.loclBGR", "tail", "u", ("x", "stem")),
    ("ш.loclBGR", "alias", "uni026F", None),
    ("щ.loclBGR", "tail", "uni026F", ("x", "stem")),
    # ... with ascenders: the stem (ж's middle one) up to l's top, its
    # serif cut; ъ's arm raised with it to the top, as b's serif runs out
    ("ь.loclBGR", "attach", "uni044C", ("x", [(-BIG, 760, BIG, BIG)],
                                         [("l", (-BIG, 700, BIG, BIG), (0, 0), (1, 1, 6, 0))])),
    ("ю.loclBGR", "attach", "uni044E", ("x", [(-BIG, 760, 560, BIG)],
                                         [("l", (-BIG, 700, BIG, BIG), (0, 0), (1, 1, 6, 0))])),
    ("ж.loclBGR", "attach", "uni0436", ("x", [(430, 760, 960, BIG)],
                                         [("l", (-BIG, 700, BIG, BIG), (0, 0), (1, 1, 415, 0))])),
    ("ъ.loclBGR", "attach", "uni044A", ("x", [(-BIG, 540, 394, BIG), (-BIG, 760, BIG, BIG)],
                                         [("l", (-BIG, 500, BIG, 1170), (0, 0), (1, 1, 194, 0)),
                                          ("uni044A", (-BIG, 540, 558, BIG), (0, 0), (1, 1, 0, 612))])),
    # в: b with β's loop above (rounded from the stem, its ball on b's bowl
    # top), not B's flat bowl: β above its waist (750) set on b's bowl top
    # (884), 0.772 as tall, its loop's thick side on b's stem where they are
    # as wide (1280; b cut above 1293); the loop one piece, β above 640 less
    # its stem below 1280 (in pieces, the seams kinked the loop); the notch
    # under the ball, between stem and b's arch, filled (along the stem, the
    # ball and the arch's hairline)
    ("в.loclBGR", "attach", "b", ("x", [(-BIG, 1293, BIG, BIG)],
                                  [("beta", ((-BIG, 640, BIG, BIG), (-BIG, 640, 400, 1280)), (0, 750),
                                    (1, 0.772, 0, 884)),
                                   ("poly", [(378, 690), (378, 905), (430, 905), (480, 862), (550, 862),
                                             (490, 800), (455, 760), (425, 720)], (0, 0), (1, 1, 0, 0))])),
    # г: the cursive г, set upright, is s mirrored (ƨ)
    ("г.loclBGR", "mirror", "s", None),
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
    # Ʈ: the stem thinning below the baseline into a light hook to the right
    # (as Charis and Libertinus; ȷ's tail scaled to the capital stem is heavy)
    ("Ʈ", "attach", "T", ("c", [(-BIG, -BIG, BIG, 400)],
                          [("poly", [(708, 401), (916, 401), ((916, 213), (890, 26), (838, -162)),
                                     (708, -162)], (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 773, -150, 130), "dir": 270, "turn": "ccw",
                                     "r": (170, 140), "sweep": 170, "ball": 65, "t": (130, 44)},
                            (0, 0), (1, 1, 0, 0))])),
    ("ɖ", "hook", "d", ("x", "down-right", "last", 48, 0, 200)),
    ("Ɖ", "alias", "Eth", None),
    ("ɭ", "hook", "l", ("x", "down-right", "first", 48, 160, 160)),
    ("ɳ", "hook", "n", ("x", "down-right", "last", 48, 160, 160)),
    ("ɽ", "hook", "r", ("x", "down-right", "first", 48, 160, 160)),
    ("Ɽ", "hook", "R", ("c", "down-right", "first", 52, 200, 200)),
    # capitals of lowercase-only shapes: enlarged to capital weight
    ("Ɛ", "enlarge", "ɛ", ("o", "O")),
    # Ɑ: the bowl of O against the right stem of H, as in Charis
    # Ɑ: the bowl of O, a little lower than the cap height so its hairlines
    # run into the side of H's right stem below the serifs, as in Charis
    ("Ɑ", "attach", "space", ("c", [],
                              [("O", (-BIG, -BIG, 1110, BIG), (0, -28), (1, 0.93, 0, 10)),
                               ("H", (1098, -BIG, BIG, BIG), (1098, 0), (1, 1, 1060, 0))], 1542)),
    ("Ɩ", "enlarge", "ɩ", ("o", "O")),
    ("Ꞷ", "stretch", "ꞷ", ("o", "O")),
    ("ɂ", "enlarge", "ʔ", ("O", "o")),
    ("Ʃ", "alias", "Sigma", None),
    # esh, ezh
    ("ʃ", "esh", "f", ("x", "uni0237")),
    # (band, end of the diagonal, bottom of the bowl, its right edge): the
    # bowl below the baseline and as wide as the bar, as in Charis
    ("Ʒ", "ezh", "Z", ("c", 680, -270, 1290)),
    ("ʒ", "ezh", "z", ("x", 450, -438, 860)),
    ("ƹ", "mirror", "ʒ", None),
    ("Ƹ", "mirror", "Ʒ", None),
    # script g, upsilon, gamma, turned m with long leg
    # ɡ: q's descender (and its foot) replaced by a tail sweeping down and
    # round to the left as wide as the bowl, into a ball under its left side
    ("ɡ", "curl", "q", ("x", [(500, -BIG, BIG, -90)],
                        {"at": ("y", -100, "last"), "dir": 270, "turn": "cw", "r": (290, 440),
                         "sweep": 165, "ball": 80, "t": (164, 52)})),
    ("ɠ", "hook", "ɡ", ("x", "up-right", "last", 800, 0, 200)),
    ("Ʊ", "turn", "Omega", "c"),
    ("ʊ", "enlarge", "Ʊ", ("O", "o")),
    ("Ɣ", "enlarge", "ɣ", ("o", "O", -500, 1434)),  # the loop below the baseline, as in Charis
    ("ɰ", "twin", "u", (600, "uni0265")),  # u and ɥ: the last stem descends
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
    # hooks drawn on (band, cuts, curl arguments): part of an elliptical ring
    # leaving the stroke at its own weight, ending in a ball
    ("ʋ", "curl", "u", ("x", [(940, -BIG, BIG, 60), (620, 600, BIG, BIG)],
                        {"at": ("y", 600, "last"), "dir": 90, "turn": "ccw", "r": (190, 262),
                         "sweep": 150, "ball": 78, "t": (164, 56)})),
    ("Ʋ", "curl", "U", ("c", [(1000, 1000, BIG, BIG)],
                        {"at": ("y", 1000, "last"), "dir": 90, "turn": "ccw", "r": (240, 400),
                         "sweep": 160, "ball": 92, "t": (64, 64)})),
    ("ƴ", "curl", "y", ("x", [(660, 700, 1000, BIG)],
                        {"at": ("y", 700, "last"), "dir": 70.7, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": 70}, 1080)),
    ("Ƴ", "curl", "Y", ("c", [(960, 1150, 1460, BIG)],
                        {"at": ("y", 1150, "last"), "dir": 63.4, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": 85})),
    # ȷ's tail at the width of N's thin left stem (64 of ȷ's 164), centred on it
    ("Ɲ", "attach", "N", ("c", [(90, -BIG, 590, 60)],
                          [("uni0237", J_TAIL, (320, 100), (64 / 164, 0.6, 326, 80))])),
    ("Ƈ", "curl", "C", ("c", [(1100, 900, BIG, BIG)],
                        {"at": ("x", 1080), "dir": 70, "turn": "cw", "r": 170,
                         "sweep": 145, "ball": 85})),
    ("Ɠ", "curl", "G", ("c", [(1100, 900, BIG, BIG)],
                        {"at": ("x", 1080), "dir": 70, "turn": "cw", "r": 170,
                         "sweep": 145, "ball": 85})),
    ("ƈ", "curl", "c", ("x", [(620, 500, BIG, BIG)],
                        {"at": ("x", 600), "dir": 70, "turn": "cw", "r": 130,
                         "sweep": 145, "ball": 70})),
    # more hooks, curls and loops drawn on
    # ʂ: s's bottom stroke turns down at the left into an upright stem below
    # the baseline, which hooks to the right, as ʈ's (and Charis's ʂ)
    ("ʂ", "attach", "s", ("x", [(-BIG, -BIG, 300, 360)],
                          [("curl", {"at": ("pt", 320, 38, 76), "dir": 180, "turn": "ccw",
                                     "r": (100, 100), "sweep": 90, "ball": 40, "t": (140, 76)},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((220, -50), (220, -300), 140), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 220, -300, 140), "dir": 270, "turn": "ccw",
                                     "r": (140, 120), "sweep": 150, "ball": 68, "t": (140, 52)},
                            (0, 0), (1, 1, 0, 0))])),
    # ʐ: the bar's right end turns down into an upright stem below the
    # baseline that hooks to the right, as ʂ (and Charis's ʐ); z's beak taken
    # off, so the hook leaves the bar's flat top (48) without a step
    ("ʐ", "attach", "z", ("x", [(700, -BIG, BIG, 500), (520, 48, 700, 200)],
                          [("curl", {"at": ("pt", 690, 24, 48), "dir": 0, "turn": "cw",
                                     "r": (100, 100), "sweep": 90, "ball": 40, "t": (140, 48)},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((790, -60), (790, -330), 140), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 790, -330, 140), "dir": 270, "turn": "ccw",
                                     "r": (150, 120), "sweep": 150, "ball": 68, "t": (140, 52)},
                            (0, 0), (1, 1, 0, 0))])),
    # ʑ: the bar turns up into a small loop and comes down through itself
    # into an upright tail below the baseline, as in Charis
    ("ʑ", "attach", "z", ("x", [(700, -BIG, BIG, 500)],
                          [("curl", {"at": ("pt", 640, 29, 57), "dir": 0, "turn": "ccw", "r": (120, 150),
                                     "sweep": 270, "ball": 40, "t": (110, 56)}, (0, 0), (1, 1, 0, 0)),
                           ("line", ((520, 200), (520, -330), 110), (0, 0), (1, 1, 0, 0))], 1000)),
    # ɕ: like ʑ, the bottom stroke runs on into a loop and comes down
    # through itself into an upright tail below the baseline, as in Charis
    ("ɕ", "attach", "c", ("x", [(620, -BIG, BIG, 400)],
                          [("curl", {"at": ("pt", 600, 18, 56), "dir": 0, "turn": "ccw",
                                     "r": (120, 150), "sweep": 270, "ball": 40, "t": (110, 56)},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((480, 200), (480, -330), 110), (0, 0), (1, 1, 0, 0))])),
    ("Ƭ", "curl", "T", ("c", [(-BIG, 600, 420, BIG)],
                        {"at": ("x", 440), "dir": 180, "turn": "ccw", "r": 150,
                         "sweep": 150, "ball": 80})),
    ("ⱳ", "curl", "w", ("x", [(1150, 700, BIG, BIG)],
                        {"at": ("y", 700, "last"), "dir": 71, "turn": "cw", "r": 160,
                         "sweep": 140, "ball": 70})),
    ("Ⱳ", "curl", "W", ("c", [(1800, 1120, BIG, BIG), (1600, 1300, BIG, BIG)],
                        {"at": ("y", 1120, "last"), "dir": 73.8, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": 85})),
    ("ɧ", "hook", "ɦ", ("x", "down-left", "last", 48, 160, 160)),
    # Ƙ: the hook on the thin arm, as on Ƴ; Ϗ: the leg run on below the
    # baseline and turned back; ʝ Ʝ: the stem's tail looped back across it
    ("Ƙ", "curl", "K", ("c", [(900, 1250, BIG, BIG), (800, 1360, BIG, BIG)],
                        {"at": ("y", 1250, "last"), "dir": 50.8, "turn": "cw", "r": 170,
                         "sweep": 150, "ball": 80})),
    # Ϗ: the leg (and its foot serif) cut above the baseline, run on in its
    # own direction and weight below it, turning back left into a ball
    # (the tail is ȷ's descender, its stem scaled to the leg's width and
    # turned to the leg's angle: its straight part overlaps the leg exactly)
    ("Ϗ", "attach", "K", ("c", [(850, -BIG, BIG, 200)],
                          [("uni0237", (-BIG, -BIG, BIG, 300), (320, -150),
                            (216 / 164, 216 / 164, 1159.5, 200, 35.6))], 1598)),
    ("ʝ", "attach", "j", ("x", [], [("line", ((-40, -520), (560, -170), 50), (0, 0), (1, 1, 0, 0))])),
    # Ʝ: the stem of J run down into the tail of ȷ (widened to the stem), crossed the same way
    ("Ʝ", "attach", "J", ("c", [(-BIG, -BIG, BIG, 250), (-BIG, -BIG, 440, 460)],
                          [("rect", (458, -110, 666, 260), (0, 0), (1, 1, 0, 0)),
                           ("uni0237", (-BIG, -BIG, BIG, -100), (238, -100), (1.27, 1, 458, -100)),
                           ("line", ((60, -540), (900, -170), 60), (0, 0), (1, 1, 0, 0))])),
    # the rhotic hook, and ɚ ɝ with it
    # ˞ rises from the letter and curls over to the right, like the ear of r
    ("˞", "curl", "space", ("x", [], {"at": ("pt", 60, 560, 56), "dir": 75, "turn": "cw",
                                      "r": (120, 140), "sweep": 170, "ball": 50}, 360)),
    # the hook joins the letter where its right side is upright
    ("ɚ", "attach", "ə", ("x", [], [("uni02DE", (-BIG, -BIG, BIG, BIG), (60, 560),
                                      (1, 1, 840, 600))], 962 + 300)),
    ("ɝ", "attach", "ɜ", ("x", [], [("uni02DE", (-BIG, -BIG, BIG, BIG), (60, 560),
                                      (1, 1, 660, 640))], 812 + 300)),
    # ɬ: l with a belt, a small ring (the degree sign) and its tail across
    ("ɬ", "attach", "l", ("x", [], [("degree", (-BIG, -BIG, BIG, BIG), (576, 1118),
                                      (0.45, 0.45, 220, 760)),
                                     ("rect", (220, 590, 564, 646), (0, 0), (1, 1, 0, 0))], 640)),
    # Ɬ: L with ɬ's belt, its ring at half the cap height on the stem's
    # left edge, a little larger for the capital's stem
    ("Ɬ", "attach", "L", ("c", [], [("degree", (-BIG, -BIG, BIG, BIG), (576, 1118),
                                      (0.5, 0.5, 314, 730)),
                                     ("rect", (314, 542, 702, 598), (0, 0), (1, 1, 0, 0))])),
    # the Greek yot and Latin chi capitals are J and X (as Libertinus's)
    ("Ϳ", "alias", "J", None),
    ("Ꭓ", "alias", "X", None),
    # Ʀ (yr): R's bowl and leg lowered on its full stem, the leg ending
    # below the baseline (as Charis and Libertinus draw it)
    ("Ʀ", "lower", "R", ("c", 200)),
    # ɞ: ɜ without its terminals, closed on the left by a drawn C at the
    # weight of ɜ's strokes, from its top stroke round to its bottom one,
    # its inside meeting ɜ's middle point
    ("ɞ", "attach", "ɜ", ("x", [(-BIG, 600, 400, BIG), (-BIG, -BIG, 400, 300)],
                          [("curl", {"at": ("pt", 400, 824.5, 145), "dir": 180, "turn": "ccw",
                                     "r": (226, 378.75), "sweep": 180, "ball": 70,
                                     "t": (180, 145)}, (0, 0), (1, 1, 0, 0))])),
    ("Ꞵ", "descend", "B", ("c", "p", "first")),
    ("ɤ", "enlarge", "gamma", ("o", "o", -16, 900)),
    ("Ɤ", "enlarge", "ɤ", ("o", "O")),
    # spacing modifiers made of existing glyphs
    # ˮ: the two as near as before ʼ took more room (respace.sidebearings 50, 90)
    ("ˮ", "double", "uni02BC", -140),
    ("꞉", "alias", "colon", None),
    # the Unicode hyphen and non-breaking hyphen: the hyphen-minus's shape
    # (babel hyphenates with U+2010 in several languages)
    ("‐", "alias", "hyphen", None),
    ("‑", "alias", "hyphen", None),
    ("ʹ", "alias", "uni0374", None),  # U+0374 decomposes to U+02B9: same glyph
    ("″", "double", "uni2032", None),
    # currency signs: letters with strokes (band, thickness, strokes)
    ("₦", "lines", "N", ("c", 64, [(40, 528, 1540, 592), (40, 842, 1540, 906)])),
    ("₩", "lines", "W", ("c", 64, [(20, 528, 2140, 592), (20, 842, 2140, 906)])),
    ("₭", "lines", "K", ("c", 64, [(40, 685, 1100, 749)])),
    ("₱", "lines", "P", ("c", 64, [(30, 1046, 1350, 1110), (30, 1220, 1350, 1284)])),
    ("₽", "lines", "P", ("c", 64, [(30, 300, 960, 364)])),
    ("₮", "lines", "T", ("c", 64, [((560, 380), (1060, 620)), ((560, 700), (1060, 940))])),
    ("₸", "lines", "T", ("c", 64, [(134, 1120, 1490, 1184)])),
    ("₲", "lines", "G", ("c", 64, [(806, -180, 870, 1640)])),
    ("₵", "lines", "C", ("c", 64, [(806, -180, 870, 1640)])),
    ("฿", "lines", "B", ("c", 64, [(668, -200, 732, 1634)])),
    ("₿", "lines", "B", ("c", 64, [(538, 1300, 602, 1634), (778, 1300, 842, 1634),
                                    (538, -200, 602, 120), (778, -200, 842, 120)])),
    ("₡", "lines", "C", ("c", 64, [((540, -150), (880, 1610)), ((840, -150), (1180, 1610))])),
    ("₫", "lines", "dcroat", ("x", 64, [(96, -330, 1098, -266)])),
    ("₨", "attach", "R", ("c", [], [("s", (-BIG, -BIG, BIG, BIG), (0, 0), (1, 1, 1490, 0))],
                          1490 + 840)),
    ("∅", "slash", "zero", ("c", "box", -0.08, -140, 1.08, 1580)),
    # more hooks, turned and barred letters
    ("Ƥ", "hook", "P", ("c", "up-left", "first", 1100, 300, -208)),
    ("ƥ", "hook", "p", ("x", "up-right", "first", 800, 300, 0)),  # below p's top serif
    ("Ɦ", "hook", "H", ("c", "up-right", "first", 1100, 300, 200)),
    ("Ɥ", "alias", "uni0427", None),  # a turned h at cap height is Ч, serifs and all
    ("ʄ", "hook", "ɟ", ("x", "up-right", "first", 830, 300, 0)),
    ("ʛ", "alias", "ɠ.sc", None),
    ("Ƃ", "alias", "uni0411", None),  # B with topbar is Б
    ("ƃ", "lines", "b", ("x", 56, [(222, 1440, 720, 1496)])),
    ("ǂ", "attach", "bar", ("x", [(-BIG, -BIG, BIG, 0)],
                            [("rect", (56, 560, 456, 624), (0, 0), (1, 1, 0, 0)),
                             ("rect", (56, 820, 456, 884), (0, 0), (1, 1, 0, 0))], 512)),
    ("ʘ", "attach", "O", ("c", [], [("period", (-BIG, -BIG, BIG, BIG), (264, 104), (1, 1, 834, 613))])),
    ("ɮ", "attach", "l", ("x", [(384, -BIG, BIG, 48)],
                          [("uni0292", (-BIG, -BIG, BIG, BIG), (78, 884), (1, 1, 330, 884))], 330 - 78 + 966)),
    ("ɺ", "attach", "uni0279", ("x", [(330, 700, 820, BIG)],
                                [("rect", (494, 650, 658, 1400), (0, 0), (1, 1, 0, 0)),
                                 ("r", (-BIG, 700, 390, BIG), (0, 0), (1, 1, 268, 628))])),
    # ɻ: ɹ's stem runs on below the baseline at its full width and hooks to
    # the right (the arm stays)
    ("ɻ", "attach", "uni0279", ("x", [(494, -BIG, BIG, 60)],
                                [("line", ((576, 80), (576, -250), 164), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 576, -250, 164), "dir": 270, "turn": "ccw",
                                           "r": (140, 120), "sweep": 150, "ball": 66,
                                           "t": (164, 52)}, (0, 0), (1, 1, 0, 0))])),
    ("ɾ", "attach", "r", ("x", [(-BIG, -BIG, 226, 60), (390, -BIG, BIG, 60), (-BIG, 780, 226, BIG)], [])),
    ("ᵳ", "midtilde", "ɾ", ("x",)),
    # raised arrows, superscript and subscript signs
    ("ꜛ", "superior", "uni2191", None),
    ("ꜜ", "superior", "uni2193", None),
    ("⁺", "superior", "plus", None),
    ("⁻", "superior", "minus", None),
    ("⁼", "superior", "equal", None),
    ("₊", "superior", "plus", "zeroinferior"),
    ("₋", "superior", "minus", "zeroinferior"),
    ("₌", "superior", "equal", "zeroinferior"),
    # punctuation and signs from existing glyphs
    ("⋮", "attach", "period", ("x", [], [("period", (-BIG, -BIG, BIG, BIG), (264, 104), (1, 1, 264, 504)),
                                         ("period", (-BIG, -BIG, BIG, BIG), (264, 104), (1, 1, 264, 904))])),
    ("⁂", "attach", "space", ("x", [], [("asterisk", (-BIG, -BIG, BIG, BIG), (552, 1067), (0.55, 0.55, 552, 1180)),
                                        ("asterisk", (-BIG, -BIG, BIG, BIG), (552, 1067), (0.55, 0.55, 302, 720)),
                                        ("asterisk", (-BIG, -BIG, BIG, BIG), (552, 1067), (0.55, 0.55, 802, 720))],
                              1104)),
    ("⫽", "attach", "slash", ("x", [], [("slash", (-BIG, -BIG, BIG, BIG), (0, 0), (1, 1, 300, 0))], 1022)),
    ("⊗", "attach", "uni25CB", ("x", [], [("multiply", (-BIG, -BIG, BIG, BIG), (576, 513), (0.79, 0.79, 614, 514))])),
    ("「", "attach", "space", ("x", [], [("rect", (300, 1362, 760, 1434), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (300, 560, 372, 1434), (0, 0), (1, 1, 0, 0))], 1000)),
    ("」", "attach", "space", ("x", [], [("rect", (240, -100, 700, -28), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (628, -100, 700, 774), (0, 0), (1, 1, 0, 0))], 1000)),
    # metrical symbols: the breve below and a macron-weight bar
    ("⏑", "attach", "space", ("x", [], [("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (1.3, 1.3, 550, 120))], 1100)),
    ("⏒", "attach", "space", ("x", [], [("rect", (200, 760, 900, 848), (0, 0), (1, 1, 0, 0)),
                                        ("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (1.1, 1.1, 550, 100))], 1100)),
    ("⏓", "attach", "space", ("x", [], [("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (1.1, 1.1, 550, 480)),
                                        ("rect", (200, 100, 900, 188), (0, 0), (1, 1, 0, 0))], 1100)),
    ("⏔", "attach", "space", ("x", [], [("rect", (200, 760, 1100, 848), (0, 0), (1, 1, 0, 0)),
                                        ("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 420, 120)),
                                        ("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 880, 120))], 1300)),
    ("⏕", "attach", "space", ("x", [], [("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 420, 500)),
                                        ("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 880, 500)),
                                        ("rect", (200, 100, 1100, 188), (0, 0), (1, 1, 0, 0))], 1300)),
    ("⏖", "attach", "space", ("x", [], [("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 425, 120)),
                                        ("uni032E", (-BIG, -BIG, BIG, BIG), (-440, -434), (0.8, 1.0, 875, 120))], 1300)),
    # triseme, tetraseme, pentaseme: a bar with an upright at the end(s), in the middle
    ("⏗", "attach", "space", ("x", [], [("rect", (200, 100, 1100, 188), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (1012, 100, 1100, 848), (0, 0), (1, 1, 0, 0))], 1300)),
    ("⏘", "attach", "space", ("x", [], [("rect", (200, 100, 1100, 188), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (200, 100, 288, 848), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (1012, 100, 1100, 848), (0, 0), (1, 1, 0, 0))], 1300)),
    ("⏙", "attach", "space", ("x", [], [("rect", (200, 100, 1100, 188), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (200, 100, 288, 848), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (606, 100, 694, 848), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (1012, 100, 1100, 848), (0, 0), (1, 1, 0, 0))], 1300)),
    # currency signs from parts of letters, with bars (64) across
    ("₴", "attach", "space", ("c", [], [("S", (-BIG, -BIG, BIG, BIG), (0, 0), (-1, 1, 1272, 0)),
                                        ("rect", (150, 528, 1120, 592), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (150, 860, 1120, 924), (0, 0), (1, 1, 0, 0))], 1272)),
    # ₺: a stem, the lower right quarter of O as its foot, two rising bars
    ("₺", "attach", "space", ("c", [], [("rect", (300, -28, 508, 1434), (0, 0), (1, 1, 0, 0)),
                                        ("O", (834, -BIG, BIG, 717), (834, 0), (1, 1, 508, 0)),
                                        ("line", ((140, 560), (720, 780), 64), (0, 0), (1, 1, 0, 0)),
                                        ("line", ((140, 840), (720, 1060), 64), (0, 0), (1, 1, 0, 0))], 1300)),
    # ₼: the top half of O on straight legs, a stem through the middle
    ("₼", "attach", "space", ("c", [], [("O", (-BIG, 717, BIG, BIG), (146, 717), (0.8, 1, 100, 717)),
                                        ("rect", (100, 0, 287, 720), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (1014, 0, 1201, 720), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (590, 0, 710, 1600), (0, 0), (1, 1, 0, 0))], 1300)),
    # ₾: O open at the upper right, two uprights in the top, a bar beneath
    ("₾", "attach", "space", ("c", [], [("O", (-BIG, -BIG, 834, BIG), (834, -28), (0.85, 0.85, 760, 120)),
                                        ("O", (834, -BIG, BIG, 717), (834, -28), (0.85, 0.85, 760, 120)),
                                        ("rect", (640, 760, 704, 1560), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (816, 760, 880, 1560), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (80, 0, 1440, 64), (0, 0), (1, 1, 0, 0))], 1520)),
    # ₹: two bars, the bowl of P, and the leg as a thick diagonal
    ("₹", "attach", "space", ("c", [], [("P", (522, 560, BIG, BIG), (522, 0), (1, 1, 350, 0)),
                                        ("rect", (150, 1382, 400, 1434), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (150, 980, 1180, 1044), (0, 0), (1, 1, 0, 0)),
                                        ("line", ((380, 650), (1000, 0), 160), (0, 0), (1, 1, 0, 0))], 1250)),
    # ₪: two arches cut from O (top half, scaled), one turned, interlocked
    ("₪", "attach", "space", ("c", [], [("O", (-BIG, 717, BIG, BIG), (146, 717), (0.55, 0.75, 100, 891)),
                                        ("rect", (100, 0, 229, 895), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (728, 350, 857, 895), (0, 0), (1, 1, 0, 0)),
                                        ("O", (-BIG, 717, BIG, BIG), (146, 717), (-0.55, -0.75, 1200, 543)),
                                        ("rect", (1071, 539, 1200, 1434), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (443, 539, 572, 1084), (0, 0), (1, 1, 0, 0))], 1300)),
    # small caps for the new case pairs, derived like their capitals
    ("ɔ.sc", "mirror", "c.sc", None),
    ("ǝ.sc", "mirror", "e.sc", None),
    ("ɐ.sc", "turn", "a.sc", "s"),
    ("ʌ.sc", "turn", "v.sc", "s"),
    ("ɯ.sc", "twin", "u.sc", 500),
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
    # ʀ.sc: the small-cap Ʀ (c2sc), r.sc lowered as Ʀ is R, in proportion
    ("ʀ.sc", "lower", "r.sc", ("s", 145)),
    ("ɬ.sc", "attach", "l.sc", ("s", [], [("degree", (-BIG, -BIG, BIG, BIG), (576, 1118),
                                           (0.4, 0.4, 227, 530)),
                                          ("rect", (227, 380, 553, 436), (0, 0), (1, 1, 0, 0))])),
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
    ("ɑ.sc", "enlarge", "Ɑ", ("O", "o.sc")),
    ("ɩ.sc", "enlarge", "ɩ", ("o", "o.sc")),
    ("ꞷ.sc", "stretch", "ꞷ", ("o", "o.sc")),
    ("ɂ.sc", "enlarge", "ʔ", ("O", "o.sc")),
    ("ʃ.sc", "alias", "sigma.sc", None),
    ("ʒ.sc", "enlarge", "Ʒ", ("O", "o.sc")),
    ("ƹ.sc", "mirror", "ʒ.sc", None),
    ("ʊ.sc", "enlarge", "Ʊ", ("O", "o.sc")),
    ("ɣ.sc", "enlarge", "ɣ", ("o", "o.sc", 0, 1062)),
    # small caps of hand-placed hooks: the capital at small-cap size
    ("ʋ.sc", "enlarge", "Ʋ", ("O", "o.sc")),
    ("ⱳ.sc", "enlarge", "Ⱳ", ("O", "o.sc")),
    ("ɤ.sc", "enlarge", "Ɤ", ("O", "o.sc")),
    ("ꞵ.sc", "enlarge", "Ꞵ", ("O", "o.sc")),
    ("ƭ.sc", "enlarge", "Ƭ", ("O", "o.sc")),
    ("ƙ.sc", "enlarge", "Ƙ", ("O", "o.sc")),
    ("ɲ.sc", "enlarge", "Ɲ", ("O", "o.sc")),
    ("ʝ.sc", "enlarge", "Ʝ", ("O", "o.sc")),
    ("ϗ.sc", "enlarge", "Ϗ", ("O", "o.sc")),
    # saltillo: the straight quote with its top at the small-cap height, as
    # ꞌ has it at the x-height and Ꞌ at the cap height
    ("ꞌ.sc", "attach", "space", ("s", [], [("quotesingle", (-BIG, -BIG, BIG, BIG), (0, 0),
                                              (1, 1, 0, 1040 - 1518))], 528)),
    ("ƴ.sc", "enlarge", "Ƴ", ("O", "o.sc")),
    ("ƈ.sc", "enlarge", "Ƈ", ("O", "o.sc")),
    ("ɠ.sc", "enlarge", "Ɠ", ("O", "o.sc")),
    ("ƥ.sc", "enlarge", "Ƥ", ("O", "o.sc")),
    ("ɦ.sc", "enlarge", "Ɦ", ("O", "o.sc")),
    ("ɥ.sc", "alias", "uni0447.sc", None),
    ("ƃ.sc", "alias", "uni0431.sc", None),
    # the IPA small capitals with a stroke are those small caps
    ("ᵻ", "alias", "ɨ.sc", None),
    ("ᵾ", "alias", "ʉ.sc", None),
]

# anchors that keep their meaning when the shape is mirrored left-right
# within the same vertical band
KEEP_ANCHORS = ("Top", "Acute", "Grave", "Dotaccent", "TopCap", "Bottom", "DotBelow")


def variant(ch):
    """A recipe's variant of a character, its suffix: "ɔ.sc" (the small
    cap), "б.loclSRB" (a localized form, unencoded); "" for the character."""
    return ch[1:] if len(ch) > 2 and ch[1] == "." and not ch[0].isascii() or ch.endswith(".sc") and len(ch) == 4 else ""


def glyph_name(ch):
    if variant(ch):
        return glyph_name(ch[0]) + variant(ch)
    return f"uni{ord(ch):04X}" if ord(ch) <= 0xFFFF else f"u{ord(ch):05X}"


def resolve(cmap, c):
    """Glyph name of a recipe's character or variant ("ƒ.sc" -> florin.sc,
    "б.loclSRB" -> uni0431.loclSRB) by the font's cmap; a glyph name as it is."""
    if variant(c):
        return cmap.get(ord(c[0]), glyph_name(c[0])) + variant(c)
    return cmap.get(ord(c), glyph_name(c)) if len(c) == 1 else c


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


def with_extremes(rec, out):
    """Replay a recording into the pen out with each cubic split where it
    turns in x or y (a sheared bowl's extremes move off its points),
    every point rounded to whole units."""
    from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT

    def turns(a, b, c, d):
        # roots of the derivative of one coordinate, inside the curve
        return [t for t in solveQuadratic(3 * (-a + 3 * b - 3 * c + d), 6 * (a - 2 * b + c), 3 * (b - a))
                if 0.02 < t < 0.98]

    def r(pt):
        return (round(pt[0]), round(pt[1]))

    current = None
    for op, args in rec.value:
        if op == "curveTo" and len(args) == 3:
            p0, (p1, p2, p3) = current, args
            ts = sorted(set(turns(p0[0], p1[0], p2[0], p3[0]) + turns(p0[1], p1[1], p2[1], p3[1])))
            for seg in splitCubicAtT(p0, p1, p2, p3, *ts) if ts else [(p0, p1, p2, p3)]:
                out.curveTo(r(seg[1]), r(seg[2]), r(seg[3]))
            current = p3
        else:
            getattr(out, op)(*[r(a) for a in args])
            current = args[-1] if args else current


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
    None); which is 'all', 'first', 'last' or 'inside' (Ө: the counter only).
    An overhang (left, right) is taken as given, past the letter's ink if
    so (ǥ: a bar standing out of the loop it crosses, not a ledge on it)."""
    y, which, over = (arg + (None, None, None))[:3]
    t, default_over = BARS[band]
    over = default_over if over is None else over
    if isinstance(over, tuple):
        stems = stems_at(font, source, bar_y(font, band, y))
        if which == "first":
            stems = stems[:1]
        elif which == "last":
            stems = stems[-1:]
        y = bar_y(font, band, y)
        rec = RecordingPen()
        rect(rec, stems[0][0] - over[0], y - t / 2, stems[-1][1] + over[1], y + t / 2)
        return rec
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


def lines_shape(font, source, band, arg):
    """Straight strokes given by hand, arg (t, items): ((x0, y0), (x1, y1))
    segments of thickness t, or (x0, y0, x1, y1) boxes (₦ ₩ ₱ ₲ ₡ ...)."""
    t, items = arg
    rec = RecordingPen()
    for it in items:
        if len(it) == 4:
            rect(rec, *it)
        else:
            stroke(rec, it[0], it[1], t)
    return rec


SHAPES = {"bar": bar_shape, "slash": slash_shape, "midtilde": midtilde_shape,
          "lines": lines_shape}

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
        # a little above the serif's top, so no hairline of it is left (the tail covers it)
        letter = path_op(letter, rect_path(ta, -BIG, BIG, foot_top(font, source, (ta, tb)) + 6), "DIFFERENCE")
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


def embolden(rec, ax, ay, factor=None):
    """Thicken vertical strokes by ax and horizontal ones by ay (negative:
    thinner). Each node moves out along its outline's normal (at a corner,
    along the bisector, as far as both edges move: a mitre, limited); its
    handles move with it and grow as their segment grows, so smooth nodes
    stay smooth and a circle stays a circle. factor(x, y, inward) -> 0..1, if
    given, scales ax at each node (make_italic: the thick strokes only)."""
    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())

    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    def unit(dx, dy):
        n = math.hypot(dx, dy)
        return (dx / n, dy / n) if n > 1e-9 else None

    # outlines wind like the largest contour, counters the other way: an
    # outline grows outward, a counter shrinks (its boundary moves into it),
    # so the ink around a counter thickens too
    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    for contour, a in zip(glyph.contours, areas, strict=True):
        P = contour.points
        n = len(P)
        sign = 1 if a > 0 else -1
        if (a > 0) != outer:
            sign = -sign
        ons = [i for i, p in enumerate(P) if p.type]
        if not ons or n < 3:
            continue
        old = [(p.x, p.y) for p in P]
        move, ks = {}, {}
        for i in ons:
            x, y = old[i]
            # the nearest distinct points before and after: the tangents
            b = next((old[(i - k) % n] for k in range(1, n) if old[(i - k) % n] != (x, y)), None)
            f = next((old[(i + k) % n] for k in range(1, n) if old[(i + k) % n] != (x, y)), None)
            t_in, t_out = unit(x - b[0], y - b[1]), unit(f[0] - x, f[1] - y)
            if not t_in or not t_out:
                move[i] = (0.0, 0.0)
                continue
            # right-hand normals of the edges, and their bisector
            n_in, n_out = (t_in[1], -t_in[0]), (t_out[1], -t_out[0])
            m = unit(n_in[0] + n_out[0], n_in[1] + n_out[1]) or n_in
            # the mitre: as far as both edges move; at a convex corner limited
            # (no spike), at a concave one (a crotch) whole, or a slit is left
            turn = t_in[0] * t_out[1] - t_in[1] * t_out[0]
            convex = turn * sign < 0
            half = max(0.5 if convex else 0.1, math.hypot(n_in[0] + n_out[0], n_in[1] + n_out[1]) / 2)
            k = factor(x, y, (-sign * m[0], -sign * m[1])) if factor else 1.0
            ks[i] = k
            move[i] = (sign * m[0] / half * ax * k / 2, sign * m[1] / half * ay / 2)
        new = list(old)
        for i in ons:
            new[i] = (old[i][0] + move[i][0], old[i][1] + move[i][1])
        # handles: along their old directions (so smooth nodes stay smooth),
        # their lengths fitted (least squares) to the curve's points offset
        # along their own normals, as far as the nodes are; a tight curve
        # keeps its shape
        def offset_fit(i, j, h1, h2, old=old, new=new, ks=ks, sign=sign):
            P0, P1, P2, P3 = old[i], old[h1], old[h2], old[j]
            A, B = new[i], new[j]
            ta = unit(P1[0] - P0[0], P1[1] - P0[1])
            tb = unit(P3[0] - P2[0], P3[1] - P2[1])
            if not ta or not tb:
                return None
            ka, kb = ks.get(i, 1.0), ks.get(j, 1.0)
            rows, rhs = [], []
            for step in range(1, 12):
                t = step / 12
                u = 1 - t
                pt = [u ** 3 * P0[q] + 3 * u * u * t * P1[q] + 3 * u * t * t * P2[q] + t ** 3 * P3[q] for q in (0, 1)]
                d = [3 * u * u * (P1[q] - P0[q]) + 6 * u * t * (P2[q] - P1[q]) + 3 * t * t * (P3[q] - P2[q])
                     for q in (0, 1)]
                tn = unit(*d)
                if not tn:
                    continue
                k = ka + (kb - ka) * t
                target = (pt[0] + sign * tn[1] * ax * k / 2, pt[1] - sign * tn[0] * ay / 2)
                b0, b1, b2, b3 = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
                base = [(b0 + b1) * A[q] + (b2 + b3) * B[q] for q in (0, 1)]
                for q in (0, 1):
                    rows.append((b1 * ta[q], -b2 * tb[q]))
                    rhs.append(target[q] - base[q])
            s11 = sum(r[0] * r[0] for r in rows)
            s12 = sum(r[0] * r[1] for r in rows)
            s22 = sum(r[1] * r[1] for r in rows)
            r1 = sum(r[0] * v for r, v in zip(rows, rhs, strict=True))
            r2 = sum(r[1] * v for r, v in zip(rows, rhs, strict=True))
            det = s11 * s22 - s12 * s12
            if abs(det) < 1e-9:
                return None
            la, lb = (r1 * s22 - r2 * s12) / det, (s11 * r2 - s12 * r1) / det
            # never shorter than a tenth of the old handles, nor turned round
            la = max(la, 0.1 * math.dist(P0, P1))
            lb = max(lb, 0.1 * math.dist(P2, P3))
            return (A[0] + ta[0] * la, A[1] + ta[1] * la), (B[0] - tb[0] * lb, B[1] - tb[1] * lb)

        for idx, i in enumerate(ons):
            j = ons[(idx + 1) % len(ons)]
            offs = [(i + k) % n for k in range(1, (j - i) % n or n)]
            if not offs:
                continue
            fitted = offset_fit(i, j, offs[0], offs[1]) if len(offs) == 2 else None
            if fitted:
                new[offs[0]], new[offs[1]] = fitted
                continue
            # other segments: the handles with their nodes, scaled as the chord
            c0, c1 = math.dist(old[i], old[j]), math.dist(new[i], new[j])
            r = c1 / c0 if c0 > 1e-6 else 1.0
            for k, h in enumerate(offs):
                own = i if k < len(offs) / 2 else j
                ox, oy = old[own]
                nx, ny = new[own]
                new[h] = (nx + (old[h][0] - ox) * r, ny + (old[h][1] - oy) * r)
        for p, (x, y) in zip(P, new, strict=True):
            p.x, p.y = x, y
    return glyph


# the alignment edges (flat tops and bottoms) of the Regular, which
# emboldening by ay moves by ay / 2: bottoms (descender, baseline), tops
ZONE_BOTTOMS = (-612, 0)
ZONE_TOPS = (884, 1040, 1434, 1496)


def rezone(glyph, ay):
    """Undo what emboldening by ay does to the alignment: the flat edges it
    moved by ay / 2 (bottoms down, tops up) put back on the zones, the
    heights between mapped linearly (by under 1 % of a zone)."""
    if not ay:
        return glyph
    moved = sorted([(z - ay / 2, z) for z in ZONE_BOTTOMS] + [(z + ay / 2, z) for z in ZONE_TOPS])

    def f(y):
        if y <= moved[0][0]:
            return y + moved[0][1] - moved[0][0]
        if y >= moved[-1][0]:
            return y + moved[-1][1] - moved[-1][0]
        for (y0, z0), (y1, z1) in itertools.pairwise(moved):
            if y0 <= y <= y1:
                return z0 + (y - y0) * (z1 - z0) / (y1 - y0)
        return y

    for c in glyph.contours:
        for p in c.points:
            p.y = f(p.y)
    return glyph


def embolden_simple(rec, ax, ay):
    """The earlier emboldening: each point (handles too) moved along the
    normal of the chord between its neighbours. Rounder at corners (it does
    not mitre), but smooth nodes come out a little broken; make_bold.py
    falls back on it where embolden() would close a gap to a slit."""
    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())

    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    for contour, a in zip(glyph.contours, areas, strict=True):
        pts = [(p.x, p.y) for p in contour.points]
        sign = 1 if a > 0 else -1
        if (a > 0) != outer:
            sign = -sign
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


def enlarge(font, source, src_ref, dst_ref, fit=None, stretch=False):
    """The source scaled so that src_ref's strokes and height become
    dst_ref's (ə -> Ә with o -> O): scaled uniformly, then the stems and
    hairlines brought to dst_ref's weight; sidebearings of dst_ref. With
    fit (y0, y1) the source's ink is scaled into that band instead (γ with
    its loop on the baseline for Ɣ)."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, src_ref), strokes(font, dst_ref)
    k = ((b1[3] - b1[1]) - h1) / ((b0[3] - b0[1]) - h0)
    # a capital made a small cap: scaled about the baseline from the cap height
    # to the small caps' (its flat edges on 0 and that height, not on O's
    # overshoots)
    on_baseline = src_ref == "O" and dst_ref.endswith(".sc")
    if on_baseline:
        k = font.lib.get("org.myiadidot.smallcapHeight", 1040) / (font.info.capHeight or 1434)
    if fit:
        sb = ink_bounds(font, source)
        k = (fit[1] - fit[0]) / (sb[3] - sb[1])
        b1 = (b1[0], fit[0], b1[2], fit[1])
    rec = DecomposingRecordingPen(font)
    if stretch:
        # stretch: across by the stem ratio, up by the height ratio, so
        # only the hairlines need bringing to weight (thinning the stems of
        # a uniform enlargement leaves slivers where thin strokes slant: Ꞷ)
        kx = s1 / s0
        font[source].draw(TransformPen(rec, (kx, 0, 0, k, 0, 0)))
        glyph = embolden(rec, 0, h1 - k * h0)
    else:
        font[source].draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
        glyph = embolden(rec, s1 - k * s0, h1 - k * h0)
        if on_baseline:  # its flat edges back on the zones
            glyph = rezone(glyph, h1 - k * h0)
    out = RecordingPen()
    glyph.draw(out)
    bp = BoundsPen(None)
    out.replay(bp)
    x0, y0, x1, _ = bp.bounds
    lsb, rsb = b1[0], font[dst_ref].width - b1[2]
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, lsb - x0, 0 if on_baseline else b1[1] - y0)))
    return moved, round(lsb + (x1 - x0) + rsb)


class CubicPen(BasePen):
    """Passes outlines on with quadratic segments made cubic."""

    def __init__(self, out):
        super().__init__(None)
        self.out = out

    def _moveTo(self, p):
        self.out.moveTo(p)

    def _lineTo(self, p):
        self.out.lineTo(p)

    def _curveToOne(self, p1, p2, p3):
        self.out.curveTo(p1, p2, p3)

    def _closePath(self):
        self.out.closePath()

    def _endPath(self):
        self.out.endPath()


def draw_path(font, src, dst, out):
    """Draw a merged outline (a pathops Path or a recording) into dst,
    rounded and in the source's contour direction."""
    from glyph_lint import LEDGE_KEEP, clean

    if isinstance(out, pathops.Path):  # no crumbs of the cuts and merges (glyph_lint)
        out = clean(out, ledges=dst.name not in LEDGE_KEEP)
    rec = RecordingPen()
    # pathops can return a quadratic segment; the font is cubic
    cubic = CubicPen(rec)
    out.draw(cubic) if hasattr(out, "draw") else out.replay(cubic)
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
# retroflex hooks (turning right: ɖ ɭ ɳ ɽ ɻ ʈ) stop short of the descender,
# as in Charis and Libertinus; the left-turning ones (ɲ ɱ ɡ) go all the way
HOOK_BOTTOM_RETROFLEX = {"x": -420, "c": -420, "s": -360}


def hook_path(font, source, band, kind, pick, cut, left, right, cuts=()):
    """The letter with a stem's end replaced by a hook from the font: kind
    'up-right' (ɓ: the top of f), 'up-left' (Ɓ: f mirrored), 'down-left'
    (ɲ: the descender of ȷ) or 'down-right' (ʈ: ȷ mirrored). The stem
    (first/last at mid height) loses its ink beyond cut, from left of it to
    right of it; the hook is scaled by the stem ratio to reach the band's
    top (or the descender). cuts: boxes also taken from the letter (an
    italic's exit stroke above the cut)."""
    up = kind.startswith("up")
    mirror = kind in ("up-left", "down-right")  # f hooks right, ȷ left
    hsrc, hend = HOOK_SRC["up" if up else "down"]
    probe = 300 if not up else max(cut - 150, 400)
    stems = stems_at(font, source, probe)
    # not the end of a stroke the probe grazes (an italic's exit stroke)
    stems = [s for s in stems if s[1] - s[0] >= 0.5 * max(t[1] - t[0] for t in stems)]
    ta, tb = stems[0] if pick == "first" else stems[-1]
    # f: stem first, ball to the right; ȷ: stem last, ball to the left
    hs = stems_at(font, hsrc, 900)[0] if up else stems_at(font, hsrc, -200)[-1]
    k = (tb - ta) / (hs[1] - hs[0])
    if up:
        # start the hook where f's stem is still straight (below 1000)
        cut = min(cut, HOOK_TOP[band] - (hend - 1000) * k)
        reach = HOOK_TOP[band] - cut
        # never below 900: f's crossbar ends at 884 (the hook is then shorter)
        s0, s1 = max(hend - reach / k, 900), BIG
    else:
        reach = cut - (HOOK_BOTTOM_RETROFLEX if kind == "down-right" else HOOK_BOTTOM)[band]
        s0, s1 = -BIG, hend + reach / k
    piece = path_op(to_path(font, font[hsrc]), rect_path(-BIG, s0, BIG, s1), "INTERSECTION")
    # the hook's stem where it meets the letter, and the letter's stem at
    # the cut: the hook is scaled across to that width exactly and put on
    # its edges, so the stroke runs on without a step
    js = stems_at(font, hsrc, s0 + 2)[0] if up else stems_at(font, hsrc, s1 - 2)[-1]
    # only ink over the stem counts (above a letter's x-height the cut may
    # meet nothing but a bowl's overshoot: ƥ); none there, the stem itself
    at_cut = [s for s in stems_at(font, source, cut - 2 if up else cut + 2) if s[1] > ta and s[0] < tb]
    ca, cb = (min(at_cut, key=lambda s: abs((s[0] + s[1]) / 2 - (ta + tb) / 2)) if at_cut
              else (ta, tb))
    sx = (cb - ca) / (js[1] - js[0])
    if mirror:
        sx, tx = -sx, ca + sx * js[1]
    else:
        tx = ca - sx * js[0]
    ty = cut - k * (s0 if up else s1)
    rec = RecordingPen()
    piece.draw(TransformPen(rec, (sx, 0, 0, k, tx, ty)))
    piece = to_path(None, rec=rec)
    if mirror:
        piece = path_op(piece, piece, "UNION")  # fix the reversed winding
    cut_box = (rect_path(ta - left, cut, tb + right, BIG) if up
               else rect_path(ta - left, -BIG, tb + right, cut))
    letter = path_op(to_path(font, font[source]), cut_box, "DIFFERENCE")
    for box in cuts:
        letter = path_op(letter, rect_path(*box), "DIFFERENCE")
    return path_op(letter, piece, "UNION"), piece.bounds


def ezh(font, source, band, ym, bottom, right):
    """Ʒ ʒ: the top bar and diagonal of Z/z down to ym, and the lower bowl
    of the figure 3 from its middle tongue hung on the end of the diagonal,
    scaled to reach down to bottom and across to right (as wide as the bar,
    as in Charis), its strokes brought back to the figure's weight."""
    top = path_op(to_path(font, font[source]), rect_path(-BIG, ym, BIG, BIG), "INTERSECTION")
    tongue_y = 760
    tx0 = stems_at(font, "three", tongue_y)[0][0]
    bowl = path_op(to_path(font, font["three"]), rect_path(-BIG, -BIG, BIG, tongue_y + 30),
                   "INTERSECTION")
    b = ink_bounds(font, "three")
    dx = stems_at(font, source, ym)[-1][0]
    kx = (right - dx) / (b[2] - tx0)
    ky = (ym - bottom) / (tongue_y - b[1])
    stem = max(e - a for a, e in stems_at(font, "three", 350))  # its upright side
    hair = vertical_runs(font, "three", 530)[0]
    hair = hair[1] - hair[0]  # its foot
    rec = RecordingPen()
    bowl.draw(TransformPen(rec, (kx, 0, 0, ky, dx - kx * tx0, ym - ky * tongue_y)))
    out = RecordingPen()
    embolden(rec, stem * (1 - kx), hair * (1 - ky)).draw(out)
    joined = path_op(top, to_path(None, rec=out), "UNION")
    # cut flat across the 3's waist, the bowl's top stands as a shelf beside
    # the diagonal: cut away above a line from where the diagonal's edge
    # meets it down to where the bowl's own top edge falls away, so the
    # diagonal meets the bowl in a crotch
    def top_at(x):
        """the top of the ink at x, looked at up to just above the cut"""
        cut = path_op(joined, rect_path(x - 0.5, -BIG, x + 0.5, ym + 120), "INTERSECTION")
        tops = [c.bounds[3] for c in cut.contours if c.bounds[1] < ym]
        return max(tops) if tops else None

    def right_at(y):
        return max(e for _, e in stems_at(font, source, y))

    x = right_at(ym + 1) + 2
    while x < right and (top_at(x) or 0) >= ym + 119:  # still under the diagonal
        x += 2
    shelf = top_at(x)
    while x < right and (top_at(x) or 0) > shelf - 4:  # along the shelf (and the stub on it)
        x += 2
    bx, by = x + 6, top_at(x + 6)
    if by is None or x >= right:
        return joined
    ay = shelf
    ax = right_at(ay - 1)
    h = 60  # the shelf and the stub of the 3's upper bowl on it
    if right_at(ay + h) >= bx:
        return joined
    cut = RecordingPen()
    cut.moveTo((ax, ay))
    cut.lineTo((bx, by))
    cut.lineTo((bx, ay + h))
    cut.lineTo((right_at(ay + h), ay + h))
    cut.closePath()
    return path_op(joined, to_path(None, rec=cut), "DIFFERENCE")


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


def superior(font, source, ref="zerosuperior"):
    """A modifier letter (ʰ ⁿ ᵃ): the letter at the size and weight of the
    superior figures (0 -> ⁰ gives the scale and the stroke changes), on
    their baseline; with ref "zeroinferior" a subscript (₊)."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, "zero"), strokes(font, ref)
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
    of a glyph (name, clip box, or boxes: the first less the others) whose
    point (px, py) goes to (x, y),
    scaled (sx, sy) and optionally turned (degrees, a fifth value); a negative
    sx mirrors. For hooks that need placing by hand (Ɲ, ₪, Ϗ); "rect" pieces
    are boxes, "line" pieces straight strokes, "poly" pieces polygons (with
    curves), "curl"
    pieces drawn hooks."""
    stems, hairs = font.lib.get(STROKE_KEY, (1, 1))

    def thick(v):
        """A drawn thickness in this font's weight: a stem's (100 and up) or a hairline's."""
        return v * (stems if v >= 100 else hairs)

    out = to_path(font, font[source])
    for box in cuts:
        out = path_op(out, rect_path(*box), "DIFFERENCE")
    for name, clip, (px, py), (sx, sy, x, y, *turn) in pieces:
        if name == "rect":  # a plain box
            part = rect_path(*clip)
        elif name == "line":  # a straight stroke: ((x0, y0), (x1, y1), thickness)
            rec = RecordingPen()
            stroke(rec, clip[0], clip[1], thick(clip[2]))
            part = to_path(None, rec=rec)
        elif name == "poly":  # a filled polygon: its points (a stroke tapering);
            # a triple of points is a curve to the last (two handles)
            rec = RecordingPen()
            rec.moveTo(clip[0])
            for pt in clip[1:]:
                rec.curveTo(*pt) if isinstance(pt[0], (tuple, list)) else rec.lineTo(pt)
            rec.closePath()
            part = to_path(None, rec=rec)
        elif name == "curl":  # a drawn hook ending in a ball: curl's arguments,
            # and optionally "cuts", boxes taken from it (so the ring's lead
            # does not stand out past the stroke it leaves)
            args = dict(clip)
            boxes = args.pop("cuts", ())
            if (stems, hairs) != (1, 1):
                if args.get("t"):
                    args["t"] = tuple(thick(v) for v in args["t"])
                if args.get("at", ("",))[0] == "pt" and len(args["at"]) > 3:
                    args["at"] = (*args["at"][:3], thick(args["at"][3]), *args["at"][4:])
                args["ball"] = args["ball"] * stems
            part = curl(font, "space", [], **args)
            for box in boxes:
                part = path_op(part, rect_path(*box), "DIFFERENCE")
        else:
            # a box, or boxes: the first kept, the others cut out of it (one
            # piece whose outline is the glyph's own, no seam to join)
            keep, *holes = clip if isinstance(clip[0], (tuple, list)) else (clip,)
            part = path_op(to_path(font, font[name]), rect_path(*keep), "INTERSECTION")
            for box in holes:
                part = path_op(part, rect_path(*box), "DIFFERENCE")
        rec = RecordingPen()
        # scaled, then turned by turn[0] degrees (counter-clockwise) about (px, py)
        t = Transform().translate(x, y).rotate(math.radians(turn[0] if turn else 0))
        part.draw(TransformPen(rec, t.scale(sx, sy).translate(-px, -py)))
        out = path_op(out, path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG),
                                   "INTERSECTION"), "UNION")
    return out


def _run_at(font, name, y, pick):
    runs = stems_at(font, name, y)
    return runs[0] if pick == "first" else runs[-1] if pick == "last" else runs[pick]


def _perpendicular(font, name, y, pick, dy=20):
    """Width of a stroke across its direction, from horizontal runs at y."""
    a, b = _run_at(font, name, y, pick)
    a2, b2 = _run_at(font, name, y + dy, pick)
    slope = ((a2 + b2) - (a + b)) / 2 / dy
    return (b - a) / math.hypot(1, slope)


def graft(font, source, cuts, piece, py, junction, clip=None, mirror=False, pick="first"):
    """The letter minus cuts, with a hook from another glyph (piece, its ink
    above py, within clip) scaled so its stroke at py is as thick, across
    the stroke, as the letter's where they meet. junction is ('y', y, pick):
    the piece's run at py goes onto the letter's run at y, edge on edge (a
    stem or arm running on: ʋ ƴ Ƴ), or ('x', x): its middle onto the middle
    of the letter's topmost ink at x (a hook rising from an arc: Ƈ ƈ Ɠ)."""
    pp = _perpendicular(font, piece, py, pick)
    if junction[0] == "y":
        _, ly, lpick = junction
        lp = _perpendicular(font, source, ly - 20, lpick)
    else:
        jx = junction[1]
        r0, r1 = vertical_runs(font, source, jx)[-1]
        q0, q1 = vertical_runs(font, source, jx + 20)[-1]
        lp = (r1 - r0) / math.hypot(1, ((q0 + q1) - (r0 + r1)) / 40)
    k = lp / pp
    box = clip or (-BIG, py, BIG, BIG)
    part = path_op(to_path(font, font[piece]),
                   rect_path(box[0], max(box[1], py - 2 / k), box[2], box[3]), "INTERSECTION")
    pa, pb = _run_at(font, piece, py, pick)
    sx = -k if mirror else k
    if junction[0] == "y":
        la, _ = _run_at(font, source, ly, lpick)
        tx = la - sx * (pb if mirror else pa)
        ty = ly - k * py
    else:
        tx = jx - sx * (pa + pb) / 2
        ty = (r0 + r1) / 2 - k * py
    rec = RecordingPen()
    part.draw(TransformPen(rec, (sx, 0, 0, k, tx, ty)))
    part = to_path(None, rec=rec)
    part = path_op(part, rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")  # winding
    out = to_path(font, font[source])
    for b in cuts:
        out = path_op(out, rect_path(*b), "DIFFERENCE")
    return path_op(out, part, "UNION")


def _ellipse(cx, cy, rx, ry):
    k = 0.5523
    rec = RecordingPen()
    rec.moveTo((cx + rx, cy))
    rec.curveTo((cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry))
    rec.curveTo((cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy))
    rec.curveTo((cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry))
    rec.curveTo((cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy))
    rec.closePath()
    return to_path(None, rec=rec)


def curl(font, source, cuts, at, dir, turn, r, sweep, ball, t=None, lead=3):
    """The letter minus cuts, with a hook drawn as part of an elliptical
    ring ending in a ball: it leaves the letter's stroke at `at` (('y', y,
    pick): the run at height y; ('x', x) / ('xb', x): the topmost /
    bottommost ink at x; ('pt', x, y, width)) going in
    direction dir (degrees; 90 = up), turning cw or ccw through sweep
    degrees on a centre line of radii r (one number: a circle). The ring is
    t thick: (across vertical parts, across horizontal parts), by default
    the stroke's own width where it meets the letter, so the stroke runs on
    at its weight; the ball (radius) sits inside the end, flush with the
    outer edge, as on f."""
    a, b = (r, r) if not isinstance(r, (tuple, list)) else r
    if at[0] == "y":
        _, y, pick = at
        ra, rb_ = _run_at(font, source, y, pick)
        px, py = (ra + rb_) / 2, y
        width = _perpendicular(font, source, y - 20, pick)
    elif at[0] == "pt":  # a given point and stroke width (˞)
        _, px, py, width = at
    else:  # 'x': the topmost ink at x, 'xb': the bottommost
        x = at[1]
        i = 0 if at[0] == "xb" else -1
        r0, r1 = vertical_runs(font, source, x)[i]
        q0, q1 = vertical_runs(font, source, x + 20)[i]
        px, py = x, (r0 + r1) / 2
        width = (r1 - r0) / math.hypot(1, ((q0 + q1) - (r0 + r1)) / 40)
    tv, th = t if t else (width, width)
    if at[0] == "y" and dir == 90:
        tv = rb_ - ra if not t else tv  # a vertical stem: its full width
    sign = -1 if turn == "cw" else 1
    # the centre lies to the side the curl turns to, across the direction
    d = math.radians(dir)
    nx, ny = -math.sin(d) * sign, math.cos(d) * sign
    start = math.degrees(math.atan2(-ny, -nx))  # from the centre to the start
    sa = math.radians(start)
    cx, cy = px - a * math.cos(sa), py - b * math.sin(sa)
    ring = path_op(_ellipse(cx, cy, a + tv / 2, b + th / 2),
                   _ellipse(cx, cy, a - tv / 2, b - th / 2), "DIFFERENCE")
    # the part swept, from just before the start (into the letter's stroke)
    # lead: degrees the ring starts back inside the letter's stroke, so a
    # stroke cut across at an angle to the ring still flows into it (Ϗ)
    angles = [start - sign * lead + sign * (sweep + lead) * i / 24 for i in range(25)]
    pts = [(cx, cy)] + [(cx + 4 * (a + tv) * math.cos(math.radians(g)),
                         cy + 4 * (b + th) * math.sin(math.radians(g))) for g in angles]
    rec = RecordingPen()
    rec.moveTo(pts[0])
    for q in pts[1:]:
        rec.lineTo(q)
    rec.closePath()
    wedge = path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")
    hook = path_op(ring, wedge, "INTERSECTION")
    end = math.radians(start + sign * sweep)
    bx = cx + (a + tv / 2 - ball) * math.cos(end)
    by = cy + (b + th / 2 - ball) * math.sin(end)
    hook = path_op(hook, _ellipse(bx, by, ball, ball), "UNION")
    out = to_path(font, font[source])
    for box in cuts:
        out = path_op(out, rect_path(*box), "DIFFERENCE")
    return path_op(out, hook, "UNION")


def lower(font, source, depth):
    """The letter right of its first stem (a bowl, a leg) moved down by
    depth, the stem and its foot serif staying: Ʀ from R."""
    _, b = stems_at(font, source, 500)[0]
    # the foot serif: as far right as the first run reaches at the baseline,
    # as high as that run is wider than the stem
    x1 = stems_at(font, source, 10)[0][1]
    top = 10
    while top < 300 and stems_at(font, source, top)[0][1] > b + 2:
        top += 2
    whole = to_path(font, font[source])
    region = path_op(rect_path(b, top, BIG, BIG), rect_path(x1, -BIG, BIG, top), "UNION")
    moved = shifted(path_op(whole, region, "INTERSECTION"), 0, -depth)
    return path_op(path_op(whole, region, "DIFFERENCE"), moved, "UNION")


def descend(font, source, band, model, pick=None):
    """A v with a stem down to the descender (ү): the stem and foot serif
    of the model's descender (p) under the vertex; with pick (first/last)
    under that stem instead (ɰ)."""
    if pick:
        stems = stems_at(font, source, 300)
        vx = sum(stems[0] if pick == "first" else stems[-1]) / 2
    else:
        runs = stems_at(font, source, 26)  # a rounded bottom (the Italic's v) is cut twice
        vx = (runs[0][0] + runs[-1][1]) / 2
    ma, mb = stems_at(font, model, -200)[0]
    piece = path_op(to_path(font, font[model]), rect_path(-BIG, -BIG, BIG, -60), "INTERSECTION")
    # up into the vertex, not into the counter above a rounded bottom; with
    # pick, up to where the stem was measured
    top = 300 if pick else 120
    while not pick and top > 0 and len(stems_at(font, source, top)) > 1:
        top -= 10
    stem = rect_path(ma, -80, mb, top)
    piece = shifted(path_op(piece, stem, "UNION"), vx - (ma + mb) / 2)
    return path_op(to_path(font, font[source]), piece, "UNION")


def mirrored_anchors(src, dst, width):
    for a in src.anchors:
        if a.name in KEEP_ANCHORS:
            dst.appendAnchor({"name": a.name, "x": width - a.x, "y": a.y})


def build(font, ch, op, source, band, name=None):
    src = font[source]
    small_cap = variant(ch) == ".sc"
    g = font.newGlyph(name or glyph_name(ch))
    if not variant(ch):
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
    elif op == "upright":
        # a sloped outline (∂) set upright about half the x-height, between
        # the sidebearings of the model letter (band: angle, model)
        angle, model = band
        s = math.tan(math.radians(angle))
        rec, sheared = DecomposingRecordingPen(font), RecordingPen()
        src.draw(rec)
        rec.replay(TransformPen(sheared, (1, 0, -s, 1, s * font.info.xHeight / 2, 0)))
        with_extremes(sheared, g.getPen())
        x0, _, x1, _ = ink_bounds(font, g.name)
        m0, _, m1, _ = ink_bounds(font, model)
        dx = round(m0 - x0)
        for c in g.contours:
            for pt in c.points:
                pt.x += dx
        g.width = round(x1 + dx + font[model].width - m1)
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
    elif op == "twin":
        # ɯ Ɯ from u U: a second copy whose first stem lies on the first's
        # last stem; the first loses what is right of that stem (its foot
        # spur, the right half of its serif), the copy brings its own
        # band: the height to find the stems at, or (height, glyph of the
        # copy): ɰ is u and ɥ
        y, other = band if isinstance(band, tuple) else (band, source)
        stems = stems_at(font, source, y)
        dx = stems[-1][1] - stems[0][1]
        first = path_op(to_path(font, src), rect_path(stems[-1][1], -BIG, BIG, BIG), "DIFFERENCE")
        out = path_op(first, shifted(to_path(font, font[other]), dx), "UNION")
        w = font[other].width
        g.width = round(w + dx)
        draw_path(font, src, g, out)
    elif op == "double":
        dx = w + (band or 0)  # band: the second one nearer by that much
        g.width = w + dx
        pen = g.getPen()
        pen.addComponent(source, (1, 0, 0, 1, 0, 0))
        pen.addComponent(source, (1, 0, 0, 1, dx, 0))
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
        sband, kind, pick, cut, left, right, *cuts = band
        out, (_, _, x1, _) = hook_path(font, source, sband, kind, pick, cut, left, right, *cuts)
        rsb = w - ink_bounds(font, source)[2]
        g.width = max(w, round(x1 + rsb))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "lower":
        _band, depth = band
        g.width = w
        draw_path(font, src, g, lower(font, source, depth))
        for a in src.anchors:
            if a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "descend":
        sband, model, *pick = band
        g.width = w
        draw_path(font, src, g, descend(font, source, sband, model, *pick))
        for a in src.anchors:
            if a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op in ("attach", "graft", "curl"):
        _band, cuts, pieces, *width = band
        if op == "graft":
            out = graft(font, source, cuts, **pieces)
        elif op == "curl":
            out = curl(font, source, cuts, **pieces)
        else:
            out = attach(font, source, cuts, pieces)
        if width:
            g.width = width[0]
        else:
            g.width = max(w, round(out.bounds[2] + w - ink_bounds(font, source)[2]))
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
        out, g.width = superior(font, source, *([band] if band else []))
        draw_path(font, src, g, out)
    elif op in ("enlarge", "stretch"):
        src_ref, dst_ref, *fit = band
        out, g.width = enlarge(font, source, src_ref, dst_ref, tuple(fit) or None,
                               stretch=op == "stretch")
        draw_path(font, src, g, out)
        ref = font[dst_ref]
        # a letter taller than dst_ref (ʒ.sc on the baseline, from Ʒ with its
        # tail below) takes its accents as far above its own top
        rise = ink_bounds(font, g.name)[3] - ink_bounds(font, dst_ref)[3]
        rise = rise if rise > 40 else 0
        for a in ref.anchors:
            g.appendAnchor({"name": a.name, "x": round(a.x * g.width / ref.width),
                            "y": a.y + (rise if a.y > 0 else 0)})
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
        order = list(font.glyphOrder)
        # a localized form after its letter (and the letter's other variants)
        stem = g.name.split(".")[0] if variant(ch) and not small_cap else None
        if stem in order:
            at = order.index(stem) + 1
            while at < len(order) and order[at].split(".")[0] == stem:
                at += 1
            order.insert(at, g.name)
        else:
            order.append(g.name)
        font.glyphOrder = order
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("chars", nargs="*")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    # characters, and small caps given whole ("ɔ.sc")
    only = set()
    for arg in args.chars:
        if variant(arg):
            only.add(arg)
        else:
            only.update(arg)

    font = ufoLib2.Font.open(args.ufo)
    from built_from import KEY as BUILT_KEY
    from built_from import Tracker, stamp

    # built on the spacing the recipes were tuned on, then cut again
    # (scripts/respace.py): scaled letters (small caps) keep the cut whole
    from respace import CUT_KEY, classifier, respace, undo

    done = font.lib.get(CUT_KEY)
    undo(font)
    cmap = {u: g.name for g in font for u in g.unicodes}
    made, kept, built = [], [], []
    bases = {}  # glyph: the glyphs its recipe read (built_from.py)
    aliases = []  # kept aliases: (glyph, source)

    def probe(ch, op, source, band, name):
        """What the recipe of an existing glyph reads, built aside and dropped."""
        tmp, order = f"_probe.{name}", font.glyphOrder
        categories = dict(font.lib.get("public.openTypeCategories", {}))
        tracker = Tracker(font)
        try:
            build(tracker, ch, op, source, band, tmp)
            return tracker.read - {tmp}
        except Exception:  # noqa: BLE001 (a recipe that no longer runs on it: no stamp)
            return None
        finally:
            if tmp in font:
                del font[tmp]
            font.glyphOrder = order
            font.lib["public.openTypeCategories"] = categories

    for ch, op, source, band in RECIPES:
        if only and ch not in only:
            continue
        if len(source) == 1 or (variant(source) and not source[0].isascii()):
            source = resolve(cmap, source)  # an earlier recipe's character
        if source not in font:
            sys.exit(f"{ch}: source {source} missing")
        name = resolve(cmap, ch)
        if name in font:
            lib = font[name].lib
            # unreviewed: a draft, or a derived small cap still marked a draft
            draft = lib.get(DRAFT_KEY) or (lib.get(DERIVED_KEY) and lib.get(SMALLCAP_DRAFT_KEY))
            if not (args.redraft and draft):
                kept.append(ch)
                if op == "alias":
                    aliases.append((name, source))
                # made before bases were recorded: recorded now, as they are
                if BUILT_KEY not in lib and not font[name].components:
                    read = probe(ch, op, source, band, name)
                    if read:
                        bases[name] = read
                continue
            del font[name]
        tracker = Tracker(font)
        try:
            g = build(tracker, ch, op, source, band, name)
        except (IndexError, KeyError, ValueError) as e:
            sys.exit(f"{ch}: {e!r}")
        if not g.components:  # an alias follows its source itself
            bases[g.name] = tracker.read
        if op == "alias":
            aliases.append((g.name, source))
        if not variant(ch):
            cmap[ord(ch)] = g.name
        made.append(ch)
        built.append(g.name)
    # what a recipe drew without merging (enlarged, turned) cleaned too
    from glyph_lint import fix

    fix(font, built)
    if done:
        respace(font, classifier(font, done["cut"], done["greekLower"]))
        font.lib[CUT_KEY] = done
    # an alias follows its source's outline, and its width too where the
    # cut moved neither (ʛ kept the width ɠ.sc had before it was redrafted)
    for name, source in aliases:
        g = font[name]
        if (len(g.components) == 1 and not g.contours
                and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            g.width = font[source].width
    # the bases as they are saved, cut again
    for name, read in bases.items():
        stamp(font, name, read)
    font.save()
    print(f"drafted {len(made)}: {''.join(made)}")
    if kept:
        print(f"kept {len(kept)} existing: {''.join(kept)}")


if __name__ == "__main__":
    main()
