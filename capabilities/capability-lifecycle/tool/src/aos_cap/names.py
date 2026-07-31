"""Skill and agent identity (§2.5) and the collision gate.

A skill id is capability-local; the name it INSTALLS under is `<prefix><id>`, and that
computed name is the shipped identity — single-owner across the whole harness, which is
why the Agent Skills limits are checked against it and never against the id. Everything
here is a pure function of files on disk: the four sources a name can already be claimed
by (this capability itself, another household capability, a lockfile link, a skill
already in the harness) each get their own reader, and `skill_collisions()` joins them.

An AGENT name is the same hazard in a different directory: harnesses keep agents in a
flat per-harness namespace too (`~/.hermes/profiles/<name>/`, `~/.claude/agents/<name>.md`),
so two capabilities shipping `archiver` silently override each other. `agent_collisions()`
is the twin gate — same computation, same exit code, and it shares the join with the skill
gate (`_household_claims` + `_name_collisions`) so the two can never drift on what
"already claimed" means."""

import os
from pathlib import Path
from typing import Iterable, Optional

import yaml

from .constants import (
    LOCK_REL, ORIGIN_PATH, RESERVED_NAME_WORDS, SKILL_NAME_MAX, SKILL_NAME_RE,
)
from .errors import Exit, fail
from .frontmatter import frontmatter_soft
from .household import HasHome, find_home_soft


def effective_prefix(manifest: dict, cap_id: str) -> str:
    """§2.2: declared prefix, else the capability id. Absent/empty means default."""
    declared = manifest.get("skill_prefix")
    if isinstance(declared, str) and declared.strip():
        return declared
    return f"{cap_id}-"


def installed_name(cap_id: str, prefix: str, skill_id: str) -> str:
    """The name the skill ships under. Entry skill verbatim; never double-prefixed."""
    if skill_id == cap_id or skill_id.startswith(prefix):
        return skill_id
    return f"{prefix}{skill_id}"


def name_errors(name: str, what: str) -> list[str]:
    errs = []
    if len(name) > SKILL_NAME_MAX:
        errs.append(f"{what} '{name}' is {len(name)} chars (max {SKILL_NAME_MAX})")
    if not SKILL_NAME_RE.match(name):
        errs.append(f"{what} '{name}' must be [a-z0-9-], no leading/trailing/double hyphens")
    for word in RESERVED_NAME_WORDS:
        if word in name:
            errs.append(f"{what} '{name}' contains the reserved word '{word}'")
    return errs


def capability_skill_names(cap_dir: Path) -> set[str]:
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


def declared_agent_ids(cap_dir: Path) -> set[str]:
    """Every agent this capability ships: each `agents/*.agent.yaml`'s `name:`, falling
    back to the filename stem when the spec is unreadable or unnamed. Soft by design —
    the same reason `frontmatter_soft` exists: a malformed spec must not raise out of a
    name computation. `main` is NOT included: it is the harness's shared agent, not a
    capability's, and the callers that need it add it themselves."""
    out: set[str] = set()
    agents_dir = Path(cap_dir) / "agents"
    if not agents_dir.is_dir():
        return out
    for spec in sorted(agents_dir.glob("*.agent.yaml")):
        try:
            name = (yaml.safe_load(spec.read_text()) or {}).get("name")
        except (yaml.YAMLError, OSError):
            name = None
        if not isinstance(name, str) or not name.strip():
            name = spec.name.replace(".agent.yaml", "")
        out.add(name)
    return out


def capability_agent_names(cap_dir: Path) -> set[str]:
    """The agent twin of `capability_skill_names`. Agents land in a flat per-harness
    namespace exactly like skills, so they take the capability's declared `skill_prefix`
    — no second manifest field, because §2.2's rule of two says a field exists only once
    two capabilities need it machine-read, and one prefix per capability is what both
    namespaces want anyway."""
    data = frontmatter_soft(Path(cap_dir) / "CAPABILITY.md")
    if data is None:
        return set()
    prefix = effective_prefix(data, Path(cap_dir).name)
    return {installed_name(Path(cap_dir).name, prefix, a) for a in declared_agent_ids(cap_dir)}


def _household_of(cap_dir: Path) -> Optional[Path]:
    """The `<home>/` a capability directory sits inside, or None.

    Deliberately NOT `find_home_soft`: that one answers "which household is this
    invocation about", so it consults `--home`, `$AOS_HOME` and the cwd first — all of
    which can name a DIFFERENT household than the package being read. This one answers
    "where does this directory live", which has exactly one honest source: the path
    itself. A household package lives at `<home>/{upstream,personal}/capabilities/<id>`,
    so the home is the ancestor whose `upstream/` or `personal/` the package is INSIDE.

    Anchored that way rather than by looking for a marker, and deliberately not `.aos/`:
    `.aos/` is machine-local and exists at `~/` on any machine that has ever installed aos,
    so a marker search would let a real household anywhere above an unrelated kit clone
    claim it — and cross-capability references in `~/work/aos` would start resolving into
    `~/personal`. A package that is in no household gets None, and `resolve_capability`
    falls back to the sibling directory for it.
    """
    cap_dir = Path(cap_dir).resolve()
    for cand in cap_dir.parents:
        for label in ("upstream", "personal"):
            root = cand / label
            if root.is_dir() and root in cap_dir.parents:
                return cand
    return None


def resolve_capability(cap_id: str, cap_dir: Path) -> tuple[Optional[Path], Optional[dict], bool]:
    """Resolve a capability id to (dir, manifest, shadowed) — personal/ first, then
    upstream/, per the install contract. NOT `cap_dir.parent`: a capability in personal/
    referencing one in upstream/ is the normal case for anything capability-build wrote,
    and a sibling-only lookup fails it on a correct reference.

    `shadowed` is True when the id exists in BOTH roots. The contract says that is
    reported loudly, never silently preferred — so callers must not just take personal/.

    The sibling directory is consulted only as a LAST resort, for a package that is in no
    household at all: a bare kit clone (this repo's own flat `capabilities/`), a fixture
    tree. That is a real invocation — `aos-cap manifest capabilities/kb` — and it has no
    upstream/personal to resolve against.
    """
    found: list[Path] = []
    root = _household_of(cap_dir)
    if root:
        for label in ("personal", "upstream"):
            cand = root / label / "capabilities" / cap_id
            if (cand / "CAPABILITY.md").is_file():
                found.append(cand)
    if not found:
        sibling = Path(cap_dir).resolve().parent / cap_id
        if (sibling / "CAPABILITY.md").is_file():
            found.append(sibling)
    if not found:
        return None, None, False
    return found[0], frontmatter_soft(found[0] / "CAPABILITY.md"), len(found) > 1


def household_owners(root: Path, exclude_cap: str, namer=capability_skill_names,
                     ) -> dict[str, str]:
    """Every name the household's OTHER capabilities claim → who claims it.

    `namer` is which namespace to read: `capability_skill_names` (the default, and the
    skill gate's) or `capability_agent_names`. Parameterized rather than copied so the
    two gates cannot drift on what counts as a household claim — the exclude rule, the
    two roots, and "a directory is a package only if it holds a CAPABILITY.md" are one
    implementation."""
    owners: dict[str, str] = {}
    for label in ("upstream", "personal"):
        caps_dir = root / label / "capabilities"
        if not caps_dir.is_dir():
            continue
        for cap in sorted(caps_dir.iterdir()):
            if cap.name == exclude_cap or not (cap / "CAPABILITY.md").is_file():
                continue
            for name in namer(cap):
                owners.setdefault(name, f"capability '{cap.name}' in {label}/")
    return owners


def lock_link_names(root: Path, capability: Optional[str]) -> dict[str, str]:
    """Skill-link basenames the lockfile attributes to one capability."""
    path = root / LOCK_REL
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    out: dict[str, str] = {}
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


def aos_owned(entry: Path, root: Optional[Path]) -> bool:
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


def harness_owners(dirs: Iterable[str], ours: set[str],
                   root: Optional[Path] = None) -> dict[str, str]:
    owners: dict[str, str] = {}
    for d in dirs:
        p = Path(d).expanduser()
        if not p.is_dir():
            fail(Exit.GENERIC, f"--harness-skills: not a directory: {d}")
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


def _household_claims(opts: HasHome, cap_id: str, cap_dir: Optional[Path], namer,
                      ) -> tuple[Optional[Path], dict[str, str], set[str], str]:
    """The two free sources — the household's other capabilities and the lockfile's
    recorded links — as (root, taken, ours, source label).

    Shared by both gates, and it returns the source LABEL rather than printing anything:
    a source that was skipped must never be indistinguishable from a source that came
    back empty, so the label says `NO HOUSEHOLD RESOLVED` in as many words."""
    taken: dict[str, str] = {}
    ours: set[str] = set()
    root = find_home_soft(opts, cap_dir)
    if root:
        ours = {Path(n).stem for n in lock_link_names(root, cap_id)}
        taken.update(household_owners(root, cap_id, namer))
        for name, cap in lock_link_names(root, None).items():
            if cap != cap_id:
                taken.setdefault(name, f"installed capability '{cap}' (lockfile link)")
        return root, taken, ours, f"household {root} (capabilities + lockfile links)"
    return None, taken, ours, ("NO HOUSEHOLD RESOLVED — other capabilities and the "
                               "lockfile were NOT checked (pass --home)")


def _name_collisions(taken: dict[str, str], cap_id: str, rows: list[dict]) -> list[str]:
    """Every computed name in `rows` against `taken`, plus rows against each other.

    Namespace-agnostic on purpose: a skill name and an agent name collide the same way
    (one flat per-harness namespace, silent override), so the join, the message shape and
    the exit code are one implementation for both."""
    out: list[str] = []
    seen: dict[str, str] = {}
    for r in rows:
        name = r["installed_name"]
        if name in seen:
            out.append(f"COLLISION {name}: computed by both '{seen[name]}' and '{r['id']}' "
                       f"in {cap_id} itself")
        seen[name] = r["id"]
        if name in taken:
            out.append(f"COLLISION {name} (from {cap_id}:{r['id']}) is already claimed by "
                       f"{taken[name]}")
    return out


def skill_collisions(opts: HasHome, harness_skills: list[str], cap_id: str,
                     rows: list[dict], cap_dir: Optional[Path] = None,
                     ) -> tuple[list[str], list[str]]:
    """(collisions, sources consulted). The caller reports the sources: a source that was
    skipped must never be indistinguishable from a source that came back empty."""
    root, taken, ours, household_source = _household_claims(
        opts, cap_id, cap_dir, capability_skill_names)
    sources = [household_source]
    for name, where in harness_owners(harness_skills, ours, root).items():
        taken.setdefault(name, where)
    sources.append(f"{len(harness_skills)} harness skills dir(s)"
                   if harness_skills else
                   "NO --harness-skills GIVEN — skills already in the harness were NOT checked")
    return _name_collisions(taken, cap_id, rows), sources


def agent_collisions(opts: HasHome, cap_id: str, rows: list[dict],
                     cap_dir: Optional[Path] = None) -> tuple[list[str], list[str]]:
    """The agent twin of `skill_collisions` — two of three sources, and it says so.

    Enumerating the agents ALREADY in the harness is deferred: it needs a per-harness
    listing command (`hermes profile list`, `ls ~/.claude/agents/`, `openclaw agents list`,
    `ncl groups list`, `ls agents/`) in all five cheat-sheets, for a source no shipped
    capability collides on today. Deferred is not silent — the third source is named in
    capitals in the report, the same discipline `skill_collisions` holds for a household it
    could not resolve."""
    _root, taken, _ours, household_source = _household_claims(
        opts, cap_id, cap_dir, capability_agent_names)
    sources = [household_source,
               "NO --harness-agents SUPPORTED YET — agents already in the harness were "
               "NOT checked"]
    return _name_collisions(taken, cap_id, rows), sources
