#!/usr/bin/env python3
"""Do the generated styles come out of their generators as they are?

    python scripts/check_reproducible.py        (make reproduce)

The Italic, the Bold and the Bold Italic are made by make_italic.py and
make_bold.py (then smallcaps.py); an edit made in one of them by hand, or by
a script the generators do not run, is lost at their next run. This reruns
them on copies (in build/reproduce/, each starting from the committed UFO,
so reviewed glyphs are kept as the generators keep them) and lists every
glyph, kerning pair, feature line and glyph-order entry that would change.
Exit status 1 if anything would.
"""

import difflib
import shutil
import subprocess
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
WORK = ROOT / "build" / "reproduce"
PY = sys.executable


def ink(font, name):
    pen = DecomposingRecordingPen(font)
    font[name].draw(pen)
    return [(op, tuple(tuple(round(v) for v in pt) for pt in args)) for op, args in pen.value]


def differences(new, cur):
    """Lines describing what new (the rerun) changes in cur (the source)."""
    out = []
    for name in (g.name for g in cur):
        if name not in new:
            out.append(f"glyph {name}: gone in the rerun")
            continue
        a, b = new[name], cur[name]
        anchors = [sorted((p.name, p.x, p.y) for p in g.anchors) for g in (a, b)]
        if a.width != b.width:
            out.append(f"glyph {name}: width {b.width} -> {a.width}")
        elif ink(new, name) != ink(cur, name):
            out.append(f"glyph {name}: outline")
        elif anchors[0] != anchors[1]:
            out.append(f"glyph {name}: anchors")
        elif dict(a.lib) != dict(b.lib):
            out.append(f"glyph {name}: lib")
    out += [f"glyph {n}: new in the rerun" for n in sorted(set(new.keys()) - set(cur.keys()))]
    for pair in sorted(set(new.kerning) | set(cur.kerning)):
        if new.kerning.get(pair) != cur.kerning.get(pair):
            out.append(f"kerning {pair}: {cur.kerning.get(pair)} -> {new.kerning.get(pair)}")
    for group in sorted(set(new.groups) | set(cur.groups)):
        if new.groups.get(group) != cur.groups.get(group):
            out.append(f"group {group}")
    out += [f"features {line}" for line in difflib.unified_diff(
        cur.features.text.splitlines(), new.features.text.splitlines(), lineterm="", n=0)
        if line[:1] in "+-" and line[:3] not in ("+++", "---")]
    for key in sorted(set(new.lib) | set(cur.lib)):
        if new.lib.get(key) != cur.lib.get(key):
            out.append(f"font lib {key}")
    return out


def run(*args):
    subprocess.run([PY, "-I", *map(str, args)], check=True, stdout=subprocess.DEVNULL)


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    for style in ("Italic", "Bold", "BoldItalic"):
        shutil.copytree(SOURCES / f"MyiaDidot-{style}.ufo", WORK / f"MyiaDidot-{style}.ufo")
    regular = SOURCES / "MyiaDidot-Regular.ufo"
    italic, bold, bold_italic = (WORK / f"MyiaDidot-{s}.ufo" for s in ("Italic", "Bold", "BoldItalic"))
    run(ROOT / "scripts/make_italic.py", regular, italic)
    run(ROOT / "scripts/make_bold.py", regular, bold)
    run(ROOT / "scripts/smallcaps.py", bold)
    # the Bold Italic from the committed Italic: each generator on its own input
    run(ROOT / "scripts/make_bold.py", SOURCES / "MyiaDidot-Italic.ufo", bold_italic)
    run(ROOT / "scripts/smallcaps.py", bold_italic)
    found = 0
    for style, path in (("Italic", italic), ("Bold", bold), ("BoldItalic", bold_italic)):
        lines = differences(ufoLib2.Font.open(path), ufoLib2.Font.open(SOURCES / f"MyiaDidot-{style}.ufo"))
        found += len(lines)
        print(f"{style}: {'as generated' if not lines else f'{len(lines)} differences'}")
        for line in lines[:60]:
            print("  " + line)
        if len(lines) > 60:
            print(f"  ... {len(lines) - 60} more")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
