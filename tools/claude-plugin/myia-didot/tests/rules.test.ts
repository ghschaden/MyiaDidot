import { describe, expect, test } from 'claude-code/testing'

import { judgeBash, judgePath } from '../hooks/rules'

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

  test('leaves the master sources and everything else alone', async () => {
    expect(judgePath(`${ROOT}/sources/MyiaDidot-Regular.ufo/features.fea`, ROOT)).toBeUndefined()
    expect(judgePath(`${ROOT}/scripts/composites.py`, ROOT)).toBeUndefined()
    expect(judgePath('/elsewhere/sources/upstream/x', ROOT)).toBeUndefined()
  })
})
