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
import case_forms
import kern_clear
from built_from import KEY as BUILT_KEY
from composites import SPECIAL, STACK_GAP_LC, Builder, stack_anchors
from derive import embolden, embolden_by_weight, embolden_simple, rezone
from glyph_lint import fix
from respace import CUT_KEY, classifier, respace, sidebearings
from space_figures import space as space_figures
from stroke_bold import SLIVER, emboldened

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
# thickens: Libre Bodoni's quarter, hairlines 23 -> 30 per 1000 (the
# person's choice, 2026-10-28; Bodoni Moda's gain nothing)
ITALIC_HAIR = 12
JOBS = 6  # processes at most (the project's limit)
# Bold Italic letters gaining more than their strokes give (ITALIC_AX and
# ITALIC_HAIR times this): z, its top and bottom waves shallow, gains little
# across and near the zones nothing up and down; still light beside n
# (the person, 2026-10-28)
ITALIC_BOLD_HEAVIER = {"z": 1.15}
# Bold Italic derived letters by strokes not joined to their base after
# (follow_bases): the same Italic strokes give the same base, the join
# tangles where they part
ITALIC_BOLD_UNJOINED = {"uni2C72": "Ⱳ: the curl's join tangled (53 nodes)"}
# Bold Italic letters still emboldened by weight: a repair after matches
# that outline's points (to redo on the stroked outline)
ITALIC_BOLD_BY_POINTS = {
    "dollar": "dollar_drawing.py's waist and ball entrances",
    "uni2135": "ℵ: aleph.py's return and join repairs",
    "trademark": "™: symbol_joins.py's shoulder and stem repair",
}
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
    "uni027E": "ɾ: a stub of the foot serif at the cut",
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
    "uni026E": "ɮ: ʒ placed by the Regular's numbers, apart from l's stem",
    "uni027A": "ɺ: l's stem at the Regular's width, a step where it meets ɹ's",
    "uni0432.loclBGR": "Bulgarian в: a ledge where β's loop meets the stem",
}
# ... and those made again though they differ from the emboldened letter
# more than rederive allows: the difference is the point (reviewed)
BOLD_REBUILD = {
    "uni0290": "ʐ: the foot at the Bold's weight; emboldened whole it was much too fat",
    "uni0260": "ɠ: the hook at the Bold's weight overhangs 5 % further than emboldened (derive.SPACING)",
    "uni0291": "ʑ: its own recipe (BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni0255": "ɕ: its own recipe (BOLD_RECIPES); emboldened, the loop's counter closed",
    "uni025E": "ɞ: its own recipe (BOLD_RECIPES); emboldened, the junction swelled and the counters closed",
}
ITALIC_BOLD_REBUILD = {
    # the slashed letters: the slash drawn on the stroked base at the Bold
    # Italic's weight (emboldened whole, it left a slit by the diagonal it
    # crosses and redrew the brackets beside it: Ⱥ; the person, 2026-10-28)
    "uni023A": "Ⱥ: the slash on the Bold Italic's A", "uni2C65": "ⱥ: the slash on the Bold Italic's a",
    "uni023B": "Ȼ: the slash on the Bold Italic's C", "uni023C": "ȼ: the slash on the Bold Italic's c",
    "uni023E": "Ⱦ: the slash on the Bold Italic's T", "uni2C65.sc": "ⱥ.sc: the slash on a.sc",
    "uni023C.sc": "ȼ.sc: the slash on c.sc", "uni2C66.sc": "ⱦ.sc: the slash on t.sc",
    # and the middle tildes, at the slashes' weight (the person, 2026-10-28:
    # emboldened whole the tilde was heavier than the slashes, and ᵭ's upper
    # counter, small and tight, came out a triangle)
    **{name: f"{ch}: the tilde on the Bold Italic's {base}" for name, ch, base in (
        ("uni026B", "ɫ", "l"), ("uni2C62", "Ɫ", "L"), ("uni1D6C", "ᵬ", "b"), ("uni1D6D", "ᵭ", "d"),
        ("uni1D6E", "ᵮ", "f"), ("uni1D6F", "ᵯ", "m"), ("uni1D70", "ᵰ", "n"), ("uni1D71", "ᵱ", "p"),
        ("uni1D72", "ᵲ", "r"), ("uni1D73", "ᵳ", "ɾ"), ("uni1D74", "ᵴ", "s"), ("uni1D75", "ᵵ", "t"),
        ("uni1D76", "ᵶ", "z"), ("uni026B.sc", "ɫ.sc", "l.sc"))},
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
    "uni0188.sc": "ƈ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0199.sc": "ƙ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01A5.sc": "ƥ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01AD.sc": "ƭ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni01B4.sc": "ƴ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0260.sc": "ɠ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni0266.sc": "ɦ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni028B.sc": "ʋ.sc: made again from the Bold Italic's capital (derive.py's recipe); emboldened from the Italic's draft, its curl closed on the ball",
    "uni049A": "Қ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the curl notched",
    "uni0496": "Җ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the ball ran into the descender",
    "uni0497": "җ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, a stub at the descender",
    "uni049B": "қ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, crumbs of the cut at the descender",
    "uni04A3": "ң: emboldened, a pinhole where the descender's curl meets its stroke",
    "uni2C64": "Ɽ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni01AE": "Ʈ: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni027D.sc": "ɽ.sc: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
    "uni0288.sc": "ʈ.sc: its own recipe (ITALIC_BOLD_RECIPES); emboldened, the tail left of the stem and heavier",
}
# recipes drawn at the Bold's weight (in the Bold Italic, in its upright
# frame), where the source's recipe scaled up does not fit (a hook's or a
# loop's counter closes, its turn too tight for a stroke twice as heavy):
# used as given, nothing scaled
BOLD_RECIPES = {
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
}
# the Bold Italic's curls over the top (ITALIC_BOLD_RECIPES): radii, turn and ball
CURL_CAP = {"r": (205, 185), "sweep": 190, "ball": 105}
CURL_LOW = {"r": (185, 165), "sweep": 190, "ball": 90}
ITALIC_BOLD_RECIPES = {
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
    # Ƈ Ɠ: the Italic's, the stroke and hook at this weight
    **{ch: ("attach", base, ("c", [(x - 50, 1330, 10000, 10000)],
                             [("line", ((x, 1320), (x, 1500), 53), (0, 0), (1, 1, 0, 0)),
                              ("curl", {"at": ("pt", x, 1500, 53), "dir": 90, "turn": "cw", "r": (165, 150),
                                        "sweep": 200, "ball": 85, "t": (53, 45), "lead": 10}, (0, 0), (1, 1, 0, 0))]))
       for ch, base, x in (("Ƈ", "C", 1090), ("Ɠ", "G", 1139))},
    # Ƭ: the Italic's, its strokes at this weight (as rederive scales them)
    # and its ball as large as the curl takes with no notch (80-90 at 180-200
    # degrees; the case's, 96, notched it): the Italic's smaller one (65)
    # scaled up would close the curl
    "Ƭ": ("attach", "T", ("c", [(-10000, 800, 420, 10000)],
                          [("curl", {"at": ("pt", 420, 1398, 92), "dir": 180, "turn": "ccw",
                                     "r": (135, 125), "sweep": 190, "ball": 90, "t": (133, 92),
                                     "lead": 10, "cuts": [(420, 1300, 10000, 10000)]}, (0, 0), (1, 1, 0, 0))])),
    # Ƙ Ƴ: the arm cut below its flare into the serif (its own width there),
    # running on in its own direction; Ʋ: U's right stem
    "Ƙ": ("curl", "K", ("c", [(870, 1130, 10000, 10000)],  # (at 1150 a step, ƙ.sc's ledges)
                        {"at": ("y", 1130, "last"), "dir": 51.6, "turn": "cw", **CURL_CAP, "t": (132, 67)})),
    "Ʋ": ("curl", "U", ("c", [(950, 1200, 10000, 10000)],
                        {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", **CURL_CAP, "t": (139, 59)})),
    "Ƴ": ("curl", "Y", ("c", [(800, 1100, 10000, 10000)],
                        {"at": ("y", 1100, "last"), "dir": 68.5, "turn": "cw", **CURL_CAP, "t": (103, 59)})),
    # ƴ ʋ: the thick right stroke (246, 251) curling over; it ends upright,
    # as thick, so its ball is half that, flush with the curl's end (90 left
    # 60 units of the end's face standing beside it)
    "ƴ": ("curl", "y", ("x", [(705, 760, 10000, 10000)],
                        {"at": ("y", 760, "last"), "dir": 90, "turn": "cw", **CURL_LOW, "ball": 124,
                         "t": (246, 62)})),
    "ʋ": ("curl", "u", ("x", [(705, 700, 10000, 10000)],
                        {"at": ("y", 700, "last"), "dir": 90, "turn": "ccw", **CURL_LOW, "ball": 126,
                         "t": (251, 62)})),
    # ⱳ: the Italic's, on the Bold Italic's arm, cut below where it flares
    # (1312-1404 at 600) and narrowing to the curl's stroke (a straight
    # stroke at the curl's width stepped 36 units aside of the arm at 645)
    "ⱳ": ("attach", "w", ("x", [(1000, 600, 10000, 10000)],
                          [("poly", [(1314, 595), (1405, 595), (1378, 770), (1298, 770)], (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 1338, 770, 80), "dir": 92, "turn": "cw", "r": (165, 150),
                                     "sweep": 200, "ball": 80, "t": (80, 53), "lead": 6}, (0, 0), (1, 1, 0, 0))])),
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
    "җ": ("attach", "uni0436", ("x", [(1025, -10000, 10000, 200), (1440, -10000, 10000, 450)],
                                [("line", ((1140, 210), (1152, -150), 215), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 1152, -150, 215), "dir": 272, "turn": "cw", "r": (150, 130),
                                           "sweep": 170, "ball": 103, "t": (215, 55)}, (0, 0), (1, 1, 0, 0))])),
    "қ": ("attach", "uni043A", ("x", [(630, -10000, 10000, 200), (960, -10000, 10000, 450)],
                                [("line", ((765, 210), (771, -150), 255), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 771, -150, 255), "dir": 270, "turn": "cw", "r": (170, 145),
                                           "sweep": 170, "ball": 122, "t": (255, 55)}, (0, 0), (1, 1, 0, 0))])),
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
    "Ɽ": ("attach", "R", ("c", [(-10000, -10000, 950, 120)],
                          [("line", ((419, 160), (419, -150), 290), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 419, -150, 290), "dir": 270, "turn": "ccw", "r": (195, 170),
                                     "sweep": 170, "ball": 145, "t": (290, 60)}, (0, 0), (1, 1, 0, 0))])),
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
    "uni027E": "ɾ: a stub of the foot serif at the cut",
    "uni044E.loclBGR": "Bulgarian ю: a spur of ю's entry stroke left under the cut",
    "uni2C66": "ⱦ: the slash at the Regular's thickness, too light",
    "uni026E": "ɮ: a notch where l's stem meets ʒ",
    "uni0270": "ɰ: a step on the last leg at the cut",
    "uni0249": "ɉ: the bar ends at the stem, no right arm for j_bar.py to extend",
    "uni0294": "ʔ: the Italic's cut, placed by number, notches the heavier stroke and leaves a sliver",
    "uni0268": "ɨ: Old Standard's own ɨ (its dot not i's); the recipe's i with a bar is another letter",
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
# ("a bit narrow", the person, 2026-10-28): ITALIC_LOOSER units less cut a
# side, its Greek lowercase alike (the Greek pairs are judged against n n)
ITALIC_LOOSER = 10
BOLD_ITALIC_CUT = BOLD_CUT - ITALIC_LOOSER
# the figures, which respace.py leaves alone, are tighter too: emboldened
# they stand looser than the Bold's letters (1.08 of their side space, where
# bold text faces have 0.8-1.0); one cut for all keeps them tabular, and the
# figure space and dash keep their width
BOLD_FIGURE_CUT = 28
FIGURE_NAMES = {f"{n}{s}" for n in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
                for s in ("", "oldstyle")} | {"uni2007", "figuredash"}
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
                     "uni04AF": (-45, 0), "uni01B4": (0, 50)}
# Pair-level corrections measured after the Bold's global kerning scale.
BOLD_KERNING = {
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
                       "uni01A5": (-60, 0), "uni0497": (0, -50), "uni04B6": (0, -45)}
# Joining the light belts changes the temporary weighted shape's optical
# fit. Keep their established advances/anchors before rebuilding the belts
# on this style's final base letters.
ITALIC_FIT_CORRECTIONS = {"uni026C": (-3, 0), "uniA7AD": (-2, 0)}
# the horn on u right, so that its outer edge runs on from the stem's as in
# the Italic (the stem top 840-981, the horn there 883-984): the heavier
# stem's top reached 1089, the horn's edge 1044, a shelf beside it
ITALIC_ANCHOR_NUDGE = {("u", "Horn"): 45}
# Bold Italic optical-pair corrections from the pinned-reference spacing
# comparison (scripts/quality/pairs.py). Values are final Bold Italic kern
# values in font units; they are applied after the source kerning is scaled.
# Most pairs had no source pair adjustment. va overrides its inherited class
# pair; fr is made 33 units looser relative to the references' range.
ITALIC_BOLD_KERNING = {
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
    ("public.kern1.alpha", "delta"): 63,  # αδ (αθ keeps the Italic's, scaled; 0 before strokes)
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
    ("T", "h"): 237,
    ("g", "a"): 89,
    ("i", "f"): 75,
    ("G", "r"): 121,
    ("a", "f"): 66,
    ("a", "y"): 67,
    ("v", "a"): 50,
    ("u", "f"): 92,
    ("R", "e"): 39,
    ("f", "t"): -66,
}
# the horn on u a little left: where the Regular's sits, the Bold's heavier
# foot leaves a ledge beside the stem (glyph_lint)
ANCHOR_NUDGE = {("u", "Horn"): -10}
# closed rounds, outer oval and counter: emboldened by the weight of the
# stroke at each node, the counter's shoulders come out boxy on one diagonal
# and flat on the other (the Bold Italic o, an egg); refitted from the
# lighter style's own curves (oval); in the Bold only, the Bold Italic's
# are drawn with the Italic's curves (stroke_bold), and refitted to its
# area the counter's handles overshoot into cusps
OVALS = {"o", "O", "zero"}
# slashed rounds, drawn whole in the lighter style: emboldened whole, the
# ring swelled where the slash crosses it (Ø not O with a stroke through);
# the ring is the round's own, the slash emboldened apart (slashed)
SLASHED = {"Oslash": "O", "oslash": "o", "oslash.sc": "o.sc"}


def slashed(wide, ring, make, refit, bar):
    """wide (a slashed round) as its round emboldened as the round itself is
    (make, oval if refit) joined to its slash (what it has beyond ring, the
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
        whole = oval(ring, whole)
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
    path = pathops.Path()
    for c in src.contours:
        c.draw(path.getPen())

    def ink(p, box):
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
            pairs.append((ta, tb, (a[5] + b[4]) / 2, gap, band, min(a[5] - a[4], b[5] - b[4])))

    def bold_path(g):
        p = pathops.Path()
        for c in g.contours:
            c.draw(p.getPen())
        return pathops.simplify(p)

    def partly(p, mid, band):
        h = ink(p, (mid - 1, band[0], mid + 1, band[1])) / 2
        return 0.05 < h / (band[1] - band[0]) < 0.95

    bp = bold_path(bold)
    bad = [pr for pr in pairs if partly(bp, pr[2], pr[4])]
    if not bad:
        return bold, 0
    for s in range(PART_STEP, int(min(pr[5] for pr in bad)) - 20, PART_STEP):
        moved = ufoLib2.objects.Glyph()
        wide.replay(moved.getPen())
        for ta, tb, *_ in bad:
            for tips, dx in ((ta, -s), (tb, s)):
                for ci, i in tips:
                    # the point with its handles, so a smooth join stays smooth
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
        out = make(rec)
        op = bold_path(out)
        if all(ink(op, (mid - gap * PART_KEEP / 2, band[0], mid + gap * PART_KEEP / 2, band[1])) == 0
               for _, _, mid, gap, band, _ in bad):
            return out, len(bad)
    return bold, 0


def faults(g, font):
    """How many notches (a slit between parts that come close), slivers and
    twists (an outline crossing itself at a tight terminal) g's contours have."""
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
    ch = chr(font[name].unicode) if font[name].unicode else ""
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


def round_smoothly(P):
    """P's points rounded to whole units, a join that ran on (nearly)
    smoothly, under 3 degrees, not broken further: where rounding leaves
    it turning by more than a degree and more than it did, one of its
    handles moved a unit to bring it more in line (a 15-unit
    handle rounded turns up to 4 degrees), a level or upright one (at an
    extreme) kept so. Handles under 10 units are left as rounded: theirs
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
        best = None
        for side, k in enumerate((a, b)):
            if P[k].type:
                continue
            bulge = overshoot(k, (P[k].x, P[k].y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (P[k].x + dx, P[k].y + dy)
                    # an extreme's handle stays level or upright
                    if math.dist(q, node) < 10 or (P[k].x == p.x and q[0] != p.x) or (P[k].y == p.y and q[1] != p.y):
                        continue
                    t = turn(q, node, ends[1]) if side == 0 else turn(ends[0], node, q)
                    # nor bulging further past its ends (an extreme lost)
                    if t < least and overshoot(k, q) <= max(bulge, 2):
                        best, least = (k, q), t
        if best:
            k, q = best
            P[k].x, P[k].y = q


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


def write(font, path, smooth=True, separate_stacks=False, plain=()):
    """font finalized and saved to path, the person's acceptances of the
    style saved there before carried over (accepted.py)."""
    from accepted import acceptances, carry
    from ufo_io import save_font

    finalize(font, smooth=smooth, separate_stacks=separate_stacks, plain=plain)
    carry(acceptances(ufoLib2.Font.open(path)) if Path(path).exists() else {}, font)
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
            # aside, which parts the curves (rounded away on saving), else
            # the letter is left as emboldened
            for nudge in (0, (0, -0.25), (0, 0.25), (0.25, 0)):
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
        if not why.endswith(("cuts its base", "does not keep its whole base")) and name not in rebuild:
            continue
        own = ch in (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)
        if own:
            op, base, band = (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)[ch]
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

            if ch in ITALIC_JOINS:  # as the Italic's, before it is judged
                derive.fair_joins(new, *ITALIC_JOINS[ch])
            if op == "enlarge" and name.endswith(".sc"):
                small_cap_stems(up, new)
        drop_specks(new)
        fill_pinholes(new, up[name], up)
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
        if name in rebuild and faults <= 0:
            close, wide = True, False
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
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    kern_clear.undo(font)  # the source's loosened pairs: this style finds its own
    angle = -(regular.info.italicAngle or 0)
    SLANT = math.tan(math.radians(angle))
    italic = bool(angle)
    if italic:
        AX, THIN, THICK = ITALIC_AX, ITALIC_THIN, ITALIC_THICK
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
    simple = []  # emboldened the rounder way (a slit otherwise)
    from make_italic import POINT_REPAIRS, SOURCE_KEY

    # the Bold Italic's letters emboldened by their strokes, all at once in
    # a pool (each about half a second); a glyph's own outline is looked up,
    # another (part_serifs' shortened serifs) drawn when asked
    def strokes_job(name, w, sc):
        gain = sc * ITALIC_BOLD_HEAVIER.get(name, 1.0)
        return (name, w.value, (ITALIC_AX * gain, AY, ITALIC_THIN * sc, ITALIC_THICK * sc,
                                ITALIC_HAIR * gain, SLANT, SLIVER * sc * sc))

    stroked, unstroked = {}, []
    if italic:
        from concurrent.futures import ProcessPoolExecutor

        jobs = []
        for g in font:
            if g.contours and g.name not in marks and g.name not in ITALIC_BOLD_BY_POINTS:
                wide = RecordingPen()
                contours_only(g).replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                jobs.append(strokes_job(g.name, wide, small_scale if g.name in small else 1.0))
        with ProcessPoolExecutor(JOBS) as pool:
            done = dict(pool.map(emboldened, jobs, chunksize=8))
        stroked = {repr(job[1]): done[job[0]] for job in jobs}

    def by_strokes(w, sc, name):
        """w (name's) emboldened by its strokes, a ufoLib2 Glyph (None: failed)"""
        value = stroked[repr(w.value)] if repr(w.value) in stroked else emboldened(strokes_job(name, w, sc))[1]
        if value is None:
            return None
        glyph = ufoLib2.objects.Glyph()
        rec = RecordingPen()
        rec.value = value
        rec.replay(glyph.getPen())
        return glyph

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
                if g.name in OVALS and not italic:
                    bold = oval(wide, bold)
                if g.name in SLASHED:
                    ring = RecordingPen()
                    contours_only(regular[SLASHED[g.name]]).replay(
                        TransformPen(TransformPen(ring, (KX, 0, 0, 1, 0, 0)), up))
                    bold = slashed(wide, ring, make, SLASHED[g.name] in OVALS and not italic,
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
                    # closer, minimum blacker (the person, 2026-10-28)
                    weighted = bridge(rezone(embolden_by_weight(wide, AX * sc, AY, THIN * sc, THICK * sc,
                                                                keep_bends=g.name not in fit_as_is), AY))
                    d = optical_fit(bold_rec(ref), bold_rec(weighted), band_height(regular, g.name))
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

        fair_bold_stem(font)
    whole = {}
    # (Ⱳ by strokes keeps its W; joined to it, the curl's join tangled)
    followed = follow_bases(regular, font, italic, whole=whole, skip=ITALIC_BOLD_UNJOINED if italic else ())
    followed += attached_small(regular, font, italic)
    followed += rederive(regular, font, italic, whole)
    if italic:
        # the joins the Italic faired, faired again (emboldened whole or
        # made again by the recipe)
        from derive import fair_joins
        from make_italic import ITALIC_JOINS

        cmap = {g.unicode: g.name for g in font if g.unicode is not None}
        for ch, band in ITALIC_JOINS.items():
            if ord(ch) in cmap:
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

    if italic:
        from y_dot import y_dot_anchor

        y_dot_anchor(font)
    log = []
    stack_anchors(font, log)
    bold_builder = Builder(font)
    rebuilt = 0
    for name in sorted(rule_made):
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
        if g.name in SPECIAL:  # upstream's deliberate designs stay as drawn (Ǻ)
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
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)
    sidebearings(font, extra)
    done = regular.lib.get(CUT_KEY, {"cut": 0, "greekLower": 0})
    font.lib[CUT_KEY] = {"cut": round(done["cut"] * KX) + cut,
                         "greekLower": round(done["greekLower"] * KX) + greek_cut}
    case_forms.make(font)  # punctuation raised onto the capitals (case), on the final widths
    if italic:
        from cyrillic_signs import redraw as redraw_cyrillic_signs
        from italic_contours import finish as finish_contours

        redraw_cyrillic_signs(font)
        finish_contours(font)
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.bold), separate_stacks=True)
    if parted:
        print("  serifs kept apart:", " ".join(parted))
    if unstroked:
        print("  emboldened by weight (by strokes failed):", " ".join(sorted(set(unstroked))))
    if simple:
        print("  emboldened the rounder way (embolden_simple; a slit otherwise):", " ".join(simple))
    print(f"{args.bold}: {len(font)} glyphs, {rebuilt} composites rebuilt from anchors, "
          f"{outlined} outlined letters made from base and mark, {len(followed)} derived letters "
          f"made of their Bold base, {len(cleaned)} cleaned")


if __name__ == "__main__":
    main()
