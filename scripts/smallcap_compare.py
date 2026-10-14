"""Comparison page for trial small-cap heights (see smallcap_heights.sh).

    python scripts/smallcap_compare.py DIR 960 1000 1040

Expects DIR/MyiaSC<h>-Regular.otf for each height and writes DIR/compare.tex:
per height, a large line over guide lines (baseline, x-height, small-cap
height, cap height) and a paragraph with small caps in running text.
"""

import sys
from pathlib import Path

UPM, X_HEIGHT, CAP_HEIGHT = 2048, 884, 1434
PT = 38

TEXT = (r"In {\SC unesco} and {\SC nato} reports of the {\SC xix}th century, {\SC Myia Didot} "
        r"sets names like {\SC Firmin Didot} and {\SC Alexey Kryukov} in small capitals. "
        r"Zwölf {\SC Boxkämpfer} jagen Viktor quer über den großen Sylter Deich. "
        r"Ἄνδρα μοι ἔννεπε, {\SC Μοῦσα}, πολύτροπον. Съешь же {\SC ещё этих} мягких булок.")


def main():
    out, heights = Path(sys.argv[1]), [int(h) for h in sys.argv[2:]]
    lines = [r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=1.6cm]{geometry}
\usepackage{fontspec,xcolor}
\setlength{\parindent}{0pt}\pagestyle{empty}
\newfontfamily\labelfont{DejaVu Sans Mono}[Scale=0.7]"""]
    for i, h in enumerate(heights):
        tag = "abcdefgh"[i]
        lines.append(rf"\newfontfamily\f{tag}{{MyiaSC{h}-Regular.otf}}[Path=./, Renderer=HarfBuzz]")
        lines.append(rf"\newfontfamily\f{tag}sc{{MyiaSC{h}-Regular.otf}}[Path=./, Renderer=HarfBuzz, Letters=SmallCaps]")
    lines.append(r"\begin{document}")
    lines.append(r"{\large Small-cap height: %s (x-height %d, cap height %d)}\par\bigskip"
                 % (" / ".join(map(str, heights)), X_HEIGHT, CAP_HEIGHT))
    for i, h in enumerate(heights):
        tag = "abcdefgh"[i]
        guides = "".join(
            r"\rlap{\textcolor{%s}{\rule[%.3fpt]{15cm}{0.3pt}}}" % (color, units / UPM * PT)
            for units, color in [(0, "black!30"), (X_HEIGHT, "blue!50"), (h, "red!70"), (CAP_HEIGHT, "black!30")]
        )
        lines.append(r"{\labelfont small caps at %d (%.0f\%% of cap height, %d above x-height)}\par\smallskip"
                     % (h, h / CAP_HEIGHT * 100, h - X_HEIGHT))
        lines.append(r"{\f%s\fontsize{%d}{%d}\selectfont\leavevmode%sHxn{\f%ssc hamburgefon}xH}\par\medskip"
                     % (tag, PT, PT + 8, guides, tag))
        body = TEXT.replace(r"\SC", rf"\f{tag}sc")
        lines.append(r"{\f%s\fontsize{12.5}{16}\selectfont %s}\par\bigskip\bigskip" % (tag, body))
    lines.append(r"\end{document}")
    (out / "compare.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
