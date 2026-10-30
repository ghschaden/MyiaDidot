"""Score local terminal evidence separately from labelled attachment function."""

from collections import Counter, defaultdict

from .region_evaluation import evaluate_regions


def arm_evidence(row, detector, side):
    """Missing evidence is unknown, not a negative terminal observation."""
    if detector == 'lower_returns':
        contexts = row.get('arm_context', [])
        context = contexts[side] if len(contexts) == 2 else {}
        cap = context.get('cap_status')
        terminal = context.get('terminal_context', {})
        cap_known = cap is not None
        capped = cap == 'short-contour-cap'
    else:
        caps, contexts = row.get('terminal_caps', []), row.get('terminal_context', [])
        cap_known = len(caps) == 2
        capped = caps[side] is True if cap_known else False
        terminal = contexts[side] if len(contexts) == 2 else {}
    status = terminal.get('status')
    known = cap_known and status in ('verified-contour-terminal', 'unresolved')
    positive = capped or status == 'verified-contour-terminal'
    return {'observed': positive if positive or known else None,
            'normal_cap': capped if cap_known else None,
            'reciprocal_closure': status, 'reason': terminal.get('reason'),
            'window_checks': terminal.get('window_checks', {})}


def evaluate_terminal_arms(corpus, report, em, slant=0):
    """Use existing source/split/region validation and retain all coverage gaps.

    Optional terminal_arms labels are anatomical judgements for left/right arms.
    Attachment context is descriptive gold data, never an inferred detector role.
    """
    for region in corpus['regions']:
        if 'terminal_arms' not in region:
            continue
        labels = region['terminal_arms']
        if (not isinstance(labels, dict) or set(labels) != {'left', 'right'}
                or any(v not in ('terminal', 'nonterminal', 'ambiguous') for v in labels.values())):
            raise ValueError('Invalid terminal arm labels')
        if region.get('attachment_context') not in ('free-end', 'stem-connection', 'interior-connection', 'uncertain'):
            raise ValueError('Invalid attachment context')
    regions = evaluate_regions(corpus, report, em, slant)
    rows = defaultdict(list)
    for detector in ('upper_arches', 'lower_returns'):
        for row in report[detector]['results']:
            rows[detector, row['glyph'], row['geometry_id']].append(row)
    results = []
    for region in regions['results']:
        if 'terminal_arms' not in region:
            continue
        observations = region['observations']
        ambiguous = len(observations) > 1 or any(r.get('ambiguous') for r in observations)
        matched = []
        if len(observations) == 1 and not ambiguous:
            matched = rows[region['detector'], region['glyph'], observations[0]['geometry_id']]
            ambiguous = len(matched) != 1
        for side, label in enumerate(('left', 'right')):
            expected = region['terminal_arms'][label]
            evidence = arm_evidence(matched[0], region['detector'], side) if len(matched) == 1 and not ambiguous else None
            if ambiguous:
                outcome = 'ambiguous-assignment'
            elif not observations:
                outcome = 'unobserved'
            elif expected == 'ambiguous':
                outcome = 'unscored'
            elif evidence['observed'] is None:
                outcome = 'unreported'
            elif expected == 'terminal':
                outcome = 'supported-terminal' if evidence['observed'] else 'unresolved-terminal'
            else:
                outcome = 'terminal-on-nonterminal' if evidence['observed'] else 'not-promoted'
            results.append({'region': region['id'], 'glyph': region['glyph'], 'side': label,
                            'family': region['family'], 'split': region['split'],
                            'expected': expected, 'attachment_context': region['attachment_context'],
                            'outcome': outcome, 'evidence': evidence,
                            'geometry_id': observations[0]['geometry_id'] if len(observations) == 1 and not ambiguous else None})
    summaries = {split: dict(Counter(r['outcome'] for r in results if r['split'] == split))
                 for split in sorted({r['split'] for r in results})}
    return {'format': 'myiadidot-terminal-arm-evaluation-v1',
            'source_sha256': regions['source_sha256'], 'corpus_sha256': regions['corpus_sha256'],
            'implementation_sha256': regions['implementation_sha256'],
            'results': results, 'summaries': summaries, 'region_evaluation': regions,
            'limitations': ['Not-promoted means no positive terminal evidence, not proven nonterminal anatomy.',
                            'A local terminal does not establish an exit or a compatible attachment role.',
                            'Labels are reviewer judgements; ambiguous and missing observations are not successes.']}
