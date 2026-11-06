"""The Italic ƥ curl meets its stem without a sudden widening."""

import ufoLib2
from conftest import SOURCES
from derive import stems_at
from italic_geometry import upright


def test_italic_p_hook_has_continuous_join_and_keeps_its_curl():
    font = upright(ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo"))
    below = stems_at(font, "uni01A5", 1100)[0]
    join = stems_at(font, "uni01A5", 1150)[0]
    assert abs((join[1] - join[0]) - (below[1] - below[0])) < 2
    assert len(stems_at(font, "uni01A5", 1200)) == 2
