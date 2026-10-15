"""Shared fixtures: the source UFOs and an in-process OTF build of each.

Fonts are built once per test session without production names, so tests
can talk about glyphs by their source names. The result of the run is
written to build/test-status.json (read by the editor tooling's status line).
"""

import json
import os
import sys
import time
from pathlib import Path

import pytest
import ufo2ft
import ufoLib2
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SOURCES = Path(os.environ.get("MYIA_SOURCES", ROOT / "sources"))
DATA = Path(__file__).resolve().parent / "data"
UFO_PATHS = sorted(p for p in SOURCES.glob("*.ufo") if p.is_dir())

sys.path.insert(0, str(ROOT / "scripts"))


def style_data(name, ufo_path):
    """A per-style baseline: the Regular's under its plain name (as before
    there were other styles), other styles' with the style added
    (shaping-golden.json -> shaping-golden-Bold.json). Coverage and the
    exception lists are shared: every style must do what the Regular does."""
    style = Path(ufo_path).stem.split("-", 1)[-1]
    if style == "Regular":
        return DATA / name
    stem, _, ext = name.partition(".")
    return DATA / f"{stem}-{style}.{ext}"


def pytest_generate_tests(metafunc):
    if "ufo_path" in metafunc.fixturenames:
        metafunc.parametrize("ufo_path", UFO_PATHS, ids=[p.stem for p in UFO_PATHS], scope="session")


@pytest.fixture(scope="session")
def ufo(ufo_path):
    return ufoLib2.Font.open(ufo_path)


@pytest.fixture(scope="session")
def otf_path(ufo_path, tmp_path_factory):
    font = ufoLib2.Font.open(ufo_path)
    otf = ufo2ft.compileOTF(font, useProductionNames=False, optimizeCFF=0)
    path = tmp_path_factory.mktemp("fonts") / f"{ufo_path.stem}.otf"
    otf.save(path)
    return path


@pytest.fixture(scope="session")
def ttfont(otf_path):
    return TTFont(otf_path)


class Shaper:
    def __init__(self, path):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.order = TTFont(path).getGlyphOrder()

    def shape(self, text, features=None, language=None, script=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        if language:
            buf.language = language
        hb.shape(self.font, buf, features or {})
        return [
            (self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions, strict=True)
        ]


@pytest.fixture(scope="session")
def shaper(otf_path):
    return Shaper(otf_path)


@pytest.fixture(scope="session")
def decomposing_shaper(otf_path, tmp_path_factory):
    """A shaper for a copy of the font with no precomposed characters in cmap.

    HarfBuzz recomposes decomposed input whenever the font maps the
    precomposed character, so this copy is what exercises mark positioning.
    """
    import unicodedata

    font = TTFont(otf_path)
    for table in font["cmap"].tables:
        for cp in list(table.cmap):
            nfd = unicodedata.normalize("NFD", chr(cp))
            if len(nfd) > 1:
                del table.cmap[cp]
    path = tmp_path_factory.mktemp("decomposed") / otf_path.name
    font.save(path)
    return Shaper(path)


def pytest_sessionfinish(session, exitstatus):
    if "MYIA_SOURCES" in os.environ:
        return  # a run on other sources (mutation tests) says nothing about ours
    status_dir = ROOT / "build"
    status_dir.mkdir(exist_ok=True)
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    stats = reporter.stats if reporter else {}
    status = {
        "time": int(time.time()),
        "exitstatus": int(exitstatus),
        "passed": len(stats.get("passed", [])),
        "failed": len(stats.get("failed", [])) + len(stats.get("error", [])),
        "failures": [r.nodeid for r in stats.get("failed", []) + stats.get("error", [])][:20],
    }
    (status_dir / "test-status.json").write_text(json.dumps(status, indent=1) + "\n")
