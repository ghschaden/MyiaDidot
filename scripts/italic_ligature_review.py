import subprocess
import sys
from html import escape
from pathlib import Path

import ufo2ft
import ufoLib2
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, "scripts")
from compare_shaping import Shaper
from italic_ligatures import NAMES

root = Path("build/italic-ligatures")
root.mkdir(parents=True, exist_ok=True)
for style in ("Italic", "BoldItalic"):
    font = ufoLib2.Font.open(f"sources/MyiaDidot-{style}.ufo")
    names = NAMES
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="2150"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
        f'<text x="25" y="38" font-size="27">{style} — new ligature drawings</text>',
        '<text x="25" y="70" font-size="16">2026-10-25 · Left: separate letters · Middle: new joined form · Right: repeated at text size</text>',
        '<text x="25" y="98" font-size="16">Final same-style bases; existing fi/fl/ff/ffi/ffl retained. ct/st are discretionary (dlig).</text>',
    ]

    def sequence(names, x, y, scale, font=font, out=out):
        for n in names:
            p = SVGPathPen(font)
            font[n].draw(p)
            out.append(f'<path d="{p.getCommands()}" transform="translate({x},{y}) scale({scale},{-scale})"/>')
            x += font[n].width * scale

    for i, n in enumerate(names):
        y = 200 + i * 100
        parts = n.split("_")
        out.append(f'<text x="25" y="{y - 25}" font-size="16">{escape(n)}</text>')
        sequence(parts, 230, y, 0.042)
        sequence([n], 530, y, 0.042)
        sequence([n] * 5, 830, y, 0.014)
    out.append(
        '<text x="25" y="2120" font-size="15">Drawings accepted 2026-10-25. Default/language/feature behaviour is checked separately.</text></g></svg>'
    )
    p = root / f"{style}-design.svg"
    p.write_text("\n".join(out))
    for fmt in ("png", "pdf"):
        subprocess.run(["rsvg-convert", "-f", fmt, str(p), "-o", str(root / f"{style}-design.{fmt}")], check=True)
    otf = root / f"{style}-review.otf"
    ufo2ft.compileOTF(font, useProductionNames=False, optimizeCFF=0).save(otf)
    shaper = Shaper(str(otf))
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="1450"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
        f'<text x="25" y="38" font-size="27">{style} — ligatures in shaped text</text>',
        '<text x="25" y="70" font-size="16">Top line in each pair: ligatures off. Bottom line: on. English language, unless marked German.</text>',
    ]
    samples = (
        ("Offbeat, offhand, offkey; after the craft.", {}, "en"),
        ("Soft light fell across the left-hand shelf.", {}, "en"),
        ("action actual structure lasting", {"dlig": True}, "en"),
        ("ſi ſl ſſ ſſi ſſl ſb ſh ſk ſt", {}, "en"),
        ("Aufbruch, Schifffahrt, kraftvoll", {}, "de"),
    )
    for i, (text, features, language) in enumerate(samples):
        y = 155 + i * 245
        out.append(f'<text x="25" y="{y-55}" font-size="16">{escape(text)} / {language}</text>')
        for row, enabled in enumerate((False, True)):
            feats = dict(features) if enabled else {"liga": False, "dlig": False}
            scale = 0.022
            x = 35
            baseline = y + row * 90
            for name, advance, dx, dy in shaper.shape(text, feats, language=language):
                pen = SVGPathPen(font)
                font[name].draw(pen)
                out.append(f'<path d="{pen.getCommands()}" transform="translate({x+dx*scale},{baseline-dy*scale}) scale({scale},{-scale})"/>')
                x += advance * scale
    out.append('<text x="25" y="1420" font-size="15">German retains its existing f-ligature exclusion; ct/st require dlig. Drawings accepted 2026-10-25.</text></g></svg>')
    p = root / f"{style}-text.svg"
    p.write_text("\n".join(out))
    for fmt in ("png", "pdf"):
        subprocess.run(["rsvg-convert", "-f", fmt, str(p), "-o", str(root / f"{style}-text.{fmt}")], check=True)
subprocess.run(
    [
        "pdfunite",
        str(root / "Italic-design.pdf"),
        str(root / "BoldItalic-design.pdf"),
        str(root / "Italic-text.pdf"),
        str(root / "BoldItalic-text.pdf"),
        "proofs/italic-ligatures-review-2026-10-25.pdf",
    ],
    check=True,
)
