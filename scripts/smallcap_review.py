"""Write a LuaLaTeX review sheet for the small capitals.

    python scripts/smallcap_review.py UFO FONT OUT.tex

One cell per small cap, drafts first (flagged DRAFT in red, built ones in
grey): the capital, the small cap and the lowercase side by side at large
size over guide lines (baseline, x-height, small-cap height, cap height),
then the small cap in context. The font is FONT (a build of UFO); the small
caps are reached through smcp/c2sc, since they have no code points.
"""

import argparse
import os
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smallcaps
from smallcaps import CAP_HEIGHT, DEFAULT_HEIGHT, DRAFT_KEY, HEIGHT_KEY, X_HEIGHT, smcp_map

UPM = 2048
SIZE = 44  # pt, the large specimen
TURKISH_LOWER = {"İ": "i"}

PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[a4paper,margin=1.2cm]{geometry}
\usepackage{fontspec,xcolor}
\setmainfont{%(font)s}[Path=%(path)s/, Renderer=HarfBuzz]
\newfontfamily\smallcapfont{%(font)s}[Path=%(path)s/, Renderer=HarfBuzz, Letters={SmallCaps,UppercaseSmallCaps}]
\newfontfamily\labelfont{DejaVu Sans Mono}[Scale=0.62]
\setlength{\parindent}{0pt}\pagestyle{empty}
\newlength\guidew
%% \guides{width}: horizontal guide lines at font-unit heights, drawn behind
\newcommand\guides[1]{\leavevmode\setlength\guidew{#1}%%
%(guides)s
}
%% \cell{label}{status}{color}{capital}{lowercase}[small-cap source, default the lowercase]
\NewDocumentCommand\cell{mmmmmO{#5}}{%%
  {\fontsize{%(size)d}{%(lead)d}\selectfont\guides{4.2cm}#4\,{\smallcapfont #6}\,#5}\newline
  {\labelfont #1 \textcolor{#3}{#2}}\newline
  {\fontsize{13}{15}\selectfont n{\smallcapfont #6}n H{\smallcapfont #6}H}}
%% \odraft{label}{source}{character}{case pair}: a drafted letter after its source
\newcommand\odraft[4]{%%
  {\fontsize{%(size)d}{%(lead)d}\selectfont\guides{4.2cm}{\color{black!35}#2}\enspace#3}\newline
  {\labelfont #1 \textcolor{red}{DRAFT}}\newline
  {\fontsize{13}{15}\selectfont x#3x H#3H\quad #4}}
%% four cells per row; each row its own table so pages break between rows
\newenvironment{cells}{\noindent\begin{tabular}{@{}*{4}{p{4.4cm}}@{}}}{\end{tabular}\par\medskip}
\begin{document}
"""


GROUPS = [
    ("sc", "IPA small capitals",
     ("Letters of their own (ɢ ɪ ʟ …) that are shaped like small capitals; they reuse "
      "the small-cap glyphs. Not the small-caps feature.")),
    ("same", "Same shape as an existing letter",
     ("A new code point for a shape the font already has (Latin ɑ = Greek α, Cyrillic "
      "һ = h); nothing is meant to look different.")),
    ("turn", "Turned",
     "Rotated by 180° (ɐ from a); the serifs end up on the wrong side, to be redrawn."),
    ("mirror", "Mirrored",
     "Mirrored left to right (ɔ from c)."),
    ("other", "From punctuation", "ʔ from the question mark, clicks from | and !."),
    ("drawn", "Drawn", "New outlines drafted from a related letter."),
]


def draft_groups(ufo):
    """Glyph name -> (group, source character) for the drafts of derive.py and ẞ."""
    import derive

    cmap = {u: g.name for g in ufo for u in g.unicodes}
    out = {"uni1E9E": ("drawn", "ß")}
    for ch, op, source, _band in derive.RECIPES:
        if ch.endswith(".sc"):
            continue
        name = cmap.get(ord(ch), derive.glyph_name(ch))
        if op == "alias":
            group = "sc" if source.endswith(".sc") else "same"
        else:
            group = {"turn": "turn", "flip": "turn", "mirror": "mirror"}.get(op, "other")
        base = source.removesuffix(".sc")
        if len(source) == 1:
            ref = source
        elif base in ufo and ufo[base].unicode:
            ref = chr(ufo[base].unicode)
            if source.endswith(".sc"):
                ref = r"{\smallcapfont %s}" % ref
        else:
            ref = ""
        out[name] = (group, ref)
    return out


def drafts_sheet(ufo, preamble):
    groups = draft_groups(ufo)
    drafts = [g for g in ufo if g.lib.get("org.myiadidot.draft") and g.unicode]
    cmap = {u for g in ufo for u in g.unicodes}
    out = [preamble, r"{\Large Myia Didot new letters — review}\par\smallskip",
           r"{\labelfont %d drafted letters. Each cell: source (grey), new letter; then in "
           r"context, and its case pair with small caps where the font has one.}"
           r"\par\bigskip" % len(drafts)]
    for key, title, note in GROUPS:
        members = [g for g in drafts if groups.get(g.name, ("drawn", ""))[0] == key]
        if not members:
            continue
        out.append(r"\par\bigskip{\large\bfseries %s}\par{\small %s}\par\medskip" % (title, note))
        cells = []
        for g in members:
            ch = chr(g.unicode)
            partner = ch.swapcase() if len(ch.swapcase()) == 1 else ch
            pair = ""
            if partner != ch and ord(partner) in cmap:
                up, lo = sorted((ch, partner), key=str.islower)
                pair = r"%s%s {\smallcapfont %s%s}" % (tex(up), tex(lo), tex(up), tex(lo))
            cells.append(r"\odraft{%s %s}{%s}{%s}{%s}"
                         % (g.name, ch, groups.get(g.name, ("", ""))[1], tex(ch), pair))
        for i in range(0, len(cells), 4):
            out.append(r"\begin{cells}" + " & ".join(cells[i:i + 4]) + r"\end{cells}")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n", len(drafts)


def tex(ch):
    return r"\symbol{%d}" % ord(ch) if ch in "\\{}$&#^_%~" else ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("font")
    ap.add_argument("out")
    ap.add_argument("--drafts", metavar="OUT2.tex", help="also write the sheet of other drafted letters")
    args = ap.parse_args()

    ufo = ufoLib2.Font.open(args.ufo)
    sc_height = ufo.lib.get(HEIGHT_KEY, DEFAULT_HEIGHT)
    smallcaps.configure(sc_height)
    guide_lines = [(0, "black!35"), (X_HEIGHT, "blue!45"), (sc_height, "red!60"), (CAP_HEIGHT, "black!35")]
    smcp, c2sc, _, _ = smcp_map(ufo)
    # one representative lowercase/capital character per small cap
    rep_lo, rep_up = {}, {}
    for name, sc in sorted(smcp.items()):
        u = ufo[name].unicode
        rep_lo.setdefault(sc, chr(u))
    for name, sc in sorted(c2sc.items()):
        rep_up.setdefault(sc, chr(ufo[name].unicode))

    scs = sorted((g for g in ufo if g.name.endswith(".sc")),
                 key=lambda g: (not g.lib.get(DRAFT_KEY), g.name))
    n_drafts = sum(1 for g in scs if g.lib.get(DRAFT_KEY))

    guides = "\n".join(
        r"\rlap{\textcolor{%s}{\rule[%.4fpt]{\guidew}{0.25pt}}}%%" % (color, units / UPM * SIZE)
        for units, color in guide_lines
    )
    path = os.path.relpath(Path(args.font).resolve().parent, Path(args.out).resolve().parent)
    preamble = PREAMBLE % {"font": Path(args.font).name, "path": path, "guides": guides,
                           "size": SIZE, "lead": int(SIZE * 1.15)}
    out = [preamble]
    out.append(r"{\Large Myia Didot small caps — review}\par\smallskip")
    out.append(r"{\labelfont %d small caps, \textcolor{red}{%d drafts} to review. "
               r"Guides: baseline, \textcolor{blue!60}{x-height %d}, "
               r"\textcolor{red!70}{small-cap height %d}, cap height %d. "
               r"Each cell: capital, small cap, lowercase; then in context.}\par\bigskip"
               % (len(scs), n_drafts, X_HEIGHT, sc_height, CAP_HEIGHT))
    skipped = []
    section = None
    row = []
    def flush():
        if row:
            out.append(r"\begin{cells}" + " & ".join(row) + r"\end{cells}")
            row.clear()

    for g in scs:
        is_draft = bool(g.lib.get(DRAFT_KEY))
        if section != is_draft:
            flush()
            section = is_draft
            title = "Drafts (FontForge, to review)" if is_draft else "Built from components"
            out.append(r"\par\bigskip{\large\bfseries %s}\par\medskip" % title)
        lo = rep_lo.get(g.name)
        up = rep_up.get(g.name)
        if lo is None and up is None:
            skipped.append(g.name)
            continue
        lo = lo or up
        if up is None:
            # ĸ, ȷ: lowercase-only letters; ch.upper() would return the letter itself
            up = lo.upper() if lo.upper() != lo else None
        status, color = ("DRAFT", "red") if is_draft else ("built", "black!45")
        label = g.name.replace("_", r"\_")
        cap = tex(up) if up else r"\textcolor{black!30}{—}"
        cell = r"\cell{%s}{%s}{%s}{%s}{%s}" % (label, status, color, cap, tex(lo))
        if lo == up and lo.lower() != lo:
            # İ: no lowercase of its own outside Turkish, where it is i; the
            # small cap is shown from the capital (c2sc)
            lo = TURKISH_LOWER.get(up)
            if lo:
                cell = r"\cell{%s (Turkish %s)}{%s}{%s}{%s}{%s}[%s]" % (
                    label, lo, status, color, cap, tex(lo), tex(up))
        row.append(cell)
        if len(row) == 4:
            flush()
    flush()
    out.append(r"\end{document}")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    if args.drafts:
        text, n = drafts_sheet(ufo, preamble)
        Path(args.drafts).write_text(text, encoding="utf-8")
        print(f"{args.drafts}: {n} drafted letters")
    print(f"{args.out}: {len(scs)} small caps ({n_drafts} drafts)"
          + (f", not reachable from a character: {' '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
