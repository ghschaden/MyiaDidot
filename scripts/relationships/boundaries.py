"""Conservative normal-section pairing on unbranched outline spans.

Measurements are in the deskewed design frame. Rays stop at the first boundary;
white-space crossings, ambiguous ink sides and failed reverse correspondence are
never accepted as stroke sections. Polyline approximation is explicit.
"""

import math
from collections import Counter, defaultdict

import numpy as np

from .geometry import POLICY, angle, flatten, length, sub

BOUNDARY_POLICY = {
    'flatten_em': 0.00005, 'sample_step_em': 0.008,
    'tangent_window_em': 0.003, 'ink_probe_em': 0.00015,
    'minimum_width_em': 0.003, 'maximum_width_em': 0.30,
    'parallel_degrees': 12.0, 'corner_degrees': 18.0,
    'reciprocal_width_fraction': 0.12, 'reciprocal_floor_em': 0.001,
    'maximum_width_gradient': 0.35, 'maximum_turn_degrees': 30.0,
    'minimum_run_em': 0.06, 'minimum_sections': 5, 'minimum_aspect_ratio': 1.5,
}


class Polygon:
    def __init__(self, segments, em):
        points, owners = [], []
        for index, segment in enumerate(segments):
            part = flatten(segment, em*BOUNDARY_POLICY['flatten_em'])
            for a, b in zip(part, part[1:]):
                if length(sub(b, a)) > 1e-9:
                    points.append(a)
                    owners.append(index)
        self.points = np.asarray(points, float)
        self.owners = owners
        self.ends = np.roll(self.points, -1, axis=0)
        self.vectors = self.ends-self.points
        self.lengths = np.linalg.norm(self.vectors, axis=1)
        self.starts = np.concatenate([[0.0], np.cumsum(self.lengths)])
        self.perimeter = float(self.starts[-1])

    def at(self, distance):
        distance %= self.perimeter
        k = min(len(self.points)-1, int(np.searchsorted(self.starts, distance, side='right')-1))
        t = (distance-self.starts[k])/self.lengths[k]
        return self.points[k]+self.vectors[k]*t, k

    def tangent(self, distance, window):
        p, _ = self.at(distance)
        before, _ = self.at(distance-window)
        after, _ = self.at(distance+window)
        a, b = p-before, after-p
        if angle(a, b) > BOUNDARY_POLICY['corner_degrees']:
            return None
        d = after-before
        norm = np.linalg.norm(d)
        return d/norm if norm > 1e-9 else None

    def samples(self, em):
        # Start phase at an intrinsic geometric vertex, not the UFO's contour start.
        k = min(range(len(self.points)), key=lambda i: tuple(self.points[i]))
        count = max(4, math.ceil(self.perimeter/(em*BOUNDARY_POLICY['sample_step_em'])))
        return [(float(self.starts[k]+(i+.5)*self.perimeter/count) % self.perimeter) for i in range(count)]


def cross(a, b):
    return a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]


class Sections:
    def __init__(self, contours, em):
        self.em = em
        self.polygons = [Polygon(c, em) for c in contours]
        self.a = np.concatenate([p.points for p in self.polygons])
        self.b = np.concatenate([p.ends for p in self.polygons])
        self.v = self.b-self.a
        self.contour = np.concatenate([np.full(len(p.points), i, int) for i, p in enumerate(self.polygons)])
        self.edge = np.concatenate([np.arange(len(p.points)) for p in self.polygons])
        self.epsilon = em*BOUNDARY_POLICY['ink_probe_em']

    def ink(self, p):
        d = cross(self.v, p-self.a)
        up = (self.a[:, 1] <= p[1]) & (self.b[:, 1] > p[1]) & (d > 0)
        down = (self.b[:, 1] <= p[1]) & (self.a[:, 1] > p[1]) & (d < 0)
        return int(np.count_nonzero(up))-int(np.count_nonzero(down)) != 0

    def inward(self, p, tangent):
        n = np.array([-tangent[1], tangent[0]])
        left, right = self.ink(p+self.epsilon*n), self.ink(p-self.epsilon*n)
        if left == right:
            return None
        return n if left else -n

    def hit(self, p, normal):
        den = cross(normal, self.v)
        valid = np.abs(den) > 1e-10
        distance = np.divide(cross(self.a-p, self.v), den, out=np.full(len(den), np.inf), where=valid)
        u = np.divide(cross(self.a-p, normal), den, out=np.full(len(den), np.inf), where=valid)
        valid &= (distance > self.epsilon) & (u >= -1e-8) & (u <= 1+1e-8)
        indices = np.flatnonzero(valid)
        if not len(indices):
            return None, 'no opposite boundary'
        best = indices[np.argmin(distance[indices])]
        tied = indices[np.abs(distance[indices]-distance[best]) < self.epsilon]
        if len(set(self.contour[tied])) != 1:
            return None, 'coincident boundaries'
        ci, edge = int(self.contour[best]), int(self.edge[best])
        poly = self.polygons[ci]
        s = float(poly.starts[edge]+np.clip(u[best], 0, 1)*poly.lengths[edge])
        return (p+distance[best]*normal, ci, s, float(distance[best])), None

    def section(self, ci, s):
        poly = self.polygons[ci]
        p, edge = poly.at(s)
        window = self.em*BOUNDARY_POLICY['tangent_window_em']
        tangent = poly.tangent(s, window)
        if tangent is None:
            return None, 'corner or degenerate tangent'
        normal = self.inward(p, tangent)
        if normal is None:
            return None, 'no unique inward side'
        hit, error = self.hit(p, normal)
        if error:
            return None, error
        q, cj, t, width = hit
        if not self.em*BOUNDARY_POLICY['minimum_width_em'] <= width <= self.em*BOUNDARY_POLICY['maximum_width_em']:
            return None, 'width outside supported range'
        other = self.polygons[cj].tangent(t, window)
        if other is None:
            return None, 'opposite corner'
        parallel = min(angle(tangent, other), angle(tangent, -other))
        if parallel > BOUNDARY_POLICY['parallel_degrees']:
            return None, 'nonparallel boundaries or junction'
        back_normal = self.inward(q, other)
        if back_normal is None:
            return None, 'ambiguous opposite ink side'
        back, error = self.hit(q, back_normal)
        if error:
            return None, 'reverse '+error
        p2, ck, _, reverse_width = back
        reciprocal = float(np.linalg.norm(p2-p))
        tolerance = max(self.em*BOUNDARY_POLICY['reciprocal_floor_em'], width*BOUNDARY_POLICY['reciprocal_width_fraction'])
        if ck != ci or reciprocal > tolerance or abs(width-reverse_width) > width*.05:
            return None, 'reverse correspondence failed'
        if not self.ink((p+q)/2):
            return None, 'section crosses white space'
        return {'p': p.tolist(), 'q': q.tolist(), 'width': width,
                'reverse_width': reverse_width, 'reciprocal_error': reciprocal,
                'source_contour': ci, 'source_segment': poly.owners[edge],
                'target_contour': cj, 'target_segment': self.polygons[cj].owners[self.polygons[cj].at(t)[1]],
                'source_arc': s, 'target_arc': t, 'tangent': tangent.tolist()}, None


def run_record(sections, em):
    centers = np.array([(np.array(s['p'])+s['q'])/2 for s in sections])
    lengths = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    distance = np.concatenate([[0], np.cumsum(lengths)])
    widths = np.array([s['width'] for s in sections])
    slope, intercept = np.polyfit(distance, widths, 1)
    residual = widths-(slope*distance+intercept)
    direction = centers[-1]-centers[0]
    degrees = math.degrees(math.atan2(direction[1], direction[0])) % 180
    axis = 'vertical' if abs(degrees-90) < 15 else 'horizontal' if min(degrees, 180-degrees) < 15 else 'oblique'
    profile = np.interp(np.linspace(0, distance[-1], 17), distance, widths)/em
    return {'relationship': 'paired-stroke-boundaries', 'evidence': 'bidirectional-ink-sections',
            'status': 'paired', 'family': 'paired-stroke/'+axis, 'sections': sections,
            'edges': [[s['p'] for s in sections], [s['q'] for s in sections]],
            'centerline': centers.tolist(), 'length_em': float(distance[-1]/em),
            'metrics': {'minimum_width_em': float(widths.min()/em), 'median_width_em': float(np.median(widths)/em),
                        'maximum_width_em': float(widths.max()/em), 'linear_taper': float(slope),
                        'width_residual_rms_em': float(np.sqrt(np.mean(residual**2))/em),
                        'maximum_width_gradient': float(np.max(np.abs(np.diff(widths)/lengths))),
                        'maximum_reciprocal_error_em': max(s['reciprocal_error'] for s in sections)/em,
                        'width_profile_em': profile.tolist()},
            'explanation': 'Opposite ink boundaries agree under forward and reverse normal sections over a coherent unbranched span. Width variation is measured, not judged aesthetically.'}


def paired_boundaries(contours, em, slant=0):
    transformed = [[tuple((x-slant*y, y) for x, y in s) for s in c] for c in contours]
    kept = [(i, c) for i, c in enumerate(transformed) if sum(sum(length(sub(b, a)) for a, b in zip(s, s[1:])) for s in c) > 1e-9]
    original_indices = [i for i, _ in kept]
    usable = [c for _, c in kept]
    if not usable:
        return [], []
    engine = Sections(usable, em)
    rows, notes = [], []
    for ci, poly in enumerate(engine.polygons):
        rejected, examples = Counter(), defaultdict(list)
        runs, current = [], []
        samples = poly.samples(em)
        for s in samples:
            section, reason = engine.section(ci, s)
            if section and current:
                prev = current[-1]
                center = (np.array(section['p'])+section['q'])/2
                old_center = (np.array(prev['p'])+prev['q'])/2
                travel = float(np.linalg.norm(center-old_center))
                target_length = engine.polygons[section['target_contour']].perimeter
                target_delta = abs(section['target_arc']-prev['target_arc'])
                target_delta = min(target_delta, target_length-target_delta)
                if section['target_contour'] != prev['target_contour'] or target_delta > em*.03+3*poly.perimeter/len(samples):
                    reason = 'partner jump at a possible branch'
                elif travel < 1e-8 or abs(section['width']-prev['width'])/travel > BOUNDARY_POLICY['maximum_width_gradient']:
                    reason = 'abrupt width change at a possible branch'
                elif min(angle(current[0]['tangent'], section['tangent']), angle(current[0]['tangent'], -np.array(section['tangent']))) > BOUNDARY_POLICY['maximum_turn_degrees']:
                    reason = 'turn exceeds supported gentle span'
            if reason:
                if current:
                    runs.append(current); current = []
                rejected[reason] += 1
                if len(examples[reason]) < 3:
                    examples[reason].append(poly.at(s)[0].tolist())
                continue
            current.append(section)
        if current:
            runs.append(current)
        for run in runs:
            if len(run) < BOUNDARY_POLICY['minimum_sections']:
                rejected['insufficient supported sections'] += len(run)
                continue
            record = run_record(run, em)
            if record['length_em'] < BOUNDARY_POLICY['minimum_run_em']:
                rejected['supported span too short'] += len(run)
                continue
            if record['length_em'] < BOUNDARY_POLICY['minimum_aspect_ratio']*record['metrics']['median_width_em']:
                rejected['insufficient longitudinal support for this width'] += len(run)
                continue
            rows.append(record)
        notes.extend({'relationship': 'paired-stroke-boundaries', 'contour': ci, 'reason': reason,
                      'sample_count': count, 'example_positions': examples[reason]}
                     for reason, count in sorted(rejected.items()))
    # The same ribbon is observed from both sides. Collapse only substantial
    # mutual centerline coverage; keep distinct/partially overlapping spans explicit.
    unique = []
    for row in sorted(rows, key=lambda r: (-r['length_em'], r['metrics']['maximum_reciprocal_error_em'])):
        a = np.asarray(row['centerline'])
        duplicate = False
        for other in unique:
            b = np.asarray(other['centerline'])
            distances = np.linalg.norm(a[:, None, :]-b[None, :, :], axis=2)
            tolerance = em*BOUNDARY_POLICY['sample_step_em']*1.2
            if np.mean(distances.min(axis=1) < tolerance) > .8 and np.mean(distances.min(axis=0) < tolerance) > .8:
                duplicate = True
                other['reverse_observation_count'] += 1
                break
        if not duplicate:
            row['reverse_observation_count'] = 0
            unique.append(row)
    for row in unique:
        for section in row['sections']:
            section['source_contour'] = original_indices[section['source_contour']]
            section['target_contour'] = original_indices[section['target_contour']]
    for note in notes:
        note['contour'] = original_indices[note['contour']]
    return unique, notes


def compare_pairs(a, b):
    if a['status'] != 'paired' or b['status'] != 'paired':
        return {'compatible': False, 'decision': 'uncertain', 'reason': 'unresolved boundary pairing'}
    if max(a['length_em'], b['length_em']) > 2*min(a['length_em'], b['length_em']):
        return {'compatible': False, 'reason': 'incompatible paired span lengths'}
    x, y = np.array(a['metrics']['width_profile_em']), np.array(b['metrics']['width_profile_em'])
    rms = float(min(np.sqrt(np.mean((x-y)**2)), np.sqrt(np.mean((x-y[::-1])**2))))
    ok = rms <= POLICY['peer_profile_rms_em']
    return {'compatible': ok, 'profile_rms_em': rms,
            'reason': 'same axis family and comparable width profile' if ok else 'different stroke width or taper'}
