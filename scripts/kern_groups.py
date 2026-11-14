"""Kerning groups for letters left out of them (run on the Regular; the
other styles take its groups when they are generated).

    python scripts/kern_groups.py UFO [--dry-run]

1. An accented letter joins its base letter's group, side by side, where
   its base is in one and it is in none (NFD base, or the base component
   of a mark composite: Ạ ẫ Ṭ й ѝ).
2. A letter whose side is shaped like another's joins that letter's group
   on that side (ALIKE: Cyrillic Ѕ Ј Ү Ө as S J Y O, Ɔ Ʌ Ɐ Ƭ, ə as o),
   found by scripts/quality/kern_coverage.py and reviewed.

A letter joins only where the group's kerning leaves its ink clear of the
letters it meets in every style (sources/MyiaDidot-*.ufo): no closer than
the base (the model) in the same pair, or MIN_GAP (kern_coverage.gap),
less SLACK.
Where an accent would come too near (Y ì, T ǐ, Τ Ἀ) the letter joins
guarded (lib GUARD_KEY): kern_clear.py gives it, in every style, an
exception to each pair that would bring it nearer than its gap allows; the
run lists those.

Idempotent: letters already in a group are left alone. Then smallcaps.py
(the small caps' groups follow the capitals'), `make normalize`.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
from kern_clear import GUARD_KEY
from kern_coverage import MIN_GAP, Profiles, base_of, membership, pairs_of

ROOT = Path(__file__).resolve().parent.parent
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
SLACK = 3  # units a letter may come nearer than its model (rounding, a serif's curve)

# letter: (model on its right side (kern1), model on its left side (kern2));
# None: that side stays as it is. Only sides as alike as the model's in all
# four styles (kern_coverage.py section 3, score under about 10), or whose
# pairs measured against the references come nearer their range in every
# style by joining (Ʋ ʋ), and letters that set with the model's script or
# alone. Sides reviewed and left out: kern_coverage.KEPT_OUT.
ALIKE = {
    # the digraphs (composites.DIGRAPHS): their left side the first
    # letter's, their right side the second's
    "uni01C4": ("Zcaron", "D"), "uni01C5": ("zcaron", "D"), "uni01C6": ("zcaron", "d"),  # Ǆ ǅ ǆ
    "uni01C7": ("J", "L"), "uni01C8": ("j", "L"), "uni01C9": ("j", "l"),  # Ǉ ǈ ǉ
    "uni01CA": ("J", "N"), "uni01CB": ("j", "N"), "uni01CC": ("j", "n"),  # Ǌ ǋ ǌ
    "uni01F1": ("Z", "D"), "uni01F2": ("z", "D"), "uni01F3": ("z", "d"),  # Ǳ ǲ ǳ
    # Cyrillic letters drawn as the Latin or Cyrillic ones
    "uni0405": ("S", "S"),  # Ѕ
    "uni0456": ("i", "i"),  # і
    "uni0458": ("j", "j"),  # ј
    "uni04AE": ("Y", "Y"),  # Ү
    "uni04B0": ("Y", "Y"),  # Ұ
    "uni04E8": ("O", "O"),  # Ө
    "uni04E9": ("uni043E", "uni043E"),  # ө
    "uni0473": ("uni043E", "uni043E"),  # ѳ
    "uni0454": (None, "uni0441"),  # є
    "uni04D8": ("uni042D", None),  # Ә
    "uni04D9": ("uni043E", None),  # ә
    "uni0432": (None, "uni0433"),  # в
    "uni0492": ("uni0413", None),  # Ғ
    "uni0493": ("uni0433", "uni0433"),  # ғ
    # Greek
    "uni037F": ("J", "J"),  # Ϳ
    "uni03F3": ("j", "j"),  # ϳ
    # Latin: turned, barred, hooked letters of African and other alphabets
    "uni0245": ("A", "A"),  # Ʌ
    "uni2C6F": ("V", "V"),  # Ɐ
    "uni0186": ("O", None),  # Ɔ
    "uni019F": ("O", "O"),  # Ɵ
    "uni0298": ("O", "O"),  # ʘ
    "uni018F": ("uni042D", None),  # Ə
    "uni0259": ("o", None),  # ə
    "uni01DD": ("o", None),  # ǝ
    "uni0254": ("o", None),  # ɔ
    "uni0275": ("o", "o"),  # ɵ
    "uni025E": (None, "o"),  # ɞ
    "Dcroat": ("D", None),  # Đ
    "uni0189": ("D", None),  # Ɖ
    "uni018A": ("D", None),  # Ɗ
    "uniA7C7": ("D", None),  # Ꟈ
    "uni0181": ("B", None),  # Ɓ
    "uni0182": ("uni0411", None),  # Ƃ
    "uni0183": ("b", None),  # ƃ
    "uni1D6C": ("b", None),  # ᵬ
    "uni01A4": ("P", None),  # Ƥ
    "uni2C63": ("P", None),  # Ᵽ
    "uni024C": ("R", None),  # Ɍ
    "uni024D": ("r", None),  # ɍ
    "uni027E": ("r", None),  # ɾ
    "uni023D": ("L", None),  # Ƚ
    "uni2C62": ("L", None),  # Ɫ
    "uniA7AD": ("L", None),  # Ɬ
    "uni01AC": ("T", None),  # Ƭ
    "Tbar": ("T", "T"),  # Ŧ
    "IJ": ("J", None),  # Ĳ
    "uni0248": ("J", "J"),  # Ɉ
    "uni0249": (None, "j"),  # ɉ
    "uni029D": (None, "j"),  # ʝ
    "uni01E4": (None, "G"),  # Ǥ
    "uni01E5": (None, "g"),  # ǥ
    "uni0263": (None, "gamma"),  # ɣ
    "uni019C": ("U", "U"),  # Ɯ
    "uni026F": (None, "u"),  # ɯ
    "uni0244": ("U", "U"),  # Ʉ
    "uni0289": (None, "u"),  # ʉ
    "uni028B": ("a", "u"),  # ʋ
    "uni01B2": ("U", "U"),  # Ʋ
    "uni2C72": (None, "V"),  # Ⱳ
    "uni2C73": (None, "v"),  # ⱳ
    "uni01B3": (None, "Y"),  # Ƴ
    "uni01B4": (None, "y"),  # ƴ
    "kgreenlandic": (None, "uni0433"),  # ĸ
    "uni01A9": (None, "Sigma"),  # Ʃ
    "uniA78D": (None, "uni0427"),  # Ɥ
    "uniA7B3": ("Chi", "Chi"),  # Ꭓ
    "uniAB53": ("chi", "chi"),  # ꭓ
    "uniA7B7": (None, "omega"),  # ꞷ
    "uni019B": ("lambda", "lambda"),  # ƛ
    # localized forms (locl): as the letter they stand for, or whose shape
    # they take; the italic's own shapes are held clear like the others
    "uni0431.loclSRB": ("uni043E", "uni043E"),  # Serbian б: ∂, round both sides
    "uni0433.loclSRB": ("uni0433", "uni0433"),  # г (italic ī)
    "uni0434.loclSRB": ("uni0434", "uni0434"),  # д (italic g)
    "uni043F.loclSRB": ("uni043F", "uni043F"),  # п (italic ū)
    "uni0442.loclSRB": ("uni0442", "uni0442"),  # т (italic ш̄)
    "uni0453.loclSRB": ("uni0453", "uni0453"),  # ѓ (italic í)
    "uni0434.loclBGR": ("uni0261", "uni0261"),  # Bulgarian д: ɡ
    "uni0438.loclBGR": ("u", "u"),  # и: u
    "uni043A.loclBGR": ("k", "k"),  # к: k
    "uni0199": ("k", None),  # ƙ: k's arm (ƙa stood as loose as k unkerned)
    "uni043B.loclBGR": ("uni028C", "uni028C"),  # л: ʌ
    "uni043F.loclBGR": ("n", "n"),  # п: n
    "uni0442.loclBGR": ("m", "m"),  # т: m
    "uni0446.loclBGR": ("uni0446", "u"),  # ц: u with ц's tail
    "uni0448.loclBGR": (None, "u"),  # ш: ɯ
    "uni0449.loclBGR": ("uni0449", "u"),  # щ: ɯ with щ's tail
    "uni0432.loclBGR": ("b", "b"),  # в: b with a bowl above
    "uni0436.loclBGR": ("uni0436", "uni0436"),  # ж: its middle stem tall
    "uni044A.loclBGR": ("uni044A", None),  # ъ: its arm raised
    "uni044C.loclBGR": ("uni044C", "b"),  # ь: with an ascender
    "uni044E.loclBGR": ("uni044E", "b"),  # ю: with an ascender
}


def clear(fonts, name, model, group, s):
    """None if name keeps clear in group's pairs in every style, else the
    closest miss: (style, other letter, kern, gap, the model's gap)."""
    for style, (font, prof) in fonts.items():
        if name not in font or model not in font:
            continue
        for other, v in pairs_of(font, group, s):
            a, b = (name, other) if s == 1 else (other, name)
            ma, mb = (model, other) if s == 1 else (other, model)
            gap, mgap = prof.gap(a, b, v), prof.gap(ma, mb, v)
            if gap is None:
                continue
            if gap < min(mgap if mgap is not None else gap, MIN_GAP) - SLACK:
                return style, other, v, gap, mgap
    return None


def proposals(font, side):
    """(name, side, model, group, why) for each letter side to join."""
    cmap = {u: g.name for g in font for u in g.unicodes}
    out = []
    for g in font:
        name = g.name
        if name.endswith(".sc") or ".sc." in name:
            continue
        base = base_of(font, cmap, name)
        alike = ALIKE.get(name, (None, None))
        for s in (1, 2):
            if name in side[s]:
                continue
            if base in side[s]:
                out.append((name, s, base, side[s][base], "accented"))
            elif alike[s - 1] in side[s]:
                out.append((name, s, alike[s - 1], side[s][alike[s - 1]], "alike"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    font = ufoLib2.Font.open(a.ufo)
    fonts = {"Regular": (font, Profiles(font))}
    for style in STYLES[1:]:
        path = ROOT / "sources" / f"MyiaDidot-{style}.ufo"
        if path.exists():
            other = ufoLib2.Font.open(path)
            fonts[style] = (other, Profiles(other))
    side = membership(font)
    joined = guarded = 0
    guard = font.lib.setdefault(GUARD_KEY, {})
    for name, s, model, group, why in proposals(font, side):
        miss = clear(fonts, name, model, group, s)
        ch = chr(font[name].unicodes[0]) if font[name].unicodes else name
        font.groups[group] = list(font.groups[group]) + [name]
        if miss:
            style, other, v, gap, mgap = miss
            near = f", {model} {mgap:.0f}" if mgap is not None else ""
            print(f"guard {ch} {name} kern{s} {group}: with {other} ({v}) in {style}, gap {gap:.0f}{near}")
            guard[name] = sorted(set(guard.get(name, [])) | {s})
            guarded += 1
            continue
        joined += 1
        print(f"join  {ch} {name} kern{s} {group} ({why})")
    font.lib[GUARD_KEY] = dict(sorted(guard.items()))
    if not font.lib[GUARD_KEY]:
        del font.lib[GUARD_KEY]
    print(f"{joined} letter sides joined a group, {guarded} guarded (kern_clear.py)")
    if not a.dry_run and joined + guarded:
        font.save()


if __name__ == "__main__":
    sys.exit(main())
