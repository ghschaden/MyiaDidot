"""Ratchets and snapshots: what the font did before, it must still do.

* Coverage only grows: every code point in data/cmap.txt stays encoded.
* The golden corpus shapes exactly as recorded in data/shaping-golden.json.
* The full corpus (every character, every letter/punctuation pair, base +
  mark sequences, NFD forms) hashes to the digest in data/shaping-digest.txt.

When a change is intended, regenerate with scripts/update_test_data.py and
review the diff of tests/data/ in the commit.
"""

import json

from conftest import DATA
from shaping import full_digest, shape_golden

UPDATE = "python scripts/update_test_data.py"


def test_coverage_never_shrinks(ttfont):
    recorded = {int(x, 16) for x in (DATA / "cmap.txt").read_text().split()}
    have = set(ttfont.getBestCmap())
    lost = sorted(recorded - have)
    assert not lost, "code points no longer encoded: " + " ".join(f"U+{u:04X}" for u in lost)


def test_golden_shaping(shaper):
    expected = json.loads((DATA / "shaping-golden.json").read_text(encoding="utf-8"))
    got = shape_golden(shaper)
    changed = [k for k in got if k in expected and got[k] != expected[k]]
    new = [k for k in got if k not in expected]
    msgs = []
    for k in changed[:15]:
        msgs.append(f"  {k}\n    was: {expected[k]}\n    now: {got[k]}")
    assert not changed, (f"{len(changed)} golden case(s) shape differently "
                         f"(if intended: {UPDATE} --golden):\n" + "\n".join(msgs))
    assert not new, f"corpus cases without a golden entry, run {UPDATE} --golden: {new}"


def test_full_corpus_digest(shaper, ttfont):
    expected = (DATA / "shaping-digest.txt").read_text().split()
    digest, n = full_digest(shaper, ttfont.getBestCmap())
    assert [digest, str(n)] == expected, (
        f"shaping of the full corpus changed ({n} strings). Inspect with `make regress`; "
        f"if intended: {UPDATE} --digest"
    )
