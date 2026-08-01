# Bootstrap: the first five minutes

You are a harness agent setting up aos for your user. There is no installer binary — **you
are the installer** (ARCHITECTURE §5.1). This file is deliberately small: it gets exactly
one capability into your harness — `capability-lifecycle` — and that capability's 10 installed skills
carry everything else.

## The experience

**Step zero — are you in the clone?** If the user pasted the README's install block, yes.
If you got here by reading `BOOTSTRAP.md` on the web, no, and every path below resolves to
nothing:

```
git clone https://github.com/AlmogBaku/aos.git ~/aos/upstream
```

Then follow `~/aos/upstream/BOOTSTRAP.md`, not the web page — §2 reads files out of the
clone. Plain clone, not a fork: a fork is a public write the contract gates on the user's
explicit yes (§1.2 offers it).

**Then welcome your user, before any check or write.** Read the
`capability-lifecycle` entry skill's `## Experience` section now
(`capabilities/capability-lifecycle/skills/capability-lifecycle/SKILL.md`) — it binds every
step below. In your own words: what aos is (batteries for the harness they already run),
what happens next (~5 minutes: a short interview, then installs), and the two promises —
*their answers become their `MOD.md`, theirs forever in their own private repo; nothing
lands without a visible diff*. Take questions, then proceed. The diff gate is the safety
net, not repeated consent prompts.

## 0. Prerequisites

- `git --version` — missing → friendly stop with an install pointer (you likely couldn't
  have cloned without it).
- `uv --version` — **required**: it carries the `aos-cap` bookkeeping tool. Missing →
  offer the official installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`), run it
  with the user's OK, verify; if they decline, stop honestly — the lockfile discipline
  cannot be prose.

## 1. The household

aos lives in one directory — **the household**, `~/aos/` by default (a plain directory,
itself never a git repo; the user may name another location — every path below shifts
with it, and `aos-cap --home` pins it). Two members, plus machine state:

```
~/aos/
├── upstream/    # this clone — the kit, pristine; NOTHING personal ever lands here
├── personal/    # the user's ONE private repo: answers, tweaks, private capabilities
├── vendor/      # third-party skills aos references, not ships (created on demand)
└── .aos/        # machine-local state (lockfile) — created by aos-cap init
```

Vocabulary for the user, if they ask: `upstream/` (and future org roots) are
*distributions*; `personal/` is *their instance* — it syncs across machines via its
private remote; only `.aos/` is machine-local.

1. Confirm the clone is at `~/aos/upstream` and clean (`git -C ~/aos/upstream status`).
   Not there at all → clone it now (the Experience section's step zero); it landed
   elsewhere (e.g. `~/aos` directly — the pre-household shape) → stage the move:
   `mv ~/aos ~/aos-kit && mkdir ~/aos && mv ~/aos-kit ~/aos/upstream` (a directory can't
   be moved inside itself in one step).
2. Remotes: `origin` = canonical is all this install needs. Mention once that contributing
   later means forking (`gh repo fork --remote`) — an offer, never something you run. No
   `gh`, or unauthenticated → say so and move on; it blocks nothing.
3. Create the personal root: `git init ~/aos/personal`, seed the mirrored shape
   (`capabilities/` directory).
   Then check the commit identity: `git -C ~/aos/personal config user.email`. Empty, and
   no global one either (`git config --global user.email`) → **ask the user** for the name
   and email to commit as, and set them — globally if they're happy with that, otherwise on
   this repo. Never invent one: a synthesized address credits a real stranger, and every
   render and MOD write from here on is a commit. A *global* identity is also the one kb's
   tool ends up falling back to for the human principal of every base write — it resolves
   `$AOS_PRINCIPAL_ID`, then `~/aos/.aos/kb-principal.yml`, then that base repo's own git
   identity — and with none of the three it synthesizes a weak `<user>@<host>.local`
   without ever asking. Offer — don't push — a private remote for backup/sync
   (`gh repo create aos-personal --private` when `gh` is available; skippable, add one
   any time). Everything personal (MOD files, rendered skills, private capabilities)
   will live and be auto-committed here.

## 2. Install the capability-lifecycle capability (inline — the only one)

1. Read
   `capabilities/capability-lifecycle/skills/capability-lifecycle/reference/contract.md`
   **in full** — it is the install contract binding this step and every install after.
2. Read `capabilities/capability-lifecycle/CAPABILITY.md` (the briefing), then:
   `uv tool install --from ~/aos/upstream/capabilities/capability-lifecycle/tool aos-cap`
   and `aos-cap --home ~/aos init`.
3. Load your cheat-sheet: `capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-<harness-runtime>.md`,
   where the **harness runtime** is the program hosting you (OpenClaw →
   `…/reference/harness-openclaw.md` · Hermes → `harness-hermes.md` · NanoClaw →
   `harness-nanoclaw.md` · Nanobot → `harness-nanobot.md`; Claude Code and OpenCode
   have no sheet yet). None for your harness → follow the entry skill's
   `reference/no-cheatsheet.md` — do not stop.
4. **Name gate**, then STAGE the ten skills per the contract (mechanical — they have no
   `{{mod}}` slots):
   `aos-cap --home ~/aos skills ~/aos/upstream/capabilities/capability-lifecycle --check
   --harness-skills <each skills dir your harness reads, per the cheat-sheet>` — exit 17
   means one of the names is already taken in this harness; stop and report it rather than
   renaming anything. Then `aos-cap render ~/aos/upstream/capabilities/capability-lifecycle
   <skill-id> --out ~/aos/personal/capabilities/capability-lifecycle/skills` for each of the
   ten, plan the symlinks (each render's own directory name) into your front agent's skills
   dir → **GATE** (show the user the plan) → **EXECUTE** (commit the render in `personal/`,
   create the links) →
   `aos-cap record capability-lifecycle --version <manifest version> --source-root upstream
   --artifact <render-file>… --link <symlink>…` — render files go to `--artifact` (hashed),
   symlinks to `--link` (a symlink passed as `--artifact` fails: exit 16).
5. Then the briefing's remaining items: the **mode-boundary context block** on your identity file,
   the **global bootstrap interview** (§3 runs it), and **`skill-creator`** — referenced,
   not copied, and best-effort: if the clone or plugin install fails, say so and continue.

## 3. Hand over

The lifecycle skills are live — from here `install <capability>` triggers
`capability-install`. Two things left:

1. **The global interview** — run `capability-onboard` against this capability's own
   `ONBOARDING.md`: identity, timezone, working hours, sacred time, red lines →
   `~/aos/personal/MOD.md`. Copy none of it into your identity file: the harness already
   owns user context, `MOD.md` is authoritative. This is the user's first experience of
   aos — take the Experience section seriously here.
2. **kb**, as an ordinary install — its interview + KB setup (adopt existing KBs / init a
   fresh one → `~/aos/personal/kb-registry.yaml`).

Close per the Experience section: what was installed, where, which schedules, any
degraded modes — specific and celebratory. Everything after is on demand:
`install <capability>` · `update` · `remove <capability>` · "change how X behaves" — all
skills now, no file re-reading required.
