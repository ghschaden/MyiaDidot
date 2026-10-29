"""Experimental whole-arc cubic fitting; source UFOs are never written.

Constrained least squares fits sampled original geometry while penalising the
third derivative in approximate arc-length coordinates. This is a fairness
proxy, not a curvature-minimisation theorem. Explicit measurements gate trials.
"""

import math
import sys
from pathlib import Path

import numpy as np
from fontTools.misc.bezierTools import solveQuadratic

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shape_curvature as curvature
import shape_seams as seams


def samples(curves, count=161):
    points = [curvature.evaluate(curve, t/80) for curve in curves for t in range(80)] + [curves[-1][-1]]
    distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if distances[-1] < 1e-8:
        raise ValueError("Degenerate arc")
    ts = np.linspace(0, 1, count)
    return ts, np.column_stack([np.interp(ts*distances[-1], distances, np.array(points)[:, i]) for i in (0, 1)]), distances[-1]


def constrained_fit(matrix, values, constraints, targets, convex_sign=None):
    """Null-space solve: equality constraints do not compete with fit weights."""
    a, y, c, d = (np.asarray(x, dtype=float) for x in (matrix, values, constraints, targets))
    _, s, vh = np.linalg.svd(c, full_matrices=True)
    rank = sum(s > s[0]*1e-12)
    null = vh[rank:].T
    particular = np.linalg.lstsq(c, d, rcond=1e-12)[0]
    free = np.linalg.lstsq(a @ null, y-a @ particular, rcond=1e-12)[0]
    if convex_sign is not None:
        scale = max(1, np.linalg.norm(np.ptp(y[:161], axis=0))/((len(particular)-1)/3))

        def residual(z, penalty_weight):
            control = particular+null @ z.reshape(free.shape)
            errors = [(a @ control-y).ravel()]
            penalties = []
            for j in range((len(control)-1)//3):
                edges = np.diff(control[j*3:j*3+4], axis=0)
                for i, k in ((0, 1), (1, 2), (0, 2)):
                    penalties.append(min(0, convex_sign*curvature.cross(edges[i], edges[k])-1e-5*scale**2)/scale)
                lo = int(j*160/((len(control)-1)//3))
                hi = int((j+1)*160/((len(control)-1)//3))
                direction = y[hi]-y[lo]
                direction /= np.linalg.norm(direction)
                penalties.extend(min(0, np.dot(e, direction)-.03*scale) for e in edges)
            errors.append(np.array(penalties)*penalty_weight)
            return np.concatenate(errors)

        initial_a, initial_y = a.copy(), y.copy()
        initial_a[161:] *= 100
        initial_y[161:] *= 100
        z = np.linalg.lstsq(initial_a @ null, initial_y-initial_a @ particular, rcond=1e-12)[0].ravel()
        for penalty_weight in (1, 10, 100, 1000, 10000):
            damping = 1e-3
            for _ in range(60):
                r = residual(z, penalty_weight)
                eps = 1e-4
                jac = np.column_stack([(residual(z+np.eye(len(z))[i]*eps, penalty_weight)-r)/eps for i in range(len(z))])
                delta = np.linalg.solve(jac.T @ jac+damping*np.eye(len(z)), -jac.T @ r)
                candidate = z+delta
                if np.linalg.norm(residual(candidate, penalty_weight)) < np.linalg.norm(r):
                    if np.linalg.norm(delta) < 1e-6:
                        break
                    z = candidate
                    damping = max(1e-8, damping/3)
                else:
                    damping = min(1e12, damping*10)
        free = z.reshape(free.shape)
    result = particular + null @ free
    if np.max(np.abs(c @ result-d)) > 1e-6:
        raise ValueError("Inconsistent curve constraints")
    return result


def fit_arc(curves, strength, pieces=8, endpoint_curvatures=None, convex_sign=None, endpoint_tangents=None):
    """C2 chain; fixed endpoint positions, tangent directions and curvature.

    Endpoint speeds use the original arc's approximate length. Setting normal
    acceleration to k*speed² and tangential acceleration to zero gives G2 joins
    to the retained boundary, even when its parameter speed is different.
    """
    if pieces < 4 or not math.isfinite(strength) or strength < 0:
        raise ValueError("Invalid fitting parameters")
    ts, points, length = samples(curves)
    size = 3*pieces+1
    constraints, targets, matrix, values = [], [], [], []

    def equation(items, target):
        row = np.zeros(size)
        for index, value in items:
            row[index] += value
        constraints.append(row)
        targets.append(target)

    for j in range(1, pieces):
        i = 3*j
        equation([(i-1, 1), (i, -2), (i+1, 1)], (0, 0))
        equation([(i-2, 1), (i-1, -2), (i+1, 2), (i+2, -1)], (0, 0))
    for end, curve, t in ((0, curves[0], 0), (size-1, curves[-1], 1)):
        sign = 1 if t == 0 else -1
        v = np.array(curvature.evaluate(curvature.derivative(curve), t) if endpoint_tangents is None else endpoint_tangents[t])
        if np.linalg.norm(v) < 1e-8:
            raise ValueError("Stationary seam endpoint")
        direction = v/np.linalg.norm(v)
        k = curvature.curvature(curve, t) if endpoint_curvatures is None else endpoint_curvatures[t]
        acceleration = np.array([-direction[1], direction[0]])*k*length**2
        equation([(end, 1)], curve[0 if t == 0 else -1])
        equation([(end+sign, sign*3*pieces), (end, -sign*3*pieces)], direction*length)
        equation([(end, 6*pieces**2), (end+sign, -12*pieces**2), (end+2*sign, 6*pieces**2)], acceleration)
    for t, p in zip(ts, points):
        j = min(pieces-1, int(t*pieces))
        u = t*pieces-j
        row = np.zeros(size)
        row[j*3:j*3+4] = [(1-u)**3, 3*u*(1-u)**2, 3*u*u*(1-u), u**3]
        matrix.append(row)
        values.append(p)
    # Normalised derivatives: a fixed strength has comparable meaning on
    # different arc lengths. Samples and the fairness rows scale together.
    weight = math.sqrt(strength*len(ts)/pieces)
    for j in range(pieces):
        row = np.zeros(size)
        row[j*3:j*3+4] = np.array([-1, 3, -3, 1])*6*pieces**3*weight
        matrix.append(row)
        values.append((0, 0))
    controls = constrained_fit(matrix, values, constraints, targets, convex_sign)
    # Keep retained outside spans byte-for-byte in coordinate space; the linear
    # solve leaves sub-nanounit endpoint residuals that otherwise propagate.
    controls[0], controls[-1] = curves[0][0], curves[-1][-1]
    return [tuple(tuple(float(v) for v in point) for point in controls[3*j:3*j+4]) for j in range(pieces)]


def extrema_arcs(contour):
    """Split a closed oval at its four native cardinal extrema.

    Require exactly four distinct extrema. Additional extrema need a different
    optical contract, rather than a nearest-match fallback.
    """
    pieces = []
    for curve in contour:
        cubic = seams.cubic(curve)
        cuts = [0., 1.]
        for axis in (0, 1):
            p, q, r, s = [v[axis] for v in cubic]
            cuts += [float(t) for t in solveQuadratic(3*(-p+3*q-3*r+s), 6*(p-2*q+r), 3*(q-p)) if 1e-8 < t < 1-1e-8]
        cuts = sorted(set(cuts))
        pieces.extend(seams.subcurve(curve, lo, hi) for lo, hi in zip(cuts, cuts[1:]))
    # Cardinal points include existing nodes with horizontal/vertical tangents.
    extrema = []
    for i, curve in enumerate(pieces):
        v = curvature.evaluate(curvature.derivative(curve), 0)
        if min(abs(x) for x in v)/math.hypot(*v) < 1e-7:
            extrema.append(i)
    if len(extrema) != 4:
        raise ValueError(f"Expected four oval extrema, found {len(extrema)}")
    arcs = []
    for j, start in enumerate(extrema):
        end = extrema[(j+1) % 4]
        arcs.append(pieces[start:end] if end > start else pieces[start:]+pieces[:end])
    return arcs


def flat_path(contours, subdivisions=64):
    """Polygonal area diagnostics avoid unstable Boolean coincident cubics."""
    return seams.path_for([[ (curvature.evaluate(c, i/subdivisions), curvature.evaluate(c, (i+1)/subdivisions))
                             for c in contour for i in range(subdivisions)] for contour in contours])


def native_contours(font, name):
    pen = seams.ports.Segments()
    font[name].draw(pen)
    contours = {}
    for ci, _, curve in pen.segments:
        contours.setdefault(ci, []).append(tuple(curve))
    return list(contours.values())


def sections(before, after, name):
    """Measure fixed rays normal to original edges, including curve shoulders.

    New widths use the same original normals, not reoriented candidate rays.
    Ambiguous correspondence is reported, never silently matched by proximity.
    """
    import ufoLib2
    from fontTools.pens.transformPen import TransformPen
    original = native_contours(before, name)
    rows, unresolved = [], []
    for ci, contour in enumerate(original):
        for si, curve in enumerate(contour):
            for t in (.25, .5, .75):
                p = np.array(curvature.evaluate(curve, t))
                v = np.array(curvature.evaluate(curvature.derivative(curve), t), dtype=float)
                if np.linalg.norm(v) < 1e-8:
                    unresolved.append([ci, si, t, 'stationary'])
                    continue
                v /= np.linalg.norm(v)
                normal = np.array([-v[1], v[0]])
                transform = (normal[0], v[0], normal[1], v[1], -float(np.dot(normal, p)), -float(np.dot(v, p)))
                scratch = ufoLib2.Font()
                for label, font in (('before', before), ('after', after)):
                    font[name].draw(TransformPen(scratch.newGlyph(label).getPen(), transform))
                old, new = [seams.derive.stems_at(scratch, label, 0) for label in ('before', 'after')]
                hits = [i for i, (a, b) in enumerate(old) if min(abs(a), abs(b)) < .01]
                if len(hits) != 1 or len(old) != len(new):
                    unresolved.append([ci, si, t, 'interval topology'])
                    continue
                i = hits[0]
                a, b = old[i], new[i]
                if min(a[1], b[1]) <= max(a[0], b[0]):
                    unresolved.append([ci, si, t, 'nonoverlapping intervals'])
                    continue
                old_width, new_width = a[1]-a[0], b[1]-b[0]
                rows.append({'contour': ci, 'segment': si, 't': t, 'origin': p.tolist(),
                             'normal': normal.tolist(), 'before_units': old_width,
                             'after_units': new_width, 'change_percent': 100*(new_width/old_width-1)})
    return {'rays': rows, 'unresolved': unresolved,
            'max_absolute_change_percent': max(abs(r['change_percent']) for r in rows),
            'scope': 'fixed original-edge normal sections, not continuous stroke thickness'}


def measurements(before, after, name, construction, subdivisions=64):
    import pathops
    old, new = native_contours(before, name), native_contours(after, name)
    a, b = (pathops.simplify(flat_path(c, subdivisions)) for c in (old, new))
    # Unchanged spans cancel. Compare only the declared counter/arc so Skia
    # need not resolve thousands of exactly coincident polygon edges. The h
    # arc closes along the identical endpoint chord in both versions.
    if name == 'o':
        index = construction['counter_contour']
        changed_parts = [old[index]], [new[index]]
    else:
        ci, start = construction['contour'], construction['start_segment']
        changed_parts = ([old[ci][start:start+construction['replaced_segments']]],
                         [new[ci][start:start+construction['fitted_segments']]])
    part_a, part_b = [pathops.simplify(flat_path(c, subdivisions)) for c in changed_parts]
    changed = seams.derive.path_op(part_a, part_b, 'XOR').area
    union = (a.area+b.area+changed)/2
    if not 0 <= changed <= union+.01:
        raise ValueError('Invalid polygonal ink area')
    strokes = sections(before, after, name)
    # Horizontal deskewed clearance retains the original seam contract's frame.
    da, _ = seams.deskew(before, name)
    db, _ = seams.deskew(after, name)
    pa, pb = seams.path_for(da), seams.path_for(db)
    clearance_box = pa.bounds if name == 'o' else [pa.bounds[0], construction['native_blend_box'][1], pa.bounds[2], construction['native_blend_box'][3]]
    clearance = seams.clearance(pa, pb, clearance_box)
    if name == 'o':
        idx = construction['counter_contour']
        unchanged = all(old[i] == new[i] for i in range(len(old)) if i != idx)
        # Equality is numerical because deskew/slant round trips can differ.
        unchanged = unchanged or all(np.allclose(old[i], new[i], rtol=0, atol=1e-9)
                                    for i in range(len(old)) if i != idx)
        outside = 0.0 if unchanged else None
        region_difference = changed/seams.path_for([old[idx]]).area*100
        part_bounds = max(abs(x-y) for x, y in zip(seams.path_for([old[idx]]).bounds, seams.path_for([new[idx]]).bounds))
    else:
        ci, start = construction['contour'], construction['start_segment']
        old_count, new_count = construction['replaced_segments'], construction['fitted_segments']
        unchanged = (old[ci][:start] == new[ci][:start]
                     and old[ci][start+old_count:] == new[ci][start+new_count:]
                     and all(old[j] == new[j] for j in range(len(old)) if j != ci))
        outside = 0.0 if unchanged else None
        old_part, new_part = old[ci][start:start+old_count], new[ci][start:start+new_count]
        # This region is an outline arc, not a standalone filled part; a closed
        # arc's area would be an arbitrary denominator. Report whole ink only.
        region_difference = None
        part_bounds = max(abs(x-y) for x, y in zip(seams.path_for([old_part]).bounds,
                                                 seams.path_for([new_part]).bounds))
    arc_inflections = sum(a['after']['interior_inflection_count'] for a in construction['arcs'])
    result = {'ink_difference_percent': 100*changed/union, 'ink_area_change_percent': 100*(b.area/a.area-1),
              'part_difference_percent': region_difference, 'part_bounds_drift_units': part_bounds,
              'native_bounds_drift_units': max(abs(x-y) for x, y in zip(before[name].getBounds(before), after[name].getBounds(after))),
              'outside_difference_square_units': outside, 'normal_sections': strokes,
              'counter_clearance': clearance, 'fitted_interior_inflections': arc_inflections,
              'area_subdivisions_per_segment': subdivisions}
    return result


def spline_oval(font, strength=1e-8):
    if font['o'].components or len(font['o'].contours) != 2:
        raise ValueError('Oval recipe requires exactly two directly drawn contours')
    contours = native_contours(font, 'o')
    index = min(range(len(contours)), key=lambda i: seams.path_for([contours[i]]).area)
    arcs = extrema_arcs(contours[index])
    ks = [(curvature.curvature(arcs[i-1][-1], 1)+curvature.curvature(a[0], 0))/2 for i, a in enumerate(arcs)]
    fitted, reports = [], []
    for i, arc in enumerate(arcs):
        new = fit_arc(arc, strength, pieces=6, endpoint_curvatures=(ks[i], ks[(i+1)%4]), convex_sign=1)
        reports.append(curvature.comparison(arc, new))
        fitted.extend(new)
    contours[index] = fitted
    return contours, {'arcs': reports, 'counter_contour': index, 'outside_contour_unchanged': True}


def inner_shoulder(font, strength=1e-5):
    """Fit the complete two-cubic inner crown arc; retain stem and return.

    Locate the inner crown by role and topology. Refuse source changes that
    invalidate this small experimental contract instead of guessing indices.
    """
    contours = native_contours(font, 'h')
    hits = []
    for ci, contour in enumerate(contours):
        for i in range(1, len(contour)-2):
            previous, first, last, following = contour[i-1:i+3]
            if (len(previous) == 2 and len(first) == len(last) == len(following) == 4
                    and .8*font.info.xHeight < last[-1][1] < .96*font.info.xHeight
                    and last[-2][1] == last[-1][1] == following[1][1]
                    and previous[0][1] < first[0][1] < last[-1][1]):
                hits.append((ci, i))
    if len(hits) != 1:
        raise ValueError('Inner shoulder topology no longer identifies a unique arc')
    ci, start = hits[0]
    contour = contours[ci]
    old, previous, following = contour[start:start+2], contour[start-1], contour[start+2]
    ks = (curvature.curvature(previous, 1), curvature.curvature(following, 0))
    tangents = (curvature.evaluate(curvature.derivative(previous), 1), curvature.evaluate(curvature.derivative(following), 0))
    new = fit_arc(old, strength, pieces=6, endpoint_curvatures=ks, endpoint_tangents=tangents)
    bounds = seams.path_for([old]).bounds
    box = [bounds[0]-10, bounds[1]-10, bounds[2]+10, bounds[3]+10]
    new_bounds = seams.path_for([new]).bounds
    if new_bounds[0] < box[0] or new_bounds[1] < box[1] or new_bounds[2] > box[2] or new_bounds[3] > box[3]:
        raise ValueError('Fitted inner shoulder escaped its declared blend box')
    contours[ci] = contour[:start]+new+contour[start+2:]
    return contours, {'arcs': [curvature.comparison(old, new)], 'contour': ci, 'start_segment': start,
                      'replaced_segments': 2, 'fitted_segments': len(new),
                      'native_blend_box': box, 'outside_curve_spans_unchanged': True,
                      'endpoint_curvature_targets': ks, 'endpoint_tangent_targets': tangents,
                      'strength': strength}


def gates(before, after, name, construction, metrics):
    """Experimental review budgets; no production or visual acceptance."""
    old, new = native_contours(before, name), native_contours(after, name)
    if name == 'h':
        ci, start = construction['contour'], construction['start_segment']
        fitted = new[ci][start:start+construction['fitted_segments']]
        joins = curvature.audit([new[ci][start-1], *fitted, new[ci][start+len(fitted)]])['joins']
    else:
        fitted = new[construction['counter_contour']]
        joins = curvature.audit([*fitted, fitted[0]])['joins']
    failures = []
    for key, limit in (('ink_difference_percent', 2), ('native_bounds_drift_units', .01)):
        if metrics[key] > limit:
            failures.append(key)
    if metrics['outside_difference_square_units'] != 0:
        failures.append('outside spans changed')
    if name == 'o' and metrics['part_bounds_drift_units'] > .01:
        failures.append('counter extrema changed')
    if metrics['normal_sections']['max_absolute_change_percent'] > 10:
        failures.append('normal stroke section changed over 10%')
    if any(r[-1] != 'stationary' for r in metrics['normal_sections']['unresolved']):
        failures.append('normal section correspondence unresolved')
    failures.extend(metrics['counter_clearance']['failures'])
    if metrics['fitted_interior_inflections'] > (1 if name == 'h' else 0):
        failures.append('bend budget')
    if any(j['tangent_angle_degrees'] is None or j['tangent_angle_degrees'] > 1e-5
           or j['curvature_jump_inverse_units'] is None or abs(j['curvature_jump_inverse_units']) > 1e-7
           or j['position_gap_units'] > 1e-7 for j in joins):
        failures.append('G2 join')
    # Positive projection of all derivative controls on one common direction
    # proves a segment has no stationary point. Convex control polygons plus
    # those nonzero derivatives certify the oval's local bend sign.
    certificates = []
    for curve in fitted:
        edges = np.diff(curve, axis=0)
        chord = np.array(curve[-1])-curve[0]
        projection = min(float(np.dot(e, chord)/np.linalg.norm(chord)) for e in edges)
        bends = [float(curvature.cross(edges[i], edges[j])) for i, j in ((0, 1), (1, 2), (0, 2))]
        certificates.append({'minimum_forward_control_projection': projection, 'control_cross_products': bends})
        if projection <= 1e-8:
            failures.append('stationary point not excluded')
        if name == 'o' and min(bends) < -1e-8:
            failures.append('counter convexity not certified')
    import pathops
    if len(list(pathops.simplify(seams.path_for(old)).contours)) != len(list(pathops.simplify(seams.path_for(new)).contours)):
        failures.append('filled contour topology changed')
    return {'failures': sorted(set(failures)), 'joins': joins, 'segment_certificates': certificates,
            'passed': not failures, 'visual_acceptance': False}


def main():
    import argparse
    import copy
    import json
    from uuid import uuid4

    import ufoLib2

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=seams.consistency.ROOT/'build/glyph-review/bolditalic-fair-curves')
    args = parser.parse_args()
    out = seams.consistency.safe_output(args.out)
    run = out/'runs'/uuid4().hex[:12]
    run.mkdir(parents=True)
    identities = seams.consistency.source_hashes()
    implementation = {p: seams.consistency.content_hash(seams.consistency.ROOT/p) for p in
                      ('scripts/shape_fairing.py', 'scripts/shape_curvature.py', 'scripts/shape_seams.py', 'scripts/shape_ports.py')}
    engine = seams.consistency.engine_hash()
    before = ufoLib2.Font.open(seams.consistency.source_paths()['BoldItalic'], lazy=False)
    after = copy.deepcopy(before)
    operations = {}
    for name, builder in (('h', inner_shoulder), ('o', spline_oval)):
        contours, construction = builder(before)
        seams.install_scratch(after[name], contours, 0)
        operations[name] = {'construction': construction}
    for name, operation in operations.items():
        metrics = measurements(before, after, name, operation['construction'])
        # Recheck polygonal area at twice the resolution; do not treat the
        # approximation as an exact Boolean area measurement.
        refined = measurements(before, after, name, operation['construction'], subdivisions=128)
        metrics['area_resolution_difference_percentage_points'] = abs(metrics['ink_difference_percent']-refined['ink_difference_percent'])
        gate = gates(before, after, name, operation['construction'], metrics)
        if metrics['area_resolution_difference_percentage_points'] > .01:
            gate['failures'].append('area convergence')
            gate['passed'] = False
        operation.update(metrics=metrics, gate=gate)
        print(name, 'gate', gate['passed'], gate['failures'], 'ink', metrics['ink_difference_percent'], flush=True)
    impact = seams.validate_font(before, after, {'h', 'o'})
    affected = ['h', 'o', *impact['component_dependants']]
    lint_before, lint_after = [seams.glyph_lint.lint(font, affected) for font in (before, after)]
    lint_new = {n: [v for v in items if v not in lint_before.get(n, [])] for n, items in lint_after.items()}
    lint_new = {n: v for n, v in lint_new.items() if v}
    before_path, after_path = run/'before.ufo', run/'candidate.ufo'
    before.save(before_path)
    after.save(after_path)
    if json.loads(after.json_dumps()) != json.loads(ufoLib2.Font.open(after_path).json_dumps()):
        raise ValueError('Scratch save/reopen changed content')
    shaping = seams.consistency.shaping_checks(before_path, after_path, before, affected)
    proof = run/'before-after.svg'
    seams.consistency.proof_renderer()(after_path, ['h', 'o', 'n', 'm', 'u', 'hcircumflex', 'odieresis'], proof,
                                     before=before_path, texts=('hoho noon high oh', 'minimum honour home', 'h\u0301 o\u0308'),
                                     language='en', script='latn', anchors=True)
    # Italic remains a reference, never an automatic recipient of this recipe.
    reference = run/'italic-reference.svg'
    seams.consistency.proof_renderer()(seams.consistency.source_paths()['Italic'], ['h', 'o', 'n', 'm', 'u'], reference,
                                     texts=('hoho noon high oh',), language='en', script='latn')
    links = [f'<li><a href="{proof.relative_to(out)}">Bold Italic before/after, peers and shaped words</a></li>',
             f'<li><a href="{reference.relative_to(out)}">Unchanged Italic reference</a></li>']
    for name in operations:
        comb = run/f'{name}-curvature.svg'
        seams.curvature_proof(before, after, {'target': name}, comb, 'Bold Italic')
        overlay = run/f'{name}-overlay.svg'
        seams.overlay(before, after, {'target': name, 'recipe': 'whole-arc fitting', 'status': 'unaccepted', 'target_ports': []}, overlay, 'Bold Italic')
        overlay.write_text(overlay.read_text().replace('Cyan: complete ink intervals at the designed seams. Source-outline proof; no hinting.',
                                                       'Original and candidate at the same em scale. Source outlines; no hinting or visual acceptance.'))
        links.append(f'<li>{name}: <a href="{overlay.relative_to(out)}">ink comparison</a> · <a href="{comb.relative_to(out)}">curvature comb</a></li>')
    if identities != seams.consistency.source_hashes():
        raise RuntimeError('Production source bytes changed during study')
    if engine != seams.consistency.engine_hash() or any(seams.consistency.content_hash(seams.consistency.ROOT/p) != h for p, h in implementation.items()):
        raise RuntimeError('Implementation changed during study')
    result = {'format': 'myiadidot-bolditalic-fair-curves-v1', 'style': 'BoldItalic', 'operations': operations,
              'source_hashes': identities, 'sources_byte_identical': True, 'implementation_sha256': implementation,
              'engine_sha256': engine, 'impact': impact, 'shaping': shaping,
              'outline_lint': {'before': lint_before, 'after': lint_after, 'new_findings': lint_new},
              'geometry_gate_passed': all(o['gate']['passed'] for o in operations.values()) and not lint_new,
              'candidate': str(after_path.relative_to(out)), 'proof': str(proof.relative_to(out)),
              'release_ready': False, 'visual_acceptance': False,
              'limitations': ['h retains one inner-arc inflection; its outer shoulder and lower return are unchanged',
                              'Fractional scratch contours; no integer finishing, hinting or generator integration',
                              'Point metadata is reconstructed; flattened dependants are reported, not rebuilt',
                              'Normal sections and clearance are sampled; no continuous thickness guarantee']}
    seams.consistency.write_json(run/'report.json', result)
    seams.consistency.write_json(out/'report.json', result)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Bold Italic curve candidates</title>'
                                 '<style>body{font:17px system-ui;max-width:1000px;margin:2em auto}li{margin:1em}</style>'
                                 '<h1>Bold Italic h and o — curve candidates</h1>'
                                 '<p>Unaccepted scratch study. h: complete inner crown arc; o: counter only. '
                                 'Retained outside curves and metrics are protected. Curvature is continuous at fitted joins.</p>'
                                 '<p>h retains one inflection; its lower return is unchanged. Source proofs do not demonstrate hinting.</p>'
                                 '<p><a href="report.json">Full measurements, gates and source identities</a></p><ul>'+''.join(links)+'</ul>')
    print('shaping', shaping['cases'], 'new lint', lint_new, 'gate', result['geometry_gate_passed'], flush=True)


if __name__ == '__main__':
    main()
