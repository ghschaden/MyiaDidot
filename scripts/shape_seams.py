"""Explicit seam design and bounded connected-outline fitting experiments.

    .venv/bin/python -I scripts/shape_seams.py

Reads source UFOs; writes unaccepted scratch candidates and evidence in build/.
The two initial contexts are n -> h entry shoulders and H -> I capital feet.
"""

import argparse
import copy
import html
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

import pathops
import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
import glyph_lint
import shape_consistency as consistency
import shape_curvature as curvature
import shape_ports as ports
import typographic_vocabulary as vocabulary

POLICY = {
    "format": "myiadidot-connected-seams-v1",
    "collar_fraction": .25,
    "max_endpoint_correction_units": 25,
    "max_handle_correction_units": 25,
    "max_part_ink_difference_percent": 10,
    "max_glyph_ink_difference_percent": 2,
    "max_outside_ink_difference_units_squared": .1,
    "max_fitting_bbox_drift_units": .01,
    "max_native_bbox_drift_units": .01,
    "recipes": [
        {"id": "entry-shoulder", "donor": "n", "target": "h", "kind": "shoulder",
         "fitting_frame": "deskewed",
         "entry_gap_fraction": .15, "exit_height_fraction": .55,
         "ports": {"left": 1, "right": 0, "bottom": 1, "top": 0}},
        {"id": "capital-foot", "donor": "H", "target": "I", "kind": "foot",
         "fitting_frame": "native",
         "stem_height_fraction": .085,
         "ports": {"left": 0, "right": 0, "bottom": 0, "top": 1}},
    ],
}


def split(points, t):
    """Exact de Casteljau subdivision, without flattening curves."""
    levels = [list(points)]
    while len(levels[-1]) > 1:
        levels.append([tuple((1-t)*a+t*b for a, b in zip(p, q))
                       for p, q in zip(levels[-1], levels[-1][1:])])
    return tuple(level[0] for level in levels), tuple(level[-1] for level in reversed(levels))


def subcurve(points, low, high):
    left = split(points, high)[0] if high < 1 else tuple(points)
    return split(left, low/high)[1] if low > 0 else left


def cubic(points):
    if len(points) == 4:
        return tuple(points)
    if len(points) == 2:
        a, b = points
        return (a, tuple((2*x+y)/3 for x, y in zip(a, b)),
                tuple((x+2*y)/3 for x, y in zip(a, b)), b)
    a, b, c = points
    return (a, tuple((x+2*y)/3 for x, y in zip(a, b)),
            tuple((2*x+y)/3 for x, y in zip(b, c)), c)


def unit(a, b):
    vector = tuple(y-x for x, y in zip(a, b))
    length = math.hypot(*vector)
    if length < 1e-8:
        raise ValueError("Degenerate seam tangent")
    return tuple(v/length for v in vector)


def deskew(font, name):
    if font[name].components:
        raise ValueError("Seam experiment requires a directly drawn glyph")
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    pen = ports.Segments()
    font[name].draw(TransformPen(pen, (1, 0, -slant, 1, 0, 0)))
    contours = defaultdict(list)
    for contour, _, points in pen.segments:
        contours[contour].append(tuple(points))
    return list(contours.values()), slant


def recording(contours, close=True):
    pen = RecordingPen()
    for contour in contours:
        pen.moveTo(contour[0][0])
        for points in contour:
            if len(points) == 2:
                pen.lineTo(points[-1])
            elif len(points) == 3:
                pen.qCurveTo(*points[1:])
            else:
                pen.curveTo(*points[1:])
        if close:
            pen.closePath()
        else:
            pen.endPath()
    return pen


def path_for(contours):
    return derive.to_path(None, rec=recording(contours))


def seam_box(font, name, recipe):
    contours, slant = deskew(font, name)
    path = path_for(contours)
    scratch = ufoLib2.Font()
    path.draw(scratch.newGlyph(name).getPen())
    height = font.info.xHeight if recipe["kind"] == "shoulder" else font.info.capHeight
    stems = [(a, b) for a, b in derive.stems_at(scratch, name, height*(.5 if recipe["kind"] == "shoulder" else .3)) if b-a > 20]
    if recipe["kind"] == "shoulder":
        if len(stems) != 2:
            raise ValueError("Entry shoulder requires exactly two stems")
        left = stems[0][1]+recipe["entry_gap_fraction"]*(stems[1][0]-stems[0][1])
        box = [left, height*recipe["exit_height_fraction"], stems[1][1]+20, height+45]
    else:
        box = [path.bounds[0]-20, -45,
               (stems[0][1]+stems[1][0])/2 if len(stems) > 1 else path.bounds[2]+20,
               height*recipe["stem_height_fraction"]]
    measured = ports.measure(path, box, slant)
    if any(s["status"] == "ambiguous" or len(s["ports"]) != recipe["ports"][s["side"]] for s in measured):
        raise ValueError("Seam no longer has the declared transverse ink intervals")
    return contours, path, box, measured, slant


def partition(contours, box):
    """Split each original contour at the seam and retain its outside spans."""
    x0, y0, x1, y1 = box
    result = []
    for contour in contours:
        chunks = []
        for points in contour:
            cuts = [0., 1.]
            for axis, value in ((0, x0), (0, x1), (1, y0), (1, y1)):
                found = ports.roots(points, axis, value)
                if found:
                    cuts.extend(t for t in found if 1e-8 < t < 1-1e-8)
            cuts = sorted(set(cuts))
            for lo, hi in zip(cuts, cuts[1:]):
                if hi-lo < 1e-8:
                    continue
                curve = subcurve(points, lo, hi)
                x, y = ports.evaluate(curve, .5)
                internal = x0 < x < x1 and y0 < y < y1
                if chunks and chunks[-1]["inside"] == internal:
                    chunks[-1]["curves"].append(curve)
                else:
                    chunks.append({"inside": internal, "curves": [curve]})
        if len(chunks) > 1 and chunks[0]["inside"] == chunks[-1]["inside"]:
            chunks[0]["curves"] = chunks[-1]["curves"]+chunks[0]["curves"]
            chunks.pop()
        result.append(chunks)
    return result


def endpoint_key(point, box):
    x0, y0, x1, y1 = box
    distances = [(abs(point[0]-x0), "left"), (abs(point[0]-x1), "right"),
                 (abs(point[1]-y0), "bottom"), (abs(point[1]-y1), "top")]
    distance, side = min(distances)
    if distance > .001:
        raise ValueError("Arc endpoint is not on its seam")
    return side


def arcs(partitioned, box):
    result = {}
    for contour in partitioned:
        for chunk in contour:
            if not chunk["inside"]:
                continue
            curves = chunk["curves"]
            key = (endpoint_key(curves[0][0], box), endpoint_key(curves[-1][-1], box))
            if key in result:
                raise ValueError("Ambiguous arc correspondence")
            result[key] = chunk
    return result


def fit_arc(donor, target, donor_bounds, target_bounds, policy):
    """Affine core with cubic transition collars preserving target G1 joins.

    Each collar is a subdivision of the first/last donor segment. Its interior
    endpoint and adjacent handle stay fixed; only its seam endpoint and handle
    move. Internal segment joins therefore retain the donor's tangent lines.
    """
    dx0, dy0, dx1, dy1 = donor_bounds
    tx0, ty0, tx1, ty1 = target_bounds
    if min(dx1-dx0, dy1-dy0, tx1-tx0, ty1-ty0) <= 0:
        raise ValueError("Degenerate part bounds")
    sx, sy = (tx1-tx0)/(dx1-dx0), (ty1-ty0)/(dy1-dy0)
    transformed = [tuple((tx0+(x-dx0)*sx, ty0+(y-dy0)*sy) for x, y in curve) for curve in donor]
    fraction = policy["collar_fraction"]
    if not 0 < fraction < .5:
        raise ValueError("Collar fraction must be between zero and one half")
    first, remaining = split(cubic(transformed[0]), fraction)
    fitted = [first, remaining, *transformed[1:]]
    remaining, last = split(cubic(fitted[-1]), 1-fraction)
    fitted[-1:] = [remaining, last]
    endpoints = [(0, 0, 1, target[0][0], unit(target[0][0], target[0][1])),
                 (-1, 3, 2, target[-1][-1], unit(target[-1][-2], target[-1][-1]))]
    corrections, handle_corrections = [], []
    for index, end, handle, position, tangent in endpoints:
        curve = list(cubic(fitted[index]))
        correction = math.dist(curve[end], position)
        if correction > policy["max_endpoint_correction_units"]:
            raise ValueError(f"Seam correction {correction:.3f} exceeds local fitting budget")
        length = math.dist(curve[end], curve[handle])
        if length < 1e-8:
            raise ValueError("Degenerate collar handle")
        old_handle = curve[handle]
        curve[end] = tuple(position)
        direction = 1 if end == 0 else -1
        curve[handle] = tuple(p+direction*length*t for p, t in zip(position, tangent))
        handle_correction = math.dist(old_handle, curve[handle])
        if handle_correction > policy["max_handle_correction_units"]:
            raise ValueError("Seam handle correction exceeds local fitting budget")
        fitted[index] = tuple(curve)
        corrections.append(correction)
        handle_corrections.append(handle_correction)
    for point, expected in ((fitted[0][0], target[0][0]), (fitted[-1][-1], target[-1][-1])):
        if math.dist(point, expected) > 1e-8:
            raise ValueError("Seam position continuity failed")
    for actual, expected in ((unit(fitted[0][0], fitted[0][1]), unit(target[0][0], target[0][1])),
                             (unit(fitted[-1][-2], fitted[-1][-1]), unit(target[-1][-2], target[-1][-1]))):
        if math.dist(actual, expected) > 1e-8:
            raise ValueError("Seam tangent continuity failed")
    return fitted, {"endpoint_corrections_units": corrections, "endpoint_error_units": 0,
                    "handle_corrections_units": handle_corrections,
                    "edge_direction_error": 0, "continuity": "G1, not curvature continuity"}


def clearance(before, after, box):
    """Sample horizontal counter gaps; this supplements vector/lint checks."""
    scratch = ufoLib2.Font()
    before.draw(scratch.newGlyph("before").getPen())
    after.draw(scratch.newGlyph("after").getPen())
    rows, failures = [], []
    for i in range(1, 33):
        y = box[1]+(box[3]-box[1])*i/33
        old, new = (derive.stems_at(scratch, name, y) for name in ("before", "after"))
        if len(old) != len(new):
            failures.append(f"ink interval count changed at y={y:g}")
            continue
        for j in range(len(old)-1):
            gap_a, gap_b = old[j+1][0]-old[j][1], new[j+1][0]-new[j][1]
            if gap_a <= .01:
                continue
            rows.append({"y": y, "before_units": gap_a, "after_units": gap_b})
            if gap_b < .9*gap_a:
                failures.append(f"counter gap reduced by more than 10% at y={y:g}")
    return {"scanlines": 32, "gaps": rows, "failures": failures,
            "scope": "sampled horizontal clearance, not a proof of continuous minimum clearance"}


def fit(font, recipe, policy=POLICY):
    donor, dp, db, dm, _ = seam_box(font, recipe["donor"], recipe)
    target, tp, tb, tm, slant = seam_box(font, recipe["target"], recipe)
    donor_chunks, target_chunks = partition(donor, db), partition(target, tb)
    da, ta = arcs(donor_chunks, db), arcs(target_chunks, tb)
    if set(da) != set(ta):
        raise ValueError("Donor and target arc topology differs")
    original_outside = copy.deepcopy([c["curves"] for contour in target_chunks for c in contour if not c["inside"]])
    donor_part, target_part = vocabulary.clip(dp, db), vocabulary.clip(tp, tb)
    arc_reports = []
    for key, chunk in ta.items():
        donor_curves, target_curves = da[key]["curves"], chunk["curves"]
        donor_bounds, target_bounds = donor_part.bounds, target_part.bounds
        if recipe["fitting_frame"] == "native":
            donor_curves = shear_curves(donor_curves, slant)
            target_curves = shear_curves(target_curves, slant)
            donor_bounds = donor_part.transform(1, 0, slant, 1, 0, 0).bounds
            target_bounds = target_part.transform(1, 0, slant, 1, 0, 0).bounds
        replacement, report = fit_arc(donor_curves, target_curves, donor_bounds, target_bounds, policy)
        native_shear = slant if recipe["fitting_frame"] == "deskewed" else 0
        report["curvature"] = curvature.comparison(shear_curves(target_curves, native_shear),
                                                    shear_curves(replacement, native_shear))
        if recipe["fitting_frame"] == "native":
            replacement = shear_curves(replacement, -slant)
        chunk["curves"] = replacement
        arc_reports.append({"from_side": key[0], "to_side": key[1], **report})
    outside = [c["curves"] for contour in target_chunks for c in contour if not c["inside"]]
    if outside != original_outside:
        raise ValueError("Fitting changed an outside curve")
    fitted = [[curve for chunk in contour for curve in chunk["curves"]] for contour in target_chunks]
    candidate = path_for(fitted)
    # Generated outlines may overlap. Raw path area double-counts overlap and
    # can falsely report zero change after clamping a negative area difference.
    tp, candidate = pathops.simplify(tp), pathops.simplify(candidate)
    candidate_part = vocabulary.clip(candidate, tb)
    outside_a = derive.path_op(tp, derive.rect_path(*tb), "DIFFERENCE")
    outside_b = derive.path_op(candidate, derive.rect_path(*tb), "DIFFERENCE")
    outside_diff = derive.path_op(outside_a, outside_b, "XOR").area
    native_bounds = BoundsPen(None)
    recording(fitted).replay(TransformPen(native_bounds, (1, 0, slant, 1, 0, 0)))
    native_drift = max(abs(a-b) for a, b in zip(font[recipe["target"]].getBounds(font), native_bounds.bounds))
    deskewed_drift = max(abs(a-b) for a, b in zip(tp.bounds, candidate.bounds))
    metrics = {"part_ink_difference_percent": vocabulary.distance(target_part, candidate_part),
               "glyph_ink_difference_percent": vocabulary.distance(tp, candidate),
               "outside_ink_difference_units_squared": outside_diff,
               "fitting_bbox_drift_units": native_drift if recipe["fitting_frame"] == "native" else deskewed_drift,
               "native_bbox_drift_units": native_drift}
    failures = [name for name, value in metrics.items() if value > policy["max_"+name]]
    counter = clearance(tp, candidate, tb)
    failures.extend(counter["failures"])
    if len(list(tp.contours)) != len(list(candidate.contours)):
        failures.append("filled contour topology changed")
    # Outside curve identity is exact; area comparisons tolerate float pathops.
    report = {"recipe": recipe["id"], "donor": recipe["donor"], "target": recipe["target"],
              "fitting_frame": recipe["fitting_frame"],
              "deskewed_bbox_drift_units": deskewed_drift,
              "donor_box": db, "target_box": tb, "donor_ports": dm, "target_ports": tm,
              "arcs": arc_reports, "metrics": metrics, "counter_clearance": counter,
              "outside_curve_spans_unchanged": True,
              "failures": failures, "status": "rejected" if failures else "geometry-checked-unaccepted",
              "outline_metadata": "Reconstructed contours; point identities and smooth flags require generator finishing. Glyph/font metadata retained."}
    return fitted, slant, report


def shear_curves(curves, shear):
    return [tuple((x+shear*y, y) for x, y in curve) for curve in curves]


def install_scratch(glyph, contours, slant):
    """Only called on an in-memory scratch copy; never saves a source font."""
    glyph.clearContours()
    recording(contours).replay(TransformPen(glyph.getPen(), (1, 0, slant, 1, 0, 0)))


def validate_font(before, after, changed):
    a, b = json.loads(before.json_dumps()), json.loads(after.json_dumps())
    for snapshot in (a, b):
        for layer in snapshot["layers"]:
            for name in changed:
                if name in layer["glyphs"]:
                    layer["glyphs"][name].pop("contours", None)
    if a != b:
        raise ValueError("Scratch candidate altered metadata or unrelated outlines")
    expected = consistency.component_dependants(before, changed)
    old, new = consistency.outlines(before), consistency.outlines(after)
    actual = {name for name in old if old[name] != new[name]}
    if actual != expected:
        raise ValueError("Unexpected component impact")
    return {"direct_changes": sorted(changed), "component_dependants": sorted(actual-changed),
            "glyph_font_metadata_preserved": True,
            "accepted_designs_affected": sorted(n for n in actual if before[n].lib.get("org.myiadidot.accepted")),
            "recorded_flattened_dependants": {g.name: sorted(set(g.lib.get("org.myiadidot.builtFrom", {})) & actual)
                                             for g in before if set(g.lib.get("org.myiadidot.builtFrom", {})) & actual}}


def overlay(before, after, report, destination, style):
    name = report["target"]
    a, b = derive.to_path(before, before[name]), derive.to_path(after, after[name])
    x0, y0, x1, y1 = a.bounds
    scale = min(290/(x1-x0), 400/(y1-y0))
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="580" viewBox="0 0 1080 580">',
             '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
             f'<text x="20" y="30" font-size="22">{html.escape(style)} · {name} · {report["recipe"]}</text>',
             f'<text x="20" y="55" font-size="15">Unaccepted seam-fitting experiment · {report["status"]}</text>']
    for x, label in ((25, "Original"), (375, "Candidate"), (725, "Overlay")):
        lines.append(f'<text x="{x}" y="90" font-size="17">{label}</text>')
    for path, offset, color, opacity in ((a, 25, "#222", 1), (b, 375, "#ba167d", 1),
                                         (a, 725, "#222", .65), (b, 725, "#ba167d", .45)):
        lines.append(vocabulary.draw(path, offset-x0*scale, 520+y0*scale, scale, color, opacity))
    for offset in (25, 375, 725):
        for side in report["target_ports"]:
            for port in side["ports"]:
                p, q = (e["native_position"] for e in port["endpoints"])
                lines.append(f'<path d="M{offset+(p[0]-x0)*scale} {520+(y0-p[1])*scale} '
                             f'L{offset+(q[0]-x0)*scale} {520+(y0-q[1])*scale}" stroke="#009caa" stroke-width="2"/>')
    lines.append('<text x="20" y="560" font-size="14">Cyan: complete ink intervals at the designed seams. Source-outline proof; no hinting.</text>')
    lines.append('</g></svg>')
    destination.write_text('\n'.join(lines))


def curvature_proof(before, after, report, destination, style):
    name = report["target"]
    bounds = before[name].getBounds(before)
    scale = min(350/(bounds[2]-bounds[0]), 400/(bounds[3]-bounds[1]))
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600">',
             '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
             f'<text x="20" y="30" font-size="22">{style} {name}: native curvature comb</text>']
    for font, offset, label in ((before, 60, "Original"), (after, 550, "Candidate")):
        x, baseline = offset-bounds[0]*scale, 510+bounds[1]*scale
        lines.append(f'<text x="{offset}" y="65" font-size="18">{label}</text>')
        lines.append(vocabulary.draw(derive.to_path(font, font[name]), x, baseline, scale, "#222", .35))
        contours, slant = deskew(font, name)
        for contour in contours:
            lines.append(curvature.comb(shear_curves(contour, slant), x, baseline, scale))
    lines.append('<text x="20" y="560" font-size="13">17 samples/segment; signed curvature × 1500, capped at ±40 font units. Not a quality score.</text>')
    lines.append('<text x="20" y="582" font-size="13">Unequal sample density follows curve subdivision. Source outlines, no hinting; candidates remain unaccepted.</text></g></svg>')
    destination.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=consistency.ROOT / "build/glyph-review/shape-seams")
    args = parser.parse_args()
    out = consistency.safe_output(args.out)
    identities = consistency.source_hashes()
    implementation = consistency.content_hash(Path(__file__))
    engine = consistency.engine_hash()
    ports_hash = consistency.content_hash(Path(ports.__file__))
    curvature_hash = consistency.content_hash(Path(curvature.__file__))
    run = consistency.safe_output(out / "runs" / uuid4().hex[:12])
    run.mkdir(parents=True)
    reports, links = {}, []
    for style, source in consistency.source_paths().items():
        before = ufoLib2.Font.open(source, lazy=False)
        after = copy.deepcopy(before)
        operations, changed = [], set()
        for recipe in POLICY["recipes"]:
            contours, slant, report = fit(before, recipe)
            # Keep original topology for exact/no-op cases.
            if not report["failures"] and report["metrics"]["part_ink_difference_percent"] < .0001:
                report["status"] = "already-consistent"
            else:
                install_scratch(after[recipe["target"]], contours, slant)
                changed.add(recipe["target"])
            operations.append(report)
        impact = validate_font(before, after, changed)
        affected = sorted(changed | set(impact["component_dependants"]))
        baseline = glyph_lint.lint(before, affected) if affected else {}
        candidate = glyph_lint.lint(after, affected) if affected else {}
        findings = {name: [item for item in values if item not in baseline.get(name, [])] for name, values in candidate.items()}
        findings = {name: values for name, values in findings.items() if values}
        directory = run / style
        directory.mkdir()
        before_path, after_path = directory / "before.ufo", directory / "candidate.ufo"
        before.save(before_path)
        after.save(after_path)
        if json.loads(after.json_dumps()) != json.loads(ufoLib2.Font.open(after_path).json_dumps()):
            raise ValueError("Scratch font round trip changed content")
        shaping = consistency.shaping_checks(before_path, after_path, before, affected)
        proof = directory / "before-after.svg"
        consistency.proof_renderer()(after_path, ["n", "h", "m", "H", "I", "o"], proof, before=before_path,
                                     texts=("minimum high thin HILL", "h\u0301 n\u0301 I\u0308"), language="en", script="latn", anchors=True)
        for operation in operations:
            detail = directory / f'{operation["recipe"]}.svg'
            overlay(before, after, operation, detail, style)
            comb_path = directory / f'{operation["recipe"]}-curvature.svg'
            curvature_proof(before, after, operation, comb_path, style)
            links.append(f'<li>{style}: <a href="{comb_path.relative_to(out)}">{operation["recipe"]} curvature comb</a></li>')
            links.append(f'<li>{style}: <a href="{detail.relative_to(out)}">{operation["recipe"]}</a> — {operation["status"]}</li>')
        links.append(f'<li><a href="{proof.relative_to(out)}">{style}: full proof with shaped text</a></li>')
        reports[style] = {"operations": operations, "impact": impact, "shaping": shaping,
                          "outline_lint": {"baseline": baseline, "candidate": candidate, "new_findings": findings},
                          "candidate": str(after_path.relative_to(out)), "proof": str(proof.relative_to(out)),
                          "release_ready": False, "geometry_gate_passed": not findings and not any(r["failures"] for r in operations)}
        print(f'{style}: {len(changed)} changes, {len(affected)} affected glyphs, {shaping["cases"]} shaping checks, {len(findings)} new lint findings', flush=True)
    if consistency.source_hashes() != identities:
        raise RuntimeError("Production source bytes changed during experiment")
    if (implementation != consistency.content_hash(Path(__file__)) or engine != consistency.engine_hash()
            or ports_hash != consistency.content_hash(Path(ports.__file__))
            or curvature_hash != consistency.content_hash(Path(curvature.__file__))):
        raise RuntimeError("Implementation changed during experiment; rerun before publishing")
    result = {"format": "myiadidot-connected-seam-preview-v1", "policy": POLICY,
              "source_hashes": identities, "sources_byte_identical": True,
              "implementation_sha256": implementation,
              "engine_sha256": engine, "ports_sha256": ports_hash,
              "curvature_sha256": curvature_hash,
              "styles": reports, "release_ready": False,
              "limitations": ["Experimental outline fitting; no generator integration or integer finishing",
                              "Contour topology and point metadata are reconstructed in scratch fonts",
                              "Component dependants are automatic; flattened generator dependencies are not rebuilt",
                              "Unhinted shaping and source proofs; no visual acceptance"]}
    consistency.write_json(run / "report.json", result)
    consistency.write_json(out / "report.json", result)
    (out / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Connected seam fitting</title>'
                                    '<style>body{font:17px system-ui;max-width:1000px;margin:2em auto}li{margin:.6em}</style>'
                                    '<h1>Connected seam fitting experiments</h1><p>Same-style shoulders and capital feet. '
                                    'Original seam positions and edge directions are retained; donor cores use local cubic transition collars. '
                                    'Unaccepted scratch outlines only. Rejected candidates remain visible for diagnosis; no source or generator changes.</p>'
                                    '<p><a href="report.json">Measurements, gates and source identities</a></p><ul>'+''.join(links)+'</ul>')


if __name__ == "__main__":
    main()
