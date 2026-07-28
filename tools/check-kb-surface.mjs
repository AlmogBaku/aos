#!/usr/bin/env node
// The kb capability surface gate: the mechanical half of the LAYOUT 2 rewrite.
// A find-replace leaves a skill naming the right paths while still teaching the old
// model, so this checks what a path sweep cannot: the retired vocabulary is absent, no
// artifact still invokes the old command name, and each skill description carries the
// trigger clauses that keep seven skills out of each other's trigger space.
//
// Deliberately NOT here: SKILL.md body length, reference-file Contents blocks, and the
// description character limit. Those are the published Agent Skills limits (500 lines /
// 100 lines / 1024 chars) and `tools/lint/aos-lint.mjs` already covers all three — as an
// error for the description (skill/description) and as warnings for the other two
// (skill/body-length, skill/reference-toc), so a 600-line SKILL.md is reported but does not
// fail CI. A second implementation here would be a second thing to keep in sync.
// There are no per-file line budgets: the authoring guide sets one body limit and nothing in
// this capability is within 350 lines of it.
//
// Scoped to capabilities/kb/ on purpose. Plan 4 generalises it repo-wide (design §3.1)
// with the transcripts / BUILD-GAPS / marked-old-pattern allowlist. What needs care then:
//
//   - `gtd` is legitimate outside this capability (capabilities/gtd-capture/ is a real
//     directory, and tests/golden/** carries aos:gtd-capture:nightly-drain).
//   - `state/` was retired as a ROOT directory but reintroduced at .kb/state/ meaning
//     something else, and `lint --ci` outlived the janitor it was built for.
//   - EIGHT of these tokens live legitimately inside tool/, which is excluded here but
//     would not be under a repo-wide sweep: `BASE.yaml`, `state.yaml`, `_ops/`, `_archive/`
//     and `triage:` because kb migrate has to NAME the old layout to move it; `growth_stage`
//     and `--write-report` in comments explaining what was removed and why; and `aos-base`
//     in a load-bearing `uv tool uninstall aos-base` instruction for anyone still on the old
//     package name. None of these is a leftover — a repo-wide gate must exempt tool/ or
//     allowlist each one deliberately.
//
// Usage: node tools/check-kb-surface.mjs [relPathPrefix ...]
//   With prefixes, only matching files are checked — that is how a single task in the
//   rewrite verifies itself while the rest of the surface is still failing.
//
// Note walkRepo does not read .gitignore, so an untracked scratch file under
// capabilities/kb/ is scanned like any other. Check `git status` before believing a
// failure in a file you do not recognise.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT, walkRepo } from './lib/repo.mjs';

const CAP = 'capabilities/kb';
// tool/ is the tool's own territory; it is checked by the Python suite, not by this gate.
const EXCLUDE = [`${CAP}/tool/`];

// Tokens the LAYOUT 2 design retires. Each is a *whole word or path fragment* that
// cannot survive anywhere in the capability surface.
const RETIRED = [
  ['_ops/', '_ops/ dissolved into .kb/ (pending · work · cache)'],
  ['_archive/', '_archive/ is gone — `kb archive <page> --reason` is a git rm + commit'],
  ['needs-entity-queue', 'unresolved mentions are .kb/pending/ entries with kind: entity'],
  ['lint-report-', 'lint output is stdout; criticals become .kb/pending/ findings'],
  ['--write-report', 'the report IS the interface — there is no report file'],
  ['triage:', 'location is the state: .kb/pending/ means pending, _raw/ means ingested'],
  ['raw/captures/', '_raw/ is flat — type: and source: already carry the fact'],
  ['BASE.yaml', 'the machine config is .kb/base.yml at LAYOUT 2'],
  ['state.yaml', 'the attention window is .kb/state/<principal>.yml, always'],
  ['.kb/state.yml', 'state is always sharded — .kb/state/<principal>.yml, no special case'],
  ['.base/', 'derived caches live in .kb/cache/'],
  ['kind: archive', 'the archive zone kind is retired with the directory'],
  ['growth_stage', 'no reader survives — expires: is the only lifetime rule kb has'],
  ['methodology:', 'a dead seam — kb IS the methodology'],
  ['principals:', 'the grants table names principal ids directly, and IS the roster'],
  ['hard-deleted', '`kb prune` deletes; git is the undo. Do not claim otherwise'],
  ['next-actions.md', 'a list is a view — `kb find --where status=next`'],
  ['adapters/github', 'the shared-KB CI infrastructure is reverted'],
  ['aos-base', 'the package is aos-kb'],
  ['aos_base', 'the module is aos_kb'],
  ['quick-capture', "the general capture path is kb's `capture` skill"],
  ['drainer', "kb has an archiver; the drainer was gtd-capture's"],
  ['gtd', "no kb artifact may name another capability's internals"],
];

// One deliberate exception, per the authoring guide's "marked as an old pattern" shape:
// adopt must name the LAYOUT 1 detection marker, because detecting it is what its step 3
// does. Keyed to a FULL PATH, never a prefix — widening this to a directory would blind
// the gate in the one file most likely to describe LAYOUT 1 both correctly and not.
const OLD_PATTERN_OK = new Map([
  [`${CAP}/skills/adopt/SKILL.md`, new Set(['BASE.yaml'])],
]);

// `base <verb>` invocations. The noun "a base" / "the base" must survive untouched, so
// this matches only the command form. The lookbehind excludes `--base <path>` and
// `example-base`, which are legitimate and appear in ci.yml / CONTRIBUTING.md / check.sh
// — out of scope today, but Plan 4's repo-wide pass would trip on all three.
const VERBS = 'init|adopt|capture|inbox|state|search|links|lint|grants|index|sync|commit'
  + '|history|refuse|verify|import|find|set|prune|archive|pending|ingest|config|migrate';
const BASE_CMD = new RegExp(`(?<![\\w-])base (?:${VERBS})\\b`);
const DA_MARKER = /\[[DA]\]/;

// The seven skills, and whether the description must carry an explicit negative clause.
// A negative is required wherever the skill competes for a trigger space: kb, capture
// and route all sound like "capture", and init/adopt/import all sound like "set up a KB".
const SKILLS = {
  kb: true, capture: true, route: true, recall: true, init: true, adopt: true, import: true,
};

// The authoring guide is explicit: descriptions are injected into the system prompt, so a
// first/second-person voice causes discovery problems. Third person only.
// Matches the imperative "Use this…" opener and any second-person address, not just a
// hand-listed set of phrasings — an earlier version listed exact strings and let both
// "Use this to file a thought" and "This skill helps you file X" through.
// Note "the user's …" and "the user wants …" are third person and must keep passing; what is
// banned is addressing the reader ("helps you", "you can") or speaking as the skill ("I can").
const FIRST_OR_SECOND_PERSON =
  /\b(?:I can|I will|I help|I'll|helps? you|lets you|allows you|enables you|you can|you should|use this (?:to|when|for))\b|^\s*"?Use this\b/i;

const failures = [];
const fail = (file, msg) => failures.push(`${file}: ${msg}`);
const prefixes = process.argv.slice(2);
// A prefix that matches nothing must be an error, not a pass. Every per-task verification
// during the rewrite ran with a prefix, so a typo'd path would otherwise report `clean` and
// exit 0 — the loudest possible way to check nothing at all.
const matched = new Set();
const wanted = (rel) => {
  if (!prefixes.length) return true;
  const hit = prefixes.find((p) => rel.startsWith(p));
  if (hit === undefined) return false;
  matched.add(hit);
  return true;
};
const lineCount = (text) => text.trimEnd().split('\n').length; // reads as `wc -l`

// 1. Retired vocabulary, the old command name, and the dropped [D]/[A] notation
for (const rel of walkRepo(REPO_ROOT)) {
  if (!rel.startsWith(`${CAP}/`)) continue;
  if (EXCLUDE.some((e) => rel.startsWith(e))) continue;
  if (!wanted(rel)) continue;
  let text;
  try { text = readFileSync(join(REPO_ROOT, rel), 'utf8'); } catch { continue; }
  for (const [token, why] of RETIRED) {
    if (!text.includes(token)) continue;
    if (OLD_PATTERN_OK.get(rel)?.has(token)) continue;
    fail(rel, `retired token "${token}" — ${why}`);
  }
  if (BASE_CMD.test(text)) fail(rel, `invokes "${text.match(BASE_CMD)[0]}" — the command is \`kb\``);
  if (DA_MARKER.test(text)) fail(rel, 'carries a [D]/[A] determinism marker — the notation is dropped');
}

// 2. Description shape. Length and the 1024 cap are aos-lint's (skill/description); what
// it cannot know is which skills compete with each other for a trigger.
for (const [id, needsNegative] of Object.entries(SKILLS)) {
  const rel = `${CAP}/skills/${id}/SKILL.md`;
  if (!wanted(rel)) continue;
  const abs = join(REPO_ROOT, rel);
  if (!existsSync(abs)) { fail(rel, 'missing'); continue; }
  const text = readFileSync(abs, 'utf8');
  const m = text.match(/^description:\s*(.*)$/m);
  if (!m) { fail(rel, 'no description in frontmatter'); continue; }
  const desc = m[1];
  if (!/\bUse when\b/.test(desc)) fail(rel, 'description has no "Use when" trigger clause');
  if (needsNegative && !/\bDo NOT use\b/.test(desc)) {
    fail(rel, 'description has no "Do NOT use" clause — this skill competes for a trigger space');
  }
  if (FIRST_OR_SECOND_PERSON.test(desc)) {
    fail(rel, `description is not third person ("${desc.match(FIRST_OR_SECOND_PERSON)[0]}") — it is injected into the system prompt`);
  }
}

for (const p of prefixes) {
  if (!matched.has(p)) fail(p, 'prefix matched no file under capabilities/kb/ — check the path');
}

if (failures.length) {
  console.error(`kb surface gate: ${failures.length} failure(s)\n`);
  for (const f of failures) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`kb surface gate: clean${prefixes.length ? ` (${prefixes.join(' ')})` : ''}`);
