"""Ordered finishing passes after rounding and before stack/horn fitting.

The registry states which styles, completed inputs and glyphs each pass owns.
The individual passes still check their local preconditions. Keep the order:
later passes may read glyphs corrected by earlier ones.
"""

from importlib import import_module
from typing import NamedTuple


class Pass(NamedTuple):
    module: str
    entry: str
    styles: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


ALL = ("Regular", "Italic", "Bold", "Bold Italic")
ITALIC = ("Italic", "Bold Italic")
BOLD = ("Bold", "Bold Italic")
BI = ("Bold Italic",)

PASSES = (
    Pass("cedilla", "finish", ALL, ("rounded Cedilla",), ("Cedilla",)),
    Pass("t_slash", "finish", BI, ("weighted uni023E",), ("uni023E",)),
    Pass("sc_feet", "finish", BOLD, ("weighted m.sc", "weighted v.sc", "weighted w.sc"), ("m.sc", "v.sc", "w.sc", "k.sc", "x.sc")),
    Pass("j_bar", "finish", BI, ("weighted uni0249",), ("uni0249",)),
    Pass("dollar_bars", "finish", BI, ("weighted dollar",), ("dollar",)),
    Pass("dollar_drawing", "finish", BI, ("dollar after bar correction",), ("dollar",)),
    Pass("aleph", "finish", BOLD, ("weighted uni2135",), ("uni2135",)),
    Pass("symbol_joins", "finish", BOLD, ("weighted symbols",), ("uni2116", "trademark")),
    Pass("glottal_modifier", "finish", ("Bold",), ("final uni0242",), ("uni02C0",)),
    Pass("phi_drawing", "finish", BI, ("final o", "final l"), ("uni0278",)),
    Pass("oldstyle_figures", "finish", ALL,
         ("final lining figures", "reviewed oldstyle GLIFs"), ("oldstyle figures", "zerooldstyle.zero")),
    Pass("r_hook", "fair_bold_stem", ("Bold",), ("final r",), ("r", "uni027D")),
    Pass("stem_handles", "finish", ("Bold",), ("final r", "rounded outlines"), ("curves into stems",)),
    Pass("r_hook", "finish_shoulders", ITALIC, ("final italic r family",), ("r family shoulders",)),
    Pass("r_hook", "finish_turned_r_top", BI, ("r family shoulders", "final l"), ("uni027A",)),
    Pass("r_hook", "finish", ITALIC, ("final same-style r",), ("uni027D",)),
    Pass("l_belt", "finish", ("Italic",), ("final l", "final L"), ("uni026C", "uniA7AD")),
    Pass("draft_ligatures", "finish", ("Bold",), ("final T", "final t", "final h"), ("T_h", "t_h")),
    Pass("italic_ligatures", "make", ITALIC,
         ("final f", "final ſ", "final partner letters"), ("accepted italic ligatures",)),
)


def finish_glyphs(font):
    for stage in PASSES:
        if font.info.styleName in stage.styles:
            getattr(import_module(stage.module), stage.entry)(font)
