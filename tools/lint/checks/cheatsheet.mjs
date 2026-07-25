import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { CHEATSHEET_SECTIONS } from '../../lib/constants.mjs';

// ARCHITECTURE §5.2 — a cheat-sheet is a contract of content, not API: the six
// sections must exist as H2 headings. A cheat-sheet is a reference file of the skill
// that consumes it — `skills/<entry>/reference/harness-<harness-runtime>.md` — so it
// travels with the render and resolves from an installed skill. The old capability-level
// `harnesses/<runtime>.md` shape did neither: nothing beside an installed skill has a
// `harnesses/` sibling, so a skill telling the agent to load one sent it hunting.
export function checkCheatsheets({ files, report, root }) {
  for (const rel of files) {
    const inReference = /\/reference\/harness-[^/]+\.md$/.test(rel);
    const legacy = /^(?:capabilities\/[^/]+\/)?harnesses\/(?!README\.md$)[^/]+\.md$/.test(rel);
    if (!inReference && !legacy) continue;
    const text = readFileSync(join(root, rel), 'utf8');
    const headings = [...text.matchAll(/^##\s+(.+?)\s*$/gm)].map((m) => m[1]);
    for (const section of CHEATSHEET_SECTIONS) {
      if (!headings.some((h) => h.toLowerCase() === section.toLowerCase())) {
        report('error', 'cheatsheet/section', rel, `missing required section "## ${section}" (ARCHITECTURE §5.2)`);
      }
    }
  }
}
