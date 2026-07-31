# Contributing upstream — the mechanics

One workflow for everyone: maintainers and first-timers differ only in where their
branches live. Everything below drafts and *offers*; nothing leaves the machine —
no PR, no issue, no +1, no push, no fork, no branch on a remote — without the user's explicit yes (the invariant in
this skill and the install contract).

## The ledger search (before judging generality alone)

The user cannot see demand; the upstream issue tracker can. Before offering any rung:

```
gh issue list --repo <canonical> --label promotion-signal --search "<gap keywords>"
```

- **Match** → the user is the *second* person to need this: the rule of two fires,
  a PR is warranted, and the PR body references the issue.
- **Near-match** → offer to +1 the existing issue instead of filing a new one.
- **No match** → the lightest rung is a new signal issue, not a PR (below).

## The issue-first path (signal issues)

For uncertain-generality promotions and gaps: draft a `promotion-signal` issue —
title the *gap* in upstream's vocabulary, one paragraph of mechanism, zero personal
context (no names, employers, schedules, tools-they-happen-to-use). This also
satisfies the agent-contribution policy in CONTRIBUTING: non-trivial agent-drafted
PRs need an accepted issue first. Show the draft; file only on explicit yes.

## The PR path

1. **Preflight**: `git -C <home>/upstream status` clean, on `main`; canonical remote
   reachable (`upstream` remote, or `origin` on a plain clone); a PR-capable remote
   available — the user's public fork, or canonical itself with push rights. Neither
   and a PR is the goal → *offer* `gh repo fork --remote` (one command — but a fork
   creates a repo on their account and a public fork event, so it runs only on their
   explicit yes, like every other outward write).
2. **Branch from canonical main** (`git fetch <canonical-remote> && git switch -c
   <topic> <canonical-remote>/main`) — never from a possibly-stale local main. One
   change per branch.
3. **Only the source change on the branch.** The clone contains nothing personal by
   construction (the household), so the branch is clean by construction — keep it
   that way: no overlay-family paths, ever (upstream CI rejects them regardless).
4. **The self-containment scrub** (judgment — this is why these mechanics are prose,
   not a tool): promoted content is genericized. No real names, companies,
   relationships; no actual KB content; `ONBOARDING.md` ships *questions*,
   `MOD.example.md` ships invented placeholders. When in doubt, redact.
5. **Gate** (run from `<home>/upstream`): `bash tools/check.sh` green; bump the
   capability's `CAPABILITY.md` `version` and confirm with
   `uv run --project tools/aos_lint python -m aos_lint.cli --base <canonical-remote>/main`
   — on a fork,
   `origin/main` is the fork's stale default and compares against the wrong base.
   Install output changed → the goldens note in CONTRIBUTING applies (a real
   re-render, never simulated).
6. **Dogfood**: with the branch checked out, run a per-capability upgrade — the
   version bump makes {{skill: upgrade}} see the work; the user now runs the
   change for real. Post-merge caution: if review altered files after dogfooding,
   re-bump (or force a re-render) so the upgrader re-fires.
7. **The PR**: draft the body — what/why in upstream's vocabulary, the referenced
   signal issue if any, a BUILD-GAPS row if a spec gap surfaced, agent-drafted
   disclosure per CONTRIBUTING, DCO sign-off (`git commit -s`). Push the branch to
   the PR-capable remote and `gh pr create` **only on the user's explicit yes** —
   show the final body first.

## After it merges

The user pulls and upgrades like everyone else; if the contribution grew from a
MOD statement, the upgrader's retirement pass offers to delete the now-redundant line
(the loop closes). If review stalls or declines: the change lives on happily in
`personal/` — a respectable steady state, not a failure.
