# No cheat-sheet for your harness?

The contract (`contract.md`) is the aos half and holds everywhere; a cheat-sheet only
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

1. **[A]** Introspect your harness: config layout, skills dirs, scheduler, secret store,
   agent primitive — read its docs and CLI help, list what already exists.
2. **[A]** Draft
   `<home>/upstream/capabilities/capability-lifecycle/harnesses/<harness-runtime>.md`
   answering §5.2's six sections (Primitive mapping, Materialization guide, Introspection
   guide, Secrets, Removal, Feature notes — `harnesses/hermes.md` in the same directory
   is the reference shape). Keep it lean: your harness's half only. Write it **on a
   branch** (`git -C <home>/upstream switch -c cheatsheet-<harness>`): a cheat-sheet is
   generic knowledge, not personalization — the clone stays pristine on `main`, and the
   draft is born contribution-shaped.
3. **[D]** Diff gate: show the user the full draft before writing it.
4. Proceed with the operation using your draft, telling the user the mappings are
   self-authored and unverified. After a verified install, it is a ready-made
   contribution (§5.2): *offer* to open the PR per
   `<home>/upstream/CONTRIBUTING.md` — and only on the user's explicit yes.
