# No cheat-sheet for your harness?

The install contract is the aos half and holds everywhere; a cheat-sheet only
adds your harness's half. Derive it yourself:

| aos concept | find your harness's |
|---|---|
| agent | isolated persona/workspace primitive (profile, group, agent dir…) |
| front agent (`main`) | the assistant the user already talks to |
| skill | where Agent Skills folders load, **per agent** (`used_by` = per-agent placement) |
| schedule | native cron/job mechanism |
| context block | identity/instruction files it actually consumes — never invent filenames |
| secret | native store (env file, vault, keychain) |
| introspection | how to enumerate all of the above |

1. Introspect your harness: config layout, skills dirs, scheduler, secret store,
   agent primitive — read its docs and CLI help, list what already exists.
2. Draft
   `<home>/upstream/capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-<harness-runtime>.md`
   answering §5.2's six sections (Primitive mapping, Materialization guide, Introspection
   guide, Secrets, Removal, Feature notes — the Hermes sheet the entry skill links is
   the reference shape). Keep it lean: your harness's half only. Write it **on a
   branch** (`git -C <home>/upstream switch -c cheatsheet-<harness>`): a cheat-sheet is
   generic knowledge, not personalization — the clone stays pristine on `main`, and the
   draft is born contribution-shaped. **The branch may already exist**, because step 5 switches
   back to `main` when the operation ends and the next operation routes here again: `switch -c`
   then fails with exit 128. Check first — if the branch is there, `switch` to it (no `-c`) and
   **read the sheet you already wrote** rather than drafting a second one. A sheet exists as
   soon as one operation has finished; re-drafting it from scratch is the failure mode this
   note exists to prevent.
3. Diff gate: show the user the full draft before writing it — then **commit it
   on the branch** (`git -C <home>/upstream add capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-<h>.md`
   + commit). Uncommitted, it would follow you back to `main` as an untracked file in a
   clone that must hold nothing but upstream's own content — and it would fail the
   contribution preflight's clean-status check.
4. Proceed with the operation using your draft (it is in the working tree on that
   branch — do not switch away yet, or the file you are following disappears), telling
   the user the mappings are self-authored and unverified.
5. **When the operation is done, switch the clone back to `main`**
   (`git -C <home>/upstream switch main`): the branch keeps the draft, and a clone left
   on a feature branch stops receiving upstream changes (the upgrader skips the pull
   there by design). After a verified install, it is a ready-made contribution (§5.2): *offer* to open the
   PR per `<home>/upstream/CONTRIBUTING.md` — and only on the user's explicit yes.
