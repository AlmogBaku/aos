import { existsSync, readFileSync } from 'node:fs';
import { join, dirname, resolve, sep } from 'node:path';
import { readFrontmatter, stripCodeFences } from '../../lib/frontmatter.mjs';

const LINK_RE = /\[[^\]]*\]\(([^)\s]+)\)/g;

// Every relative markdown link in the repo must resolve — the reading order,
// capability cross-links, and design exhibits are all load-bearing.
export function checkReferences({ files, report, root }) {
  for (const rel of files) {
    if (!rel.endsWith('.md')) continue;
    const abs = join(root, rel);
    const { body } = readFrontmatter(abs);
    const text = stripCodeFences(body ?? readFileSync(abs, 'utf8'));
    for (const match of text.matchAll(LINK_RE)) {
      let target = match[1];
      if (/^(https?:|mailto:|#)/.test(target)) continue;
      target = target.split('#')[0];
      if (!target) continue;
      const resolved = resolve(dirname(abs), decodeURI(target));
      if (!resolved.startsWith(root.replace(/[\\/]+$/, '') + sep)) {
        report('error', 'refs/escape', rel, `link "${match[1]}" points outside the repo`);
      } else if (!existsSync(resolved)) {
        report('error', 'refs/dead', rel, `link "${match[1]}" does not resolve`);
      }
    }
  }
}
