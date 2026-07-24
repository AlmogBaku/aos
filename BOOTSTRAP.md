# Bootstrap: the first five minutes

You are a harness agent setting up aos for your user. There is no installer binary — **you
are the installer** (ARCHITECTURE §5.1). This file is deliberately small: it gets exactly
one capability into your harness — `capability-lifecycle` — and that capability's skills
carry everything else. Steps are **[D]** (mechanical — do it precisely, verify, record) or
**[A]** (judgment — think, then show your work).

## The experience

You are already in the clone (the paste-block forked-and-cloned it — silent, harmless; a
plain clone is fine too). **Before any check or write, welcome your user**, in the voice
defined by the `capability-lifecycle` entry skill's `## Experience` section
(`capabilities/capability-lifecycle/skills/capability-lifecycle/SKILL.md` — read it now;
it binds every step below and every lifecycle interaction after): warm + expert, concept
before mechanics, explain-then-act. Tell them, in your own friendly words: what aos is
(batteries for the harness they already run), what's about to happen (~5 minutes — a short
interview, then installs), and the two promises — *their answers become their `MOD.md`,
forever theirs in their own private repo; nothing lands without a visible diff*. Answer
questions if they have any, then proceed — the diff gate is the safety net, not repeated
consent prompts.

## 0. [D] Prerequisites

- `git --version` — missing → friendly stop with an install pointer (you likely couldn't
  have cloned without it).
- `uv --version` — **required**: it carries the `aos-lock` bookkeeping tool. Missing →
  offer the official installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`), run it
  with the user's OK, verify; if they decline, stop honestly — the lockfile discipline
  cannot be prose.

## 1. [D] The household

aos lives in one directory — **the household**, `~/aos/` (a plain directory, itself never
a git repo). Two members, plus machine state:

```
~/aos/
├── upstream/    # this clone — the kit, pristine; NOTHING personal ever lands here
├── personal/    # the user's ONE private repo: answers, tweaks, private capabilities
└── .aos/        # machine-local state (lockfile) — created by aos-lock init
```

Vocabulary for the user, if they ask: `upstream/` (and future org roots) are
*distributions*; `personal/` is *their instance* — it syncs across machines via its
private remote; only `.aos/` is machine-local.

1. Confirm this clone is at `~/aos/upstream` and clean (`git -C ~/aos/upstream status`).
   If the paste-block landed it elsewhere (e.g. `~/aos` directly — the pre-household
   shape), move it to `~/aos/upstream` first.
2. Check remotes: the fork shape is `origin` = the user's fork, `upstream` = canonical.
   A plain clone (origin = canonical) is fine — note once that forking later is one
   command (`gh repo fork --remote`) and move on. **Forks are public** — which is safe,
   because nothing personal ever enters this clone.
3. Create the personal root: `git init ~/aos/personal`, seed the mirrored shape
   (`capabilities/` directory). Offer — don't push — a private remote for backup/sync
   (`gh repo create aos-personal --private` when `gh` is available; skippable, add one
   any time). Everything personal (MOD files, rendered skills, private capabilities)
   will live and be auto-committed here.

## 2. [D] Install the capability-lifecycle capability (inline — the only one)

1. Read
   `capabilities/capability-lifecycle/skills/capability-lifecycle/reference/contract.md`
   **in full** — it is the install contract binding this step and every install after.
2. Read `capabilities/capability-lifecycle/CAPABILITY.md` (the briefing), then:
   `uv tool install --from ~/aos/upstream/capabilities/capability-lifecycle/tool aos-lock`
   and `aos-lock --home ~/aos init`.
3. Load your cheat-sheet: `capabilities/capability-lifecycle/harnesses/<harness-runtime>.md`,
   where the **harness runtime** is the program hosting you (OpenClaw →
   `harnesses/openclaw.md` · Hermes → `harnesses/hermes.md` · NanoClaw →
   `harnesses/nanoclaw.md` · Nanobot → `harnesses/nanobot.md`; Claude Code and OpenCode
   have no sheet yet). None for your harness → follow the entry skill's
   `reference/no-cheatsheet.md` — do not stop.
4. **STAGE** the five skills per the contract (mechanical — they have no `{{mod}}` slots):
   render into `~/aos/personal/capabilities/capability-lifecycle/skills/…`, plan the
   symlinks into your front agent's skills dir → **GATE** (show the user the plan) →
   **EXECUTE** (commit the render in `personal/`, create the links) →
   `aos-lock record capability-lifecycle --version <manifest version> --artifact …` per
   link/path.

## 3. Hand over

The lifecycle skills are live — from here `install <capability>` triggers
`capability-installer`. Use it now, as ordinary installs:

1. **onboarding** — its interview *is* the global one (identity, timezone, working hours,
   sacred time, red lines → `~/aos/personal/MOD.md`).
2. **kb** — its interview + KB setup (adopt existing KBs / init a fresh one →
   `~/aos/personal/kb-registry.yaml`).

Close per the Experience section: what was installed, where, which schedules, any
degraded modes — specific and celebratory. Everything after is on demand:
`install <capability>` · `update` · `remove <capability>` · "change how X behaves" — all
skills now, no file re-reading required.
