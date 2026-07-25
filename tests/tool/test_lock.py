#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tier-0 tests for the capability-lifecycle `aos-lock` tool.

Black-box subprocess invocation against a throwaway household — stdout text and exit
codes are the contract; no imports of tool internals.
Run: uv run tests/tool/test_lock.py
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "capabilities/capability-lifecycle/tool"

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


def run(args, env_extra=None, cwd=None):
    env = dict(os.environ)
    env.pop("AOS_HOME", None)
    env.update(env_extra or {})
    return subprocess.run(["uv", "run", "--quiet", "--project", str(TOOL_DIR),
                           "aos-lock", *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


class LockToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)
        cap = self.home / "capabilities" / "democap"
        (cap / "skills" / "democap").mkdir(parents=True)
        (cap / "CAPABILITY.md").write_text(VALID_MANIFEST)
        (cap / "README.md").write_text("# democap\n\n| a | b |\n|---|---|\n")
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
                         "--job", "job-abc123", "--config-key", "gtd.drain_hour")

    # -- manifest ----------------------------------------------------------
    def test_manifest_valid_prints_json(self):
        r = self.lock("manifest", str(self.home / "capabilities" / "democap"))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["id"], "democap")
        self.assertEqual(data["version"], "1.2.3")

    def test_manifest_unknown_key_rejected(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text(VALID_MANIFEST.replace("summary:", "sneaky: yes\nsummary:"))
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 12)
        self.assertIn("sneaky", r.stderr)

    def test_manifest_x_fields_allowed(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text(VALID_MANIFEST.replace("summary:", "x-vendor: hi\nsummary:"))
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_manifest_bad_version_rejected(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text(VALID_MANIFEST.replace("1.2.3", "v1.2"))
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 12)
        self.assertIn("version", r.stderr)

    def test_manifest_undeclared_skill_dir_rejected(self):
        extra = self.home / "capabilities" / "democap" / "skills" / "ghost"
        extra.mkdir()
        (extra / "SKILL.md").write_text("---\nname: ghost\ndescription: g. Use when.\n---\n")
        r = self.lock("manifest", str(self.home / "capabilities" / "democap"))
        self.assertEqual(r.returncode, 12)
        self.assertIn("ghost", r.stderr)

    # -- lockfile lifecycle ------------------------------------------------
    def test_init_creates_empty_lockfile(self):
        self.init()
        text = (self.home / ".aos" / "installs.lock.yaml").read_text()
        self.assertIn("version: 1", text)
        self.assertIn("installs:", text)

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
        self.assertIn("gtd.drain_hour", entry["config_keys"])
        for sha in entry["artifacts"].values():
            self.assertRegex(sha, r"^[0-9a-f]{64}$")

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

    def test_init_creates_aos_dir_on_fresh_clone(self):
        fresh = Path(self.tmp.name) / "fresh"
        fresh.mkdir()
        r = run(["--home", str(fresh), "init"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((fresh / ".aos" / "installs.lock.yaml").is_file())

    def test_init_requires_explicit_clone(self):
        bare = Path(self.tmp.name) / "bare"
        bare.mkdir()
        r = run(["init"], cwd=str(bare))
        self.assertEqual(r.returncode, 15)
        self.assertIn("--home", r.stderr)

    def test_record_resolves_relative_paths(self):
        self.init()
        r = run(["record", "democap", "--version", "1.2.3",
                 "--artifact", "artifact-one.md"], cwd=str(self.home))
        self.assertEqual(r.returncode, 0, r.stderr)
        s = run(["show", "democap"], cwd=str(Path(self.tmp.name)),
                env_extra={"AOS_HOME": str(self.home)})
        entry = json.loads(s.stdout)
        (path,) = entry["artifacts"].keys()
        self.assertTrue(Path(path).is_absolute())
        v = run(["verify", "democap"], cwd=str(Path(self.tmp.name)),
                env_extra={"AOS_HOME": str(self.home)})
        self.assertEqual(v.returncode, 0, v.stderr)

    def test_record_missing_artifact_clean_error(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(self.home / "no-such.md"))
        self.assertEqual(r.returncode, 16)
        self.assertIn("no-such.md", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

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

    def test_manifest_schedule_and_depends_rules(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text(VALID_MANIFEST.replace("skills:",
            "depends:\n  capabilities: [ghostcap]\n"
            "schedules:\n  - cron: \"0 4 * * *\"\n    agent: main\nskills:"))
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 12)
        self.assertIn("ghostcap", r.stderr)      # missing dependency
        self.assertIn("id", r.stderr)            # schedule id required
        self.assertIn("prompt_ref", r.stderr)    # agent form needs prompt_ref
        self.assertIn("degraded", r.stderr)      # degraded required

    def test_manifest_malformed_shapes_exit_12(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text(VALID_MANIFEST.replace("skills:",
            "depends: [not, a, mapping]\nschedules: [oops]\nskills:"))
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 12)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("mapping", r.stderr)

    def test_manifest_scalar_frontmatter_exit_12(self):
        cap = self.home / "capabilities" / "democap" / "CAPABILITY.md"
        cap.write_text("---\njust a string\n---\nbody\n")
        r = self.lock("manifest", str(cap.parent))
        self.assertEqual(r.returncode, 12)
        self.assertIn("mapping", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_manifest_accepts_all_shipped_capabilities(self):
        # drift guard: the tool must accept every in-repo manifest the lint accepts
        for cap in sorted((REPO / "capabilities").iterdir()):
            if (cap / "CAPABILITY.md").is_file():
                r = run(["--home", str(self.home), "manifest", str(cap)])
                self.assertEqual(r.returncode, 0, f"{cap.name}: {r.stderr}")

    def test_init_over_existing_lockfile_errors(self):
        self.init()
        r = self.lock("init")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)

    def test_verify_unknown_capability(self):
        self.init()
        r = self.lock("verify", "nope")
        self.assertEqual(r.returncode, 14)

    def test_record_env_lines_and_scripts_roundtrip(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3",
                      "--artifact", str(self.a1),
                      "--env-line", "MY_TOKEN_NAME", "--script", str(self.a2))
        self.assertEqual(r.returncode, 0, r.stderr)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertIn("MY_TOKEN_NAME", entry["env_lines"])
        self.assertEqual(len(entry["scripts"]), 1)

    # -- links + source roots (the household symlink-install contract) -----
    def make_link(self, name="skill-link"):
        target = self.home / "personal" / "capabilities" / "democap" / "skills" / "democap"
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text("---\nname: democap\n---\nrendered\n")
        link = self.home / name
        link.symlink_to(target)
        return link, target

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

    def test_verify_flags_missing_and_retargeted_link(self):
        self.init()
        link, target = self.make_link()
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

    def test_record_link_on_regular_file_errors(self):
        self.init()
        r = self.lock("record", "democap", "--version", "1.2.3", "--link", str(self.a1))
        self.assertEqual(r.returncode, 16)
        self.assertIn("not a symlink", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_home_verb_prints_resolved_root(self):
        self.init()
        r = self.lock("home")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), str(self.home))
        bare = Path(self.tmp.name) / "nohome"
        bare.mkdir()
        r = run(["home"], cwd=str(bare))
        self.assertEqual(r.returncode, 15)

    def test_relative_and_absolute_links_compare_equal(self):
        self.init()
        link, target = self.make_link()
        self.lock("record", "democap", "--version", "1.2.3", "--link", str(link))
        link.unlink()
        # same destination, relative spelling — must NOT read as drift
        link.symlink_to(os.path.relpath(target, link.parent))
        v = self.lock("verify", "democap")
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)

    def test_symlink_as_artifact_rejected(self):
        self.init()
        f = self.home / "real.md"
        f.write_text("x\n")
        ln = self.home / "link-to-file.md"
        ln.symlink_to(f)
        r = self.lock("record", "democap", "--version", "1.2.3", "--artifact", str(ln))
        self.assertEqual(r.returncode, 16)
        self.assertIn("--link", r.stderr)

    def test_rehash_refuses_to_empty_an_entry(self):
        self.init()
        self.record()
        self.a1.unlink()
        self.a2.unlink()
        r = self.lock("rehash", "democap")
        self.assertEqual(r.returncode, 16)
        entry = json.loads(self.lock("show", "democap").stdout)
        self.assertEqual(len(entry["artifacts"]), 2)   # entry left intact

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

    # -- clone discovery ---------------------------------------------------
    def test_discovery_walks_up_from_cwd(self):
        self.init()
        self.record()
        nested = self.home / "capabilities" / "democap" / "skills"
        r = run(["list"], cwd=str(nested))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap", r.stdout)

    def test_no_clone_found_errors(self):
        bare = Path(self.tmp.name) / "elsewhere"
        bare.mkdir()
        r = run(["list"], cwd=str(bare))
        self.assertEqual(r.returncode, 15)
        self.assertIn(".aos", r.stderr)

    def test_env_override_wins_over_cwd(self):
        self.init()
        self.record()
        bare = Path(self.tmp.name) / "elsewhere2"
        bare.mkdir()
        r = run(["list"], env_extra={"AOS_HOME": str(self.home)}, cwd=str(bare))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap", r.stdout)


SKILL_MD = "---\nname: {name}\ndescription: {name}. Use when testing {name}.\n---\nbody\n"


class SkillNameTest(unittest.TestCase):
    """The installed name (§2.5) and the collision gate. The shipped identity is the
    computed name, so that is what carries the Agent Skills limits."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / ".aos").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def cap(self, cap_id, skills, prefix=None, root="upstream", version="1.0.0"):
        """Write a capability and return its directory."""
        cap = self.home / root / "capabilities" / cap_id
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
        cap = self.cap("democap", ["democap", "sort"], prefix='""')
        self.assertEqual(self.names(cap)["sort"], "democap-sort")

    def test_json_reports_prefix_and_rows(self):
        cap = self.cap("democap", ["democap", "sort"], prefix="demo-")
        r = self.skills(cap, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["skill_prefix"], "demo-")
        self.assertEqual([s["installed_name"] for s in data["skills"]],
                         ["democap", "demo-sort"])

    # -- manifest validation ----------------------------------------------
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

    # -- the collision gate (exit 17) --------------------------------------
    def test_clean_check_reports_unclaimed(self):
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean: 2 skill names unclaimed", r.stdout)

    def test_collision_with_another_household_capability(self):
        self.cap("othercap", ["othercap", "sort"], prefix="democap-", root="personal")
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check")
        self.assertEqual(r.returncode, 17)
        self.assertIn("democap-sort", r.stderr)
        self.assertIn("othercap", r.stderr)

    def test_collision_inside_one_capability(self):
        """The entry skill's name, reached a second time through the prefix."""
        cap = self.cap("gtd-capture", ["gtd-capture", "capture"], prefix="gtd-")
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

    def test_reinstall_over_our_own_links_is_clean(self):
        harness = self.home / "harness" / "skills"
        (harness / "democap-sort").mkdir(parents=True)
        self.write_lock({"democap": {"links": {
            str(harness / "democap-sort"): "/elsewhere/skills/democap-sort"}}})
        cap = self.cap("democap", ["democap", "sort"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_non_skill_link_is_not_a_skill_name(self):
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

    def test_missing_harness_dir_errors(self):
        cap = self.cap("democap", ["democap"])
        r = self.skills(cap, "--check", "--harness-skills", str(self.home / "nope"))
        self.assertEqual(r.returncode, 16)

    def test_explicit_home_without_state_dir_errors(self):
        cap = self.cap("democap", ["democap"])
        bare = Path(self.tmp.name) / "bare"
        bare.mkdir()
        r = run(["--home", str(bare), "skills", str(cap), "--check"])
        self.assertEqual(r.returncode, 15)

    def write_lock(self, installs):
        (self.home / ".aos" / "installs.lock.yaml").write_text(
            "version: 1\ninstalls:\n" + "".join(
                f"  {cap}:\n    version: 1.0.0\n    links:\n" + "".join(
                    f"      {k}: {v}\n" for k, v in entry["links"].items())
                for cap, entry in installs.items()))

    # -- render ------------------------------------------------------------
    def test_render_lands_under_the_installed_name(self):
        cap = self.cap("democap", ["democap", "sort"])
        out = Path(self.tmp.name) / "renders"
        r = run(["render", str(cap), "sort", "--out", str(out)])
        self.assertEqual(r.returncode, 0, r.stderr)
        rendered = out / "democap-sort" / "SKILL.md"
        self.assertTrue(rendered.is_file())
        self.assertIn("name: democap-sort", rendered.read_text())
        self.assertIn("x-aos-origin: democap@1.0.0", rendered.read_text())

    def test_render_carries_bundled_assets(self):
        cap = self.cap("democap", ["democap", "sort"])
        (cap / "skills" / "sort" / "reference").mkdir()
        (cap / "skills" / "sort" / "reference" / "deep.md").write_text("depth\n")
        out = Path(self.tmp.name) / "renders"
        run(["render", str(cap), "sort", "--out", str(out)])
        self.assertEqual((out / "democap-sort" / "reference" / "deep.md").read_text(),
                         "depth\n")

    def test_render_preserves_mod_slots(self):
        cap = self.cap("democap", ["democap", "sort"])
        skill = cap / "skills" / "sort" / "SKILL.md"
        skill.write_text(skill.read_text() + "Confirm with {{mod: confirm_style}}.\n")
        out = Path(self.tmp.name) / "renders"
        run(["render", str(cap), "sort", "--out", str(out)])
        self.assertIn("{{mod: confirm_style}}", (out / "democap-sort" / "SKILL.md").read_text())

    def test_render_is_idempotent(self):
        cap = self.cap("democap", ["democap", "sort"])
        out = Path(self.tmp.name) / "renders"
        run(["render", str(cap), "sort", "--out", str(out)])
        first = (out / "democap-sort" / "SKILL.md").read_text()
        r = run(["render", str(cap), "sort", "--out", str(out), "--force"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((out / "democap-sort" / "SKILL.md").read_text(), first)

    def test_render_refuses_to_clobber_without_force(self):
        cap = self.cap("democap", ["democap", "sort"])
        out = Path(self.tmp.name) / "renders"
        run(["render", str(cap), "sort", "--out", str(out)])
        r = run(["render", str(cap), "sort", "--out", str(out)])
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stderr)

    def test_render_never_inherits_a_stale_origin_tag(self):
        cap = self.cap("democap", ["democap", "sort"])
        skill = cap / "skills" / "sort" / "SKILL.md"
        skill.write_text(skill.read_text().replace(
            "---\nbody", "x-aos-origin: someoneelse@9.9.9\n---\nbody"))
        out = Path(self.tmp.name) / "renders"
        run(["render", str(cap), "sort", "--out", str(out)])
        text = (out / "democap-sort" / "SKILL.md").read_text()
        self.assertNotIn("someoneelse", text)
        self.assertEqual(text.count("x-aos-origin"), 1)

    def test_relative_capability_dir_works(self):
        """`aos-lock skills .` from inside the capability — the contract's commands are
        written with <cap-dir> paths, so a relative one must not break the id check."""
        cap = self.cap("democap", ["democap", "sort"])
        r = run(["--home", str(self.home), "skills", "."], cwd=str(cap))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("democap-sort", r.stdout)

    def test_readme_in_a_flat_skills_dir_is_not_a_skill(self):
        harness = self.home / "harness" / "skills"
        harness.mkdir(parents=True)
        (harness / "README.md").write_text("what lives here\n")
        cap = self.cap("readme", ["readme"])
        r = self.skills(cap, "--check", "--harness-skills", str(harness))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_render_unknown_skill_errors(self):
        cap = self.cap("democap", ["democap"])
        r = run(["render", str(cap), "ghost", "--out", str(Path(self.tmp.name) / "r")])
        self.assertEqual(r.returncode, 14)


if __name__ == "__main__":
    unittest.main(verbosity=1)
