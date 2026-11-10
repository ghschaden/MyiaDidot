#!/usr/bin/env python3
"""What moved in a style since a revision, in units: the sweep after a redraw.

    python scripts/redraw_sweep.py sources/MyiaDidot-Italic.ufo            (against HEAD)
    python scripts/redraw_sweep.py UFO --rev 563c43f3 --json build/redraw/sweep.json
    python scripts/redraw_sweep.py UFO --against build/redraw/before.ufo

After a batch is installed and `make generate` run, only the redrawn
letters and what is made of them may have moved, and by little
(docs/claude/redraw.md, step 7). check_reproducible.py and git compare
point by point, which says nothing once the nodes differ; this measures
the outlines themselves: for every glyph that differs, the greatest
distance between the old and the new outline (both ways, decomposed, as
they stand on their advances) and the change of the advance, anchors and
kerning. One line a glyph, sorted by kind:

    redrawn    carries redraw.py's record (org.myiadidot.redrawn)
    composite  components only, one of them (at any depth) redrawn
    other      everything else: letters derived from a redrawn one, letters
               that only read one for a measure (Ꞷ: o's stem), and whatever
               should not have moved at all

A line is flagged (!) when the outline moved more than --limit (4 units,
redraw.DEV) or the advance changed by more than --advance (5 units), a
composite when it moved more than its parts or its advance changed at
all. Exit status 1 if anything is flagged. A flag is a question, not a
verdict: the 2026-11-10 pilot's first run had 30 advances 32 narrower
(the Italic's cut taken twice from what was built on a kept letter),
found only in the shaping tests' diffs.
"""

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

import numpy as np
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

ROOT = Path(__file__).resolve().parent.parent
KEY = "org.myiadidot.redrawn"
STEP = 4.0  # units between the samples along an outline


def polylines(font, name):
    """the glyph's contours (decomposed) as closed polylines, a point every
    STEP units or less"""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    out, pts, cur = [], [], None

    def line(a, b):
        n = max(1, int(np.hypot(b[0] - a[0], b[1] - a[1]) / STEP))
        pts.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1))

    for op, args in rec.value:
        if op == "moveTo":
            pts, cur = [args[0]], args[0]
        elif op == "lineTo":
            line(cur, args[0])
            cur = args[0]
        elif op == "curveTo":
            p0, p1, p2, p3 = (np.array(p, float) for p in (cur, *args))
            n = max(2, int((np.hypot(*(p1 - p0)) + np.hypot(*(p2 - p1)) + np.hypot(*(p3 - p2))) / STEP))
            for k in range(1, n + 1):
                t = k / n
                pts.append(tuple((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3))
            cur = args[-1]
        elif op == "qCurveTo":
            raise ValueError(f"{name}: quadratic curves")
        elif op in ("closePath", "endPath"):
            if pts and pts[0] != pts[-1]:
                line(pts[-1], pts[0])
            if len(pts) > 1:
                out.append(np.array(pts, float))
            pts = []
    return out


def one_way(a, b):
    """(the greatest distance from a's points to b's outline, where)"""
    if not a and not b:
        return 0.0, None
    if not a or not b:
        return float("inf"), None
    p = np.concatenate(a)
    s0 = np.concatenate([c[:-1] for c in b])
    d = np.concatenate([c[1:] for c in b]) - s0
    dd = np.maximum((d * d).sum(1), 1e-12)
    best = np.full(len(p), np.inf)
    for i in range(0, len(s0), 512):  # in blocks: a glyph can have 10 000 samples
        w = p[:, None, :] - s0[None, i:i + 512, :]
        t = np.clip((w * d[None, i:i + 512, :]).sum(2) / dd[None, i:i + 512], 0, 1)
        r = w - t[:, :, None] * d[None, i:i + 512, :]
        best = np.minimum(best, np.sqrt((r * r).sum(2)).min(1))
    k = int(best.argmax())
    return float(best[k]), (round(float(p[k][0])), round(float(p[k][1])))


def distance(old, new, name):
    """the greatest distance between the two outlines of a glyph, and where"""
    a, b = polylines(old, name), polylines(new, name)
    return max(one_way(a, b), one_way(b, a), key=lambda r: r[0])


def at_revision(ufo, rev, work):
    rel = ufo.resolve().relative_to(ROOT)
    data = subprocess.run(["git", "-C", str(ROOT), "archive", rev, str(rel)], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=BytesIO(data)) as tar:
        tar.extractall(work, filter="data")
    return ufoLib2.Font.open(Path(work) / rel)


def reaches(font, name, redrawn, seen=None):
    seen = seen or set()
    for c in font[name].components:
        if c.baseGlyph in redrawn or (c.baseGlyph in font and c.baseGlyph not in seen
                                     and reaches(font, c.baseGlyph, redrawn, seen | {name})):
            return True
    return False


def sweep(old, new, limit, advance):
    redrawn = {g.name for g in new if g.lib.get(KEY) and (g.name not in old or old[g.name].lib.get(KEY) != g.lib[KEY])}
    rows = []
    for name in sorted(set(old.keys()) | set(new.keys())):
        if name not in old or name not in new:
            rows.append({"glyph": name, "kind": "other", "flag": True,
                         "what": "new" if name in new else "gone"})
            continue
        a, b = old[name], new[name]
        rec = [DecomposingRecordingPen(f) for f in (old, new)]
        a.draw(rec[0])
        b.draw(rec[1])
        anchors = [sorted((p.name, round(p.x), round(p.y)) for p in g.anchors) for g in (a, b)]
        same_ink = rec[0].value == rec[1].value
        if same_ink and a.width == b.width and anchors[0] == anchors[1]:
            continue
        d, where = (0.0, None) if same_ink else distance(old, new, name)
        kind = ("redrawn" if name in redrawn else
                "composite" if not b.contours and reaches(new, name, redrawn) else "other")
        moved = max((abs(p[1] - q[1]) + abs(p[2] - q[2]) for p, q in zip(*anchors) if p[0] == q[0]), default=0)
        if [p[0] for p in anchors[0]] != [p[0] for p in anchors[1]]:
            moved = float("inf")
        rows.append({"glyph": name, "kind": kind, "distance": round(d, 1), "where": where,
                     "advance": [a.width, b.width], "anchors": moved,
                     "flag": bool(d > limit or abs(a.width - b.width) > (0 if kind != "other" else advance)
                                  or moved > limit)})
    kerning = {f"{l} {r}": [old.kerning.get((l, r)), new.kerning.get((l, r))]
               for l, r in sorted(set(old.kerning) | set(new.kerning))
               if old.kerning.get((l, r)) != new.kerning.get((l, r))}
    return rows, kerning


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo", type=Path)
    ap.add_argument("--rev", default="HEAD", help="the revision to compare with (HEAD)")
    ap.add_argument("--against", type=Path, help="a UFO to compare with, in place of a revision")
    ap.add_argument("--limit", type=float, default=4.0, help="units an outline or anchor may move unflagged (4)")
    ap.add_argument("--advance", type=float, default=5.0, help="units an advance may change unflagged (5)")
    ap.add_argument("--json", type=Path, help="the full report")
    ap.add_argument("--all", action="store_true", help="print every line, not only the flagged and the others")
    args = ap.parse_args()
    new = ufoLib2.Font.open(args.ufo)
    with tempfile.TemporaryDirectory(prefix="myia-sweep-") as work:
        old = ufoLib2.Font.open(args.against) if args.against else at_revision(args.ufo, args.rev, work)
        rows, kerning = sweep(old, new, args.limit, args.advance)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"glyphs": rows, "kerning": kerning}, indent=1, ensure_ascii=False) + "\n")
    order = {"redrawn": 0, "composite": 1, "other": 2}
    for kind in order:
        mine = [r for r in rows if r["kind"] == kind]
        if not mine:
            continue
        worst = max((r.get("distance", 0) for r in mine), default=0)
        print(f"{kind}: {len(mine)} glyphs, furthest {worst}, flagged {sum(r['flag'] for r in mine)}")
        for r in sorted(mine, key=lambda r: (-r["flag"], -r.get("distance", 0))):
            if not (args.all or r["flag"] or kind == "other"):
                continue
            if "what" in r:
                print(f"  ! {r['glyph']}: {r['what']}")
                continue
            w0, w1 = r["advance"]
            print(f"  {'!' if r['flag'] else ' '} {r['glyph']:<18} moved {r['distance']:>5}"
                  + (f" at {r['where'][0]},{r['where'][1]}" if r["where"] else "")
                  + (f"  advance {w0} -> {w1}" if w0 != w1 else "")
                  + (f"  anchors {r['anchors']}" if r["anchors"] else ""))
    if kerning:
        print(f"kerning: {len(kerning)} pairs changed")
        for pair, (a, b) in list(kerning.items())[:20]:
            print(f"  {pair}: {a} -> {b}")
    flagged = sum(r["flag"] for r in rows)
    print(f"{len(rows)} glyphs differ, {flagged} flagged")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
