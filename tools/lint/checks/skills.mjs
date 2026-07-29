import { join } from 'node:path';
import { readFileSync } from 'node:fs';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import {
  ORIGIN_FRONTMATTER_KEY, ORIGIN_FRONTMATTER_PATH, LEGACY_ORIGIN_FRONTMATTER_KEY,
  MAIN_AGENT, SKILL_NAME_RE, SKILL_NAME_MAX,
  RESERVED_NAME_WORDS, REFERENCE_TOC_LINES,
} from '../../lib/constants.mjs';
import { agentNames } from './agents.mjs';

// Agent Skills spec (agentskills.io/specification) — the portable core every
// skills/<id>/ folder must satisfy standalone (ARCHITECTURE §2.1 normative).
const SKILL_KEYS = ['name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'];
const NAME_RE = SKILL_NAME_RE;
// The spec forbids XML tags in name/description: both are injected into the system prompt,
// where an angle-bracket token reads as markup. Placeholders belong in the body.
const XML_TAG_RE = /<[^\s>]+>/;

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
        if (key === LEGACY_ORIGIN_FRONTMATTER_KEY) {
          report('error', 'skill/origin-tag', file, `${LEGACY_ORIGIN_FRONTMATTER_KEY} is retired — the stamp is ${ORIGIN_FRONTMATTER_KEY}, and it is an install-time tag never shipped upstream`);
        } else if (!SKILL_KEYS.includes(key)) {
          report('error', 'skill/unknown-key', file, `"${key}" is not an Agent Skills spec field (allowed: ${SKILL_KEYS.join(', ')})`);
        }
      }
      // The stamp moved inside `metadata`, so rejecting the old top-level key is no longer
      // enough — an upstream skill carrying metadata.aos.origin is the same defect wearing
      // the new spelling, and a check that only knew the old one would pass it silently.
      if (readOrigin(data) !== undefined) {
        report('error', 'skill/origin-tag', file, `${ORIGIN_FRONTMATTER_KEY} is an install-time tag — never shipped upstream`);
      }
      const name = data.name;
      if (typeof name !== 'string' || !name.length || name.length > SKILL_NAME_MAX || !NAME_RE.test(name)) {
        report('error', 'skill/name', file, `name must be 1–${SKILL_NAME_MAX} chars of [a-z0-9-], no leading/trailing/double hyphens`);
      } else if (name !== id) {
        report('error', 'skill/name-dir', file, `name "${name}" must equal directory name "${id}"`);
      }
      if (typeof name === 'string') {
        for (const word of RESERVED_NAME_WORDS) {
          if (name.includes(word)) {
            report('error', 'skill/reserved-word', file, `name "${name}" contains the reserved word "${word}" (Agent Skills spec)`);
          }
        }
      }
      const desc = data.description;
      if (typeof desc !== 'string' || !desc.trim().length || desc.length > 1024) {
        report('error', 'skill/description', file, 'description is required, 1–1024 chars');
      } else if (!/\bwhen\b/i.test(desc)) {
        report('warn', 'skill/description-when', file, 'description should say when to use the skill (trigger phrasing)');
      }
      // A description is injected into the system prompt to choose among a hundred skills, so
      // its point of view is load-bearing: the authoring guide calls first/second person a
      // discovery problem, not a style preference. Every shipped skill already passes, which is
      // why this is an error rather than a warning — it guards a property we have, instead of
      // reporting one we lack. The review skill's reference/skill-rubric.md carries the
      // judgment half of description quality, which no regex can reach.
      if (typeof desc === 'string') {
        const pov = desc.match(
          /\b(?:I can|I will|I help|I'll|helps? you|lets you|allows you|enables you|you can|you should|use this (?:to|when|for))\b/i);
        if (pov) {
          report('error', 'skill/description-person', file,
            `description says "${pov[0]}" — write it in third person ("Records a thought…", `
            + `not "I can help you…" or "Use this to…"); it is injected into the system prompt`);
        }
      }
      for (const [field, value] of [['name', name], ['description', desc]]) {
        if (typeof value === 'string' && XML_TAG_RE.test(value)) {
          report('error', 'skill/xml-tags', file,
            `${field} contains "${value.match(XML_TAG_RE)[0]}" — no XML tags in frontmatter (it is injected into the system prompt); use a plain placeholder or move the example into the body`);
        }
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

    checkReferenceDepth(cap, files, report);

    // §2.2: a multi-skill capability scoping everything to main is the degenerate case the
    // linter questions — but only where an alternative EXISTED. A capability with no agents
    // and no schedules has no role to scope to, so "is that deliberate?" is unanswerable
    // rather than unanswered, and a warning nobody can act on is one people learn to ignore.
    // (capability-lifecycle is the case: install/upgrade/remove are all things the user asks
    // the front agent.) A capability that LATER declares an agent and forgets to scope a
    // skill to it fires this again, which is the signal worth keeping.
    const hasRoles = agents.length > 0 || (manifest.schedules ?? []).length > 0;
    const allUsedBy = [...declared.values()].flatMap((s) => s.used_by ?? []);
    if (hasRoles && declared.size > 1 && allUsedBy.length && allUsedBy.every((u) => u === MAIN_AGENT)) {
      report('warn', 'skill/all-main', `${cap.rel}/CAPABILITY.md`, 'every skill is scoped to main — is that deliberate? (§2.2)');
    }
  }
}

// The stamp, read as structured data at whatever depth the spec hatch puts it.
function readOrigin(data) {
  let node = data;
  for (const key of ORIGIN_FRONTMATTER_PATH) {
    if (node === null || typeof node !== 'object' || !(key in node)) return undefined;
    node = node[key];
  }
  return node;
}

// Progressive disclosure, per the Agent Skills authoring guide: every reference file hangs
// directly off SKILL.md. A file reached *through* another one gets partially read (the
// agent previews with head -100 rather than reading it whole), so a chain silently
// truncates. And past ~100 lines a preview no longer shows the file's scope — hence the
// Contents block.
function checkReferenceDepth(cap, files, report) {
  const refs = files.filter((f) => f.startsWith(`${cap.rel}/`)
    && f.endsWith('.md') && f.split('/').includes('reference'));
  for (const file of refs) {
    const dir = file.slice(0, file.lastIndexOf('/'));
    const siblings = new Set(refs.filter((f) => f.startsWith(`${dir}/`))
      .map((f) => f.slice(dir.length + 1)));
    let text;
    try {
      text = readFileSync(join(cap.dir, ...file.split('/').slice(2)), 'utf8');
    } catch {
      continue;
    }
    // Two forms, because authors write both and the truncation is identical: a markdown link
    // `](deep.md)`, and a backticked path `` `reference/deep.md` `` — which is in fact the
    // commoner shape in this kit. Matching only the link form left the majority invisible.
    // The basename is compared, so `reference/x.md` and `./x.md` and `x.md` all resolve to the
    // same sibling; a file naming ITSELF is not a violation, and neither is a path into a
    // different skill's reference/ (that is skill/no-cross-path's job).
    const self = file.slice(dir.length + 1);
    const NESTED_RE = /]\((?:\.\/)?([a-z0-9._/-]+\.md)(?:#[^)]*)?\)|`(?:\.\/)?([a-z0-9._/-]+\.md)`/gi;
    for (const m of text.matchAll(NESTED_RE)) {
      const target = (m[1] ?? m[2]).split('/').pop();
      if (target !== self && siblings.has(target)) {
        report('error', 'skill/nested-reference', file,
          `references the sibling "${target}" — every reference file must hang directly off SKILL.md, or it gets read only in part (name the SKILL instead, and let it link both)`);
      }
    }
    const lines = text.split('\n');
    if (lines.length > REFERENCE_TOC_LINES
        && !lines.slice(0, 15).some((l) => /^#{1,3}\s*contents\b/i.test(l))) {
      report('warn', 'skill/reference-toc', file,
        `${lines.length} lines with no "## Contents" block — a partial read must still show the file's scope`);
    }
  }
}
