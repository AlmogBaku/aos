# weekly-maintain

First get the list of bases: read `$AOS_REGISTRY` (or `<home>/personal/kb-registry.yaml`) and
take the `name:` of each entry under `kbs:`. **There is no verb that enumerates the registry**,
so this is the only way — and every command below then carries `--base <name>` explicitly.
That is not decoration: a bare `kb prune` resolves by walking up from the current directory and
then falling back to the registry *default*, so unqualified it would prune the same base once
per iteration and never touch the others.

For each base name:

1. **`kb --base <name> prune --dry-run` first, then the same command without `--dry-run`.**
   The dry run lists what would go; read it before deleting. This is the only step in this job
   that destroys anything, and while git is the undo, an undo nobody notices they need is no
   undo — so look at the list rather than trusting the count. Deleting what `expires:` already
   declared needs no user confirmation, but a page you did not expect to see there is worth
   surfacing in step 3. If the two runs disagree on what went, stop and file a finding: that
   means something changed the tree between them.
2. `kb --base <name> lint` — the deterministic catalog runs in the tool and its **stdout is the report**;
   there is no report file, because nothing ever read one. Mechanical fixes you may apply
   directly: `kb index rebuild`. Judgment findings (Contested inventory, duplicate
   suspicions, unverified-with-inbound, grants-audit hits) → `kb pending add --kind finding
   --waits-on human --title "<what>" --body "<evidence, and the default you would pick>"`.
   **`--body` (or `--file -` for stdin) is required** — an entry with no body is rejected, so
   the evidence is not optional prose, it is the argument. Never resolve them yourself.
3. Raise **Critical** findings for the user's next brief — only Critical.
4. Nothing to report → output exactly `ARCHIVER: maintenance clean.` and deliver nothing.
