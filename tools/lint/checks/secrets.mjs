import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// Backstop only — the real defense is the extraction redaction checklist.
// Fixture fakes must use FAKE-… shapes, which are exempt by construction.
const PATTERNS = [
  { code: 'secrets/token', re: /\b(sk|xox[bapsr]|ghp|gho|glpat|AKIA)[-_][A-Za-z0-9_-]{16,}\b/g, what: 'API-token-shaped string' },
  { code: 'secrets/jwt', re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b/g, what: 'JWT-shaped string' },
  { code: 'secrets/private-key', re: /-----BEGIN [A-Z ]*PRIVATE KEY-----/g, what: 'private key block' },
  { code: 'secrets/phone', re: /(?<!\+0{3})\+[1-9]\d{9,14}\b/g, what: 'phone-number-shaped string (use +000000000000)' },
  { code: 'secrets/whatsapp-jid', re: /\b\d{10,15}@s\.whatsapp\.net\b/g, what: 'WhatsApp JID' },
];

const TEXT_EXT = /\.(md|ya?ml|json|mjs|js|sh|txt|tmpl)$/;

export function checkSecrets({ files, report, root }) {
  for (const rel of files) {
    if (!TEXT_EXT.test(rel)) continue;
    const text = readFileSync(join(root, rel), 'utf8');
    for (const { code, re, what } of PATTERNS) {
      for (const m of text.matchAll(re)) {
        if (/FAKE|EXAMPLE|PLACEHOLDER|xxx/i.test(m[0])) continue;
        report('error', code, rel, `${what}: "${m[0].slice(0, 12)}…" — this repo is public; redact (CLAUDE.md self-containment)`);
      }
    }
  }
}
