"""Recipe bands that read their base (2026-11-27; TODO.md, "Recipes that read
their bases, family by family").

A recipe's band (derive.build's third element) copied its base's numbers: a
stem's centre and width, where a curl starts, cut boxes on the stem's edges.
When the base moved the copies went stale silently (step C: ɮ ɭ ʈ ƃ, found
only by a sweep, 2026-11-26). A band here is a callable

    band(up, source, name) -> the band derive.build takes

called by make_bold.rederive and scripts/only_glyph.py, `up` the style in
the recipes' upright frame, `source` the style it is generated from, `name`
the glyph's name. Every number that belongs to the base is measured in `up`
(derive.stems_at), as make_bold.lezh_band does; what is the family's (a
depth, the style's curl) is one constant.

Tail: a base's stem or leg run on below a cut and curled through 170 degrees
into a ball, right (ccw) for the retroflex tails (ɖ ɭ ɳ ʈ ɻ Ɽ Ʈ ɽ.sc ʈ.sc),
left (cw) for the Cyrillic descenders. Family rule: the ball as heavy as the
tail's stroke (half of it as a radius), the depth the source glyph's (the
Bold Italic keeps the Italic's, as the Bold the Regular's: the designer,
2026-11-26, option A).
"""

import math
from dataclasses import dataclass

BIG = 10000

# a style's reference curl at its stroke: radii and hairline scale with the
# stem, the ball (a radius) is `ball` of the stroke. The Bold Italic's is
# Ʈ's: 195/170 on a stroke of 290, hairline 60, ball half the stroke
BOLD_ITALIC_CURL = {"stroke": 290, "r": (195, 170), "th": 60, "ball": 0.5}
# a measured stem's width against o's stem: outside it, the band picked the
# wrong run (a hairline, a serif, two stems merged)
STEM_RANGE = (0.6, 1.4)


def rel(v, x):
    """a cut box's x counted from the stem's centre x (+-BIG: open)"""
    return v if abs(v) >= BIG else x + v


@dataclass(frozen=True)
class Tail:
    """the stem of `base` measured at `stem_y` (its `pick`th ink run in the
    upright frame, where it runs straight, not at a serif's bracket); a line
    from `top` down to where the curl must start for the tail to reach its
    depth, as wide as the stem; the curl `ref` scaled to the stem, or its own
    radii `r`, hairline `th`, ball `ball`. `cuts` are derive.attach's boxes
    (x0, y0, x1, y1), each x within +-BIG counted from the stem's centre.

    The ring's lowest point lies b + t_h / 2 below the curl's start (b its
    vertical radius, t_h the hairline across), for either turn: the curl
    starts at -(depth - b - t_h / 2), rounded away from zero."""

    base: str
    stem_y: float
    top: float
    cuts: tuple
    pick: int = 0  # which ink run at stem_y, left to right (n d ɹ: 1, the leg, not the exit hairline)
    frame: str = "x"
    ref: dict | None = None  # the style's curl (None: BOLD_ITALIC_CURL)
    r: tuple | None = None  # radii of its own, not ref's scaled
    th: float | None = None  # a hairline of its own
    ball: float | None = None  # a ball of its own (a radius)
    depth: float | None = None  # the family's depth; None: the source glyph's
    turn: str = "ccw"  # ccw: curling right (retroflex); cw: left (descenders)

    def stem(self, up):
        """the stem's centre and width; refused when the run picked is no
        stem (2026-11-27: the draft's pick -1 took n's exit hairline, 63
        units, for its leg)"""
        import derive

        runs = derive.stems_at(up, self.base, self.stem_y)
        x0, x1 = runs[self.pick]
        o = derive.strokes(up, "o")[1]
        if not STEM_RANGE[0] * o <= x1 - x0 <= STEM_RANGE[1] * o:
            raise ValueError(f"Tail on {self.base}: the run picked at y {self.stem_y} ({self.pick} of "
                             f"{[(round(a), round(b)) for a, b in runs]}) is {x1 - x0:.0f} wide, o's stem {o:.0f}")
        return (x0 + x1) / 2, x1 - x0

    def curl(self, w):
        ref = self.ref or BOLD_ITALIC_CURL
        k = w / ref["stroke"]
        r = self.r or tuple(round(v * k) for v in ref["r"])
        th = self.th or round(ref["th"] * k)
        ball = self.ball or round(w * ref["ball"])
        return r, th, ball

    def depth_of(self, source, name):
        if self.depth is not None:
            return self.depth
        from fontTools.pens.boundsPen import BoundsPen

        pen = BoundsPen(source)
        source[name].draw(pen)
        return -pen.bounds[1]

    def __call__(self, up, source, name):
        import derive

        stems, hairs = up.lib.get(derive.STROKE_KEY, (1, 1))
        x, w = self.stem(up)
        w /= stems  # (derive.attach draws it at stems times this)
        x, w = round(x * 2) / 2, round(w * 2) / 2  # (the recipes' half units)
        r, th, ball = self.curl(w)
        drawn_th = th * (stems if th >= 100 else hairs)  # (as derive.attach scales it)
        y = -math.ceil(round(self.depth_of(source, name)) - r[1] - drawn_th / 2)
        boxes = [(rel(x0, x), y0, rel(x1, x), y1) for x0, y0, x1, y1 in self.cuts]
        curl = {"at": ("pt", x, y, w), "dir": 270, "turn": self.turn, "r": r,
                "sweep": 170, "ball": ball, "t": (w, th)}
        return (self.frame, boxes,
                [("line", ((x, self.top), (x, y), w), (0, 0), (1, 1, 0, 0)),
                 ("curl", curl, (0, 0), (1, 1, 0, 0))])
