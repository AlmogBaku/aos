#!/usr/bin/env python3
"""Copy a rendered tree into a golden snapshot, normalizing run-varying values so
the committed diff shows only meaningful changes.

Usage: python -m aos_lint.golden.normalize <src-dir> <dest-dir>
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml

from ..constants import ORIGIN_FRONTMATTER_PATH


class _NoStamp:
    """Stands in for JS `undefined`: "there is no stamp", as distinct from a stamp whose value
    is empty or null. Both callers must test for THIS object, so `has_stamp()` below is the
    only supported test — an `is _SENTINEL` against a locally-defined `object()` compares two
    different objects and silently answers "stamped" for every file. That exact mistake made
    the ported golden/origin-tag check pass on a snapshot with the stamp cut out of it."""

    def __repr__(self):
        return "<no origin stamp>"


NO_STAMP = _NoStamp()


def has_stamp(value) -> bool:
    """Is this `origin_stamp()` result a stamp at all? The one supported test."""
    return value is not NO_STAMP


# The install-time provenance stamp, read as structured frontmatter. Both golden scripts used
# `.includes('x-aos-origin:')`, which matched the string anywhere in the file — including in a
# skill whose prose merely discussed provenance. Now that the stamp is nested inside the spec's
# `metadata` hatch there is no line to match at all, so this has to parse.
def origin_stamp(skill_md):
    try:
        text = Path(skill_md).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return NO_STAMP
    if not text.startswith("---\n"):
        return NO_STAMP
    end = text.find("\n---", 3)
    if end == -1:
        return NO_STAMP
    try:
        data = yaml.safe_load(text[4:end + 1])
    except yaml.YAMLError:
        return NO_STAMP
    node = data
    for key in ORIGIN_FRONTMATTER_PATH:
        if not isinstance(node, dict) or key not in node:
            return NO_STAMP
        node = node[key]
    return node


SKIP = {
    # harness runtime state: provider/model details are run-varying and private
    "config.yaml", "profile.yaml",
    # harness-owned skill-store metadata + caches (megabytes of run-varying JSON)
    ".hub", "index-cache", ".bundled_manifest",
    "node_modules", ".git", "sessions", "logs", "memories", "state.db",
    "audio_cache", "cache", ".env", "auth.json", "state-snapshots", "bin",
    # Harness runtime state inside a profile. `home` is the agent's own sandbox HOME
    # (npm/node caches — megabytes, and it carries absolute developer paths a snapshot
    # must never commit); `lsp` is language-server state. Neither is ever an aos artifact.
    # NOTE: SKIP matches on basename, so these two names are also unusable as source dir
    # names anywhere in a snapshotted tree. Acceptable for harness runtime state; do not
    # add a name a capability might legitimately ship (`skills`, `reference`, `templates`).
    "home", "lsp",
    # The household's kit clone. It is upstream's own tree, not anything an install produced —
    # recording it would snapshot this repo inside itself (2.7MB, including the lint selftest's
    # PLANTED violations, which then fail the linter on the copy). What the snapshot must prove
    # about upstream is that renders point INTO personal/, which the links and lockfile already
    # say. Excluded deliberately, and the pre-2026-07-29 snapshots did the same.
    "upstream",
    # …and the vendor clone, for the same reason plus one: it is a THIRD PARTY's repo, cloned by
    # reference and never rendered (§2.1), so it is neither ours to commit nor ours to normalize
    # — and Anthropic's own example code carries token-shaped strings that trip this kit's
    # secret scanner on the copy. What an install must prove about vendor/ is that it recorded
    # a link into it, which the lockfile says.
    "vendor",
    # Harness-written marker/notice files: presence depends on the build and the model in
    # use, not on anything an install did.
    ".no-bundled-skills", ".codex_gpt55_autoraise_notice",
    "executions.db", ".jobs.lock", "auth.lock", "state.db-shm", "state.db-wal",
    ".skills_prompt_snapshot.json", ".update_check", "context_length_cache.yaml",
    "verification_evidence.db", "models_dev_cache.json",
}
# A known trailing suffix (e.g. `.sh.unused`, left when a harness renames a script)
# must still normalize — otherwise absolute developer paths land in a committed
# snapshot. Deliberately an allowlist: `.json.gz` must NOT be read as text.
TEXT = re.compile(r"\.(md|ya?ml|json|txt|sh|tmpl)(\.(unused|bak|orig|old|disabled))?$")

HOME = os.environ.get("HOME") or "/home/user"

_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SHA256 = re.compile(r"\b[0-9a-f]{64}\b")
_ID = re.compile(r"\b[0-9a-f]{12}\b")
# A synthesized principal (`aos_kb.identity.synthesize_principal`) is `<user>@<host>.local`,
# built from getpass.getuser() and socket.gethostname() — two facts about whoever ran the e2e
# and none about the install. It reached a committed snapshot once, because $HOME was the only
# thing normalized here.
#
# Matched by SHAPE rather than by substituting $USER: a username is often an ordinary word
# (`dana`, `user`, `home`), and a bare \buser\b replace corrupts unrelated prose and
# `home/.local/share/uv` paths. The shape carries no literal, so this rule is identical on
# every machine — which is what makes a snapshot portable rather than merely scrubbed.
_PRINCIPAL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.local\b")
# An agent session/run uuid. MUST run before _ID, whose 12-hex pattern otherwise eats the
# uuid's last group and leaves the first four in place — a partial redaction that still
# identifies the run.
_SESSION = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def normalize_text(text: str) -> str:
    # $HOME FIRST, always. A username usually appears INSIDE $HOME, so any rule naming the
    # user has to run after the path collapse or it rewrites the path's interior and the
    # $HOME replace then no longer matches (`/home/<USER>/.hermes`, with $HOME dead). The
    # rules below are shape-based and so are order-independent against HOME today; the
    # ordering is kept because the next user-derived rule added here will not be.
    text = text.replace(HOME, "<HOME>")
    text = _PRINCIPAL.sub("<PRINCIPAL>", text)
    text = _TIMESTAMP.sub("<TIMESTAMP>", text)
    text = _DATE.sub("<DATE>", text)
    text = _SHA256.sub("<SHA256>", text)
    text = _SESSION.sub("<SESSION-ID>", text)  # before _ID — see above
    return _ID.sub("<ID>", text)


def _scrub(o):
    """provider/model snapshots are run-varying and private — scrub before committing."""
    if isinstance(o, list):
        for item in o:
            _scrub(item)
    elif isinstance(o, dict):
        for k in list(o):
            if k in ("provider_snapshot", "model_snapshot"):
                o[k] = None
            else:
                _scrub(o[k])


def normalize_tree(s, d) -> None:
    """The `copy` of normalize.mjs, by its exported name."""
    s, d = Path(s), Path(d)
    if s.is_dir():
        if s.name in SKIP:
            return
        d.mkdir(parents=True, exist_ok=True)
        # A skills/ dir with a .bundled_manifest is a harness-managed skill store:
        # snapshot ONLY what the INSTALL materialized (top-level dirs whose SKILL.md
        # carries the origin stamp) — bundled harness content and the store's own metadata
        # (.bundled_manifest, .hub) are run-varying noise.
        if (s / ".bundled_manifest").exists():
            for name in _readdir(s):
                child = s / name
                if not child.is_dir():
                    continue
                if name == ".hub":
                    continue
                skill_md = child / "SKILL.md"
                if skill_md.exists() and has_stamp(origin_stamp(skill_md)):
                    normalize_tree(child, d / name)
            return
        for name in _readdir(s):
            normalize_tree(s / name, d / name)
        # An empty directory is noise in the committed diff — the harness creates a dozen
        # of them per profile, and none of them is something an install wrote.
        if not _readdir(d):
            d.rmdir()
    else:
        if s.name in SKIP:
            return
        d.parent.mkdir(parents=True, exist_ok=True)
        if TEXT.search(s.name):
            text = s.read_text(encoding="utf-8")
            if s.name.endswith(".json"):
                try:
                    parsed = json.loads(text)
                    _scrub(parsed)
                    # JSON.stringify(x, undefined, 2): 2-space indent, `": "` separator, and
                    # no trailing newline. `ensure_ascii=False` because JS emits the character,
                    # not a \uXXXX escape — and the snapshots carry em dashes.
                    text = json.dumps(parsed, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            d.write_text(normalize_text(text), encoding="utf-8")
        elif s.stat().st_size < 64 * 1024:
            d.write_bytes(s.read_bytes())


def _readdir(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print("usage: normalize.py <src-dir> <dest-dir>", file=sys.stderr)
        return 1
    src, dest = args[0], args[1]
    if not Path(src).exists():
        print(f"source {src} does not exist", file=sys.stderr)
        return 1
    normalize_tree(src, dest)
    print(f"normalized {src} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
