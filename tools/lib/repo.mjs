import { readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const REPO_ROOT = fileURLToPath(new URL('../..', import.meta.url));

// Paths the repo-wide walks never enter. The lint selftest fixture contains
// planted violations and is linted only by its own runner.
// .aos/ is deliberately NOT skipped: a committed .aos path must be caught by
// the overlay check (in CI the tree is a clean checkout, so no local noise).
const SKIP_DIRS = new Set(['.git', 'node_modules', '.sandbox']);
const SKIP_PREFIXES = ['tools/lint/selftest/'];

export function walkRepo(root = REPO_ROOT) {
  const out = [];
  const visit = (dir) => {
    for (const name of readdirSync(dir)) {
      const abs = join(dir, name);
      const rel = relative(root, abs).split(sep).join('/');
      if (SKIP_PREFIXES.some((p) => rel.startsWith(p) || `${rel}/` === p)) continue;
      const st = statSync(abs);
      if (st.isDirectory()) {
        if (SKIP_DIRS.has(name)) continue;
        visit(abs);
      } else {
        out.push(rel);
      }
    }
  };
  visit(root);
  return out;
}

// A capability is any capabilities/<id>/ directory holding a CAPABILITY.md.
// (`capabilities/<id>.md` one-pagers are the spec docs and live alongside.)
export function listCapabilities(root = REPO_ROOT) {
  const capsDir = join(root, 'capabilities');
  if (!existsSync(capsDir)) return [];
  return readdirSync(capsDir)
    .filter((name) => {
      const dir = join(capsDir, name);
      return statSync(dir).isDirectory() && existsSync(join(dir, 'CAPABILITY.md'));
    })
    .map((id) => ({ id, dir: join(capsDir, id), rel: `capabilities/${id}` }));
}
