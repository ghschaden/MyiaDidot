"""Shared geometric primitives and explicit retrieval policy."""

import math

from fontTools.pens.basePen import BasePen

POLICY = {
    "smooth_degrees": 3.0, "boundary_margin_degrees": 0.25,
    "minimum_line_em": 0.04, "flatten_tolerance_em": 0.00005,
    "section_step_em": 0.002, "transition_window_em": 0.08,
    "step_notice_em": 0.002, "anchor_tolerance_em": 0.001,
    "peer_profile_rms_em": 0.008, "peer_length_ratio": 2.0,
}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def length(a):
    return math.hypot(*a)


def unit(a):
    size = length(a)
    return (a[0] / size, a[1] / size) if size else (0.0, 0.0)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def angle(a, b):
    if not length(a) or not length(b):
        return 180.0
    return abs(math.degrees(math.atan2(cross(a, b), dot(a, b))))


def tangent(s, end=False):
    origin = s[-1] if end else s[0]
    points = reversed(s[:-1]) if end else s[1:]
    for p in points:
        d = sub(origin, p) if end else sub(p, origin)
        if length(d) > 1e-9:
            return unit(d)
    return (0.0, 0.0)


def is_line(s):
    """Includes monotone collinear quadratic/cubic representations of lines."""
    chord = sub(s[-1], s[0])
    size = length(chord)
    if size < 1e-9:
        return False
    projections = [dot(sub(p, s[0]), chord) / size**2 for p in s]
    return (all(abs(cross(sub(p, s[0]), chord)) / size < 1e-7 for p in s)
            and all(a <= b + 1e-10 for a, b in zip(projections, projections[1:])))


class Outline(BasePen):
    def __init__(self):
        super().__init__(None)
        self.contours = []
        self.current = []
        self.issues = []

    def _moveTo(self, p):
        self.start = p
        self.current = []

    def _lineTo(self, p):
        self.current.append((self._getCurrentPoint(), p))

    def _curveToOne(self, a, b, c):
        self.current.append((self._getCurrentPoint(), a, b, c))

    def _qCurveToOne(self, a, b):
        self.current.append((self._getCurrentPoint(), a, b))

    def _closePath(self):
        if self._getCurrentPoint() != self.start:
            self._lineTo(self.start)
        self.contours.append(self.current)

    def _endPath(self):
        self.issues.append("open contour omitted")

    def addComponent(self, glyphName, transformation):
        # Component provenance is handled separately, avoiding duplicate geometry.
        pass


def split(s):
    levels = [list(s)]
    while len(levels[-1]) > 1:
        levels.append([((a[0]+b[0])/2, (a[1]+b[1])/2)
                       for a, b in zip(levels[-1], levels[-1][1:])])
    return tuple(row[0] for row in levels), tuple(row[-1] for row in reversed(levels))


def flatten(s, tolerance, depth=0):
    polygon = sum(length(sub(b, a)) for a, b in zip(s, s[1:]))
    chord = sub(s[-1], s[0])
    deviation = max((abs(cross(sub(p, s[0]), chord)) / length(chord)
                     for p in s), default=0) if length(chord) else polygon
    if len(s) == 2 or (deviation <= tolerance and polygon-length(chord) <= tolerance):
        return [s[0], s[-1]]
    if depth >= 18:
        raise ValueError("adaptive flattening did not converge")
    a, b = split(s)
    return flatten(a, tolerance, depth+1)[:-1] + flatten(b, tolerance, depth+1)


def resample(points, step):
    distances = [0.0]
    for a, b in zip(points, points[1:]):
        distances.append(distances[-1]+length(sub(b, a)))
    if distances[-1] < 1e-9:
        return points[:1]
    count = max(2, math.ceil(distances[-1]/step)+1)
    result, k = [], 0
    for i in range(count):
        d = distances[-1]*i/(count-1)
        while k < len(points)-2 and distances[k+1] < d:
            k += 1
        den = distances[k+1]-distances[k]
        t = (d-distances[k])/den if den else 0
        result.append(tuple(a+(b-a)*t for a, b in zip(points[k], points[k+1])))
    return result


def transition_metrics(points, line_direction, em):
    """Arc-distance samples, measured back from the junction; no node-count score.

    Excess lateral travel over net travel detects a reversal, not every possible
    step. No claim that a positive value is an unintended design feature.
    """
    points = resample(list(reversed(points)), em*POLICY['section_step_em'])
    selected, distance = [points[0]], 0.0
    for a, b in zip(points, points[1:]):
        distance += length(sub(b, a))
        if distance > em*POLICY['transition_window_em']:
            break
        selected.append(b)
    lateral = [cross(line_direction, sub(p, points[0])) for p in selected]
    travel = sum(abs(b-a) for a, b in zip(lateral, lateral[1:]))
    excess = max(0.0, (travel-abs(lateral[-1]-lateral[0]))/2)
    profile = resample(selected, max(sum(length(sub(b, a)) for a, b in zip(selected, selected[1:]))/32, 1e-9))
    # Fixed-length descriptor in the local tangent frame, independent of translation.
    profile = [profile[round(i*(len(profile)-1)/32)] for i in range(33)]
    local = [[dot(line_direction, sub(p, points[0]))/em,
              cross(line_direction, sub(p, points[0]))/em] for p in profile]
    return {"profile": local, "lateral_reversal_em": excess/em, "window_length_em": sum(length(sub(b, a)) for a, b in zip(selected, selected[1:]))/em,
            "sample_count": len(selected), "lateral_samples_em": [v/em for v in lateral]}

