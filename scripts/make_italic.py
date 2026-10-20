"""Make the Italic master: Old Standard's italic in Myia's frame.

    python scripts/make_italic.py [REGULAR.ufo] [ITALIC.ufo]

The letters, figures and signs come from Old Standard Italic (Alexey
Kryukov, SIL OFL 1.1; sources/oldstand, converted with FontForge into
build/oldstand), the cursive companion by Theano's own designer. They are
scaled in zones so that its x-height (456 of 1000) lands on Myia's 884 and
its capitals and ascenders (712) on 1434, the descenders in proportion;
their stems and hairlines are brought to Myia's (lighter by AX, AY). The
glyph set, features, accents and marks are Myia's: the accents sloped to
the italic angle (with their anchors), the accented letters rebuilt from
the anchors by the rules of composites.py, upstream's special composites
kept with each accent moved as the anchor it sits on moves.

What Old Standard does not have is made from what it has, in an upright
frame (the whole font unslanted, the glyph made, slanted again), so that
recipes tuned on the upright Regular apply and mirroring keeps the slant:
the letters of derive.py's recipes (IPA, African, Cyrillic extras), the
old-style figures (its lining figures fitted to the Regular's), the small
caps (FontForge's drafts of its capitals, as for the Regular). Arrows,
geometric shapes and circled letters stay upright, the Regular's. What is left is the roman
sloped. Then smallcaps.py runs on the Italic (accented small caps,
features). Afterwards: make normalize.

Each glyph's lib key org.myiadidot.italicSource says where it came from.
A rerun keeps what was reviewed: glyphs marked "drawn" (hand-edited: set
it after editing any glyph), and drafts ("derived", "figure draft",
"small cap draft") whose draft key has been cleared.
"""

import argparse
import copy
import math
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import case_forms
import kern_clear
from composites import SPECIAL, Builder, stack_anchors
from derive import BIG, draw_path, embolden, rezone
from make_bold import WHOLE_KEY, mark_like, redraw, write
from respace import CUT_KEY, classifier, respace, sidebearings, undo
from smallcaps import ink_bounds, ink_slice
from space_figures import space as space_figures

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SFD = ROOT / "sources/oldstand/OldStandard-Italic.sfd"
SOURCE_UFO = ROOT / "build/oldstand/OldStandard-Italic.ufo"
ANGLE = 15.2  # Old Standard's italic angle
SLANT = math.tan(math.radians(ANGLE))
KX = 1.98  # across: between the x-height (1.939) and cap-height (2.014) scales
OS_XH, OS_CAP = 456, 712
XH, CAP = 884, 1434
AX, AY = -16, -10  # Old Standard's strokes, scaled, are a little heavier than Myia's
# ... but so the Italic was light: 0.80 of the Regular's colour, where
# italics have 0.93-1.04. Its letters (and all made of them) are built at
# that weight, which the recipes and transplants are tuned to, and their
# thick upright strokes then made WEIGHT heavier (weight_thick: hairlines and
# thin strokes as they are, so the contrast grows): stems about the
# Regular's, as Old Standard's italic has its roman's
WEIGHT = 44
WEIGHTED = ("Old Standard", "derived", "small cap draft")
# off each side of a letter: Old Standard's spacing, scaled, is loose too (10;
# less what the added weight takes of the stems at the sides)
ITALIC_CUT = 3
# the Greek lowercase tighter: Old Standard's Greek, so cut, stood 0.07 of an
# n n gap looser than the Italic's Latin against Greek references
# (scripts/quality/greek_pairs.py)
ITALIC_CUT_GREEK = ITALIC_CUT + 11
SOURCE_KEY = "org.myiadidot.italicSource"
DRAFT_KEY = "org.myiadidot.draft"
SMALLCAP_DRAFT_KEY = "org.myiadidot.smallcapDraft"
FIGURES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def reviewed(g):
    """A glyph a rerun must keep: hand-drawn, or a draft that was reviewed."""
    src = g.lib.get(SOURCE_KEY)
    if src == "drawn":
        return True
    return (src in ("derived", "figure draft", "small cap draft")
            and not g.lib.get(DRAFT_KEY) and not g.lib.get(SMALLCAP_DRAFT_KEY))


# signs Old Standard draws for mathematics, far larger than Myia's (+ is
# 1861 wide to the Regular's 1152), and its raised and lowered + − =: the
# Regular's are taken instead, upright
MATH_SIGNS = set(map(ord, "+<=>±×÷¬−≈≠≤≥⁺⁻⁼₊₋₌⊗"))
# Myia's own, sloped, though Old Standard has them: the guillemets
# (draft_symbols.py's chevrons; Old Standard's are small crescents)
ROMAN_SIGNS = set(map(ord, "‹›"))


def keeps_upright(u):
    """Signs an italic sets upright (the letterlike and mathematical
    letters 𝔐 𝑙 ℓ ℵ are slanted with the rest)."""
    return (0x2190 <= u <= 0x21FF or 0x2460 <= u <= 0x24FF or 0x25A0 <= u <= 0x25FF
            or 0x3000 <= u <= 0x303F or 0x23D1 <= u <= 0x23D9 or u in (0x22EE, 0x2042)
            or u in MATH_SIGNS)


def ymap(y):
    """Old Standard's heights to Myia's, zone by zone."""
    if y <= OS_XH:
        return y * XH / OS_XH
    return XH + (y - OS_XH) * (CAP - XH) / (OS_CAP - OS_XH)


class Zones(FilterPen):
    def _t(self, pts):
        return [(x * KX, ymap(y)) for x, y in pts]

    def moveTo(self, p):
        self._outPen.moveTo(*self._t([p]))

    def lineTo(self, p):
        self._outPen.lineTo(*self._t([p]))

    def curveTo(self, *ps):
        self._outPen.curveTo(*self._t(ps))

    def qCurveTo(self, *ps):
        self._outPen.qCurveTo(*self._t(ps))

    def closePath(self):
        self._outPen.closePath()

    def endPath(self):
        self._outPen.endPath()


def source_font():
    if not SOURCE_UFO.exists():
        SOURCE_UFO.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["fontforge", "-quiet", "-lang=py", "-c",
                        f"import fontforge; fontforge.open({str(SOURCE_SFD)!r}).generate({str(SOURCE_UFO)!r})"],
                       check=True)
    return ufoLib2.Font.open(SOURCE_UFO)


def sloped(t_y0):
    """The italic slant as a transformation, about the height t_y0."""
    return (1, 0, SLANT, 1, -SLANT * t_y0, 0)


def shear(g, s, y0=XH / 2):
    """Slant (s > 0) or unslant (s < 0) a glyph about the height y0."""
    if g.contours:
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
        out = ufoLib2.objects.Glyph()
        rec.replay(TransformPen(out.getPen(), (1, 0, s, 1, -s * y0, 0)))
        redraw(g, out)
    for c in g.components:
        xx, xy, yx, yy, dx, dy = c.transformation
        c.transformation = (xx, xy, yx, yy, round(dx + dy * s), dy)
    for a in g.anchors:
        a.x = round(a.x + (a.y - y0) * s)


def upright(font):
    """The whole font unslanted: what is made in it is slanted back."""
    up = copy.deepcopy(font)
    for g in up:
        shear(g, -SLANT)
    return up


def weight_thick(rec, ax, thin=80, thick=120):
    """rec with its thick upright strokes ax heavier, its hairlines and thin
    strokes as they are (embolden() with a factor per node): none below
    thin, all above thick, by the stroke's thickness measured across the
    ink. A node at the end of a long straight edge takes the thickness at
    the edge's middle, so both ends of the edge move alike (it keeps its
    slant)."""
    import numpy as np

    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())
    # the outline as straight segments, to measure across
    flat = RecordingPen()
    glyph.draw(flat)
    segs, start, cur = [], None, None
    for op, args in flat.value:
        if op == "moveTo":
            start = cur = args[0]
        elif op == "lineTo":
            segs.append((cur, args[0]))
            cur = args[0]
        elif op == "curveTo":
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = cur, *args
            prev = cur
            for k in range(1, 11):
                t = k / 10
                q = ((1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 * x3,
                     (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * y3)
                segs.append((prev, q))
                prev = q
            cur = args[-1]
        elif op in ("closePath", "endPath") and cur != start:
            segs.append((cur, start))
            cur = start
    if not segs:
        return glyph
    a = np.array([s[0] for s in segs], float)
    d = np.array([s[1] for s in segs], float) - a

    def across(px, py, ux, uy):
        """distance from (px, py) along (ux, uy) to the outline's other side"""
        den = d[:, 0] * uy - d[:, 1] * ux
        ok = np.abs(den) > 1e-9
        wx, wy = a[:, 0] - px, a[:, 1] - py
        t = np.where(ok, (d[:, 0] * wy - d[:, 1] * wx) / np.where(ok, den, 1), -1)  # along the ray
        s = np.where(ok, (ux * wy - uy * wx) / np.where(ok, den, 1), -1)  # along the segment
        hit = ok & (t > 3) & (s >= 0) & (s <= 1)
        return float(t[hit].min()) if hit.any() else 0.0

    def k_of(w):
        return min(1.0, max(0.0, (w - thin) / (thick - thin)))

    # the long straight edges: their thickness at the middle, for both ends
    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    edge_k = {}
    for contour, ar in zip(glyph.contours, areas, strict=True):
        sign = 1 if ar > 0 else -1
        if (ar > 0) != outer:
            sign = -sign
        P = contour.points
        ons = [p for p in P if p.type]
        for p0, p1 in zip(ons, ons[1:] + ons[:1], strict=True):
            if p1.type != "line" or math.dist((p0.x, p0.y), (p1.x, p1.y)) < 60:
                continue
            ux, uy = (p1.x - p0.x), (p1.y - p0.y)
            L = math.hypot(ux, uy)
            nx, ny = uy / L, -ux / L  # right-hand normal; outward is sign x it
            mx, my = (p0.x + p1.x) / 2, (p0.y + p1.y) / 2
            k = k_of(across(mx, my, -sign * nx, -sign * ny))
            for q in (p0, p1):
                edge_k.setdefault((q.x, q.y), []).append(k)

    def factor(x, y, inward):
        if (x, y) in edge_k:
            return max(edge_k[(x, y)])
        return k_of(across(x, y, *inward))

    return embolden(rec, ax, 0, factor)


def put(font, up, name, source):
    """A glyph made in the upright frame, slanted into the Italic."""
    import derive
    from glyph_lint import (
        FIXED,
        LEDGE_KEEP,
        ink,
        ledge_findings,
        step_findings,
        vector_findings,
    )

    g = copy.deepcopy(up[name])
    shear(g, SLANT)
    # crumbs the cuts and merges left (specks, pinholes, an outline crossing
    # itself, steps, a curve's end split off at a corner): the outline
    # merged and cleaned (glyph_lint)
    # (again if rounding the merged outline to whole units crossed it anew)
    for _ in range(3):
        if not (g.contours and not g.components):
            break
        path = ink(font, g)
        found = vector_findings(path) + step_findings(path, crumbs=True)
        if name not in LEDGE_KEEP:
            found += ledge_findings(path)
        if not any(k in FIXED for k, *_ in found):
            break
        before = copy.deepcopy(g)
        g.clearContours()
        derive.draw_path(font, before, g, derive.to_path(font, before))
    g.lib[SOURCE_KEY] = source
    font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)


# recipes placed by the Regular's coordinates (attach, curl, graft), and
# hooks on capitals (the Italic's f and ȷ are swashes, its capitals sloped
# romans): transplanted from the Regular instead
TRANSPLANT_OPS = ("attach", "curl", "graft")
LETTERS = {"₨": "Rs"}  # signs that are letters side by side
# ... closer by this much, joined: R's leg runs out into the ball of s
LETTER_JOIN = {"₨": 240}
NO_TRANSPLANT = {"ɞ", "ʝ", "ɕ", "ʂ", "ʑ", "ɚ", "ɝ", "ɮ", "Ɓ", "Ɗ", "Ƥ", "ɺ", "ɰ",
                 "Ƙ", "Ʋ", "Ƴ", "ƴ", "Ƭ", "Ɲ", "Ʈ", "ƥ", "ɖ", "ɗ", "ɭ", "Ɽ",
                 "ң", "ҷ", "қ", "җ", "ҳ", "ɧ", "ɱ", "ɳ", "ɽ", "ɻ", "Ƒ", "Ꞵ", "Ʝ", "ʄ", "ʋ", "ʈ", "Ɦ", "Ⱳ", "Ɠ", "ƈ", "ƃ", "ƛ", "ɹ", "Ƈ", "ⱳ", "ʐ", "г.loclSRB",
                 "ь.loclBGR", "ю.loclBGR", "ж.loclBGR", "ъ.loclBGR", "в.loclBGR"}  # its own recipe fits the Italic better
TRANSPLANT = set()  # other recipes better transplanted
# where ɗ leaves the italic d for ɓ's top: above the bowl, below where ɓ's
# stem begins to bend into its hook (upright frame)
DHOOK_CUT = 1000
# small caps left to FontForge's drafts of the Italic's capitals (as the
# others), not derive.py's recipes: a capital scaled down (ʛ from Ɠ) is
# heavier than the small caps beside it
SC_DRAFTED = {"ɑ.sc", "ɂ.sc", "ʒ.sc", "ʊ.sc", "ʋ.sc", "ⱳ.sc", "ꞵ.sc", "ƭ.sc", "ƙ.sc",
              "ɲ.sc", "ʝ.sc", "ϗ.sc", "ƴ.sc", "ƈ.sc", "ɠ.sc", "ƥ.sc", "ɦ.sc"}
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


ITALIC_RECIPES = {"ɡ": ("alias", "g", None), "ɥ": ("turn", "h", "x"),
                  # ǥ: the single-storey g's bar across its stem below the
                  # baseline, above the hook, as in DejaVu (the roman's
                  # height crossed the tail, easy to miss)
                  "ǥ": ("bar", "g", ("x", -130, "all", (200, 70))),
                  # r without its entry stroke, on a foot serif
                  "ɾ": ("attach", "r", ("x", [(-BIG, 442, 297, BIG)], [("rect", (213, 0, 493, 50), (0, 0), (1, 1, 0, 0))])),
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
                  # z's rising end curls back into a loop and runs down
                  # through its bottom stroke into a tail turning left
                  "ʑ": ("attach", "z", ("x", [(690, 150, BIG, 400)],
                                        [("curl", {"at": ("pt", 727.5, 150, 58), "dir": 66.6, "turn": "ccw",
                                                   "r": (85, 100), "sweep": 205, "ball": 20, "t": (58, 40),
                                                   "lead": 10, "cuts": [(690, -BIG, BIG, 150)]}, (0, 0), (1, 1, 0, 0)),
                                         ("line", ((564.5, 190), (566, 60), 58), (0, 0), (1, 1, 0, 0)),
                                         ("line", ((566, 96), (562, -100), 85), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 562, -100, 85), "dir": 268, "turn": "cw",
                                                   "r": (85, 65), "sweep": 110, "ball": 34, "t": (85, 38)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # z's bottom stroke, where it turns up, turns down instead into a
                  # stem that hooks to the right (as the Regular's and Charis's ʐ),
                  # the stem 110 before the weight pass (0.85 of n after it), run up
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
                  # l on a straight stem to the baseline, Old Standard's ʒ from
                  # it: its entry stroke cut, the end of its diagonal in the stem
                  "ɮ": ("attach", "l", ("x", [(-BIG, -BIG, BIG, 250), (300, -BIG, BIG, 600)],  # l's exit stroke too
                                        [("rect", (176, 0, 292, 260), (0, 0), (1, 1, 0, 0)),
                                         ("uni0292", (240, 0, BIG, BIG), (0, 0), (1, 1, 0, 0)),
                                         ("uni0292", (-BIG, -BIG, BIG, 0), (0, 0), (1, 1, 0, 0)),
                                         # filling the notch where ʒ's diagonal meets its bowl
                                         ("line", ((393, 307), (452, 300), 14), (0, 0), (1, 1, 0, 0)),
                                         ("line", ((390, 300), (430, 300), 10), (0, 0), (1, 1, 0, 0))], 950)),
                  # the stem rising through the top serif and curling over to the left
                  **{ch: ("curl", base, ("c", [(-BIG, 1300, 300, BIG)],
                                         {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                          "sweep": 200, "ball": 90, "t": (166, 60)}))
                     for ch, base in (("Ɓ", "B"), ("Ɗ", "D"), ("Ƥ", "P"))},
                  # the arm or stem itself curling over at the top (its serif
                  # cut away), at its own weight
                  "Ƙ": ("curl", "K", ("c", [(850, 1250, BIG, BIG)],
                                      {"at": ("y", 1250, "last"), "dir": 51, "turn": "cw", "r": (110, 100),
                                       "sweep": 210, "ball": 55, "t": (89, 45)})),
                  "Ʋ": ("curl", "U", ("c", [(930, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", "r": (140, 120),
                                       "sweep": 200, "ball": 50, "t": (64, 40)})),
                  "Ƴ": ("curl", "Y", ("c", [(780, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 62, "turn": "cw", "r": (110, 100),
                                       "sweep": 210, "ball": 50, "t": (68, 40)})),
                  "ƴ": ("curl", "y", ("x", [(700, 760, BIG, BIG)],
                                      {"at": ("y", 760, "last"), "dir": 90, "turn": "cw", "r": (100, 90),
                                       "sweep": 200, "ball": 58, "t": (116, 40)})),  # flush: half the end's 116
                  # p's stem (its entry stroke cut away) rising and curling over
                  "ƥ": ("attach", "p", ("x", [(-BIG, 700, 400, BIG), (-BIG, 400, 270, BIG)],
                                        [("rect", (296, 650, 397, 1150), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 346.5, 1150, 101), "dir": 90, "turn": "cw",
                                                   "r": (150, 130), "sweep": 210, "ball": 55, "t": (101, 45)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # the bar's left end (its serif cut away) curling down; the curl
                  # leaves the bar where it is as thin as the curl (it flares
                  # toward the serif), so they meet without a ledge
                  "Ƭ": ("attach", "T", ("c", [(-BIG, 800, 420, BIG)],
                                        [("curl", {"at": ("pt", 420, 1398, 62), "dir": 180, "turn": "ccw",
                                                   "r": (135, 125), "sweep": 200, "ball": 50, "t": (90, 62),
                                                   "lead": 10, "cuts": [(420, 1300, BIG, BIG)]}, (0, 0), (1, 1, 0, 0))])),
                  # the top hairline rising from where its ball was into a hook
                  # to the right (as Charis and Libertinus)
                  "ƈ": ("attach", "c", ("x", [(540, 450, BIG, BIG)],
                                        [("line", ((515, 858), (560, 1100), 44), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 560, 1100, 44), "dir": 75, "turn": "cw",
                                                   "r": (110, 100), "sweep": 200, "ball": 42, "t": (44, 34),
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
                                                   "r": (105, 95), "sweep": 210, "ball": 40, "t": (36, 30),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # G's spur rising above the cap height into a hook to the right
                  # (as Charis and Libertinus), not curling back over the bowl
                  "Ɠ": ("attach", "G", ("c", [(1080, 1330, BIG, BIG)],
                                        [("line", ((1139, 1320), (1139, 1500), 36), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1139, 1500, 36), "dir": 90, "turn": "cw",
                                                   "r": (105, 95), "sweep": 210, "ball": 40, "t": (36, 30),
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
                  "җ": ("attach", "uni0436", ("x", [(1000, -BIG, BIG, 200), (1350, -BIG, BIG, 450)],
                                              descender(1087.7, 210, 1224.5, -150, 100, 290.8, (100, 90), 40))),
                  "ҳ": ("attach", "uni0445", ("x", [(560, -BIG, BIG, 150), (900, -BIG, BIG, 350)],
                                              descender(612, 155, 810, -150, 58, 303, (90, 80), 34))),
                  # ȷ's descender on the last stem, as ɲ has it on the first: it
                  # thins as the italic stems do (cut in where the stem is as
                  # wide as ɲ's, below its swell; the exit stroke cleared)
                  "ɧ": ("hook", "uni0266", ("x", "down-left", "last", 200, 160, 400, [(780, -BIG, BIG, 450)])),
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
                                                    (-BIG, 410, 362, 474), (483, 410, BIG, 474)],
                                              [("rect", (364, 550, 483, 1150), (0, 0), (1, 1, 0, 0)),
                                               ("rect", (173, 414, 673, 470), (0, 0), (1, 1, 0, 0)),
                                               ("curl", {"at": ("pt", 423.5, 1150, 119), "dir": 90, "turn": "cw",
                                                         "r": (150, 130), "sweep": 210, "ball": 57, "t": (119, 45)},
                                                (0, 0), (1, 1, 0, 0))], 760)),
                  # u's last stem curling over to the left at the top
                  "ʋ": ("curl", "u", ("x", [(700, 700, BIG, BIG)],
                                      {"at": ("y", 700, "last"), "dir": 90, "turn": "ccw", "r": (120, 110),
                                       "sweep": 200, "ball": 55, "t": (120, 42)})),
                  "ʈ": ("attach", "t", ("x", [(-BIG, -BIG, BIG, 300), (300, -BIG, BIG, 600)],
                                        retroflex(232, 232, 350, 116, (110, 100), 45, 40))),
                  # the left stem curling over to the left, as on Ɓ; W's right arm to the right
                  "Ɦ": ("curl", "H", ("c", [(-BIG, 1300, 700, BIG)],
                                      {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                       "sweep": 200, "ball": 90, "t": (164, 60)})),
                  # w's hairline arm (its ball cut away) rising straight to the
                  # x-height and curling over (the Regular's curl, carried
                  # across, left slivers beside the diagonal)
                  "ⱳ": ("attach", "w", ("x", [(1000, 645, BIG, BIG)],
                                        [("line", ((1289, 620), (1287, 770), 54), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1287, 770, 54), "dir": 92, "turn": "cw",
                                                   "r": (105, 95), "sweep": 200, "ball": 45, "t": (54, 36),
                                                   "lead": 6}, (0, 0), (1, 1, 0, 0))])),
                  "Ⱳ": ("curl", "W", ("c", [(1480, 1150, BIG, BIG)],
                                      {"at": ("y", 1150, "last"), "dir": 79, "turn": "cw", "r": (120, 110),
                                       "sweep": 210, "ball": 50, "t": (81, 40)})),
                  # v on a stem under its round bottom
                  "ү": ("descend", "v", ("x", "p")),
                  # Serbian and Macedonian italic (locl SRB, MKD; the
                  # Regular's are its plain letters, ITALIC_LOCL): б leaning
                  # back is Old Standard's д, ∂; д is g; ѓ is ı with the
                  # acute alone, as í
                  "б.loclSRB": ("alias", "uni0434", None),
                  "д.loclSRB": ("alias", "g", None),
                  "ѓ.loclSRB": ("alias", "iacute", None),
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
                  "ж.loclBGR": ("attach", "uni0436", ("x", [(680, 800, 980, BIG)],
                                                       [("l", (-BIG, 790, BIG, BIG), (0, 0), (1, 1, 594, 0))])),
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
                  # г is ī: ı without its entry hook, below where its stem
                  # is as wide as ū's (650), under the top of ū's first stem
                  # with its bar, which overhangs the stem equally each side
                  "г.loclSRB": ("attach", "dotlessi", ("x", [(-BIG, 650, BIG, BIG), (-BIG, 400, 240, BIG)],
                                                        [("uni043F.loclSRB", (-BIG, 645, 497, BIG), (0, 0),
                                                          (1, 1, 82, 0))]))}
# Old Standard's own Serbian italic п and т (ū and ш with the bar above)
OS_LOCL = {"uni043F.loclSRB": "afii10831", "uni0442.loclSRB": "afii10832"}
# aliases of a plain letter in the Regular that the Italic makes itself
ITALIC_LOCL = {"uni0433.loclSRB", "uni0434.loclSRB", "uni0453.loclSRB",
               "uni0438.loclBGR", "uni043F.loclBGR", "uni0442.loclBGR", "uni0448.loclBGR"}


def shifted(path, dx):
    from derive import to_path

    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return to_path(None, rec=rec)


def pathops_empty():
    import pathops

    return pathops.Path()


def derive_rect(x0, y0, x1, y1):
    from derive import rect_path

    return rect_path(x0, y0, x1, y1)


def transplant(up, regular, name, source, curl=False):
    """name as the Regular makes it of source: what the Regular adds (a
    hook) and takes away (a serif), moved onto the same stroke of the
    Italic's source, found where the added part meets the letter, and
    scaled about the join as much as that stroke is lighter in the Italic. A part that
    does not touch the letter (the dot of ʘ) is centred as in the Regular."""
    import derive
    from derive import path_op, to_path

    rs, rt = to_path(regular, regular[source]), to_path(regular, regular[name])
    if rs.bounds == (0, 0, 0, 0):  # drawn from nothing (₪ on space): the Regular's
        g = up[name]
        draw_path(regular, regular[name], g, rt)
        g.width = regular[name].width
        return
    added, removed = path_op(rt, rs, "DIFFERENCE"), path_op(rs, rt, "DIFFERENCE")
    if added.bounds == (0, 0, 0, 0):
        raise ValueError("nothing added")

    def grown(path, by=4):
        out = path
        for d in (-by, by):
            out = path_op(out, shifted(path, d), "UNION")
            rec = RecordingPen()
            path.draw(TransformPen(rec, (1, 0, 0, 1, 0, d)))
            out = path_op(out, to_path(None, rec=rec), "UNION")
        return out

    def strokes_at(font, glyph_name, y):
        xs = ink_slice(font, glyph_name, y + 0.01)
        return list(zip(xs[::2], xs[1::2]))

    join = path_op(grown(added), rs, "INTERSECTION")
    if join.bounds == (0, 0, 0, 0):
        # apart from the letter: where the Regular has it within the ink
        y = (added.bounds[1] + added.bounds[3]) / 2
        r_xs, i_xs = ink_slice(regular, source, y + 0.01), ink_slice(up, source, y + 0.01)
        if not r_xs or not i_xs:
            raise ValueError("no ink beside the part")
        dx = (i_xs[0] + i_xs[-1]) / 2 - (r_xs[0] + r_xs[-1]) / 2
        ratio = 1
    else:
        jx0, jy0, jx1, jy1 = join.bounds
        ax, ay = (jx0 + jx1) / 2, (jy0 + jy1) / 2
        # at the join, or a little up the stroke (a hook at a stem's foot)
        for y in (ay, (ay + jy1) / 2, jy1 - 1, jy1 + 30, jy1 + 80, jy1 + 150):
            r_runs, i_runs = strokes_at(regular, source, y), strokes_at(up, source, y)
            if r_runs and i_runs:
                break
        else:
            raise ValueError("no stroke where the part joins")
        k = min(range(len(r_runs)), key=lambda n: abs((r_runs[n][0] + r_runs[n][1]) / 2 - ax))
        right = ax > (rs.bounds[0] + rs.bounds[2]) / 2
        # the Italic's stroke where the join falls in proportion to the ink
        # (its letters may cross a height more or fewer times)
        (r0, _, r1, _), (i0, _, i1, _) = rs.bounds, to_path(up, up[source]).bounds
        ix = i0 + ((r_runs[k][0] + r_runs[k][1]) / 2 - r0) * (i1 - i0) / (r1 - r0)
        run = min(i_runs, key=lambda r: abs((r[0] + r[1]) / 2 - ix))
        dx = (run[0] + run[1]) / 2 - (r_runs[k][0] + r_runs[k][1]) / 2
        # as much lighter as the stroke it joins, at most as much as the
        # Italic's stems are (a hairline or terminal: just that much; a bar
        # met at its end, whose run is its length, not its weight (ʐ's
        # foot from z's bar): that much too)
        capital = ink_bounds(regular, source)[3] > (XH + CAP) / 2 and source[:1].isupper()
        # the Italic's stems to the Regular's, as they are now (before the
        # weight pass: the part is weighted with the letter)
        ref, h = ("H", CAP / 2) if capital else ("n", XH / 2)
        (a0, a1), (b0, b1) = derive.stems_at(up, ref, h)[0], derive.stems_at(regular, ref, h)[0]
        stems = (a1 - a0) / (b1 - b0)
        w_r, w_i = r_runs[k][1] - r_runs[k][0], run[1] - run[0]
        wider = 1.15 * (208 if capital else 164)  # than any stem of its kind in the Regular
        ratio = stems if w_r < 100 or w_r > wider else min(1, max(stems, w_i / w_r))
        if curl and right:
            # a curl from a terminal (Ƈ Ɠ Ƙ Ƴ): the Italic's stroke ends
            # where it ends, with no beak to cut; the curl starts there, as
            # in the Regular it starts where the stroke ends once cut
            band = derive_rect(-10000, jy0 - 150, 10000, jy1 + 150)
            r_ext = path_op(path_op(rs, removed, "DIFFERENCE"), band, "INTERSECTION").bounds
            i_ext = path_op(to_path(up, up[source]), band, "INTERSECTION").bounds
            if r_ext != (0, 0, 0, 0) and i_ext != (0, 0, 0, 0):
                dx = i_ext[2] - r_ext[2] if right else i_ext[0] - r_ext[0]
            removed = pathops_empty()
    if ratio < 0.97:
        # the part scaled about the join, so it is the Italic's weight (and
        # size) with its hairlines in proportion
        rec = RecordingPen()
        added.draw(TransformPen(rec, (ratio, 0, 0, ratio, ax * (1 - ratio), ay * (1 - ratio))))
        added = to_path(None, rec=rec)
    added = shifted(added, dx)
    letter = to_path(up, up[source])
    if join.bounds != (0, 0, 0, 0) and removed.bounds != (0, 0, 0, 0):
        # only what lies beyond the join, where the part takes the letter's
        # place: what the Regular takes off before it (z's beak, for ʐ) is
        # the Regular's own shape, which the Italic's letter does not have
        beyond = derive_rect(jx0 - 10, -10000, 10000, 10000) if right else derive_rect(-10000, -10000, jx1 + 10, 10000)
        removed = path_op(removed, beyond, "INTERSECTION")
    if removed.bounds != (0, 0, 0, 0):
        # what the Regular cuts away (a serif, a terminal), with room: the
        # Italic's is not quite where the Regular's is; the stroke the part
        # joins is kept
        x0, y0, x1, y1 = shifted(removed, dx).bounds
        cut = derive_rect(x0 - 30, y0 - 30, x1 + 30, y1 + 30)
        if join.bounds != (0, 0, 0, 0):
            cut = path_op(cut, derive_rect(run[0], -10000, run[1], 10000), "DIFFERENCE")
        letter = path_op(letter, cut, "DIFFERENCE")
    if join.bounds != (0, 0, 0, 0):
        # where the part and the letter come within a few units of each
        # other, the gap filled (Old Standard's letters do not all stand at
        # 0, its terminals are not the Regular's)
        bridge = path_op(grown(added, 10), grown(letter, 10), "INTERSECTION")
        added = path_op(added, path_op(bridge, grown(shifted(join, dx), 30),
                                       "INTERSECTION"), "UNION")
    out = path_op(letter, added, "UNION")
    g = up[name]
    draw_path(up, up[source], g, out)
    g.width = up[source].width + max(0, regular[name].width - regular[source].width)
    for a in up[source].anchors:
        g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})


def rhotic(up, source, y):
    """The letter with the rhotic hook (˞) rising from its right side at y:
    the hook's start (its left end) a little inside the stroke."""
    import derive

    ink = ink_bounds(up, "uni02DE")
    sx = ink[0] + 12
    sy = derive.vertical_runs(up, "uni02DE", sx)[0][0]
    tx = derive.stems_at(up, source, y)[-1][1] - 30
    out = derive.attach(up, source, [], [("uni02DE", (-BIG, -BIG, BIG, BIG), (sx, sy), (1, 1, tx, y))])
    return out, round(tx + ink[2] - sx + 70)


def glottal(up, source):
    """ʔ from the italic ?: its stroke cut across where it heads down to the
    left, before it curls, and turned down into a stem to the baseline."""
    import derive
    from fontTools.pens.recordingPen import RecordingPen

    px, py, d = 525, 740, math.radians(213)  # on the stroke, its direction
    ux, uy, vx, vy = math.cos(d), math.sin(d), -math.sin(d), math.cos(d)
    far = 5000
    rec = RecordingPen()  # the half-plane ahead of that point
    rec.moveTo((px + vx * far, py + vy * far))
    rec.lineTo((px + (vx + ux) * far, py + (vy + uy) * far))
    rec.lineTo((px + (ux - vx) * far, py + (uy - vy) * far))
    rec.lineTo((px - vx * far, py - vy * far))
    rec.closePath()
    ahead = derive.path_op(derive.to_path(None, rec=rec), derive.rect_path(-BIG, -BIG, BIG, 820), "INTERSECTION")
    top = derive.path_op(derive.to_path(up, up[source]), ahead, "DIFFERENCE")
    top = derive.path_op(top, derive.rect_path(-BIG, 400, BIG, BIG), "INTERSECTION")  # the dot
    stem = derive.attach(up, "space", [],
                         [("curl", {"at": ("pt", px, py, 112), "dir": 213, "turn": "ccw", "r": 200,
                                    "sweep": 57, "ball": 5, "t": (112, 112), "lead": 0}, (0, 0), (1, 1, 0, 0)),
                          ("line", ((434, 590), (434, 0), 112), (0, 0), (1, 1, 0, 0))])
    return derive.path_op(top, stem, "UNION")


# derived from a glyph kept from the last run, which has its weight
# already: not weighted again (derive_stage fills it)
PREWEIGHTED = set()


def derive_stage(font, regular, late=False, kept=()):
    """derive.py's recipes for the glyphs still sloped roman. Those made
    from a small cap (ɔ.sc from c.sc, ʁ from r.sc) wait for the Italic's
    small caps (smallcaps_stage), late: before it, their sources are the
    Regular's small caps, sloped. Returns what was made, what failed, and
    the names left for the late pass."""
    import derive

    up = upright(font)
    cmap = {u: g.name for g in up for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    # the clicks' bar: upright here, so sloped in the Italic, as heavy
    # against l as the Regular's | against its l
    bar = up.newGlyph("_clickbar")
    bar.width = 512
    def stem(f, name):
        a, b = derive.stems_at(f, name, XH / 2)[0]
        return b - a

    w = stem(regular, "bar") / stem(regular, "l") * stem(up, "l")
    draw_path(up, bar, bar, derive.rect_path(256 - w / 2, -520, 256 + w / 2, CAP))

    made, failed, later = [], [], []
    for ch, op, source, band in derive.RECIPES:
        if ch in SC_DRAFTED:
            continue
        op, source, band = ITALIC_RECIPES.get(ch, (op, source, band))
        name = resolve(ch)
        if name not in font or font[name].lib.get(SOURCE_KEY) != "sloped roman":
            continue
        if len(source) == 1 or (derive.variant(source) and not source[0].isascii()):
            source = resolve(source)
        if source.endswith(".sc") != late:
            if not late:
                later.append(name)
            continue
        if source not in up:
            failed.append(f"{ch}: no {source}")
            continue
        capital = band == "c" or (isinstance(band, tuple) and band[:1] == ("c",))
        # (an alias, г.sc of gamma.sc, has its outline's weight)
        held = source
        while not up[held].contours and len(up[held].components) == 1:
            held = up[held].components[0].baseGlyph
        if held in kept:
            PREWEIGHTED.add(name)
        old = up[name]
        try:
            if ch == "ɗ":
                # the italic d (its bowl, its exit stroke) with ɓ's top: the
                # f-hook recipe does not fit the italic f, and the Regular's
                # hook transplanted leaves d's flag. ɓ's stem above the cut is
                # scaled across onto d's stem edges, so it runs on without a step
                hooked = resolve("ɓ")
                (a0, a1), (b0, b1) = (derive.stems_at(up, source, DHOOK_CUT)[-1],
                                      derive.stems_at(up, hooked, DHOOK_CUT)[0])
                del up[name]
                derive.build(up, ch, "attach", source, (
                    "x", [(-BIG, DHOOK_CUT, BIG, BIG)],
                    [(hooked, (-BIG, DHOOK_CUT - 20, BIG, BIG), (b0, 0), ((a1 - a0) / (b1 - b0), 1, a0, 0))]), name)
            elif op in ("rhotic", "glottal"):
                if op == "rhotic":
                    out, width = rhotic(up, source, band)
                else:
                    out, width = glottal(up, source), up[source].width
                g = up[name]
                g.clearContours()
                g.clearComponents()
                g.clearAnchors()
                draw_path(up, up[source], g, out)
                g.width = width
                for a in up[source].anchors:
                    g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
            elif op == "stem":
                # through the middle, from the descender to the ascender
                ink = ink_bounds(up, source)
                w = derive.stems_at(up, "l", XH / 2)[0]
                cx, half = (ink[0] + ink[2]) / 2, (w[1] - w[0]) / 2
                out = derive.path_op(derive.to_path(up, up[source]),
                                     derive.rect_path(cx - half, -560, cx + half, 1400), "UNION")
                g = up[name]
                g.clearContours()
                g.clearComponents()
                g.clearAnchors()
                draw_path(up, up[source], g, out)
                g.width = up[source].width
                for a in up[source].anchors:
                    g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
            elif ch in LETTERS:
                g = up[name]
                g.clearContours()
                g.clearComponents()
                x = 0
                for k, c in enumerate(LETTERS[ch]):
                    x -= LETTER_JOIN.get(ch, 0) if k else 0
                    g.getPen().addComponent(cmap[ord(c)], (1, 0, 0, 1, x, 0))
                    x += up[cmap[ord(c)]].width
                g.width = x
            elif ((op in TRANSPLANT_OPS or (op == "hook" and capital) or ch in TRANSPLANT) and ch not in NO_TRANSPLANT
                  and source in regular and name in regular):
                g = up[name]
                g.clearContours()
                g.clearComponents()
                g.clearAnchors()
                try:
                    transplant(up, regular, name, source, curl=op == "curl")
                except (IndexError, ValueError):  # the Regular's is not source plus a part
                    del up[name]
                    derive.build(up, ch, op, source, band, name)
            else:
                del up[name]
                derive.build(up, ch, op, source, band, name)
        except (IndexError, KeyError, ValueError, ZeroDivisionError, AttributeError, TypeError) as e:
            # a recipe the Italic's shapes do not fit
            up.layers.defaultLayer.insertGlyph(old, name, overwrite=True)
            failed.append(f"{ch} ({op}): {e!r}")
            continue
        up[name].lib[DRAFT_KEY] = True
        put(font, up, name, "derived")
        made.append(ch)
    return made, failed, later


def figures_stage(font, regular):
    """Old-style figures: the lining ones fitted into the band of the
    Regular's, the stems halfway to the lining weight, hairlines kept."""
    import derive
    from smallcaps import ink_bounds

    up = upright(font)
    made = []
    _, stem, hair = derive.strokes(up, "zero")  # the 1 and 4 have no clear hairline
    for d in FIGURES:
        name = d + "oldstyle"
        if name not in font or font[name].lib.get(SOURCE_KEY) != "sloped roman":
            continue
        target, lining = ink_bounds(regular, name), ink_bounds(up, d)
        k = (target[3] - target[1]) / (lining[3] - lining[1])
        # overlaps removed first (Old Standard's 1 and 4 are drawn in parts)
        merged = derive.path_op(derive.to_path(up, up[d]), derive.to_path(up, up[d]), "UNION")
        rec = RecordingPen()
        merged.draw(TransformPen(derive.CubicPen(rec), (k, 0, 0, k, 0, 0)))
        out = embolden(rec, stem * (1 + k) / 2 - k * stem, hair - k * hair)
        x0, y0, x1, _ = out.getBounds()
        dx = (lining[0] + lining[2]) / 2 - (x0 + x1) / 2
        g = up[name]
        g.clearComponents()
        g.clearAnchors()
        g.clearContours()
        out.draw(TransformPen(g.getPen(), (1, 0, 0, 1, dx, target[1] - y0)))
        g.width = up[d].width
        g.lib[DRAFT_KEY] = True
        put(font, up, name, "figure draft")
        made.append(name)
    return made


def smallcaps_stage(font, later=()):
    """Small caps still sloped roman: FontForge's drafts of the Italic's
    capitals, imported (with their anchors) in the upright frame; not
    those derive_stage makes from them afterwards (later)."""
    import derive
    import smallcaps as sc

    for g in font:
        if ".sc" in g.name and g.lib.get(SOURCE_KEY) == "sloped roman" and g.name not in later:
            g.lib[SMALLCAP_DRAFT_KEY] = True  # to be replaced
            g.lib.pop("org.myiadidot.derived", None)  # the Regular's ɠ.sc is derived; this one is drafted
    up = upright(font)
    work = ROOT / "build/italic"
    work.mkdir(parents=True, exist_ok=True)
    up.features.text = ""  # FontForge only needs the outlines
    up.save(work / "upright.ufo", overwrite=True)
    height = font.lib.get(sc.HEIGHT_KEY, sc.DEFAULT_HEIGHT)
    lc = derive.stems_at(up, "n", XH / 2)[0]
    uc = derive.stems_at(up, "H", CAP - 300)[0]
    lc, uc = lc[1] - lc[0], uc[1] - uc[0]
    stem = lc + (height - XH) / (CAP - XH) * (uc - lc)
    subprocess.run(["fontforge", "-quiet", "-lang=py", "-script", str(ROOT / "scripts/smallcaps_draft.py"),
                    str(work / "upright.ufo"), str(work / "smallcaps.ufo"), str(height), f"{stem:.0f}/{uc:.0f}"],
                   check=True)
    drafts = ufoLib2.Font.open(work / "smallcaps.ufo")
    sc.configure(height)
    log = []
    sc.import_drafts(up, {g.name: g for g in drafts if g.name.endswith(".sc")}, log, redraft=True)
    made = [line.split()[1] for line in log]
    for name in made:
        put(font, up, name, "small cap draft")
    return made


def drop_ligatures(font):
    """The Regular's ligatures Old Standard has no italic for (fb fh fk ft,
    their ff forms, the long-s ones, ct st): an italic f does not clash
    with the next letter, and historical italics had only fi fl ff ffi ffl,
    so the Italic leaves them out, with their rules (and any lookup left
    empty) and their kerning."""
    gone = {g.name for g in font
            if g.lib.get(SOURCE_KEY) == "sloped roman" and "_" in g.name
            and all(p in font for p in g.name.split("_"))}
    for name in gone:
        del font[name]
    font.glyphOrder = [n for n in font.glyphOrder if n not in gone]
    cats = font.lib.get("public.openTypeCategories", {})
    for name in gone:
        cats.pop(name, None)
    for group, members in list(font.groups.items()):
        font.groups[group] = [m for m in members if m not in gone]
    font.kerning = {pair: v for pair, v in font.kerning.items() if not set(pair) & gone}
    names = "|".join(re.escape(n) for n in sorted(gone, key=len, reverse=True))
    rule = re.compile(rf"^\s*sub\b[^;]*\\(?:{names})(?![\w.]).*;\s*$")
    lines = [line for line in font.features.text.splitlines() if not rule.match(line)]
    text = "\n".join(lines) + "\n"
    # lookups with no rule left, and every reference to them
    empty = re.findall(r"^lookup (\w+) \{\s*(?:lookupflag [^;]*;\s*)?\} \1;\n", text, re.MULTILINE)
    for name in empty:
        text = re.sub(rf"^lookup {name} \{{\s*(?:lookupflag [^;]*;\s*)?\}} {name};\n\n?", "", text, flags=re.MULTILINE)
        text = re.sub(rf"^\s*lookup {name};\n", "", text, flags=re.MULTILINE)
    font.features.text = text
    return sorted(gone)


# the Italic's own kerning over the Regular's (measured against italics):
# v w y before round letters less tight (the Regular's -50 left them
# crowded), and f, its top hanging over, closer to the letters with a stem
ITALIC_KERNING = {
    ("public.kern1.v", "public.kern2.c"): -10, ("public.kern1.y", "public.kern2.c"): -10,
    ("f", "public.kern2.i"): -60, ("f", "public.kern2.u"): -60, ("f", "m"): -60, ("f", "p"): -60, ("f", "r"): -60,
    # a's exit stroke rises to the right: before v w less kerning than the Regular's -124
    ("public.kern1.a", "public.kern2.v"): -44,
    # Greek (Old Standard's letters) against Greek references, as the
    # Italic's Latin sets them (scripts/quality/greek_pairs.py)
    ("public.kern1.chi", "public.kern2.epsilontonos"): -47,  # χε (the Regular's -158)
    ("public.kern1.eta", "public.kern2.nu"): 86,  # ην
    ("public.kern1.eta", "public.kern2.rho"): 82,  # ηρ
    ("public.kern1.theta", "public.kern2.nu"): 71,  # θν
    ("public.kern1.alpha", "public.kern2.delta"): -70,  # αθ
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
# the Regular's pairs the Italic does without: tt tf were tightened for the
# roman t (pair review); the italic t's frequent pairs were in range without;
# Cyrillic pairs made for upright forms, in range unkerned in the Italic
# (ду уд уе ул уѫ ъу ѫб оѵ; greek_pairs.py --script cyrillic)
ITALIC_UNKERNED = {("t", "t"), ("t", "f"),
                   ("uni0434", "public.kern2.uni0443"), ("public.kern1.uni0443", "public.kern2.uni0434"),
                   ("public.kern1.uni0443", "public.kern2.uni0435"), ("public.kern1.uni0443", "public.kern2.uni043B"),
                   ("public.kern1.uni0443", "public.kern2.uni046B"), ("public.kern1.uni044A", "public.kern2.uni0443"),
                   ("public.kern1.uni046B", "public.kern2.uni0431"), ("public.kern1.uni043E", "public.kern2.uni0475")}
# ß's left side looser: with the heavier stems it stood tight against the
# letter before it (measured, scripts/quality/colour.py)
# г's ī: its bar starts where ı's entry hook did not (ITALIC_RECIPES)
# ʼ ʻ: the Regular's, sloped about half the x-height, stood far right for
# glyphs this high (ʼl touched): as far from l and i as ’ ‘, upright
ITALIC_SIDEBEARINGS = {"germandbls": (25, 0), "uni0433.loclSRB": (-80, 0),
                       "uni02BC": (-145, 145), "uni02BB": (-130, 130)}
# the horn's foot sunk into the top of u's stem: set on it, it leaves a
# ledge beside the stem (glyph_lint)
HORN_NUDGE = {"u": (-20, -30), "U": (-20, 0), "u.sc": (-20, 0)}
# the Regular's horn, sloped, was lighter and smaller than every reference
# italic's (ơ: 19 % of o's ink, EB Garamond 22, Libertinus 34, Charis 24):
# scaled about its tip (where it attaches), the Bold Italic's with it
ITALIC_HORN = {"horn": 1.2, "Horn": 1.2}


def swapped_sidebearings(font):
    """Side bearings for the derived letters that are their base turned or
    mirrored (as wide in ink, upright): the base's, swapped, measured
    upright, as the Regular's are. A letter made before its base was
    respaced (Ʊ, turned from Ω before the Greek cut widened it) keeps
    the old spacing otherwise. Returns {glyph: (left, right)} deltas for
    sidebearings()."""
    import derive

    cmap = {u: g.name for g in font for u in g.unicodes}

    def upright_sb(name):
        g = copy.deepcopy(font[name])
        shear(g, -SLANT)
        b = g.getBounds(font)
        return (b.xMin, g.width - b.xMax, b.xMax - b.xMin) if b else None

    deltas = {}
    for ch, op, source, band in derive.RECIPES:
        op, source, band = ITALIC_RECIPES.get(ch, (op, source, band))
        if op not in ("turn", "mirror") or len(ch) != 1 or len(source) != 1:
            continue
        name, base = cmap.get(ord(ch)), cmap.get(ord(source))
        if name is None or base is None or font[name].lib.get(SOURCE_KEY) != "derived":
            continue
        mine, theirs = upright_sb(name), upright_sb(base)
        if mine is None or theirs is None or abs(mine[2] - theirs[2]) > 3:
            continue
        left, right = round(theirs[1] - mine[0]), round(theirs[0] - mine[1])
        if left or right:
            deltas[name] = (left, right)
    return deltas


def horn_stage(font, kept=()):
    """The Horn anchors (draft_vietnamese_marks.py) on the Italic's O U o u,
    their small caps and Ư's bases, found on the upright outlines."""
    from draft_vietnamese_marks import HORN_BASES, horn_anchor

    up = upright(font)
    for base in HORN_BASES:
        if base in kept or base not in font:  # its anchor was set when it was made
            continue
        x, y = horn_anchor(up, base)
        dx, dy = HORN_NUDGE.get(base, (0, 0))
        x, y = x + dx, y + dy
        g = font[base]
        for a in [a for a in g.anchors if a.name == "Horn"]:
            g.anchors.remove(a)
        g.appendAnchor({"name": "Horn", "x": round(x + (y - XH / 2) * SLANT), "y": y})


def os_anchor(osg, name):
    for a in osg.anchors:
        if a.name == name:
            return a.x * KX, ymap(a.y)
    return None


# Myia's anchor names, and Old Standard's to take their place from
ANCHOR_SOURCES = {
    "Top": ["Top"], "Acute": ["Top"], "Grave": ["Top"], "Dotaccent": ["Dotaccent", "Top"],
    "TopCap": ["Top"], "Bottom": ["Bottom"], "DotBelow": ["Bottom"], "Cedilla": ["Bottom"],
    "GreekTop": ["GreekTop", "Top"], "GreekCap": ["GreekCap"], "IotaSubscript": ["Bottom"],
}
# anchors moved a little from there (dx, dy): the cedilla's top corner, from
# Old Standard's Bottom of c, would poke out into the counter
ANCHOR_NUDGE = {("c", "Cedilla"): (0, -4), ("e", "Cedilla"): (0, -10)}


def roman_anchor(roman, a, width_it):
    """x of the Regular's anchor a on an italic glyph width_it wide: in
    proportion to the widths, slanted about half the x-height."""
    return a.x * width_it / (roman.width or 1) + (a.y - XH / 2) * SLANT


def missing_anchors(font, regular, marks):
    """The anchors the Regular's glyph has and the Italic's lacks (a turned
    letter takes none from its source, a drafted small cap only its
    capital's), placed as roman_anchor places them; hand-drawn glyphs stay
    as drawn. Returns the names given anchors."""
    given = []
    for g in font:
        if g.name in marks or g.name not in regular or not g.width or g.lib.get(SOURCE_KEY) == "drawn":
            continue
        have = {a.name for a in g.anchors}
        roman = regular[g.name]
        for a in roman.anchors:
            if a.name not in have:
                g.appendAnchor({"name": a.name, "x": round(roman_anchor(roman, a, g.width)), "y": a.y})
                given.append(g.name)
    return sorted(set(given))


def italic_anchors(roman, osg, width_it):
    """Myia's anchors for an Old Standard letter: where Old Standard has the
    anchor (or its stand-in), there, slid along the slant to Myia's height;
    else Myia's, in proportion to the widths and slanted."""
    out = []
    for a in roman.anchors:
        pos = None
        for src in ANCHOR_SOURCES.get(a.name, [a.name]):
            pos = os_anchor(osg, src)
            if pos:
                break
        if pos:
            x = pos[0] + (a.y - pos[1]) * SLANT
        else:
            x = roman_anchor(roman, a, width_it)
        dx, dy = ANCHOR_NUDGE.get((roman.name, a.name), (0, 0))
        out.append((a.name, round(x + dx), a.y + dy))
    return out


def attach(font, glyph_name, mark, bases):
    """The anchor (name, x in the composite) a mark component sits on: the
    base anchor nearest to the mark's ink (as in make_bold)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    if ink is None:
        return None
    mx = mark.transformation[4] + (ink[0] + ink[2]) / 2
    my = mark.transformation[5] + (ink[1] + ink[3]) / 2
    # the anchors this mark attaches to (those of the combining marks made
    # of it, without the underscore); any if none is known
    names = set()
    for g in font:
        if g.width == 0 and len(g.components) == 1 and g.components[0].baseGlyph == mark.baseGlyph:
            names |= {a.name[1:] for a in g.anchors if a.name.startswith("_") and "Mark" not in a.name}
    best = None
    for base, bdx, bdy in bases:
        for a in font[base].anchors:
            if a.name.startswith("_") or (names and a.name not in names):
                continue
            d = abs(a.x + bdx - mx) + abs(a.y + bdy - my)
            if best is None or d < best[0]:
                best = (d, base, a.name)
    return best[1:] if best else None


# the breathings and accents set before a Greek capital (Ἀ Ἔ Ὦ ...), and
# the composite measured for each capital
GREEK_CAP_SAMPLES = {"Alpha": "uni1F08", "Epsilon": "uni1F18", "Eta": "uni1F28", "Iota": "uni1F38",
                     "Omicron": "uni1F48", "Rho": "uni1FEC", "Upsilon": "uni1F59", "Omegagreek": "uni1F68"}


def greek_cap_room(font, regular):
    """Old Standard's GreekCap anchors leave a breathing far from its
    capital (Ἀ about twice the Regular's white): each capital's mark is
    brought as near as it stands in the Regular, judged upright (the
    letter's leftmost ink against the mark's), and the capital moved left
    by as much, in its composites (with what follows it: ᾈ's iota) and in
    the room the GreekCapsafter... lookups make for a combining mark, so
    that the decomposed text sets the same. Returns {capital: shift}."""
    def left(f, c, slant):
        pen = BoundsPen(f)
        f[c.baseGlyph].draw(TransformPen(TransformPen(pen, (1, 0, -slant, 1, 0, 0)), c.transformation))
        return pen.bounds[0]

    def spread(f, name, base, slant):
        comps = f[name].components
        b = next(c for c in comps if c.baseGlyph == base)
        m = next(c for c in comps if c.baseGlyph != base)
        return left(f, b, slant) - left(f, m, slant)

    shift = {}
    for base, sample in GREEK_CAP_SAMPLES.items():
        if sample in font and sample in regular:
            shift[base] = round(spread(font, sample, base, SLANT) - spread(regular, sample, base, 0))
    for base, d in shift.items():
        for a in font[base].anchors:
            if a.name == "GreekCap":
                a.x += d
    for g in font:
        if g.unicode is None or not g.components or g.contours:
            continue
        if not unicodedata.name(chr(g.unicode), "").startswith("GREEK CAPITAL"):
            continue
        caps = [c for c in g.components if c.baseGlyph in shift]
        if len(caps) != 1 or caps[0].transformation[4] <= 0:
            continue  # no room made before the capital
        cap = caps[0]
        x0, d = cap.transformation[4], shift[cap.baseGlyph]
        for c in g.components:
            t = c.transformation
            if t[4] >= x0:
                c.transformation = (t[0], t[1], t[2], t[3], t[4] - d, t[5])
        g.width -= d
    rule = re.compile(r"(lookup GreekCapsafter\w+ \{.*?\} GreekCapsafter\w+;)", re.DOTALL)
    pos = re.compile(r"pos \\(\w+) <(-?\d+) 0 (-?\d+) 0>;")

    def room(m):
        return pos.sub(lambda p: (f"pos \\{p[1]} <{int(p[2]) - shift.get(p[1], 0)} 0 "
                                  f"{int(p[3]) - shift.get(p[1], 0)} 0>;"), m[1])

    font.features.text = rule.sub(room, font.features.text)
    return shift


def move_parts(font, regular, marks, rule_made):
    """The composites the rules do not make keep their parts: their marks
    moved as the base anchor they sit on moved, later letters with the
    first's change of width, the width following the base."""
    for g in font:
        if not g.components or g.contours or g.name in rule_made or g.name in marks:
            continue
        rg = regular[g.name]
        bases = [(c.baseGlyph, c.transformation[4], c.transformation[5])
                 for c in rg.components if c.baseGlyph not in marks]
        if not bases:
            continue
        first = bases[0][0]
        for c, rc in zip(g.components, rg.components, strict=True):
            xx, xy, yx, yy, dx, dy = rc.transformation
            if c.baseGlyph in marks:
                hit = attach(regular, g.name, rc, bases)
                if hit:
                    base, anchor = hit
                    ra = {a.name: (a.x, a.y) for a in regular[base].anchors}.get(anchor)
                    ia = {a.name: a.x for a in font[base].anchors}.get(anchor)
                    if ra is not None and ia is not None:
                        # the base anchor moved; the sloped mark's own anchor
                        # moved by its height along the slant
                        dx = dx + ia - ra[0] - ra[1] * SLANT
            elif dx:
                # a second letter (Ĳ, ...) or room for an accent (Έ): letters
                # after the first move with the first's change of width
                if rg.components[0].baseGlyph != c.baseGlyph and dx >= regular[first].width:
                    dx = dx + font[first].width - regular[first].width
            c.transformation = (xx, xy, yx, yy, round(dx), dy)
        room = [(base, dx) for base, dx, _ in bases if dx > 0]
        if len(bases) == 1 and room and rg.width == regular[room[0][0]].width + room[0][1]:
            g.width = font[room[0][0]].width + room[0][1]
        elif len(bases) == 1:
            g.width = font[first].width + (rg.width - regular[first].width)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("italic", nargs="?", default=str(ROOT / "sources/MyiaDidot-Italic.ufo"))
    args = ap.parse_args()
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    # the Regular as it was spaced before respace.py: the offsets and widths
    # taken from it below were tuned on that; the Italic has its own cut
    undo(regular)
    undo(font)
    kern_clear.undo(font)  # the Regular's loosened pairs: the Italic finds its own
    oldstd = source_font()
    previous = ufoLib2.Font.open(args.italic) if (Path(args.italic) / "metainfo.plist").exists() else None
    os_cmap = {u: g.name for g in oldstd for u in g.unicodes}

    marks = {g.name for g in regular if mark_like(g)}
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            marks.add(g.components[0].baseGlyph)

    # composites the rules make as they are: rebuilt from the Italic's anchors
    builder = Builder(regular)
    rule_made = set()
    for g in regular:
        if not g.components or g.contours or g.unicode is None or g.name in SPECIAL:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = builder.recipe(g.unicode)
        except ValueError:
            continue
        mine = sorted((c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components)
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) == mine:
            rule_made.add(g.name)

    taken, kept_roman = 0, 0
    for g in font:
        osname = os_cmap.get(g.unicode) if g.unicode is not None else (g.name if g.name in oldstd else None)
        osname = OS_LOCL.get(g.name, osname)
        if g.name in ITALIC_LOCL:
            # made below by its italic recipe, as what Old Standard lacks
            g.clearComponents()
            g.lib[SOURCE_KEY] = "sloped roman"
            continue
        if g.unicode is not None and (keeps_upright(g.unicode) or g.unicode in ROMAN_SIGNS):
            osname = None  # Myia's own, upright or sloped (below)
        if g.name in marks:
            # Myia's accents, sloped about the height they sit at
            t = sloped(0)
            if g.name in ITALIC_HORN:
                k = ITALIC_HORN[g.name]
                t = (k, 0, SLANT * k, k, 440 * (1 - k), 0)  # scaled about (440, 0), then sloped
            if g.contours:
                rec = RecordingPen()
                for c in g.contours:
                    c.draw(rec)
                out = ufoLib2.objects.Glyph()
                rec.replay(TransformPen(out.getPen(), t))
                redraw(g, out)
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, round(dx + dy * SLANT), dy)
            for a in g.anchors:
                a.x = round(a.x + a.y * SLANT)
        elif osname and (not (g.components and not g.contours) or g.name in OS_LOCL):
            # an Old Standard letter, unless Myia makes this glyph of others
            # (an alias, an accented letter rebuilt below)
            osg = oldstd[osname]
            rec = DecomposingRecordingPen(oldstd)
            osg.draw(rec)
            zoned = RecordingPen()
            rec.replay(Zones(zoned))
            out = rezone(embolden(zoned, AX, AY), AY)  # the flat edges kept on the zones
            anchors = italic_anchors(regular[g.name], osg, osg.width * KX)
            g.clearComponents()
            redraw(g, out)
            g.width = round(osg.width * KX)
            if not g.width and regular[g.name].width:
                # Old Standard's paragraphos ⸏ ⸐ ⸑ hang at zero width; the
                # Regular gives them an advance (fontbakery: base_has_width)
                g.width = regular[g.name].width
            g.clearAnchors()
            for name, x, y in anchors:
                g.appendAnchor({"name": name, "x": x, "y": y})
            g.lib["org.myiadidot.italicSource"] = "Old Standard"
            if g.unicode and (0x2100 <= g.unicode <= 0x214F or 0x1D400 <= g.unicode <= 0x1D7FF):
                shear(g, SLANT)  # its mathematical letters (𝔐 ℵ) are upright
            taken += 1
        elif g.contours:
            # not in Old Standard: Myia's roman, sloped about half the x-height
            t = sloped(XH / 2)
            rec = RecordingPen()
            for c in g.contours:
                c.draw(rec)
            out = ufoLib2.objects.Glyph()
            rec.replay(TransformPen(out.getPen(), t))
            redraw(g, out)
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, round(dx + dy * SLANT), dy)
            for a in g.anchors:
                a.x = round(a.x + (a.y - XH / 2) * SLANT)
            g.lib["org.myiadidot.italicSource"] = "sloped roman"
            kept_roman += 1

    # what was reviewed or drawn in the Italic stays
    # (and the Italic's own, reviewed: ʀ.sc, drafted from its Ʀ, is not in the Regular)
    kept = [g.name for g in (previous or []) if reviewed(g)
            and (g.name in font or g.name.endswith(".sc"))]
    for name in kept:
        font.layers.defaultLayer.insertGlyph(copy.deepcopy(previous[name]), name, overwrite=True)
    # what Old Standard lacks, made from what it has
    upright_signs = 0
    for g in list(font):
        if g.unicode is not None and g.lib.get(SOURCE_KEY) == "sloped roman" and keeps_upright(g.unicode):
            r = copy.deepcopy(regular[g.name])
            r.lib[SOURCE_KEY] = "roman"
            font.layers.defaultLayer.insertGlyph(r, g.name, overwrite=True)
            upright_signs += 1
    derived, failed, later = derive_stage(font, regular, kept=kept)
    figures = figures_stage(font, regular)
    small_caps = smallcaps_stage(font, later)
    # a small cap the Regular lacks (ʀ.sc, drafted from the Italic's own Ʀ):
    # in the glyph order after its letter, a base glyph
    order = list(font.glyphOrder)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    for name in sorted(g.name for g in font if g.name not in order):
        stem = name.split(".")[0]
        order.insert(order.index(stem) + 1 if stem in order else len(order), name)
        cats.setdefault(name, "base")
    font.glyphOrder = order
    derived_late, failed_late, _ = derive_stage(font, regular, late=True, kept=kept)
    derived += derived_late
    failed += failed_late
    horn_stage(font, kept)
    ligatures = drop_ligatures(font)
    font.kerning.update(ITALIC_KERNING)
    for pair in ITALIC_UNKERNED:
        font.kerning.pop(pair, None)
    still = sorted(g.name for g in font if g.lib.get(SOURCE_KEY) == "sloped roman")

    # aliases (one letter, unmoved: Cyrillic Е is E) show the Italic letter:
    # its width and its anchors, before anything is built from them
    for g in font:
        if (len(g.components) == 1 and not g.contours and g.name not in marks and g.name not in kept
                and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            src = font[g.components[0].baseGlyph]
            g.width = src.width
            if {a.name for a in g.anchors} <= {a.name for a in src.anchors} or not g.anchors:
                g.clearAnchors()
                for a in src.anchors:
                    g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})

    # letters Old Standard draws with their accent in one outline (Ť): made
    # from base and mark like the decomposed text (not upstream's specials)
    log = []
    stack_anchors(font, log)
    b = Builder(font)
    exceptions = {line.split()[0] for line in (ROOT / "tests/data/nfd-exceptions.txt").read_text().splitlines()
                  if line.startswith("U+")}
    for g in list(font):
        if (g.unicode is None or not g.contours or g.components or g.name in SPECIAL
                or f"U+{g.unicode:04X}" in exceptions or g.lib.get("org.myiadidot.italicSource") != "Old Standard"):
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = g.name, dict(g.lib)
        del font[g.name]
        b.write(r)
        font[r.name].lib.update(lib)

    # composites: the others first (i, made of ı and a dot, is a base of the
    # rules' ones), then those of the rules rebuilt, then the others again
    move_parts(font, regular, marks, rule_made)
    rebuilt = 0
    for name in sorted(rule_made):
        g = font[name]
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = name, dict(g.lib)
        del font[name]
        b.write(r)
        font[name].lib.update(lib)
        rebuilt += 1
    move_parts(font, regular, marks, rule_made)
    greek_shift = greek_cap_room(font, regular)  # the breathings nearer their capitals
    info = font.info
    info.styleName = "Italic"
    info.styleMapStyleName = "italic"
    info.italicAngle = -ANGLE
    info.postscriptFontName = "MyiaDidot-Italic"
    info.postscriptFullName = "Myia Didot Italic"
    info.copyright = info.copyright.replace(
        " Copyright 2012", " Copyright 2006-2008 Alexey Kryukov (Old Standard Italic). Copyright 2012", 1)
    # (the italic bit comes from styleMapStyleName; USE_TYPO_METRICS stays)
    font.lib.pop("org.myiadidot.figuresLightened", None)  # the Regular's (lighten_figures.py), not these
    font.lib["org.myiadidot.italicSource"] = "Old Standard Italic, akryukov/oldstand (see sources/oldstand/COMMIT)"
    # Old Standard's outlines crossing themselves at serif tips, crumbs of
    # the cuts (glyph_lint); hand-drawn glyphs stay as drawn
    from glyph_lint import fix

    # the added weight (WEIGHT), on the outlines of the letters, the accents
    # and upright signs left as they are
    before = copy.deepcopy(font)
    for g in font:
        # (not those kept from the last run, nor those made from them: they have it)
        if (g.contours and g.name not in marks and g.name not in kept and g.name not in PREWEIGHTED
                and g.lib.get(SOURCE_KEY) in WEIGHTED):
            rec = RecordingPen()
            for c in g.contours:
                c.draw(rec)
            g.clearContours()
            weight_thick(rec, WEIGHT).draw(g.getPen())
    # a derived letter weighted on its own thickens at its junctions unlike
    # its base (ɨ's bar, Ⱦ's slash): made of the weighted base instead, as
    # the Bold's are (make_bold.follow_bases)
    from make_bold import follow_bases

    whole = {}
    followed = follow_bases(before, font, True, kx=1, slant=SLANT, skip=set(kept) | PREWEIGHTED, whole=whole)
    # (those kept from the last run were weighted as they were then)
    last = previous.lib.get(WHOLE_KEY, {}) if previous else {}
    whole.update((n, why) for n, why in last.items() if n in kept and n in font)
    font.lib[WHOLE_KEY] = dict(sorted(whole.items()))
    cleaned = fix(font, [g.name for g in font if g.lib.get(SOURCE_KEY) != "drawn"])
    # the letters spaced tighter (scripts/respace.py), not those kept from the
    # last run, which were (what comes from the Regular has its cut too)
    letter_cut = classifier(font, ITALIC_CUT, ITALIC_CUT_GREEK)
    # what is made only of kept glyphs (their aliases, accented forms) has
    # the cut through them: not cut again; the kept ones not touched at all
    settled = set(kept)
    grew = True
    while grew:
        grew = False
        for g in font:
            if (g.name not in settled and g.components and not g.contours
                    and all(c.baseGlyph in settled or c.baseGlyph in marks for c in g.components)
                    and any(c.baseGlyph in settled for c in g.components)):
                settled.add(g.name)
                grew = True
    respace(font, lambda n: 0 if n in settled else letter_cut(n), [g.name for g in font if g.name not in kept])
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)
    sidebearings(font, swapped_sidebearings(font))
    sidebearings(font, ITALIC_SIDEBEARINGS)
    # an alias a recipe made (Serbian д of g) follows its letter's final width,
    # as derive.py's do in the Regular
    for g in font:
        if (g.lib.get(SOURCE_KEY) == "derived" and g.name not in kept and len(g.components) == 1
                and not g.contours and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            g.width = font[g.components[0].baseGlyph].width
    # the kept ones as they were (the side bearings above, respace carrying
    # composites along, moved them again each run: г.loclSRB -80 a run);
    # an alias still as wide as its letter
    for name in kept:
        g = copy.deepcopy(previous[name])
        if len(g.components) == 1 and not g.contours and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0):
            g.width = font[g.components[0].baseGlyph].width
        font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)
    font.lib[CUT_KEY] ={"cut": ITALIC_CUT, "greekLower": ITALIC_CUT_GREEK}
    anchored = missing_anchors(font, regular, marks)
    case_forms.make(font)  # punctuation raised onto the capitals (case), on the final widths
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.italic))
    # the accented small caps and the smcp/c2sc features, from the new drafts
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts/smallcaps.py"), args.italic], check=True)
    print(f"{args.italic}: {taken} from Old Standard, {len(kept)} kept as reviewed, "
          f"{upright_signs} signs upright, {len(derived)} derived, {len(figures)} figures, "
          f"{len(small_caps)} small caps drafted, {len(ligatures)} ligatures left out, {rebuilt} composites rebuilt, "
          f"{len(followed)} made of their weighted base, {len(cleaned)} cleaned, "
          f"{len(anchored)} given the Regular's anchors they lacked; "
          f"{len(still)} still sloped roman (of {kept_roman}); Greek capitals' marks nearer: "
          + " ".join(f"{n} {d}" for n, d in greek_shift.items()))
    for line in failed:
        print("  recipe failed:", line)
    print("  still sloped roman:", " ".join(still))


if __name__ == "__main__":
    main()
