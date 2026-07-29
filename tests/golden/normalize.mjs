#!/usr/bin/env node
// Copy a rendered tree into a golden snapshot, normalizing run-varying values so
// the committed diff shows only meaningful changes.
// Usage: normalize.mjs <src-dir> <dest-dir>
import { readdirSync, statSync, mkdirSync, readFileSync, writeFileSync, existsSync, rmdirSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { parse } from 'yaml';
import { ORIGIN_FRONTMATTER_PATH } from '../../tools/lib/constants.mjs';

// The install-time provenance stamp, read as structured frontmatter. Both golden scripts used
// `.includes('x-aos-origin:')`, which matched the string anywhere in the file — including in a
// skill whose prose merely discussed provenance. Now that the stamp is nested inside the spec's
// `metadata` hatch there is no line to match at all, so this has to parse.
export function originStamp(skillMd) {
  let text;
  try { text = readFileSync(skillMd, 'utf8'); } catch { return undefined; }
  if (!text.startsWith('---\n')) return undefined;
  const end = text.indexOf('\n---', 3);
  if (end === -1) return undefined;
  let data;
  try { data = parse(text.slice(4, end + 1)); } catch { return undefined; }
  let node = data;
  for (const key of ORIGIN_FRONTMATTER_PATH) {
    if (node === null || typeof node !== 'object' || !(key in node)) return undefined;
    node = node[key];
  }
  return node;
}

const [src, dest] = process.argv.slice(2);

const SKIP = new Set(['config.yaml', 'profile.yaml',  // harness runtime state: provider/model details are run-varying and private
  '.hub', 'index-cache', '.bundled_manifest',  // harness-owned skill-store metadata + caches (megabytes of run-varying JSON)
  'node_modules', '.git', 'sessions', 'logs', 'memories', 'state.db',
  'audio_cache', 'cache', '.env', 'auth.json', 'state-snapshots', 'bin',
  // Harness runtime state inside a profile. `home` is the agent's own sandbox HOME
  // (npm/node caches — megabytes, and it carries absolute developer paths a snapshot
  // must never commit); `lsp` is language-server state. Neither is ever an aos artifact.
  // NOTE: SKIP matches on basename, so these two names are also unusable as source dir
  // names anywhere in a snapshotted tree. Acceptable for harness runtime state; do not
  // add a name a capability might legitimately ship (`skills`, `reference`, `templates`).
  'home', 'lsp',
  // Harness-written marker/notice files: presence depends on the build and the model in
  // use, not on anything an install did.
  '.no-bundled-skills', '.codex_gpt55_autoraise_notice',
  'executions.db', '.jobs.lock', 'auth.lock', 'state.db-shm', 'state.db-wal',
  '.skills_prompt_snapshot.json', '.update_check', 'context_length_cache.yaml',
  'verification_evidence.db', 'models_dev_cache.json']);
// A known trailing suffix (e.g. `.sh.unused`, left when a harness renames a script)
// must still normalize — otherwise absolute developer paths land in a committed
// snapshot. Deliberately an allowlist: `.json.gz` must NOT be read as text.
const TEXT = /\.(md|ya?ml|json|txt|sh|tmpl)(\.(unused|bak|orig|old|disabled))?$/;

const HOME = process.env.HOME || '/home/user';
function normalizeText(text) {
  return text
    .split(HOME).join('<HOME>')
    .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?/g, '<TIMESTAMP>')
    .replace(/\d{4}-\d{2}-\d{2}/g, '<DATE>')
    .replace(/\b[0-9a-f]{64}\b/g, '<SHA256>')
    .replace(/\b[0-9a-f]{12}\b/g, '<ID>');
}

function copy(s, d) {
  const st = statSync(s);
  if (st.isDirectory()) {
    if (SKIP.has(s.split('/').pop())) return;
    mkdirSync(d, { recursive: true });
    // A skills/ dir with a .bundled_manifest is a harness-managed skill store:
    // snapshot ONLY what the INSTALL materialized (top-level dirs whose SKILL.md
    // carries the origin stamp) — bundled harness content and the store's own metadata
    // (.bundled_manifest, .hub) are run-varying noise.
    if (existsSync(join(s, '.bundled_manifest'))) {
      for (const name of readdirSync(s)) {
        const child = join(s, name);
        if (!statSync(child).isDirectory()) { continue; }
        if (name === '.hub') { continue; }
        const skillMd = join(child, 'SKILL.md');
        if (existsSync(skillMd) && originStamp(skillMd) !== undefined) {
          copy(child, join(d, name));
        }
      }
      return;
    }
    for (const name of readdirSync(s)) copy(join(s, name), join(d, name));
    // An empty directory is noise in the committed diff — the harness creates a dozen
    // of them per profile, and none of them is something an install wrote.
    if (!readdirSync(d).length) rmdirSync(d);
  } else {
    if (SKIP.has(s.split('/').pop())) return;
    mkdirSync(join(d, '..'), { recursive: true });
    if (TEXT.test(s)) {
      let text = readFileSync(s, 'utf8');
      if (s.endsWith('.json')) {
        // provider/model snapshots are run-varying and private — scrub before committing
        try {
          const scrub = (o) => {
            if (Array.isArray(o)) o.forEach(scrub);
            else if (o && typeof o === 'object') {
              for (const k of Object.keys(o)) {
                if (k === 'provider_snapshot' || k === 'model_snapshot') o[k] = null;
                else scrub(o[k]);
              }
            }
          };
          const parsed = JSON.parse(text);
          scrub(parsed);
          text = JSON.stringify(parsed, undefined, 2);
        } catch {}
      }
      writeFileSync(d, normalizeText(text));
    } else if (st.size < 64 * 1024) {
      writeFileSync(d, readFileSync(s));
    }
  }
}

export { copy as normalizeTree, SKIP };

// Only act as a CLI when invoked directly — check.mjs imports the pipeline to assert
// that re-normalizing a committed snapshot is a no-op.
if (process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (!src || !dest) {
    console.error('usage: normalize.mjs <src-dir> <dest-dir>');
    process.exit(1);
  }
  if (!existsSync(src)) {
    console.error(`source ${src} does not exist`);
    process.exit(1);
  }
  copy(src, dest);
  console.log(`normalized ${src} -> ${dest}`);
}
