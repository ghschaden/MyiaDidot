"""Derive the Bold master from the Regular (and the Bold Italic from the Italic).

    python scripts/make_bold.py [REGULAR.ufo] [BOLD.ufo]
    python scripts/make_bold.py sources/MyiaDidot-Italic.ufo sources/MyiaDidot-BoldItalic.ufo

A Didone bold is mostly the regular with heavier stems: the hairlines stay
nearly as fine, so the contrast grows. Every outline of a letter, figure or
sign is scaled across by KX (so the counters do not close up), its thick
strokes thickened by AX across in whatever direction they run and every edge
by AY (derive.embolden_by_weight: an edge moves by the weight of the stroke
it is on, so the upright hairlines stay hairlines and a thick diagonal gains
as much as a stem), and shifted right by AX/2, its advance growing by AX.
Accents and marks are only made a little heavier (MARK_AX, MARK_AY) and stay
where they are. Anchors and the offsets of components move with the
outlines, so composites land where the Regular's would; those the anchor
rules of composites.py can make are then rebuilt from the Bold's anchors,
after its stacking anchors are recomputed from its ink. The letters are then
spaced tighter (BOLD_CUT, scripts/respace.py). Kerning is scaled
by KX, and so are the horizontal values of the hand-set positioning in the
features. Pinholes and crumbs the emboldening leaves are cleaned
(glyph_lint.py). Afterwards: smallcaps.py on the Bold, make normalize.

This regenerates the whole Bold from the Regular: until the Bold has its own
reviewed edits, rerun it after changes to the Regular. From an italic
source (the Bold Italic from the Italic) the same is done in the upright
frame: each outline, anchor and offset deslanted by the source's italic
angle, emboldened, and slanted again (tx), so the stems gain AX across.
"""

import argparse
import functools
import math
import os
import re
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arithmetic  # noqa: F401  (first: one thread, AVX2 at most, before numpy loads)
import case_forms
import italic_inside
import kern_clear
import stroke_cache
from built_from import KEY as BUILT_KEY
from composites import SPECIAL, STACK_GAP_LC, Builder, stack_anchors
from derive import embolden, embolden_by_weight, embolden_simple, rezone
from glyph_lint import fix
from respace import CUT_KEY, classifier, respace, sidebearings
from space_figures import space as space_figures
from stroke_bold import SLIVER, emboldened, smooth_counter

ROOT = Path(__file__).resolve().parent.parent
KX = 1.04  # widening, so the counters keep their light
AX, AY = 90, 8  # stems 164 -> 254 (lowercase), 208 -> 298 (capitals); hairlines +8
# the Bold Italic's, from the Italic's lighter stems (make_italic.WEIGHT 10):
# its stems 0.96 of the Bold's, as the Italic's of the Regular's (reference
# bold italics 0.95-0.98; AX gave 0.92, the heavier Italic of before 1.01)
ITALIC_AX = 102
# strokes this thick and thinner gain no weight across, from there the more
# the thicker, all of it from THICK on (derive.embolden_by_weight)
THIN, THICK = 60, 160
ITALIC_THIN, ITALIC_THICK = 60, 160
# the Bold Italic is emboldened by its strokes (stroke_bold), its hairlines
# gaining this across (both sides), fading into ITALIC_AX as a stroke
# thickens: Libre Bodoni's quarter, hairlines 23 -> 30 per 1000
# (chosen 2026-10-28; Bodoni Moda's gain nothing)
ITALIC_HAIR = 12
JOBS = int(os.environ.get("MYIA_JOBS", "4"))  # processes at most (the project's limit: 4, 2026-11-03)
# Bold Italic letters gaining more than their strokes give (ITALIC_AX and
# ITALIC_HAIR times this): z, its top and bottom waves shallow, gains little
# across and near the zones nothing up and down; still light beside n
# (2026-10-28)
ITALIC_BOLD_HEAVIER = {"z": 1.15,
                       # the small caps the Italic's drafts leave light against h.sc,
                       # o.sc 0.86 and x.sc 0.75 where the Bold's are 1.07 and 0.87
                       # (samples.pdf, 2026-11-01); n.sc's 1.32 dropped
                       # once the Italic made it from N at weight (2026-11-05: its
                       # diagonal stood 1.28 of h.sc, N's 0.77)
                       "o.sc": 1.15, "c.sc": 1.15, "g.sc": 1.15, "q.sc": 1.15,
                       "x.sc": 1.6, "z.sc": 1.32}
# Bold Italic derived letters by strokes not joined to their base after
# (follow_bases): the same Italic strokes give the same base, the join
# tangles where they part
ITALIC_BOLD_UNJOINED = {"uni2C72": "Ⱳ: the curl's join tangled (53 nodes)"}
# the Italic's joins faired (make_italic.ITALIC_JOINS) in the bands of the
# Bold Italic's own recipes: ɰ's seam where ɥ's descender meets ɯ's last
# stem (the cut's top, 300); the Italic's band (250-350) also took ɯ's own
# nodes there, the first stroke's at 310 and the last hairline's at 256
# and where it meets the descender (276), each refitted in one curve to
# the next node: the hairline 41-45 against ɯ's 62-64 (2026-11-10)
ITALIC_BOLD_JOINS = {"ɰ": (290, 305)}
# Bold Italic letters still emboldened by weight: a repair after matches
# that outline's points (to redo on the stroked outline)
ITALIC_BOLD_BY_POINTS = {
    "dollar": "dollar_drawing.py's waist and ball entrances",
    "uni2135": "ℵ: aleph.py's return and join repairs",
    "trademark": "™: symbol_joins.py's shoulder and stem repair",
}
# heavier by ITALIC_BOLD_HEAVIER in their thick strokes only: x.sc's hairlines
# as much heavier swelled, a knee where each runs into its serif
ITALIC_BOLD_HAIR_KEPT = {"x.sc"}
MARK_AX, MARK_AY = 30, 8  # accents a little heavier
# lib: derived letters left emboldened whole, with why (follow_bases);
# tests/test_emboldened.py holds them to a list that only shrinks
WHOLE_KEY = "org.myiadidot.emboldenedWhole"
# derived letters their recipe does not make well from the Bold's glyphs
# (rederive): its cuts, placed for the Regular, leave a stub of the Bold's
# wider serif or step into the stem; left emboldened whole (reviewed)
BOLD_KEEP_WHOLE = {
    "uni044A.loclBGR": "Bulgarian ъ: a step where the raised arm's stem meets l's",
    "uni0265": "ɥ: a stub of the foot serif at the cut",
    "uni0261": "ɡ: a stub of the ear at the cut",
    "uni028B": "ʋ: a stub of the foot serif at the cut",
    "uni01AE": "Ʈ: the hook thin, a step where it meets the stem",
    "uni01B2": "Ʋ: the hook a thin ring, the stem standing above it",
    "uni0284": "ʄ: a piece of the bar left at the cut",
    "uni019D": "Ɲ: the hook thin, a speck of the foot serif left",
    "uni01B3": "Ƴ: a stub of the arm's serif left apart from the hook",
    "uni027B": "ɻ: a notch beside the stem at the cut",
    "uniA7B2": "Ʝ: a step at the foot of the stem",
    "uni01C2": "ǂ: the bars at the Regular's length, 0.85 of its advance",
    "uni01B4": "ƴ: y's arms thinner than the Bold y's under the curl's cut",
    "uni027A": "ɺ: l's stem at the Regular's width, a step where it meets ɹ's",
    "uni0432.loclBGR": "Bulgarian в: a ledge where β's loop meets the stem",
}
# ... and those made again though they differ from the emboldened letter
# more than rederive allows: the difference is the point (reviewed)
BOLD_REBUILD = {
    "uni0290": "ʐ: the foot at the Bold's weight; emboldened whole it was much too fat",
    "uni026E": "ɮ: its own recipe (BOLD_RECIPES); by the Regular's numbers the ʒ's spur stood inside the stem",
    "uni0260": "ɠ: the hook at the Bold's weight overhangs 5 % further than emboldened (derive.SPACING)",
    "uni0291": "ʑ: its own recipe (BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni0255": "ɕ: its own recipe (BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni025E": "ɞ: its own recipe (BOLD_RECIPES); emboldened, the junction swelled and the counters closed",
    "uni027E": "ɾ: its own recipe (BOLD_RECIPES), the Bold r's stem and foot slab under the Bold f's hook",
    # the middle tildes on the Bold's own base, as the Bold Italic's
    # (ITALIC_BOLD_REBUILD): emboldened whole and joined to the base, the
    # foot serif's left end was cut at a slant, the stem's left edge swelled
    # about 8 units at the tilde, and ᵲ ᵳ kept the inward bump at the
    # shoulder that fair_bold_stem takes out of r (2026-11-04)
    **{name: f"{ch}: the tilde on the Bold's {base}" for name, ch, base in (
        ("uni1D6C", "ᵬ", "b"), ("uni1D6D", "ᵭ", "d"), ("uni1D6E", "ᵮ", "f"), ("uni1D6F", "ᵯ", "m"),
        ("uni1D70", "ᵰ", "n"), ("uni1D71", "ᵱ", "p"), ("uni1D72", "ᵲ", "r"), ("uni1D73", "ᵳ", "ɾ"),
        # and the rest (2026-11-09): emboldened whole, the tapered tilde
        # moved ᵶ's node at the foot's right edge up to 24 (a 2-degree kink)
        ("uni1D74", "ᵴ", "s"), ("uni1D75", "ᵵ", "t"), ("uni1D76", "ᵶ", "z"),
        ("uni026B", "ɫ", "l"), ("uni2C62", "Ɫ", "L"), ("uni026B.sc", "ɫ.sc", "l.sc"))},
}
# Bold Italic recipes made again whole from the Bold Italic's final bases,
# every letter they make: the modifier letters (ʰ ʷ ʸ ᵘ ⁿ ⁱ ᶤ ᶶ ...),
# its w y u n i at the superior figures' size and weight, as the Italic
# makes them of its own. Stroked at their scale from the Italic's, the
# entry hook's inner curl was squeezed into a corner (32 degrees: the
# strokes gain 34 across, 4 up and down; 2026-11-02). Set with
# the side bearings their optical fit gave them; only those the Italic
# derived so, and only where the gate takes them (ᵘ ⁿ: the arch's crotch a
# notch at that size, kept as stroked)
ITALIC_BOLD_REBUILD_OPS = {"superior": "a modifier letter: the Bold Italic's letter made small"}
ITALIC_BOLD_REBUILD = {
    # the slashed letters: the slash drawn on the stroked base at the Bold
    # Italic's weight (emboldened whole, it left a slit by the diagonal it
    # crosses and redrew the brackets beside it: Ⱥ; 2026-10-28)
    "uni023A": "Ⱥ: the slash on the Bold Italic's A", "uni2C65": "ⱥ: the slash on the Bold Italic's a",
    "uni023B": "Ȼ: the slash on the Bold Italic's C", "uni023C": "ȼ: the slash on the Bold Italic's c",
    "uni023E": "Ⱦ: the slash on the Bold Italic's T", "uni2C65.sc": "ⱥ.sc: the slash on a.sc",
    "uni023C.sc": "ȼ.sc: the slash on c.sc", "uni2C66.sc": "ⱦ.sc: the slash on t.sc",
    "uni2C66": "ⱦ: the slash on the Bold Italic's t (ITALIC_BOLD_RECIPES)",
    # ɉ: emboldened whole its dot came out larger than j's (2026-11-09); the
    # bar on the Bold Italic's j, its arms then lengthened by j_bar.py
    "uni0249": "ɉ: the bar on the Bold Italic's j (ITALIC_BOLD_RECIPES)",
    # ʝ ʲ: made on the Bold Italic's own j whatever the Italic's (its dot
    # set as j's, 2026-11-09, the rebuild was no longer taken and the
    # emboldened Italic letter came back, its spacing 19 and 11 wider)
    "uni029D": "ʝ: the crossed tail on the Bold Italic's j",
    "uni02B2": "ʲ: the Bold Italic's j made small",
    # ʊ: Ʊ made small, emboldened whole from the Italic's: its top-left
    # flag ran into the bowl and closed the counter (2026-11-09); made
    # small from the Bold Italic's Ʊ, which keeps the gap
    "uni028A": "ʊ: the Bold Italic's Ʊ made small",
    # and the middle tildes, at the slashes' weight (2026-10-28:
    # emboldened whole the tilde was heavier than the slashes, and ᵭ's upper
    # counter, small and tight, came out a triangle)
    **{name: f"{ch}: the tilde on the Bold Italic's {base}" for name, ch, base in (
        ("uni026B", "ɫ", "l"), ("uni2C62", "Ɫ", "L"), ("uni1D6C", "ᵬ", "b"), ("uni1D6D", "ᵭ", "d"),
        ("uni1D6E", "ᵮ", "f"), ("uni1D6F", "ᵯ", "m"), ("uni1D70", "ᵰ", "n"), ("uni1D71", "ᵱ", "p"),
        ("uni1D72", "ᵲ", "r"), ("uni1D73", "ᵳ", "ɾ"), ("uni1D74", "ᵴ", "s"), ("uni1D75", "ᵵ", "t"),
        ("uni1D76", "ᵶ", "z"), ("uni026B.sc", "ɫ.sc", "l.sc"))},
    # Ɯ, U twinned: its stems the Bold Italic U's (by strokes its own, its
    # third stem's edge unioned with U's crossed it in a step;
    # 2026-10-29)
    "uni019C": "Ɯ: the twin of the Bold Italic's U",
    # ǥ.sc: the bar on the Bold Italic's g.sc (emboldened whole and joined
    # to g.sc again, the two outlines nearly one, the union left 3 short
    # wobbles in the bowl by the bar and 27 nodes more: 2026-11-05)
    "uni01E5.sc": "ǥ.sc: the bar on the Bold Italic's g.sc",
    # n.sc: made from the Bold Italic's N as the Italic's from its N
    # (make_italic ITALIC_SC_RECIPES); stroked from the Italic's, the
    # diagonal stood 1.21 of h.sc (N's 0.77), the left foot lost its
    # bracket and the right stem's top bracket wobbled (2026-11-05)
    "n.sc": "n.sc: the Bold Italic's N enlarged",
    # ɴ, n.sc enlarged (derive.RECIPES): stroked from the Italic's, its
    # diagonal and feet came out as n.sc's did
    "uni0274": "ɴ: the Bold Italic's n.sc enlarged",
    # ʉ, the bar on u: u's knees drawn as the Italic turns (stroke_bold
    # KNEE_QUARTER); by strokes its own, the bar cutting the stem, its knee
    # stayed and its union with u left scraps (2026-10-29); its own recipe
    # (ITALIC_BOLD_RECIPES: the bar's weight)
    "uni0289": "ʉ: the bar on the Bold Italic's u (ITALIC_BOLD_RECIPES)",
    "uni0284": "ʄ: its own recipe (ITALIC_BOLD_RECIPES); emboldened whole, it lost its ɟ base and stayed light",
    "uni0290": "ʐ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the hook's counter closed",
    "uni0291": "ʑ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni0255": "ɕ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni025E": "ɞ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the junction swelled and the counters closed",
    "uni04B2": "Ҳ: the tail on the Bold Italic's X; the Italic's tail emboldened, a kink where it meets the serif",
    "uni0273": "ɳ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the descender too light, the leg pinched",
    "uni0271": "ɱ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the hook too light, the leg notched",
    "uni0267": "ɧ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the leg pinched above the hook",
    "uni0188": "ƈ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the hook a hairline pinched where it leaves c",
    "uni0187": "Ƈ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni0193": "Ɠ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni0198": "Ƙ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni01B2": "Ʋ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni01B3": "Ƴ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni01B4": "ƴ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni028B": "ʋ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni2C73": "ⱳ: its own recipe (ITALIC_BOLD_RECIPES); emboldened or scaled from the Italic's, its curl closed on the ball",
    "uni01AC": "Ƭ: its own recipe (ITALIC_BOLD_RECIPES); the Italic's ball scaled up closed the curl",
    "uni0188.sc": "ƈ.sc: its own curl on the Bold Italic ƈ.sc (ITALIC_BOLD_RECIPES); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0199.sc": "ƙ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01A5.sc": "ƥ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01AD.sc": "ƭ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01B4.sc": "ƴ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0260.sc": "ɠ.sc: its own curl on the Bold Italic ɠ.sc (ITALIC_BOLD_RECIPES); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0266.sc": "ɦ.sc: its own curl on the Bold Italic h.sc (ITALIC_BOLD_RECIPES); emboldened from the Italic's draft, its curl closed on the ball",
    "uni028B.sc": "ʋ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni049A": "Қ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the curl notched",
    "uni0496": "Җ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the ball ran into the descender",
    "uni0497": "җ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, a stub at the descender",
    "uni049B": "қ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, crumbs of the cut at the descender",
    "uni04A3": "ң: its own recipe (ITALIC_BOLD_RECIPES); emboldened, a pinhole where the descender's curl meets its stroke",
    "uni0270": "ɰ: its own recipe (ITALIC_BOLD_RECIPES): ɯ, ɥ's descender",
    "uni2C64": "Ɽ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni01AE": "Ʈ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni027D.sc": "ɽ.sc: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni0288.sc": "ʈ.sc: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    # the currency bars on the Bold Italic's own letters (
    # 2026-11-08): emboldened whole, the stem and the S grew over the bars'
    # left ends, which no longer showed
    "uni20AE": "₮: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the bars hidden left of the stem",
    "uni0436.loclBGR": "ж.loclBGR: its own recipe (ITALIC_BOLD_RECIPES); the Italic's left a notch where l meets the stem",
    "uni20B4": "₴: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the bars hidden left of the S",
}
# recipes drawn at the Bold's weight (in the Bold Italic, in its upright
# frame), where the source's recipe scaled up does not fit (a hook's or a
# loop's counter closes, its turn too tight for a stroke twice as heavy):
# used as given, nothing scaled
BOLD_RECIPES = {
    # ᵴ: on the Bold's s (2026-11-09) the tapered tilde's left tip hung
    # 5-8 units over the foot serif's top, a notch; 30 higher it stands clear
    # (from 487 its right end crowds the top serif)
    "ᵴ": ("midtilde", "s", ("x", 472)),
    # Ƭ: the Regular's curl, but leaving the bar at the bar's own weight (60)
    # with the bracket under it cut away (420-560): from the Regular's
    # recipe the ring took the stroke where the bracket swells (124 at 420),
    # so it thickened toward the ball (2026-11-06); the upright
    # part of the ring thick (110), as the Bold Italic's
    "Ƭ": ("curl", "T", ("c", [(-10000, 600, 420, 10000), (420, 1250, 560, 1374)],
                        {"at": ("pt", 420, 1404, 60), "dir": 180, "turn": "ccw", "r": (150, 150),
                         "sweep": 150, "ball": None, "t": (110, 60), "lead": 10})),
    # ʑ, ɕ: the Regular's, the loop 0.55 of o's stem (as there), wider and
    # rounder so its counter stays open; the base cut at the tail, the loop
    # alone the bottom (overshooting as o does), so no edge of the bar steps
    # into the counter; ʑ as much wider than z as its loop needs
    "ʑ": ("attach", "z", ("x", [(605, -10000, 10000, 320), (800, -10000, 10000, 500)],
                          [("curl", {"at": ("pt", 690, 20, 60), "dir": 0, "turn": "ccw", "r": (160, 150),
                                     "sweep": 270, "ball": 60, "t": (150, 60), "lead": 35},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((530, 200), (530, -330), 150), (0, 0), (1, 1, 0, 0))], 1075)),
    "ɕ": ("attach", "c", ("x", [(585, -10000, 10000, 400)],
                          [("curl", {"at": ("pt", 670, 10, 60), "dir": 0, "turn": "ccw", "r": (160, 150),
                                     "sweep": 270, "ball": 60, "t": (150, 60), "lead": 35},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((510, 200), (510, -330), 150), (0, 0), (1, 1, 0, 0))])),
    # ɞ: the Regular's, its bowl met to the Bold ɜ's top stroke (821, 156
    # thick at x=400), wider and lighter than o's stem so both counters stay open
    "ɞ": ("attach", "ɜ", ("x", [(-10000, 600, 400, 10000), (-10000, -10000, 400, 300)],
                          [("curl", {"at": ("pt", 400, 821, 156), "dir": 180, "turn": "ccw",
                                     "r": (250, 375.5), "sweep": 180, "ball": 70, "t": (230, 156)},
                            (0, 0), (1, 1, 0, 0))])),
    # ɾ: the Regular's, the Bold r's stem under the Bold f's hook, placed
    # by their own stems and tops (by the Regular's numbers f's stem stood
    # off r's; emboldened whole, its stem's right edge wobbled under r's
    # shoulder: 2026-11-04)
    "ɾ": ("attach", "r", lambda up: fishhook_band(up)),
    # ɮ: the Regular's, placed on the Bold's l and ʒ by their own stems
    # (by the Regular's numbers the ʒ's spur stood inside the heavier stem,
    # its leaning edge the stem's right edge, 2026-11-09)
    "ɮ": ("attach", "l", lambda up: lezh_band(up)),
}


def lezh_band(font):
    """the Regular's ɮ recipe (derive.RECIPES) on font's l and ʒ: the ʒ
    where its spur leaves the l's stem at its right edge at 600 (as in the
    Regular, 107 units right), the l's foot serif cut right of its stem"""
    import derive
    from derive import BIG

    stem = derive.stems_at(font, "l", 700)[0][1]
    spur = derive.stems_at(font, "uni0292", 600)[0][1]
    dx = round(stem - spur)
    foot = max(p.y for c in font["l"].contours for p in c.points if p.y < 200)
    return ("x", [(stem + 20, -BIG, BIG, foot)],
            [("uni0292", (-BIG, -BIG, BIG, BIG), (0, 0), (1, 1, dx, 0))], dx + font["uni0292"].width)


def fishhook_band(font):
    """the Regular's ɾ recipe (derive.RECIPES) placed on font's r and f:
    f taken from just above its crossbar up, brought down until its top is
    r's, onto r's stem cut there"""
    import derive

    top = lambda n: max(p.y for c in font[n].contours for p in c.points)  # noqa: E731
    dy = top("r") - top("f")
    # above f's crossbar, where its stem still runs straight (920 in the Regular)
    bar = max(p.y for c in font["f"].contours for p in c.points if p.type and p.y <= 1.02 * font.info.xHeight)
    hook = bar + 36
    f0, r0 = derive.stems_at(font, "f", hook - 200)[0][0], derive.stems_at(font, "r", hook + dy - 200)[0][0]
    return ("x", [(-10000, hook + dy, 10000, 10000)],
            [("f", (-10000, hook, 10000, 10000), (0, 0), (1, 1, r0 - f0, dy))])


# the Bold Italic's ff ffi ffl ffj: the second f this much further right
# than the Italic sets it. Both fs have the hook below (2026-11-11); the
# Italic leaves 36 units between the second's ball and the first's tail,
# and at the Bold Italic's weight the two closed on each other (a white
# island between the stems). Chosen by the designer, 2026-11-11, over one
# hook only and over leaving them joined.
ITALIC_BOLD_FF_APART = 100
FF_LIGATURES = ("ff", "ffi", "ffl", "f_f_j")
FF_STRETCH = 0.6  # of the way between the stems the arch is stretched over; the head's join to the second stem moves whole


def part_ff(font, apart=ITALIC_BOLD_FF_APART):
    """font's (the Italic's, before it is emboldened) ff-ligatures with the
    second f and all after it moved apart to the right: above the baseline
    the white between the two stems stretched (lines stay lines, the first
    f's arch a little wider), below it the first f with its hook where it
    is and the second with its hook moved whole. Advance, anchors and
    carets with them."""
    import derive

    for name in FF_LIGATURES:
        g = font[name]
        (_, b1), (a2, _) = derive.stems_at(font, name, 700)[:2]
        # upright by the stem's own slant (the Italic's f leans 15.7 degrees,
        # the font 15.2: over the descender the difference is the white
        # between the hooks)
        slant = (b1 - derive.stems_at(font, name, 200)[0][1]) / 500
        b1, a2 = b1 - slant * 700, a2 - slant * 700
        m = b1 + FF_STRETCH * (a2 - b1)
        low = [p.x - slant * p.y for c in g.contours for p in c.points if p.type and p.y < -20]
        if any(b1 + 1 < x < b1 + 8 for x in low):
            raise ValueError(f"{name}: the two hooks are not apart at the first stem's edge")

        def moved(x, y, b1=b1, m=m, slant=slant):
            u = x - slant * y
            if y < -20:
                return apart if u > b1 + 8 else 0
            return apart * min(1.0, max(0.0, (u - b1) / (m - b1)))

        for c in g.contours:
            for pt in c.points:
                pt.x = round(pt.x + moved(pt.x, pt.y))
        for a in g.anchors:
            a.x = round(a.x + moved(a.x, a.y))
        g.width += apart


# the Bold Italic's curls over the top (ITALIC_BOLD_RECIPES): radii, turn and ball
CURL_CAP = {"r": (205, 185), "sweep": 190, "ball": 105}
CURL_LOW = {"r": (185, 165), "sweep": 190, "ball": 90}
ITALIC_BOLD_RECIPES = {
    # ʉ: the bar on the Bold Italic's u (ITALIC_BOLD_REBUILD) as heavy and
    # long as emboldened, as ɨ's: the Italic's 56 and AY, its overhang
    # less by about half of AX (the stems are wider)
    "ʉ": ("bar", "u", ("x", None, None, 143, 56 + AY)),
    # ǥ.sc: the bar on the Bold Italic's g.sc (ITALIC_BOLD_REBUILD) at the
    # Italic's 60 and AY, as heavy as emboldened (69; at 60 it stood lighter
    # than g.sc's own bar, 64, as Ǥ's does not: 76 against G's 73)
    "ǥ.sc": ("bar", "g.sc", ("s", 190, "last", None, 60 + AY)),
    # Ⱦ ⱦ.sc: the slash hid in the T's arm and stem, only its ends showing
    # ("the bar is not very visible", 2026-11-09): wider (0.15 of the ink's
    # width further out each side) and 60 lower, flatter, so it crosses the
    # white under the arm and beside the stem, a quarter heavier than the
    # Regular's (chosen 2026-11-09 from heavier x1.5, x2); its top at the
    # top line as before (40 higher, its square end stood a peak on it)
    "Ⱦ": ("slash", "T", ("c", "box", 0.10, -140, 0.90, 1434, 96)),
    "ⱦ.sc": ("slash", "t.sc", ("s", "box", 0.10, -120, 0.90, 1040, 83)),
    # ⱦ: emboldened whole its slash kept the Regular's thickness, too light
    # (55): a quarter heavier, as Ⱦ ⱦ.sc's, where the Italic's runs (chosen
    # 2026-11-09 from 69 / 83, each also lower and longer)
    "ⱦ": ("slash", "t", ("x", "box", 0.05, -80, 0.95, 960, 69)),
    # ɉ: the bar on the Bold Italic's j (ITALIC_BOLD_REBUILD), centred as
    # the Italic's, as heavy as emboldened (the Italic's 56 and AY, as ʉ's;
    # at the stroke scale it came to 56); j_bar.py then sets its arms
    "ɉ": ("bar", "j", ("x", None, "all", (92, 92), 56 + AY)),
    # ʄ: keep ɟ's descender and stem at this weight. Its entry stroke and
    # bar ends are cut away; the new bar is centred on the extended stem.
    # At y=600 the upright ɟ stem spans about 335..586. The light recipe's
    # 351..495 extension and 500-unit cut no longer fit that stem.
    # The hook follows the old open counter and rounded terminal, with a
    # continuous inner return. A narrow elliptical curl pinches the counter
    # and leaves a lump where its terminal overlaps. These upright curves
    # join the retained stem gradually and keep the old right edge.
    # 848 minus the inherited 130-unit left adjustment and the 38-unit
    # Bold cut keeps the 680-unit advance.
    "ʄ": ("attach", "uni025F", ("x", [(-10000, 600, 10000, 10000), (-10000, 475, 300, 10000),
                                       (-10000, 410, 330, 474), (590, 410, 10000, 474)],
                                 [("poly", [
                                      (335, 550),
                                      (335, 900),
                                      ((335, 1000), (339.45, 1055), (339.73, 1146)),
                                      ((340.0, 1237), (508.44, 1309), (617.44, 1309)),
                                      ((710.44, 1309), (867.57, 1257), (889.03, 1178)),
                                      ((910.23, 1100), (845.52, 1029), (756.52, 1029)),
                                      ((706.52, 1029), (649.54, 1051), (641.12, 1082)),
                                      ((631.88, 1116), (667.57, 1165), (652.62, 1220)),
                                      ((648.82, 1234), (641.37, 1243), (617.37, 1243)),
                                      ((565.37, 1243), (581.78, 1201), (581.73, 1146)),
                                      ((581.91, 1057), (586, 1000), (586, 900)),
                                      (586, 550),
                                  ], (0, 0), (1, 1, 0, 0)),
                                  ("rect", (201, 414, 721, 470), (0, 0), (1, 1, 0, 0))], 848)),
    # the curls over the top (Ƈ Ɠ ƈ Ƙ Ʋ Ƴ ƴ ʋ ⱳ): the Italic's, at this
    # weight; the Italic's balls (its case's, derive.ball_for) closed the
    # Italic's small curls once their strokes were this heavy (2026-10-27):
    # the curls wider and turned less, the balls as large as leaves their
    # counters open (CURL_CAP, CURL_LOW; the drawn c's is 121, J's 143)
    # ƈ: the Italic's (c's top hairline rising from where its ball was into
    # a hook), its stroke as heavy as the Bold Italic's arch there (55):
    # emboldened whole, the hook stayed a hairline, pinched where it left c
    "ƈ": ("attach", "c", ("x", [(552, 450, 10000, 10000), (490, 450, 565, 818)],
                          [("line", ((532, 855), (580, 1100), 60), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 580, 1100, 60), "dir": 75, "turn": "cw", "r": (150, 135),
                                     "sweep": 200, "ball": 80, "t": (60, 46), "lead": 10}, (0, 0), (1, 1, 0, 0))])),
    # Ƈ Ɠ: the Italic's, the stroke and hook at this weight; the stroke from
    # y0, within the terminal's ink (Ɠ's from 1320 left a notch on the faired
    # G, fair_arcs, 2026-10-28)
    **{ch: ("attach", base, ("c", [(x - 50, 1330, 10000, 10000)],
                             [("line", ((x, y0), (x, 1500), 53), (0, 0), (1, 1, 0, 0)),
                              ("curl", {"at": ("pt", x, 1500, 53), "dir": 90, "turn": "cw", "r": (165, 150),
                                        "sweep": 200, "ball": 85, "t": (53, 45), "lead": 10}, (0, 0), (1, 1, 0, 0))]))
       for ch, base, x, y0 in (("Ƈ", "C", 1090, 1320), ("Ɠ", "G", 1139, 1310))},
    # Ƭ: the Italic's, its strokes at this weight (as rederive scales them)
    # and its ball as large as the curl takes with no notch (80-90 at 180-200
    # degrees; the case's, 96, notched it): the Italic's smaller one (65)
    # scaled up would close the curl
    # The bar run on 220 units left before it curls, as the Italic's
    # (2026-11-06: the left arm short against the right, 196 against
    # 641; at 0.8 too long, now about 0.65): the T's own bar (1352-1434, 82)
    # from the stem, the stub of its top-left serif under it cut away (to
    # 495, where the underside runs level; these numbers are the recipe's
    # frame, the T as rederive meets it, 172 units left of the saved T's):
    # left there, the edge sank along the bar and climbed the stub again, a
    # wobble. Cut to 662 it took the stem's left side, a step
    "Ƭ": ("attach", "T", ("c", [(-10000, 800, 420, 10000), (420, 1150, 495, 1352)],
                          [("line", ((680, 1393), (200, 1393), 82), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 200, 1393, 82), "dir": 180, "turn": "ccw",
                                     "r": (135, 125), "sweep": 190, "ball": 90, "t": (133, 82),
                                     "lead": 10, "cuts": [(200, 1300, 10000, 10000)]}, (0, 0), (1, 1, 0, 0))])),
    # ƈ.sc ɠ.sc: derive's curl on c.sc g.sc, its ring at this weight as Ƈ's
    # (thin, 45 across its top) with a smaller ball (75): at the scaled
    # stroke and the case's ball the hook's inside closed to a straight
    # slant (2026-11-06: "not very round"). It leaves the top
    # stroke further left (720) and flatter (35 degrees), turning further:
    # from 782 at 70 degrees it rose off the stroke with a dip outside and
    # a cusp inside ("badly attached")
    **{ch: ("curl", base, ("s", [(735, 530, 10000, 10000)],
                           {"at": ("x", 720), "dir": 35, "turn": "cw", "r": (165, 140),
                            "sweep": 195, "ball": 75, "t": (100, 45)}))
       for ch, base in (("ƈ.sc", "c.sc"), ("ɠ.sc", "g.sc"))},
    # Ƙ Ƴ: the arm cut below its flare into the serif (its own width there),
    # running on in its own direction; Ʋ: U's right stem
    "Ƙ": ("curl", "K", ("c", [(870, 1130, 10000, 10000)],  # (at 1150 a step, ƙ.sc's ledges)
                        {"at": ("y", 1130, "last"), "dir": 51.6, "turn": "cw", **CURL_CAP, "t": (132, 67)})),
    # Ɓ Ɗ Ƥ: the Italic's recipe (the stem rising through the top serif and
    # curling over to the left), the serif cut from 1290 a unit inside the
    # stem's left edge, 290 here (266 once spaced): the Italic's cut at 300
    # took 11 units off the stem, a step where the curl begins (
    # 2026-11-05, on ɦ)
    **{ch: ("curl", base, ("c", [(-10000, 1290, 291, 10000)],
                           {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                            "sweep": 200, "ball": None, "t": (166, 60)}))
       for ch, base in (("Ɓ", "B"), ("Ɗ", "D"), ("Ƥ", "P"))},
    # Ɦ: as the Bold Italic's Ɓ (the Italic's recipe for Ɓ Ɗ Ƥ): the stem
    # rising to its top at its own weight, the curl leaving it on the left;
    # only the serif cut, left of the stem and right of it: from 1290 (the
    # bracket begins at 1297) a unit inside the stem's edges, 290 and 577 in
    # the frame the recipes are drawn in here (553 once the Bold Italic is
    # spaced; cut at 553, the step left in the stem was cleaned into an
    # edge leaning 5 degrees in). The Italic's Ɦ curls the whole stem over: at
    # the Italic's 164 it stepped 45 units in on both sides of the Bold
    # Italic's 287 stem (ɦ.sc alike), at 287 it closed its eye
    # (2026-11-05)
    # Ꞵ: B's stem running on down at its own weight (the Italic's 166-unit
    # descender stood 120 units lighter than the Bold Italic's 288 stem,
    # 2026-11-08): the stem's edges 294 and 582 in the recipe
    # frame (150-438 upright), cut a unit inside below the foot's bracket;
    # the foot serif as B's own, 67 tall, overhanging the stem 167 a side
    # Bulgarian ж: the Bold Italic ж's stem (715-949 where this runs,
    # before the letters are spaced; the mirrored ж, make_italic.mirror_zhe)
    # run up into l's (144-380: centred on it, 570 right) by a piece
    # widening from the one to the other, l's top above it (the Italic's
    # cut and place left a notch at the stem's right edge;
    # 2026-11-08)
    "ж.loclBGR": ("attach", "uni0436", ("x", [],
                                         [("poly", [(715, 790), (949, 790), (950, 1110), (714, 1110)], (0, 0), (1, 1, 0, 0)),
                                          ("l", (-10000, 1100, 10000, 10000), (0, 0), (1, 1, 570, 0))])),
    # ₮: the bars centred on the Bold Italic T's stem (541-828 here) and
    # standing out 150 a side at their middles, rising as the Regular's
    # (0.48), as heavy as emboldened (104 across)
    "₮": ("lines", "T", ("c", 104, [((380, 354), (990, 646)), ((380, 674), (990, 966))])),
    # ₴: Ƨ (the Bold Italic's S mirrored) with its bars standing out on
    # both sides: the S's outer edges at the bars are 158 and 210 on the
    # left here, the bars stand out about 140-150 on both sides, 75 thick as
    # emboldened; all moved 57 right and the advance set (1467) for side
    # bearings of about 45 by the bar's thin end and the old 54 on the right
    "₴": ("attach", "space", ("c", [], [("S", (-10000, -10000, 10000, 10000), (0, 0), (-1, 1, 1329, 0)),
                                        ("rect", (77, 520, 1317, 595), (0, 0), (1, 1, 0, 0)),
                                        ("rect", (117, 851, 1282, 926), (0, 0), (1, 1, 0, 0))], 1467)),
    "Ꞵ": ("attach", "B", ("c", [(-10000, -10000, 295, 120)],
                          [("rect", (294, -413, 582, 130), (0, 0), (1, 1, 0, 0)),
                           ("rect", (127, -480, 749, -413), (0, 0), (1, 1, 0, 0))])),
    "Ɦ": ("curl", "H", ("c", [(-10000, 1290, 291, 10000), (576, 1290, 880, 10000)],
                        {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                         "sweep": 200, "ball": None, "t": (166, 60)})),
    # ɦ.sc: as Ɦ, drawn on h.sc at the small caps' size (its stem's edges
    # 199 and 494 here, 175 and 470 once spaced; the curl's radii a little larger than
    # Ɦ's scaled, 0.725: Ɦ enlarged, its eye closed to a pinhole, as ƥ.sc's)
    "ɦ.sc": ("curl", "h.sc", ("c", [(-10000, 915, 200, 10000), (493, 915, 684, 10000)],
                              {"at": ("y", 940, "first"), "dir": 90, "turn": "ccw", "r": (165, 125),
                               "sweep": 200, "ball": None, "t": (120, 48)})),
    "Ʋ": ("curl", "U", ("c", [(950, 1200, 10000, 10000)],
                        {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", **CURL_CAP, "t": (139, 59)})),
    "Ƴ": ("curl", "Y", ("c", [(800, 1100, 10000, 10000)],
                        {"at": ("y", 1100, "last"), "dir": 68.5, "turn": "cw", **CURL_CAP, "t": (103, 59)})),
    # ƴ (and ʋ before): the thick right stroke (246, 251) curling over; it ends upright,
    # as thick, so it ends in a round cap touching both its edges ("end";
    # 90 left 60 units of the end's face standing beside it; half the
    # stroke, 124 and 126, stood a few units into the counter in a dent:
    # 2026-10-29)
    "ƴ": ("curl", "y", ("x", [(705, 760, 10000, 10000)],
                        {"at": ("y", 760, "last"), "dir": 90, "turn": "cw", **CURL_LOW, "ball": "end",
                         "t": (246, 62)})),
    # ʋ: a short hook over the stem, ending in a ball hanging from its outer
    # edge, as on r (2026-10-29: curling on, 190 degrees, the
    # ring lay on the left stem's hook and closed the top; narrower, its
    # eye closed to a slit; the stem tapered into it, a dead end)
    "ʋ": ("curl", "u", ("x", [(705, 700, 10000, 10000)],
                        {"at": ("y", 700, "last"), "dir": 90, "turn": "ccw", **CURL_LOW, "sweep": 105,
                         "ball": 95, "t": (251, 62)})),
    # ⱳ: the Italic's, on the Bold Italic's arm, cut below where it flares
    # (1312-1404 at 600) and narrowing to the curl's stroke (a straight
    # stroke at the curl's width stepped 36 units aside of the arm at 645);
    # the ball 95, as the other x-height curl (80 stood thin:
    # 2026-11-08). The finished ⱳ is drawn (its arm evened by hand, kept)
    "ⱳ": ("attach", "w", ("x", [(1000, 600, 10000, 10000)],
                          [("poly", [(1314, 595), (1405, 595), (1378, 770), (1298, 770)], (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 1338, 770, 80), "dir": 92, "turn": "cw", "r": (165, 150),
                                     "sweep": 200, "ball": 95, "t": (80, 53), "lead": 6}, (0, 0), (1, 1, 0, 0))])),
    # Қ Җ җ қ: the Italic's (make_italic.descender), on the Bold Italic's
    # leg (its centre and weight at 200, where it is cut), the exit stroke
    # cut away, the ball half the stroke (as there, so the curl's end has no
    # step): emboldened whole, the curls closed on their strokes
    "Қ": ("attach", "uni041A", ("c", [(900, -10000, 10000, 200), (1270, -10000, 10000, 450)],
                                [("line", ((1057, 210), (1062, -150), 300), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 1062, -150, 300), "dir": 270, "turn": "cw", "r": (195, 170),
                                           "sweep": 170, "ball": 144, "t": (300, 60)}, (0, 0), (1, 1, 0, 0))])),
    "Җ": ("attach", "uni0416", ("c", [(1495, -10000, 10000, 200), (1900, -10000, 10000, 450)],
                                [("line", ((1664, 210), (1669, -150), 318), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 1669, -150, 318), "dir": 270, "turn": "cw", "r": (205, 175),
                                           "sweep": 155, "ball": 134, "t": (318, 60)}, (0, 0), (1, 1, 0, 0))])),
    "җ": ("attach", "uni0436", ("x", [(975, -10000, 10000, 200), (1390, -10000, 10000, 450)],
                                [("line", ((1090, 210), (1102, -150), 215), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 1102, -150, 215), "dir": 272, "turn": "cw", "r": (150, 130),
                                           "sweep": 170, "ball": 103, "t": (215, 55)}, (0, 0), (1, 1, 0, 0))])),
    "қ": ("attach", "uni043A", ("x", [(630, -10000, 10000, 200), (960, -10000, 10000, 450)],
                                [("line", ((765, 210), (771, -150), 255), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 771, -150, 255), "dir": 270, "turn": "cw", "r": (170, 145),
                                           "sweep": 170, "ball": 122, "t": (255, 55)}, (0, 0), (1, 1, 0, 0))])),
    # ң: the Italic's, on the Bold Italic's н (the stem's centre 855 in the
    # upright frame, 241 thick at the cut, its ball between қ's and җ's): by the Italic's numbers the
    # stroke stood 40 units beside the stem, a step on either side
    "ң": ("attach", "uni043D", ("x", [(675, -10000, 10000, 200), (1015, -10000, 10000, 450)],
                                [("line", ((855, 210), (858, -150), 245), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 858, -150, 245), "dir": 270, "turn": "cw", "r": (162, 139),
                                           "sweep": 170, "ball": 114, "t": (245, 55)}, (0, 0), (1, 1, 0, 0))])),
    # ɰ: the Bold Italic's ɯ, its last stem running down into ɥ's descender,
    # narrowed to that stem (216 at the cut, ɥ's 236): emboldened from the
    # Italic's ɰ, it was notched at the knees where ɯ is whole
    "ɰ": ("attach", "uni026F", ("x", [(1205, -10000, 10000, 300), (1445, -10000, 10000, 600)],
                                [("uni0265", (717, -10000, 10000, 300), (0, 0), (0.92, 1, 554, 0))], 1620)),
    # ɳ: the Italic's (make_italic.retroflex), on the Bold Italic's leg (its
    # centre 836, 229 thick at the cut): emboldened whole, the descender took
    # only part of the weight (its stroke under the thick threshold) and the
    # leg pinched at the join; the ball half the stroke, as the Italic's and
    # Ɽ's (80 left a straight step where the curl ran into it)
    "ɳ": ("attach", "n", ("x", [(700, -10000, 10000, 200), (1000, -10000, 10000, 450)],
                          [("line", ((836, 210), (836, -150), 229), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 836, -150, 229), "dir": 270, "turn": "ccw", "r": (150, 130),
                                     "sweep": 170, "ball": 115, "t": (229, 55)}, (0, 0), (1, 1, 0, 0))])),
    # Ɽ Ʈ ɽ.sc ʈ.sc: the Italic's (make_italic.retroflex: the foot serif cut
    # away, the stem run on and curled right), on the Bold Italic's stem
    # (its centre and weight, 290 or 299 thick at the cut), the ball half
    # the stroke (as there, so the curl's end has no step): emboldened
    # whole, the tail stood left of the stem and heavier than it
    # (Ɽ's stem is 298 at its cut: the tail at R's 290 stood 9
    # units in from its right edge, a step at 120, 2026-11-03)
    "Ɽ": ("attach", "R", ("c", [(-10000, -10000, 950, 120)],
                          [("line", ((429, 160), (429, -150), 309), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 429, -150, 309), "dir": 270, "turn": "ccw", "r": (195, 170),
                                     "sweep": 170, "ball": 154, "t": (309, 60)}, (0, 0), (1, 1, 0, 0))])),
    "Ʈ": ("attach", "T", ("c", [(-10000, -10000, 10000, 150)],
                          [("line", ((692, 200), (692, -150), 290), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 692, -150, 290), "dir": 270, "turn": "ccw", "r": (195, 170),
                                     "sweep": 170, "ball": 145, "t": (290, 60)}, (0, 0), (1, 1, 0, 0))])),
    "ɽ.sc": ("attach", "r.sc", ("s", [(-10000, -10000, 700, 120)],
                                [("line", ((332.5, 160), (332.5, -150), 299), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 332.5, -150, 299), "dir": 270, "turn": "ccw",
                                           "r": (180, 155), "sweep": 170, "ball": 150, "t": (299, 55)},
                                  (0, 0), (1, 1, 0, 0))])),
    # ʈ: the Italic's (make_italic: t's tail and foot cut away), on the Bold
    # Italic's stem (121-359 upright, its centre 240): with the Italic's
    # numbers the cut at 300 took a slice off the stem, a step at 350
    "ʈ": ("attach", "t", ("x", [(-10000, -10000, 10000, 300), (380, -10000, 10000, 600)],
                          [("line", ((240, 350), (240, -150), 238), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 240, -150, 238), "dir": 270, "turn": "ccw", "r": (150, 130),
                                     "sweep": 170, "ball": 119, "t": (238, 55)}, (0, 0), (1, 1, 0, 0))])),
    "ʈ.sc": ("attach", "t.sc", ("s", [(-10000, -10000, 10000, 120)],
                                [("line", ((538.5, 160), (538.5, -150), 299), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 538.5, -150, 299), "dir": 270, "turn": "ccw",
                                           "r": (180, 155), "sweep": 170, "ball": 150, "t": (299, 55)},
                                  (0, 0), (1, 1, 0, 0))])),
    # ɧ: the Italic's (ȷ's descender on ɦ's leg where it is still whole: 251
    # at 250, centred at 714.5), the exit stroke cut away beyond 874
    "ɧ": ("attach", "uni0266", ("x", [(480, -10000, 10000, 250), (890, -10000, 10000, 450)],
                                [("uni0237", (-10000, -10000, 10000, 260), (443.5, 250),
                                  (251 / 241, 1, 714.5, 250))])),
    # ɱ: ȷ's descender (its stem 241, centred at 442.5) on m's last leg
    # (229 at the cut, centred at 1317.5), the exit stroke cut away beyond
    # 1479 (the hook recipe takes the emboldened exit stroke for the last
    # stem): emboldened whole, the hook thinned to 0.8 of ȷ's
    "ɱ": ("attach", "m", ("x", [(1150, -10000, 10000, 200), (1490, -10000, 10000, 450)],
                          [("uni0237", (-10000, -10000, 10000, 210), (442.5, 200), (229 / 241, 1, 1317.5, 200))])),
    # ʐ: the Italic's, its stem 225 (0.85 of n) and the turns opened to suit
    "ʐ": ("attach", "z", ("x", [(660, -10000, 10000, 400)],
                          [("curl", {"at": ("pt", 660, 40, 125), "dir": 0, "turn": "cw",
                                     "r": (150, 120), "sweep": 90, "ball": 30, "t": (225, 125)},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((810, -60), (810, -300), 225), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 810, -300, 225), "dir": 270, "turn": "ccw",
                                     "r": (180, 140), "sweep": 150, "ball": 95, "t": (225, 60)},
                            (0, 0), (1, 1, 0, 0))])),
    # ʑ: the Italic's: the bottom stroke run on (its rising end cut away),
    # thinning into a small loop at its end, an upright tail down through
    # the loop's left side
    "ʑ": ("attach", "z", ("x", [(600, -10000, 10000, 400)],
                          [("poly", [(560, -20), (600, -23), ((630, -21), (660, -18), (690, -15)),
                                     (690, 55), ((660, 66), (630, 88), (600, 108)), (560, 108)],
                            (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 680, 20, 70), "dir": 3, "turn": "ccw",
                                     "r": (125, 135), "sweep": 270, "ball": 40, "t": (150, 70), "lead": 10},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((555, 200), (555, -200), 152), (0, 0), (1, 1, 0, 0))])),
    # ɕ: the Italic's, its loop and tail at the Bold Italic's weight, c cut
    # at the tail, the loop alone the bottom (as ʑ)
    "ɕ": ("attach", "c", ("x", [(525, -10000, 10000, 400)],
                          [("curl", {"at": ("pt", 600, 10, 60), "dir": 10, "turn": "ccw",
                                     "r": (150, 150), "sweep": 270, "ball": 55, "t": (160, 60),
                                     "lead": 35},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((445, 180), (445, -200), 160), (0, 0), (1, 1, 0, 0))])),
    # ɞ: the Italic's (ɜ closed by the left half of o), joined at x=440,
    # where o's and ɜ's strokes meet at one height; the half 80 further left
    # than there, so o's stem, twice as heavy, leaves the counters open (its
    # side bearing given back in ITALIC_SIDEBEARINGS)
    "ɞ": ("attach", "ɜ", ("x", [(-10000, 600, 440, 10000), (-10000, -10000, 440, 300)],
                          [("o", (-10000, -10000, 560, 10000), (0, 0), (1, 1, -100, 0))])),
}
ITALIC_BOLD_KEEP_WHOLE = {
    "uni019D": "Ɲ: crumbs of the foot serif at the cut",
    "uni0191": "Ƒ: the tail far lighter than the stem",
    "uni0256": "ɖ: the tail thin where it meets the stem",
    "uni027E": "ɾ: the Italic's fishhook (r's stem under f's hook) emboldened whole, as the Italic built it",
    "uni044E.loclBGR": "Bulgarian ю: a spur of ю's entry stroke left under the cut",
    "uni026E": "ɮ: a notch where l's stem meets ʒ",
    "uni0294": "ʔ: the Italic's cut, placed by number, notches the heavier stroke and leaves a sliver",
    "uni0268": "ɨ: Old Standard's own ɨ (its dot set as i's by i_bar_dot.py); the recipe's i with a bar is another letter",
    "uni026D": "ɭ: a step on the stem at the cut",
    "uni027B": "ɻ: a step on the stem's right side at the cut",
    "uni04B7": "ҷ: a notch at the tail, the stem shifted below the cut",
    "uniA7B2": "Ʝ: steps on both sides of the stem at the cut",
}
# Reviewed weight-aware choices: the rounder emboldening can lighten or
# dent a body, and a local contour repair must not switch its construction.
BOLD_BY_WEIGHT = {
    # kept as chosen before by weight kept a curve's bends (keep_bends,
    # 2026-10-27), which changed the fault counts the choice is made by
    "uni0190": "Ɛ: kept by weight",
}
# letters whose fitted curves keep their bends as they came (keep_bends
# off): there the guard thins a beak to a sliver
BOLD_FIT_AS_IS = {"uni0190": "Ɛ: the beak at its lower arm's end thinned to a sliver"}
# the Bold Italic's bends kept too (2026-10-27): fewer new inflections
ITALIC_BOLD_FIT_AS_IS = {
    "uni2135": "ℵ: aleph.py's repairs are made on the outline as it came",
}
ITALIC_BOLD_BY_WEIGHT = {
    "uni044B": "ы: the rounder way light, its bowl dented where it meets the stem",
    "uni044C": "ь: the rounder way light (0.82 of its kind), its hook a hairline",
    # Keep the established stem construction after rounding r's shoulder:
    # the local return must not switch these to a heavier/dented body.
    "uni024D": "ɍ: keep the weighted r body after its shoulder is rounded",
    "uni027A": "ɺ: keep the weighted turned-r body after its shoulder is rounded",
    "uni027B": "ɻ: keep the weighted turned-r body after its shoulder is rounded",
    "uni027E": "ɾ: keep the weighted r body after its shoulder is rounded",
}
# and the other way: letters emboldened the rounder way though no slit is
# found, their parts a hair too far apart for it
BOLD_ROUNDER = {
    # kept as chosen before the rounder way kept smooth nodes smooth (2026-10-27)
    "uni02C0": "ˀ: kept the rounder way (accepted)",
    "psi": "ψ: by weight the right arm's terminal overshoots its curve, a shoulder under it",
    # kept the rounder way when by weight came to keep its bends (2026-10-27)
    "uni0255": "ɕ: kept the rounder way",
    "uni0266.sc": "ɦ.sc: kept the rounder way",
}
# Bold Italic letters whose hairline leaves its crotch heavier, the
# weight there (0..1, a stem's 1) fading over stroke_bold.ROOT units (k's
# arm a thin wedge where it left the stem; chosen: 0.7 of 0.3, 0.5,
# 0.7, k only, 2026-10-28); &'s bowl tail at its stem, where the crotch,
# moved by the hairline only, drew the stem's foot into a knee (19 units
# aside, 29 without; 1.0 bracketed the diagonal's crotch, 2026-11-02)
ITALIC_BOLD_ROOTS = {"k": 0.7, "ampersand": 0.7}
# Bold Italic letters whose curves running into a crotch are fitted with
# more cubics where one strays from the stroked points (stroke_bold.SPLIT_ERR):
# ξ's bowl, run on to its hairline, drew in a waist above its middle crotch
# (2026-11-03; for every letter it bent ɱ's hook and щ's stems)
ITALIC_BOLD_SPLIT = {"xi"}
# Bold Italic letters whose sides near a crotch are not held back by the
# white in front (stroke_bold.CLEAR), within this many units of it: q.sc's
# bowl, its counter narrowing into the crotch over the tail's loop, bent in
# above it (2026-11-03; for every letter it broke the oldstyle 2 and filled q)
ITALIC_BOLD_CAP_FREE = {"q.sc": 300}
# Bold Italic letters whose smallest counter is refitted smooth over this
# many units after stroking (stroke_bold.smooth_counter), its one corner
# kept: q.sc's loop, the tail's weight changing fast along it, left with a
# flat slanted side and a double kink (2026-11-03)
ITALIC_BOLD_SMOOTH_COUNTER = {"q.sc": 16}
ITALIC_BOLD_ROUNDER = {
    "uni044B.sc": "ы.sc: by weight its bowl closes up on the stem (5 units apart, the rounder way 18)",
    "uni027D": "ɽ: keep its established spacing reference; its final body and hook are rebuilt from r",
    # kept the rounder way when by weight came to keep its bends (2026-10-27):
    # by weight heavier and wider (§ +21, 1 +63)
    "section": "§: kept the rounder way",
    "oneoldstyle": "oldstyle 1: kept the rounder way",
    "uni02B0": "ʰ: kept the rounder way",
    "uni20B5": "₵: kept the rounder way",
}
# The reviewed body choices above must retain their previous rounder
# optical-spacing reference; body weighting and spacing are independent.
ITALIC_REFERENCE_ROUNDER = {"uni024D", "uni027A", "uni027B", "uni027E"}
# and rounder bodies spaced on the reference by weight they had before
BOLD_REFERENCE_BY_WEIGHT = {"psi"}
# and bodies kept by weight spaced on the rounder reference they had
BOLD_REFERENCE_ROUNDER = {"uni0190"}

# recipes that scale or reshape their one source outline, adding no piece:
# no junction to thicken, emboldened whole as any letter is
RESHAPES = {"enlarge", "stretch", "superior", "lower", "ezh", "esh", "nodot", "upright"}
# the Bold's letters are spaced tighter than the Regular's (the Regular's
# sidebearings times KX), as a bold's are: 40 off each side in all of the
# Regular's 20 (times KX) and BOLD_CUT, Greek lowercase 25 of 10 and BOLD_CUT_GREEK
BOLD_CUT, BOLD_CUT_GREEK = 19, 15
# the Bold Italic's Greek lowercase tighter still: emboldened from the
# Italic's (Old Standard's) it stood 0.10 of an n n gap looser than its Latin
# against Greek references (scripts/quality/greek_pairs.py)
BOLD_ITALIC_CUT_GREEK = BOLD_CUT_GREEK + 16
# the Bold Italic's letters by strokes a little looser than the Bold's
# ("a bit narrow", 2026-10-28): ITALIC_LOOSER units less cut a
# side, its Greek lowercase alike (the Greek pairs are judged against n n);
# tighter than the Bold's since 2026-11-01: lowercase +8.6 % of the Italic,
# as the Bold of the Regular (the name stays: a negative looseness)
ITALIC_LOOSER = -5
BOLD_ITALIC_CUT = BOLD_CUT - ITALIC_LOOSER
# the figures, which respace.py leaves alone, are tighter too: emboldened
# they stand looser than the Bold's letters (1.08 of their side space, where
# bold text faces have 0.8-1.0); one cut for all keeps them tabular, and the
# figure space and dash keep their width
BOLD_FIGURE_CUT = 28
FIGURE_NAMES = {f"{n}{s}" for n in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
                for s in ("", "oldstyle")} | {"uni2007", "figuredash"}
LINING_FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


def tabular_figures(font):
    """The lining figures tabular again: emboldening widens each by its own
    strokes (Bold 1202-1231, Bold Italic 1199-1240 after the cut, where the
    Regular's and the Italic's share one width), so columns of figures no
    longer lined up. Each takes the mean of their widths, the difference
    split evenly between its sides (its fit as emboldened, moved as a whole);
    the figure space and figure dash take the same width. Returns it."""
    width = round(sum(font[n].width for n in LINING_FIGURES) / len(LINING_FIGURES))
    deltas = {}
    for n in LINING_FIGURES + ("uni2007", "figuredash"):
        d = width - font[n].width
        deltas[n] = (d // 2, d - d // 2)
    sidebearings(font, deltas)
    return width
# t's right side tighter in the Bold: emboldened, it stood looser before
# straight letters than in bold text faces; г and є tight on the right, т on
# the left (measured, scripts/quality/pairs.py and colour.py); ж, emboldened
# into its neighbours, tight on both sides (greek_pairs.py --script cyrillic)
BOLD_SIDEBEARINGS = {"t": (0, -40), "uni0433": (0, 34), "uni0454": (0, 30), "uni0442": (26, 0),  # t; г є т
                     "uni0436": (40, 40), "uni0436.loclBGR": (40, 40), "uni0497": (40, 40),  # ж, Bulgarian ж, җ
                     # Greek sides that stood tight against the Greek references in
                     # most of their pairs, as the Bold's Latin sets them (greek_pairs.py)
                     "sigma": (0, 40), "tau": (0, 35), "eta": (0, 45), "kappa": (50, 0),
                     # derived letters still set otherwise against their base than the
                     # references (scripts/quality/derived_spacing.py Bold, to the
                     # median; ƴ just inside the tight end, as the Regular's): Ɗ ɽ Ⱳ Ƥ ʋ ɲ ү ƴ
                     # (ɞ and ʈ too, but their width then strays from the Regular's: to review)
                     "uni018A": (-80, 0), "uni027D": (-65, 0),
                     "uni2C72": (0, -85), "uni01A4": (-80, 0), "uni028B": (0, -45), "uni0272": (-50, 0),
                     "uni04AF": (-45, 0), "uni01B4": (0, 50),
                     # N and n.sc: their hairline uprights, emboldened by AY, not
                     # AX, left them tight against H (H N 0.86 of H H, N H 0.83;
                     # h.sc n.sc 0.81, n.sc h.sc 0.79): brought back to the
                     # Regular's ratios (0.95 0.94; 0.95 0.93; sc_sides.py, 2026-11-08)
                     "N": (37, 45), "n.sc": (39, 40)}
# Pair-level corrections measured after the Bold's global kerning scale.
BOLD_KERNING = {
    # ƴ: its hook sets its right side; the diagonal under it stood far
    # from a, o, e (kerned until the hook comes near a's terminal)
    ("uni01B4", "public.kern2.a"): -60,
    ("uni01B4", "public.kern2.agrave"): -60,
    ("uni01B4", "public.kern2.c"): -60,
    ("uni01B4", "public.kern2.egrave"): -60,
    ("public.kern1.X.sc", "k.sc"): -30,  # wide beside the pairs around it (BOXKÄMPFER, 2026-11-01)
    # Greek: σ's right side stood tight against the Greek references, as
    # the Bold's Latin sets them (scripts/quality/greek_pairs.py); what is
    # left of it after its sidebearing (BOLD_SIDEBEARINGS, 40)
    ("public.kern1.sigma", "public.kern2.etatonos"): 41,  # ση
    ("public.kern1.sigma", "public.kern2.tau"): 37,  # στ
    ("public.kern1.sigma", "public.kern2.omicron"): 22,  # σο
    ("public.kern1.sigma", "public.kern2.iota"): 15,  # σι
    ("public.kern1.tau", "public.kern2.omega"): 14,  # τω (τ's sidebearing 35)
    ("public.kern1.epsilon", "public.kern2.chi"): 49,  # εχ
    ("public.kern1.epsilon", "public.kern2.lambda"): -53,  # ελ
    # Cyrillic against Cyrillic references, as the Bold's Latin sets them
    # (greek_pairs.py --script cyrillic)
    ("public.kern1.uni0433", "public.kern2.uni0434"): -150,  # гд (the Regular's -40, scaled)
    ("public.kern1.uni0443", "public.kern2.uni0447"): 52,  # уч
    ("public.kern1.uni044A", "public.kern2.uni0447"): -26,  # ъч (-75)
    # after emboldening by weight: ње tight (њ shares ъ's right side), уд loose
    ("public.kern1.uni044A", "public.kern2.uni0435"): 40,  # ње
    ("public.kern1.uni0443", "public.kern2.uni0434"): -210,  # уд (the -160 it had, 50 tighter)
    ("n", "t"): -28,
    ("a", "t"): -45,
    ("a", "s"): -29,
    ("a", "u"): -24,
    ("k", "t"): -113,  # -44, then still loose against the Bold references (pairs.py)
    ("z", "t"): -25,
    ("f", "s"): -41,
    ("S", "m"): -28,
    ("t", "r"): -40,
    ("a", "g"): -56,
    ("x", "t"): -77,
}
# the Bold Italic's capital rounds and bowls: STROKE_OUT gave them back
# part of the white the strokes took (O O 0.75 of H H to 0.80), the
# Italic's 0.89 and the references' 0.87-0.95 not reached; each side
# brought to the Italic's ratio against H (scripts/quality/sc_sides.py
# Italic|BoldItalic --caps: the difference times H H's 456 units). R's
# right side (9) left; C's open right and G's spur side as measured.
# Added to the strokes' own and passed on to what is made of them (Ö Ç С)
ITALIC_CAPITAL_ROUNDS = {"O": (41, 41), "Q": (41, 41), "C": (41, 23), "G": (41, 32),
                         "D": (0, 41), "B": (0, 36), "P": (0, 46), "S": (36, 32)}
# the Bold Italic's own (from the Italic)
ITALIC_SIDEBEARINGS = {"uni025E": (100, 0),  # ɞ: its bowl widened leftward (ITALIC_BOLD_RECIPES)
                       # Ж/ж contour finishing moves the optical fit's rounded
                       # Bulgarian ж origin one unit left; retain its reviewed
                       # ink/anchor position and advance.
                       "uni0436.loclBGR": (1, 0),
                       # derived letters still set otherwise against their base than the
                       # references (derived_spacing.py BoldItalic, to the median; Ƴ Ƈ again for their own curls, 2026-10-27): ɖ Ƴ ƈ ɚ ҳ Қ Ƙ Җ ƥ җ Ҷ
                       "uni0256": (0, -140), "uni01B3": (0, 56), "uni0188": (0, -85), "uni0187": (0, 85), "uni025A": (0, -100),
                       "uni04B3": (0, -65), "uni049A": (0, -60), "uni0198": (0, -70), "uni0496": (0, -55),
                       "uni01A5": (-60, 0), "uni0497": (0, -50), "uni04B6": (0, -45),
                       # ɦ.sc (its own curl on h.sc): the least white before its hook as
                       # h.sc h.sc's (119); on h.sc's advance the hook came within 8
                       "uni0266.sc": (149, 0)}  # (with the Italic's -38, taken in as it is rebuilt)
# Joining the light belts changes the temporary weighted shape's optical
# fit. Keep their established advances/anchors before rebuilding the belts
# on this style's final base letters.
ITALIC_FIT_CORRECTIONS = {"uni026C": (-3, 0), "uniA7AD": (-2, 0)}
# by strokes, a letter's side whose ink stands further out than by weight
# gets that white back (letters only: figures, punctuation, signs as fitted) (MYIA_STROKE_OUT=0 to compare; MYIA_STROKE_OUT_LOG=FILE lists them)
STROKE_OUT = os.environ.get("MYIA_STROKE_OUT", "1") != "0"
STROKE_OUT_LOG = os.environ.get("MYIA_STROKE_OUT_LOG")
# gains under this are the measure's noise (1-3 units, most at straight sides:
# H's, m's; the finished letters' side bearings are held within a unit)
STROKE_OUT_MIN = 4
# the horn on u right, so that its outer edge runs on from the stem's as in
# the Italic (the stem top 840-981, the horn there 883-984): the heavier
# stem's top reached 1089, the horn's edge 1044, a shelf beside it
# ė ż: the Italic's dot 90 further left (make_italic ANCHOR_NUDGE); the
# Bold Italic's stays where it was ("ok as is", 2026-11-09): 90 * KX back
ITALIC_ANCHOR_NUDGE = {("u", "Horn"): 45, ("e", "Dotaccent"): 93, ("z", "Dotaccent"): 94,
                       # and the letters made of e and z, which took the
                       # Italic's anchor with them (ɘ turned: the other way)
                       ("uni0258", "Dotaccent"): -94, ("uni0291", "Dotaccent"): 94,
                       ("uni0435", "Dotaccent"): 93, ("uni1D76", "Dotaccent"): 94}
# Bold Italic optical-pair corrections from the pinned-reference spacing
# comparison (scripts/quality/pairs.py). Values are final Bold Italic kern
# values in font units; they are applied after the source kerning is scaled.
# Most pairs had no source pair adjustment. va overrides its inherited class
# pair; fr is made 33 units looser relative to the references' range.
ITALIC_BOLD_KERNING = {
    # ſ ſſ before the round letters tighter than the Regular's -60
    # (from a proof at 0 to -80, 2026-11-05: ſc too wide); the
    # accented ones kept clear by kern_clear.GUARDED_AGAINST
    **{(left, right): -80 for left in ("longs", "longs_longs")
       for right in ("public.kern2.c", "public.kern2.egrave", "public.kern2.g", "q")},
    # Greek against Greek references, as the Bold Italic's Latin sets them
    # (scripts/quality/greek_pairs.py)
    ("public.kern1.delta", "public.kern2.iota"): 78,  # δι
    ("public.kern1.omicron", "public.kern2.upsilon"): 69,  # ου
    ("public.kern1.tau", "public.kern2.iota"): -70,  # τι
    ("public.kern1.nu", "public.kern2.delta"): -76,  # νθ
    ("public.kern1.upsilon", "public.kern2.sigma1"): -80,  # υς
    ("public.kern1.tau", "public.kern2.epsilontonos"): -90,  # τε
    ("public.kern1.mugreek", "public.kern2.pi"): -100,  # μπ
    # where Charis and Libertinus agree against the Bold Italic (tests/test_greek_pairs.py)
    ("public.kern1.mugreek", "public.kern2.alphatonos"): 50,  # μα
    ("public.kern1.lambda", "public.kern2.alphatonos"): 31,  # λα
    ("public.kern1.alpha", "delta"): 63,  # αδ (0 before strokes)
    ("public.kern1.alpha", "theta"): 10,  # αθ, the θ closed (δ ϐ in its class stay)
    # after emboldening by weight σ's thin arm is spaced in: σα σω σφ tight
    ("public.kern1.sigma", "public.kern2.alphatonos"): 58,  # σα
    ("public.kern1.sigma", "public.kern2.omega"): 66,  # σω
    ("public.kern1.sigma", "phi"): 60,  # σφ (σο, in the same group, is in range)
    # tight against the references after the spacing of 2026-10-20
    ("public.kern1.delta", "public.kern2.etatonos"): 62,  # δη
    ("public.kern1.rho", "public.kern2.etatonos"): 60,  # ρη
    ("public.kern1.rho", "public.kern2.upsilon"): 56,  # ρυ
    ("public.kern1.eta", "public.kern2.mugreek"): 66,  # ημ
    # tight against the references after emboldening by strokes (2026-10-28):
    # the rounds' ink sits otherwise in the same advances
    ("public.kern1.omega", "public.kern2.rho"): 81,  # ωρ
    ("public.kern1.omega", "public.kern2.mugreek"): 50,  # ωμ
    ("public.kern1.rho", "public.kern2.omega"): 50,  # ρω
    ("public.kern1.gamma", "public.kern2.alphatonos"): 53,  # γα
    # wide after G2 refit λ's legs (2026-10-28; Charis and Libertinus agree)
    ("public.kern1.lambda", "public.kern2.lambda"): -72,  # λλ
    # Cyrillic against Cyrillic references, as the Bold Italic's Latin sets
    # them (greek_pairs.py --script cyrillic): а a little wide before the
    # letters with a stem (аг ак ан ап ар ащ) and з э
    ("public.kern1.uni0430", "public.kern2.uni0433"): -56,  # ан
    ("public.kern1.uni0430", "public.kern2.uni0437"): -60,  # аз
    ("uni043A", "public.kern2.uni043B"): -76,  # кл
    ("uni0427", "public.kern2.uni043B"): -110,  # Чл
    ("public.kern1.uni0413", "public.kern2.uni0434"): -100,  # Гд (the Italic's -196, scaled)
    # loose after emboldening by strokes (2026-10-28): the entries and exits
    # shorter in the same advances
    ("uni0448", "public.kern2.uni0442"): -69,  # шт
    ("uni0456", "public.kern2.uni0433"): -68,  # ін
    ("public.kern1.uni0413", "public.kern2.uni0431"): 68,  # Гб (-46)
    ("public.kern1.uni0422", "public.kern2.uni0431"): 34,  # Тб (-42)
    ("public.kern1.uni0430", "public.kern2.uni043B"): -55,  # ал (loose after emboldening by weight)
    ("u", "t"): 41,
    ("w", "a"): 57,
    ("g", "h"): 43,
    ("f", "r"): -95,
    ("g", "a"): 89,
    ("i", "f"): 75,
    ("G", "r"): 121,
    ("a", "f"): 66,
    ("a", "y"): 67,
    ("v", "a"): 50,
    ("u", "f"): 92,
    ("R", "e"): 39,
    ("f", "t"): -66,
    # small caps close against their neighbours in a word (ZWÖLF
    # BOXKÄMPFER, 2026-11-01): the white of B O 232 and E R 291 against the
    # 350-375 around them; the Bold's 282 and 317
    ("public.kern1.B.sc", "public.kern2.O.sc"): 40,
    ("e.sc", "r.sc"): 20,
    # a little wide at the tighter spacing of 2026-11-01 (ин лн, 0.16 past the
    # references, greek_pairs.py --script cyrillic)
    ("uni0438", "public.kern2.uni0433"): -20,
    ("uni043B", "public.kern2.uni0433"): -20,
    ("public.kern1.X.sc", "k.sc"): -30,
}
# the horn on u a little left: where the Regular's sits, the Bold's heavier
# foot leaves a ledge beside the stem (glyph_lint)
ANCHOR_NUDGE = {("u", "Horn"): -10}
# closed rounds, outer oval and counter: emboldened by the weight of the
# stroke at each node, the counter's shoulders come out boxy on one diagonal
# and flat on the other (the Bold Italic o, an egg); refitted from the
# lighter style's own curves (oval); in the Bold only: the Bold Italic's
# are drawn with the Italic's curves (stroke_bold), and refitted to its
# area the counter's handles overshoot into cusps; its counters instead
# take the Italic's whole (ITALIC_OVALS, italic_counter)
OVALS = {"o", "O", "zero"}
# the Bold Italic's closed rounds: the stroked counter ran nearly straight
# with tight turns (o, top right and bottom left), o.sc's a rounded
# rectangle (2026-11-05: "very unround"); the Italic's counter
# put in its place (italic_counter); their slashed forms through their ring.
# g's bowl too: stroked it came to a point at the bottom left, where the
# Italic's is round (2026-11-06: c g C G unround inside); the
# open rounds' insides from the Italic's run (italic_inside)
ITALIC_OVALS = OVALS | {"o.sc", "g"}
# slashed rounds, drawn whole in the lighter style: emboldened whole, the
# ring swelled where the slash crosses it (Ø not O with a stroke through);
# the ring is the round's own, the slash emboldened apart (slashed)
SLASHED = {"Oslash": "O", "oslash": "o", "oslash.sc": "o.sc"}


def slashed(wide, ring, make, refit, bar):
    """wide (a slashed round) as its round emboldened as the round itself is
    (make, then refit: oval, italic_counter or None) joined to its slash (what it has beyond ring, the
    round's own wide outline: slivers where the two rings differ left out)
    emboldened apart (bar: by weight; by strokes its hairline edge runs on
    along the counter and the union leaves crumbs of curve there)."""
    def path(rec):
        p = pathops.Path()
        (rec.replay if hasattr(rec, "replay") else rec.draw)(p.getPen())
        return p

    def contours(rec):
        out = []
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    rest = RecordingPen()
    pathops.op(path(wide), path(ring), pathops.PathOp.DIFFERENCE).draw(rest)
    # the slash whole, as one straight bar (the hull of its pieces' straight
    # edges): cut at the ring, its ends would be thin wedges along it,
    # emboldened into fins; where the two rings differ the pieces carry
    # slivers of ring along
    pts = set()
    for c in contours(rest):
        start = cur = c[0][1][0]
        for op, ps in c[1:]:
            end = ps[-1] if ps else start
            if op in ("lineTo", "closePath") and math.dist(cur, end) > 50:
                pts |= {cur, end}
            cur = end
    pts = sorted(pts)

    def half(seq):
        h = []
        for p in seq:
            while len(h) > 1 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                  - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]

    hull = half(pts) + half(pts[::-1])
    slash = RecordingPen()
    slash.moveTo(hull[0])
    for p in hull[1:]:
        slash.lineTo(p)
    slash.closePath()
    whole = make(ring)
    if refit:
        whole = refit(ring, whole)
    before, rec = RecordingPen(), RecordingPen()
    (whole.replay if hasattr(whole, "replay") else whole.draw)(before)
    pathops.op(path(whole), path(bar(slash)), pathops.PathOp.UNION).draw(rec)
    # wound as the round is (pathops winds its own way)
    glyph = ufoLib2.objects.Glyph()
    pen = glyph.getPen()
    if (max(map(area, contours(rec)), key=abs) > 0) != (max(map(area, contours(before)), key=abs) > 0):
        pen = ReverseContourPen(pen)
    rec.replay(pen)
    return glyph


def italic_counter(wide, bold):
    """bold (a two-contour round, the Bold Italic's, upright frame) with its
    counter replaced by wide's (the Italic's) mapped onto the stroked
    counter's box, then scaled about its middle to that counter's area: an
    affine image keeps the Italic's curves as smooth as they are (the
    oval's handle tension, matching the area, drove them into cusps here),
    the ink and its weight stay as stroked."""
    def contours(path):
        rec, out = RecordingPen(), []
        (path.replay if hasattr(path, "replay") else path.draw)(rec)
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    def bounds(c):
        pen = BoundsPen(None)
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.bounds

    def moved(c, t):
        a, d, e, f = t
        return [(op, tuple((a * x + e, d * y + f) for x, y in pts)) for op, pts in c]

    old, new = contours(wide), contours(bold)
    if len(old) != 2 or len(new) != 2:
        raise ValueError("italic_counter: two contours each")
    old.sort(key=lambda c: abs(area(c)))
    new.sort(key=lambda c: abs(area(c)))
    (x0, y0, x1, y1), (u0, v0, u1, v1) = bounds(old[0]), bounds(new[0])
    sx, sy = (u1 - u0) / (x1 - x0), (v1 - v0) / (y1 - y0)
    c = moved(old[0], (sx, sy, u0 - x0 * sx, v0 - y0 * sy))
    k = math.sqrt(abs(area(new[0])) / abs(area(c)))
    cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
    c = moved(c, (k, k, cx * (1 - k), cy * (1 - k)))
    out = RecordingPen()
    for op, pts in new[1]:
        getattr(out, op)(*pts)
    pen = out if (area(c) > 0) == (area(new[0]) > 0) else ReverseContourPen(out)
    for op, pts in c:
        getattr(pen, op)(*pts)
    return out


def inside_from(wide, bold, name):
    """bold (an open round, upright frame) with the run facing its bowl
    redrawn from wide's (italic_inside); as it was where they do not match"""
    w, b = ufoLib2.objects.Glyph(), ufoLib2.objects.Glyph()
    for path, glyph in ((wide, w), (bold, b)):
        (path.replay if hasattr(path, "replay") else path.draw)(glyph.getPen())
    try:
        italic_inside.replace(w, b, *italic_inside.RUNS[name])
    except ValueError as e:
        print(f"  {name}: inside kept as stroked ({e})")
        return bold
    out = RecordingPen()
    b.draw(out)
    return out


def oval(wide, bold):
    """bold (a two-contour round) redrawn with wide's curves: each contour of
    the lighter round fitted to the box of the emboldened one, then its
    handles lengthened or shortened alike (smooth nodes stay smooth) until
    it holds the same area, so the ink and its weight stay as emboldened."""
    def contours(path):
        rec, out = RecordingPen(), []
        (path.replay if hasattr(path, "replay") else path.draw)(rec)
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    def bounds(c):
        pen = BoundsPen(None)
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.bounds

    def tension(c, k):
        """each curve's handles k times as long, from the nodes they leave"""
        out, cur = [], None
        for op, pts in c:
            if op == "curveTo":
                (h1, h2, p) = pts
                h1 = (cur[0] + k * (h1[0] - cur[0]), cur[1] + k * (h1[1] - cur[1]))
                h2 = (p[0] + k * (h2[0] - p[0]), p[1] + k * (h2[1] - p[1]))
                pts = (h1, h2, p)
            out.append((op, pts))
            if pts:
                cur = pts[-1]
        return out

    def fit(c, box):
        (x0, y0, x1, y1), (u0, v0, u1, v1) = bounds(c), box
        sx, sy = (u1 - u0) / (x1 - x0), (v1 - v0) / (y1 - y0)
        return [(op, tuple((u0 + (x - x0) * sx, v0 + (y - y0) * sy) for x, y in pts)) for op, pts in c]

    old, new = contours(wide), contours(bold)
    if len(old) != 2 or len(new) != 2 or any(op not in ("moveTo", "curveTo", "lineTo", "closePath")
                                             for c in old for op, _ in c):
        raise ValueError("oval: two contours each, drawn")
    old.sort(key=lambda c: abs(area(c)))
    new.sort(key=lambda c: abs(area(c)))
    out = RecordingPen()
    for src, dst in zip(old, new):
        box, target = bounds(dst), abs(area(dst))
        c = fit(src, box)
        for _ in range(4):  # the handles move the box a little: fitted again
            lo, hi = 0.5, 1.5
            for _ in range(40):
                k = (lo + hi) / 2
                if abs(area(tension(c, k))) < target:
                    lo = k
                else:
                    hi = k
            c = fit(tension(c, (lo + hi) / 2), box)
        for op, pts in c:
            getattr(out, op)(*pts)
    return out


def bridge(glyph, maxgap=24, overlap=8):
    """glyph with the narrow gaps between straight edges that face each other
    (serif ends that emboldening brought within maxgap: x's inner feet, the
    top of ч) filled, so the parts join instead of leaving a slit."""
    import math

    from derive import draw_path

    path = pathops.Path()
    for c in glyph.contours:
        c.draw(path.getPen())
    path = pathops.simplify(path)
    edges = []
    for c in glyph.contours:
        ons = [p for p in c.points if p.type]
        for p0, p1 in zip(ons, ons[1:] + ons[:1], strict=True):
            if p1.type == "line" and math.dist((p0.x, p0.y), (p1.x, p1.y)) >= overlap:
                edges.append(((p0.x, p0.y), (p1.x, p1.y)))
    fills = []
    for i, (a0, a1) in enumerate(edges):
        ax, ay = a1[0] - a0[0], a1[1] - a0[1]
        la = math.hypot(ax, ay)
        ux, uy = ax / la, ay / la
        for b0, b1 in edges[i + 1:]:
            bx, by = b1[0] - b0[0], b1[1] - b0[1]
            lb = math.hypot(bx, by)
            if (ux * bx + uy * by) / lb > -0.985:  # facing edges run opposite ways, parallel
                continue
            # B's distance from A's line, and their overlap along it
            gap = (b0[0] - a0[0]) * -uy + (b0[1] - a0[1]) * ux
            if not 0 < abs(gap) < maxgap:
                continue
            t = sorted(((b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy, (b1[0] - a0[0]) * ux + (b1[1] - a0[1]) * uy))
            lo, hi = max(0, t[0]), min(la, t[1])
            if hi - lo < overlap:
                continue
            nx, ny = -uy * gap, ux * gap
            mid = (a0[0] + ux * (lo + hi) / 2 + nx / 2, a0[1] + uy * (lo + hi) / 2 + ny / 2)
            probe = pathops.Path()
            pen = probe.getPen()
            pen.moveTo((mid[0] - 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] + 0.5))
            pen.lineTo((mid[0] - 0.5, mid[1] + 0.5))
            pen.closePath()
            if pathops.op(path, probe, pathops.PathOp.INTERSECTION).bounds != (0, 0, 0, 0):
                continue  # ink between them: not a gap
            q = [(a0[0] + ux * lo, a0[1] + uy * lo), (a0[0] + ux * hi, a0[1] + uy * hi)]
            fill = pathops.Path()
            pen = fill.getPen()
            pen.moveTo(q[0])
            pen.lineTo(q[1])
            pen.lineTo((q[1][0] + nx, q[1][1] + ny))
            pen.lineTo((q[0][0] + nx, q[0][1] + ny))
            pen.closePath()
            fills.append(fill)
    if not fills:
        return glyph
    for f in fills:
        path = pathops.op(path, f, pathops.PathOp.UNION)
    out = ufoLib2.objects.Glyph()
    draw_path(None, glyph, out, path)
    return out


PART_GAP = 300  # serifs nearer than this (units) may meet when emboldened
PART_KEEP = 0.5  # of the source's gap that stays open where they would only touch
PART_STEP = 8
GAP_SHARE = 0.9  # of the share the source's gap has of the white between the strokes (keep_gaps)
GAP_AT = 221  # units into the letter from the serifs' edge where that white is measured: a quarter of the x-height
GAP_MIN_WHITE = 120  # a white narrower than this between the strokes is no counter
GAP_STEP = 4


def _ink(p, box):
    r = pathops.Path()
    pen = r.getPen()
    x0, y0, x1, y1 = box
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    out = pathops.op(p, r, pathops.PathOp.INTERSECTION)
    return abs(out.area) if out.contours else 0


def _simple_path(g):
    p = pathops.Path()
    for c in g.contours:
        c.draw(p.getPen())
    return pathops.simplify(p)


def _shortened(wide, pairs, s):
    """wide with both tips of each pair moved s apart: each point with its
    handles, so a smooth join stays smooth"""
    moved = ufoLib2.objects.Glyph()
    wide.replay(moved.getPen())
    for ta, tb, *_ in pairs:
        for tips, dx in ((ta, -s), (tb, s)):
            for ci, i in tips:
                pts = moved.contours[ci].points
                near = {i}
                for step in (-1, 1):
                    j = (i + step) % len(pts)
                    if pts[j].type is None:
                        near.add(j)
                for j in near:
                    pts[j].x += dx
    rec = RecordingPen()
    moved.draw(rec)
    return rec


def serif_pairs(src):
    """The serif tips that face each other across less than PART_GAP in src:
    [(tips a, tips b, mid x, gap, band, shortest edge, ink above)]; band is
    the serifs' height at the gap, ink above says on which side of the flat
    edge the letter lies."""
    path = pathops.Path()
    for c in src.contours:
        c.draw(path.getPen())
    ink = _ink
    # flat edges: (contour, start index, end index, y, xmin, xmax, ink above)
    edges = []
    for ci, c in enumerate(src.contours):
        pts = c.points
        n = len(pts)
        for i in range(n):
            p0, p1 = pts[i], pts[(i + 1) % n]
            if p0.type and p1.type == "line" and p0.y == p1.y and abs(p1.x - p0.x) >= 30:
                mx = (p0.x + p1.x) / 2
                above = ink(path, (mx - 1, p0.y, mx + 1, p0.y + 4)) > 4
                edges.append((ci, i, (i + 1) % n, p0.y, min(p0.x, p1.x), max(p0.x, p1.x), above))

    def tip(ci, i, step):
        """The tip's two points: the edge's end i and the corner beside it on
        the serif's other face (the next point away from the edge)."""
        pts = src.contours[ci].points
        j = (i + step) % len(pts)
        q = pts[j]
        if q.type == "line" and 10 <= abs(q.y - pts[i].y) <= 150:
            return [(ci, i), (ci, j)], abs(q.y - pts[i].y)
        return [(ci, i)], None

    pairs = []
    for a in edges:
        for b in edges:
            if a[3] != b[3] or a[6] != b[6] or not 0 < b[4] - a[5] < PART_GAP:
                continue
            # a's right end faces b's left end
            ia = a[1] if src.contours[a[0]].points[a[1]].x == a[5] else a[2]
            ib = b[1] if src.contours[b[0]].points[b[1]].x == b[4] else b[2]
            sa = 1 if ia == a[2] else -1  # away from a's edge
            sb = 1 if ib == b[2] else -1
            ta, ha = tip(a[0], ia, sa)
            tb, hb = tip(b[0], ib, sb)
            t = min(h for h in (ha, hb) if h) if (ha or hb) else 40
            gap = b[4] - a[5]
            band = (a[3], a[3] + t) if a[6] else (a[3] - t, a[3])
            pairs.append((ta, tb, (a[5] + b[4]) / 2, gap, band, min(a[5] - a[4], b[5] - b[4]), a[6]))
    return pairs


def part_serifs(wide, bold, make):
    """bold (wide emboldened by make) with neighbouring serifs kept apart
    where emboldening brings their tips together only partly: the italics'
    v.sc w.sc y.sc tops and ʌ.sc's feet, 125 units apart in the Italic,
    meet in a notch over a joint a few units thick.  Serifs joined over their
    whole height (x.sc's inner feet, by bridge; ш.sc's base) and serifs that
    stay apart are left alone.  Both tips of such a pair are shortened in the
    source by the same amount, in steps, until PART_KEEP of the source's gap
    stays open.  Returns (glyph, number of pairs parted)."""
    src = ufoLib2.objects.Glyph()
    wide.replay(src.getPen())
    pairs = serif_pairs(src)
    ink, bold_path = _ink, _simple_path

    def partly(p, mid, band):
        h = ink(p, (mid - 1, band[0], mid + 1, band[1])) / 2
        return 0.05 < h / (band[1] - band[0]) < 0.95

    bp = bold_path(bold)
    bad = [pr for pr in pairs if partly(bp, pr[2], pr[4])]
    if not bad:
        return bold, 0
    for s in range(PART_STEP, int(min(pr[5] for pr in bad)) - 20, PART_STEP):
        out = make(_shortened(wide, bad, s))
        op = bold_path(out)
        if all(ink(op, (mid - gap * PART_KEEP / 2, band[0], mid + gap * PART_KEEP / 2, band[1])) == 0
               for _, _, mid, gap, band, _, _ in bad):
            return out, len(bad)
    return bold, 0


def _white(path, x, y):
    """The white run across through (x, y): its width; 0 where there is ink,
    or no ink on one of the sides."""
    reach = 900
    strip = pathops.Path()
    pen = strip.getPen()
    pen.moveTo((x - reach, y - 1))
    pen.lineTo((x + reach, y - 1))
    pen.lineTo((x + reach, y + 1))
    pen.lineTo((x - reach, y + 1))
    pen.closePath()
    left = right = None
    for c in pathops.op(path, strip, pathops.PathOp.INTERSECTION).contours:
        x0, _, x1, _ = c.bounds
        if x0 <= x <= x1:
            return 0
        if x1 < x and (left is None or x1 > left):
            left = x1
        if x0 > x and (right is None or x0 < right):
            right = x0
    return right - left if left is not None and right is not None else 0


def keep_gaps(wide, bold, make):
    """bold (wide emboldened by make) with the gaps between facing serifs
    kept in proportion (the upright Bold; docs/claude/bold.md, B1, approved
    2026-11-11).  The stems grow toward each other and the serifs keep their
    reach, so the gap between n's feet fell to 0.39 of the Regular's while
    the counter kept 0.82; the reference bolds keep the gap's share of the
    counter (0.89 to 0.91).  For part_serifs' pairs: where the gap's share
    of the white between the strokes, measured GAP_AT into the letter, is
    below GAP_SHARE of the source's, both tips are shortened in the source
    in steps of GAP_STEP until it is.  A glyph where that is not reached
    within the serifs' length stays as it is.  The far tip of a diagonal's
    serif follows by a few units: embolden_by_weight weighs a serif's edge
    at its middle, which the shortening moves.  Returns (glyph, pairs)."""
    src = ufoLib2.objects.Glyph()
    wide.replay(src.getPen())
    sp, bp = _simple_path(src), _simple_path(bold)
    todo = []
    for pair in serif_pairs(src):
        ta, tb, mid, gap, band, _, above = pair
        if len(ta) < 2 or len(tb) < 2:
            continue  # no serif's end but a stroke's flat foot (M's vertex): shortening it would thin the stroke
        y, side = (band[0], 1) if above else (band[1], -1)
        w_src, w_bold = _white(sp, mid, y + side * GAP_AT), _white(bp, mid, y + side * GAP_AT)
        g_bold = _white(bp, mid, y + side * 6)
        if w_src >= max(GAP_MIN_WHITE, gap) and w_bold >= GAP_MIN_WHITE and g_bold \
                and g_bold < GAP_SHARE * gap / w_src * w_bold - 2:
            todo.append((*pair, y + side * 6, y + side * GAP_AT, GAP_SHARE * gap / w_src))
    if not todo:
        return bold, 0
    for s in range(GAP_STEP, int(min(t[5] for t in todo)) - 20, GAP_STEP):
        out = make(_shortened(wide, todo, s))
        op = _simple_path(out)
        if all(_white(op, t[2], t[7]) >= t[9] * _white(op, t[2], t[8]) - 2 for t in todo):
            return out, len(todo)
    return bold, 0


FAULTS = {}  # faults' counts by outline, for the run (each letter asks up to five times)


def faults(g, font):
    """How many notches (a slit between parts that come close), slivers and
    twists (an outline crossing itself at a tight terminal) g's contours have
    (only the contours: font does not change it)."""
    key = repr([[(p.x, p.y, p.type, p.smooth) for p in c.points] for c in g.contours])
    if key not in FAULTS:
        FAULTS[key] = _faults(g, font)
    return FAULTS[key]


def _faults(g, font):
    from glyph_lint import notch_findings, vector_findings

    p = pathops.Path()
    for c in g.contours:
        c.draw(p.getPen())
    if not p.contours:
        return 0
    only = ufoLib2.objects.Glyph()
    for c in g.contours:
        c.drawPoints(only.getPointPen())
    vec = [f for f in vector_findings(pathops.simplify(p)) if f[0] in ("sliver", "twist")]
    return len(notch_findings(font, only, p.bounds)) + len(vec)


def slit(glyph, before, font):
    """Whether glyph (emboldened contours) has a fault the Regular's glyph
    (before) has not."""
    return faults(glyph, font) > faults(before, font)


def mark_like(g):
    """Accents and combining marks: zero width, the spacing modifier
    symbols (´ ˆ ΄ ᾿ ..., whatever their width) and the unencoded 880-wide
    spacing accents (Acute ...), not a small cap that width (the Italic's
    ґ.sc, 880 wide, emboldened as an accent)."""
    if g.width == 0:
        return True
    if g.unicode is not None:
        return unicodedata.category(chr(g.unicode)) in ("Sk", "Mn")
    return g.width == 880 and not g.name.endswith(".sc")


SLANT = 0.0  # the source's slant (tan of its italic angle), set in main()


def optical_fit(ref, new, h, depth=0.2, steps=40):
    """(left, right) side space to add to new (an outline, upright) so that
    the white beside its ink across 0..h is ref's, as space_figures.optical
    measures white (rows across the band, deep white clipped): both
    measured from the same edges and clipped in ref's window, so a part
    shorter than ref's (the f's bar end) counts as the white it adds across
    the band, not as the whole side moving."""
    from space_figures import _runs

    paths = []
    for rec in (ref, new):
        p = pathops.Path()
        rec.replay(p.getPen())
        p = pathops.simplify(p)
        if not p.contours:
            return None
        paths.append(p)
    x0 = min(p.bounds[0] for p in paths)
    x1 = max(p.bounds[2] for p in paths)
    rows = [[_runs(p, h * (i + 0.5) / steps) for i in range(steps)] for p in paths]
    out = []
    for which in "LR":
        dist = [[None if not rr else (rr[0][0] - x0 if which == "L" else x1 - rr[-1][1]) for rr in r] for r in rows]
        real = [v for v in dist[0] if v is not None]
        if not real:
            return None
        cap = min(real) + depth * h
        mean = [sum(min(v, cap) if v is not None else cap for v in d) / steps for d in dist]
        out.append(round(mean[0] - mean[1]))
    return tuple(out)


def band_height(font, name):
    """The height a glyph's side space is judged over: the x-height for
    lowercase, the small caps' for small caps, the cap height for the rest."""
    if name.split(".")[1:2] == ["sc"]:
        return font.lib.get("org.myiadidot.smallcapHeight", 1040)
    # a ligature is judged as the unencoded ones are, whatever its code
    # point (U+FB05 U+FB06 on ſt st moved them 9 units, 2026-11-08)
    ch = chr(font[name].unicode) if font[name].unicode and "_" not in name else ""
    if ch and unicodedata.category(ch) == "Ll":
        return font.info.xHeight or 884
    return font.info.capHeight or 1434


def bold_rec(glyph):
    rec = RecordingPen()
    glyph.draw(rec)
    return rec


def rec_bounds(rec):
    """The ink bounds of a recording or glyph (overlaps merged)."""
    p = pathops.Path()
    (rec.replay if hasattr(rec, "replay") else rec.draw)(p.getPen())
    p = pathops.simplify(p)
    return p.bounds if p.contours else None


def tx(x, y):
    """Where an x at height y lands in the Bold: in the upright frame scaled
    across by KX and moved AX / 2 right."""
    return (x - y * SLANT) * KX + AX / 2 + y * SLANT


def tx_offset(dx, dy):
    """A component offset in the Bold: scaled across in the upright frame."""
    return (dx - dy * SLANT) * KX + dy * SLANT


def attach_point(font, mark, bases, centre):
    """Where a mark component attaches, in the Regular's composite and in the
    Bold's: the anchor of the base component nearest to the mark's ink, or
    failing that the mark's own attachment point (centre)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    mdx, mdy = mark.transformation[4], mark.transformation[5]

    def moved(x, y):  # unanchored: the composite's outline moves so
        return x, tx(x, y)

    if ink is None:
        return moved(mdx + centre[mark.baseGlyph], mdy)
    mx, my = mdx + (ink[0] + ink[2]) / 2, mdy + (ink[1] + ink[3]) / 2
    best = None
    for base, bdx, bdy in bases:
        for a in font[base].anchors:
            if a.name.startswith("_"):
                continue
            ax, ay = a.x + bdx, a.y + bdy
            d = abs(ax - mx) + abs(ay - my)
            if best is None or d < best[0]:
                # in the Bold: the base's anchor and its offset, rounded as
                # they are written, so the mark lands exactly where mark
                # positioning puts it
                best = (d, ax, round(tx(a.x, a.y)) + round(tx_offset(bdx, bdy)))
    return best[1:] if best else moved(mdx + centre[mark.baseGlyph], my)


def slant_back(path, pen, transforms, split):
    """path drawn into pen through transforms (applied in the order given);
    split: its curves split where slanting again sets them past their
    points (italic_geometry.EXTREME_PAST), as the Italic split them."""
    from derive import with_extremes
    from italic_geometry import EXTREME_PAST

    rec = RecordingPen()
    pen_t = rec
    for t in reversed(transforms):
        pen_t = TransformPen(pen_t, t)
    path.draw(pen_t)
    if split:
        with_extremes(rec, pen, round_points=False, past=EXTREME_PAST)
    else:
        rec.replay(pen)


def contours_only(g):
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    return rec


def redraw(g, glyph):
    """Replace g's contours with those of glyph (an emboldened ufoLib2 Glyph);
    quadratic segments (pathops' results may hold some) made cubic."""
    g.clearContours()
    if any(p.type == "qcurve" for c in glyph.contours for p in c.points):
        from derive import CubicPen

        for c in glyph.contours:
            c.draw(CubicPen(g.getPen()))
        return
    pen = g.getPointPen()
    for c in glyph.contours:
        c.drawPoints(pen)


def refit_horns(font):
    """The letters with a horn composed again on the outlines as saved:
    composites.py fits the horn to its base and keeps the marks above
    clear of it by their ink, which rounding and cleaning still move."""
    from composites import Builder

    builder = Builder(font)
    for g in [g for g in font if g.unicode is not None and g.components]:
        if (len(unicodedata.normalize("NFD", chr(g.unicode))) < 2
                or not any(c.baseGlyph in ("horn", "Horn") for c in g.components)):
            continue
        r = builder.recipe(g.unicode)
        if [(c.glyph, c.dx, c.dy) for c in r.components] != [(c.baseGlyph, *c.transformation[4:]) for c in g.components]:
            r.name, lib = g.name, dict(g.lib)
            del font[g.name]
            builder.write(r)
            font[r.name].lib.update(lib)


def in_line(glyph, base, most=5):
    """a curve running into a line (or out of one) within most degrees of
    it, where base has that node (within 1.5 units) running on smoothly
    (under a degree): its handle there put in line, its length kept (a
    letter made again in the upright frame is rounded there, then slanted
    back: ʉ's stem under its bar turned 3.7 degrees where u's runs on,
    more than round_smoothly mends)"""
    def joins(g):
        for c in g.contours:
            P, n = c.points, len(c.points)
            for i, p in enumerate(P):
                prev, nxt = P[(i - 1) % n], P[(i + 1) % n]
                if p.type == "line" and prev.type and not nxt.type:
                    o, h = prev, nxt  # a line in, a curve out
                elif p.type == "curve" and not prev.type and nxt.type == "line":
                    o, h = nxt, prev  # a curve in, a line out
                else:
                    continue
                lx, ly = p.x - o.x, p.y - o.y
                hx, hy = h.x - p.x, h.y - p.y
                ll, hl = math.hypot(lx, ly), math.hypot(hx, hy)
                if ll > 1e-9 and hl > 1e-9:
                    t = math.degrees(math.acos(max(-1.0, min(1.0, (lx * hx + ly * hy) / (ll * hl)))))
                    yield p, h, (lx / ll, ly / ll), hl, t

    smooth = [(p.x, p.y) for p, _, _, _, t in joins(base) if t < 1]
    for p, h, (ux, uy), hl, t in list(joins(glyph)):
        if 0 < t <= most and any(math.dist((p.x, p.y), q) <= 1.5 for q in smooth):
            h.x, h.y = p.x + ux * hl, p.y + uy * hl


def round_smoothly(P):
    """P's points rounded to whole units, a join that ran on (nearly)
    smoothly, under 3 degrees, not broken further: where rounding leaves
    it turning by more than a degree and more than it did, its handles
    moved a unit each, together, to bring it more in line (a 15-unit
    handle rounded turns up to 4 degrees, one moved alone in steps of 3-4),
    a level or upright one (at an extreme) kept so. Handles under 10 units are left as rounded: theirs
    is no angle worth the name (checks.py)."""
    def turn(a, h, b):
        t = math.atan2(h[1] - a[1], h[0] - a[0]) - math.atan2(b[1] - h[1], b[0] - h[0])
        return abs(math.degrees((t + math.pi) % (2 * math.pi) - math.pi))

    def overshoot(k, q):
        """how far the curve through handle k, put at q, bulges past its ends"""
        h = [(P[(k + d) % n].x, P[(k + d) % n].y) for d in (-2, -1, 0, 1, 2)]
        seg = h[1:5] if P[(k - 1) % n].type else h[0:4]
        seg = [q if pt == (P[k].x, P[k].y) else pt for pt in seg]
        most = 0.0
        for step in range(1, 32):
            t = step / 32
            u = 1 - t
            pt = [u ** 3 * seg[0][c] + 3 * u * u * t * seg[1][c] + 3 * u * t * t * seg[2][c] + t ** 3 * seg[3][c]
                  for c in (0, 1)]
            for c in (0, 1):
                lo, hi = sorted((seg[0][c], seg[3][c]))
                most = max(most, lo - pt[c], pt[c] - hi)
        return most

    n = len(P)
    raw = [(p.x, p.y) for p in P]
    for p in P:
        p.x, p.y = round(p.x), round(p.y)
    if n < 3:
        return
    for i, p in enumerate(P):
        if not p.type:
            continue
        a, b = (i - 1) % n, (i + 1) % n
        if min(math.dist(raw[a], raw[i]), math.dist(raw[i], raw[b])) < 1 or turn(raw[a], raw[i], raw[b]) > 3:
            continue
        node = (p.x, p.y)
        ends = [(P[a].x, P[a].y), (P[b].x, P[b].y)]
        least = turn(ends[0], node, ends[1])
        # only what the rounding broke (an outline in whole units, a drawn
        # glyph kept, stays as it is)
        if least <= max(1, turn(raw[a], raw[i], raw[b]) + 0.25) or min(math.dist(e, node) for e in ends) < 10:
            continue
        # each handle's places a unit around it (an on-curve neighbour, a
        # line's end, stays), tried together: one alone, 15-20 units long,
        # turns in steps of 3-4 degrees
        options = []
        for k in (a, b):
            places = [(P[k].x, P[k].y)]
            if not P[k].type:
                bulge = overshoot(k, (P[k].x, P[k].y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (P[k].x + dx, P[k].y + dy)
                        # an extreme's handle stays level or upright
                        if (dx or dy) and math.dist(q, node) >= 10 and not (P[k].x == p.x and q[0] != p.x) \
                                and not (P[k].y == p.y and q[1] != p.y) and overshoot(k, q) <= max(bulge, 2):
                            places.append(q)  # (nor bulging further past its ends: an extreme lost)
            options.append(places)
        best = None
        for qa in options[0]:
            for qb in options[1]:
                t = turn(qa, node, qb)
                moved = abs(qa[0] - P[a].x) + abs(qa[1] - P[a].y) + abs(qb[0] - P[b].x) + abs(qb[1] - P[b].y)
                if t < least - 1e-9 or (best and abs(t - least) < 1e-9 and moved < best[2]):
                    best, least = (qa, qb, moved), t
        if best:
            (P[a].x, P[a].y), (P[b].x, P[b].y) = best[0], best[1]


def separate_breve_grave_stacks(font):
    """Keep the inherited grave/breathing pairs clear of the Greek breve.

    These legacy mark ligatures use fixed component offsets rather than
    Builder's stacking anchors. Weighting makes the grave touch the breve.
    Move the complete upper pair, preserving its internal arrangement and
    the stack's attachment anchor, with the usual lowercase mark gap.
    """
    from smallcaps import ink_bounds

    for breathing in ("0313", "0314"):
        glyph = font[f"brevecmb_uni{breathing}_gravecomb.grek"]
        upper, breve = glyph.components
        upper_bounds = ink_bounds(font, upper.baseGlyph)
        breve_bounds = ink_bounds(font, breve.baseGlyph)
        gap = upper_bounds[1] + upper.transformation.dy - (breve_bounds[3] + breve.transformation.dy)
        if gap < STACK_GAP_LC:
            xx, xy, yx, yy, dx, dy = upper.transformation
            upper.transformation = (xx, xy, yx, yy, dx, dy + math.ceil(STACK_GAP_LC - gap))


def finalize(font, smooth=True, separate_stacks=False, plain=()):
    """Finish a generated style before persistence. Its
    points, anchors and component offsets are rounded to whole units first,
    and what that leaves cleaned (glyph_lint). The Regular's record of what
    its derived glyphs were built from (built_from.py) is left behind: a
    generated style is checked by being generated again.
    smooth: joins the rounding would break kept smooth (round_smoothly).
    plain: glyphs rounded plainly all the same.
    separate_stacks: fit legacy Greek breve/grave stacks after rounding;
    enabled for the bold styles, not for the Italic's shared writer."""
    for g in font:
        g.lib.pop(BUILT_KEY, None)
        for c in g.contours:
            if smooth and g.name not in plain:
                round_smoothly(c.points)
            else:
                for p in c.points:
                    p.x, p.y = round(p.x), round(p.y)
        for a in g.anchors:
            a.x, a.y = round(a.x), round(a.y)
        for c in g.components:
            xx, xy, yx, yy, dx, dy = c.transformation
            c.transformation = (xx, xy, yx, yy, round(dx), round(dy))
    fix(font)  # what rounding left (a unit's step)
    from finalization import finish_glyphs

    finish_glyphs(font)
    if separate_stacks:
        separate_breve_grave_stacks(font)
    refit_horns(font)


def write(font, path, smooth=True, separate_stacks=False, plain=(), kept=None):
    """font finalized and saved to path, the acceptances of the
    style saved there before carried over (accepted.py), and the glyphs
    kept as drawn (drawn.py: kept, as saved) put back as they were."""
    from accepted import acceptances, carry
    from drawn import restore
    from ufo_io import save_font

    finalize(font, smooth=smooth, separate_stacks=separate_stacks, plain=plain)
    carry(acceptances(ufoLib2.Font.open(path)) if Path(path).exists() else {}, font)
    restore(kept or {}, font)
    save_font(font, path)

SMALL_SUFFIXES = ("superior", "inferior", ".numr", ".dnom", ".sups", ".subs")


def small_glyphs(regular, italic):
    """(names, scale): the glyphs that are letters or figures made small (the
    superior and inferior figures, numerators, ª º, the modifier letters),
    and their scale, the superior zero's round stem against the zero's.
    Emboldened by weight at full size their stems (about 100) would gain a
    fraction of AX; as a letter at that scale, they gain AX times it."""
    import derive
    from derived import recipes

    scale = derive.strokes(regular, "zerosuperior")[1] / derive.strokes(regular, "zero")[1]
    names = {g.name for g in regular if g.name.split(".")[0].endswith(SMALL_SUFFIXES[:2])
             or any(g.name.endswith(sfx) for sfx in SMALL_SUFFIXES[2:])}
    names |= {"ordfeminine", "ordmasculine"} & set(regular.keys())
    cmap = {u: g.name for g in regular for u in g.unicodes}
    for ch, op, _base, _band in recipes(italic):
        if op == "superior":
            names.add(derive.resolve(cmap, ch))
    for u, name in cmap.items():
        uname = unicodedata.name(chr(u), "")
        if uname.startswith(("MODIFIER LETTER SMALL", "MODIFIER LETTER CAPITAL")) or "SUPERSCRIPT" in uname \
                or "SUBSCRIPT" in uname:
            names.add(name)
    return names, scale


def saved_flaws(path):
    """The steps and crumbs (glyph_lint) of path as saved, rounded to whole
    units and cleaned (write: a step a unit high taken out), by kind and
    place; None where they cannot be told (a contour rounded away to
    nothing)."""
    from fontTools.pens.roundingPen import RoundingPen
    from glyph_lint import clean, step_findings, vector_findings

    rounded = pathops.Path()
    pathops.simplify(path).draw(RoundingPen(rounded.getPen()))
    try:
        rounded = clean(rounded)
        return {f[:2] for f in step_findings(rounded) + vector_findings(rounded)}
    except (pathops.PathOpsError, StopIteration):
        return None


def follow_bases(source, font, italic, kx=None, slant=None, skip=(), whole=None):
    """Derived letters (derive.py's recipes) made of the Bold's own base:
    emboldened whole, a letter's junctions (a slash meeting a stem, a tilde
    crossing a diagonal) thicken unlike its base's strokes, eating the stem
    beside them. One that is its base turned, mirrored or flipped (exactly,
    in the source) becomes the Bold base so moved; one that adds to its
    base without cutting any of it is joined with the Bold base, placed
    where the source's base sits in it, unless the emboldened letter keeps
    that base already. Letters that cut their base (a hook replacing a
    stem's end) stay as emboldened. kx and slant: the widening and the
    italic's slant (make_bold's by default); skip: names to leave; whole:
    a dict that gets the letters left emboldened whole, with the reason.
    Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import KEEPS, TRANSFORMS, Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    kx = KX if kx is None else kx
    slant = SLANT if slant is None else slant
    # recipes that only cut their base
    recuts = {"unserif": derive.unserif_cut}
    deslant = (1, 0, -slant, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    def ink(name):
        p = pathops.Path()
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(p.getPen())
        return p

    changed, failed = [], []
    whole = {} if whole is None else whole
    for ch, op, base, band in recipes(italic):
        name, base = resolve(ch), resolve(base)
        if name not in source or base not in source or base == "space" or name not in font or name in skip:
            continue
        g = font[name]
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        if g.components:
            continue
        if op in recuts:
            # only a cut of its base (U.horn: the serif's outer arm): the
            # same cut of this font's base, found in the upright frame and
            # made in the font's own (pathops splits curves at the extremes
            # of the frame it cuts in)
            from make_italic import XH, shear

            work = ufoLib2.Font()
            piece = work.newGlyph(base)
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            rec.replay(piece.getPen())
            shear(piece, -slant, XH / 2)
            cut = pathops.Path()
            recuts[op](work, base).draw(TransformPen(cut.getPen(), (1, 0, slant, 1, -slant * XH / 2, 0)))
            out = derive.path_op(derive.to_path(font, font[base]), cut, "DIFFERENCE")
            g.clearContours()
            derive.draw_path(font, font[base], g, out)
            g.width = font[base].width
            changed.append(name)
            continue
        if op not in KEEPS | TRANSFORMS:
            if op not in RESHAPES:
                whole[name] = f"{op}: cuts its base"
            continue
        mine = Outline(source, name, deslant)
        if mine.bounds is None:
            continue
        if op in TRANSFORMS:
            w = source[base].width
            sb = band if isinstance(band, str) else band[0] if isinstance(band, tuple) else "x"
            cy = derive.band_middle(source, sb) if op != "mirror" else 0
            a, _, _, d, e, f = {"turn": (-1, 0, 0, -1, w, 2 * cy), "mirror": (-1, 0, 0, 1, w, 0),
                                "flip": (1, 0, 0, -1, 0, 2 * cy)}[op]
            shares, _, _ = compare(Outline(source, base, (a, 0, -a * slant, d, e, f)), mine)
            if shares["exact"] < 0.98:
                whole[name] = f"{op}: not exactly its base so moved"
                continue
            # the same move of the Bold base, in the upright frame the Italic
            # makes its letters in (make_italic.shear: about half the
            # x-height, where the frames agree); about the baseline, a
            # mirrored or turned letter's ink moved right by twice the slant
            # times its height (ɘ ɐ against the next letter)
            from make_italic import XH

            y0 = XH / 2
            bw = font[base].width
            e = bw if op in ("turn", "mirror") else 0
            out = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            # slanted again, its curves split where they run past their
            # points (the Italic's turned and mirrored letters, ɔ ƹ ɜ, are)
            slant_back(rec, out.getPen(), [(1, 0, -slant, 1, slant * y0, 0), (a, 0, 0, d, e, f),
                                           (1, 0, slant, 1, -slant * y0, 0)], bool(slant))
            g.width = bw
        else:
            shares, dx, _ = compare(Outline(source, base, deslant), mine)
            # only a letter that keeps its whole base in the source: the
            # Italic's ɨ has the dot of its own, not i's, and would get both
            if shares["lost"] > 0.02:
                if op not in RESHAPES:
                    whole[name] = f"{op}: does not keep its whole base"
                continue
            # nothing to mend when the emboldened letter keeps its Bold base
            # (ʘ: O's outline, the dot inside); and Skia's union fails on
            # curves that coincide, as theirs then do
            if compare(Outline(font, base, deslant), Outline(font, name, deslant))[0]["lost"] <= 0.02:
                continue
            placed = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            rec.replay(TransformPen(placed.getPen(), (1, 0, 0, 1, dx * kx, 0)))
            # each simplified on its own first: a base rebuilt here (ə turned)
            # winds the other way, and in one path the two would cancel
            a = pathops.simplify(ink(name))
            # the union holds all of both, row by row, or it failed (curves
            # that coincide): then tried with the base a hair lower, higher
            # (ⱥ.sc: a.sc's foot a third of a unit above the letter's) or
            # aside, either way (ǥ.sc's bar on g.sc, 2026-11-05: only to the
            # left), which parts the curves (rounded away on saving), else
            # the letter is left as emboldened
            for nudge in (0, (0, -0.25), (0, 0.25), (0.25, 0), (-0.25, 0)):
                b = pathops.simplify(placed)
                if nudge:
                    b = pathops.Path()
                    placed.draw(TransformPen(b.getPen(), (1, 0, 0, 1, *nudge)))
                    b = pathops.simplify(b)
                try:
                    out = pathops.op(a, b, pathops.PathOp.UNION)
                except pathops.PathOpsError:  # failed outright: as a union that lost ink
                    held = False
                    continue
                joined = Outline(None, None, deslant, path=out)
                held = all(compare(Outline(None, None, deslant, path=p), joined)[0]["lost"] <= 0.01 for p in (a, b))
                if held and nudge:
                    # a nudged join that leaves a step or a crumb, once
                    # rounded and cleaned as it is saved, is no better
                    flaws = saved_flaws(out)
                    held = flaws is not None and not flaws
                if held:
                    break
            if not held:
                failed.append(name)
                whole[name] = f"{op}: the union with its base failed"
                continue
        out = pathops.simplify(out)
        glyph = ufoLib2.objects.Glyph()
        out.draw(glyph.getPen())
        redraw(g, glyph)
        changed.append(name)
    if failed:
        print("  derived letters left as emboldened (their union failed):", " ".join(failed))
    return changed


MIN_PIECE = 3000  # units²: an added piece (ɬ.sc's bar is 8000), not a sliver
SPECK = 8000  # units²: a cut's remnant apart from the letter (Bulgarian ж's 4590, Bold Italic Ɦ's serif end 6622),
# not a piece (i's dot 40000)


def attached_small(source, font, italic):
    """Derived letters that attach a glyph scaled down to their base (ɬ's
    ring, the degree sign at 0.45; ⁂'s asterisks): emboldened whole, the
    small piece thickens like a stem and closes up. Made of the Bold base
    and the source's added parts, those emboldened at the weight of their
    scale (a ring at 0.45 gains 0.45 of a stem's AX), as the Bold degree
    sign scaled would be. Recipes that cut the base (Ɲ) stay as they are.
    Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    deslant = (1, 0, -SLANT, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    def path(f, name, t=(1, 0, 0, 1, 0, 0)):
        p = pathops.Path()
        rec = DecomposingRecordingPen(f)
        f[name].draw(rec)
        rec.replay(TransformPen(p.getPen(), t))
        return pathops.simplify(p)

    changed = []
    for ch, op, base, band in recipes(italic):
        if op != "attach" or band[1]:
            continue
        scales = [min(abs(sx), abs(sy)) for piece, _, _, (sx, sy, *_) in band[2]
                  if piece not in ("rect", "line", "poly", "counter", "curl")]
        if not scales or min(scales) >= 0.8:
            continue
        name, base = resolve(ch), resolve(base)
        if name not in source or name not in font or base not in source:
            continue
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        k = min(scales)
        mine = path(source, name, deslant)
        added = mine
        dx = 0
        if source[base].contours or source[base].components:
            _, dx, _ = compare(Outline(source, base, deslant), Outline(source, name, deslant))
            added = pathops.op(mine, path(source, base, (1, 0, -SLANT, 1, dx, 0)), pathops.PathOp.DIFFERENCE)
        if italic and name in ("uni026C", "uniA7AD"):
            from l_belt import attachment_band

            low, high = attachment_band(name)
            # Joined belts can carry a thin base-rounding sliver into the
            # same contour as the real piece. Do not embolden that sliver
            # into an extra stem or an ascender extension.
            added = pathops.op(added, derive.rect_path(-derive.BIG, low, derive.BIG, high),
                               pathops.PathOp.INTERSECTION)
        # only the pieces the recipe added: where the source letter's edge
        # strays a unit from its base's (the Italic's), slivers are left
        kept = pathops.Path()
        for c in added.contours:
            if abs(c.area) >= MIN_PIECE:
                c.draw(kept.getPen())
        rec = RecordingPen()
        kept.draw(TransformPen(rec, (KX, 0, 0, 1, 0, 0)))
        heavier = embolden(rec, AX * k, AY)
        out = pathops.Path()
        heavier.draw(TransformPen(out.getPen(), (1, 0, 0, 1, AX / 2, 0)))
        if source[base].contours or source[base].components:
            b = path(font, base, (1, 0, -SLANT, 1, dx * KX, 0))
            out = pathops.op(pathops.simplify(out), b, pathops.PathOp.UNION)
            # the union holds all of the base, or it failed: left as it was
            if compare(Outline(None, None, path=b), Outline(None, None, path=out))[0]["lost"] > 0.01:
                continue
        glyph = ufoLib2.objects.Glyph()
        pathops.simplify(out).draw(TransformPen(glyph.getPen(), (1, 0, SLANT, 1, 0, 0)))
        redraw(font[name], glyph)
        changed.append(name)
    return changed


def small_cap_stems(up, glyph):
    """A small cap made from its capital (derive.enlarge: all its strokes
    brought to o.sc's round by one amount), its stems to h.sc's: the Bold
    Italic's small-cap stems stand heavier against its rounds than its
    capitals' do (h.sc 304, o.sc 263; ƙ.sc ƥ.sc ƭ.sc ɠ.sc ɦ.sc came out
    255, 2026-10-27). Only a letter whose main stroke is a stem; its round
    strokes then reach the stem's weight, within the stroke check's band."""
    from derived import Outline
    from strokes import main_stroke, zone

    top = zone(up, "sc")
    stem = main_stroke(Outline(up, "h.sc"), top)[0]
    weight, straight = main_stroke(Outline(up, glyph.name), top)
    if not (weight and straight and stem and weight < stem):
        return
    ax = stem - weight
    rec = RecordingPen()
    glyph.draw(rec)
    out = embolden(rec, ax, 0)
    glyph.clearContours()
    out.draw(TransformPen(glyph.getPen(), (1, 0, 0, 1, ax / 2, 0)))  # its left side bearing kept
    glyph.width = round(glyph.width + ax)
    for a in glyph.anchors:
        a.x = round(a.x + ax / 2)


def fill_stem_notches(glyph, most=12):
    """glyph (in place) with the notches beside its vertical stems filled:
    a short straight run leaving the stem's edge back the way the edge came
    (a middle tilde whose underside dips below its join with the stem, ᵰ:
    9 units out, 21 down) closed along the edge, the stem running on to the
    run's far end. glyph_lint cleans it as a ledge, shrunk to its middle,
    and so pulled the stem's node aside (ᵰ's left stem leaned 5 units,
    2026-11-04). most: the furthest out the run reaches."""
    from glyph_lint import LEDGE

    for contour in glyph.contours:
        points = contour.points
        i = 0
        while i < len(points):
            n = len(points)
            a, prev = points[i], points[i - 1]
            j = next(k for k in range(i + 1, i + n) if points[k % n].type)
            b = points[j % n]
            run = [points[k % n] for k in range(i + 1, j)]
            # the run straight: its handles on the line from a to b
            straight = all(abs((q.x - a.x) * (b.y - a.y) - (q.y - a.y) * (b.x - a.x))
                           <= math.dist((a.x, a.y), (b.x, b.y)) for q in run)
            up = (a.y - prev.y) if prev.type and abs(prev.x - a.x) < 0.5 else 0
            if (a.type == "line" and up and straight and 0 < abs(b.x - a.x) <= most
                    and math.dist((a.x, a.y), (b.x, b.y)) < LEDGE and (b.y - a.y) * up < 0
                    and abs(b.y - a.y) > abs(b.x - a.x)):
                a.y = b.y
                b.x = a.x
                for k in sorted(range(i + 1, j + 1), reverse=True):
                    del points[k % n]
                i = 0
                continue
            i += 1


def drop_specks(glyph):
    """glyph (in place) without the specks a recipe's cut leaves apart from
    the letter (a corner of the Bold's wider serif outside the cut box, Ɲ's
    feet, Bulgarian ж's and ю's arms): outer contours under SPECK.
    Counters stay (a pinhole is judged as such)."""
    p = pathops.Path()
    glyph.draw(p.getPen())
    contours = list(pathops.simplify(p).contours)
    if len(contours) < 2:
        return
    outer = max(contours, key=lambda c: abs(c.area)).clockwise
    kept = [c for c in contours if c.clockwise != outer or abs(c.area) >= SPECK]
    if len(kept) == len(contours):
        return
    glyph.clearContours()
    pen = glyph.getPen()
    for c in kept:
        c.draw(pen)


def fill_pinholes(glyph, solid, font):
    """glyph (in place) with its pinholes filled where solid, the letter
    emboldened whole, has ink: counters under MIN_PIECE in a join the
    letter had solid (Bold Ɦ's ball over the serif it meets). One the
    emboldened letter has too, a curl closed on its stroke (ң), stays to
    be judged."""
    p = pathops.Path()
    glyph.draw(p.getPen())
    contours = list(pathops.simplify(p).contours)
    if len(contours) < 2:
        return
    outer = max(contours, key=lambda c: abs(c.area)).clockwise
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    ink, rec = pathops.Path(), DecomposingRecordingPen(font)
    solid.draw(rec)
    rec.replay(ink.getPen())
    ink = pathops.simplify(ink, fix_winding=True)
    holes = []
    for c in contours:
        if c.clockwise == outer or abs(c.area) >= MIN_PIECE:
            continue
        hole = pathops.Path()
        c.draw(hole.getPen())
        hole = pathops.op(pathops.simplify(hole, fix_winding=True), ink, pathops.PathOp.DIFFERENCE)
        if abs(hole.area) < 0.05 * abs(c.area):  # covered by the emboldened letter's ink
            holes.append(id(c))
    if not holes:
        return
    glyph.clearContours()
    pen = glyph.getPen()
    for c in contours:
        if id(c) not in holes:
            c.draw(pen)


def serif_top(font, name, pick):
    """Where the foot serif under a letter's first or last stem ends: the
    lowest height at which that stem is no wider than above (None: no foot
    serif)."""
    import derive

    stems = derive.stems_at(font, name, 300)
    if not stems:
        return None
    a, b = stems[0] if pick == "first" else stems[-1]
    for y in range(1, 200):  # above the baseline row (a sliver there in the Bold's d)
        runs = [r for r in derive.stems_at(font, name, y) if r[1] > a and r[0] < b]
        if runs and max(r[1] - r[0] for r in runs) <= 1.05 * (b - a):
            return y if y > 1 else None
    return None


def rederive(source, font, italic, whole):
    """Derived letters left emboldened whole because they cut their base (a
    hook replacing a stem's end, Ц's tail its foot) made again by their
    recipe (derive.py) from the Bold's own glyphs, in the upright frame: a
    Bold base and a Bold f-top hook, each at its weight, joined as in the
    Regular, where emboldened whole the joins thicken and open (ɓ's bowl
    meeting the stem). A recipe placed by the Regular's coordinates can miss
    in the Bold, so the new letter replaces the old only if it stays close
    to it (rows overlapping by IOU, the advance within WIDTH) and has no
    more outline faults (glyph_lint); else it is left as it was, the reason
    in whole updated. Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import copy

    import derive
    from derived import Outline, _best_iou, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from glyph_lint import lint_glyph

    iou, width = 0.85, 0.03
    keep = ITALIC_BOLD_KEEP_WHOLE if italic else BOLD_KEEP_WHOLE
    up = copy.deepcopy(font)
    if italic:
        from make_italic import XH, shear

        for g in up:
            shear(g, -SLANT)
    cmap = {u: g.name for g in up for u in g.unicodes}
    # what the recipes draw by number (a hook's stem, a curl), at the Bold's
    # stems and hairlines, not the source's
    (_, stem, hair), (_, stem0, hair0) = derive.strokes(up, "o"), derive.strokes(source, "o")
    scale = (stem / stem0, hair / hair0)
    if italic:
        # the Italic's recipes are tuned at lighter strokes than the Italic's
        # (make_italic.recipe_scale), here without the Italic's added
        # weight: the Bold Italic's descenders were chosen so (as heavy as
        # ȷ's); with it ң's curl closes on its stroke
        from make_italic import recipe_scale

        tuned = recipe_scale(stem0, hair0, weight=0)
        scale = (scale[0] * tuned[0], scale[1] * tuned[1])

    def resolve(c):
        return derive.resolve(cmap, c)

    def parts(f, g):
        """the outer contours, not the counters (ɯ.sc's closed counter is
        no remnant; simplified, the outer ones all wind like the largest),
        and the pinholes: counters under MIN_PIECE, where a curl closed on
        its stroke (ң emboldened whole)"""
        p = pathops.Path()
        rec = DecomposingRecordingPen(f)
        g.draw(rec)
        rec.replay(p.getPen())
        contours = list(pathops.simplify(p).contours)
        if not contours:
            return 0, 0
        outer = max(contours, key=lambda c: abs(c.area)).clockwise
        return (sum(c.clockwise == outer for c in contours),
                sum(c.clockwise != outer and abs(c.area) < MIN_PIECE for c in contours))

    changed = []
    for ch, op, base, band in recipes(italic):
        name = resolve(ch)
        why = whole.get(name, "")
        rebuild = ITALIC_BOLD_REBUILD if italic else BOLD_REBUILD
        # (only what the Italic made so: its ᵃ is the sloped roman's, its ⁺ ⁼
        # the roman's, not its own a + = made small)
        by_op = (italic and op in ITALIC_BOLD_REBUILD_OPS and name in source
                 and source[name].lib.get("org.myiadidot.italicSource") == "derived")
        if not why.endswith(("cuts its base", "does not keep its whole base")) and name not in rebuild and not by_op:
            continue
        own = ch in (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)
        if own:
            op, base, band = (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)[ch]
            if callable(band):  # placed on the Bold's own glyphs
                band = band(up)
        up.lib[derive.STROKE_KEY] = (1, 1) if own else scale
        if name in keep:
            whole[name] = f"{op}: emboldened whole, made again from the Bold it misses ({keep[name]})"
            continue
        if len(base) == 1 or (derive.variant(base) and not base[0].isascii()):
            base = resolve(base)
        if base not in up:
            continue
        if op == "hook" and band[1].startswith("down"):
            # the stem cut where the source's foot serif ends: the Bold's
            # serif stands taller, cut there the hook took the serif's width
            # (ɭ's a ball as wide as its foot)
            sband, kind, pick, cut, *rest = band
            was, now = serif_top(source, base, pick), serif_top(up, base, pick)
            if was is not None and now is not None and was <= cut <= was + 15:
                band = (sband, kind, pick, cut + now - was, *rest)
        tmp = f"_rederived.{name}"
        order, cats = up.glyphOrder, dict(up.lib.get("public.openTypeCategories", {}))
        try:
            if italic:
                from make_italic import build_own

                # ɗ ɚ ɝ ʔ: the Italic's own constructions, from the Bold Italic's glyphs
                own_built = build_own(up, ch, op, base, band, tmp, resolve)
            new = up[tmp] if italic and own_built else derive.build(up, ch, op, base, band, tmp)
        except Exception as e:  # noqa: BLE001 (a recipe that does not run on the Bold: left whole)
            whole[name] = f"{op}: emboldened whole, its recipe fails on the Bold ({type(e).__name__})"
            continue
        finally:
            up.glyphOrder = order
            up.lib["public.openTypeCategories"] = cats
        if italic:
            from make_italic import ITALIC_JOINS

            joins = {**ITALIC_JOINS, **ITALIC_BOLD_JOINS}
            if ch in joins:  # as the Italic's, before it is judged
                derive.fair_joins(new, *joins[ch])
            from make_italic import ITALIC_CORNERS, ITALIC_RUNS, round_corner, straighten_run

            if ch in ITALIC_RUNS:  # as the Italic's (җ's descender into its c)
                straighten_run(new, *ITALIC_RUNS[ch])
            if ch in ITALIC_CORNERS:
                round_corner(new, *ITALIC_CORNERS[ch])
            from make_italic import SC_DRAFT_SIDES, SC_LEVEL_GAIN, capital_width, level_gain, uncrossed

            if name in SC_DRAFT_SIDES:
                # as the Italic makes them: uncrossed, the main stroke brought
                # to the capital's proportion (small_cap_stems took n.sc's
                # straight diagonal for a stem)
                uncrossed(up, tmp)
                # and its ink to h.sc's as the capital's to H's: the gain
                # widens the Bold Italic's serif ends too (thick here); twice,
                # so weight and width both settle
                for _ in range(2 if name in SC_LEVEL_GAIN else 0):
                    level_gain(up, tmp, *SC_LEVEL_GAIN[name])
                    capital_width(up, tmp, SC_LEVEL_GAIN[name][0])
            elif op == "enlarge" and name.endswith(".sc"):
                small_cap_stems(up, new)
        drop_specks(new)
        fill_pinholes(new, up[name], up)
        if op == "midtilde" and not italic:
            fill_stem_notches(new)
        # the steps and ledges where the recipe's piece meets the base, a
        # unit or two off: cleaned as the font is after (fix), not counted
        # as faults (the stroked bases, 2026-10-28: Ƴ ʄ ҳ)
        fix(up, [tmp])
        # the side bearings the source style gave the letter after its recipe
        # (the Regular's derive.SPACING, the Italic's ITALIC_SIDEBEARINGS):
        # the recipe's width alone has its hook counted in again
        if italic:
            from make_italic import ITALIC_SIDEBEARINGS as SOURCE_SPACING

            delta = SOURCE_SPACING.get(name)
        else:
            delta = derive.SPACING.get(ch)
        if delta:
            sidebearings(up, {tmp: delta})
        old = up[name]
        made, was = Outline(up, tmp), Outline(up, name)
        faults = len(lint_glyph(up, new)) - len(lint_glyph(up, old))
        # a part more than before: a remnant of what the cut should take (a
        # serif's end); a pinhole more or fewer
        (pn, hn), (po, ho) = parts(up, new), parts(up, old)
        faults += max(0, pn - po) + hn - ho
        close = made.bounds is not None and was.bounds is not None and _best_iou(made, was) >= iou
        if (name in rebuild or by_op) and faults <= 0:
            close, wide = True, by_op
        else:
            wide = abs(new.width - old.width) > width * old.width
        if close and wide and faults <= 0:
            # close to the letter but set otherwise (the recipe's spacing, not
            # the optical fit the emboldened letter got): the old side
            # bearings around the new outline
            (x0, _, x1, _), (o0, _, o1, _) = derive.ink_bounds(up, tmp), derive.ink_bounds(up, name)
            dx = round(o0 - x0)
            for contour in new.contours:
                for point in contour.points:
                    point.x += dx
            for anchor in new.anchors:
                anchor.x += dx
            new.width = round(old.width + (x1 - x0) - (o1 - o0))
            wide = False
        if not close or wide or faults > 0:
            if by_op and not why:
                # (a stroked letter the rebuild missed stays as stroked, no
                # letter emboldened whole)
                del up[tmp]
                continue
            whole[name] = (f"{op}: emboldened whole, made again from the Bold it "
                           + ("strays" if not close else "has faults" if faults > 0 else "changes its advance"))
            del up[tmp]
            continue
        glyph = ufoLib2.objects.Glyph()
        # slanted back as unslanted above (make_italic.shear, about half the
        # x-height): about the baseline, the ink stood SLANT * XH / 2 right;
        # its curves split where the slant sets them past their points, as
        # the emboldened letters' are (ɓ.sc's hook ran 80 units past)
        y0 = XH / 2 if italic else 0
        from make_italic import POINT_REPAIRS

        slant_back(new, glyph.getPen(), [(1, 0, SLANT, 1, -SLANT * y0, 0)],
                   italic and name not in POINT_REPAIRS)
        in_line(glyph, font[base])  # (the base's smooth joins kept so)
        if op == "bar" and new.width == font[base].width:
            # a bar on its whole base, set as it (ʉ on u): its accents where
            # the base has them (as emboldened, they stood 3 units left of
            # the ink made again)
            font[name].clearAnchors()
            for anchor in font[base].anchors:
                font[name].appendAnchor({"name": anchor.name, "x": anchor.x, "y": anchor.y})
        redraw(font[name], glyph)
        font[name].width = new.width
        # the recipes after it build on the letter made again, not the
        # emboldened one (ƈ.sc from Ƈ: the Italic's draft emboldened closed
        # its curl, 2026-10-27)
        redraw(up[name], new)
        up[name].width = new.width
        # its aliases as wide as it (ʛ, ɠ.sc)
        for g in font:
            if (len(g.components) == 1 and not g.contours and g.components[0].baseGlyph == name
                    and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
                g.width = up[g.name].width = font[name].width
        del up[tmp]
        whole.pop(name, None)
        changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("bold", nargs="?", default=str(ROOT / "sources/MyiaDidot-Bold.ufo"))
    args = ap.parse_args()
    global SLANT, AX, THIN, THICK
    from drawn import restore, saved

    # the glyphs kept as drawn (drawn.py), as last saved: put back before
    # anything is derived from them, and again at the end
    kept = saved(args.bold)
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    kern_clear.undo(font)  # the source's loosened pairs: this style finds its own
    angle = -(regular.info.italicAngle or 0)
    SLANT = math.tan(math.radians(angle))
    italic = bool(angle)
    if italic:
        AX, THIN, THICK = ITALIC_AX, ITALIC_THIN, ITALIC_THICK
        part_ff(font)
    nudge, extra = (ITALIC_ANCHOR_NUDGE, ITALIC_SIDEBEARINGS) if italic else (ANCHOR_NUDGE, BOLD_SIDEBEARINGS)
    by_weight = ITALIC_BOLD_BY_WEIGHT if italic else BOLD_BY_WEIGHT
    rounder_ones = ITALIC_BOLD_ROUNDER if italic else BOLD_ROUNDER
    fit_as_is = ITALIC_BOLD_FIT_AS_IS if italic else BOLD_FIT_AS_IS
    up, down = (1, 0, -SLANT, 1, 0, 0), (1, 0, SLANT, 1, 0, 0)  # deslant, slant again
    marks = {g.name for g in regular if mark_like(g)}
    # the paragraphos ⸏ ⸐ ⸑, rules under a line: a mark's weight and
    # advance, though they have one (fontbakery: base_has_width)
    marks |= {g.name for g in regular if g.unicode in (0x2E0F, 0x2E10, 0x2E11)}
    # a modifier symbol that is another sign as it is (꞉, the colon): that
    # sign, emboldened and widened with it, not an accent keeping its width
    marks -= {g.name for g in regular if g.name in marks and g.width and not g.contours
              and len(g.components) == 1 and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)
              and unicodedata.category(chr(g.unicode or 0x2C)) == "Sk"
              and not mark_like(regular[g.components[0].baseGlyph])}
    # what a combining mark is made of is an accent too (the spacing
    # ypogegrammeni ͺ is a modifier letter, but uni0345 is built on it)
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            marks.add(g.components[0].baseGlyph)
    # where each mark attaches: its own _ anchor, else the convention's 440
    # (spacing accents) or -440 (combining marks); offsets then move as the
    # anchors do, so a precomposed letter matches mark positioning
    centre = {}
    for name in marks:
        own = [a.x for a in regular[name].anchors if a.name.startswith("_")]
        centre[name] = own[0] if own else (440 if regular[name].width else -440)
    # a spacing accent attaches where the combining mark made of it does
    # (that mark's anchor, 880 to the right): the Greek ones are not at 440
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            c = g.components[0]
            own = [a.x for a in g.anchors if a.name.startswith("_")]
            if own and c.baseGlyph in marks and round(c.transformation[4]) == -880:
                centre[c.baseGlyph] = own[0] + 880

    # the composites the anchor rules make as they are: rebuilt in the Bold
    builder = Builder(regular)
    rule_made = set()
    for g in regular:
        if not g.components or g.contours or g.unicode is None:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = builder.recipe(g.unicode)
        except ValueError:
            continue
        mine = [(c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components]
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) == sorted(mine):  # in any order
            rule_made.add(g.name)

    small, small_scale = small_glyphs(regular, italic)
    fit = {}  # glyph: (left, right) side space to change, after emboldening by weight
    parted = []  # serifs kept apart (part_serifs)
    gapped = []  # gaps between facing serifs kept in proportion (keep_gaps)
    simple = []  # emboldened the rounder way (a slit otherwise)
    from make_italic import POINT_REPAIRS, SOURCE_KEY

    # the Bold Italic's letters emboldened by their strokes, all at once in
    # a pool (each about half a second); a glyph's own outline is looked up,
    # another (part_serifs' shortened serifs) drawn when asked
    def strokes_job(name, w, sc):
        gain = sc * ITALIC_BOLD_HEAVIER.get(name, 1.0)
        return (name, w.value, (ITALIC_AX * gain, AY, ITALIC_THIN * sc, ITALIC_THICK * sc,
                                ITALIC_HAIR * (sc if name in ITALIC_BOLD_HAIR_KEPT else gain), SLANT, SLIVER * sc * sc, ITALIC_BOLD_ROOTS.get(name, 0.0),
                                name in ITALIC_BOLD_SPLIT, ITALIC_BOLD_CAP_FREE.get(name, 0.0)))

    stroked, unstroked = {}, []
    cache = stroke_cache.Cache() if italic else None
    if italic:
        from concurrent.futures import ProcessPoolExecutor

        jobs = []
        for g in font:
            if g.contours and g.name not in marks and g.name not in ITALIC_BOLD_BY_POINTS:
                wide = RecordingPen()
                contours_only(g).replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                jobs.append(strokes_job(g.name, wide, small_scale if g.name in small else 1.0))
        # those stroked before with the same outline, arguments and code
        # come from the cache (stroke_cache: 9 of make generate's 11 minutes)
        done = cache.get(jobs)
        todo = [job for job in jobs if job[0] not in done]
        if todo:
            with ProcessPoolExecutor(JOBS) as pool:
                new = dict(pool.map(emboldened, todo, chunksize=8))
            cache.put(todo, new)
            done.update(new)
        if cache.db is not None:
            print(f"  emboldened by strokes: {len(jobs) - len(todo)} from the cache, {len(todo)} stroked")
        stroked = {repr(job[1]): done[job[0]] for job in jobs}

    def by_strokes(w, sc, name):
        """w (name's) emboldened by its strokes, a ufoLib2 Glyph (None: failed)"""
        if repr(w.value) in stroked:
            value = stroked[repr(w.value)]
        else:
            job = strokes_job(name, w, sc)
            kept = cache.get([job])
            if name in kept:
                value = kept[name]
            else:
                value = emboldened(job)[1]
                cache.put([job], {name: value})
        if value is None:
            return None
        glyph = ufoLib2.objects.Glyph()
        rec = RecordingPen()
        rec.value = value
        rec.replay(glyph.getPen())
        return glyph

    is_letter = classifier(font, 1, 1)  # the letters respace cuts (STROKE_OUT's)
    stroke_out = {}
    for g in font:
        is_mark = g.name in marks
        if g.contours:
            rec = contours_only(g)
            if is_mark and not italic:
                redraw(g, embolden(rec, MARK_AX, MARK_AY))
            elif is_mark:
                flat = RecordingPen()
                rec.replay(TransformPen(flat, up))
                heavier = embolden(flat, MARK_AX, MARK_AY)
                sloped = ufoLib2.objects.Glyph()
                heavier.draw(TransformPen(sloped.getPen(), down))
                redraw(g, sloped)
            else:
                wide = RecordingPen()
                rec.replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                # thick strokes AX heavier in any direction, hairlines AY
                # (a node moved by the weight of the stroke it is on)
                # a letter or figure made small, as at its scale (ᵃ, ⁰, ª)
                sc = small_scale if g.name in small else 1.0

                def make(w, sc=sc, bends=g.name not in fit_as_is, name=g.name, strokes=True):
                    # the Bold Italic's by its strokes (stroke_bold), where
                    # that fails by weight
                    if italic and strokes and name not in ITALIC_BOLD_BY_POINTS:
                        drawn = by_strokes(w, sc, name)
                        if drawn is not None:
                            if name in ITALIC_BOLD_SMOOTH_COUNTER:
                                drawn = smooth_counter(drawn, ITALIC_BOLD_SMOOTH_COUNTER[name])
                            return bridge(rezone(drawn, AY))
                        unstroked.append(name)
                    # short edges running on into a curve weighed as it in
                    # the Bold (ƒ)
                    return bridge(rezone(embolden_by_weight(w, AX * sc, AY, THIN * sc, THICK * sc,
                                                            runs_on=not italic,
                                                            keep_bends=bends),
                                         AY))

                bold = make(wide)
                # (a slashed round as its round: by weight, ring and slash apart)
                if g.name in rounder_ones or (g.name not in by_weight and g.name not in SLASHED
                                              and slit(bold, regular[g.name], regular)):
                    # parts close to each other (x's inner serifs) closed to a
                    # slit: the rounder emboldening, which leaves them apart,
                    # where it has fewer faults (a thin arch springing from a
                    # thick stem, the italic n's, is a narrow crotch either way)
                    def rounder(w, sc=sc):
                        # smooth nodes kept smooth in the Bold (φ); the Bold
                        # Italic's rounder letters not yet reviewed so
                        return rezone(embolden_simple(w, AX * sc, AY, weighted=True, keep_smooth=not italic, thin=THIN * sc,
                                                      thick=THICK * sc), AY)

                    alt = rounder(wide)
                    if g.name in rounder_ones or faults(alt, regular) < faults(bold, regular):
                        make, bold = rounder, alt
                        simple.append(g.name)
                bold, n = part_serifs(wide, bold, make)
                if n:
                    parted.append(g.name)
                elif not italic:
                    bold, n = keep_gaps(wide, bold, make)
                    if n:
                        gapped.append(g.name)
                refit = (italic_counter if italic else oval) if g.name in (ITALIC_OVALS if italic else OVALS) else None
                if refit:
                    bold = refit(wide, bold)
                if italic and g.name in italic_inside.RUNS:
                    bold = inside_from(wide, bold, g.name)
                if g.name in SLASHED:
                    ring = RecordingPen()
                    contours_only(regular[SLASHED[g.name]]).replay(
                        TransformPen(TransformPen(ring, (KX, 0, 0, 1, 0, 0)), up))
                    round_ = SLASHED[g.name]
                    bold = slashed(wide, ring, make,
                                   (italic_counter if italic else oval) if round_ in (ITALIC_OVALS if italic else OVALS) else None,
                                   functools.partial(make, strokes=False))
                # each side's ink grew by the weight of the stroke there, not
                # as the earlier emboldening grew it (every side AX / 2, its
                # convex corners up to twice that: a serif's tip): the side
                # space set after this loop so that the outermost ink stands
                # where that emboldening put it, the spacing and kerning tuned
                # on it kept (N's hairline sides would gain AX / 2 of white,
                # the italic H's shorter serifs 23 units a side)
                ref = bridge(rezone(embolden(wide, AX, AY), AY))
                if ((g.name in rounder_ones and (italic or g.name not in BOLD_REFERENCE_BY_WEIGHT))
                        or (g.name in (ITALIC_REFERENCE_ROUNDER if italic else BOLD_REFERENCE_ROUNDER))
                        or (g.name not in by_weight and slit(ref, regular[g.name], regular))):
                    ref = rezone(embolden_simple(wide, AX, AY), AY)
                # judged optically (the white beside the ink across the band,
                # as the figures are spaced): a thin stroke end that no longer
                # grows (the italic f's bar, r's arm, s's and e's terminals)
                # leaves white even where the outermost ink stays
                d = optical_fit(bold_rec(ref), bold_rec(bold), band_height(regular, g.name))
                if (italic and g.name not in ITALIC_BOLD_BY_POINTS and g.name not in simple
                        and g.name not in unstroked):
                    # by strokes spaced as by weight (the stems stand where it
                    # put them): fitted to the stroked letter's own white, the
                    # thinner entries and exits drew the letters some 23 units
                    # closer, minimum blacker (2026-10-28)
                    weighted = bridge(rezone(embolden_by_weight(wide, AX * sc, AY, THIN * sc, THICK * sc,
                                                                keep_bends=g.name not in fit_as_is), AY))
                    d = optical_fit(bold_rec(ref), bold_rec(weighted), band_height(regular, g.name))
                    # but never closer than by weight: where the strokes put
                    # ink further out (the rounds, 5-9 % heavier, gained
                    # outward too: O O 0.75 of H H, references 0.87-0.95,
                    # 2026-11-05), that side gets it back; thinner ends,
                    # which leave white, keep the by-weight side. Added with
                    # the other side bearings once the letters made of these
                    # are drawn: the recipes cut and attach at fixed points of
                    # their base's frame (Ƈ's hook moved 9 units onto C)
                    if d and STROKE_OUT and is_letter(g.name):
                        out = optical_fit(bold_rec(weighted), bold_rec(bold), band_height(regular, g.name))
                        out = out and tuple(b if b >= STROKE_OUT_MIN else 0 for b in out)
                        if out and any(out):
                            stroke_out[g.name] = out
                if d:
                    if italic and g.name in ITALIC_FIT_CORRECTIONS:
                        adjustment = ITALIC_FIT_CORRECTIONS[g.name]
                        d = tuple(a + b for a, b in zip(d, adjustment))
                    fit[g.name] = d
                moved = ufoLib2.objects.Glyph()
                # the Italic's slanted letters (its derived ones, sloped
                # romans, small-cap drafts) split at their extremes there:
                # again here, where emboldened upright they move off them
                # (Old Standard's own, and the repairs matching exact
                # points, as they come)
                split = (italic and g.name not in POINT_REPAIRS and regular[g.name].lib.get(SOURCE_KEY)
                         in ("derived", "sloped roman", "small cap draft"))
                slant_back(bold, moved.getPen(), [(1, 0, 0, 1, AX / 2, 0), down], split)
                redraw(g, moved)
        if not is_mark:
            # the Regular's offsets, before any is changed below
            bases = [(c.baseGlyph, c.transformation[4], c.transformation[5])
                     for c in g.components if c.baseGlyph not in marks]
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                if c.baseGlyph in marks:
                    # the mark moves as the point it hangs on moves: the
                    # anchor of the base letter it sits on (nearest to it)
                    x, x_bold = attach_point(regular, c, bases, centre)
                    dx = dx + x_bold - x
                else:
                    dx = tx_offset(dx, dy)
                c.transformation = (xx, xy, yx, yy, round(dx), dy)
            for a in g.anchors:
                a.x = round(tx(a.x, a.y)) + nudge.get((g.name, a.name), 0)
            room = [(b, dx) for b, dx, _ in bases if dx]
            if len(bases) == 1 and room and g.width == regular[room[0][0]].width + room[0][1]:
                # a capital given room on its left for its accent (Ἤ; less
                # than none in the italic's Ἀ): as wide as the base plus that
                # room, rounded as the positioning rule is
                b, dx = room[0]
                g.width = round(regular[b].width * KX + AX) + round(dx * KX)
            elif g.width:
                g.width = round(g.width * KX + AX)

    # the side space emboldening by weight did not take (composites and
    # aliases carried along, their marks with them); a composite of one
    # letter placed anywhere (Έ: Ε given room for its accent) changes as
    # its letter does, as the decomposed form will (NFC and NFD alike)
    grown = True
    while grown:
        grown = False
        for g in font:
            if g.name in fit or g.contours or not g.components:
                continue
            letters = [c.baseGlyph for c in g.components if c.baseGlyph not in marks]
            if len(letters) == 1 and letters[0] in fit:
                fit[g.name] = fit[letters[0]]
                grown = True
    # a slashed round spaced as its round (the Regular's Ø is as wide as O,
    # its ring where O's is): the slash is not fitted
    for name, ring in SLASHED.items():
        fit[name] = fit.get(ring, (0, 0))
    sidebearings(font, {n: d for n, d in fit.items() if d != (0, 0)})
    if italic:
        from italic_contours import finish_bases

        finish_bases(font)
        # (r's shoulders not rounded after: the by-weight r's stepped arch
        # and return, the stroked r has neither)
    else:
        from r_hook import fair_bold_stem

        fair_bold_stem(font, bold=True)  # (the font still named Regular)
        from stem_handles import fair

        fair(font, bold=True)  # curves into a stem kept off its edge (n m u J Œ ...)
    whole = {}
    restore(kept, font, spaced=True)
    # (Ⱳ by strokes keeps its W; joined to it, the curl's join tangled)
    followed = follow_bases(regular, font, italic, whole=whole,
                            skip=set(ITALIC_BOLD_UNJOINED if italic else ()) | set(kept))
    followed += attached_small(regular, font, italic)
    followed += rederive(regular, font, italic, whole)
    restore(kept, font, spaced=True)
    if italic:
        # the joins the Italic faired, faired again (emboldened whole or
        # made again by the recipe)
        from derive import fair_joins
        from make_italic import ITALIC_JOINS

        cmap = {g.unicode: g.name for g in font if g.unicode is not None}
        for ch, band in {**ITALIC_JOINS, **ITALIC_BOLD_JOINS}.items():
            if ord(ch) in cmap and cmap[ord(ch)] not in kept:
                fair_joins(font[cmap[ord(ch)]], *band)
    font.lib[WHOLE_KEY] = {n: why for n, why in sorted(whole.items()) if n not in followed}

    font.kerning = {pair: round(v * KX) for pair, v in font.kerning.items()}
    if italic:
        font.kerning.update(ITALIC_BOLD_KERNING)
    else:
        font.kerning.update(BOLD_KERNING)
    # hand-set positioning (room for the accents of Greek capitals, ...):
    # horizontal placement and advance scale with the outlines
    font.features.text = re.sub(
        r"<(-?\d+) (-?\d+) (-?\d+) (-?\d+)>",
        lambda m: f"<{round(int(m[1]) * KX)} {m[2]} {round(int(m[3]) * KX)} {m[4]}>",
        font.features.text)

    info = font.info
    info.styleName = "Bold Italic" if italic else "Bold"
    info.styleMapStyleName = "bold italic" if italic else "bold"
    info.openTypeOS2WeightClass = 700
    info.postscriptFontName = "MyiaDidot-BoldItalic" if italic else "MyiaDidot-Bold"
    info.postscriptFullName = "Myia Didot Bold Italic" if italic else "Myia Didot Bold"
    # USE_TYPO_METRICS (bit 7) kept, as in the Regular: without it Word spaces
    # the Bold's lines by the win metrics, 11% looser; ufo2ft sets the
    # bold, italic and regular bits from styleMapStyleName
    info.openTypeOS2Selection = list(info.openTypeOS2Selection or [])

    # the dots round again, as the source style's (emboldening widens them
    # three times as much as it heightens them); before y's dot below is
    # placed and the composites and recipes take them
    from bold_dots import finish as round_dots

    round_dots(font)
    if italic:
        from y_dot import y_dot_anchor

        y_dot_anchor(font)
    log = []
    stack_anchors(font, log)
    bold_builder = Builder(font)
    rebuilt = 0
    for name in sorted(rule_made - set(kept)):
        g = font[name]
        r = bold_builder.recipe(g.unicode)
        r.name = name
        lib = dict(g.lib)
        del font[name]
        bold_builder.write(r)
        font[name].lib.update(lib)
        rebuilt += 1
    # letters drawn with their accent in one outline (Ť, Ǫ): in the Bold their
    # accent would be thickened like a letter; made from base and mark like
    # the decomposed text, unless the Regular already renders them apart
    exceptions = {line.split()[0] for line in (ROOT / "tests/data/nfd-exceptions.txt").read_text().splitlines()
                  if line.startswith("U+")}
    outlined = 0
    for g in list(font):
        if g.unicode is None or not g.contours or g.components or f"U+{g.unicode:04X}" in exceptions:
            continue
        if g.name in SPECIAL or g.name in kept:  # upstream's deliberate designs (Ǻ), ours (drawn.py)
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = bold_builder.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = g.name, dict(g.lib)
        del font[g.name]
        bold_builder.write(r)
        font[r.name].lib.update(lib)
        outlined += 1
    # what emboldening leaves: counters closed to pinholes, outlines crossing
    # themselves (glyph_lint)
    cleaned = fix(font)
    greek_cut = BOLD_ITALIC_CUT_GREEK - ITALIC_LOOSER if italic else BOLD_CUT_GREEK
    cut = BOLD_ITALIC_CUT if italic else BOLD_CUT
    respace(font, classifier(font, cut, greek_cut))
    respace(font, lambda n: BOLD_FIGURE_CUT if n in FIGURE_NAMES else 0)
    tabular_figures(font)
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)
    # a composite follows its base (sidebearings), as the letters made of one;
    # also one set off for its accent (Έ Ἐ Ῥ: the letter at an offset, the
    # mark before it), else it would stand narrower than its NFD
    if italic and STROKE_OUT:
        # the capital rounds' white beyond what the strokes gave back (2026-11-08)
        for n, side in ITALIC_CAPITAL_ROUNDS.items():
            stroke_out[n] = tuple(a + b for a, b in zip(stroke_out.get(n, (0, 0)), side))
    stroke_out = {n: v for n, v in stroke_out.items() if n in font and not font[n].components}
    grown = True
    while grown:
        grown = False
        for g in font:
            if g.name in stroke_out or g.contours or not g.components:
                continue
            bases = [c.baseGlyph for c in g.components if c.baseGlyph in stroke_out]
            if len(bases) == 1 and all(c.baseGlyph in stroke_out or c.baseGlyph in marks for c in g.components):
                stroke_out[g.name] = stroke_out[bases[0]]
                grown = True
    if STROKE_OUT_LOG is not None:
        Path(os.environ["MYIA_STROKE_OUT_LOG"]).write_text("".join(f"{n} {a} {b}\n" for n, (a, b) in stroke_out.items()))
    sidebearings(font, {n: tuple(a + b for a, b in zip(extra.get(n, (0, 0)), stroke_out.get(n, (0, 0))))
                        for n in set(extra) | set(stroke_out)})
    done = regular.lib.get(CUT_KEY, {"cut": 0, "greekLower": 0})
    font.lib[CUT_KEY] = {"cut": round(done["cut"] * KX) + cut,
                         "greekLower": round(done["greekLower"] * KX) + greek_cut}
    case_forms.make(font)  # punctuation raised onto the capitals (case), on the final widths
    if italic:
        from cyrillic_signs import redraw as redraw_cyrillic_signs
        from italic_contours import finish as finish_contours

        redraw_cyrillic_signs(font)
        finish_contours(font)
        # Serbian ѓ: its acute stacked over ī's bar as this style's ḗ,
        # rebuilt from anchors above, stacks it (carried along from the
        # Italic, it kept the Italic's step)
        from make_italic import serbian_bars, serbian_gje

        if "uni0453.loclSRB" in font and "uni0453.loclSRB" not in kept:
            serbian_gje(font)
        # п т: their bars over и ш as this style's ū has its own
        if not {"uni043F.loclSRB", "uni0442.loclSRB"} & set(kept):
            serbian_bars(font)
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.bold), separate_stacks=True, kept=kept)
    if parted:
        print("  serifs kept apart:", " ".join(parted))
    if gapped:
        print("  serif gaps kept in proportion:", " ".join(gapped))
    if unstroked:
        print("  emboldened by weight (by strokes failed):", " ".join(sorted(set(unstroked))))
    if simple:
        print("  emboldened the rounder way (embolden_simple; a slit otherwise):", " ".join(simple))
    print(f"{args.bold}: {len(font)} glyphs, {rebuilt} composites rebuilt from anchors, "
          f"{outlined} outlined letters made from base and mark, {len(followed)} derived letters "
          f"made of their Bold base, {len(cleaned)} cleaned")


if __name__ == "__main__":
    main()
