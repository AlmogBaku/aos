from ..constants import OVERLAY_BASENAMES, OVERLAY_EXEMPT_PREFIXES, STATE_DIR
from ..frontmatter import read_frontmatter
from .onboarding import question_ids


# ARCHITECTURE §3.1 — THE inviolable contract. Upstream never ships, writes,
# or merges any overlay-family path. tests/fixtures/ simulates the *user
# clone* (where those files legitimately live), hence the exemption.
def check_overlay_paths(ctx) -> None:
    # The overlay family is banned from UPSTREAM; a personal root is where it belongs
    # (ARCHITECTURE §3.1), so linting one skips this check rather than inverting it.
    if ctx.personal_root:
        return
    for rel in ctx.files:
        if any(rel.startswith(p) for p in OVERLAY_EXEMPT_PREFIXES):
            continue
        base = rel.rsplit("/", 1)[-1]
        if base in OVERLAY_BASENAMES:
            ctx.report("error", "overlay/shipped", rel,
                       f'"{base}" is user-owned overlay family — upstream must never contain '
                       f"it (ARCHITECTURE §3.1)")
        if STATE_DIR.rstrip("/") in rel.split("/"):
            ctx.report("error", "overlay/state-dir", rel,
                       f"{STATE_DIR} is machine-local state — never committed")


# MOD.example.md (shipped seed) and fixture MOD.md files validate against the
# owning capability's ONBOARDING.md questions — the single source of schema.
def check_overlay_schemas(ctx) -> None:
    targets = []
    for rel in ctx.files:
        base = rel.rsplit("/", 1)[-1]
        if base == "MOD.example.md":
            targets.append(rel)
        elif base == "MOD.md" and any(rel.startswith(p) for p in OVERLAY_EXEMPT_PREFIXES):
            targets.append(rel)
    for rel in targets:
        parsed = read_frontmatter(ctx.root / rel)
        if parsed.error:
            ctx.report("error", "overlay/parse", rel, parsed.error)
            continue
        data = parsed.data
        if not data:
            continue  # a body-only MOD file carries prose nuance, no typed answers
        if not data.get("capability"):
            ctx.report("error", "overlay/capability", rel,
                       "frontmatter must name its capability")
            continue
        # Global MOD.md validates against the onboarding capability's own questions.
        cap_dir = ctx.root / "capabilities" / str(data["capability"])
        ids = question_ids(cap_dir)
        answers = data.get("answers") or {}
        if ids:
            for key in answers:
                if key not in ids["all"]:
                    ctx.report("error", "overlay/answer-key", rel,
                               f'answer "{key}" matches no ONBOARDING.md question of '
                               f'"{data["capability"]}"')
            # The shipped example must exercise every required question, so the
            # installer's golden path is demonstrated.
            if rel.rsplit("/", 1)[-1] == "MOD.example.md":
                for req in sorted(ids["required"]):
                    if req not in answers and req not in ids["secret"]:
                        ctx.report("error", "overlay/answer-missing", rel,
                                   f'required question "{req}" has no example answer')
        for key, val in (data.get("secrets") or {}).items():
            ok = (isinstance(val, dict) and isinstance(val.get("store"), str)
                  and isinstance(val.get("key"), str))
            if not ok:
                ctx.report("error", "overlay/secret-ref", rel,
                           f'secret "{key}" must be a {{store, key}} reference — values live '
                           f"in the harness store (§3.1)")
