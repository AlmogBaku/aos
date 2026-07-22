import { execFileSync } from 'node:child_process';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { join } from 'node:path';
import { REPO_ROOT } from '../../lib/repo.mjs';

// design/install-flow.md §3: upgrades key off version; CI requires a bump when
// a capability's files change. Diff-aware — runs only with --base.
export function checkVersionBumps({ caps, report, base }) {
  if (!base) return;
  let changed;
  try {
    changed = execFileSync('git', ['diff', '--name-only', `${base}...HEAD`], { cwd: REPO_ROOT, encoding: 'utf8' })
      .split('\n').filter(Boolean);
  } catch {
    report('warn', 'version/base', '.', `cannot diff against "${base}" — skipping version-bump check`);
    return;
  }
  for (const cap of caps) {
    const touched = changed.filter((f) => f.startsWith(`${cap.rel}/`));
    if (!touched.length) continue;
    const current = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data?.version;
    let previous = null;
    try {
      const old = execFileSync('git', ['show', `${base}:${cap.rel}/CAPABILITY.md`], { cwd: REPO_ROOT, encoding: 'utf8' });
      previous = /^version:\s*["']?([\d.]+)/m.exec(old.split('\n---')[0])?.[1] ?? null;
    } catch {
      continue; // capability is new in this diff — no bump needed
    }
    if (previous && current === previous) {
      report('error', 'version/bump', `${cap.rel}/CAPABILITY.md`, `files changed vs ${base} but version stayed ${current} (install-flow §3)`);
    }
  }
}
