#!/usr/bin/env node
// Tier-1 deterministic lint (RFC-002). Blocking: exits non-zero on any error.
// Usage: node tools/lint/aos-lint.mjs [--base <ref>] [--root <dir>]
import { resolve } from 'node:path';
import { walkRepo, listCapabilities, REPO_ROOT } from '../lib/repo.mjs';
import { checkManifests } from './checks/manifest.mjs';
import { checkSkills } from './checks/skills.mjs';
import { checkAgents } from './checks/agents.mjs';
import { checkOnboarding } from './checks/onboarding.mjs';
import { checkOverlayPaths, checkOverlaySchemas } from './checks/overlay.mjs';
import { checkReferences } from './checks/refs.mjs';
import { checkCheatsheets } from './checks/cheatsheet.mjs';
import { checkCrossPaths } from './checks/crosspath.mjs';
import { checkSecrets } from './checks/secrets.mjs';
import { checkVersionBumps } from './checks/version-bump.mjs';
import { checkStructure } from './checks/structure.mjs';

const args = process.argv.slice(2);
const base = args.includes('--base') ? args[args.indexOf('--base') + 1] : null;
// --root lints a tree other than this checkout — capability-builder points it at the
// user's personal root so a freshly built package is actually linted (not the kit).
const rootArg = args.includes('--root') ? args[args.indexOf('--root') + 1] : null;
const root = rootArg ? resolve(rootArg) : REPO_ROOT;

const findings = [];
const report = (severity, code, file, message) => findings.push({ severity, code, file, message });

const ctx = {
  root,
  files: walkRepo(root),
  caps: listCapabilities(root),
  report,
  base,
};

for (const check of [
  checkManifests, checkSkills, checkAgents, checkOnboarding,
  checkOverlayPaths, checkOverlaySchemas, checkReferences,
  checkCheatsheets, checkCrossPaths, checkSecrets, checkVersionBumps, checkStructure,
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
