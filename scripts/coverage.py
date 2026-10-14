"""Report coverage of the target glyphsets and classify what is missing.

    python scripts/coverage.py FONT [--sets GF_Latin_Core ...] [--list]

Each missing character is classified as
  compose   - NFD base and all marks are in the font (or are themselves
              composable), so it can be built from components;
  needmark  - decomposes, but a combining mark is missing;
  draw      - no canonical decomposition (or its base is missing): needs a
              newly drawn base shape.
"""

import argparse
import unicodedata
from collections import defaultdict

import glyphsets
from fontTools.ttLib import TTFont

# Target agreed for Myia Didot (Phase 1). Latin: all GF tiers incl. African and
# Vietnamese, plus standard IPA; Greek up to Pro; basic Cyrillic.
TARGET = [
    "GF_Latin_Kernel",
    "GF_Latin_Core",
    "GF_Latin_Plus",
    "GF_Latin_Vietnamese",
    "GF_Latin_PriAfrican",
    "GF_Latin_African",
    "GF_Latin_Beyond",
    "GF_Phonetics_IPAStandard",
    "GF_Phonetics_APA",
    "GF_Greek_Core",
    "GF_Greek_Plus",
    "GF_Greek_Pro",
    "GF_Cyrillic_Core",
]


def classify(cp, have):
    nfd = unicodedata.normalize("NFD", chr(cp))
    if len(nfd) == 1:
        return "draw", nfd
    base, marks = nfd[0], nfd[1:]
    if ord(base) not in have:
        return "draw", nfd
    if all(ord(m) in have for m in marks):
        return "compose", nfd
    return "needmark", nfd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("--sets", nargs="*", default=TARGET)
    ap.add_argument("--list", action="store_true", help="list every missing character")
    args = ap.parse_args()

    have = set(TTFont(args.font).getBestCmap())
    seen = set()
    totals = defaultdict(int)
    missing_marks = defaultdict(set)
    for gs in args.sets:
        wanted = [u for u in glyphsets.unicodes_per_glyphset(gs) if u not in seen]
        seen.update(wanted)
        missing = sorted(u for u in wanted if u not in have)
        buckets = defaultdict(list)
        for u in missing:
            kind, nfd = classify(u, have)
            buckets[kind].append(u)
            totals[kind] += 1
            if kind == "needmark":
                missing_marks[gs].update(ord(m) for m in nfd[1:] if ord(m) not in have)
        print(f"{gs:26} {len(wanted):4} chars, missing {len(missing):4}  "
              + "  ".join(f"{k} {len(v)}" for k, v in sorted(buckets.items())))
        if args.list:
            for kind, us in sorted(buckets.items()):
                for u in us:
                    print(f"    {kind:8} U+{u:04X} {chr(u)}  {unicodedata.name(chr(u), '?')}")
    print("\ntotal missing:", sum(totals.values()), dict(totals))
    marks = set().union(*missing_marks.values()) if missing_marks else set()
    if marks:
        print("marks to draw:", " ".join(f"U+{m:04X}" for m in sorted(marks)))


if __name__ == "__main__":
    main()
