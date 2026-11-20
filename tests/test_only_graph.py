"""The `--only` graph (scripts/only.py): what a generator reads to make a glyph.

Tier 1 of docs/claude/only.md: no generator runs. Whether an edge is missing
is found only by the single-glyph tier that runs the generators."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import only  # noqa: E402

pytestmark = pytest.mark.skipif(not (ROOT / "sources" / "MyiaDidot-Regular.ufo").exists(), reason="no sources")


@pytest.fixture(scope="module", params=["Bold", "Italic", "BoldItalic"])
def style(request):
    source, regular, italic = only.load(request.param)
    return request.param, source, only.reads(source, regular, italic)


def test_every_edge_ends_in_the_source(style):
    _, source, graph = style
    names = {g.name for g in source}
    for reader, bases in graph.items():
        assert reader in names
        assert bases <= names, (reader, bases - names)


def test_roots_exist(style):
    _, source, _ = style
    assert set(only.ROOTS) <= {g.name for g in source}


def test_extra_ends_exist_in_the_regular():
    source, _, _ = only.load("Bold")
    names = {g.name for g in source}
    for reader, base, where in only.EXTRA:
        assert reader in names and base in names, (reader, base, where)


@pytest.mark.parametrize("root", only.ROOTS)
def test_a_measure_cannot_be_asked_for(style, root):
    _, source, graph = style
    with pytest.raises(only.OnlyError, match="measure"):
        only.closure(graph, source, [root])


def test_a_glyph_the_source_lacks_is_refused(style):
    _, source, graph = style
    with pytest.raises(only.OnlyError, match="not in the source"):
        only.closure(graph, source, ["nonesuchglyph"])


@pytest.mark.parametrize("asked, built", [
    ("b", "uni0253"),      # ɓ: builtFrom b and f
    ("e", "uni0258"),      # ɘ: swapped_sidebearings
    ("a", "aacute"),       # components
    ("O", "Oslash"),       # data_bold.SLASHED
])
def test_what_is_built_from_a_glyph(style, asked, built):
    _, source, graph = style
    D, N = only.closure(graph, source, [asked])
    assert built in D
    assert asked in D and set(only.ROOTS) <= N and D <= N


def test_the_italics_w_follows_v():
    source, regular, italic = only.load("Italic")
    D, _ = only.closure(only.reads(source, regular, italic), source, ["V"])
    assert "W" in D


def test_a_closure_is_a_small_part_of_the_font(style):
    _, source, graph = style
    for ch in "aeOgs":
        _, N = only.closure(graph, source, [ch])
        assert len(N) < len(source) / 4, (ch, len(N))


def test_the_test_can_fail(monkeypatch):
    """With the edges named in the code emptied, the Italic's W is no longer
    found from V (redraw_w reads V by name): the expectation above can fail."""
    monkeypatch.setattr(only, "EXTRA", [])
    source, regular, italic = only.load("Italic")
    D, _ = only.closure(only.reads(source, regular, italic), source, ["V"])
    assert "W" not in D
