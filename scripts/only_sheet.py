"""The sheet of a scratch run (T2, docs/claude/only.md): source style |
committed | new, node views, 144 pt, and words at 24 and 12 pt.

    python scripts/only_sheet.py STYLE GLYPH ... [--source UFO] [--new UFO] [--out PDF]

STYLE is Italic, Bold or BoldItalic; the new UFO is build/only/MyiaDidot-STYLE.ufo
(make_bold.py / make_italic.py --out), the committed one sources/', the
source the style is made from (the Regular, or the Italic for the Bold
Italic) sources/' unless --source names a trial. GLYPH: names or single
characters. The words: each glyph between n and o and between H and O, and
three words holding it from the proofs' texts. Called by `make only`.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import ufoLib2

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
MADE_FROM = {"Italic": "Regular", "Bold": "Regular", "BoldItalic": "Italic"}
TEXTS = ("proofs/textpages.tex", "proofs/samples.tex")


def characters(font, names):
    """the glyphs asked for as characters where they have one, else names"""
    out = []
    for name in names:
        if len(name) == 1 or name not in font:
            out.append(name)
        else:
            g = font[name]
            out.append(chr(g.unicode) if g.unicode else name)
    return out


def words(chars, limit=3):
    """the spacing strings and up to `limit` words from the proofs per character"""
    text = " ".join((ROOT / t).read_text(encoding="utf-8") for t in TEXTS if (ROOT / t).exists())
    text = re.sub(r"\\[A-Za-z]+|[{}\[\]%]", " ", text)
    vocabulary = list(dict.fromkeys(w for w in re.findall(r"\w+", text) if len(w) > 2))
    out = []
    for ch in chars:
        if len(ch) != 1:
            continue
        out += [f"n{ch}o", f"H{ch}O"]
        out += [w for w in vocabulary if ch in w][:limit]
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("style", choices=sorted(MADE_FROM))
    ap.add_argument("glyphs", nargs="+")
    ap.add_argument("--source", help="the UFO the style was made from (default: sources/')")
    ap.add_argument("--new", help="the scratch run (default: build/only/MyiaDidot-STYLE.ufo)")
    ap.add_argument("--out", help="the PDF (default: build/only/STYLE-FIRSTGLYPH.pdf)")
    a = ap.parse_args()
    source = a.source or ROOT / f"sources/MyiaDidot-{MADE_FROM[a.style]}.ufo"
    committed = ROOT / f"sources/MyiaDidot-{a.style}.ufo"
    new = Path(a.new or ROOT / f"build/only/MyiaDidot-{a.style}.ufo")
    if not (new / "metainfo.plist").exists():
        raise SystemExit(f"{new}: no scratch run (make only STYLE={a.style} GLYPHS=...)")
    chars = characters(ufoLib2.Font.open(committed), a.glyphs)
    out = Path(a.out or ROOT / f"build/only/{a.style}-{a.glyphs[0]}.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([PY, "-I", str(ROOT / "scripts/redraw_sheet.py"), str(out), " ".join(chars),
                    "--col", f"source={source}", "--col", f"committed={committed}", "--col", f"new={new}",
                    "--words", words(chars), "--title", f"{a.style}: {' '.join(a.glyphs)} made again (--out)"],
                   check=True)


if __name__ == "__main__":
    main()
