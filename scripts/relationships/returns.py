"""Lower counter turns and their observed paired-stroke neighbours.

This pilot locates open counter floors, not reusable outlines. Missing neighbours
and terminal/tail context stay unresolved; an end of the observed graph is not a
proof that the glyph has an exit role.
"""

import math

from .boundaries import Polygon, Sections
from .counter_scope import SCOPE_POLICY, classify_scope, counter_topology
from .geometry import angle, length, sub
from .identity import digest
from .return_context import CONTEXT_POLICY, arm_context, resolve_context
from .return_matching import match_returns
from .terminal_context import TERMINAL_POLICY

RETURN_POLICY = {'rise_em': .08, 'minimum_opening_em': .015,
                 'maximum_backtrack_em': .003, 'neighbour_distance_em': .06,
                 'minimum_stem_length_em': .10, 'corner_degrees': 25.0}


def lower_returns(contours, pairs, em, slant=0):
    contours = [[tuple((x-slant*y, y) for x, y in s) for s in c] for c in contours if c]
    if not contours:
        return [], [{'reason': 'No own closed contours; component ancestry is not expanded.'}]
    field = Sections(contours, em)
    rows, notes = [], []
    for ci, contour in enumerate(contours):
        poly = Polygon(contour, em)
        points = [tuple(p) for p in poly.points]
        count = len(points)
        for i, p in enumerate(points):
            if points[(i-1) % count][1] <= p[1]+1e-7:
                continue
            j = i
            while j-i < count and abs(points[(j+1) % count][1]-p[1]) <= 1e-7:
                j += 1
            if j-i >= count or points[(j+1) % count][1] <= p[1]+1e-7:
                continue
            q = points[j % count]
            bottom = ((p[0]+q[0])/2, p[1])
            probe = em*.001
            if field.ink((bottom[0], bottom[1]+probe)) or not field.ink((bottom[0], bottom[1]-probe)):
                continue  # Outer bottom, closed contour exterior, or ambiguous ink.
            paths = []
            for start, direction in [(i, -1), (j % count, 1)]:
                path = [points[start]]
                for k in range(1, count):
                    a, b = path[-1], points[(start+direction*k) % count]
                    if b[1] < a[1]-em*RETURN_POLICY['maximum_backtrack_em']:
                        break
                    if b[1] >= bottom[1]+em*RETURN_POLICY['rise_em']:
                        t = (bottom[1]+em*RETURN_POLICY['rise_em']-a[1])/(b[1]-a[1])
                        path.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
                        paths.append(path)
                        break
                    path.append(b)
            if len(paths) != 2:
                notes.append({'contour': ci, 'bottom': bottom, 'reason': 'Turn does not reach both observation shoulders.'})
                continue
            paths.sort(key=lambda path: path[-1][0])
            left, right = paths
            opening = right[-1][0]-left[-1][0]
            bend = angle(sub(p, points[(i-1) % count]), sub(points[(j+1) % count], q)) if i == j else max(
                angle(sub(p, points[(i-1) % count]), sub(q, p)),
                angle(sub(q, p), sub(points[(j+1) % count], q)))
            if bend > RETURN_POLICY['corner_degrees']:
                notes.append({'contour': ci, 'bottom': bottom, 'reason': 'Angular lower junction; rounded-return role withheld.'})
                continue
            if opening < em*RETURN_POLICY['minimum_opening_em']:
                notes.append({'contour': ci, 'bottom': bottom, 'reason': 'Counter opening too narrow or arms reversed.'})
                continue
            # Measure clear horizontal intervals between the two ascending arms.
            def at_height(path, y):
                for a, b in zip(path, path[1:]):
                    if a[1] <= y <= b[1] and b[1] > a[1]:
                        t = (y-a[1])/(b[1]-a[1])
                        return a[0]+t*(b[0]-a[0])
                return None
            sections = []
            for k in range(1, 9):
                y = bottom[1]+em*RETURN_POLICY['rise_em']*k/8
                x0, x1 = at_height(left, y), at_height(right, y)
                if x0 is None or x1 is None or x1 <= x0 or any(field.ink((x0+(x1-x0)*t/10, y)) for t in range(1, 10)):
                    break
                sections.append({'y': y, 'left': x0, 'right': x1, 'clearance_units': x1-x0})
            if len(sections) != 8:
                notes.append({'contour': ci, 'bottom': bottom, 'reason': 'Counter cross-sections interrupted or ambiguous.'})
                continue
            neighbours = []
            for path in paths:
                endpoint = path[-1]
                candidates = []
                for pair in pairs:
                    if pair['length_em'] < RETURN_POLICY['minimum_stem_length_em']:
                        continue
                    center = pair['centerline']
                    dx, dy = sub(center[-1], center[0])
                    if abs(dy) < abs(dx)*2:
                        continue
                    distance = min(length(sub(endpoint, p)) for edge in pair['edges'] for p in edge)
                    if distance <= em*RETURN_POLICY['neighbour_distance_em']:
                        candidates.append({'geometry_id': pair['geometry_id'], 'distance_units': distance})
                neighbours.append(sorted(candidates, key=lambda c: (c['distance_units'], c['geometry_id'])))
            supported = all(len(n) == 1 for n in neighbours) and neighbours[0][0]['geometry_id'] != neighbours[1][0]['geometry_id']
            geometry = {'bottom': [round(v, 6) for v in bottom], 'shoulders': [[round(v, 6) for v in path[-1]] for path in paths]}
            rows.append({'geometry_id': 'turn-'+digest(geometry)[:24], 'contour': ci,
                         'counter_topology': counter_topology(field, ci, bottom, em),
                         'arm_context': [arm_context(field, ci, path, bottom, em) for path in paths],
                         'bottom': bottom, 'paths': paths, 'direction': 'lower-return',
                         'status': 'supported-local-turn' if supported else 'unresolved',
                         'role': 'unresolved', 'neighbours': neighbours, 'counter_sections': sections,
                         'opening_units': opening,
                         'attachment_directions': [list(sub(path[-1], path[-2])) for path in paths],
                         'reason': 'Both observed stroke neighbours are unique; terminal and tail context remains unverified.' if supported else 'Missing or competing paired-stroke neighbours; no complete connection graph.'})
    for row in rows:
        if row['counter_topology']['kind'] == 'closed-counter':
            row['status'] = 'counter-observed'
            row['reason'] = row['counter_topology']['reason']
    rows.sort(key=lambda r: (r['bottom'][0], r['bottom'][1]))
    for row in rows:
        if row['status'] != 'supported-local-turn':
            continue
        right = row['neighbours'][1][0]['geometry_id']
        following = [r for r in rows if r is not row and r['status'] == 'supported-local-turn'
                     and r['bottom'][0] > row['bottom'][0] and r['neighbours'][0][0]['geometry_id'] == right]
        if len(following) == 1:
            row['role'] = 'interior'
            row['next_turn'] = following[0]['geometry_id']
            row['reason'] = 'The right observed stroke also supports the next lower return.'
    resolve_context(rows, em)
    for row in rows:
        classify_scope(row, row['status'] == 'supported-local-turn',
                       [c['cap_status'] == 'short-contour-cap' or c['terminal_context']['status'] == 'verified-contour-terminal'
                        for c in row['arm_context']])
    return rows, notes


def return_report(font, report, names):
    from .geometry import Outline
    em = font.info.unitsPerEm
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    results, omissions = [], []
    for name in sorted(names):
        outline = Outline()
        font[name].draw(outline)
        pairs = [r for r in report['relationships'] if r['glyph'] == name
                 and r['relationship'] == 'paired-stroke-boundaries' and r['identity_status'] == 'unique']
        rows, notes = lower_returns(outline.contours, pairs, em, slant)
        for row in rows:
            row.update(glyph=name, source_sha256=report['source_identity'])
            row['geometry_id'] = 'turn-'+digest([name, row['geometry_id']])[:24]
        # Resolve graph references after glyph-scoping identities.
        for row in rows:
            if 'next_turn' in row:
                row['next_turn'] = 'turn-'+digest([name, row['next_turn']])[:24]
        results.extend(rows)
        omissions.extend({'glyph': name, **note} for note in notes)
        if not rows:
            omissions.append({'glyph': name, 'reason': 'No supported lower-counter candidate found; absence is not proof of no return.'})
    return {'format': 'myiadidot-lower-returns-v3', 'policy': RETURN_POLICY, 'context_policy': CONTEXT_POLICY, 'scope_policy': SCOPE_POLICY, 'terminal_policy': TERMINAL_POLICY,
            'scope': sorted(names), 'results': results, 'omissions': omissions,
            'matches': match_returns(results, em, font.info.styleName),
            'limitations': ['Source-outline pilot; no repair, design acceptance or verified base inheritance.',
                           'Exit requires supported local bands and a traced short cap; below-floor context withholds exit, without proving tail attachment.',
                           'Counter clearance is sampled over a fixed lower window, not the whole counter.',
                           'Components are not expanded. Missing paired stems prevent a complete graph.']}
