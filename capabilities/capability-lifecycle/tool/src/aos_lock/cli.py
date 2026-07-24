"""aos-lock — deterministic lifecycle bookkeeping (ARCHITECTURE §2.4 capability tool).

Two jobs, no judgment:
  manifest  parse + validate a CAPABILITY.md -> JSON on stdout
  init/record/verify/show/list/remove  own the lockfile
  (<home>/.aos/installs.lock.yaml — the aos household root, e.g. ~/aos)

The lockfile is THIS TOOL'S file: agents call verbs, never edit the YAML.
Exit codes: 0 ok · 1 generic (e.g. init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml

LOCK_REL = Path(".aos") / "installs.lock.yaml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
CRON5 = re.compile(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$")

# Mirrors tools/lib/constants.mjs + tools/lint/checks/manifest.mjs (the kit-side gate).
MANIFEST_KEYS = {"id", "version", "tags", "summary", "depends", "schedules", "skills", "kb"}
CAPABILITY_TAGS = {"infra", "usecase"}
HOST_FEATURES = {"cron", "messaging.inbound", "messaging.outbound", "voice.stt",
                 "voice.tts", "calendar.read", "calendar.write", "email", "secrets-store"}
HOST_LEVELS = {"required", "preferred", "optional"}
SCHEDULE_KEYS = {"id", "cron", "agent", "prompt_ref", "exec", "degraded"}
DEGRADED = {"manual", "skip", "inline"}
SKILL_ENTRY_KEYS = {"id", "used_by"}
KB_KEYS = {"writes", "zones"}


def fail(code, msg):
    print(f"aos-lock: {msg}", file=sys.stderr)
    sys.exit(code)


def find_home(args, require_existing=True):
    if args.home:
        root = Path(args.home).expanduser()
    elif os.environ.get("AOS_HOME"):
        root = Path(os.environ["AOS_HOME"]).expanduser()
    elif not require_existing:
        fail(15, "init creates state — name the household explicitly (--home or AOS_HOME)")
    else:
        cur = Path.cwd()
        for cand in [cur, *cur.parents]:
            if (cand / ".aos").is_dir():
                return cand
        fail(15, "no household found: no .aos/ directory from cwd upward "
                 "(pass --home or set AOS_HOME)")
    if require_existing and not (root / ".aos").is_dir():
        fail(15, f"no .aos/ directory under {root}")
    return root


def frontmatter(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(12, f"{path}: no YAML frontmatter block")
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if not m:
        fail(12, f"{path}: unterminated frontmatter block")
    end = 4 + m.start()
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as e:
        fail(12, f"{path}: frontmatter is not valid YAML: {e}")
    if not isinstance(data, dict):
        fail(12, f"{path}: frontmatter must be a YAML mapping")
    return data


def cmd_manifest(args):
    cap_dir = Path(args.dir)
    mf = cap_dir / "CAPABILITY.md"
    if not mf.is_file():
        fail(12, f"{cap_dir}: no CAPABILITY.md")
    data = frontmatter(mf)
    errs = []
    for key in data:
        if key not in MANIFEST_KEYS and not str(key).startswith("x-"):
            errs.append(f"unknown key '{key}' (rule of two; x-* is the extension namespace)")
    if data.get("id") != cap_dir.name:
        errs.append(f"id '{data.get('id')}' must equal the directory name '{cap_dir.name}'")
    if not isinstance(data.get("version"), str) or not SEMVER.match(data.get("version", "")):
        errs.append(f"version '{data.get('version')}' must be MAJOR.MINOR.PATCH")
    tags = data.get("tags")
    if not isinstance(tags, list) or not tags or not set(tags) <= CAPABILITY_TAGS:
        errs.append(f"tags {tags!r} must be a non-empty subset of {sorted(CAPABILITY_TAGS)}")
    if not isinstance(data.get("summary"), str) or not data.get("summary", "").strip():
        errs.append("summary must be a non-empty string")

    depends = data.get("depends") or {}
    if not isinstance(depends, dict):
        errs.append("depends must be a mapping")
        depends = {}
    for key in depends:
        if key not in ("capabilities", "host"):
            errs.append(f"depends: unknown key '{key}'")
    host = depends.get("host") or {}
    if not isinstance(host, dict):
        errs.append("depends.host must be a mapping")
        host = {}
    for feat, level in host.items():
        if feat not in HOST_FEATURES:
            errs.append(f"depends.host: unknown feature '{feat}'")
        if level not in HOST_LEVELS:
            errs.append(f"depends.host.{feat}: level '{level}' not in {sorted(HOST_LEVELS)}")

    agent_names = {"main"}
    for spec in (cap_dir / "agents").glob("*.agent.yaml"):
        try:
            name = (yaml.safe_load(spec.read_text()) or {}).get("name")
        except yaml.YAMLError:
            name = None
        agent_names.add(name or spec.name.replace(".agent.yaml", ""))
    for dep in (depends.get("capabilities") or []):
        if not (cap_dir.parent / str(dep) / "CAPABILITY.md").is_file():
            errs.append(f"depends.capabilities: '{dep}' has no capabilities/{dep}/CAPABILITY.md")
    if not (cap_dir / "README.md").is_file():
        errs.append("README.md is required")
    if (cap_dir / "ONBOARDING.md").is_file() and not (cap_dir / "MOD.example.md").is_file():
        errs.append("ONBOARDING.md without MOD.example.md (presence-paired)")
    seen_sched = set()
    for s in data.get("schedules") or []:
        if not isinstance(s, dict):
            errs.append(f"schedules: entry {s!r} must be a mapping")
            continue
        for key in s:
            if key not in SCHEDULE_KEYS:
                errs.append(f"schedules[{s.get('id')}]: unknown key '{key}'")
        sid = s.get("id")
        if sid in seen_sched:
            errs.append(f"schedules: duplicate id '{sid}'")
        seen_sched.add(sid)
        if not CRON5.match(str(s.get("cron", ""))):
            errs.append(f"schedules[{sid}]: cron '{s.get('cron')}' is not 5-field")
        if sid is None:
            errs.append("schedules: every entry requires an id")
        has_exec = "exec" in s
        has_agent = "agent" in s or "prompt_ref" in s
        if has_exec == has_agent:
            errs.append(f"schedules[{sid}]: exactly one of exec | agent+prompt_ref")
        if has_agent:
            if s.get("agent") not in agent_names:
                errs.append(f"schedules[{sid}]: agent '{s.get('agent')}' is not main or a declared agent")
            pref = s.get("prompt_ref")
            if not pref:
                errs.append(f"schedules[{sid}]: agent form requires prompt_ref")
            elif not (cap_dir / str(pref)).is_file():
                errs.append(f"schedules[{sid}]: prompt_ref '{pref}' does not resolve in the capability")
        if has_exec:
            first = str(s.get("exec", "")).split()[0] if str(s.get("exec", "")).strip() else ""
            if "/" in first and not (cap_dir / first).is_file():
                errs.append(f"schedules[{sid}]: exec path '{first}' does not resolve in the capability")
        if s.get("degraded") is None:
            errs.append(f"schedules[{sid}]: degraded is required (manual|skip|inline)")
        elif s["degraded"] not in DEGRADED:
            errs.append(f"schedules[{sid}]: degraded '{s['degraded']}' not in {sorted(DEGRADED)}")

    declared = set()
    for entry in data.get("skills") or []:
        if not isinstance(entry, dict):
            errs.append(f"skills: entry {entry!r} must be a mapping")
            continue
        for key in entry:
            if key not in SKILL_ENTRY_KEYS:
                errs.append(f"skills[{entry.get('id')}]: unknown key '{key}'")
        sid = entry.get("id")
        declared.add(sid)
        if not (cap_dir / "skills" / str(sid) / "SKILL.md").is_file():
            errs.append(f"skills: declared '{sid}' has no skills/{sid}/SKILL.md")
        used = entry.get("used_by")
        if not isinstance(used, list) or not used:
            errs.append(f"skills[{sid}]: used_by must be a non-empty list")
        else:
            for u in used:
                if u not in agent_names:
                    errs.append(f"skills[{sid}]: used_by '{u}' is not main or a declared agent")
    skills_dir = cap_dir / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in declared:
                errs.append(f"skills: on-disk skill '{d.name}' is not declared in skills[]")

    kb = data.get("kb") or {}
    if not isinstance(kb, dict):
        errs.append("kb must be a mapping")
        kb = {}
    for key in kb:
        if key not in KB_KEYS:
            errs.append(f"kb: unknown key '{key}'")
    for zone in (kb.get("zones") or []):
        if not isinstance(zone, dict):
            errs.append(f"kb.zones: entry {zone!r} must be a mapping")
            continue
        for key in zone:
            if key not in ("path", "owner_agent"):
                errs.append(f"kb.zones: unknown key '{key}'")
        if zone.get("owner_agent") and zone["owner_agent"] not in agent_names:
            errs.append(f"kb.zones: owner_agent '{zone['owner_agent']}' is not main or a declared agent")

    if errs:
        for e in errs:
            print(f"aos-lock: manifest: {e}", file=sys.stderr)
        sys.exit(12)
    json.dump(data, sys.stdout, indent=2, default=str)
    print()


def load_lock(root):
    path = root / LOCK_REL
    if not path.is_file():
        fail(15, f"no lockfile at {path} (run: aos-lock init)")
    data = yaml.safe_load(path.read_text()) or {}
    data.setdefault("version", 1)
    data.setdefault("installs", {})
    return data


def save_lock(root, data):
    (root / LOCK_REL).write_text(yaml.safe_dump(data, sort_keys=True))


def sha256(path):
    p = Path(path)
    if not p.is_file():
        fail(16, f"artifact not found: {path}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def readlink_or_fail(path):
    p = Path(path).expanduser()
    if not p.is_symlink():
        fail(16, f"not a symlink: {path}")
    return link_target(p)


def artifact_path(arg):
    """Artifacts are files; symlinks belong in --link (they are verified structurally,
    and hashing through one would silently record the target's identity instead)."""
    p = Path(arg).expanduser()
    if p.is_symlink():
        fail(16, f"symlink passed as --artifact (use --link): {arg}")
    return p.resolve()


def link_target(p):
    """Absolute + lexically normalized, identically for relative and absolute links, so
    the two spellings of one destination compare equal. Deliberately NOT resolve(): a
    household under a symlinked path must not read as drift."""
    target = os.readlink(p)
    if not os.path.isabs(target):
        target = os.path.join(str(Path(p).parent.absolute()), target)
    return os.path.normpath(target)


def cmd_init(args):
    root = find_home(args, require_existing=False)
    path = root / LOCK_REL
    if path.is_file():
        fail(1, f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    save_lock(root, {"version": 1, "installs": {}})
    print(f"initialized {path}")


def cmd_record(args):
    root = find_home(args)
    lock = load_lock(root)
    entry = {
        "version": args.version,
        "source_root": args.source_root,
        "artifacts": {str(artifact_path(a)): sha256(artifact_path(a)) for a in args.artifact},
        "links": {os.path.normpath(str(Path(l).expanduser().absolute())): readlink_or_fail(l) for l in args.link},
        "schedules_owned": list(args.job),
        "config_keys": list(args.config_key),
        "env_lines": list(args.env_line),
        "scripts": list(args.script),
    }
    lock["installs"][args.capability] = entry
    save_lock(root, lock)
    print(f"recorded {args.capability}@{args.version}: "
          f"{len(entry['artifacts'])} artifacts, {len(entry['links'])} links, "
          f"{len(entry['schedules_owned'])} schedules")


def cmd_rehash(args):
    root = find_home(args)
    lock, entry = get_entry(root, args.capability)
    kept, dropped = {}, []
    for path in entry.get("artifacts", {}):
        if Path(path).is_file():
            kept[path] = sha256(path)
        else:
            dropped.append(path)
    if dropped and not kept:
        fail(16, f"{args.capability}: every recorded artifact is gone — that is a broken "
                 f"install, not a rehash. Re-install, or `aos-lock remove` the entry.")
    entry["artifacts"] = kept
    save_lock(root, lock)
    for path in dropped:
        print(f"dropped (no longer on disk): {path}")
    print(f"rehashed {args.capability}: {len(kept)} artifacts"
          + (f", {len(dropped)} dropped" if dropped else ""))


def get_entry(root, capability):
    lock = load_lock(root)
    if capability not in lock["installs"]:
        fail(14, f"no lockfile entry for '{capability}'")
    return lock, lock["installs"][capability]


def cmd_verify(args):
    root = find_home(args)
    lock = load_lock(root)
    caps = [args.capability] if args.capability else sorted(lock["installs"])
    drift = []
    for cap in caps:
        if cap not in lock["installs"]:
            fail(14, f"no lockfile entry for '{cap}'")
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
        sys.exit(13)
    print(f"clean: {len(caps)} entr{'y' if len(caps) == 1 else 'ies'} verified")


def cmd_show(args):
    root = find_home(args)
    _, entry = get_entry(root, args.capability)
    json.dump(entry, sys.stdout, indent=2, default=str)
    print()


def cmd_home(args):
    print(find_home(args))


def cmd_list(args):
    root = find_home(args)
    lock = load_lock(root)
    for cap, entry in sorted(lock["installs"].items()):
        print(f"{cap}  {entry.get('version', '?')}  "
              f"{len(entry.get('artifacts', {}))} artifacts  "
              f"{len(entry.get('links', {}))} links  "
              f"{len(entry.get('schedules_owned', []))} schedules")


def cmd_remove(args):
    root = find_home(args)
    lock, _ = get_entry(root, args.capability)
    del lock["installs"][args.capability]
    save_lock(root, lock)
    print(f"removed lockfile entry for {args.capability}")


def main():
    p = argparse.ArgumentParser(
        prog="aos-lock",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--home", help="household root, e.g. ~/aos (else $AOS_HOME, else cwd-upward .aos/ search)")
    sub = p.add_subparsers(dest="verb", required=True)

    s = sub.add_parser("manifest", help="parse + validate a CAPABILITY.md -> JSON")
    s.add_argument("dir", help="capability directory")
    s.set_defaults(fn=cmd_manifest)

    sub.add_parser("init", help="create an empty lockfile").set_defaults(fn=cmd_init)

    s = sub.add_parser("record", help="write a capability's entry (computes sha256s)")
    s.add_argument("capability")
    s.add_argument("--version", required=True)
    s.add_argument("--artifact", action="append", default=[], help="repeatable file path")
    s.add_argument("--link", action="append", default=[],
                   help="repeatable harness symlink path (target read from the link itself)")
    s.add_argument("--source-root", default="upstream",
                   help="which household root shipped the capability (upstream|personal|<org>)")
    s.add_argument("--job", action="append", default=[], help="repeatable schedule/job id")
    s.add_argument("--config-key", action="append", default=[])
    s.add_argument("--env-line", action="append", default=[], help="env var NAME added (never the value)")
    s.add_argument("--script", action="append", default=[], help="script/hook file installed")
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("rehash", help="re-hash a capability's recorded artifacts in place (after an approved evolve)")
    s.add_argument("capability")
    s.set_defaults(fn=cmd_rehash)

    s = sub.add_parser("verify", help="re-hash artifacts vs disk; 13 on drift")
    s.add_argument("capability", nargs="?")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("show", help="print a capability's entry as JSON")
    s.add_argument("capability")
    s.set_defaults(fn=cmd_show)

    sub.add_parser("home", help="print the resolved household root (exit 15 if none)").set_defaults(fn=cmd_home)

    sub.add_parser("list", help="installed capabilities + versions").set_defaults(fn=cmd_list)

    s = sub.add_parser("remove", help="drop a capability's entry (after the removal walk)")
    s.add_argument("capability")
    s.set_defaults(fn=cmd_remove)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
