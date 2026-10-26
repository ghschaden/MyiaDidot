"""Compare HarfBuzz shaping of two fonts over a broad test corpus.

    python scripts/compare_shaping.py REFERENCE NEW [--renames glyph-renames.json]

Glyph names of REFERENCE are mapped through the renames file before being
compared with NEW, so build NEW without production names
(fontmake --no-production-names). Exits non-zero if anything differs.
"""

import argparse
import itertools
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


FEATURE_TESTS = [
    # (text, features, script, language)
    ("0123456789", {"onum": True}, None, None),
    ("H0123456789", {"sups": True}, None, None),
    ("H0123456789", {"subs": True}, None, None),
    ("H0123456789", {"numr": True}, None, None),
    ("H0123456789", {"dnom": True}, None, None),
    ("1/2 3/4 12/345", {"frac": True}, None, None),
    ("fi fl ff ffi ffl fj ffj", {}, None, None),
    ("fi fl ff ffi ffl", {}, "latn", "TRK"),
    ("ct st sp Qu", {"dlig": True}, None, None),
    ("ch ck tz", {"dlig": True}, "latn", "DEU"),
    ("ŞşŢţ", {}, "latn", "ROM"),
    ("ŞşŢţ", {"ss01": True}, None, None),
    ("ἌΝΘΡΩΠΟΣ ἄνθρωπος", {"case": True}, None, None),
    ("βθφπκρϲ ὁ λόγος", {"salt": True}, None, None),
    ("βθφπκρ", {"ss11": True}, None, None),
    ("ὁ λόγος ἐστὶν θεός βίβλος", {}, "grek", None),
    ("ᾼ ᾳ ᾈ ᾠ ᾯ", {}, "grek", None),
    ("Ἀ Ἁ Ἄ Ἅ Ἂ Ἃ Ἆ Ἇ Ὤ Ὦ Ἱ Ὁ Ὑ Ῥ", {}, "grek", None),
    ("ἈἈ ΆἌ Ἐ Ὁ", {}, "grek", None),
    ("ı̇ i̇ j́ í ǰ", {}, None, None),
    ("ИИ́ и́ а̀ ё̄", {}, "cyrl", None),
]


def letters_and_punct(cmap):
    keep = []
    for cp in sorted(cmap):
        cat = unicodedata.category(chr(cp))
        if cat[0] in "LPN" or cat in ("Sm", "Sc", "Sk"):
            keep.append(chr(cp))
    return keep


def corpus(cmap):
    chars = [chr(cp) for cp in sorted(cmap)]
    yield from ((c, {}, None, None) for c in chars)

    lp = letters_and_punct(cmap)
    for a, b in itertools.product(lp, repeat=2):
        yield (a + b, {}, None, None)

    marks = [c for c in chars if unicodedata.category(c) == "Mn"]
    bases = [c for c in chars if unicodedata.category(c)[0] == "L"]
    for b, m in itertools.product(bases, marks):
        yield (b + m, {}, None, None)

    for c in chars:
        nfd = unicodedata.normalize("NFD", c)
        if nfd != c:
            yield (nfd, {}, None, None)

    yield from FEATURE_TESTS


from font_shaping import Shaper


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("new")
    ap.add_argument("--renames")
    ap.add_argument("--show", type=int, default=25)
    args = ap.parse_args()

    rename = {}
    if args.renames:
        with open(args.renames, encoding="utf-8") as fh:
            rename = json.load(fh)

    ref, new = Shaper(args.reference), Shaper(args.new)
    if set(ref.cmap) != set(new.cmap):
        print("cmap differs:", sorted(set(ref.cmap) ^ set(new.cmap)))

    total, diffs, kinds = 0, [], Counter()
    for text, feats, script, lang in corpus(ref.cmap):
        total += 1
        a = [(rename.get(n, n), *pos) for n, *pos in ref.shape(text, feats, script=script, language=lang)]
        b = new.shape(text, feats, script=script, language=lang)
        if a != b:
            if [g[0] for g in a] != [g[0] for g in b]:
                kinds["glyphs"] += 1
            else:
                kinds["positions"] += 1
            diffs.append((text, feats, lang, a, b))

    print(f"{total} strings shaped, {len(diffs)} differ {dict(kinds)}")
    for text, feats, lang, a, b in diffs[: args.show]:
        print(f"\n{text!r} {feats or ''} {lang or ''}")
        print("  ref:", a)
        print("  new:", b)
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
