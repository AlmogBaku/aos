"""Vocabulary the rest of the tool reads: the manifest key/value sets, the two regexes
that recognise a version and a cron line, the Agent Skills name limits, and where the
provenance stamp lives.

This is now the SINGLE definition, not a copy: the kit-side lint (`tools/aos_lint`) imports
these names from here rather than restating them. It used to keep its own copies in
`tools/lib/constants.mjs` under a comment saying the two "must agree", with nothing testing
the agreement — so a schema the installer and the linter disagreed about was undetectable.
Changing a value here therefore changes what CI enforces, which is the point."""

import re
from pathlib import Path

VERSION = "0.6.0"                       # tracks the capability-lifecycle version
LOCK_REL = Path(".aos") / "installs.lock.yaml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
CRON5 = re.compile(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$")

# The kit-side lint imports these (aos_lint.constants re-exports them) — one definition.
MANIFEST_KEYS = {"id", "version", "tags", "summary", "depends", "cron", "skills", "kb",
                 "skill_prefix", "uses"}
CAPABILITY_TAGS = {"infra", "usecase"}
HOST_FEATURES = {"cron", "messaging.inbound", "messaging.outbound", "voice.stt",
                 "voice.tts", "calendar.read", "calendar.write", "email", "secret"}
HOST_LEVELS = {"required", "preferred", "optional"}
CRON_KEYS = {"id", "expr", "agent", "prompt_ref", "exec", "degraded"}
DEGRADED = {"manual", "skip", "inline"}
SKILL_ENTRY_KEYS = {"id", "used_by"}
# RFC-009 option 2: a consumer grants one of ITS agents a skill another capability ships.
USES_ENTRY_KEYS = {"capability", "skill", "agents"}
KB_KEYS = {"writes", "zones"}

# The cheat-sheet frontmatter (§5.2): one per harness, `reference/harness-<runtime>.md` of the
# lifecycle entry skill. The installer reads it as guidance; `aos-session` reads
# `mapping.session` at run time; the lint checks every sheet against these sets.
CHEATSHEET_KEYS = {"harness", "status", "source", "rules", "files", "mapping"}
CHEATSHEET_STATUS = {"verified", "research-drafted"}
# Ten aos concepts, plus every `depends.host` word that is not already one of them, so a new
# host word forces a row on every sheet (cron and secret answer their own word).
CHEATSHEET_CONCEPTS = ("agent", "main", "skill", "cron", "context_block", "secret", "config",
                       "hook", "session", "plan_mode")
CHEATSHEET_ROWS = CHEATSHEET_CONCEPTS + tuple(sorted(HOST_FEATURES - set(CHEATSHEET_CONCEPTS)))
# A row is either `primitive:` (the harness has it) or `support:` one of these.
CHEATSHEET_SUPPORT = {"via", "none", "unknown"}
# What `aos-session` reads from `mapping.session`: two command templates, the regex that finds
# the new session id on stderr, and the stderr regex that means the session is gone.
SESSION_KEYS = ("open", "continue", "id", "missing")
SESSION_PLACEHOLDERS = ("<profile>", "<title>", "<file>", "<session_id>", "<workdir>", "<skills>")
HARNESS_REL = Path(".aos") / "harness.yml"

# Agent Skills spec (agentskills.io/specification): the shipped `name` is what a harness
# keys on, so these limits bind the INSTALLED name, not the capability-local id.
SKILL_PREFIX_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_NAME_MAX = 64
RESERVED_NAME_WORDS = ("anthropic", "claude")
# The provenance stamp lives inside the Agent Skills spec's own extension hatch, because
# SKILL.md is an EXTERNAL schema and we are a vendor in it — inventing a top-level `x-`
# key there was us reserving namespace in somebody else's house. `x-*` stays reserved in
# CAPABILITY.md, which is ours, for THIRD parties.
ORIGIN_PATH = ("metadata", "aos", "origin")
ORIGIN_KEY = "metadata.aos.origin"          # display form, for messages
LEGACY_ORIGIN_KEY = "x-aos-origin"          # stripped from renders; never written
