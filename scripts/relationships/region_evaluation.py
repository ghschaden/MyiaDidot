"""Score source-pinned, prelabelled regions without hiding detector omissions."""

import math
from collections import Counter, defaultdict

from .identity import digest


def evaluate_regions(corpus, report, em, slant=0):
    """Boxes use original font coordinates; detections use deskewed coordinates.

    A negative candidate label rejects that anatomy from this recogniser's scope,
    not the drawing. Unknown gold roles are excluded from role accuracy. Unlabelled
    detections and ambiguous assignments are retained rather than counted correct.
    """
    if corpus.get('format') != 'myiadidot-region-corpus-v1':
        raise ValueError('Unsupported region corpus')
    if corpus.get('source_sha256') != report['source']['sha256']:
        raise ValueError('Stale region corpus source')
    if report.get('source_preserved') is not True:
        raise ValueError('Report does not verify source preservation')
    if not math.isfinite(em) or em <= 0 or not math.isfinite(slant):
        raise ValueError('Invalid coordinate frame')
    regions = corpus['regions']
    ids, splits = set(), defaultdict(set)
    for region in regions:
        if region['id'] in ids:
            raise ValueError('Duplicate region id')
        ids.add(region['id'])
        if region['split'] not in ('transfer', 'heldout', 'development'):
            raise ValueError('Unknown evaluation split')
        splits[region['family']].add(region['split'])
        box = region['box']
        if (len(box) != 4 or not all(math.isfinite(v) for v in box)
                or box[0] >= box[2] or box[1] >= box[3]):
            raise ValueError('Invalid region box')
        if region['candidate'] not in ('present', 'absent', 'uncertain'):
            raise ValueError('Invalid candidate label')
        if region.get('anatomical_scope') not in (None, 'closed-counter', 'terminal-curve', 'supported-stem-connection'):
            raise ValueError('Invalid anatomical scope label')
        if region['role'] not in (None, 'entry', 'interior', 'exit'):
            raise ValueError('Invalid role label')
        if region['detector'] not in ('upper_arches', 'lower_returns'):
            raise ValueError('Invalid detector')
        if region['glyph'] not in corpus['scope']:
            raise ValueError('Region outside declared scope')
    if any(len(v) > 1 for v in splits.values()):
        raise ValueError('Family leaks across evaluation splits')
    for region in corpus['conflict_regions']:
        box = region['box']
        if (region['glyph'] not in corpus['scope'] or region['expected'] not in ('present', 'absent', 'uncertain')
                or len(box) != 4 or not all(math.isfinite(v) for v in box)
                or box[0] >= box[2] or box[1] >= box[3]):
            raise ValueError('Invalid conflict region')
    assignments = defaultdict(list)
    unmatched, ambiguous, conflicts = [], [], []
    for detector in ('upper_arches', 'lower_returns'):
        if detector not in report or not set(corpus['scope']) <= set(report[detector]['scope']):
            raise ValueError('Incomplete detector scope')
        point_key = 'crown' if detector == 'upper_arches' else 'bottom'
        for row in report[detector]['results']:
            if row['glyph'] not in corpus['scope']:
                continue
            x, y = row[point_key]
            point = [x+slant*y, y]
            matches = [r for r in regions if r['glyph'] == row['glyph'] and r['detector'] == detector
                       and r['box'][0] <= point[0] <= r['box'][2]
                       and r['box'][1] <= point[1] <= r['box'][3]]
            observed = {'geometry_id': row['geometry_id'], 'glyph': row['glyph'],
                        'detector': detector, 'point': point, 'role': row['role'],
                        'anatomical_scope': row.get('anatomical_scope', {'kind': 'unreported'})}
            if not matches:
                unmatched.append(observed)
            elif len(matches) != 1:
                ambiguous.append({**observed, 'regions': [r['id'] for r in matches]})
                for region in matches:
                    assignments[region['id']].append({**observed, 'ambiguous': True})
            else:
                assignments[matches[0]['id']].append(observed)
            # Conflict location is the lower turn, not the arch crown. Score
            # against independently labelled conflict regions below.
            for conflict in row.get('conflicts', []):
                cx, cy = conflict['terminal_bottom']
                locations = [r for r in corpus['conflict_regions'] if r['glyph'] == row['glyph']
                             and r['box'][0] <= cx+slant*cy <= r['box'][2]
                             and r['box'][1] <= cy <= r['box'][3]]
                label = locations[0]['expected'] if len(locations) == 1 else 'unlabelled'
                conflicts.append({'glyph': row['glyph'], 'point': [cx+slant*cy, cy], 'finding': conflict,
                                  'outcome': 'false-conflict' if label == 'absent' else
                                  'correct-conflict' if label == 'present' else 'unscored-conflict'})
    results = []
    for region in regions:
        observations = assignments[region['id']]
        if any(r.get('ambiguous') for r in observations) or len(observations) > 1:
            outcome = 'ambiguous'
        elif region['candidate'] == 'uncertain':
            outcome = 'unscored'
        elif region['candidate'] == 'present':
            outcome = 'detected' if observations else 'missed'
        else:
            outcome = 'out-of-scope-candidate' if observations else 'correct-absence'
        role = 'unscored'
        if region['role'] is not None and region['candidate'] == 'present':
            if outcome != 'detected':
                role = 'unobserved' if outcome == 'missed' else 'ambiguous'
            elif observations[0]['role'] == 'unresolved':
                role = 'unresolved'
            else:
                role = 'correct' if observations[0]['role'] == region['role'] else 'wrong'
        scope = 'unscored'
        if region.get('anatomical_scope') is not None:
            if not observations:
                scope = 'unobserved'
            elif len(observations) != 1 or observations[0].get('ambiguous'):
                scope = 'ambiguous'
            else:
                observed_scope = observations[0]['anatomical_scope']['kind']
                scope = ('unresolved' if observed_scope in ('unresolved', 'unreported') else
                         'correct' if observed_scope == region['anatomical_scope'] else 'wrong')
        results.append({**region, 'scope_outcome': scope, 'observations': observations, 'candidate_outcome': outcome, 'role_outcome': role})
    conflict_results = []
    for region in corpus['conflict_regions']:
        findings = [c for c in conflicts if c['glyph'] == region['glyph']
                    and region['box'][0] <= c['point'][0] <= region['box'][2]
                    and region['box'][1] <= c['point'][1] <= region['box'][3]]
        if region['expected'] == 'uncertain' or any(c['outcome'] == 'unscored-conflict' for c in findings):
            outcome = 'unscored'
        elif region['expected'] == 'present':
            outcome = 'detected' if findings else 'missed'
        else:
            outcome = 'false-conflict' if findings else 'no-finding'
        conflict_results.append({**region, 'outcome': outcome, 'finding_count': len(findings)})
    summaries = {}
    for split in sorted({r['split'] for r in regions}):
        subset = [r for r in results if r['split'] == split]
        summaries[split] = {'candidate_outcomes': dict(Counter(r['candidate_outcome'] for r in subset)),
                            'role_outcomes': dict(Counter(r['role_outcome'] for r in subset)),
                            'scope_outcomes': dict(Counter(r['scope_outcome'] for r in subset)),
                            'families': sorted({r['family'] for r in subset})}
    return {'format': 'myiadidot-region-evaluation-v1', 'corpus_sha256': digest(corpus),
            'source_sha256': report['source']['sha256'], 'implementation_sha256': report.get('implementation_sha256'),
            'results': results, 'summaries': summaries, 'units_per_em': em,
            'conflict_regions': conflict_results, 'unmatched_detections': unmatched,
            'ambiguous_assignments': ambiguous, 'conflicts': conflicts,
            'limitations': ['Single-reviewer anatomical labels, not design acceptance or universal accuracy.',
                            'Zero conflict findings on negative drawings does not measure bad-splice recall.']}
