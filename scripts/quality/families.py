"""The known quality findings sorted by where each is mended.

    python scripts/quality/families.py                 (the four styles, a table each)
    python scripts/quality/families.py --style Italic --names
    python scripts/quality/families.py --family smallcap --kind kink --names
    python scripts/quality/families.py --clusters --names   (the design kinds by what they say;
                                                             ^ the parent's too, * a base's)
    python scripts/quality/families.py --json build/quality/families.json

Reads tests/data/quality*.txt and the four UFOs, changes nothing. Each
line of a list (glyph kind count) gets one family, the first that
applies (docs/claude/longtail.md has the method and what each family's
repair is):

    parent    the same glyph has the same kind in the list of the style
              it is made from (the Regular for the Italic and the Bold,
              the Italic for the Bold Italic): mended there, or one
              verdict for both
    base      a glyph it is built from (the recipe's builtFrom, its
              components, a small cap's letter and capital) has the kind
              in this style's list: mended in the base
    verdict   a design kind (stroke, slant, zone, weight, width, accent,
              base, stem, advance, style): no outline fault, a decision
    kept      a construction kind (kink, smooth, extreme, step, wobble)
              on a glyph kept as drawn in this style (scripts/drawn.py):
              mended on the letter
    marks     ... on a mark or sign the Italic takes from the Regular
              without a source of its own
    smallcap  ... on a small cap
    recipe    ... on a derived letter (derive.py and the styles' recipes);
              the table names the recipe's operation (attach, hook, bar)
    ligature  ... on a ligature or another draft
    letter    ... on a letter taken as it comes (Old Standard's, the
              Regular's sloped, the Regular's own source outline)

The second column of a table is the lineage (who makes the glyph), so a
family reads "smallcap kink": the small caps' kinks.
"""

import argparse
import collections
import json
import sys
import unicodedata
from pathlib import Path

import ufoLib2

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
PARENT = {"Italic": "Regular", "Bold": "Regular", "BoldItalic": "Italic"}
K = "org.myiadidot."
DESIGN = ("stroke", "slant", "zone", "weight", "width", "accent", "base", "stem", "advance", "style")
LIGATURES = {"ff": "f", "fi": "fi", "fl": "fl", "ffi": "fi", "ffl": "fl"}  # the letters of the unnamed ones
ITALIC_SOURCE = {
    "Old Standard": "letter", "sloped roman": "letter", "roman": "letter", "cyrillic sign drawing": "letter",
    "derived": "recipe", "small cap draft": "smallcap", "ligature": "ligature", "figure draft": "ligature",
    None: "marks",
}


def list_path(style):
    return ROOT / "tests/data" / ("quality.txt" if style == "Regular" else f"quality-{style}.txt")


def read_list(style):
    """[(glyph, kind, count, reason)] of a style's list"""
    out = []
    for line in list_path(style).read_text(encoding="utf-8").splitlines():
        head, _, why = line.partition("#")
        if head.strip():
            glyph, kind, count = head.split()
            out.append((glyph, kind, int(count), why.strip()))
    return out


def lineage(fonts, style, name):
    """who makes the glyph in this style"""
    lib = fonts[style][name].lib
    if K + "drawn" in lib:  # the one mark (drawn.py); a redraw's record alone passes on to the Bold Italic
        return "kept"
    if name.endswith(".sc") or ".sc." in name:
        return "smallcap"
    if style in ("Italic", "BoldItalic"):
        return ITALIC_SOURCE.get(fonts["Italic"][name].lib.get(K + "italicSource"), "letter")
    regular = fonts["Regular"][name].lib if name in fonts["Regular"] else {}
    if K + "builtFrom" in regular or K + "derived" in lib:
        return "recipe"
    if K + "draft" in lib:
        return "ligature"
    return "letter"


def bases(fonts, style, name):
    """the glyphs name is built from: the recipe's, its components, a
    small cap's letter and that letter's capital, a ligature's letters"""
    font = fonts[style]
    out = set(fonts["Regular"][name].lib.get(K + "builtFrom", ())) if name in fonts["Regular"] else set()
    out.update(c.baseGlyph for c in font[name].components)
    if name.endswith(".sc"):
        letter = name[: -len(".sc")]
        if letter in font:
            out.add(letter)
            u = font[letter].unicode
            cap = ord(chr(u).upper()) if u and len(chr(u).upper()) == 1 else None
            out.update(g.name for g in font if cap and cap in g.unicodes)
    stem = name.split(".")[0]
    parts = LIGATURES.get(stem) or (stem.split("_") if "_" in stem else ())
    out.update(p for p in parts if p in font)
    out.discard(name)
    return sorted(out)


def operations():
    """{style: {glyph name: its recipe's operation}}: the Regular's
    recipes, the italics' own over them"""
    import data_italic
    import data_regular
    from derive import glyph_name

    upright = {glyph_name(ch): op for ch, op, _, _ in data_regular.RECIPES}
    italic = dict(upright)
    italic.update({glyph_name(ch): recipe[0] for ch, recipe in data_italic.ITALIC_RECIPES.items()})
    return {"Regular": upright, "Bold": upright, "Italic": italic, "BoldItalic": italic}


def sort(fonts=None):
    """one row per line of the four lists: style, glyph, kind, count,
    reason, lineage, family, for parent and base where it stands, a
    recipe's operation, the script"""
    fonts = fonts or {s: ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{s}.ufo") for s in STYLES}
    lists = {s: read_list(s) for s in STYLES}
    ops = operations()
    rows = []
    for style in STYLES:
        here = {(g, k) for g, k, _, _ in lists[style]}
        above = {(g, k) for g, k, _, _ in lists.get(PARENT.get(style), ())}
        for glyph, kind, count, why in lists[style]:
            who = lineage(fonts, style, glyph)
            held = [b for b in bases(fonts, style, glyph) if (b, kind) in here]
            if (glyph, kind) in above:
                family, at = "parent", [PARENT[style]]
            elif held:
                family, at = "base", held
            elif kind in DESIGN:
                family, at = "verdict", []
            else:
                family, at = who, []
            rows.append({"style": style, "glyph": glyph, "kind": kind, "count": count, "reason": why,
                         "lineage": who, "family": family, "at": at,
                         "op": ops[style].get(glyph, "") if who == "recipe" else "",
                         "script": script(fonts[style], glyph)})
    return rows


def script(font, name):
    """Latin, Greek, Cyrillic or other, from the character's name (a
    small cap's or variant's from its letter's)"""
    glyph = font[name] if font[name].unicode else font.get(name.split(".")[0])
    word = unicodedata.name(chr(glyph.unicode), "").split(" ")[0] if glyph is not None and glyph.unicode else ""
    return word.capitalize() if word in ("LATIN", "GREEK", "CYRILLIC") else "other"


def clusters(row):
    """for a design kind, what the line says with the glyph's own numbers
    left out, so that lines of one decision come together: a zone and
    the offset from it, a stroke's script, case and side, a slant's side"""
    detail = row["reason"].rsplit(": ", 1)[-1]
    if row["kind"] == "zone":
        return [f"zone {part}" for part in detail.split("; ")]
    if row["kind"] == "stroke":
        side = detail.rstrip(")").split()[-1]
        return [f"stroke {row['script']} {detail.split()[0]} {side}" if side in ("lighter", "darker") else "stroke"]
    if row["kind"] == "slant":
        try:
            found, _, _, wanted = detail.replace(",", "").split()
            return ["slant " + ("upright of the angle" if float(found) < float(wanted) else "past the angle")]
        except ValueError:
            pass
    return [row["kind"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--style", action="append", choices=STYLES)
    ap.add_argument("--family", action="append")
    ap.add_argument("--kind", action="append")
    ap.add_argument("--names", action="store_true", help="the glyphs of each group")
    ap.add_argument("--clusters", action="store_true",
                    help="the design kinds by what they say (a zone's offset, a stroke's side), whatever the family")
    ap.add_argument("--json", help="every row, in full")
    args = ap.parse_args()
    rows = sort()
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for style in args.style or STYLES:
        mine = [r for r in rows if r["style"] == style and (not args.family or r["family"] in args.family)
                and (not args.kind or r["kind"] in args.kind)]
        groups = collections.defaultdict(list)
        for r in mine:
            groups[r["family"], r["op"] if r["family"] == "recipe" else r["lineage"], r["kind"]].append(r)
        totals = collections.Counter(r["family"] for r in mine)
        if args.clusters:
            said = collections.defaultdict(list)
            for r in mine:
                if r["kind"] in DESIGN:
                    for key in clusters(r):
                        said[key].append(r)
            print(f"{style}: {len(said)} clusters of the design kinds")
            for key, found in sorted(said.items(), key=lambda kv: -len(kv[1])):
                marks = {"parent": "^", "base": "*"}
                names = " ".join(r["glyph"] + marks.get(r["family"], "") for r in found)
                print(f"  {key:<28}{len(found):>4}" + (f"  {names}" if args.names else ""))
            print()
            continue
        print(f"{style}: {len(mine)} lines, {sum(r['count'] for r in mine)} findings")
        print("  " + ", ".join(f"{f} {n}" for f, n in totals.most_common()))
        for (family, who, kind), found in sorted(groups.items(), key=lambda kv: (-totals[kv[0][0]], kv[0][0], -len(kv[1]))):
            print(f"  {family:<9}{who:<9}{kind:<8}{len(found):>4} lines {sum(r['count'] for r in found):>4} findings")
            if args.names:
                names = " ".join(r["glyph"] + (f"({','.join(r['at'])})" if family == "base" else "") for r in found)
                print(f"      {names}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
