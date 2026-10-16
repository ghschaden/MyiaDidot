"""cases.py: colour (ink over advance x zone height) of capitals and small
caps against the lowercase, Myia and references."""
import statistics
import sys
from pathlib import Path

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import MYIA, REFS, Face

LC = "abcdeghkmnopqrsuvxyz"; UC = "ABCDEGHKMNOPQRSUVXYZ"
def col(face, names, h):
    vals = []
    for n in names:
        g = face.gs[n]; a = AreaPen(face.gs); g.draw(a)
        vals.append(abs(a.value) / (g.width * h))
    return statistics.mean(vals)
for style in ("Regular", "Italic", "Bold"):
    for path in [MYIA.format(style)] + REFS[style]:
        f = Face(path)
        lc = col(f, [f.cmap[ord(c)] for c in LC], f.xh)
        uc = col(f, [f.cmap[ord(c)] for c in UC], f.cap)
        sc_names = [f.cmap[ord(c)] + ".sc" for c in LC]
        sc = None
        if all(n in f.gs for n in sc_names):
            b = BoundsPen(f.gs); f.gs["x.sc"].draw(b)
            sc = col(f, sc_names, b.bounds[3])
        print(f"{style:8} {f.name[:24]:24} caps/lc {uc/lc:.2f}" + (f"   small caps/lc {sc/lc:.2f}" if sc else ""))
