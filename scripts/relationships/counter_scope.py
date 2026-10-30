"""Separate bounded white-space geometry from evidence for stem connections."""

import numpy as np

from .boundaries import cross

SCOPE_POLICY = {'probe_em': .001,
                'terminal_evidence': 'verified same-contour cap or reciprocal-cut terminal closure',
                'unresolved_is_terminal': False}


def counter_topology(field, ci, bottom, em):
    # A white probe inside this boundary's winding region cannot reach infinity
    # without crossing that boundary. Winding sign is deliberately irrelevant.
    probe = np.array([bottom[0], bottom[1]+em*SCOPE_POLICY['probe_em']])
    poly = field.polygons[ci]
    d = cross(poly.vectors, probe-poly.points)
    up = (poly.points[:, 1] <= probe[1]) & (poly.ends[:, 1] > probe[1]) & (d > 0)
    down = (poly.ends[:, 1] <= probe[1]) & (poly.points[:, 1] > probe[1]) & (d < 0)
    winding = int(np.count_nonzero(up))-int(np.count_nonzero(down))
    closed = winding != 0 and not field.ink(probe)
    return {'kind': 'closed-counter' if closed else 'unresolved-open-context',
            'probe': probe.tolist(), 'boundary_winding': winding,
            'reason': 'White probe is enclosed by the candidate contour.' if closed else
                      'No enclosure by this contour; this alone does not prove a stem connection.'}


def classify_scope(row, supported, caps):
    topology = row['counter_topology']
    if topology['kind'] == 'closed-counter':
        kind, reason = 'closed-counter', topology['reason']
    elif supported:
        kind, reason = 'supported-stem-connection', 'Independent adjoining stem evidence supports the connection.'
    elif any(caps):
        kind, reason = 'terminal-curve', 'Verified contour terminal, but incomplete adjoining stem support.'
    else:
        kind, reason = 'unresolved', 'Neither complete stem support nor a verified contour terminal.'
    row['anatomical_scope'] = {'kind': kind, 'reason': reason,
                               'terminal_caps': list(caps)}
