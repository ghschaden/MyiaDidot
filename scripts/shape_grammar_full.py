"""Compile all four source styles into a standalone, exact shape grammar.

The only drawing primitives are relative LINE and CUBIC. Repeated translations
of fragments share productions, mined by deterministic adjacent-pair factoring.
Contours stitch productions; glyphs compose contours and transformed glyphs.
No whole-outline/path escape hatch or reference UFO is used by the decoder.

    .venv/bin/python -I scripts/shape_grammar_full.py
    .venv/bin/python -I scripts/shape_grammar_full.py replay GRAMMAR.json --out DIR
"""

import argparse
import copy
import hashlib
import html
import json
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from ufoLib2.objects import Glyph

ROOT = Path(__file__).resolve().parents[1]
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
FORMAT = "myiadidot-complete-shape-grammar-v1"
COLORS = ("#2675b9", "#ca6b20", "#229879", "#a4479c", "#8a7925", "#6859ad")


def dump(value, path):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def digest(value):
    # UFO coordinates may serialise as 12 or 12.0; those are the same value.
    def canonical(item):
        if isinstance(item, dict):
            return {k: canonical(v) for k, v in item.items()}
        if isinstance(item, list):
            return [canonical(v) for v in item]
        if isinstance(item, float) and item.is_integer():
            return int(item)
        return item

    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def decimal(value):
    return Decimal(str(value))


def number(value):
    """An exact decimal string, not a binary floating-point subtraction."""
    return format(value.normalize(), "f") if value else "0"


def encode_contour(contour, intern):
    pen = RecordingPen()
    contour.draw(pen)
    start = pen.value[0]
    if start[0] != "moveTo" or pen.value[-1][0] not in ("closePath", "endPath"):
        raise ValueError("Unsupported contour structure")
    origin = [number(decimal(v)) for v in start[1][0]]
    cursor = tuple(map(decimal, origin))
    sequence = []
    for op, points in pen.value[1:-1]:
        if (op, len(points)) not in (("lineTo", 1), ("curveTo", 3)):
            raise ValueError(f"Unsupported primitive: {op} {points}")
        coordinates = []
        for point in points:
            coordinates.extend(number(decimal(v)-c) for v, c in zip(point, cursor))
        sequence.append(intern(("L" if op == "lineTo" else "C", *coordinates)))
        cursor = tuple(map(decimal, points[-1]))
    # Preserve point names/smooth flags/identifiers separately, with no geometry.
    meta = json.loads(contour.json_dumps())
    point_meta = [{k: v for k, v in p.items() if k not in ("x", "y", "type")} for p in meta.pop("points")]
    return {"origin": origin, "rules": sequence, "closed": pen.value[-1][0] == "closePath",
            "metadata": meta, "point_metadata": point_meta}


def factor(sequences, rules, limit):
    """Greedy dictionary grammar: replace frequent pairs, never alter geometry."""
    added = 0
    while limit is None or added < limit:
        counts = Counter()
        for seq in sequences:
            previous, used = None, False
            for pair in zip(seq, seq[1:]):
                if pair[0] == pair[1] and pair == previous and used:
                    used = False
                else:
                    counts[pair] += 1
                    used = True
                previous = pair
        if not counts:
            break
        pair, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
        if count < 4:
            break
        name = f"r{added:04d}"
        replacements = 0
        for seq in sequences:
            result = []
            i = 0
            while i < len(seq):
                if i+1 < len(seq) and (seq[i], seq[i+1]) == pair:
                    result.append(name)
                    replacements += 1
                    i += 2
                else:
                    result.append(seq[i])
                    i += 1
            seq[:] = result
        if not replacements:
            raise ValueError("Factoring failed to make progress")
        rules[name] = {"join": list(pair)}
        added += 1
        if added % 256 == 0:
            print(f"Factored {added} shared fragments; next pair frequency {count}", flush=True)
    return added


def extract(source_dir, max_rules=None):
    rules, atoms, styles, sequences, originals = {}, {}, {}, [], {}

    def intern(atom):
        if atom not in atoms:
            name = f"p{len(atoms):05d}"
            atoms[atom] = name
            rules[name] = {"primitive": atom[0], "parameters": list(atom[1:])}
        return atoms[atom]

    for style in STYLES:
        source = source_dir / f"MyiaDidot-{style}.ufo"
        font = ufoLib2.Font.open(source)
        snapshot = json.loads(font.json_dumps())
        originals[style] = snapshot
        template = copy.deepcopy(snapshot)
        # Font/layer metadata, anchors, features, metrics and components survive
        # the round trip. Only actual contour geometry is replaced by grammar.
        layers = []
        for layer_index, layer in enumerate(font.layers):
            recipes = {}
            for glyph in sorted(layer, key=lambda g: g.name):
                metadata = copy.deepcopy(snapshot["layers"][layer_index]["glyphs"][glyph.name])
                metadata.pop("contours", None)
                components = metadata.pop("components", [])
                contours = [encode_contour(c, intern) for c in glyph.contours]
                for contour in contours:
                    sequences.append(contour["rules"])
                recipes[glyph.name] = {"contours": contours, "components": components, "metadata": metadata}
            template["layers"][layer_index]["glyphs"] = {}
            layers.append({"name": layer.name, "glyphs": recipes})
        styles[style] = {"source_sha256": digest(snapshot), "font_metadata": template, "layers": layers}
        print(f"Extracted {style}: {len(font)} glyphs", flush=True)
    raw_references = sum(map(len, sequences))
    added = factor(sequences, rules, max_rules)
    grammar = {"format": FORMAT, "primitives": {"L": "line(dx,dy)", "C": "cubic(dx1,dy1,dx2,dy2,dx3,dy3)"},
               "rules": rules, "styles": styles,
               "construction": {"method": "exact decimal relative segments + greedy repeated-pair factoring",
                                "raw_segment_occurrences": raw_references, "atomic_rules": len(atoms),
                                "fragment_rules": added, "contour_rule_references": sum(map(len, sequences)),
                                "fragment_reference_limit": max_rules}}
    return grammar, originals


class Decoder:
    def __init__(self, grammar):
        if grammar.get("format") != FORMAT:
            raise ValueError("Unsupported grammar format")
        self.grammar = grammar
        self.rules = grammar["rules"]
        self.expanded = {}
        self.validate_rules()

    def validate_rules(self):
        visited, active = set(), set()

        def visit(name):
            if name in active:
                raise ValueError(f"Cyclic fragment rule: {name}")
            if name in visited:
                return
            if name not in self.rules:
                raise ValueError(f"Missing fragment rule: {name}")
            active.add(name)
            rule = self.rules[name]
            if set(rule) == {"join"}:
                if len(rule["join"]) != 2:
                    raise ValueError("A join rule requires two children")
                for child in rule["join"]:
                    visit(child)
            elif set(rule) == {"primitive", "parameters"}:
                size = {"L": 2, "C": 6}.get(rule["primitive"])
                if size is None or len(rule["parameters"]) != size:
                    raise ValueError(f"Invalid primitive rule: {name}")
                if not all(decimal(v).is_finite() for v in rule["parameters"]):
                    raise ValueError("Non-finite coordinate")
            else:
                raise ValueError(f"Invalid rule: {name}")
            active.remove(name)
            visited.add(name)

        for name in self.rules:
            visit(name)

    def expand(self, name):
        if name in self.expanded:
            return self.expanded[name]
        rule = self.rules[name]
        if "join" in rule:
            result = tuple(atom for child in rule["join"] for atom in self.expand(child))
        else:
            result = ((rule["primitive"], tuple(map(decimal, rule["parameters"]))),)
        self.expanded[name] = result
        return result

    def draw_fragment(self, names, cursor, pen):
        for name in names:
            for op, values in self.expand(name):
                points = [(cursor[0]+values[i], cursor[1]+values[i+1]) for i in range(0, len(values), 2)]
                getattr(pen, "lineTo" if op == "L" else "curveTo")(*[tuple(map(float, p)) for p in points])
                cursor = points[-1]
        return cursor

    def contour(self, recipe):
        cursor = tuple(map(decimal, recipe["origin"]))
        g = Glyph()
        pen = g.getPen()
        pen.moveTo(tuple(map(float, cursor)))
        self.draw_fragment(recipe["rules"], cursor, pen)
        getattr(pen, "closePath" if recipe["closed"] else "endPath")()
        if len(g.contours) != 1:
            raise ValueError("Contour did not decode to one contour")
        result = json.loads(g.contours[0].json_dumps())
        if len(result["points"]) != len(recipe["point_metadata"]):
            raise ValueError("Decoded point count differs from metadata")
        for point, metadata in zip(result["points"], recipe["point_metadata"]):
            # SegmentToPointPen guesses smoothness; source metadata is authoritative.
            for key in list(point):
                if key not in ("x", "y", "type"):
                    del point[key]
            point.update(metadata)
        result.update(recipe["metadata"])
        return result

    def font(self, style):
        data = self.grammar["styles"][style]
        result = copy.deepcopy(data["font_metadata"])
        for index, layer in enumerate(data["layers"]):
            recipes = layer["glyphs"]
            self.validate_components(recipes)
            glyphs = {}
            for name, recipe in recipes.items():
                glyph = copy.deepcopy(recipe["metadata"])
                if recipe["contours"]:
                    glyph["contours"] = [self.contour(c) for c in recipe["contours"]]
                if recipe["components"]:
                    glyph["components"] = copy.deepcopy(recipe["components"])
                glyphs[name] = glyph
            result["layers"][index]["glyphs"] = glyphs
        return ufoLib2.Font.json_loads(json.dumps(result))

    @staticmethod
    def validate_components(recipes):
        visited, active = set(), set()

        def visit(name):
            if name not in recipes:
                raise ValueError(f"Missing component glyph: {name}")
            if name in active:
                raise ValueError(f"Cyclic component glyph: {name}")
            if name in visited:
                return
            active.add(name)
            for component in recipes[name]["components"]:
                visit(component["baseGlyph"])
            active.remove(name)
            visited.add(name)

        for name in recipes:
            visit(name)


def validate(grammar, originals=None, export_dir=None):
    decoder = Decoder(grammar)
    reports, fonts = {}, {}
    for style, data in grammar["styles"].items():
        font = decoder.font(style)
        snapshot = json.loads(font.json_dumps())
        actual_hash = digest(snapshot)
        if actual_hash != data["source_sha256"]:
            if originals:
                expected = originals[style]
                for a, b in zip(expected["layers"], snapshot["layers"]):
                    for name in a["glyphs"]:
                        if a["glyphs"][name] != b["glyphs"][name]:
                            raise ValueError(f"Round-trip mismatch: {style}/{name}")
            raise ValueError(f"Round-trip font content mismatch: {style}")
        if originals and snapshot != originals[style]:
            raise ValueError(f"Independent full-object comparison failed: {style}")
        if export_dir:
            destination = export_dir / f"MyiaDidot-{style}.ufo"
            font.save(destination, overwrite=True)
            reopened = ufoLib2.Font.open(destination)
            if digest(json.loads(reopened.json_dumps())) != actual_hash:
                raise ValueError(f"Saved UFO round-trip mismatch: {style}")
        stats = Counter()
        for layer in data["layers"]:
            for recipe in layer["glyphs"].values():
                stats["glyphs"] += 1
                stats["contours"] += len(recipe["contours"])
                stats["components"] += len(recipe["components"])
                stats["points"] += sum(len(c["point_metadata"]) for c in recipe["contours"])
                stats["empty_glyphs"] += not recipe["contours"] and not recipe["components"]
                stats["open_contours"] += sum(not c["closed"] for c in recipe["contours"])
                stats["glyphs_with_components"] += bool(recipe["components"])
        reports[style] = {**stats, "exact_source_match": True, "sha256": actual_hash}
        fonts[style] = font
        print(f"Validated {style}: {stats['glyphs']} glyphs, {stats['points']} points, exact font content", flush=True)
    return reports, fonts


def statistics(grammar):
    decoder = Decoder(grammar)
    uses, styles_by_rule, contour_types, examples = Counter(), {}, Counter(), {}
    contour_instances = 0
    for style, data in grammar["styles"].items():
        for layer in data["layers"]:
            for name, recipe in layer["glyphs"].items():
                for contour in recipe["contours"]:
                    contour_instances += 1
                    signature = tuple(contour["rules"]), contour["closed"]
                    contour_types[signature] += 1
                    for rule in contour["rules"]:
                        uses[rule] += 1
                        styles_by_rule.setdefault(rule, set()).add(style)
                        examples.setdefault(rule, [])
                        if len(examples[rule]) < 4:
                            examples[rule].append(f"{style}/{name}")
    raw = grammar["construction"]["raw_segment_occurrences"]
    refs = sum(uses.values())
    atom_numbers = sum(len(r.get("parameters", [])) for r in grammar["rules"].values())
    raw_numbers = sum(len(params) for data in grammar["styles"].values() for layer in data["layers"]
                      for recipe in layer["glyphs"].values() for c in recipe["contours"]
                      for rule in c["rules"] for _, params in decoder.expand(rule))
    motifs = [{"rule": r, "uses_in_contours": n, "segments": len(decoder.expand(r)),
               "styles": sorted(styles_by_rule[r]), "examples": examples[r]}
              for r, n in uses.most_common() if "join" in grammar["rules"][r]]
    return {**grammar["construction"], "contour_instances": contour_instances,
            "distinct_relative_contour_recipes": len(contour_types),
            "raw_coordinate_parameters": raw_numbers, "stored_primitive_parameters": atom_numbers,
            "fragment_definition_references": 2*grammar["construction"]["fragment_rules"],
            "top_level_reference_reduction_percent": 100*(raw-refs)/raw,
            "rules_used_directly_in_multiple_styles": sum(len(s) > 1 for s in styles_by_rule.values()),
            "motifs": motifs}


def glyph_svg(glyph, font, size=180):
    pen = SVGPathPen(font)
    glyph.draw(pen)
    bounds = glyph.getBounds(font)
    if bounds is None:
        bounds = (0, 0, max(glyph.width, 1), 1000)
    x0, y0, x1, y1 = bounds
    scale = min((size-28)/max(x1-x0, 1), (size-28)/max(y1-y0, 1))
    tx = size/2-(x0+x1)*scale/2
    ty = size/2+(y0+y1)*scale/2
    return (f'<svg viewBox="0 0 {size} {size}" aria-label="{html.escape(glyph.name)}">'
            f'<path d="{pen.getCommands()}" transform="translate({tx},{ty}) scale({scale}, {-scale})"/></svg>')


def catalogue(grammar, fonts, reports, stats, directory):
    """Self-contained, searchable local HTML; no server, fetch or font dependency."""
    directory.mkdir(parents=True, exist_ok=True)
    for style, font in fonts.items():
        recipes = grammar["styles"][style]["layers"][0]["glyphs"]
        cards = []
        for name in sorted(recipes):
            g = font[name]
            codes = " ".join(f"U+{u:04X}" for u in g.unicodes)
            rule_names = list(dict.fromkeys(r for c in recipes[name]["contours"] for r in c["rules"]))
            buttons = " ".join(f'<button type="button" data-rule="{r}">{r}</button>' for r in rule_names)
            bases = " ".join(html.escape(c["baseGlyph"]) for c in recipes[name]["components"])
            card = (f'<article data-search="{html.escape(name + " " + codes + " " + "".join(chr(u) for u in g.unicodes), quote=True)}">'
                    f'<h2>{html.escape(name)}</h2>{glyph_svg(g, font)}<p>{codes or "Unencoded glyph"}</p>'
                    f'<details><summary>Inspect boundary fragments</summary>{buttons or "No direct contours."}'
                    f'{"<p>Components: " + bases + "</p>" if bases else ""}</details>'
                    f'<details><summary>Construction recipe</summary><pre>{html.escape(json.dumps(recipes[name], indent=2))}</pre></details></article>')
            cards.append(card)
        page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Shape grammar STYLE</title>
<style>body{font:16px/1.5 system-ui;margin:24px;color:#222}header{position:sticky;top:0;background:white;padding:12px;z-index:1}
input{font:inherit;padding:10px;width:min(80%,540px)}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
article{border:1px solid #ddd;padding:14px;min-width:0}article svg{width:100%;height:180px}h2{font-size:16px;overflow-wrap:anywhere}
pre{overflow:auto;max-height:400px;font-size:12px}a{color:#1767a2}[hidden]{display:none}
button{margin:3px;padding:5px;cursor:pointer}dialog{width:min(650px,90%);border:1px solid #aaa}dialog svg{width:100%;height:220px}</style>
<header><a href="index.html">All styles and verification</a><h1>STYLE — complete glyph grammar</h1>
<p>All drawings reconstructed from LINE/CUBIC productions and component recipes. Each preview fits its own box; it is not a spacing proof.</p>
<input id="search" placeholder="Find a glyph: name, character, or U+ code" aria-label="Filter glyphs"><span id="count"></span></header>
<main>CARDS</main>
<dialog id="fragment"><button id="close-dialog">Close</button><h2 id="rule-name"></h2>
<p>A directed contour fragment. Curves describe the boundary of ink; this preview does not fill them.</p>
<svg id="rule-preview"><path fill="none" stroke="#2675b9" stroke-width="2" vector-effect="non-scaling-stroke"/></svg><pre id="rule-definition"></pre></dialog>
<script type="application/json" id="rules-data">RULES_DATA</script><script>
const cards=[...document.querySelectorAll('article')], input=document.querySelector('#search');
function filter(){let n=0,q=input.value.toLowerCase();for(const c of cards){c.hidden=!c.dataset.search.toLowerCase().includes(q);if(!c.hidden)n++}document.querySelector('#count').textContent=' '+n+' glyphs'}
input.addEventListener('input',filter);filter();
const rules=JSON.parse(document.querySelector('#rules-data').textContent), dialog=document.querySelector('#fragment');
function expand(name){const r=rules[name];return r.join?r.join.flatMap(expand):[r]}
document.addEventListener('click',event=>{const name=event.target.dataset.rule;if(!name)return;
let x=0,y=0,xs=[0],ys=[0],d='M0 0';
for(const r of expand(name)){const a=r.parameters.map(Number),pts=[];for(let i=0;i<a.length;i+=2){pts.push(x+a[i],y+a[i+1]);xs.push(x+a[i]);ys.push(y+a[i+1])}d+=' '+r.primitive+' '+pts.join(' ');x=pts.at(-2);y=pts.at(-1)}
const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),pad=Math.max(x1-x0,y1-y0,1)*.1;
const svg=document.querySelector('#rule-preview');svg.setAttribute('viewBox',`${x0-pad} ${-y1-pad} ${x1-x0+2*pad} ${y1-y0+2*pad}`);
const path=svg.querySelector('path');path.setAttribute('d',d);path.setAttribute('transform','scale(1,-1)');
document.querySelector('#rule-name').textContent=name;
document.querySelector('#rule-definition').textContent=JSON.stringify({rule:rules[name],expanded:expand(name)},null,2);dialog.showModal();});
document.querySelector('#close-dialog').addEventListener('click',()=>dialog.close());
</script></html>'''.replace("STYLE", html.escape(style)).replace("CARDS", "\n".join(cards))
        page = page.replace("RULES_DATA", json.dumps(grammar["rules"], separators=(",", ":")))
        (directory / f"{style}.html").write_text(page)
    rows = "".join(f'<tr><td><a href="{s}.html">{s}</a></td><td>{r["glyphs"]}</td><td>{r["contours"]}</td>'
                   f'<td>{r["components"]}</td><td>Exact</td></tr>' for s, r in reports.items())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Complete Myia Didot shape grammar</title>
<style>body{font:18px/1.6 system-ui;max-width:1050px;margin:40px auto;padding:0 24px;color:#222}td,th{padding:10px 20px;border-bottom:1px solid #ddd;text-align:left}a{color:#1767a2}code{background:#eee;padding:2px 5px}</style>
<h1>Myia Didot: a complete geometric shape grammar</h1>
<p>Every glyph in all four styles is reconstructed from two parameterised drawing primitives:
<strong>straight line</strong> and <strong>cubic Bézier curve</strong>. Repeated fragments form shared rules;
rules form directed contours; glyphs combine contours and affine component references.</p>
<p><strong>No whole-outline fallback.</strong> All contour points, component transforms, widths, anchors,
character mappings, feature code and other serialised font data round-trip exactly. The grammar decoder
does not read the original fonts. The original production sources remain unchanged.</p>
<table><tr><th>Browse every recipe</th><th>Glyphs</th><th>Contours</th><th>Components</th><th>Round trip</th></tr>ROWS</table>
<h2>Shared constructions</h2><p>ATOMS distinct primitive parameter sets and MOTIFS shared fragment rules
represent RAW segment occurrences using REFS contour references. The full accounting is in the report;
this is deterministic factoring, not a proof of globally minimal description length.</p>
<p><a href="fragments.svg">Shared fragment atlas</a> · <a href="specimen.svg">Same-scale four-style specimen</a></p>
<p>This is a complete <em>geometric</em> grammar of the current designs. It is not a claim that two
fixed silhouettes, or a handful of identical stems and bowls, generate every letter. Curves carry
parameters, and style-specific optical decisions remain in those parameters. Named typographic families
are an interpretation above this exact construction layer.</p>
<p><a href="grammar.json">Standalone executable grammar</a> · <a href="validation.json">Validation report</a> ·
<a href="statistics.json">Reuse statistics</a></p></html>'''
    for key, value in {"ROWS": rows, "ATOMS": stats["atomic_rules"], "MOTIFS": stats["fragment_rules"],
                       "RAW": stats["raw_segment_occurrences"], "REFS": stats["contour_rule_references"]}.items():
        page = page.replace(key, str(value))
    (directory / "index.html").write_text(page)
    atlas(grammar, stats, directory / "fragments.svg")
    specimen(fonts, directory / "specimen.svg")


def atlas(grammar, stats, destination):
    decoder = Decoder(grammar)
    motifs = stats["motifs"][:36]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1900" viewBox="0 0 1200 1900">',
           '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
           '<text x="24" y="32" font-size="22">Shared contour fragments — directed boundary paths, not filled strokes</text>']
    for i, item in enumerate(motifs):
        x, y = 24+(i % 3)*395, 75+(i//3)*150
        g = Glyph()
        pen = g.getPen()
        pen.moveTo((0, 0))
        decoder.draw_fragment([item["rule"]], (Decimal(0), Decimal(0)), pen)
        pen.endPath()
        bounds = g.getBounds({})
        x0, y0, x1, y1 = bounds or (0, 0, 1, 1)
        scale = min(320/max(x1-x0, 1), 75/max(y1-y0, 1))
        path = SVGPathPen(None)
        g.draw(path)
        svg.extend([f'<text x="{x}" y="{y}" font-size="14">{item["rule"]}: {item["segments"]} segments, {item["uses_in_contours"]} uses</text>',
                    f'<path d="{path.getCommands()}" transform="translate({x-x0*scale},{y+90+y0*scale}) scale({scale}, {-scale})" fill="none" stroke="{COLORS[i % len(COLORS)]}" stroke-width="{1.8/scale}"/>',
                    f'<text x="{x}" y="{y+115}" font-size="11">{html.escape(", ".join(item["styles"]))}</text>'])
    svg.append('</g></svg>')
    destination.write_text("\n".join(svg))


def specimen(fonts, destination):
    names = ("H", "O", "n", "o", "m", "a", "g", "S", "alpha", "uni0431", "Pi", "uni0278", "odieresis")
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">',
           '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
           '<text x="24" y="35" font-size="24">All shapes reconstructed from the complete grammar</text>',
           '<text x="24" y="60" font-size="15">Same em scale; source spacing, no kerning/shaping. Exact outline and metadata comparison covers every glyph.</text>']
    for row, (style, font) in enumerate(fonts.items()):
        y = 110+row*250
        svg.append(f'<text x="24" y="{y}" font-size="20">{style}</text>')
        x, baseline, scale = 24, y+130, .065
        for name in names:
            p = SVGPathPen(font)
            font[name].draw(p)
            svg.append(f'<path d="{p.getCommands()}" transform="translate({x},{baseline}) scale({scale},{-scale})"/>')
            x += font[name].width*scale+22
    svg.append('</g></svg>')
    destination.write_text("\n".join(svg))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("build", "replay"), nargs="?", default="build")
    ap.add_argument("grammar", nargs="?", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "build/glyph-review/shape-grammar/complete")
    ap.add_argument("--max-fragments", type=int, help="Optional exploration cap; by default factor until no pair saves symbols")
    args = ap.parse_args()
    if args.command == "replay" and args.grammar is None:
        ap.error("replay requires a grammar JSON file")
    if args.max_fragments is not None and args.max_fragments < 0:
        ap.error("--max-fragments must be nonnegative")
    args.out.mkdir(parents=True, exist_ok=True)
    if args.command == "build":
        grammar, originals = extract(ROOT / "sources", args.max_fragments)
        grammar["reference_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dump(grammar, args.out / "grammar.json")
        grammar = json.loads((args.out / "grammar.json").read_text())
    else:
        grammar = json.loads(args.grammar.read_text())
        originals = None
        if args.grammar.resolve() != (args.out / "grammar.json").resolve():
            dump(grammar, args.out / "grammar.json")
    export = args.out / "ufos"
    export.mkdir(exist_ok=True)
    reports, fonts = validate(grammar, originals, export)
    stats = statistics(grammar)
    dump(reports, args.out / "validation.json")
    dump(stats, args.out / "statistics.json")
    catalogue(grammar, fonts, reports, stats, args.out)
    print(f"Complete grammar and catalogue: {args.out / 'index.html'}", flush=True)


if __name__ == "__main__":
    main()
