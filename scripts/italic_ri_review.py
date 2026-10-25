"""Review current Italic r/I against a modest lighter trial in text."""
import json
import math
import subprocess
import sys
import tarfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_italic import XH, shear, weight_thick
from quality.strokes import strokes
from upright_aleph import add_extrema, fair_joins

ROOT = Path("build/italic-ri-review")
TEXT = (
    "I remember the river.",
    "There were narrow roads",
    "running through the garden.",
    "In the library I read her",
    "rare story of returning.",
    "Her writing was regular.",
)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    reference = ROOT / "reference"
    reference.mkdir(exist_ok=True)
    archive = subprocess.run(["git", "archive", "7b2a1117", "sources/MyiaDidot-Italic.ufo"],
                             capture_output=True, check=True)
    with tarfile.open(fileobj=BytesIO(archive.stdout)) as files:
        files.extractall(reference, filter="data")
    font = ufoLib2.Font.open(reference / "sources/MyiaDidot-Italic.ufo")
    trial = deepcopy(font)
    slant = math.tan(math.radians(-font.info.italicAngle))
    for name in ("r", "I"):
        g = trial[name]
        source = deepcopy(g)
        shear(source, -slant, XH / 2)
        rec = RecordingPen()
        source.draw(rec)
        out = weight_thick(rec, -15)
        old, new = source.getBounds(None), out.getBounds()
        dx = (old[0] + old[2] - new[0] - new[2]) / 2
        g.clearContours()
        out.draw(TransformPen(RoundingPen(g.getPen()), (1, 0, slant, 1, dx - slant * XH / 2, 0)))
        add_extrema(g)
        fair_joins(g)
        assert g.width == font[name].width
        assert g.anchors == font[name].anchors
    trial.save(ROOT / "Trial.ufo", overwrite=True)
    measures = {label: strokes(f, only=("r", "I", "n", "H"))[1]
                for label, f in (("Current", font), ("Lighter trial", trial))}
    (ROOT / "measurements.json").write_text(json.dumps(measures, indent=2) + "\n")
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="1550">',
         '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
         '<text x="30" y="40" font-size="26">Italic r / I — weight review in text</text>',
         '<text x="30" y="70" font-size="15">2026-10-25 · Right: thick-stroke adjustment −15; advances preserved · unkerned outline specimens</text>']
    for col, (label, f) in enumerate((("Current", font), ("Lighter trial", trial))):
        x = 30 + col * 625
        s.append(f'<text x="{x}" y="120" font-size="22">{label}</text>')
        cmap = {u: g.name for g in f for u in g.unicodes}

        def row(text, y, scale, f=f, x=x, cmap=cmap):
            pos = x
            for ch in text:
                name = cmap[ord(ch)]
                pen = SVGPathPen(f)
                f[name].draw(pen)
                s.append(f'<path d="{pen.getCommands()}" transform="translate({pos},{y}) scale({scale},{-scale})"/>')
                pos += f[name].width * scale

        row("n r n  H I H", 290, .045)
        for line, name in enumerate(("r", "I")):
            weight, ratio, *_ = measures[label][name]
            s.append(f'<text x="{x}" y="{335+line*24}" font-size="15">{name}: measured stroke {weight}; reference ratio {ratio:.3f}</text>')
        for group, scale in enumerate((.012, .016, .020)):
            y = 435 + group * 340
            s.append(f'<text x="{x}" y="{y-30}" font-size="14">{scale * 2048:g} px em</text>')
            for i, text in enumerate(TEXT):
                row(text, y + i * (scale * 2600), scale)
    s.append('<text x="30" y="1515" font-size="15">Trial for comparison only; production unchanged. Judge text colour before changing these inherited drawings.</text></g></svg>')
    source = ROOT / "comparison.svg"
    source.write_text("\n".join(s))
    for fmt, dest in (("png", ROOT / "comparison.png"),
                      ("pdf", Path("proofs/italic-ri-weight-review-2026-10-25.pdf"))):
        subprocess.run(["rsvg-convert", "-f", fmt, str(source), "-o", str(dest)], check=True)
    print(json.dumps(measures, indent=2))


if __name__ == "__main__":
    main()
