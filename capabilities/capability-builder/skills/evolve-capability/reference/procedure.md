# Major-change procedure

Scaled-down version of capability-builder's flow — skip Intake (the capability and the
feedback already supply the context), keep the rest, sized down:

- **Research** — impact only: what depends on this, what else reads/writes the same
  files or zones, does the change conflict with anything already scheduled/owned
  (single-owner rule).
- **Design** — a diff, not a full proposal: what file(s) change, what's added, what's
  removed, and why. Same bar as a new capability's Design stage — one artifact, not
  scattered across replies.
- **Approval** — nothing applies until the user signs off on the diff.
- **Apply** — same materialization rules as `capability-builder`'s Build stage: the
  change lands in the capability package in the clone; bump the capability's
  `version` per semver. The running install doesn't change until the
  already-specified install/update flow re-renders it — say that explicitly, and
  offer to walk the user into that flow now.

Never installs, never opens a PR on its own — same invariant as everywhere else in this
capability.
