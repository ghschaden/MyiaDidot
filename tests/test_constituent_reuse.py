"""Independent positive, negative and unresolved constituent controls."""

import copy
import math
import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.discovery import analyse
from relationships.provenance import verified_declarations
from relationships.reuse import constituent_reuse
from shape_relationships import ROOT, run


def fixture(taper=0):
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Test'
    for name, offsets in [('base', [0]), ('target', [0, 180])]:
        pen = font.newGlyph(name).getPen()
        for x in offsets:
            pen.moveTo((x, 0))
            for p in [(x+100, 0), (x+100+taper, 600), (x, 600)]:
                pen.lineTo(p)
            pen.closePath()
    report = analyse(font, paired=True)
    spans = {name: sorted([r for r in report['relationships'] if r['glyph'] == name], key=lambda r: r['centerline'][0][0]) for name in font.keys()}
    declarations = []
    for i in range(2):
        declarations.append({'id': str(i), 'target': 'target', 'base': 'base', 'operation': 'stroke-copy',
                             'constituent': f'part-{i}', 'evidence_origin': 'independent synthetic construction',
                             'transform': [1, 0, 0, 1, 180*i, 0], 'protected_landmarks': [],
                             'part': {'base_geometry_id': spans['base'][0]['geometry_id'],
                                      'target_geometry_id': spans['target'][i]['geometry_id']}})
    manifest = {'format': 'myiadidot-provenance-v1',
                'source': {'sha256': report['source_identity'], 'style': 'Test'}, 'declarations': declarations}
    return font, report, manifest


def evaluate(font, report, manifest):
    report['declarations'] = verified_declarations(manifest, font, report, report['source_identity'])
    return [r for r in constituent_reuse(report, 1000)['results'] if r['glyph'] == 'target']


def test_adjacent_constituents_are_separate_not_shared():
    font, report, manifest = fixture()
    rows = evaluate(font, report, manifest)
    assert [r['status'] for r in rows] == ['repeated-but-separate']
    assert rows[0]['metrics']['sampled_boundary_clearance_units'] == pytest.approx(80)


def test_two_constituents_share_observed_region():
    font, report, manifest = fixture()
    a, b = manifest['declarations']
    b['part'] = copy.deepcopy(a['part'])
    b['transform'] = list(a['transform'])
    assert evaluate(font, report, manifest)[0]['status'] == 'shared'
    # Duplicate labels for one constituent are not independent shared-stem evidence.
    b['constituent'] = a['constituent']
    assert all(r['status'] != 'shared' for r in evaluate(font, report, manifest))


@pytest.mark.parametrize('transform', [[1, 0, 0, 1, 195, 0], [1.2, 0, 0, 1, 180, 0], [1, 0, 0, 1, 180, 20]])
def test_displaced_wrong_weight_or_endpoint_copy_is_unresolved(transform):
    font, report, manifest = fixture()
    manifest['declarations'][1]['transform'] = transform
    assert evaluate(font, report, manifest)[0]['status'] == 'unresolved'
    assert report['declarations'][1]['status'] == 'rejected'


def test_reflection_and_edge_reversal_verify():
    font, report, manifest = fixture()
    manifest['declarations'][0]['transform'] = [-1, 0, 0, 1, 100, 0]
    assert evaluate(font, report, manifest)[0]['status'] == 'repeated-but-separate'
    assert report['declarations'][0]['status'] == 'verified'


def test_unproven_resemblance_and_erased_union_remain_distinct():
    font, report, _ = fixture()
    report['provenance'].append({'from': 'target', 'to': 'base', 'kind': 'recorded-generator-input'})
    assert {r['status'] for r in constituent_reuse(report, 1000)['results']} == {'similar-only', 'unresolved'}


def test_stale_and_missing_constituent_rejected():
    font, report, manifest = fixture()
    manifest['source']['sha256'] = 'old'
    with pytest.raises(ValueError, match='Stale'):
        evaluate(font, report, manifest)
    manifest['source']['sha256'] = report['source_identity']
    del manifest['declarations'][0]['constituent']
    with pytest.raises(ValueError, match='constituent'):
        evaluate(font, report, manifest)


def test_cli_artifacts_are_read_only(tmp_path):
    font, _, _ = fixture()
    source = tmp_path/'test.ufo'
    font.save(source)
    out = ROOT/'build/test-constituent-reuse'
    report = run(source, out, proof_names=['base', 'target'], reuse=True)
    assert report['source_preserved']
    assert report['constituent_reuse']['results'][0]['status'] == 'similar-only'
    assert 'Constituent reuse' in (out/'index.html').read_text()
    assert '#23a05b' in (out/'proof.svg').read_text()


@pytest.mark.parametrize('taper', [25, -25])
def test_heldout_tapered_constituents_preserve_intended_width_profile(taper):
    font, report, manifest = fixture(taper)
    assert evaluate(font, report, manifest)[0]['status'] == 'repeated-but-separate'
    a, b = manifest['declarations']
    b['part'] = copy.deepcopy(a['part'])
    b['transform'] = list(a['transform'])
    assert evaluate(font, report, manifest)[0]['status'] == 'shared'


def test_single_failed_claim_remains_visible():
    font, report, manifest = fixture()
    manifest['declarations'] = manifest['declarations'][:1]
    manifest['declarations'][0]['transform'][4] = 50
    rows = evaluate(font, report, manifest)
    assert any(r['status'] == 'unresolved' and r.get('declarations') == ['0'] for r in rows)


def test_partial_longitudinal_overlap_does_not_establish_shared_stem():
    # Classifier control: two independently supported spans on the same straight
    # stroke, with unequal endpoints. This is intentionally not a full-copy claim.
    font, report, manifest = fixture()
    evaluate(font, report, manifest)
    a, b = [next(r for r in report['relationships'] if r['geometry_id'] == d['part']['target_geometry_id'])
            for d in report['declarations']]
    b['edges'] = [[(x, y+200) for x, y in edge] for edge in a['edges']]
    rows = constituent_reuse(report, 1000)['results']
    assert rows[0]['status'] == 'unresolved'
    assert 'Partial overlap' in rows[0]['reason']


@pytest.mark.parametrize('mode', ['separate', 'shared', 'displaced', 'reverse'])
def test_independent_curved_ribbon_constituents(mode):
    """A radial ribbon is a separate family from the straight/tapered controls."""
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Evaluation'
    angles = [-.25+i*.5/80 for i in range(81)]
    outline = ([(540*math.cos(a), 540*math.sin(a)) for a in angles]
               + [(460*math.cos(a), 460*math.sin(a)) for a in reversed(angles)])
    for name, offsets in [('base', [0]), ('target', [0, 250])]:
        pen = font.newGlyph(name).getPen()
        for dx in offsets:
            points = list(reversed(outline)) if mode == 'reverse' and name == 'target' else outline
            pen.moveTo((points[0][0]+dx, points[0][1]))
            for x, y in points[1:]:
                pen.lineTo((x+dx, y))
            pen.closePath()
    report = analyse(font, paired=True)
    pairs = [r for r in report['relationships'] if r['relationship'] == 'paired-stroke-boundaries']
    base = max((r for r in pairs if r['glyph'] == 'base'), key=lambda r: r['length_em'])
    targets = []
    for dx in [0, 250]:
        candidates = [r for r in pairs if r['glyph'] == 'target'
                      and 450+dx < r['centerline'][0][0] < 550+dx]
        targets.append(max(candidates, key=lambda r: r['length_em']))
    declarations = []
    for i, target in enumerate(targets):
        declarations.append({'id': str(i), 'base': 'base', 'target': 'target',
            'operation': 'stroke-copy', 'constituent': f'ribbon-{i}',
            'transform': [1, 0, 0, 1, 250*i, 0], 'protected_landmarks': [],
            'evidence_origin': 'independent radial ribbon control',
            'part': {'base_geometry_id': base['geometry_id'], 'target_geometry_id': target['geometry_id']}})
    if mode == 'shared':
        declarations[1]['part'] = copy.deepcopy(declarations[0]['part'])
        declarations[1]['transform'] = list(declarations[0]['transform'])
    elif mode == 'displaced':
        declarations[1]['transform'][5] = 12
    manifest = {'format': 'myiadidot-provenance-v1',
                'source': {'sha256': report['source_identity'], 'style': 'Evaluation'},
                'declarations': declarations}
    rows = evaluate(font, report, manifest)
    claimed = [r for r in rows if r.get('declarations') == ['0', '1']]
    expected = {'shared': 'shared', 'displaced': 'unresolved'}.get(mode, 'repeated-but-separate')
    assert len(claimed) == 1
    assert claimed[0]['status'] == expected
    if mode != 'displaced':
        assert all(d['status'] == 'verified' for d in report['declarations'])
