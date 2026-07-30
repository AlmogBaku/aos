#!/usr/bin/env node
// Does the template repo `kb init` clones still match the templates in this checkout?
//
// This gap bit twice in one session. `kb init` clones TEMPLATE_REPO_URL by default, but
// every test passes `--templates <local-dir>` to skip the network — so the entire suite
// can be green while the primary materialization path ships a stale contract file. The
// second time, the base's AGENTS.md was 30 lines longer than the kit's and still carried
// prose the rewrite existed to retire.
//
// Network-dependent by nature, so this is NOT part of `tools/check.sh` or CI: a gate that
// fails on a plane is a gate people learn to skip. Run it after touching
// capabilities/kb/skills/init/templates/, and before trusting a release.
//
// Usage: node tools/check-template-drift.mjs [--json]
// Exit 0 = in sync (or offline, reported as a skip), 1 = drift, 2 = could not check.
import { readFileSync, existsSync, mkdtempSync, rmSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { REPO_ROOT } from './lib/repo.mjs';

const TEMPLATES = join(REPO_ROOT, 'capabilities/kb/skills/init/templates');
const asJson = process.argv.includes('--json');

// The URL the tool actually clones — read from the tool, never duplicated here, or this
// check drifts from the thing it is checking.
const constants = readFileSync(
  join(REPO_ROOT, 'capabilities/kb/tool/src/aos_kb/constants.py'), 'utf8');
const m = constants.match(/^TEMPLATE_REPO_URL\s*=\s*["'](.+?)["']/m);
if (!m) {
  console.error('could not find TEMPLATE_REPO_URL in the tool constants');
  process.exit(2);
}
const url = m[1];

const walk = (dir, base = dir) => readdirSync(dir).flatMap((n) => {
  const abs = join(dir, n);
  if (n === '.git') return [];
  return statSync(abs).isDirectory() ? walk(abs, base) : [relative(base, abs)];
});

const tmp = mkdtempSync(join(tmpdir(), 'aos-tpl-'));
const clone = join(tmp, 'template');
try {
  try {
    execFileSync('git', ['clone', '-q', '--depth', '1', url, clone], { stdio: 'pipe' });
  } catch (e) {
    const msg = `could not clone ${url} — offline? (${String(e.stderr || e.message).trim().split('\n')[0]})`;
    if (asJson) console.log(JSON.stringify({ status: 'skipped', reason: msg }));
    else console.log(`template drift: SKIPPED — ${msg}`);
    process.exit(0);   // offline is not a failure; this check is advisory by design
  }

  const drift = [];
  for (const rel of walk(TEMPLATES)) {
    const mine = readFileSync(join(TEMPLATES, rel), 'utf8');
    const theirs = existsSync(join(clone, rel))
      ? readFileSync(join(clone, rel), 'utf8') : null;
    if (theirs === null) drift.push({ file: rel, why: 'missing from the template repo' });
    else if (theirs !== mine) drift.push({ file: rel, why: 'differs from this checkout' });
  }
  // The template repo's own README describes the repo and is deliberately NOT a template
  // (base.README.md is the one that renders into a base), so it is not expected here.
  const extra = walk(clone).filter((r) => r !== 'README.md' && !existsSync(join(TEMPLATES, r)));
  for (const rel of extra) drift.push({ file: rel, why: 'in the template repo but not in this checkout' });

  if (asJson) {
    console.log(JSON.stringify({ status: drift.length ? 'drift' : 'in-sync', url, drift }, null, 2));
  } else if (drift.length) {
    console.error(`template drift: ${drift.length} file(s) out of sync with ${url}\n`);
    for (const d of drift) console.error(`  ${d.file}: ${d.why}`);
    console.error('\nA default `kb init` clones that repo, so users get the repo\'s version,');
    console.error('not this checkout\'s. Push the templates, or explain the divergence.');
  } else {
    console.log(`template drift: in sync with ${url}`);
  }
  process.exit(drift.length ? 1 : 0);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
