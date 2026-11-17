#!/usr/bin/env python3
"""Phase 6's sheet: the Italic against the Regular (docs/claude/italic.md).

    .venv/bin/python -I scripts/italic_sheet.py [OUT.pdf]

Default OUT: proofs/YYYY-MM/italic-against-regular-DATE.pdf. Measures as
scripts/quality/italic_measures.py does (it is run here, from the UFOs
and build/refs/), then one PDF, A3 across:

1. the table: every measure, Myia's two own-scale values and relation,
   the three Didones', the position, the spread, the second voice, R/OS
   and I/OS, the verdict; findings first;
2. one page per finding of the change list, and one for the long stems'
   question: Myia Regular, Myia Italic, the nearest Didone's pair (for
   the long stems Old Standard's and Bodoni Moda's), the letters at up
   to 144 pt with the measured places drawn (strokes in vermilion, the
   discs of balls and counters in green, the zones' lines in ochre, the
   advances as grey ticks) and each letter's own-scale value beneath it,
   with the relation under the italic;
3. running text, roman with italic words, at 24 and 12 pt: Myia, Old
   Standard, Bodoni Moda;
4. the change list, each entry with its measures, letters and where it
   would be mended.

Every letter is set from the outlines and advances (no kerning, no
features in any face), so that faces differ only in their letters. The
italics are drawn as they are, slanted; the marks, measured on the
deslanted outline, are slanted with them. The tools find candidates;
the designer's eye decides.
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
import bold_measures as bm  # noqa: E402
import italic_measures as im  # noqa: E402
from common import REFDIR, ROOT  # noqa: E402

W, H = 1190, 842  # A3 across, pt
INK = "#22160a"
MARK = "#d2361f"  # vermilion: strokes measured
DISC = "#17803a"  # green: balls and counters
GUIDE = "#c58a00"  # ochre: baseline, x-height, cap height
TICK = "#9c8466"
LABEL = "#5a4630"
VERDICT = {"another typeface": "#f3c2ae", "candidate": "#f5dc94", im.KEPT: "#d3e3ad",
           "inside": None, "shown: the references spread": "#ece3d3", "shown": "#ece3d3"}

# The change list (italic.md, "The first run", and "The long stems"):
# title, measures, letters for the page, where it would be mended, pages'
# references ("nearest" or names), guides drawn.
FINDINGS = [
    ("1. The round letters' bowls, and O",
     ["counter n / x-height", "counter o / x-height", "counter d / x-height", "counter p / x-height",
      "counter q / x-height", "width O / cap height"],
     "nodpq O", ("The designer's drawing: a letter's proportions (italic.md, 'Where a fault is "
     "mended', width in the outlines). The widths of a-z and A-Z as a whole are inside: it is the "
     "round letters, not the fit. The Regular's side: R/OS +8 to +20, I/OS within 1."),
     "nearest", ""),
    ("2. The balls of r and c",
     ["ball r / stem", "ball c / stem"], "rcfyj",
     ("One letter's each: r and c in the Italic, by a small script or by hand, fitted by "
     "redraw.py, sheet, --install. f's and j's are inside: one family is not one size. "
     "The Regular's side: R/OS -17 and -14."),
     "nearest", ""),
    ("3. v's thin stroke",
     ["hairline v thin / stem"], "vwy",
     ("v (and w y, not measured) in the Italic, a family's change in the core set: one script "
     "over the kept letters, each through redraw.py's gate. The Regular's side: R/OS -27."),
     "nearest", ""),
    ("4. The ascenders against the capitals",
     ["ascender b / cap height", "ascender d / cap height", "ascender l / cap height"], "Hbdlhk",
     ("Zones: kept letters by hand within the fit's 1-unit bound is not enough (40 units); an "
     "install with the reason, b d f h k l and what is built on them, and make_italic's zone "
     "scaling for the tail. Every reference's ascenders stand at its capitals in both styles; "
     "Myia's Regular stands 4 % over them, its Italic at them. The likeliest of the five to be "
     "seen in running text."),
     "nearest", "cap"),
    ("5. The Italic's own: o's and O's overshoots; p's foot",
     ["overshoot o bottom % x-height", "overshoot O top % cap height", "foot p reach L / x-height"],
     "oxzO pq",
     ("Overshoots: o and O in the Italic by hand (O drawn 2026-11-12), taken back to the "
     "Regular's. p's foot (3 %, at the gate's edge): proposed to leave as it is."),
     "nearest", "x cap"),
    ("The question: the long stems",
     ["long stem l / stem", "long stem t / stem", "long stem f / stem", "long stem b / stem",
      "long stem d / stem", "long stem h / stem", "long stem k / stem", "long stem p / stem",
      "long stem q / stem"],
     "niu ltf bdhk pq",
     ("Inside by the gate (Old Standard draws its italic so). Kept as Old Standard's, the "
     "quality list's 52 'stroke Latin lc lighter' and 'weight' lines get 'designed'; or the "
     "long stems brought to the x-height letters' stem: reweight on the nine kept letters "
     "and what is built on them (a family's change, italic.md's second row)."),
     ["Old Standard", "Bodoni Moda"], "x"),
]

TEXT = [
    ("Latin", ("The *little* mill below the hill was *full* of poplars; the old door stood "
     "open, and the river ran *very slowly* under the bridge. *Quod erat demonstrandum*, "
     "wrote the clerk in the margin, beside a *bold* drawing of the *pupil's* hand. "
     "A *dark* cloud, a *tilted* roof, a *quick brown fox* over the *lazy dog*.")),
    ("Greek", "Η *ποίηση* του τόπου, *δηλαδή* η γλώσσα του, *είναι* η μνήμη του."),
    ("Cyrillic", "Это *книга* о *языке* и *письме*, *очень* старая и *добрая*."),
]
TEXT_FACES = ["Myia", "Old Standard", "Bodoni Moda"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def label(x, y, s, size=8, fill=LABEL, weight="normal", anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def page(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="#fffdf8"/>{"".join(body)}</svg>')


def group(src, ox, oy, k):
    """The SVG transform from a Source's deslanted 1000-em units to the
    page, slanted back: x = ox + k (x' + slant y), y = oy - k y."""
    return f'transform="matrix({k:.5f} 0 {k * src.slant:.5f} {-k:.5f} {ox:.2f} {oy:.2f})"'


def outline(src, ch):
    pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}")
    src.path(ch).draw(pen)
    return pen.getCommands()


def run_line(runs, ox, oy, size):
    """[(src, text)] set on one line from ox; returns (svg, width)."""
    k, x, out = size / bm.EM, ox, []
    for src, text in runs:
        d = []
        for ch in text:
            if not src.has(ch):
                continue
            if ch != " ":
                d.append(f'<path {group(src, x, oy, k)} d="{outline(src, ch)}"/>')
            x += src.advance(ch) * k
        out.append("".join(d))
    return f'<g fill="{INK}">{"".join(out)}</g>', x - ox


def words(roman, italic, text):
    """[(src, word)] from text with *italic* spans."""
    out, it, prev = [], False, " "
    for part in text.split("*"):
        for n, w in enumerate(part.split()):
            # a word glued to the one before (a comma after an italic word)
            glued = bool(n == 0 and out and not part[:1].isspace() and not prev[-1:].isspace())
            out.append((italic if it else roman, w, glued))
        it, prev = not it, part or prev
    return out


def wrap(ws, size, width):
    k = size / bm.EM
    lines, cur, cw = [], [], 0.0
    for src, w, glued in ws:
        ww = sum(src.advance(c) for c in w if src.has(c)) * k
        sp = 0 if glued else (src.advance(" ") if src.has(" ") else 250) * k
        if cur and not glued and cw + sp + ww > width:
            lines.append(cur)
            cur, cw = [], 0.0
        if cur and not glued:
            cur.append((src, " "))
        if cur:
            cw += sp
        cur.append((src, w))
        cw += ww
    return lines + [cur] if cur else lines


# -- the measured places, drawn


def ball_disc(src, ch):
    """(x, y, r) of the ball's disc, as bold_measures.ball finds it."""
    if ch not in bm.BALLS or not src.has(ch):
        return None
    ras = bm.Raster(src.path(ch))
    x0, y0, x1, y1 = src.path(ch).bounds
    fx0, fx1, fy0, fy1 = bm.BALLS[ch]
    c0, r0 = ras.cell(x0 + fx0 * (x1 - x0), y0 + fy1 * (y1 - y0))
    c1, r1 = ras.cell(x0 + fx1 * (x1 - x0), y0 + fy0 * (y1 - y0))
    region = ras.ink_d[r0:r1 + 1, c0:c1 + 1]
    if not region.size or region.max() <= 0:
        return None
    r, c = np.unravel_index(np.argmax(region), region.shape)
    x, y = ras.xy(c0 + c + 0.5, r0 + r + 0.5)
    return x, y, float(region.max())


def counter_disc(src, ch):
    """(x, y, r) of the widest disc in the largest counter (bold_measures.counters)."""
    if not src.has(ch):
        return None
    ras = bm.Raster(src.path(ch))
    zone, ink = src.zone(ch), ras.ink
    inner = ~ink & (bm._rays(ink) >= bm.ENCLOSED)
    labels = bm._label(inner)
    best = None
    for n in np.unique(labels[labels > 0]):
        mask = labels == n
        if mask.sum() * bm.PX * bm.PX < bm.MIN_COUNTER * zone * zone:
            continue
        d = np.maximum(bm.edt(~mask) - 0.5, 0) * bm.PX
        d[~mask] = 0
        if 2 * d.max() < bm.MIN_WIDTH * zone:
            continue
        if best is None or mask.sum() > best[0]:
            r, c = np.unravel_index(np.argmax(d), d.shape)
            best = (mask.sum(), *ras.xy(c + 0.5, r + 0.5), float(d.max()))
    return best[1:] if best else None


def marks(src, ch, names):
    """The segments and discs of the measures `names` taken on ch."""
    if not src.has(ch) or not src.path(ch).bounds:
        return [], []
    segs, discs = [], []
    for name in names:
        parts = name.split()
        c = im.Cut(src, ch)
        if parts[0] == "counter" and parts[1] == ch:
            if got := counter_disc(src, ch):
                discs.append(got)
        elif parts[0] == "ball" and parts[1] == ch:
            if got := ball_disc(src, ch):
                discs.append(got)
        elif parts[:2] == ["hairline", "v"] and ch == "v":
            im.thin_stroke(c, 0.5)
        elif parts[:2] == ["foot", ch]:
            im.foot(c, 0 if ch == "p" else -1)
        elif parts[:2] == ["long", "stem"] and parts[2] == ch:
            im.stem(c) if ch in "ltf" else im.long_stem(c)
        elif parts[0] == "stem" and ch in im.STEMS["lc"]:
            im.stem(c)
        elif parts[0] == "overshoot" and parts[1] == ch:
            y = c.y0 if "bottom" in name else c.y1
            c.mark(c.x0 + 0.3 * (c.x1 - c.x0), y, c.x1 - 0.3 * (c.x1 - c.x0), y)
        elif parts[0] == "ascender" and parts[1] == ch:
            c.mark(c.x0 - 10, c.y1, c.x1 + 10, c.y1)
        segs += c.marks
    return segs, discs


def value_of(entry, style, name):
    got = entry[style].get(name)
    return None if got is None else got[0]


def letter_names(ch, measures):
    """The measures taken on ch; on the long stems' page n i u's stem
    (marked, its value the median's, not printed)."""
    if ch in "niu" and any(n.startswith("long stem") for n in measures):
        return ["stem lc / x-height"]
    return [n for n in measures if n.split()[1] == ch or (n.startswith("long stem") and n.split()[2] == ch)]


def fmt(x, name):
    if x is None:
        return ""
    return f"{x:+.1f}" if name.startswith("overshoot") else f"{x:.2f}"


def specimen_row(src, entry, style, text, measures, guides, ox, oy, size, other=None):
    """One face's letters with their marks; the values beneath."""
    k = size / bm.EM
    body, x = [], ox
    lw = 1.1 / k
    xs = []
    for ch in text:
        if ch == " ":
            x += 0.25 * size
            continue
        if not src.has(ch):
            continue
        adv = src.advance(ch) * k
        g = group(src, x, oy, k)
        segs, discs = marks(src, ch, letter_names(ch, measures))
        parts = [f'<path d="{outline(src, ch)}" fill="{INK}" fill-opacity="0.82"/>']
        for cx, cy, r in discs:
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{DISC}" '
                         f'stroke-width="{1.6 * lw:.1f}"/>')
        for x0, y0, x1, y1 in segs:
            parts.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{MARK}" '
                         f'stroke-width="{3.2 * lw:.1f}" stroke-linecap="round"/>')
        body.append(f'<g {g}>{"".join(parts)}</g>')
        for tx in (x, x + adv):
            body.append(f'<line x1="{tx:.1f}" y1="{oy + 3:.1f}" x2="{tx:.1f}" y2="{oy + 9:.1f}" '
                        f'stroke="{TICK}" stroke-width="0.6"/>')
        xs.append((ch, x, adv))
        x += adv
    below = oy + 0.27 * size + 9
    for ch, cx, adv in xs:
        for j, n in enumerate(letter_names(ch, measures)):
            v = value_of(entry, style, n)
            if v is None or n.startswith("stem "):
                continue
            body.append(label(cx + adv / 2, below + 18 * j, fmt(v, n), 7, INK, anchor="middle"))
            if other is not None and (r := value_of(other, "regular", n)) is not None:
                rel = v - r if n.startswith("overshoot") else v / r
                sign = "Δ" if n.startswith("overshoot") else "×"
                body.append(label(cx + adv / 2, below + 18 * j + 8, f"{sign}{fmt(rel, n)}", 7, MARK,
                                  anchor="middle"))
    zone_lines = []
    if "x" in guides.split():
        zone_lines.append(src.xh)
    if "cap" in guides.split():
        zone_lines.append(src.cap)
    for y in [0, *zone_lines]:
        body.append(f'<line x1="{ox - 6:.1f}" y1="{oy - y * k:.1f}" x2="{x + 6:.1f}" y2="{oy - y * k:.1f}" '
                    f'stroke="{GUIDE}" stroke-width="0.5" stroke-dasharray="3 2"/>')
    return "".join(body)


def nearest(rows, measures, data):
    """The Didone whose relation lies nearest Myia's, over the measures."""
    by = {r["name"]: r for r in rows}
    score = {}
    for name in measures:
        r = by.get(name)
        if not r:
            continue
        for f, v in r["refs"].items():
            score[f] = score.get(f, 0) + abs(v - r["myia"])
    return [min(score, key=score.get)] if score else []


def finding_page(title, measures, letters, where, refs, guides, rows, data, srcs):
    by = {r["name"]: r for r in rows}
    if refs == "nearest":
        refs = nearest(rows, measures, data)
    faces = [("Myia", "regular"), ("Myia", "italic")] + [(f, s) for f in refs for s in ("regular", "italic")]
    step = (H - 150) / len(faces)
    size = min(144, round(step * 0.62))
    body = [label(30, 28, f"Phase 6: the Italic against the Regular — {title}", 13, INK, "bold"),
            label(30, 44, f"{size} pt, outlines and advances only. Vermilion: the stroke measured; green: the "
                  "disc measured; ochre: baseline and zones; ticks: the advances. Under each letter its own-"
                  "scale value; under the italic, × the relation (Δ for overshoots).", 8)]
    for i, (font, style) in enumerate(faces):
        oy = 70 + step * i + size * 0.8
        entry = data[font]
        body.append(label(30, oy - size * 0.8 + 2, f"{font} {style.title()}", 9, LABEL, "bold"))
        body.append(specimen_row(srcs[font][style], entry, style, letters, measures, guides, 150, oy, size,
                                 entry if style == "italic" else None))
    y = H - 72
    for name in measures:
        r = by.get(name)
        if not r:
            continue
        refs_s = ", ".join(f"{f} {fmt(v, name)}" for f, v in r["refs"].items())
        voice = ", ".join(f"{f} {fmt(v, name)}" for f, v in r["voice"].items() if v is not None)
        pos = f"{r['pos']:+.1f}" if r["kind"] == "diff" else f"{100 * r['pos']:+.0f} %"
        body.append(label(30, y, f"{name}: Myia {fmt(r['myia'], name)}; {refs_s}; past {pos}; {voice} — "
                          f"{r['verdict']}", 7.5))
        y += 9.5
        if y > H - 14:
            break
    return page(body)


def table_pages(rows):
    order = {"another typeface": 0, "candidate": 1, im.KEPT: 2, "inside": 3,
             "shown: the references spread": 4, "shown": 5}
    rows = [r for r in rows if not (r["name"].startswith("colour ") and r["name"] != "colour a-z")]
    rows.sort(key=lambda r: order[r["verdict"]])
    refs, voice, shown = (list(rows[0][k]) for k in ("refs", "voice", "shown"))
    cols = (["measure", "kind", "Myia R", "Myia I", "Myia"] + refs + ["pos", "spread"] + voice + shown
            + ["R/OS", "I/OS", "verdict"])
    widths = [190, 44, 46, 46, 46] + [58] * len(refs) + [40, 40] + [52] * (len(voice) + len(shown)) + [36, 36, 150]
    per = 68
    pages = []
    for p in range(0, len(rows), per):
        body = [label(30, 28, "Phase 6: the Italic against the Regular — the table", 13, INK, "bold"),
                label(30, 44, "Relation: the Italic's own-scale value over the Regular's; own: the Italic's value; "
                      "diff: Italic less Regular. pos: Myia past the three Didones' range (per cent; diff: the "
                      "measure's unit); spread: their range over their median, per cent. R/OS, I/OS: Myia's "
                      "styles over Old Standard's, per cent. Findings first.", 7.5)]
        y = 64
        x = 30
        for c, w in zip(cols, widths):
            body.append(label(x, y, c, 7.5, INK, "bold"))
            x += w
        for r in rows[p:p + per]:
            y += 10.6
            fill = VERDICT.get(r["verdict"])
            if fill:
                body.append(f'<rect x="26" y="{y - 8:.1f}" width="{sum(widths) + 8}" height="10.4" fill="{fill}"/>')
            k = r["kind"]
            (mr, mi), (osr, osi) = r["own"].values()

            def f(v, k=k):
                return "" if v is None else f"{v:+.1f}" if k == "diff" else f"{v:.3f}"

            pos = "" if k == "shown" else f"{r['pos']:+.1f}" if k == "diff" else f"{100 * r['pos']:+.0f}"
            rel = [f"{100 * (a / b - 1):+.0f}" if a is not None and b and k in ("relation", "own") else ""
                   for a, b in ((mr, osr), (mi, osi))]
            cells = ([r["name"], k, "" if mr is None else f"{mr:.3f}", "" if mi is None else f"{mi:.3f}",
                      f(r["myia"])] + [f(r["refs"][n]) for n in refs]
                     + [pos, "" if r["spread"] is None else str(round(100 * r["spread"]))]
                     + [f({**r["voice"], **r["shown"]}[n]) for n in voice + shown] + rel + [r["verdict"]])
            x = 30
            for c, w in zip(cells, widths):
                body.append(label(x, y, c, 7.2, INK))
                x += w
        pages.append(page(body))
    return pages


def text_pages(srcs):
    pages = []
    faces = [f for f in TEXT_FACES if f in srcs]
    # 24 pt: the faces under each other
    body = [label(30, 28, "Phase 6: the Italic against the Regular — running text, 24 pt", 13, INK, "bold"),
            label(30, 44, "Roman with italic words, outlines and advances only (no kerning in any face). "
                  "A face without the script's letters is left blank there.", 8)]
    y = 70
    size = 24
    for font in faces:
        r, i = srcs[font]["regular"], srcs[font]["italic"]
        body.append(label(30, y, font, 9, LABEL, "bold"))
        y += 8
        for script, text in TEXT:
            if not all(r.has(c) for c in text.replace("*", "") if c.isalpha()):
                body.append(label(40, y + 16, f"(no {script})", 8))
                y += 24
                continue
            for ln in wrap(words(r, i, text), size, W - 60):
                y += size * 1.25
                body.append(run_line(ln, 30, y, size)[0])
        y += 34
    pages.append(page(body))
    # 12 pt: side by side
    body = [label(30, 28, "Phase 6: the Italic against the Regular — running text, 12 pt", 13, INK, "bold")]
    cw = (W - 60) / len(faces) - 20
    size = 12
    for n, font in enumerate(faces):
        r, i = srcs[font]["regular"], srcs[font]["italic"]
        x, y = 30 + n * (cw + 20), 60
        body.append(label(x, y, font, 9, LABEL, "bold"))
        for script, text in TEXT:
            if not all(r.has(c) for c in text.replace("*", "") if c.isalpha()):
                y += 18
                body.append(label(x, y, f"(no {script})", 8))
                y += 6
                continue
            for _ in range(2):
                for ln in wrap(words(r, i, text), size, cw):
                    y += size * 1.35
                    body.append(run_line(ln, x, y, size)[0])
                y += 8
    pages.append(page(body))
    return pages


def change_page(rows):
    by = {r["name"]: r for r in rows}
    body = [label(30, 28, "Phase 6: the Italic against the Regular — the change list, for the designer", 13,
                  INK, "bold"),
            label(30, 44, "A proposal for one review round: strike what is not wanted, choose where there is a "
                  "choice. Nearly every finding is the Regular's side (R/OS); the Regular is the master, so "
                  "each is a choice to give the Italic what the Regular has, not a fault in the Italic.", 8)]
    y = 72
    for title, measures, _letters, where, _refs, _g in FINDINGS:
        body.append(label(30, y, title, 11, INK, "bold"))
        y += 15
        for name in measures:
            r = by.get(name)
            if not r:
                continue
            lo, hi = min(r["refs"].values()), max(r["refs"].values())
            pos = f"{r['pos']:+.1f}" if r["kind"] == "diff" else f"{100 * r['pos']:+.0f} %"
            body.append(label(44, y, f"{name}: Myia {fmt(r['myia'], name)}, the Didones {fmt(lo, name)} to "
                              f"{fmt(hi, name)}, past {pos} — {r['verdict']}", 8))
            y += 10.5
        line = ""
        for w in ("Where: " + where).split():
            if len(line) + len(w) > 190:
                body.append(label(44, y, line, 8, LABEL))
                y, line = y + 10.5, ""
            line = f"{line} {w}".strip()
        body.append(label(44, y, line, 8, LABEL))
        body.append(label(44, y + 12, "[ ] take   [ ] strike   note: ______________________________", 8, LABEL))
        y += 32
    return page(body)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out", nargs="?")
    args = ap.parse_args()
    today = datetime.date.today()
    out = Path(args.out) if args.out else (ROOT / "proofs" / f"{today:%Y-%m}"
                                           / f"italic-against-regular-{today}.pdf")
    data, srcs = {}, {}
    for name, roman, italic, part in im.PAIRS:
        paths = [ROOT / p if p.endswith(".ufo") else REFDIR / p for p in (roman, italic)]
        if missing := [p.name for p in paths if not p.exists()]:
            print(f"{name}: {', '.join(missing)} missing (fetch_refs.py), left out", file=sys.stderr)
            continue
        srcs[name] = {s: bm.Source(p) for s, p in zip(("regular", "italic"), paths)}
        data[name] = {"part": part, **{s: im.measure(src) for s, src in srcs[name].items()}}
    rows = im.judge(data)
    pages = table_pages(rows)
    pages += [finding_page(*f, rows, data, srcs) for f in FINDINGS]
    pages += text_pages(srcs)
    pages.append(change_page(rows))
    out.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, svg in enumerate(pages):
        f = out.with_name(f"{out.stem}-{i:02d}.svg")
        f.write_text(svg)
        pdf = f.with_suffix(".pdf")
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(f)], check=True)
        f.unlink()
        parts.append(pdf)
    subprocess.run(["pdfunite", *map(str, parts), str(out)], check=True)
    for p in parts:
        p.unlink()
    found = [r["name"] for r in rows if r["verdict"] in ("another typeface", "candidate")]
    print(f"{out}: {len(pages)} pages; findings: {len(found)}", file=sys.stderr)


if __name__ == "__main__":
    main()
