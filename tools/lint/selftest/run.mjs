#!/usr/bin/env node
// Selftest: every lint check must fire at least once on the planted-violation
// fixture. Guards against checks silently rotting into no-ops.
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { walkRepo, listCapabilities } from '../../lib/repo.mjs';
import { checkManifests } from '../checks/manifest.mjs';
import { checkSkills } from '../checks/skills.mjs';
import { checkSkillNames } from '../checks/skill-names.mjs';
import { checkAgents } from '../checks/agents.mjs';
import { checkOnboarding } from '../checks/onboarding.mjs';
import { checkOverlayPaths, checkOverlaySchemas } from '../checks/overlay.mjs';
import { checkReferences } from '../checks/refs.mjs';
import { checkCheatsheets } from '../checks/cheatsheet.mjs';
import { checkCrossPaths } from '../checks/crosspath.mjs';
import { checkSecrets } from '../checks/secrets.mjs';
import { checkStructure } from '../checks/structure.mjs';

const ROOT = fileURLToPath(new URL('./fixture', import.meta.url));

const EXPECTED = [
  'manifest/unknown-key', 'manifest/id', 'manifest/version', 'manifest/tags',
  'manifest/summary', 'manifest/readme', 'manifest/mod-example',
  'depends/capability', 'depends/host-feature', 'depends/host-level',
  'schedules/unknown-key', 'schedules/id', 'schedules/cron', 'schedules/agent',
  'schedules/prompt-ref', 'schedules/degraded',
  'skills/unknown-key', 'skills/missing-dir', 'skills/undeclared',
  'skill/no-cross-path',
  'skill/origin-tag', 'skill/unknown-key', 'skill/name', 'skill/description',
  'skill/used-by', 'skill/used-by-ref',
  // §2.5 skill identity: the installed name is what ships, so it carries the limits
  'skills/prefix-format', 'skills/prefix-redundant', 'skills/installed-name',
  'skills/installed-collision', 'skills/ref-unqualified',
  // ...and its mirror: the computed name written literally, plus a slot that resolves to
  // nothing. Both are what a prefix rename silently invalidated with green CI.
  'skills/ref-hardcoded', 'skills/ref-dangling', 'agents/ref-dangling',
  // Agent Skills authoring conformance
  'skill/reserved-word', 'skill/xml-tags', 'skill/nested-reference', 'skill/reference-toc',
  'skill/description-person',
  'skill/package-path', 'skill/foreign-reference',
  'agent/unknown-key', 'agent/required', 'agent/name-file', 'agent/model-class',
  'agent/tool', 'agent/workspace', 'agent/context-file',
  'onboarding/unknown-key', 'onboarding/required', 'onboarding/duplicate-id',
  'onboarding/type', 'onboarding/flag',
  'overlay/shipped', 'overlay/state-dir', 'overlay/answer-key', 'overlay/answer-missing', 'overlay/secret-ref',
  'refs/dead',
  'cheatsheet/section', 'structure/harnesses-dir',
  'secrets/token', 'secrets/jwt', 'secrets/phone', 'secrets/whatsapp-jid',
  'kb/zone-key', 'kb/owner-agent',
  // §2.2's degenerate case, and it is EXPECTED rather than tolerated: the check only fires
  // where an alternative existed (an agent or a schedule to scope to), so nothing else in
  // this fixture can plant it — prefix-cap carries a `janitor` agent for exactly this.
  'skill/all-main',
];

const findings = [];
const report = (severity, code, file, message) => findings.push({ severity, code, file, message });
const ctx = { root: ROOT, files: walkRepo(ROOT), caps: listCapabilities(ROOT), report, base: null };

for (const check of [
  checkManifests, checkSkills, checkSkillNames, checkAgents, checkOnboarding,
  checkOverlayPaths, checkOverlaySchemas, checkReferences,
  checkCheatsheets, checkCrossPaths, checkSecrets, checkStructure,
]) {
  check(ctx);
}

const fired = new Set(findings.map((f) => f.code));
// the cheat-sheet section check must fire on the sanctioned shape (a reference file of the
// skill that reads it) AND on the retired capability-level layout, which must not go
// silently unchecked while it still exists in the wild
const cheatFiles = new Set(findings.filter((f) => f.code === 'cheatsheet/section').map((f) => f.file));
for (const want of ['harnesses/badharness.md', 'skills/capture/reference/harness-badharness.md', 'capabilities/half-cap/harnesses/stale.md']) {
  if (![...cheatFiles].some((f) => f.endsWith(want))) {
    console.error(`selftest FAILED — cheatsheet/section did not fire on ${want}`);
    process.exit(1);
  }
}
// skill/all-main must fire where a role EXISTED to scope to and was ignored, and must stay
// silent where there was never an alternative. Both halves are pinned by file, because the
// code firing at all proves nothing: `name-cap` is five main-only skills with no agents, so a
// check that ignored the role question entirely would still light this code up.
const allMainFiles = new Set(findings.filter((f) => f.code === 'skill/all-main').map((f) => f.file));
if (![...allMainFiles].some((f) => f.includes('prefix-cap'))) {
  console.error('selftest FAILED — skill/all-main did not fire on prefix-cap, which scopes '
    + 'every skill to main while declaring a `janitor` agent');
  process.exit(1);
}
for (const quiet of ['name-cap', 'half-cap']) {
  if ([...allMainFiles].some((f) => f.includes(quiet))) {
    console.error(`selftest FAILED — skill/all-main fired on ${quiet}, which declares no agent `
      + 'and no schedule: there was no role to scope to, so the question is unanswerable '
      + 'rather than unanswered');
    process.exit(1);
  }
}

// The slot checks must fire on a dangling slot and stay SILENT on an escaped one. Pinned by
// line, because the codes firing at all proves nothing: the same fixture line carries both
// forms, so a check that ignored the `(?<!\\)` guard would light the codes up identically
// while failing every doc that TEACHES the syntax — starting with reference/naming.md. The
// line is located by content rather than numbered, so editing the fixture cannot quietly
// aim this assertion at a blank line.
const REFER_REL = 'capabilities/name-cap/skills/refer/SKILL.md';
const referLines = readFileSync(join(ROOT, REFER_REL), 'utf8').split('\n');
const escapedLine = referLines.findIndex((l) => l.includes('escaped example')) + 1;
if (!escapedLine) {
  console.error(`selftest FAILED — ${REFER_REL} no longer carries the escaped-slot line the `
    + 'negative assertion is about');
  process.exit(1);
}
const slotFindings = findings.filter((f) => f.code.endsWith('/ref-dangling'));
const onEscaped = slotFindings.filter((f) => f.file === `${REFER_REL}:${escapedLine}`);
if (onEscaped.length) {
  console.error(`selftest FAILED — ${onEscaped.length} ref-dangling finding(s) on ${REFER_REL}:`
    + `${escapedLine}, the escaped-slot line: \\{{skill: …}} is invisible to render, so it must `
    + `be invisible to lint too\n  ${onEscaped.map((f) => f.message).join('\n  ')}`);
  process.exit(1);
}
for (const [code, want] of [['skills/ref-dangling', '{{skill: kapture}}'],
  ['agents/ref-dangling', '{{agent: ghost}}']]) {
  if (!slotFindings.some((f) => f.code === code && f.message.includes(want))) {
    console.error(`selftest FAILED — ${code} did not fire on the unescaped ${want}`);
    process.exit(1);
  }
}

const missing = EXPECTED.filter((code) => !fired.has(code));
const unexpected = [...fired].filter((code) => !EXPECTED.includes(code) && !code.startsWith('structure/') && code !== 'skill/description-when' && code !== 'skill/name-dir');

if (missing.length) {
  console.error(`selftest FAILED — checks that never fired on the fixture:\n  ${missing.join('\n  ')}`);
}
if (unexpected.length) {
  console.error(`selftest NOTE — codes fired that the contract does not list (add or fix):\n  ${unexpected.join('\n  ')}`);
}
console.log(`lint selftest: ${fired.size} distinct codes fired, ${missing.length} expected codes missing`);
process.exit(missing.length || unexpected.length ? 1 : 0);
