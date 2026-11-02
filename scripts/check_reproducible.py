#!/usr/bin/env python3
"""Do the generated styles come out of their generators as they are?

    python scripts/check_reproducible.py        (make reproduce)

The Italic, the Bold and the Bold Italic are made by make_italic.py and
make_bold.py (then smallcaps.py); an edit made in one of them by hand, or by
a script the generators do not run, is lost at their next run. This reruns
them on copies (in an isolated workspace, each starting from the current UFO,
so reviewed glyphs are kept as the generators keep them) and lists every
glyph, kerning pair, feature line and glyph-order entry that would change.
Exit status 1 if anything would.
"""

import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
PY = sys.executable


def ink(font, name):
    pen = DecomposingRecordingPen(font)
    font[name].draw(pen)
    return [(op, tuple(tuple(round(v) for v in pt) for pt in args)) for op, args in pen.value]


def outline_change(new, cur):
    """None if the outlines agree; else how: the largest point move and
    where, when only coordinates differ, or how the structure differs (so
    that a machine's rounding is told from a real change)."""
    if new == cur:
        return None
    if [(op, len(args)) for op, args in new] != [(op, len(args)) for op, args in cur]:
        return f"structure: {len(cur)} -> {len(new)} segments"
    worst = (0, None, None)
    for (_, a), (_, b) in zip(new, cur):
        for p, q in zip(a, b):
            d = max(abs(p[0] - q[0]), abs(p[1] - q[1]))
            if d > worst[0]:
                worst = (d, q, p)
    return f"points moved up to {worst[0]}: {worst[1]} -> {worst[2]}"


def differences(new, cur):
    """Lines describing what new (the rerun) changes in cur (the source)."""
    # No volatile font-info fields are currently excluded. Add exclusions only
    # with a documented reason and a mutation test.
    out = [f"font info {field.name}" for field in cur.info.__attrs_attrs__
           if getattr(new.info, field.name) != getattr(cur.info, field.name)]
    for name in (g.name for g in cur):
        if name not in new:
            out.append(f"glyph {name}: gone in the rerun")
            continue
        a, b = new[name], cur[name]
        anchors = [sorted((p.name, p.x, p.y) for p in g.anchors) for g in (a, b)]
        if a.unicodes != b.unicodes:
            out.append(f"glyph {name}: unicodes {b.unicodes} -> {a.unicodes}")
        if a.width != b.width:
            out.append(f"glyph {name}: width {b.width} -> {a.width}")
        elif (moved := outline_change(ink(new, name), ink(cur, name))) is not None:
            out.append(f"glyph {name}: outline ({moved})")
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


def reproduce(work, sources):
    for style in ("Italic", "Bold", "BoldItalic"):
        shutil.copytree(sources / f"MyiaDidot-{style}.ufo", work / f"MyiaDidot-{style}.ufo")
    regular = sources / "MyiaDidot-Regular.ufo"
    italic, bold, bold_italic = (work / f"MyiaDidot-{s}.ufo" for s in ("Italic", "Bold", "BoldItalic"))
    run(ROOT / "scripts/make_italic.py", regular, italic)
    run(ROOT / "scripts/make_bold.py", regular, bold)
    run(ROOT / "scripts/smallcaps.py", bold)
    # the Bold Italic from the snapshot Italic: each generator on its own input
    run(ROOT / "scripts/make_bold.py", sources / "MyiaDidot-Italic.ufo", bold_italic)
    run(ROOT / "scripts/smallcaps.py", bold_italic)
    found = 0
    for style, path in (("Italic", italic), ("Bold", bold), ("BoldItalic", bold_italic)):
        lines = differences(ufoLib2.Font.open(path), ufoLib2.Font.open(sources / f"MyiaDidot-{style}.ufo"))
        found += len(lines)
        print(f"{style}: {'as generated' if not lines else f'{len(lines)} differences'}")
        for line in lines[:60]:
            print("  " + line)
        if len(lines) > 60:
            print(f"  ... {len(lines) - 60} more")
    return 1 if found else 0


def main():
    # Freeze all source UFOs before running any generator. Each invocation owns
    # its scratch tree, including the Regular and the Bold Italic's input.
    with tempfile.TemporaryDirectory(prefix="myia-reproduce-") as temporary:
        work = Path(temporary)
        sources = work / "sources"
        shutil.copytree(SOURCES, sources)
        raise SystemExit(reproduce(work, sources))


if __name__ == "__main__":
    main()
