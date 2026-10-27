"""Experimental shape grammar: extract a palette, compose, and measure it.

Read-only with respect to font sources. Outputs a standalone JSON grammar,
SVG proof and metrics for each style. No glyph is installed or accepted.

    .venv/bin/python -I scripts/shape_grammar.py
    .venv/bin/python -I scripts/shape_grammar.py --replay build/glyph-review/shape-grammar/Regular.json

The JSON is executable without a UFO: path and rectangle leaves, named
references, affine transforms, and unions. Extracted paths are deliberately
counted as stored geometry, not claimed to be a minimal geometric basis.
"""

import argparse
import html
import json
import math
import subprocess
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive

ROOT = Path(__file__).resolve().parents[1]
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
UNRESOLVED = ("a", "g", "S", "alpha", "uni0431")
COLORS = ("#2077b4", "#e07b28", "#269b75", "#ab55a1", "#9c8827", "#735cbe")
BIG = 10000


def ref(name):
    return {"op": "ref", "name": name}


def union(*items):
    return {"op": "union", "items": list(items)}


def transform(item, matrix):
    return {"op": "transform", "matrix": list(matrix), "item": item}


def translate(item, dx=0, dy=0):
    return transform(item, (1, 0, 0, 1, dx, dy))


def rectangle(x0, y0, x1, y1):
    return {"op": "rect", "box": [x0, y0, x1, y1]}


def stored_path(path):
    pen = RecordingPen()
    path.draw(pen)
    return {"op": "path", "commands": pen.value}


def evaluate(node, palette, stack=()):
    op = node["op"]
    if op == "ref":
        name = node["name"]
        if name in stack:
            raise ValueError(f"Cyclic shape reference: {stack + (name,)}")
        return evaluate(palette[name]["shape"], palette, stack + (name,))
    if op == "path":
        p = pathops.Path()
        replayRecording(node["commands"], p.getPen())
        return p
    if op == "rect":
        return derive.rect_path(*node["box"])
    if op == "transform":
        return evaluate(node["item"], palette, stack).transform(*node["matrix"])
    if op == "union":
        result = pathops.Path()
        for item in node["items"]:
            result = derive.path_op(result, evaluate(item, palette, stack), "UNION")
        return result
    raise ValueError(f"Unknown shape operation: {op}")


def clip(p, x0=-BIG, y0=-BIG, x1=BIG, y1=BIG):
    return derive.path_op(p, derive.rect_path(x0, y0, x1, y1), "INTERSECTION")


def source_path(font, name):
    return derive.to_path(font, font[name])


def extract(font, source, revision):
    xh, cap = font.info.xHeight, font.info.capHeight
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    # Extraction in an upright frame keeps cut boundaries meaningful in italics.
    upright = ufoLib2.Font()
    for name in ("H", "n", "m", "o", "O", "Pi", "dieresis", "uni0278"):
        p = source_path(font, name).transform(1, 0, -slant, 1, 0, 0)
        p.draw(upright.newGlyph(name).getPen())
    palette = {}

    def add(name, p, origin):
        palette[name] = {"shape": stored_path(p), "origin": origin}

    hp = source_path(upright, "H")
    hs = derive.stems_at(upright, "H", cap * .7)
    if len(hs) != 2:
        raise ValueError(f"Expected two H stems, got {hs}")
    (_, left_end), (right_start, _) = hs
    middle = (left_end + right_start) / 2
    bar = clip(hp, left_end, cap * .25, right_start, cap * .75)
    stems = derive.path_op(hp, bar, "DIFFERENCE")
    add("cap-left", clip(stems, x1=middle), "H, left serifed stem after removing crossbar")
    add("cap-right", clip(stems, x0=middle), "H, right serifed stem after removing crossbar")
    add("crossbar", bar, "H, central crossbar; endpoints measured at 70% cap height")

    np = source_path(upright, "n")
    ns = derive.stems_at(upright, "n", xh * .5)
    if len(ns) != 2:
        raise ValueError(f"Expected two n stems, got {ns}")
    centers = [sum(s) / 2 for s in ns]
    mid = sum(centers) / 2
    cut = xh * .6
    add("leg-left", clip(np, x1=mid, y1=cut), "n, lower left stem and foot")
    add("leg-right", clip(np, x0=mid, y1=cut), "n, lower right stem and foot")
    add("shoulder", clip(np, y0=cut), "n, upper arch INCLUDING entry serif; reuse may need a join variant")
    for name in ("o", "O"):
        add(f"bowl-{name}", source_path(upright, name), f"{name}, whole two-contour bowl; independently drawn per size/style")
    # Keep the two distinct dot drawings: symmetry is a hypothesis, not assumed.
    dots = list(source_path(upright, "dieresis").contours)
    if len(dots) != 2:
        raise ValueError("Dieresis is not two independent contours")
    for i, dot in enumerate(sorted(dots, key=lambda p: p.bounds[0])):
        add(f"dot-{i}", dot, f"dieresis, contour {i}")

    recipes = {}

    def recipe(name, shape, kind, note):
        recipes[name] = {"shape": shape, "kind": kind, "note": note,
                         "advance": font[name].width}

    recipe("H", union(ref("cap-left"), ref("cap-right"), ref("crossbar")),
           "reconstruction", "Partition and reassemble H; a numerical control, not independent prediction.")
    for name in ("O", "o"):
        recipe(name, ref(f"bowl-{name}"), "retained-bowl", "Retains this glyph's entire bowl geometry.")
    recipe("n", union(ref("leg-left"), ref("shoulder"), ref("leg-right")),
           "reconstruction", "Partition and reassemble n; no claim of compression.")

    # Fit only stem positions from m; all its ink comes from the n palette.
    ms = derive.stems_at(upright, "m", xh * .5)
    if len(ms) != 3:
        raise ValueError(f"Expected three m stems, got {ms}")
    mc = [sum(s) / 2 for s in ms]
    arches = []
    for a, b in zip(mc, mc[1:]):
        scale = (b - a) / (centers[1] - centers[0])
        arches.append(transform(ref("shoulder"), (scale, 0, 0, 1, a-scale*centers[0], 0)))
    recipe("m", union(translate(ref("leg-left"), mc[0]-centers[0]), *arches,
                       translate(ref("leg-right"), mc[1]-centers[1]),
                       translate(ref("leg-right"), mc[2]-centers[1])),
           "reuse-trial", "Two n shoulders fitted to m stem centers; no local join corrections.")

    # Existing component placement is a calibrated anchor result, not inferred.
    components = {c.baseGlyph: c.transformation for c in font["odieresis"].components}
    if set(components) != {"o", "dieresis"}:
        raise ValueError("Expected o + dieresis components")

    def upright_component(node, matrix):
        xx, xy, yx, yy, dx, dy = matrix
        if (xx, xy, yx, yy) != (1, 0, 0, 1):
            raise ValueError("Prototype expects translation-only accent components")
        return translate(node, dx-slant*dy, dy)

    recipe("odieresis", union(upright_component(ref("bowl-o"), components["o"]),
                               upright_component(union(ref("dot-0"), ref("dot-1")), components["dieresis"])),
           "reuse-trial", "o + two stored accent dots at existing component positions.")
    ps = derive.stems_at(upright, "Pi", cap * .7)
    if len(ps) != 2:
        raise ValueError("Expected two Pi stems")
    shifts = [sum(p)/2-sum(h)/2 for p, h in zip(ps, hs)]
    bar_runs = derive.vertical_runs(upright, "H", middle)
    if len(bar_runs) != 1:
        raise ValueError(f"Expected one central H crossbar, got {bar_runs}")
    thickness = bar_runs[0][1] - bar_runs[0][0]
    recipe("Pi", union(translate(ref("cap-left"), shifts[0]), translate(ref("cap-right"), shifts[1]),
                        rectangle(ps[0][0], cap-thickness, ps[1][1], cap)),
           "reuse-trial", "H stems at Pi stem centers + top bar of H crossbar thickness.")
    recipe("uni041D", recipes["H"]["shape"], "reuse-trial", "Cyrillic En from Latin H parts.")
    recipe("uni041F", recipes["Pi"]["shape"], "reuse-trial", "Cyrillic Pe from the experimental Pi recipe.")
    ob = source_path(upright, "o").bounds
    pb = source_path(upright, "uni0278").bounds
    cx = (ob[0]+ob[2])/2
    width = ns[0][1]-ns[0][0]
    recipe("uni0278", union(ref("bowl-o"), rectangle(cx-width/2, pb[1], cx+width/2, pb[3])),
           "reuse-trial", "o + plain stem of n thickness; phi height fitted, terminals and counter corrections omitted.")

    for name in UNRESOLVED:
        add(f"unresolved-{name}", source_path(font, name).transform(1, 0, -slant, 1, 0, 0),
            f"{name}, entire outline retained explicitly as an unresolved fallback")
        recipe(name, ref(f"unresolved-{name}"), "unresolved", "No structural decomposition attempted; exact fallback is not evidence of reusable coverage.")
    return {"format": "myiadidot-shape-grammar-experiment-v1", "source": source,
            "revision": revision, "style": font.info.styleName, "upm": font.info.unitsPerEm,
            "xHeight": xh, "capHeight": cap, "slant": slant,
            "palette": palette, "recipes": recipes,
            "calibration": {"H_stems": hs, "n_stems": ns, "m_stems": ms, "Pi_stems": ps,
                            "n_cut": cut, "crossbar_thickness": thickness,
                            "accent_components": {k: list(v) for k, v in components.items()}},
            "reference": {n: stored_path(source_path(font, n)) for n in recipes}}


def leaves(node, palette):
    """Keep palette pieces separate for the coloured construction view."""
    if node["op"] == "union":
        return [p for item in node["items"] for p in leaves(item, palette)]
    if node["op"] == "transform":
        return [p.transform(*node["matrix"]) for p in leaves(node["item"], palette)]
    return [evaluate(node, palette)]


def svg_path(p, x, y, scale, color, opacity=1):
    pen = SVGPathPen(None)
    p.draw(pen)
    return (f'<path d="{pen.getCommands()}" fill="{color}" opacity="{opacity}" '
            f'transform="translate({x},{y}) scale({scale}, {-scale})"/>')


def proof(data, out):
    palette = data["palette"]
    names = list(data["recipes"])
    row_h = 270
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="{150+row_h*len(names)}" viewBox="0 0 1400 {150+row_h*len(names)}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="sans-serif" fill="#222">',
           f'<text x="24" y="32" font-size="23">Shape grammar experiment — {html.escape(data["style"])}</text>',
           '<text x="24" y="57" font-size="14">Source outlines only. Trials are unaccepted. Coloured parts may overlap; overlay: original black, candidate magenta.</text>']
    for x, label in ((220, "Original"), (510, "Grammar parts"), (800, "Overlay"), (1110, "At 24 px/em")):
        svg.append(f'<text x="{x}" y="94" font-size="17">{label}</text>')
    metrics = []
    for i, name in enumerate(names):
        r = data["recipes"][name]
        candidate = evaluate(r["shape"], palette).transform(1, 0, data["slant"], 1, 0, 0)
        original = evaluate(data["reference"][name], {})
        xor = derive.path_op(original, candidate, "XOR").area
        total = derive.path_op(original, candidate, "UNION").area
        error = xor/total*100 if total else 0
        metrics.append({"glyph": name, "kind": r["kind"], "xor_area": xor,
                        "xor_percent_of_union": error, "original_bounds": original.bounds,
                        "candidate_bounds": candidate.bounds, "advance": r["advance"], "note": r["note"]})
        y = 125 + i*row_h
        base = y+157
        svg.extend([f'<path d="M24 {y-14} H1376" stroke="#ddd"/>',
                    f'<text x="24" y="{y+10}" font-size="17">{name}</text>',
                    f'<text x="24" y="{y+33}" font-size="12">{r["kind"]}</text>',
                    f'<text x="24" y="{y+54}" font-size="13">Ink difference: {error:.3f}%</text>'])
        for x in (220, 510, 800):
            svg.append(f'<path d="M{x-10} {base} h250" stroke="#ddd"/>')
        scale = .095 * 2048 / data["upm"]
        svg.append(svg_path(original, 220, base, scale, "#222"))
        for j, p in enumerate(leaves(r["shape"], palette)):
            svg.append(svg_path(p.transform(1, 0, data["slant"], 1, 0, 0), 510, base, scale, COLORS[j % len(COLORS)], .8))
        svg.append(svg_path(original, 800, base, scale, "#222", .7))
        svg.append(svg_path(candidate, 800, base, scale, "#dd168c", .5))
        svg.append(svg_path(original, 1120, y+65, 24/data["upm"], "#222"))
        svg.append(svg_path(candidate, 1170, y+65, 24/data["upm"], "#dd168c"))
        svg.append(f'<text x="24" y="{y+248}" font-size="12">{html.escape(r["note"])}</text>')
    svg.append('</g></svg>')
    out.write_text("\n".join(svg))
    return metrics


def index(report, out):
    rows = []
    for name in ("m", "odieresis", "Pi", "uni041D", "uni041F", "uni0278"):
        cells = "".join(f'<td>{next(r for r in report[s] if r["glyph"] == name)["xor_percent_of_union"]:.3f}%</td>'
                        for s in STYLES)
        rows.append(f"<tr><th>{name}</th>{cells}</tr>")
    links = "".join(f'<li><a href="{s}.svg">{s}: coloured construction proof</a> · '
                    f'<a href="{s}.json">executable grammar JSON</a></li>' for s in STYLES)
    out.write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Myia Didot shape grammar experiment</title>
<style>body{font:17px/1.55 system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#222}
td,th{padding:8px 18px;text-align:right;border-bottom:1px solid #ddd}th:first-child{text-align:left}
a{color:#1767a2}code{background:#eee;padding:2px 5px}</style>
<h1>Can a small shape grammar describe Myia Didot?</h1>
<p>Follow-up: <a href="complete/index.html">the complete geometric grammar and all-glyph catalogue</a>
cover all four styles. The experiment below retains the initial typographic-parts trials.</p>
<p>A first experiment: 15 glyphs in each of four styles. Font sources are unchanged.
Ten reusable stored pieces per style: two capital stems, a crossbar, two lowercase
legs, a shoulder, two bowls and two accent dots. A rectangle adds new straight strokes.</p>
<p><strong>Partial success, not a minimal or complete grammar.</strong> H and n are
partition/reassembly controls; O and o retain their full bowl drawings.
a, g, S, alpha and Cyrillic be are explicitly unresolved whole-outline fallbacks.
The six trials below test reuse beyond the donor letters. Widths and some placements
are calibrated from the target glyphs; this is not automatic design from a character code.</p>
<h2>Inspect the constructions</h2><ul>''' + links + '''</ul>
<p>Each proof shows the original, coloured grammar parts, an overlay, and a 24 px/em
outline comparison. These are not hinted font renders. Magenta in the overlay is
the candidate. Failed trials are deliberately visible and have not been accepted.</p>
<h2>Ink differences</h2><p>Area of the symmetric difference divided by union area.
Zero means geometric agreement within displayed precision, not typographic acceptance.</p>
<table><tr><th>Glyph</th>''' + "".join(f"<th>{s}</th>" for s in STYLES) + "</tr>" + "".join(rows) + '''</table>
<p>Repeating n's shoulder leaves the wrong interior entry and foot in m, especially
in Italic. The phi trial lacks terminal and counter adjustments. The small Pi
differences show that shared structure does not guarantee identical stem drawings.</p>
<p>The next step is a distinction between entry, interior and exit joins, then
separate serif/terminal parts and constrained bowl parameters. No all-font coverage
or reduction in total stored coordinates has yet been established.</p>
<p><a href="metrics.json">Full measurements and notes</a></p></html>''')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/glyph-review/shape-grammar")
    ap.add_argument("--replay", type=Path, help="Render a saved JSON grammar without reading a UFO")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.replay:
        data = json.loads(args.replay.read_text())
        metrics = proof(data, args.out / f"{args.replay.stem}-replay.svg")
        (args.out / f"{args.replay.stem}-replay-metrics.json").write_text(json.dumps(metrics, indent=2)+"\n")
        return
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = {}
    for style in STYLES:
        source = f"sources/MyiaDidot-{style}.ufo"
        font = ufoLib2.Font.open(ROOT / source)
        data = extract(font, source, revision)
        path = args.out / f"{style}.json"
        path.write_text(json.dumps(data, indent=2)+"\n")
        # Exercise the JSON boundary, not just the original Python objects.
        restored = json.loads(path.read_text())
        report[style] = proof(restored, args.out / f"{style}.svg")
        controls = [r for r in report[style] if r["kind"] in ("reconstruction", "retained-bowl", "unresolved")]
        if any(r["xor_percent_of_union"] > .01 for r in controls):
            raise ValueError(f"{style}: reconstruction/serialization control exceeds 0.01% ink difference")
        print(style, ", ".join(f'{r["glyph"]}={r["xor_percent_of_union"]:.3f}%' for r in report[style] if r["kind"] == "reuse-trial"))
    (args.out / "metrics.json").write_text(json.dumps(report, indent=2)+"\n")
    index(report, args.out / "index.html")


if __name__ == "__main__":
    main()
