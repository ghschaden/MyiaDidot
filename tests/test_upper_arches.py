"""Independent upper-counter topology and interior-detour controls."""
import math
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.arches import horizontal_band, shared_sections, upper_arches
from relationships.boundaries import Sections
from relationships.geometry import Outline
from shape_relationships import ROOT, run


def fixture(mode='normal', detour=False, cap=True, final_terminal=False):
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Synthetic'
    pen = font.newGlyph('arches').getPen()
    if mode == 'reverse':
        pen = ReverseContourPen(pen)
    if mode == 'shear':
        font.info.italicAngle = -math.degrees(math.atan(.25))
        pen = TransformPen(pen, (1, 0, .25, 1, 0, 0))
    # Three round open counters. Left cap is independent of the shared stems.
    pen.moveTo((0, 300))
    pen.lineTo((0, 600))
    pen.lineTo((1000, 600))
    if final_terminal:
        pen.lineTo((1000, 150))
        pen.curveTo((1000, 122), (1022, 100), (1050, 100))
        pen.curveTo((1078, 100), (1100, 122), (1100, 150))
        pen.lineTo((1100, 250))
        pen.lineTo((1140, 250))
        pen.lineTo((1140, 100))
        pen.curveTo((1140, 0), (900, 0), (900, 100))
    else:
        pen.lineTo((1000, 0))
        pen.lineTo((900, 0))
    for x in [900, 600, 300]:
        pen.lineTo((x, 450))
        curves = [((x, 450), (x, 478), (x-22, 500), (x-50, 500)),
                  ((x-150, 500), (x-178, 500), (x-200, 478), (x-200, 450))]
        pen.curveTo(*curves[0][1:])
        pen.lineTo((x-150, 500))
        pen.curveTo(*curves[1][1:])
        if x > 300:
            if detour and x == 600:
                # A lower U-turn on the middle stem; it remains connected to
                # the next arch, but takes a terminal-like detour at its foot.
                pen.lineTo((x-200, 150))
                pen.curveTo((x-200, 122), (x-178, 100), (x-150, 100))
                pen.curveTo((x-122, 100), (x-100, 122), (x-100, 150))
                pen.lineTo((x-100, 250))
                pen.lineTo((x-60, 250))
                if cap:
                    pen.lineTo((x-60, 100))
                pen.curveTo((x-60, 0), (x-300, 0), (x-300, 100))
            else:
                pen.lineTo((x-200, 0))
                pen.lineTo((x-300, 0))
        else:
            pen.lineTo((100, 300))
    pen.closePath()
    if mode == 'start':
        points = font['arches'].contours[0].points
        points[:] = points[3:]+points[:3]
    if mode == 'subdivide':
        from relationships.geometry import split
        outline = Outline()
        font['arches'].draw(outline)
        font['arches'].clearContours()
        pen = font['arches'].getPen()
        for contour in outline.contours:
            pen.moveTo(contour[0][0])
            for segment in contour:
                for part in split(segment):
                    pen.curveTo(*part[1:])
            pen.closePath()
    return font


def rows(font):
    outline = Outline()
    font['arches'].draw(outline)
    return upper_arches(outline.contours, font.info.unitsPerEm,
                        math.tan(math.radians(-(font.info.italicAngle or 0))))[0]


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'shear', 'subdivide'])
def test_upper_roles_from_shared_bands_not_graph_position(mode):
    result = rows(fixture(mode))
    assert [r['role'] for r in result] == ['entry', 'interior', 'unresolved']
    assert all(not r['conflicts'] for r in result)
    assert result[-1]['reason'].startswith('Incomplete')
    assert all(r['direction'] == 'upper-arch' for r in result)


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'shear', 'subdivide'])
def test_interior_lower_terminal_diagnosed(mode):
    result = rows(fixture(mode, detour=True))
    conflicts = [c for r in result for c in r['conflicts']]
    assert len(conflicts) == 1
    assert conflicts[0]['kind'] == 'interior-terminal-conflict'
    assert conflicts[0]['shared_sections'] >= 3
    assert conflicts[0]['following_arch'] in {r['geometry_id'] for r in result}


def test_separate_stems_do_not_share_by_width_alone():
    a = [{'p': [0, y], 'q': [100, y]} for y in range(5)]
    b = [{'p': [110, y], 'q': [210, y]} for y in range(5)]
    assert shared_sections(a, b, 1000) == 0
    assert shared_sections(a, a, 1000) == 5
    assert shared_sections(a, [None]*5, 1000) == 0


def test_horizontal_sections_do_not_cross_counter():
    outline = Outline()
    fixture()['arches'].draw(outline)
    field = Sections(outline.contours, 1000)
    result = horizontal_band(field, [(100, 400), (100, 200)], [390, 370, 350])
    assert all(s and s['width'] == pytest.approx(100) for s in result)
    assert all(s['q'][0] == 0 for s in result)


def test_component_only_is_omitted():
    assert upper_arches([], 1000)[0] == []


def test_cli_read_only_and_scoped_links(tmp_path):
    font = fixture(detour=True)
    source = tmp_path/'synthetic.ufo'
    font.save(source)
    report = run(source, ROOT/'build/test-upper-arches', arches=True,
                 proof_names=['arches'], boundary_glyphs=['arches'])
    assert report['source_preserved']
    results = report['upper_arches']['results']
    ids = {r['geometry_id'] for r in results}
    assert all(n['geometry_id'] in ids for r in results for side in r['neighbours'] for n in side)
    assert all(c['arch'] in ids and c['following_arch'] in ids for r in results for c in r['conflicts'])
    assert 'interior-terminal-conflict' in (ROOT/'build/test-upper-arches/arches.svg').read_text()


def test_unverified_cap_retains_detour_diagnosis_only():
    result = rows(fixture(detour=True, cap=False))
    conflicts = [c for r in result for c in r['conflicts']]
    assert len(conflicts) == 1
    assert conflicts[0]['kind'] == 'interior-return-detour'
    assert not any(t['cap_verified'] for r in result for t in r.get('lower_terminals', []))


def test_final_terminal_is_exit_without_interior_conflict():
    result = rows(fixture(final_terminal=True))
    assert [r['role'] for r in result] == ['entry', 'interior', 'exit']
    assert not any(r['conflicts'] for r in result)


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'shear', 'subdivide'])
@pytest.mark.parametrize('kind', ['normal', 'detour', 'uncapped', 'exit'])
def test_terminal_experiment_preserves_roles_caps_scope_and_conflicts(mode, kind):
    import copy

    from relationships.returns import lower_returns
    font = fixture(mode, detour=kind in ('detour', 'uncapped'),
                   cap=kind != 'uncapped', final_terminal=kind == 'exit')
    outline = Outline()
    font['arches'].draw(outline)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    for observe in [lambda policy: upper_arches(outline.contours, 1000, slant, terminal_policy=policy),
                    lambda policy: lower_returns(outline.contours, [], 1000, slant, terminal_policy=policy)]:
        base = observe('baseline')
        wide = copy.deepcopy(observe('wide-morphology'))
        assert [r['geometry_id'] for r in base[0]] == [r['geometry_id'] for r in wide[0]]
        # Every field outside reciprocal-terminal morphology must remain equal.
        for old, new in zip(base[0], wide[0]):
            if 'arm_context' in old:
                for a, b in zip(old['arm_context'], new['arm_context']):
                    assert b['terminal_context'].pop('baseline_status') == a['terminal_context']['status']
                    b['terminal_context'] = a['terminal_context']
            else:
                for a, b in zip(old['terminal_context'], new['terminal_context']):
                    assert b['baseline_status'] == a['status']
                new['terminal_context'] = old['terminal_context']
        assert base == wide
