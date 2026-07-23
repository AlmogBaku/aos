#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tier-0 tests for the kb capability's `base` tool.

Pattern (per the spec's testing doctrine): black-box subprocess invocation against
throwaway bases — the report/stdout text is the contract; no imports of tool
internals. Run: uv run tests/tool/test_base.py
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "capabilities/kb/skills/kb/scripts/base.py"
TEMPLATES = REPO / "capabilities/kb/skills/init/templates"


def run(args, env_extra=None, cwd=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


class BaseToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.reg = self.dir / "kb-registry.yaml"
        self.env = {"AOS_REGISTRY": str(self.reg), "AOS_AGENT": "agent:main"}
        self.root = self.dir / "b"
        r = run(["init", "b", "--path", str(self.root), "--purpose", "test base",
                 "--templates", str(TEMPLATES), "--default"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def b(self, *args):
        return run(["--base", str(self.root), *args], self.env)

    # -- init / scaffold ---------------------------------------------------
    def test_init_scaffolds_and_registers(self):
        for f in ["BASE.yaml", "AGENTS.md", "index.md", "log.md", "state.yaml",
                  ".gitignore"]:
            self.assertTrue((self.root / f).exists(), f)
        self.assertTrue((self.root / "raw" / "captures").is_dir())
        self.assertIn("name: b", self.reg.read_text())
        self.assertIn("default: b", self.reg.read_text())

    def test_init_fills_preseeded_registry_entry(self):
        # interview-first flow: registry entry exists, tree doesn't -> init fills it
        pre = self.dir / "pre"
        self.reg.write_text(
            f"default: p\nkbs:\n- name: p\n  path: {pre}\n  audience: private\n")
        r = run(["init", "p", "--path", str(pre), "--purpose", "preseeded",
                 "--templates", str(TEMPLATES)], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((pre / "BASE.yaml").exists())
        self.assertEqual(self.reg.read_text().count("name: p"), 1)  # no duplicate

    def test_init_refuses_double(self):
        r = run(["init", "b2", "--path", str(self.root),
                 "--templates", str(TEMPLATES)], self.env)
        self.assertNotEqual(r.returncode, 0)

    def test_fresh_base_lints_clean(self):
        r = self.b("lint")
        self.assertIn("Critical (0)", r.stdout)
        self.assertIn("Findings (0)", r.stdout)

    # -- layout guard ------------------------------------------------------
    def test_layout_mismatch_fails_loudly(self):
        by = self.root / "BASE.yaml"
        by.write_text(by.read_text().replace("layout: 1", "layout: 99"))
        r = self.b("inbox")
        self.assertEqual(r.returncode, 11)
        self.assertIn("Refusing to guess", r.stderr)

    # -- capture -----------------------------------------------------------
    def test_capture_lands_pending_with_log_line(self):
        r = self.b("capture", "--text", "Call the accountant", "--source", "t:x")
        self.assertIn("triage: pending", r.stdout)
        caps = list((self.root / "raw" / "captures").glob("*.md"))
        self.assertEqual(len(caps), 1)
        text = caps[0].read_text()
        self.assertIn("source_sha256:", text)
        self.assertIn("triage: pending", text)
        log = (self.root / "log.md").read_text()
        self.assertRegex(log, r"\| agent:main \| capture \| raw/captures/")

    def test_duplicate_capture_dropped(self):
        self.b("capture", "--text", "same content")
        r = self.b("capture", "--text", "same content")
        self.assertIn("duplicate", r.stdout)
        self.assertEqual(len(list((self.root / "raw" / "captures").glob("*.md"))), 1)

    def test_inbox_lists_pending(self):
        self.b("capture", "--text", "hello world")
        r = self.b("inbox")
        self.assertIn("1 pending item", r.stdout)

    # -- state -------------------------------------------------------------
    def test_state_add_bump_drop(self):
        self.assertEqual(self.b("state", "add", "--note", "Wife expecting",
                                "--ref", "entities/people/wife").returncode, 0)
        self.assertEqual(self.b("state", "bump", "--note", "expecting").returncode, 0)
        r = self.b("state", "show")
        self.assertIn("Wife expecting", r.stdout)
        self.assertEqual(self.b("state", "drop", "--note", "expecting").returncode, 0)
        self.assertNotIn("Wife expecting", self.b("state", "show").stdout)

    def test_state_cap_forces_eviction(self):
        by = self.root / "BASE.yaml"
        by.write_text(by.read_text().replace("max_items: 20", "max_items: 2"))
        self.b("state", "add", "--note", "one")
        self.b("state", "add", "--note", "two")
        r = self.b("state", "add", "--note", "three")
        self.assertEqual(r.returncode, 12)
        self.assertIn("cap", r.stderr)

    def test_state_check_flags_stale(self):
        self.b("state", "add", "--note", "old thing")
        sy = self.root / "state.yaml"
        sy.write_text(sy.read_text().replace("since: ", "since: 2020-01-01 #"))
        r = self.b("state", "check")
        self.assertIn("stale:", r.stdout)

    # -- search ------------------------------------------------------------
    def _page(self, rel, title, body="Body text.", **extra):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        fm = [f'title: "{title}"', "type: note", "created: 2026-01-01",
              "timestamp: 2026-01-01", f"description: {title} page"]
        for k, v in extra.items():
            fm.append(f"{k}: {v}")
        p.write_text("---\n" + "\n".join(fm) + f"\n---\n{body}\n")
        return p

    def test_search_exact_title_says_exists(self):
        self._page("concepts/acme.md", "Acme Corp")
        r = self.b("search", "Acme Corp")
        self.assertIn("EXISTS", r.stdout)
        self.assertIn("create_safety: exists", r.stdout)

    def test_search_alias_says_exists(self):
        self._page("concepts/acme.md", "Acme Corp", aliases='["Acme"]')
        r = self.b("search", "acme")
        self.assertIn("create_safety: exists", r.stdout)

    def test_search_weak_match_probable(self):
        self._page("concepts/pricing.md", "Pricing strategy",
                   body="Acme objected to the pricing.")
        r = self.b("search", "objected")
        self.assertIn("create_safety: probable", r.stdout)

    def test_search_no_match_unknown(self):
        r = self.b("search", "zebra-xylophone")
        self.assertIn("create_safety: unknown", r.stdout)

    # -- links -------------------------------------------------------------
    def test_links_backlinks_and_orphans(self):
        self._page("concepts/a.md", "A", body="links to [[concepts/b]]")
        self._page("concepts/b.md", "B")
        r = self.b("links", "concepts/b")
        self.assertIn("concepts/a.md", r.stdout)
        r = self.b("links", "--orphans")
        self.assertIn("concepts/a.md", r.stdout)  # nothing links to a

    # -- lint checks -------------------------------------------------------
    def test_lint_alias_collision_critical(self):
        self._page("concepts/x.md", "X", aliases='["acme"]')
        self._page("concepts/y.md", "Y", aliases='["acme"]')
        r = self.b("lint")
        self.assertIn("alias collision", r.stdout)

    def test_lint_index_drift_both_directions(self):
        self._page("concepts/unlisted.md", "Unlisted")
        idx = self.root / "index.md"
        idx.write_text(idx.read_text() + "\n- [[concepts/ghost]] — gone\n")
        out = self.b("lint").stdout
        self.assertIn("not listed in index.md", out)
        self.assertIn("dead index entry", out)

    def test_lint_broken_wikilink(self):
        self._page("concepts/a.md", "A", body="see [[concepts/missing]]")
        self.assertIn("broken wikilink", self.b("lint").stdout)

    def test_lint_unknown_type_and_field(self):
        self._page("concepts/t.md", "T")
        p = self.root / "concepts" / "t.md"
        p.write_text(p.read_text().replace("type: note", "type: alien\nweird: 1"))
        out = self.b("lint").stdout
        self.assertIn("not in BASE.yaml types", out)
        self.assertIn("outside schema", out)

    def test_lint_backup_file_critical(self):
        (self.root / "concepts").mkdir(exist_ok=True)
        (self.root / "concepts" / "x.md.backup.1").write_text("old")
        self.assertIn("backup file", self.b("lint").stdout)

    def test_lint_failed_capture_critical(self):
        self.b("capture", "--text", "will fail")
        cap = next((self.root / "raw" / "captures").glob("*.md"))
        cap.write_text(cap.read_text().replace("triage: pending", "triage: failed"))
        self.assertIn("failed state", self.b("lint").stdout)

    def test_lint_state_stale(self):
        self._page("concepts/new.md", "New")
        os.utime(self.root / "state.yaml", (1, 1))  # state far in the past
        self.assertIn("state_stale", self.b("lint").stdout)

    def test_lint_log_grammar(self):
        with open(self.root / "log.md", "a") as f:
            f.write("not a log line at all\n")
        self.assertIn("five-field grammar", self.b("lint").stdout)

    def test_lint_timeline_shape(self):
        self._page("concepts/tl.md", "TL",
                   body="Truth.\n\n---\n\n## Timeline\n- undated event\n")
        self.assertIn("timeline entry not dated", self.b("lint").stdout)

    # -- write verbs log themselves ---------------------------------------
    def test_every_write_verb_logs(self):
        self.b("capture", "--text", "log me")
        self.b("state", "add", "--note", "item")
        self._page("concepts/v.md", "V", verified="false")
        self.b("verify", "concepts/v")
        self.b("index", "rebuild")
        log = (self.root / "log.md").read_text()
        for verb in ["capture", "state", "verify", "create", "bootstrap"]:
            self.assertRegex(log, rf"\| {verb} \|", f"missing log verb {verb}")

    # -- grants ------------------------------------------------------------
    def test_grants_granted_and_denied(self):
        ok = self.b("grants", "check", "--subject", "agent:main", "--verb", "write",
                    "--path", "state.yaml")
        self.assertEqual(ok.returncode, 0)
        no = self.b("grants", "check", "--subject", "capability:sideload-x",
                    "--verb", "write", "--path", "state.yaml")
        self.assertEqual(no.returncode, 1)

    def test_grants_glob_semantics(self):
        # ** crosses /, * does not; archiver may write entities but not profile
        deep = self.b("grants", "check", "--subject", "agent:archiver",
                      "--verb", "write", "--path", "entities/people/deep/x.md")
        self.assertEqual(deep.returncode, 0)
        prof = self.b("grants", "check", "--subject", "agent:archiver",
                      "--verb", "write", "--path", "profile/soul.md")
        self.assertEqual(prof.returncode, 1)

    # -- verify ------------------------------------------------------------
    def test_verify_flips_flag(self):
        self._page("concepts/v.md", "V", verified="false")
        self.b("verify", "concepts/v")
        self.assertIn("verified: true", (self.root / "concepts" / "v.md").read_text())

    # -- index rebuild -----------------------------------------------------
    def test_index_rebuild_lists_descriptions(self):
        self._page("concepts/idea.md", "Big Idea")
        self.b("index", "rebuild")
        idx = (self.root / "index.md").read_text()
        self.assertIn("[[concepts/idea]]", idx)
        self.assertIn("Big Idea page", idx)

    # -- sync conflict -----------------------------------------------------
    def test_sync_conflict_aborts_clean_and_surfaces(self):
        remote = self.dir / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)

        def git(*a, cwd=self.root):
            subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)

        git("remote", "add", "origin", str(remote))
        git("add", "-A")
        git("commit", "-qm", "seed", "--allow-empty")
        git("push", "-qu", "origin", "HEAD")
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                cwd=self.root, capture_output=True,
                                text=True).stdout.strip()
        other = self.dir / "other"
        subprocess.run(["git", "clone", "-q", "-b", branch, str(remote), str(other)],
                       check=True, capture_output=True)
        (other / "AGENTS.md").write_text(
            (other / "AGENTS.md").read_text() + "\nremote change\n")
        git("-c", "user.name=other", "-c", "user.email=o@x",
            "commit", "-aqm", "remote", cwd=other)
        git("push", "-q", cwd=other)
        (self.root / "AGENTS.md").write_text(
            (self.root / "AGENTS.md").read_text() + "\nlocal conflicting change\n")

        r = self.b("sync")
        self.assertEqual(r.returncode, 3)
        self.assertIn("sync-conflict", (self.root / "log.md").read_text())
        self.assertIn("sync conflict",
                      (self.root / "_ops" / "needs-review.md").read_text())
        # repo left consistent (no rebase in progress)
        st = subprocess.run(["git", "status"], cwd=self.root, capture_output=True,
                            text=True).stdout
        self.assertNotIn("rebase in progress", st)

    # -- adopt -------------------------------------------------------------
    def test_adopt_zero_writes_and_most_restrictive_audience(self):
        foreign = self.dir / "foreign"
        foreign.mkdir()
        (foreign / "BASE.yaml").write_text(
            "layout: 1\nname: f\naudience: shared\nzones: {}\n")
        before = sorted(p.name for p in foreign.rglob("*"))
        r = run(["adopt", str(foreign), "--name", "f", "--audience", "private"],
                self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("audience: shared", r.stdout)  # shared wins over private claim
        after = sorted(p.name for p in foreign.rglob("*"))
        self.assertEqual(before, after)  # zero writes into the tree

    def test_adopt_non_base_reports_convergence(self):
        foreign = self.dir / "plain"
        foreign.mkdir()
        (foreign / "notes.md").write_text("# notes\n")
        r = run(["adopt", str(foreign)], self.env)
        self.assertIn("no BASE.yaml", r.stdout)
        self.assertIn("convergence path", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
