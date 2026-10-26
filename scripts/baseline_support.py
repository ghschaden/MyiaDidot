"""Locations and readers for reviewed per-style baselines."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tests/data"


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

