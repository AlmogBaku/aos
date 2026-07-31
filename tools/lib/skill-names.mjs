// The installed name is a skill's shipped identity (ARCHITECTURE §2.5): the only name a
// harness ever sees, and the one that must be globally unique. Authors write short,
// capability-local ids; this computes what they become.
//
// Mirrored in capabilities/capability-lifecycle/tool/src/aos_cap/cli.py — the runtime
// half, which agents call at install time. The two must agree; the goldens are the tie-break.
import { readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { SKILL_PREFIX_RE, SKILL_NAME_RE, SKILL_NAME_MAX, RESERVED_NAME_WORDS } from './constants.mjs';
import { readFrontmatter } from './frontmatter.mjs';

// §2.2: absent or empty means "default to the capability id".
export function effectivePrefix(manifest, capId) {
  const declared = manifest?.skill_prefix;
  return typeof declared === 'string' && declared.trim() ? declared : `${capId}-`;
}

export function isPrefixWellFormed(prefix) {
  return typeof prefix === 'string' && SKILL_PREFIX_RE.test(prefix);
}

// The entry skill ships verbatim; nothing is ever prefixed twice.
export function installedName(capId, prefix, skillId) {
  if (skillId === capId || skillId.startsWith(prefix)) return skillId;
  return `${prefix}${skillId}`;
}

// Agent Skills spec limits, applied to the *installed* name — that is what ships.
export function nameProblems(name) {
  const out = [];
  if (name.length > SKILL_NAME_MAX) out.push(`is ${name.length} chars (max ${SKILL_NAME_MAX})`);
  if (!SKILL_NAME_RE.test(name)) out.push('must be [a-z0-9-] with no leading/trailing/double hyphens');
  for (const word of RESERVED_NAME_WORDS) {
    if (name.includes(word)) out.push(`contains the reserved word "${word}"`);
  }
  return out;
}

// Every installed name a capability would claim: declared entries plus any on-disk skill
// dir (an undeclared dir is its own error, but it would still land if installed).
export function capabilitySkillNames(cap) {
  const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
  const prefix = effectivePrefix(manifest, cap.id);
  const ids = new Set((manifest.skills ?? []).map((s) => s?.id).filter((i) => typeof i === 'string'));
  const skillsDir = join(cap.dir, 'skills');
  if (existsSync(skillsDir)) {
    for (const name of readdirSync(skillsDir)) {
      if (existsSync(join(skillsDir, name, 'SKILL.md'))) ids.add(name);
    }
  }
  return new Map([...ids].map((id) => [installedName(cap.id, prefix, id), id]));
}
