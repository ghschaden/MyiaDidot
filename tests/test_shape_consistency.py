"""Production-preparation safeguards without modifying project font sources."""

import copy
import json
import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_consistency as consistency


def circle(glyph, x, y, size, k=.55228475):
    pen = glyph.getPen()
    r = size/2
    pen.moveTo((x, y+r))
    pen.curveTo((x, y+r+k*r), (x+r-k*r, y+size), (x+r, y+size))
    pen.curveTo((x+r+k*r, y+size), (x+size, y+r+k*r), (x+size, y+r))
    pen.curveTo((x+size, y+r-k*r), (x+r+k*r, y), (x+r, y))
    pen.curveTo((x+r-k*r, y), (x, y+r-k*r), (x, y+r))
    pen.closePath()


@pytest.fixture
def policy():
    return consistency.read_policy(consistency.POLICY)


@pytest.fixture
def recipe(policy):
    return next(g["preview"] for g in policy["groups"] if g.get("preview"))


@pytest.fixture
def font():
    f = ufoLib2.Font()
    f.info.unitsPerEm = 1000
    circle(f.newGlyph("dotaccent"), 0, 500, 100)
    target = f.newGlyph("dieresis")
    target.width = 600
    target.unicodes = [168]
    target.appendAnchor({"name": "top", "x": 250, "y": 800})
    target.lib["test"] = "keep"
    circle(target, 50, 700, 80, .56)
    circle(target, 200, 700, 80, .56)
    target.contours[0].identifier = "target-contour"
    target.contours[0].points[0].identifier = "target-point"
    for name, base in (("uni0308", "dieresis"), ("adieresis", "uni0308")):
        f.newGlyph(name).getPen().addComponent(base, (1, 0, 0, 1, 0, 20))
    flat = f.newGlyph("flattened")
    circle(flat, 0, 0, 40)
    flat.lib[consistency.built_from.KEY] = {"dieresis": "old fingerprint"}
    return f


def test_profile_preserves_geometry_contract_and_is_idempotent(font, recipe, policy):
    before = copy.deepcopy(font)
    result = consistency.apply_preview(font, recipe, policy)
    assert result["glyph_ink_difference_percent"] > 0
    assert all(row["bbox_drift_units"] < .001 for row in result["parts"])
    impact = consistency.validate_candidate(before, font, {"dieresis"})
    assert impact["direct_changes"] == ["dieresis"]
    assert set(impact["component_impact"]) == {"adieresis", "uni0308"}
    assert impact["flattened_recipe_dependencies"] == {"flattened": ["dieresis"]}
    assert font["dieresis"].contours[0].identifier == "target-contour"
    assert font["dieresis"].contours[0].points[0].identifier == "target-point"
    snapshot = json.loads(font.json_dumps())
    consistency.apply_preview(font, recipe, policy)
    assert snapshot == json.loads(font.json_dumps())


def test_unrelated_width_or_anchor_change_is_rejected(font, recipe, policy):
    before = copy.deepcopy(font)
    consistency.apply_preview(font, recipe, policy)
    font["dieresis"].width += 1
    with pytest.raises(ValueError, match="metadata, metrics"):
        consistency.validate_candidate(before, font, {"dieresis"})


def test_point_metadata_loss_is_rejected(font, recipe, policy):
    before = copy.deepcopy(font)
    consistency.apply_preview(font, recipe, policy)
    font["dieresis"].contours[0].points[0].identifier = None
    with pytest.raises(ValueError, match="point metadata"):
        consistency.validate_candidate(before, font, {"dieresis"})


def test_counters_and_overlapping_parts_are_not_isolated(font, recipe, policy):
    target = font["dieresis"]
    target.clearContours()
    circle(target, 0, 0, 200)
    circle(target, 50, 50, 100)
    with pytest.raises(ValueError, match="not isolated"):
        consistency.apply_preview(font, recipe, policy)


def test_components_are_not_flattened(font, recipe, policy):
    font["dieresis"].getPen().addComponent("dotaccent", (1, 0, 0, 1, 0, 0))
    with pytest.raises(ValueError, match="flatten"):
        consistency.apply_preview(font, recipe, policy)


def test_geometry_budget_and_topology_are_checked(font, recipe, policy):
    limits = {**policy, "max_preview_part_difference_percent": 0}
    with pytest.raises(ValueError, match="budget"):
        consistency.apply_preview(font, recipe, limits)
    font["dotaccent"].contours[0].points[0].type = "line"
    with pytest.raises(ValueError, match="topology"):
        consistency.apply_preview(font, recipe, policy)


def test_output_cannot_escape_build_or_follow_source_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(consistency, "ROOT", tmp_path)
    (tmp_path / "sources").mkdir()
    (tmp_path / "build").mkdir()
    assert consistency.safe_output(tmp_path / "build/review") == tmp_path / "build/review"
    with pytest.raises(ValueError, match="build/"):
        consistency.safe_output(tmp_path / "sources")
    (tmp_path / "build/escape").symlink_to(tmp_path / "sources", target_is_directory=True)
    with pytest.raises(ValueError, match="build/"):
        consistency.safe_output(tmp_path / "build/escape/candidate.ufo")
    with pytest.raises(ValueError, match="symlinks"):
        consistency.safe_output(tmp_path / "build")


def test_stale_and_modified_plans_are_rejected(policy, monkeypatch):
    monkeypatch.setattr(consistency, "engine_hash", lambda: "engine-v1")
    identities = {s: "bytes" for s in consistency.STYLES}
    plan = {"format": "myiadidot-shape-consistency-plan-v1", "source_hashes": identities,
            "policy_sha256": consistency.json_digest(policy), "engine_sha256": "engine-v1",
            "proposals": [{"style": s, "group": g["id"], "recipe": g["preview"]}
                          for s in consistency.STYLES for g in policy["groups"] if g.get("preview")]}
    consistency.validate_plan(plan, policy, identities)
    with pytest.raises(ValueError, match="source font bytes"):
        consistency.validate_plan(plan, policy, {**identities, "Regular": "new bytes"})
    with pytest.raises(ValueError, match="policy or implementation"):
        consistency.validate_plan(plan, {**policy, "shape_notice_percent": 1}, identities)
    modified = copy.deepcopy(plan)
    modified["proposals"][0]["recipe"]["target_glyph"] = "o"
    with pytest.raises(ValueError, match="unauthorised"):
        consistency.validate_plan(modified, policy, identities)


def test_policy_rejects_ambiguous_membership(policy, tmp_path):
    policy["groups"][1]["members"].append(policy["groups"][0]["donor"])
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="multiple contexts"):
        consistency.read_policy(path)
