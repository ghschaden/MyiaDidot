"""Conservative constituent reuse over verified, complete paired spans."""

from collections import defaultdict
from itertools import combinations

from .boundaries import compare_pairs
from .geometry import dot, length, sub
from .provenance import polyline_distance


def stroke_error(a, b):
    """Compare both boundaries, allowing edge order and traversal reversal."""
    return min(max(polyline_distance(x, y) for x, y in zip(a, order))
               for order in (b, b[::-1]))


def sampled_clearance(a, b):
    """Minimum vertex-to-segment distance in both directions."""
    def point_segment(p, x, y):
        d = sub(y, x)
        t = max(0, min(1, dot(sub(p, x), d)/dot(d, d))) if dot(d, d) else 0
        return length(sub(p, (x[0]+t*d[0], x[1]+t*d[1])))
    return min(point_segment(p, x, y)
               for first, second in ((a, b), (b, a))
               for edge in first for p in edge
               for other in second for x, y in zip(other, other[1:]))


def local_pairs(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    for group in groups.values():
        yield from combinations(group, 2)


def constituent_reuse(report, em):
    """Intent comes from declarations; geometry alone never establishes ancestry."""
    pairs = {r['geometry_id']: r for r in report['relationships']
             if r['relationship'] == 'paired-stroke-boundaries'
             and r['identity_status'] == 'unique'}
    claims = [d for d in report.get('declarations', []) if d['operation'] == 'stroke-copy']
    results = []
    for a, b in local_pairs(claims, 'target'):
        if a['target'] != b['target'] or a['constituent'] == b['constituent']:
            continue
        x = pairs.get(a['part']['target_geometry_id'])
        y = pairs.get(b['part']['target_geometry_id'])
        row = {'glyph': a['target'], 'declarations': [a['id'], b['id']],
               'constituents': [a['constituent'], b['constituent']],
               'target_spans': [a['part']['target_geometry_id'], b['part']['target_geometry_id']],
               'status': 'unresolved', 'reason': 'Constituent correspondence failed verification.'}
        if a['status'] == b['status'] == 'verified' and x and y:
            error = stroke_error(x['edges'], y['edges'])
            clearance = sampled_clearance(x['edges'], y['edges'])
            # Separation is conservative: disjoint bounding boxes prove disjoint regions.
            boxes = [(min(p[0] for e in r['edges'] for p in e), min(p[1] for e in r['edges'] for p in e),
                      max(p[0] for e in r['edges'] for p in e), max(p[1] for e in r['edges'] for p in e)) for r in (x, y)]
            u, v = boxes
            separated = u[2] < v[0] or v[2] < u[0] or u[3] < v[1] or v[3] < u[1]
            row['metrics'] = {'boundary_distance_units': error, 'sampled_boundary_clearance_units': clearance}
            if error <= em*.001:
                row.update(status='shared', reason='Distinct declared constituents geometrically coincide on both observed stroke boundaries.')
            elif separated:
                row.update(status='repeated-but-separate', reason='Verified constituent spans occupy disjoint regions.')
            else:
                row['reason'] = 'Partial overlap or ambiguous region; full shared stroke is not established.'
        results.append(row)
    for x, y in local_pairs(pairs.values(), 'glyph'):
        if x['glyph'] != y['glyph'] or x['family'] != y['family']:
            continue
        if any(r['glyph'] == x['glyph'] and set(r['target_spans']) == {x['geometry_id'], y['geometry_id']} for r in results):
            continue
        if compare_pairs(x, y)['compatible']:
            results.append({'glyph': x['glyph'], 'status': 'similar-only',
                            'target_spans': [x['geometry_id'], y['geometry_id']],
                            'reason': 'Comparable local width and axis; constituent ancestry and connection roles are unverified.'})
    scope = set(report.get('paired_boundary_scope', []))
    for edge in report['provenance']:
        if edge['from'] in scope and edge['kind'] == 'recorded-generator-input' and not any(d['target'] == edge['from'] and d['base'] == edge['to'] for d in claims):
            results.append({'glyph': edge['from'], 'base': edge['to'], 'status': 'unresolved',
                            'target_spans': [], 'reason': 'Generator input alone does not establish surviving constituent boundaries.'})
    for declaration in claims:
        if not any(declaration['id'] in r.get('declarations', []) for r in results):
            results.append({'glyph': declaration['target'], 'status': 'unresolved',
                            'declarations': [declaration['id']],
                            'target_spans': [declaration['part']['target_geometry_id']],
                            'reason': 'No distinct constituent with verified correspondence available for comparison.'})
    for name in sorted(scope):
        if not any(d['target'] == name for d in claims) and not any(r['glyph'] == name and r['status'] == 'unresolved' for r in results):
            results.append({'glyph': name, 'status': 'unresolved', 'target_spans': [],
                            'reason': 'No verified constituent correspondence supplied for this glyph.'})
    return {'format': 'myiadidot-constituent-reuse-v1', 'results': results,
            'limitations': ['Complete sampled paired spans only; erased union boundaries and partial overlaps remain unresolved.',
                            'Verified geometry supports declared intent, not historical authorship or interchangeable connection roles.',
                            'Clearance is sampled boundary distance, not a certified counter minimum.']}
