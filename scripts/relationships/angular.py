"""Separate angular counter-boundary observation; no branch or terminal roles."""

import math

from .arches import reflect_terminal
from .boundaries import Sections
from .counter_scope import counter_topology
from .identity import digest
from .observation import observed_outline
from .returns import RETURN_POLICY, lower_returns
from .terminal_context import reciprocal_terminal_context
from .terminal_context import terminal_policy as resolve_terminal_policy

ANGULAR_POLICY = {'seed': 'inward extremum exceeding the rounded-turn bend limit',
                  'minimum_bend_degrees_exclusive': RETURN_POLICY['corner_degrees'],
                  'rise_em': RETURN_POLICY['rise_em'],
                  'maximum_backtrack_em': RETURN_POLICY['maximum_backtrack_em'],
                  'backtrack_reference': 'maximum rise reached by this arm',
                  'minimum_opening_em': RETURN_POLICY['minimum_opening_em'],
                  'clearance_sections': 8, 'interior_samples_per_section': 9,
                  'terminal_evidence': 'not-evaluated', 'use_for_roles': False}


def bounded_arm(arm, floor, em):
    """Stop cumulative reversal before following another lobe or remote exit."""
    path, high = [], floor
    for point in arm['path']:
        if point[1] < high-em*ANGULAR_POLICY['maximum_backtrack_em']:
            return {**arm, 'path': path, 'reaches_window': False,
                    'achieved_rise_em': (high-floor)/em, 'stop': 'cumulative-backtrack'}
        path.append(point)
        high = max(high, point[1])
    return {**arm, 'path': path}


def at_height(path, y):
    for a, b in zip(path, path[1:]):
        if a[1] <= y <= b[1] and b[1] > a[1]:
            return a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])
    return None


def angular_terminal_context(field, ci, arm, em, policy):
    """Use the traced occurrence and direction, without projecting to a peer."""
    distance = sum(math.hypot(b[0]-a[0], b[1]-a[1])
                   for a, b in zip(arm['path'], arm['path'][1:]))
    arc = arm['start_arc_units']+arm['source_direction']*distance
    shoulder = field.polygons[ci].at(arc)[0]
    if math.hypot(*(shoulder-arm['path'][-1])) > em*1e-7:
        return withheld_terminal('Traced shoulder does not agree with its source arc occurrence.')
    return reciprocal_terminal_context(field, ci, arc, arm['source_direction'], em, policy)


def withheld_terminal(reason):
    return {'status': 'not-evaluated', 'reason': reason, 'section': None,
            'trace': [], 'window_checks': {}}


def angular_observations(contours, em, slant=0, *, terminal_policy=None):
    """Keep angular seeds and partial arms outside rounded-return results.

    Measurements use the same fixed shoulders and sampled white intervals as
    returns. Reflection discovers upper seeds only; all output is restored to
    the deskewed font frame. Visible arms do not establish anatomical branching.
    """
    if terminal_policy is not None:
        resolve_terminal_policy(terminal_policy)
    if not math.isfinite(em) or em <= 0 or not math.isfinite(slant):
        raise ValueError('Invalid angular observation coordinate frame')
    deskewed = [[tuple((x-slant*y, y) for x, y in s) for s in c] for c in contours if c]
    if not deskewed:
        return []
    results = []
    for detector, sign in [('lower_returns', 1), ('upper_arches', -1)]:
        framed = [[tuple((x, sign*y) for x, y in s) for s in c] for c in deskewed]
        traces = []
        lower_returns(framed, [], em, diagnostics=traces)
        field = Sections(framed, em)
        for seed in traces:
            bend = seed['measurements'].get('bend_degrees')
            if bend is None or bend <= ANGULAR_POLICY['minimum_bend_degrees_exclusive']:
                continue
            point = seed['point']
            arms = sorted([bounded_arm(a, point[1], em) for a in seed['arms']],
                          key=lambda a: a['path'][-1][0])
            sections, failure = [], None
            for k in range(1, ANGULAR_POLICY['clearance_sections']+1):
                y = point[1]+em*ANGULAR_POLICY['rise_em']*k/ANGULAR_POLICY['clearance_sections']
                left, right = [at_height(a['path'], y) for a in arms]
                if left is None or right is None:
                    failure = 'arm-window-unavailable'
                    break
                if right <= left:
                    failure = 'reversed-or-coincident-arms'
                    break
                if any(field.ink((left+(right-left)*t/10, y)) for t in range(1, 10)):
                    failure = 'interrupted-clearance'
                    break
                sections.append({'y': sign*y, 'left': left, 'right': right,
                                 'clearance_units': right-left})
            complete = all(a['reaches_window'] for a in arms)
            if not complete:
                reason = 'One or both arms stop before the fixed observation window; partial paths retained.'
            elif failure:
                reason = 'Both arms reach the window, but counter sections are incomplete: '+failure+'.'
            elif sections[-1]['clearance_units'] < em*ANGULAR_POLICY['minimum_opening_em']:
                failure = 'narrow-opening'
                reason = 'Observed opening is below the fixed minimum.'
            else:
                reason = 'Two angular boundary arms reach the fixed window with sampled clear intervals; branch anatomy remains unqualified.'
            topology = counter_topology(field, seed['contour'], point, em)
            topology['probe'][1] *= sign
            restored_arms = [{**a, 'path': [(x, sign*y) for x, y in a['path']]} for a in arms]
            geometry = {'point': [point[0], sign*point[1]],
                        'paths': [a['path'] for a in restored_arms]}
            row = {'geometry_id': 'angular-'+digest([detector, geometry])[:24],
                            'seed_detector': detector, 'contour': seed['contour'],
                            **geometry, 'arms': restored_arms, 'bend_degrees': bend,
                            'counter_topology': topology, 'counter_sections': sections,
                            'clearance_failure': failure,
                            'status': 'visible-angular-arms' if complete and failure is None else 'unresolved',
                            'role': 'unresolved', 'terminal_evidence': 'not-evaluated',
                            'reason': reason}
            if terminal_policy is not None:
                eligible = row['status'] == 'visible-angular-arms'
                contexts = ([angular_terminal_context(field, seed['contour'], a, em, terminal_policy) for a in arms]
                            if eligible else [withheld_terminal('Incomplete angular arm window or counter clearance.') for _ in arms])
                row['terminal_context'] = [reflect_terminal(c) if sign == -1 else c for c in contexts]
                row['terminal_evidence'] = ('withheld-incomplete-window' if not eligible else
                                            'withheld-source-occurrence' if any(c['status'] == 'not-evaluated' for c in contexts) else
                                            'reciprocal-closure-evaluated')
            results.append(row)
    return results


def angular_report(font, report, names, *, terminal_policy=None):
    selected_terminal_policy = resolve_terminal_policy(terminal_policy) if terminal_policy is not None else None
    em = font.info.unitsPerEm
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    names = sorted(set(names))
    results, observations, omissions = [], {}, []
    for name in names:
        outline = observed_outline(font, name, report['source_identity'])
        observations[name] = {k: v for k, v in outline.items() if k != 'contours'}
        omissions.extend({'glyph': name, **issue} for issue in outline['issues'])
        rows = angular_observations(outline['contours'], em, slant, terminal_policy=terminal_policy)
        for row in rows:
            row.update(glyph=name, source_sha256=report['source_identity'],
                       contour_origin=outline['origins'][row['contour']])
            row['geometry_id'] = 'angular-'+digest([name, row['geometry_id'], row['contour_origin']])[:24]
        results.extend(rows)
        if not rows:
            omissions.append({'glyph': name, 'reason': 'No angular inward seed observed; absence is not anatomical classification.'})
    result = {'format': 'myiadidot-angular-observations-v2' if selected_terminal_policy else 'myiadidot-angular-observations-v1', 'source_sha256': report['source_identity'],
            'policy': dict(ANGULAR_POLICY), 'scope': names, 'results': results,
            'observations': observations, 'omissions': omissions,
            'limitations': ['Separate angular-boundary scope, not accepted rounded-return relationships.',
                            'Partial arms and sampled clearance do not establish normal stroke support, branch anatomy or ancestry.',
                            'Terminal closure is local morphology only; no attachment role, repair or design acceptance is inferred.' if selected_terminal_policy else
                            'No terminal closure, attachment role, repair or design acceptance is inferred.',
                            'Component geometry retains provenance without Boolean union.']}

    if selected_terminal_policy:
        result['terminal_policy'] = selected_terminal_policy
        result['policy']['terminal_evidence'] = 'reciprocal-closure-on-visible-arms'
    return result
