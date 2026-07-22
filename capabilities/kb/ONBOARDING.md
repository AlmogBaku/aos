---
questions:
  - id: existing_kbs
    prompt: Do you already keep knowledge bases (paths to any existing KB repos)?
    type: list
  - id: create_default
    prompt: Should I create a fresh personal KB for you?
    type: boolean
  - id: default_kb
    prompt: Which KB should be the default (where uncertain captures land)?
    type: string
    required: true
  - id: sync_mode
    prompt: How should your KBs sync — automatic 5-minute git sync, or manual?
    type: enum
    re_ask: true
---

# kb interview

Runs during bootstrap (step 3) or on first install of any KB-touching capability. The
typed answers above land in this capability's MOD.md; the *registry details* (per-KB
audience, purpose, channels) are collected by the `init`/`adopt` skills right after and
land in `kb-registry.yaml` — registry data belongs in the registry, not the overlay.

Script:

1. **`existing_kbs`** — "Do you already keep notes/knowledge repos an agent should know
   about? Obsidian vault, a notes git repo, a wiki checkout — paths, if so." For each path
   given, the `adopt` skill runs next (registration + divergence report, no rewrites —
   promise that out loud, it's the thing users fear).
2. **`create_default`** — if they named no existing KB, recommend yes: "a private
   `personal` KB, scaffolded from the shipped methodology." If they named KBs, still
   offer — some users want a fresh kit-native KB beside the adopted ones.
3. **`default_kb`** — explain what default means: *uncertain captures land in this KB's
   inbox and get sorted later; nothing is lost, latency is never spent on asking you
   "work or personal?" mid-capture.* Default: the created/first KB.
4. **`sync_mode`** — options are exactly `rebase-5min` or `manual`. `rebase-5min` needs a
   remote; conflicts are never auto-resolved, they surface to you. Adopted KBs default to
   `manual` regardless (opt-in only). `re_ask` because infrastructure choices drift.
5. Anything they say about *what belongs where* ("work stuff never in my personal KB",
   "book notes are their own thing") is routing gold — capture it as body prose; the
   init/adopt skills turn it into `purpose` paragraphs and keyword bindings.
