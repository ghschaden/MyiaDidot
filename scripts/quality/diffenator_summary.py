"""Summarize diffenator2's HTML reports as plain text.

    python scripts/quality/diffenator_summary.py build/visual/diffenator [--examples 6]

Reads DIR/STYLE/*-diffenator.html (make diffenator) and prints, per style:
the tables that differ (head's dates and checksum left out), glyphs whose
advance or outline changed, new, missing and modified encoded glyphs, the
misshapen words per script with examples, and the letter pairs behind them:
where a word's glyphs match its characters one to one, the letter whose
advance changed and the one after it, with the change in units.
"""

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

NOISE = {("head", "created"), ("head", "modified"), ("head", "checkSumAdjustment")}
BOX = re.compile(r'<div class="box-title">(.*?)</div>(.*?)(?=<div class="box-title">|<script>var fontdiff)', re.S)
TIP = re.compile(r'<div class="tooltip">\s*(.*?)<br>\s*<span class="tooltiptext">(.*?)</span>', re.S)
POS = re.compile(r"gid=(\d+), pos=\((-?\d+), (-?\d+), (-?\d+), (-?\d+)\)")


def parse(path):
    text = path.read_text(encoding="utf-8")
    sections = {}
    for title, body in BOX.findall(text):
        sections[html.unescape(title.strip())] = [(html.unescape(w.strip()), tip) for w, tip in TIP.findall(body)]
    m = re.search(r"<script>var fontdiff = (\{.*?\});</script>", text, re.S)
    tables = json.loads(m.group(1)) if m else {}
    return sections, tables


def pixels(tip):
    m = re.search(r"changed pixels: ([\d.]+)%", tip)
    return float(m.group(1)) if m else 0.0


def pairs(word, tip):
    """(left, right, delta) for each glyph whose advance changed."""
    halves = re.split(r"After:", tip)
    if len(halves) != 2:
        return []
    before, after = (POS.findall(h) for h in halves)
    if len(before) != len(after) or len(before) != len(word):
        return []
    out = []
    for i, (b, a) in enumerate(zip(before, after)):
        d = int(a[3]) - int(b[3])
        if d:
            out.append((word[i], word[i + 1] if i + 1 < len(word) else "", d))
    return out


def table_lines(tables):
    lines = []
    for tag, diff in sorted(tables.items()):
        if tag == "hmtx":
            metrics = diff.get("metrics", {})
            adv = [f"{g} {v['0'][0]}→{v['0'][1]}" for g, v in sorted(metrics.items()) if "0" in v]
            lsb = [g for g, v in sorted(metrics.items()) if "0" not in v]
            if adv:
                lines.append(f"  advance: {', '.join(adv)}")
            if lsb:
                lines.append(f"  sidebearing only: {', '.join(lsb)}")
        elif tag in ("glyf", "CFF "):
            glyphs = sorted(diff.get("glyphs", diff))
            lines.append(f"  outlines ({tag.strip()}): {len(glyphs)}: {', '.join(glyphs[:20])}"
                         + (" ..." if len(glyphs) > 20 else ""))
        else:
            keys = [k for k in sorted(diff) if (tag, k) not in NOISE] if isinstance(diff, dict) else [str(diff)]
            if keys:
                lines.append(f"  table {tag}: {', '.join(keys[:12])}" + (" ..." if len(keys) > 12 else ""))
    return lines


def summarize(style, path, examples):
    sections, tables = parse(path)
    lines = [f"== {style}"]
    lines += table_lines(tables)
    for title in ("New encoded glyphs", "Missing encoded Glyphs", "Modified encoded Glyphs"):
        items = sections.get(title, [])
        if items:
            shown = ", ".join(f"{w} {pixels(t):.1f}%" if pixels(t) else w for w, t in items)
            lines.append(f"  {title.lower()}: {len(items)}: {shown}")
    pair_count, pair_words = Counter(), defaultdict(list)
    for title, items in sections.items():
        if not (title.startswith("Misshapen") and items):
            continue
        items = sorted(items, key=lambda it: -pixels(it[1]))
        lines.append(f"  {title.removeprefix('Misshapen ')}: {len(items)}: "
                     + ", ".join(w for w, _ in items[:examples]) + (" ..." if len(items) > examples else ""))
        for word, tip in items:
            for left, right, d in pairs(word, tip):
                pair_count[(left, right, d)] += 1
                pair_words[(left, right, d)].append(word)
    if pair_count:
        lines.append("  pairs whose left letter's advance changed (its width or its kerning; units, words):")
        for (left, right, d), n in pair_count.most_common():
            lines.append(f"    {left}{right or '·'} {d:+d}  ({n}: {', '.join(pair_words[left, right, d][:3])})")
    if len(lines) == 1:
        lines.append("  no differences")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dir", type=Path)
    ap.add_argument("--examples", type=int, default=6)
    args = ap.parse_args()
    for style_dir in sorted(p for p in args.dir.iterdir() if p.is_dir()):
        for report in sorted(style_dir.glob("*-diffenator.html")):
            print("\n".join(summarize(style_dir.name, report, args.examples)))


if __name__ == "__main__":
    main()
