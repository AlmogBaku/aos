import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { walkRepo } from '../../lib/repo.mjs';

// Two honesty flags from ARCHITECTURE §2.1 / §5.3 — warnings, not gates.
export function checkStructure({ caps, report }) {
  for (const cap of caps) {
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
