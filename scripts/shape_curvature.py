"""Native-outline curvature diagnostics; measurements are not design gates."""

import math

from fontTools.misc.bezierTools import solveQuadratic


def evaluate(points, t):
    while len(points) > 1:
        points = [tuple((1-t)*a+t*b for a, b in zip(p, q)) for p, q in zip(points, points[1:])]
    return points[0]


def derivative(points):
    degree = len(points)-1
    return [tuple(degree*(b-a) for a, b in zip(p, q)) for p, q in zip(points, points[1:])]


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def curvature(points, t):
    """Signed curvature in inverse font units; stationary points are unresolved."""
    first = derivative(points)
    velocity = evaluate(first, t)
    speed = math.hypot(*velocity)
    if speed < 1e-10:
        return None
    acceleration = evaluate(derivative(first), t) if len(first) > 1 else (0, 0)
    return cross(velocity, acceleration)/speed**3


def inflections(points):
    """Interior sign-changing roots of cross(B', B''); not sampled bend counts."""
    if len(points) != 4:
        return []
    p, q, r, s = points
    a = tuple(-x+3*y-3*z+w for x, y, z, w in zip(p, q, r, s))
    b = tuple(3*x-6*y+3*z for x, y, z in zip(p, q, r))
    c = tuple(3*(y-x) for x, y in zip(p, q))
    aa, bb, cc = -6*cross(a, b), 6*cross(c, a), 2*cross(c, b)
    roots = sorted({float(t) for t in solveQuadratic(aa, bb, cc) if 1e-9 < t < 1-1e-9})
    result = []
    for i, t in enumerate(roots):
        lo = ((roots[i-1] if i else 0)+t)/2
        hi = (t+(roots[i+1] if i+1 < len(roots) else 1))/2
        if (aa*lo*lo+bb*lo+cc)*(aa*hi*hi+bb*hi+cc) < 0 and curvature(points, t) is not None:
            result.append(t)
    return result


def audit(curves):
    segments, joins = [], []
    for index, curve in enumerate(curves):
        samples = [curvature(curve, i/32) for i in range(33)]
        segments.append({"segment": index, "inflections": inflections(curve),
                         "sampled_curvature": samples,
                         "unresolved_samples": sum(k is None for k in samples)})
    for index, (left, right) in enumerate(zip(curves, curves[1:])):
        v, w = evaluate(derivative(left), 1), evaluate(derivative(right), 0)
        kl, kr = curvature(left, 1), curvature(right, 0)
        angle = None if min(math.hypot(*v), math.hypot(*w)) < 1e-10 else math.degrees(math.atan2(abs(cross(v, w)), sum(a*b for a, b in zip(v, w))))
        joins.append({"after_segment": index, "position_gap_units": math.dist(left[-1], right[0]),
                      "tangent_angle_degrees": angle,
                      "curvature_jump_inverse_units": None if kl is None or kr is None else kr-kl})
    return {"segments": segments, "joins": joins,
            "interior_inflection_count": sum(len(s["inflections"]) for s in segments),
            "unresolved_sample_count": sum(s["unresolved_samples"] for s in segments)}


def comparison(before, after):
    return {"frame": "native", "units": "inverse font units", "diagnostic_only": True,
            "before": audit(before), "after": audit(after),
            "seam_curvature_changes": [
                None if (a := curvature(before[i], t)) is None or (b := curvature(after[i], t)) is None else b-a
                for i, t in ((0, 0), (-1, 1))]}


def comb(curves, x, baseline, scale):
    """Clipped curvature comb; sampling and display cap are explicitly labelled."""
    lines = []
    for curve in curves:
        for i in range(17):
            t = i/16
            k = curvature(curve, t)
            if k is None:
                continue
            p = evaluate(curve, t)
            vx, vy = evaluate(derivative(curve), t)
            speed = math.hypot(vx, vy)
            length = max(-40, min(40, k*1500))
            q = (p[0]-vy/speed*length, p[1]+vx/speed*length)
            lines.append(f'<path d="M{x+p[0]*scale} {baseline-p[1]*scale} L{x+q[0]*scale} {baseline-q[1]*scale}" stroke="#009caa" stroke-width=".7"/>')
    return ''.join(lines)
