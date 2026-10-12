"""Where a machine's bases are registered, and where that registry file itself lives.

The aos home is `$AOS_HOME`, else `~/aos` — named, never discovered: a cwd-upward
search for `.aos/` let any folder carrying one become the household. The registry is
`--registry`/`$AOS_REGISTRY`, else `<home>/.aos/kb-registry.yaml`, and only `kb init`
and `kb adopt` may create it; every other reader of a missing one is an error that
names the path."""

import os
from pathlib import Path

import yaml


def find_household() -> Path:
    """The household root: <home>/{upstream,personal,.aos}."""
    env = os.environ.get("AOS_HOME")
    return Path(env).expanduser() if env else Path.home() / "aos"


def find_upstream_root() -> Path:
    return find_household() / "upstream"


def registry_named(args) -> bool:
    """Was a registry asked for (`--registry`/$AOS_REGISTRY), rather than defaulted?"""
    return bool(getattr(args, "registry", None) or os.environ.get("AOS_REGISTRY"))


def registry_path(args) -> Path:
    if getattr(args, "registry", None):
        return Path(args.registry).expanduser()
    env = os.environ.get("AOS_REGISTRY")
    if env:
        return Path(env).expanduser()
    return find_household() / ".aos" / "kb-registry.yaml"


def load_registry(args, create: bool = False) -> dict:
    """`create=True` is for `init` and `adopt` alone: they start an absent registry
    empty. Anyone else reading a missing one is pointed at the path it expected."""
    p = registry_path(args)
    if not p.exists():
        if not create:
            from .identity import die   # identity imports this module
            die(f"no registry at {p} — create it with `kb init` or `kb adopt`, "
                f"or pass --registry")
        return {"default": None, "kbs": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.setdefault("kbs", [])
    return data


def save_registry(args, data: dict):
    p = registry_path(args)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                 encoding="utf-8")
