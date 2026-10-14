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
from smallcaps import CAP_HEIGHT, DRAFT_KEY, SC_HEIGHT, X_HEIGHT, smcp_map

UPM = 2048
SIZE = 44  # pt, the large specimen
GUIDES = [(0, "black!35"), (X_HEIGHT, "blue!45"), (SC_HEIGHT, "red!60"), (CAP_HEIGHT, "black!35")]

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
        for units, color in GUIDES
    )
    path = os.path.relpath(Path(args.font).resolve().parent, Path(args.out).resolve().parent)
    out = [PREAMBLE % {"font": Path(args.font).name, "path": path, "guides": guides,
                       "size": SIZE, "lead": int(SIZE * 1.15)}]
    out.append(r"{\Large Myia Didot small caps — review}\par\smallskip")
    out.append(r"{\labelfont %d small caps, \textcolor{red}{%d drafts} to review. "
               r"Guides: baseline, \textcolor{blue!60}{x-height %d}, "
               r"\textcolor{red!70}{small-cap height %d}, cap height %d. "
               r"Each cell: capital, small cap, lowercase; then in context.}\par\bigskip"
               % (len(scs), n_drafts, X_HEIGHT, SC_HEIGHT, CAP_HEIGHT))
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
        up = up or lo.upper()
        status, color = ("DRAFT", "red") if is_draft else ("built", "black!45")
        label = g.name.replace("_", r"\_")
        row.append(r"\cell{%s}{%s}{%s}{%s}{%s}" % (label, status, color, tex(up), tex(lo)))
        if len(row) == 4:
            flush()
    flush()
    out.append(r"\end{document}")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{args.out}: {len(scs)} small caps ({n_drafts} drafts)"
          + (f", not reachable from a character: {' '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
