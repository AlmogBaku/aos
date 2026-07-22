import { join, basename } from 'node:path';
import { readFrontmatter } from '../../lib/frontmatter.mjs';
import { OVERLAY_BASENAMES, OVERLAY_EXEMPT_PREFIXES, STATE_DIR } from '../../lib/constants.mjs';
import { questionIds } from './onboarding.mjs';

// ARCHITECTURE §3.1 — THE inviolable contract. Upstream never ships, writes,
// or merges any overlay-family path. tests/fixtures/ simulates the *user
// clone* (where those files legitimately live), hence the exemption.
export function checkOverlayPaths({ files, report }) {
  for (const rel of files) {
    if (OVERLAY_EXEMPT_PREFIXES.some((p) => rel.startsWith(p))) continue;
    const base = basename(rel);
    if (OVERLAY_BASENAMES.includes(base)) {
      report('error', 'overlay/shipped', rel, `"${base}" is user-owned overlay family — upstream must never contain it (ARCHITECTURE §3.1)`);
    }
    if (rel.split('/').includes(STATE_DIR.replace(/\/$/, ''))) {
      report('error', 'overlay/state-dir', rel, `${STATE_DIR} is machine-local state — never committed`);
    }
  }
}

// MOD.example.md (shipped seed) and fixture MOD.md files validate against the
// owning capability's ONBOARDING.md questions — the single source of schema.
export function checkOverlaySchemas({ files, report, root }) {
  const targets = files.filter((rel) => {
    const base = basename(rel);
    if (base === 'MOD.example.md') return true;
    return base === 'MOD.md' && OVERLAY_EXEMPT_PREFIXES.some((p) => rel.startsWith(p));
  });
  for (const rel of targets) {
    const { data, error } = readFrontmatter(join(root, rel));
    if (error) {
      report('error', 'overlay/parse', rel, error.message);
      continue;
    }
    if (!data) continue; // a body-only MOD file carries prose nuance, no typed answers
    if (!data.capability) {
      report('error', 'overlay/capability', rel, 'frontmatter must name its capability');
      continue;
    }
    // Global MOD.md validates against the onboarding capability's own questions.
    const capDir = join(root, 'capabilities', data.capability);
    const ids = questionIds(capDir);
    if (ids) {
      for (const key of Object.keys(data.answers ?? {})) {
        if (!ids.all.has(key)) {
          report('error', 'overlay/answer-key', rel, `answer "${key}" matches no ONBOARDING.md question of "${data.capability}"`);
        }
      }
      // The shipped example must exercise every required question, so the
      // installer's golden path is demonstrated.
      if (basename(rel) === 'MOD.example.md') {
        for (const req of ids.required) {
          if (!(req in (data.answers ?? {})) && !ids.secret.has(req)) {
            report('error', 'overlay/answer-missing', rel, `required question "${req}" has no example answer`);
          }
        }
      }
    }
    for (const [key, val] of Object.entries(data.secrets ?? {})) {
      const ok = val && typeof val === 'object' && typeof val.store === 'string' && typeof val.key === 'string';
      if (!ok) {
        report('error', 'overlay/secret-ref', rel, `secret "${key}" must be a {store, key} reference — values live in the harness store (§3.1)`);
      }
    }
  }
}
