"""The generators' data modules hold data only (T5, docs/claude/tables.md):
each imports only other data modules, italic_geometry and the standard
library, its functions read nothing but their own arguments and math,
and its generator re-exports every name, so GENERATOR.NAME still reads
the table.
"""

import ast
import builtins
import importlib
import sys

import pytest
from conftest import ROOT

DATA = sorted((ROOT / "scripts").glob("data_*.py"))
GENERATOR = {"data_regular": "derive", "data_italic": "make_italic",
             "data_bold": "make_bold", "data_bold_italic": "make_bold"}


def test_the_four_modules():
    assert sorted(p.stem for p in DATA) == sorted(GENERATOR)


@pytest.mark.parametrize("path", DATA, ids=lambda p: p.stem)
def test_imports_only_data(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [node.module]
        else:
            continue
        for mod in mods:
            top = mod.split(".")[0]
            assert top.startswith("data_") or top == "italic_geometry" or top in sys.stdlib_module_names, \
                f"{path.name}:{node.lineno} imports {mod}"


@pytest.mark.parametrize("path", DATA, ids=lambda p: p.stem)
def test_functions_read_only_their_arguments(path):
    tree = ast.parse(path.read_text())
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        own = {a.arg for a in ast.walk(fn.args) if isinstance(a, ast.arg)}
        own |= {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
        read = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
        outside = read - own - {"math"} - set(dir(builtins))
        assert not outside, f"{path.name}: {fn.name} reads {sorted(outside)}"


@pytest.mark.parametrize("path", DATA, ids=lambda p: p.stem)
def test_generator_reexports(path):
    data = importlib.import_module(path.stem)
    generator = importlib.import_module(GENERATOR[path.stem])
    tree = ast.parse(path.read_text())
    names = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names |= {x.id for x in ast.walk(target) if isinstance(x, ast.Name)}
    missing = sorted(n for n in names if getattr(generator, n, None) is not getattr(data, n))
    assert not missing, f"{GENERATOR[path.stem]} does not re-export {missing}"
