"""What a derived glyph was built from, and whether that has changed since.

    python scripts/built_from.py UFO                 # glyphs whose bases changed
    python scripts/built_from.py UFO GLYPH ... --accept

derive.py records in each glyph it makes (lib KEY) a fingerprint of every
glyph the recipe read: outline (decomposed), width and anchors, as they are
in the saved font. A base edited afterwards leaves the derived glyph built
on the old one (an anchor copied from where it was, a turned serif that no
longer matches), which tests/test_built_from.py reports. Then either rebuild
it (derive.py --redraft for an unreviewed draft) or, having looked at it,
--accept: the glyph still fits, its fingerprints are taken anew.

Only the Regular carries the key: the generated styles are checked by
`make reproduce`, and make_bold.write drops it.
"""

import argparse
import hashlib
import json
import sys

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

KEY = "org.myiadidot.builtFrom"


def fingerprint(font, name):
    """A short hash of a glyph's decomposed outline, width and anchors."""
    g = font[name]
    rec = DecomposingRecordingPen(font)
    g.draw(rec)
    outline = [(op, [(round(x), round(y)) for x, y in args]) for op, args in rec.value]
    anchors = sorted((a.name or "", round(a.x), round(a.y)) for a in g.anchors)
    data = json.dumps([outline, g.width, anchors], separators=(",", ":"))
    return hashlib.sha1(data.encode()).hexdigest()[:12]


class Tracker:
    """The font, recording the names of the glyphs read from it."""

    def __init__(self, font):
        self._font = font
        self.read = set()

    def __getitem__(self, name):
        g = self._font[name]
        self.read.add(name)
        return g

    def get(self, name, default=None):
        return self[name] if name in self._font else default

    def __contains__(self, name):
        return name in self._font

    def __iter__(self):
        return iter(self._font)

    def __len__(self):
        return len(self._font)

    def __getattr__(self, attr):
        return getattr(self._font, attr)

    def __setattr__(self, attr, value):
        if attr.startswith("_") or attr == "read":
            object.__setattr__(self, attr, value)
        else:
            setattr(self._font, attr, value)

    def __delitem__(self, name):
        del self._font[name]


def stamp(font, name, bases):
    """Record the current fingerprints of bases in glyph name."""
    font[name].lib[KEY] = {b: fingerprint(font, b) for b in sorted(set(bases) - {name}) if b in font}


def changed(font, names=None):
    """{glyph: [base: why, ...]} for glyphs whose recorded bases differ now."""
    out = {}
    for g in font:
        if names and g.name not in names:
            continue
        recorded = g.lib.get(KEY)
        if not recorded:
            continue
        why = []
        for base, fp in sorted(recorded.items()):
            if base not in font:
                why.append(f"{base} gone")
            elif fingerprint(font, base) != fp:
                why.append(f"{base} changed")
        if why:
            out[g.name] = why
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--accept", action="store_true",
                    help="take the bases' current fingerprints (the glyphs were checked)")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    found = changed(font, set(args.glyphs) or None)
    if args.accept:
        if not args.glyphs:
            sys.exit("--accept needs the glyphs, by name")
        for name in args.glyphs:
            if KEY not in font[name].lib:
                sys.exit(f"{name}: no {KEY}")
            stamp(font, name, font[name].lib[KEY])
        font.save()
        print(f"accepted {len(args.glyphs)}")
        return
    for name, why in sorted(found.items()):
        print(f"{name}: {', '.join(why)}")
    print(f"{len(found)} built on bases changed since", file=sys.stderr)
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
