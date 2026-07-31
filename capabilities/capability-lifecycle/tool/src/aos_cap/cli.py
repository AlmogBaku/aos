"""aos-cap — the deterministic half of a capability's lifecycle (ARCHITECTURE §2.4).

No judgment anywhere: files, stdout and exit codes are the whole interface. Four
areas of work, which is why the tool is named for the capability and not for the
lockfile — only the last group is lockfile bookkeeping:

  manifest  parse + validate a CAPABILITY.md -> JSON on stdout
  skills    compute each skill's INSTALLED name; --check IS the collision gate
  render    copy one skill to its installed name (mechanical, idempotent)
  home      print the resolved household root
  init/record/rehash/verify/show/list/remove  own the lockfile
  (<home>/.aos/installs.lock.yaml — the aos household root, e.g. ~/aos)

The lockfile is THIS TOOL'S file: agents call verbs, never edit the YAML.
Exit codes: 0 ok · 1 generic (e.g. init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing ·
17 skill-name collision.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

LOCK_REL = Path(".aos") / "installs.lock.yaml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
CRON5 = re.compile(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$")

# Mirrors tools/lib/constants.mjs + tools/lint/checks/manifest.mjs (the kit-side gate).
MANIFEST_KEYS = {"id", "version", "tags", "summary", "depends", "schedules", "skills", "kb",
                 "skill_prefix"}
CAPABILITY_TAGS = {"infra", "usecase"}
HOST_FEATURES = {"cron", "messaging.inbound", "messaging.outbound", "voice.stt",
                 "voice.tts", "calendar.read", "calendar.write", "email", "secrets-store"}
HOST_LEVELS = {"required", "preferred", "optional"}
SCHEDULE_KEYS = {"id", "cron", "agent", "prompt_ref", "exec", "degraded"}
DEGRADED = {"manual", "skip", "inline"}
SKILL_ENTRY_KEYS = {"id", "used_by"}
KB_KEYS = {"writes", "zones"}

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


def fail(code, msg):
    print(f"aos-cap: {msg}", file=sys.stderr)
    sys.exit(code)


def effective_prefix(manifest, cap_id):
    """§2.2: declared prefix, else the capability id. Absent/empty means default."""
    declared = manifest.get("skill_prefix")
    if isinstance(declared, str) and declared.strip():
        return declared
    return f"{cap_id}-"


def installed_name(cap_id, prefix, skill_id):
    """The name the skill ships under. Entry skill verbatim; never double-prefixed."""
    if skill_id == cap_id or skill_id.startswith(prefix):
        return skill_id
    return f"{prefix}{skill_id}"


def name_errors(name, what):
    errs = []
    if len(name) > SKILL_NAME_MAX:
        errs.append(f"{what} '{name}' is {len(name)} chars (max {SKILL_NAME_MAX})")
    if not SKILL_NAME_RE.match(name):
        errs.append(f"{what} '{name}' must be [a-z0-9-], no leading/trailing/double hyphens")
    for word in RESERVED_NAME_WORDS:
        if word in name:
            errs.append(f"{what} '{name}' contains the reserved word '{word}'")
    return errs


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


def validated_manifest(cap_dir):
    # resolve() so a relative invocation (`aos-cap skills .`) still has a directory name
    # to compare `id` against — the contract's commands are written with <cap-dir> paths.
    cap_dir = Path(cap_dir).resolve()
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

    # Absent or empty means "default to the capability id" (§2.2), so only a non-empty
    # value is held to the format.
    prefix_declared = data.get("skill_prefix")
    if isinstance(prefix_declared, str) and prefix_declared.strip():
        if not SKILL_PREFIX_RE.match(prefix_declared):
            errs.append(f"skill_prefix '{prefix_declared}' must be [a-z0-9-] ending in a hyphen "
                        f"(e.g. 'capability-'); omit it to default to '<id>-'")
    elif prefix_declared is not None and not isinstance(prefix_declared, str):
        errs.append(f"skill_prefix must be a string (got {prefix_declared!r})")
    prefix = effective_prefix(data, cap_dir.name)

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
        if isinstance(sid, str) and SKILL_NAME_RE.match(sid):
            # The installed name is the shipped identity — it carries the spec's limits.
            for e in name_errors(installed_name(cap_dir.name, prefix, sid), f"skills[{sid}]: installed name"):
                errs.append(e)
        else:
            errs.append(f"skills[{sid!r}]: id must be [a-z0-9-], no leading/trailing/double hyphens")
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
            print(f"aos-cap: manifest: {e}", file=sys.stderr)
        sys.exit(12)
    return data


def cmd_manifest(args):
    json.dump(validated_manifest(Path(args.dir)), sys.stdout, indent=2, default=str)
    print()


# ---- skill names (§2.5): the installed name is the shipped identity ----------------

def frontmatter_soft(path):
    """Like frontmatter() but returns None instead of exiting — a malformed neighbour
    capability must not block an unrelated install's collision check."""
    try:
        text = path.read_text()
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if not m:
        return None
    try:
        data = yaml.safe_load(text[4:4 + m.start()]) or {}
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def find_home_soft(args, cap_dir=None):
    """The household if one is resolvable, else None.

    Discovery walks up from the CAPABILITY DIRECTORY as well as the cwd, because that is
    the one path every caller supplies: a capability lives at
    `<home>/{upstream,personal}/capabilities/<id>`, while the agent's cwd is wherever the
    harness put it. Relying on cwd alone made `--check` skip the household and lockfile
    sources on a real machine and still report "clean" — a silent no-op in the gate."""
    if args.home:
        root = Path(args.home).expanduser()
        if not (root / ".aos").is_dir():
            fail(15, f"no .aos/ directory under {root}")
        return root
    if os.environ.get("AOS_HOME"):
        root = Path(os.environ["AOS_HOME"]).expanduser()
        if (root / ".aos").is_dir():
            return root
    starts = ([Path(cap_dir).resolve()] if cap_dir else []) + [Path.cwd()]
    for start in starts:
        for cand in [start, *start.parents]:
            if (cand / ".aos").is_dir():
                return cand
    return None


def skill_rows(cap_dir):
    """(manifest, [{id, installed_name, used_by}]) for a validated capability."""
    cap_dir = Path(cap_dir).resolve()
    data = validated_manifest(cap_dir)
    prefix = effective_prefix(data, cap_dir.name)
    rows = [{"id": e["id"],
             "installed_name": installed_name(cap_dir.name, prefix, e["id"]),
             "used_by": list(e.get("used_by") or [])}
            for e in (data.get("skills") or [])]
    return data, rows


def capability_skill_names(cap_dir):
    """Installed names a capability would claim — declared entries plus any on-disk
    skill dir (an undeclared dir is a lint error, but it would still land if installed)."""
    data = frontmatter_soft(cap_dir / "CAPABILITY.md")
    if data is None:
        return set()
    prefix = effective_prefix(data, cap_dir.name)
    ids = {e.get("id") for e in (data.get("skills") or []) if isinstance(e, dict)}
    skills_dir = cap_dir / "skills"
    if skills_dir.is_dir():
        ids |= {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}
    return {installed_name(cap_dir.name, prefix, i) for i in ids if isinstance(i, str) and i}


def household_owners(root, exclude_cap):
    owners = {}
    for label in ("upstream", "personal"):
        caps_dir = root / label / "capabilities"
        if not caps_dir.is_dir():
            continue
        for cap in sorted(caps_dir.iterdir()):
            if cap.name == exclude_cap or not (cap / "CAPABILITY.md").is_file():
                continue
            for name in capability_skill_names(cap):
                owners.setdefault(name, f"capability '{cap.name}' in {label}/")
    return owners


def lock_link_names(root, capability):
    """Skill-link basenames the lockfile attributes to one capability."""
    path = root / LOCK_REL
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    out = {}
    for cap, entry in (data.get("installs") or {}).items():
        for link in (entry.get("links") or {}):
            # Only skill links participate — a linked script's basename is not a skill name.
            if "skills" not in Path(link).parts[:-1]:
                continue
            # .stem, not .name: a harness that installs skills as flat `<name>.md` files
            # (Nanobot) records a link whose basename carries the extension, and it has to
            # compare equal to a computed installed name at all three sites.
            out.setdefault(Path(link).stem, cap)
    return {name: cap for name, cap in out.items() if capability is None or cap == capability}


def aos_owned(entry, root):
    """Is this harness entry something aos materialized? Provenance answers it without the
    lockfile: a render is a symlink into the household, and every rendered SKILL.md carries
    the origin tag. The lockfile is machine-local and gitignored — if it is lost, a gate
    that trusted it alone would refuse every re-install of an already-installed capability,
    turning a recoverable state into a stuck one. Cross-capability conflicts are still
    caught: both capabilities are in the household, which the source scan reads.

    The tag is read as structured frontmatter, never as a substring. `ORIGIN_KEY in text`
    matched the string anywhere in the file — so a skill whose PROSE discussed provenance
    read as aos-installed, and the gate handed a stranger's name to an install that should
    have stopped at exit 17. This decision is what stands between a name collision and a
    silently overwritten skill, so it reads the key or it does not claim the entry."""
    if entry.is_symlink():
        target = os.path.normpath(os.path.join(str(entry.parent), os.readlink(entry)))
        if root and (str(root) + os.sep) in target + os.sep:
            return True
    skill_md = entry / "SKILL.md" if entry.is_dir() else entry
    data = frontmatter_soft(skill_md)
    if data is None:
        return False
    node = data
    for key in ORIGIN_PATH:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return bool(node)


def harness_owners(dirs, ours, root=None):
    owners = {}
    for d in dirs:
        p = Path(d).expanduser()
        if not p.is_dir():
            fail(1, f"--harness-skills: not a directory: {d}")
        for child in sorted(p.iterdir()):
            if child.is_dir():
                name = child.name
            elif child.suffix == ".md" and child.stem.upper() != "README":
                name = child.stem   # Nanobot's flat skills/<name>.md form
            else:
                continue
            if Path(name).stem in ours:
                continue        # our own link, per the lockfile
            if aos_owned(child, root):
                continue        # ...or per its provenance, when the lockfile cannot say
            owners.setdefault(name, f"skill already in the harness at {child}")
    return owners


def skill_collisions(args, cap_id, rows, cap_dir=None):
    """(collisions, sources consulted). The caller reports the sources: a source that was
    skipped must never be indistinguishable from a source that came back empty."""
    taken, ours, sources = {}, set(), []
    root = find_home_soft(args, cap_dir)
    if root:
        ours = {Path(n).stem for n in lock_link_names(root, cap_id)}
        taken.update(household_owners(root, cap_id))
        for name, cap in lock_link_names(root, None).items():
            if cap != cap_id:
                taken.setdefault(name, f"installed capability '{cap}' (lockfile link)")
        sources.append(f"household {root} (capabilities + lockfile links)")
    else:
        sources.append("NO HOUSEHOLD RESOLVED — other capabilities and the lockfile were "
                       "NOT checked (pass --home)")
    for name, where in harness_owners(args.harness_skills, ours, root).items():
        taken.setdefault(name, where)
    sources.append(f"{len(args.harness_skills)} harness skills dir(s)"
                   if args.harness_skills else
                   "NO --harness-skills GIVEN — skills already in the harness were NOT checked")

    out, seen = [], {}
    for r in rows:
        name = r["installed_name"]
        if name in seen:
            out.append(f"COLLISION {name}: computed by both '{seen[name]}' and '{r['id']}' "
                       f"in {cap_id} itself")
        seen[name] = r["id"]
        if name in taken:
            out.append(f"COLLISION {name} (from {cap_id}:{r['id']}) is already claimed by "
                       f"{taken[name]}")
    return out, sources


def cmd_skills(args):
    cap_dir = Path(args.dir).resolve()
    data, rows = skill_rows(cap_dir)
    if args.check:
        collisions, sources = skill_collisions(args, cap_dir.name, rows, cap_dir)
        if collisions:
            for line in collisions:
                print(line, file=sys.stderr)
            fail(17, f"{cap_dir.name}: {len(collisions)} skill-name collision(s) — "
                     f"resolve upstream, never rename at install time")
    if args.json:
        json.dump({"capability": cap_dir.name,
                   "skill_prefix": effective_prefix(data, cap_dir.name),
                   "skills": rows}, sys.stdout, indent=2)
        print()
    else:
        for r in rows:
            print(f"{r['id']}\t{r['installed_name']}\t{','.join(r['used_by'])}")
    if args.check:
        print(f"clean: {len(rows)} skill name{'' if len(rows) == 1 else 's'} unclaimed")
        for s in sources:
            print(f"  checked: {s}")


def stamp_render(path, name, origin):
    """Rewrite the render's frontmatter `name` to the installed name and stamp origin.

    Parses and re-emits the frontmatter rather than editing lines. The stamp lives at
    `metadata.aos.origin` — inside the Agent Skills spec's own extension hatch, because
    SKILL.md is somebody else's schema and we are the vendor in it. That makes the write a
    MERGE: `metadata.<harness>.*` is legitimate sibling data a line-based writer could not
    see, so appending a key would leave a stale nested one intact and clobber nothing it
    meant to. Losing comment and key-order fidelity is acceptable here and nowhere else:
    this runs on a render, which is a generated artifact.
    """
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(12, f"{path}: no YAML frontmatter block")
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if m is None:
        fail(12, f"{path}: unterminated frontmatter block")
    end = 4 + m.start()
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as e:
        fail(12, f"{path}: frontmatter is not valid YAML: {e}")
    if not isinstance(data, dict):
        fail(12, f"{path}: frontmatter must be a YAML mapping")
    if "name" not in data:
        fail(12, f"{path}: frontmatter has no name: field")

    data["name"] = name
    data.pop(LEGACY_ORIGIN_KEY, None)     # never inherit a stale top-level tag
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    aos = meta.get("aos")
    if not isinstance(aos, dict):
        aos = {}
    aos["origin"] = origin                # ours to overwrite; siblings are not
    meta["aos"] = aos
    data["metadata"] = meta

    body = text[end + len(m.group(0)):].lstrip("\n")
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(f"---\n{fm}---\n{body}")


def cmd_render(args):
    cap_dir = Path(args.dir).resolve()
    data, rows = skill_rows(cap_dir)
    row = next((r for r in rows if r["id"] == args.skill), None)
    if row is None:
        fail(14, f"{cap_dir.name}: no declared skill '{args.skill}'")
    src = cap_dir / "skills" / args.skill
    dest = Path(args.out).expanduser() / row["installed_name"]
    # `--out` must never point inside the package being rendered. Two distinct failures
    # live here, and a capability that `capability-build` or `capability-import` wrote hits
    # them on its FIRST upgrade, because it lives in `personal/capabilities/<id>/` — which
    # is exactly where install and upgrade say to render:
    #
    #   1. DATA LOSS, when dest lands on the source itself (the entry skill, whose id
    #      equals the capability's, so `installed_name == args.skill`). The rmtree below
    #      runs before the copytree, so the user's hand-written skill and its whole
    #      reference/ tree are deleted and then the copy dies on what it just removed.
    #   2. A BRICKED MANIFEST, when dest lands elsewhere under the package's `skills/`
    #      (any non-entry skill: `skills/drain` renders to `skills/<prefix>drain`). That
    #      is a second on-disk skill nothing declares, so every later `manifest`, `skills`
    #      and `render` on the capability fails exit 12 — and the install that created it
    #      can no longer be upgraded or removed.
    #
    # Rejecting the whole package directory covers both, and is what the skills mean by
    # "render into the household's skills root": somewhere outside the package.
    src_r, dest_r, pkg_r = src.resolve(), dest.resolve(), cap_dir.resolve()
    if dest_r == pkg_r or pkg_r in dest_r.parents:
        fail(1, f"--out points inside the package being rendered ({dest}) — that would "
                f"{'delete the source' if dest_r == src_r else 'add an undeclared skill the manifest then rejects'}. "
                f"Render to a destination outside {cap_dir}.")
    if dest.is_symlink():
        # A link where the render belongs is someone else's artifact, not ours to rmtree.
        fail(1, f"{dest} is a symlink — remove it first (renders are real directories)")
    if dest.exists() and not dest.is_dir():
        fail(1, f"{dest} exists and is not a directory")
    if dest.is_dir() and any(dest.iterdir()) and not args.force:
        fail(1, f"{dest} exists and is not empty (pass --force to re-render in place)")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    stamp_render(dest / "SKILL.md", row["installed_name"],
                 f"{cap_dir.name}@{data.get('version')}")
    print(f"rendered {cap_dir.name}:{args.skill} -> {dest}")


def load_lock(root):
    path = root / LOCK_REL
    if not path.is_file():
        fail(15, f"no lockfile at {path} (run: aos-cap init)")
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
                 f"install, not a rehash. Re-install, or `aos-cap remove` the entry.")
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
        prog="aos-cap",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--home", help="household root, e.g. ~/aos (else $AOS_HOME, else cwd-upward .aos/ search)")
    sub = p.add_subparsers(dest="verb", required=True)

    s = sub.add_parser("manifest", help="parse + validate a CAPABILITY.md -> JSON")
    s.add_argument("dir", help="capability directory")
    s.set_defaults(fn=cmd_manifest)

    s = sub.add_parser("skills", help="each skill's installed name; --check gates collisions (17)")
    s.add_argument("dir", help="capability directory")
    s.add_argument("--check", action="store_true",
                   help="fail (17) if any installed name is already claimed")
    s.add_argument("--harness-skills", action="append", default=[], metavar="DIR",
                   help="repeatable: a skills directory the harness already reads")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_skills)

    s = sub.add_parser("render", help="copy one skill to its installed name (idempotent)")
    s.add_argument("dir", help="capability directory")
    s.add_argument("skill", help="capability-local skill id")
    s.add_argument("--out", required=True, help="parent dir for the render (…/skills)")
    s.add_argument("--force", action="store_true", help="re-render over an existing render")
    s.set_defaults(fn=cmd_render)

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
