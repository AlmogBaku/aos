#!/usr/bin/env node
// The retired-token gate: the mechanical proof there are no leftovers.
//
// Generalises the kb-scoped surface gate to the whole tracked tree. A find-replace leaves a
// document naming the right paths while still teaching the old model, so this checks what a
// path sweep cannot: the retired vocabulary is absent everywhere, no artifact still invokes
// the old command name, and every shipped skill description carries the trigger clauses that
// keep twenty-two skills out of each other's trigger space.
//
// Why a gate rather than care: docs drifted once already here — the 2026-07-26 ledger row
// records the architecture diagram still drawing the world of nine days earlier. A sweep this
// wide will drift again unless something fails on it, so this turns "did we get everything?"
// from a judgment call at the end into a build error that has to be driven to zero.
//
// Deliberately NOT here: SKILL.md body length, reference-file Contents blocks, and the
// description character limit. Those are the published Agent Skills limits (500 / 100 / 1024)
// and tools/lint/aos-lint.mjs already covers all three. A second implementation would be a
// second thing to keep in sync. There are no per-file line budgets.
//
// Two tokens need care rather than a blunt grep, and getting either wrong makes the gate
// useless:
//
//   - The NOUN "a base" / "the base" must survive. `base == one git repo` is still the
//     concept; only the command was renamed. So only `base <verb>` invocations are banned,
//     via a lookbehind that also spares `--base <path>` and `example-base lint`.
//   - `state/` is deliberately absent from RETIRED. It was retired as a ROOT directory and
//     REINTRODUCED at .kb/state/ meaning something else, so a token would ban the new tree.
//     The root form is caught by the `state.yaml` entry instead.
//
// Usage: node tools/check-retired.mjs [relPathPrefix ...]
//   With prefixes, only matching files are checked — that is how one task in a sweep verifies
//   itself while the rest of the tree is still failing. A prefix matching nothing is an ERROR,
//   not a pass: a typo'd prefix once reported `clean` while checking nothing at all.
//
// Note walkRepo does not read .gitignore, so an untracked scratch file is scanned like any
// other. Check `git status` before believing a failure in a file you do not recognise.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT, walkRepo, listCapabilities } from './lib/repo.mjs';
import { readFrontmatter } from './lib/frontmatter.mjs';

// Records of real runs and append-only ledger rows quote the world as it was — the ledger's
// own precedent is that historical material stays verbatim. The other two are not history:
//
//   - capabilities/kb/tool/ — `kb migrate` has to NAME LAYOUT 1 in order to move it, and
//     `uv tool uninstall aos-base` is a live instruction for anyone still on the old package
//     name. Eight tokens live there legitimately. The tool is checked by its own Python suite.
//   - tests/golden/hermes/ — frozen snapshots of a real install, regenerated only by the live
//     e2e and never hand-edited. This entry retires with that run.
const ALLOW_PREFIX = [
  'tests/transcripts/',
  'docs/BUILD-GAPS.md',
  // NOT capabilities/kb/tool/ wholesale — see TOOL_SOURCE_OK below. A whole-directory
  // exemption there hid nine source files from every token, which is the shape this gate's
  // own header warns about.

  'tests/golden/hermes/',
  // LAYOUT 1 by design: import-src-v1/ is the source an import walks, so its shape IS the
  // fixture. A gate that "fixed" it would delete the thing under test. Same for the eval
  // queries, whose negative cases quote the old layout on purpose.
  'tests/fixtures/import-src-v1/',
  'tests/evals/',
  // The suite's job includes proving the old shape is GONE — `test_layout_1_artifacts_are_
  // absent` names every retired path in order to assert it does not exist, and MigrateTest
  // builds a layout-1 tree inline because that is what migration takes as input. A gate
  // firing here would ban the tests that keep the retirement honest. (MigrateTest's own
  // docstring says it built the tree inline rather than committing a second fixture for
  // exactly this reason.)
  'tests/tool/test_kb.py',
  // This file names every retired token in order to ban it.
  'tools/check-retired.mjs',
];

// A section deliberately showing a superseded pattern marks itself — the shape Anthropic's
// authoring guide endorses for old patterns — so the exemption is visible in the file rather
// than hidden in this gate.
const MARKER = /<!--\s*retired-ok:([^>]*?)-->/g;

// Tokens the LAYOUT 2 design retires. Each is a whole word or path fragment that cannot
// survive anywhere in the tracked tree outside the allowlist above.
const RETIRED = [
  // the layout
  ['log.md', 'git is the audit substrate — there is no log file'],
  ['_ops/', '_ops/ dissolved into .kb/ (pending · work · cache)'],
  ['_archive/', 'git is the archive — `kb archive <page> --reason` is a git rm + commit'],
  ['needs-entity-queue', 'an unresolved mention is a .kb/pending/ entry, kind: entity'],
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
  // the tool
  ['aos-base', 'the package is aos-kb'],
  ['aos_base', 'the module is aos_kb'],
  // the capability
  ['gtd-capture', 'the capability is work-tracker'],
  ['gtd-', 'the skill prefix is wt-'],
  ['gtd_triaged', 'the ordering contract is gone, not decoupled'],
  ['quick-capture', "kb owns `capture`; work-tracker owns `wt-capture`"],
  ['drainer', 'work-tracker has a steward'],
  // reverted
  ['--no-ci', 'the shared-KB CI infrastructure is out of scope (RFC-010 Q1)'],
  ['unattended janitor', 'the CI janitor is descoped — RFC-010 Q1. NOTE: `lint --ci` itself '
    + 'SURVIVES (Plan 00b kept it deliberately, on its own merits); this bans the stale '
    + 'justification, not the flag'],
  ['adapters/github', 'the shared-KB CI infrastructure is reverted'],
];

// `base <verb>` invocations, and only those. The lookbehind is load-bearing: a bare \b form
// matches `--base <path>` and `example-base lint`, which appear legitimately in ci.yml,
// CONTRIBUTING.md and check.sh.
const VERBS = 'init|adopt|capture|inbox|state|search|links|lint|grants|index|sync|commit'
  + '|history|refuse|verify|import|find|set|prune|archive|pending|ingest|config|migrate';
// The lookbehind also has to exclude `..base` / `.base`, or a Python `from ..base import Base`
// reads as a `base import` invocation — which is how the wholesale tool/ allowlist came to
// look necessary. It was hiding a false positive, not eight true ones.
// `\s+` not a literal space, so a wrapped or double-spaced invocation still matches; global,
// so a file with three of them reports three rather than one.
const BASE_CMD = new RegExp(`(?<![\\w.-])base\\s+(?:${VERBS})\\b`, 'g');

// The line that installs kb's tool must name the new package. Scoped to lines installing from
// a kb tool path rather than every `uv tool install`, because aos-lock's own install line is
// legitimate and identical in shape. The bare `aos-base` token catches the package rename; this
// catches a kb install line that names some OTHER package, or none.
const KB_INSTALL_LINE = /uv tool install --from[^\n]*kb\/tool[^\n]*/g;

// The [D]/[A] determinism notation is NOT retired kit-wide — capability-lifecycle uses it
// deliberately in seven files (and capability-review's whole step structure is built on the
// distinction). Dropping it was a decision about kb's own surface, where it appeared in three of
// seven skills and taught nothing consistent. So this check is scoped to the two capabilities
// that dropped it, exactly as the kb-scoped gate had it.
const DA_MARKER = /\[[DA]\]/;
// The prose surface only. The tool's own source is code — its comments are not a skill
// teaching a notation, and `admin.py` uses [D] in a docstring about determinism itself.
const DA_SCOPE = ['capabilities/kb/skills/', 'capabilities/kb/docs/',
  'capabilities/work-tracker/'];

// One deliberate old-pattern exception, per the authoring guide's shape: adopt must name the
// LAYOUT 1 detection marker, because detecting it is what its step 3 does. Keyed to a FULL
// PATH with a single token — widening this to a directory would blind the gate in the one
// file most likely to describe LAYOUT 1 both correctly and not.
const OLD_PATTERN_OK = new Map([
  ['capabilities/kb/skills/adopt/SKILL.md', new Set(['BASE.yaml'])],
  // Prose describing what was REMOVED and why, which is the opposite of a leftover: each
  // sentence's subject is the retired thing's absence.
  ['capabilities/kb/docs/design.md', new Set(['next-actions.md', '_ops/'])],
  // The tool has to NAME LAYOUT 1 in order to migrate it, and explain what it removed. Keyed
  // per file and per token rather than exempting the directory: a wholesale exemption hid nine
  // source files from every token, and appending a fresh `_ops/` leftover to base.py still
  // reported clean. Verified by planting exactly that.
  ['capabilities/kb/tool/src/aos_kb/base.py', new Set(['BASE.yaml'])],
  ['capabilities/kb/tool/src/aos_kb/cli.py', new Set(['BASE.yaml', 'log.md'])],
  ['capabilities/kb/tool/src/aos_kb/commands/admin.py', new Set(['log.md'])],
  ['capabilities/kb/tool/src/aos_kb/commands/capture.py', new Set(['triage:'])],
  ['capabilities/kb/tool/src/aos_kb/commands/lifecycle.py', new Set([
    'aos-base', '_archive/', 'BASE.yaml', 'methodology:', '_ops/', 'state.yaml',
    'raw/captures/', 'triage:', '.base/', 'principals:'])],
  ['capabilities/kb/tool/src/aos_kb/commands/lint.py',
    new Set(['growth_stage', 'triage:', '--write-report'])],
  ['capabilities/kb/tool/src/aos_kb/commands/survey.py', new Set(['BASE.yaml'])],
  ['capabilities/kb/tool/src/aos_kb/commands/wiki.py', new Set(['_archive/'])],
  ['capabilities/kb/tool/src/aos_kb/constants.py', new Set(['log.md'])],
  // `uv tool uninstall aos-base` is the whole point of the sentence: anyone upgrading from
  // the old package name has it on PATH, where it shadows the new command and both appear to
  // work. The instruction has to NAME the retired package to remove it.
  ['docs/INSTALL.md', new Set(['aos-base'])],
]);

// Descriptions are injected into the system prompt, so the authoring guide is explicit that a
// first/second-person voice causes discovery problems. Third person only. This matches the
// imperative "Use this…" opener and any second-person address rather than a hand-listed set of
// phrasings — an earlier version listed exact strings and let both "Use this to file a thought"
// and "This skill helps you file X" through. "the user's …" and "the user wants …" are third
// person and must keep passing; what is banned is addressing the reader or speaking as the skill.
const FIRST_OR_SECOND_PERSON =
  /\b(?:I can|I will|I help|I'll|helps? you|lets you|allows you|enables you|you can|you should|use this (?:to|when|for))\b|^\s*"?Use this\b/i;

// A negative clause, in either of the two forms these descriptions use. "Do NOT use" is the
// guide's phrasing and the one to reach for; "Does not <verb>" / "Not for <x>" are accepted
// because forcing the imperative into some sentences produced worse English, not a better
// trigger, and the discriminating content is identical.
//
// A bare negative is NOT enough: the phrase is far too common to be evidence of anything —
// "Does not need any configuration." passed the first version of this check while
// discriminating nothing at all. What makes a negative clause real is that it says where the
// work goes INSTEAD, so it must also name a sibling skill. That is the same bar the prose
// already meets, now enforced rather than assumed.
const NEGATIVE_CLAUSE = /\bDo NOT use\b|\bDoes not\b|\bNot for\b|\bnot for\b/;

const failures = [];
const fail = (file, msg) => failures.push(`${file}: ${msg}`);
const prefixes = process.argv.slice(2);
const matched = new Set();
const wanted = (rel) => {
  if (!prefixes.length) return true;
  const hit = prefixes.find((p) => rel.startsWith(p));
  if (hit === undefined) return false;
  matched.add(hit);
  return true;
};

// 1. Retired vocabulary, the old command name, and the dropped [D]/[A] notation.
for (const rel of walkRepo(REPO_ROOT)) {
  if (ALLOW_PREFIX.some((p) => rel.startsWith(p) || rel === p)) continue;
  if (!wanted(rel)) continue;
  let text;
  try { text = readFileSync(join(REPO_ROOT, rel), 'utf8'); } catch { continue; }
  // The marker exempts the TOKENS IT NAMES, not the file. `<!-- retired-ok: log.md, _ops/ -->`
  // reads as "this file deliberately discusses those two". A bare marker with no tokens
  // exempts nothing and says so — the earlier version skipped the whole file on any marker,
  // so the first use would have silently blinded every unrelated leftover in it.
  const marked = new Set();
  for (const m of text.matchAll(MARKER)) {
    for (const tok of m[1].split(',')) if (tok.trim()) marked.add(tok.trim());
  }

  for (const [token, why] of RETIRED) {
    if (!text.includes(token)) continue;
    if (OLD_PATTERN_OK.get(rel)?.has(token) || marked.has(token)) continue;
    fail(rel, `retired token "${token}" — ${why}`);
  }
  // "base config" and "base schema" read as the command form but are ordinary noun phrases —
  // a base's config, a base's schema. The verb list cannot tell them apart, so the two words
  // that collide are named here rather than dropped from the list.
  for (const cmd of text.match(BASE_CMD) ?? []) {
    if (/^base\s+(?:config|schema)$/.test(cmd)) continue;
    fail(rel, `invokes "${cmd.replace(/\s+/g, ' ')}" — the command is \`kb\``);
  }
  for (const line of text.match(KB_INSTALL_LINE) ?? []) {
    if (!line.includes('aos-kb')) fail(rel, `kb install line does not name aos-kb: "${line.trim()}"`);
  }
  if (DA_SCOPE.some((p) => rel.startsWith(p)) && DA_MARKER.test(text)) {
    fail(rel, 'carries a [D]/[A] determinism marker — kb and work-tracker dropped the notation');
  }
}

// 2. Description shape, for every shipped skill in every capability. Length and the 1024 cap
// are aos-lint's (skill/description); what it cannot know is which skills compete for a
// trigger. Every skill in this kit does: kb's `capture` and work-tracker's are the same word
// for two different speech acts, init/adopt/import all sound like "set up a KB", and the ten
// lifecycle skills are ten verbs on one noun. So the negative clause is required of all of
// them rather than of a hand-maintained subset that a new skill would silently miss.
for (const cap of listCapabilities(REPO_ROOT)) {
  const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
  for (const skill of manifest.skills ?? []) {
    const rel = `${cap.rel}/skills/${skill.id}/SKILL.md`;
    if (!wanted(rel)) continue;
    const abs = join(REPO_ROOT, rel);
    if (!existsSync(abs)) { fail(rel, 'declared in CAPABILITY.md but missing on disk'); continue; }
    const desc = readFrontmatter(abs).data?.description;
    if (typeof desc !== 'string' || !desc.length) { fail(rel, 'no description in frontmatter'); continue; }

    if (!/\bUse when\b|\bUse BEFORE\b|\bUse for\b/.test(desc)) {
      fail(rel, 'description has no trigger clause ("Use when …") — it states what but never when');
    }
    if (!NEGATIVE_CLAUSE.test(desc)) {
      fail(rel, 'description has no negative clause ("Do NOT use" / "Does not …" / "Not for …") '
        + '— every skill in this kit competes for a trigger space');
    } else if (!siblingNamed(desc, cap)) {
      fail(rel, 'description has a negative clause but names no sibling skill — say where the '
        + 'work goes instead, or the clause discriminates nothing');
    }
    if (FIRST_OR_SECOND_PERSON.test(desc)) {
      fail(rel, `description is not third person ("${desc.match(FIRST_OR_SECOND_PERSON)[0]}") `
        + '— it is injected into the system prompt');
    }
  }
}

// A negative clause discriminates only if it points somewhere. "Somewhere" is any sibling's
// installed name, or the capability itself — computed from the manifest rather than a regex of
// known prefixes, so a new capability is covered the day it lands.
function siblingNamed(desc, cap) {
  const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
  const prefix = typeof manifest.skill_prefix === 'string' && manifest.skill_prefix.trim()
    ? manifest.skill_prefix : `${cap.id}-`;
  const names = (manifest.skills ?? [])
    .map((s) => (s.id === cap.id || String(s.id).startsWith(prefix) ? s.id : `${prefix}${s.id}`));
  // A SIBLING, not the capability itself. `cap.id` appears in most descriptions anyway, so
  // accepting it let "Does not need any configuration — kb works out of the box." pass while
  // discriminating nothing. The entry skill is the one exception: its id IS the capability id,
  // so it can only point at the narrower skills, which the filter below leaves it able to do.
  return names.filter((n) => n !== cap.id).some((n) => desc.includes(n));
}

for (const p of prefixes) {
  if (!matched.has(p)) fail(p, 'prefix matched no file — check the path');
}

if (failures.length) {
  console.error(`retired-token gate: ${failures.length} failure(s)\n`);
  for (const f of failures) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`retired-token gate: clean${prefixes.length ? ` (${prefixes.join(' ')})` : ''}`);
