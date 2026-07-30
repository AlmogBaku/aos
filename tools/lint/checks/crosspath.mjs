import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// ARCHITECTURE §2.1/§2.5 — in-capability cross-skill references are by skill NAME,
// never by relative path: materialization renames each skill dir to its installed name,
// so an authored ../<dir>/ path breaks at runtime. Relative paths must stay inside
// the skill's own folder (the whole-folder render keeps those intact; link names
// differ from shipped dir names, so cross-skill refs go by name).
export function checkCrossPaths(ctx) {
  const { files, report, root } = ctx;
  checkOwnReferences(ctx);
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

// The same failure from the other side: a bare `reference/<file>` that lives in a
// DIFFERENT skill's reference dir. It reads as this skill's own depth, resolves to
// nothing, and the agent goes looking. Naming the owning skill is the fix — the agent
// loads that skill, and the path resolves inside it.
function checkOwnReferences({ files, report, root }) {
  const skillDirs = new Set(files
    .filter((f) => /^capabilities\/[^/]+\/skills\/[^/]+\/SKILL\.md$/.test(f))
    .map((f) => f.slice(0, f.lastIndexOf('/'))));
  const have = new Set(files.filter((f) => f.includes('/reference/')));
  for (const rel of files) {
    if (!/^capabilities\/[^/]+\/skills\/[^/]+\/.*\.md$/.test(rel)) continue;
    const parts = rel.split('/');
    const skillDir = parts.slice(0, 4).join('/');
    if (!skillDirs.has(skillDir)) continue;
    // Skill names in this capability — a reference attributed to one of them is fine:
    // the agent loads that skill, and the path resolves inside it.
    const siblings = [...skillDirs]
      .filter((d) => d.startsWith(parts.slice(0, 3).join('/')))
      .map((d) => d.split('/').pop());
    const lines = readFileSync(join(root, rel), 'utf8').split('\n');
    const seen = new Set();
    lines.forEach((line, i) => {
      // The enclosing prose, not just this line: a numbered step wraps over several
      // lines, and attribution at its head still tells the agent where to look.
      const context = lines.slice(Math.max(0, i - 3), i + 1).join('\n');
      const attributed = /\bskill\b/i.test(context)
        || siblings.some((s) => context.includes(`\`${s}\``));
      for (const m of line.matchAll(/(?:\]\(|`)(reference\/[A-Za-z0-9_-]+\.md)/g)) {
        if (have.has(`${skillDir}/${m[1]}`) || attributed || seen.has(m[1])) continue;
        seen.add(m[1]);
        report('error', 'skill/foreign-reference', `${rel}:${i + 1}`,
          `names "${m[1]}", which is not in this skill's own reference/ and is not `
          + 'attributed — say which skill owns it ("the `<skill>` skill\'s `'
          + m[1] + '`"), so the agent loads that skill and the path resolves inside it');
      }
    });
  }
}

// A bare relative path (no scheme, no anchor, not rooted at a household dir) whose first
// segment is a capability-package directory. Deliberately narrow: `.kb/pending/…` and
// `_raw/…` are paths inside a user's KB, and `<id>-draft/agents/…` is a draft the skill
// writes — neither is a load target in the source tree.
const PACKAGE_PATH = /(?:\]\(|`)((?:harnesses|adapters|tool|capabilities)\/[A-Za-z0-9_<>./-]*\.(?:md|ya?ml))/g;
