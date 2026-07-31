#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "typer>=0.15", "aos-cap"]
#
# [tool.uv.sources]
# aos-cap = { path = "../../capabilities/capability-lifecycle/tool", editable = true }
# ///
"""Tier-0 tests for the capability-lifecycle `aos-cap` tool.

In-process via typer's CliRunner, invoking the same `aos_cap.cli:app` that
`[project.scripts] aos-cap = "aos_cap.cli:main"` wires up — the exit code and the report
text (stdout/stderr) are the whole contract, and no import here reaches below `cli.py`'s
own `app` object. `InstalledScriptTest` at the bottom is the one subprocess class left:
proving that console script actually resolves and runs is the single thing an in-process
CliRunner call structurally cannot do, since it never leaves this process and so never
reads `[project.scripts]` or crosses a process boundary.

One class per module boundary in the tool, so a failure names the module that broke.
What each class must cover — every verb, every failure mode, and the bug behind each
regression pin — is mapped in `COVERAGE-cap.md`, which is diffable against this file:

  grep -o '^- \\[ \\] test_\\w*' tests/tool/COVERAGE-cap.md | sed 's/^- \\[ \\] //' | sort
  grep -o '  {four spaces}def test_\\w*' tests/tool/test_cap.py | sed 's/.*def //' | sort

(spelled with a placeholder above on purpose: the real pattern is four spaces, and
written literally this line would match itself and show up as a phantom test name.)

Run: uv run tests/tool/test_cap.py
"""
import contextlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from typer.testing import CliRunner

from aos_cap.cli import app

REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "capabilities/capability-lifecycle/tool"

_runner = CliRunner()

VALID_MANIFEST = """---
id: democap
version: 1.2.3
tags: [usecase]
summary: A demo capability for lock tests.
skills:
  - id: democap
    used_by: [main]
---
# democap briefing
"""

SKILL_MD = "---\nname: {name}\ndescription: {name}. Use when testing {name}.\n---\nbody\n"


def write_cap(home, cap_id, skills, prefix=None, root="upstream", version="1.0.0"):
    """Write a fixture capability under <home>/<root>/capabilities/ and return its dir.

    Module-level, taking `home` as a parameter, rather than a method on a shared base
    class: the test classes here are deliberately concrete leaves (CLAUDE.md's note that
    `BaseToolTest` is a leaf, not a base), and three byte-identical copies of this is a
    worse answer than one function they each call.
    """
    cap = home / root / "capabilities" / cap_id
    (cap / "skills").mkdir(parents=True)
    entries = "".join(f"  - id: {s}\n    used_by: [main]\n" for s in skills)
    cap.joinpath("CAPABILITY.md").write_text(
        f"---\nid: {cap_id}\nversion: {version}\ntags: [usecase]\n"
        f"summary: Fixture capability {cap_id}.\n"
        + (f"skill_prefix: {prefix}\n" if prefix is not None else "")
        + f"skills:\n{entries}---\n# {cap_id}\n")
    cap.joinpath("README.md").write_text(f"# {cap_id}\n")
    for s in skills:
        (cap / "skills" / s).mkdir()
        (cap / "skills" / s / "SKILL.md").write_text(SKILL_MD.format(name=s))
    return cap


class Result:
    """Adapts typer's CliRunner Result to the subprocess.CompletedProcess-shaped surface
    (.returncode/.stdout/.stderr) the assertions in this file are written against — the
    invocation layer is what changed, not the contract being asserted."""

    def __init__(self, cli_result):
        self._r = cli_result

    @property
    def returncode(self):
        return self._r.exit_code

    @property
    def stdout(self):
        return self._r.stdout

    @property
    def stderr(self):
        return self._r.stderr


@contextlib.contextmanager
def chdir(path):
    """`contextlib.chdir` is 3.11+ and this file's floor is 3.10, so: the same thing.

    Needed because CliRunner runs in *this* process and therefore inherits its cwd —
    unlike the subprocess era, where `cwd=` was free. Several behaviours here are genuine
    functions of the process cwd (the upward `.aos/` search, a relative `--artifact`, a
    relative capability dir), and `find_home_soft`'s comment records what relying on cwd
    alone once cost: `--check` skipped sources and still reported "clean".

    Deliberately not `CliRunner.isolated_filesystem()`: that makes its own temp dir, and
    every test below needs the household it built, not a fresh empty one."""
    before = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(before)


def run(args, env_extra=None, cwd=None):
    """In-process invocation of the same `app` the installed `aos-cap` script wires to.

    `AOS_HOME` is popped for every call: the household is an explicit argument of every
    test (via `--home`, `$AOS_HOME` set on purpose, or a cwd the test controls), and a
    developer with the variable exported would otherwise silently redirect the ones that
    assert discovery. `cwd`, when given, is applied for the duration of the call."""
    env = {"AOS_HOME": None}
    env.update(env_extra or {})
    with (chdir(cwd) if cwd else contextlib.nullcontext()):
        return Result(_runner.invoke(app, list(args), env=env, catch_exceptions=False))


class ManifestTest(unittest.TestCase):
    """`manifest` — §2.2 validation, and the exit-12 family. Mirrors
    `aos_cap.manifest` + `aos_cap.frontmatter`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.cap_dir = self.home / "capabilities" / "democap"
        (self.cap_dir / "skills" / "democap").mkdir(parents=True)
        (self.cap_dir / "CAPABILITY.md").write_text(VALID_MANIFEST)
        (self.cap_dir / "README.md").write_text("# democap\n\n| a | b |\n|---|---|\n")
        (self.cap_dir / "skills" / "democap" / "SKILL.md").write_text(
            "---\nname: democap\ndescription: demo. Use when testing.\n---\nbody\n")

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, *args):
        return run(["--home", str(self.home), "manifest", *args])

    def rewrite(self, old, new):
        mf = self.cap_dir / "CAPABILITY.md"
        mf.write_text(VALID_MANIFEST.replace(old, new))
        return mf.parent

    # -- valid packages ----------------------------------------------------
    def test_manifest_valid_prints_json(self):
        r = self.manifest(str(self.cap_dir))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["id"], "democap")
        self.assertEqual(data["version"], "1.2.3")

    def test_manifest_x_fields_allowed(self):
        # `x-*` is reserved in CAPABILITY.md — our schema — for THIRD parties.
        r = self.manifest(str(self.rewrite("summary:", "x-vendor: hi\nsummary:")))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_manifest_accepts_all_shipped_capabilities(self):
        # drift guard: the tool must accept every in-repo manifest the lint accepts
        for cap in sorted((REPO / "capabilities").iterdir()):
            if (cap / "CAPABILITY.md").is_file():
                r = self.manifest(str(cap))
                self.assertEqual(r.returncode, 0, f"{cap.name}: {r.stderr}")

    # -- exit 12 -----------------------------------------------------------
    def test_manifest_unknown_key_rejected(self):
        r = self.manifest(str(self.rewrite("summary:", "sneaky: yes\nsummary:")))
        self.assertEqual(r.returncode, 12)
        self.assertIn("sneaky", r.stderr)

    def test_manifest_bad_version_rejected(self):
        r = self.manifest(str(self.rewrite("1.2.3", "v1.2")))
        self.assertEqual(r.returncode, 12)
        self.assertIn("version", r.stderr)

    def test_manifest_undeclared_skill_dir_rejected(self):
        extra = self.cap_dir / "skills" / "ghost"
        extra.mkdir()
        (extra / "SKILL.md").write_text("---\nname: ghost\ndescription: g. Use when.\n---\n")
        r = self.manifest(str(self.cap_dir))
        self.assertEqual(r.returncode, 12)
        self.assertIn("ghost", r.stderr)

    def test_manifest_schedule_and_depends_rules(self):
        # One invocation reports EVERY problem: an installer fixing a manifest wants the
        # whole list, not the first line of it.
        cap = self.rewrite("skills:",
                           "depends:\n  capabilities: [ghostcap]\n"
                           "schedules:\n  - cron: \"0 4 * * *\"\n    agent: main\nskills:")
        r = self.manifest(str(cap))
        self.assertEqual(r.returncode, 12)
        self.assertIn("ghostcap", r.stderr)      # missing dependency
        self.assertIn("id", r.stderr)            # schedule id required
        self.assertIn("prompt_ref", r.stderr)    # agent form needs prompt_ref
        self.assertIn("degraded", r.stderr)      # degraded required

    def test_manifest_malformed_shapes_exit_12(self):
        cap = self.rewrite("skills:", "depends: [not, a, mapping]\nschedules: [oops]\nskills:")
        r = self.manifest(str(cap))
        self.assertEqual(r.returncode, 12)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("mapping", r.stderr)

    def test_manifest_scalar_frontmatter_exit_12(self):
        (self.cap_dir / "CAPABILITY.md").write_text("---\njust a string\n---\nbody\n")
        r = self.manifest(str(self.cap_dir))
        self.assertEqual(r.returncode, 12)
        self.assertIn("mapping", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class LockfileTest(unittest.TestCase):
    """The seven verbs that own `<home>/.aos/installs.lock.yaml` — `init record rehash
    verify show list remove`. Mirrors `aos_cap.lockfile` + `commands/lockfile.py`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        cap = self.home / "capabilities" / "democap"
        (cap / "skills" / "democap").mkdir(parents=True)
        (cap / "CAPABILITY.md").write_text(VALID_MANIFEST)
        (cap / "README.md").write_text("# democap\n")
        (cap / "skills" / "democap" / "SKILL.md").write_text(
            "---\nname: democap\ndescription: demo. Use when testing.\n---\nbody\n")
        self.a1 = self.home / "artifact-one.md"
        self.a2 = self.home / "artifact-two.md"
        self.a1.write_text("alpha\n")
        self.a2.write_text("beta\n")

    def tearDown(self):
        self.tmp.cleanup()

    def lock(self, *args, cwd=None, env=None):
        return run(["--home", str(self.home), *args] if cwd is None else list(args),
                   env_extra=env, cwd=cwd)

    def init(self):
        r = self.lock("init")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def record(self):
        return self.lock("record", "democap", "--version", "1.2.3",
                         "--artifact", str(self.a1), "--artifact", str(self.a2),
                         "--job", "job-abc123", "--config-key", "democap.run_hour")

    def make_link(self, name="skill-link"):
        target = self.home / "personal" / "capabilities" / "democap" / "skills" / "democap"
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text("---\nname: democap\n---\nrendered\n")
        link = self.home / name
        link.symlink_to(target)
        return link, target

    # -- init --------------------------------------------------------------
    def test_init_creates_empty_lockfile(self):
        self.init()
        text = (self.home / ".aos" / "installs.lock.yaml").read_text()
        self.assertIn("version: 1", text)
        self.assertIn("installs:", text)

    def test_init_creates_aos_dir_on_fresh_clone(self):
        # `init` is the one verb allowed to find no .aos/ — it is what creates it.
        fresh = Path(self.tmp.name) / "fresh"
        fresh.mkdir()
        r = run(["--home", str(fresh), "init"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((fresh / ".aos" / "installs.lock.yaml").is_file())

    def test_init_over_existing_lockfile_errors(self):
        self.init()
        r = self.lock("init")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)

    # -- record ------------------------------------------------------------
    def test_record_then_show(self):
        self.init()
        r = self.record()
        self.assertEqual(r.returncode, 0, r.stderr)
        s = self.lock("show", "democap")
        self.assertEqual(s.returncode, 0, s.stderr)
        entry = json.loads(s.stdout)
        self.assertEqual(entry["version"], "1.2.3")
        self.assertEqual(len(entry["artifacts"]), 2)
        self.assertIn("job-abc123", entry["schedules_owned"])
        self.assertIn("democap.run_hour", entry["config_keys"])
        for sha in entry["artifacts"].values():
            self.assertRegex(sha, r"^[0-9a-f]{64}$")

    def test_record_resolves_relative_paths(self):
        self.init()
        # cwd-dependent by design: a relative --artifact resolves against the process cwd,
        # and what is recorded must be absolute so a later verify from anywhere still passes.
        r = run(["record", "democap", "--version", "1.2.3",
                 "--artifact", "artifact-one.md"], cwd=str(self.home),
                env_extra={"AOS_HOME": str(self.home)})
        self.assertEqual(r.returncode, 0, r.stderr)
        s = run(["show", "democap"], cwd=str(Path(self.tmp.name)),
                env_extra={"AOS_HOME": str(self.home)})
        entry = json.loads(s.stdout)
        (path,) = entry["artifacts"].keys()
        self.assertTrue(Path(path).is_absolute())
        v = run(["verify", "democap"], cwd=str(Path(self.tmp.name)),
                env_extra={"AOS_HOME": str(self.home)})
        self.assertEqual(v.returncode, 0, v.stderr)

    def test_record_env_lines_and_scripts_roundtrip(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(self.a1),
                      "--env-line", "MY_TOKEN_NAME", "--script", str(self.a2))
        self.assertEqual(r.returncode, 0, r.stderr)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertIn("MY_TOKEN_NAME", entry["env_lines"])   # the NAME, never the value
        self.assertEqual(len(entry["scripts"]), 1)

    def test_record_link_and_verify_clean(self):
        self.init()
        link, target = self.make_link()
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(target / "SKILL.md"), "--link", str(link))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 links", r.stdout)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(entry["links"][str(link)], str(target))
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 0, v.stderr)

    def test_source_root_defaults_and_records(self):
        self.init()
        self.record()
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(entry["source_root"], "upstream")
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(self.a1), "--source-root", "personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(entry["source_root"], "personal")

    def test_relative_and_absolute_links_compare_equal(self):
        """PIN: link targets are stored absolute + lexically normalized and deliberately
        NOT resolve()d, so the two spellings of one destination compare equal — otherwise
        a relatively-spelled link (or a household under a symlinked path) reads as drift
        and every verify reports a break that is not there."""
        self.init()
        link, target = self.make_link()
        self.lock("record", "democap", "--version", "1.2.3", "--link", str(link))
        link.unlink()
        link.symlink_to(os.path.relpath(target, link.parent))
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)

    def test_record_missing_artifact_clean_error(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(self.home / "no-such.md"))
        self.assertEqual(r.returncode, 16)
        self.assertIn("no-such.md", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_record_link_on_regular_file_errors(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3", "--link", str(self.a1))
        self.assertEqual(r.returncode, 16)
        self.assertIn("not a symlink", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_symlink_as_artifact_rejected(self):
        # Hashing through a link would silently record the target's identity instead.
        self.init()
        f = self.home / "real.md"
        f.write_text("x\n")
        ln = self.home / "link-to-file.md"
        ln.symlink_to(f)
        r = self.lock("record", "democap", "--version", "1.2.3", "--artifact", str(ln))
        self.assertEqual(r.returncode, 16)
        self.assertIn("--link", r.stderr)

    # -- rehash ------------------------------------------------------------
    def test_rehash_refreshes_only_hashes(self):
        self.init()
        self.record()
        self.a1.write_text("alpha v2\n")
        r = self.lock("rehash", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 0, v.stderr)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(len(entry["artifacts"]), 2)
        self.assertIn("job-abc123", entry["schedules_owned"])

    def test_rehash_refuses_to_empty_an_entry(self):
        """PIN: when every recorded artifact is gone, that is a broken install and not a
        rehash. Emptying the entry would make the very next `verify` report clean — the
        drift check would be silently answering about nothing."""
        self.init()
        self.record()
        self.a1.unlink()
        self.a2.unlink()
        r = self.lock("rehash", "democap")
        self.assertEqual(r.returncode, 16)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(len(entry["artifacts"]), 2)   # entry left intact

    # -- verify ------------------------------------------------------------
    def test_verify_clean_and_drift(self):
        self.init()
        self.record()
        r = self.lock("verify", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean", r.stdout)
        self.a2.write_text("mutated\n")
        r = self.lock("verify", "democap")
        self.assertEqual(r.returncode, 13)
        self.assertIn("artifact-two.md", r.stdout)

    def test_verify_flags_missing_and_retargeted_link(self):
        self.init()
        link, _ = self.make_link()
        self.lock("record", "democap", "--version", "1.2.3", "--link", str(link))
        link.unlink()
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 13)
        self.assertIn("MISSING LINK", v.stdout)
        link.symlink_to(self.home / "elsewhere")
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 13)
        self.assertIn("RELINKED", v.stdout)

    def test_verify_flags_dangling_link(self):
        self.init()
        link, target = self.make_link()
        self.lock("record", "democap", "--version", "1.2.3", "--link", str(link))
        (target / "SKILL.md").unlink()
        target.rmdir()
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 13)
        self.assertIn("DANGLING LINK", v.stdout)

    def test_verify_unknown_capability(self):
        self.init()
        r = self.lock("verify", "nope")
        self.assertEqual(r.returncode, 14)

    # -- show / list / remove ---------------------------------------------
    def test_show_unknown_capability(self):
        self.init()
        r = self.lock("show", "nope")
        self.assertEqual(r.returncode, 14)

    def test_list_and_remove(self):
        self.init()
        self.record()
        r = self.lock("list")
        self.assertIn("democap", r.stdout)
        self.assertIn("1.2.3", r.stdout)
        r = self.lock("remove", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.lock("list")
        self.assertNotIn("democap", r.stdout)


class HouseholdTest(unittest.TestCase):
    """Resolving the household root: `home`, the cwd-upward `.aos/` search, `--home`,
    `$AOS_HOME` — the exit-15 family. Mirrors `aos_cap.household`.

    This is where the cwd-sensitive tests live, and cwd is the one thing an in-process
    CliRunner does not isolate for free (see the `chdir` helper)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.home = self.dir / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.artifact = self.home / "artifact-one.md"
        self.artifact.write_text("alpha\n")

    def tearDown(self):
        self.tmp.cleanup()

    def cap(self, cap_id, skills, **kw):
        return write_cap(self.home, cap_id, skills, **kw)

    def seed_lockfile(self):
        r = run(["--home", str(self.home), "init"])
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(["--home", str(self.home), "record", "democap", "--version", "1.2.3",
                 "--artifact", str(self.artifact)])
        self.assertEqual(r.returncode, 0, r.stderr)

    def bare(self, name):
        d = self.dir / name
        d.mkdir()
        return d

    # -- home --------------------------------------------------------------
    def test_home_verb_prints_resolved_root(self):
        self.seed_lockfile()
        r = run(["--home", str(self.home), "home"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(self.home))
        r = run(["home"], cwd=str(self.bare("nohome")))
        self.assertEqual(r.returncode, 15)

    def test_explicit_home_without_state_dir_errors(self):
        # An explicit --home with no .aos/ is an error, not a fresh start: only `init`
        # may create one.
        cap = self.cap("democap", ["democap"])
        r = run(["--home", str(self.bare("bare")), "skills", str(cap), "--check"])
        self.assertEqual(r.returncode, 15)

    def test_init_requires_explicit_clone(self):
        # `init` creates state, so the household is named rather than discovered.
        r = run(["init"], cwd=str(self.bare("bare-init")))
        self.assertEqual(r.returncode, 15)
        self.assertIn("--home", r.stderr)

    # -- discovery ---------------------------------------------------------
    def test_discovery_walks_up_from_cwd(self):
        self.seed_lockfile()
        nested = self.home / "upstream" / "capabilities"
        nested.mkdir(parents=True, exist_ok=True)
        r = run(["list"], cwd=str(nested))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap", r.stdout)

    def test_no_clone_found_errors(self):
        r = run(["list"], cwd=str(self.bare("elsewhere")))
        self.assertEqual(r.returncode, 15)
        self.assertIn(".aos", r.stderr)

    def test_env_override_wins_over_cwd(self):
        self.seed_lockfile()
        r = run(["list"], env_extra={"AOS_HOME": str(self.home)},
                cwd=str(self.bare("elsewhere2")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap", r.stdout)

    def test_collision_found_when_cwd_is_outside_the_household(self):
        """PIN: on a real machine the agent's cwd is the harness workspace, not the
        household, and no documented invocation passes --home. Resolving from cwd alone
        made `--check` skip the household and lockfile sources and still say "clean" — a
        silent no-op in the one gate that stops an overwrite. Discovery therefore also
        walks up from the capability directory, the one path every caller supplies."""
        self.cap("othercap", ["othercap", "sort"], prefix="democap-", root="personal")
        cap = self.cap("democap", ["democap", "sort"])
        r = run(["skills", str(cap), "--check"], cwd=str(self.bare("elsewhere3")))
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)
        self.assertIn("othercap", r.stderr)


class SkillNameTest(unittest.TestCase):
    """`skills` — the installed name (§2.5) and the collision gate. Mirrors
    `aos_cap.names`. The shipped identity is the COMPUTED name, so that is what carries
    the Agent Skills limits and what every source is compared against."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def cap(self, cap_id, skills, **kw):
        return write_cap(self.home, cap_id, skills, **kw)

    def write_lock(self, installs):
        (self.home / ".aos" / "installs.lock.yaml").write_text(
            "version: 1\ninstalls:\n" + "".join(
                f"  {cap}:\n    version: 1.0.0\n    links:\n" + "".join(
                    f"      {k}: {v}\n" for k, v in entry["links"].items())
                for cap, entry in installs.items()))

    def skills(self, cap, *extra):
        return run(["--home", str(self.home), "skills", str(cap), *extra])

    def names(self, cap, *extra):
        r = self.skills(cap, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return {line.split("\t")[0]: line.split("\t")[1]
                for line in r.stdout.strip().split("\n") if "\t" in line}

    # -- the algorithm -----------------------------------------------------
    def test_prefix_defaults_to_capability_id(self):
        cap = self.cap("democap", ["democap", "sort"])
        self.assertEqual(self.names(cap), {"democap": "democap", "sort": "democap-sort"})

    def test_declared_prefix_wins(self):
        cap = self.cap("democap", ["democap", "sort"], prefix="demo-")
        self.assertEqual(self.names(cap)["sort"], "demo-sort")

    def test_entry_skill_installs_verbatim(self):
        cap = self.cap("democap", ["democap"], prefix="demo-")
        self.assertEqual(self.names(cap)["democap"], "democap")

    def test_already_prefixed_id_is_not_double_prefixed(self):
        cap = self.cap("democap", ["democap", "demo-sort"], prefix="demo-")
        self.assertEqual(self.names(cap)["demo-sort"], "demo-sort")

    def test_empty_prefix_falls_back_to_default(self):
        # `skill_prefix: ""` means absent, not malformed.
        cap = self.cap("democap", ["democap", "sort"], prefix='""')
        self.assertEqual(self.names(cap)["sort"], "democap-sort")

    def test_json_reports_prefix_and_rows(self):
        cap = self.cap("democap", ["democap", "sort"], prefix="demo-")
        r = self.skills(cap, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["skill_prefix"], "demo-")
        self.assertEqual([s["installed_name"] for s in data["skills"]],
                         ["democap", "demo-sort"])

    def test_relative_capability_dir_works(self):
        """`aos-cap skills .` from inside the capability — the contract's commands are
        written with <cap-dir> paths, so a relative one must not break the id check."""
        cap = self.cap("democap", ["democap", "sort"])
        r = run(["--home", str(self.home), "skills", "."], cwd=str(cap))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap-sort", r.stdout)

    # -- name validation, against the INSTALLED name -----------------------
    def test_malformed_prefix_rejected(self):
        cap = self.cap("democap", ["democap"], prefix="Demo_")
        r = self.skills(cap)
        self.assertEqual(r.returncode, 12)
        self.assertIn("skill_prefix", r.stderr)

    def test_prefix_without_trailing_hyphen_rejected(self):
        cap = self.cap("democap", ["democap"], prefix="demo")
        self.assertEqual(self.skills(cap).returncode, 12)

    def test_over_long_installed_name_rejected(self):
        long_id = "a" + "-very" * 14          # id ok alone, too long once prefixed
        cap = self.cap("democap", ["democap", long_id])
        r = self.skills(cap)
        self.assertEqual(r.returncode, 12)
        self.assertIn("max 64", r.stderr)

    def test_reserved_word_in_installed_name_rejected(self):
        cap = self.cap("democap", ["democap", "claude-sync"])
        r = self.skills(cap)
        self.assertEqual(r.returncode, 12)
        self.assertIn("reserved", r.stderr)

    # -- the collision gate says no (exit 17) ------------------------------
    def test_collision_with_another_household_capability(self):
        self.cap("othercap", ["othercap", "sort"], prefix="democap-", root="personal")
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 17)
        self.assertIn("democap-sort", r.stderr)
        self.assertIn("othercap", r.stderr)

    def test_collision_inside_one_capability(self):
        """The entry skill's name, reached a second time through the prefix."""
        cap = self.cap("work-tracker", ["work-tracker", "tracker"], prefix="work-")
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 17)
        self.assertIn("itself", r.stderr)

    def test_collision_with_a_lockfile_link(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        self.write_lock({"othercap": {"links": {
            str(harness / "democap-sort"): "/elsewhere/skills/democap-sort"}}})
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 17)
        self.assertIn("othercap", r.stderr)

    def test_collision_with_a_skill_already_in_the_harness(self):
        harness = self.home / "harness" / "skills"
        (harness / "democap-sort").mkdir(parents=True)
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 17)
        self.assertIn("already in the harness", r.stderr)

    def test_flat_harness_skill_file_also_collides(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        (harness / "democap-sort.md").write_text("flat form (Nanobot)\n")
        cap = self.cap("democap", ["democap", "sort"])
        self.assertEqual(self.skills(cap, "--check", "--harness-skills",
                                     str(harness)).returncode, 17)

    def test_a_skill_merely_MENTIONING_the_origin_key_is_not_claimed_as_ours(self):
        """PIN: the collision gate falls back to provenance when the lockfile is lost, and
        the old test was `ORIGIN_KEY in text` — a substring, so a skill whose PROSE
        discussed the tag read as aos-installed. That hands a stranger's name to an
        install that should have stopped at exit 17."""
        cap = self.cap("democap", ["democap"])
        harness = self.home / "harness-skills"
        stranger = harness / "democap"
        stranger.mkdir(parents=True)
        (stranger / "SKILL.md").write_text(
            "---\nname: democap\ndescription: Not ours. Use when nothing.\n---\n"
            "This document explains what metadata.aos.origin means. It carries no such key.\n")
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 17, f"expected a collision, got:\n{r.stdout}{r.stderr}")

    def test_another_capabilitys_flat_form_link_still_collides(self):
        """PIN: the mirror of the flat-form exemption test — a flat-form link owned by
        someone ELSE must still be seen as a claim, so all three comparison sites have to
        agree on stems."""
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        self.write_lock({"othercap": {"links": {
            str(harness / "democap-sort.md"): "/elsewhere/skills/democap-sort.md"}}})
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)
        self.assertIn("othercap", r.stderr)

    def test_a_stranger_still_blocks_when_the_lockfile_is_lost(self):
        """PIN: the other half of the provenance fallback — it exempts our renders, not
        every name in the directory."""
        harness = self.home / "harness" / "skills"
        (harness / "democap-sort").mkdir(parents=True)
        (harness / "democap-sort" / "SKILL.md").write_text(
            "---\nname: democap-sort\ndescription: someone else got here first.\n---\nb\n")
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)

    # -- the gate says yes, for the right reason ---------------------------
    def test_clean_check_reports_unclaimed(self):
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean: 2 skill names unclaimed", r.stdout)

    def test_reinstall_over_our_own_links_is_clean(self):
        harness = self.home / "harness" / "skills"
        (harness / "democap-sort").mkdir(parents=True)
        self.write_lock({"democap": {"links": {
            str(harness / "democap-sort"): "/elsewhere/skills/democap-sort"}}})
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_non_skill_link_is_not_a_skill_name(self):
        # A linked script's basename is not a skill name.
        self.write_lock({"othercap": {"links": {
            "/h/scripts/democap-sort": "/elsewhere/scripts/democap-sort"}}})
        cap = self.cap("democap", ["democap", "sort"])
        self.assertEqual(self.skills(cap, "--check").returncode, 0)

    def test_malformed_neighbour_does_not_block_the_check(self):
        broken = self.home / "personal" / "capabilities" / "broken"
        broken.mkdir(parents=True)
        (broken / "CAPABILITY.md").write_text("not frontmatter at all\n")
        cap = self.cap("democap", ["democap", "sort"])
        self.assertEqual(self.skills(cap, "--check").returncode, 0)

    def test_readme_in_a_flat_skills_dir_is_not_a_skill(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        (harness / "README.md").write_text("what lives here\n")
        cap = self.cap("readme", ["readme"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_reinstall_over_our_own_flat_form_link_is_clean(self):
        """Nanobot installs skills as skills/<name>.md, so the lockfile records a link
        whose basename carries .md — it still has to match our own exemption."""
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        (harness / "democap-sort.md").write_text("flat form\n")
        self.write_lock({"democap": {"links": {
            str(harness / "democap-sort.md"): "/elsewhere/skills/democap-sort.md"}}})
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lost_lockfile_does_not_block_reinstall(self):
        """PIN: .aos/ is machine-local and gitignored. If it is lost, a gate that trusted
        it alone would see our own installed skills as strangers and refuse every
        re-install — turning a recoverable state into a stuck one. Provenance answers
        instead."""
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        cap = self.cap("democap", ["democap", "sort"])
        render = self.home / "personal" / "capabilities" / "democap" / "skills" / "democap-sort"
        render.mkdir(parents=True)
        (render / "SKILL.md").write_text(
            "---\nname: democap-sort\ndescription: d. Use when.\n"
            "metadata:\n  aos:\n    origin: democap@1.0.0\n---\nb\n")
        (harness / "democap-sort").symlink_to(render)
        # no lockfile entry at all — the household knows nothing about this install
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_clean_report_names_the_sources_it_could_not_check(self):
        """PIN: a skipped source must never be indistinguishable from an empty one."""
        lone = Path(self.tmp.name) / "lone" / "lonecap"
        (lone / "skills" / "lonecap").mkdir(parents=True)
        (lone / "CAPABILITY.md").write_text(
            "---\nid: lonecap\nversion: 1.0.0\ntags: [infra]\nsummary: No household.\n"
            "skills:\n  - id: lonecap\n    used_by: [main]\n---\nbody\n")
        (lone / "README.md").write_text("# lonecap\n")
        (lone / "skills" / "lonecap" / "SKILL.md").write_text(SKILL_MD.format(name="lonecap"))
        r = run(["skills", str(lone), "--check"], cwd=str(Path(self.tmp.name) / "lone"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NO HOUSEHOLD RESOLVED", r.stdout)
        self.assertIn("NO --harness-skills GIVEN", r.stdout)

    def test_clean_report_names_the_sources_it_did_check(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        cap = self.cap("democap", ["democap"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("household", r.stdout)
        self.assertIn("1 harness skills dir", r.stdout)

    # -- bad input ---------------------------------------------------------
    def test_bad_harness_skills_arg_is_a_generic_error(self):
        cap = self.cap("democap", ["democap"])
        r = self.skills(cap, "--check", "--harness-skills", str(self.home / "nope"))
        self.assertEqual(r.returncode, 1)


class RenderTest(unittest.TestCase):
    """`render` — the one verb that materializes a skill. Mirrors `commands/render.py`:
    the copy, the frontmatter stamp, and the guards on `--out`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.out = Path(self.tmp.name) / "renders"

    def tearDown(self):
        self.tmp.cleanup()

    def cap(self, cap_id, skills, **kw):
        return write_cap(self.home, cap_id, skills, **kw)

    def origin(self, skill_md):
        """The provenance stamp, read as YAML. Deliberately not a substring check: the
        whole point of `metadata.aos` is that it is structured data, and an assertIn would
        pass on the string appearing anywhere — including in prose."""
        fm = yaml.safe_load(skill_md.read_text().split("---", 2)[1])
        return ((fm or {}).get("metadata") or {}).get("aos", {}).get("origin")

    def render(self, cap, skill, *extra, out=None):
        return run(["render", str(cap), skill, "--out", str(out or self.out), *extra])

    # -- the happy path ----------------------------------------------------
    def test_render_lands_under_the_installed_name(self):
        cap = self.cap("democap", ["democap", "sort"])
        r = self.render(cap, "sort")
        self.assertEqual(r.returncode, 0, r.stderr)
        rendered = self.out / "democap-sort" / "SKILL.md"
        self.assertTrue(rendered.is_file())
        self.assertIn("name: democap-sort", rendered.read_text())
        self.assertEqual(self.origin(rendered), "democap@1.0.0")

    def test_render_carries_bundled_assets(self):
        cap = self.cap("democap", ["democap", "sort"])
        (cap / "skills" / "sort" / "reference").mkdir()
        (cap / "skills" / "sort" / "reference" / "deep.md").write_text("depth\n")
        self.render(cap, "sort")
        self.assertEqual((self.out / "democap-sort" / "reference" / "deep.md").read_text(),
                         "depth\n")

    def test_render_preserves_mod_slots(self):
        # render is mechanical: overlay slots are resolved by the harness agent, not here.
        cap = self.cap("democap", ["democap", "sort"])
        skill = cap / "skills" / "sort" / "SKILL.md"
        skill.write_text(skill.read_text() + "Confirm with {{mod: confirm_style}}.\n")
        self.render(cap, "sort")
        self.assertIn("{{mod: confirm_style}}",
                      (self.out / "democap-sort" / "SKILL.md").read_text())

    def test_render_is_idempotent(self):
        cap = self.cap("democap", ["democap", "sort"])
        self.render(cap, "sort")
        first = (self.out / "democap-sort" / "SKILL.md").read_text()
        r = self.render(cap, "sort", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.out / "democap-sort" / "SKILL.md").read_text(), first)

    def test_render_never_inherits_a_stale_origin_tag(self):
        cap = self.cap("democap", ["democap", "sort"])
        skill = cap / "skills" / "sort" / "SKILL.md"
        skill.write_text(skill.read_text().replace(
            "---\nbody", "metadata:\n  aos:\n    origin: someoneelse@9.9.9\n---\nbody"))
        self.render(cap, "sort")
        rendered = self.out / "democap-sort" / "SKILL.md"
        self.assertNotIn("someoneelse", rendered.read_text())
        self.assertEqual(self.origin(rendered), "democap@1.0.0")

    def test_render_merges_the_stamp_into_an_existing_metadata_block(self):
        """PIN: `metadata` is the Agent Skills spec's own extension hatch, so a skill may
        already carry harness-specific keys there. Stamping ours must merge, never clobber
        — the old line-based writer appended a top-level key and could not see a sibling
        at all."""
        cap = self.cap("democap", ["democap", "sort"])
        skill = cap / "skills" / "sort" / "SKILL.md"
        skill.write_text(skill.read_text().replace(
            "---\nbody", "metadata:\n  hermes:\n    profile: aos-test\n---\nbody"))
        r = self.render(cap, "sort")
        self.assertEqual(r.returncode, 0, r.stderr)
        fm = yaml.safe_load((self.out / "democap-sort" / "SKILL.md").read_text().split("---", 2)[1])
        self.assertEqual(fm["metadata"]["aos"]["origin"], "democap@1.0.0")
        self.assertEqual(fm["metadata"]["hermes"]["profile"], "aos-test")

    # -- refusals ----------------------------------------------------------
    def test_render_refuses_to_clobber_without_force(self):
        cap = self.cap("democap", ["democap", "sort"])
        self.render(cap, "sort")
        r = self.render(cap, "sort")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)

    def test_render_destination_that_is_a_file_errors_cleanly(self):
        cap = self.cap("democap", ["democap", "sort"])
        self.out.mkdir()
        (self.out / "democap-sort").write_text("a file sits where the render goes\n")
        r = self.render(cap, "sort")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)

    def test_render_destination_that_is_a_symlink_errors_cleanly(self):
        cap = self.cap("democap", ["democap", "sort"])
        self.out.mkdir()
        target = Path(self.tmp.name) / "someone-elses-dir"
        target.mkdir()
        (self.out / "democap-sort").symlink_to(target)
        r = self.render(cap, "sort", "--force")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertTrue(target.is_dir())      # never rmtree'd through the link

    def test_render_into_the_packages_own_skills_dir_is_refused(self):
        """PIN, and the destructive case — not a corner case: a capability that
        `capability-build` or `capability-import` wrote lives in
        `personal/capabilities/<id>/`, which is exactly where the install and upgrade
        skills say to render — so `--out <pkg>/skills` fires on that capability's FIRST
        upgrade. rmtree runs before copytree, so the user's hand-written skill and its
        whole reference/ tree are deleted and then the copy dies on the source it just
        removed. Refuse before touching anything."""
        cap = self.cap("democap", ["democap", "sort"])
        precious = cap / "skills" / "democap" / "reference" / "deep.md"
        precious.parent.mkdir(parents=True, exist_ok=True)
        precious.write_text("irreplaceable hand-written content\n")
        entry = cap / "skills" / "democap" / "SKILL.md"
        before = entry.read_text()

        r = self.render(cap, "democap", "--force", out=cap / "skills")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)          # not an unhandled FileNotFoundError
        self.assertIn("inside the package", r.stderr)
        # the whole point: the source survived
        self.assertTrue(precious.is_file(), "reference/ tree was destroyed")
        self.assertEqual(precious.read_text(), "irreplaceable hand-written content\n")
        self.assertEqual(entry.read_text(), before)

        # and a render to a genuinely separate root still works
        self.assertEqual(self.render(cap, "democap").returncode, 0)

    def test_render_of_a_non_entry_skill_into_the_package_is_refused_too(self):
        """PIN, the second half of the same defect, which a narrower guard misses. A
        non-entry skill renders to `<prefix><id>`, so `skills/sort` -> `skills/democap-sort`
        never touches the source — but it plants a second on-disk skill nothing declares,
        and every later manifest/skills/render on that capability then fails exit 12. The
        install that created it can no longer be upgraded or removed."""
        cap = self.cap("democap", ["democap", "sort"])
        r = self.render(cap, "sort", out=cap / "skills")
        self.assertEqual(r.returncode, 1)
        self.assertIn("inside the package", r.stderr)
        self.assertFalse((cap / "skills" / "democap-sort").exists())
        # the manifest the guard was protecting still validates
        self.assertEqual(run(["manifest", str(cap)]).returncode, 0)

    def test_render_to_the_package_root_is_refused(self):
        """PIN: `--out <pkg>` puts the render beside CAPABILITY.md rather than under
        skills/. It destroys nothing and does not brick the manifest, so it is the mildest
        case — but it is still litter inside a package the user owns, and no skill ever
        asks for it. Refusing keeps the rule simple enough to state: --out lives outside."""
        cap = self.cap("democap", ["democap"])
        r = self.render(cap, "democap", "--force", out=cap)
        self.assertEqual(r.returncode, 1)
        self.assertIn("inside the package", r.stderr)

    def test_render_unknown_skill_errors(self):
        cap = self.cap("democap", ["democap"])
        r = self.render(cap, "ghost")
        self.assertEqual(r.returncode, 14)


class ToolIdentityTest(unittest.TestCase):
    """The command name and the version pair. Both drifted silently once: the rename left
    `pyproject.toml` at 0.3.4 while CAPABILITY.md said 0.3.5, and nothing failed — there was
    no --version verb and no gate on the pair. Mirrors test_kb.py's equivalent."""

    def declared(self):
        return re.search(r"^version: (\S+)",
                         (REPO / "capabilities/capability-lifecycle/CAPABILITY.md").read_text(),
                         re.M).group(1)

    def test_the_command_is_aos_cap(self):
        r = run(["--version"])
        self.assertEqual(r.returncode, 0, r.stderr)
        # Read from the manifest, not pinned: the number is the capability's, and a literal
        # here is one more thing a bump has to remember.
        self.assertIn(f"aos-cap {self.declared()}", r.stdout)

    def test_pyproject_version_tracks_the_capability(self):
        """PIN: the comment in pyproject says it tracks the capability version. Nothing
        enforced that, so it silently fell a patch behind during the rename."""
        declared = self.declared()
        pyproject = (TOOL_DIR / "pyproject.toml").read_text()
        # re.M, because assertRegex does not apply it and `^` would only match the
        # string start — which is `[project]`, not the version line.
        self.assertTrue(re.search(rf'^version = "{re.escape(declared)}"', pyproject, re.M),
                        f"pyproject version does not track the capability's {declared}")

    def test_the_old_command_name_is_gone(self):
        pyproject = (TOOL_DIR / "pyproject.toml").read_text()
        self.assertIn('name = "aos-cap"', pyproject)
        self.assertIn('aos-cap = "aos_cap.cli:main"', pyproject)
        # Spelled defensively: a sed sweep of the module name would rewrite a naive check
        # into passing against itself.
        old_pkg, old_mod = "aos" + "-lock", "aos" + "_lock"
        self.assertNotIn(old_pkg, pyproject)
        self.assertNotIn(old_mod, pyproject)
        self.assertFalse((TOOL_DIR / "src" / old_mod).exists())


class InstalledScriptTest(unittest.TestCase):
    """The one thing CliRunner structurally cannot prove: that `[project.scripts]
    aos-cap = "aos_cap.cli:main"` actually resolves and runs as an installed console
    script, crossing a real process boundary. Every other class in this file runs
    in-process — this is deliberately the sole subprocess survivor."""

    def run_installed(self, args, env_extra=None):
        env = dict(os.environ)
        env.pop("AOS_HOME", None)
        env.update(env_extra or {})
        return subprocess.run(["uv", "run", "--quiet", "--project", str(TOOL_DIR),
                               "aos-cap", *args],
                              capture_output=True, text=True, env=env)

    def test_the_installed_script_runs_and_reports_its_version(self):
        r = self.run_installed(["--version"])
        self.assertEqual(r.returncode, 0, r.stderr)
        declared = re.search(r"^version: (\S+)",
                             (REPO / "capabilities/capability-lifecycle/CAPABILITY.md").read_text(),
                             re.M).group(1)
        self.assertIn(f"aos-cap {declared}", r.stdout)

    def test_the_installed_script_completes_a_real_verb_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            (home / ".aos").mkdir(parents=True)
            artifact = home / "artifact.md"
            artifact.write_text("alpha\n")
            r = self.run_installed(["--home", str(home), "init"])
            self.assertEqual(r.returncode, 0, r.stderr)
            r = self.run_installed(["--home", str(home), "record", "democap",
                                    "--version", "1.2.3", "--artifact", str(artifact)])
            self.assertEqual(r.returncode, 0, r.stderr)
            r = self.run_installed(["--home", str(home), "list"])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("democap  1.2.3", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
