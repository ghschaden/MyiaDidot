"""HarfBuzz setup shared by tests and command-line tools; English by default."""

import uharfbuzz as hb
from fontTools.ttLib import TTFont


class Shaper:
    def __init__(self, path):
        blob = hb.Blob.from_file_path(str(path))
        self.font = hb.Font(hb.Face(blob))
        tt = TTFont(path)
        self.order = tt.getGlyphOrder()
        self.cmap = tt.getBestCmap()

    def shape(self, text, features=None, *, script=None, language=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        buf.language = {"TRK": "tr", "ROM": "ro", "DEU": "de"}.get(language, language) or "en"
        hb.shape(self.font, buf, features or {})
        return [
            (self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions, strict=True)
        ]

