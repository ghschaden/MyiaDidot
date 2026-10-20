"""Draft the Vietnamese hook above (U+0309) and horn (U+031B), with the
Horn anchors on O U o u and their small caps.

    python scripts/draft_vietnamese_marks.py UFO [--redraft]

hook above: the curve of the question mark (ʔ above its stem), scaled to
    accent size and brought up to the weight of the other accents; spacing
    forms `hook`/`Hook` (880 wide, centred at 440, unencoded), combining
    `hookcomb` (U+0309) and `hookcomb.cap`, like acute/acutecomb.
horn: the comma scaled down and brought up to an accent's weight (scaled
    alone it stood at half the comma's weight, lighter than any reference's
    horn: Old Standard's is 0.7 of its comma; at 0.56 of it and +24 it was
    still smaller and lighter than EB Garamond's and Libertinus's, now
    about their size), its tail on the base's Horn
    anchor so the ball rises up and to the right; `horn`/`Horn` and `horncomb` (U+031B) /
    `horncomb.cap` with a `_Horn` anchor at the tail.
Horn anchors: on the bowl's outline at 50 degrees (O o), on the right end
    of the top right serif or stem (U u), 24 units inside the ink; on Ư's
    own bases, U without its serif's outer arm (derive.py's U.horn,
    u.sc.horn; composites.py uses them), on the stem below the top.
circumflex with a tone mark: as habitual in Vietnamese typesetting
    (Trương, Vietnamese Typography), the acute, grave and hook above sit
    to the right of the circumflex, from halfway up its right arm, not on
    top of it: spacing `circumflex_acute` ... `Circumflex_Hook`, combining
    `circumflexcmb_acutecomb` ... `.cap`, formed from the separate marks by
    the ccmp lookup ccmpVietnameseToneMarks and used by composites.py for
    the precomposed letters. The tilde stays above the circumflex.

Glyphs are marked as drafts (lib org.myiadidot.draft). Existing glyphs are
kept unless they are unreviewed drafts and --redraft is given. Afterwards:
composites.py --stack-anchors, --add-missing, smallcaps.py.
"""

import argparse
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import BIG, draw_path, embolden, path_op, rect_path, stem_horn_anchor, stems_at, to_path
from smallcaps import ink_bounds

DRAFT_KEY = "org.myiadidot.draft"

# (spacing name, ink height, ink bottom, extra stem, extra hairline)
HOOKS = {"hook": (340, 1062, 44, 14), "Hook": (300, 1570, 50, 16)}
# (spacing name: scale of the comma, extra stem, extra hairline)
HORNS = {"horn": (0.67, 40, 12), "Horn": (0.79, 46, 14)}
INSIDE = 24
HORN_BASES = ("O", "U", "o", "u", "o.sc", "u.sc", "U.horn", "u.sc.horn")
# circumflex + tone mark: (spacing circumflex, tone, combining tone, overlap):
# the tone's ink starts overlap units left of the circumflex's right end
TONES = [("acute", "acutecomb", 70), ("grave", "gravecomb", 70), ("hook", "hookcomb", 40)]


def can_write(font, name, redraft):
    if name not in font:
        return True
    if redraft and font[name].lib.get(DRAFT_KEY):
        del font[name]
        return True
    return False


def new(font, name, width, unicode=None, category="base"):
    g = font.newGlyph(name)
    g.width = width
    if unicode:
        g.unicodes = [unicode]
    g.lib[DRAFT_KEY] = True
    font.lib.setdefault("public.openTypeCategories", {})[name] = category
    if name not in font.glyphOrder:
        font.glyphOrder = [*font.glyphOrder, name]
    return g


def hook_outline(font, height, bottom, ax, ay):
    """The question mark's curve above its stem, at accent size."""
    q = font["uni0294"] if "uni0294" in font else font["question"]
    stem_top = 700  # just below the curve: keeps a short tail of the stem
    curve = path_op(to_path(font, q), rect_path(-BIG, stem_top, BIG, BIG), "INTERSECTION")
    _, y0, _, y1 = curve.bounds
    k = (height - ay) / (y1 - y0)
    rec = RecordingPen()
    curve.draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
    g = embolden(rec, ax, ay)
    out = RecordingPen()
    g.draw(out)
    b = path_op(to_path(None, rec=out), rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION").bounds
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, 440 - (b[0] + b[2]) / 2, bottom - b[1])))
    return moved


def horn_outline(font, k, ax=0, ay=0):
    """The comma scaled by k and emboldened by (ax, ay), its tail tip at (0, 0)."""
    scaled = DecomposingRecordingPen(font)
    font["comma"].draw(TransformPen(scaled, (k, 0, 0, k, 0, 0)))
    rec = RecordingPen()
    embolden(scaled, ax, ay).draw(rec)
    tip = min((pt for _op, args in rec.value for pt in args), key=lambda p: (p[1], p[0]))
    moved = RecordingPen()
    rec.replay(TransformPen(moved, (1, 0, 0, 1, -tip[0], -tip[1])))
    return moved, tip


def horn_anchor(font, name):
    """Where the horn's tail goes: on a round bowl at 50°, else the right
    end of the ink at the top (serif or stem), INSIDE units into the ink;
    on a stem without its serif's outer arm (U.horn), on the stem."""
    if name.endswith(".horn"):
        return stem_horn_anchor(font, name, INSIDE)
    _, y0, _, y1 = ink_bounds(font, name)
    if name[0] in "Oo":
        cy, ry = (y0 + y1) / 2, (y1 - y0) / 2
        y = cy + ry * math.sin(math.radians(50))
        x = stems_at(font, name, y)[-1][1]
        a = math.radians(50)
        return round(x - INSIDE * math.cos(a)), round(y - INSIDE * math.sin(a))
    top = font.info.xHeight if name == "u" else y1
    y = top - 30
    x = stems_at(font, name, y)[-1][1]
    return round(x - INSIDE), round(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    made = []

    for name, (height, bottom, ax, ay) in HOOKS.items():
        cap = name[0].isupper()
        comb = "hookcomb" + (".cap" if cap else "")
        if can_write(font, name, args.redraft):
            g = new(font, name, 880)
            draw_path(font, font["acute"], g, hook_outline(font, height, bottom, ax, ay))
            made.append(name)
        if can_write(font, comb, args.redraft):
            g = new(font, comb, 0, None if cap else 0x0309, "mark")
            g.getPen().addComponent(name, (1, 0, 0, 1, -880, 0))
            anchor = ("_TopCap", 1580) if cap else ("_Top", 1000)
            g.appendAnchor({"name": anchor[0], "x": -440, "y": anchor[1]})
            made.append(comb)

    for name, (k, ax, ay) in HORNS.items():
        cap = name[0].isupper()
        comb = "horncomb" + (".cap" if cap else "")
        outline, _tip = horn_outline(font, k, ax, ay)
        if can_write(font, name, args.redraft):
            g = new(font, name, 880)
            moved = RecordingPen()
            outline.replay(TransformPen(moved, (1, 0, 0, 1, 440, 0)))
            draw_path(font, font["comma"], g, moved)
            made.append(name)
        if can_write(font, comb, args.redraft):
            g = new(font, comb, 0, None if cap else 0x031B, "mark")
            g.getPen().addComponent(name, (1, 0, 0, 1, -880, 0))
            g.appendAnchor({"name": "_Horn", "x": -440, "y": 0})
            made.append(comb)

    for cap in (False, True):
        circ = "Circumflex" if cap else "circumflex"
        c0, c1 = ink_bounds(font, circ)[0::2], ink_bounds(font, circ)[1::2]
        for tone, comb_tone, overlap in TONES:
            spacing_tone = tone.capitalize() if cap else tone
            spacing = f"{circ}_{spacing_tone}"
            comb = f"circumflexcmb_{comb_tone}" + (".cap" if cap else "")
            if can_write(font, spacing, args.redraft):
                t = ink_bounds(font, spacing_tone)
                dx = c0[1] - overlap - t[0]                 # just right of the circumflex
                dy = c1[0] + (c1[1] - c1[0]) / 2 - t[1]     # from halfway up its arm
                g = new(font, spacing, 880)
                pen = g.getPen()
                pen.addComponent(circ, (1, 0, 0, 1, 0, 0))
                pen.addComponent(spacing_tone, (1, 0, 0, 1, round(dx), round(dy)))
                made.append(spacing)
            if can_write(font, comb, args.redraft):
                g = new(font, comb, 0, None, "mark")
                g.getPen().addComponent(spacing, (1, 0, 0, 1, -880, 0))
                anchor = ("_TopCap", 1580) if cap else ("_Top", 1000)
                g.appendAnchor({"name": anchor[0], "x": -440, "y": anchor[1]})
                made.append(comb)

    for base in [b for b in HORN_BASES if b in font]:
        g = font[base]
        for a in [a for a in g.anchors if a.name == "Horn"]:
            g.anchors.remove(a)
        x, y = horn_anchor(font, base)
        g.appendAnchor({"name": "Horn", "x": x, "y": y})
        made.append(f"{base}.Horn({x},{y})")

    font.save()
    print("drafted:", " ".join(made))


if __name__ == "__main__":
    main()
