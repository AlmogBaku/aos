import { join } from 'node:path';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { ORIGIN_FRONTMATTER_KEY, MAIN_AGENT } from '../../lib/constants.mjs';
import { agentNames } from './agents.mjs';

// Agent Skills spec (agentskills.io/specification) — the portable core every
// skills/<id>/ folder must satisfy standalone (ARCHITECTURE §2.1 normative).
const SKILL_KEYS = ['name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'];
const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export function checkSkills({ caps, files, report }) {
  for (const cap of caps) {
    const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
    const declared = new Map((manifest.skills ?? []).map((s) => [s.id, s]));
    const agents = agentNames(cap);

    // Every SKILL.md in the capability must be a valid Agent Skills folder —
    // including methodology-shipped ones outside skills/ (those aren't in the
    // manifest bijection; the methodology contract carries them).
    const skillFiles = files.filter((f) => f.startsWith(`${cap.rel}/`) && f.endsWith('/SKILL.md'));
    for (const file of skillFiles) {
      const parts = file.split('/');
      const id = parts[parts.length - 2];
      const inSkillsDir = parts[2] === 'skills' && parts.length === 5;
      const path = join(cap.dir, ...parts.slice(2));
      const { data, body, error } = readFrontmatter(path);
      if (error || !data) {
        report('error', 'skill/parse', file, error ? error.message : 'missing frontmatter');
        continue;
      }

      // Strict-portable profile: shipped skills carry only spec fields. Harness-
      // specific extension goes in metadata.<harness>.* per the spec's own escape hatch.
      for (const key of Object.keys(data)) {
        if (key === ORIGIN_FRONTMATTER_KEY) {
          report('error', 'skill/origin-tag', file, `${ORIGIN_FRONTMATTER_KEY} is an install-time tag — never shipped upstream`);
        } else if (!SKILL_KEYS.includes(key)) {
          report('error', 'skill/unknown-key', file, `"${key}" is not an Agent Skills spec field (allowed: ${SKILL_KEYS.join(', ')})`);
        }
      }
      const name = data.name;
      if (typeof name !== 'string' || !name.length || name.length > 64 || !NAME_RE.test(name)) {
        report('error', 'skill/name', file, `name must be 1–64 chars of [a-z0-9-], no leading/trailing/double hyphens`);
      } else if (name !== id) {
        report('error', 'skill/name-dir', file, `name "${name}" must equal directory name "${id}"`);
      }
      const desc = data.description;
      if (typeof desc !== 'string' || !desc.trim().length || desc.length > 1024) {
        report('error', 'skill/description', file, 'description is required, 1–1024 chars');
      } else if (!/\bwhen\b/i.test(desc)) {
        report('warn', 'skill/description-when', file, 'description should say when to use the skill (trigger phrasing)');
      }
      if (body.split('\n').length > 500) {
        report('warn', 'skill/body-length', file, 'SKILL.md body exceeds 500 lines — split into sections/ (progressive disclosure)');
      }

      // used_by scoping (ARCHITECTURE §2.2, normative — the anti-pollution rule).
      // Only skills/<id>/ entries participate in the manifest bijection.
      const entry = inSkillsDir ? declared.get(id) : null;
      if (entry) {
        const usedBy = entry.used_by;
        if (!Array.isArray(usedBy) || !usedBy.length) {
          report('error', 'skill/used-by', `${cap.rel}/CAPABILITY.md`, `skill "${id}" must declare a non-empty used_by list`);
        } else {
          for (const u of usedBy) {
            if (u !== MAIN_AGENT && !agents.includes(u)) {
              report('error', 'skill/used-by-ref', `${cap.rel}/CAPABILITY.md`, `skill "${id}" used_by "${u}" is neither "${MAIN_AGENT}" nor a declared agent`);
            }
          }
        }
      }
    }

    // §2.2: a multi-skill capability scoping everything to main is the degenerate
    // case the linter questions.
    const allUsedBy = [...declared.values()].flatMap((s) => s.used_by ?? []);
    if (declared.size > 1 && allUsedBy.length && allUsedBy.every((u) => u === MAIN_AGENT)) {
      report('warn', 'skill/all-main', `${cap.rel}/CAPABILITY.md`, 'every skill is scoped to main — is that deliberate? (§2.2)');
    }
  }
}
