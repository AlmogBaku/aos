# Bootstrap: the first five minutes

You are a harness agent setting up aos for your user. There is no installer binary — **you
are the installer** (ARCHITECTURE §5.1). Follow this sequence exactly. Steps are marked
**[D]** (mechanical — do it precisely, verify, record) or **[A]** (judgment — think, then
show your work).

This kit is prompts: capability declarations you can read and act on directly. Your
**harness runtime** — the agent program hosting you — has a cheat-sheet at
`harnesses/<harness-runtime>.md` mapping aos concepts to its native primitives
(OpenClaw → `harnesses/openclaw.md` · Hermes → `harnesses/hermes.md` · NanoClaw →
`harnesses/nanoclaw.md` · Nanobot → `harnesses/nanobot.md` · Claude Code →
`harnesses/claude-code.md` · OpenCode → `harnesses/opencode.md`). The cheat-sheet is an
aid, not a gate: load it at the steps marked below — not as standing context. If none
exists for your harness, follow [the last section](#no-cheat-sheet-for-your-harness) —
do not stop.

## 0. The install contract (binds every step below, on every harness)

- **The diff gate is never optional.** Nothing lands in the harness until the user has seen
  the full diff of what you are about to write and approved it (§5.4).
- **You never write** any `MOD.md` except through the onboarding interview, and you never
  edit shipped capability files in the clone — personalization lives only in the overlay
  (§3.1) and the materialized artifacts.
- **Everything you materialize is recorded** in `.aos/installs.lock.yaml` with its path and
  sha256 (schedules by job id under `schedules_owned`). No lockfile record, no artifact.
- **Skills** are copied **whole** (`reference/`, `scripts/`, `templates/` travel with the
  skill; scripts are executed, never loaded as context) into the skills location of every
  agent in their `used_by`, as **`<capability>-<id>/`**; fill `{{mod: …}}` slots (leave
  unfilled slots intact) and add `x-aos-origin: <capability>@<version>` to the
  materialized copy's frontmatter.
- **Schedules** are named `aos:<capability>:<schedule-id>` and single-owner (§5.5): check
  for the job across agents first — exists elsewhere → ask the user to reassign, never
  duplicate. Exec-type entries run the tool the capability's briefing installs (verify
  `uv --version` before wiring). An absent host feature triggers the schedule's declared
  degraded mode: `manual` = materialize the prompt as an invocable skill and tell the user
  how to run it · `inline` = append it (inside markers) to an existing aos-owned job ·
  `skip` = record it so doctor reports it.
- **Context blocks** are appended only inside
  `<!-- aos:<capability>@<version> begin -->` … `<!-- aos:<capability>@<version> end -->`
  markers; never touch text outside them.
- **Secrets**: values go to the harness's store, never into files or chat; `MOD.md` and
  configs carry references only — `{store: <name>, key: <key>}`.
- **Removal** walks the lockfile entry backwards; `MOD.md` is never deleted (§3.3). Verify
  by re-running introspection until no aos provenance (`x-aos-origin:`, `aos:` names,
  marker blocks) remains.
- Harness-owned files (e.g. Hermes `config.yaml`, `cron/jobs.json`) are touched only
  through the harness's own CLI, per the cheat-sheet.

## 1. [D] Clone + state

1. Clone the kit to `~/aos` (or confirm it's already there and clean: `git -C ~/aos status`).
2. Check `harnesses/<harness-runtime>.md` exists. Missing → run
   [No cheat-sheet for your harness?](#no-cheat-sheet-for-your-harness) before continuing.
3. Create `.aos/` in the clone with an empty lockfile:

```yaml
# ~/aos/.aos/installs.lock.yaml
version: 1
installs: {}
```

`.aos/` is machine-local and already gitignored. Whether the user tracks their overlay in a
private fork or keeps it local is their choice (RFC-005) — don't decide it for them; if they
ask, present both options neutrally.

## 2. [A] Global interview → root MOD.md

Run the **onboarding** capability's own interview: read
`capabilities/onboarding/ONBOARDING.md` and follow its script conversationally — identity,
timezone, working hours, sacred time, red lines. Then:

- **[D]** validate every answer against the question list (typed frontmatter is the schema);
- **[D]** any `secret: true` answer: load `harnesses/<harness-runtime>.md` (Secrets
  section) now; value → harness secret store, reference `{store, key}` → MOD.md;
- **[A]** write `~/aos/MOD.md` — typed answers in frontmatter, prose nuances in the body.

Re-running later is safe: only missing or `re_ask`-triggered questions are asked again;
`--refresh` re-asks everything and shows a diff before writing (§3.2).

## 3. [A] KB setup → kb-registry.yaml

Ask the user about their knowledge bases:

- **Existing KB(s)** → for each, run the kb capability's `adopt` skill
  (`capabilities/kb/skills/adopt/SKILL.md`): register it in `~/aos/kb-registry.yaml` and
  lint-report divergence from its methodology — **never rewrite the user's KB**.
- **No KB yet** → run the `init` skill: `kb init personal` scaffolds a private default KB
  from the templates bundled in `capabilities/kb/skills/init/templates/` and registers it.

Either way this writes `~/aos/kb-registry.yaml` (user-owned, overlay family).

## 4. [D] Install the two root capabilities

**Load `harnesses/<harness-runtime>.md` now** — it governs every host check and
materialization below. The installer needs kb and onboarding installed; their interviews
already ran above, so their install steps are carried here inline (this breaks the
chicken-and-egg):

**onboarding** (`capabilities/onboarding/`):
1. [D] Read its `CAPABILITY.md`; check `depends.host` against the cheat-sheet Feature notes.
2. [A] Transform: original skills × root `MOD.md` → personalized copies (fill `{{mod: …}}`
   slots; leave unfilled slots intact).
3. [A] Materialize per the cheat-sheet: its skills are `used_by: [main]` → the front agent's
   skills location.
4. [D] Diff gate → write → record in lockfile.

**kb** (`capabilities/kb/`):
1. [D] Read its `CAPABILITY.md`; host check (`cron: preferred` — if absent, note the
   degraded mode for each schedule). Install the tool first:
   `uv tool install --from <clone>/capabilities/kb/tool aos-base` (records in the lockfile;
   no uv → skills fall back to prose execution per the cheat-sheet).
2. [A] Transform its skills (`kb`, `route`, `recall`, `init`, `adopt`, `import`) with
   `MOD.md` + `kb-registry.yaml` context.
3. [A] Materialize: `main`-scoped skills to the front agent; the `kb` entry skill also goes
   to the front agent (`used_by: [main, archiver]`); create the **archiver** agent per
   `agents/archiver.agent.yaml` and the cheat-sheet's agent mapping; the `kb` entry skill
   (the map + reference docs; the tool itself is the installed `base` command — lint is a
   tool verb now, not its own skill) into the archiver's workspace too.
4. [A] Register schedules (nightly promote, weekly lint, sync) on the archiver per the
   cheat-sheet's schedule mapping.
5. [A] Register KB zones: append this capability's grant rows to each target KB's
   `AGENTS.md` `## Grants` table (drafted by you, approved by the user — kb-authorization
   §3.3).
6. [D] Diff gate → write → record artifacts + hashes + `schedules_owned`.

## 5. Done

Tell the user what was installed, where, and any degraded modes in effect. Everything after
this is on demand — load `harnesses/<harness-runtime>.md` per operation, not as standing
context:

- `install <capability>` — read its CAPABILITY.md, recurse into missing deps, interview,
  transform, diff gate, materialize, record (design/install-flow.md §2).
- `update` — after `git pull`: backup → LLM merge (new template × current install × MOD.md)
  → diff gate → record (§3).
- `remove <capability>` — walk the lockfile entry backwards per the cheat-sheet's Removal
  section; MOD.md is never deleted (§4).
- User hand-edits to installed artifacts are normal — capture them back into MOD.md when you
  notice them (`sync-mod`, §3.3 round-trip).

## No cheat-sheet for your harness?

The contract in §0 is the aos half and holds everywhere; a cheat-sheet only adds your
harness's half. Derive it yourself:

| aos concept | find your harness's |
|---|---|
| agent | isolated persona/workspace primitive (profile, group, agent dir…) |
| front agent (`main`) | the assistant the user already talks to |
| skill | where Agent Skills folders load, **per agent** (`used_by` = per-agent placement) |
| schedule | native cron/job mechanism |
| context block | identity/instruction files it actually consumes — never invent filenames |
| secret | native store (env file, vault, keychain) |
| introspection | how to enumerate all of the above |

1. **[A]** Introspect your harness: config layout, skills dirs, scheduler, secret store,
   agent primitive — read its docs and CLI help, list what already exists.
2. **[A]** Draft `harnesses/<harness-runtime>.md` answering §5.2's six sections (Primitive
   mapping, Materialization guide, Introspection guide, Secrets, Removal, Feature notes —
   `harnesses/hermes.md` is the reference shape). Keep it lean: your harness's half only.
3. **[D]** Diff gate: show the user the full draft before writing it. The draft is
   untracked in the clone — expected; clean-clone checks concern tracked files and
   `git pull` won't touch it.
4. Proceed with the sequence above using your draft, telling the user the mappings are
   self-authored and unverified. After a verified install, suggest contributing it
   upstream (CONTRIBUTING.md).
