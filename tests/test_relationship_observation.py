"""Component observations agree with explicitly drawn geometry and retain lineage."""
import sys
from pathlib import Path

import pytest
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Component

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.arches import arch_report
from relationships.discovery import analyse
from relationships.observation import observed_outline
from relationships.returns import return_report
from test_lower_returns import fixture


@pytest.mark.parametrize('matrix', [(1, 0, 0, 1, 30, 40), (-1, 0, 0, 1, 450, 0),
                                    (1, .1, .2, 1, 20, 30), (1, 0, 0, -1, 0, 600)])
def test_nested_component_matches_drawn_geometry(matrix):
    font = fixture()
    font.newGlyph('wrapper').components.append(Component('u', Transform(*matrix)))
    font.newGlyph('nested').components.append(Component('wrapper', Transform(1, 0, 0, 1, 50, 60)))
    combined = Transform(1, 0, 0, 1, 50, 60).transform(Transform(*matrix))
    font['u'].draw(TransformPen(font.newGlyph('drawn').getPen(), combined))
    before = font.json_dumps()
    report = analyse(font, paired=True)
    expanded = observed_outline(font, 'nested', report['source_identity'])
    assert expanded['contours'] == observed_outline(font, 'drawn', report['source_identity'])['contours']
    origin = expanded['origins'][0]
    assert origin['source_glyph'] == 'u'
    assert origin['component_path'] == [0, 0]
    assert origin['transform'] == list(combined)
    for reporter in (return_report, arch_report):
        a = reporter(font, report, ['nested'])['results']
        b = reporter(font, report, ['drawn'])['results']
        assert len(a) == len(b)
        for x, y in zip(a, b):
            for key in ('paths', 'role', 'anatomical_scope', 'counter_sections'):
                assert x[key] == y[key]
            assert x['contour_origin'] == origin
    assert font.json_dumps() == before


@pytest.mark.parametrize('fault', ['missing', 'cycle', 'singular', 'nan', 'open'])
def test_incomplete_field_withholds_all_observations(fault):
    font = fixture()
    glyph = font.newGlyph('broken')
    glyph.components.append(Component('u'))
    if fault == 'open':
        pen = glyph.getPen()
        pen.moveTo((0, 0)); pen.lineTo((100, 100)); pen.endPath()
    else:
        base = 'absent' if fault == 'missing' else 'broken' if fault == 'cycle' else 'u'
        matrix = (0, 0, 0, 0, 0, 0) if fault == 'singular' else (1, 0, 0, 1, float('nan'), 0) if fault == 'nan' else (1, 0, 0, 1, 0, 0)
        glyph.components.append(Component(base, Transform(*matrix)))
    observed = observed_outline(font, 'broken', 'pinned')
    assert observed['status'] == 'unresolved'
    assert observed['contours'] == observed['origins'] == []
    assert observed['issues']


def test_repeated_instances_and_mixed_contours_keep_distinct_paths():
    font = fixture()
    glyph = font.newGlyph('mixed')
    font['u'].draw(glyph.getPen())
    glyph.components.extend([Component('u'), Component('u', Transform(1, 0, 0, 1, 500, 0))])
    observed = observed_outline(font, 'mixed', 'pinned')
    assert observed['status'] == 'complete'
    assert [o['component_path'] for o in observed['origins']] == [[], [0], [1]]
    assert all(o['source_sha256'] == 'pinned' for o in observed['origins'])
