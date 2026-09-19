---
name: ghostwriter
description: Use when the user wants content ideas, asks to develop or resume a piece, wants to review stalled editorial work, or asks to turn interviews and stored knowledge into Blog, LinkedIn, or X content, and no narrower ghostwriter skill matches. Do NOT use to do the editorial work itself — proposing abstracts is ghostwriter-ingest, drafting and advancing a piece is ghostwriter-develop, reviewing a draft is ghostwriter-critique, and channel variants are ghostwriter-repurpose.
---

# Ghostwriter

The user is the source and final editor. Ghostwriter removes blank-page work and owns the path to a manual-publish-ready bundle.

## Route

Before changing editorial state, run:

```bash
python3 "{{mod: backlog_checker}}" \
  --workspace "{{mod: editorial_workspace}}" \
  --kb-base "{{mod: kb_base}}" \
  --ideas-limit {{mod: ideas_limit}} \
  --pieces-limit {{mod: active_pieces_limit}} \
  --idea-stale-days {{mod: idea_stale_days}} \
  --piece-stale-days {{mod: piece_stale_days}}
```

Exit `0` permits routing. Exit `2`, broken references, or invalid metadata is a hard stop. Archive reported stale items before adding work and surface their titles in the same mutation.

The checker exits `2` for an approval route with any unresolved `unsupported_claims`, `approval_required: true`, uncleared private/sensitive material, or Evidence-map entry marked `needs-confirmation`. For that state the only route is `stop`: surface blockers; do not convert it to `user-decision`, critique, repurpose, or manual approval.

- A scheduled run arrives as a titled session the schedules opened for the user, carrying its own opening prompt — treat the interview one as a user-initiated `interview me` and the editorial one as a user-initiated `resume`, in that session, and never as a reminder.
- `interview me` → hand the request to the shared main agent as `source-interview`; consume only its returned InterviewRecord contract. The main agent owns selection and invocation of any interview capability.
- `content ideas` → use {{skill: ingest}}.
- `develop <idea>` or `let's write <topic>` → use {{skill: develop}}.
- `resume <piece>` → read its `piece.md`, then route its finite `next_action`: `develop` → {{skill: develop}}; `critique` → {{skill: critique}}; `user-decision` or `manual-approval` → surface `## Next action` and wait; `repurpose` → {{skill: repurpose}}; `manual-publish` → return the approved bundle; `none` → report the terminal state.
- User confirms a manual post succeeded → under the workspace lock and fresh preflight, atomically set `status: published`, `next_action: none`, and `last_touched_at`. Never infer publication from returning the bundle.
- `repurpose <piece>` → use {{skill: repurpose}}.
- `what's stalled?` → show stale/blocked items and one next decision each.
- `dismiss <item>` → set `status: dismissed`, move ideas to `archive/ideas/` and pieces to `archive/pieces/`, never delete it.

All mutations use one atomic workspace lock. Before changing state, run `mkdir "{{mod: editorial_workspace}}/.mutation.lock"`; contention means stop or defer. Re-run preflight after acquiring it, and always release it with `rmdir "{{mod: editorial_workspace}}/.mutation.lock"` after success or failure. Never break an existing lock automatically.

Never start a second piece when the active limit is full.

Valid transitions are explicit:

```text
idea: queued → selected | parked | dismissed
piece: developing ↔ waiting → review → approved-manual-publish → published
piece: approved-manual-publish → review  after repurpose
piece: developing | waiting | review → parked → developing | waiting | review
piece: developing | waiting | review | parked → dismissed
```

Any other transition stops and surfaces the current state.

Stale queued ideas are parked under `archive/ideas/<idea-id>.md`: record `parked_from_status: queued`, set `status: parked` and `next_action: user-decision`, and surface the title before releasing the lock. Resume restores `queued` and returns it to `ideas/`. Stale pieces follow the same synchronous rule under `archive/pieces/<slug>/`: record both prior fields, park, surface, then release. Resume restores both fields atomically.

## Workspace

Root: `{{mod: editorial_workspace}}`

```text
ideas/<idea-id>.md
pieces/<slug>/piece.md
pieces/<slug>/assets/       optional
archive/
```

The KB `{{mod: kb_base}}` owns sources. This workspace owns active editorial state.

## Approval boundary

Nothing publishes or schedules externally. The terminal state is `approved-manual-publish`; the user posts it.
