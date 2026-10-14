PY       := .venv/bin/python -I
FONTMAKE := .venv/bin/fontmake
FAMILY   := MyiaDidot
UPSTREAM := sources/upstream/TheanoDidot-Regular.sfd
UFOS     := sources/$(FAMILY)-Regular.ufo

OTF   := $(patsubst sources/%.ufo,fonts/otf/%.otf,$(UFOS))
TTF   := $(patsubst sources/%.ufo,fonts/ttf/%.ttf,$(UFOS))
WOFF2 := $(patsubst sources/%.ufo,fonts/webfonts/%.woff2,$(UFOS))

# Rebuild when any file inside the UFO changes.
.SECONDEXPANSION:
UFO_FILES = $$(shell find sources/$$*.ufo -type f)
.SECONDARY:

.PHONY: all fonts otf ttf webfonts compare regress qa proof normalize reimport clean

all: fonts

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
	cd build/proofs && lualatex -interaction=nonstopmode charset.tex >/dev/null
	cd proofs && lualatex -interaction=nonstopmode --output-directory=../build/proofs proof.tex >/dev/null
	@echo "proofs: build/proofs/charset.pdf build/proofs/proof.pdf"

# --- QA ------------------------------------------------------------------

qa: $(OTF) $(TTF)
	@mkdir -p build/qa
	for fmt in otf ttf; do \
	    .venv/bin/fontbakery check-universal --html build/qa/fontbakery-$$fmt.html \
	        --ghmarkdown build/qa/fontbakery-$$fmt.md fonts/$$fmt/*.$$fmt || true; \
	done
	@echo "reports: build/qa/fontbakery-{otf,ttf}.html"

normalize:
	.venv/bin/ufonormalizer -m $(UFOS)

# --- one-off import (overwrites the source UFO!) -------------------------

reimport: build/reference/TheanoDidot-Regular.otf
	@test "$(FORCE)" = 1 || { echo "reimport overwrites $(UFOS); run 'make reimport FORCE=1'"; exit 1; }
	fontforge -quiet -lang=py -script scripts/sfd_export.py $(UPSTREAM) build/import
	$(PY) scripts/postprocess_import.py build/import $< $(UFOS)
	.venv/bin/ufonormalizer -m $(UFOS)

clean:
	rm -rf build fonts
