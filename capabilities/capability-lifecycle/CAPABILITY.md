---
id: capability-lifecycle
version: 0.3.3
tags: [infra]
summary: The capability lifecycle as one capability — install, upgrade, remove, onboard, import, build, contribute, evolve, and review as skills for the front agent; the MOD.md overlay with its promote/retire exit side; the household layout with pinned renders and symlink installs; the per-harness cheat-sheets; and the aos-lock tool that owns the lockfile and computes every skill's installed name.
skill_prefix: capability-
skills:
  - id: capability-lifecycle
    used_by: [main]
  - id: install
    used_by: [main]
  - id: upgrade
    used_by: [main]
  - id: remove
    used_by: [main]
  - id: onboard
    used_by: [main]
  - id: import
    used_by: [main]
  - id: build
    used_by: [main]
  - id: contribute
    used_by: [main]
  - id: evolve
    used_by: [main]
  - id: review
    used_by: [main]
---

# capability-lifecycle — the installer's briefing

You are reading this at bootstrap, installing the capability that will make every later
install a skill. This is the only capability `BOOTSTRAP.md` installs inline (the
chicken-and-egg break); everything else goes through the `capability-install` skill
afterwards. The household is already in place when you get here (BOOTSTRAP §1):
`<home>/upstream` this clone, `<home>/personal` the user's private repo, `<home>/.aos`
machine state, and `<home>/vendor` for third-party skills this capability references.

## What you materialize

1. **The `aos-lock` tool first**:
   `uv tool install --from <home>/upstream/capabilities/capability-lifecycle/tool aos-lock`
   (`uv` is a hard bootstrap prerequisite). Then `aos-lock --home <home> init` creates
   the lockfile — the tool's file from this moment on; you call verbs, you never edit
   the YAML.
2. **All ten skills to the front agent** (`used_by: [main]` throughout), per your
   cheat-sheet (the entry skill's `reference/harness-<harness-runtime>.md`; none for your
   harness → its `reference/no-cheatsheet.md`). The skills are
   `{{mod}}`-slot-free, so the render is purely mechanical — `aos-lock render` does it,
   one skill at a time, into `personal/capabilities/capability-lifecycle/skills/…`
   (committed), plus symlinks into the front agent's skills dir. Read
   `reference/contract.md` in full before this step (household resolution, installed
   names, provenance, STAGE→GATE→EXECUTE, the persist hook) and `reference/naming.md`
   for the identity rules the tool enforces.
3. **The global bootstrap interview.** This capability ships `ONBOARDING.md` +
   `MOD.example.md`, and its subject is the *user*, not this capability's behaviour:
   identity, timezone, working hours, sacred time, red lines, diff-review preference.
   Run it through the `capability-onboard` skill you just installed — it writes the root
   `MOD.md` every other capability's transform reads. This is why the ten skills being
   slot-free matters: the inline install is mechanical, and personalization arrives
   immediately afterwards, from the same capability.
4. **One context block** on the front agent's identity file (on Hermes: `SOUL.md`), inside
   its marker pair per `reference/contract.md`:
   - `aos:capability-lifecycle:mode-boundary@<ver>` — the MARS building-mode boundary
     (ARCHITECTURE §9), materialized verbatim:

     > Mode boundary (MARS): before creating any cron job, scheduled task, recurring
     > reminder, persona, or standing automation in response to a conversational
     > request, stop and follow the `capability-build` skill — say what you noticed
     > and ask "Hey, should we plan it methodically?" first. Proceed ad hoc only if
     > the user declines. One-off tasks are unaffected, and so is changing something
     > aos already installed (a schedule, a threshold, a preference) — that is
     > `capability-evolve`, not building.

     The carve-out earns its place: without it the block fires on "change my drain time",
     which is the overlay round-trip, not a new automation — found in the 0.3.0 e2e.
     This block is the detector's teeth. A skill description is pull-context (consulted
     only when the model thinks to), but a harness with a native cron tool will satisfy a
     schedule-shaped ask the shortest way and never consult it — so the boundary must be
     push-context, always present. Found the hard way in the first live e2e.

     **And that is the only block.** Do not distil the user's identity facts — timezone,
     working hours, sacred time, red lines — into the front agent's file. Every harness in
     scope already owns user context (Hermes: `memories/USER.md`, maintained by its own
     always-active memory), so writing them again would be a second source of truth for
     facts we do not own, in an agent aos did not create, that nothing in the kit reads.
     `MOD.md` stays the authoritative store, read at render time. Agents aos *creates* are
     the opposite case: their identity file is written whole, by us, because they have no
     other source.
5. **`skill-creator`, by reference — never copied in.** Anthropic's skill-authoring
   skill (`github.com/anthropics/skills`, Apache-2.0) is what `capability-build` and
   `capability-contribute` lean on for generic skill craft. Install it the way the
   harness prefers, and make sure it is current:
   - The repo is a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) —
     where the harness has a plugin mechanism, use it (`/plugin marketplace add
     anthropics/skills`, then install `skill-creator`).
   - Otherwise: `git clone --depth 1 https://github.com/anthropics/skills
     <home>/vendor/anthropic-skills` and symlink `skills/skill-creator/` into the front
     agent's skills dir — never a copy, the same rule our own renders follow. Updating is
     `git -C <home>/vendor/anthropic-skills pull --ff-only`; the clone's
     `git rev-parse HEAD` is its version, so nothing new is recorded in the lockfile
     schema.
   - Record it under **this** capability so `verify` sees drift, `remove` unlinks it, and
     the collision gate recognizes the name as ours on the next install instead of
     reporting a conflict against itself. The clone path records both (`--link` the
     symlink, `--artifact` the vendored `SKILL.md`); the plugin path creates no symlink of
     ours, so record the harness's installed `SKILL.md` as an `--artifact` and say in the
     summary that the harness owns its lifecycle.
   - **Best-effort, never a gate**: no network, no git, or a declined plugin install →
     say so in the install summary and carry on. Our procedure stands on its own; this is
     an aid, exactly as a cheat-sheet is.
   - It is **not** a render: no `{{mod}}` slots, no `x-aos-origin` stamp (it is not ours
     to tag), and it does not live under `personal/capabilities/`.
6. Nothing else: no agents, no schedules, no KB zones.

## Why it is shaped this way

- **One capability, not four.** `onboarding`, `importer`, and `capability-builder` were
  absorbed here because they were carving one subject. The authoring skills share an
  invariant word for word — read-only on the live harness, write-only into a draft under
  `personal/capabilities/<id>/`, never install, never open the PR — and `capability-build`'s
  mechanism/nuance split is `capability-import`'s in reverse. Four documents describing
  one flow is a seam that costs more than it buys.
- **Building mode is still a boundary; it is just not a package boundary** (§9). Its teeth
  are the push-context block above plus the detector skill, and both survive the merge
  intact. The honest cost: the boundary now reaches consume-only users too, because
  BOOTSTRAP installs this capability for everyone.
- **Skill ids are action-oriented and short** (`install`, `evolve`, `contribute`); agents
  are role-oriented (`archiver`, `drainer`). The id is capability-local — the name that
  ships is `<skill_prefix><id>`, computed by `aos-lock skills`. That is why the id here is
  `install` and not the old `capability-installer`: the prefix carries that meaning now, so
  the id must not repeat it. Full rules in `reference/naming.md`.
- **A skill name is single-owner.** Harnesses keep one flat skill namespace, so two
  capabilities shipping one name is a silent override. `aos-lock skills --check` is the
  gate — against every capability in the household, the lockfile's recorded links, and the
  skills the harness already has. A collision is fixed by renaming in the package, never
  at install time.
- The ten skills are the runtime face of ARCHITECTURE §5–§6 and §9 plus
  design/install-flow.md §2–§4; the entry skill carries the shared depth (`reference/`)
  and the Experience rules every lifecycle interaction obeys.
- **`capability-evolve` is a two-way door**: personalization flows in (the MOD), and
  generally-useful mechanism flows out — promotion (signal-gated) to `capability-contribute`,
  and retirement closing the loop when upstream absorbs a line. The judgment lives once,
  in the entry skill's `reference/overlay.md`.
- Renders are **pinned** (committed in `personal/`) because filling `{{mod}}` slots is
  agentic even though the copy is not: the commit is the render's lockfile, upgrades review
  as a git diff, and rollback is `git revert`. Harnesses symlink to the one canonical
  render — never copies.
- The cheat-sheets live here because these skills are their only consumer; each is lean —
  the harness half only — and points back at `reference/contract.md` for the aos half.
- `aos-lock` is deterministic bookkeeping only (§2.4): manifest parse/validate, installed
  names and the collision gate, the mechanical render, and the lockfile verbs. Judgment
  stays with you; hashes and names never do.

## Contracts to preserve

- **Nine skills scoped to `main`** trips the linter's `skill/all-main` warning. That is
  deliberate: every one of them is a front-agent skill, and §2.2's anti-pollution rule is
  about bodies an agent never uses. The cost is ten descriptions in the front agent's
  context, which is what the entry skill's map is for.
- **Only `capability-onboard` writes `MOD.md` files.** Re-runs ask only unanswered or
  `re_ask` questions; `--refresh` re-asks all and shows a diff before writing. Nothing
  self-deletes (§3.2). Secret values live in the harness store, never inline.
- **`capability-import` and `capability-build` are read-only on the live harness** and
  write only into drafts they own — no file moves, no cleanups, ever. Secrets are flagged
  by name, never copied by value.
- **Nothing durable without an approved design.** `capability-build` never writes a
  capability's files without an explicit, user-approved design; research subagents are
  investigative only. The detector fires on use-case-shaped language (recurring,
  systemic, "build me something that persists") and never on one-off task language, even
  when the wording contains add/create/make — gating everything trains the user to stop
  reading what they approve.
- **No upstream write without explicit approval** — no PR, issue, +1, push, fork, or
  remote branch. Build and `capability-contribute` produce a package under the user's
  `personal/` root and say so; the install flow picks it up from there. The graduation
  flow's PR opens only on the user's explicit confirm. `capability-evolve`'s small path is
  the one deliberate exception to "materialize, don't install": it adjusts the user's own
  overlay answers (through `capability-onboard`, the only MOD.md writer) and syncs the live
  artifact those answers personalize — the §3.3 round-trip, not an install.
- **Building mode is a procedural mode-switch `main` enforces on itself**, not a
  materialized agent — no harness here exposes a live conversation-handoff primitive, so
  the boundary lives in prompt-level instruction, not a process boundary.
- **Nothing personal lands in a shippable file** — intake nuance splits into the package's
  interview questions and the user's own MOD.md, exactly the mechanism/nuance split
  `capability-import` performs in reverse.
- Small evolve-feedback is applied directly and summarized afterward, never silently.

## Upgrading from the pre-merge layout

A household installed before 0.3.0 has four lockfile entries where there is now one
(`capability-lifecycle`, `onboarding`, `importer`, `capability-builder`) and skills under
the old names. `capability-upgrade` walks it: unlink the absorbed capabilities' skill
links, `aos-lock remove <capability>` each absorbed entry, then render and record the
merged one. The old `aos:capability-builder@…` marker is replaced by the single
mode-boundary block above; `aos:onboarding@…` — the distilled identity block — is
**removed outright, not renamed** (item 4: the harness owns user context). This is a
documented walk, not an automated migration — no released users exist yet.

## Removal

`aos-lock show capability-lifecycle` → delete the ten skill symlinks and the
`skill-creator` link, then the render dirs in `personal/` via a commit → remove the
`aos:capability-lifecycle:*` context blocks → `<home>/vendor/anthropic-skills` if nothing
else uses it → `uv tool uninstall aos-lock` → the lockfile entry is the last thing
standing. Removing this capability last, after every other capability is removed, is the
only safe order — the other removals need its skills and its tool.
