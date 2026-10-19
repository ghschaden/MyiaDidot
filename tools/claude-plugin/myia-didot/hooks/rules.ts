// Pure decision rules for the guards, kept apart so tests can call them.

export type Verdict = { decision: 'deny' | 'ask'; reason: string }

const PREFIX = 'myia-didot'

// The styles made by make_bold.py / make_italic.py from the Regular.
const GENERATED_UFO = String.raw`MyiaDidot-(?:Italic|Bold|BoldItalic)\.ufo`
const GENERATED = new RegExp(String.raw`\b${GENERATED_UFO}`)
const GENERATED_REASON = `${PREFIX}: the Italic, Bold and Bold Italic UFOs are generated (make_italic.py, make_bold.py): ` +
  'an edit made in them alone is undone by the next run and fails make reproduce. Change the Regular or the ' +
  'generator (a recipe, a constant) instead; a hand-drawn Italic glyph is kept when marked "drawn".'
// Scripts that change the UFO they are given (their check modes excepted).
const MUTATORS = /\b(kern_clear|composites|derive|respace|adjust_accents|kern_groups|cpsp|space_figures|case_forms|nfd_compose|draft_\w+|smallcaps_draft|set_win_metrics)\.py\b/
const CHECK_ONLY = /\s--(check|dry-run)\b/

/** Whether a shell command writes into a generated style's UFO by any way
 * but its generator (make_bold.py, make_italic.py, smallcaps.py on it). */
export function writesGenerated(command: string): boolean {
  // inline Python saving a font, with a generated style named in it (also
  // through a loop over the styles: f"MyiaDidot-{style}.ufo")
  if (/\.save\(/.test(command) && (GENERATED.test(command) ||
    (/MyiaDidot-\{[^}]*\}\.ufo/.test(command) && /["'](?:Italic|Bold|BoldItalic)["']/.test(command)))) {
    return true
  }
  for (const part of command.split(/\n|;|&&|\|\||\|/)) {
    const seg = part.trim()
    if (!GENERATED.test(seg)) continue
    if (MUTATORS.test(seg) && !CHECK_ONLY.test(seg)) return true
    if (/\bglyph_lint\.py\b/.test(seg) && /\s--fix\b/.test(seg)) return true
    if (/\bbuilt_from\.py\b/.test(seg) && /\s--accept\b/.test(seg)) return true
    if (/\bsed\b[^|;&]*\s-i/.test(seg) || /^(?:\S+=\S+\s+)*(rm|tee|truncate)\b/.test(seg)) return true
    if (new RegExp(String.raw`>{1,2}\s*\S*${GENERATED_UFO}`).test(seg)) return true
    const words = seg.split(/\s+/)
    if (/^(cp|mv|rsync)$/.test(words[0] ?? '') && GENERATED.test(words[words.length - 1] ?? '')) return true
  }
  return false
}

// Scripts that measure the built fonts in fonts/otf/ rather than the UFOs.
const MEASURES_BUILT = /\b(greek_pairs|capsc_pairs|pairs|cases|colour|evenness|transitions|feature_audit|proof_svg)\.py\b/

/** Whether a shell command runs a script that reads fonts/otf/. */
export function measuresBuiltFonts(command: string): boolean {
  return MEASURES_BUILT.test(command)
}

/** The styles whose OTF is older than its UFO, from `staleCheck`'s output. */
export function staleStyles(output: string): string[] {
  return output.split('\n').map(l => l.trim()).filter(l => /^(Regular|Italic|Bold|BoldItalic)$/.test(l))
}

/** A shell script printing each style whose fonts/otf/ OTF is missing or
 * older than some file in its UFO. */
export const STALE_CHECK = 'for s in Regular Italic Bold BoldItalic; do o=fonts/otf/MyiaDidot-$s.otf; ' +
  'if [ ! -e "$o" ] || [ -n "$(find sources/MyiaDidot-$s.ufo -newer "$o" -print -quit)" ]; then echo $s; fi; done'

/** The status-line suffix and the note for a measurement, or undefined. */
export function staleNote(styles: string[]): { status: string; context: string } | undefined {
  if (styles.length === 0) return undefined
  return {
    status: `OTF stale: ${styles.join(' ')} (make otf)`,
    context: `${PREFIX}: fonts/otf/ is older than the UFO for ${styles.join(', ')}; this script measured the ` +
      'built fonts, so its results for those styles describe the sources before the latest changes. Run make otf ' +
      'and measure again before relying on them.',
  }
}

/** Verdict for a shell command, or undefined to leave it to the session. */
export function judgeBash(command: string): Verdict | undefined {
  const c = command.replace(/\s+/g, ' ')
  // Flags are read with quoted arguments (commit messages, ...) blanked out.
  const flags = c.replace(/'[^']*'|"(?:[^"\\]|\\.)*"/g, "''")

  if (/\bmake\b[^;&|]*\breimport\b/.test(c) || /\b(postprocess_import|sfd_export)\.py\b/.test(c)) {
    return {
      decision: 'deny',
      reason: `${PREFIX}: re-importing from the upstream SFD overwrites the master UFO and every edit since. Only the person runs that, themselves.`,
    }
  }
  if (/\bsources\/upstream\b/.test(c) && /(\bsed\b[^|;&]*\s-i|\brm\b|\bmv\b|\bcp\b|\btee\b|>{1,2}|\btruncate\b|\bgit (rm|mv|checkout)\b)/.test(c)) {
    return {
      decision: 'deny',
      reason: `${PREFIX}: sources/upstream/ is the pinned upstream Theano source and stays read-only.`,
    }
  }
  if (writesGenerated(command)) {
    return { decision: 'ask', reason: GENERATED_REASON }
  }
  if (/\bupdate_test_data\.py\b/.test(c) || /\bmake\b[^;&|]*\btest-data\b/.test(c)) {
    return {
      decision: 'ask',
      reason: `${PREFIX}: this rewrites the test baselines (tests/data/), accepting the font's current behaviour as correct.`,
    }
  }
  if (/\bgit\b[^;&|]*\bcommit\b[^;&|]*(--no-verify|\s-[a-zA-Z]*n[a-zA-Z]*\b)/.test(flags)) {
    return {
      decision: 'ask',
      reason: `${PREFIX}: this commit skips the pre-commit test suite.`,
    }
  }
  if (/\bgit\b[^;&|]*\bpush\b[^;&|]*(--force\b|--force-with-lease\b|\s-f\b)/.test(flags)) {
    return { decision: 'ask', reason: `${PREFIX}: force-push rewrites the shared history.` }
  }
  return undefined
}

/** Verdict for a file edit, or undefined to leave it to the session. */
export function judgePath(path: string, root: string): Verdict | undefined {
  if (path.startsWith(`${root}/sources/upstream/`)) {
    return {
      decision: 'deny',
      reason: `${PREFIX}: sources/upstream/ is the pinned upstream Theano source and stays read-only.`,
    }
  }
  if (path.startsWith(`${root}/sources/`) && GENERATED.test(path.slice(root.length))) {
    return { decision: 'ask', reason: GENERATED_REASON }
  }
  if (path.startsWith(`${root}/tests/data/`)) {
    return {
      decision: 'ask',
      reason: `${PREFIX}: tests/data/ holds the regression baselines; editing them changes what counts as correct.`,
    }
  }
  return undefined
}

// Commands that rewrite many UFO files at once, after which the file sync
// can leave "(conflicted)" copies or lose a glyph file.
const WRITES_UFOS = /\bmake\b[^;&|\n]*\b(generate|normalize)\b|\b(make_bold|make_italic|smallcaps|kern_clear|composites|derive|respace|adjust_accents|kern_groups|cpsp|space_figures|case_forms|nfd_compose|draft_\w+|smallcaps_draft|glyph_lint|ufonormalizer)(\.py)?\b|\.save\(/

/** Whether a shell command may have rewritten UFO files in bulk. */
export function writesUfos(command: string): boolean {
  return WRITES_UFOS.test(command)
}

/** The toast and the note for scripts/sync_check.py's output, or undefined. */
export function syncNote(output: string): { toast: string; context: string } | undefined {
  const lines = output.split('\n').map(l => l.trim()).filter(Boolean)
  if (lines.length === 0) return undefined
  const ufos = [...new Set(lines.map(l => l.split('/')[0]))]
  return {
    toast: `Sync leftovers in ${ufos.join(', ')}: ${lines.length} (scripts/sync_check.py)`,
    context: `${PREFIX}: the file sync left these in sources/ (scripts/sync_check.py): ${lines.slice(0, 20).join('; ')}` +
      `${lines.length > 20 ? ` ... and ${lines.length - 20} more` : ''}. Delete the "(conflicted)" copies and ` +
      'restore missing glyph files (rerun the generator, or git checkout) before going on; tests/test_ufo.py fails on them.',
  }
}
