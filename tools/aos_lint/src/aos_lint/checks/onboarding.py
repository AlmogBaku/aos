from ..constants import QUESTION_KEYS, QUESTION_REQUIRED_KEYS, QUESTION_TYPES
from ..frontmatter import read_frontmatter


# ONBOARDING.md frontmatter is the typed question list — and doubles as the
# MOD.md answer schema (ARCHITECTURE §3.1: "the questions are the allowed-
# frontmatter definition — no second schema").
def check_onboarding(ctx) -> None:
    for cap in ctx.caps:
        path = cap.dir / "ONBOARDING.md"
        if not path.exists():
            continue
        file = f"{cap.rel}/ONBOARDING.md"
        parsed = read_frontmatter(path)
        if parsed.error or parsed.data is None:
            ctx.report("error", "onboarding/parse", file,
                       parsed.error or "missing frontmatter")
            continue
        questions = parsed.data.get("questions")
        if not isinstance(questions, list) or not questions:
            ctx.report("error", "onboarding/questions", file,
                       "frontmatter must declare a non-empty questions[] list")
            continue
        seen = set()
        for q in questions:
            q = q if isinstance(q, dict) else {}
            label = q.get("id", "<missing id>")
            for key in q:
                if key not in QUESTION_KEYS:
                    ctx.report("error", "onboarding/unknown-key", file,
                               f'question "{label}": unknown key "{key}"')
            for key in QUESTION_REQUIRED_KEYS:
                if q.get(key) is None:
                    ctx.report("error", "onboarding/required", file,
                               f'question "{label}": "{key}" is required')
            if q.get("id") is not None:
                if q["id"] in seen:
                    ctx.report("error", "onboarding/duplicate-id", file,
                               f'duplicate question id "{q["id"]}"')
                seen.add(q["id"])
            if q.get("type") is not None and q["type"] not in QUESTION_TYPES:
                ctx.report("error", "onboarding/type", file,
                           f'question "{label}": type "{q["type"]}" not in '
                           f'{{{", ".join(QUESTION_TYPES)}}} (BUILD-GAPS G2)')
            for flag in ("required", "secret"):
                if q.get(flag) is not None and not isinstance(q[flag], bool):
                    ctx.report("error", "onboarding/flag", file,
                               f'question "{label}": "{flag}" must be a boolean')


def question_ids(cap_dir):
    """The three id sets the overlay check validates MOD answers against: every question,
    the required ones, and the secret ones. None when the capability ships no ONBOARDING.md
    (the pair is optional, §2.1) — which the caller distinguishes from an empty set."""
    path = cap_dir / "ONBOARDING.md"
    if not path.exists():
        return None
    data = read_frontmatter(path).data or {}
    questions = [q if isinstance(q, dict) else {} for q in (data.get("questions") or [])]
    return {
        "all": {q.get("id") for q in questions if q.get("id")},
        "required": {q["id"] for q in questions if q.get("required") and q.get("id")},
        "secret": {q["id"] for q in questions if q.get("secret") and q.get("id")},
    }
