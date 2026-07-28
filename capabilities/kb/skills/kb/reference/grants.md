# Grants reference — the one ACL

## The table

The first markdown table under `## Grants` in each base's `AGENTS.md` — one ACL for
routing, writing and the future permission gate. The columns are parsed, so do not rename
them: `subject | object | verbs | grantor | granted | via | notes`.

- `subject`: a principal id (`alice@acme.com`) · `user` (the single-human case) ·
  `agent:<name>` · `capability:<id>` · `*` (any *registered* subject — an unregistered one
  matches nothing, not even `*`). Rows name principals directly, so this table **is** the
  roster; there is no second list to disagree with it.
- `object`: git-style glob(s), space-separated, relative to the base root (`**` crosses
  `/`, `*` does not).
- `verbs`: a subset of `read write route-into grant`. Default posture is **deny** — no row,
  no verb, `read` included. `grant` is user-only.

## Checking

`kb grants check --subject agent:archiver --verb write --path entities/acme.md` →
GRANTED/DENIED plus exit 0/1. Run it before any non-obvious write. A refusal never loses
data: the payload stays with the caller and `kb refuse --path <p> --subject <s> --reason
<r>` records the attempt as a `kind: refusal` entry in `.kb/pending/`.

## Registering and revoking

At capability install, draft one row per `kb.zones` manifest entry — subject
`agent:<owner_agent>` or `capability:<id>`, object the zone glob, verbs as declared,
`grantor: user`, `granted: <today>`, `via: <capability>@<version>`. Rows land **only after
the user approves the install diff**. At removal, delete the rows whose `via` matches,
record it with `kb commit --verb resolve --path AGENTS.md --summary "revoke <capability> rows"`
(`--path` and `--summary` are both required), and re-run `kb lint`. Expect the audit to keep
flagging the removed capability's *historical* writes for the rest of the window —
revocation is not retroactive amnesty; the `resolve` commit is the answer, and the findings
age out.

## Enforcement, honestly

Three layers, weakest first. **(1)** The self-check at write time — this lookup, which
catches honest mistakes. **(2)** The weekly lint's audit: git authorship crossed against
this table. Every write is its own commit, author = the human principal and committer = the
acting agent, so a write with no matching row is a finding every time and nothing is batched
under one identity to hide behind. Only `bootstrap` is exempt, because it scaffolds the tree
before any row exists. **(3)** The future permission gate at the harness layer, sharing this
vocabulary. Inside one user's harness, agents are cooperating processes; across a trust
boundary, enforcement is the gate's job. On a **shared** base, agent writes land as
proposals in the queue and never directly.

**Reads are not yet enforced by the tool.** `grant_check` is consulted by `kb grants check`
and by the weekly audit — no read verb calls it, so `kb search` and `kb find` will return
what is on disk regardless of this table. Honouring read scope is currently the agent's own
discipline (and, across a trust boundary, the future gate's job). Treat a `read` row as a
statement of what you are *permitted* to look at, not as a wall that will stop you.
