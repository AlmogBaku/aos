#!/usr/bin/env node
// Copy a rendered tree into a golden snapshot, normalizing run-varying values so
// the committed diff shows only meaningful changes.
// Usage: normalize.mjs <src-dir> <dest-dir>
import { readdirSync, statSync, mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const [src, dest] = process.argv.slice(2);
if (!src || !dest) {
  console.error('usage: normalize.mjs <src-dir> <dest-dir>');
  process.exit(1);
}

const SKIP = new Set(['config.yaml', 'profile.yaml',  // harness runtime state: provider/model details are run-varying and private
  '.hub', 'index-cache', '.bundled_manifest',  // harness-owned skill-store metadata + caches (megabytes of run-varying JSON)
  'node_modules', '.git', 'sessions', 'logs', 'memories', 'state.db',
  'audio_cache', 'cache', '.env', 'auth.json', 'state-snapshots', 'bin',
  'executions.db', '.jobs.lock', 'auth.lock', 'state.db-shm', 'state.db-wal',
  '.skills_prompt_snapshot.json', '.update_check', 'context_length_cache.yaml',
  'verification_evidence.db', 'models_dev_cache.json']);
const TEXT = /\.(md|ya?ml|json|txt|sh|tmpl)$/;

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
    // carries x-aos-origin) — bundled harness content and the store's own metadata
    // (.bundled_manifest, .hub) are run-varying noise.
    if (existsSync(join(s, '.bundled_manifest'))) {
      for (const name of readdirSync(s)) {
        const child = join(s, name);
        if (!statSync(child).isDirectory()) { continue; }
        if (name === '.hub') { continue; }
        const skillMd = join(child, 'SKILL.md');
        if (existsSync(skillMd) &&
            readFileSync(skillMd, 'utf8').includes('x-aos-origin:')) {
          copy(child, join(d, name));
        }
      }
      return;
    }
    for (const name of readdirSync(s)) copy(join(s, name), join(d, name));
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

if (!existsSync(src)) {
  console.error(`source ${src} does not exist`);
  process.exit(1);
}
copy(src, dest);
console.log(`normalized ${src} -> ${dest}`);
