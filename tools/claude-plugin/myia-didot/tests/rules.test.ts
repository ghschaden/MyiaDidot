import { describe, expect, test } from 'claude-code/testing'

import { judgeBash, judgePath, measuresBuiltFonts, staleNote, staleStyles, syncNote, writesGenerated, writesUfos } from '../hooks/rules'

const ROOT = '/home/u/src/MyiaDidot'

describe('judgeBash', () => {
  test('denies re-importing over the master UFO', async () => {
    for (const cmd of ['make reimport FORCE=1', 'make  reimport', 'cd x && make -C . reimport FORCE=1',
      'python scripts/postprocess_import.py build/import a.otf b.ufo',
      'fontforge -script scripts/sfd_export.py x y']) {
      expect(judgeBash(cmd)?.decision).toBe('deny')
    }
  })

  test('denies writing into sources/upstream', async () => {
    for (const cmd of ['sed -i s/a/b/ sources/upstream/OFL.txt', 'rm sources/upstream/Theano.cfg',
      'echo x > sources/upstream/FONTLOG.txt', 'cp a.sfd sources/upstream/', 'git rm -r sources/upstream']) {
      expect(judgeBash(cmd)?.decision).toBe('deny')
    }
  })

  test('lets reading sources/upstream through', async () => {
    for (const cmd of ['grep -n Kern sources/upstream/TheanoDidot-Regular.sfd', 'sed -n 1,5p sources/upstream/OFL.txt',
      'head sources/upstream/FONTLOG.txt | wc -l', 'git diff sources/upstream']) {
      expect(judgeBash(cmd)).toBeUndefined()
    }
  })

  test('asks before rewriting test baselines, skipping hooks or force-pushing', async () => {
    for (const cmd of ['.venv/bin/python -I scripts/update_test_data.py --golden', 'make test-data',
      'git commit --no-verify -m x', 'git commit -nm x', 'git push --force', 'git push -f origin main']) {
      expect(judgeBash(cmd)?.decision).toBe('ask')
    }
  })

  test('leaves ordinary work alone', async () => {
    for (const cmd of ['make fonts', 'make test', 'git commit -m "add ogonek anchors"', 'git push',
      '.venv/bin/pytest -q', 'make regress', 'git commit -m "fix -n handling"']) {
      expect(judgeBash(cmd)).toBeUndefined()
    }
  })
})

describe('judgePath', () => {
  test('denies edits under sources/upstream and asks for tests/data', async () => {
    expect(judgePath(`${ROOT}/sources/upstream/OFL.txt`, ROOT)?.decision).toBe('deny')
    expect(judgePath(`${ROOT}/tests/data/nfd-exceptions.txt`, ROOT)?.decision).toBe('ask')
  })

  test('asks before editing a generated style', async () => {
    for (const style of ['Italic', 'Bold', 'BoldItalic']) {
      expect(judgePath(`${ROOT}/sources/MyiaDidot-${style}.ufo/kerning.plist`, ROOT)?.decision).toBe('ask')
      expect(judgePath(`${ROOT}/sources/MyiaDidot-${style}.ufo/glyphs/a.glif`, ROOT)?.decision).toBe('ask')
    }
  })

  test('leaves the master sources and everything else alone', async () => {
    expect(judgePath(`${ROOT}/sources/MyiaDidot-Regular.ufo/features.fea`, ROOT)).toBeUndefined()
    expect(judgePath(`${ROOT}/scripts/composites.py`, ROOT)).toBeUndefined()
    expect(judgePath('/elsewhere/sources/upstream/x', ROOT)).toBeUndefined()
  })
})

describe('writesGenerated', () => {
  test('asks for writes into a generated style other than by its generator', async () => {
    for (const cmd of [
      '.venv/bin/python -I scripts/kern_clear.py sources/MyiaDidot-Bold.ufo',
      'python scripts/composites.py sources/MyiaDidot-Italic.ufo --rebuild-stacked',
      'python scripts/glyph_lint.py sources/MyiaDidot-BoldItalic.ufo --fix',
      'python scripts/built_from.py sources/MyiaDidot-Bold.ufo a --accept',
      "sed -i 's/a/b/' sources/MyiaDidot-Italic.ufo/features.fea",
      'rm sources/MyiaDidot-Bold.ufo/glyphs/a.glif',
      'cp /tmp/a.glif sources/MyiaDidot-Bold.ufo/glyphs/a.glif',
      'echo x >> sources/MyiaDidot-Italic.ufo/features.fea',
      '.venv/bin/python -I - <<\'EOF\'\nimport ufoLib2\nf = ufoLib2.Font.open("sources/MyiaDidot-Bold.ufo")\nf.kerning[("a", "b")] = -10\nf.save()\nEOF',
      'python - <<EOF\nfor s in ["Regular", "Bold"]:\n    f = ufoLib2.Font.open(f"sources/MyiaDidot-{s}.ufo")\n    f.save()\nEOF',
    ]) {
      expect(writesGenerated(cmd)).toBe(true)
      expect(judgeBash(cmd)?.decision).toBe('ask')
    }
  })

  test('lets the generators, checks, reads and the Regular through', async () => {
    for (const cmd of [
      'make generate', 'make reproduce', 'make normalize',
      '.venv/bin/python -I scripts/make_bold.py sources/MyiaDidot-Italic.ufo sources/MyiaDidot-BoldItalic.ufo',
      '.venv/bin/python -I scripts/smallcaps.py sources/MyiaDidot-Bold.ufo',
      'python scripts/composites.py sources/MyiaDidot-Italic.ufo --check',
      'python scripts/kern_clear.py sources/MyiaDidot-Bold.ufo --dry-run',
      'python scripts/glyph_lint.py sources/MyiaDidot-Bold.ufo > /tmp/lint.txt 2>&1',
      'cp -r sources/MyiaDidot-Bold.ufo /tmp/scratch/Bold.ufo',
      'git checkout sources/MyiaDidot-Italic.ufo', 'git diff sources/MyiaDidot-Bold.ufo/kerning.plist',
      'python scripts/kern_clear.py sources/MyiaDidot-Regular.ufo',
      'python - <<EOF\nf = ufoLib2.Font.open("sources/MyiaDidot-Regular.ufo")\nf.save()\nEOF',
    ]) {
      expect(writesGenerated(cmd)).toBe(false)
    }
  })
})

describe('stale fonts', () => {
  test('knows the scripts that measure fonts/otf/', async () => {
    for (const cmd of ['.venv/bin/python -I scripts/quality/greek_pairs.py Bold --script cyrillic',
      'python scripts/quality/pairs.py', 'python scripts/feature_audit.py', 'python scripts/quality/colour.py Regular']) {
      expect(measuresBuiltFonts(cmd)).toBe(true)
    }
    for (const cmd of ['python scripts/glyph_lint.py sources/MyiaDidot-Bold.ufo', 'python scripts/quality/strokes.py',
      'python scripts/quality/kern_coverage.py sources/MyiaDidot-Regular.ufo', 'make pairs']) {
      expect(measuresBuiltFonts(cmd)).toBe(false)
    }
  })

  test('reads the check and words the note', async () => {
    expect(staleStyles('Bold\nBoldItalic\n')).toEqual(['Bold', 'BoldItalic'])
    expect(staleStyles('find: warning\n')).toEqual([])
    expect(staleNote([])).toBeUndefined()
    expect(staleNote(['Italic'])?.status).toBe('OTF stale: Italic (make otf)')
  })
})

describe('sync leftovers', () => {
  test('knows the commands that rewrite UFOs in bulk', async () => {
    for (const cmd of ['make generate', 'make normalize', 'make -C . generate > log 2>&1',
      '.venv/bin/python -I scripts/make_bold.py', 'python scripts/smallcaps.py sources/MyiaDidot-Regular.ufo',
      'python scripts/composites.py sources/MyiaDidot-Regular.ufo --stack-anchors',
      'python - <<EOF\nf = ufoLib2.Font.open(p)\nf.save()\nEOF']) {
      expect(writesUfos(cmd)).toBe(true)
    }
    for (const cmd of ['make test', 'make otf', 'git status', 'python scripts/quality/pairs.py Bold', 'make reproduce']) {
      expect(writesUfos(cmd)).toBe(false)
    }
  })

  test('words the toast and the note from sync_check.py', async () => {
    expect(syncNote('')).toBeUndefined()
    expect(syncNote('\n')).toBeUndefined()
    const note = syncNote('MyiaDidot-Bold.ufo/glyphs/a (conflicted).glif: sync conflict copy\n' +
      'MyiaDidot-Bold.ufo/glyphs/b.glif: listed for b, missing\nMyiaDidot-Italic.ufo/glyphs/c.glif: not listed\n')
    expect(note?.toast).toBe('Sync leftovers in MyiaDidot-Bold.ufo, MyiaDidot-Italic.ufo: 3 (scripts/sync_check.py)')
    expect(note?.context).toContain('b.glif: listed for b, missing')
  })
})
