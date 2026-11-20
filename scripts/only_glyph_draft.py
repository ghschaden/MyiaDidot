"""DRAFT (2026-11-19), the throwaway behind TODO.md "Next session" (generate(glyph)): Ƈ Ɠ attach recipe on the saved Bold Italic, a list of (y0, cut, cx) tried, a sheet of the junction. Run from the repo root: python scripts/only_glyph_draft.py OUTDIR "[(1290, 1320, 10)]". Not tested, not in the Makefile, to be replaced by scripts/only_glyph.py."""

import copy
import subprocess
import sys

sys.path.insert(0, "scripts")
import derive
import make_bold as mb
import ufoLib2
from fontTools.pens.svgPathPen import SVGPathPen

S = sys.argv[1]
font = ufoLib2.Font.open("sources/MyiaDidot-BoldItalic.ufo")
import math

mb.SLANT = math.tan(math.radians(-(font.info.italicAngle or 0)))
up = copy.deepcopy(font)
for g in up:
    mb.shear(g, -mb.SLANT)
up.lib[derive.STROKE_KEY] = (1, 1)
cells = []


def recipe(x, y0, cut, cx=50):
    return (
        "attach",
        None,
        (
            "c",
            [(x - cx, cut, 10000, 10000)],
            [
                ("line", ((x, y0), (x, 1500), 53), (0, 0), (1, 1, 0, 0)),
                (
                    "curl",
                    {
                        "at": ("pt", x, 1500, 53),
                        "dir": 90,
                        "turn": "cw",
                        "r": (165, 150),
                        "sweep": 200,
                        "ball": 85,
                        "t": (53, 45),
                        "lead": 10,
                    },
                    (0, 0),
                    (1, 1, 0, 0),
                ),
            ],
        ),
    )


for ch, base, x in (("Ƈ", "C", 1235), ("Ɠ", "G", 1287)):
    for y0, cut, cx in eval(sys.argv[2]):
        tmp = "_t"
        _, _, band = recipe(x, y0, cut, cx)
        new = derive.build(up, ch, "attach", base, band, tmp)
        mb.drop_specks(new)
        mb.fix(up, [tmp])
        g = ufoLib2.objects.Glyph()
        mb.slant_back(new, g.getPen(), [(1, 0, mb.SLANT, 1, -mb.SLANT * mb.XH / 2, 0)], True)
        p = SVGPathPen(font)
        g.draw(p)
        cells.append((f"{ch} y0={y0} cut={cut} cx={cx}", p.getCommands()))
        del up[tmp]
w = 360
out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * 4}" height="{w * ((len(cells) + 3) // 4)}" style="background:white">'
]
for i, (t, d) in enumerate(cells):
    ox, oy = (i % 4) * w, (i // 4) * w
    out.append(
        f'<g transform="translate({ox},{oy})"><text x="6" y="16" font-size="13">{t}</text><svg x="0" y="20" width="{w}" height="{w - 20}" viewBox="1050 -1600 700 700"><g transform="scale(1,-1)"><path d="{d}" fill="#222"/></g></svg></g>'
    )
out.append("</svg>")
open(f"{S}/ta.svg", "w").write("".join(out))
subprocess.run(["rsvg-convert", f"{S}/ta.svg", "-o", f"{S}/ta.png"])
