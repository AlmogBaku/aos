"""The seven verbs that own `<home>/.aos/installs.lock.yaml`: `init` creates it,
`record` writes one capability's entry, `rehash` refreshes its hashes after an approved
evolve, `verify` compares it against disk, and `show`/`list`/`remove` read and prune it.

Grouped because they all begin with the same two lines — resolve the household, load the
lockfile — and because the file is a single unit: only `init` may find it absent."""

import json
import os
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from ..constants import LOCK_REL
from ..errors import Exit, fail
from ..household import find_home
from ..lockfile import (
    artifact_path, get_entry, link_target, load_lock, readlink_or_fail, save_lock, sha256,
)

app = typer.Typer()


@app.command("init", help="create an empty lockfile")
def cmd_init(ctx: typer.Context) -> None:
    root = find_home(ctx.obj, require_existing=False)
    path = root / LOCK_REL
    if path.is_file():
        fail(Exit.GENERIC, f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    save_lock(root, {"version": 1, "installs": {}})
    print(f"initialized {path}")


@app.command("record", help="write a capability's entry (computes sha256s)")
def cmd_record(
    ctx: typer.Context,
    capability: str,
    version: Annotated[str, typer.Option("--version")],
    artifact: Annotated[Optional[list[str]], typer.Option(
        "--artifact", help="repeatable file path")] = None,
    link: Annotated[Optional[list[str]], typer.Option(
        "--link",
        help="repeatable harness symlink path (target read from the link itself)")] = None,
    source_root: Annotated[str, typer.Option(
        "--source-root",
        help="which household root shipped the capability (upstream|personal|<org>)")] = "upstream",
    job: Annotated[Optional[list[str]], typer.Option(
        "--job", help="repeatable schedule/job id")] = None,
    config_key: Annotated[Optional[list[str]], typer.Option("--config-key")] = None,
    env_line: Annotated[Optional[list[str]], typer.Option(
        "--env-line", help="env var NAME added (never the value)")] = None,
    script: Annotated[Optional[list[str]], typer.Option(
        "--script", help="script/hook file installed")] = None,
) -> None:
    artifact, link = list(artifact or []), list(link or [])
    job, config_key = list(job or []), list(config_key or [])
    env_line, script = list(env_line or []), list(script or [])
    root = find_home(ctx.obj)
    lock = load_lock(root)
    entry = {
        "version": version,
        "source_root": source_root,
        "artifacts": {str(artifact_path(a)): sha256(artifact_path(a)) for a in artifact},
        "links": {os.path.normpath(str(Path(l).expanduser().absolute())): readlink_or_fail(l) for l in link},
        "schedules_owned": list(job),
        "config_keys": list(config_key),
        "env_lines": list(env_line),
        "scripts": list(script),
    }
    lock["installs"][capability] = entry
    save_lock(root, lock)
    print(f"recorded {capability}@{version}: "
          f"{len(entry['artifacts'])} artifacts, {len(entry['links'])} links, "
          f"{len(entry['schedules_owned'])} schedules")


@app.command("rehash", help="re-hash a capability's recorded artifacts in place "
                            "(after an approved evolve)")
def cmd_rehash(ctx: typer.Context, capability: str) -> None:
    root = find_home(ctx.obj)
    lock, entry = get_entry(root, capability)
    kept, dropped = {}, []
    for path in entry.get("artifacts", {}):
        if Path(path).is_file():
            kept[path] = sha256(path)
        else:
            dropped.append(path)
    if dropped and not kept:
        fail(Exit.ARTIFACT_MISSING,
             f"{capability}: every recorded artifact is gone — that is a broken "
             f"install, not a rehash. Re-install, or `aos-cap remove` the entry.")
    entry["artifacts"] = kept
    save_lock(root, lock)
    for path in dropped:
        print(f"dropped (no longer on disk): {path}")
    print(f"rehashed {capability}: {len(kept)} artifacts"
          + (f", {len(dropped)} dropped" if dropped else ""))


@app.command("verify", help="re-hash artifacts vs disk; 13 on drift")
def cmd_verify(ctx: typer.Context, capability: Optional[str] = typer.Argument(None)) -> None:
    root = find_home(ctx.obj)
    lock = load_lock(root)
    caps = [capability] if capability else sorted(lock["installs"])
    drift = []
    for cap in caps:
        if cap not in lock["installs"]:
            fail(Exit.NO_ENTRY, f"no lockfile entry for '{cap}'")
        for path, sha in lock["installs"][cap].get("artifacts", {}).items():
            p = Path(path)
            if not p.is_file():
                drift.append(f"{cap}: MISSING {path}")
            elif sha256(p) != sha:
                drift.append(f"{cap}: DRIFT {path}")
        for path, target in lock["installs"][cap].get("links", {}).items():
            p = Path(path)
            if not p.is_symlink():
                # present-but-not-a-link is the banned copy case; absent is a plain miss
                kind = "NOT A LINK (copies are banned)" if p.exists() else "MISSING LINK"
                drift.append(f"{cap}: {kind} {path}")
            elif link_target(p) != target:
                drift.append(f"{cap}: RELINKED {path} -> {link_target(p)} (recorded: {target})")
            elif not p.exists():
                drift.append(f"{cap}: DANGLING LINK {path} -> {target}")
    if drift:
        for line in drift:
            print(line)
        sys.exit(Exit.DRIFT)
    print(f"clean: {len(caps)} entr{'y' if len(caps) == 1 else 'ies'} verified")


@app.command("show", help="print a capability's entry as JSON")
def cmd_show(ctx: typer.Context, capability: str) -> None:
    root = find_home(ctx.obj)
    _, entry = get_entry(root, capability)
    json.dump(entry, sys.stdout, indent=2, default=str)
    print()


# `list` shadows the builtin, so the function is named for what it does and the verb name
# is declared on the decorator — the CLI surface is unchanged.
@app.command("list", help="installed capabilities + versions")
def list_installs(ctx: typer.Context) -> None:
    root = find_home(ctx.obj)
    lock = load_lock(root)
    for cap, entry in sorted(lock["installs"].items()):
        print(f"{cap}  {entry.get('version', '?')}  "
              f"{len(entry.get('artifacts', {}))} artifacts  "
              f"{len(entry.get('links', {}))} links  "
              f"{len(entry.get('schedules_owned', []))} schedules")


@app.command("remove", help="drop a capability's entry (after the removal walk)")
def cmd_remove(ctx: typer.Context, capability: str) -> None:
    root = find_home(ctx.obj)
    lock, _ = get_entry(root, capability)
    del lock["installs"][capability]
    save_lock(root, lock)
    print(f"removed lockfile entry for {capability}")
