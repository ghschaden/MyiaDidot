"""Local arm sections and bounded contour context; no inferred ancestry."""

import numpy as np

from .geometry import length, sub
from .terminal_context import reciprocal_terminal_context

CONTEXT_POLICY = {'section_step_em': .015, 'section_count': 5,
                  'cap_trace_em': .35, 'cap_height_em': .16,
                  'cap_width_em': .12, 'below_floor_em': .04,
                  'shared_section_em': .003, 'cap_return_em': .003,
                  'band_axis_ratio': 2, 'maximum_width_ratio': 1.25}


def locate(poly, point):
    """Project onto a flattened contour, retaining its arc position."""
    point = np.asarray(point)
    t = np.clip(np.sum((point-poly.points)*poly.vectors, axis=1)/poly.lengths**2, 0, 1)
    candidates = poly.points+t[:, None]*poly.vectors
    distances = np.linalg.norm(candidates-point, axis=1)
    k = int(np.argmin(distances))
    return float(poly.starts[k]+t[k]*poly.lengths[k])


def arm_context(field, ci, path, bottom, em, *, terminal_policy='baseline'):
    poly = field.polygons[ci]
    shoulder = path[-1]
    arc = locate(poly, shoulder)
    forward = poly.at(arc+em*.001)[0]
    backward = poly.at(arc-em*.001)[0]
    direction = 1 if np.dot(forward-backward, sub(path[-1], path[-2])) > 0 else -1
    samples, reasons = [], []
    for k in range(CONTEXT_POLICY['section_count']):
        section, reason = field.section(ci, arc+direction*k*em*CONTEXT_POLICY['section_step_em'])
        if section:
            samples.append(section)
        else:
            reasons.append({'sample': k, 'reason': reason})
    # Require an uninterrupted band. A few successful rays do not bridge a junction.
    supported = len(samples) == CONTEXT_POLICY['section_count']
    if supported:
        centers = [(np.array(s['p'])+s['q'])/2 for s in samples]
        delta = centers[-1]-centers[0]
        widths = [s['width'] for s in samples]
        supported = (abs(delta[1]) > CONTEXT_POLICY['band_axis_ratio']*abs(delta[0])
                     and max(widths) <= min(widths)*CONTEXT_POLICY['maximum_width_ratio'])
        if not supported:
            reasons.append({'reason': 'Local band is nonvertical or changes width too rapidly.'})
    # Follow the same contour arm, not a nearby outline. A short cap must return
    # below shoulder height on its other side within a bounded arc/height/width.
    trace = [list(shoulder)]
    cap = 'unresolved'
    first_section, _ = field.section(ci, arc)
    opposite = first_section['q'] if first_section and first_section['target_contour'] == ci else None
    cap_return_distance = None
    for distance in np.arange(em*.002, em*CONTEXT_POLICY['cap_trace_em'], em*.002):
        p = poly.at(arc+direction*distance)[0]
        trace.append(p.tolist())
        if p[1] > shoulder[1]+em*CONTEXT_POLICY['cap_height_em']:
            cap = 'continues-above-window'
            break
        if p[1] < min(shoulder[1], opposite[1] if opposite else shoulder[1])-em*.002:
            high = max(q[1] for q in trace)
            width = max(q[0] for q in trace)-min(q[0] for q in trace)
            cap_return_distance = min(length(sub(q, opposite)) for q in trace) if opposite else None
            if (high > shoulder[1]+em*.005 and width <= em*CONTEXT_POLICY['cap_width_em']
                    and cap_return_distance is not None and cap_return_distance <= em*CONTEXT_POLICY['cap_return_em']):
                cap = 'short-contour-cap'
            break
    low = min(float(p.points[:, 1].min()) for p in field.polygons)
    below_threshold = min(0, bottom[1])-em*CONTEXT_POLICY['below_floor_em']
    below = low < below_threshold
    return {'status': 'supported-local-band' if supported else 'unresolved',
            'sections': samples, 'failures': reasons, 'cap_status': cap,
            'terminal_context': reciprocal_terminal_context(field, ci, arc, direction, em, terminal_policy),
            'cap_trace': trace, 'below_floor_context': 'present' if below else 'not-observed',
            'cap_return_distance_units': cap_return_distance,
            'below_floor_depth_units': bottom[1]-low,
            'below_floor_threshold_units': below_threshold,
            'scope': 'Local sections and bounded contour cap; below-floor context is glyph-wide, not proven attachment.'}


def same_band(a, b, em):
    """Opposite observations must agree on both ends of several ink sections."""
    if a['status'] != 'supported-local-band' or b['status'] != 'supported-local-band':
        return False
    matches = []
    for x in a['sections']:
        distances = []
        for y in b['sections']:
            error = min(max(length(sub(x['p'], y[u])), length(sub(x['q'], y[v])))
                        for u, v in [('p', 'q'), ('q', 'p')])
            distances.append(error)
        matches.append(min(distances) <= em*CONTEXT_POLICY['shared_section_em'])
    return sum(matches) >= 3


def resolve_context(rows, em):
    for row in rows:
        if row.get('counter_topology', {}).get('kind') == 'closed-counter':
            continue
        left, right = row['arm_context']
        if left['status'] != 'supported-local-band' or right['status'] != 'supported-local-band':
            continue
        if same_band(left, right, em):
            continue
        row['status'] = 'supported-local-turn'
        row['reason'] = 'Both counter arms have independent uninterrupted local ink-section bands.'
        following = [r for r in rows if r is not row and r.get('counter_topology', {}).get('kind') != 'closed-counter'
                     and r['bottom'][0] > row['bottom'][0]
                     and same_band(right, r['arm_context'][0], em)]
        if len(following) == 1:
            row.update(role='interior', next_turn=following[0]['geometry_id'],
                       reason='Both arms are supported; the right band agrees with the next turn on at least three complete ink sections.')
        elif not following and right['cap_status'] == 'short-contour-cap' and right['below_floor_context'] == 'not-observed':
            row.update(role='exit', reason='Both arms are supported and the right contour closes through a short cap; no below-floor context observed.')
        elif right['below_floor_context'] == 'present':
            row['reason'] = 'Local arms are supported, but below-floor geometry leaves terminal/tail context unresolved.'
