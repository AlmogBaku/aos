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

    // The same failure without a "../": a path into the capability *package*. Only the
    // skill's own folder travels, so `harnesses/hermes.md` or `tool/README.md` resolves
    // in the source tree and nowhere else — the agent goes hunting, which is exactly
    // what a shipped skill must never make it do. Package-level knowledge belongs in a
    // reference/ file of the skill that reads it; package-level *paths* are written from
    // a household root (`<home>/upstream/…`), which does resolve at runtime.
    for (const m of text.matchAll(PACKAGE_PATH)) {
      report('error', 'skill/package-path', rel,
        `references "${m[1]}" — that path exists only in the source package, not beside `
        + 'an installed skill. Put the content in this skill\'s reference/, name the skill '
        + 'that owns it, or write the path from a household root (<home>/upstream/…)');
    }
  }
}

// A bare relative path (no scheme, no anchor, not rooted at a household dir) whose first
// segment is a capability-package directory. Deliberately narrow: `_ops/…` and `state/…`
// are paths inside a user's KB, and `<id>-draft/agents/…` is a draft the skill writes —
// neither is a load target in the source tree.
const PACKAGE_PATH = /(?:\]\(|`)((?:harnesses|adapters|tool|capabilities)\/[A-Za-z0-9_<>./-]*\.(?:md|ya?ml))/g;
