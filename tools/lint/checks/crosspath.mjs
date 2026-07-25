import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// ARCHITECTURE §2.1/§2.5 — in-capability cross-skill references are by skill NAME,
// never by relative path: materialization renames each skill dir to its installed name,
// so an authored ../<dir>/ path breaks at runtime. Relative paths must stay inside
// the skill's own folder (the whole-folder render keeps those intact; link names
// differ from shipped dir names, so cross-skill refs go by name).
export function checkCrossPaths({ files, report, root }) {
  for (const rel of files) {
    if (!/^capabilities\/[^/]+\/skills\/[^/]+\/.*\.md$/.test(rel)) continue;
    const text = readFileSync(join(root, rel), 'utf8');
    if (/\.\.\//.test(text)) {
      report('error', 'skill/no-cross-path', rel,
        'contains a "../" reference — cross-skill references are by skill name '
        + '(materialized dirs carry the installed name, not the source id, §2.5); '
        + 'relative paths must stay inside the skill\'s own folder');
    }
  }
}
