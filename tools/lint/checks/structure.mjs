import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { walkRepo } from '../../lib/repo.mjs';

// Two honesty flags from ARCHITECTURE §2.1 / §5.3 — warnings, not gates —
// plus the §2.5 entry-skill convention.
export function checkStructure({ caps, report }) {
  for (const cap of caps) {
    // §2.1: there is no capability-level harnesses/ dir. Cheat-sheets are reference files
    // of the skill that reads them (so they travel with the render and resolve from an
    // installed skill); other per-harness content is adapters/<harness>/.
    if (existsSync(join(cap.dir, 'harnesses'))) {
      report('error', 'structure/harnesses-dir', cap.rel,
        'no capability-level harnesses/ dir (§2.1) — a cheat-sheet belongs in the consuming skill\'s reference/ as harness-<runtime>.md, and other per-harness content in adapters/<harness>/');
    }
    // §2.5: every capability ships an entry skill named after itself.
    const entry = join(cap.dir, 'skills', cap.id, 'SKILL.md');
    if (!existsSync(entry)) {
      report('error', 'structure/entry-skill', cap.rel,
        `no skills/${cap.id}/SKILL.md — the §2.5 entry skill is required`);
    }
    const readme = join(cap.dir, 'README.md');
    if (existsSync(readme) && !/\|/.test(readFileSync(readme, 'utf8'))) {
      report('warn', 'structure/support-matrix', `${cap.rel}/README.md`, 'no table found — the support matrix lives here (§2.4)');
    }
    const adaptersDir = join(cap.dir, 'adapters');
    if (!existsSync(adaptersDir)) continue;
    const size = (dir) =>
      walkRepo(dir).reduce((sum, rel) => sum + statSync(join(dir, rel)).size, 0);
    const adapterBytes = size(adaptersDir);
    const totalBytes = size(cap.dir);
    if (adapterBytes > (totalBytes - adapterBytes)) {
      report('warn', 'structure/adapter-ratio', cap.rel, `adapters/ (${adapterBytes}B) outweighs the neutral core — is this capability actually portable? (§2.1)`);
    }
  }
}
