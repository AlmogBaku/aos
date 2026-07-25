#!/usr/bin/env node
// Selftest: every lint check must fire at least once on the planted-violation
// fixture. Guards against checks silently rotting into no-ops.
import { fileURLToPath } from 'node:url';
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
  // Agent Skills authoring conformance
  'skill/reserved-word', 'skill/xml-tags', 'skill/nested-reference', 'skill/reference-toc',
  'skill/package-path',
  'agent/unknown-key', 'agent/required', 'agent/name-file', 'agent/model-class',
  'agent/tool', 'agent/workspace', 'agent/context-file',
  'onboarding/unknown-key', 'onboarding/required', 'onboarding/duplicate-id',
  'onboarding/type', 'onboarding/flag',
  'overlay/shipped', 'overlay/state-dir', 'overlay/answer-key', 'overlay/answer-missing', 'overlay/secret-ref',
  'refs/dead',
  'cheatsheet/section', 'structure/harnesses-dir',
  'secrets/token', 'secrets/jwt', 'secrets/phone', 'secrets/whatsapp-jid',
  'kb/zone-key', 'kb/owner-agent',
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
const missing = EXPECTED.filter((code) => !fired.has(code));
const unexpected = [...fired].filter((code) => !EXPECTED.includes(code) && !code.startsWith('structure/') && code !== 'skill/description-when' && code !== 'skill/name-dir' && code !== 'skill/all-main');

if (missing.length) {
  console.error(`selftest FAILED — checks that never fired on the fixture:\n  ${missing.join('\n  ')}`);
}
if (unexpected.length) {
  console.error(`selftest NOTE — codes fired that the contract does not list (add or fix):\n  ${unexpected.join('\n  ')}`);
}
console.log(`lint selftest: ${fired.size} distinct codes fired, ${missing.length} expected codes missing`);
process.exit(missing.length || unexpected.length ? 1 : 0);
