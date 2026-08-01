---
rfc: 010
title: "Multi-user bases — who ingests, who curates, and who is anybody"
status: open
date: 2026-07-27
decides: whether `audience: shared` describes a working multi-human base or only a repo two people happen to pull
informs: ARCHITECTURE §4.3–§4.4; design/kb-methodology.md §6.5, §7; design/kb-authorization.md §4.1, §4.5, §8
relates: RFC-006 (routing), RFC-007 (subject identity — §8 Q2 is the door this walks through)
---

# RFC-010 — Multi-user bases

## The question

`base == repo`, and `audience: shared` means "a git repo other humans pull". Everything
downstream assumed one human. When several people share a base: **who ingests, who
promotes, and how does each person's material stay theirs?**

The spec had committed to enough of this to be dangerous and not enough to work. It said
shared bases exist, that their grant table "travels with the repo and is visible to every
collaborator", and that a shared base's state is "the team's current-truth — that is a
feature". It also said, in a sibling document, that two distinct authors touching state
inside a lint window is a violation. Both cannot be true of one file.

## Non-goal, stated up front

**Centralized ingestion is out of scope.** A design where one actor ingests on everyone's
behalf loses the property that makes capture good: the capturing agent has the context.
It may be a sensible external offering; it is not this kit's answer, and nothing here
should be read as a step toward it.

## What is decided (and already built)

These were not close calls once the evidence was in, and they are implemented on `main`.

**1. Ingestion stays per-person; only curation is a choice.** Everyone captures with their
own agent. `kb inbox` shows the acting principal's pending captures. Two reasons, and the
second is the serious one:

- N households draining one shared inbox promote the same capture N times.
- One person's raw material otherwise enters another person's agent context — an agent
  holding write access to shared knowledge. That is the primitive Aim Labs named **LLM
  scope violation**: untrusted input acquires the agent's privilege over trusted data. It
  is not hypothetical; it is the shape of every major assistant incident of the last two
  years, and the published audits say internal oversharing outnumbers external roughly 5:1.

**2. A principal is a human, and git already models this.** Author = the person whose
knowledge it is; committer = the acting agent. Rebase preserves the author, forges show it
in `blame`, and no new identity system is invented. **The Grants table IS the roster** — it
names principal ids directly, so a separate `principals:` map would have been a second copy
of the same fact, and the two could disagree. **Absent any row every write is `user`** — so
a private base needs no configuration and nothing changes for it.

This extends the closed subject vocabulary of `kb-authorization.md` §4.1, which is
RFC-007 §8 Q2's territory. **This RFC does not resolve RFC-007.** It records that a shared
base cannot express "each person writes their own area" without *some* principal form, and
offers the cheapest one that works as evidence.

**3. One file per record, everywhere.** The inbox-as-view rule was right and was applied
once. The three artifacts it was not applied to — the log, the review queue, state — were
exactly the three that conflicted on every sync. See kb-methodology §2, §6.5, §7. No merge
driver is used anywhere, deliberately: `merge=union` scrambles order under rebase, dedups
only when hunk boundaries coincide, and forge-side merges ignore `.gitattributes` outright.

**4. Enforcement is by routing method, never by refusing the verb.** A shared base has
`raw/` and accepts explicit and rule-matched captures — §4.3 bars the *method*, and
kb-authorization §6.2 Case 3 walks through an explicit-tagged capture landing in a shared
base. Refusing `kb capture` would have contradicted four normative statements. What was
missing was §4.5's layer-2 check, which had never been built: **zero `method: llm` records
in a shared base, ever**. It exists now.

## What is open

### Q1 — Does CI ever curate, and whose key pays?

The deterministic half of curation is free — the grants audit, the zero-LLM check, index
drift, unattributed commits, left-behind git state, all with no API key. **Promotion is
judgment**, and moving it into CI would need an API key in repository secrets and an answer
to "whose, and who pays". It would also be the neutral curator a shared base otherwise
lacks.

**The deterministic half was built, then descoped.** A CI janitor shipped on `main` — and
`kb init --audience shared` emitted it — under the reasoning that a shared base otherwise
has no neutral actor, and that on the plan a small team actually has, a failing check is the
only enforcement that exists: GitHub gates rulesets, branch protection and CODEOWNERS to
Pro/Team/Enterprise for private repositories, so on the free plan you cannot block a bad
push, only fail it, loudly, every time. **That finding stands.** What did not stand was
shipping it as a decision: it answers the mechanical half while this question — who decides
what gets promoted — is still open, and emitting a workflow implied a shared base has a
neutral actor today, which it does not.

**Descoping the runner is not descoping the checks.** Every check the janitor ran is a
`kb lint` check and runs anywhere — by hand, in a member's own hook, or in an Action they
wire themselves. `lint --ci` survives for exactly that: report-only stays the default, and
the flag is what makes that contract falsifiable.

Against doing it: the external evidence on automatic promotion is bad. GovMem's
verification gate, run over 133 external candidates, concluded *"zero candidates are safe
for automatic promotion"*. A public audit of one agent-memory store found 97.8% of 10,134
entries were junk, with a single hallucinated fact copied 808 times. The archiver's
default-empty promotion and the shared-base review gate are the differentiator here — no
shipped memory system (mem0, Letta, Zep) gates writes into shared memory at all — and a
cheap unattended curator is the obvious way to lose it.

**Deliberately left open.** Today curation is a household's job, in one of two shapes:

| Mode | Grants shape | Cost |
|---|---|---|
| Per-principal (default) | everyone holds capture + propose grants | none — each drains only their own |
| Designated curator | one principal holds the wiki write grants | that household's agent reads everyone's raw material |

> **Reversed 2026-07-29: `curation:` is now a declared field** (`self` | `designated`, plus
> `curator:` naming the person), in `.kb/base.yml`. This paragraph previously refused it on
> rule-of-two grounds, and that reasoning was wrong for a reason worth keeping: the two modes
> are not two *configurations* of one behaviour, they are two different answers to "whose
> queue is this", and the tool has to know which before it can route a single entry. Leaving
> it implicit in the grants table meant the answer had to be *inferred* from an ACL every
> time — and an inference that is usually right is exactly the kind of thing that fails
> silently on the base where it matters. Declaring it costs one line and makes the mode
> greppable, testable, and visible to the person reading their own base's config. The
> rule-of-two bar still holds for a *third* mode.

### Q2 — Does the review gate become a pull request?

`.kb/pending/` is a hand-rolled editorial workflow. Decap CMS ships the same thing as
branch-per-entry plus a PR against markdown-in-git, and branch protection would make
"agents propose, humans apply" genuinely enforced rather than cooperative.

Blocking it: the plan gate above (a private free repo cannot protect a branch at all), and
rate limits — GitHub allows 500 content-creating requests an hour, so a five-minute timer
across a few machines must keep one long-lived branch and PR per machine rather than
opening one per sync. Proposed shape: in-repo queue as the floor, branch+PR documented as
the upgrade for teams with a forge that can enforce it.

### Q3 — Cross-base provenance

A page promoted into a shared base from a capture in someone's private base has a dangling
`origin:`. `origin:` is a bare relative path with no base qualifier and nothing validates
it. `source_origin` is an already-schema-legal, entirely unclaimed raw frontmatter field.
Proposal: `origin:` stays base-local and lint-checkable; `source_origin` carries a
base-qualified reference. Note the appendix of kb-authorization leans against cross-base
addressing, so this needs an explicit decision rather than a quiet adoption.

> **A second consumer (2026-07-29), which raises this from tidy to load-bearing.**
> `work-tracker` stores commitments in their own private base and links each one to the
> project it belongs to — a `project:` field pointing at a page that legitimately lives in a
> *different* base (the work KB). So the dangling reference is no longer only a provenance
> back-pointer an auditor might follow; it is a link a user follows to answer "what is this
> for", and it breaks in the ordinary case rather than the archaeological one.
>
> It also settles what the answer cannot be: **a markdown link does not rescue this.** A
> relative `../acme-kb/…` assumes the two bases sit adjacent on disk, which the registry
> never guarantees and a second machine routinely violates. Only a base-qualified wikilink
> (`[[acme-kb:projects/kubecon]]`) or an absolute URL can work — see kb-methodology §5.4,
> which now states the intra-base/external split explicitly and names this as the gap.
> Two consumers, so the rule-of-two bar for a schema answer is met; the *shape* is still
> this RFC's to decide.

### Q4 — Subtree privacy

There is no way to keep `_raw/` readable only to its owner inside one shared repo.
sparse-checkout and partial clone hide **nothing** (all objects are cloned; they are
performance mechanisms), and neither GitHub nor GitLab has per-branch read ACLs. Only a
separate private repo — optionally wired in as a submodule — puts the boundary where a
server enforces it, and it leaks the path, the URL and the pinned SHA. `git-crypt` works
only for a single-writer directory, since ciphertext cannot be merged at all.

This is why the default posture is what it is: **keep private material in a private base.**
The shared base is for what you meant to share.

## Decision method

Evidence, in the same spirit RFC-006 asks for. Q1 should not be settled by argument: run a
month of a real two-person base with per-principal curation and `lint` run by hand or by
each member's own automation, and count what the review queue actually accumulates and what
a human had to fix. If per-principal curation keeps the queue drainable, CI curation is
machinery nobody needed.

## Process

Q1 blocks nothing — a shared base works today with per-principal curation, and the missing
neutral actor is a known limitation rather than a blocker. Q2 and Q4 are documentation-shaped until
somebody runs a base on a forge that can enforce them. Q3 should be decided before any
capability promotes across bases in anger.
