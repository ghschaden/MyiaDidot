"""Test a small typographic vocabulary against measured anatomical samples.

Read-only source study. Extracts explicitly labelled regions, normalises only
translation, axis scale, declared reflection and stem direction, and compares
actual ink. It does not call a curve compressor a typographic vocabulary.

    .venv/bin/python -I scripts/typographic_vocabulary.py
"""

import argparse
import html
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
import shape_grammar_full

ROOT = Path(__file__).resolve().parents[1]
STYLES = shape_grammar_full.STYLES
ROLES = ("stem", "bar", "diagonal", "shoulder", "return", "bowl", "serif", "dot")
FIVE = {"stem": "straight", "bar": "straight", "diagonal": "straight",
        "shoulder": "turn", "return": "turn", "bowl": "bowl", "serif": "serif", "dot": "dot"}
SIX = {**FIVE, "shoulder": "arch", "return": "round_turn"}
BIG = 10000


def clip(path, box):
    return derive.path_op(path, derive.rect_path(*box), "INTERSECTION")


def normalise(path):
    x0, y0, x1, y1 = path.bounds
    if x1-x0 < 1e-4 or y1-y0 < 1e-4 or path.area <= 0:
        raise ValueError("Empty or degenerate sample")
    return path.transform(1000/(x1-x0), 0, 0, 1000/(y1-y0), -1000*x0/(x1-x0), -1000*y0/(y1-y0))


def distance(a, b):
    union = derive.path_op(a, b, "UNION").area
    # |A xor B| = 2|A union B| - |A| - |B|. Avoid a second boolean operation
    # on nearly coincident boundaries; clamp only negative numerical roundoff.
    return 100 * max(0, 2*union-a.area-b.area) / union if union else 0


def commands(path):
    pen = RecordingPen()
    path.draw(pen)
    return pen.value


def extract(style):
    source = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    font = ufoLib2.Font()
    slant = math.tan(math.radians(-(source.info.italicAngle or 0)))
    names = ("H", "I", "E", "F", "L", "T", "n", "h", "m", "l", "V", "A", "u",
             "o", "O", "zero", "o.sc", "period", "dotaccent", "i", "j", "dieresis", "colon", "hyphen", "minus")
    for name in names:
        derive.to_path(source, source[name]).transform(1, 0, -slant, 1, 0, 0).draw(font.newGlyph(name).getPen())
    xh, cap = source.info.xHeight, source.info.capHeight
    samples = []

    def add(role, name, label, path, extraction, matrix=(1, 0, 0, 1, 0, 0)):
        oriented = path.transform(*matrix)
        samples.append({"id": f"{style}/{name}/{label}", "style": style, "glyph": name,
                        "role": role, "family": SIX[role], "label": label,
                        "extraction": extraction, "orientation": matrix, "bounds": list(path.bounds),
                        "normalised": normalise(oriented), "source_part": path})

    def path(name):
        return derive.to_path(font, font[name])

    def runs(name, y):
        return [(a, b) for a, b in derive.stems_at(font, name, y) if b-a > 20]

    # A small isolated band avoids serif and crossbar contamination. Its own
    # measured centreline direction is removed; taper and curved edges remain.
    def shaft(name, height, pick, role):
        y0, y1 = (height*.50, height*.62) if name == "A" else (height*.28, height*.43)
        middle = runs(name, (y0+y1)/2)
        left, right = middle[pick]
        lo = (middle[pick-1][1]+left)/2 if pick else -BIG
        hi = (right+middle[pick+1][0])/2 if pick+1 < len(middle) else BIG
        region = clip(path(name), (lo, y0, hi, y1))
        low = [(a, b) for a, b in runs(name, y0+.1) if lo < (a+b)/2 < hi]
        high = [(a, b) for a, b in runs(name, y1-.1) if lo < (a+b)/2 < hi]
        if len(low) != 1 or len(high) != 1:
            raise ValueError(f"Ambiguous shaft: {style}/{name}/{pick}")
        slope = (sum(high[0])-sum(low[0]))/2/(y1-y0-.2)
        add(role, name, f"shaft-{pick}", region, {"clip": [lo, y0, hi, y1], "centreline_slope": slope},
            (1, 0, -slope, 1, 0, 0))

    for name, height, picks in (("H", cap, (0, 1)), ("I", cap, (0,)), ("n", xh, (0, 1)),
                                ("h", xh, (0, 1)), ("m", xh, (0, 1, 2)), ("l", xh, (0,))):
        for pick in picks:
            shaft(name, height, pick, "stem")
    for name in ("V", "A"):
        for pick in (0, 1):
            shaft(name, cap, pick, "diagonal")

    for name in ("hyphen", "minus"):
        p = path(name)
        x0, y0, x1, y1 = p.bounds
        box = [x0+(x1-x0)*.25, y0-1, x1-(x1-x0)*.25, y1+1]
        add("bar", name, "bar-interior", clip(p, box), {"clip": box, "excludes": "terminal quarters"}, (0, 1, -1, 0, 0, 0))
    hs = runs("H", cap*.7)
    bar = clip(path("H"), (hs[0][1]+30, cap*.2, hs[1][0]-30, cap*.8))
    add("bar", "H", "crossbar", bar, {"clip": [hs[0][1]+30, cap*.2, hs[1][0]-30, cap*.8]},
        (0, 1, -1, 0, 0, 0))

    # Shoulder samples exclude the entry serif and ascender. Crop boundaries
    # are recorded; these are comparisons of regions, not a complete partition.
    for name in ("n", "h", "m"):
        stems = runs(name, xh*.5)
        for i in range(len(stems)-1):
            x0, x1 = stems[i][1], sum(stems[i+1])/2
            box = [x0, xh*.55, x1, xh+45]
            add("shoulder", name, f"arch-{i}", clip(path(name), box), {"clip": box})
    us = runs("u", xh*.5)
    box = [sum(us[0])/2, -45, us[1][0], xh*.45]
    add("shoulder", "u", "bottom-return", clip(path("u"), box),
        {"clip": box, "role_note": "a stem-to-stem return, oriented as a shoulder"}, (-1, 0, 0, -1, 0, 0))
    for name in ("o", "O", "zero", "o.sc"):
        p = path(name)
        x0, y0, x1, y1 = p.bounds
        box = [x0, y0, x1, (y0+y1)/2]
        add("return", name, "bottom-turn", clip(p, box), {"clip": box}, (-1, 0, 0, -1, 0, 0))
        add("bowl", name, "closed-bowl", p, {"whole": True})

    for name in ("H", "I", "E", "F", "L"):
        stems = runs(name, cap*.3)
        x1 = (stems[0][1]+stems[1][0])/2 if len(stems) > 1 else BIG
        # L/E's bottom arm is not a foot serif: truncate at the symmetric
        # extension of the left serif around the measured stem centre.
        x0 = path(name).bounds[0]
        if name in ("E", "L"):
            x1 = min(x1, sum(stems[0])-x0)
        box = [x0, -45, x1, cap*.085]
        add("serif", name, "left-foot", clip(path(name), box), {"clip": box})
    box = [-BIG, cap*.915, (hs[0][1]+hs[1][0])/2, cap+45]
    add("serif", "H", "left-head", clip(path("H"), box), {"clip": box}, (1, 0, 0, -1, 0, 0))

    for name in ("period", "dotaccent", "i", "j", "dieresis", "colon"):
        contours = sorted(path(name).contours, key=lambda c: (c.bounds[1], c.bounds[0]))
        selected = contours[-1:] if name in ("i", "j") else contours
        for i, contour in enumerate(selected):
            add("dot", name, f"dot-{i}", contour, {"contour_bounds": list(contour.bounds)})
    return samples, shape_grammar_full.digest(json.loads(source.json_dumps()))


def matrix_for(samples):
    result = [[0.0]*len(samples) for _ in samples]
    for i, a in enumerate(samples):
        for j in range(i):
            if a["style"] != samples[j]["style"]:
                continue
            result[i][j] = result[j][i] = distance(a["normalised"], samples[j]["normalised"])
    return result


def medoid(indices, distances):
    return min(indices, key=lambda i: (sum(distances[i][j] for j in indices), i))


def partitions(items):
    """Every unlabelled set partition exactly once (Bell(8) = 4140)."""
    if not items:
        yield ()
        return
    first, *rest = items
    for partition in partitions(rest):
        yield ((first,), *partition)
        for i in range(len(partition)):
            yield (*partition[:i], (first, *partition[i]), *partition[i+1:])


def vocabulary_frontier(samples, distances):
    """Exhaust all ways to merge the eight declared roles, with fixed geometry.

    Select by training error only; report donor-glyph-held-out error separately.
    This is conditional minimality for the stated finite model, not universal
    typographic minimality. Crops, roles, transformations and one template per
    family/style are fixed before the search.
    """
    cache = {}
    for mask in range(1, 1 << len(ROLES)):
        roles = {role for bit, role in enumerate(ROLES) if mask & (1 << bit)}
        train_sum = test_sum = 0
        test_count = 0
        for style in STYLES:
            indices = [i for i, s in enumerate(samples) if s["style"] == style and s["role"] in roles]
            center = medoid(indices, distances)
            train_sum += sum(distances[i][center] for i in indices)
            for glyph in sorted({samples[i]["glyph"] for i in indices}):
                training = [j for j in indices if samples[j]["glyph"] != glyph]
                if not training:
                    continue
                choice = medoid(training, distances)
                targets = [i for i in indices if samples[i]["glyph"] == glyph]
                test_sum += sum(distances[i][choice] for i in targets)
                test_count += len(targets)
        cache[mask] = train_sum, test_sum, test_count
    best, count = {}, 0
    for groups in partitions(list(range(len(ROLES)))):
        count += 1
        masks = [sum(1 << i for i in group) for group in groups]
        loss = sum(cache[mask][0] for mask in masks)/len(samples)
        tests = sum(cache[mask][2] for mask in masks)
        row = {"families": len(groups), "groups": [[ROLES[i] for i in group] for group in groups],
               "mean_error": loss, "held_out_mean": sum(cache[mask][1] for mask in masks)/tests,
               "held_out_samples": tests}
        if len(groups) not in best or loss < best[len(groups)]["mean_error"]:
            best[len(groups)] = row
    baseline = best[len(ROLES)]["mean_error"]
    budgets = [{"extra_error_budget_pp": budget,
                "smallest_family_count": min(k for k, row in best.items() if row["mean_error"] <= baseline+budget)}
               for budget in (.25, .5, 1, 2)]
    return {"partitions_tested": count, "selection": "minimum training ink difference per family count",
            "scope": "all mergers of eight fixed roles, one medoid per family per style",
            "minimum_within_budget": budgets,
            "frontier": [best[k] for k in sorted(best)]}


def evaluate_model(samples, distances, mapping):
    groups = defaultdict(list)
    for i, sample in enumerate(samples):
        groups[sample["style"], mapping[sample["role"]]].append(i)
    rows, errors, heldout = [], [], []
    for (style, family), indices in sorted(groups.items()):
        center = medoid(indices, distances)
        values = [distances[i][center] for i in indices]
        errors.extend(values)
        # Each entire donor glyph is excluded. Multiple parts of that glyph
        # cannot make its own held-out match look artificially successful.
        loo = []
        for i in indices:
            training = [j for j in indices if samples[j]["glyph"] != samples[i]["glyph"]]
            if training:
                choice = medoid(training, distances)
                error = distances[i][choice]
                heldout.append(error)
                loo.append({"sample": samples[i]["id"], "template": samples[choice]["id"], "error": error})
        # Greedy covering counts distinct silhouettes needed at each tolerance;
        # this is an upper bound, not a minimum set-cover solution.
        palettes = {}
        for tolerance in (2, 5, 10):
            uncovered, chosen = set(indices), []
            while uncovered:
                choice = min(indices, key=lambda j: (-sum(distances[i][j] <= tolerance for i in uncovered),
                                                     sum(distances[i][j] for i in uncovered), j))
                chosen.append(choice)
                uncovered = {i for i in uncovered if distances[i][choice] > tolerance}
            palettes[str(tolerance)] = [samples[i]["id"] for i in chosen]
        rows.append({"style": style, "family": family, "samples": len(indices), "template": samples[center]["id"],
                     "mean_error": statistics.mean(values), "worst_error": max(values),
                     "held_out_mean": statistics.mean(v["error"] for v in loo) if loo else None,
                     "held_out": loo, "cover_palettes": palettes})
    return {"families": len(set(mapping.values())), "mean_error": statistics.mean(errors),
            "worst_error": max(errors), "held_out_mean": statistics.mean(heldout),
            "rows": rows}


def model_mappings():
    result = {"eight_roles": {r: r for r in ROLES}, "six_families": SIX, "five_families": FIVE}
    for a, b in (("straight", "serif"), ("straight", "turn"), ("turn", "bowl"), ("bowl", "dot"), ("serif", "dot")):
        result[f"merge_{a}_{b}"] = {r: b if f == a else f for r, f in FIVE.items()}
    return result


def paired_return(path):
    """Two oriented half-bowls: explicit composition, not a new outline leaf."""
    top = path.transform(1, 0, 0, .5, 0, 500)
    bottom = top.transform(-1, 0, 0, -1, 1000, 1000)
    return derive.path_op(top, bottom, "UNION")


def bowl_reduction(samples, distances):
    rows = []
    for sample in samples:
        if sample["role"] != "bowl":
            continue
        turns = [j for j, s in enumerate(samples) if s["style"] == sample["style"] and s["role"] == "return"]
        own = next(j for j in turns if samples[j]["glyph"] == sample["glyph"])
        others = [j for j in turns if samples[j]["glyph"] != sample["glyph"]]
        choice = medoid(others, distances)
        rows.append({"sample": sample["id"], "half": samples[own]["id"], "held_out_half": samples[choice]["id"],
                     "own_half_error": distance(sample["normalised"], paired_return(samples[own]["normalised"])),
                     "held_out_error": distance(sample["normalised"], paired_return(samples[choice]["normalised"]))})
    return {"rule": "bowl = top(round_turn) UNION rotate180(top(round_turn))",
            "own_half_mean": statistics.mean(r["own_half_error"] for r in rows),
            "held_out_mean": statistics.mean(r["held_out_error"] for r in rows), "rows": rows}


def draw(path, x, baseline, scale, color, opacity=1):
    pen = SVGPathPen(None)
    path.draw(pen)
    return f'<path d="{pen.getCommands()}" transform="translate({x},{baseline}) scale({scale},{-scale})" fill="{color}" opacity="{opacity}"/>'


def proofs(samples, models, reduction, directory):
    by_id = {s["id"]: s for s in samples}
    rows = models["six_families"]["rows"]
    for style in STYLES:
        subset = [s for s in samples if s["style"] == style]
        cols, width, cell_h = 5, 1500, 280
        height = 100 + math.ceil(len(subset)/cols)*cell_h
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
               '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
               f'<text x="24" y="30" font-size="23">Typographic vocabulary — {style}</text>',
               '<text x="24" y="56" font-size="15">Six-family model. Black: measured region. Magenta: family medoid. Regions normalised to a square; not a font proof.</text>']
        for i, sample in enumerate(subset):
            row = next(r for r in rows if r["style"] == style and r["family"] == sample["family"])
            donor = by_id[row["template"]]
            error = distance(sample["normalised"], donor["normalised"])
            x, y = 24+(i % cols)*300, 105+(i//cols)*cell_h
            svg.extend([f'<text x="{x}" y="{y}" font-size="15">{sample["glyph"]}/{sample["label"]}</text>',
                        f'<text x="{x}" y="{y+22}" font-size="13">{sample["role"]} → {sample["family"]}; {error:.1f}%</text>',
                        draw(sample["normalised"], x+20, y+220, .17, "#222", .75),
                        draw(donor["normalised"], x+20, y+220, .17, "#d21d8e", .45),
                        f'<text x="{x}" y="{y+245}" font-size="11">Template: {donor["glyph"]}/{donor["label"]}</text>'])
        svg.append('</g></svg>')
        (directory / f"{style}.svg").write_text("\n".join(svg))

    # Context proof shows precisely where each sample came from, rather than
    # relying solely on a normalised silhouette to establish its role.
    for style in STYLES:
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
        names = ("H", "n", "m", "u", "V", "o", "O", "zero", "I", "i")
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">',
               '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
               f'<text x="24" y="35" font-size="24">Anatomical sampling in context — {style}</text>',
               '<text x="24" y="62" font-size="15">Grey: source. Blue: straight; green: shoulder; teal: rounded return; purple: bowl; orange: serif; red: dot. Regions may overlap.</text>']
        colors = {"straight": "#237bbc", "arch": "#2a9d64", "round_turn": "#238b97", "bowl": "#8855bc", "serif": "#dc8524", "dot": "#ce3659"}
        for i, name in enumerate(names):
            x, baseline = 24+(i % 5)*315, 480+(i//5)*500
            scale = .16
            svg.append(f'<text x="{x}" y="{baseline-300}" font-size="19">{name}</text>')
            svg.append(draw(derive.to_path(font, font[name]), x, baseline, scale, "#bbb"))
            for sample in samples:
                if sample["style"] == style and sample["glyph"] == name:
                    svg.append(draw(sample["source_part"].transform(1, 0, slant, 1, 0, 0), x, baseline, scale,
                                    colors[sample["family"]], .65))
        svg.append('</g></svg>')
        (directory / f"{style}-context.svg").write_text("\n".join(svg))

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1420" viewBox="0 0 1400 1420">',
           '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
           '<text x="24" y="32" font-size="23">Can a bowl be made from two copies of one rounded return?</text>',
           '<text x="24" y="57" font-size="15">Normalised outlines. Original black; two-half construction magenta. This tests within-glyph symmetry, not independent prediction.</text>']
    for i, row in enumerate(reduction["rows"]):
        sample, half = by_id[row["sample"]], by_id[row["half"]]
        x, y = 24+(i % 4)*350, 110+(i//4)*320
        svg.extend([f'<text x="{x}" y="{y}" font-size="16">{sample["style"]}/{sample["glyph"]}</text>',
                    f'<text x="{x}" y="{y+24}" font-size="14">Own half: {row["own_half_error"]:.2f}%; other glyph: {row["held_out_error"]:.2f}%</text>',
                    draw(sample["normalised"], x+40, y+260, .20, "#222", .8),
                    draw(paired_return(half["normalised"]), x+40, y+260, .20, "#d21d8e", .4)])
    svg.append('</g></svg>')
    (directory / "bowl-reduction.svg").write_text("\n".join(svg))

    families = ("straight", "arch", "round_turn", "bowl", "serif", "dot")
    labels = ("Straight stroke", "Shoulder", "Rounded return", "Bowl", "Serif", "Dot")
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1200" viewBox="0 0 1500 1200">',
           '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
           '<text x="24" y="32" font-size="24">Six measured typographic families</text>',
           '<text x="24" y="58" font-size="15">Representative silhouettes, each fitted to a square. The families need parameters and contextual variants.</text>']
    for col, label in enumerate(labels):
        svg.append(f'<text x="{24+col*250}" y="96" font-size="18">{label}</text>')
    for row_index, style in enumerate(STYLES):
        top = 140+row_index*260
        svg.append(f'<text x="24" y="{top}" font-size="16">{style}</text>')
        for col, family in enumerate(families):
            row = next(r for r in rows if r["style"] == style and r["family"] == family)
            sample = by_id[row["template"]]
            x = 24+col*250
            svg.append(draw(sample["normalised"], x+20, top+200, .16, colors[family]))
            svg.append(f'<text x="{x}" y="{top+225}" font-size="12">{sample["glyph"]}/{sample["label"]}</text>')
    svg.append('</g></svg>')
    (directory / "vocabulary.svg").write_text("\n".join(svg))


def overview(samples, models, reduction, frontier, directory):
    rows = "".join(f'<tr><td>{html.escape(name)}</td><td>{m["families"]}</td><td>{m["mean_error"]:.2f}%</td>'
                   f'<td>{m["held_out_mean"]:.2f}%</td><td>{m["worst_error"]:.2f}%</td></tr>' for name, m in models.items())
    links = "".join(f'<li>{s}: <a href="{s}-context.svg">parts in context</a> · <a href="{s}.svg">normalised comparisons</a></li>' for s in STYLES)
    frontier_rows = "".join(f'<tr><td>{r["families"]}</td><td>{r["mean_error"]:.2f}%</td><td>{r["held_out_mean"]:.2f}%</td>'
                            f'<td>{html.escape(" | ".join(" + ".join(g) for g in r["groups"]))}</td></tr>' for r in frontier["frontier"])
    (directory / "index.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Minimal typographic vocabulary study</title>
<style>body{font:18px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#222}td,th{padding:8px 15px;border-bottom:1px solid #ddd;text-align:left}a{color:#1767a2}</style>
<h1>A small typographic vocabulary for Myia Didot</h1>
<p>Best-supported working vocabulary: <strong>straight stroke, shoulder, rounded return, bowl, serif, dot</strong>.
Eight anatomical roles are compared with six and five flat families, then selected four-family reductions.
Parameters and contextual joins remain necessary; six families do not mean six fixed silhouettes.</p>
<p>SAMPLES labelled regions across all four styles. Source fonts are unchanged.
The corpus samples Latin anatomy; it does not establish coverage of every script or symbol.</p>
<h2>Inspect the evidence</h2><p><a href="vocabulary.svg">The six families across all four styles</a></p><ul>LINKS</ul>
<p><a href="bowl-reduction.svg">Bowl composition experiment</a>: own-half mean error OWN_ERROR%;
using a held-out donor glyph's return gives HELD_ERROR%. Symmetry is not universal.</p>
<h2>One measured template per family per style</h2>
<p>Templates are medoids selected to minimise mean symmetric ink difference. Regions are independently
scaled to a unit square after removing their declared orientation and centreline direction.
The diagnostic is XOR area / union area; it is not a perceptual acceptance threshold.</p>
<table><tr><th>Model</th><th>Families</th><th>Mean error</th><th>Held-out glyph mean</th><th>Worst</th></tr>ROWS</table>
<h2>Exhaustive merger search</h2><p>All 4,140 partitions of the eight fixed roles were tested.
For each family count, select the partition with lowest training error, then report its held-out error.
This is an exact search within this finite model, not a proof over every possible typographic vocabulary.</p>
<table><tr><th>Families</th><th>Mean error</th><th>Held-out mean</th><th>Best grouping</th></tr>FRONTIER_ROWS</table>
<p>Six is the smallest family count within 0.25, 0.5, 1 or 2 percentage points of the eight-role
training error. These are explicit study budgets, not perceptual acceptance thresholds.</p>
<p>Held-out evaluation excludes every region from the target's donor glyph, then selects the training
medoid. It does not exclude separately encoded identical designs or related generator sources.
Region selection and normalisation remain author-specified.</p>
<p>The detailed report also estimates how many measured silhouettes cover each family at 2%, 5% and
10% ink difference. These are greedy upper bounds, not a proof of the minimum palette size.</p>
<p><a href="report.json">Measurements, held-out comparisons and palette sizes</a> ·
<a href="samples.json">All samples, labels, crop bounds and geometry</a> ·
<a href="vocabulary.json">Six-family exemplar library</a></p></html>'''
        .replace("FRONTIER_ROWS", frontier_rows).replace("ROWS", rows).replace("LINKS", links).replace("SAMPLES", str(len(samples)))
        .replace("OWN_ERROR", f'{reduction["own_half_mean"]:.2f}').replace("HELD_ERROR", f'{reduction["held_out_mean"]:.2f}'))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/glyph-review/typographic-vocabulary")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    samples, fingerprints = [], {}
    for style in STYLES:
        extracted, fingerprints[style] = extract(style)
        samples.extend(extracted)
        print(style, dict(Counter(s["role"] for s in extracted)), flush=True)
    distances = matrix_for(samples)
    models = {name: evaluate_model(samples, distances, mapping) for name, mapping in model_mappings().items()}
    reduction = bowl_reduction(samples, distances)
    frontier = vocabulary_frontier(samples, distances)
    report = {"source_fingerprints": fingerprints, "sample_count": len(samples), "models": models,
              "bowl_reduction": reduction, "frontier": frontier,
              "metric": "100 * area(XOR) / area(UNION); normalised regions",
              "limitations": ["Author-selected anatomical crops", "No full-glyph generation or all-script coverage",
                              "Glyph-held-out evaluation does not exclude related designs", "No perceptual acceptance threshold"]}
    (args.out / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    serialised = [{**s, "normalised": commands(s["normalised"]), "source_part": commands(s["source_part"])} for s in samples]
    (args.out / "samples.json").write_text(json.dumps(serialised, indent=2)+"\n")
    by_id = {s["id"]: s for s in serialised}
    library = {"format": "myiadidot-typographic-exemplars-v1",
               "status": "Measured family exemplars, not universal generating templates",
               "normalisation": "Ink bounding box fitted to 1000 x 1000 after recorded orientation changes",
               "families": {}}
    for row in models["six_families"]["rows"]:
        entry = library["families"].setdefault(row["family"], {"roles": [r for r in ROLES if SIX[r] == row["family"]], "styles": {}})
        entry["styles"][row["style"]] = {"representative": by_id[row["template"]],
                                          "five_percent_palette": [by_id[name] for name in row["cover_palettes"]["5"]]}
    (args.out / "vocabulary.json").write_text(json.dumps(library, indent=2)+"\n")
    proofs(samples, models, reduction, args.out)
    overview(samples, models, reduction, frontier, args.out)
    for name, result in models.items():
        print(f'{name}: mean={result["mean_error"]:.2f}%, held-out={result["held_out_mean"]:.2f}%, worst={result["worst_error"]:.2f}%')


if __name__ == "__main__":
    main()
