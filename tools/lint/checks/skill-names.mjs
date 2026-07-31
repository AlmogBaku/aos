import { join } from 'node:path';
import { readFileSync } from 'node:fs';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { listCapabilities } from '../../lib/repo.mjs';
import {
  effectivePrefix, installedName, isPrefixWellFormed, nameProblems, capabilitySkillNames,
} from '../../lib/skill-names.mjs';

// The only cross-capability check in the suite. Skills land in one flat namespace per
// harness, so two capabilities computing the same installed name is a silent override —
// the same hazard §5.5's single-owner rule closes for schedules. Everything here works
// off ctx.caps, never ctx.files: the golden snapshots contain dozens of rendered
// SKILL.md copies that are not shipped skills.
export function checkSkillNames({ caps, files, root, depRoots = [], report }) {
  // A personal capability must be unique against the kit too (capability-builder's
  // post-build gate lints the personal root with the kit as a depRoot).
  const foreign = new Map();
  for (const depRoot of depRoots) {
    for (const cap of listCapabilities(depRoot)) {
      for (const [name] of capabilitySkillNames(cap)) {
        foreign.set(name, `capability "${cap.id}" in ${depRoot}`);
      }
    }
  }

  const claimed = new Map();
  for (const cap of caps) {
    const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
    const declared = manifest.skill_prefix;
    if (declared !== undefined && declared !== null
        && !(typeof declared === 'string' && !declared.trim())
        && !isPrefixWellFormed(declared)) {
      report('error', 'skills/prefix-format', `${cap.rel}/CAPABILITY.md`,
        `skill_prefix "${declared}" must be [a-z0-9-] ending in a hyphen (e.g. "capability-"); omit it to default to "${cap.id}-"`);
    }
    const prefix = effectivePrefix(manifest, cap.id);

    for (const entry of manifest.skills ?? []) {
      const id = entry?.id;
      if (typeof id !== 'string' || !id) continue;   // manifest.mjs owns shape errors
      const name = installedName(cap.id, prefix, id);
      const where = `${cap.rel}/skills/${id}/SKILL.md`;

      // Authors write bare, capability-local ids: the prefix is applied once, by the tool.
      if (id !== cap.id && id.startsWith(prefix)) {
        report('error', 'skills/prefix-redundant', where,
          `id "${id}" already carries the prefix "${prefix}" — ship the bare id ("${id.slice(prefix.length)}"); the installed name is computed (§2.5)`);
      }
      for (const problem of nameProblems(name)) {
        report('error', 'skills/installed-name', where,
          `installed name "${name}" ${problem}`);
      }
      const owner = claimed.get(name) ?? foreign.get(name);
      if (owner) {
        report('error', 'skills/installed-collision', where,
          `installed name "${name}" is already claimed by ${owner} — one flat namespace per harness, so this would silently override`);
      } else {
        claimed.set(name, `${cap.id}:${id}`);
      }
    }
  }

  checkQualifiedRefs(caps, files, root, report);
}

// Cross-skill references resolve by name at runtime (crosspath.mjs bans relative paths),
// and the name a harness knows is the installed one. A bare sibling id in shipped prose
// points at nothing once installed. Scoped to "`<id>` skill" / "the `<id>` skill" so it
// never fires on a tool verb — `kb capture`, `kb import survey`, `aos-cap init`.
function checkQualifiedRefs(caps, files, root, report) {
  for (const cap of caps) {
    const manifest = readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data ?? {};
    const prefix = effectivePrefix(manifest, cap.id);
    const bare = new Map();
    for (const [name, id] of capabilitySkillNames(cap)) {
      if (name !== id) bare.set(id, name);          // only ids the prefix actually rewrites
    }
    if (!bare.size) continue;
    const ids = [...bare.keys()].join('|');
    const patterns = [
      // "the `capture` skill" — prose. The adjacent "skill" is what keeps this off tool
      // verbs (`kb capture`, `kb import survey`, `aos-cap init`).
      new RegExp(`\`(${ids})\`\\s+skill\\b`, 'g'),
      // A routing-table cell that is nothing but the id — the mechanics map in every entry
      // skill. Tool verbs in a cell carry their command (`kb capture`), so they don't match.
      new RegExp(`\\|\\s*\`(${ids})\`\\s*(?=\\||$)`, 'g'),
    ];

    // cap.rel scopes this to the capability's own tree, so the golden snapshots' rendered
    // copies are never read.
    for (const file of files.filter((f) => f.startsWith(`${cap.rel}/`) && f.endsWith('.md'))) {
      let text;
      try {
        text = readFileSync(join(root, file), 'utf8');
      } catch {
        continue;
      }
      const lines = text.split('\n');
      for (let i = 0; i < lines.length; i += 1) {
        const hits = new Set();
        for (const pattern of patterns) {
          for (const m of lines[i].matchAll(pattern)) hits.add(m[1]);
        }
        for (const hit of hits) {
          report('error', 'skills/ref-unqualified', `${file}:${i + 1}`,
            `"\`${hit}\`" names a capability-local skill id — installed it is "${bare.get(hit)}" (§2.5)`);
        }
      }
    }
  }
}
