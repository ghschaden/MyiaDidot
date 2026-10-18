#!/usr/bin/env python3
"""Add the static family axes used to describe Myia Didot's styles."""

import argparse

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", help="compiled OTF or TTF to update")
    args = parser.parse_args()

    font = TTFont(args.font)
    weight = font["OS/2"].usWeightClass
    italic = font["post"].italicAngle != 0
    weight_name = "Bold" if weight >= 600 else "Regular"

    axes = [
        {
            "tag": "wght",
            "name": "Weight",
            "ordering": 0,
            "values": [
                {
                    "value": weight,
                    "name": weight_name,
                    "flags": 0x2 if weight < 600 else 0,
                }
            ],
        },
        {
            "tag": "ital",
            "name": "Italic",
            "ordering": 1,
            "values": [
                (
                    {
                        "value": 0,
                        "linkedValue": 1,
                        "name": "Roman",
                        "flags": 0x2,
                    }
                    if not italic
                    else {"value": 1, "name": "Italic"}
                )
            ],
        },
    ]
    buildStatTable(font, axes, elidedFallbackName=weight_name, macNames=False)
    font.save(args.font)


if __name__ == "__main__":
    main()
