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

const SKIP = new Set(['node_modules', '.git', 'sessions', 'logs', 'memories', 'state.db',
  'audio_cache', 'cache', '.env', 'auth.json', 'state-snapshots', 'bin']);
const TEXT = /\.(md|ya?ml|json|txt|sh|tmpl)$/;

function normalizeText(text) {
  return text
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
    for (const name of readdirSync(s)) copy(join(s, name), join(d, name));
  } else {
    if (SKIP.has(s.split('/').pop())) return;
    mkdirSync(join(d, '..'), { recursive: true });
    if (TEXT.test(s)) {
      let text = readFileSync(s, 'utf8');
      if (s.endsWith('.json')) {
        try { text = JSON.stringify(JSON.parse(text), Object.keys(JSON.parse(text)).sort ? undefined : undefined, 2); } catch {}
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
