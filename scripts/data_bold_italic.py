"""The Bold Italic's tables and numbers (make_bold.py).

Data only, re-exported by make_bold as data_bold's; built on data_bold's
where a table extends the Bold's. Imports only other data modules,
italic_geometry and the standard library (tests/test_data_modules.py).
"""

from data_bold import AY, BOLD_CUT, BOLD_CUT_GREEK, OVALS

# the Bold Italic's, from the Italic's lighter stems (data_italic.WEIGHT 10):
# its stems 0.96 of the Bold's, as the Italic's of the Regular's (reference
# bold italics 0.95-0.98; AX gave 0.92, the heavier Italic of before 1.01)
ITALIC_AX = 102

ITALIC_THIN, ITALIC_THICK = 60, 160
# the Bold Italic is emboldened by its strokes (stroke_bold), its hairlines
# gaining this across (both sides), fading into ITALIC_AX as a stroke
# thickens: Libre Bodoni's quarter, hairlines 23 -> 30 per 1000
# (chosen 2026-10-28; Bodoni Moda's gain nothing)
ITALIC_HAIR = 12

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

# the Italic's joins faired (data_italic.ITALIC_JOINS) in the bands of the
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
    # ɴ, n.sc enlarged (data_regular.RECIPES): stroked from the Italic's, its
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
    # ₵ ₿ (2026-11-12, on the sheet after the capitals' redraw): emboldened
    # whole (₵ the rounder way), ₵'s line bent 15 units and C's back got a
    # bump; ₿'s stubs grew into the stem's bracket and the bars
    "uni20B5": "₵: its own recipe (ITALIC_BOLD_RECIPES); emboldened whole, the line bent and C's back bumped",
    "uni20BF": "₿: its own recipe (ITALIC_BOLD_RECIPES); emboldened whole, the stubs ran into the stem and the bars",
}

# the Bold Italic's curls over the top (ITALIC_BOLD_RECIPES): radii, turn and ball
CURL_CAP = {"r": (205, 185), "sweep": 190, "ball": 105}
CURL_ARM = {"r": (215, 195), "sweep": 190, "ball": 122}
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
    # running on in its own direction; Ʋ: U's right stem.
    # 2026-11-12 ("the arm leading to the hook is not good"; version C of
    # proofs/bold-italic-hook-arms-2026-11-12.pdf, for Ʋ version D): Ƙ Ƴ's
    # hook at the arm's own thickness all round, as the Italic's ⱳ (it was
    # 132 and 103 on the sides, 67 and 59 on top, on an arm of about 98);
    # the curl begun 14 degrees back in the arm ("lead"): the arm is cut
    # level, the curl starts square to its direction, and the wedge between
    # was missing on the upper side (a ledge of 24 units, 72 at the arm's
    # thickness); a larger curl and ball (CURL_ARM). Ʋ: 100 on the sides
    # for 139 where the curl leaves the thin stem (a thickening there), 80
    # on top: at the stem's own thickness its top stood too tight and
    # closed the eye; no lead (on an upright stem a jog of 7 units)
    "Ƙ": ("curl", "K", ("c", [(870, 1130, 10000, 10000)],  # (at 1150 a step, ƙ.sc's ledges)
                        {"at": ("y", 1130, "last"), "dir": 51.6, "turn": "cw", **CURL_ARM, "lead": 14})),
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
    # ₵: the line 98 across as ₲'s comes out, straight, its middle 64 right
    # of the Bold Italic C's (138-1320 here), as the Italic's stands to its C
    "₵": ("lines", "C", ("c", 98, [(744, -180, 842, 1640)])),
    # ₿: the stubs 96 across as emboldened, 104 apart (were 154: "closer")
    # and clear of the stem's bracket; only outside the B, 34 into its bars
    # ("not impact the thickness of the outline of the B", 2026-11-12)
    "₿": ("lines", "B", ("c", 96, [(636, 1400, 732, 1634), (836, 1400, 932, 1634),
                                    (636, -200, 732, 34), (836, -200, 932, 34)])),
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
                        {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", **CURL_ARM, "t": (100, 80)})),
    "Ƴ": ("curl", "Y", ("c", [(800, 1100, 10000, 10000)],
                        {"at": ("y", 1100, "last"), "dir": 68.5, "turn": "cw", **CURL_ARM, "lead": 14})),
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
    # Қ Җ җ қ: the Italic's (data_italic.descender), on the Bold Italic's
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
    # ɳ: the Italic's (data_italic.retroflex), on the Bold Italic's leg (its
    # centre 836, 229 thick at the cut): emboldened whole, the descender took
    # only part of the weight (its stroke under the thick threshold) and the
    # leg pinched at the join; the ball half the stroke, as the Italic's and
    # Ɽ's (80 left a straight step where the curl ran into it)
    "ɳ": ("attach", "n", ("x", [(700, -10000, 10000, 200), (1000, -10000, 10000, 450)],
                          [("line", ((836, 210), (836, -150), 229), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 836, -150, 229), "dir": 270, "turn": "ccw", "r": (150, 130),
                                     "sweep": 170, "ball": 115, "t": (229, 55)}, (0, 0), (1, 1, 0, 0))])),
    # Ɽ Ʈ ɽ.sc ʈ.sc: the Italic's (data_italic.retroflex: the foot serif cut
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
# Bold Italic knees the blend's gate cannot find, by their curves' keys
# (contour, segment) in the Italic's outline: the stem's line running into
# the counter's bottom as u's (stroke_bold.knee_turned). Since и ц ш щ took
# u's knee in the Italic's redraw (2026-11-12), the stroked outline leaves
# there not a step but a curve with both handles on its end, a bend (u's
# was mended by hand, drawn 2026-11-11); ш щ's middle stem too (not м's
# right stem into its foot: turned as a knee, its foot's inner edge came
# out a straight diagonal, 2026-11-12)
ITALIC_BOLD_KNEES = {"uni0438": ((0, 4),), "uni0446": ((0, 4),), "uni0448": ((0, 4), (0, 11)),
                     "uni0449": ((0, 4), (0, 11))}
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
}
# The reviewed body choices above must retain their previous rounder
# optical-spacing reference; body weighting and spacing are independent.
ITALIC_REFERENCE_ROUNDER = {"uni024D", "uni027A", "uni027B", "uni027E"}

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

# the Bold Italic's capital rounds and bowls: stroke_out gave them back
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
                       # ₵ ₿ on the Bold Italic's C and B (ITALIC_BOLD_RECIPES, 2026-11-12):
                       # the side bearings they had emboldened whole (10 and 261, 9 and 200)
                       "uni20B5": (16, 3), "uni20BF": (16, 14),
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
# values in font units; they are applied after the source kerning is scaled
# and the Latin pairs computed (italic_kerning.py), over both.
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

# the Bold Italic's closed rounds: the stroked counter ran nearly straight
# with tight turns (o, top right and bottom left), o.sc's a rounded
# rectangle (2026-11-05: "very unround"); the Italic's counter
# put in its place (italic_counter); their slashed forms through their ring.
# g's bowl too: stroked it came to a point at the bottom left, where the
# Italic's is round (2026-11-06: c g C G unround inside); the
# open rounds' insides from the Italic's run (italic_inside)
ITALIC_OVALS = OVALS | {"o.sc", "g"}
