"""The Regular's derived letters: recipes, their spacing and the numbers
they are written in (derive.py). Every style takes them unless it
replaces an entry.

Data only: derive imports every name from here and re-exports it, so
that derive.NAME goes on working. This module imports only other data
modules, italic_geometry and the standard library
(tests/test_data_modules.py).
"""


BIG = 10000
# parts of f and ȷ used as hooks by "attach"
F_TOP = (-BIG, 1000, BIG, BIG)
F_HOOK = (-BIG, 1100, BIG, BIG)
J_TAIL = (-BIG, -BIG, BIG, 100)

# (character, operation, source, band) -- band only for turn/flip
RECIPES = [
    # same shape as an existing letter
    # ɑ: d's bowl and stem, the ascender cut at the x-height (the bowl's
    # overshoot kept), as in Charis; an alias of α was the same letter
    # a in IPA text (locl, language IPPH): the two-storey a, which the
    # italics' own a is not (make_italic.py: the roman's, sloped)
    ("a.ipa", "alias", "a", None),
    ("ɑ", "attach", "d", ("x", [(600, 884, BIG, BIG), (-BIG, 1000, BIG, BIG)], [])),
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
    # IPA small capitals at the x-height, weighted as the lowercase beside them
    # (Charis 0.98-1.00 of it); the small caps' height stood above the line.
    # Their weight goes by straight stems, i.sc to n: the italics' small caps
    # have heavier stems for their rounds than the lowercase has
    ("ɢ", "enlarge", "g.sc", ("o.sc", "o", -20, 884, "o.sc", "o")),  # round, the foot on the line
    ("ɪ", "enlarge", "i.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ʟ", "enlarge", "l.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ɴ", "enlarge", "n.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ʀ", "enlarge", "r.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ʏ", "enlarge", "y.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ʙ", "enlarge", "b.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ʜ", "enlarge", "h.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    # ᴅ ɶ: as aliases of d.sc oe.sc they stood at the small caps' height
    # (1040), a size above ɪ ʙ ʀ (2026-11-09); ɶ's round side overshoots as o
    ("ᴅ", "enlarge", "d.sc", ("o.sc", "o", 0, 884, "i.sc", "n")),
    ("ɶ", "enlarge", "oe.sc", ("o.sc", "o", -20, 904, "i.sc", "n")),
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
    # ɹ: r turned, as in the italics, Charis and Libertinus (
    # 2026-11-05: the Didot terminal drawn here before looked very unlike r's)
    ("ɹ", "turn", "r", "x"),
    ("ʌ", "turn", "v", "x"),
    ("ʍ", "turn", "w", "x"),
    ("ʎ", "turn", "y", "x"),
    ("ɒ", "turn", "ɑ", "x"),  # turned alpha
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
    # ball and the arch's hairline); the counter's floor carried level from
    # the top of the ball (961), from the stem (where the ball rose from
    # 905; a sharp corner: a rounded one turns over in the Bold) into the
    # loop's right side (β's waist left a dip, 952 at 577); b's counter
    # kept (β's waist reached into its top: kinks at 518 and 607)
    ("в.loclBGR", "attach", "b", ("x", [(-BIG, 1293, BIG, BIG)],
                                  [("beta", ((-BIG, 640, BIG, BIG), (-BIG, 640, 400, 1280)), (0, 750),
                                    (1, 0.772, 0, 884)),
                                   ("poly", [(378, 690), (378, 905), (430, 905), (480, 862), (550, 862),
                                             (490, 800), (455, 760), (425, 720)], (0, 0), (1, 1, 0, 0)),
                                   ("poly", [(360, 900), (360, 961), (496, 961), ((540, 961), (604, 961), (647, 999)),
                                             (647, 930), (496, 900)], (0, 0), (1, 1, 0, 0)),
                                   ("counter", (-BIG, -BIG, BIG, BIG), (0, 0), (1, 1, 0, 0))])),
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
                                     "r": (170, 140), "sweep": 170, "ball": None, "t": (130, 44)},
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
                         "sweep": 165, "ball": None, "t": (164, 52)})),
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
    # ʋ: its own ball (as drawn before 2026-10-27): at its stem's size it merges into u's first stem in the Bold
    ("ʋ", "curl", "u", ("x", [(940, -BIG, BIG, 60), (620, 600, BIG, BIG)],
                        {"at": ("y", 600, "last"), "dir": 90, "turn": "ccw", "r": (190, 262),
                         "sweep": 150, "ball": 78, "t": (164, 56)})),
    ("Ʋ", "curl", "U", ("c", [(1000, 1000, BIG, BIG)],
                        {"at": ("y", 1000, "last"), "dir": 90, "turn": "ccw", "r": (240, 400),
                         "sweep": 160, "ball": None, "t": (64, 64)})),
    ("ƴ", "curl", "y", ("x", [(660, 700, 1000, BIG)],
                        {"at": ("y", 700, "last"), "dir": 70.7, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": None}, 1080)),
    ("Ƴ", "curl", "Y", ("c", [(960, 1150, 1460, BIG)],
                        {"at": ("y", 1150, "last"), "dir": 63.4, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": None})),
    # ȷ's tail at the width of N's thin left stem (64 of ȷ's 164), centred on it
    ("Ɲ", "attach", "N", ("c", [(90, -BIG, 590, 60)],
                          [("uni0237", J_TAIL, (320, 100), (64 / 164, 0.6, 326, 80))])),
    ("Ƈ", "curl", "C", ("c", [(1100, 900, BIG, BIG)],
                        {"at": ("x", 1080), "dir": 70, "turn": "cw", "r": 170,
                         "sweep": 145, "ball": None})),
    ("Ɠ", "curl", "G", ("c", [(1100, 900, BIG, BIG)],
                        {"at": ("x", 1080), "dir": 70, "turn": "cw", "r": 170,
                         "sweep": 145, "ball": None})),
    ("ƈ", "curl", "c", ("x", [(620, 500, BIG, BIG)],
                        {"at": ("x", 600), "dir": 70, "turn": "cw", "r": 130,
                         "sweep": 145, "ball": None})),
    # more hooks, curls and loops drawn on
    # ʂ: s's bottom stroke turns down at the left into an upright stem below
    # the baseline, which hooks to the right, as ʈ's (and Charis's ʂ). The
    # turn leaves s where its bottom stroke runs level (x 420: -16..32) at
    # its weight, the stem starting where the turn stands upright
    # (2026-11-05: the turn into the hook "still not great"; from
    # x 320 it stood 44 units above s's stroke, a bump and a notch)
    ("ʂ", "attach", "s", ("x", [(-BIG, -BIG, 420, 360)],
                          [("curl", {"at": ("pt", 420, 8, 48), "dir": 180, "turn": "ccw",
                                     "r": (200, 100), "sweep": 90, "ball": 40, "t": (140, 48)},
                            (0, 0), (1, 1, 0, 0)),
                           ("line", ((220, -92), (220, -300), 140), (0, 0), (1, 1, 0, 0)),
                           ("curl", {"at": ("pt", 220, -300, 140), "dir": 270, "turn": "ccw",
                                     "r": (140, 120), "sweep": 150, "ball": None, "t": (140, 52)},
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
                                     "r": (150, 120), "sweep": 150, "ball": None, "t": (140, 52)},
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
    # Ƭ: the bar cut where the curl leaves it (cut at 420, the curl from 440
    # had the bar's corner stand 1.6 units under the ring's inner edge, a
    # 30-degree kink once faired: "the right transition uneven")
    ("Ƭ", "curl", "T", ("c", [(-BIG, 600, 420, BIG)],
                        {"at": ("x", 420), "dir": 180, "turn": "ccw", "r": 150,
                         "sweep": 150, "ball": None})),
    ("ⱳ", "curl", "w", ("x", [(1150, 700, BIG, BIG)],
                        {"at": ("y", 700, "last"), "dir": 71, "turn": "cw", "r": 160,
                         "sweep": 140, "ball": None})),
    ("Ⱳ", "curl", "W", ("c", [(1800, 1120, BIG, BIG), (1600, 1300, BIG, BIG)],
                        {"at": ("y", 1120, "last"), "dir": 73.8, "turn": "cw", "r": 200,
                         "sweep": 140, "ball": None})),
    ("ɧ", "hook", "ɦ", ("x", "down-left", "last", 48, 160, 160)),
    # Ƙ: the hook on the thin arm, as on Ƴ; Ϗ: the leg run on below the
    # baseline and turned back; ʝ Ʝ: the stem's tail looped back across it
    ("Ƙ", "curl", "K", ("c", [(900, 1250, BIG, BIG), (800, 1360, BIG, BIG)],
                        {"at": ("y", 1250, "last"), "dir": 50.8, "turn": "cw", "r": 170,
                         "sweep": 150, "ball": None})),
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
    ("₸", "lines", "T", ("c", 64, [(144, 1498, 1480, 1562)])),  # the second line above the T (Charis, Libertinus)
    ("₲", "lines", "G", ("c", 64, [(708, -180, 772, 1640)])),  # centred on the bowl (146-1334), not the spur
    ("₵", "lines", "C", ("c", 64, [(688, -180, 752, 1640)])),  # centred on the C (126-1314)
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
    # ɻ: its own ball: at its stem's size it fills the tail's counter in the Bold
    ("ɻ", "attach", "uni0279", ("x", [(494, -BIG, BIG, 60)],
                                [("line", ((576, 80), (576, -250), 164), (0, 0), (1, 1, 0, 0)),
                                 ("curl", {"at": ("pt", 576, -250, 164), "dir": 270, "turn": "ccw",
                                           "r": (140, 120), "sweep": 150, "ball": 66,
                                           "t": (164, 52)}, (0, 0), (1, 1, 0, 0))])),
    # ɾ: r's stem and foot slab under f's hook brought down onto the
    # x-height, f taken from above its crossbar (884) where its stem still
    # runs straight (its curve begins at 954; f's stem 4 right of r's): no
    # stem above the hook, the turn thinning as f's (2026-11-04:
    # r without its entry serif was too like r)
    ("ɾ", "attach", "r", ("x", [(-BIG, 308, BIG, BIG)], [("f", (-BIG, 920, BIG, BIG), (0, 0), (1, 1, -4, -612))])),
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
    # Ư's base: the horn grows out of the stem, where the serif's outer arm
    # was (EB Garamond, Old Standard); on it, it stood like a thing put there
    ("U.horn", "unserif", "U", None),
    # small caps for the new case pairs, derived like their capitals
    ("ɔ.sc", "mirror", "c.sc", None),
    ("ǝ.sc", "mirror", "e.sc", None),
    ("ɐ.sc", "turn", "a.sc", "s"),
    ("ʌ.sc", "turn", "v.sc", "s"),
    ("ɯ.sc", "twin", "u.sc", 500),
    ("ɪ.sc", "alias", "i.sc", None),
    ("ɨ.sc", "bar", "i.sc", ("s",)),
    ("ʉ.sc", "bar", "u.sc", ("s",)),
    ("u.sc.horn", "unserif", "u.sc", None),
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
    # ƈ.sc ɠ.sc: Ƈ Ɠ's curl drawn on c.sc g.sc (its place scaled as o.sc
    # from O, 0.73), at radius 150 (Ƈ 170, ƈ 130): enlarged from the
    # capitals their hooks stood smaller than ƈ's (2026-11-06).
    # The cut from 530: the italics' c.sc g.sc hang their ball to 575 (cut
    # from 657, its foot stood alone in the Bold Italic's rebuild); the
    # uprights have no ink right of 797 between 500 and 700
    ("ƈ.sc", "curl", "c.sc", ("s", [(797, 530, BIG, BIG)],
                              {"at": ("x", 782), "dir": 70, "turn": "cw", "r": 150,
                               "sweep": 145, "ball": None})),
    ("ɠ.sc", "curl", "g.sc", ("s", [(797, 530, BIG, BIG)],
                              {"at": ("x", 782), "dir": 70, "turn": "cw", "r": 150,
                               "sweep": 145, "ball": None})),
    # ʛ: ɠ.sc scaled and placed as ɢ from g.sc (ENLARGE_LIKE), its curl
    # above; as ɠ.sc's alias it stood at the small caps' height (1060), a
    # size above ɢ ɪ ʙ (2026-11-08)
    ("ʛ", "enlarge", "ɠ.sc", ("o.sc", "o", -20, 884, "o.sc", "o")),
    ("ƥ.sc", "enlarge", "Ƥ", ("O", "o.sc")),
    ("ɦ.sc", "enlarge", "Ɦ", ("O", "o.sc")),
    ("ɥ.sc", "alias", "uni0447.sc", None),
    ("ƃ.sc", "alias", "uni0431.sc", None),
    # the IPA small capitals with a stroke are those small caps
    ("ᵻ", "alias", "ɨ.sc", None),
    ("ᵾ", "alias", "ʉ.sc", None),
]

# sidebearing changes (left, right) after the recipe, where what it added
# (a hook, tail, curl) left the letter set otherwise beside its neighbours
# than the references set it against its base: scripts/quality/
# derived_spacing.py, each side moved to the references' median (2026-10-21).
# The Regular's only (main): the Bold fits its sides to the Regular's, the
# italics are measured on their own (their ITALIC_SIDEBEARINGS).
# Most hooks were counted into the advance (ɗ ɖ ɳ ʐ); ƴ's curl and the
# hooks of Ɓ Ɗ Ƥ ran into their neighbours. ƴ: not to the median (+355 left
# a hole in ƴaƴa) but +160, its ball clear of the a (chosen from renders).
# ɾ: none since it keeps r's foot slab (2026-11-04; -120 for the cut foot).
SPACING = {
    "ɗ": (0, -270), "ɖ": (0, -175), "ɭ": (0, -205), "ɳ": (0, -195), "ɠ": (0, -305), "ʐ": (0, -440),
    "ʈ": (0, -130), "ƭ": (0, -140), "ʄ": (0, -195), "ʝ": (0, -110), "ʑ": (0, -125), "ɕ": (0, -75),
    "ɚ": (0, -110), "ʂ": (-55, 0), "ʃ": (-145, -140), "ʒ": (145, 0), "ƴ": (0, 160),
    "Ɓ": (340, 0), "Ɗ": (340, 0), "Ƥ": (340, 0), "Ƭ": (-235, 0), "Ƈ": (0, -125), "ƈ.sc": (0, -85), "Ƙ": (0, -105),
    "Ʀ": (0, -85), "Ʋ": (0, -80),
    "Қ": (0, -125), "қ": (0, -95), "Җ": (0, -125), "җ": (0, -100), "Ҳ": (0, -130), "ҳ": (0, -115),
}

# letters made from a wider base whose bowl, left of the last stem, is
# narrowed by the factor towards it (the stem and its serifs unchanged,
# the left side bearing kept, the advance shortened by as much), and the
# letter whose marks above they take (the base's are over its ascender).
# ɑ from d: 1.18 times a's ink width, Charis and Libertinus 1.10-1.13;
# at 0.93 1.12 (2026-11-02).
NARROW = {"ɑ": (0.93, "q")}

# the derived letters whose curves are made smooth between these heights
# after they are built (smooth_curves)
SMOOTH_CURVES = {"Ƭ": (1300, 1400)}
# an enlarged letter with a part beyond its body (ʛ's curl over ɢ's top):
# scaled into the fit band as the plain letter would be, not by its own ink
ENLARGE_LIKE = {"ʛ": "g.sc"}
