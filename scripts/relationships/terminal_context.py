"""Bounded terminal closure, separate from parallel-sided stem sections."""

import numpy as np

TERMINAL_POLICY = {'section': 'reciprocal horizontal first-hit ink interval',
                   'limits': 'Existing context_policy cap_trace_em/cap_height_em/cap_width_em',
                   'minimum_rise_em': .005,
                   'use_for_roles': False,
                   'diagnostics': 'terminal-window-checks-v1; unmeasured limits are not passes'}


def terminal_context(field, ci, arc, direction, em, limits):
    """Cut a contour arm horizontally and follow it to the verified other edge.

    This proves a bounded terminal lobe, not normal width or stem support. The
    directed arc must stay above the cut; a return via the counter floor fails.
    """
    poly = field.polygons[ci]
    p = poly.at(arc)[0]
    result = {'status': 'unresolved', 'section': None, 'trace': [],
              'reason': None, 'arc_length_units': None, 'window_checks': {}}

    def refuse(reason):
        result['reason'] = reason
        return result

    def maximum_check(name, value, limit):
        result['window_checks'][name] = {
            'measured_units': value, 'measured_em': value/em,
            'maximum_em': limit, 'ratio_to_maximum': value/(em*limit),
            'excess_units': max(0., value-em*limit), 'passes': value <= em*limit}

    left, right = field.ink(p+[-field.epsilon, 0]), field.ink(p+[field.epsilon, 0])
    if left == right:
        return refuse('No unique horizontal ink side at the shoulder.')
    normal = np.array([-1., 0.]) if left else np.array([1., 0.])
    hit, error = field.hit(p, normal)
    if error:
        return refuse('Horizontal section: '+error)
    q, cj, target_arc, width = hit
    if cj != ci:
        return refuse('Opposite boundary belongs to another contour.')
    if not field.ink(q-normal*field.epsilon) or field.ink(q+normal*field.epsilon):
        return refuse('No unique opposite ink side at the terminal cut.')
    back, error = field.hit(q, -normal)
    if error or back[1] != ci or np.linalg.norm(back[0]-p) > field.epsilon:
        return refuse('Horizontal reverse correspondence failed.')
    if not all(field.ink(p+(q-p)*t/10) for t in range(1, 10)):
        return refuse('Horizontal section crosses white space.')
    result['section'] = {'p': p.tolist(), 'q': q.tolist(), 'width': width,
                         'source_contour': ci, 'target_contour': cj,
                         'source_arc': arc, 'target_arc': target_arc}
    distance = float(((target_arc-arc)*direction) % poly.perimeter)
    result['arc_length_units'] = distance
    maximum_check('trace', distance, limits['cap_trace_em'])
    if distance > em*limits['cap_trace_em']:
        return refuse('Contour route to the opposite edge exceeds the cap trace window.')
    # Include every flattened vertex: a uniform sample could skip a short detour.
    offsets = (direction*(poly.starts[:-1]-arc)) % poly.perimeter
    order = np.argsort(offsets)
    trace = [p, *[poly.points[k] for k in order if 0 < offsets[k] < distance], q]
    result['trace'] = [point.tolist() for point in trace]
    points = np.array(trace)
    rise = float(points[:, 1].max()-p[1])
    span = float(np.ptp(points[:, 0]))
    result.update(rise_units=rise, span_units=span)
    maximum_check('rise', rise, limits['cap_height_em'])
    maximum_check('span', span, limits['cap_width_em'])
    result['window_checks']['rise'].update(
        minimum_em=TERMINAL_POLICY['minimum_rise_em'],
        passes_minimum=rise > em*TERMINAL_POLICY['minimum_rise_em'])
    if float(points[:, 1].min()) < p[1]-field.epsilon:
        return refuse('Contour route crosses below its terminal cut.')
    if not em*TERMINAL_POLICY['minimum_rise_em'] < rise <= em*limits['cap_height_em']:
        return refuse('Terminal rise is outside the existing cap window.')
    if span > em*limits['cap_width_em']:
        return refuse('Terminal extent exceeds the existing cap width window.')
    result.update(status='verified-contour-terminal',
                  reason='Directed contour closes above a reciprocal ink cut on its verified opposite edge.')
    return result
