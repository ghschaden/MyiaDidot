"""The graph behind `--only`: which glyphs a generator reads to make a glyph.

    python scripts/only.py STYLE GLYPH ...     # D and N for the glyphs asked
    python scripts/only.py --closures          # D and N for a-z A-Z -> build/only/closures.txt

Specified in docs/claude/only.md ("Stage B: the closure"). `reads(source,
regular, italic)` returns {glyph: set of glyphs it is made from}, put
together from six sources; **too many edges cost time, a missing edge costs a
wrong preview**, so where in doubt the edge is added.

    D = the glyphs asked for and every glyph that reads one, however far
    N = D, everything D reads, however far, and ROOTS (what a run holds)

`closure()` refuses (OnlyError) a glyph not in the source, and one whose D
meets ROOTS: a measure of the whole style cannot be asked for.

EXTRA is what the generators read by name, found by reading their functions;
it is to be completed by grepping `font["` and `regular["` in what the two
`main`s call. tests/test_only_graph.py holds the expectations, and the
single-glyph tier of tests/test_only.py (when `--only` exists) is what finds
an edge that is missing.
"""

import re
import sys
from pathlib import Path

import ufoLib2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "quality"))

BUILT_FROM = "org.myiadidot.builtFrom"

# glyphs every other glyph is measured against, always present in a run:
# o (derive.strokes scales every recipe), n, H, l, bar, zero and zerosuperior
# (small_glyphs' scale), f (the hooks' top)
ROOTS = ["o", "n", "H", "l", "bar", "zero", "zerosuperior", "f"]

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

# (reader, read, where): glyphs a generator reads by name, not through a
# recipe, a component or a name. To be completed.
EXTRA = [
    ("W", "V", "make_italic.redraw_w"),
    ("w.sc", "v.sc", "make_italic.redraw_w"),
    ("uni0258", "e", "make_italic.swapped_sidebearings"),
    ("uni027A", "l", "make_italic r_hook"),
    ("uni027D", "r", "make_italic r_hook"),
    ("y", "dotbelowcomb", "y_dot.y_dot_anchor"),
    ("t", "dotbelowcomb", "t_dot_anchor"),
]


class OnlyError(Exception):
    pass


def _cmap(font):
    return {u: g.name for g in font for u in g.unicodes}


def _recipe_edges(font, italic, edges):
    import derive
    from derived import recipes

    cmap = _cmap(font)
    for ch, op, base, band in recipes(italic):
        reader = derive.resolve(cmap, ch)
        if reader not in font:
            continue
        names = []
        if isinstance(base, str):
            names.append(derive.resolve(cmap, base))
        if op == "attach" and isinstance(band, tuple) and len(band) >= 3 and band[2]:
            names += [p[0] for p in band[2] if isinstance(p, (tuple, list)) and p and isinstance(p[0], str)]
        for n in names:
            if n in font and n != reader:
                edges[reader].add(n)


def _name_edges(font, edges):
    import smallcaps

    names = {g.name for g in font}
    for name in names:
        stem = name.split(".")[0]
        if "_" in stem:  # ligatures read their parts
            for part in stem.split("_"):
                if part in names:
                    edges[name].add(part)
        if "." in name and name.endswith(".sc") is False and stem in names and stem != name:
            edges[name].add(stem)
    smcp, c2sc, multi_lo, multi_up = smcp_pairs(font, smallcaps)
    for source, target in list(smcp.items()) + list(c2sc.items()):
        if target in names and source in names:
            edges[target].add(source)
    for source, targets in list(multi_lo.items()) + list(multi_up.items()):
        for t in targets:
            if t in names and source in names:
                edges[t].add(source)
    # a small cap reads its capital and its lowercase both, whichever the pairing named
    for name in names:
        if name.endswith(".sc") and "." not in name[:-3]:
            for other in smcp_partners(name[:-3], names):
                edges[name].add(other)
    # figures: each of a set reads all ten of the set, and zero
    sets = {}
    for name in names:
        m = re.fullmatch(r"(" + "|".join(DIGITS) + r")(oldstyle)?(\..+)?", name)
        if m:
            sets.setdefault((m.group(2) or "", m.group(3) or ""), []).append(name)
    for members in sets.values():
        for a in members:
            edges[a].update(b for b in members if b != a)
            if "zero" in names and a != "zero":
                edges[a].add("zero")


def smcp_pairs(font, smallcaps):
    smcp, c2sc, multi_lo, multi_up = smallcaps.smcp_map(font)
    return smcp, c2sc, multi_lo, multi_up


def smcp_partners(stem, names):
    out = []
    for cand in (stem, stem[:1].upper() + stem[1:], stem.upper()):
        if cand in names and cand != stem + ".sc":
            out.append(cand)
    return out


def reads(source, regular, italic):
    """{glyph: set of glyphs read to make it} for the style whose source font
    is `source` (the Regular for the Italic and the Bold, the Italic for the
    Bold Italic)."""
    from collections import defaultdict

    edges = defaultdict(set)
    names = {g.name for g in source}
    # 1. components
    for g in source:
        for c in g.components:
            edges[g.name].add(c.baseGlyph)
    # 2. builtFrom of the Regular's glyph of the same name
    for g in regular:
        for b in (g.lib.get(BUILT_FROM) or {}):
            if g.name in names:
                edges[g.name].add(b)
    # 3. recipes
    _recipe_edges(source, italic, edges)
    # 4. names
    _name_edges(source, edges)
    # 5. named in the code
    import data_bold

    for reader, base in data_bold.SLASHED.items():
        edges[reader].add(base)
    for reader, base, _where in EXTRA:
        edges[reader].add(base)
    return {k: {x for x in v if x in names and x != k} for k, v in edges.items() if k in names}


def reverse(graph):
    from collections import defaultdict

    rev = defaultdict(set)
    for reader, bases in graph.items():
        for b in bases:
            rev[b].add(reader)
    return rev


def _reach(start, edges):
    seen = set(start)
    todo = list(start)
    while todo:
        for n in edges.get(todo.pop(), ()):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def closure(graph, font, asked):
    """(D, N) for the glyphs asked. OnlyError for a glyph the font lacks or a
    measure of the whole style."""
    names = {g.name for g in font}
    cmap = _cmap(font)
    want = []
    for a in asked:
        n = a if a in names else cmap.get(ord(a)) if len(a) == 1 else None
        if n is None or n not in names:
            raise OnlyError(f"{a}: not in the source (a new glyph changes the glyph order: use --out without --only)")
        want.append(n)
    roots = [r for r in ROOTS if r in names]
    D = _reach(want, reverse(graph))
    hit = sorted(set(roots) & D)
    if hit:
        raise OnlyError(f"{' '.join(want)}: {' '.join(hit)} is a measure of the whole style "
                        "(or built on what is asked): use --out without --only")
    N = _reach(D, graph) | set(roots)
    return D, N


def load(style):
    italic = style in ("Italic", "BoldItalic")
    src = {"Italic": "Regular", "Bold": "Regular", "BoldItalic": "Italic"}[style]
    source = ufoLib2.Font.open(ROOT / "sources" / f"MyiaDidot-{src}.ufo")
    regular = ufoLib2.Font.open(ROOT / "sources" / "MyiaDidot-Regular.ufo")
    return source, regular, italic


def main(argv):
    if argv[:1] == ["--closures"]:
        out = ROOT / "build" / "only" / "closures.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for style in ("Bold", "Italic", "BoldItalic"):
            source, regular, italic = load(style)
            graph = reads(source, regular, italic)
            lines.append(f"{style}: {len(source)} glyphs, {sum(len(v) for v in graph.values())} edges")
            for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                try:
                    D, N = closure(graph, source, [ch])
                    lines.append(f"  {ch}: D {len(D)}  N {len(N)}")
                except OnlyError as e:
                    lines.append(f"  {ch}: refused ({e})")
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    style, asked = argv[0], argv[1:]
    source, regular, italic = load(style)
    try:
        D, N = closure(reads(source, regular, italic), source, asked)
    except OnlyError as e:
        print(f"only: {e}")
        return 1
    print(f"only: {len(asked)} asked, {len(D) - len(asked)} built from them, {len(N)} read")
    print("D:", *sorted(D))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
