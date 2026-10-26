"""The release archive: one version for every style, checksums that hold,
the same bytes each time."""

import hashlib
import zipfile

import pytest
import release


def test_versions_must_agree(monkeypatch):
    fonts = [release.ROOT / f"fonts/otf/{release.FAMILY}-{style}.otf" for style in release.STYLES]
    monkeypatch.setattr(release, "ufo_version", lambda style: "0.100")
    monkeypatch.setattr(release, "font_version", lambda path: "0.101" if "Bold" in path.name else "0.100")
    monkeypatch.setattr(release.Path, "exists", lambda self: True)
    with pytest.raises(SystemExit, match="versions disagree"):
        release.check(fonts)
    monkeypatch.setattr(release, "font_version", lambda path: "0.100")
    assert release.check(fonts) == "0.100"


def test_archive_checksums_and_reproducible(monkeypatch, tmp_path):
    fonts = []
    for folder, ext in release.FORMATS:
        (tmp_path / folder).mkdir()
        p = tmp_path / folder / f"{release.FAMILY}-Regular.{ext}"
        p.write_bytes(ext.encode() * 10)
        fonts.append(p)
    monkeypatch.setattr(release, "SPECIMEN", tmp_path / "none.pdf")
    files = release.members("0.100", fonts)
    top = f"{release.FAMILY}-0.100"
    assert f"{top}/otf/{release.FAMILY}-Regular.otf" in files and f"{top}/OFL.txt" in files
    sums = dict(line.split("  ")[::-1] for line in files[f"{top}/SHA256SUMS"].decode().splitlines())
    assert set(sums) == {name.split("/", 1)[1] for name in files} - {"SHA256SUMS"}
    for name, data in files.items():
        if not name.endswith("SHA256SUMS"):
            assert sums[name.split("/", 1)[1]] == hashlib.sha256(data).hexdigest()
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    release.write(a, files, 1761500000)
    release.write(b, dict(reversed(list(files.items()))), 1761500000)
    assert a.read_bytes() == b.read_bytes()
    assert zipfile.ZipFile(a).namelist() == sorted(files)
