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
import unicodedata
from pathlib import Path

import ufoLib2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "quality"))

BUILT_FROM = "org.myiadidot.builtFrom"

# glyphs every other glyph is measured against, always present in a run:
# o (derive.strokes scales every recipe), n, H, l, bar, zero and zerosuperior
# (small_glyphs' scale), f (the hooks' top), I (space_figures' floor), space (a recipe's width)
ROOTS = ["o", "n", "H", "I", "l", "bar", "zero", "zerosuperior", "f", "space"]

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
    ("t", "z", "make_italic.t_dot_anchor"),
    # make_italic.serbian_gje, serbian_bars (and make_bold's calls of them)
    *[("uni0453.loclSRB", r, "make_italic.serbian_gje") for r in ("imacron", "uni1E17", "macron.i", "macron", "acute")],
    *[(w, r, "make_italic.serbian_bars") for w, l in (("uni043F.loclSRB", "uni0438"), ("uni0442.loclSRB", "uni0448"))
      for r in ("umacron", "macron", "u", l)],
    # make_italic.level_gain (SC_LEVEL_GAIN): the small cap's stroke against h.sc's as the capital's against H's
    ("s.sc", "h.sc", "make_italic.level_gain"), ("s.sc", "S", "make_italic.level_gain"),
    ("s.sc", "H", "make_italic.level_gain"),
    ("n.sc", "h.sc", "make_italic.level_gain"), ("n.sc", "N", "make_italic.level_gain"),
    ("n.sc", "H", "make_italic.level_gain"),
]


# finishing passes (finalization.PASSES) that act on a set of glyphs together:
# (label, a set of names or a regex over names). A group that meets D is made
# again whole (but its roots, which are measures); one that meets N is held
# whole, so the pass can run: a pass that names a glyph the run lacks is
# skipped (finalization.SKIPPED) and leaves its glyphs as the generator drew
# them. To be completed as the single-glyph tier finds them.
PASS_GROUPS = [
    ("sc_feet.finish", {"m.sc", "v.sc", "w.sc", "k.sc", "x.sc"}),
    ("draft_ligatures.finish_f", re.compile(r"(f|f_.+|longs_.+|ff|fi|fl|fj|ffi|ffl|ffj|dotlessi|uni0237)")),
]


def _group(names, spec):
    if isinstance(spec, set):
        return spec & names
    return {n for n in names if spec.fullmatch(n.split(".")[0])}


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
        if names and names[0].endswith(".sc"):  # derive.ball_for: a ball's size from l.sc's stem
            names.append("l.sc")
        if op == "enlarge" and reader.endswith(".sc"):  # make_bold.small_cap_stems; derive.enlarge's o.sc
            names += ["h.sc", "o.sc"]
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
    # a mark is placed by the anchor rule in the variant its base wants (.cap
    # over a capital, .i over i ...): it reads them all
    cats = font.lib.get("public.openTypeCategories", {})
    for name in names:
        stem, _, suffix = name.partition(".")
        if suffix and stem in names and cats.get(stem) == "mark" and stem != name:
            edges[stem].add(name)
    # a precomposed letter is made by the anchor rule from the glyphs of its
    # decomposition (Á from A and U+0301's own glyph, not its .cap form)
    cmap = _cmap(font)
    for g in font:
        if g.unicode is None or len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        nfd = unicodedata.normalize("NFD", chr(g.unicode))
        for ch in nfd:
            n = cmap.get(ord(ch))
            if n and n != g.name:
                edges[g.name].add(n)
        # circumflex + tone: the pair glyph composites.vietnamese_tones looks for
        for a, b in zip(nfd[1:], nfd[2:], strict=False):
            pair = f"{cmap.get(ord(a))}_{cmap.get(ord(b))}"
            if pair in names:
                edges[g.name].add(pair)
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
    if italic:
        import italic_ligatures
        import make_italic

        edges["Q_u"].add("O")  # italic_ligatures.make: qu_ligature on this style's O and u
        for reader, base in italic_ligatures.LONGS:  # the long-s ligature from the f one
            edges[reader].add(base)

        for reader, base in make_italic.ITALIC_STANDS_AS.items():  # make_italic.stand_as
            edges[reader].add(base)
        for reader, base in make_italic.GREEK_CAP_SAMPLES.items():  # greek_cap_room: the capital's shift from its sample
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
    rev = reverse(graph)
    groups = [(label, _group(names, spec)) for label, spec in PASS_GROUPS]
    D = _reach(want, rev)
    for _ in range(len(groups) + 1):  # a group made again whole may reach another
        before = len(D)
        for _label, group in groups:
            if group & D:
                D |= _reach(group - set(roots), rev)
        if len(D) == before:
            break
    hit = sorted(set(roots) & D)
    if hit:
        raise OnlyError(f"{' '.join(want)}: {' '.join(hit)} is a measure of the whole style "
                        "(or built on what is asked): use --out without --only")
    N = _reach(D, graph) | set(roots)
    for _ in range(len(groups) + 1):
        before = len(N)
        for _label, group in groups:
            if group & N:
                N |= _reach(group, graph)
        if len(N) == before:
            break
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
