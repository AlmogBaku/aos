#!/usr/bin/env node
// Two mechanical coverage checks, so the docs cannot quietly fall behind the tools.
//
//   1. every CLI verb appears in docs/USAGE.md and AGENTS.md's verb list
//   2. every count quoted in docs/TESTING.md matches what the tools actually report
//
// Why mechanical: the CLI grew by eight verbs in one pass and the docs did not, and
// docs/TESTING.md claimed "85 checks in 14 code families" while the linter emitted 81 in 13.
// Neither is a mistake anyone makes on purpose — they are what happens when a number lives in
// prose and its source lives in code. Both checks derive the truth from the tool rather than
// from a second hand-maintained list, so there is nothing to keep in sync.
//
// AGENTS.md, not CLAUDE.md: the latter is a symlink to the former (one source, two names), so
// reading both would check the same bytes twice and reading only CLAUDE.md would hide that.
//
// Usage: node tools/check-coverage.mjs
//   Requires `uv` to interrogate the tool's own --help. Skips with a note if absent — the same
//   shape as check.sh's tier-0 guard, so a machine without uv reports honestly instead of green.
import { readFileSync } from 'node:fs';
import { execFileSync, spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { REPO_ROOT, walkRepo, listCapabilities } from './lib/repo.mjs';

const read = (rel) => readFileSync(join(REPO_ROOT, rel), 'utf8');
const failures = [];
const fail = (where, msg) => failures.push(`${where}: ${msg}`);

function uvAvailable() {
  try {
    execFileSync('uv', ['--version'], { stdio: 'ignore' });
    return true;
  } catch { return false; }
}

// ---- 1. verb coverage ------------------------------------------------------------------
// Parsed from the CLI's own --help, so the list cannot drift from the implementation.
if (!uvAvailable()) {
  console.log('coverage gate: verb coverage SKIPPED (uv not found — install: https://docs.astral.sh/uv/)');
} else {
  const help = execFileSync('uv', ['run', '--quiet', '--project', 'capabilities/kb/tool',
    'kb', '--help'], { cwd: REPO_ROOT, encoding: 'utf8' });
  const block = help.slice(help.indexOf('Commands:'));
  const verbs = [...block.matchAll(/^\s{2}(\S+)\s{2,}/gm)].map((m) => m[1]);
  if (verbs.length < 20) {
    fail('kb --help', `parsed only ${verbs.length} verbs from the Commands block — the parser has `
      + 'drifted from typer\'s output format, and a coverage check that sees no verbs passes vacuously');
  }
  for (const doc of ['docs/USAGE.md', 'AGENTS.md']) {
    const text = read(doc);
    const missing = verbs.filter((v) => !new RegExp(`\\b${v}\\b`).test(text));
    if (missing.length) {
      fail(doc, `${missing.length} CLI verb(s) undocumented: ${missing.join(' ')}`);
    }
  }
}

// ---- 2. quoted counts -----------------------------------------------------------------
// A number in prose is a claim about the tools. Check it against them.
const testing = read('docs/TESTING.md');

// The linter's own check inventory: every code it can emit, and the families they group into.
const codes = new Set();
for (const rel of walkRepo(REPO_ROOT)) {
  if (!rel.startsWith('tools/lint/checks/') || !rel.endsWith('.mjs')) continue;
  for (const m of read(rel).matchAll(/report\(\s*'(?:error|warn)'\s*,\s*'([a-z]+\/[a-z-]+)'/g)) {
    codes.add(m[1]);
  }
}
// version/* is emitted by the diff-aware pass, which lives outside checks/ and fires only
// with --base. It is still one of the linter's checks, so it counts.
for (const m of read('tools/lint/aos-lint.mjs').matchAll(/'(version\/[a-z-]+)'/g)) codes.add(m[1]);
const families = new Set([...codes].map((c) => c.split('/')[0]));

const claim = testing.match(/\((\d+) checks in (\d+) code families/);
if (!claim) {
  fail('docs/TESTING.md', 'no "(N checks in M code families" claim found — if the sentence was '
    + 'reworded, update this check rather than dropping it');
} else {
  if (Number(claim[1]) !== codes.size) {
    fail('docs/TESTING.md', `claims ${claim[1]} checks; the linter emits ${codes.size} distinct codes`);
  }
  if (Number(claim[2]) !== families.size) {
    fail('docs/TESTING.md', `claims ${claim[2]} code families; there are ${families.size} `
      + `(${[...families].sort().join(' ')})`);
  }
}

// Suite sizes, if the doc quotes them. `unittest` prints "Ran N tests" to stderr.
if (uvAvailable()) {
  for (const [suite, label] of [['tests/tool/test_kb.py', 'test_kb.py'],
    ['tests/tool/test_lock.py', 'test_lock.py']]) {
    const quoted = testing.match(new RegExp(`${label.replace('.', '\\.')}[^\\n]*?\\b(\\d+) tests`));
    if (!quoted) continue;   // the doc need not quote a size; if it does, it must be right
    // unittest prints "Ran N tests" to STDERR, and passes without throwing — so the stream has
    // to be captured explicitly. Piping stdout to the parent would leak the dots into this
    // gate's own output, hence the pipe on both.
    const res = spawnSync('uv', ['run', '--quiet', suite],
      { cwd: REPO_ROOT, encoding: 'utf8' });
    const ran = (`${res.stdout ?? ''}${res.stderr ?? ''}`.match(/Ran (\d+) tests/) ?? [])[1];
    if (ran && Number(quoted[1]) !== Number(ran)) {
      fail('docs/TESTING.md', `claims ${label} has ${quoted[1]} tests; it has ${ran}`);
    }
  }
}

// The installed-skill count, wherever prose states one. `aos-lock skills` is the authority,
// and the same number appears in README support tables and the golden expectations.
const skillCount = listCapabilities(REPO_ROOT)
  .reduce((n, cap) => n + (read(`${cap.rel}/CAPABILITY.md`).match(/^\s+- id:/gm) ?? []).length, 0);
for (const doc of ['docs/TESTING.md', 'README.md']) {
  const m = read(doc).match(/\b(\d+) installed skills?\b/);
  if (m && Number(m[1]) !== skillCount) {
    fail(doc, `claims ${m[1]} installed skills; the manifests declare ${skillCount}`);
  }
}

if (failures.length) {
  console.error(`coverage gate: ${failures.length} failure(s)\n`);
  for (const f of failures) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`coverage gate: clean (${codes.size} lint codes in ${families.size} families)`);
