"""Terminal morphology must not stand in for attachment role or missing evidence."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.terminal_evaluation import evaluate_terminal_arms
from test_relationship_regions import fixture, row


def example():
    corpus, report = fixture()
    corpus['regions'][0].update(terminal_arms={'left': 'nonterminal', 'right': 'terminal'},
                                attachment_context='interior-connection')
    detected = row()
    detected.update(terminal_caps=[False, False], terminal_context=[
        {'status': 'unresolved', 'reason': 'continues'},
        {'status': 'verified-contour-terminal', 'reason': 'closes'}])
    report['upper_arches']['results'] = [detected]
    return corpus, report


def test_terminal_morphology_does_not_replace_attachment_function():
    corpus, report = example()
    before = copy.deepcopy((corpus, report))
    result = evaluate_terminal_arms(corpus, report, 1000)['results']
    assert [r['outcome'] for r in result] == ['not-promoted', 'supported-terminal']
    assert result[1]['attachment_context'] == 'interior-connection'
    assert (corpus, report) == before


@pytest.mark.parametrize('mode,outcome', [('missing', 'unobserved'), ('multiple', 'ambiguous-assignment'),
                                         ('overlap', 'ambiguous-assignment'), ('unreported', 'unreported'),
                                         ('uncertain', 'unscored'), ('negative', 'terminal-on-nonterminal'),
                                         ('unresolved', 'unresolved-terminal')])
def test_missing_ambiguous_and_wrong_results_remain_visible(mode, outcome):
    corpus, report = example()
    rows = report['upper_arches']['results']
    if mode == 'missing':
        rows.clear()
    elif mode == 'multiple':
        rows.append({**rows[0], 'geometry_id': 'other'})
    elif mode == 'overlap':
        corpus['regions'].append({**corpus['regions'][0], 'id': 'overlap'})
    elif mode == 'unreported':
        rows[0].pop('terminal_context')
    elif mode == 'uncertain':
        corpus['regions'][0]['terminal_arms']['right'] = 'ambiguous'
    elif mode == 'negative':
        corpus['regions'][0]['terminal_arms']['right'] = 'nonterminal'
    elif mode == 'unresolved':
        rows[0]['terminal_context'][1]['status'] = 'unresolved'
    result = evaluate_terminal_arms(corpus, report, 1000)
    assert result['results'][1]['outcome'] == outcome


def test_lower_normal_cap_is_evidence_even_if_reciprocal_check_unresolved():
    corpus, report = example()
    corpus['regions'][0]['detector'] = 'lower_returns'
    detected = report['upper_arches']['results'].pop()
    detected['bottom'] = detected.pop('crown')
    detected['arm_context'] = [
        {'cap_status': 'continues', 'terminal_context': {'status': 'unresolved'}},
        {'cap_status': 'short-contour-cap', 'terminal_context': {'status': 'unresolved'}}]
    report['lower_returns']['results'] = [detected]
    assert evaluate_terminal_arms(corpus, report, 1000)['results'][1]['outcome'] == 'supported-terminal'


@pytest.mark.parametrize('bad', ['label', 'side', 'attachment', 'source', 'scope'])
def test_invalid_labels_and_stale_or_incomplete_reports_are_rejected(bad):
    corpus, report = example()
    if bad == 'label':
        corpus['regions'][0]['terminal_arms']['left'] = 'maybe'
    elif bad == 'side':
        corpus['regions'][0]['terminal_arms'].pop('right')
    elif bad == 'attachment':
        corpus['regions'][0]['attachment_context'] = 'exit'
    elif bad == 'source':
        corpus['source_sha256'] = 'stale'
    else:
        report['lower_returns']['scope'] = []
    with pytest.raises(ValueError):
        evaluate_terminal_arms(corpus, report, 1000)
