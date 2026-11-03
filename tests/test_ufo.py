"""Structural integrity of the source UFOs (no build needed)."""

import subprocess
import sys
import unicodedata
from collections import Counter

from conftest import ROOT


def test_components_exist(ufo):
    missing = [(g.name, c.baseGlyph) for g in ufo for c in g.components if c.baseGlyph not in ufo]
    assert not missing, f"components referencing missing glyphs: {missing}"


def test_no_component_cycles(ufo):
    def walk(name, seen):
        if name in seen:
            raise AssertionError(f"component cycle through {name}")
        for c in ufo[name].components:
            walk(c.baseGlyph, seen | {name})

    for g in ufo:
        walk(g.name, frozenset())


def test_unicodes_unique(ufo):
    counts = Counter(u for g in ufo for u in g.unicodes)
    dup = {f"U+{u:04X}": [g.name for g in ufo if u in g.unicodes] for u, n in counts.items() if n > 1}
    assert not dup, f"code points encoded twice: {dup}"


def test_glyph_order_complete(ufo):
    order = ufo.glyphOrder
    assert len(order) == len(set(order)), "duplicate names in public.glyphOrder"
    assert set(ufo.keys()) <= set(order), f"glyphs missing from glyphOrder: {sorted(set(ufo.keys()) - set(order))}"
    assert order[0] == ".notdef"


def test_every_glyph_has_a_category(ufo):
    cats = ufo.lib.get("public.openTypeCategories", {})
    missing = sorted(set(ufo.keys()) - set(cats) - {".notdef"})
    assert not missing, f"no public.openTypeCategories entry: {missing}"
    stale = sorted(set(cats) - set(ufo.keys()))
    assert not stale, f"categories for glyphs that do not exist: {stale}"


def test_marks_have_zero_width_and_attachment_anchors(ufo):
    cats = ufo.lib.get("public.openTypeCategories", {})
    known_spacing = {"uni0314"}  # upstream oddity, tracked for Phase 1
    bad_width, no_anchor = [], []
    for name, cat in cats.items():
        if cat != "mark" or name not in ufo:
            continue
        g = ufo[name]
        if g.width != 0 and name not in known_spacing:
            bad_width.append(name)
        if g.unicode is not None and not any(a.name.startswith("_") for a in g.anchors):
            no_anchor.append(name)
    assert not bad_width, f"mark glyphs with width: {bad_width}"
    known_unanchored = {"uni0328"}  # ogonek: attached by ccmp ligatures only
    assert not set(no_anchor) - known_unanchored, f"encoded marks without _anchor: {no_anchor}"


def test_anchor_names_unique_per_glyph(ufo):
    dup = {g.name: n for g in ufo for n, k in Counter(a.name for a in g.anchors).items() if k > 1}
    assert not dup, f"duplicate anchors: {dup}"


def test_encoded_marks_are_categorised_mark(ufo):
    cats = ufo.lib.get("public.openTypeCategories", {})
    known = {"uni0327", "uni0328"}  # upstream: cedilla/ogonek classed base
    wrong = [g.name for g in ufo
             if g.unicode is not None and unicodedata.category(chr(g.unicode)) == "Mn"
             and cats.get(g.name) != "mark" and g.name not in known]
    assert not wrong, f"combining characters not in the mark class: {wrong}"


def test_ufo_is_normalized(ufo_path, tmp_path):
    """Sources are committed normalized, so diffs stay readable."""
    copy = tmp_path / ufo_path.name
    subprocess.run(
        [str(ROOT / ".venv/bin/ufonormalizer"), "-q", "-a", "-m", "-o", str(copy), str(ufo_path)],
        check=True,
    )
    diff = subprocess.run(["diff", "-rq", str(ufo_path), str(copy)],
                          capture_output=True, text=True, check=False)
    assert diff.returncode == 0, "UFO not normalized; run `make normalize`:\n" + diff.stdout[:2000]


def test_no_sync_leftovers(ufo_path):
    """The working copy is in a synced folder: rewriting many files fast can
    leave "(conflicted)" copies and glyphs listed whose file is gone
    (scripts/sync_check.py)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from sync_check import leftovers

    found = leftovers(ufo_path)
    assert not found, f"sync leftovers: {found[:20]}"


def test_names_and_code_points_agree(ufo):
    """A glyph named for a character (AGL name, uniXXXX, uXXXXX) is mapped to
    it: code points look alike (U+A780 was typed for U+A7AD), names less so."""
    from fontTools import agl

    wrong = []
    for g in ufo:
        if "." in g.name or "_" in g.name:
            continue
        ch = agl.toUnicode(g.name)
        if len(ch) == 1 and 0xE000 <= ord(ch) <= 0xF8FF:
            continue  # Adobe's private-use names (Acute, oneoldstyle): left unencoded
        if len(ch) == 1 and ord(ch) not in g.unicodes:
            wrong.append(f"{g.name} -> {[f'U+{u:04X}' for u in g.unicodes]}")
    assert not wrong, f"glyph names and code points disagree: {wrong}"
