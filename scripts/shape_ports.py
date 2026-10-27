"""Measure attachment boundaries of anatomical samples; never replace outlines.

    .venv/bin/python -I scripts/shape_ports.py

Ports describe ink intervals on a crop boundary, not approved assembly seams.
Coordinates are deskewed font units, with native coordinates also recorded.
"""

import argparse
import html
import math
import sys
from collections import Counter
from pathlib import Path

import ufoLib2
from fontTools.misc.bezierTools import solveCubic
from fontTools.pens.basePen import BasePen
from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
import shape_consistency as consistency
import typographic_vocabulary as vocabulary

EPS = 1e-6


class Segments(BasePen):
    """Keep analytic curves and their contour/segment provenance."""

    def __init__(self):
        super().__init__(None)
        self.segments = []
        self.contour = -1
        self.index = 0

    def _moveTo(self, pt):
        self.start = pt
        self.contour += 1
        self.index = 0

    def add(self, points):
        self.segments.append((self.contour, self.index, points))
        self.index += 1

    def _lineTo(self, pt):
        self.add((self._getCurrentPoint(), pt))

    def _curveToOne(self, a, b, c):
        self.add((self._getCurrentPoint(), a, b, c))

    def _qCurveToOne(self, a, b):
        self.add((self._getCurrentPoint(), a, b))

    def _closePath(self):
        if self._getCurrentPoint() != self.start:
            self._lineTo(self.start)

    def _endPath(self):
        raise ValueError("Attachment measurement requires closed contours")


def evaluate(points, t):
    while len(points) > 1:
        points = [tuple((1-t)*a+t*b for a, b in zip(p, q)) for p, q in zip(points, points[1:])]
    return points[0]


def roots(points, axis, value):
    p = [point[axis]-value for point in points]
    if len(p) == 2:
        coeff = (0, 0, p[1]-p[0], p[0])
    elif len(p) == 3:
        coeff = (0, p[0]-2*p[1]+p[2], 2*(p[1]-p[0]), p[0])
    else:
        coeff = (-p[0]+3*p[1]-3*p[2]+p[3], 3*p[0]-6*p[1]+3*p[2], 3*(p[1]-p[0]), p[0])
    if all(abs(c) < EPS for c in coeff):
        return None  # outline lies on the cut: no unambiguous transverse seam
    return sorted({max(0, min(1, float(t))) for t in solveCubic(*coeff) if -EPS <= t <= 1+EPS})


def inside(path, point):
    pen = PointInsidePen(None, point, evenOdd=False)
    path.draw(pen)
    return pen.getResult()


def measure(path, box, slant=0):
    """Intersect original curves, not the artificial edges created by clipping.

    Vertex hits, corner hits, tangencies and coincident edges remain explicitly
    unresolved. No attempt to smooth away or repair an ambiguous connection.
    """
    pen = Segments()
    path.draw(pen)
    x0, y0, x1, y1 = box
    sides = (("left", 0, x0, y0, y1), ("right", 0, x1, y0, y1),
             ("bottom", 1, y0, x0, x1), ("top", 1, y1, x0, x1))
    result = []
    for name, axis, value, low, high in sides:
        events, issues = [], []
        for limit in (low, high):
            corner = (value, limit) if axis == 0 else (limit, value)
            if inside(path, corner):
                issues.append("ink reaches crop corner")
        for contour, index, points in pen.segments:
            found = roots(points, axis, value)
            if found is None:
                extent = [p[1-axis] for p in points]
                if max(extent) >= low and min(extent) <= high:
                    issues.append(f"coincident edge {contour}:{index}")
                continue
            for t in found:
                pt = evaluate(points, t)
                if not low-EPS <= pt[1-axis] <= high+EPS:
                    continue
                n = len(points)-1
                derivative = evaluate([tuple(n*(b-a) for a, b in zip(p, q))
                                       for p, q in zip(points, points[1:])], t)
                length = math.hypot(*derivative)
                tangent = [v/length for v in derivative] if length > EPS else None
                native = (derivative[0]+slant*derivative[1], derivative[1])
                native_length = math.hypot(*native)
                flags = []
                if t < EPS or t > 1-EPS:
                    flags.append("vertex")
                if abs(pt[1-axis]-low) < EPS or abs(pt[1-axis]-high) < EPS:
                    flags.append("corner")
                if tangent is None or abs(tangent[axis]) < EPS:
                    flags.append("tangent")
                events.append({"position": list(pt), "native_position": [pt[0]+slant*pt[1], pt[1]],
                               "tangent": tangent,
                               "native_tangent": [v/native_length for v in native] if native_length > EPS else None,
                               "contour": contour, "segment": index, "t": t,
                               "flags": flags})
        events.sort(key=lambda e: e["position"][1-axis])
        ports = []
        # A clear side has transverse interior crossings only. Nonzero winding
        # distinguishes a counter from ink and handles overlapping contours.
        if not issues and not any(e["flags"] for e in events):
            for a, b in zip(events, events[1:]):
                middle = tuple((u+v)/2 for u, v in zip(a["position"], b["position"]))
                if inside(path, middle):
                    ports.append({"endpoints": [a, b], "center": list(middle),
                                  "cut_width_units": math.dist(a["position"], b["position"])})
        result.append({"side": name, "events": events, "ports": ports, "issues": issues,
                       "status": "ambiguous" if issues or any(e["flags"] for e in events)
                       else "measured" if ports else "no-port"})
    return result


def proof(path, box, sides, title):
    pen = SVGPathPen(None)
    path.draw(pen)
    x0, y0, x1, y1 = path.bounds
    margin = 50
    view = f"{x0-margin} {-y1-margin} {x1-x0+2*margin} {y1-y0+2*margin}"
    bx0, by0, bx1, by1 = box
    # Very large crop bounds are deliberate sentinels. Clip them for display.
    bx0, by0, bx1, by1 = max(bx0, x0-margin/2), max(by0, y0-margin/2), min(bx1, x1+margin/2), min(by1, y1+margin/2)
    marks = []
    for side in sides:
        for port in side["ports"]:
            a, b = [e["position"] for e in port["endpoints"]]
            marks.append(f'<path d="M{a[0]} {a[1]} L{b[0]} {b[1]}" stroke="#00835c" stroke-width="5"/>')
        for event in side["events"]:
            x, y = event["position"]
            color = "#d64b00" if event["flags"] else "#005fc4"
            marks.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
            if event["tangent"]:
                dx, dy = event["tangent"]
                marks.append(f'<path d="M{x-15*dx} {y-15*dy} l{30*dx} {30*dy}" stroke="{color}" stroke-width="2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="360" height="400">'
            f'<title>{html.escape(title)}</title><g transform="scale(1,-1)">'
            f'<path d="{pen.getCommands()}" fill="#ddd"/>'
            f'<rect x="{bx0}" y="{by0}" width="{bx1-bx0}" height="{by1-by0}" fill="none" stroke="#a4268a" stroke-width="2"/>'
            + ''.join(marks) + '</g></svg>')


def compare(record, donor):
    """Report seam constraints, without interpreting differences as defects."""
    if any(s["status"] == "ambiguous" for r in (record, donor) for s in r["sides"]):
        return {"status": "needs-seam-design"}
    if any(len(a["ports"]) != len(b["ports"]) for a, b in zip(record["sides"], donor["sides"])):
        return {"status": "different-cut-topology"}
    pairs = []
    for side, reference in zip(record["sides"], donor["sides"]):
        for target, source in zip(side["ports"], reference["ports"]):
            angles = []
            for a, b in zip(target["endpoints"], source["endpoints"]):
                dot = sum(x*y for x, y in zip(a["tangent"], b["tangent"]))
                # Outline direction is not a design distinction. Compare lines,
                # not directed vectors, and report both boundary edge tangents.
                angles.append(math.degrees(math.acos(min(1, abs(dot)))))
            pairs.append({"side": side["side"],
                          "cut_width_difference_units": target["cut_width_units"]-source["cut_width_units"],
                          "edge_tangent_difference_degrees": angles})
    return {"status": "measured-constraints" if pairs else "no-attachments", "pairs": pairs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=consistency.ROOT / "build/glyph-review/shape-ports")
    args = parser.parse_args()
    out = consistency.safe_output(args.out)
    out.mkdir(parents=True, exist_ok=True)
    before = consistency.source_hashes()
    records, cards = [], []
    policy = consistency.read_policy(consistency.POLICY)
    contexts = {member: group["id"] for group in policy["groups"] for member in group["members"]}
    for style, source in consistency.source_paths().items():
        font = ufoLib2.Font.open(source)
        slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
        samples, _ = vocabulary.extract(style)
        for sample in samples:
            box = sample["extraction"].get("clip")
            if box is None:
                continue
            name = sample["glyph"]
            path = derive.to_path(font, font[name]).transform(1, 0, -slant, 1, 0, 0)
            sides = measure(path, box, slant)
            record = {"id": sample["id"], "context": contexts[sample["id"].split("/", 1)[1]],
                      "frame": "deskewed-font-units", "native_shear": slant, "box": box,
                      "sides": sides, "replacement_allowed": False}
            filename = sample["id"].replace("/", "-")+".svg"
            (out / filename).write_text(proof(path, box, sides, sample["id"]))
            record["proof"] = filename
            records.append(record)
            count = sum(len(s["ports"]) for s in sides)
            ambiguous = sum(s["status"] == "ambiguous" for s in sides)
            cards.append(f'<article><h2>{html.escape(sample["id"])}</h2><p>{count} measured ink intervals; {ambiguous} ambiguous sides</p>'
                         f'<img src="{filename}" alt="{html.escape(sample["id"])} attachment boundaries"></article>')
    after = consistency.source_hashes()
    if after != before:
        raise RuntimeError("Source fonts changed during measurement")
    summary = dict(Counter(s["status"] for r in records for s in r["sides"]))
    by_id = {r["id"]: r for r in records}
    donors = {g["id"]: g["donor"] for g in policy["groups"]}
    rows = []
    for record in records:
        donor_id = record["id"].split("/")[0]+"/"+donors[record["context"]]
        record["donor"] = donor_id
        record["comparison"] = compare(record, by_id[donor_id])
        comparison = record["comparison"]
        pairs = comparison.get("pairs", [])
        width = max((abs(p["cut_width_difference_units"]) for p in pairs), default=0)
        angle = max((a for p in pairs for a in p["edge_tangent_difference_degrees"]), default=0)
        row = [record["id"], donor_id, comparison["status"],
               f"{width:.3f}" if pairs else "—", f"{angle:.3f}" if pairs else "—"]
        rows.append('<tr>'+''.join(f'<td>{html.escape(cell)}</td>' for cell in row)+'</tr>')
    consistency.write_json(out / "ports.json", {"format": "myiadidot-shape-ports-v1", "source_hashes": before,
                                               "implementation_sha256": consistency.content_hash(Path(__file__)),
                                               "engine_sha256": consistency.engine_hash(),
                                               "policy_sha256": consistency.json_digest(policy),
                                               "sources_unchanged": True, "summary": summary, "records": records})
    (out / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Shape attachment measurements</title>'
                                    '<style>body{font:16px system-ui;margin:2em}main{display:flex;flex-wrap:wrap}article{width:380px}h2{font-size:16px}td,th{padding:.3em;text-align:left}tr:nth-child(even){background:#eee}</style>'
                                    '<h1>Connected shape boundaries</h1><p>Read-only measurements, not assembly-ready parts. '
                                    'Green: ink interval on a cut. Blue: crossing and tangent. Orange: ambiguous contact. '
                                    'Purple: crop; grey: original deskewed outline. Widths are along the cut, not stroke-normal thickness. '
                                    'Corners, vertices and coincident edges require explicit seam design.</p>'
                                    '<p><a href="ports.json">Full measurements and source identities</a></p>'
                                    '<p>Donor comparisons retain actual dimensions. Differences are constraints for a future fitting rule, not defects. '
                                    'Matching cuts do not establish compatible counters or joins.</p><table><tr><th>Sample</th><th>Donor</th>'
                                    '<th>Comparison</th><th>Maximum cut width difference (units)</th><th>Maximum edge angle difference (degrees)</th></tr>'
                                    + ''.join(rows) + '</table><main>' + ''.join(cards) + '</main>')
    print(f"Measured {len(records)} connected samples: {summary}. Sources unchanged. {out / 'index.html'}")


if __name__ == "__main__":
    main()
