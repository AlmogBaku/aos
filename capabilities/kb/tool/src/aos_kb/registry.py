"""Where a machine's bases are registered, and where that registry file itself lives.
`find_household()` is the one function nearly everything else in the tool roots
through — the household is `<home>/{upstream,personal,.aos}`, and `.aos/` is the
marker, checked before any `capabilities/` heuristic so a render inside `personal/`
(which also carries `capabilities/`) is never mistaken for the household or upstream."""

import os
from pathlib import Path

import yaml


def find_household() -> Path | None:
    """The household root: <home>/{upstream,personal,.aos}. `.aos/` is the marker —
    checked before any capabilities/ heuristic, so a render inside personal/ (which
    also carries capabilities/) is never mistaken for the household or for upstream."""
    env = os.environ.get("AOS_HOME")
    if env:
        return Path(env).expanduser()
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / ".aos").is_dir():
            return p
    return None


def find_upstream_root() -> Path:
    home = find_household()
    if home:
        return home / "upstream"
    # not inside a household: a bare kit checkout is its own upstream root
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "capabilities" / "kb" / "CAPABILITY.md").is_file():
            return p
    return Path.home() / "aos" / "upstream"


def find_personal_root() -> Path:
    home = find_household()
    if home:
        return home / "personal"
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "kb-registry.yaml").exists():
            return p
    return Path.home() / "aos" / "personal"


def registry_path(args) -> Path:
    if getattr(args, "registry", None):
        return Path(args.registry).expanduser()
    env = os.environ.get("AOS_REGISTRY")
    if env:
        return Path(env).expanduser()
    return find_personal_root() / "kb-registry.yaml"


def load_registry(args) -> dict:
    p = registry_path(args)
    if not p.exists():
        return {"default": None, "kbs": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.setdefault("kbs", [])
    return data


def save_registry(args, data: dict):
    p = registry_path(args)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                 encoding="utf-8")
