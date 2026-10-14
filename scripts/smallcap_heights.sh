#!/bin/sh
# Build trial fonts with small caps at several heights, for comparison.
#
#   scripts/smallcap_heights.sh OUTDIR 960 1000 1040
#
# Each height gets a copy of the master UFO in OUTDIR/<h>/, freshly drafted
# small caps (unreviewed drafts replaced), and OUTDIR/MyiaSC<h>-Regular.otf
# under its own family name. The master UFO is not touched.
set -e
out=$1; shift
root=$(cd "$(dirname "$0")/.." && pwd)
py="$root/.venv/bin/python -I"
for h in "$@"; do
    dir="$out/$h"
    rm -rf "$dir" && mkdir -p "$dir"
    cp -r "$root/sources/MyiaDidot-Regular.ufo" "$dir/"
    ufo="$dir/MyiaDidot-Regular.ufo"
    stem=$($py -c "import sys; sys.path.insert(0, '$root/scripts'); import smallcaps; print(smallcaps.stem_for($h))")
    fontforge -quiet -lang=py -script "$root/scripts/smallcaps_draft.py" "$ufo" "$dir/draft.ufo" "$h" "$stem" 2>/dev/null
    $py "$root/scripts/smallcaps.py" "$ufo" --drafts "$dir/draft.ufo" --redraft --height "$h" >/dev/null
    $py - "$ufo" "$h" <<'EOF'
import sys, ufoLib2
f = ufoLib2.Font.open(sys.argv[1])
f.info.familyName = f.info.styleMapFamilyName = f"Myia SC{sys.argv[2]}"
f.info.postscriptFontName = f"MyiaSC{sys.argv[2]}-Regular"
f.info.postscriptFullName = f"Myia SC{sys.argv[2]} Regular"
f.save()
EOF
    "$root/.venv/bin/fontmake" -u "$ufo" -o otf --output-path "$out/MyiaSC$h-Regular.otf" >/dev/null 2>&1
    echo "$h: stem $stem -> $out/MyiaSC$h-Regular.otf"
done
