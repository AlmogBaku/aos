#!/usr/bin/env node
// Every `kb <verb> --flag` the kb capability's prose names must exist in the tool.
//
// Why this is a script and not a careful read: the LAYOUT 2 rewrite was reviewed twice by
// hand, and both passes still missed documented commands that fail on invocation — a verb
// spelled as a positional when it is an option, a required flag omitted, a flag deleted from
// the tool but still advertised. The failure mode is uniform: the agent runs what the skill
// says, the tool exits non-zero or silently does the wrong thing, and nothing in CI noticed
// because the prose is just markdown. A verb/flag extractor closes that class mechanically.
//
// What it does NOT check: whether the *semantics* match (that `inbox` is agent-scoped, that
// prune resolves a base by walking parents). Those need a human or a test. This only proves
// that every command named is a command that exists, with flags that exist.
//
// Usage: node tools/check-kb-commands.mjs
//   Requires `uv` to interrogate the tool's own --help. Skips with a note if absent, the
//   same shape as check.sh's tier-0 guard.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { REPO_ROOT, walkRepo } from './lib/repo.mjs';

const CAP = 'capabilities/kb';
// Any capability whose prose invokes `kb` is in scope, not just the one that ships the
// tool: work-tracker composes with kb ONLY through this command on PATH (RFC-009 keeps
// cross-capability skill references out), so its skills carry real invocations with no
// other check on them. A documented command that fails on invocation is the same defect
// wherever it is written.
const CAPS = [CAP, 'capabilities/work-tracker'];
const TOOL = join(REPO_ROOT, 'capabilities/kb/tool');

function uvAvailable() {
  try {
    execFileSync('uv', ['--version'], { stdio: 'ignore' });
    return true;
  } catch { return false; }
}

if (!uvAvailable()) {
  console.log('kb command check: SKIPPED (uv not found — install: https://docs.astral.sh/uv/)');
  process.exit(0);
}

const help = (args) => {
  try {
    return execFileSync('uv', ['run', '--quiet', '--project', TOOL, 'kb', ...args, '--help'],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
  } catch { return null; }
};

// Parse `kb --help` for the verb list, then each verb's own --help for its flags and
// whether it takes positional arguments.
const rootHelp = help([]);
if (!rootHelp) {
  console.error('kb command check: could not run `kb --help` — is the tool installable?');
  process.exit(1);
}

const verbs = new Map();   // verb -> {flags:Set, subcommands:Set, positional:boolean}
const commandsBlock = rootHelp.slice(rootHelp.indexOf('Commands:'));
for (const line of commandsBlock.split('\n').slice(1)) {
  const m = line.match(/^\s{2,}([a-z][a-z-]*)\s{2,}\S/);
  if (m) verbs.set(m[1], null);
}

const flagsOf = (text) => new Set([...text.matchAll(/(--[a-z][a-z0-9-]*)/g)].map((m) => m[1]));
// Two shapes carry a verb's operations. Typer subcommands show up under `Commands:`
// (`kb pending add`), while some verbs take the op as an enumerated positional instead
// (`kb state {op}:<add|bump|drop|check|show>`). Both are "kb <verb> <op>" to a reader, so
// both have to be validated, or a typo in the second shape sails through.
const subsOf = (text) => {
  const out = new Set();
  if (text.includes('Commands:')) {
    const block = text.slice(text.indexOf('Commands:'));
    for (const l of block.split('\n').slice(1)) {
      const m = l.match(/^\s{2,}([a-z][a-z-]*)\s{2,}\S/);
      if (m) out.add(m[1]);
    }
  }
  const usage = text.match(/^Usage:.*$/m);
  if (usage) {
    const enumerated = usage[0].match(/<([a-z|-]+\|[a-z|-]+)>/);
    if (enumerated) for (const op of enumerated[1].split('|')) out.add(op);
  }
  return out;
};

for (const verb of verbs.keys()) {
  const text = help([verb]);
  if (text === null) { verbs.set(verb, { flags: new Set(), subcommands: new Set() }); continue; }
  const subcommands = subsOf(text);
  const entry = { flags: flagsOf(text), subcommands, sub: new Map() };
  for (const s of subcommands) {
    const st = help([verb, s]);
    entry.sub.set(s, st === null ? new Set() : flagsOf(st));
  }
  verbs.set(verb, entry);
}

// Global options live on the root and are legal after `kb` before any verb.
const GLOBAL_FLAGS = flagsOf(rootHelp.slice(0, rootHelp.indexOf('Commands:')));

const failures = [];
// Prose writes commands inside backticks, sometimes wrapped across lines. Normalise
// whitespace so a wrapped invocation still parses as one command.
const CMD_RE = /`kb\s+([^`]+)`/g;

for (const rel of walkRepo(REPO_ROOT)) {
  if (!CAPS.some((c) => rel.startsWith(`${c}/`))) continue;
  if (rel.startsWith(`${CAP}/tool/`)) continue;      // the tool documents itself
  if (!rel.endsWith('.md') && !rel.endsWith('.yaml')) continue;
  const abs = join(REPO_ROOT, rel);
  if (!existsSync(abs)) continue;
  const text = readFileSync(abs, 'utf8');

  for (const m of text.matchAll(CMD_RE)) {
    const raw = m[1].replace(/\s+/g, ' ').trim();
    // Prose sometimes names a verb precisely to say it does NOT exist ("There is no
    // `kb promote` verb"). That is the correct thing to document, so honour the negation
    // rather than forcing the sentence to avoid the backticks.
    const before = text.slice(Math.max(0, m.index - 40), m.index);
    if (/\b(?:no|not a|never)\s*$/i.test(before)) continue;
    // Placeholders and prose fragments: `kb <verb>`, `kb --help`, `kb capture|set`.
    if (/^[<|]/.test(raw) || raw.includes('|')) continue;
    const tokens = raw.split(' ');
    let i = 0;
    // skip global options (and their values) that precede the verb
    while (i < tokens.length && tokens[i].startsWith('-')) {
      const flag = tokens[i].split('=')[0];
      if (!GLOBAL_FLAGS.has(flag)) {
        failures.push(`${rel}: \`kb ${raw}\` — "${flag}" is not a global option`);
      }
      i += tokens[i].includes('=') ? 1 : 2;   // assume `--flag value`
    }
    if (i >= tokens.length) continue;
    const verb = tokens[i];
    if (/^[<{]/.test(verb)) continue;                // `kb <verb> …` placeholder
    if (!verbs.has(verb)) {
      failures.push(`${rel}: \`kb ${raw}\` — no such verb "${verb}"`);
      continue;
    }
    const entry = verbs.get(verb);
    let rest = tokens.slice(i + 1);
    // a subcommand, if this verb has them and the next token names one
    let flagSet = entry.flags;
    if (entry.subcommands.size && rest.length && !rest[0].startsWith('-')) {
      if (entry.subcommands.has(rest[0])) {
        flagSet = new Set([...entry.flags, ...(entry.sub.get(rest[0]) || [])]);
        rest = rest.slice(1);
      } else if (/^[a-z][a-z-]*$/.test(rest[0])) {
        failures.push(`${rel}: \`kb ${raw}\` — "${rest[0]}" is not a ${verb} subcommand `
          + `(have: ${[...entry.subcommands].join(' ')})`);
        continue;
      }
    }
    for (const tok of rest) {
      if (!tok.startsWith('--')) continue;
      const flag = tok.split('=')[0].replace(/[.,;:)]+$/, '');
      if (!flagSet.has(flag) && !GLOBAL_FLAGS.has(flag)) {
        failures.push(`${rel}: \`kb ${raw}\` — "${flag}" is not an option of \`kb ${verb}\``);
      }
    }
  }
}

if (failures.length) {
  console.error(`kb command check: ${failures.length} failure(s)\n`);
  for (const f of [...new Set(failures)]) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`kb command check: every documented kb command exists (${verbs.size} verbs)`);
