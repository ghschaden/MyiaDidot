// Pure decision rules for the guards, kept apart so tests can call them.

export type Verdict = { decision: 'deny' | 'ask'; reason: string }

const PREFIX = 'myia-didot'

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
  if (path.startsWith(`${root}/tests/data/`)) {
    return {
      decision: 'ask',
      reason: `${PREFIX}: tests/data/ holds the regression baselines; editing them changes what counts as correct.`,
    }
  }
  return undefined
}
