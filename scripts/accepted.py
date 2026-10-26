"""Which glyphs the person has accepted, and whether they have changed since.

    python scripts/accepted.py UFO                              # accepted glyphs changed since
    python scripts/accepted.py UFO GLYPH ... --date D --review DOC
    python scripts/accepted.py UFO --drafts                     # drafts not accepted

A glyph's lib KEY records the person's visual acceptance: the date, the
review it was given in (a doc or proof) and the fingerprint of the glyph
accepted (built_from.fingerprint: outline, width, anchors). It does not
freeze anything: unlike clearing an Italic draft's flag (make_italic.reviewed),
the generators still make the glyph anew, and make_bold.write carries the
key over to it. A glyph that has changed since is reported here and by
tests/test_accepted.py: look at it again, then accept it anew (or remove
the key with --withdraw).
"""

import argparse
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint

KEY = "org.myiadidot.accepted"
DRAFT_KEYS = ("org.myiadidot.draft", "org.myiadidot.smallcapDraft")


def stamp(font, name, date, review):
    font[name].lib[KEY] = {"date": date, "review": review, "glyph": fingerprint(font, name)}


def changed(font):
    """{glyph: its acceptance} for accepted glyphs no longer as accepted."""
    return {g.name: g.lib[KEY] for g in font if KEY in g.lib and g.lib[KEY]["glyph"] != fingerprint(font, g.name)}


def acceptances(font):
    return {g.name: g.lib[KEY] for g in font if KEY in g.lib}


def carry(accepted, font):
    """accepted (acceptances of the style as last saved) onto font, the same
    style made anew, in place of any it has (those of the style it was made
    from: the Bold begins as the Regular's glyphs)."""
    for g in font:
        g.lib.pop(KEY, None)
    for name, acceptance in accepted.items():
        if name in font:
            font[name].lib[KEY] = acceptance


def unaccepted_drafts(font):
    return [g.name for g in font if KEY not in g.lib and any(g.lib.get(k) for k in DRAFT_KEYS)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--review")
    ap.add_argument("--withdraw", action="store_true")
    ap.add_argument("--drafts", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    if args.drafts:
        print("\n".join(unaccepted_drafts(font)))
        return
    if not args.glyphs:
        for name, was in sorted(changed(font).items()):
            print(f"{name}: changed since accepted {was['date']} ({was['review']})")
        return
    missing = [n for n in args.glyphs if n not in font]
    if missing:
        sys.exit(f"not in the font: {' '.join(missing)}")
    if not args.withdraw and not (args.date and args.review):
        sys.exit("--date and --review name the acceptance")
    for name in args.glyphs:
        if args.withdraw:
            font[name].lib.pop(KEY, None)
        else:
            stamp(font, name, args.date, args.review)
    font.save()
    print(f"{'withdrawn' if args.withdraw else 'accepted'}: {len(args.glyphs)}")


if __name__ == "__main__":
    main()
