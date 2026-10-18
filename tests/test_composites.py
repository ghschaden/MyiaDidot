"""Composites agree with the anchor rules and with decomposed shaping.

* Each composite built by scripts/composites.py must still be what the rules
  produce from the current anchors (move an anchor, rerun the builder).
* Precomposed text (NFC) and decomposed text (NFD) must draw the same ink,
  so a document renders the same whichever normalization it is in.

Known exceptions live in tests/data/*.txt, one glyph or code point per line
with a reason; a test also fails when an exception has become stale, so the
lists only ever shrink.
"""

import unicodedata

from composites import SPECIAL, Builder
from conftest import DATA
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen


def read_list(name):
    path = DATA / name
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)
        key, reason = line[0].strip(), (line[1].strip() if len(line) > 1 else "")
        if key:
            out[key] = reason
    return out


def composite_mismatches(ufo):
    b = Builder(ufo)
    bad = {}
    for g in ufo:
        if g.unicode is None or g.contours or not g.components or g.name in SPECIAL:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        if "GREEK" in unicodedata.name(chr(g.unicode), ""):
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError as e:
            bad[g.name] = f"no recipe: {e}"
            continue
        have = sorted((c.baseGlyph, round(c.transformation[4]), round(c.transformation[5]))
                      for c in g.components)
        want = sorted((c.glyph, c.dx, c.dy) for c in r.components)
        if have != want:
            bad[g.name] = f"has {have}, rules give {want}"
    return bad


def test_composites_follow_rules(ufo):
    allowed = read_list("composite-exceptions.txt")
    bad = composite_mismatches(ufo)
    new = {k: v for k, v in bad.items() if k not in allowed}
    stale = sorted(set(allowed) - set(bad))
    assert not new, ("composites out of sync with anchors (rerun scripts/composites.py "
                     "or add to tests/data/composite-exceptions.txt):\n"
                     + "\n".join(f"  {k}: {v}" for k, v in new.items()))
    assert not stale, f"exceptions no longer needed, remove them: {stale}"


def ink(glyphset, shaped):
    """Contours of a shaped run, positioned, as a sorted tuple of point tuples."""
    contours, x = [], 0
    for name, adv, dx, dy in shaped:
        pen = DecomposingRecordingPen(glyphset)
        glyphset[name].draw(TransformPen(pen, (1, 0, 0, 1, x + dx, dy)))
        cur = []
        for op, args in pen.value:
            if op == "moveTo":
                cur = [tuple(round(v) for v in args[0])]
            elif op in ("closePath", "endPath"):
                contours.append(tuple(cur))
            else:
                cur.extend(tuple(round(v) for v in p) for p in args)
        x += adv
    return tuple(sorted(contours)), x


def nfd_mismatches(ttfont, shaper, decomposing_shaper):
    """Code points whose precomposed glyph differs from base + positioned marks.

    Singleton decompositions (U+0387 -> U+00B7, ...) map to a different
    character on purpose and are not compared.
    """
    gs = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()
    bad = {}
    for cp in sorted(cmap):
        ch = chr(cp)
        nfd = unicodedata.normalize("NFD", ch)
        if len(nfd) < 2 or not all(ord(c) in cmap for c in nfd):
            continue
        a, b = ink(gs, shaper.shape(ch)), ink(gs, decomposing_shaper.shape(nfd))
        if a != b:
            why = "advance differs" if a[0] == b[0] else "ink differs"
            bad[f"U+{cp:04X}"] = f"{ch} {why}"
    return bad


def test_nfc_and_nfd_render_the_same(ttfont, shaper, decomposing_shaper):
    allowed = read_list("nfd-exceptions.txt")
    bad = nfd_mismatches(ttfont, shaper, decomposing_shaper)
    new = {k: v for k, v in bad.items() if k not in allowed}
    stale = sorted(set(allowed) - set(bad))
    assert not new, ("precomposed and decomposed forms render differently (fix the anchors, "
                     "or compose them: scripts/nfd_compose.py; or add to "
                     "tests/data/nfd-exceptions.txt with a reason):\n"
                     + "\n".join(f"  {k} {v}" for k, v in new.items()))
    assert not stale, f"NFD exceptions no longer needed, remove them: {stale}"



def smallcap_mismatches(ttfont, shaper, decomposing_shaper):
    """Characters whose small cap differs between NFC and NFD input."""
    gs = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()
    bad = {}
    for cp in sorted(cmap):
        ch = chr(cp)
        if unicodedata.category(ch) not in ("Ll", "Lu", "Lt"):
            continue
        nfd = unicodedata.normalize("NFD", ch)
        if len(nfd) < 2 or not all(ord(c) in cmap for c in nfd):
            continue
        feats = {"smcp": True, "c2sc": True}
        a = ink(gs, shaper.shape(ch, feats))
        b = ink(gs, decomposing_shaper.shape(nfd, feats))
        if a != b:
            bad[f"U+{cp:04X}"] = f"{ch} small cap {'advance' if a[0] == b[0] else 'ink'} differs"
    return bad


def test_smallcaps_nfc_and_nfd_render_the_same(ttfont, shaper, decomposing_shaper):
    allowed = read_list("smallcap-nfd-exceptions.txt")
    bad = smallcap_mismatches(ttfont, shaper, decomposing_shaper)
    new = {k: v for k, v in bad.items() if k not in allowed}
    stale = sorted(set(allowed) - set(bad))
    assert not new, ("small caps differ between precomposed and decomposed input:\n"
                     + "\n".join(f"  {k} {v}" for k, v in new.items()))
    assert not stale, f"small-cap NFD exceptions no longer needed, remove them: {stale}"


def test_every_small_cap_is_reachable(ufo, ttfont):
    """Each .sc glyph is the target of smcp, c2sc or a stylistic set, or a component of one."""
    gsub = ttfont["GSUB"].table
    reached = set()
    for rec in gsub.FeatureList.FeatureRecord:
        if rec.FeatureTag not in ("smcp", "c2sc") and not rec.FeatureTag.startswith("ss"):
            continue
        for i in rec.Feature.LookupListIndex:
            for st in gsub.LookupList.Lookup[i].SubTable:
                for v in (getattr(st, "mapping", None) or {}).values():
                    reached.update(v if isinstance(v, list) else [v])
                for ligs in (getattr(st, "ligatures", None) or {}).values():
                    reached.update(lig.LigGlyph for lig in ligs)
    used_as_component = {c.baseGlyph for g in ufo for c in g.components}
    unreached = sorted(g.name for g in ufo if g.name.endswith(".sc")
                       and g.name not in reached and g.name not in used_as_component)
    assert not unreached, f"small caps no feature produces: {unreached}"
