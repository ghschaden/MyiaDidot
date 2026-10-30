"""Positive geometry and policy refusal controls for local return retrieval."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.return_matching import compare_returns, match_returns
from test_lower_returns import capped_fixture, result


def rows():
    a = result(capped_fixture())['results'][0]
    font = capped_fixture()
    for contour in font['u'].contours:
        for p in contour.points:
            p.x += 170
    b = result(font)['results'][0]
    b['glyph'] = 'peer'
    return a, b


def compare(a, b):
    return compare_returns(a, b, 1000, 1000, 'Test', 'Test')


def test_translated_same_role_has_compatible_profiles():
    a, b = rows()
    c = compare(a, b)
    assert c['decision'] == 'candidate'
    assert c['metrics']['counter_rms_em'] == pytest.approx(0)
    assert c['metrics']['cap_rms_em'] == pytest.approx(0, abs=1e-10)
    assert compare(b, a)['decision'] == 'candidate'
    assert match_returns([a, b], 1000, 'Test')['comparisons'][0]['decision'] == 'candidate'


@pytest.mark.parametrize('change', ['counter', 'width', 'direction', 'cap'])
def test_close_role_peers_reject_incompatible_local_evidence(change):
    a, b = rows()
    # Controlled independent perturbations of measured evidence isolate each gate.
    if change == 'counter':
        for s in b['counter_sections']:
            s['clearance_units'] += 30
    elif change == 'width':
        for s in b['arm_context'][0]['sections']:
            s['width'] *= 1.3
    elif change == 'direction':
        b['attachment_directions'][0] = [100, 100]
    else:
        for p in b['arm_context'][1]['cap_trace'][1:]:
            p[0] += 40
    c = compare(a, b)
    assert c['decision'] == 'incompatible'
    assert c['reasons']


def test_entry_exit_cannot_be_placed_in_interior_role():
    a, b = rows()
    b['role'] = 'interior'
    assert compare(a, b)['decision'] == 'incompatible'


@pytest.mark.parametrize('missing', ['role', 'band', 'tail', 'cap'])
def test_missing_context_never_becomes_positive(missing):
    a, b = rows()
    if missing == 'role':
        b['role'] = 'unresolved'
    elif missing == 'band':
        b['arm_context'][0]['status'] = 'unresolved'
    elif missing == 'tail':
        b['arm_context'][1]['below_floor_context'] = 'present'
    else:
        b['arm_context'][1]['cap_status'] = 'unresolved'
    assert compare(a, b)['decision'] == 'unresolved'


def test_cross_style_reference_is_not_reuse():
    a, b = rows()
    assert compare_returns(a, b, 1000, 1000, 'Regular', 'Italic')['decision'] == 'unresolved'


def test_em_normalization_preserves_same_geometry():
    a, b = rows()
    b = copy.deepcopy(b)
    for s in b['counter_sections']:
        s['clearance_units'] *= 2
    for c in b['arm_context']:
        for s in c['sections']:
            s['width'] *= 2
        c['cap_trace'] = [[2*x, 2*y] for x, y in c['cap_trace']]
    assert compare_returns(a, b, 1000, 2000, 'Test', 'Test')['decision'] == 'candidate'


def test_heldout_rounded_cap_family():
    import ufoLib2

    def rounded(dx):
        font = ufoLib2.Font()
        font.info.unitsPerEm = 1000
        font.info.styleName = 'Rounded'
        from fontTools.pens.transformPen import TransformPen
        pen = TransformPen(font.newGlyph('u').getPen(), (1, 0, 0, 1, dx, 0))
        pen.moveTo((0, 600))
        for p in [(0, 0), (400, 0), (400, 250)]:
            pen.lineTo(p)
        pen.curveTo((400, 316), (300, 316), (300, 250))
        pen.lineTo((300, 150))
        pen.curveTo((300, 122), (278, 100), (250, 100))
        pen.lineTo((150, 100))
        pen.curveTo((122, 100), (100, 122), (100, 150))
        pen.lineTo((100, 600))
        pen.closePath()
        return result(font)['results'][0]

    a, b = rounded(0), rounded(180)
    b['glyph'] = 'round-peer'
    assert a['role'] == b['role'] == 'exit'
    assert compare(a, b)['decision'] == 'candidate'
    b['role'] = 'interior'
    assert compare(a, b)['decision'] == 'incompatible'
