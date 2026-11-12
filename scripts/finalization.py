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
    Pass("i_bar_dot", "finish", ("Bold", *ITALIC), ("final i j", "their derivatives"), ("uni0268", "uni0249", "uni029D", "uni2071", "uni02B2", "uni1DA4")),
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
    Pass("draft_ligatures", "finish", ("Bold",), ("final T", "final t", "final h", "final O", "final u"),
         ("T_h", "t_h", "t_t", "Q_u")),
    Pass("draft_ligatures", "finish_f", ("Bold",), ("final f", "final ı ȷ l b h k t"),
         ("ff fi fl ffi ffl fj ffj", "f- and ff-ligatures before b h k t", "long-s ligatures")),
    Pass("italic_ligatures", "make", ITALIC,
         ("final f", "final ſ", "final partner letters"), ("accepted italic ligatures",)),
    Pass("smooth_joins", "finish", ITALIC, ("finished outlines",), ("named joins and brackets",)),
    # the designer's rule of 2026-11-10: no stem steps in at its serif
    Pass("stem_joins", "finish", ("Italic", "Bold", "Bold Italic"), ("finished outlines",),
         ("every bracket a stem's edge stood outside of",)),
    # the designer, 2026-11-10: a bowl's inside two curves (D Ь Ы and
    # their small caps), in the styles made from Old Standard's italic
    Pass("bowl_counters", "finish", ITALIC, ("finished outlines", "mended stem joins"), ("bowls' insides",)),
    # the designer, 2026-11-12: ы.sc's two parts and psi.sc's serif and arms do not touch
    # the designer, 2026-11-12: Ʌ's thin leg straight down to its foot, as Λ's
    Pass("turned_v", "finish", ITALIC, ("final V", "uni0245 turned from it"), ("uni0245",)),
    Pass("sc_clearance", "finish", BI, ("finished small caps",), ("uni044B.sc", "psi.sc")),
)


def finish_glyphs(font):
    for stage in PASSES:
        if font.info.styleName in stage.styles:
            getattr(import_module(stage.module), stage.entry)(font)
