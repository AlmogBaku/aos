#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Tier-0 tests for the kb capability's `kb` tool (capabilities/kb/tool).

Pattern (per the spec's testing doctrine): black-box subprocess invocation against
throwaway bases — the report/stdout text is the contract; no imports of tool
internals. Run: uv run tests/tool/test_kb.py
"""
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "capabilities/kb/tool"
TEMPLATES = REPO / "capabilities/kb/skills/init/templates"


# A CI runner has no git identity, and `git commit` exits 128 without one. Several tests
# make ordinary git commits (seeding a remote, letting sync's merge commit), so the
# identity is supplied here rather than in the workflow: a test that needs one should
# carry it, or it only passes on a developer's machine.
#
# Deliberately NOT `git config --global` — that would mutate the runner. These env vars
# lose to the tool's own --author/AOS_PRINCIPAL_* handling, which is what the
# attribution tests assert, so they change no behavior those tests measure.
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test Runner", "GIT_AUTHOR_EMAIL": "runner@example.test",
    "GIT_COMMITTER_NAME": "Test Runner", "GIT_COMMITTER_EMAIL": "runner@example.test",
}


def git_env(extra=None):
    env = dict(os.environ)
    env.update(GIT_IDENTITY)
    env.update(extra or {})
    return env


def run(args, env_extra=None, cwd=None):
    return subprocess.run(["uv", "run", "--quiet", "--project", str(TOOL_DIR),
                           "kb", *args],
                          capture_output=True, text=True,
                          env=git_env(env_extra), cwd=cwd)


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

    def git(self, *args, root=None):
        return subprocess.run(["git", *args], cwd=root or self.root,
                              capture_output=True, text=True, check=False).stdout

    def log_lines(self, fmt="%s", root=None, n="-20"):
        """git is the audit substrate now, so the assertions read it directly."""
        return self.git("log", n, f"--pretty={fmt}", root=root).splitlines()

    # -- init / scaffold ---------------------------------------------------
    def test_init_scaffolds_and_registers(self):
        for f in ["BASE.yaml", "AGENTS.md", "index.md", "state.yaml",
                  ".gitignore"]:
            self.assertTrue((self.root / f).exists(), f)
        # log.md is gone: git holds the audit trail, and a single append-only file
        # written by every verb was the one thing guaranteed to conflict on sync.
        self.assertFalse((self.root / "log.md").exists())
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
    def test_capture_lands_pending_with_attributed_commit(self):
        r = self.b("capture", "--text", "Call the accountant", "--source", "t:x")
        self.assertIn("triage: pending", r.stdout)
        caps = list((self.root / "raw" / "captures").glob("*.md"))
        self.assertEqual(len(caps), 1)
        text = caps[0].read_text()
        self.assertIn("source_sha256:", text)
        self.assertIn("triage: pending", text)
        # One write, one commit: the committer is the acting agent, and the trailers
        # carry what the five-field log line used to.
        body = self.git("log", "-1", "--pretty=%cn%n%s%n%b")
        self.assertIn("agent:main", body)
        self.assertIn("capture:", body)
        self.assertIn("aos-verb: capture", body)
        self.assertRegex(body, r"aos-path: raw/captures/")

    def test_capture_author_is_the_principal_committer_is_the_agent(self):
        self.b("--author-name", "Dana Fixture", "--author-email", "dana@example.com",
               "--agent", "agent:archiver",
               "capture", "--text", "who wrote this")
        an, ae, cn = self.git("log", "-1", "--pretty=%an%n%ae%n%cn").splitlines()[:3]
        self.assertEqual(an, "Dana Fixture")     # the human whose knowledge it is
        self.assertEqual(ae, "dana@example.com")
        self.assertEqual(cn, "agent:archiver")   # the agent that applied it

    def test_capture_stays_well_inside_the_quick_capture_budget(self):
        # Capture now writes a file *and* commits, so the budget is worth pinning:
        # gtd-capture promises under 5s end to end. Measured here at ~0.12s including
        # process launch (the commit itself is ~30ms); the bound is deliberately loose
        # so this catches a regression, not a slow machine.
        start = time.perf_counter()
        self.b("capture", "--text", "how long does this take")
        self.assertLess(time.perf_counter() - start, 2.0)

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

    def test_lint_reports_by_default_and_returns_a_verdict_on_demand(self):
        """Report-only is the contract, and --ci is what makes it falsifiable: "the
        report is the interface" only means something if there is a second mode to
        contrast with. The flag outlived the CI janitor it was built for — a user's own
        hook or Action still needs an exit code, and parsing the report text instead
        would be far worse."""
        (self.root / "concepts").mkdir(exist_ok=True)
        (self.root / "concepts" / "x.md.backup.1").write_text("old")
        self.assertEqual(self.b("lint").returncode, 0)
        self.assertNotEqual(self.b("lint", "--ci").returncode, 0)

    def test_no_base_gets_ci_wiring(self):
        """The shared-KB CI infrastructure is descoped. A base is a git repo and
        nothing more; whether its forge runs anything is the owner's business, not
        something `init` decides for them."""
        self.assertFalse((self.root / ".github").exists())

    def test_lint_failed_capture_critical(self):
        self.b("capture", "--text", "will fail")
        cap = next((self.root / "raw" / "captures").glob("*.md"))
        cap.write_text(cap.read_text().replace("triage: pending", "triage: failed"))
        self.assertIn("failed state", self.b("lint").stdout)

    def test_lint_state_stale(self):
        self._page("concepts/new.md", "New")
        os.utime(self.root / "state.yaml", (1, 1))  # state far in the past
        self.assertIn("state_stale", self.b("lint").stdout)

    def test_lint_reports_uncommitted_writes(self):
        # A hand-write that never became a commit has no acting subject recorded.
        self._page("concepts/loose.md", "Loose")
        self.assertIn("uncommitted changes", self.b("lint").stdout)

    def test_lint_reports_sequencer_state_as_critical(self):
        # Left-behind operation state is what blocks every later sync, so the lint
        # has to see it rather than let the next tick fail silently forever.
        (self.root / ".git" / "MERGE_HEAD").write_text("0" * 40 + "\n")
        self.assertIn("mid-MERGE_HEAD", self.b("lint").stdout)

    def test_lint_timeline_shape(self):
        self._page("concepts/tl.md", "TL",
                   body="Truth.\n\n---\n\n## Timeline\n- undated event\n")
        self.assertIn("timeline entry not dated", self.b("lint").stdout)

    # -- write verbs commit themselves ------------------------------------
    def test_every_write_verb_commits(self):
        self.b("capture", "--text", "commit me")
        self.b("state", "add", "--note", "item")
        self._page("concepts/v.md", "V", verified="false")
        self.b("commit", "--verb", "create", "--path", "concepts/v.md",
               "--summary", "new page")
        self.b("verify", "concepts/v")
        self.b("index", "rebuild")
        trailers = "\n".join(self.log_lines("%b"))
        for verb in ["capture", "state", "verify", "create", "bootstrap"]:
            self.assertIn(f"aos-verb: {verb}", trailers, f"missing aos-verb {verb}")

    def test_commit_rejects_a_verb_outside_the_vocabulary(self):
        self._page("concepts/w.md", "W")
        r = self.b("commit", "--verb", "yolo", "--path", "concepts/w.md",
                   "--summary", "nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown aos-verb", r.stderr)

    def test_history_renders_recent_activity(self):
        self.b("capture", "--text", "orient me")
        out = self.b("history", "--limit", "5").stdout
        self.assertIn("capture:", out)
        self.assertIn("agent:main", out)
        self.assertIn("raw/captures/", out)

    def test_lint_via_grammar(self):
        am = self.root / "AGENTS.md"
        s = am.read_text()
        s = s.replace(
            "| `*` | `**` | read | user |",
            "| agent:x | `foo/**` | write | user | 2026-01-01 | kb+other@1.2.3 | bad |\n"
            "| `*` | `**` | read | user |")
        am.write_text(s)
        out = self.b("lint").stdout
        self.assertIn("doesn't parse as <capability>@<x.y.z>", out)

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


    # -- LFS (workstream B) ------------------------------------------------
    def test_init_scaffolds_gitattributes(self):
        ga = self.root / ".gitattributes"
        self.assertTrue(ga.exists())
        self.assertIn("filter=lfs", ga.read_text())

    def test_lint_flags_large_binary_dodging_lfs(self):
        big = self.root / "concepts" / "video.xyz"
        big.parent.mkdir(exist_ok=True)
        big.write_bytes(b"x" * (1024 * 1024 + 10))
        self.assertIn("not matching any LFS pattern", self.b("lint").stdout)
        tracked = self.root / "concepts" / "clip.mp4"
        tracked.write_bytes(b"x" * (1024 * 1024 + 10))
        out = self.b("lint").stdout
        self.assertNotIn("clip.mp4", out.split("not matching")[0].rsplit(chr(10), 1)[-1]
                         if "not matching" in out else out)
        self.assertNotIn("clip.mp4: large non-text", out)

    # -- import (workstream A) ---------------------------------------------
    FIXTURE = REPO / "tests/fixtures/import-src-v1"

    def _tree_hash(self, root):
        import hashlib as h
        acc = h.sha256()
        for p in sorted(root.rglob("*")):
            if p.is_file():
                acc.update(p.relative_to(root).as_posix().encode())
                acc.update(p.read_bytes())
        return acc.hexdigest()

    def test_import_survey_shapes(self):
        r = run(["import", "survey", str(self.FIXTURE)], self.env)
        self.assertIn("shape: old-methodology", r.stdout)
        self.assertIn("markdown files:", r.stdout)
        r = run(["import", "survey", str(self.root)], self.env)
        self.assertIn("shape: base-v2", r.stdout)
        self.assertIn("adopt", r.stdout)

    def test_import_survey_is_read_only(self):
        before = self._tree_hash(self.FIXTURE)
        run(["import", "survey", str(self.FIXTURE)], self.env)
        run(["import", "survey", str(self.FIXTURE), "--json"], self.env)
        self.assertEqual(before, self._tree_hash(self.FIXTURE))


    # -- review-sweep regression + coverage-gap tests ----------------------
    def test_glob_boundary_no_name_suffix_match(self):
        # `**/x.md` must not match `not-x.md` (ACL over-grant regression)
        am = self.root / "AGENTS.md"
        am.write_text(am.read_text().replace(
            "| agent:archiver | `raw/**` |",
            "| agent:x | `**/secret.md` | write | user | 2026-01-01 | — | t |\n"
            "| agent:archiver | `raw/**` |"))
        deep = self.b("grants", "check", "--subject", "agent:x", "--verb", "write",
                      "--path", "a/b/secret.md")
        self.assertEqual(deep.returncode, 0)
        top = self.b("grants", "check", "--subject", "agent:x", "--verb", "write",
                     "--path", "secret.md")
        self.assertEqual(top.returncode, 0)
        suffix = self.b("grants", "check", "--subject", "agent:x", "--verb", "write",
                        "--path", "not-secret.md")
        self.assertEqual(suffix.returncode, 1)

    def test_sync_first_push_to_empty_remote_is_not_conflict(self):
        remote = self.dir / "empty.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)],
                       cwd=self.root, check=True)
        r = self.b("sync")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertNotIn("aos-verb: sync-conflict", "\n".join(self.log_lines("%b")))

    def test_adopt_layout_guard_before_registry(self):
        foreign = self.dir / "f99"
        foreign.mkdir()
        (foreign / "BASE.yaml").write_text("layout: 99\nname: f99\nzones: {}\n")
        r = run(["adopt", str(foreign), "--name", "f99"], self.env)
        self.assertEqual(r.returncode, 11)
        self.assertNotIn("f99", self.reg.read_text())  # nothing half-registered

    def test_refuse_records_commit_and_review_entry(self):
        r = self.b("refuse", "--path", "state.yaml",
                   "--subject", "capability:sideload-x", "--reason", "no grant")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("aos-verb: refuse", "\n".join(self.log_lines("%b")))
        # One file per queue entry — a single appended queue file is written by every
        # agent on every machine, which is exactly what conflicts on every sync.
        entries = list((self.root / "_ops" / "needs-review").glob("*.md"))
        self.assertEqual(len(entries), 1)
        self.assertIn("refused write", entries[0].read_text())

    def test_inbox_failed_with_scalar_meta_survives(self):
        self.b("capture", "--text", "will fail oddly")
        cap = next((self.root / "raw" / "captures").glob("*.md"))
        cap.write_text(cap.read_text()
                       .replace("triage: pending", "triage: failed")
                       .replace("verified: false", "verified: false\nmeta: broken"))
        r = self.b("inbox", "--failed")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 failed item", r.stdout)

    def test_state_exact_match_beats_substring(self):
        self.b("state", "add", "--note", "item 2")
        self.b("state", "add", "--note", "item 20")
        r = self.b("state", "bump", "--note", "item 2")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_index_drift_not_fooled_by_substring(self):
        self._page("concepts/car.md", "Car")
        self._page("concepts/car-search.md", "Car search")
        self.b("index", "rebuild")
        idx = self.root / "index.md"
        # remove only the car.md entry; car-search remains (whose stem CONTAINS "car")
        idx.write_text("\n".join(l for l in idx.read_text().splitlines()
                                  if "[[concepts/car]]" not in l))
        out = self.b("lint").stdout
        self.assertIn("concepts/car.md not listed", out)

    def test_timeline_in_code_fence_ignored(self):
        self._page("concepts/doc.md", "Doc",
                   body="Text.\n\n```markdown\n## Timeline\n- undated\n```\nMore.\n")
        self.assertNotIn("timeline", self.b("lint").stdout.lower())

    def test_orphan_self_link_still_orphan(self):
        self._page("concepts/loner.md", "Loner", body="see [[concepts/loner]]")
        self.assertIn("concepts/loner.md", self.b("links", "--orphans").stdout)

    def test_lint_duplicate_title_critical(self):
        self._page("concepts/a1.md", "Same Title")
        self._page("concepts/a2.md", "Same Title")
        self.assertIn("duplicate title", self.b("lint").stdout)

    def test_lint_state_over_cap_critical(self):
        sy = self.root / "state.yaml"
        items = "items:\n" + "".join(
            f"- note: n{i}\n  since: 2026-01-01\n" for i in range(25))
        sy.write_text(items)
        self.assertIn("state.yaml over cap", self.b("lint").stdout)

    def test_lint_stale_seedling(self):
        self._page("concepts/old-seed.md", "Old Seed",
                   growth_stage="seedling")
        p = self.root / "concepts" / "old-seed.md"
        p.write_text(p.read_text().replace("created: 2026-01-01",
                                           "created: 2025-01-01"))
        self.assertIn("stale seedling", self.b("lint").stdout)

    def test_lint_unverified_with_inbound_info(self):
        self._page("concepts/hunch.md", "Hunch", verified="false")
        self._page("concepts/citer.md", "Citer", body="builds on [[concepts/hunch]]")
        self.assertIn("unverified pages with inbound", self.b("lint").stdout)

    def test_lint_reports_a_sweep_commit_as_unattributed(self):
        # sync commits a hand-write rather than dropping it — data safety first — but
        # marks it, so the audit sees a write with no acting subject.
        self._page("concepts/swept.md", "Swept")
        self.b("sync")
        self.assertIn("swept by sync", self.b("lint").stdout)

    def test_lint_invalid_triage_and_missing_frontmatter(self):
        raw = self.root / "raw" / "captures"
        raw.mkdir(parents=True, exist_ok=True)
        (raw / "weird.md").write_text("no frontmatter at all\n")
        self.b("capture", "--text", "triage test")
        cap = next(p for p in raw.glob("*.md") if p.name != "weird.md")
        cap.write_text(cap.read_text().replace("triage: pending", "triage: maybe"))
        out = self.b("lint").stdout
        self.assertIn("raw file without frontmatter", out)
        self.assertIn("not in ['done', 'failed', 'pending']", out)

    def test_lint_grants_audit_flags_ungranted_author(self):
        def git(*a):
            subprocess.run(["git", *a], cwd=self.root, check=True, env=git_env(),
                           capture_output=True)
        (self.root / "concepts").mkdir(exist_ok=True)
        (self.root / "concepts" / "rogue.md").write_text("---\ntitle: R\n---\nx\n")
        git("add", "-A")
        # This commit's whole point is WHO made it, so it names its own identity via
        # env rather than `-c`: GIT_COMMITTER_* from git_env() would otherwise win over
        # a `-c user.name`, and the audit reads the committer.
        subprocess.run(["git", "commit", "-qm", "rogue write"], cwd=self.root,
                       check=True, capture_output=True,
                       env=git_env({"GIT_COMMITTER_NAME": "agent:rogue",
                                    "GIT_COMMITTER_EMAIL": "r@x"}))
        self.assertIn("grants audit: agent:rogue", self.b("lint").stdout)

    # -- sync conflict -----------------------------------------------------
    def test_sync_conflict_aborts_clean_and_surfaces(self):
        remote = self.dir / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)

        def git(*a, cwd=self.root):
            subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                           env=git_env())

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
        self.assertIn("aos-verb: sync-conflict", "\n".join(self.log_lines("%b")))
        entries = list((self.root / "_ops" / "needs-review").glob("*.md"))
        self.assertTrue(any("sync conflict" in e.read_text() for e in entries))
        # repo left consistent — nothing mid-flight, so the next tick can run
        st = subprocess.run(["git", "status"], cwd=self.root, capture_output=True,
                            text=True).stdout
        self.assertNotIn("rebase in progress", st)
        self.assertNotIn("You have unmerged paths", st)

    def test_sync_refuses_while_an_operation_is_mid_flight(self):
        # The permanent-stall bug: staging a conflicted worktree commits the conflict
        # markers, and git then refuses to start another operation over the leftover
        # state, so every later tick fails too. Refusing up front keeps it recoverable.
        (self.root / ".git" / "MERGE_HEAD").write_text("0" * 40 + "\n")
        (self.root / "AGENTS.md").write_text("<<<<<<< HEAD\nUNMERGED-SENTINEL\n")
        r = self.b("sync")
        self.assertEqual(r.returncode, 5)
        self.assertIn("mid-MERGE_HEAD", r.stderr)
        # and it did NOT commit the conflicted worktree
        self.assertNotIn("UNMERGED-SENTINEL", self.git("show", "HEAD:AGENTS.md"))

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


class SharedBaseTest(unittest.TestCase):
    """A base two people share.

    Every property here only appears once there is more than one principal — which is
    exactly the question the single-user design never had to answer."""

    ALICE = {"AOS_PRINCIPAL_NAME": "Alice Example",
             "AOS_PRINCIPAL_EMAIL": "alice@example.com"}
    BOB = {"AOS_PRINCIPAL_NAME": "Bob Example",
           "AOS_PRINCIPAL_EMAIL": "bob@example.com"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.reg = self.dir / "kb-registry.yaml"
        self.env = {"AOS_REGISTRY": str(self.reg), "AOS_AGENT": "agent:main"}
        self.root = self.dir / "team"
        r = run(["init", "team", "--path", str(self.root), "--audience", "shared",
                 "--purpose", "team base", "--templates", str(TEMPLATES),
                 "--default"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        cfg = self.root / "BASE.yaml"
        cfg.write_text(cfg.read_text() +
                       "\nprincipals:\n"
                       "  alice@example.com: user:alice\n"
                       "  bob@example.com: user:bob\n")

    def tearDown(self):
        self.tmp.cleanup()

    def b(self, *args, who=None):
        return run(["--base", str(self.root), *args], {**self.env, **(who or {})})

    def test_a_shared_base_gets_no_workflow_either(self):
        """`--audience shared` used to emit a janitor workflow. It no longer does: a
        shared base has no neutral actor today, and shipping a workflow that implies
        otherwise is the claim being withdrawn."""
        self.assertFalse((self.root / ".github").exists())

    def test_state_is_sharded_per_principal(self):
        self.b("state", "add", "--note", "alice's thread", who=self.ALICE)
        self.b("state", "add", "--note", "bob's thread", who=self.BOB)
        alice = self.root / "state" / "user-alice.yaml"
        bob = self.root / "state" / "user-bob.yaml"
        self.assertTrue(alice.exists() and bob.exists())
        # Each shard has exactly one writer, so neither rewrites the other's file —
        # which is what makes "single writer" literally true on a shared base.
        self.assertIn("alice's thread", alice.read_text())
        self.assertNotIn("bob's thread", alice.read_text())

    def test_inbox_shows_only_this_principals_captures(self):
        self.b("capture", "--text", "alice note", who=self.ALICE)
        self.b("capture", "--text", "bob note", who=self.BOB)
        mine = self.b("inbox", who=self.ALICE).stdout
        self.assertIn("(1 pending item)", mine)
        self.assertIn("belong to other principals", mine)
        # A count, never a path: the other principal's material must not land in
        # this agent's context at all.
        self.assertNotIn("bob", mine.lower())
        self.assertIn("(2 pending items)", self.b("inbox", "--all",
                                                  who=self.ALICE).stdout)

    def test_dedup_does_not_drop_another_principals_identical_capture(self):
        self.b("capture", "--text", "the same link", who=self.ALICE)
        r = self.b("capture", "--text", "the same link", who=self.BOB)
        self.assertNotIn("duplicate", r.stdout)
        self.assertEqual(len(list((self.root / "raw" / "captures").glob("*.md"))), 2)
        self.assertNotIn("alice", r.stdout.lower())  # no path disclosure either

    def test_dedup_still_drops_the_same_principals_resend(self):
        self.b("capture", "--text", "double send", who=self.ALICE)
        self.assertIn("duplicate",
                      self.b("capture", "--text", "double send",
                             who=self.ALICE).stdout)

    def test_llm_routed_write_into_a_shared_base_is_critical(self):
        self.b("capture", "--text", "routed by a classifier", who=self.ALICE)
        cap = next((self.root / "raw" / "captures").glob("*.md"))
        cap.write_text(cap.read_text().replace(
            "triage: pending",
            "triage: pending\nkb_routing:\n  method: llm\n  confidence: 0.9\n"
            "  status: routed"))
        self.assertIn("no LLM-routed write may ever land here",
                      self.b("lint", who=self.ALICE).stdout)

    def test_unrostered_author_is_reported_as_unattributed(self):
        self.b("capture", "--text", "who are you",
               who={"AOS_PRINCIPAL_NAME": "Stranger",
                    "AOS_PRINCIPAL_EMAIL": "nobody@elsewhere.test"})
        self.assertIn("is not in the BASE.yaml principals roster",
                      self.b("lint", who=self.ALICE).stdout)

    def test_two_machines_capturing_concurrently_do_not_conflict(self):
        remote = self.dir / "team.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)],
                       cwd=self.root, check=True)
        self.assertEqual(self.b("sync", who=self.ALICE).returncode, 0)

        clone = self.dir / "bobs-machine"
        subprocess.run(["git", "clone", "-q", str(remote), str(clone)],
                       check=True, capture_output=True)

        # Both capture before either syncs — the real shape of two machines on one
        # interval. One file per record means there is simply nothing to merge.
        self.b("capture", "--text", "alice's find", who=self.ALICE)
        run(["--base", str(clone), "capture", "--text", "bob's find"],
            {**self.env, **self.BOB})

        self.assertEqual(self.b("sync", who=self.ALICE).returncode, 0)
        r = run(["--base", str(clone), "sync"], {**self.env, **self.BOB})
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

        caps = list((clone / "raw" / "captures").glob("*.md"))
        self.assertEqual(len(caps), 2, [p.name for p in caps])
        self.assertFalse(list((clone / "_ops" / "needs-review").glob("*.md"))
                         if (clone / "_ops" / "needs-review").is_dir() else [])


class PackagingTest(unittest.TestCase):
    """The command is `kb`, because `base<TAB>` is ambiguous against base32/base64/
    basename on every Linux box. `base == repo` survives as the *concept* — a command
    needn't be named after its object (`git` acts on repositories)."""

    def test_the_command_is_kb(self):
        # `--version` also reports the layout; that it reads 2 is LayoutTest's
        # assertion, since LAYOUT flips in the task that can honour it.
        r = run(["--version"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("kb 0.7.0", r.stdout)

    def test_the_old_command_name_is_gone(self):
        pyproject = (TOOL_DIR / "pyproject.toml").read_text()
        self.assertIn('name = "aos-kb"', pyproject)
        self.assertIn('kb = "aos_kb.cli:main"', pyproject)
        # The old names, spelled defensively: a `sed` sweep of the module name would
        # otherwise rewrite these assertions into tautologies.
        old_pkg, old_mod = "aos" + "-base", "aos" + "_base"
        self.assertNotIn(old_pkg, pyproject)
        self.assertNotIn(old_mod, pyproject)
        self.assertFalse((TOOL_DIR / "src" / old_mod).exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
