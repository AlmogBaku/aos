# weekly-maintain

For each registered base:

1. **`kb prune --dry-run` first, then `kb prune`.** The dry run lists what would go; read it
   before deleting. This is the only step in this job that destroys anything, and while git
   is the undo, an undo nobody notices they need is no undo — so look at the list rather
   than trusting the count. Deleting what `expires:` already declared needs no user
   confirmation, but a page you did not expect to see there is worth surfacing in step 3.
   If the two runs disagree on what went, stop and file a finding: that means something
   changed the tree between them.
2. `kb lint` — the deterministic catalog runs in the tool and its **stdout is the report**;
   there is no report file, because nothing ever read one. Mechanical fixes you may apply
   directly: `kb index rebuild`. Judgment findings (Contested inventory, duplicate
   suspicions, unverified-with-inbound, grants-audit hits) → `kb pending add --kind finding
   --waits-on human` with evidence and a stated default. Never resolve them yourself.
3. Raise **Critical** findings for the user's next brief — only Critical.
4. Nothing to report → output exactly `ARCHIVER: maintenance clean.` and deliver nothing.
