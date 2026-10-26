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
import ufoLib2
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SOURCES = Path(os.environ.get("MYIA_SOURCES", ROOT / "sources"))
DATA = Path(__file__).resolve().parent / "data"
UFO_PATHS = sorted(p for p in SOURCES.glob("*.ufo") if p.is_dir())

sys.path.insert(0, str(ROOT / "scripts"))
from baseline_support import style_data as style_data


def pytest_generate_tests(metafunc):
    if "ufo_path" in metafunc.fixturenames:
        metafunc.parametrize("ufo_path", UFO_PATHS, ids=[p.stem for p in UFO_PATHS], scope="session")


@pytest.fixture(scope="session")
def ufo(ufo_path):
    return ufoLib2.Font.open(ufo_path)


@pytest.fixture(scope="session")
def otf_path(ufo_path):
    from font_builds import compiled_variant

    return compiled_variant(ufo_path, "test_otf")


@pytest.fixture(scope="session")
def ttfont(otf_path):
    return TTFont(otf_path)


from font_shaping import Shaper


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
