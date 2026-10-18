PY       := .venv/bin/python -I
FONTMAKE := .venv/bin/fontmake
FAMILY   := MyiaDidot
UPSTREAM := sources/upstream/TheanoDidot-Regular.sfd
UFOS     := sources/$(FAMILY)-Regular.ufo sources/$(FAMILY)-Bold.ufo sources/$(FAMILY)-Italic.ufo sources/$(FAMILY)-BoldItalic.ufo

OTF   := $(patsubst sources/%.ufo,fonts/otf/%.otf,$(UFOS))
TTF   := $(patsubst sources/%.ufo,fonts/ttf/%.ttf,$(UFOS))
WOFF2 := $(patsubst sources/%.ufo,fonts/webfonts/%.woff2,$(UFOS))

# Rebuild when any file inside the UFO changes.
.SECONDEXPANSION:
UFO_FILES = $$(shell find sources/$$*.ufo -type f)
.SECONDARY:

.PHONY: all setup test test-data fonts otf ttf webfonts compare regress qa quality pairs proof proof-svg udhr normalize winmetrics reimport clean reproduce strokes kerntouch generate

all: fonts

setup:
	uv sync
	git config core.hooksPath tools/git-hooks
	@echo "pre-commit hook installed (tools/git-hooks/pre-commit)"

test:
	.venv/bin/pytest

# Accept the current behaviour as the new baseline (review git diff tests/data!):
# run once, read the strings that differ from HEAD, then again with N=that many
test-data:
	$(PY) scripts/update_test_data.py --golden --digest --cmap $(if $(N),--expect-changes $(N))

winmetrics:
	$(PY) scripts/set_win_metrics.py $(UFOS)

fonts: otf ttf webfonts
otf: $(OTF)
ttf: $(TTF)
webfonts: $(WOFF2)

fonts/otf/%.otf: sources/%.ufo $(UFO_FILES) scripts/add_stat.py
	$(FONTMAKE) -u $< -o otf --output-path $@
	$(PY) scripts/add_stat.py $@

# Unhinted TTF in build/, then ttfautohint into fonts/ttf.
build/unhinted/%.ttf: sources/%.ufo $(UFO_FILES)
	$(FONTMAKE) -u $< -o ttf --flatten-components --output-path $@

fonts/ttf/%.ttf: build/unhinted/%.ttf scripts/add_stat.py
	@mkdir -p $(dir $@)
	ttfautohint --no-info --stem-width-mode=nss --windows-compatibility $< $@
	$(PY) scripts/add_stat.py $@

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
	for s in Italic Bold BoldItalic; do \
	    $(PY) scripts/charset_proof.py fonts/otf/$(FAMILY)-$$s.otf build/proofs/charset-$$s.tex || exit 1; \
	done
	$(PY) scripts/smallcap_review.py sources/$(FAMILY)-Regular.ufo fonts/otf/$(FAMILY)-Regular.otf build/proofs/smallcaps-review.tex \
	    --drafts build/proofs/drafts-review.tex
	$(PY) scripts/smallcap_review.py sources/$(FAMILY)-Italic.ufo fonts/otf/$(FAMILY)-Italic.otf build/proofs/smallcaps-review-Italic.tex \
	    --drafts build/proofs/drafts-review-Italic.tex
	cd build/proofs && for t in charset charset-Italic charset-Bold charset-BoldItalic smallcaps-review drafts-review smallcaps-review-Italic drafts-review-Italic; do \
	    lualatex -interaction=nonstopmode $$t.tex >/dev/null; done
	cd proofs && for t in proof smallcaps samples textpages; do \
	    lualatex -interaction=nonstopmode --output-directory=../build/proofs $$t.tex >/dev/null; done
	@echo "proofs: build/proofs/{charset,charset-Italic,charset-Bold,charset-BoldItalic,proof,samples,textpages,smallcaps,smallcaps-review,drafts-review}.pdf, *-review-Italic.pdf"

proof-svg: $(OTF)
	$(PY) scripts/proof_svg.py $(OTF) --out build/proofs/ci

# One quarto page per language, the UDHR (texts fetched once into build/udhr)
udhr: $(OTF)
	@mkdir -p build/proofs
	$(PY) scripts/udhr_book.py fonts/otf build/proofs/udhr-quarto.tex --cache build/udhr
	cd build/proofs && lualatex -interaction=nonstopmode udhr-quarto.tex >/dev/null
	@echo "proof: build/proofs/udhr-quarto.pdf"

# --- QA ------------------------------------------------------------------

qa: $(OTF) $(TTF)
	@mkdir -p build/qa
	set -u; qa_failed=0; for fmt in otf ttf; do \
	    .venv/bin/fontbakery check-universal -x fontdata_namecheck -x fontbakery_version \
	        --html build/qa/fontbakery-$$fmt.html \
	        --ghmarkdown build/qa/fontbakery-$$fmt.md fonts/$$fmt/*.$$fmt || qa_failed=1; \
	done; exit $$qa_failed
	@echo "reports: build/qa/fontbakery-{otf,ttf}.html"

# Design quality measured against reference fonts (scripts/quality/; the
# references fetched once into build/refs): colour, spacing, pairs,
# alignment, construction, transitions, accents, slant, small sizes
QPY := $(PY) scripts/quality
quality: $(OTF) $(TTF)
	@mkdir -p build/quality
	$(QPY)/fetch_refs.py
	for s in Regular Italic Bold BoldItalic; do \
	    $(QPY)/colour.py $$s > build/quality/colour-$$s.txt; \
	    $(QPY)/evenness.py $$s > build/quality/evenness-$$s.txt; \
	    $(QPY)/transitions.py $$s > build/quality/transitions-$$s.txt; \
	    $(QPY)/pairs.py $$s > build/quality/pairs-$$s.txt; \
	    $(QPY)/zones.py sources/$(FAMILY)-$$s.ufo > build/quality/zones-$$s.txt; \
	    $(QPY)/outlines.py sources/$(FAMILY)-$$s.ufo > build/quality/outlines-$$s.txt; \
	    $(QPY)/accents.py sources/$(FAMILY)-$$s.ufo > build/quality/accents-$$s.txt; \
	done
	$(QPY)/slant.py sources/$(FAMILY)-Italic.ufo 15.2 > build/quality/slant-Italic.txt
	$(QPY)/cases.py > build/quality/cases.txt
	$(QPY)/smallsize.py fonts/ttf/*.ttf > build/quality/smallsize.txt
	@echo "reports: build/quality/*.txt"

# kerning that brings inks together, drawn for review (scripts/quality/kern_touch.py)
kerntouch:
	@mkdir -p build/quality
	for s in Regular Italic Bold BoldItalic; do \
	    $(PY) scripts/quality/kern_touch.py sources/$(FAMILY)-$$s.ufo --sheet build/quality/kern-touch-$$s.pdf > build/quality/kern-touch-$$s.txt || exit 1; \
	done
	@echo "sheets: build/quality/kern-touch-*.pdf"

# glyphs darker or lighter than their kind, drawn for review (scripts/quality/strokes.py)
strokes:
	@mkdir -p build/quality
	for s in Regular Italic Bold BoldItalic; do \
	    $(PY) scripts/quality/strokes.py sources/$(FAMILY)-$$s.ufo --sheet build/quality/strokes-$$s.pdf > build/quality/strokes-$$s.txt || exit 1; \
	done

# regenerate the Italic, Bold and Bold Italic from the Regular, in order, then
# normalize and look for files the sync client renamed ("conflicted")
generate:
	$(PY) scripts/make_italic.py
	$(PY) scripts/make_bold.py
	$(PY) scripts/smallcaps.py sources/$(FAMILY)-Bold.ufo
	$(PY) scripts/make_bold.py sources/$(FAMILY)-Italic.ufo sources/$(FAMILY)-BoldItalic.ufo
	$(PY) scripts/smallcaps.py sources/$(FAMILY)-BoldItalic.ufo
	$(MAKE) normalize
	@if find sources -iname '*conflict*' | grep -q .; then \
	    echo "sync conflicts in sources/:"; find sources -iname '*conflict*'; exit 1; fi

# the generated styles as their generators make them (scripts/check_reproducible.py)
reproduce:
	$(PY) scripts/check_reproducible.py

pairs: $(OTF)
	@mkdir -p build/quality
	$(PY) scripts/quality/fetch_refs.py
	for s in Regular Italic Bold BoldItalic; do \
	    $(PY) scripts/quality/pairs.py $$s > build/quality/pairs-$$s.txt || exit 1; \
	done
	@echo "reports: build/quality/pairs-*.txt"

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
