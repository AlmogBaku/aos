import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import {
  MANIFEST_KEYS, CAPABILITY_TAGS, DEPENDS_KEYS, HOST_FEATURES, HOST_LEVELS,
  SCHEDULE_KEYS, DEGRADED_MODES, SKILL_ENTRY_KEYS, KB_KEYS, KB_ZONE_KEYS, MAIN_AGENT,
} from '../../lib/constants.mjs';
import { agentNames } from './agents.mjs';

const SEMVER = /^\d+\.\d+\.\d+$/;
const CRON = /^\S+ \S+ \S+ \S+ \S+$/;

export function checkManifests({ caps, report, root }) {
  for (const cap of caps) {
    const file = `${cap.rel}/CAPABILITY.md`;
    const { data, error } = readFrontmatter(join(cap.dir, 'CAPABILITY.md'));
    if (error || !data) {
      report('error', 'manifest/parse', file, error ? error.message : 'missing frontmatter');
      continue;
    }

    // Rule of two, enforced mechanically: a field nobody specced is an error.
    for (const key of Object.keys(data)) {
      if (!MANIFEST_KEYS.includes(key)) {
        report('error', 'manifest/unknown-key', file, `unknown frontmatter key "${key}" (ARCHITECTURE §2.2 — rule of two)`);
      }
    }

    if (data.id !== cap.id) report('error', 'manifest/id', file, `id "${data.id}" != directory name "${cap.id}"`);
    if (!SEMVER.test(String(data.version ?? ''))) report('error', 'manifest/version', file, `version "${data.version}" is not x.y.z semver`);
    if (!Array.isArray(data.tags) || !data.tags.length || data.tags.some((t) => !CAPABILITY_TAGS.includes(t))) {
      report('error', 'manifest/tags', file, `tags must be a non-empty subset of {${CAPABILITY_TAGS.join(', ')}}`);
    }
    if (typeof data.summary !== 'string' || !data.summary.trim()) report('error', 'manifest/summary', file, 'summary is required (one line)');

    checkDepends(data.depends, file, report, root);
    const agents = agentNames(cap);
    checkSchedules(data.schedules, cap, file, report, agents);
    checkSkillsBijection(data.skills, cap, file, report);
    checkKb(data.kb, cap, file, report, agents);

    if (!existsSync(join(cap.dir, 'README.md'))) {
      report('error', 'manifest/readme', file, 'README.md is required (humans + PR review, ARCHITECTURE §2.1)');
    }
    // BUILD-GAPS G3: MOD.example.md is presence-paired with ONBOARDING.md.
    const hasOnboarding = existsSync(join(cap.dir, 'ONBOARDING.md'));
    const hasModExample = existsSync(join(cap.dir, 'MOD.example.md'));
    if (hasOnboarding && !hasModExample) {
      report('error', 'manifest/mod-example', file, 'ONBOARDING.md present but MOD.example.md missing (they are presence-paired)');
    }
  }
}

function checkDepends(depends, file, report, root) {
  if (depends == null) return;
  for (const key of Object.keys(depends)) {
    if (!DEPENDS_KEYS.includes(key)) report('error', 'depends/unknown-key', file, `unknown depends key "${key}"`);
  }
  for (const dep of depends.capabilities ?? []) {
    if (!existsSync(join(root, 'capabilities', dep, 'CAPABILITY.md'))) {
      report('error', 'depends/capability', file, `depends on "${dep}" but capabilities/${dep}/CAPABILITY.md does not exist`);
    }
  }
  for (const [feature, level] of Object.entries(depends.host ?? {})) {
    if (!HOST_FEATURES.includes(feature)) {
      report('error', 'depends/host-feature', file, `"${feature}" is not in the §5.2 host vocabulary {${HOST_FEATURES.join(', ')}}`);
    }
    if (!HOST_LEVELS.includes(level)) {
      report('error', 'depends/host-level', file, `host level "${level}" must be one of {${HOST_LEVELS.join(', ')}}`);
    }
  }
}

function checkSchedules(schedules, cap, file, report, agents) {
  if (schedules == null) return;
  const seen = new Set();
  for (const s of schedules) {
    for (const key of Object.keys(s)) {
      if (!SCHEDULE_KEYS.includes(key)) report('error', 'schedules/unknown-key', file, `schedule "${s.id}": unknown key "${key}"`);
    }
    if (!s.id || seen.has(s.id)) report('error', 'schedules/id', file, `schedule id "${s.id}" missing or duplicate`);
    seen.add(s.id);
    if (!CRON.test(String(s.cron ?? ''))) report('error', 'schedules/cron', file, `schedule "${s.id}": cron "${s.cron}" is not a 5-field expression`);
    // §2.2: exec (mechanical, deterministic-only) XOR agent+prompt_ref (judgment).
    const hasExec = s.exec != null;
    const hasAgent = s.agent != null || s.prompt_ref != null;
    if (hasExec && hasAgent) {
      report('error', 'schedules/exec-xor-agent', file, `schedule "${s.id}": exec and agent/prompt_ref are mutually exclusive`);
    } else if (hasExec) {
      // First token: a capability-relative path (must resolve) or a bare command
      // (no slash) provided by the capability's tool install (§2.4 — the briefing
      // documents the install; the cheat-sheet wires the degraded form).
      const execTok = String(s.exec).split(' ')[0];
      if (execTok.includes('/') && !existsSync(join(cap.dir, execTok))) {
        report('error', 'schedules/exec-ref', file, `schedule "${s.id}": exec "${execTok}" does not resolve inside the capability`);
      }
    } else {
      if (s.agent !== MAIN_AGENT && !agents.includes(s.agent)) {
        report('error', 'schedules/agent', file, `schedule "${s.id}": agent "${s.agent}" is neither "${MAIN_AGENT}" nor a declared agents/*.agent.yaml name`);
      }
      if (!s.prompt_ref || !existsSync(join(cap.dir, s.prompt_ref))) {
        report('error', 'schedules/prompt-ref', file, `schedule "${s.id}": prompt_ref "${s.prompt_ref}" does not resolve inside the capability`);
      }
    }
    if (!DEGRADED_MODES.includes(s.degraded)) {
      report('error', 'schedules/degraded', file, `schedule "${s.id}": degraded "${s.degraded}" must be one of {${DEGRADED_MODES.join(', ')}}`);
    }
  }
}

function checkSkillsBijection(skills, cap, file, report) {
  const declared = new Set();
  for (const s of skills ?? []) {
    for (const key of Object.keys(s)) {
      if (!SKILL_ENTRY_KEYS.includes(key)) report('error', 'skills/unknown-key', file, `skill "${s.id}": unknown key "${key}"`);
    }
    declared.add(s.id);
    if (!existsSync(join(cap.dir, 'skills', s.id, 'SKILL.md'))) {
      report('error', 'skills/missing-dir', file, `declared skill "${s.id}" has no skills/${s.id}/SKILL.md`);
    }
  }
  const skillsDir = join(cap.dir, 'skills');
  if (existsSync(skillsDir)) {
    const onDisk = readdirSync(skillsDir).filter((n) => statSync(join(skillsDir, n)).isDirectory());
    for (const id of onDisk) {
      if (!declared.has(id)) {
        report('error', 'skills/undeclared', file, `skills/${id}/ exists but is not declared in the manifest skills[] list`);
      }
    }
  }
}

function checkKb(kb, cap, file, report, agents) {
  if (kb == null) return;
  for (const key of Object.keys(kb)) {
    if (!KB_KEYS.includes(key)) report('error', 'kb/unknown-key', file, `unknown kb key "${key}"`);
  }
  for (const zone of kb.zones ?? []) {
    for (const key of Object.keys(zone)) {
      if (!KB_ZONE_KEYS.includes(key)) report('error', 'kb/zone-key', file, `kb zone "${zone.path}": unknown key "${key}"`);
    }
    if (zone.owner_agent !== MAIN_AGENT && !agents.includes(zone.owner_agent)) {
      report('error', 'kb/owner-agent', file, `kb zone "${zone.path}": owner_agent "${zone.owner_agent}" does not resolve`);
    }
  }
}
