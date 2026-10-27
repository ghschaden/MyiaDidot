"""Read-only roundness study: isolated emboldening controls, not master edits.

    .venv/bin/python -I scripts/shape_roundness.py

Compare identical construction inputs with existing curve protections off/on.
The stage results omit the rest of the production generator deliberately.
"""

import argparse
import copy
import html
import math
import sys
from collections import Counter
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
import glyph_lint
import make_bold
import shape_consistency as consistency
import shape_ports
import typographic_vocabulary as vocabulary

NAMES = ("n", "h", "m", "o", "O", "a", "b", "d", "g", "p", "q", "s", "S", "u", "v", "w", "y",
         "alpha", "phi", "psi", "uni0431", "uni0433")


def diagnostics(glyph):
    """Geometric indicators; intentional inflections/corners are not defects."""
    pen = shape_ports.Segments()
    glyph.draw(pen)
    contours = {}
    for contour, _, curve in pen.segments:
        contours.setdefault(contour, []).append(curve)
    inflections, breaks = [], []
    for ci, curves in contours.items():
        for i, curve in enumerate(curves):
            if len(curve) == 4 and derive.inflects(curve):
                inflections.append({"contour": ci, "segment": i, "point": shape_ports.evaluate(curve, .5)})
            following = curves[(i+1) % len(curves)]
            if len(curve) != 4 or len(following) != 4:
                continue
            a = (curve[-1][0]-curve[-2][0], curve[-1][1]-curve[-2][1])
            b = (following[1][0]-following[0][0], following[1][1]-following[0][1])
            if min(math.hypot(*a), math.hypot(*b)) < 5:
                continue
            angle = math.degrees(math.acos(max(-1, min(1, sum(x*y for x, y in zip(a, b))/(math.hypot(*a)*math.hypot(*b))))))
            if 2 < angle < 45:
                breaks.append({"contour": ci, "segment": i, "point": curve[-1], "degrees": angle})
    return {"inflecting_cubics": inflections, "near_smooth_curve_breaks": breaks}


def construction(source, name, method, protect):
    """Same input, weight and width; toggle only the named curve protection."""
    italic = bool(source.info.italicAngle)
    slant = math.tan(math.radians(-(source.info.italicAngle or 0)))
    pen = RecordingPen()
    source[name].draw(TransformPen(pen, (make_bold.KX, 0, -slant*make_bold.KX, 1, 0, 0)))
    ax = make_bold.ITALIC_AX if italic else make_bold.AX
    if method == "weighted":
        glyph = derive.embolden_by_weight(pen, ax, make_bold.AY, make_bold.THIN, make_bold.THICK,
                                          runs_on=not italic, keep_bends=protect)
    elif method == "rounder":
        glyph = derive.embolden_simple(pen, ax, make_bold.AY, weighted=True, thin=make_bold.THIN,
                                      thick=make_bold.THICK, keep_smooth=protect)
    else:
        raise ValueError("Unknown emboldening method")
    native = ufoLib2.objects.Glyph(name=name)
    glyph.draw(TransformPen(native.getPen(), (1, 0, slant, 1, ax/2, 0)))
    return native


def difference(a, b):
    pa = pathops.simplify(derive.to_path(None, rec=record(a)))
    pb = pathops.simplify(derive.to_path(None, rec=record(b)))
    union = derive.path_op(pa, pb, "UNION").area
    # Direct XOR can misorient coincident curved fragments and return more
    # area than the union. Use the filled-area identity after simplification.
    changed = 2*union-pa.area-pb.area
    if changed < -.01 or changed > union+.01:
        raise ValueError("Inconsistent filled-area comparison")
    return 100*max(0, changed)/union if union else 0


def record(glyph):
    pen = RecordingPen()
    glyph.draw(pen)
    return pen


def oval_trial(source, current, name):
    """A separately fitted outer oval and counter, retaining optical context.

    Only the explicit o/O/zero study is supported. This is not an automatic
    contour smoother and is not applied to connected bowls or arbitrary marks.
    """
    if name not in ("o", "O", "zero"):
        raise ValueError("Oval study requires an explicit closed-round context")
    old = current[name]
    if old.components or source[name].components or len(old.contours) != 2 or len(source[name].contours) != 2:
        raise ValueError("Oval study requires two directly drawn contours")
    slant = math.tan(math.radians(-(current.info.italicAngle or 0)))
    flat_source, flat_current = (ufoLib2.objects.Glyph(name=name) for _ in range(2))
    source[name].draw(TransformPen(flat_source.getPen(), (1, 0, -slant, 1, 0, 0)))
    old.draw(TransformPen(flat_current.getPen(), (1, 0, -slant, 1, 0, 0)))
    source_contours = sorted(flat_source.contours, key=lambda c: consistency.contour_path(c).area, reverse=True)
    target_contours = sorted(flat_current.contours, key=lambda c: consistency.contour_path(c).area, reverse=True)
    flat = ufoLib2.objects.Glyph(name=name)
    contour_reports = []
    for src, dst in zip(source_contours, target_contours):
        a, b = consistency.contour_path(src), consistency.contour_path(dst)
        if a.clockwise != b.clockwise:
            raise ValueError("Oval contour winding mismatch")
        x0, y0, x1, y1 = a.bounds
        u0, v0, u1, v1 = b.bounds
        sx, sy = (u1-u0)/(x1-x0), (v1-v0)/(y1-y0)
        src.draw(TransformPen(flat.getPen(), (sx, 0, 0, sy, u0-x0*sx, v0-y0*sy)))
        contour_reports.append({"scale_x": sx, "scale_y": sy, "target_deskewed_bounds": b.bounds})
    candidate = copy.deepcopy(old)
    candidate.clearContours()
    flat.draw(TransformPen(candidate.getPen(), (1, 0, slant, 1, 0, 0)))
    a, b = (pathops.simplify(derive.to_path(None, rec=record(g))) for g in (old, candidate))
    font = ufoLib2.Font()
    font.addGlyph(copy.deepcopy(old))
    lint_before = glyph_lint.lint(font, [name])
    font[name] = candidate
    lint_after = glyph_lint.lint(font, [name])
    new_lint = [v for v in lint_after.get(name, []) if v not in lint_before.get(name, [])]
    # Compare thickness through the middle of each axis, not only total area.
    widths = []
    for axis in ("horizontal", "vertical"):
        f = ufoLib2.Font()
        transform = (1, 0, 0, 1, 0, 0) if axis == "horizontal" else (0, 1, -1, 0, 0, 0)
        for label, glyph in (("before", flat_current), ("after", flat)):
            glyph.draw(TransformPen(f.newGlyph(label).getPen(), transform))
        bounds = f["before"].getBounds(f)
        for fraction in (.1, .25, .5, .75, .9):
            y = bounds[1]+fraction*(bounds[3]-bounds[1])
            runs = [[right-left for left, right in derive.stems_at(f, label, y)] for label in ("before", "after")]
            widths.append({"axis": axis, "fraction": fraction, "before_units": runs[0], "after_units": runs[1]})
    return candidate, {"contours": contour_reports, "ink_difference_percent": difference(old, candidate),
                       "ink_area_change_percent": 100*(b.area/a.area-1),
                       "native_bbox_drift_units": max(abs(x-y) for x, y in zip(old.getBounds({}), candidate.getBounds({}))),
                       "before": diagnostics(old), "after": diagnostics(candidate),
                       "stroke_samples": widths, "new_lint_findings": new_lint, "release_ready": False}


def oval_proof(original, candidate, style, name, destination):
    box = original.getBounds({})
    x0, y0, x1, y1 = box
    scale = min(280/(x1-x0), 390/(y1-y0))
    a, b = (derive.to_path(None, rec=record(g)) for g in (original, candidate))
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="560" viewBox="0 0 1080 560">',
             '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
             f'<text x="20" y="30" font-size="23">{style} · {name} · source-guided oval experiment</text>',
             '<text x="20" y="58" font-size="15">Outer and counter fitted separately to bold dimensions. Unaccepted shape study; no source change.</text>']
    for x, title in ((25, "Current"), (375, "Rebuilt oval"), (725, "Overlay")):
        lines.append(f'<text x="{x}" y="93" font-size="17">{title}</text>')
    for path, x, color, opacity in ((a, 25, "#222", 1), (b, 375, "#ad0d78", 1), (a, 725, "#222", .6), (b, 725, "#ad0d78", .45)):
        lines.append(vocabulary.draw(path, x-x0*scale, 500+y0*scale, scale, color, opacity))
    lines.append('<text x="20" y="540" font-size="14">Same em scale. Stroke distribution changes: assess weight and counters, not only smoothness.</text></g></svg>')
    destination.write_text('\n'.join(lines))


def proof(source, current, plain, protected, style, name, method, destination):
    glyphs = [source, current, plain, protected]
    bounds = [g.getBounds({}) for g in glyphs]
    y0, y1 = min(b[1] for b in bounds), max(b[3] for b in bounds)
    scale = min(380/(y1-y0), 280/max(b[2]-b[0] for b in bounds))
    rows = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="570" viewBox="0 0 1400 570">',
            '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">',
            f'<text x="20" y="30" font-size="23">{style} · {html.escape(name)} · {method}</text>',
            '<text x="20" y="57" font-size="15">Construction-stage comparison, not a finished-font replacement. Same em scale; ink aligned for inspection.</text>']
    labels = ["Lighter source", "Current finished outline", "Stage: protection OFF", "Stage: protection ON"]
    for i, (glyph, box, label) in enumerate(zip(glyphs, bounds, labels)):
        x = 20+350*i
        rows.append(f'<text x="{x}" y="90" font-size="16">{label}</text>')
        path = derive.to_path(None, rec=record(glyph))
        rows.append(vocabulary.draw(path, x-box[0]*scale, 490+y0*scale, scale, "#a51076" if i == 3 else "#222"))
        diag = diagnostics(glyph)
        rows.append(f'<text x="{x}" y="525" font-size="13">{len(diag["inflecting_cubics"])} inflecting curves; '
                    f'{len(diag["near_smooth_curve_breaks"])} near-smooth breaks</text>')
    rows.append('<text x="20" y="554" font-size="13">Counts are diagnostic: deliberate S-curves and corners can be valid. Stage columns omit zoning, repairs, spacing and finishing.</text></g></svg>')
    destination.write_text('\n'.join(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=consistency.ROOT / "build/glyph-review/shape-roundness")
    args = parser.parse_args()
    out = consistency.safe_output(args.out)
    out.mkdir(parents=True, exist_ok=True)
    identities = consistency.source_hashes()
    records, sections, ovals, oval_sections = [], [], [], []
    for style, source_style in (("Bold", "Regular"), ("BoldItalic", "Italic")):
        source = ufoLib2.Font.open(consistency.source_paths()[source_style])
        current = ufoLib2.Font.open(consistency.source_paths()[style])
        for name in ("o", "O", "zero"):
            candidate, report = oval_trial(source, current, name)
            filename = f"{style}-{name}-oval.svg"
            oval_proof(current[name], candidate, style, name, out / filename)
            ovals.append({"style": style, "glyph": name, "proof": filename, **report})
            consistency.write_json(out / f"{style}-{name}-oval.json", {"status": "unaccepted isolated outline; not a master", "glyph": json_glyph(candidate)})
            oval_sections.append(f'<article><h2>{style} / {name} / rebuilt oval</h2>'
                                 f'<p>Ink difference {report["ink_difference_percent"]:.2f}%; ink area change {report["ink_area_change_percent"]:+.2f}%.</p>'
                                 f'<a href="{filename}"><img src="{filename}" alt="{style} {name} oval experiment"></a></article>')
        for name in NAMES:
            for method in ("weighted", "rounder"):
                plain = construction(source, name, method, False)
                protected = construction(source, name, method, True)
                filename = f'{style}-{name}-{method}.svg'
                proof(source[name], current[name], plain, protected, style, name, method, out / filename)
                before, after = diagnostics(plain), diagnostics(protected)
                changed = difference(plain, protected)
                row = {"style": style, "glyph": name, "method": method, "ink_difference_percent": changed,
                       "lighter_source": diagnostics(source[name]), "current": diagnostics(current[name]),
                       "unprotected": before, "protected": after, "proof": filename,
                       "already_enabled_in_production_branch": style == "Bold" and (method == "rounder" or name not in make_bold.BOLD_FIT_AS_IS),
                       "release_ready": False}
                records.append(row)
                if changed > .0001:
                    sections.append(f'<article><h2>{style} / {html.escape(name)} / {method}</h2><p>Changed stage ink: {changed:.3f}%. '
                                    f'Inflecting cubics: {len(before["inflecting_cubics"])} → {len(after["inflecting_cubics"])}; '
                                    f'near-smooth breaks: {len(before["near_smooth_curve_breaks"])} → {len(after["near_smooth_curve_breaks"])}.</p>'
                                    f'<a href="{filename}"><img src="{filename}" alt="{style} {html.escape(name)} stage comparison"></a></article>')
        print(f"{style}: completed paired construction experiments", flush=True)
    if consistency.source_hashes() != identities:
        raise RuntimeError("Sources changed during study")
    counts = Counter((r["style"], r["method"]) for r in records if r["ink_difference_percent"] > .0001)
    consistency.write_json(out / "report.json", {"format": "myiadidot-roundness-study-v1", "source_hashes": identities,
                                                "sources_byte_identical": True, "records": records,
                                                "oval_experiments": ovals,
                                                "implementation_sha256": consistency.content_hash(Path(__file__)),
                                                "generator_sha256": consistency.content_hash(Path(make_bold.__file__)),
                                                "derive_sha256": consistency.content_hash(Path(derive.__file__)),
                                                "scope": "22 glyphs, two styles, two independently toggled methods. Not production route selection or full regeneration."})
    (out / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Roundness construction study</title>'
                                    '<style>body{font:16px system-ui;margin:2em}img{width:100%;max-width:1400px}article{border-top:1px solid #aaa;margin-top:2em}</style>'
                                    '<h1>Preventing irregular curves during emboldening</h1>'
                                    '<p>Existing protections compared off/on with identical inputs and weights. Bold already enables them; '
                                    'Bold Italic currently does not. This sheet shows changed stage pairs only; the full report includes every pair. '
                                    'Neither column is an authorised final drawing. No font sources or generators were changed.</p>'
                                    '<p><a href="report.json">Full diagnostic report</a></p>'
                                    '<h2>Separate experiment: reconstruct closed rounds from their lighter sources</h2>'
                                    '<p>Preserves each outer/counter deskewed bounding box. Changes stroke distribution; not a blanket smoothing operation.</p>'
                                    +''.join(oval_sections)+'<h2>Existing generator protections</h2>'+''.join(sections))
    print(dict(counts))


def json_glyph(glyph):
    import json
    return json.loads(glyph.json_dumps())


if __name__ == "__main__":
    main()
