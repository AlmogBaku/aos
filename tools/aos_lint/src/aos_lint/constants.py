"""Everything name-derived, so the RFC-001 rename stays a one-file sweep (plus grep).

That is the whole reason the retired `tools/lib/constants.mjs` existed, and it is why this
file exists rather than the strings being inlined: `KIT_NAME` is a placeholder until RFC-001
picks the real name, and when it does, this file plus a grep is the change.

What this file does NOT own: the SCHEMA vocabulary. `MANIFEST_KEYS`, `CAPABILITY_TAGS`,
`HOST_FEATURES`, `HOST_LEVELS`, `SCHEDULE_KEYS`, `DEGRADED`, `SKILL_ENTRY_KEYS`, `KB_KEYS`,
the name regexes, the slot regexes and `ORIGIN_PATH` are re-exported from
`aos_cap.constants` — the SHIPPED tool's. The .mjs version carried its own copies and a
comment saying they "must agree", with nothing testing the agreement; a schema the lint and
the installer disagree about is a bug in whichever one the goldens do not match, so there is
now one definition and the lint imports it.
"""

from aos_cap.constants import (  # noqa: F401  (re-exported vocabulary)
    CAPABILITY_TAGS,
    CRON5,
    DEGRADED,
    HOST_FEATURES,
    HOST_LEVELS,
    KB_KEYS,
    MANIFEST_KEYS,
    ORIGIN_KEY,
    ORIGIN_PATH,
    RESERVED_NAME_WORDS,
    SCHEDULE_KEYS,
    SEMVER,
    SKILL_ENTRY_KEYS,
    SKILL_NAME_MAX,
    SKILL_NAME_RE,
    SKILL_PREFIX_RE,
)
from aos_cap.slots import AGENT_SLOT, ESCAPED_SLOT, SKILL_SLOT  # noqa: F401

# The project name is a placeholder — RFC-001 picks the real one.
KIT_NAME = "aos"
STATE_DIR = f".{KIT_NAME}/"  # machine-local state, gitignored (ARCHITECTURE §3.1)

# The install-time provenance stamp, never shipped upstream. It lives inside SKILL.md's own
# `metadata` extension hatch, because that schema is EXTERNAL and we are a vendor in it —
# a top-level `x-aos-origin` was us reserving namespace in somebody else's house. `x-*` stays
# reserved in CAPABILITY.md, which is ours, for THIRD parties. ORIGIN_PATH/ORIGIN_KEY come
# from aos_cap.constants above; only the retired spelling and the jobs.json form are ours.
ORIGIN_FRONTMATTER_PATH = ORIGIN_PATH
ORIGIN_FRONTMATTER_KEY = ORIGIN_KEY                     # display form
LEGACY_ORIGIN_FRONTMATTER_KEY = f"x-{KIT_NAME}-origin"  # retired; must not ship
ORIGIN_JOB_PREFIX = f"{KIT_NAME}:"   # jobs.json entries: origin: aos:<cap>@<ver>

# ARCHITECTURE §3.1 — the user-owned overlay family. Upstream never contains these.
OVERLAY_BASENAMES = ["MOD.md", "kb-registry.yaml"]
# Fixtures simulate the user clone and golden snapshots record the rendered user
# side, so overlay paths are allowed there (RFC-002) — ARCHITECTURE §3.1's
# invariant is about *shipped* paths.
OVERLAY_EXEMPT_PREFIXES = ["tests/fixtures/", "tests/golden/"]

# ARCHITECTURE §2.2 — the lint's own halves of the manifest schema. These two are lint-only
# (aos_cap validates `depends`/`kb.zones` structurally without naming the key sets), so they
# stay here rather than being pushed into the shipped tool for one reader.
DEPENDS_KEYS = ["capabilities", "host"]
KB_ZONE_KEYS = ["path", "owner_agent"]
MAIN_AGENT = "main"  # §2.2: `main` = the front agent

# A reference/ file past this length needs a Contents block: partial reads (head -100)
# must still reveal the full scope of what is in there.
REFERENCE_TOC_LINES = 100

# Migration prose legitimately names retired skills (`capability-installer`,
# `capability-builder`) that resolve to nothing by design. A path allowlist would rot; a
# marker on the line keeps the intent local and greppable.
HISTORICAL_NAME_MARKER = "<!-- aos-lint-allow: historical -->"

# ARCHITECTURE §2.3 — neutral agent spec
AGENT_KEYS = ["name", "purpose", "model_class", "tools", "workspace", "context_files"]
AGENT_REQUIRED_KEYS = ["name", "purpose", "model_class"]
MODEL_CLASSES = ["fast", "balanced", "deep"]
AGENT_TOOLS = ["fs.read", "fs.write", "shell", "web"]
AGENT_WORKSPACES = ["own", "shared"]

# ONBOARDING.md question schema (type vocabulary: BUILD-GAPS G2 / ARCHITECTURE §3.1)
QUESTION_KEYS = ["id", "prompt", "type", "required", "secret", "re_ask"]
QUESTION_REQUIRED_KEYS = ["id", "prompt", "type"]
QUESTION_TYPES = ["string", "number", "boolean", "enum", "list", "path"]

# ARCHITECTURE §5.2 — required cheat-sheet sections, verbatim.
CHEATSHEET_SECTIONS = [
    "Primitive mapping",
    "Materialization guide",
    "Introspection guide",
    "Secrets",
    "Removal",
    "Feature notes",
]

# The vocabulary sets above arrive from aos_cap as SETS; the lint prints several of them in
# error messages, where a set's iteration order would make the message unstable. These are
# the ordered forms the messages use, and they are asserted to cover the same members.
MANIFEST_KEYS_ORDERED = ["id", "version", "tags", "summary", "depends", "schedules",
                         "skills", "kb", "skill_prefix"]
CAPABILITY_TAGS_ORDERED = ["infra", "usecase"]
HOST_FEATURES_ORDERED = ["cron", "messaging.inbound", "messaging.outbound", "voice.stt",
                         "voice.tts", "calendar.read", "calendar.write", "email",
                         "secrets-store"]
HOST_LEVELS_ORDERED = ["required", "preferred", "optional"]
SCHEDULE_KEYS_ORDERED = ["id", "cron", "agent", "prompt_ref", "exec", "degraded"]
DEGRADED_MODES = ["manual", "skip", "inline"]
SKILL_ENTRY_KEYS_ORDERED = ["id", "used_by"]
KB_KEYS_ORDERED = ["writes", "zones"]

# The ordered forms are a display concern, never a second source of truth: if the shipped
# tool gains a manifest key and this file is not updated, the mismatch fails at import time
# rather than silently printing a stale vocabulary in an error message.
for _ordered, _canonical, _what in [
    (MANIFEST_KEYS_ORDERED, MANIFEST_KEYS, "MANIFEST_KEYS"),
    (CAPABILITY_TAGS_ORDERED, CAPABILITY_TAGS, "CAPABILITY_TAGS"),
    (HOST_FEATURES_ORDERED, HOST_FEATURES, "HOST_FEATURES"),
    (HOST_LEVELS_ORDERED, HOST_LEVELS, "HOST_LEVELS"),
    (SCHEDULE_KEYS_ORDERED, SCHEDULE_KEYS, "SCHEDULE_KEYS"),
    (DEGRADED_MODES, DEGRADED, "DEGRADED"),
    (SKILL_ENTRY_KEYS_ORDERED, SKILL_ENTRY_KEYS, "SKILL_ENTRY_KEYS"),
    (KB_KEYS_ORDERED, KB_KEYS, "KB_KEYS"),
]:
    if set(_ordered) != set(_canonical):
        raise AssertionError(
            f"aos_lint.constants: {_what} display order is out of sync with "
            f"aos_cap.constants — {set(_ordered) ^ set(_canonical)}")
del _ordered, _canonical, _what
