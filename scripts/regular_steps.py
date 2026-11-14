"""The Regular's generated parts made again in place: the scripts of
tests/test_generated_current.py's STEPS, in its order, then
nfd_compose.py and the normalizer; what `make check-regular` runs before
the Regular's tests (docs/claude/tests.md).

    python scripts/regular_steps.py [UFO]

One list: STEPS is the test's own, so the sequence run here is the one
the test holds the Regular to.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from test_generated_current import STEPS  # noqa: E402


def main():
    ufo = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sources" / "MyiaDidot-Regular.ufo"
    for script, *args in [*STEPS, ["scripts/nfd_compose.py"]]:
        r = subprocess.run([sys.executable, "-I", str(ROOT / script), str(ufo), *args],
                           capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        print(f"{Path(script).name}: {'ok' if r.returncode == 0 else 'FAILED'}  {last[:100]}")
        if r.returncode:
            print(r.stderr[-2000:], file=sys.stderr)
            return 1
    subprocess.run([str(ROOT / ".venv/bin/ufonormalizer"), "-q", "-m", str(ufo)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
