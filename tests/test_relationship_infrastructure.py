"""Stage-0 identities, evidence verification and family-separated evaluation."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.discovery import analyse
from relationships.evaluation import evaluate, fixture_font
from relationships.identity import identify
from relationships.matching import related
from relationships.provenance import fragment_evidence, verified_declarations
from shape_relationships import ROOT

CORPUS = ROOT/'scripts/data/relationship-evaluation.json'


@pytest.fixture
def corpus():
    return json.loads(CORPUS.read_text())


def curve_record(report, name='dcurve'):
    return next(r for r in report['relationships'] if r['glyph'] == name and r.get('junction') == [100, 100])


def declaration(font, report):
    return {'format': 'myiadidot-provenance-v1',
            'source': {'sha256': report['source_identity'], 'style': font.info.styleName},
            'declarations': [{'id': 'base-copy', 'target': 'dattached', 'base': 'dbase',
                              'operation': 'component', 'part': {'component_index': 0},
                              'evidence_origin': 'independent synthetic recipe',
                              'transform': [1, 0, 0, 1, 0, 0], 'protected_landmarks': []}]}


def test_id_is_source_pinned_but_locator_survives_subdivision(corpus):
    from relationships.geometry import split

    a = analyse(fixture_font(corpus), 'first')
    altered = copy.deepcopy(corpus)
    c = altered['glyphs']['dcurve']['contours'][0]
    c[:1] = split(c[0])
    b = analyse(fixture_font(altered), 'second')
    x, y = curve_record(a), curve_record(b)
    assert x['geometry_id'] == y['geometry_id']
    assert x['id'] != y['id']
    assert x['segments'] != y['segments']


def test_report_order_does_not_define_identity(corpus):
    report = analyse(fixture_font(corpus), 'same-source')
    rows = copy.deepcopy(list(reversed(report['relationships'])))
    identify(rows, 'same-source')
    assert {r['id'] for r in rows} == {r['id'] for r in report['relationships']}


def test_coincident_locators_are_not_silently_unique(corpus):
    from relationships.matching import compare_relationships

    r = curve_record(analyse(fixture_font(corpus)))
    rows = [copy.deepcopy(r), copy.deepcopy(r)]
    identify(rows, 'source')
    assert len({r['id'] for r in rows}) == 2
    assert compare_relationships(*rows)['decision'] == 'uncertain'


def test_local_query_and_limit(corpus):
    report = analyse(fixture_font(corpus))
    span = curve_record(report)
    query = related(report, 'dcurve', span=span['geometry_id'], limit=1)
    assert {m['target'] for m in query['matches']} == {span['id']}
    assert len(query['ranked_families']) == 1
    with pytest.raises(ValueError, match='another glyph'):
        related(report, 'hcurve', span=span['id'])
    with pytest.raises(ValueError, match='positive'):
        related(report, 'dcurve', limit=0)


def test_grouping_uses_ancestry_and_does_not_collapse_lookalikes(corpus):
    from relationships.matching import derivative_roots

    report = analyse(fixture_font(corpus))
    roots = derivative_roots(report)
    assert roots['dattached'] == 'dbase'
    assert roots['dcopy'] == 'dcopy'
    assert roots['dmisplaced'] == 'dmisplaced'


def test_verified_component_and_false_claim(corpus):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report)
    before = font.json_dumps()
    assert verified_declarations(manifest, font, report, report['source_identity'])[0]['status'] == 'verified'
    manifest['declarations'][0]['transform'][4] = 10
    result = verified_declarations(manifest, font, report, report['source_identity'])[0]
    assert result['status'] == 'rejected'
    assert font.json_dumps() == before


def test_stale_declarations_fail_closed(corpus):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report)
    manifest['source']['sha256'] = 'stale'
    with pytest.raises(ValueError, match='Stale'):
        verified_declarations(manifest, font, report, report['source_identity'])


@pytest.mark.parametrize('change', ['duplicate', 'singular', 'nonfinite', 'origin', 'part'])
def test_malformed_declarations_rejected(corpus, change):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report); d = manifest['declarations'][0]
    if change == 'duplicate':
        manifest['declarations'].append(copy.deepcopy(d))
    elif change == 'singular':
        d['transform'] = [0]*6
    elif change == 'nonfinite':
        d['transform'][0] = float('nan')
    elif change == 'origin':
        d['evidence_origin'] = ''
    else:
        d['part'] = []
    with pytest.raises(ValueError):
        verified_declarations(manifest, font, report, report['source_identity'])


def test_protected_landmark_checks_real_anchors(corpus):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report)
    manifest['declarations'][0]['protected_landmarks'] = [{'base_anchor': 'Top', 'target_anchor': 'missing'}]
    assert verified_declarations(manifest, font, report, report['source_identity'])[0]['status'] == 'rejected'


def test_declared_affine_span_copy_is_checked(corpus):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report)
    d = manifest['declarations'][0]
    d.update(base='dcurve', target='dcopy', operation='span-copy',
             part={'base_geometry_id': curve_record(report)['geometry_id'],
                   'target_geometry_id': curve_record(report, 'dcopy')['geometry_id']})
    assert verified_declarations(manifest, font, report, report['source_identity'])[0]['status'] == 'verified'
    d['transform'][4] = 20
    assert verified_declarations(manifest, font, report, report['source_identity'])[0]['status'] == 'rejected'


def test_labelled_evaluation_and_family_leakage(corpus):
    result = evaluate(corpus)
    assert result['all_passed'], result['cases']
    assert result['splits']['heldout']['cases'] == 8
    corpus['cases'][0]['split'] = 'heldout'
    with pytest.raises(ValueError, match='leakage'):
        evaluate(corpus)


def test_bad_label_is_reported_not_accepted(corpus):
    corpus['cases'][0]['expected'] = 'absent'
    result = evaluate(corpus)
    assert not result['all_passed']
    assert result['splits']['development']['unexpected_positive'] == 1


def test_evaluation_source_must_be_pinned(corpus):
    with pytest.raises(ValueError, match='Stale'):
        evaluate(corpus, fixture_font(corpus), 'external-source')


def test_fragment_library_verified_against_observed_font(corpus):
    import shape_grammar_full as engine

    corpus = copy.deepcopy(corpus)
    corpus['glyphs'] = {n: g for n, g in corpus['glyphs'].items() if not n.startswith('h')}
    font = fixture_font(corpus)
    for i in range(4):
        font['dcurve'].draw(font.newGlyph(f'fragment_copy{i}').getPen())
    snapshot = json.loads(font.json_dumps())
    template = copy.deepcopy(snapshot)
    rules, atoms, recipes = {}, {}, {}
    def intern(atom):
        if atom not in atoms:
            key = f'p{len(atoms)}'; atoms[atom] = key
            rules[key] = {'primitive': atom[0], 'parameters': list(atom[1:])}
        return atoms[atom]
    for glyph in font:
        metadata = copy.deepcopy(snapshot['layers'][0]['glyphs'][glyph.name])
        metadata.pop('contours', None)
        components = metadata.pop('components', [])
        recipes[glyph.name] = {'contours': [engine.encode_contour(c, intern) for c in glyph.contours],
                               'metadata': metadata, 'components': components}
    engine.factor([c['rules'] for r in recipes.values() for c in r['contours']], rules, 2)
    template['layers'][0]['glyphs'] = {}
    grammar = {'format': engine.FORMAT, 'rules': rules,
               'styles': {'Evaluation': {'source_sha256': engine.digest(snapshot), 'font_metadata': template,
                                        'layers': [{'name': font.layers.defaultLayer.name, 'glyphs': recipes}]}}}
    evidence = fragment_evidence(grammar, font, 'Evaluation')
    assert evidence['status'] == 'verified-exact-reconstruction'
    assert evidence['shared_fragments']
    grammar['styles']['Evaluation']['source_sha256'] = 'stale'
    with pytest.raises(ValueError, match='Stale'):
        fragment_evidence(grammar, font, 'Evaluation')


@pytest.mark.parametrize('change', ['record', 'source', 'missing_part'])
def test_provenance_schema_failures_are_explicit(corpus, change):
    font = fixture_font(corpus); report = analyse(font)
    manifest = declaration(font, report)
    if change == 'record':
        manifest['declarations'][0] = []
    elif change == 'source':
        manifest['source'] = []
    else:
        manifest['declarations'][0]['part'] = {}
    with pytest.raises(ValueError):
        verified_declarations(manifest, font, report, report['source_identity'])
