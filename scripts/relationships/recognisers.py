"""Local relationship recognisers; no repair or acceptance operations."""

import math
import unicodedata
from collections import defaultdict

from fontTools.misc.transform import Transform

from .geometry import POLICY, angle, flatten, is_line, length, resample, sub, tangent, transition_metrics


def transitions(contours, em, slant=0):
    found, issues = [], []
    for ci, native in enumerate(contours):
        kept = [(index, s) for index, s in enumerate(native)
                if sum(length(sub(b, a)) for a, b in zip(s, s[1:])) >= 1e-9]
        if len(kept) != len(native):
            issues.append({"contour": ci, "reason": "zero-length segments ignored for geometry; original source retained",
                           "ignored_segments": [i for i in range(len(native)) if i not in {k for k, _ in kept}]})
        original_indices = [index for index, _ in kept]
        segs = [tuple((x-slant*y, y) for x, y in s) for _, s in kept]
        size = len(segs)
        for i in range(size):
            # Orient each boundary so a curve runs towards a line, even if the
            # contour itself traverses it in the opposite direction.
            a, b = segs[i-1], segs[i]
            if is_line(a) == is_line(b):
                continue
            forward = not is_line(a)
            oriented = segs if forward else [tuple(reversed(s)) for s in reversed(segs)]
            j = i if forward else (size-i) % size
            join_angle = angle(tangent(oriented[j-1], True), tangent(oriented[j]))
            if join_angle > POLICY['smooth_degrees']:
                continue
            run, indices, k = [], [], (j-1) % size
            while not is_line(oriented[k]):
                run.insert(0, oriented[k])
                indices.insert(0, k if forward else size-1-k)
                prev = (k-1) % size
                if is_line(oriented[prev]) or angle(tangent(oriented[prev], True), tangent(oriented[k])) > POLICY['smooth_degrees']:
                    break
                k = prev
            line_length, k = 0.0, j
            direction = tangent(oriented[j])
            while is_line(oriented[k]) and angle(direction, tangent(oriented[k])) < 1e-5:
                line_length += length(sub(oriented[k][-1], oriented[k][0]))
                k = (k+1) % size
                if k == j:
                    break
            if line_length < em*POLICY['minimum_line_em']:
                continue
            pts = []
            for s in run:
                pts += flatten(s, em*POLICY['flatten_tolerance_em'])[:-1]
            pts.append(run[-1][-1])
            measured = transition_metrics(pts, direction, em)
            degrees = math.degrees(math.atan2(direction[1], direction[0])) % 180
            axis = 'vertical' if abs(degrees-90) < 15 else 'horizontal' if min(degrees, 180-degrees) < 15 else 'oblique'
            uncertain = join_angle > POLICY['smooth_degrees']-POLICY['boundary_margin_degrees']
            found.append({"relationship": "curve-to-line", "evidence": "geometry",
                          "status": "boundary-uncertain" if uncertain else "structural-candidate",
                          "family": f"curve-to-line/{axis}", "contour": ci,
                          "segments": [original_indices[k] for k in indices], "junction": list(run[-1][-1]),
                          "line_direction": list(direction), "line_length_em": line_length/em,
                          "join_angle_degrees": join_angle, "metrics": measured,
                          "curve_length_em": sum(length(sub(b, a)) for a, b in zip(pts, pts[1:]))/em,
                          "review_notice": measured['lateral_reversal_em'] > POLICY['step_notice_em'],
                          "explanation": "A complete smooth curved run meets a sufficiently long straight edge; family indicates structural similarity, not a shared defect or repair.",
                          "span": [list(p) for p in resample(pts, em*0.005)]})
    return found, issues


def cmap(font):
    result = defaultdict(list)
    for g in font:
        for cp in g.unicodes:
            result[cp].append(g.name)
    return result


def anchor_candidates(font, mark_name, target_name):
    """Map a combining wrapper's attachment anchors into its component's frame."""
    g, transform, visited = font[mark_name], Transform(), set()
    anchors = [(a.name, (a.x, a.y)) for a in g.anchors if a.name and a.name.startswith('_')]
    while True:
        if g.name in visited:
            return [], 'component cycle'
        visited.add(g.name)
        if g.name == target_name:
            try:
                inverse = transform.inverse()
            except ZeroDivisionError:
                return [], 'singular component transform'
            return [(name[1:], inverse.transformPoint(p)) for name, p in anchors], None
        if len(g.components) != 1 or g.contours:
            return [], 'mark is not a single-component wrapper of the attached piece'
        c = g.components[0]
        if c.baseGlyph not in font:
            return [], 'missing component'
        transform = transform.transform(c.transformation)
        g = font[c.baseGlyph]


def attachments(font):
    mapping, found = cmap(font), []
    for g in sorted(font, key=lambda g: g.name):
        for cp in g.unicodes:
            chars = unicodedata.normalize('NFD', chr(cp))
            if len(chars) < 2 or not all(unicodedata.combining(c) for c in chars[1:]):
                continue
            base_names = mapping.get(ord(chars[0]), [])
            bases = [(i, c) for i, c in enumerate(g.components) if c.baseGlyph in base_names]
            record = {"glyph": g.name, "relationship": "base-mark-attachment",
                      "evidence": "unicode-decomposition+components", "unicode": cp,
                      "status": "unresolved", "family": None, "base": None,
                      "reason": "Requires one identifiable base and one mark component, without own contours."}
            if len(chars) != 2 or len(g.components) != 2 or len(bases) != 1 or g.contours:
                found.append(record)
                continue
            index, base = bases[0]
            mark = g.components[1-index]
            record.update(base=base.baseGlyph, mark=mark.baseGlyph,
                          component_indices=[index, 1-index],
                          transforms=[list(base.transformation), list(mark.transformation)])
            if base.baseGlyph not in font or mark.baseGlyph not in font:
                record['reason'] = 'missing component'
                found.append(record)
                continue
            matches = []
            for mark_name in mapping.get(ord(chars[1]), []):
                anchors, _ = anchor_candidates(font, mark_name, mark.baseGlyph)
                for role, pos in anchors:
                    for a in font[base.baseGlyph].anchors:
                        if a.name != role:
                            continue
                        p = base.transformation.transformPoint((a.x, a.y))
                        q = mark.transformation.transformPoint(pos)
                        matches.append({"role": role, "wrapper": mark_name, "base_position": list(p),
                                        "mark_position": list(q), "distance_em": length(sub(p, q))/font.info.unitsPerEm})
            close = [m for m in matches if m['distance_em'] <= POLICY['anchor_tolerance_em']]
            record['anchor_evidence'] = matches
            if len(close) == 1:
                record.update(status='confirmed', family=f"base-mark/{close[0]['role']}",
                              reason='Explicit base and mark components agree with the unique matching transformed attachment anchor.')
            elif len(close) > 1:
                record['reason'] = 'Multiple attachment anchors or Unicode wrappers match; role is ambiguous.'
            elif matches:
                record['reason'] = 'Named anchor correspondence exists, but transformed positions do not agree.'
            else:
                record['reason'] = 'Component ancestry is known; attachment anchors could not be established.'
            found.append(record)
    return found

