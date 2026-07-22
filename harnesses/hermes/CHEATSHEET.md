# Hermes cheat-sheet

Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
**Hermes**. You are the installer (ARCHITECTURE §5.1) — this file teaches you what Hermes
calls things, where artifacts land, and which safety rails to route through. It is knowledge,
not a program.

**The one rule that outranks everything here: never hand-edit `config.yaml` or
`cron/jobs.json`.** Both are machine-rewritten merge targets (config comments do not survive;
jobs.json holds live scheduler state and has schema drift). Every mutation goes through the
`hermes` CLI, which writes atomically and validates. The 18 `config.yaml.bak*` files a study
of a live install found are the scar tissue this rule prevents.

## Primitive mapping

| aos concept | Hermes primitive | Where |
|---|---|---|
| agent (`agents/*.agent.yaml`) | **profile** — a full parallel HERMES_HOME with its own `config.yaml`, `.env`, `SOUL.md`, `skills/`, `cron/`, `memories/` | `~/.hermes/profiles/<name>/` — **directory-defined**; there is no profiles section in root `config.yaml`. Create with `hermes profile create <name>`; target with `hermes -p <name> …` |
| the front agent (`main`) | the **default profile** — the root of `~/.hermes` itself | `~/.hermes/` |
| skill | native Agent Skills folder | `~/.hermes/skills/<id>/` (default profile) or `~/.hermes/profiles/<p>/skills/<id>/` — **per-profile dirs are how `used_by` scoping works**; there is no per-skill audience field |
| schedule | **cron job** owned by exactly one profile — the job→profile mapping is by directory (`cron/jobs.json` per HERMES_HOME), not a field | `hermes -p <profile> cron create '<cron-expr>' '<prompt>' --name … --skill …` |
| context block | `SOUL.md` = the profile's identity/persona (stable system prompt). `workspace/AGENTS.md` = per-working-dir operating instructions. | inside the profile dir |
| secret | `.env` line (root or per-profile) | see Secrets |

**Files Hermes actually consumes** (anything else you write is inert):
`SOUL.md`, `AGENTS.md`/`CLAUDE.md`/`.cursorrules` (discovered under the working dir),
`memories/MEMORY.md`, `memories/USER.md`, `skills/*/SKILL.md`, `cron/jobs.json`, `config.yaml`,
`.env`, `mcp.json`, `hooks/`. A live install was found with the archiver's personality written
to a `persona.md` Hermes never reads, beside an **empty** `SOUL.md` — the personalization
silently never reached the prompt. Do not invent filenames; when in doubt, `SOUL.md`.

**Model classes** (`agent.yaml model_class`): map through `hermes config set model.default …`
in the profile — `fast`/`balanced`/`deep` translate to whatever cheap/default/frontier models
this install has configured (`hermes config get model` shows the current default; don't
hardcode provider names — §2.3 keeps them out of the neutral spec).

## Materialization guide

Work top-down from `CAPABILITY.md`. Every artifact you create gets provenance (below), every
path you touch gets a line in `.aos/installs.lock.yaml`, and the full diff is shown to the
user **before** anything lands (§5.4 — the gate is never optional).

**1. Agents → profiles.** For each `agents/<name>.agent.yaml`: `hermes profile create <name>`.
Then materialize inside `~/.hermes/profiles/<name>/`:
- `purpose` + the capability's persona content → **`SOUL.md`** (replace the seeded default;
  never leave it empty).
- `context_files` → copy into the profile workspace and reference from `workspace/AGENTS.md`.
- `model_class` → `hermes -p <name> config set model.default <model>` only if the user's
  default doesn't already match the class; otherwise leave the profile on defaults.
- `workspace: own` is the default (a profile IS its own workspace); `shared` means skip
  profile creation and wire the agent's skills/schedules into the default profile.

**2. Skills → skills dirs, scoped by `used_by`.** Copy each `skills/<id>/` folder into the
skills dir of **every profile named in its `used_by`** (`main` = `~/.hermes/skills/`,
agent name = `~/.hermes/profiles/<name>/skills/`). Nowhere else — that scoping is what keeps
N capabilities from becoming N×skills in every agent's context (§2.2). After personalizing
skill text with MOD.md nuances (the `{{mod: …}}` slots), add the provenance key to the
materialized copy's frontmatter (shipped originals never carry it):

```yaml
x-aos-origin: <capability>@<version>
```

**3. Schedules → cron jobs in the owning profile.** For each `schedules[]` entry:

```
hermes -p <agent-profile> cron create '<cron>' "$(cat <prompt_ref, personalized>)" \
  --name 'aos:<capability>:<schedule-id>' [--skill <id> …] [--deliver <target>]
```

(agent `main` ⇒ run without `-p`.) Provenance: the `aos:<capability>:<schedule-id>` **name
prefix** plus the job `id` Hermes returns, recorded in the lockfile under `schedules_owned`.
Do **not** write an `origin:` field into jobs.json — Hermes already uses `origin` for chat
provenance with a different schema, and editing jobs.json races the scheduler ticker.
Single-owner rule (§5.5): before creating, `hermes cron list` across profiles; if this
schedule id already exists from another install, ask the user to reassign, never duplicate.

**4. Context blocks.** Persona/identity fragments → append to the target profile's `SOUL.md`
inside clearly delimited markers:

```
<!-- aos:<capability>@<version> begin -->
…
<!-- aos:<capability>@<version> end -->
```

Working-dir instructions (e.g. a KB's conventions) → the same marker block in
`workspace/AGENTS.md` (or the KB's own `AGENTS.md` when the capability says so).

**5. Config keys.** Only via `hermes config set <dotted.key> <value>` (add `-p <profile>` for
profile config). Never invent keys — check against `hermes config get <key>` first; a typo'd
key silently deep-merges and does nothing. Record every key you set in the lockfile.

**6. Native code** (`adapters/hermes/plugins/`, §2.4): hooks land in the profile's `hooks/`
dir; standalone programs stay standalone (their own dir under the profile, invoked across a
process boundary). Scripts referenced by `--script` live under `~/.hermes/scripts/`.

**Lockfile.** `.aos/installs.lock.yaml` in the user's aos clone records, per capability and
harness: version, every artifact path written, its sha256, cron job ids under
`schedules_owned`, and every config key set. This is what makes Removal mechanical.

## Introspection guide

To enumerate what exists (powers the importer, §6 — read-only):

- `hermes status` — components, model/provider, which API keys are set (masked).
- `hermes profile list` — all profiles; the Distribution column shows provenance
  (blank = hand-rolled). `hermes profile show <name>` / `hermes profile info <name>`.
- `hermes skills list` (per profile with `-p`); `hermes skills list-modified` and
  `hermes skills diff <skill>` — stock-vs-user-modified divergence, already tracked natively.
- `hermes cron list` (per profile with `-p`) and `hermes cron runs`; job shape lives in
  `cron/jobs.json` (`{jobs: [{id, name, prompt, skills, schedule: {kind, expr…}, deliver,
  enabled, …}]}` — read freely, write never).
- `hermes config show` (defaults-merged view) / `hermes config get <dotted.key>`;
  `hermes doctor` for diagnostics.
- Filesystem truth: `~/.hermes/skills/`, `~/.hermes/profiles/*/`, `~/.hermes/cron/jobs.json`,
  `channel_directory.json` (known channels cache).
- aos-specific: `.aos/installs.lock.yaml` (what aos installed), `x-aos-origin:` frontmatter,
  `aos:` job-name prefixes, `<!-- aos:… -->` markers.

## Secrets

- **Values go into `.env`** — root `~/.hermes/.env` for `main`, the profile's `.env` for a
  profile-scoped secret. Append `KEY=value`; never echo values back into the conversation.
- `auth.json` is Hermes's **provider-credential state** (LLM API pools, fingerprints).
  Installs never write it.
- MOD.md stores **references only** (§3.1): `{store: hermes-env, key: <ENV_VAR>}`. Resolving
  a reference = reading that variable from the owning profile's `.env`.
- Optional external stores (Bitwarden/1Password) exist behind `hermes secrets` — if the user
  says they use one, store there and reference `{store: hermes-secrets, key: …}` instead.
- Skills that need a variable inside sandboxes declare it in SKILL.md
  `required_environment_variables` — Hermes passes it through automatically.

## Removal

Everything comes from the lockfile entry for this capability on this harness — remove in
this order, then verify:

1. **Cron jobs**: `hermes -p <profile> cron remove <id>` for every id in `schedules_owned`.
   Then delete the run artifacts Hermes leaves behind: `cron/output/<id>*` (a live install
   was found with 24 orphaned output dirs from past removals — don't add to them).
2. **Skills**: delete the materialized `skills/<id>/` dir from **every** profile the lockfile
   says received a copy (per-profile copies, not links — removing one place is not enough).
3. **Context blocks**: strip the `<!-- aos:<capability>… -->` marker blocks from `SOUL.md` /
   `AGENTS.md`. Never touch text outside the markers.
4. **Config keys**: `hermes config unset <key>` for every recorded key.
5. **Secrets**: remove the `.env` lines added at install (ask the user first — they may be
   shared with something else).
6. **Profiles**: if the profile was created by this capability *and* the lockfile shows no
   other capability uses it, `hermes profile delete <name>` (removes the whole tree cleanly).
7. **Scripts / plugins**: delete recorded files under `~/.hermes/scripts/` and `hooks/`.
8. Remove the capability's lockfile entry; leave `MOD.md` alone (§3.3 — it survives
   reinstall; deleting it is the user's explicit choice).

Verify: re-run the Introspection steps — no `aos:<capability>` job names, no `x-aos-origin:
<capability>@` frontmatter, no marker blocks may remain.

## Feature notes

`depends.host` vocabulary (§5.2) on Hermes:

| feature | status | notes / degraded translation |
|---|---|---|
| `scheduler` | ✓ native | `hermes cron` (cron/interval/once kinds). Degraded `manual` never needed here |
| `messaging.inbound` | ✓ native | gateway platforms: WhatsApp, Slack, Telegram, Discord, Signal, Mattermost, Matrix. Channel→agent binding via `profile_routes` (`gateway.multiplex_profiles: true`) |
| `messaging.outbound` | ✓ native | cron `--deliver origin|local|<platform>:<chat_id>`; agent-initiated sends via the messaging toolset |
| `voice.stt` / `voice.tts` | ✓ native | `stt`/`tts`/`voice` config sections |
| `calendar.read` / `calendar.write` | ⚠ via skill | not a native primitive — present only if a calendar skill (e.g. a Google-calendar CLI skill) is installed. Check `hermes skills list`; absent ⇒ treat as missing and apply the capability's `degraded:` mode |
| `email` | ⚠ via skill | same story as calendar |
| `secrets-store` | ✓ native | `.env` (+ optional Bitwarden/1Password via `hermes secrets`) |

Degraded modes (§5.5): `manual` ⇒ skip the cron job, materialize the schedule's prompt as an
invocable skill in the same profile and tell the user how to run it; `inline` ⇒ append the
prompt (inside provenance markers) to an existing aos-owned scheduled job's prompt via
`hermes cron edit`; `skip` ⇒ record the skipped schedule in the lockfile so `doctor` can
report it.

Safety rails worth routing through instead of reinventing: `hermes backup --quick` (pre-
install snapshot), `state-snapshots/` (automatic pre-update backups), `hermes doctor`
(drift/diagnostics), `hermes skills diff` (user-modification detection — feeds the §3.3
round-trip), `hermes profile export` (tar.gz of a whole profile before risky surgery).

**Native seam worth knowing** (for future capability authors): Hermes has its own
distribution mechanism — `hermes profile install <git-url>` with a `distribution.yaml`
manifest, distribution-owned vs user-owned paths, and a `local/` customization namespace.
An aos capability that is exactly one agent could ship its Hermes adapter as a profile
distribution and get update/user-data protection natively. v0.1 materializes directly (the
capability→profile mapping is rarely 1:1); revisit if the `adapters/hermes/` volume grows.
