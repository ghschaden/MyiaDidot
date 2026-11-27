"""RECORD, not part of the build (TODO.md T7, 2026-11-27): run once, what
it made was kept in the UFO where accepted (in a generated style marked
drawn); no generator, Makefile target or test calls it. Kept to show how those glyphs were made; do not run it again
on sources/ (it would redo what was since reviewed or drawn over).

The Regular's `hook` family mended (longtail.md, 2026-11-24): two causes
the operation shares, both mended in the kept glyphs.

    python scripts/regular_hook.py UFO [--h-hook]

(--h-hook: steps 0 and 3 for Ɦ ɦ.sc alone, on letters already mended.)

0. Ɦ turned the other way (the designer, 2026-11-24, on
   proofs/2026-11/H-hook-left-trial-2026-11-24.pdf): its hook curled right
   over the counter onto the right stem and read as "HA"; Charis, Noto
   Serif, DejaVu, Fira and the Italic and Bold Italic curl it left. Now
   Ɗ's recipe (up-left, the top serif's right half kept), made again.
1. The join of the hook on its stem (ɓ ɗ ƙ ɦ ɧ, ɖ below; the old Ɦ): derive.hook_path
   takes the hook from f above 954, where f's straight stem ends, so the
   piece starts on f's curve already leaning out, a corner of 2.1-3.2
   degrees where it meets the letter's stem. Beside a duplicate node (a
   zero-length line) in all but ɧ, which checks.construction does not see
   past: listed for ɧ alone. The curve's first handle put in line with the
   stem, the duplicate dropped (smooth_joins.align).
2. f's node at 648,1334 (and ȷ's at 32,-417): handles of 22-24 units,
   1.2 (0.6) degrees off line by rounding; the hook's scaling across turns
   that to 2.4 in Ɓ Ɗ Ƥ Ɦ Ƒ. Their handles put in line (smooth_joins.align,
   then the whole units nearest that turn least).
3. ƥ.sc ɦ.sc, enlarged from Ƥ Ɦ, made again on them.

The Regular's derived letters are kept once made (derive.py); ɓ ɗ ƙ ɦ ɧ
are no longer what their recipes make (redrawn since: ɓ's re-derived
advance is 1110 -> 1865), so these mend the kept glyphs, not the recipes.
Run once on the Regular, then make normalize; the Bold and the italics
follow in make generate.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smooth_joins  # noqa: E402
from regular_attach import rederive  # noqa: E402

JOINS = {
    "uni0253": [(200, 1000)],  # ɓ
    "uni0257": [(746, 1000)],  # ɗ
    "uni0199": [(200, 1000)],  # ƙ
    "uni0266": [(200, 1000)],  # ɦ
    "uni0267": [(200, 1000)],  # ɧ
    "uni0256": [(746, 48)],  # ɖ: ȷ's tail on d's stem
}
SMOOTH = {
    "uni0181": [(284, 1236)],  # Ɓ
    "uni018A": [(284, 1236)],  # Ɗ
    "uni01A4": [(284, 1236)],  # Ƥ
    "uniA7AA": [(284, 1236)],  # Ɦ (with Ɗ's hook)
    "uni0191": [(56, -359)],  # Ƒ
}
# Ɦ made again on its new recipe (step 0)
H_HOOK = {"uniA7AA": "Ɦ"}
# enlarged from Ƥ Ɦ, made again on them (ɦ.sc's smooth 2.9 at its join and
# kink 5.4 go with the old hook; on Ɗ's hook its node at 268,895 1.35 degrees
# off line)
SMALL_CAPS = {"uni01A5.sc": "ƥ.sc", "uni0266.sc": "ɦ.sc"}
SC_IN_LINE = {"uni0266.sc": [(268, 895)]}


def _turn(a, p, b):
    t = math.atan2(b[1] - p[1], b[0] - p[0]) - math.atan2(p[1] - a[1], p[0] - a[0])
    return abs(math.degrees((t + math.pi) % (2 * math.pi) - math.pi))


def in_line(glyph, x, y):
    """the handles at the smooth node (x, y), within a unit of where align
    rounded them, set to the whole units that turn least (short handles:
    align's rounding alone leaves 1.5 degrees)"""
    for c in glyph.contours:
        P = c.points
        for i, p in enumerate(P):
            if p.type and (p.x, p.y) == (x, y):
                a, b = P[i - 1], P[(i + 1) % len(P)]
                ax, ay, bx, by = a.x, a.y, b.x, b.y
                best = min((_turn((ax + i, ay + j), (x, y), (bx + k, by + m)), i, j, k, m)
                           for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) for m in (-1, 0, 1))
                _, i, j, k, m = best
                a.x, a.y, b.x, b.y = ax + i, ay + j, bx + k, by + m
                return
    raise ValueError(f"{glyph.name}: no node at {x},{y}")


def main():
    path = sys.argv[1]
    h_only = "--h-hook" in sys.argv[2:]
    font = rederive(path, H_HOOK)
    for name, places in JOINS.items():
        for x, y in places:
            if not h_only:
                smooth_joins.align(font[name], x, y)
    for name, places in SMOOTH.items():
        for x, y in places:
            if h_only and name not in H_HOOK:
                continue
            smooth_joins.align(font[name], x, y)
            in_line(font[name], x, y)
    font.save()
    font = rederive(path, SMALL_CAPS)
    for name, places in SC_IN_LINE.items():
        for x, y in places:
            in_line(font[name], x, y)
    font.save()


if __name__ == "__main__":
    main()
