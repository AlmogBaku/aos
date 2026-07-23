---
questions:
  - id: existing_kbs
    prompt: Do you already keep knowledge bases (paths to any existing KB/notes repos)?
    type: list
  - id: create_default
    prompt: Should I create a fresh personal base for you?
    type: boolean
  - id: default_base
    prompt: Which base should be the default (where uncertain captures land)?
    type: string
    required: true
  - id: sync_mode
    prompt: How should your bases sync — automatic 5-minute git sync, or manual?
    type: enum
    re_ask: true
---

# kb interview

Runs during bootstrap (step 3) or on first install of any base-touching capability.
The typed answers above land in this capability's MOD.md; the *registry details*
(per-base audience, purpose, channels) and the *structure design* (zones, types —
written into each base's BASE.yaml) are collected by the `init`/`adopt` skills right
after — registry data belongs in the registry, base structure in BASE.yaml, not the
overlay.

Script:

1. **`existing_kbs`** — "Do you already keep notes/knowledge repos an agent should
   know about? Obsidian vault, a notes git repo, a wiki checkout — paths, if so." For
   each path, the `adopt` skill runs next (registration + divergence report, no
   rewrites — promise that out loud, it's the thing users fear).
2. **`create_default`** — if they named no existing base, recommend yes: "a private
   personal base, scaffolded from the shipped templates." The `init` skill's
   *structure interview* follows: theme → zones/types, designed once with the user,
   autonomous afterwards.
3. **`default_base`** — explain what default means: *uncertain captures land there
   with `triage: pending` and get sorted by the nightly drain; nothing is lost,
   latency is never spent on asking you "work or personal?" mid-capture.*
4. **`sync_mode`** — exactly `rebase-5min` or `manual`. `rebase-5min` needs a remote
   and runs as a script-only cron (no LLM); conflicts are never auto-resolved — they
   surface in your review queue. Adopted bases default to `manual` regardless.
5. Anything they say about *what belongs where* ("work stuff never in my personal
   base", "book notes are their own thing") is routing gold — capture it as body
   prose; init/adopt turn it into `purpose` paragraphs and keyword bindings.
