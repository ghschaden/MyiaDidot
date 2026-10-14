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
%% \cell{label}{status}{color}{capital}{lowercase}
\newcommand\cell[5]{%%
  {\fontsize{%(size)d}{%(lead)d}\selectfont\guides{4.2cm}#4\,{\smallcapfont #5}\,#5}\newline
  {\labelfont #1 \textcolor{#3}{#2}}\newline
  {\fontsize{13}{15}\selectfont n{\smallcapfont #5}n H{\smallcapfont #5}H}}
%% four cells per row; each row its own table so pages break between rows
\newenvironment{cells}{\noindent\begin{tabular}{@{}*{4}{p{4.4cm}}@{}}}{\end{tabular}\par\medskip}
\begin{document}
"""


def tex(ch):
    return r"\symbol{%d}" % ord(ch) if ch in "\\{}$&#^_%~" else ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("font")
    ap.add_argument("out")
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
    out = [PREAMBLE % {"font": Path(args.font).name, "path": path, "guides": guides,
                       "size": SIZE, "lead": int(SIZE * 1.15)}]
    out.append(r"{\Large Myia Didot small caps — review}\par\smallskip")
    others = [g for g in ufo if g.lib.get("org.myiadidot.draft") and g.unicode]
    out.append(r"{\labelfont %d small caps, \textcolor{red}{%d drafts} to review. "
               r"Guides: baseline, \textcolor{blue!60}{x-height %d}, "
               r"\textcolor{red!70}{small-cap height %d}, cap height %d. "
               r"Each cell: capital, small cap, lowercase; then in context.}\par\bigskip"
               % (len(scs), n_drafts, X_HEIGHT, sc_height, CAP_HEIGHT))
    skipped = []
    section = None
    row = []
    if others:
        out.append(r"{\large\bfseries Other drafts}\par\medskip")
        cells = []
        for g in others:
            ch = chr(g.unicode)
            lo = ch.lower() if len(ch.lower()) == 1 else ch
            cells.append(r"\cell{%s}{%s}{%s}{%s}{%s}" % (g.name, "DRAFT", "red", tex(ch), tex(lo)))
        out.append(r"\begin{cells}" + " & ".join(cells) + r"\end{cells}")

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
        row.append(r"\cell{%s}{%s}{%s}{%s}{%s}" % (label, status, color, cap, tex(lo)))
        if len(row) == 4:
            flush()
    flush()
    out.append(r"\end{document}")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{args.out}: {len(scs)} small caps ({n_drafts} drafts)"
          + (f", not reachable from a character: {' '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
