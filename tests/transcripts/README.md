# Transcripts of real runs

Records of real installs, removals, probes and behavioral runs — the evidence behind the
[`BUILD-GAPS`](../../docs/BUILD-GAPS.md) rows and [`PROTOCOL.md`](../golden/PROTOCOL.md) that
cite them. Historical by nature, and quoted verbatim: `aos_lint.gates.retired` exempts this
directory in its `ALLOW_PREFIX` for exactly that reason, because a record that named the world
as it is now would no longer be a record.

## The one exception: redaction

This repo is public, and verbatimness is a policy about *retired vocabulary*, not about
privacy — the redaction rule ([CONTRIBUTING](../../CONTRIBUTING.md) § the scrub) has no
historical exemption. So one mechanical pass runs over these files, replacing what identifies
a machine with the placeholder vocabulary `aos_lint.golden.normalize` already writes into the
committed snapshots:

| what | becomes |
|---|---|
| an absolute path in the operator's home | `~` |
| a home directory flattened into a filename (tooling rewrites `/` to `-`) | `-<project>-` |
| a synthesized `<user>@<host>.local` principal | `<user>@<host>.local` |
| a numeric uid in a temp path | `/tmp/claude-<uid>` |
| a session/run UUID | `<session-id>` |

Path **structure** survives — that is what these files are evidence about. Only whose machine
it was is dropped. A handful of sentences whose subject *was* the private machine (an mtime, a
working-tree state) were rewritten to state the invariant instead; those are prose edits, not
substitutions, and the [ledger](../../docs/BUILD-GAPS.md) records them.

`aos_lint.gates.privacy` enforces this, with **no exemption for this directory** — the
opposite of the retired-token gate's policy, and deliberately so.
