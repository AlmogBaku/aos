# RFC-005: MOD.md persistence model

**Status:** resolved 2026-07-25 (proposed — closes after the dogfood period) · **Decides:** how users' `MOD.md` files are versioned and survive `git pull`

## Resolution: the `personal/` repo (the household layout)

The overlay's durable home is **one private git repo — `~/aos/personal/`** — sibling to a pristine kit clone (`~/aos/upstream/`) in the aos household (ARCHITECTURE §3.1). It holds, at mirrored capability paths: the ledger (`MOD.md` global + per-capability, `kb-registry.yaml`), the **pinned renders** (rendered artifacts, tracked — the agentic transform's lockfile-equivalent), and the user's **private capabilities** as full §2.1 packages. The lifecycle skills auto-commit it after every ledger write with a dated message; harnesses symlink into it (§5.3). Bootstrap creates it (`git init` + an offered private remote) before the first interview.

Why this shape won:

- **Private capabilities are git-native source, so a private repo must exist anyway** — one persistence mechanism instead of two.
- **The render is agentic (non-deterministic), so its output deserves pinning**: upgrades become intentional — review is a `git diff` in the user's own repo, `git revert` is rollback (§3.4).
- **The clone stays permanently pristine** — nothing personal in it, not even untracked files. The option-2 footgun (`git clean` eats nuances) dies structurally, and every branch cut from the clone is clean by construction, which is what makes the one-workflow contribution story (CONTRIBUTING) mechanical.
- **Leak-proofing is by construction, not discipline**: the personal repo's only remote is private; public-facing repos never contain overlay paths.
- **The graduation seam falls out**: promoting a private capability = duplicate the package onto an upstream branch (tap→core shape, §9); future org "distributions" are further sibling roots (§1.1).

Vocabulary: sibling source roots are *distributions*; `personal/` is *your instance* — it syncs across machines via its private remote; the machine-local state is `~/aos/.aos/`.

## Alternatives considered (kept for the record)

1. **Tracked in a private fork of the whole kit** (original option 1): one repo holds everything, but the user's daily git life points away from upstream (fork-to-personalize in disguise — the exact disease the overlay exists to cure), every upstream release must be woven into a mixed history, contribution requires untangling, and a wrong push publishes personal content. Documented as a solo-operator pattern only. Its `aos contribute` clean-branch tool parenthetical is superseded: the clean-branch step involves the self-containment scrub (judgment), so the mechanics ship as skill knowledge, not a tool (no-program-anywhere).
2. **Gitignored + `aos backup`** (original option 2): simplest, but no history/sync and the `git clean` footgun; also gitignoring MOD would have hardcoded a persistence choice into the kit repo.
3. **Nested/two-gits overlay repo over the clone** (original option 3, refined): a second git dir tracking only overlay paths in place. Leak-proof and clone-co-located, but nonstandard git ceremony, and it leaves renders and private capabilities unsolved — the household subsumes it.
4. **KB-mirror**: mirror the overlay into the default private KB (`.aos/` tree). Zero git knowledge required and one personal-data plane — but capability *source* doesn't belong in a knowledge store, and it leaves private capabilities needing a repo anyway. Remains the fallback idea for a future zero-git on-ramp.
5. **Encrypted overlay branch in the public fork** (chezmoi/age pattern): one repo total, cryptographic privacy — but key loss is fatal, history is opaque, and the psychological bar of "my life on public GitHub, encrypted" is real.

## Evidence & process

Adopted with the household layout during the one-way-of-working build (2026-07-25); the owner's live migration + a real promotion round-trip are the dogfood evidence. Per RFC-003, the proposed resolution closes after that period absent counter-evidence (lost files, dirty PRs, link breakage on a harness).
