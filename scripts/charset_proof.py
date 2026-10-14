"""Write a LuaLaTeX proof of every encoded character, grouped by block.

    python scripts/charset_proof.py FONT OUT.tex [--baseline OLDFONT]

Characters missing from --baseline are printed in red, so new glyphs can be
reviewed at a glance. Each character is also shown between H/n (or Η/η,
Н/н for Greek and Cyrillic) to judge spacing.
"""

import argparse
import os
import unicodedata

from fontTools.ttLib import TTFont
from fontTools.unicodedata import block

PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[a4paper,margin=1.5cm]{geometry}
\usepackage{fontspec,xcolor}
\setmainfont{%(name)s}[Path=%(path)s/, Renderer=HarfBuzz]
\newfontfamily\labelfont{DejaVu Sans Mono}[Scale=0.55]
\setlength{\parindent}{0pt}
\pagestyle{empty}
\newcommand\cell[3]{\parbox[b]{1.7cm}{\centering{\fontsize{20}{24}\selectfont\color{#3}#2}\\[-1pt]{\labelfont #1}}\hspace{0pt}}
\begin{document}
"""


def tex_escape(ch):
    if ch in "\\{}$&#^_%~":
        return r"\symbol{%d}" % ord(ch)
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("out")
    ap.add_argument("--baseline")
    args = ap.parse_args()

    cmap = TTFont(args.font).getBestCmap()
    old = set(TTFont(args.baseline).getBestCmap()) if args.baseline else set(cmap)

    font_path = os.path.relpath(os.path.dirname(os.path.abspath(args.font)),
                                os.path.dirname(os.path.abspath(args.out)))
    lines = [PREAMBLE % {"name": os.path.basename(args.font), "path": font_path}]
    new = sorted(set(cmap) - old)
    lines.append(r"{\Large %s}\par\medskip" % os.path.basename(args.font).replace("_", r"\_"))
    lines.append(r"%d characters, \textcolor{red}{%d new}\par\bigskip" % (len(cmap), len(new)))

    current = None
    for cp in sorted(cmap):
        if cp < 0x20 or cp == 0xAD or unicodedata.category(chr(cp)) in ("Cc", "Zs", "Cf"):
            continue
        b = block(chr(cp))
        if b != current:
            lines.append(r"\par\bigskip{\large\bfseries %s}\par\smallskip" % b)
            current = b
        ch = chr(cp)
        shown = ("◌" + ch) if unicodedata.category(ch) == "Mn" and 0x25CC in cmap else ch
        color = "red" if cp in new else "black"
        lines.append(r"\cell{%04X}{%s}{%s}" % (cp, tex_escape(shown), color))

    if new:
        lines.append(r"\newpage{\large\bfseries New characters in context}\par\medskip")
        lines.append(r"{\raggedright\fontsize{18}{30}\selectfont")
        for cp in new:
            ch = chr(cp)
            if unicodedata.category(ch)[0] != "L":
                continue
            name = unicodedata.name(ch, "")
            h, n = ("Η", "η") if "GREEK" in name else ("Н", "н") if "CYRILLIC" in name else ("H", "n")
            ctx = h if unicodedata.category(ch) == "Lu" else n
            lines.append(f"{ctx}{ctx}{tex_escape(ch)}{ctx}{ctx}\\quad")
        lines.append(r"\par}")
    lines.append(r"\end{document}")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
