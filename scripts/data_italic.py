"""The Italic's tables and numbers (make_italic.py): its recipes, small
caps, joins, kerning, side bearings and anchors, the weights and cuts
it is made with, and the two constructors its recipes are written with.

Data only: make_italic imports every name from here and re-exports it,
so that make_italic.NAME goes on working. This module imports only
other data modules, italic_geometry and the standard library
(tests/test_data_modules.py).
"""

import math

from data_regular import BIG
from italic_geometry import SLANT

KX = 1.98  # across: between the x-height (1.939) and cap-height (2.014) scales

# Old Standard's strokes as they are, scaled (AX, AY across and up: none),
# their thick upright strokes made WEIGHT heavier as they are taken
# (weight_thick: hairlines and thin strokes as they are), the capitals
# CAP_WEIGHT. All made of them (derived letters, small caps, figures) is
# built from those weighted letters, as the Bold's are from the Bold's: a
# letter weighted on its own thickens at its junctions unlike its base. Thinned hairlines (-16, -10) and stems at the
# Regular's (+44) gave a contrast of 4.6 where italics have 3.1-4.2 and a
# colour twice as uneven as Old Standard's (letters of thick strokes, a b g q,
# and the capitals dark, hairline ones light), hard to read on a full page;
# chosen from full pages of variants (2026-10-21)
AX, AY = 0, 0
WEIGHT = 10
CAP_WEIGHT = 0
# what the recipes' drawn strokes (ITALIC_RECIPES' lines and curls, by
# number) were tuned at: Old Standard's strokes thinned by (-16, -10). They
# are drawn scaled to the strokes as they are now (recipe_scale), so a
# descender stays as heavy as the stem it continues
TUNED_AX, TUNED_AY = -16, -10

# off each side of a letter: Old Standard's spacing, scaled, is loose for
# its narrow letters (side space 0.180 of the x-height at a cut of 3, Bodoni
# Moda's and Libre Bodoni's italics 0.172 and 0.162); 13 more chosen
# from full pages cut 10, 13 and 16 more (2026-10-21)
ITALIC_CUT = 16
# the Greek lowercase tighter: Old Standard's Greek, so cut, stood 0.07 of an
# n n gap looser than the Italic's Latin against Greek references
# (scripts/quality/greek_pairs.py)
ITALIC_CUT_GREEK = ITALIC_CUT + 11

MADE_WITH = {"weight": [AX, AY, WEIGHT, CAP_WEIGHT], "cut": [ITALIC_CUT, ITALIC_CUT_GREEK]}

# signs Old Standard draws for mathematics, far larger than Myia's (+ is
# 1861 wide to the Regular's 1152), and its raised and lowered + − =: the
# Regular's are taken instead, upright
MATH_SIGNS = set(map(ord, "+<=>±×÷¬−≈≠≤≥⁺⁻⁼₊₋₌⊗"))
# Myia's own, sloped, though Old Standard has them: the guillemets
# (draft_symbols.py's chevrons; Old Standard's are small crescents)
# θ closed, not the cursive form Old Standard shares with ϑ: IPA needs the
# two apart; æ ɐ ᵃ the roman's, sloped, keeping the two-storey a apart from
# ɑ as in the roman (Old Standard's æ, of the one-storey a, read as œ; ɐ
# turned from it read as ɒ)
ROMAN_SIGNS = set(map(ord, "‹›θæɐᵃ"))
# unencoded glyphs taken the same way: a in IPA text (locl IPPH)
ROMAN_GLYPHS = {"a.ipa"}

LETTERS = {"₨": "Rs"}  # signs that are letters side by side
# ... closer by this much, joined: R's leg runs out into the ball of s
LETTER_JOIN = {"₨": 240}
NO_TRANSPLANT = {"ɞ", "ʝ", "ɕ", "ʂ", "ʑ", "ɚ", "ɝ", "ɮ", "Ɓ", "Ɗ", "Ƥ", "ɺ", "ɰ",
                 "Ƙ", "Ʋ", "Ƴ", "ƴ", "Ƭ", "Ɲ", "Ʈ", "ƥ", "ɖ", "ɗ", "ɭ", "Ɽ",
                 "ң", "ҷ", "қ", "җ", "Қ", "Җ", "ҳ", "ɧ", "ɱ", "ɳ", "ɽ", "ɻ", "Ƒ", "Ꞵ", "Ʝ", "ʄ", "ʋ", "ʈ", "Ɦ", "Ⱳ", "ⱳ.sc", "Ɠ", "ƈ", "ƃ", "ƛ", "ɹ", "Ƈ", "ⱳ", "ʐ", "г.loclSRB",
                 "ɽ.sc", "ʈ.sc", "ь.loclBGR", "ю.loclBGR", "ж.loclBGR", "ъ.loclBGR", "в.loclBGR"}  # its own recipe fits the Italic better
TRANSPLANT = set()  # other recipes better transplanted

# small caps left to FontForge's drafts of the Italic's capitals (as the
# others), not derive.py's recipes: a capital scaled down (ʛ from Ɠ) is
# heavier than the small caps beside it (ⱳ.sc not: drafted from the
# uncrossed Ⱳ, its narrow diagonals came out light, as w.sc's)
SC_DRAFTED = {"ɑ.sc", "ɂ.sc", "ʒ.sc", "ʊ.sc", "ʋ.sc", "ꞵ.sc", "ƭ.sc", "ƙ.sc",
              "ɲ.sc", "ʝ.sc", "ϗ.sc", "ƴ.sc", "ƈ.sc", "ɠ.sc", "ƥ.sc",
              # ƒ.sc: the Regular's hook recipe takes ȷ's tail, a swash here,
              # scaled to f.sc's stem a crescent under the letter before
              "ƒ.sc"}
# small caps the Italic makes from its own capitals where FontForge's
# draft was faulty, before derive.py's recipes (those made of them follow:
# ǥ.sc, ɢ): g.sc's counter ran straight down its left side into a corner
# (G's is round); ɦ.sc (ITALIC_RECIPES) notched where its hook met the stem
# s.sc n.sc є.sc ϟ.sc: as_capitals could not bring the draft's main stroke
# to its capital's weight (s.sc's spine 0.65 of h.sc against S's 0.99,
# n.sc's diagonal 0.63 against N's 0.84, є.sc 0.83 against Є's 1.07, ϟ.sc's
# bar 0.91; the weighting thickened their bowls and serifs, not that
# stroke): made from the capital, which has it, at the draft's side bearings
ITALIC_SC_RECIPES = [("g.sc", "enlarge", "G", ("O", "o.sc")),
                     ("s.sc", "enlarge", "S", ("O", "o.sc")),
                     ("n.sc", "enlarge", "N", ("O", "o.sc")),
                     ("є.sc", "enlarge", "Є", ("O", "o.sc")),
                     ("ϟ.sc", "enlarge", "Ϟ", ("O", "o.sc")),
                     # ѳ.sc: the draft's counters ran lumpy beside the bar
                     # (the Regular's wave bar's ends, 2026-11-09); Ѳ's are
                     # Old Standard's, round
                     ("ѳ.sc", "enlarge", "Ѳ", ("O", "o.sc"))]

# made from their capitals, s.sc's spine and n.sc's diagonal still stood
# light (0.81 and 0.69 of h.sc): enlarge's emboldening thickens strokes by
# their lean (a level stroke by the hairlines' amount), so their thick
# strokes are made heavier (level_gain) until the main stroke stands to
# h.sc's as the capital's to H's: s.sc's up and down (its spine near
# level), n.sc's sideways (its diagonal steep; up and down its top serif
# grew heavy and its vertex dropped)
SC_LEVEL_GAIN = {"s.sc": ("S", True), "n.sc": ("N", False)}
# of those, drafted all the same and remade at the draft's side bearings
# (its spacing and kerning kept), its anchors moved with its ink
SC_DRAFT_SIDES = {"s.sc", "n.sc", "uni0454.sc", "uni03DF.sc", "uni0473.sc"}
# the Italic's own letters already have the shape: Old Standard's g is ɡ,
# its h turned is ɥ (the Regular's is u and a descender, its h's serifs
# would turn)
def retroflex(x0, x1, y, w, r, ball, th, turn=0):
    """attach pieces: a stem w thick from (x0, y) down to (x1, -150), curling
    to the right there through 170 degrees on radii r, ending in a ball."""
    return [("line", ((x0, y), (x1, -150), w), (0, 0), (1, 1, 0, 0)),
            ("curl", {"at": ("pt", x1, -150, w), "dir": 270 + turn, "turn": "ccw", "r": r,
                      "sweep": 170, "ball": ball, "t": (w, th)}, (0, 0), (1, 1, 0, 0))]

def descender(x0, y0, x1, y1, w, d, r, th):
    """attach pieces: a stroke w thick from (x0, y0) to (x1, y1) (running on
    a little into the curl), curling to the left there through 170
    degrees on radii r, the ball as heavy as the stroke."""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    return [("line", ((x0, y0), (x1 + dx / n * 12, y1 + dy / n * 12), w), (0, 0), (1, 1, 0, 0)),
            ("curl", {"at": ("pt", x1, y1, w), "dir": d, "turn": "cw", "r": r, "sweep": 170,
                      "ball": max(36, round(w * 0.48)), "t": (w, th)}, (0, 0), (1, 1, 0, 0))]

# where a recipe's straight piece meets an italic stroke that leans or
# curves (ɰ ɱ ɳ: a leg running on into a descender; ⱳ: the arm into its
# curl), the join faired between these heights (derive.fair_joins): the
# piece is straight in the upright frame, the stroke is not, and the edges
# broke there by 5-20 degrees (seen in print)
# (ɱ's band up to 520, 2026-11-11: the outer edge's node where the m's
# shoulder runs into the descender stands at 500 and kept a corner of 4
# degrees, "a kind of kink" in the downstroke on the sheet)
ITALIC_JOINS = {"ɰ": (250, 350), "ɧ": (200, 300), "ɱ": (190, 520), "ɳ": (190, 460), "ⱳ": (590, 700)}
# those whose join runs on through the letter's own smooth node in the band
# (fair_joins' min_turn 0), up the stem's straight edge to its top: ɳ's
# did only because n had a kink of 1.3 degrees at that node (682,361);
# with n redrawn smooth there (2026-11-10) the curve ended at it, the
# whole turn of 10 degrees in its last 40 units
# ɱ's too (2026-11-11, with its band to 520): its inner edge bent at
# 1146,361 where m's leg ran into the descender ("a kind of kink" on the
# sheet); run through, one curve from 1094,153 to the leg's top at 1272,649,
# turning one way. (The spike of two nodes on one point at 1069,45, first
# blamed on this, is ȷ's, there with or without it: smooth_joins.ITALIC_JOINS.)
ITALIC_JOINS_THROUGH = {"ɳ", "ɱ"}
# corners rounded off where a descender's straight edge meets the curve of
# the letter it hangs from (round_corner: at that height, a curve tangent to
# both reaching that far either way): җ's descender leans 14 degrees, the
# back of ж's right c it meets rises at 2, a kink with a swelling above it
# (2026-11-08). Not fair_joins: one curve from the descender's
# foot to the c would bend the whole edge (as it thinned ⱳ's arm).
ITALIC_CORNERS = {"җ": (200, 120)}

# an edge run straight between two heights: from the rightmost on-curve
# point at the first (within 6 units) going down, to the second on the
# line below, one curve tangent at both ends (straighten_run). җ's inner
# edge left the crossbar leaning as the descender does, dropped upright down
# the c's lower inside, then leaned again: a kink at the cut in the Italic,
# a swelling above it in the Bold Italic (2026-11-08)
ITALIC_RUNS = {"җ": (417, 50)}

# the curls over the top end in a ball as the case draws them ("ball":
# None, derive.ball_for, 2026-10-27; the Bold Italic draws its own at its
# weight, data_bold_italic.ITALIC_BOLD_RECIPES); tails off a stem (retroflex,
# descender) keep a ball half their stroke, flush with the curl's end;
# Ⱳ keeps its number (its ball 50, the curl run on straight from W's arm)
# ɮ: how far right of l's stem its ʒ stands (ITALIC_RECIPES)
ZH_DX = 150
# the roman's own, sloped, not remade on the italic letter: ʌ turned from the
# italic v rounds its apex and reads as a (2026-11-01)
# Old Standard has it, but derive.py's recipe matches the IPA small capitals
# around it (Old Standard's ʀ stood lower and lighter)
# ɑ is the italic's one-storey a (Old Standard's ɑ is its α), ɒ that turned
OWN_RECIPE = {"ʀ", "ɑ"}
KEPT_SLOPED = {"ʌ", "ɐ", "ᵃ", "a.ipa"}
ITALIC_RECIPES = {"л.loclBGR": ("turn", "v", "x"),  # the rounded form ʌ had
                  # ɴ: n.sc's ink fitted from its vertex, 25 below the line
                  # (21 at ɴ's size), so its feet stand on it (from 0 they
                  # stood 23 above, 2026-11-05)
                  "ɴ": ("enlarge", "n.sc", ("o.sc", "o", -21, 884, "i.sc", "n")),
                  # ȼ.sc: c.sc at its capital's weight (as_capitals) is about
                  # 40 wider; at 0.8 of its box the slash's top met the
                  # terminal in a notch, at 0.78 it stands where it stood
                  "ȼ.sc": ("slash", "c.sc", ("s", "box", 0.25, -90, 0.78, 1130)),
                  # ᵶ: the tilde's right end, tapered (2026-11-09), stopped
                  # just short of the spine, a sliver of white between them
                  # (a notch once emboldened), and its left end touched the
                  # spine; both 60 longer they stand clear, visible, not in
                  # the stem (chosen 2026-11-09 from drafts at 0-80)
                  "ᵶ": ("midtilde", "z", ("x", None, None, 60, 60)),
                  "ɡ": ("alias", "g", None), "ɥ": ("turn", "h", "x"),
                  "ɑ": ("alias", "a", None),
                  # ₩: the bars from 20 to 20 past the uncrossed W's
                  # advance (redraw_w), as the Regular's across its W
                  "₩": ("lines", "W", ("c", 64, [(20, 528, 1807, 592), (20, 842, 1807, 906)])),
                  # ₿: the Regular's stubs (538 and 778, from 1300 and to 120)
                  # stood 65 units into the Italic B's counters under its
                  # thinner bars and by the stem's bracket: only outside
                  # the B, 30 into its bars, and nearer each other (116
                  # apart for 176; "closer, higher, leave the B-form as
                  # is", 2026-11-12)
                  "₿": ("lines", "B", ("c", 64, [(568, 1404, 632, 1634), (748, 1404, 812, 1634),
                                                  (568, -200, 632, 30), (748, -200, 812, 30)])),
                  # ⱳ.sc: w.sc (made of v.sc as W of V) with Ⱳ's curl at
                  # the small caps' 0.725, the cut between the middle serif
                  # and the right one (all of it); enlarged from that Ⱳ, its
                  # narrow diagonals thinned by the stem's amount (0.84 of
                  # its kind)
                  "ⱳ.sc": ("curl", "w.sc", ("c", [(940, 834, BIG, BIG)],
                                         {"at": ("y", 834, "last"), "dir": 79, "turn": "cw", "r": (87, 80),
                                          "sweep": 210, "ball": None, "t": (59, 30)})),
                  # ǥ: the single-storey g's bar across its stem below the
                  # baseline, above the hook, as in DejaVu (the roman's
                  # height crossed the tail, easy to miss)
                  "ǥ": ("bar", "g", ("x", -130, "all", (200, 70))),
                  # ɉ: the bar centred on the stem, its length as before
                  # (derive's bar stops at the ink, j's stem on the right:
                  # 169 left, 14 right; "not centred", 2026-11-05)
                  "ɉ": ("bar", "j", ("x", None, "all", (92, 92))),
                  # ₸'s line across the T's top bar, ₫'s under the bowl and
                  # stem (the Regular's numbers run past the narrower italics)
                  "₸": ("lines", "T", ("c", 64, [(118, 1498, 1205, 1562)])),
                  "₫": ("lines", "dcroat", ("x", 64, [(120, -330, 940, -266)])),
                  # f's hook brought down onto the x-height, on a foot serif
                  # (fishhook; as the Regular's, 2026-11-04)
                  "ɾ": ("fishhook", "f", ("r", (213, 0, 493, 50))),
                  # ɦ.sc: Ɦ made small, H's stems brought to h.sc's (by o.sc's
                  # round alone they came out 152 against h.sc's 194)
                  "ɦ.sc": ("enlarge", "uniA7AA", ("O", "o.sc", "H", "h.sc")),
                  "ɸ": ("stem", "o", None),  # o with a stem as heavy as l's through it
                  "ɯ": ("turn", "m", "x"),  # the turned m it is named after
                  # ɯ with its last stem running down into ɥ's descender
                  "ɰ": ("attach", "uni026F", ("x", [(1150, -BIG, BIG, 300), (1300, -BIG, BIG, 600)],
                                              [("uni0265", (700, -BIG, BIG, 300), (0, 0), (1, 1, 459, 0))], 1500)),
                  # the italic r turned (as Charis's), not the roman's drawn ɹ:
                  # its stem as light as the other italic stems
                  "ɹ": ("turn", "r", "x"),
                  # ɹ's stem to ascender height, l's top on it
                  "ɺ": ("attach", "uni0279", ("x", [(-BIG, 850, BIG, BIG)],
                                              [("l", (-BIG, 850, BIG, BIG), (0, 0), (1, 1, 268, 0))])),
                  # the clicks are letters: a sloped bar (the Italic's | is upright)
                  "ǀ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)], [])),
                  "ǁ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)],
                                                [("_clickbar", (-BIG, 0, BIG, BIG), (0, 0), (1, 1, 230, 0))])),
                  "ǂ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)],
                                                [("rect", (56, 560, 456, 612), (0, 0), (1, 1, 0, 0)),
                                                 ("rect", (56, 820, 456, 872), (0, 0), (1, 1, 0, 0))], 512)),
                  # the rhotic hook rising from the bowl's right side (at that height)
                  "ɚ": ("rhotic", "ə", 500), "ɝ": ("rhotic", "ɜ", 690),
                  # the italic ? (its stroke curls at the foot) turning down
                  # into a stem: ʕ ʡ ʢ follow
                  "ʔ": ("glottal", "question", None),
                  # ɜ closed on the left by the left half of o
                  "ɞ": ("attach", "ɜ", ("x", [(-BIG, 600, 400, BIG), (-BIG, -BIG, 400, 300)],
                                        [("o", (-BIG, -BIG, 440, BIG), (0, 0), (1, 1, -20, 0))])),
                  # c's bottom stroke runs on into a loop, an upright tail
                  # through it; s's turns down at the left and hooks right
                  "ɕ": ("attach", "c", ("x", [(560, -BIG, BIG, 400)],
                                        [("curl", {"at": ("pt", 550, 12, 50), "dir": 10, "turn": "ccw",
                                                   "r": (100, 130), "sweep": 270, "ball": 36, "t": (90, 50)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((433, 150), (433, -200), 90), (0, 0), (1, 1, 0, 0))])),
                  # z's bottom stroke runs on (its rising end cut away), thinning
                  # into a small loop at its end, an upright tail down through
                  # the loop's left side (as the Regular's)
                  "ʑ": ("attach", "z", ("x", [(600, -BIG, BIG, 400)],
                                        [("poly", [(560, -23), (600, -21), ((630, -18), (660, -14), (690, -12)),
                                                   (690, 52), ((660, 62), (630, 84), (600, 106)), (560, 106)],
                                          (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 680, 20, 50), "dir": 3, "turn": "ccw",
                                                   "r": (95, 115), "sweep": 270, "ball": 30, "t": (90, 50), "lead": 10},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((578, 140), (578, -200), 92), (0, 0), (1, 1, 0, 0))])),
                  # z's bottom stroke, where it turns up, turns down instead into a
                  # stem that hooks to the right (as the Regular's and Charis's ʐ),
                  # the stem 110 as tuned (0.85 of the weighted n), run up
                  # into the stroke so the inner corner is the two edges meeting
                  "ʐ": ("attach", "z", ("x", [(600, -BIG, BIG, 400)],
                                        [("curl", {"at": ("pt", 600, 35, 117), "dir": 0, "turn": "cw",
                                                   "r": (90, 90), "sweep": 90, "ball": 30, "t": (110, 117)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((690, -20), (690, -330), 110), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 690, -330, 110), "dir": 270, "turn": "ccw",
                                                   "r": (135, 95), "sweep": 150, "ball": 60, "t": (110, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # s's bottom stroke runs on to the left and hooks down and round
                  "ʂ": ("attach", "s", ("x", [(-BIG, -BIG, 405, 360)],
                                        [("curl", {"at": ("pt", 405, 1.5, 36), "dir": 172, "turn": "ccw",
                                                   "r": (120, 150), "sweep": 188, "ball": 40, "t": (80, 36),
                                                   "lead": 10, "cuts": [(405, -80, BIG, BIG)]}, (0, 0), (1, 1, 0, 0))])),
                  # the stroke across the tail higher, where the tail is
                  "ʝ": ("attach", "j", ("x", [], [("line", ((-20, -400), (580, -110), 50), (0, 0), (1, 1, 0, 0))])),
                  # l on a straight stem to the baseline, Old Standard's ʒ beside
                  # it (as the Regular's): its entry stroke cut, its top bar
                  # run on to the stem, its diagonal and bowl clear of it
                  "ɮ": ("attach", "l", ("x", [(-BIG, -BIG, BIG, 250), (300, -BIG, BIG, 600)],  # l's exit stroke too
                                        [("rect", (163, 0, 304, 260), (0, 0), (1, 1, 0, 0)),
                                         ("uni0292", (250, 0, BIG, BIG), (0, 0), (1, 1, ZH_DX, 0)),
                                         ("uni0292", (-BIG, -BIG, BIG, 0), (0, 0), (1, 1, ZH_DX, 0)),
                                         ("rect", (280, 720, 250 + ZH_DX + 20, 880), (0, 0), (1, 1, 0, 0)),
                                         # filling the notch where ʒ's diagonal meets its bowl
                                         ("line", ((393 + ZH_DX, 307), (452 + ZH_DX, 300), 14), (0, 0), (1, 1, 0, 0)),
                                         ("line", ((390 + ZH_DX, 300), (430 + ZH_DX, 300), 10), (0, 0), (1, 1, 0, 0))],
                                        950 + ZH_DX)),
                  # the stem rising through the top serif and curling over to the left
                  **{ch: ("curl", base, ("c", [(-BIG, 1300, 300, BIG)],
                                         {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                          "sweep": 200, "ball": None, "t": (166, 60)}))
                     for ch, base in (("Ɓ", "B"), ("Ɗ", "D"), ("Ƥ", "P"))},
                  # the arm or stem itself curling over at the top (its serif
                  # cut away), at its own weight
                  # Ƙ Ƴ Ʋ: curls 1.25 times what they were, as large as Ƈ Ɠ's
                  # (their balls growing with them; 2026-11-08)
                  "Ƙ": ("curl", "K", ("c", [(850, 1250, BIG, BIG)],
                                      {"at": ("y", 1250, "last"), "dir": 51, "turn": "cw", "r": (140, 120),
                                       "sweep": 210, "ball": None, "t": (89, 45)})),
                  "Ʋ": ("curl", "U", ("c", [(930, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", "r": (175, 150),
                                       "sweep": 200, "ball": None, "t": (64, 40)})),
                  "Ƴ": ("curl", "Y", ("c", [(780, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 62, "turn": "cw", "r": (140, 120),
                                       "sweep": 210, "ball": None, "t": (68, 40)})),
                  "ƴ": ("curl", "y", ("x", [(700, 760, BIG, BIG)],
                                      {"at": ("y", 760, "last"), "dir": 90, "turn": "cw", "r": (100, 90),
                                       "sweep": 200, "ball": None, "t": (116, 40)})),
                  # p's stem (its entry stroke cut away) rising and curling over
                  "ƥ": ("attach", "p", ("x", [(-BIG, 700, 400, BIG), (-BIG, 400, 270, BIG)],
                                        [("rect", (296, 650, 397, 1150), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 346.5, 1150, 101), "dir": 90, "turn": "cw",
                                                   "r": (150, 130), "sweep": 210, "ball": None, "t": (101, 45)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # the bar's left end (its serif cut away) curling down; the curl
                  # leaves the bar where it is as thin as the curl (it flares
                  # toward the serif), so they meet without a ledge
                  # (its ball less than the case's 86: that nearly filled the
                  # curl, its small cap's draft closed to a slit)
                  # the bar run on 220 units left at the curl's weight first: it
                  # stood 197 against the right arm's 648 (the T's own 377;
                  # 2026-11-06: short against the other styles'; at 0.8
                  # of it, as the Regular's 0.85, too long), now about 0.65
                  "Ƭ": ("attach", "T", ("c", [(-BIG, 800, 420, BIG)],
                                        [("line", ((440, 1398), (200, 1398), 62), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 200, 1398, 62), "dir": 180, "turn": "ccw",
                                                   "r": (135, 125), "sweep": 200, "ball": 65, "t": (90, 62),
                                                   "lead": 10, "cuts": [(200, 1300, BIG, BIG)]}, (0, 0), (1, 1, 0, 0))])),
                  # the top hairline rising from where its ball was into a hook
                  # to the right (as Charis and Libertinus)
                  "ƈ": ("attach", "c", ("x", [(540, 450, BIG, BIG), (470, 450, 545, 800)],
                                        [("line", ((515, 858), (560, 1100), 44), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 560, 1100, 44), "dir": 75, "turn": "cw",
                                                   "r": (110, 100), "sweep": 200, "ball": None, "t": (44, 34),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # b's stem without its flag serif, the bar its top run on to
                  # the right
                  "ƃ": ("attach", "b", ("x", [(-BIG, 1300, 173, BIG)],
                                        [("rect", (173, 1379, 720, 1435), (0, 0), (1, 1, 0, 0))])),
                  # λ whole, a bar drawn across its upper stroke (the Regular's,
                  # transplanted, cut the arch off the long stroke)
                  "ƛ": ("attach", "lambda", ("x", [], [("line", ((130, 1010), (610, 1285), 46), (0, 0), (1, 1, 0, 0))])),
                  # C's spur likewise (as Ɠ)
                  "Ƈ": ("attach", "C", ("c", [(1040, 1330, BIG, BIG)],
                                        [("line", ((1090, 1320), (1090, 1500), 36), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1090, 1500, 36), "dir": 90, "turn": "cw",
                                                   "r": (105, 95), "sweep": 210, "ball": None, "t": (36, 30),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # G's spur rising above the cap height into a hook to the right
                  # (as Charis and Libertinus), not curling back over the bowl
                  "Ɠ": ("attach", "G", ("c", [(1080, 1330, BIG, BIG)],
                                        [("line", ((1139, 1320), (1139, 1500), 36), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1139, 1500, 36), "dir": 90, "turn": "cw",
                                                   "r": (105, 95), "sweep": 210, "ball": None, "t": (36, 30),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # the stem (its foot serif cut away) running down into the hook
                  "Ɲ":("attach", "N", ("c", [(-BIG, -BIG, 700, 250)],
                                        [("line", ((363, 300), (363, -200), 63), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 363, -200, 63), "dir": 270, "turn": "cw",
                                                   "r": (100, 90), "sweep": 160, "ball": 45, "t": (63, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # (the ball half the stem, flush with the curl's end, as Ɽ's)
                  "Ʈ": ("attach", "T", ("c", [(-BIG, -BIG, BIG, 150)],
                                        retroflex(667.5, 667.5, 200, 165, (150, 125), 82, 50))),
                  # the stem (below its swell, without the exit stroke) going on
                  # below the baseline and curling right, as ɭ ɽ ʈ (the bowl kept
                  # joined)
                  "ɖ": ("attach", "d", ("x", [(700, -BIG, BIG, 200), (820, -BIG, BIG, 450)],
                                        retroflex(733, 733, 210, 114, (110, 100), 57, 40))),
                  "ɭ": ("attach", "l", ("x", [(-BIG, -BIG, BIG, 300), (300, -BIG, BIG, 600)],
                                        retroflex(234, 234, 350, 116, (110, 100), 45, 40))),
                  # the tail on the stem (its foot serif cut away), as ɽ's
                  "Ɽ": ("attach", "R", ("c", [(-BIG, -BIG, 800, 120)],
                                        retroflex(393, 393, 160, 166, (150, 125), 82, 50))),
                  "ɳ": ("attach", "n", ("x", [(700, -BIG, BIG, 200), (900, -BIG, BIG, 450)],
                                        retroflex(795, 795, 210, 112, (110, 100), 56, 40))),
                  "ɽ": ("attach", "r", ("x", [], retroflex(354.5, 354.5, 100, 119, (110, 100), 55, 40))),
                  # ɽ.sc ʈ.sc: the tail on the stem (its foot serif cut away),
                  # as Ɽ's and Ʈ's at the small caps' size: the hook recipe
                  # took the Italic's ȷ, a swash, and ran it out along the baseline
                  "ɽ.sc": ("attach", "r.sc", ("s", [(-BIG, -BIG, 690, 110)],
                                              retroflex(309.5, 309.5, 150, 174, (125, 105), 87, 45))),
                  "ʈ.sc": ("attach", "t.sc", ("s", [(-BIG, -BIG, BIG, 110)],
                                              retroflex(521.5, 521.5, 150, 174, (125, 105), 87, 45))),
                  "ɻ": ("attach", "uni0279", ("x", [(440, -BIG, BIG, 200), (560, 200, BIG, 400)],
                                              retroflex(502, 502, 250, 110, (120, 105), 55, 40))),
                  # the last stem or leg running on below the baseline (the
                  # exit stroke cut away) and curling to the left
                  "ң": ("attach", "uni043D", ("x", [(700, -BIG, BIG, 250), (950, -BIG, BIG, 450)],
                                              descender(802.5, 300, 802.5, -150, 119, 270, (105, 95), 40))),
                  "ҷ": ("attach", "uni0447", ("x", [(680, -BIG, BIG, 250), (950, -BIG, BIG, 450)],
                                              descender(761.5, 300, 761.5, -150, 117, 270, (105, 95), 40))),
                  "қ": ("attach", "uni043A", ("x", [(640, -BIG, BIG, 200), (900, -BIG, BIG, 450)],
                                              descender(730, 250, 735, -150, 125, 270, (105, 95), 40))),
                  # (ж 41 left of Old Standard's: mirror_zhe)
                  "җ": ("attach", "uni0436", ("x", [(959, -BIG, BIG, 200), (1309, -BIG, BIG, 450)],
                                              descender(1047, 210, 1059, -150, 112, 272, (100, 90), 40))),
                  # the capitals as the lowercase: the leg's exit stroke cut
                  # away, a descender in its place (not Ц's tail under it)
                  "Қ": ("attach", "uni041A", ("c", [(895, -BIG, BIG, 200), (1215, -BIG, BIG, 450)],
                                              descender(1001, 250, 1008, -150, 165, 270, (130, 115), 45))),
                  "Җ": ("attach", "uni0416", ("c", [(1480, -BIG, BIG, 200), (1820, -BIG, BIG, 450)],
                                              descender(1596, 250, 1603, -150, 182, 270, (130, 115), 45))),
                  "ҳ": ("attach", "uni0445", ("x", [(560, -BIG, BIG, 150), (900, -BIG, BIG, 350)],
                                              descender(612, 155, 810, -150, 58, 303, (90, 80), 34))),
                  # ȷ's descender on the last stem, as ɲ has it on the first: it
                  # thins as the italic stems do (cut in where the stem is as
                  # wide as ɲ's, below its swell; the exit stroke cleared)
                  # ɧ: ȷ's descender (its stem 144, centred at 405) on ɦ's leg
                  # where it is still whole (152 at 250, centred at 661), the
                  # exit stroke cut away: cut lower, where the leg thins into
                  # its exit, the hook was scaled to that and the leg pinched
                  "ɧ": ("attach", "uni0266", ("x", [(450, -BIG, BIG, 250), (800, -BIG, BIG, 450)],
                                              [("uni0237", (-BIG, -BIG, BIG, 260), (405, 250),
                                                (152 / 144, 1, 661, 250))])),
                  "ɱ": ("hook", "m", ("x", "down-left", "last", 200, 160, 400, [(1360, -BIG, BIG, 450)])),
                  # F's stem (its foot serif cut away) tapering into the hook
                  "Ƒ": ("attach", "F", ("c", [(-BIG, -BIG, BIG, 150)],
                                        [("poly", [(310, 150), (477, 150), (477, -150), (357, -150)], (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 417, -150, 120), "dir": 270, "turn": "cw",
                                                   "r": (130, 110), "sweep": 170, "ball": 58, "t": (120, 45)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # B's stem running on down (its foot serif cut away) to a serif of its own
                  "Ꞵ": ("attach", "B", ("c", [(-BIG, -BIG, 309, 110)],
                                        [("rect", (310, -480, 476, 40), (0, 0), (1, 1, 0, 0)),
                                         ("rect", (170, -480, 616, -428), (0, 0), (1, 1, 0, 0))])),
                  # J's stem straight down into a tail curling left, crossed
                  "Ʝ": ("attach", "J", ("c", [(-BIG, -BIG, BIG, 400), (-BIG, -BIG, 500, 600)],
                                        [("line", ((713, 450), (713, -262), 164), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 713, -250, 164), "dir": 270, "turn": "cw",
                                                   "r": (150, 130), "sweep": 170, "ball": 78, "t": (164, 50)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((380, -330), (980, -80), 50), (0, 0), (1, 1, 0, 0))])),
                  # ɟ's stem (its entry stroke cut away) rising and curling over like f's
                  # (its bar centred on the stem)
                  "ʄ": ("attach", "uni025F", ("x", [(-BIG, 600, BIG, BIG), (-BIG, 475, 330, BIG),
                                                    (-BIG, 410, 345, 474), (500, 410, BIG, 474)],
                                              [("rect", (351, 550, 495, 1150), (0, 0), (1, 1, 0, 0)),
                                               ("rect", (173, 414, 673, 470), (0, 0), (1, 1, 0, 0)),
                                               ("curl", {"at": ("pt", 423, 1150, 122), "dir": 90, "turn": "cw",
                                                         "r": (150, 130), "sweep": 210, "ball": None, "t": (122, 45)},
                                                (0, 0), (1, 1, 0, 0))], 760)),
                  # u's last stem curling over to the left at the top
                  "ʋ": ("curl", "u", ("x", [(700, 700, BIG, BIG)],
                                      {"at": ("y", 700, "last"), "dir": 90, "turn": "ccw", "r": (120, 110),
                                       "sweep": 200, "ball": None, "t": (120, 42)})),
                  "ʈ": ("attach", "t", ("x", [(-BIG, -BIG, BIG, 300), (300, -BIG, BIG, 600)],
                                        retroflex(232, 232, 350, 116, (110, 100), 45, 40))),
                  # the left stem curling over to the left, as on Ɓ; W's right arm to the right
                  "Ɦ": ("curl", "H", ("c", [(-BIG, 1300, 700, BIG)],
                                      {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                       "sweep": 200, "ball": None, "t": (164, 60)})),
                  # w's hairline arm (its ball cut away) rising straight to the
                  # x-height and curling over (the Regular's curl, carried
                  # across, left slivers beside the diagonal)
                  "ⱳ": ("attach", "w", ("x", [(1000, 645, BIG, BIG)],
                                        [("line", ((1289, 620), (1287, 770), 54), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1287, 770, 54), "dir": 92, "turn": "cw",
                                                   "r": (105, 95), "sweep": 200, "ball": None, "t": (54, 36),
                                                   "lead": 6}, (0, 0), (1, 1, 0, 0))])),
                  # W's last arm cut below its flare into the serif
                  # (redraw_w) and run on straight (its centre 1386.5 at
                  # 900, 1414.5 at 1000; 77 across) to 1150, where the
                  # curl leaves it at its own slant: cut at 1150, the
                  # flare's upright bend stayed under the curl, a bump on
                  # its outer edge (2026-11-03)
                  "Ⱳ": ("attach", "W", ("c", [(1255, 990, BIG, BIG)],
                                        [("line", ((1386.5, 900), (1459.9, 1162), 77), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1456.5, 1150, 77), "dir": 74.4, "turn": "cw",
                                                   "r": (120, 110), "sweep": 210, "ball": 50, "t": (77, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # v on a stem under its round bottom
                  "ү": ("descend", "v", ("x", "p")),
                  # Serbian and Macedonian italic (locl SRB, MKD; the
                  # Regular's are its plain letters, ITALIC_LOCL): б leaning
                  # back is Old Standard's д, ∂; д is g; ѓ is ī with the
                  # acute over its bar, as Charis and Libertinus stack them
                  # (serbian_gje: the acute added once the letters are
                  # spaced; 2026-11-08)
                  "б.loclSRB": ("alias", "uni0434", None),
                  "д.loclSRB": ("alias", "g", None),
                  "ѓ.loclSRB": ("alias", "imacron", None),
                  # Bulgarian: the italic's own и п т ц ш щ have the shapes
                  # the upright takes from Latin (u n m)
                  "и.loclBGR": ("alias", "uni0438", None),
                  "п.loclBGR": ("alias", "uni043F", None),
                  "т.loclBGR": ("alias", "uni0442", None),
                  "ц.loclBGR": ("alias", "uni0446", None),
                  "ш.loclBGR": ("alias", "uni0448", None),
                  "щ.loclBGR": ("alias", "uni0449", None),
                  "г.loclBGR": ("alias", "uni0433", None),  # the cursive г is ƨ already
                  # ascenders: ь's entry curl and stem top cut where its stem
                  # is as wide as b's (600), b's stem and flag on it (b's
                  # bowl clipped); ю's first and ж's middle stem take l's,
                  # as light as theirs
                  "ь.loclBGR": ("attach", "uni044C", ("x", [(-BIG, 600, BIG, BIG), (-BIG, 520, 200, BIG)],
                                                       [("b", (-BIG, 595, 320, BIG), (0, 0), (1, 1, 107, 0))])),
                  "ю.loclBGR": ("attach", "uni044E", ("x", [(-BIG, 650, 470, BIG), (-BIG, 540, 230, BIG)],
                                                       [("l", (-BIG, 645, BIG, BIG), (0, 0), (1, 1, 122, 0))])),
                  # ж: l's ascender on the stem (ж's own left half is the
                  # right c mirrored, 41 left of Old Standard's: mirror_zhe;
                  # 2026-11-08)
                  "ж.loclBGR": ("attach", "uni0436", ("x", [(639, 800, 939, BIG)],
                                                       [("l", (-BIG, 790, BIG, BIG), (0, 0), (1, 1, 553, 0))])),
                  # в: b with β's loop above, as in the Regular: the loop (its
                  # left side lighter than b's stem) over the stem's top, the
                  # stem cut where the loop's curve rounds it off; the ball on
                  # the stem; β's waist (780) on b's bowl top (860), 0.837 as tall;
                  # below the waist only the ball (not the stroke into β's lower
                  # bowl): one piece, β above 735 less its stem below 1290 and
                  # that stroke (in pieces, the seams kinked the loop); the
                  # notch between stem, ball and b's arch filled; the
                  # counter's floor carried level from the top of the ball
                  # (931) into the loop's right side, where β's waist left a
                  # dip (883 at 508)
                  "в.loclBGR": ("attach", "b", ("x", [(-BIG, 1355, BIG, BIG), (-BIG, 1300, 203, BIG)],
                                                [("beta", ((-BIG, 735, BIG, BIG), (-BIG, 735, 414, 1290),
                                                           (674, 735, BIG, 790)),
                                                  (0, 780), (1, 0.837, -154, 860)),
                                                 ("poly", [(300, 690), (300, 835), (360, 835), (430, 820), (395, 800),
                                                           (375, 780), (360, 760), (345, 740), (335, 720), (325, 700)],
                                                  (0, 0), (1, 1, 0, 0)),
                                                 ("poly", [(354, 915), (354, 931), ((430, 931), (554, 942), (564, 991)),
                                                           (580, 960), (510, 872)],
                                                  (0, 0), (1, 1, 0, 0))])),
                  # ъ (its stem a cursive diagonal): the ь above with ъ's
                  # wave arm raised to the ascender, left of the stem
                  "ъ.loclBGR": ("attach", "ь.loclBGR", ("x", [], [("uni044A", (-BIG, 620, 300, BIG), (300, 884),
                                                                    (1, 1, 270, 1434))])),
                  # г is ī, the bar free above ı as Charis and Libertinus
                  # draw it (2026-11-08; ū's first stem with its
                  # bar, srb_ge, kept too little of the bar to read)
                  "г.loclSRB": ("alias", "imacron", None),
                  # п and т are и and ш with the bar free above them, as
                  # Charis and Libertinus draw them (serbian_bars; Old
                  # Standard's own, afii10831/2, had it fused onto the
                  # stems: 2026-11-08)
                  "п.loclSRB": ("alias", "uni0438", None),
                  "т.loclSRB": ("alias", "uni0448", None)}
# Old Standard's own localized forms taken as they are (none now)
OS_LOCL = {}
# Old Standard letters drawn off their base: {glyph: (base, dx)}, the outline
# moved by dx (Old Standard's units) and the anchors taken from the base's.
# Į stood 84 right of its I at the same advance (160 in the Italic: bounds
# 131..1097 against -29..923), the only precomposed letter so (swept
# 2026-11-13); kern_clear then gave it about +200 before every ascender
OS_SHIFT = {"Iogonek": ("I", -84)}

# the Regular's short fs (calt before a mark f's hook meets; draft_ligatures
# SHORT_F) are the italic f and ff: their hook clears the marks
# (2026-11-14). Made a component of the letter, which it then follows
ITALIC_ALIASES = {"f.short": "f", "ff.short": "ff"}

# aliases of a plain letter in the Regular that the Italic makes itself
ITALIC_LOCL = {"uni0433.loclSRB", "uni0434.loclSRB", "uni0453.loclSRB",
               "uni0438.loclBGR", "uni043F.loclBGR", "uni0442.loclBGR", "uni0448.loclBGR"}

# Old Standard leans Λ and Δ about 30 and 34 degrees (A 18.5): their right
# leg drawn as an upright stroke slanted, the left one flatter still, a
# right-angled triangle where the references' lean as their A (2026-11-08)
LEAN_AS = {"Lambda": "A", "Deltagreek": "A"}

# the Italic's own kerning, over the Latin pairs computed from the Regular's
# (italic_kerning.py) and the Regular's others; the reviewed exceptions
# (docs/claude/spacing.md, "What stays a hand exception"): f, its top
# hanging over, closer to the letters with a stem
ITALIC_KERNING = {
    # ƴ: its hook sets its right side; the diagonal under it stood far
    # from a, o, e (kerned until the hook comes near a's terminal)
    ("uni01B4", "public.kern2.a"): -120,
    ("uni01B4", "public.kern2.agrave"): -120,
    ("uni01B4", "public.kern2.c"): -120,
    ("uni01B4", "public.kern2.egrave"): -120,
    ("f", "public.kern2.i"): -60, ("f", "public.kern2.u"): -60, ("f", "m"): -60, ("f", "p"): -60, ("f", "r"): -60,
    # K y slightly tighter ("Kyoto", review of 2026-11-11): unkerned in the
    # Regular, so the rule cannot give it; to be set on a sheet with K v K w
    ("public.kern1.K", "public.kern2.y"): -30,
    # [j (j {j looser: j's ball tucks under the bracket's foot, near on
    # the diagonal though 56 units clear across, so kern_clear leaves it
    # (chosen +60 of +20..+80 on
    # proofs/italic-bracket-j-candidates-2026-11-13.pdf, 2026-11-13;
    # the Bold Italic takes it scaled)
    **{(o, "public.kern2.j"): 60 for o in ("parenleft", "bracketleft", "braceleft")},
    # Greek (Old Standard's letters) against Greek references, as the
    # Italic's Latin sets them (scripts/quality/greek_pairs.py)
    ("public.kern1.chi", "public.kern2.epsilontonos"): -47,  # χε (the Regular's -158)
    ("public.kern1.eta", "public.kern2.nu"): 86,  # ην
    ("public.kern1.eta", "public.kern2.rho"): 82,  # ηρ
    ("public.kern1.theta", "public.kern2.nu"): 71,  # θν
    ("public.kern1.alpha", "public.kern2.delta"): -70,  # αθ
    ("public.kern1.alpha", "delta"): 0,  # αδ (tight at the cut of 2026-10-21, as in the Bold Italic)
    ("public.kern1.alpha", "public.kern2.xi"): -73,  # αξ
    ("public.kern1.alpha", "public.kern2.zeta"): -79,  # αζ
    ("public.kern1.alpha", "public.kern2.sigma1"): -91,  # ας
    ("public.kern1.tau", "public.kern2.etatonos"): -110,  # τη
    ("public.kern1.sigma", "public.kern2.upsilon"): -120,  # συ
    ("public.kern1.sigma", "public.kern2.etatonos"): -124,  # ση
    ("public.kern1.sigma", "public.kern2.kappa"): -127,  # σκ
    ("public.kern1.Kappa", "public.kern2.alphatonos"): -175,  # Κα
    ("public.kern1.lambda", "public.kern2.epsilontonos"): 15,  # λε (the Regular's -57)
    # where Charis and Libertinus agree against the Italic (tests/test_greek_pairs.py)
    ("public.kern1.sigma", "public.kern2.mugreek"): -21,  # σμ
    ("public.kern1.rho", "public.kern2.gamma"): 32,  # ργ
    # Cyrillic against Cyrillic references, as the Italic's Latin sets them
    # (greek_pairs.py --script cyrillic): the Regular's pairs were made for
    # the upright д л ѵ, the italic's round д and hooked л stood crowded
    ("public.kern1.uni0420", "public.kern2.uni0434"): -94,  # Рд (the Regular's -192)
    ("public.kern1.uni0423", "public.kern2.uni0434"): -130,  # Уд (-352)
    ("public.kern1.uni0490", "public.kern2.uni0434"): -72,  # Ґд (-342)
    ("public.kern1.uni0490", "public.kern2.uni0443"): -168,  # Ґу (-348)
    ("public.kern1.uni0433", "public.kern2.uni043B"): -72,  # гл (-156)
    ("public.kern1.uni0430", "public.kern2.uni0475"): -32,  # аѵ (-124)
}
# the Regular's pairs the Italic does without (the Latin ones the rule
# drops itself): Cyrillic pairs made for upright forms, in range unkerned
# in the Italic (ду уд уе ул уѫ ъу ѫб оѵ; greek_pairs.py --script cyrillic)
ITALIC_UNKERNED = {("uni0434", "public.kern2.uni0443"), ("public.kern1.uni0443", "public.kern2.uni0434"),
                   ("public.kern1.uni0443", "public.kern2.uni0435"), ("public.kern1.uni0443", "public.kern2.uni043B"),
                   ("public.kern1.uni0443", "public.kern2.uni046B"), ("public.kern1.uni044A", "public.kern2.uni0443"),
                   ("public.kern1.uni046B", "public.kern2.uni0431"), ("public.kern1.uni043E", "public.kern2.uni0475"),
                   # ΔΥ ΟΥ (and their small caps, copied from them): the
                   # Regular's -206 and -148 made for the upright Δ's open
                   # upper right; the italic Δ's right side is a sloped
                   # stem, Δ ran into Υ (Δ.sc into Υ.sc, the Bold Italic's
                   # overlapping), below every Greek reference; unkerned in
                   # range (greek_pairs refs, capitals and small caps,
                   # samples.pdf review 2026-11-04)
                   ("public.kern1.Deltagreek", "public.kern2.Upsilon"), ("public.kern1.Omicron", "public.kern2.Upsilon")}
# ß's left side looser: with the heavier stems it stood tight against the
# letter before it (measured, scripts/quality/colour.py)
# ʼ ʻ: the Regular's, sloped about half the x-height, stood far right for
# glyphs this high (ʼl touched): as far from l and i as ’ ‘, upright
# the derived letters whose hook, tail or curl set them otherwise beside
# their neighbours than the references set them against their base
# (scripts/quality/derived_spacing.py Italic, to the references' median;
# the Regular's are data_regular.SPACING): ɠ ʂ ʐ ʃ Ƭ ɻ ҷ қ Ƈ ң Ƴ ƭ ɮ ʄ Ƙ ɳ Ʋ ɱ ɧ Ҳ ʝ ɾ
ITALIC_SIDEBEARINGS = {"germandbls": (25, 0),
                       "uni02BC": (-145, 145), "uni02BB": (-130, 130),
                       "uni0260": (0, -380), "uni0282": (-265, 0), "uni0290": (0, -275), "uni0283": (-215, -135),
                       "uni01AC": (5, 0), "uni027B": (0, -170), "uni04B7": (0, -145), "uni049B": (0, -125),
                       "uni0187": (0, -165), "uni04A3": (0, -145), "uni01B3": (0, -235), "uni01AD": (0, -105),
                       "uni026E": (0, -85), "uni0284": (-130, 0), "uni0198": (0, -180), "uni0273": (0, -130),
                       "uni01B2": (0, -80), "uni0271": (0, -100), "uni0267": (0, -100), "uni04B2": (0, -65),
                       "uni029D": (0, -55), "uni027E": (-90, 0),
                       # ɗ: the hook overhangs, the advance 32 past d's as in the
                       # Regular (Charis 35); set by the hook, ɗa stood 150 looser than da
                       "uni0257": (0, -119),
                       # ɦ.sc (from Ɦ): the least white before its hook as h.sc h.sc's
                       # (107; Ɦ's advance kept, it stood 145, the draft's -19)
                       "uni0266.sc": (-38, 0)}
# the horn's foot sunk into the top of u's stem: set on it, it leaves a
# ledge beside the stem (glyph_lint)
HORN_NUDGE = {"u": (-20, -30), "U": (-20, 0), "u.sc": (-20, 0)}
# the Regular's horn, sloped, was lighter and smaller than every reference
# italic's (ơ: 19 % of o's ink, EB Garamond 22, Libertinus 34, Charis 24):
# scaled about its tip (where it attaches), the Bold Italic's with it
ITALIC_HORN = {"horn": 1.2, "Horn": 1.2}
# the lowercase dot smaller than the Regular's, about its centre (the Bold
# Italic follows): 1.52 of the stem as the Regular's, Bodoni's italic 1.44,
# Old Standard's 1.32 (its roman 1.45); 0.948 (236 across) chosen
# 2026-11-09 from 0.948 and 0.867 ("a bit fat for the italics")
ITALIC_MARK_SCALE = {"dotaccent": 0.948}

# Myia's anchor names, and Old Standard's to take their place from
ANCHOR_SOURCES = {
    "Top": ["Top"], "Acute": ["Top"], "Grave": ["Top"], "Dotaccent": ["Dotaccent", "Top"],
    "TopCap": ["Top"], "Bottom": ["Bottom"], "DotBelow": ["Bottom"], "Cedilla": ["Bottom"],
    "GreekTop": ["GreekTop", "Top"], "GreekCap": ["GreekCap"], "IotaSubscript": ["Bottom"],
}
# anchors moved a little from there (dx, dy): the cedilla's top corner, from
# Old Standard's Bottom of c, would poke out into the counter
ANCHOR_NUDGE = {("c", "Cedilla"): (0, -4), ("e", "Cedilla"): (0, -10),
                # The Roman t dot rose 59 units after the italic family was
                # reviewed. Retain its recipe anchor for hooked/tailed t;
                # t_dot_anchor sets the plain italic t independently below.
                ("t", "Dotaccent"): (-59 * SLANT, -59),
                # ė ż: the dot 90 further left (it stood right of the
                # letter, 2026-11-09, chosen from 30 60 90); the Bold Italic
                # keeps its own (make_bold ITALIC_ANCHOR_NUDGE)
                ("e", "Dotaccent"): (-90, 0), ("z", "Dotaccent"): (-90, 0)}

# the breathings and accents set before a Greek capital (Ἀ Ἔ Ὦ ...), and
# the composite measured for each capital
GREEK_CAP_SAMPLES = {"Alpha": "uni1F08", "Epsilon": "uni1F18", "Eta": "uni1F28", "Iota": "uni1F38",
                     "Omicron": "uni1F48", "Rho": "uni1FEC", "Upsilon": "uni1F59", "Omegagreek": "uni1F68"}

# their repairs match their exact points (aleph.py, l_belt.py): slanted
# without splitting their curves at the extremes the slant moves
POINT_REPAIRS = {"uni2135", "uni026C", "uniA7AD"}
# Rounded plainly, not smoothly (make_bold.round_smoothly): the repairs of
# ℵ (aleph.py) and of ɬ Ɬ's belts (l_belt.py) match their exact points;
# ȷ's descender is cut and attached for the Bold Italic ɱ and ɧ, where a
# unit moves the cut; ƹ's smoothed handle takes its top off the x-height
# zone once CFF-hinted (12-15 ppem); the rest gain little or nothing here
# and break joins or extremes in the Bold Italic (ϗ.sc: two findings fewer
# here, five more there).
ROUND_PLAIN = ("uni2135", "uni026C", "uniA7AD", "uni0237", "uni01B9", "eight", "k.sc", "section", "uni023B", "uni03D7.sc")
