"""Do the Italic, Bold and Bold Italic have all the Regular has?

    python scripts/style_coverage.py [--sources DIR]

For every code point in the Regular's cmap, whether each style maps it; for
every glyph, whether each style has the Regular's anchors (a mark unattached
in one style only). The differences by Unicode block, exit 1 if there are
any. tests/test_styles_agree.py holds the same with reasons for what differs
on purpose; this is the plain report.
"""

import argparse
import collections
import sys
from pathlib import Path

import ufoLib2
from fontTools.unicodedata import block

ROOT = Path(__file__).resolve().parent.parent
STYLES = ("Italic", "Bold", "BoldItalic")


def missing(regular, font):
    """({block: [code point]}, {block: [(glyph, anchor)]}) of what font lacks."""
    mine = {g.name: g for g in font}
    points = {u for g in font for u in g.unicodes}
    chars, anchors = collections.defaultdict(list), collections.defaultdict(list)
    for g in regular:
        where = block(chr(g.unicodes[0])) if g.unicodes else "(unencoded)"
        for u in g.unicodes:
            if u not in points:
                chars[block(chr(u))].append(u)
        if g.name in mine:
            have = {a.name for a in mine[g.name].anchors}
            anchors[where] += [(g.name, a.name) for a in g.anchors if a.name not in have]
    return dict(chars), {k: v for k, v in anchors.items() if v}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sources", type=Path, default=ROOT / "sources")
    args = ap.parse_args()
    regular = ufoLib2.Font.open(args.sources / "MyiaDidot-Regular.ufo")
    failed = False
    for style in STYLES:
        chars, anchors = missing(regular, ufoLib2.Font.open(args.sources / f"MyiaDidot-{style}.ufo"))
        print(f"{style}: {sum(map(len, chars.values()))} code points, "
              f"{sum(map(len, anchors.values()))} anchors missing")
        for name in sorted(chars):
            print(f"  {name}: " + " ".join(f"U+{u:04X}" for u in sorted(chars[name])))
        for name in sorted(anchors):
            print(f"  {name}: " + " ".join(f"{g}/{a}" for g, a in sorted(anchors[name])))
        failed = failed or bool(chars or anchors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
