"""Construction references for small caps with a distinctive capital profile.

The tag describes the capital used to draw the small cap. It calibrates
stroke proportion and overshoot; it does not suppress either diagnostic.
"""

KEY = "org.myiadidot.caseReference"


def case_reference(font, glyph):
    name = glyph.lib.get(KEY)
    if name is None:
        return None
    base = glyph.name.removesuffix(".sc")
    if (not glyph.name.endswith(".sc") or not isinstance(name, str)
            or name not in font or base not in font):
        raise ValueError(f"{glyph.name}: invalid capital construction reference {name!r}")
    reference = font[name]
    capital, lower = reference.unicode, font[base].unicode
    if (capital is None or lower is None or not chr(capital).isupper()
            or chr(capital).lower() != chr(lower)):
        raise ValueError(f"{glyph.name}: {name!r} is not its corresponding capital")
    return reference


def reference_top(font, glyph):
    reference = case_reference(font, glyph)
    if reference is None:
        return None
    bounds = reference.getBounds(font)
    if bounds is None or not font.info.capHeight:
        raise ValueError(f"{glyph.name}: capital reference has no usable height")
    height = font.lib.get("org.myiadidot.smallcapHeight", 1040)
    return bounds.yMax * height / font.info.capHeight
