"""Independent geometry and provenance checks for relationship discovery."""

import copy
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.misc.transform import Transform
from ufoLib2.objects import Anchor, Component

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import shape_relationships as rel


def contour():
    # Quarter-like curve meeting a vertical line, with sharp closure corners.
    return [((0, 0), (60, 0), (100, 40), (100, 100)),
            ((100, 100), (100, 300)), ((100, 300), (-100, 300)),
            ((-100, 300), (-100, 0)), ((-100, 0), (0, 0))]


def features(c, em=1000, slant=0):
    rows, issues = rel.transitions([c], em, slant)
    assert not issues
    return sorted(rows, key=lambda r: tuple(r['junction']))


def compare(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x['family'] == y['family']
        assert rel.compare_relationships(x, y)['compatible']
        assert x['junction'] == pytest.approx(y['junction'])
        assert x['line_length_em'] == pytest.approx(y['line_length_em'])
        assert x['metrics']['lateral_reversal_em'] == pytest.approx(y['metrics']['lateral_reversal_em'], abs=0.0001)


def test_subdivision_line_splitting_and_cyclic_start_do_not_change_relationships():
    c = contour()
    original = features(c)
    assert len(original) == 2
    curve = rel.split(c[0])
    revised = list(curve)+[((100, 100), (100, 190)), ((100, 190), (100, 300))]+c[2:]
    compare(original, features(revised))
    for i in range(len(revised)):
        compare(original, features(revised[i:]+revised[:i]))


def test_reversing_contour_preserves_relationships():
    compare(features(contour()), features([tuple(reversed(s)) for s in reversed(contour())]))


def test_collinear_cubic_is_a_line_but_backtracking_is_not():
    assert rel.is_line(((0, 0), (0, 30), (0, 70), (0, 100)))
    assert not rel.is_line(((0, 0), (0, 130), (0, -30), (0, 100)))
    c = contour()
    compare(features(c), features([c[0], ((100, 100), (100, 140), (100, 250), (100, 300))]+c[2:]))


def test_deskew_and_scale_invariance():
    c = contour()
    sheared = [tuple((x+.25*y, y) for x, y in s) for s in c]
    compare(features(c), features(sheared, slant=.25))
    scaled = [tuple((x*2, y*2) for x, y in s) for s in c]
    a, b = features(c), features(scaled, em=2000)
    for x, y in zip(a, b):
        assert x['family'] == y['family']
        assert x['line_length_em'] == pytest.approx(y['line_length_em'])
        assert x['metrics']['lateral_reversal_em'] == pytest.approx(y['metrics']['lateral_reversal_em'])


def test_short_lines_and_degenerate_contours_are_not_silent_candidates():
    assert features([((0, 0), (20, 0), (30, 10), (30, 30)), ((30, 30), (30, 35)), ((30, 35), (0, 0))]) == []
    rows, issues = rel.transitions([contour()+[((0, 0), (0, 0))]], 1000)
    compare(features(contour()), sorted(rows, key=lambda r: tuple(r['junction'])))
    assert issues[0]['reason'].startswith('zero-length')


def attachment_font():
    f = ufoLib2.Font()
    f.info.unitsPerEm = 1000
    b = f.newGlyph('a'); b.unicodes = [0x61]
    b.anchors = [Anchor(name='Top', x=100, y=500)]
    mark = f.newGlyph('accentPiece')
    wrapper = f.newGlyph('acutecomb'); wrapper.unicodes = [0x301]
    wrapper.components = [Component(mark.name, Transform(1, 0, 0, 1, -200, 0))]
    wrapper.anchors = [Anchor(name='_Top', x=-150, y=500)]
    g = f.newGlyph('aacute'); g.unicodes = [0xE1]
    g.components = [Component('a'), Component('accentPiece', Transform(1, 0, 0, 1, 50, 0))]
    return f


def test_wrapper_anchor_is_mapped_back_into_actual_component_frame():
    f = attachment_font()
    r, = rel.attachments(f)
    assert r['status'] == 'confirmed' and r['family'] == 'base-mark/Top'
    assert r['anchor_evidence'][0]['distance_em'] == 0
    assert r['anchor_evidence'][0]['mark_position'] == [100, 500]


def test_offset_and_ambiguous_anchors_are_unresolved():
    f = attachment_font()
    f['aacute'].components[1].transformation = Transform(1, 0, 0, 1, 65, 0)
    assert rel.attachments(f)[0]['status'] == 'unresolved'
    f = attachment_font()
    f['a'].anchors.append(Anchor(name='Top', x=100, y=500))
    assert 'Multiple' in rel.attachments(f)[0]['reason']


def test_unicode_name_alone_does_not_establish_attachment():
    f = attachment_font()
    f['aacute'].components.clear()
    assert rel.attachments(f)[0]['status'] == 'unresolved'
    f['aacute'].unicodes.clear()
    assert rel.attachments(f) == []


def test_nonidentity_component_transforms():
    f = attachment_font()
    f['aacute'].components[0].transformation = Transform(2, 0, 0, 2, 10, 10)
    f['aacute'].components[1].transformation = Transform(2, 0, 0, 2, 110, 10)
    assert rel.attachments(f)[0]['status'] == 'confirmed'


def test_cycles_in_wrappers_are_unresolved():
    f = attachment_font()
    f['acutecomb'].components[0].baseGlyph = 'acutecomb'
    result, reason = rel.anchor_candidates(f, 'acutecomb', 'accentPiece')
    assert not result and reason == 'component cycle'


def test_analysis_preserves_sources_and_query_explains_ancestry():
    f = attachment_font()
    before = copy.deepcopy(f.json_dumps())
    report = rel.analyse(f)
    assert f.json_dumps() == before
    assert rel.related(report, 'a')['component_dependants'] == ['aacute']
    assert rel.related(report, 'aacute')['component_ancestors'] == ['a', 'accentPiece']
    with pytest.raises(ValueError, match='Unknown'):
        rel.related(report, 'missing')


def test_output_is_restricted_to_build(tmp_path):
    with pytest.raises(ValueError, match='below'):
        rel.safe_output(tmp_path)
    assert rel.safe_output(rel.ROOT/'build/relationships-test').name == 'relationships-test'


def test_real_known_attachment_and_no_alias_as_attachment():
    f = ufoLib2.Font.open(rel.ROOT/'sources/MyiaDidot-BoldItalic.ufo')
    records = rel.attachments(f)
    assert any(r['glyph'] == 'yacute' and r['status'] == 'confirmed' for r in records)
    assert not any(r['glyph'] == 'acutecomb' for r in records)


def test_related_filters_same_family_with_wrong_local_shape():
    a = features(contour())[1]
    b = copy.deepcopy(a)
    assert rel.compare_relationships(a, b)['compatible']
    b['metrics']['profile'] = [[x, y+.05] for x, y in b['metrics']['profile']]
    assert not rel.compare_relationships(a, b)['compatible']
    b = copy.deepcopy(a)
    b['line_length_em'] *= 3
    assert not rel.compare_relationships(a, b)['compatible']
    b = copy.deepcopy(a)
    b['status'] = 'boundary-uncertain'
    assert not rel.compare_relationships(a, b)['compatible']


def test_lateral_metric_has_independent_known_reversal():
    # Walk away from a vertical junction: x goes 0 -> 10 -> 0.
    # Half of total lateral travel minus net travel is 10 units.
    points = [(0, 60), (10, 30), (0, 0)]
    m = rel.transition_metrics(points, (0, -1), 1000)
    assert m['lateral_reversal_em'] == pytest.approx(.01, abs=.0004)
    plain = rel.transition_metrics([(0, 60), (0, 0)], (0, -1), 1000)
    assert plain['lateral_reversal_em'] == 0


def test_end_to_end_artifacts_and_source_hash(tmp_path):
    import tempfile

    build = rel.ROOT/'build'
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build, prefix='relationships-test-') as directory:
        root = Path(directory)
        source = root/'source.ufo'
        f = attachment_font()
        f.save(source)
        before = rel.content_hash(source)
        report = rel.run(source, root/'report', 'a', ['aacute'])
        assert report['source_preserved'] and rel.content_hash(source) == before
        assert (root/'report/index.html').is_file()
        assert (root/'report/proof.svg').read_text().endswith('</g></svg>')
        assert report['query']['component_dependants'] == ['aacute']
        with pytest.raises(ValueError, match='disjoint'):
            rel.run(source, source/'nested')
