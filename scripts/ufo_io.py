"""Persist a completed UFO without applying design or geometry operations."""

import ufoLib2


def save_font(font, path):
    if not path.exists():
        font.save(path)
        return
    if not (path / "metainfo.plist").exists() or not (path / "layercontents.plist").exists():
        font.save(path, overwrite=True)  # what a failed run left: not a UFO yet
        return
    target = ufoLib2.Font.open(path)
    # delete only what is gone: deleting a glyph and inserting it again under
    # the same name gets its file removed on saving
    for name in [n for n in target.keys() if n not in font]:  # noqa: SIM118 (a Font iterates glyphs)
        del target[name]
    for g in font:
        target.layers.defaultLayer.insertGlyph(g, g.name, overwrite=True)
    target.info = font.info
    target.kerning = font.kerning
    target.groups = font.groups
    target.features = font.features
    target.lib = font.lib
    target.save()

