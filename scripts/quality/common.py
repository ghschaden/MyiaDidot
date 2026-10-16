"""Shared measuring for the quality evaluation (scripts/quality/).

The scripts compare Myia's fonts (fonts/otf, built with `make`) with
reference fonts: Didots (Bodoni Moda at its 11 pt size, Libre Bodoni,
Old Standard, GFS Didot) fetched once into build/refs/ by fetch_refs.py,
and text faces from the system (Libertinus, Charis) where installed, and
EB Garamond. A reference missing is left out. Outlines are measured
deslanted by the font's italic angle.
"""

import math
import subprocess
from pathlib import Path

import pathops
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent.parent
REFDIR = ROOT / "build" / "refs"
OUT = ROOT / "build" / "quality"
MYIA = str(ROOT / "fonts" / "otf" / "MyiaDidot-{}.otf")


def system_font(pattern):
    try:
        path = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True,
                              check=False).stdout
    except FileNotFoundError:
        return None
    family = pattern.split(":")[0].split()[0].lower()
    return path if path and family in Path(path).name.lower() else None


def _refs(style):
    names = {
        "Regular": ["BodoniModa-11-Regular", "LibreBodoni-Regular", "OldStandard-Regular",
                    "EBGaramond-Regular", "GFSDidot-Regular"],
        "Italic": ["BodoniModa-11-Italic", "LibreBodoni-Italic", "OldStandard-Italic", "EBGaramond-Italic"],
        "Bold": ["BodoniModa-11-Bold", "LibreBodoni-Bold", "OldStandard-Bold", "EBGaramond-Bold"],
        "BoldItalic": ["BodoniModa-11-BoldItalic", "LibreBodoni-BoldItalic", "EBGaramond-BoldItalic"],
    }[style]
    paths = [str(REFDIR / f"{n}.ttf") for n in names if (REFDIR / f"{n}.ttf").exists()]
    variant = {"Regular": "", "Italic": ":style=Italic", "Bold": ":style=Bold", "BoldItalic": ":style=Bold Italic"}[style]
    for family in ("Libertinus Serif", "Charis SIL"):
        p = system_font(family + variant)
        if p:
            paths.append(p)
    return paths


REFS = {style: _refs(style) for style in ("Regular", "Italic", "Bold", "BoldItalic")}
SETS = {
    "latin-lc": "abcdefghijklmnopqrstuvwxyzßæœøðþıȷ",
    "latin-uc": "ABCDEFGHIJKLMNOPQRSTUVWXYZÆŒØÐÞ",
    "figures": "0123456789",
    "greek-lc": "αβγδεζηθικλμνξοπρσςτυφχψω",
    "greek-uc": "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
    "cyr-lc": "абвгдежзийклмнопрстуфхцчшщъыьэюяёђѓєѕіїјљњћќўџ",
    "cyr-uc": "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЁЂЃЄЅІЇЈЉЊЋЌЎЏ",
}
# running text in five scripts and languages (evenness.py, pairs.py)
TEXTS = {
    "en": "When the Didot family set up their presses in Paris in the last decades of the eighteenth century the printed page in France had already been through two hundred years of quiet change and almost nobody outside the trade noticed what happened next",
    "fr": "Les Didot étaient à la fois imprimeurs libraires fondeurs et fabricants de papier et c’est sans doute cette réunion des métiers qui leur a permis d’aller si loin quand on fabrique soi-même le papier",
    "de": "Bis weit ins neunzehnte Jahrhundert hinein wurden die meisten Bücher in Fraktur gesetzt und die runde helle Schrift aus Paris galt vielen Lesern als fremd ja als Zeichen einer Gesinnung",
    "el": "Ο Φιρμέν Ντιντό χάραξε ελληνικά στοιχεία για να σταθούν δίπλα στα λατινικά του και εγκατέλειψε τα περισσότερα από τα συμπλέγματα των παλαιότερων στοιχείων",
    "ru": "Гражданский шрифт введённый Петром Великим в тысяча семьсот восьмом году был сам создан по образцу голландских антикв своего времени и следовал за латиницей",
}
REF_CHAR = {"latin-lc": "n", "latin-uc": "H", "figures": "0", "greek-lc": "ν", "greek-uc": "Η",
            "cyr-lc": "н", "cyr-uc": "Н"}


class Face:
    """A font's outlines by character, merged and deslanted."""

    def __init__(self, path):
        self.file = path
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.slant = -math.tan(math.radians(self.f["post"].italicAngle))
        self.xh = self.top("x")
        self.cap = self.top("H")
        self.name = Path(path).stem
        self._p = {}

    def has(self, ch):
        return ord(ch) in self.cmap

    def top(self, ch):
        b = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(b)
        return b.bounds[3]

    def path(self, ch, deslant=True):
        key = (ch, deslant)
        if key not in self._p:
            p = pathops.Path()
            pen = p.getPen(glyphSet=self.gs)
            g = self.gs[self.cmap[ord(ch)]]
            g.draw(TransformPen(pen, (1, 0, -self.slant if deslant else 0, 1, 0, 0)))
            self._p[key] = pathops.simplify(p)
        return self._p[key]

    def width(self, ch):
        return self.gs[self.cmap[ord(ch)]].width


def band(path, y0, y1, x0=-9000, x1=9000):
    """The part of path between y0 and y1 (and x0, x1)."""
    r = pathops.Path()
    pen = r.getPen()
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    return pathops.op(path, r, pathops.PathOp.INTERSECTION)


def runs(path, y):
    """(x0, x1) of the ink crossed at height y, left to right."""
    q = band(path, y - 0.5, y + 0.5)
    return sorted((c.bounds[0], c.bounds[2]) for c in q.contours)


def side(path, w, h, which, depth=0.2, steps=40):
    """Optical side space ("L" or "R"): the white between the sidebearing
    line and the ink, averaged over the zone 0..h, each depth clipped at
    depth x h beyond the nearest point (white deep in a counter counts no more)."""
    vals = []
    for i in range(steps):
        rr = runs(path, h * (i + 0.5) / steps)
        vals.append(None if not rr else (rr[0][0] if which == "L" else w - rr[-1][1]))
    real = [v for v in vals if v is not None]
    if not real:
        return None
    near = min(real)
    return sum(min(v, near + depth * h) if v is not None else near + depth * h for v in vals) / steps


def zone_of(setname, face):
    return face.cap if setname.endswith("uc") or setname == "figures" else face.xh
