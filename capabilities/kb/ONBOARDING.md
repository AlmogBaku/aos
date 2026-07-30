---
questions:
  - id: principal_id
    prompt: What email should your knowledge be attributed to?
    type: string
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
  - id: curation
    prompt: On a base several people write to, does each person review their own captures, or does one designated curator review everyone's?
    type: enum
---

# kb interview

Runs during bootstrap or on the first install of any base-touching capability. The typed
answers land in this capability's MOD.md. Registry details (per-base audience, purpose,
channels) and structure design (zones, types) are collected by the `kb-init` and `kb-adopt`
skills right afterwards — registry data belongs in the registry and base structure in
`.kb/base.yml`, not in the overlay.

1. **`principal_id`** — the tool already wrote `<home>/.aos/kb-principal.yml` on its first
   verb call, detected from `git config user.email` or synthesized. Show them what it found
   and ask if it is right: *"writes will be attributed to `<detected>` — is that the address
   you want your knowledge under?"* One person is not one identity, so if they name a work
   address too, record both — the file is a list matched against base names, first match
   wins, and a bare `*` belongs last. This is the only place the asking happens: the tool
   never prompts, because capture must not wait on a tty a cron does not have.
2. **`existing_kbs`** — "Obsidian vault, a notes git repo, a wiki checkout — paths, if so."
   For each path the `kb-adopt` skill runs next: registration plus a divergence report, and
   no rewrites. Promise that out loud, it is the thing users fear.
3. **`create_default`** — if they named nothing, recommend yes: a private personal base
   scaffolded from the shipped templates. The `kb-init` skill's structure interview follows.
4. **`default_base`** — explain what default means: *uncertain captures land there and get
   sorted by the archiver overnight; nothing is lost, and latency is never spent asking you
   "work or personal?" mid-capture.*
5. **`sync_mode`** — exactly `rebase-5min` or `manual`. `rebase-5min` needs a remote and
   runs as a script-only cron; conflicts are never auto-resolved, they land in the queue.
   Adopted bases default to `manual` regardless.
6. **`curation`** — exactly `self` or `designated`, and only relevant once a base is shared.
   `self` (the default) means each person's agent ingests their own captures. `designated`
   names one curator whose agent drains everyone's — which also means that agent reads
   everyone's raw material, so say so plainly before they pick it.
7. Anything they say about *what belongs where* ("work stuff never in my personal base",
   "book notes are their own thing") is routing gold — capture it as body prose, and
   init/adopt turn it into `purpose` paragraphs and keyword bindings.
