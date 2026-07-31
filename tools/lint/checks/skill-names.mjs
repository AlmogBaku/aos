import { join } from 'node:path';
import { readFileSync } from 'node:fs';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { listCapabilities } from '../../lib/repo.mjs';
import {
  effectivePrefix, installedName, isPrefixWellFormed, nameProblems, capabilitySkillNames,
  capabilityAgentNames,
} from '../../lib/skill-names.mjs';
import { SKILL_SLOT_RE, AGENT_SLOT_RE, HISTORICAL_NAME_MARKER } from '../../lib/constants.mjs';

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
  checkAuthoredNames(caps, files, root, report);
}

// The mirror image of checkQualifiedRefs, and the defect that motivated both. That one
// catches a BARE sibling id in shipped prose; this one catches the computed installed name
// written LITERALLY — the case that let `skill_prefix: capability-` → `lc-` rename 80+
// references with green CI, because a literal is only wrong relative to a prefix nothing
// re-derived. Deliberately lint's job and not a runtime gate's: a hardcoded name and a
// dangling slot are both mechanically decidable, and CI is where the author is. (Informal
// prose — "hand it to the archiver" — is the non-mechanical half, and belongs to
// capability-review §6a.)
function checkAuthoredNames(caps, files, root, report) {
  // Every installed name in the repo, and who owns it — so a literal naming ANOTHER
  // capability's skill gets told the qualified slot (`{{skill: <cap>/<id>}}`) rather than
  // the local one.
  const owners = new Map();     // installed name -> { capId, id, kind }
  for (const cap of caps) {
    for (const [name, id] of capabilitySkillNames(cap)) {
      // installedName() returns the id unchanged when id === cap.id, so an entry-skill name
      // is not prefix-fragile: `kb` stays `kb` under any prefix, and demanding a slot for it
      // would be noise. Only names the prefix actually rewrites can rot.
      if (name !== id) owners.set(name, { capId: cap.id, id, kind: 'skill' });
    }
    for (const [name, id] of capabilityAgentNames(cap)) {
      if (name !== id) owners.set(name, { capId: cap.id, id, kind: 'agent' });
    }
  }

  // What a slot may resolve to, per capability: declared skills (the manifest is the source,
  // as in slots.py — an undeclared on-disk skill is its own error and must not make a slot
  // resolvable) and declared agents.
  const declared = new Map();
  for (const cap of caps) {
    declared.set(cap.id, {
      skill: new Set(readFrontmatter(join(cap.dir, 'CAPABILITY.md')).data?.skills
        ?.map((s) => s?.id).filter((i) => typeof i === 'string' && i) ?? []),
      agent: new Set(capabilityAgentNames(cap).values()),
    });
  }

  const literalRe = owners.size
    ? new RegExp(`\`(${[...owners.keys()].sort((a, b) => b.length - a.length).join('|')})\``, 'g')
    : null;

  for (const cap of caps) {
    // RENDERED prose only. CAPABILITY.md is the installer's briefing — read from the clone,
    // never rendered — so it keeps literal names; same for docs/, README.md, BOOTSTRAP.md and
    // AGENTS.md, which describe the kit rather than ship into a harness. cap.rel also keeps
    // the golden snapshots' rendered copies (which correctly hold literals) out.
    const scope = `${cap.rel}/skills/`;
    for (const file of files.filter((f) => f.startsWith(scope) && f.endsWith('.md'))) {
      let text;
      try {
        text = readFileSync(join(root, file), 'utf8');
      } catch {
        continue;
      }
      const lines = text.split('\n');
      for (let i = 0; i < lines.length; i += 1) {
        const line = lines[i];
        const where = `${file}:${i + 1}`;
        // Migration prose names retired skills on purpose; the marker keeps that intent on
        // the line rather than in a path allowlist that would rot.
        if (line.includes(HISTORICAL_NAME_MARKER)) continue;

        if (literalRe) {
          for (const m of new Set([...line.matchAll(literalRe)].map((x) => x[1]))) {
            const owner = owners.get(m);
            const slot = owner.capId === cap.id
              ? `{{${owner.kind}: ${owner.id}}}`
              : `{{${owner.kind}: ${owner.capId}/${owner.id}}}`;
            report('error', 'skills/ref-hardcoded', where,
              `"\`${m}\`" is a computed installed name written as a literal — use ${slot} `
              + `so a ${owner.capId} prefix change cannot invalidate it (§2.5)`);
          }
        }

        // The escaped form (`\{{skill: <id>}}`) is invisible here for the same reason it is
        // invisible to render: the shared regexes carry the `(?<!\\)` guard. A doc that
        // teaches the syntax must not be a lint failure.
        for (const [re, kind, code] of [
          [SKILL_SLOT_RE, 'skill', 'skills/ref-dangling'],
          [AGENT_SLOT_RE, 'agent', 'agents/ref-dangling'],
        ]) {
          for (const m of line.matchAll(re)) {
            const [first, second] = [m[1], m[2]];
            const targetCap = second === undefined ? cap.id : first;
            const targetId = second === undefined ? first : second;
            const known = declared.get(targetCap);
            if (!known) {
              report('error', code, where,
                `${m[0]} names capability "${targetCap}", which is not in this tree`);
            } else if (!known[kind].has(targetId)) {
              report('error', code, where,
                `${m[0]} names no ${kind} declared by "${targetCap}" — it declares `
                + `${[...known[kind]].sort().join(', ') || 'none'}`);
            }
          }
        }
      }
    }
  }
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
