"""The Bold Italic's stroke cache (scripts/stroke_cache.py) keeps a result
only under the exact job and code that made it.

`make reproduce` checks a run from the cache against the saved styles; this
checks the key: every module stroke_bold reads is in it, any change to the
job or the code gives another key, and the cache can be turned off.
"""

import stroke_cache


def test_modules_cover_the_stroker():
    mods = stroke_cache.modules()
    # stroke_bold's own imports and theirs (derive imports others in turn)
    assert {"stroke_bold", "fair_arcs", "derive"} <= set(mods)


def test_round_trip_and_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("MYIA_STROKE_CACHE", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("MYIA_BLEND_LOG", raising=False)
    cache = stroke_cache.Cache()
    job = ("a", [("moveTo", ((0.1, 2.0),)), ("closePath", ())], (56.0, 30, False))
    twin = ("a.alt", job[1], job[2])  # drawn alike: shares the result
    other = ("a", job[1], (56.0000001, 30, False))
    assert cache.get([job]) == {}
    cache.put([job], {"a": [("moveTo", ((1.5, 2.25),))]})
    assert cache.get([job, twin, other]) == {"a": [("moveTo", ((1.5, 2.25),))],
                                             "a.alt": [("moveTo", ((1.5, 2.25),))]}
    cache.put([other], {"a": None})  # a failure is kept as one
    assert cache.get([other]) == {"a": None}
    code = cache.code
    monkeypatch.setenv("MYIA_G2_ERR", "4")  # stroke_bold reads it
    assert stroke_cache.code_key() != code
    monkeypatch.setenv("MYIA_JOBS", "1")  # only steers the run
    monkeypatch.delenv("MYIA_G2_ERR")
    assert stroke_cache.code_key() == code
    cache.close()


def test_off(monkeypatch):
    monkeypatch.setenv("MYIA_STROKE_CACHE", "0")
    assert stroke_cache.Cache().db is None
    monkeypatch.setenv("MYIA_STROKE_CACHE", "")
    monkeypatch.setenv("MYIA_BLEND_LOG", "/dev/null")
    assert stroke_cache.Cache().db is None
