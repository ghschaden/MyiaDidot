"""The Bold's tables and numbers, and those both bolds read (make_bold.py).

Data only: make_bold imports every name from here and re-exports it, so
that make_bold.NAME goes on working; KX, AX, THIN and THICK are rebound
there at run time (the Bold Italic's values, the pilots), so read them
through make_bold. This module imports only other data modules,
italic_geometry and the standard library (tests/test_data_modules.py).
"""


KX = 1.04  # widening, so the counters keep their light
AX, AY = 90, 8  # stems 164 -> 254 (lowercase), 208 -> 298 (capitals); hairlines +8

# strokes this thick and thinner gain no weight across, from there the more
# the thicker, all of it from THICK on (derive.embolden_by_weight)
THIN, THICK = 60, 160

# Ʌ: V turned, but for its thin leg's inner edge by the foot, drawn straight
# as Λ's in both italics (turned_v.py, 2026-11-12: up to 60 units over 230
# of its height)
MOVED_EXACT_FOR = {"uni0281": 0.97, "uni0245": 0.85}

MARK_AX, MARK_AY = 30, 8  # accents a little heavier

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
    "ɾ": ("attach", "r", "fishhook_band"),
    # ɮ: the Regular's, placed on the Bold's l and ʒ by their own stems
    # (by the Regular's numbers the ʒ's spur stood inside the heavier stem,
    # its leaning edge the stem's right edge, 2026-11-09)
    "ɮ": ("attach", "l", "lezh_band"),
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

# and rounder bodies spaced on the reference by weight they had before
BOLD_REFERENCE_BY_WEIGHT = {"psi"}
# and bodies kept by weight spaced on the rounder reference they had
BOLD_REFERENCE_ROUNDER = {"uni0190"}

# the Bold's letters are spaced tighter than the Regular's (the Regular's
# sidebearings times KX), as a bold's are: 40 off each side in all of the
# Regular's 20 (times KX) and BOLD_CUT, Greek lowercase 25 of 10 and BOLD_CUT_GREEK
BOLD_CUT, BOLD_CUT_GREEK = 19, 15

# the figures, which respace.py leaves alone, are tighter too: emboldened
# they stand looser than the Bold's letters (1.08 of their side space, where
# bold text faces have 0.8-1.0); one cut for all keeps them tabular, and the
# figure space and dash keep their width
BOLD_FIGURE_CUT = 28

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

# slashed rounds, drawn whole in the lighter style: emboldened whole, the
# ring swelled where the slash crosses it (Ø not O with a stroke through);
# the ring is the round's own, the slash emboldened apart (slashed)
SLASHED = {"Oslash": "O", "oslash": "o", "oslash.sc": "o.sc"}
