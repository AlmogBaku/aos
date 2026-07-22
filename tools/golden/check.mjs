#!/usr/bin/env node
// Golden-render structural checks (RFC-002 tier 2, deterministic layer).
// Modes:
//   default      — validate committed snapshots under tests/golden/hermes/<name>/
//   --live NAME  — validate the real materialized tree per PROTOCOL.md roots
// Exits non-zero on any failure. No LLM anywhere in here.
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { parse } from 'yaml';
import { REPO_ROOT } from '../lib/repo.mjs';
import { ORIGIN_FRONTMATTER_KEY } from '../lib/constants.mjs';

const args = process.argv.slice(2);
const live = args.includes('--live');
const names = args.filter((a) => !a.startsWith('--'));

const failures = [];
const fail = (code, msg) => failures.push({ code, msg });

function liveRoots(exp) {
  const roots = {
    front: join(homedir(), '.hermes', 'profiles', 'aos-test'),
    clone: join(REPO_ROOT, 'tests', '.sandbox', 'aos-clone'),
  };
  for (const a of exp.agents ?? []) roots[a] = join(homedir(), '.hermes', 'profiles', `aos-${a}`);
  return roots;
}

function snapshotRoots(exp, snapDir) {
  const roots = { front: join(snapDir, 'front'), clone: join(snapDir, 'clone') };
  for (const a of exp.agents ?? []) roots[a] = join(snapDir, a);
  return roots;
}

function resolveRef(roots, ref) {
  const [root, ...rest] = ref.split(':');
  if (!(root in roots)) return null;
  return join(roots[root], rest.join(':'));
}

function* walk(dir) {
  if (!existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const abs = join(dir, name);
    if (statSync(abs).isDirectory()) yield* walk(abs);
    else yield abs;
  }
}

function runExpectations(expName, roots) {
  const exp = parse(readFileSync(join(REPO_ROOT, 'tools', 'golden', 'expectations', `${expName}.yaml`), 'utf8'));

  for (const ref of exp.expect_files ?? []) {
    const p = resolveRef(roots, ref);
    if (!p || !existsSync(p)) fail('golden/missing', `${expName}: expected ${ref}`);
  }
  for (const ref of exp.forbid_files ?? []) {
    const p = resolveRef(roots, ref);
    if (p && existsSync(p)) fail('golden/forbidden', `${expName}: ${ref} must not exist (used_by scoping)`);
  }
  for (const ref of exp.origin_tag_roots ?? []) {
    const dir = resolveRef(roots, ref);
    for (const f of walk(dir ?? '')) {
      if (!f.endsWith('SKILL.md')) continue;
      if (!readFileSync(f, 'utf8').includes(`${ORIGIN_FRONTMATTER_KEY}:`)) {
        fail('golden/origin-tag', `${expName}: ${f} lacks ${ORIGIN_FRONTMATTER_KEY}`);
      }
    }
  }
  for (const s of exp.schedules ?? []) {
    const jobsPath = resolveRef(roots, `${s.profile}:cron/jobs.json`);
    let found = false;
    if (jobsPath && existsSync(jobsPath)) {
      try {
        const jobs = JSON.parse(readFileSync(jobsPath, 'utf8')).jobs ?? [];
        const matches = jobs.filter((j) => (j.name ?? '').startsWith(s.name_prefix));
        found = matches.length === 1; // single-owner: exactly one
        if (matches.length > 1) fail('golden/schedule-dup', `${expName}: ${s.name_prefix} appears ${matches.length}× (single-owner rule)`);
      } catch (e) {
        fail('golden/jobs-parse', `${expName}: ${jobsPath}: ${e.message}`);
      }
    }
    if (!found) fail('golden/schedule', `${expName}: no job named ${s.name_prefix}* in profile ${s.profile}`);
  }
  for (const s of exp.sentinels ?? []) {
    if (s.in) {
      const p = resolveRef(roots, s.in);
      if (!p || !existsSync(p) || !readFileSync(p, 'utf8').includes(s.text)) {
        fail('golden/sentinel', `${expName}: "${s.text}" not found in ${s.in}`);
      }
    } else if (s.in_dir) {
      const dir = resolveRef(roots, s.in_dir);
      let found = false;
      for (const f of walk(dir ?? '')) {
        try { if (readFileSync(f, 'utf8').includes(s.text)) { found = true; break; } } catch {}
      }
      if (!found) fail('golden/sentinel', `${expName}: "${s.text}" not found anywhere under ${s.in_dir}`);
    }
  }
  if (exp.lockfile_capabilities) {
    const p = resolveRef(roots, 'clone:.aos/installs.lock.yaml');
    if (!p || !existsSync(p)) {
      fail('golden/lockfile', `${expName}: lockfile missing`);
    } else {
      const lock = readFileSync(p, 'utf8');
      for (const cap of exp.lockfile_capabilities) {
        if (!lock.includes(cap)) fail('golden/lockfile', `${expName}: lockfile has no entry for "${cap}"`);
      }
    }
  }
}

// Canary check lives in the protocol, not here: re-run tools/golden/prestate.sh to a
// second file and `diff` it against the pre-install one — byte-equal or the install
// touched something it must not.

if (live) {
  for (const name of names.length ? names : ['full-install']) {
    const exp = parse(readFileSync(join(REPO_ROOT, 'tools', 'golden', 'expectations', `${name}.yaml`), 'utf8'));
    runExpectations(name, liveRoots(exp));
  }
} else {
  const goldenDir = join(REPO_ROOT, 'tests', 'golden', 'hermes');
  const snaps = existsSync(goldenDir) ? readdirSync(goldenDir) : [];
  for (const snap of snaps) {
    const expPath = join(REPO_ROOT, 'tools', 'golden', 'expectations', `${snap}.yaml`);
    if (!existsSync(expPath)) continue;
    const exp = parse(readFileSync(expPath, 'utf8'));
    runExpectations(snap, snapshotRoots(exp, join(goldenDir, snap)));
  }
  if (!snaps.length) {
    console.log('golden: no committed snapshots yet (first render lands in WP5)');
    process.exit(0);
  }
}

for (const f of failures) console.log(`FAIL ${f.code.padEnd(20)} ${f.msg}`);
console.log(`golden: ${failures.length} failures`);
process.exit(failures.length ? 1 : 0);
