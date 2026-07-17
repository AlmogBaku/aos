# RFC-004: Install bookkeeping — helper tool or prose all the way down?

**Status:** open · **Decides:** whether the install/upgrade bookkeeping gets a small helper tool

## Settled (not this RFC)

ARCHITECTURE §5.1–5.2 is firm: **the harness's own LLM installs capabilities**, guided by the capability's declarative manifest and a per-harness cheat-sheet. There is no installer program, no code adapters. §5.4 is also firm: every mutation is diff-previewed, recorded in `installs.lock.yaml`, backed up before upgrades, and auditable via `doctor`.

## Question

Who carries the bookkeeping mechanics — hashing artifacts, maintaining the lockfile, rendering diffs, snapshotting backups? The LLM *can* do all of it by following the playbook; the question is whether it *should*.

## Options

1. **Small bookkeeping helper (recommended):** a tiny CLI or script set (shipped in the repo, e.g. `bin/aos-lock`, `aos-diff`, `aos-backup`) that the LLM *calls* during install. It contains zero capability knowledge and zero judgment — pure mechanics. Pros: hashes don't lie, lockfile format stays consistent across harnesses and models, drift detection is trustworthy. Cons: a dependency (needs a shell), a small thing to maintain.
2. **Prose all the way down:** the cheat-sheet playbook instructs the LLM to compute hashes, edit the lockfile, and take backups itself. Pros: zero dependencies, pure-markdown kit. Cons: bookkeeping fidelity depends on prompt adherence — a skipped backup or a hand-waved hash is invisible until it hurts; different models will drift the lockfile format.
3. **Per-harness native mechanisms:** lean on whatever each harness has (git history, its own state dirs), no unified lockfile. Pros: least invention. Cons: `doctor`, drift detection, and the round-trip contract (§3.3) lose their shared substrate.

## Recommendation

Option 1. The line to hold: *judgment in the LLM, mechanics in the helper* — the moment the helper grows an opinion about capabilities, it has failed this RFC.

## Process

Auto-accept per RFC-003 window.
