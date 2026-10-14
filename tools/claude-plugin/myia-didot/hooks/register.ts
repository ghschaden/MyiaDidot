import type { EngineInterface, Register, Timer } from 'claude-code'

import { judgeBash, judgePath } from './rules'

// Active only inside the Myia Didot repository (recognised by its status
// script and master UFO); everywhere else every hook passes straight through.
const MARKERS = ['scripts/status.py', 'sources/MyiaDidot-Regular.ufo']

// Tool calls after which the status line is worth recomputing.
const TOUCHES_FONT = /\b(make|pytest|fontmake|composites\.py|update_test_data\.py|set_win_metrics\.py|ufonormalizer|git (checkout|reset|pull|merge|rebase|stash))\b/

// Module state: reset on each reload, which only costs one lookup.
let root: string | null | undefined // undefined: not looked up yet; null: not our repo
let pendingRefresh: Timer | undefined

async function projectRoot($: EngineInterface): Promise<string | null> {
  if (root !== undefined) return root
  const r = await $.session.root()
  const found = await Promise.all(MARKERS.map(m => $.fs.exists(`${r}/${m}`)))
  root = found.every(Boolean) ? r : null
  return root
}

async function run($: EngineInterface, dir: string, argv: string[], timeoutMs = 30_000) {
  return $.process.run(argv, { cwd: dir, timeoutMs })
}

async function refreshStatus($: EngineInterface) {
  const dir = await projectRoot($)
  if (dir === null) return
  try {
    const { exitCode, stdout, stderr } = await run($, dir, [`${dir}/.venv/bin/python`, '-I', 'scripts/status.py'])
    $.ui.status(exitCode === 0 ? stdout.trim() : `Myia Didot · status failed: ${stderr.trim().split('\n').pop()}`)
  } catch {
    $.ui.status('Myia Didot · status unavailable (run make setup)')
  }
}

// Coalesce bursts of edits into one refresh a moment after the last one.
function scheduleRefresh($: EngineInterface) {
  pendingRefresh?.cancel()
  pendingRefresh = $.clock.after(1500, () => {
    pendingRefresh = undefined
    void refreshStatus($)
  })
}

async function refreshIfSource($: EngineInterface, path: string) {
  const dir = await projectRoot($)
  if (dir !== null && path.startsWith(`${dir}/sources/`)) scheduleRefresh($)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    if ((await projectRoot($)) === null) return result
    await $.command.register({ name: 'font-status', description: 'Myia Didot: coverage per glyph set and last test run' })
    await $.command.register({ name: 'font-test', description: 'Myia Didot: run the test suite and report' })
    await $.command.register({ name: 'font-proof', description: 'Myia Didot: build the PDF proofs and open the character set' })
    await refreshStatus($)
    return result
  })

  // --- guards ------------------------------------------------------------

  on('tool.check', { tool: 'Bash' }, async ($, e, next) => {
    if ((await projectRoot($)) === null) return next(e)
    const verdict = judgeBash(String((e.input as { command?: unknown }).command ?? ''))
    return verdict ?? next(e)
  }).catch(($, e, next) => (next.called ? next(e) : { decision: 'ask', reason: 'myia-didot: its guard failed; please confirm.' }))

  for (const tool of ['Edit', 'Write', 'NotebookEdit'] as const) {
    on('tool.check', { tool }, async ($, e, next) => {
      const dir = await projectRoot($)
      if (dir === null) return next(e)
      const input = e.input as { file_path?: unknown; notebook_path?: unknown }
      const verdict = judgePath(String(input.file_path ?? input.notebook_path ?? ''), dir)
      return verdict ?? next(e)
    }).catch(($, e, next) => (next.called ? next(e) : { decision: 'ask', reason: 'myia-didot: its guard failed; please confirm.' }))
  }

  // --- status line upkeep -------------------------------------------------

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const result = await next(e)
    if (TOUCHES_FONT.test(e.command) && (await projectRoot($)) !== null) scheduleRefresh($)
    return result
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const result = await next(e)
    await refreshIfSource($, e.file_path)
    return result
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const result = await next(e)
    await refreshIfSource($, e.file_path)
    return result
  }).catch(($, e, next) => next(e))

  // --- commands -----------------------------------------------------------

  on('command.run', { command: 'font-status' }, async $ => {
    const dir = await projectRoot($)
    if (dir === null) return { text: 'Not in the Myia Didot repository.' }
    const { stdout, stderr, exitCode } = await run($, dir, [`${dir}/.venv/bin/python`, '-I', 'scripts/status.py', '--long'])
    return { text: exitCode === 0 ? stdout.trimEnd() : `status.py failed:\n${stderr}` }
  })

  on('command.run', { command: 'font-test' }, async $ => {
    const dir = await projectRoot($)
    if (dir === null) return { text: 'Not in the Myia Didot repository.' }
    $.ui.status('Myia Didot · running tests…')
    const { stdout, stderr, exitCode } = await run($, dir, [`${dir}/.venv/bin/pytest`, '-q', '-p', 'no:cacheprovider'], 600_000)
    await refreshStatus($)
    const out = (stdout + stderr).trimEnd().split('\n')
    const shown = exitCode === 0 ? out.slice(-1) : out.slice(-60)
    return {
      text: (exitCode === 0 ? 'Tests passed: ' : 'Tests FAILED:\n') + shown.join('\n'),
      context: exitCode === 0 ? undefined : ['The Myia Didot test suite failed; output above.'],
    }
  })

  on('command.run', { command: 'font-proof' }, async $ => {
    const dir = await projectRoot($)
    if (dir === null) return { text: 'Not in the Myia Didot repository.' }
    $.ui.status('Myia Didot · building proofs…')
    const made = await run($, dir, ['make', 'fonts', 'proof'], 600_000)
    await refreshStatus($)
    if (made.exitCode !== 0) {
      return { text: `make proof failed:\n${(made.stdout + made.stderr).trimEnd().split('\n').slice(-30).join('\n')}` }
    }
    const proofs = `${dir}/build/proofs`
    for (const name of ['charset', 'smallcaps-review']) {
      await run($, dir, ['xdg-open', `${proofs}/${name}.pdf`]).catch(() => undefined)
    }
    return {
      text: `Proofs built in ${proofs}: charset.pdf and smallcaps-review.pdf (opened), proof.pdf, smallcaps.pdf`,
    }
  })
}
