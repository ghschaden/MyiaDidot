"""Lower-return controls independent of the real font pilot."""
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.discovery import analyse
from relationships.returns import return_report
from shape_relationships import ROOT, run


def fixture(mode='normal'):
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Test'
    glyph = font.newGlyph('u')
    pen = glyph.getPen()
    if mode == 'reverse':
        pen = ReverseContourPen(pen)
    if mode == 'upper':
        pen = TransformPen(pen, (1, 0, 0, -1, 0, 600))
    if mode == 'shear':
        font.info.italicAngle = -14.036243467926479
        pen = TransformPen(pen, (1, 0, .25, 1, 0, 0))
    pen.moveTo((0, 600))
    pen.lineTo((0, 100))
    pen.curveTo((0, 45), (45, 0), (100, 0))
    pen.lineTo((300, 0))
    pen.curveTo((355, 0), (400, 45), (400, 100))
    pen.lineTo((400, 600))
    pen.lineTo((300, 600))
    pen.lineTo((300, 200))
    if mode == 'angular':
        pen.lineTo((200, 100))
        pen.lineTo((100, 200))
    else:
        curves = [((300, 200), (300, 145), (255, 100), (200, 100)),
                  ((200, 100), (145, 100), (100, 145), (100, 200))]
        if mode == 'subdivide':
            from relationships.geometry import split
            curves = [part for curve in curves for part in split(curve)]
        for curve in curves:
            pen.curveTo(*curve[1:])
    pen.lineTo((100, 600))
    pen.closePath()
    if mode == 'start':
        contour = glyph.contours[0]
        contour.points[:] = contour.points[4:]+contour.points[:4]
    return font


def result(font):
    report = analyse(font, paired=True)
    return return_report(font, report, ['u'])


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'shear', 'subdivide'])
def test_round_counter_and_neighbours(mode):
    rows = result(fixture(mode))['results']
    assert len(rows) == 1
    row = rows[0]
    assert row['bottom'] == pytest.approx((200, 100))
    assert row['status'] == 'supported-local-turn'
    assert row['role'] == 'unresolved'  # No terminal/tail context, even at graph end.
    assert len(row['counter_sections']) == 8
    assert row['opening_units'] > 190
    assert row['direction'] == 'lower-return'


@pytest.mark.parametrize('mode', ['upper', 'angular'])
def test_upper_arch_and_sharp_v_are_not_lower_returns(mode):
    assert not result(fixture(mode))['results']


def test_missing_stems_do_not_manufacture_roles():
    font = fixture()
    report = analyse(font)
    row = return_report(font, report, ['u'])['results'][0]
    assert row['status'] == row['role'] == 'unresolved'
    assert row['neighbours'] == [[], []]


def test_cli_read_only_artifact(tmp_path):
    source = tmp_path/'Test.ufo'
    fixture().save(source)
    out = ROOT/'build/test-lower-returns'
    report = run(source, out, proof_names=['u'], returns=True, boundary_glyphs=['u'])
    assert report['source_preserved']
    assert report['lower_returns']['results']
    assert '#b52a90' in (out/'returns.svg').read_text()


def test_interior_requires_shared_observed_neighbour():
    from relationships.geometry import Outline
    from relationships.returns import lower_returns
    outline = Outline()
    fixture()['u'].draw(outline)
    contours = outline.contours + [[tuple((x+300, y) for x, y in s) for s in c] for c in outline.contours]
    pairs = [{'geometry_id': f'stem-{x}', 'length_em': .5,
              'centerline': [(x+50, 100), (x+50, 600)],
              'edges': [[(edge, y) for y in range(100, 601, 20)] for edge in [x, x+100]]}
             for x in [0, 300, 600]]
    rows, _ = lower_returns(contours, pairs, 1000)
    assert len(rows) == 2
    assert rows[0]['role'] == 'interior'
    assert rows[0]['next_turn'] == rows[1]['geometry_id']
    assert rows[1]['role'] == 'unresolved'
    # A competing stroke prevents confident graph linkage.
    rows, _ = lower_returns(contours, pairs+[dict(pairs[1], geometry_id='competitor')], 1000)
    assert all(r['status'] == r['role'] == 'unresolved' for r in rows)


def test_interrupted_counter_is_not_clear():
    font = fixture()
    pen = font['u'].getPen()
    pen.moveTo((50, 140))
    for point in [(350, 140), (350, 160), (50, 160)]:
        pen.lineTo(point)
    pen.closePath()
    report = result(font)
    assert not report['results']
    assert any('interrupted' in note['reason'] for note in report['omissions'])


def test_component_only_geometry_has_explicit_origin():
    font = fixture()
    font.newGlyph('derived').getPen().addComponent('u', (1, 0, 0, 1, 0, 0))
    report = return_report(font, analyse(font, paired=True), ['derived'])
    assert report['results']
    assert all(r['contour_origin']['source_glyph'] == 'u' for r in report['results'])


def capped_fixture(tail=False, tall=False, reverse=False):
    """Short rounded floor with straight arms and independently known cap."""
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Context'
    glyph = font.newGlyph('u')
    pen = glyph.getPen()
    if reverse:
        pen = ReverseContourPen(pen)
    pen.moveTo((0, 600))
    pen.lineTo((0, 0))
    pen.lineTo((400, 0))
    pen.lineTo((400, 600 if tall else 300))
    pen.lineTo((300, 600 if tall else 300))
    pen.lineTo((300, 150))
    pen.curveTo((300, 122), (278, 100), (250, 100))
    pen.lineTo((150, 100))
    pen.curveTo((122, 100), (100, 122), (100, 150))
    pen.lineTo((100, 600))
    pen.closePath()
    if tail:
        # A separate descender is enough to withhold an exit: no attachment
        # inference is made from the glyph-wide context screen.
        pen.moveTo((500, -100))
        for p in [(550, -100), (550, 0), (500, 0)]:
            pen.lineTo(p)
        pen.closePath()
    return font


@pytest.mark.parametrize('reverse', [False, True])
def test_local_band_and_contour_cap_establish_exit_without_global_pairs(reverse):
    font = capped_fixture(reverse=reverse)
    report = return_report(font, analyse(font), ['u'])
    row = report['results'][0]
    assert row['neighbours'] == [[], []]
    assert row['status'] == 'supported-local-turn'
    assert row['role'] == 'exit'
    assert all(a['status'] == 'supported-local-band' for a in row['arm_context'])
    assert row['arm_context'][1]['cap_status'] == 'short-contour-cap'
    assert row['arm_context'][1]['cap_return_distance_units'] <= 3


@pytest.mark.parametrize('kind', ['tail', 'tall'])
def test_descender_context_and_uncapped_stem_withhold_exit(kind):
    row = result(capped_fixture(**{kind: True}))['results'][0]
    assert row['role'] == 'unresolved'
    right = row['arm_context'][1]
    if kind == 'tail':
        assert right['below_floor_context'] == 'present'
        assert right['cap_status'] == 'short-contour-cap'
    else:
        assert right['cap_status'] == 'continues-above-window'


def test_nearby_band_is_not_shared_without_both_boundaries():
    import copy

    from relationships.return_context import same_band
    row = result(capped_fixture())['results'][0]
    band = row['arm_context'][0]
    assert same_band(band, band, 1000)
    wrong = copy.deepcopy(band)
    for section in wrong['sections']:
        section['q'][0] += 20
    assert not same_band(band, wrong, 1000)


def test_two_returns_share_local_middle_band_without_global_pairs():
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Twin'
    pen = font.newGlyph('u').getPen()
    pen.moveTo((0, 600))
    for p in [(0, 0), (700, 0), (700, 300), (600, 300), (600, 150)]:
        pen.lineTo(p)
    pen.curveTo((600, 122), (578, 100), (550, 100))
    pen.lineTo((450, 100))
    pen.curveTo((422, 100), (400, 122), (400, 150))
    for p in [(400, 600), (300, 600), (300, 150)]:
        pen.lineTo(p)
    pen.curveTo((300, 122), (278, 100), (250, 100))
    pen.lineTo((150, 100))
    pen.curveTo((122, 100), (100, 122), (100, 150))
    pen.lineTo((100, 600))
    pen.closePath()
    rows = return_report(font, analyse(font), ['u'])['results']
    assert [r['role'] for r in rows] == ['interior', 'exit']
    assert rows[0]['next_turn'] == rows[1]['geometry_id']
    assert all(r['neighbours'] == [[], []] for r in rows)
