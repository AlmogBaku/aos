# Major-change procedure

Scaled-down version of the {{skill: build}} flow — skip Intake (the capability and the
feedback already supply the context), keep the rest, sized down:

- **Research** — impact only: what depends on this, what else reads/writes the same
  files or zones, does the change conflict with anything already scheduled/owned
  (single-owner rule).
- **Design** — a diff, not a full proposal: what file(s) change, what's added, what's
  removed, and why. Same bar as a new capability's Design stage — one artifact, not
  scattered across replies.
- **Approval** — nothing applies until the user signs off on the diff.
- **Apply** — same materialization rules as {{skill: build}}'s Build stage: names *and*
  reference placement per the `capability-lifecycle` skill's naming rules (a shipped skill
  may only reference paths inside its own folder, and a reference to another skill or agent
  is written as a slot — `\{{skill: <id>}}` — never as a computed name), and
  `aos-cap skills --check` before any
  new skill is written, `skill-creator` for the craft if present (lint
  the tree you actually wrote: `--root <home>/personal` for the user's own packages): the
  user's own package → the change lands in `personal/capabilities/<id>/`;
  upstream-shipped → the change lands on a branch in `<home>/upstream` and continues
  per the contribution mechanics the {{skill: contribute}} skill links. Bump
  the capability's `version` per semver
  either way. The running install doesn't change until the already-specified
  install/update flow re-renders it — say that explicitly, and offer to walk the
  user into that flow now.

Never installs, never opens a PR on its own — same invariant as everywhere else in this
capability; every upstream write waits for the user's explicit yes.
