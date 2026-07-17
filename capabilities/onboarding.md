# Capability: onboarding

**Tags:** infra · **Build order:** 2 (with kb) · **Seam it proves:** interview → MOD.md; re-runnable diffs; secret references

## Scope

The interview engine every capability's install invokes: reads the target capability's `ONBOARDING.md` (frontmatter = typed questions, body = the conversational script), runs the interview, writes typed answers to `MOD.md` frontmatter and prose nuances to its body, resolves `secret: true` answers into harness-store references. Re-run asks only missing/`re_ask`-triggered questions; `--refresh` re-asks all and shows a diff before writing. Also owns the global `MOD.md` bootstrap (identity, timezone, working hours, sacred time, red lines) — the first interview any new user runs.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

Nothing packaged — this is the biggest genuine gap in the live setup (personalization is hardcoded in `state/SOUL.md` and persona files). Patterns to steal: the "interview me, I hate blank pages" interview flow already proven in Almog's setup; the BOOTSTRAP interview UX of coleam00/second-brain-starter (but re-runnable, never self-deleting).

## Depends

None at runtime (must work before anything else is installed). The installer depends on *it*.

## Onboarding sketch

(Bootstraps itself: the global MOD.md interview.)

## v0.1 acceptance

Install gtd-capture end-to-end: interview → MOD.md → personalized install; re-run produces a no-op diff; `--refresh` round-trips.
