"""Role-gated local return retrieval; compatibility is not repair acceptance."""

import math
from itertools import combinations

from .geometry import angle, resample

RETURN_MATCH_POLICY = {'counter_rms_em': .008, 'counter_max_em': .015,
                       'arm_width_rms_em': .008, 'arm_width_fraction': .15,
                       'attachment_degrees': 12, 'cap_rms_em': .01}


def rms(values):
    return math.sqrt(sum(v*v for v in values)/len(values))


def cap_profile(context, em):
    points = context['cap_trace']
    origin = points[0]
    normal = [((p[0]-origin[0])/em, (p[1]-origin[1])/em) for p in points]
    # Fixed count via common normalized arc fractions, not source node indices.
    total = sum(math.dist(a, b) for a, b in zip(normal, normal[1:]))
    return resample(normal, total/16*(1+1e-12)) if total else []


def compare_returns(a, b, em_a, em_b, style_a, style_b):
    result = {'left': a['geometry_id'], 'right': b['geometry_id'],
              'source_sha256': [a.get('source_sha256'), b.get('source_sha256')],
              'glyphs': [a['glyph'], b['glyph']], 'decision': 'unresolved', 'reasons': []}
    if style_a != style_b:
        result['reasons'] = ['Different styles are reference observations, not reuse candidates.']
        return result
    if a['role'] not in ('interior', 'exit') or b['role'] not in ('interior', 'exit'):
        result['reasons'] = ['At least one connection role is unresolved.']
        return result
    if a['status'] != 'supported-local-turn' or b['status'] != 'supported-local-turn':
        result['reasons'] = ['Both turns must have supported local geometry.']
        return result
    if a['direction'] != b['direction'] or a['role'] != b['role']:
        result.update(decision='incompatible', reasons=['Connection direction or role differs.'])
        return result
    contexts = [r.get('arm_context', []) for r in (a, b)]
    if any(len(c) != 2 or any(x['status'] != 'supported-local-band' for x in c) for c in contexts):
        result['reasons'] = ['Complete local support on both arms is required for matching.']
        return result
    if any(x['below_floor_context'] != 'not-observed' for c in contexts for x in c):
        result['reasons'] = ['Tail/descender attachment context remains unresolved.']
        return result
    if a['role'] == 'exit' and any(c[1]['cap_status'] != 'short-contour-cap' for c in contexts):
        result['reasons'] = ['Both exit caps must be verified.']
        return result
    counters = [[s['clearance_units']/em for s in r['counter_sections']] for r, em in [(a, em_a), (b, em_b)]]
    if len(counters[0]) != 8 or len(counters[1]) != 8:
        result['reasons'] = ['Incomplete fixed-height counter profile.']
        return result
    if any(len(x['sections']) != 5 for c in contexts for x in c):
        result['reasons'] = ['Incomplete fixed-window arm profile.']
        return result
    delta = [x-y for x, y in zip(*counters)]
    metrics = {'counter_rms_em': rms(delta), 'counter_max_em': max(map(abs, delta)),
               'arm_width_rms_em': [], 'arm_width_fraction': [], 'attachment_degrees': []}
    for side in range(2):
        x, y = contexts[0][side], contexts[1][side]
        wa = [s['width']/em_a for s in x['sections']]
        wb = [s['width']/em_b for s in y['sections']]
        metrics['arm_width_rms_em'].append(rms([p-q for p, q in zip(wa, wb)]))
        metrics['arm_width_fraction'].append(max(abs(p-q)/max(min(p, q), 1e-12) for p, q in zip(wa, wb)))
        metrics['attachment_degrees'].append(angle(a['attachment_directions'][side], b['attachment_directions'][side]))
    if a['role'] == 'exit':
        ca, cb = cap_profile(contexts[0][1], em_a), cap_profile(contexts[1][1], em_b)
        if len(ca) != 17 or len(cb) != 17:
            result['reasons'] = ['Degenerate terminal trace.']
            return result
        metrics['cap_rms_em'] = rms([math.dist(p, q) for p, q in zip(ca, cb)])
    reasons = []
    for key, value in metrics.items():
        worst = max(value) if isinstance(value, list) else value
        if worst > RETURN_MATCH_POLICY[key]:
            reasons.append(f'{key} exceeds the matching limit.')
    result.update(metrics=metrics, decision='incompatible' if reasons else 'candidate',
                  reasons=reasons or ['Same observed role and compatible counter, arm-width, direction and terminal context; no ancestry or repair acceptance inferred.'])
    return result


def match_returns(rows, em, style):
    comparisons = [compare_returns(a, b, em, em, style, style)
                   for a, b in combinations(rows, 2) if a['glyph'] != b['glyph']]
    return {'format': 'myiadidot-return-matches-v1', 'policy': RETURN_MATCH_POLICY,
            'comparisons': comparisons,
            'scope': 'Same-style local retrieval; unresolved roles cannot become positive matches. No fitting, ancestry inference or repair acceptance.'}
