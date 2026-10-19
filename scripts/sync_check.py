"""Leftovers of the file sync in the UFOs: "(conflicted)" copies, glyphs
listed whose file is gone, glyph files listed nowhere.  Without arguments
also the conflict copies in the tracked folders around them (TREES: a
baseline in tests/data rewritten fast became one, its own file gone, and
the test read an empty list).

    python scripts/sync_check.py [UFO ...]   (default: every sources/*.ufo, and TREES)

The working copy is in a synced folder: rewriting many files fast (make
generate, make normalize) can leave them. Prints one line per finding and
exits 1 when there are any; tests/test_ufo.py holds the UFOs to none.
"""

import plistlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREES = ("tests", "scripts", "tools", "proofs")


def leftovers(ufo):
    """The findings for one UFO, as paths relative to it with what is wrong."""
    ufo = Path(ufo)
    out = [f"{p.relative_to(ufo)}: sync conflict copy" for p in sorted(ufo.rglob("*")) if "conflict" in p.name.lower()]
    layers = ufo / "layercontents.plist"
    if not layers.exists():
        return out + ["layercontents.plist: missing"]
    for _layer, folder in plistlib.loads(layers.read_bytes()):
        contents = ufo / folder / "contents.plist"
        if not contents.exists():
            out.append(f"{folder}/contents.plist: missing")
            continue
        listed = plistlib.loads(contents.read_bytes())
        out += [f"{folder}/{file}: listed for {name}, missing" for name, file in listed.items()
                if not (ufo / folder / file).exists()]
        files = set(listed.values())
        out += [f"{folder}/{p.name}: not listed" for p in sorted((ufo / folder).glob("*.glif")) if p.name not in files]
    return out


def tree_leftovers():
    """Conflict copies in TREES, as paths relative to the repository."""
    return [f"{p.relative_to(ROOT)}: sync conflict copy" for t in TREES for p in sorted((ROOT / t).rglob("*"))
            if "conflicted" in p.name.lower() and "__pycache__" not in p.parts]


def main():
    ufos = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "sources").glob("*.ufo"))
    found = 0
    for ufo in ufos:
        for line in leftovers(ufo):
            print(f"{ufo.name}/{line}")
            found += 1
    if not sys.argv[1:]:
        for line in tree_leftovers():
            print(line)
            found += 1
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
