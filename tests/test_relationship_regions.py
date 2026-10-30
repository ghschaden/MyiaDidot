"""Region accounting controls: missing and unsupported geometry cannot vanish."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.region_evaluation import evaluate_regions


def fixture():
    corpus = {'format': 'myiadidot-region-corpus-v1', 'source_sha256': 'source', 'scope': ['g'],
              'regions': [{'id': 'arch', 'glyph': 'g', 'family': 'independent', 'split': 'heldout',
                           'box': [0, 400, 300, 600], 'detector': 'upper_arches',
                           'candidate': 'present', 'role': 'entry'}],
              'conflict_regions': [{'glyph': 'g', 'box': [0, 0, 500, 1000], 'expected': 'absent'}]}
    report = {'source': {'sha256': 'source'}, 'source_preserved': True,
              'upper_arches': {'scope': ['g'], 'results': []},
              'lower_returns': {'scope': ['g'], 'results': []}}
    return corpus, report


def row(role='entry', point=(100, 500)):
    return {'glyph': 'g', 'geometry_id': 'arch-1', 'role': role, 'crown': point, 'conflicts': []}


def test_missed_region_is_retained_and_role_not_counted_correct():
    corpus, report = fixture()
    result = evaluate_regions(corpus, report, 1000)
    assert result['results'][0]['candidate_outcome'] == 'missed'
    assert result['results'][0]['role_outcome'] == 'unobserved'


@pytest.mark.parametrize('role,outcome', [('entry', 'correct'), ('exit', 'wrong'), ('unresolved', 'unresolved')])
def test_role_accuracy_separates_unresolved(role, outcome):
    corpus, report = fixture()
    report['upper_arches']['results'] = [row(role)]
    result = evaluate_regions(corpus, report, 1000)['results'][0]
    assert result['candidate_outcome'] == 'detected'
    assert result['role_outcome'] == outcome


def test_scope_negative_is_not_success_when_candidate_role_unresolved():
    corpus, report = fixture()
    corpus['regions'][0].update(candidate='absent', role=None)
    report['upper_arches']['results'] = [row('unresolved')]
    assert evaluate_regions(corpus, report, 1000)['results'][0]['candidate_outcome'] == 'out-of-scope-candidate'


def test_unlabelled_detection_and_conflict_are_retained():
    corpus, report = fixture()
    detected = row(point=(600, 500))
    detected['conflicts'] = [{'terminal_bottom': [600, 10], 'kind': 'detour'}]
    report['upper_arches']['results'] = [detected]
    result = evaluate_regions(corpus, report, 1000)
    assert len(result['unmatched_detections']) == 1
    assert result['conflicts'][0]['outcome'] == 'unscored-conflict'


def test_overlap_and_multiple_candidates_are_ambiguous():
    corpus, report = fixture()
    corpus['regions'].append({**corpus['regions'][0], 'id': 'overlap'})
    report['upper_arches']['results'] = [row()]
    result = evaluate_regions(corpus, report, 1000)
    assert all(r['candidate_outcome'] == 'ambiguous' for r in result['results'])
    assert len(result['ambiguous_assignments']) == 1
    corpus['regions'].pop()
    report['upper_arches']['results'].append({**row(), 'geometry_id': 'another'})
    assert evaluate_regions(corpus, report, 1000)['results'][0]['candidate_outcome'] == 'ambiguous'


def test_coordinates_are_restored_before_region_and_conflict_assignment():
    corpus, report = fixture()
    detected = row(point=(-200, 500))
    detected['conflicts'] = [{'terminal_bottom': [-200, 500], 'kind': 'detour'}]
    report['upper_arches']['results'] = [detected]
    result = evaluate_regions(corpus, report, 1000, slant=.6)
    assert result['results'][0]['candidate_outcome'] == 'detected'
    assert result['conflicts'][0]['outcome'] == 'false-conflict'
    assert result['conflict_regions'][0]['outcome'] == 'false-conflict'


def test_missing_positive_conflict_is_reported():
    corpus, report = fixture()
    corpus['conflict_regions'][0]['expected'] = 'present'
    assert evaluate_regions(corpus, report, 1000)['conflict_regions'][0]['outcome'] == 'missed'


@pytest.mark.parametrize('problem', ['source', 'preservation', 'scope', 'box', 'duplicate', 'leakage', 'conflict'])
def test_invalid_corpus_or_source_is_rejected(problem):
    corpus, report = fixture()
    if problem == 'source':
        corpus['source_sha256'] = 'stale'
    elif problem == 'preservation':
        report['source_preserved'] = False
    elif problem == 'scope':
        report['lower_returns']['scope'] = []
    elif problem == 'box':
        corpus['regions'][0]['box'][2] = -1
    elif problem in ('duplicate', 'leakage'):
        extra = copy.deepcopy(corpus['regions'][0])
        if problem == 'leakage':
            extra.update(id='development', split='development')
        corpus['regions'].append(extra)
    else:
        corpus['conflict_regions'][0]['expected'] = 'anything'
    with pytest.raises(ValueError):
        evaluate_regions(corpus, report, 1000)


@pytest.mark.parametrize('observed,outcome', [('terminal-curve', 'correct'), ('closed-counter', 'wrong'),
                                            ('unresolved', 'unresolved'), ('unreported', 'unresolved')])
def test_anatomical_scope_scored_separately_from_raw_candidates(observed, outcome):
    corpus, report = fixture()
    corpus['regions'][0].update(candidate='absent', role=None, anatomical_scope='terminal-curve')
    report['upper_arches']['results'] = [{**row('unresolved'), 'anatomical_scope': {'kind': observed}}]
    result = evaluate_regions(corpus, report, 1000)['results'][0]
    assert result['scope_outcome'] == outcome
    assert result['candidate_outcome'] == 'out-of-scope-candidate'


def test_missing_scope_observation_and_invalid_label():
    corpus, report = fixture()
    corpus['regions'][0]['anatomical_scope'] = 'terminal-curve'
    assert evaluate_regions(corpus, report, 1000)['results'][0]['scope_outcome'] == 'unobserved'
    corpus['regions'][0]['anatomical_scope'] = 'made-up'
    with pytest.raises(ValueError, match='scope label'):
        evaluate_regions(corpus, report, 1000)
