"""! ? ¡ ¿ from Old Standard Regular, and ʔ made again on the new ?
(the designer, 2026-11-24).

    python scripts/regular_signs.py UFO [--glottal]

(--glottal: step 3 alone.)

Theano's ? was a round head on a straight hairline stem, light beside its
!: ink(!)/ink(?) 1.04 in the Regular (1.08 in the Bold), where every
reference has 0.72-0.88 and our italics, whose signs were redrawn from Old
Standard on 2026-11-16, 0.78. Option B of
build/pending/exclam-question-options-2026-11-24.pdf, chosen and approved
on proofs/2026-11/exclam-question-B-2026-11-24.pdf:

1. ! ? ¡ ¿ taken from Old Standard Regular (its CFF OTF, the TTF's
   outlines), scaled to the Regular's cap height, their side bearings
   with them; Old Standard's own ¡ ¿; turned to the Regular's contour
   direction (clockwise).
2. Redrawn onto clean nodes (redraw.py --install, tolerance 2), its
   record's source "Old Standard"; no "drawn" mark (the Regular is the
   master: nothing makes it again).
3. ʔ made again (data_regular.py: derive.glottal_stem, the new ?'s head on
   ı's stem and foot serif; proofs/2026-11/glottal-serif-trial-2026-11-24.pdf),
   and what is made of it: Ɂ ʕ ʡ ʢ ɂ ˀ ˁ ɂ.sc.
4. ǃ (the click, ! as a component) spaced again around the new !: 106 a
   side, as the spacing of 2026-10-16 left it.

Then make normalize; check-regular reruns kern_clear (its record undone
first: the signs' clearances follow their new shapes) and case_forms (¡ ¿'s
case forms).
"""
import subprocess
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regular_attach import rederive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OLD_STANDARD = Path("/usr/share/texmf-dist/fonts/opentype/public/oldstandard/OldStandard-Regular.otf")
SIGNS = {"exclam": "!", "question": "?", "exclamdown": "¡", "questiondown": "¿"}
DATE = "2026-11-24"
REVIEW = "proofs/2026-11/exclam-question-B-2026-11-24.pdf"
REDRAWN_KEY = "org.myiadidot.redrawn"
DRAWN_KEY = "org.myiadidot.drawn"
CLICK, CLICK_SIDE = "uni01C3", 106
GLOTTAL = {"uni0294": "ʔ", "uni0241": "Ɂ", "uni0295": "ʕ", "uni02A1": "ʡ", "uni02A2": "ʢ",
           "uni0242": "ɂ", "uni02C0": "ˀ", "uni02C1": "ˁ", "uni0242.sc": "ɂ.sc"}


def take(path):
    """step 1"""
    t = TTFont(OLD_STANDARD)
    gs, cmap = t.getGlyphSet(), t.getBestCmap()
    font = ufoLib2.Font.open(path)
    k = font.info.capHeight / t["OS/2"].sCapHeight
    for name, ch in SIGNS.items():
        src, g = gs[cmap[ord(ch)]], font[name]
        g.clearContours()
        g.clearComponents()
        # Old Standard's CFF outlines wind counter-clockwise, the Regular's
        # clockwise: turned, or a bar merged across ʔ's stem (ʡ ʢ) cancelled
        # against it and left a hole
        src.draw(TransformPen(ReverseContourPen(SegmentToPointPen(g.getPointPen())), (k, 0, 0, k, 0, 0)))
        for c in g.contours:
            for p in c.points:
                p.x, p.y = round(p.x), round(p.y)
        g.width = round(src.width * k)
    font.save()


def redraw(path):
    """step 2"""
    out = ROOT / "build/redraw/regular-signs.ufo"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts/redraw.py"), str(path), str(out), *SIGNS,
                    "--tol", "2", "--install", "--date", DATE, "--review", REVIEW, "--regular", str(path)],
                   check=True)
    font = ufoLib2.Font.open(path)
    for name in SIGNS:
        lib = font[name].lib
        if name not in [n for n in SIGNS if REDRAWN_KEY in lib]:
            sys.exit(f"{name}: not installed (redraw.py's gate)")
        lib.pop(DRAWN_KEY, None)
        lib[REDRAWN_KEY]["source"] = "Old Standard"
    font.save()


def click(path):
    """step 4: ǃ, ! as a letter (a component of it), spaced as on
    2026-10-16 (CLICK_SIDE each side; Theano's ! in 488 at -20); on the
    narrower new ! its sides had become 137 and 101"""
    font = ufoLib2.Font.open(path)
    g, ink = font[CLICK], font["exclam"].getBounds(font)
    (comp,) = g.components
    comp.transformation = (1, 0, 0, 1, round(CLICK_SIDE - ink.xMin), 0)
    g.width = round(ink.xMax - ink.xMin + 2 * CLICK_SIDE)
    font.save()


def main():
    path = sys.argv[1]
    if "--glottal" not in sys.argv[2:]:
        take(path)
        redraw(path)
    rederive(path, GLOTTAL)
    click(path)


if __name__ == "__main__":
    main()
