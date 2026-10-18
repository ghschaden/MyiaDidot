"""The styles agree with the Regular where they must.

Each generated style has the Regular's glyphs, code points, categories,
kerning-group membership, and at least the Regular's anchors on each glyph
(an anchor missing leaves a mark unattached in that style only). What a
style differs in on purpose is on its list, data/styles-agree-Italic.txt
..., one "kind glyph [detail]" per line with a reason; a new difference
fails, and so does a listed one that is gone, so the lists only shrink.
After an intended change: scripts/update_test_data.py --styles --ufo UFO.
"""

import pytest
from conftest import SOURCES, style_data
from test_composites import read_list

REGULAR = SOURCES / "MyiaDidot-Regular.ufo"


def differences(regular, ufo):
    """{"kind glyph [detail]": what} where ufo differs from the Regular."""
    out = {}
    for name in regular.keys():  # noqa: SIM118 (a Font iterates glyphs)
        if name not in ufo:
            out[f"missing {name}"] = "not in this style"
            continue
        r, g = regular[name], ufo[name]
        if r.unicodes != g.unicodes:
            out[f"unicodes {name}"] = f"{r.unicodes} here {g.unicodes}"
        lost = sorted({a.name for a in r.anchors} - {a.name for a in g.anchors})
        if lost:
            out[f"anchors {name} {','.join(lost)}"] = "the Regular's anchors missing here"
    for name in ufo.keys():  # noqa: SIM118
        if name not in regular:
            out[f"extra {name}"] = "not in the Regular"
    rc = regular.lib.get("public.openTypeCategories", {})
    gc = ufo.lib.get("public.openTypeCategories", {})
    for name in sorted(set(rc) | set(gc)):
        if name in regular and name in ufo and rc.get(name) != gc.get(name):
            out[f"category {name}"] = f"{rc.get(name)} here {gc.get(name)}"

    def membership(font):
        return {(side, n): grp for grp, names in font.groups.items()
                for side in ("kern1", "kern2") if grp.startswith(f"public.{side}.") for n in names}

    rm, gm = membership(regular), membership(ufo)
    for side, name in sorted(set(rm) | set(gm)):
        if name in regular and name in ufo and rm.get((side, name)) != gm.get((side, name)):
            out[f"group {name} {side}"] = f"{rm.get((side, name))} here {gm.get((side, name))}"
    return out


def test_styles_agree_with_the_regular(ufo, ufo_path):
    if ufo_path.resolve() == REGULAR.resolve():
        pytest.skip("the Regular itself")
    import ufoLib2

    listed = read_list(style_data("styles-agree.txt", ufo_path).name)
    found = differences(ufoLib2.Font.open(REGULAR), ufo)
    new = {k: v for k, v in found.items() if k not in listed}
    stale = sorted(set(listed) - set(found))
    assert not new, ("differs from the Regular (fix the generator, or if intended: "
                     f"update_test_data.py --styles --ufo UFO --reason ...): {dict(list(new.items())[:30])}")
    assert not stale, f"no longer differs from the Regular, remove from the list: {stale}"
