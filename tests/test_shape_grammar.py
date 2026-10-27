"""Geometry invariants of the experimental grammar, independent of font data."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_grammar as grammar


def test_union_removes_overlap_after_json_roundtrip():
    node = grammar.union(grammar.rectangle(0, 0, 10, 10), grammar.rectangle(5, 0, 15, 10))
    result = grammar.evaluate(json.loads(json.dumps(node)), {})
    assert result.area == pytest.approx(150)
    assert result.bounds == pytest.approx((0, 0, 15, 10))


def test_stored_counter_survives_reflection_and_json_roundtrip():
    outer = grammar.evaluate(grammar.rectangle(0, 0, 10, 10), {})
    inner = grammar.evaluate(grammar.rectangle(2, 2, 8, 8), {})
    ring = grammar.derive.path_op(outer, inner, "DIFFERENCE")
    palette = json.loads(json.dumps({"ring": {"shape": grammar.stored_path(ring)}}))
    node = grammar.transform(grammar.ref("ring"), (-2, 0, 0, 3, 20, 0))
    result = grammar.evaluate(node, palette)
    assert result.area == pytest.approx(64 * 6)
    assert result.contains((2, 3))
    assert not result.contains((10, 15))


def test_reference_cycle_is_rejected():
    with pytest.raises(ValueError, match="Cyclic shape reference"):
        grammar.evaluate(grammar.ref("a"), {"a": {"shape": grammar.ref("b")},
                                            "b": {"shape": grammar.ref("a")}})
