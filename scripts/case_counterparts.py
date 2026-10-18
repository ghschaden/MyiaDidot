#!/usr/bin/env python3
"""Add the uppercase counterparts missing from Myia Didot's encoded coverage.

The shared forms use existing uppercase outlines: L with belt from Ƚ, Greek
Yot from J, and Latin chi from X. Latin YR is scaled from the font's small-cap
R to cap height. The generated glyphs are tagged with their source so reruns
leave reviewed glyphs untouched.

    python scripts/case_counterparts.py [UFO ...]
"""

import argparse
from pathlib import Path

import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Anchor, Component


COUNTERPART_KEY = "org.myiadidot.caseCounterpart"
SMALLCAP_HEIGHT_KEY = "org.myiadidot.smallcapHeight"
DEFAULT_SMALLCAP_HEIGHT = 1040

COUNTERPARTS = (
    ("uniA7AD", 0xA7AD, "uni023D", 1.0),  # Latin capital L with belt
    ("uni01A6", 0x01A6, "uni0280", "cap"),  # Latin letter YR
    ("uni037F", 0x037F, "J", 1.0),  # Greek capital letter Yot
    ("uniA7B3", 0xA7B3, "X", 1.0),  # Latin capital chi
)


def add_counterparts(path: Path) -> None:
    font = ufoLib2.Font.open(path)
    cap_height = font.info.capHeight or 1434
    smallcap_height = font.lib.get(SMALLCAP_HEIGHT_KEY, DEFAULT_SMALLCAP_HEIGHT)

    for name, codepoint, source_name, scale_spec in COUNTERPARTS:
        scale = cap_height / smallcap_height if scale_spec == "cap" else scale_spec
        if name in font:
            if font[name].lib.get(COUNTERPART_KEY) != source_name:
                raise SystemExit(f"{path}: {name} already exists; refusing to overwrite")
        else:
            source = font[source_name]
            glyph = font.newGlyph(name)
            glyph.unicodes = [codepoint]
            glyph.width = round(source.width * scale)
            if scale == 1.0:
                glyph.components.append(Component(source_name))
            else:
                recording = DecomposingRecordingPen(font)
                source.draw(recording)
                recording.replay(
                    TransformPen(glyph.getPen(), Transform(scale, 0, 0, scale, 0, 0))
                )
            glyph.anchors = [
                Anchor(round(anchor.x * scale), round(anchor.y * scale), anchor.name)
                for anchor in source.anchors
            ]
            glyph.lib[COUNTERPART_KEY] = source_name
            glyph.note = f"Uppercase counterpart derived from {source_name}."

        category = font.lib.setdefault("public.openTypeCategories", {})
        category[name] = "base"
        order = list(font.glyphOrder)
        if name not in order:
            order.insert(order.index(source_name) + 1, name)
            font.glyphOrder = order

    font.save()
    print(f"{path}: added four case-counterpart drafts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "ufos",
        nargs="*",
        type=Path,
        default=sorted(Path("sources").glob("MyiaDidot-*.ufo")),
    )
    args = parser.parse_args()
    for path in args.ufos:
        add_counterparts(path)


if __name__ == "__main__":
    main()
