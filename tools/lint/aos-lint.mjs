#!/usr/bin/env node
// Tier-1 deterministic lint (RFC-002). Blocking: exits non-zero on any error.
// Usage: node tools/lint/aos-lint.mjs [--base <ref>] [--root <dir>]
import { walkRepo, listCapabilities, REPO_ROOT } from '../lib/repo.mjs';
import { checkManifests } from './checks/manifest.mjs';
import { checkSkills } from './checks/skills.mjs';
import { checkAgents } from './checks/agents.mjs';
import { checkOnboarding } from './checks/onboarding.mjs';
import { checkOverlayPaths, checkOverlaySchemas } from './checks/overlay.mjs';
import { checkReferences } from './checks/refs.mjs';
import { checkCheatsheets } from './checks/cheatsheet.mjs';
import { checkSecrets } from './checks/secrets.mjs';
import { checkVersionBumps } from './checks/version-bump.mjs';
import { checkStructure } from './checks/structure.mjs';

const args = process.argv.slice(2);
const base = args.includes('--base') ? args[args.indexOf('--base') + 1] : null;

const findings = [];
const report = (severity, code, file, message) => findings.push({ severity, code, file, message });

const ctx = {
  root: REPO_ROOT,
  files: walkRepo(),
  caps: listCapabilities(),
  report,
  base,
};

for (const check of [
  checkManifests, checkSkills, checkAgents, checkOnboarding,
  checkOverlayPaths, checkOverlaySchemas, checkReferences,
  checkCheatsheets, checkSecrets, checkVersionBumps, checkStructure,
]) {
  try {
    check(ctx);
  } catch (e) {
    report('error', 'lint/crash', check.name, e.stack ?? String(e));
  }
}

findings.sort((a, b) => a.file.localeCompare(b.file) || a.code.localeCompare(b.code));
for (const f of findings) {
  console.log(`${f.severity === 'error' ? 'ERROR' : 'WARN '} ${f.code.padEnd(24)} ${f.file}: ${f.message}`);
}
const errors = findings.filter((f) => f.severity === 'error').length;
const warns = findings.length - errors;
console.log(`\naos-lint: ${ctx.caps.length} capabilities, ${errors} errors, ${warns} warnings`);
process.exit(errors ? 1 : 0);
