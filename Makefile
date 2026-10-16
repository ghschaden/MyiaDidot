PY       := .venv/bin/python -I
FONTMAKE := .venv/bin/fontmake
FAMILY   := MyiaDidot
UPSTREAM := sources/upstream/TheanoDidot-Regular.sfd
UFOS     := sources/$(FAMILY)-Regular.ufo sources/$(FAMILY)-Bold.ufo sources/$(FAMILY)-Italic.ufo

OTF   := $(patsubst sources/%.ufo,fonts/otf/%.otf,$(UFOS))
TTF   := $(patsubst sources/%.ufo,fonts/ttf/%.ttf,$(UFOS))
WOFF2 := $(patsubst sources/%.ufo,fonts/webfonts/%.woff2,$(UFOS))

# Rebuild when any file inside the UFO changes.
.SECONDEXPANSION:
UFO_FILES = $$(shell find sources/$$*.ufo -type f)
.SECONDARY:

.PHONY: all setup test test-data fonts otf ttf webfonts compare regress qa proof udhr normalize winmetrics reimport clean

all: fonts

setup:
	uv sync
	git config core.hooksPath tools/git-hooks
	@echo "pre-commit hook installed (tools/git-hooks/pre-commit)"

test:
	.venv/bin/pytest

# Accept the current behaviour as the new baseline (review git diff tests/data!).
test-data:
	$(PY) scripts/update_test_data.py --golden --digest --cmap

winmetrics:
	$(PY) scripts/set_win_metrics.py $(UFOS)

fonts: otf ttf webfonts
otf: $(OTF)
ttf: $(TTF)
webfonts: $(WOFF2)

fonts/otf/%.otf: sources/%.ufo $(UFO_FILES)
	$(FONTMAKE) -u $< -o otf --output-path $@

# Unhinted TTF in build/, then ttfautohint into fonts/ttf.
build/unhinted/%.ttf: sources/%.ufo $(UFO_FILES)
	$(FONTMAKE) -u $< -o ttf --flatten-components --output-path $@

fonts/ttf/%.ttf: build/unhinted/%.ttf
	@mkdir -p $(dir $@)
	ttfautohint --no-info --stem-width-mode=nss --windows-compatibility $< $@

fonts/webfonts/%.woff2: fonts/ttf/%.ttf
	@mkdir -p $(dir $@)
	$(PY) -m fontTools.ttLib.woff2 compress -o $@ $<

# --- upstream round-trip check -------------------------------------------
# Builds Theano Didot straight from the pinned SFD with FontForge and
# compares HarfBuzz shaping against our build (without production names).

build/reference/TheanoDidot-Regular.otf: $(UPSTREAM) scripts/sfd_reference.py
	fontforge -quiet -lang=py -script scripts/sfd_reference.py $< build/reference

build/compare/%.otf: sources/%.ufo $(UFO_FILES)
	$(FONTMAKE) -u $< -o otf --no-production-names --output-path $@

compare: build/reference/TheanoDidot-Regular.otf build/compare/$(FAMILY)-Regular.otf
	$(PY) scripts/compare_shaping.py $^ --renames sources/glyph-renames.json

# --- regression check against a git revision (default: HEAD) ------------

REF ?= HEAD

regress: build/compare/$(FAMILY)-Regular.otf
	rm -rf build/baseline && mkdir -p build/baseline
	git archive $(REF) sources | tar -x -C build/baseline
	$(FONTMAKE) -u build/baseline/sources/$(FAMILY)-Regular.ufo -o otf \
	    --no-production-names --output-path build/baseline/$(FAMILY)-Regular.otf
	$(PY) scripts/compare_shaping.py build/baseline/$(FAMILY)-Regular.otf $<

# --- proofs ----------------------------------------------------------------

proof: $(OTF) build/baseline/$(FAMILY)-Regular.otf
	@mkdir -p build/proofs
	$(PY) scripts/charset_proof.py fonts/otf/$(FAMILY)-Regular.otf build/proofs/charset.tex \
	    --baseline build/baseline/$(FAMILY)-Regular.otf
	$(PY) scripts/smallcap_review.py sources/$(FAMILY)-Regular.ufo fonts/otf/$(FAMILY)-Regular.otf build/proofs/smallcaps-review.tex \
	    --drafts build/proofs/drafts-review.tex
	$(PY) scripts/smallcap_review.py sources/$(FAMILY)-Italic.ufo fonts/otf/$(FAMILY)-Italic.otf build/proofs/smallcaps-review-Italic.tex \
	    --drafts build/proofs/drafts-review-Italic.tex
	cd build/proofs && for t in charset smallcaps-review drafts-review smallcaps-review-Italic drafts-review-Italic; do \
	    lualatex -interaction=nonstopmode $$t.tex >/dev/null; done
	cd proofs && for t in proof smallcaps samples textpages; do \
	    lualatex -interaction=nonstopmode --output-directory=../build/proofs $$t.tex >/dev/null; done
	@echo "proofs: build/proofs/{charset,proof,samples,textpages,smallcaps,smallcaps-review,drafts-review}.pdf, *-review-Italic.pdf"

# One quarto page per language, the UDHR (texts fetched once into build/udhr)
udhr: $(OTF)
	@mkdir -p build/proofs
	$(PY) scripts/udhr_book.py fonts/otf build/proofs/udhr-quarto.tex --cache build/udhr
	cd build/proofs && lualatex -interaction=nonstopmode udhr-quarto.tex >/dev/null
	@echo "proof: build/proofs/udhr-quarto.pdf"

# --- QA ------------------------------------------------------------------

qa: $(OTF) $(TTF)
	@mkdir -p build/qa
	for fmt in otf ttf; do \
	    .venv/bin/fontbakery check-universal --html build/qa/fontbakery-$$fmt.html \
	        --ghmarkdown build/qa/fontbakery-$$fmt.md fonts/$$fmt/*.$$fmt || true; \
	done
	@echo "reports: build/qa/fontbakery-{otf,ttf}.html"

normalize:
	for u in $(UFOS); do .venv/bin/ufonormalizer -m $$u || exit 1; done

# --- one-off import (overwrites the source UFO!) -------------------------

reimport: build/reference/TheanoDidot-Regular.otf
	@test "$(FORCE)" = 1 || { echo "reimport overwrites $(UFOS); run 'make reimport FORCE=1'"; exit 1; }
	fontforge -quiet -lang=py -script scripts/sfd_export.py $(UPSTREAM) build/import
	$(PY) scripts/postprocess_import.py build/import $< $(UFOS)
	.venv/bin/ufonormalizer -m $(UFOS)

clean:
	rm -rf build fonts
