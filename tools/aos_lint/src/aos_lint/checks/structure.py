from ..repo import walk_repo


# Two honesty flags from ARCHITECTURE §2.1 / §5.3 — warnings, not gates —
# plus the §2.5 entry-skill convention.
def check_structure(ctx) -> None:
    for cap in ctx.caps:
        # §2.1: there is no capability-level harnesses/ dir. Cheat-sheets are reference files
        # of the skill that reads them (so they travel with the render and resolve from an
        # installed skill); other per-harness content is adapters/<harness>/.
        if (cap.dir / "harnesses").exists():
            ctx.report("error", "structure/harnesses-dir", cap.rel,
                       "no capability-level harnesses/ dir (§2.1) — a cheat-sheet belongs in "
                       "the consuming skill's reference/ as harness-<runtime>.md, and other "
                       "per-harness content in adapters/<harness>/")
        # §2.5: every capability ships an entry skill named after itself.
        if not (cap.dir / "skills" / cap.id / "SKILL.md").exists():
            ctx.report("error", "structure/entry-skill", cap.rel,
                       f"no skills/{cap.id}/SKILL.md — the §2.5 entry skill is required")
        readme = cap.dir / "README.md"
        if readme.exists() and "|" not in readme.read_text(encoding="utf-8"):
            ctx.report("warn", "structure/support-matrix", f"{cap.rel}/README.md",
                       "no table found — the support matrix lives here (§2.4)")
        adapters_dir = cap.dir / "adapters"
        if not adapters_dir.exists():
            continue

        def size(directory):
            return sum((directory / rel).stat().st_size for rel in walk_repo(directory))

        adapter_bytes = size(adapters_dir)
        total_bytes = size(cap.dir)
        if adapter_bytes > (total_bytes - adapter_bytes):
            ctx.report("warn", "structure/adapter-ratio", cap.rel,
                       f"adapters/ ({adapter_bytes}B) outweighs the neutral core — is this "
                       f"capability actually portable? (§2.1)")
