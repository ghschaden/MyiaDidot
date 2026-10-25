"""Install the approved lighter Italic I in final spacing."""
from pathlib import Path

from fontTools.ufoLib.glifLib import readGlyphFromString
from ufoLib2.objects import Glyph

DATA = Path(__file__).parent / "data" / "italic-i" / "I.glif"


def install(font):
    """Load the reviewed outline in final spacing.

    Preserve the generated glyph's advance, anchors and metadata. Loading a
    fixed design avoids progressively thinning the output on regeneration.
    """
    design = Glyph()
    readGlyphFromString(DATA.read_text(), glyphObject=design, pointPen=design.getPointPen())
    glyph = font["I"]
    glyph.clearContours()
    glyph.clearComponents()
    design.draw(glyph.getPen())
