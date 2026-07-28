# weekly-maintain

For each registered base:

1. `kb prune` — delete what has expired and record what went. Git is the undo, so this needs
   no confirmation; read the report and mention anything surprising.
2. `kb lint` — the deterministic catalog runs in the tool and its **stdout is the report**;
   there is no report file, because nothing ever read one. Mechanical fixes you may apply
   directly: `kb index rebuild`. Judgment findings (Contested inventory, duplicate
   suspicions, unverified-with-inbound, grants-audit hits) → `kb pending add --kind finding
   --waits-on human` with evidence and a stated default. Never resolve them yourself.
3. Raise **Critical** findings for the user's next brief — only Critical.
4. Nothing to report → output exactly `ARCHIVER: maintenance clean.` and deliver nothing.
