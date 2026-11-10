"""stem_retreats.py UFO ...: stems that step into the ink before their serif.

The rule: a straight stem keeps one thickness from top to bottom and never
narrows where it meets its serif (docs/claude/quality.md; the designer,
2026-11-10, on the Bold Italic's small-cap D at the x-height). The measure
is scripts/stem_joins.py's `retreats`: one line a glyph, worst first, x,y
of the stem's end at the join and the units the outline goes into the
ink there. Composites are not read (their base is). tests/test_stem_joins.py
holds the styles to it.
"""

import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stem_joins import retreats  # noqa: E402


def found(font):
    return {g.name: r for g in font if g.contours and (r := retreats(g))}


def main():
    for path in sys.argv[1:]:
        got = found(ufoLib2.Font.open(path))
        print(Path(path).stem.split("-")[-1], len(got), "glyphs,", sum(len(r) for r in got.values()), "joins")
        for name, r in sorted(got.items(), key=lambda kv: -max(x[2] for x in kv[1])):
            print("  ", name, " ".join(f"{x},{y}:{d}" for x, y, d in r))


if __name__ == "__main__":
    main()
