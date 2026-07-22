import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { CHEATSHEET_SECTIONS } from '../../lib/constants.mjs';

// ARCHITECTURE §5.2 — a cheat-sheet is a contract of content, not API: the six
// sections must exist as H2 headings.
export function checkCheatsheets({ files, report, root }) {
  for (const rel of files) {
    if (!/^harnesses\/[^/]+\/CHEATSHEET\.md$/.test(rel)) continue;
    const text = readFileSync(join(root, rel), 'utf8');
    const headings = [...text.matchAll(/^##\s+(.+?)\s*$/gm)].map((m) => m[1]);
    for (const section of CHEATSHEET_SECTIONS) {
      if (!headings.some((h) => h.toLowerCase() === section.toLowerCase())) {
        report('error', 'cheatsheet/section', rel, `missing required section "## ${section}" (ARCHITECTURE §5.2)`);
      }
    }
  }
}
