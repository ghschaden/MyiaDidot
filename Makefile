SHELL := /bin/sh
.SHELLFLAGS := -eu -c
.DELETE_ON_ERROR:

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

.PHONY: all setup oldstand test lint test-data fonts otf ttf webfonts release compare regress qa quality pairs proof proof-svg udhr normalize winmetrics reimport clean reproduce strokes kerntouch generate visual visual-approve diffenator

all: fonts

setup:
	uv sync
	git config core.hooksPath tools/git-hooks
	@echo "git hooks installed (tools/git-hooks: pre-commit runs the tests, post-commit rebuilds the proofs)"

# one test or validation run at a time across all working copies
# (worktrees), at most JOBS cores each (review: 4, 2026-11-03)
JOBS ?= 4
export MYIA_JOBS = $(JOBS)
VALIDATE_LOCK = $(shell cd "$$(git rev-parse --git-common-dir)" && pwd)/myia-validate.lock

test:
	flock $(VALIDATE_LOCK) .venv/bin/pytest -n $(JOBS)

# ruff, lint only (no formatter: the recipe tables are aligned by hand)
lint:
	.venv/bin/ruff check .

# Accept the current behaviour as the new baseline (review git diff tests/data!):
# run once, review build/baseline-review.json, then rerun with ACCEPT=its digest
test-data:
	$(PY) scripts/update_test_data.py --golden --digest --cmap $(if $(N),--expect-changes $(N)) $(if $(ACCEPT),--accept-report $(ACCEPT))

winmetrics:
	$(PY) scripts/set_win_metrics.py $(UFOS)

fonts: otf ttf webfonts
otf: $(OTF)
ttf: $(TTF)
webfonts: $(WOFF2)

# The release archive, prepared only: build/release/MyiaDidot-VERSION.zip
# (fonts, OFL, FONTLOG, install notes, specimen once `make proof` has run,
# checksums); every style must state the same version
release: fonts
	$(PY) scripts/release.py

# PostScript hints: zones and stems measured per style, then otfautohint.
fonts/otf/%.otf: sources/%.ufo $(UFO_FILES) scripts/add_stat.py scripts/ps_hints.py scripts/build_font.py scripts/build_support.py uv.lock
	$(PY) scripts/build_font.py otf $< $@

# Unhinted TTF in build/, then ttfautohint (with a control file made for the
# font, kept in build/hinting/) into fonts/ttf.
build/unhinted/%.ttf: sources/%.ufo $(UFO_FILES) scripts/build_font.py scripts/build_support.py uv.lock
	$(PY) scripts/build_font.py unhinted $< $@

fonts/ttf/%.ttf: build/unhinted/%.ttf scripts/add_stat.py scripts/hint_control.py scripts/quality/hint_zones.py scripts/build_font.py scripts/build_support.py uv.lock
	$(PY) scripts/build_font.py ttf $< $@

fonts/webfonts/%.woff2: fonts/ttf/%.ttf scripts/build_font.py scripts/build_support.py uv.lock
	$(PY) scripts/build_font.py woff2 $< $@

# --- upstream round-trip check -------------------------------------------
# Builds Theano Didot straight from the pinned SFD with FontForge and
# compares HarfBuzz shaping against our build (without production names).

build/reference/TheanoDidot-Regular.otf: $(UPSTREAM) scripts/sfd_reference.py scripts/build_reference.py scripts/build_support.py
	$(PY) scripts/build_reference.py $< build/reference

build/compare/%.otf: sources/%.ufo $(UFO_FILES) scripts/build_font.py scripts/build_support.py uv.lock
	$(PY) scripts/build_font.py compare $< $@

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

proof:
	@mkdir -p build
	flock build/proofs.lock $(MAKE) _proof

.PHONY: _proof
_proof: $(OTF) build/reference/TheanoDidot-Regular.otf
	@mkdir -p build/proofs
	$(PY) scripts/charset_proof.py fonts/otf/$(FAMILY)-Regular.otf build/proofs/charset.tex \
	    --baseline build/reference/TheanoDidot-Regular.otf
	for s in Italic Bold BoldItalic; do \
	    $(PY) scripts/charset_proof.py fonts/otf/$(FAMILY)-$$s.otf build/proofs/charset-$$s.tex || exit 1; \
	done
	$(PY) scripts/smallcap_review.py sources/$(FAMILY)-Regular.ufo fonts/otf/$(FAMILY)-Regular.otf build/proofs/smallcaps-review.tex \
	    --drafts build/proofs/drafts-review.tex
	for s in Italic Bold BoldItalic; do \
	    $(PY) scripts/smallcap_review.py sources/$(FAMILY)-$$s.ufo fonts/otf/$(FAMILY)-$$s.otf build/proofs/smallcaps-review-$$s.tex \
	        --drafts build/proofs/drafts-review-$$s.tex || exit 1; \
	done
	cd build/proofs && for t in charset charset-Italic charset-Bold charset-BoldItalic smallcaps-review drafts-review \
	    smallcaps-review-Italic drafts-review-Italic smallcaps-review-Bold drafts-review-Bold \
	    smallcaps-review-BoldItalic drafts-review-BoldItalic; do \
	    lualatex -halt-on-error -interaction=nonstopmode $$t.tex >/dev/null; done
	cd proofs && for t in proof smallcaps samples textpages; do \
	    lualatex -halt-on-error -interaction=nonstopmode --output-directory=../build/proofs $$t.tex >/dev/null; done
	@echo "proofs: build/proofs/{charset,charset-Italic,charset-Bold,charset-BoldItalic,proof,samples,textpages,smallcaps,smallcaps-review,drafts-review}.pdf, *-review-{Italic,Bold,BoldItalic}.pdf"

proof-svg: $(OTF)
	$(PY) scripts/proof_svg.py $(OTF) --out build/proofs/ci

# Rendered specimens against an approved build: the tag proofs-approved
# (`make visual-approve` sets it to HEAD), else HEAD; VISUAL_REF=rev for
# another. Baseline fonts are built once per revision into build/visual/.
VISUAL_STYLES := Regular Italic Bold BoldItalic
VISUAL_REF ?= $(shell git rev-parse -q --verify refs/tags/proofs-approved >/dev/null && echo proofs-approved || echo HEAD)
VISUAL_BASE = build/visual/base-$(shell git rev-parse --short $(VISUAL_REF))

$(VISUAL_BASE)/done:
	rm -rf $(VISUAL_BASE) && mkdir -p $(VISUAL_BASE)
	git archive $(VISUAL_REF) sources | tar -x -C $(VISUAL_BASE)
	for s in $(VISUAL_STYLES); do \
	    $(FONTMAKE) -u $(VISUAL_BASE)/sources/$(FAMILY)-$$s.ufo -o otf \
	        --output-path $(VISUAL_BASE)/$(FAMILY)-$$s.otf || exit 1; \
	done
	for s in $(VISUAL_STYLES); do test -f $(VISUAL_BASE)/$(FAMILY)-$$s.otf || exit 1; done
	rm -rf $(VISUAL_BASE)/sources && touch $@

visual: $(OTF) $(VISUAL_BASE)/done
	$(PY) scripts/visual_diff.py $(VISUAL_BASE) fonts/otf --out build/visual/report \
	    --label-before "$(VISUAL_REF) ($(shell git rev-parse --short $(VISUAL_REF)))"

# diffenator2 (glyphs, words of its wordlists per script, tables) on
# unhinted TTFs, the same baseline revision: build/visual/diffenator/
$(VISUAL_BASE)/ttf-done: $(VISUAL_BASE)/done
	git archive $(VISUAL_REF) sources | tar -x -C $(VISUAL_BASE)
	for s in $(VISUAL_STYLES); do \
	    $(FONTMAKE) -u $(VISUAL_BASE)/sources/$(FAMILY)-$$s.ufo -o ttf --flatten-components \
	        --output-path $(VISUAL_BASE)/$(FAMILY)-$$s.ttf || exit 1; \
	done
	for s in $(VISUAL_STYLES); do test -f $(VISUAL_BASE)/$(FAMILY)-$$s.ttf || exit 1; done
	rm -rf $(VISUAL_BASE)/sources && touch $@

diffenator: $(patsubst sources/%.ufo,build/unhinted/%.ttf,$(UFOS)) $(VISUAL_BASE)/ttf-done
	rm -rf build/visual/diffenator && mkdir -p build/visual/diffenator
	# from build/visual: diffenator2 leaves build.ninja and .ninja_log where it runs
	cd build/visual && for s in $(VISUAL_STYLES); do \
	    PATH=$(CURDIR)/.venv/bin:$$PATH $(CURDIR)/.venv/bin/diffenator2 diff --no-diffbrowsers \
	        -fb $(CURDIR)/$(VISUAL_BASE)/$(FAMILY)-$$s.ttf -fa $(CURDIR)/build/unhinted/$(FAMILY)-$$s.ttf \
	        -o diffenator/$$s >diffenator-$$s.log 2>&1 || exit 1; \
	done
	$(PY) scripts/quality/diffenator_summary.py build/visual/diffenator | tee build/visual/diffenator-summary.txt
	@echo "summary: build/visual/diffenator-summary.txt; reports: build/visual/diffenator/STYLE/diffenator2-report.html"

visual-approve:
	git tag -f proofs-approved HEAD

# One quarto page per language, the UDHR (texts fetched once into build/udhr)
udhr: $(OTF)
	@mkdir -p build/proofs
	$(PY) scripts/udhr_book.py fonts/otf build/proofs/udhr-quarto.tex --cache build/udhr
	cd build/proofs && lualatex -halt-on-error -interaction=nonstopmode udhr-quarto.tex >/dev/null
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
# the Italic and the Bold side by side (both read only the Regular, a core
# each; the Italic's report after the Bold's), then the Bold Italic
generate:
	@mkdir -p build
	$(PY) scripts/make_italic.py > build/make-italic.log 2>&1 & italic=$$!; \
	$(PY) scripts/make_bold.py && $(PY) scripts/smallcaps.py sources/$(FAMILY)-Bold.ufo; bold=$$?; \
	wait $$italic; status=$$?; cat build/make-italic.log; \
	[ $$status -eq 0 ] || { echo "make_italic.py failed"; exit 1; }; [ $$bold -eq 0 ]
	$(PY) scripts/make_bold.py sources/$(FAMILY)-Italic.ufo sources/$(FAMILY)-BoldItalic.ufo
	$(PY) scripts/smallcaps.py sources/$(FAMILY)-BoldItalic.ufo
	$(MAKE) normalize
	@if find sources -iname '*conflict*' | grep -q .; then \
	    echo "sync conflicts in sources/:"; find sources -iname '*conflict*'; exit 1; fi

# Old Standard's SFD converted again with FontForge (scripts/fontforge_inputs.py)
oldstand:
	$(PY) -c "import sys; sys.path.insert(0, 'scripts'); import fontforge_inputs; fontforge_inputs.convert_source()"

# the generated styles as their generators make them (scripts/check_reproducible.py)
reproduce:
	flock $(VALIDATE_LOCK) $(PY) scripts/check_reproducible.py

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
	for u in $(UFOS); do .venv/bin/ufonormalizer -m $$u; done

clean:
	rm -rf build fonts
