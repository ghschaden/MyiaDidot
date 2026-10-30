"""Upper-counter roles from contour arms and shared horizontal ink bands.

Reflection is only a candidate-discovery device. Lower-return roles and terminal
semantics are discarded; all reported coordinates are in the deskewed font frame.
"""

import math

import numpy as np

from .boundaries import Sections
from .counter_scope import SCOPE_POLICY, classify_scope
from .geometry import Outline, sub
from .identity import digest
from .return_context import CONTEXT_POLICY, locate
from .returns import RETURN_POLICY, lower_returns
from .terminal_context import TERMINAL_POLICY

ARCH_POLICY = {'depth_em': .32, 'trace_step_em': .002, 'trace_limit_em': 1.2,
               'terminal_trace_depth_em': .6,
               'section_depths_em': [.12, .16, .20, .24, .28],
               'shared_tolerance_em': .003, 'minimum_shared_sections': 3}


def descending_arm(field, ci, path, crown, em, depth=None):
    poly = field.polygons[ci]
    arc = locate(poly, path[-1])
    direction = 1 if np.dot(poly.at(arc+em*.001)[0]-poly.at(arc-em*.001)[0], sub(path[-1], path[-2])) > 0 else -1
    trace = [list(p) for p in path]
    for distance in np.arange(em*.002, em*ARCH_POLICY['trace_limit_em'], em*ARCH_POLICY['trace_step_em']):
        p = poly.at(arc+direction*distance)[0].tolist()
        if p[1] > min(q[1] for q in trace)+em*.003:
            break
        trace.append(p)
        if p[1] <= crown[1]-em*(ARCH_POLICY['depth_em'] if depth is None else depth):
            break
    return trace


def horizontal_band(field, trace, heights):
    """First-hit ink intervals: topology evidence, not normal stroke widths."""
    sections = []
    for y in heights:
        hits = []
        for a, b in zip(trace, trace[1:]):
            if b[1] <= y < a[1]:
                hits.append(np.array([a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]), y]))
        if len(hits) != 1:
            sections.append(None)
            continue
        p = hits[0]
        left, right = field.ink(p+[-field.epsilon, 0]), field.ink(p+[field.epsilon, 0])
        if left == right:
            sections.append(None)
            continue
        normal = np.array([-1., 0.]) if left else np.array([1., 0.])
        hit, error = field.hit(p, normal)
        if error or not field.ink((p+hit[0])/2):
            sections.append(None)
            continue
        q = hit[0]
        back, error = field.hit(q, -normal)
        if error or np.linalg.norm(back[0]-p) > field.epsilon:
            sections.append(None)
            continue
        sections.append({'p': p.tolist(), 'q': q.tolist(), 'width': float(abs(q[0]-p[0]))})
    return sections


def shared_sections(a, b, em):
    errors = [max(abs(min(x['p'][0], x['q'][0])-min(y['p'][0], y['q'][0])),
                  abs(max(x['p'][0], x['q'][0])-max(y['p'][0], y['q'][0])))
              for x, y in zip(a, b) if x and y]
    return sum(e <= em*ARCH_POLICY['shared_tolerance_em'] for e in errors)


def reflect_terminal(context):
    """Restore every geometric coordinate from candidate reflection."""
    result = {**context, 'trace': [[x, -y] for x, y in context['trace']]}
    if context['section']:
        result['section'] = {**context['section'],
                             **{key: [context['section'][key][0], -context['section'][key][1]]
                                for key in ('p', 'q')}}
    return result


def upper_arches(contours, em, slant=0):
    contours = [[tuple((x-slant*y, y) for x, y in s) for s in c] for c in contours if c]
    reflected = [[tuple((x, -y) for x, y in s) for s in c] for c in contours]
    candidates, notes = lower_returns(reflected, [], em)
    if not contours:
        return [], notes
    field = Sections(contours, em)
    rows = []
    for candidate in candidates:
        paths = [[(x, -y) for x, y in path] for path in candidate['paths']]
        crown = (candidate['bottom'][0], -candidate['bottom'][1])
        contexts = candidate['arm_context']
        rows.append({'geometry_id': 'arch-'+digest([crown, [p[-1] for p in paths]])[:24],
                     'counter_topology': {**candidate['counter_topology'],
                                          'probe': [candidate['counter_topology']['probe'][0], -candidate['counter_topology']['probe'][1]]},
                     'contour': candidate['contour'], 'crown': crown, 'paths': paths,
                     'direction': 'upper-arch', 'role': 'unresolved',
                     'status': 'counter-observed',
                     'counter_sections': [{**s, 'y': -s['y']} for s in candidate['counter_sections']],
                     'arm_traces': [descending_arm(field, candidate['contour'], p, crown, em) for p in paths],
                     'terminal_caps': [c['cap_status'] == 'short-contour-cap' for c in contexts],
                     'cap_traces': [[(x, -y) for x, y in c['cap_trace']] if c['cap_status'] == 'short-contour-cap' else [] for c in contexts],
                     'terminal_context': [reflect_terminal(c['terminal_context']) for c in contexts],
                     'local_band_status': [c['status'] for c in contexts],
                     'neighbours': [[], []]})
    rows.sort(key=lambda r: r['crown'][0])
    # Every link has its own common height window: unrelated tall glyph regions
    # cannot move the sample band. Multiple neighbours remain explicit ambiguity.
    for a in rows:
        for b in rows:
            if (a['counter_topology']['kind'] == 'closed-counter'
                    or b['counter_topology']['kind'] == 'closed-counter'
                    or a['crown'][0] >= b['crown'][0]):
                continue
            heights = [min(a['crown'][1], b['crown'][1])-em*d for d in ARCH_POLICY['section_depths_em']]
            sa = horizontal_band(field, a['arm_traces'][1], heights)
            sb = horizontal_band(field, b['arm_traces'][0], heights)
            count = shared_sections(sa, sb, em)
            if count >= ARCH_POLICY['minimum_shared_sections']:
                for row, side, peer in [(a, 1, b), (b, 0, a)]:
                    row['neighbours'][side].append({'geometry_id': peer['geometry_id'], 'shared_sections': count,
                                                   'sections': sa if row is a else sb})
    for row in rows:
        left, right = row['neighbours']
        cap_left, cap_right = row['terminal_caps']
        # Entry and interior are positive local contexts. Exit requires an
        # independent lower terminal observation, supplied by the report layer.
        if len(left) > 1 or len(right) > 1:
            row['reason'] = 'Competing shared-stem neighbours.'
        elif cap_left and len(right) == 1:
            row.update(role='entry', reason='Left contour closes through a short cap; right arm shares an ink band with the next arch.')
        elif len(left) == len(right) == 1 and not cap_left and not cap_right:
            row.update(role='interior', reason='Both arms share verified ink intervals with distinct adjoining arches.')
        else:
            row['reason'] = 'Incomplete neighbour or terminal evidence; graph position alone does not establish an exit.'
    conflicts = terminal_links(contours, rows, em)
    for row in rows:
        classify_scope(row, row['role'] != 'unresolved' or all(row['neighbours']), [cap or c['status'] == 'verified-contour-terminal'
                        for cap, c in zip(row['terminal_caps'], row['terminal_context'])])
        row['conflicts'] = [c for c in conflicts if c['arch'] == row['geometry_id']]
    return rows, [{**n, 'bottom': (n['bottom'][0], -n['bottom'][1])} if 'bottom' in n else n for n in notes]


def arch_report(font, report, names):
    em = font.info.unitsPerEm
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    results, omissions = [], []
    for name in sorted(names):
        outline = Outline()
        font[name].draw(outline)
        rows, notes = upper_arches(outline.contours, em, slant)
        for row in rows:
            row.update(glyph=name, source_sha256=report['source_identity'])
            row['geometry_id'] = 'arch-'+digest([name, row['geometry_id']])[:24]
            for conflict in row['conflicts']:
                for key in ('arch', 'following_arch'):
                    conflict[key] = 'arch-'+digest([name, conflict[key]])[:24]
            for neighbours in row['neighbours']:
                for neighbour in neighbours:
                    neighbour['geometry_id'] = 'arch-'+digest([name, neighbour['geometry_id']])[:24]
        results.extend(rows)
        omissions.extend({'glyph': name, **note} for note in notes)
        if not rows:
            omissions.append({'glyph': name, 'reason': 'No upper-counter candidate; absence is not proof of no arch.'})
    return {'format': 'myiadidot-upper-arches-v2', 'policy': ARCH_POLICY, 'candidate_policy': RETURN_POLICY,
            'cap_policy': CONTEXT_POLICY, 'scope_policy': SCOPE_POLICY, 'terminal_policy': TERMINAL_POLICY, 'results': results,
            'omissions': omissions, 'scope': sorted(names),
            'limitations': ['Horizontal ink intervals establish local shared-stem topology, not normal width compatibility or ancestry.',
                            'Open-counter pilot; components, tail attribution and independent real-family accuracy remain unsupported.']}


def terminal_links(contours, rows, em):
    """Link a lower counter turn to an upper arm by common ink intervals."""
    turns, _ = lower_returns(contours, [], em)
    if not contours:
        return []
    field = Sections(contours, em)
    reflected = [[tuple((x, -y) for x, y in s) for s in c] for c in contours]
    reverse_field = Sections(reflected, em)
    findings = []
    for turn in turns:
        if turn['counter_topology']['kind'] == 'closed-counter':
            continue
        capped = turn['arm_context'][1]['cap_status'] == 'short-contour-cap'
        path = [(x, -y) for x, y in turn['paths'][0]]
        trace = descending_arm(reverse_field, turn['contour'], path, (turn['bottom'][0], -turn['bottom'][1]), em, depth=ARCH_POLICY['terminal_trace_depth_em'])
        rising = [(x, -y) for x, y in trace]
        heights = [turn['bottom'][1]+em*d for d in ARCH_POLICY['section_depths_em']]
        # horizontal_band accepts descending paths; reverse the rising trace.
        lower_sections = horizontal_band(field, list(reversed(rising)), heights)
        matches = []
        for row in rows:
            if row['counter_topology']['kind'] == 'closed-counter':
                continue
            upper_trace = descending_arm(field, row['contour'], row['paths'][1], row['crown'], em, depth=ARCH_POLICY['terminal_trace_depth_em'])
            upper_sections = horizontal_band(field, upper_trace, heights)
            count = shared_sections(upper_sections, lower_sections, em)
            if count >= ARCH_POLICY['minimum_shared_sections']:
                matches.append((row, count, upper_sections))
        if len(matches) != 1:
            continue
        row, count, sections = matches[0]
        row.setdefault('lower_terminals', []).append({'bottom': turn['bottom'], 'shared_sections': count,
            'sections': sections, 'cap_trace': turn['arm_context'][1]['cap_trace'],
            'cap_verified': capped, 'below_floor_context': turn['arm_context'][1]['below_floor_context'], 'lower_role': turn['role'], 'scope': 'Terminal morphology and shared ink band only; lower-return width support is separate.'})
        if len(row['neighbours'][1]) == 1:
            findings.append({'kind': 'interior-terminal-conflict' if capped else 'interior-return-detour', 'arch': row['geometry_id'],
                'following_arch': row['neighbours'][1][0]['geometry_id'],
                'terminal_bottom': turn['bottom'], 'shared_sections': count,
                'reason': 'The stem feeding a following upper arch also feeds a lower counter return. A terminal-like detour occupies an interior connection; inspect for intentional construction.',
                'decision': 'review-conflict'})
        elif (capped and not row['neighbours'][1] and len(row['neighbours'][0]) == 1
              and turn['arm_context'][1]['below_floor_context'] == 'not-observed'):
            row.update(role='exit', reason='Left arm shares the preceding stem; right arm shares an ink band with a lower capped terminal.')
    return findings
