"""Checks for vocabulary measurements and the finite minimum search."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import typographic_vocabulary as vocabulary


def test_partition_search_is_exhaustive_without_duplicates():
    partitions = list(vocabulary.partitions(list(range(8))))
    keys = {tuple(sorted(tuple(sorted(group)) for group in partition)) for partition in partitions}
    assert len(partitions) == len(keys) == 4140
    assert all(sorted(i for group in p for i in group) == list(range(8)) for p in partitions)


def test_distance_counts_counter_and_survives_axis_normalisation():
    box = vocabulary.derive.rect_path(0, 0, 100, 100)
    hole = vocabulary.derive.rect_path(20, 20, 80, 80)
    ring = vocabulary.derive.path_op(box, hole, "DIFFERENCE")
    assert vocabulary.distance(box, ring) == pytest.approx(36)
    moved = ring.transform(2, 0, 0, 3, 47, -19)
    assert vocabulary.distance(vocabulary.normalise(ring), vocabulary.normalise(moved)) == pytest.approx(0, abs=.0001)


def test_paired_return_closes_a_symmetric_counter():
    outer = vocabulary.derive.rect_path(0, 0, 1000, 1000)
    inner = vocabulary.derive.rect_path(200, 100, 800, 900)
    ring = vocabulary.derive.path_op(outer, inner, "DIFFERENCE")
    upper = vocabulary.clip(ring, (0, 500, 1000, 1000))
    result = vocabulary.paired_return(vocabulary.normalise(upper))
    assert vocabulary.distance(ring, result) == pytest.approx(0, abs=.0001)


def test_held_out_excludes_all_parts_from_a_donor_glyph():
    samples = [{"id": str(i), "style": "Regular", "glyph": g, "role": "stem"}
               for i, g in enumerate(("A", "A", "B"))]
    result = vocabulary.evaluate_model(samples, [[0, 0, 35], [0, 0, 35], [35, 35, 0]], {"stem": "straight"})
    assert result["held_out_mean"] == 35


def test_frontier_recovers_known_six_group_optimum():
    samples = [{"id": f"{style}/{role}/{copy}", "style": style, "glyph": f"{role}{copy}", "role": role}
               for style in vocabulary.STYLES for role in vocabulary.ROLES for copy in range(2)]
    distances = [[0 if vocabulary.SIX[a["role"]] == vocabulary.SIX[b["role"]] else 40 for b in samples] for a in samples]
    result = vocabulary.vocabulary_frontier(samples, distances)
    assert result["partitions_tested"] == 4140
    by_count = {r["families"]: r for r in result["frontier"]}
    assert by_count[6]["mean_error"] == by_count[6]["held_out_mean"] == 0
    assert by_count[5]["mean_error"] > 0
    assert by_count[8]["mean_error"] == 0
