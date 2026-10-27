"""Context-aware shape audit and source-protected standardisation previews.

    .venv/bin/python -I scripts/shape_consistency.py audit
    .venv/bin/python -I scripts/shape_consistency.py preview --plan build/glyph-review/shape-consistency/plan.json

There is deliberately no apply/install command. Candidates are isolated whole
font snapshots under build/, not edits to the masters or style generators.
"""

import argparse
import copy
import importlib.util
import json
import sys
import unicodedata
from collections import defaultdict, deque
from pathlib import Path
from uuid import uuid4

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import built_from
import derive
import glyph_lint
import shape_grammar_full
import typographic_vocabulary as vocabulary
from build_support import content_hash, json_digest, toolchain
from font_builds import compiled_variant
from font_shaping import Shaper

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "scripts/data/shape-consistency.json"
OUT = ROOT / "build/glyph-review/shape-consistency"
STYLES = vocabulary.STYLES


def safe_output(path):
    """Only physical paths below this repository's build/ are writable."""
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve() / "build"):
        raise ValueError("Output must be inside the repository build/ directory")
    if path.exists() and path.is_dir() and any(p.is_symlink() for p in path.rglob("*")):
        raise ValueError("Output tree contains symlinks; refusing to write through them")
    return path


def write_json(path, value):
    path = safe_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")


def source_paths():
    return {style: ROOT / f"sources/MyiaDidot-{style}.ufo" for style in STYLES}


def source_hashes():
    return {style: content_hash(path) for style, path in source_paths().items()}


def engine_hash():
    files = {name: content_hash(ROOT / name) for name in
             ("scripts/shape_consistency.py", "scripts/typographic_vocabulary.py", "scripts/derive.py",
              "scripts/shape_grammar_full.py", "scripts/glyph_lint.py", "scripts/font_builds.py",
              "scripts/font_shaping.py", "skills/glyph-review/scripts/proof.py")}
    return json_digest({"files": files, "toolchain": toolchain()})


def read_policy(path):
    data = json.loads(Path(path).read_text())
    if data.get("format") != "myiadidot-shape-consistency-v1":
        raise ValueError("Unsupported consistency policy")
    ids, samples = set(), set()
    for group in data["groups"]:
        if group["id"] in ids or group["donor"] not in group["members"]:
            raise ValueError("Duplicate group or donor outside its comparison group")
        ids.add(group["id"])
        for sample in group["members"]:
            if sample in samples:
                raise ValueError(f"Sample assigned to multiple contexts: {sample}")
            samples.add(sample)
        if group.get("preview", {}).get("method", "isolated-contour-profile") != "isolated-contour-profile":
            raise ValueError("Only whole isolated contour previews are supported")
    for field in ("shape_notice_percent", "max_preview_part_difference_percent", "max_preview_glyph_difference_percent", "max_bbox_drift_units"):
        if not isinstance(data[field], (int, float)) or not 0 <= data[field] < 100:
            raise ValueError(f"Invalid limit: {field}")
    return data


def audit(policy, out):
    identities = source_hashes()
    records, proposals = [], []
    for style in STYLES:
        samples, _ = vocabulary.extract(style)
        by_name = {s["id"].split("/", 1)[1]: s for s in samples}
        assigned = set()
        for group in policy["groups"]:
            donor = by_name[group["donor"]]
            for name in group["members"]:
                assigned.add(name)
                sample = by_name[name]
                error = vocabulary.distance(donor["normalised"], sample["normalised"])
                x0, y0, x1, y1 = sample["bounds"]
                records.append({"style": style, "group": group["id"], "sample": name, "donor": group["donor"],
                                "shape_difference_percent": error, "width_units": x1-x0, "height_units": y1-y0,
                                "status": "review" if error > policy["shape_notice_percent"] else "consistent",
                                "reason": group["reason"], "preview_supported": bool(group.get("preview"))})
            if group.get("preview"):
                proposals.append({"id": f"{style}/{group['id']}", "style": style, "group": group["id"],
                                  "recipe": group["preview"], "status": "unaccepted-experiment"})
        if assigned != set(by_name):
            raise ValueError(f"Unclassified or missing anatomical samples: {style}: {set(by_name) ^ assigned}")
    plan = {"format": "myiadidot-shape-consistency-plan-v1", "source_hashes": identities,
            "policy_sha256": json_digest(policy), "engine_sha256": engine_hash(), "proposals": proposals}
    if source_hashes() != identities:
        raise RuntimeError("Source fonts changed during audit")
    write_json(out / "audit.json", {"source_hashes": identities, "groups": len(policy["groups"]), "records": records})
    write_json(out / "plan.json", plan)
    return records, plan


def validate_plan(plan, policy, identities):
    if plan.get("format") != "myiadidot-shape-consistency-plan-v1":
        raise ValueError("Unsupported plan")
    if plan["source_hashes"] != identities:
        raise ValueError("Stale plan: source font bytes changed; run audit again")
    if plan["policy_sha256"] != json_digest(policy) or plan["engine_sha256"] != engine_hash():
        raise ValueError("Stale plan: policy or implementation changed; run audit again")
    expected = {(style, g["id"]): g["preview"] for style in STYLES for g in policy["groups"] if g.get("preview")}
    found = set()
    for proposal in plan["proposals"]:
        key = proposal["style"], proposal["group"]
        if key in found or expected.get(key) != proposal["recipe"]:
            raise ValueError("Plan contains duplicate or unauthorised preview recipes")
        found.add(key)
    if found != set(expected):
        raise ValueError("Plan is missing preview recipes")


def contour_path(contour):
    pen = RecordingPen()
    contour.draw(pen)
    return derive.to_path(None, rec=pen)


def contour_profile(donor, target):
    """Retain the target point metadata; fit only a whole closed contour."""
    if donor.open or target.open:
        raise ValueError("Profile replacement requires closed isolated contours")
    if [p.type for p in donor.points] != [p.type for p in target.points]:
        raise ValueError("Contour topology changed; review the profile recipe")
    dp, tp = contour_path(donor), contour_path(target)
    if dp.clockwise != tp.clockwise:
        raise ValueError("Contour direction differs; review the profile recipe")
    dx0, dy0, dx1, dy1 = dp.bounds
    tx0, ty0, tx1, ty1 = tp.bounds
    if min(dx1-dx0, dy1-dy0, tx1-tx0, ty1-ty0) <= 0:
        raise ValueError("Degenerate contour")
    result = copy.deepcopy(target)
    sx, sy = (tx1-tx0)/(dx1-dx0), (ty1-ty0)/(dy1-dy0)
    for src, dst in zip(donor.points, result.points):
        dst.x = tx0 + (src.x-dx0)*sx
        dst.y = ty0 + (src.y-dy0)*sy
    return result


def apply_preview(font, recipe, policy):
    donor, target = font[recipe["donor_glyph"]], font[recipe["target_glyph"]]
    if donor.components or target.components:
        raise ValueError("A preview may not flatten existing components")
    if len(donor.contours) != recipe["expected_donor_contours"] or len(target.contours) != recipe["expected_target_contours"]:
        raise ValueError("Contour inventory changed; run a new drawing review")
    # A closed contour can also be a counter or a touching stroke. The supported
    # handler is deliberately restricted to spatially separated solid pieces.
    for index in recipe["target_contours"]:
        a = contour_path(target.contours[index]).bounds
        for other, contour in enumerate(target.contours):
            if other == index:
                continue
            b = contour_path(contour).bounds
            separated = a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]
            if not separated:
                raise ValueError("Preview contour is not isolated: overlapping bounds, a counter or a touching part")
    before = derive.to_path(font, target)
    rows = []
    for index in recipe["target_contours"]:
        old = contour_path(target.contours[index])
        replacement = contour_profile(donor.contours[recipe["donor_contour"]], target.contours[index])
        new = contour_path(replacement)
        error = vocabulary.distance(old, new)
        canonical = vocabulary.normalise(contour_path(donor.contours[recipe["donor_contour"]]))
        before_distance = vocabulary.distance(vocabulary.normalise(old), canonical)
        after_distance = vocabulary.distance(vocabulary.normalise(new), canonical)
        if after_distance > .01 or after_distance > before_distance+.0001:
            raise ValueError("Candidate did not converge to its declared contour profile")
        drift = max(abs(a-b) for a, b in zip(old.bounds, new.bounds))
        if error > policy["max_preview_part_difference_percent"] or drift > policy["max_bbox_drift_units"]:
            raise ValueError("Candidate exceeds the configured part-change or bounds budget")
        if error > 0.0001:
            target.contours[index] = replacement
        rows.append({"contour": index, "ink_difference_percent": error, "bbox_drift_units": drift,
                     "profile_difference_before_percent": before_distance,
                     "profile_difference_after_percent": after_distance})
    after = derive.to_path(font, target)
    error = vocabulary.distance(before, after)
    if error > policy["max_preview_glyph_difference_percent"]:
        raise ValueError("Candidate exceeds the glyph-change budget")
    return {"glyph": target.name, "parts": rows, "glyph_ink_difference_percent": error}


def component_dependants(font, changed):
    reverse = defaultdict(set)
    for glyph in font:
        for component in glyph.components:
            reverse[component.baseGlyph].add(glyph.name)
    seen, todo = set(changed), deque(changed)
    while todo:
        for name in reverse[todo.popleft()]:
            if name not in seen:
                seen.add(name)
                todo.append(name)
    return seen


def outlines(font):
    result = {}
    for glyph in font:
        pen = DecomposingRecordingPen(font)
        glyph.draw(pen)
        result[glyph.name] = json_digest(pen.value)
    return result


def validate_candidate(before, after, allowed):
    a, b = json.loads(before.json_dumps()), json.loads(after.json_dumps())
    changed = set()
    for name in before.keys():
        if json.loads(before[name].json_dumps()) != json.loads(after[name].json_dumps()):
            changed.add(name)
    if not changed <= set(allowed):
        raise ValueError(f"Unexpected direct glyph changes: {changed-set(allowed)}")
    for name in changed:
        def point_metadata(glyph):
            contours = json.loads(glyph.json_dumps()).get("contours", [])
            for contour in contours:
                for point in contour["points"]:
                    point.pop("x", None)
                    point.pop("y", None)
            return contours

        if point_metadata(before[name]) != point_metadata(after[name]):
            raise ValueError("Contour/point metadata or topology changed")
    for layer in a["layers"]:
        for name in changed:
            layer["glyphs"][name].pop("contours", None)
    for layer in b["layers"]:
        for name in changed:
            layer["glyphs"][name].pop("contours", None)
    if a != b:
        raise ValueError("Candidate changed font metadata, metrics, anchors, components or feature data")
    expected = component_dependants(before, changed)
    original, proposed = outlines(before), outlines(after)
    actual = {name for name in original if original[name] != proposed[name]}
    if actual != expected:
        raise ValueError(f"Unexpected rendered-outline impact: {actual ^ expected}")
    flat = {g.name: sorted(set(g.lib.get(built_from.KEY, {})) & actual) for g in before
            if set(g.lib.get(built_from.KEY, {})) & actual}
    accepted = sorted(name for name in actual if before[name].lib.get("org.myiadidot.accepted"))
    return {"direct_changes": sorted(changed), "component_impact": sorted(actual-changed),
            "flattened_recipe_dependencies": flat, "accepted_designs_affected": accepted,
            "metadata_metrics_anchors_components_unchanged": True}


def shaping_checks(before_path, after_path, font, impacted):
    before = Shaper(compiled_variant(before_path, "test_otf"))
    after = Shaper(compiled_variant(after_path, "test_otf"))
    cases = [("naïve coöperate äëïöüÿ", "latn", "en", {}),
             ("ÄÖÜ äöü Straße", "latn", "de", {}),
             ("a\u0308 o\u0308 u\u0308", "latn", "en", {}),
             ("ϊ ϋ ΐ ΰ", "grek", "el", {}), ("ёж ЁЖ", "cyrl", "ru", {}),
             ("ÄÖÜ äöü", "latn", "de", {"smcp": True}), ("İIıi", "latn", "tr", {})]
    for name in sorted(impacted):
        for cp in font[name].unicodes:
            ch = chr(cp)
            script, language = ("grek", "el") if "GREEK" in unicodedata.name(ch, "") else ("cyrl", "ru") if "CYRILLIC" in unicodedata.name(ch, "") else ("latn", "en")
            text = "a"+ch if unicodedata.combining(ch) else ch
            cases.append((text, script, language, {}))
            decomposed = unicodedata.normalize("NFD", text)
            if decomposed != text:
                cases.append((decomposed, script, language, {}))
    failures = []
    for text, script, language, features in cases:
        a = before.shape(text, features, script=script, language=language)
        b = after.shape(text, features, script=script, language=language)
        if a != b:
            failures.append({"text": text, "script": script, "language": language, "before": a, "after": b})
    if failures:
        raise ValueError(f"Shaping or positioning changed in {len(failures)} cases")
    return {"cases": len(cases), "glyph_sequences_advances_offsets_unchanged": True,
            "scope": "impacted encoded glyphs, NFD forms, selected Latin/Greek/Cyrillic/Turkish and small-cap text; unhinted"}


def proof_renderer():
    spec = importlib.util.spec_from_file_location("shape_consistency_proof", ROOT / "skills/glyph-review/scripts/proof.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def detail_proof(before, after, path, style):
    """Magnify the changed mark; text-size proofs alone hide sub-unit changes."""
    a, b = contour_path(before["dieresis"].contours[0]), contour_path(after["dieresis"].contours[0])
    x0, y0, _, _ = a.bounds
    a, b = a.transform(1, 0, 0, 1, -x0, -y0), b.transform(1, 0, 0, 1, -x0, -y0)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="440" viewBox="0 0 1200 440">',
           '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#222">',
           f'<text x="24" y="32" font-size="23">Accent profile experiment — {style}</text>',
           '<text x="24" y="57" font-size="15">First dieresis dot, same scale and position. Original black; candidate magenta. Unaccepted outline proposal.</text>']
    for x, label in ((24, "Original"), (424, "Candidate"), (824, "Overlay")):
        svg.append(f'<text x="{x}" y="95" font-size="18">{label}</text>')
    svg.extend([vocabulary.draw(a, 40, 380, 1, "#222"), vocabulary.draw(b, 440, 380, 1, "#d21d8e"),
                vocabulary.draw(a, 840, 380, 1, "#222", .7), vocabulary.draw(b, 840, 380, 1, "#d21d8e", .45), '</g></svg>'])
    safe_output(path).write_text("\n".join(svg))


def preview(plan, policy, out):
    identities = source_hashes()
    validate_plan(plan, policy, identities)
    # Each run is immutable once published. A failed run cannot overwrite the
    # candidates linked from a previous successful report.
    run = safe_output(out / "runs" / f"{json_digest(plan)[:12]}-{uuid4().hex[:8]}")
    reports = {}
    for style, source in source_paths().items():
        before = ufoLib2.Font.open(source, lazy=False)
        after = copy.deepcopy(before)
        proposals = [p for p in plan["proposals"] if p["style"] == style]
        operations = [apply_preview(after, p["recipe"], policy) for p in proposals]
        allowed = {p["recipe"]["target_glyph"] for p in proposals}
        impact = validate_candidate(before, after, allowed)
        # A production rule must converge: repeating it changes nothing.
        snapshot = json.loads(after.json_dumps())
        for proposal in proposals:
            apply_preview(after, proposal["recipe"], policy)
        if snapshot != json.loads(after.json_dumps()):
            raise ValueError("Candidate rule is not idempotent")
        directory = safe_output(run / "candidates" / style)
        directory.mkdir(parents=True, exist_ok=True)
        before_path, after_path = safe_output(directory / "before.ufo"), safe_output(directory / "candidate.ufo")
        before.save(before_path, overwrite=True)
        after.save(after_path, overwrite=True)
        reopened = ufoLib2.Font.open(after_path)
        if shape_grammar_full.digest(json.loads(reopened.json_dumps())) != shape_grammar_full.digest(snapshot):
            raise ValueError("Saved candidate changed on round trip")
        all_changed = set(impact["direct_changes"] + impact["component_impact"])
        baseline_lint = glyph_lint.lint(before, sorted(all_changed)) if all_changed else {}
        candidate_lint = glyph_lint.lint(after, sorted(all_changed)) if all_changed else {}
        new_findings = {name: [item for item in items if item not in baseline_lint.get(name, [])]
                        for name, items in candidate_lint.items()}
        new_findings = {name: items for name, items in new_findings.items() if items}
        if new_findings:
            raise ValueError(f"Candidate introduces outline findings: {new_findings}")
        shaping = shaping_checks(before_path, after_path, before, all_changed)
        proof = safe_output(run / f"{style}-before-after.svg")
        proof_renderer()(after_path, ["dotaccent", "dieresis", "odieresis", "adieresis", "uni0308", "i", "period"], proof,
                         before=before_path, texts=("naïve coöperate äëïöü", "a\u0308 o\u0308 u\u0308"),
                         language="en", script="latn", anchors=True)
        detail = safe_output(run / f"{style}-detail.svg")
        detail_proof(before, after, detail, style)
        reports[style] = {"operations": operations, "impact": impact, "shaping": shaping,
                          "outline_lint": {"baseline": baseline_lint, "candidate": candidate_lint, "new_findings": new_findings},
                          "proof": str(proof.relative_to(out)), "candidate": str(after_path.relative_to(out)),
                          "detail_proof": str(detail.relative_to(out)),
                          "idempotent": True, "saved_round_trip_verified": True, "release_ready": False,
                          "status": "unaccepted geometry experiment; whole-style generators have not been rerun",
                          "dependency_scope": "components and recorded builtFrom links only; generator code and flattened unrecorded derivations require separate integration review",
                          "future_source_owner": "Regular source/design input" if style == "Regular" else "make_italic.py / make_bold.py and shared style construction; never copy this candidate over generated sources"}
        print(f"{style}: {len(impact['direct_changes'])} direct changes, {len(impact['component_impact'])} component dependants, {shaping['cases']} shaping checks", flush=True)
    if source_hashes() != identities:
        raise RuntimeError("Source fonts changed during preview")
    result = {"source_hashes_before": identities, "source_hashes_after": source_hashes(), "sources_byte_identical": True,
              "run": str(run.relative_to(out)),
              "plan_sha256": json_digest(plan), "engine_sha256": plan["engine_sha256"],
              "policy_sha256": json_digest(policy), "styles": reports}
    write_json(out / "preview.json", result)
    return result


def overview(out, records, result=None):
    from html import escape

    rows = "".join(f'<tr><td>{r["style"]}</td><td>{escape(r["group"])}</td><td>{escape(r["sample"])}</td>'
                   f'<td>{r["shape_difference_percent"]:.3f}%</td><td>{r["status"]}</td></tr>' for r in records if r["status"] == "review")
    links = "".join(f'<li>{style}: <a href="{data["proof"]}">original and candidate, anchors and shaped text</a> · <a href="{data["detail_proof"]}">enlarged overlay</a></li>' for style, data in result["styles"].items()) if result else "<li>Run preview with the pinned plan to create candidates.</li>"
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Myia Didot shape consistency</title>
<style>body{font:18px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#222}td,th{padding:7px 14px;border-bottom:1px solid #ddd;text-align:left}a{color:#1767a2}</style>
<h1>Shape consistency: production preparation</h1>
<p>Comparisons respect style, optical size and entry/interior/exit context. A finding is a review
candidate, not evidence of a faulty drawing. The policy names donors explicitly; it does not minimise the number of shapes.</p>
<p><strong>No source font is changed.</strong> The only editable experiment is an isolated accent-dot
profile: dotaccent supplies the contour shape of dieresis dots, with each target bounding box preserved.
Letter dots and punctuation remain in separate comparison groups. Connected shapes are audit-only.</p>
<p>These candidates are unaccepted and not release-ready. They are complete scratch font snapshots,
not a rerun of the style generators. Derived outline recipes may require regeneration; their known dependencies are reported.</p>
<h2>Candidate proofs</h2><ul>LINKS</ul>
<p><a href="audit.json">Full audit</a> · <a href="plan.json">Pinned preview plan</a> PREVIEW_LINK</p>
<h2>Differences above the policy's review threshold</h2>
<table><tr><th>Style</th><th>Context</th><th>Sample</th><th>Shape difference</th><th>Status</th></tr>ROWS</table>
<p>Audit differences use the anatomical study's normalised regions; preview limits are measured again
in actual font coordinates. Dimensions and joining context must be considered separately.</p></html>'''
    safe_output(out / "index.html").write_text(html.replace("LINKS", links).replace("ROWS", rows).replace("PREVIEW_LINK", '· <a href="preview.json">Impact and validation</a>' if result else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("audit", "preview"))
    ap.add_argument("--policy", type=Path, default=POLICY)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--plan", type=Path, help="Required pinned audit plan for preview")
    args = ap.parse_args()
    out = safe_output(args.out)
    policy = read_policy(args.policy)
    identities = source_hashes()
    try:
        if args.command == "audit":
            out.mkdir(parents=True, exist_ok=True)
            records, _ = audit(policy, out)
            overview(out, records)
            print(f"Audited {len(records)} samples in {len(policy['groups'])} explicit contexts; {out / 'index.html'}")
        else:
            if args.plan is None:
                ap.error("preview requires --plan from an audit")
            plan = json.loads(args.plan.read_text())
            validate_plan(plan, policy, identities)
            out.mkdir(parents=True, exist_ok=True)
            # Copy the verified plan/report when a separate preview directory is used.
            records = json.loads((args.plan.parent / "audit.json").read_text())["records"]
            write_json(out / "plan.json", plan)
            write_json(out / "audit.json", {"source_hashes": identities, "records": records})
            result = preview(plan, policy, out)
            overview(out, records, result)
    finally:
        if source_hashes() != identities:
            raise RuntimeError("Source font bytes changed during this command")


if __name__ == "__main__":
    main()
