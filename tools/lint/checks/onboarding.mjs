import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { QUESTION_KEYS, QUESTION_REQUIRED_KEYS, QUESTION_TYPES } from '../../lib/constants.mjs';

// ONBOARDING.md frontmatter is the typed question list — and doubles as the
// MOD.md answer schema (ARCHITECTURE §3.1: "the questions are the allowed-
// frontmatter definition — no second schema").
export function checkOnboarding({ caps, report }) {
  for (const cap of caps) {
    const path = join(cap.dir, 'ONBOARDING.md');
    if (!existsSync(path)) continue;
    const file = `${cap.rel}/ONBOARDING.md`;
    const { data, error } = readFrontmatter(path);
    if (error || !data) {
      report('error', 'onboarding/parse', file, error ? error.message : 'missing frontmatter');
      continue;
    }
    const questions = data.questions;
    if (!Array.isArray(questions) || !questions.length) {
      report('error', 'onboarding/questions', file, 'frontmatter must declare a non-empty questions[] list');
      continue;
    }
    const seen = new Set();
    for (const q of questions) {
      const label = q?.id ?? '<missing id>';
      for (const key of Object.keys(q ?? {})) {
        if (!QUESTION_KEYS.includes(key)) report('error', 'onboarding/unknown-key', file, `question "${label}": unknown key "${key}"`);
      }
      for (const key of QUESTION_REQUIRED_KEYS) {
        if (q?.[key] == null) report('error', 'onboarding/required', file, `question "${label}": "${key}" is required`);
      }
      if (q?.id != null) {
        if (seen.has(q.id)) report('error', 'onboarding/duplicate-id', file, `duplicate question id "${q.id}"`);
        seen.add(q.id);
      }
      if (q?.type != null && !QUESTION_TYPES.includes(q.type)) {
        report('error', 'onboarding/type', file, `question "${label}": type "${q.type}" not in {${QUESTION_TYPES.join(', ')}} (BUILD-GAPS G2)`);
      }
      for (const flag of ['required', 'secret']) {
        if (q?.[flag] != null && typeof q[flag] !== 'boolean') {
          report('error', 'onboarding/flag', file, `question "${label}": "${flag}" must be a boolean`);
        }
      }
    }
  }
}

export function questionIds(capDir) {
  const path = join(capDir, 'ONBOARDING.md');
  if (!existsSync(path)) return null;
  const { data } = readFrontmatter(path);
  return {
    all: new Set((data?.questions ?? []).map((q) => q?.id).filter(Boolean)),
    required: new Set((data?.questions ?? []).filter((q) => q?.required).map((q) => q.id)),
    secret: new Set((data?.questions ?? []).filter((q) => q?.secret).map((q) => q.id)),
  };
}
