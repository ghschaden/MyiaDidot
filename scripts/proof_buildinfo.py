"""The build a proof PDF was made from, for its footer: writes
build/proofs/buildinfo.tex with \\buildinfo = date, short commit, and
"+ changes" when sources/ differs from it (samples.tex, specimen.tex,
textpages.tex read it).

    python scripts/proof_buildinfo.py
"""

import datetime
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    def git(*args):
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)

    commit = git("rev-parse", "--short", "HEAD").stdout.strip() or "no commit"
    changed = git("diff", "--quiet", "HEAD", "--", "sources").returncode != 0
    info = f"{datetime.date.today().isoformat()}, {commit}{' + changes' if changed else ''}"
    out = ROOT / "build" / "proofs" / "buildinfo.tex"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"\\def\\buildinfo{{{info}}}\n", encoding="utf-8")
    print(f"{out}: {info}")


if __name__ == "__main__":
    main()
