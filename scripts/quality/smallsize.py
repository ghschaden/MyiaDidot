"""smallsize.py FONT...: glyphs that break apart when rendered small (hinted,
grey): bitmap pieces (8-connected, coverage over 35%) beyond the outline's own."""
import sys

import freetype
import numpy as np

CH = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789αβγδεζηθικλμνξοπρστυφχψωабвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЖЗИЛПФЦЧШЩЭЮЯ"
def render(face, ch, ppem, hint=True):
    face.set_pixel_sizes(0, ppem)
    flags = freetype.FT_LOAD_RENDER | (0 if hint else freetype.FT_LOAD_NO_HINTING)
    face.load_char(ch, flags)
    bm = face.glyph.bitmap
    if not bm.rows:
        return np.zeros((1, 1), np.uint8)
    return np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)


def pieces(mask):
    h, w = mask.shape; seen = np.zeros_like(mask, bool); n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                n += 1; st = [(y, x)]; seen[y, x] = True
                while st:
                    cy, cx = st.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = cy + dy, cx + dx
                            if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True; st.append((yy, xx))
    return n
for path in sys.argv[1:]:
    face = freetype.Face(path)
    res = {}
    for ppem in (9, 11, 13, 16):
        broken = []
        for ch in CH:
            if face.get_char_index(ch) == 0:
                continue
            big = render(face, ch, 200, hint=False) > 128
            want = pieces(big)
            a = render(face, ch, ppem)
            got = pieces(a > 90)
            if got > want:
                broken.append(ch)
        res[ppem] = broken
    name = path.split("/")[-1][:24]
    print(f"{name:24} " + "  ".join(f"{p}px: {len(b):3}" for p, b in res.items()) + "   e.g. 11px: " + "".join(res[11][:30]))
