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
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from typer.testing import CliRunner

from aos_cap.cli import app

# `send2trash` fixes its trash directory from $XDG_DATA_HOME the first time it is imported,
# and every test here runs in this one process — so a per-test XDG_DATA_HOME would be read
# once and ignored after. Pin one throwaway trash for the whole run, before anything can
# import it: no test ever reaches the developer's real trash, and each test empties it.
TRASH_HOME = Path(tempfile.mkdtemp(prefix="aos-cap-test-trash-"))
os.environ["XDG_DATA_HOME"] = str(TRASH_HOME)
import send2trash  # noqa: E402,F401 — imported after the pin, on purpose

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


def write_cap(home, cap_id, skills, prefix=None, root="upstream", version="1.0.0",
              agents=(), depends=()):
    """Write a fixture capability under <aos_home>/<root>/capabilities/ and return its dir.

    Module-level, taking `home` as a parameter, rather than a method on a shared base
    class: the test classes here are deliberately concrete leaves (CLAUDE.md's note that
    `BaseToolTest` is a leaf, not a base), and three byte-identical copies of this is a
    worse answer than one function they each call.

    `agents` writes an `agents/<name>.agent.yaml` per id — extended here rather than in a
    second builder, since an agent is one more thing the same package declares and a
    parallel `write_cap_with_agents` would drift from this one on the next manifest field.
    """
    cap = home / root / "capabilities" / cap_id
    (cap / "skills").mkdir(parents=True)
    entries = "".join(f"  - id: {s}\n    used_by: [main]\n" for s in skills)
    dep = (f"depends:\n  capabilities: [{', '.join(depends)}]\n" if depends else "")
    cap.joinpath("CAPABILITY.md").write_text(
        f"---\nid: {cap_id}\nversion: {version}\ntags: [usecase]\n"
        f"summary: Fixture capability {cap_id}.\n"
        + dep
        + (f"skill_prefix: {prefix}\n" if prefix is not None else "")
        + f"skills:\n{entries}---\n# {cap_id}\n")
    cap.joinpath("README.md").write_text(f"# {cap_id}\n")
    for s in skills:
        (cap / "skills" / s).mkdir()
        (cap / "skills" / s / "SKILL.md").write_text(SKILL_MD.format(name=s))
    for a in agents:
        (cap / "agents").mkdir(exist_ok=True)
        (cap / "agents" / f"{a}.agent.yaml").write_text(
            f"name: {a}\npurpose: Fixture agent {a}.\nmodel_class: balanced\n")
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
    unlike the subprocess era, where `cwd=` was free. Some behaviours here are genuine
    functions of the process cwd (a relative `--artifact`, a relative capability dir),
    and one is pinned as NOT being one: the household never comes from the cwd.

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

    `AOS_HOME` is popped and HOME is a fresh empty directory for every call, unless the
    test sets either on purpose: the household is `--home`, else `$AOS_HOME`, else
    `~/aos`, so an inherited AOS_HOME would redirect the tests that assert resolution, and
    an inherited HOME would point the rest at the developer's real `~/aos`. `cwd`, when
    given, is applied for the duration of the call."""
    with tempfile.TemporaryDirectory() as home, \
            (chdir(cwd) if cwd else contextlib.nullcontext()):
        env = {"AOS_HOME": None, "HOME": home, **(env_extra or {})}
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

    def test_depends_resolves_across_the_two_household_roots(self):
        """PIN: the check was `cap_dir.parent / dep` — the SIBLING directory only — so a
        capability in `personal/` declaring a dependency on one in `upstream/` failed
        validation on a CORRECT declaration. That is every capability `capability-build`
        writes. Resolution is personal/ first, then upstream/, per the install contract."""
        write_cap(self.home, "kbc", ["kbc"], root="upstream")
        mine = write_cap(self.home, "mine", ["mine"], root="personal", depends=["kbc"])
        r = self.manifest(str(mine))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

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

    def test_manifest_cron_and_depends_rules(self):
        # One invocation reports EVERY problem: an installer fixing a manifest wants the
        # whole list, not the first line of it.
        cap = self.rewrite("skills:",
                           "depends:\n  capabilities: [ghostcap]\n"
                           "cron:\n  - expr: \"0 4 * * *\"\n    agent: main\nskills:")
        r = self.manifest(str(cap))
        self.assertEqual(r.returncode, 12)
        self.assertIn("ghostcap", r.stderr)      # missing dependency
        self.assertIn("id", r.stderr)            # cron job id required
        self.assertIn("prompt_ref", r.stderr)    # agent form needs prompt_ref
        self.assertIn("degraded", r.stderr)      # degraded required

    def test_manifest_cron_entry_needs_expr(self):
        # `cron` is the aos term (ALM-51): the entry's expression field is `expr`.
        cap = self.rewrite("skills:", "cron:\n  - id: nightly\n    exec: true\n"
                                      "    degraded: manual\nskills:")
        r = self.manifest(str(cap))
        self.assertEqual(r.returncode, 12)
        self.assertIn("expr", r.stderr)

    def test_manifest_malformed_shapes_exit_12(self):
        cap = self.rewrite("skills:", "depends: [not, a, mapping]\ncron: [oops]\nskills:")
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
    """The seven verbs that own `<aos_home>/.aos/installs.lock.yaml` — `init record rehash
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
        self.assertIn("job-abc123", entry["cron_owned"])
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
        self.assertIn("job-abc123", entry["cron_owned"])

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
    """Resolving the household root: `home`, `--home`, `$AOS_HOME`, the `~/aos` default —
    the exit-15 family. Mirrors `aos_cap.household`. Nothing is discovered from the cwd,
    and the cwd-sensitive tests here run from cwds chosen to prove it (see `chdir`)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.home = self.dir / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.artifact = self.home / "artifact-one.md"
        self.artifact.write_text("alpha\n")
        # A HOME of the test's own, for the `~/aos` default: `run()` otherwise hands every
        # call a fresh empty one.
        self.user = self.dir / "user"
        self.user.mkdir()

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

    def as_user(self, **extra):
        return {"HOME": str(self.user), **extra}

    # -- home --------------------------------------------------------------
    def test_home_verb_prints_resolved_root(self):
        self.seed_lockfile()
        r = run(["--home", str(self.home), "home"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(self.home))
        r = run(["home"], env_extra=self.as_user())      # no ~/aos at all
        self.assertEqual(r.returncode, 15)

    def test_explicit_home_without_state_dir_errors(self):
        # An explicit --home with no .aos/ is an error, not a fresh start: only `init`
        # may create one.
        cap = self.cap("democap", ["democap"])
        r = run(["--home", str(self.bare("bare")), "skills", str(cap), "--check"])
        self.assertEqual(r.returncode, 15)

    def test_init_requires_explicit_clone(self):
        # `init` creates state, so the household is named rather than defaulted — even
        # with a `~/aos` right there to default to.
        (self.user / "aos").mkdir()
        r = run(["init"], env_extra=self.as_user())
        self.assertEqual(r.returncode, 15)
        self.assertIn("--home", r.stderr)
        self.assertFalse((self.user / "aos" / ".aos").exists())

    # -- the default -------------------------------------------------------
    def test_the_default_is_tilde_aos_never_a_dot_aos_above_cwd(self):
        """PIN: the household was the first `.aos/` found walking up from the cwd, so any
        project folder carrying one became the household for every verb run beneath it."""
        (self.user / "aos" / ".aos").mkdir(parents=True)
        stray = self.dir / "project"
        (stray / ".aos").mkdir(parents=True)
        deep = stray / "src" / "deep"
        deep.mkdir(parents=True)
        r = run(["home"], env_extra=self.as_user(), cwd=str(deep))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(self.user / "aos"))

    def test_no_clone_found_errors(self):
        r = run(["list"], env_extra=self.as_user())
        self.assertEqual(r.returncode, 15)
        self.assertIn(f"no .aos/ directory under {self.user / 'aos'}", r.stderr)

    def test_env_override_wins_over_the_default(self):
        self.seed_lockfile()
        (self.user / "aos" / ".aos").mkdir(parents=True)  # a household the default names
        r = run(["list"], env_extra=self.as_user(AOS_HOME=str(self.home)))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap", r.stdout)

    def test_aos_home_without_dot_aos_exits_15_for_strict_and_soft_verbs(self):
        """PIN: the collision gate skipped an `$AOS_HOME` with no `.aos/` silently and went
        looking elsewhere — so it could report "clean" against a household nobody named.
        An explicit home is never a fallthrough, for the gate or for anything else."""
        cap = self.cap("democap", ["democap"])        # inside a real household, too
        (self.user / "aos" / ".aos").mkdir(parents=True)
        env = self.as_user(AOS_HOME=str(self.bare("not-a-household")))
        r = run(["list"], env_extra=env)
        self.assertEqual(r.returncode, 15, r.stdout + r.stderr)
        r = run(["skills", str(cap), "--check"], env_extra=env)
        self.assertEqual(r.returncode, 15, r.stdout + r.stderr)
        self.assertIn("not-a-household", r.stderr)

    def test_collision_found_when_cwd_is_outside_the_household(self):
        """PIN: on a real machine the agent's cwd is the harness workspace, not the
        household, and no documented invocation passes --home. Resolving from cwd alone
        made `--check` skip the household and lockfile sources and still say "clean" — a
        silent no-op in the one gate that stops an overwrite. The household is `~/aos` by
        default, so the gate checks it whatever the cwd."""
        household = self.user / "aos"
        (household / ".aos").mkdir(parents=True)
        write_cap(household, "othercap", ["othercap", "sort"], prefix="democap-",
                  root="personal")
        cap = write_cap(household, "democap", ["democap", "sort"])
        r = run(["skills", str(cap), "--check"], env_extra=self.as_user(),
                cwd=str(self.bare("elsewhere3")))
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
        (harness / "democap-sort.md").write_text("flat form\n")
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
        """A harness that installs skills as skills/<name>.md records a link whose
        basename carries .md — it still has to match our own exemption."""
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
        r = run(["skills", str(lone), "--check"])    # no --home, and no ~/aos either
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NO HOUSEHOLD RESOLVED", r.stdout)
        self.assertIn("NO --harness-skills GIVEN", r.stdout)

    def test_a_dot_aos_without_capability_roots_is_not_a_household(self):
        """PIN: a resolved root holding a `.aos/` is not proof of a household — `~/aos/.aos/`
        exists as soon as `aos-cap init` has run, before anything is cloned beside it. So
        checking a kit clone printed "checked: household ~/aos" after consulting a
        household with zero capabilities in it — a clean-looking gate that checked
        nothing. The report must say the source was skipped, which is the same discipline
        as the test above."""
        user = Path(self.tmp.name) / "user"
        (user / "aos" / ".aos").mkdir(parents=True)
        # The capability sits in a plain kit clone, not under ~/aos/{upstream,personal}/.
        cap = write_cap(Path(self.tmp.name) / "work", "lonecap", ["lonecap"], root="clone")
        r = run(["skills", str(cap), "--check"], env_extra={"HOME": str(user)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"{user / 'aos'} HOLDS A .aos/ BUT NO upstream/ OR personal/", r.stdout)
        self.assertNotIn(f"checked: household {user / 'aos'} (", r.stdout)

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


class AgentNameTest(unittest.TestCase):
    """`agents` — the agent half of §2.5 identity, and its collision gate.

    Same hazard as skills, one directory over: harnesses keep agents in a flat per-harness
    namespace (`~/.hermes/profiles/<name>/`, `~/.claude/agents/<name>.md`), so two
    capabilities shipping `archiver` silently override each other. The gate is deliberately
    two of three sources — enumerating the harness's existing agents needs a listing command
    per cheat-sheet — and the report has to SAY which source it skipped, which is what
    `test_agent_check_names_the_source_it_could_not_check` pins."""

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

    def agents(self, cap, *extra):
        return run(["--home", str(self.home), "agents", str(cap), *extra])

    def names(self, cap, *extra):
        r = self.agents(cap, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return {line.split("\t")[0]: line.split("\t")[1]
                for line in r.stdout.strip().split("\n") if "\t" in line}

    # -- the algorithm -----------------------------------------------------
    def test_agent_installed_name_takes_the_capability_prefix(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver"])
        self.assertEqual(self.names(cap), {"archiver": "kb-archiver"})

    def test_agent_prefix_defaults_to_the_capability_id(self):
        cap = self.cap("democap", ["democap"], agents=["archiver"])
        self.assertEqual(self.names(cap)["archiver"], "democap-archiver")

    def test_a_capability_with_no_agents_is_clean(self):
        """The common case — most capabilities ship none — and it must not be an error."""
        cap = self.cap("democap", ["democap"])
        r = self.agents(cap)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_agent_json_reports_the_mapping(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver", "router"])
        r = self.agents(cap, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["capability"], "kbc")
        self.assertEqual(data["skill_prefix"], "kb-")
        self.assertEqual([(a["id"], a["installed_name"]) for a in data["agents"]],
                         [("archiver", "kb-archiver"), ("router", "kb-router")])

    # -- the gate says yes -------------------------------------------------
    def test_agent_check_clean_reports_unclaimed(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver"])
        r = self.agents(cap, "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean: 1 agent name unclaimed", r.stdout)

    def test_agent_check_names_the_source_it_could_not_check(self):
        """PIN: the gate covers two of three sources on purpose — `--harness-agents` would
        need a new enumeration command in each of the five cheat-sheets for a source no
        shipped capability collides on. What is NOT optional is saying so: `names.py`'s own
        rule is that a skipped source must never be indistinguishable from an empty one."""
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver"])
        r = self.agents(cap, "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NO --harness-agents SUPPORTED YET", r.stdout)
        self.assertIn("household", r.stdout)

    # -- the gate says no (exit 17) ----------------------------------------
    def test_agent_collision_with_another_household_capability(self):
        self.cap("othercap", ["othercap"], prefix="kb-", agents=["archiver"],
                 root="personal")
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver"])
        r = self.agents(cap, "--check")
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)
        self.assertIn("kb-archiver", r.stderr)
        self.assertIn("othercap", r.stderr)

    def test_agent_collision_with_a_lockfile_link(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        self.write_lock({"othercap": {"links": {
            str(harness / "kb-archiver"): "/elsewhere/skills/kb-archiver"}}})
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver"])
        r = self.agents(cap, "--check")
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)
        self.assertIn("othercap", r.stderr)

    def test_agent_collision_inside_one_capability(self):
        """Two agent ids, one computed name: `archiver` prefixes to `kb-archiver`, and
        `kb-archiver` is never double-prefixed — so the pair collides with itself."""
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["archiver", "kb-archiver"])
        r = self.agents(cap, "--check")
        self.assertEqual(r.returncode, 17, r.stdout + r.stderr)
        self.assertIn("itself", r.stderr)

    # -- name validation, against the INSTALLED name -----------------------
    def test_over_long_agent_installed_name_rejected(self):
        long_id = "a" + "-very" * 14          # fits alone, too long once prefixed
        cap = self.cap("democap", ["democap"], agents=[long_id])
        r = self.agents(cap)
        self.assertEqual(r.returncode, 12, r.stdout + r.stderr)
        self.assertIn("max 64", r.stderr)

    def test_reserved_word_in_agent_installed_name_rejected(self):
        cap = self.cap("democap", ["democap"], agents=["claude-router"])
        r = self.agents(cap)
        self.assertEqual(r.returncode, 12, r.stdout + r.stderr)
        self.assertIn("reserved", r.stderr)


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
        skills said to render before 0.7.0 — so `--out <pkg>/skills` fired on that
        capability's FIRST upgrade. rmtree runs before copytree, so the user's hand-written skill and its
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


class HarnessTest(unittest.TestCase):
    """`harness set|show` — the record of the harness `aos-session` drives — and the render,
    which ships every cheat-sheet and needs no record."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.bin = root / "bin"
        self.bin.mkdir()
        fake = self.bin / "fakeharness"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o755)
        self.sheet = root / "harness-fake.md"
        self.sheet.write_text("---\nharness: fake\nmapping:\n  session:\n"
                              "    primitive: a session\n"
                              "    open: fakeharness chat -c <title> --file <file>\n---\n# Fake\n")
        self.out = root / "renders"

    def tearDown(self):
        self.tmp.cleanup()

    def harness(self, *args, path=None):
        env = {"PATH": str(self.bin)} if path is None else {"PATH": path}
        return run(["--home", str(self.home), "harness", *args], env_extra=env)

    def test_set_records_harness_sheet_and_absolute_cli(self):
        r = self.harness("set", "fake", "--source", str(self.sheet))
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = yaml.safe_load((self.home / ".aos" / "harness.yml").read_text())
        self.assertEqual(rec["harness"], "fake")
        self.assertTrue(rec["sheet"].endswith("reference/harness-fake.md"))
        # The CLI is recorded as an absolute path, so a caller with a reduced PATH still
        # reaches the harness — the drift shape of the 2026-10-19 incident.
        self.assertEqual(rec["cli"], str(self.bin / "fakeharness"))

    def test_set_without_the_cli_on_path_records_none_and_says_so(self):
        r = self.harness("set", "fake", "--source", str(self.sheet), path="")
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = yaml.safe_load((self.home / ".aos" / "harness.yml").read_text())
        self.assertIsNone(rec["cli"])
        self.assertIn("aos-session cannot run", r.stdout)

    def test_set_rejects_a_bad_runtime_id(self):
        r = self.harness("set", "Bad Name")
        self.assertEqual(r.returncode, 1)

    def test_show_without_a_record_exits_20(self):
        r = self.harness("show")
        self.assertEqual(r.returncode, 20)
        self.assertIn("harness set", r.stderr)

    def test_set_defaults_the_sheet_to_the_rendered_lifecycle_render(self):
        r = self.harness("set", "fake", "--source", str(self.sheet))
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = yaml.safe_load((self.home / ".aos" / "harness.yml").read_text())
        self.assertEqual(rec["sheet"], str(self.home / "rendered/capability-lifecycle/skills/"
                                           "capability-lifecycle/reference/harness-fake.md"))

    def test_render_keeps_every_sheet_and_needs_no_record(self):
        # One household can serve several harnesses (Hermes and Claude Code read the same
        # renders), so the render ships every sheet; only aos-session reads the record.
        cap = write_cap(self.home, "democap", ["democap"])
        ref = cap / "skills" / "democap" / "reference"
        ref.mkdir()
        for name in ("harness-a.md", "harness-b.md", "no-cheatsheet.md", "contract.md"):
            (ref / name).write_text(f"# {name}\n")
        r = run(["--home", str(self.home), "render", str(cap), "democap", "--out", str(self.out)])
        self.assertEqual(r.returncode, 0, r.stderr)
        kept = sorted(p.name for p in (self.out / "democap" / "reference").iterdir())
        self.assertEqual(kept, ["contract.md", "harness-a.md", "harness-b.md", "no-cheatsheet.md"])


class SlotTest(unittest.TestCase):
    """`{{skill:}}` / `{{agent:}}` slot resolution at render — mirrors `aos_cap.slots`.

    The defect this class exists for: an installed name is COMPUTED (`<skill_prefix><id>`),
    so prose that hardcodes one silently points at nothing the moment the prefix changes.
    Two probes proved nothing caught it — renaming a `skill_prefix` and corrupting a
    hardcoded name both left CI green. A slot fails loudly instead: exit 18."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.out = Path(self.tmp.name) / "renders"

    def tearDown(self):
        self.tmp.cleanup()

    def cap(self, cap_id, skills, **kw):
        return write_cap(self.home, cap_id, skills, **kw)

    def body(self, cap, skill, text):
        """Replace the skill body, keeping the frontmatter the render stamps."""
        path = cap / "skills" / skill / "SKILL.md"
        path.write_text(SKILL_MD.format(name=skill).replace("body\n", text))
        return path

    def render(self, cap, skill, *extra, out=None):
        return run(["render", str(cap), skill, "--out", str(out or self.out), *extra])

    def rendered(self, name, rel="SKILL.md"):
        return (self.out / name / rel).read_text()

    # -- resolution --------------------------------------------------------
    def test_slot_resolves_an_own_capability_skill(self):
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        self.body(cap, "kbc", "Hand off to {{skill: route}} when routing.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.rendered("kbc")
        self.assertIn("kb-route", text)
        self.assertNotIn("{{skill:", text)

    def test_agent_slot_takes_the_same_prefix_as_skills(self):
        # No second manifest field: §2.2's rule of two, and one prefix per capability is
        # what both flat namespaces want anyway.
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["keeper"])
        self.body(cap, "kbc", "Delegate to {{agent: keeper}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("kb-keeper", self.rendered("kbc"))

    def test_cross_capability_slot_resolves_within_upstream(self):
        self.cap("kbc", ["kbc", "capture"], prefix="kb-", root="upstream")
        cap = self.cap("wt", ["wt"], root="upstream")
        self.body(cap, "wt", "Capture with {{skill: kbc/capture}}.\n")
        r = self.render(cap, "wt")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("kb-capture", self.rendered("wt"))

    def test_cross_capability_slot_resolves_from_personal_into_upstream(self):
        """PIN: the two-root case. The lookup used to be `cap_dir.parent` — the SIBLING
        directory only — so a capability in `personal/` naming one in `upstream/` failed on
        a CORRECT reference. That is every capability `capability-build` writes: they live
        in personal/ and depend on kb in upstream/."""
        self.cap("kbc", ["kbc", "capture"], prefix="kb-", root="upstream")
        cap = self.cap("mine", ["mine"], root="personal")
        self.body(cap, "mine", "Capture with {{skill: kbc/capture}}.\n")
        r = self.render(cap, "mine")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("kb-capture", self.rendered("mine"))

    def test_entry_skill_slot_is_never_double_prefixed(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-")
        self.body(cap, "kbc", "See {{skill: kbc}} for the map.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.rendered("kbc")
        self.assertIn("See kbc for the map.", text)
        self.assertNotIn("kb-kbc", text)

    def test_slots_in_reference_files_are_resolved_too(self):
        # Depth lives in a sibling `reference/`, so most prose that names a skill is there
        # rather than in SKILL.md — substituting only the entry file would miss the bulk.
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        ref = cap / "skills" / "kbc" / "reference"
        ref.mkdir()
        (ref / "deep.md").write_text("Routing is {{skill: route}}'s job.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("kb-route", self.rendered("kbc", "reference/deep.md"))

    def test_mod_slots_still_survive_the_slot_pass(self):
        """The two halves of replacement are deliberately different: a `{{mod:}}` slot is
        left intact by contract (the agentic transform fills it), while a name slot that
        resolves to nothing is a hard failure."""
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        self.body(cap, "kbc", "Confirm with {{mod: confirm_style}} then {{skill: route}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.rendered("kbc")
        self.assertIn("{{mod: confirm_style}}", text)
        self.assertIn("kb-route", text)

    # -- the escape guard --------------------------------------------------
    def test_escaped_skill_slot_renders_as_a_literal(self):
        """PIN: capability-lifecycle documents the very syntax it is rendered by, so
        without an escape, installing it corrupts its own naming reference. The escaped
        form is neither substituted nor validated; an unescaped one in the same file
        still resolves, so the guard is a per-slot decision, not a per-file mode."""
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        self.body(cap, "kbc", "Write \\{{skill: route}}; it becomes {{skill: route}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.rendered("kbc").splitlines()[-1],
                         "Write {{skill: route}}; it becomes kb-route.")

    def test_escaped_agent_slot_renders_as_a_literal(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["keeper"])
        self.body(cap, "kbc", "Write \\{{agent: keeper}} to show the syntax.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("{{agent: keeper}}", self.rendered("kbc"))
        self.assertNotIn("kb-keeper", self.rendered("kbc"))

    def test_escaped_mod_slot_renders_as_a_literal(self):
        # One escape rule for every slot type, so an author holds one sentence: a
        # backslash before any {{...}} slot makes it a literal example.
        cap = self.cap("kbc", ["kbc"], prefix="kb-")
        self.body(cap, "kbc", "Write \\{{mod: confirm_style}} in prose.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Write {{mod: confirm_style}} in prose.", self.rendered("kbc"))

    def test_an_escaped_slot_naming_nothing_is_not_an_error(self):
        """The point of an example is that it names a placeholder. Validating escaped
        slots would make every documented sample a dangling reference."""
        cap = self.cap("kbc", ["kbc"], prefix="kb-")
        self.body(cap, "kbc", "e.g. \\{{skill: <id>}} or \\{{agent: ghostagent}} "
                              "or \\{{skill: ghostcap/ghost}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("{{skill: ghostcap/ghost}}", self.rendered("kbc"))

    # -- exit 18 -----------------------------------------------------------
    def test_unknown_skill_id_in_a_slot_exits_18(self):
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        self.body(cap, "kbc", "Hand off to {{skill: ghost}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 18, r.stdout + r.stderr)
        self.assertIn("ghost", r.stderr)
        self.assertIn("route", r.stderr)      # and says what IS declared

    def test_unknown_agent_id_in_a_slot_exits_18(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-", agents=["keeper"])
        self.body(cap, "kbc", "Delegate to {{agent: ghostagent}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 18, r.stdout + r.stderr)
        self.assertIn("ghostagent", r.stderr)

    def test_unknown_capability_in_a_slot_exits_18(self):
        cap = self.cap("kbc", ["kbc"], prefix="kb-")
        self.body(cap, "kbc", "Capture with {{skill: ghostcap/capture}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 18, r.stdout + r.stderr)
        self.assertIn("ghostcap", r.stderr)

    def test_a_shadowed_capability_in_a_slot_exits_18_naming_both_roots(self):
        """The install contract: a personal package shadowing an upstream id is reported
        loudly, never silently preferred. A slot that quietly took personal/ would resolve
        against a package the installer never mentioned."""
        self.cap("kbc", ["kbc", "capture"], prefix="kb-", root="upstream")
        self.cap("kbc", ["kbc", "capture"], prefix="mine-", root="personal")
        cap = self.cap("wt", ["wt"], root="upstream")
        self.body(cap, "wt", "Capture with {{skill: kbc/capture}}.\n")
        r = self.render(cap, "wt")
        self.assertEqual(r.returncode, 18, r.stdout + r.stderr)
        self.assertIn("personal/", r.stderr)
        self.assertIn("upstream/", r.stderr)

    def test_a_mod_only_personal_directory_is_not_a_shadow(self):
        """The contract's own caveat: `personal/capabilities/<id>/` exists for every
        capability the user has answers for — it is the mirrored overlay path. Only a
        directory holding a CAPABILITY.md is a package, or a shadow would be reported on
        every ordinary install."""
        self.cap("kbc", ["kbc", "capture"], prefix="kb-", root="upstream")
        overlay = self.home / "personal" / "capabilities" / "kbc"
        overlay.mkdir(parents=True)
        (overlay / "MOD.md").write_text("---\nonboarded_version: 1.0.0\n---\nanswers\n")
        cap = self.cap("wt", ["wt"], root="upstream")
        self.body(cap, "wt", "Capture with {{skill: kbc/capture}}.\n")
        r = self.render(cap, "wt")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("kb-capture", self.rendered("wt"))

    def test_a_bare_clone_resolves_siblings_not_a_household_above_it(self):
        """`.aos/` is machine-local and sits at `~/` on any machine that has ever installed
        aos, so recognising a household by a marker above the package would make a bare kit
        clone (this repo's own flat `capabilities/`) resolve references into the user's real
        `personal/`. The clone resolves against its siblings instead."""
        self.cap("kbc", ["kbc", "capture"], prefix="decoy-", root="personal")
        # `root="clone"` is neither household root, so the package is in no household —
        # exactly the shape of `<repo>/capabilities/<id>` in a bare kit checkout.
        self.cap("kbc", ["kbc", "capture"], prefix="kb-", root="clone")
        wt = self.cap("wt", ["wt"], root="clone")
        self.body(wt, "wt", "Capture with {{skill: kbc/capture}}.\n")
        r = self.render(wt, "wt")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.rendered("wt")
        self.assertIn("kb-capture", text)          # the sibling's prefix
        self.assertNotIn("decoy-", text)           # never the household's

    def test_a_failed_slot_pass_leaves_no_partial_render(self):
        """The copy already landed when the slot pass runs. A half-substituted skill reads
        as complete to the next step (the diff gate, the symlink), so the failure has to be
        total — the directory goes away."""
        cap = self.cap("kbc", ["kbc", "route"], prefix="kb-")
        self.body(cap, "kbc", "Good: {{skill: route}}. Bad: {{skill: ghost}}.\n")
        r = self.render(cap, "kbc")
        self.assertEqual(r.returncode, 18, r.stdout + r.stderr)
        self.assertFalse((self.out / "kbc").exists(), "a partial render survived")


class UsesTest(unittest.TestCase):
    """`uses` (RFC-009 option 2) — a consumer's agent loading a skill another capability
    ships. Mirrors `aos_cap.manifest` (validation, `uses_rows`) and the `uses_links` half of
    `commands/lockfile.py`. The incident behind it: a provider's upgrade re-derived its links
    from its own `used_by` and moved the consumer's link away, silently, for two weeks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        run(["--home", str(self.home), "init"])
        self.prov = write_cap(self.home, "provcap", ["provcap", "share"], prefix="prov-")

    def tearDown(self):
        self.tmp.cleanup()

    def consumer(self, uses, depends=("provcap",), agents=("scribe",)):
        cap = write_cap(self.home, "conscap", ["conscap"], root="personal",
                        agents=agents, depends=depends)
        mf = cap / "CAPABILITY.md"
        mf.write_text(mf.read_text().replace("skills:\n", f"uses:\n{uses}skills:\n", 1))
        return cap

    def manifest(self, cap):
        return run(["--home", str(self.home), "manifest", str(cap)])

    def cap_cmd(self, *args):
        return run(["--home", str(self.home), *args])

    def link(self, name, target):
        link = self.home / "harness" / name / target.name
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        return link

    GRANT = "  - {capability: provcap, skill: share, agents: [scribe]}\n"

    # -- manifest ----------------------------------------------------------
    def test_valid_grant_carries_the_providers_installed_name(self):
        # Consumer in personal/, provider in upstream/ — the normal household shape.
        r = self.manifest(self.consumer(self.GRANT))
        self.assertEqual(r.returncode, 0, r.stderr)
        row = json.loads(r.stdout)["uses"][0]
        self.assertEqual(row["installed_name"], "prov-share")   # the PROVIDER's prefix
        self.assertEqual(row["agents"], ["scribe"])

    def test_provider_must_be_a_dependency(self):
        r = self.manifest(self.consumer(self.GRANT, depends=()))
        self.assertEqual(r.returncode, 12)
        self.assertIn("must be in depends.capabilities", r.stderr)

    def test_a_capability_cannot_use_itself(self):
        r = self.manifest(self.consumer(
            "  - {capability: conscap, skill: conscap, agents: [scribe]}\n"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("scopes its own skills with used_by", r.stderr)

    def test_skill_must_be_declared_by_the_provider(self):
        r = self.manifest(self.consumer(
            "  - {capability: provcap, skill: nosuch, agents: [scribe]}\n"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("declares no skill 'nosuch'", r.stderr)

    def test_agents_must_be_main_or_declared_and_non_empty(self):
        r = self.manifest(self.consumer(
            "  - {capability: provcap, skill: share, agents: [ghost]}\n"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("agent 'ghost' is not main or a declared agent", r.stderr)
        shutil.rmtree(self.home / "personal")
        r = self.manifest(self.consumer(
            "  - {capability: provcap, skill: share, agents: []}\n"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("agents must be a non-empty list", r.stderr)

    def test_duplicate_and_unknown_keys_rejected(self):
        r = self.manifest(self.consumer(
            self.GRANT + "  - {capability: provcap, skill: share, agents: [main], why: x}\n"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("duplicate entry", r.stderr)
        self.assertIn("unknown key 'why'", r.stderr)

    def test_malformed_shape_is_exit_12_not_a_traceback(self):
        cap = write_cap(self.home, "conscap", ["conscap"], root="personal")
        mf = cap / "CAPABILITY.md"
        mf.write_text(mf.read_text().replace("skills:\n", "uses: not-a-list\nskills:\n", 1))
        r = self.manifest(cap)
        self.assertEqual(r.returncode, 12)
        self.assertIn("uses must be a list", r.stderr)

    # -- lockfile ----------------------------------------------------------
    def test_uses_link_roundtrip_and_damage_is_drift(self):
        target = self.prov / "skills" / "share"
        link = self.link("scribe", target)
        r = self.cap_cmd("record", "conscap", "--version", "1.0.0", "--uses-link", str(link))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 uses links", r.stdout)
        entry = json.loads(self.cap_cmd("show", "conscap").stdout)
        self.assertEqual(entry["uses_links"], {str(link): str(target)})
        self.assertEqual(entry["links"], {})
        self.assertEqual(self.cap_cmd("verify", "conscap").returncode, 0)
        link.unlink()
        v = self.cap_cmd("verify", "conscap")
        self.assertEqual(v.returncode, 13)
        self.assertIn("MISSING LINK", v.stdout)

    def test_a_link_has_exactly_one_owner(self):
        """PIN: the 9/22 shape. The consumer's link sat on the provider's entry, so the
        provider's re-record decided where it lived. With one owner per link, recording a
        path another entry holds is refused (19) and the lockfile is left untouched."""
        link = self.link("scribe", self.prov / "skills" / "share")
        r = self.cap_cmd("record", "conscap", "--version", "1.0.0", "--uses-link", str(link))
        self.assertEqual(r.returncode, 0, r.stderr)
        lock = self.home / ".aos" / "installs.lock.yaml"
        before = lock.read_text()
        r = self.cap_cmd("record", "provcap", "--version", "1.0.0", "--link", str(link))
        self.assertEqual(r.returncode, 19)
        self.assertIn("LINK_OWNED", r.stderr)
        self.assertIn("'conscap'", r.stderr)
        self.assertEqual(lock.read_text(), before)
        # and the other direction: a provider's own link is never claimable as a used one
        own = self.link("main", self.prov / "skills" / "provcap")
        self.assertEqual(self.cap_cmd("record", "provcap", "--version", "1.0.0",
                                      "--link", str(own)).returncode, 0)
        r = self.cap_cmd("record", "conscap", "--version", "1.0.0", "--uses-link", str(own))
        self.assertEqual(r.returncode, 19)

    def test_rerecording_your_own_links_is_not_a_conflict(self):
        link = self.link("scribe", self.prov / "skills" / "share")
        for _ in range(2):
            r = self.cap_cmd("record", "conscap", "--version", "1.0.0", "--uses-link", str(link))
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_one_path_cannot_be_both_kinds(self):
        link = self.link("scribe", self.prov / "skills" / "share")
        r = self.cap_cmd("record", "conscap", "--version", "1.0.0",
                         "--link", str(link), "--uses-link", str(link))
        self.assertEqual(r.returncode, 1)
        self.assertIn("both --link and --uses-link", r.stderr)

    def test_a_consumers_uses_link_is_not_a_name_claim(self):
        """PIN: `links` basenames are name claims. Had the consumer recorded the provider's
        skill there, the provider's own upgrade gate would report its own skill as taken."""
        link = self.link("scribe", self.prov / "skills" / "share")
        link = link.rename(link.parent / "prov-share")
        self.assertEqual(self.cap_cmd("record", "conscap", "--version", "1.0.0",
                                      "--uses-link", str(link)).returncode, 0)
        r = self.cap_cmd("skills", str(self.prov), "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


def tree_bytes(root):
    """Every file and symlink under `root` as {relative path: bytes or link target} — the
    "wrote nothing" assertion compares two of these."""
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = os.fspath(p.relative_to(root))
        if p.is_symlink():
            out[rel] = "-> " + os.readlink(p)
        elif p.is_file():
            out[rel] = p.read_bytes()
    return out


def trashed_names():
    files = TRASH_HOME / "Trash" / "files"
    return sorted(p.name for p in files.iterdir()) if files.is_dir() else []


def empty_trash():
    shutil.rmtree(TRASH_HOME / "Trash", ignore_errors=True)


class RenderedTest(unittest.TestCase):
    """`swap` / `discard` and the guards that keep a render's writes in
    `rendered/.staging/<id>/` — `render --out`, `record`, `rehash` (capability-lifecycle 0.7.0)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "home"
        (self.home / ".aos").mkdir(parents=True)
        run(["--home", str(self.home), "init"])
        empty_trash()
        self.rendered = self.home / "rendered"
        self.links = root / "harness" / "skills"
        self.links.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        return run(["--home", str(self.home), *args])

    def stage(self, cap, body="new\n", rel="skills/democap/SKILL.md"):
        f = self.rendered / ".staging" / cap / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
        return f

    def live(self, cap, body="old\n", rel="skills/democap/SKILL.md"):
        f = self.rendered / cap / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
        return f

    # -- swap -----------------------------------------------------------------
    def test_swap_replaces_the_live_render_and_trashes_the_old_one(self):
        live = self.live("democap")
        (self.links / "democap").symlink_to(live.parent)
        self.stage("democap")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(live.read_text(), "new\n")
        self.assertEqual((self.links / "democap" / "SKILL.md").read_text(), "new\n")
        self.assertFalse((self.rendered / ".staging" / "democap").exists())
        self.assertFalse((self.rendered / ".replaced" / "democap").exists())
        self.assertEqual(trashed_names(), ["democap"])

    def test_swap_on_a_first_install_only_moves_the_staged_render_in(self):
        self.stage("democap")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("first install", r.stdout)
        self.assertEqual((self.rendered / "democap/skills/democap/SKILL.md").read_text(), "new\n")
        self.assertEqual(trashed_names(), [])

    def test_swap_puts_an_interrupted_swaps_old_render_back_live(self):
        # PIN: a crash between swap's two renames leaves the only copy of the old render in
        # .replaced/<id> and no live render; the next swap must not trash it.
        aside = self.rendered / ".replaced" / "democap" / "skills/democap/SKILL.md"
        aside.parent.mkdir(parents=True)
        aside.write_text("old\n")
        self.stage("democap")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 26)
        self.assertEqual((self.rendered / "democap/skills/democap/SKILL.md").read_text(), "old\n")
        self.assertTrue((self.rendered / ".staging" / "democap").is_dir())
        self.assertEqual(self.cli("swap", "democap").returncode, 0)

    def test_swap_trashes_a_finished_swaps_leftover_and_proceeds(self):
        self.live("democap")
        aside = self.rendered / ".replaced" / "democap" / "x"
        aside.parent.mkdir(parents=True)
        aside.write_text("stale\n")
        self.stage("democap")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.rendered / "democap/skills/democap/SKILL.md").read_text(), "new\n")

    def test_swap_refuses_a_staged_file_naming_its_own_staging_path(self):
        self.live("democap")
        staged = self.rendered / ".staging" / "democap"
        self.stage("democap", body=f"run {staged}/skills/democap/run.sh\n")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 23)
        self.assertEqual((self.rendered / "democap/skills/democap/SKILL.md").read_text(), "old\n")

    def test_swap_refuses_a_staged_tree_that_drops_a_linked_target(self):
        # PIN: a staged render without adapters/ would leave a gate plugin's link dangling.
        plugin = self.live("democap", rel="adapters/plugins/gate/__init__.py")
        link = self.links.parent / "plugins" / "gate"
        link.parent.mkdir()
        link.symlink_to(plugin.parent)
        self.assertEqual(self.cli("record", "democap", "--version", "1.0.0",
                                  "--link", str(link)).returncode, 0)
        self.stage("democap")
        r = self.cli("swap", "democap")
        self.assertEqual(r.returncode, 23)
        self.assertIn("dangling", r.stderr)
        self.assertTrue(link.exists())

    # -- discard ----------------------------------------------------------------
    def test_discard_trashes_the_staged_render_and_leaves_the_live_one(self):
        live = self.live("democap")
        before = tree_bytes(self.rendered / "democap")
        self.stage("democap")
        r = self.cli("discard", "democap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.rendered / ".staging" / "democap").exists())
        self.assertEqual(tree_bytes(self.rendered / "democap"), before)
        self.assertEqual(live.read_text(), "old\n")
        self.assertEqual(trashed_names(), ["democap"])

    def test_swap_and_discard_refuse_anything_but_a_capability_id(self):
        # PIN: `discard ..` resolves .staging/.. to rendered/ itself, inside the tree.
        self.live("democap")
        self.stage("democap")
        before = tree_bytes(self.rendered)
        for verb in ("swap", "discard"):
            for bad in ("..", ".staging", "", "a/b", "Democap"):
                r = self.cli(verb, bad)
                self.assertEqual(r.returncode, 21, f"{verb} {bad!r}: {r.stderr}")
        self.assertEqual(tree_bytes(self.rendered), before)

    def test_swap_and_discard_refuse_a_symlinked_staging_dir(self):
        live = self.live("democap")
        (self.rendered / ".staging").mkdir()
        (self.rendered / ".staging" / "democap").symlink_to(self.rendered / "democap")
        for verb in ("swap", "discard"):
            self.assertEqual(self.cli(verb, "democap").returncode, 21)
        self.assertEqual(live.read_text(), "old\n")

    def test_swap_without_a_staged_render_exits_22(self):
        self.assertEqual(self.cli("swap", "democap").returncode, 22)
        self.assertEqual(self.cli("discard", "democap").returncode, 22)

    # -- render writes only to staging -------------------------------------------
    def test_render_into_staging_is_accepted(self):
        cap = write_cap(self.home, "democap", ["democap"])
        r = self.cli("render", str(cap), "democap", "--out",
                     str(self.rendered / ".staging" / "democap" / "skills"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.rendered / ".staging/democap/skills/democap/SKILL.md").is_file())

    def test_render_into_the_live_render_is_refused_and_writes_nothing(self):
        # PIN: `render --force` is rmtree-then-copy; into rendered/<id> it would replace a
        # live render with no gate and no trash.
        cap = write_cap(self.home, "democap", ["democap"])
        self.live("democap")
        before = tree_bytes(self.rendered)
        for out in (self.rendered / "democap" / "skills",
                    self.rendered / ".staging" / ".." / "democap" / "skills"):
            r = self.cli("render", str(cap), "democap", "--out", str(out), "--force")
            self.assertEqual(r.returncode, 24, f"{out}: {r.stderr}")
        self.assertEqual(tree_bytes(self.rendered), before)

    def test_render_through_a_symlinked_staging_dir_is_refused(self):
        cap = write_cap(self.home, "democap", ["democap"])
        self.live("democap")
        (self.rendered / ".staging").mkdir()
        (self.rendered / ".staging" / "democap").symlink_to(self.rendered / "democap")
        r = self.cli("render", str(cap), "democap", "--force", "--out",
                     str(self.rendered / ".staging" / "democap" / "skills"))
        self.assertEqual(r.returncode, 24)
        self.assertEqual((self.rendered / "democap/skills/democap/SKILL.md").read_text(), "old\n")

    def test_render_under_personal_is_refused_and_names_the_migration(self):
        cap = write_cap(self.home, "democap", ["democap"])
        out = self.home / "personal" / "capabilities" / "democap" / "skills"
        r = self.cli("render", str(cap), "democap", "--out", str(out))
        self.assertEqual(r.returncode, 24)
        self.assertIn("migrate rendered", r.stderr)
        self.assertFalse(out.exists())

    def test_record_and_rehash_refuse_a_staged_path(self):
        staged = self.stage("democap")
        r = self.cli("record", "democap", "--version", "1.0.0", "--artifact", str(staged))
        self.assertEqual(r.returncode, 24)
        link = self.links / "democap"
        link.symlink_to(staged.parent)
        r = self.cli("record", "democap", "--version", "1.0.0", "--link", str(link))
        self.assertEqual(r.returncode, 24)
        self.assertNotIn("democap", yaml.safe_load(
            (self.home / ".aos" / "installs.lock.yaml").read_text())["installs"])
        lock = self.home / ".aos" / "installs.lock.yaml"
        lock.write_text(yaml.safe_dump({"version": 1, "installs": {"democap": {
            "version": "1.0.0", "artifacts": {str(staged): "0" * 64}}}}))
        self.assertEqual(self.cli("rehash", "democap").returncode, 24)


def old_layout_household(root):
    """A pre-0.7.0 household with every shape the migration must handle, all synthetic:

      shipcap   a shipped package (no CAPABILITY.md in personal/): its render at
                personal/capabilities/shipcap/skills/ beside its MOD.md; one render file
                bakes its own absolute path; harness.yml's sheet lives in it
      owncap    the user's own package: source at personal/capabilities/owncap/, render
                at personal/renders/owncap/ — a skill, a plugin with a planted .pyc, an
                ext file linked as a FILE; it `uses` shipcap's skill
      plugcap   a plugin-only own package recording NO artifacts, found only from its
                deep link target
    plus an unrecorded link, outside references in a harness config.yaml and in owncap's
    MOD.md, and one in a session log that must be skipped. `root` is the fake $HOME."""
    home = root / "aos"
    run(["--home", str(home), "init"])
    p = home / "personal"
    caps = p / "capabilities"
    ship = caps / "shipcap" / "skills" / "shipcap"
    ship.mkdir(parents=True)
    (caps / "shipcap" / "MOD.md").write_text("---\ncapability: shipcap\n---\nprefer short\n")
    (ship / "SKILL.md").write_text("---\nname: shipcap\ndescription: x. Use when x.\n---\nbody\n")
    (ship / "run.sh").write_text(f"#!/bin/sh\nexec {ship}/run.sh --again\n")
    (ship / "reference").mkdir()
    (ship / "reference" / "harness-fake.md").write_text("# fake\n")
    (caps / "owncap" / "skills" / "owncap").mkdir(parents=True)
    (caps / "owncap" / "CAPABILITY.md").write_text("---\nid: owncap\n---\n")
    (caps / "owncap" / "skills" / "owncap" / "SKILL.md").write_text("source\n")
    own = p / "renders" / "owncap"
    (own / "skills" / "owncap").mkdir(parents=True)
    (own / "skills" / "owncap" / "SKILL.md").write_text("render\n")
    gate = own / "adapters" / "plugins" / "gate"
    (gate / "__pycache__").mkdir(parents=True)
    (gate / "__init__.py").write_text(f"ROOT = '{own}'\n")
    (gate / "__pycache__" / "__init__.cpython-312.pyc").write_bytes(
        b"\x00\x01" + os.fsencode(own) + b"\x00bytecode")
    (own / "adapters" / "ext").mkdir()
    (own / "adapters" / "ext" / "wrap.mjs").write_text("export default 1\n")
    (caps / "owncap" / "MOD.md").write_text(f"---\ncapability: owncap\nanswers:\n  dir: {own}/skills/owncap\n---\n")
    (caps / "plugcap").mkdir()
    (caps / "plugcap" / "CAPABILITY.md").write_text("---\nid: plugcap\n---\n")
    plug = p / "renders" / "plugcap" / "adapters" / "hermes" / "plugins" / "plugcap"
    plug.mkdir(parents=True)
    (plug / "hook.py").write_text("ALLOW = []\n")
    (p / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    hz = root / ".fakeh"
    for d in ("skills", "plugins", "ext", "profiles/o/skills", "sessions"):
        (hz / d).mkdir(parents=True)
    links = {
        "ship": (hz / "skills" / "shipcap", ship),
        "own": (hz / "skills" / "owncap", own / "skills" / "owncap"),
        "gate": (hz / "plugins" / "gate", gate),
        "file": (hz / "ext" / "wrap.mjs", own / "adapters" / "ext" / "wrap.mjs"),
        "plug": (hz / "plugins" / "plugcap", plug),
        "uses": (hz / "profiles" / "o" / "skills" / "shipcap", ship),
        "unrecorded": (hz / "skills" / "extra", own / "skills" / "owncap"),
    }
    for link, target in links.values():
        link.symlink_to(target)
    (hz / "config.yaml").write_text(f"hooks:\n  pre_tool_call:\n    - command: {gate}/__init__.py\n")
    (hz / "sessions" / "s1.jsonl").write_text(f'{{"cmd": "{own}/skills/owncap"}}\n')
    H = ["--home", str(home)]
    env = {"HOME": str(root)}
    def rec(*args):
        r = run([*H, "record", *args], env_extra=env)
        assert r.returncode == 0, r.stderr
    rec("shipcap", "--version", "1.0.0",
        *[x for f in sorted(ship.rglob("*")) if f.is_file() for x in ("--artifact", str(f))],
        "--link", str(links["ship"][0]))
    rec("owncap", "--version", "0.1.0", "--source-root", "personal",
        "--artifact", str(own / "skills" / "owncap" / "SKILL.md"),
        "--artifact", str(gate / "__init__.py"),
        "--link", str(links["own"][0]), "--link", str(links["gate"][0]),
        "--link", str(links["file"][0]), "--uses-link", str(links["uses"][0]))
    rec("plugcap", "--version", "0.1.0", "--source-root", "personal", "--link", str(links["plug"][0]))
    (home / ".aos" / "harness.yml").write_text(yaml.safe_dump(
        {"harness": "fake", "sheet": str(ship / "reference" / "harness-fake.md"), "cli": None}))
    git = ["git", "-C", str(p), "-c", "user.name=Dana Fixture", "-c", "user.email=dana@example.com"]
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "seed"], check=True)
    return home, hz, links


class MigrateTest(unittest.TestCase):
    """`migrate rendered` — a pre-0.7.0 household's renders move from personal/ to
    rendered/ in three steps (plan, --apply, --finish), old paths live until the last."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home, self.hz, self.links = old_layout_household(self.root)
        empty_trash()
        self.lock = self.home / ".aos" / "installs.lock.yaml"

    def tearDown(self):
        self.tmp.cleanup()

    def mig(self, *args):
        return run(["--home", str(self.home), "migrate", "rendered", *args],
                   env_extra={"HOME": str(self.root)})

    def cli(self, *args):
        return run(["--home", str(self.home), *args], env_extra={"HOME": str(self.root)})

    def fix_outside_references(self):
        gate = self.home / "rendered" / "owncap" / "adapters" / "plugins" / "gate"
        (self.hz / "config.yaml").write_text(f"hooks:\n  pre_tool_call:\n    - command: {gate}/__init__.py\n")
        mod = self.home / "personal" / "capabilities" / "owncap" / "MOD.md"
        mod.write_text(mod.read_text().replace("personal/renders/owncap", "rendered/owncap"))

    def test_plan_writes_nothing_but_the_scan_set_and_lists_every_reference(self):
        before = (tree_bytes(self.home / "personal"), tree_bytes(self.hz),
                  self.lock.read_bytes(), (self.home / ".aos" / "harness.yml").read_bytes())
        r = self.mig()
        self.assertEqual(r.returncode, 0, r.stderr)
        after = (tree_bytes(self.home / "personal"), tree_bytes(self.hz),
                 self.lock.read_bytes(), (self.home / ".aos" / "harness.yml").read_bytes())
        self.assertEqual(after, before)
        self.assertFalse((self.home / "rendered").exists())
        self.assertTrue((self.home / ".aos" / "migrate-rendered.yaml").is_file())
        self.assertIn(f"{self.hz / 'config.yaml'}:3", r.stdout)
        self.assertIn(f"{self.home / 'personal/capabilities/owncap/MOD.md'}:4", r.stdout)
        # path:line only — the scan reads harness homes, which hold keys.
        self.assertNotIn("- command:", r.stdout.split("## outside references")[1])
        self.assertNotIn("s1.jsonl", r.stdout)
        self.assertIn(str(self.links["unrecorded"][0]), r.stdout)
        self.assertIn("(0)", r.stdout.split("## renders with drift")[1].splitlines()[0])

    def test_a_drifted_render_is_listed_and_blocks_apply(self):
        ship = self.links["ship"][1]
        (ship / "SKILL.md").write_text("hand-edited\n")
        r = self.mig()
        self.assertIn("shipcap: DRIFT", r.stdout)
        r = self.mig("--apply")
        self.assertEqual(r.returncode, 25)
        self.assertFalse((self.home / "rendered" / "shipcap").exists())

    def test_apply_copies_repoints_and_rewrites_while_old_renders_stay(self):
        self.assertEqual(self.mig().returncode, 0)
        r = self.mig("--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        new = self.home / "rendered"
        for name, (link, _) in self.links.items():
            target = Path(os.readlink(link))
            self.assertTrue(new in target.parents, f"{name}: {target}")
            self.assertTrue(link.exists(), name)
        run_sh = (new / "shipcap/skills/shipcap/run.sh").read_text()
        self.assertIn(str(new / "shipcap/skills/shipcap/run.sh"), run_sh)
        self.assertNotIn("personal", run_sh)
        self.assertFalse(list(new.rglob("*.pyc")))
        self.assertEqual(self.cli("verify").returncode, 0, self.cli("verify").stdout)
        entry = yaml.safe_load(self.lock.read_text())["installs"]
        self.assertTrue(any("plugcap" in a for a in entry["plugcap"]["artifacts"]),
                        "a no-artifact entry gets its moved files recorded")
        self.assertNotIn("personal/", yaml.safe_dump(entry))
        self.assertIn("rendered/shipcap", (self.home / ".aos/harness.yml").read_text())
        self.assertTrue((self.home / "personal/capabilities/shipcap/MOD.md").is_file())
        self.assertEqual((self.home / "personal/capabilities/owncap/skills/owncap/SKILL.md").read_text(),
                         "source\n")
        self.assertTrue((self.home / "personal/renders/owncap").is_dir())
        self.assertTrue((self.home / "personal/capabilities/shipcap/skills").is_dir())

    def test_apply_rerun_after_a_crash_reaches_the_same_state(self):
        self.mig()
        pre_lock = self.lock.read_bytes()
        self.assertEqual(self.mig("--apply").returncode, 0)
        good = {n: os.readlink(l) for n, (l, _) in self.links.items()}
        # crash before the lockfile write: copies in place, one link back on the old render,
        # the old lockfile, no "applied" in the state
        self.lock.write_bytes(pre_lock)
        st = self.home / ".aos" / "migrate-rendered.yaml"
        state = yaml.safe_load(st.read_text())
        state.pop("applied"); state.pop("roots")
        st.write_text(yaml.safe_dump(state))
        own_link = self.links["own"][0]
        own_link.unlink()
        own_link.symlink_to(self.links["own"][1])
        self.assertEqual(self.mig("--apply").returncode, 0)
        self.assertEqual({n: os.readlink(l) for n, (l, _) in self.links.items()}, good)
        self.assertEqual(self.cli("verify").returncode, 0)
        self.assertNotIn("personal/", self.lock.read_text())

    def test_finish_refuses_while_a_reference_or_an_old_link_remains(self):
        self.mig()
        self.mig("--apply")
        r = self.mig("--finish")
        self.assertEqual(r.returncode, 25)
        self.assertIn("config.yaml:3", r.stdout)
        self.assertTrue((self.home / "personal/renders/owncap").is_dir())
        self.fix_outside_references()
        stray = self.hz / "skills" / "stray"
        stray.symlink_to(self.links["own"][1])
        r = self.mig("--finish")
        self.assertEqual(r.returncode, 25)
        self.assertIn(f"LINK {stray}", r.stdout)
        stray.unlink()
        r = self.mig("--finish")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.home / "personal/renders").exists())
        self.assertFalse((self.home / "personal/capabilities/shipcap/skills").exists())
        self.assertTrue((self.home / "personal/capabilities/shipcap/MOD.md").is_file())
        self.assertIn("owncap", trashed_names())
        for args in ((), ("--apply",), ("--finish",)):
            r = self.mig(*args)
            self.assertEqual(r.returncode, 0, args)
            self.assertIn("nothing to migrate", r.stdout)

    def test_apply_and_finish_refuse_to_scan_less_than_the_plan(self):
        self.assertEqual(self.mig("--apply").returncode, 25)  # no plan yet
        self.mig()
        self.assertEqual(self.mig("--apply", "--ignore", "config.yaml").returncode, 25)

    def test_a_new_layout_household_has_nothing_to_migrate(self):
        fresh = self.root / "fresh"
        run(["--home", str(fresh), "init"])
        (fresh / "rendered" / "democap").mkdir(parents=True)
        for args in ((), ("--apply",), ("--finish",)):
            r = run(["--home", str(fresh), "migrate", "rendered", *args])
            self.assertEqual(r.returncode, 0)
            self.assertIn("nothing to migrate", r.stdout)


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
        # The same throwaway HOME as `run()`; uv keeps its real cache and interpreters,
        # which otherwise default to paths under HOME and would re-download per call.
        env = dict(os.environ)
        env.pop("AOS_HOME", None)
        env.update({"UV_CACHE_DIR": self.uv_dir("cache"),
                    "UV_PYTHON_INSTALL_DIR": self.uv_dir("python")})
        with tempfile.TemporaryDirectory() as home:
            env.update({"HOME": home, **(env_extra or {})})
            return subprocess.run(["uv", "run", "--quiet", "--project", str(TOOL_DIR),
                                   "aos-cap", *args],
                                  capture_output=True, text=True, env=env)

    @staticmethod
    def uv_dir(kind):
        return subprocess.run(["uv", kind, "dir"], capture_output=True,
                              text=True).stdout.strip()

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
